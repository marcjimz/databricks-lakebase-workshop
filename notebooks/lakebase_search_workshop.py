# Databricks notebook source
# MAGIC %md
# MAGIC # AI-DLC with Lakebase Search
# MAGIC
# MAGIC The one notebook for the workshop. Run each section when `docs/exercises.md` tells you to;
# MAGIC VS Code (with the Lakebase SCM extension) handles branches, migrations and tests.
# MAGIC
# MAGIC | Section | Exercise |
# MAGIC |---|---|
# MAGIC | 0. Setup | before you start |
# MAGIC | 1. Stage your data | Prepare synthetic data |
# MAGIC | 2. Sync into Lakebase | Prepare synthetic data |
# MAGIC | 3. Connect to a branch | Exercises 2 and 3 |
# MAGIC | 4. Search and query plans | Exercise 5 |
# MAGIC | 5. Scale up and down | Scale up and scale down |
# MAGIC | 6. Confirm the baseline is unchanged | Exercise 6 |
# MAGIC | 7. Optional: incremental ingestion | extra |
# MAGIC
# MAGIC Every section is safe to re-run.

# COMMAND ----------

# MAGIC %md ## 0. Setup

# COMMAND ----------

# MAGIC %pip install -q "databricks-sdk>=0.131.0" "psycopg[binary]>=3.2"
# MAGIC %restart_python

# COMMAND ----------

dbutils.widgets.text("catalog", "<CATALOG>", "Catalog")
dbutils.widgets.text("shared_schema", "lakebase_workshop_shared", "Shared schema")
dbutils.widgets.text("lakebase_project", "<LAKEBASE_PROJECT_ID>", "Lakebase project")
dbutils.widgets.text("branch", "production", "Lakebase branch")
dbutils.widgets.text("stop_after", "", "Stop after (job use)")

# COMMAND ----------

import re
import time

import psycopg
from databricks.sdk import WorkspaceClient
from databricks.sdk.common.types.fieldmask import FieldMask
from databricks.sdk.errors import NotFound
from databricks.sdk.service import postgres as pg

w = WorkspaceClient()

catalog = dbutils.widgets.get("catalog")
shared_schema = dbutils.widgets.get("shared_schema")
project = dbutils.widgets.get("lakebase_project")
assert not catalog.startswith("<") and not project.startswith("<"), "Fill in the catalog and lakebase_project widgets."

user = spark.sql("SELECT current_user()").first()[0]
# Same rule as WorkshopNaming.SchemaFor in the C# project: marcin.jimenez@... -> lakebase_marcin_jimenez
schema = "lakebase_" + re.sub("[^a-z0-9]+", "_", user.split("@")[0].lower()).strip("_")

source_table = f"`{catalog}`.`{schema}`.support_articles"
shared_table = f"`{catalog}`.`{shared_schema}`.support_articles"
synced_table_id = f"{catalog}.{schema}.support_articles_synced"
pg_articles = f'"{schema}".support_articles_synced'
project_name = f"projects/{project}"
baseline_branch = next(b for b in w.postgres.list_branches(parent=project_name) if b.status.default).name.split("/")[-1]


def selected_branch():
    return dbutils.widgets.get("branch")


def endpoint_for(branch_id):
    return next(e for e in w.postgres.list_endpoints(parent=f"{project_name}/branches/{branch_id}")
                if e.status.endpoint_type == pg.EndpointType.ENDPOINT_TYPE_READ_WRITE)


def connect(branch_id=None):
    """Open a Postgres connection to a Lakebase branch with a fresh OAuth credential."""
    ep = endpoint_for(branch_id or selected_branch())
    cred = w.postgres.generate_database_credential(endpoint=ep.name)
    return psycopg.connect(host=ep.status.hosts.host, dbname="databricks_postgres", user=user,
                           password=cred.token, sslmode="require", autocommit=True)


def query(sql, params=None, branch_id=None):
    with connect(branch_id) as conn:
        cur = conn.execute(sql, params)
        return cur.fetchall() if cur.description else []


print(f"User           : {user}")
print(f"Your schema    : {catalog}.{schema}")
print(f"Lakebase       : {project_name} (baseline branch: {baseline_branch})")
print(f"Selected branch: {selected_branch()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Stage your data
# MAGIC Copies the shared support articles (and their precomputed embeddings) into **your own schema**.
# MAGIC Change data feed is on so the synced table can pick up later changes incrementally.

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{schema}`")
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {source_table} (
  article_id BIGINT NOT NULL, title STRING, category STRING, product STRING, body STRING,
  updated_at TIMESTAMP, batch INT, embedding ARRAY<FLOAT>
) TBLPROPERTIES (delta.enableChangeDataFeed = true)
""")
# MERGE (not overwrite) keeps re-runs idempotent and the change feed intact.
spark.sql(f"""
MERGE INTO {source_table} t
USING (SELECT * FROM {shared_table} WHERE batch = 1) s ON t.article_id = s.article_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
""")
display(spark.sql(f"SELECT count(*) AS articles, max(size(embedding)) AS embedding_dim FROM {source_table}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Sync into Lakebase
# MAGIC Creates a synced table from your Delta table into the **baseline** Lakebase branch (once), then waits
# MAGIC for it to come online. Embeddings land as a pgvector `vector` column.

# COMMAND ----------

embedding_dim = spark.sql(f"SELECT max(size(embedding)) FROM {source_table}").first()[0]
synced_name = f"synced_tables/{synced_table_id}"

# The vector column type comes from pgvector, which must exist before the sync is created.
query("CREATE EXTENSION IF NOT EXISTS vector", branch_id=baseline_branch)

try:
    existing = w.postgres.get_synced_table(name=synced_name)
    state = existing.status.detailed_state.value if existing.status and existing.status.detailed_state else ""
    if "FAILED" in state:
        print(f"Synced table is {state}; deleting it so it can be recreated.")
        w.postgres.delete_synced_table(name=synced_name)
        while True:
            try:
                w.postgres.get_synced_table(name=synced_name)
                time.sleep(10)
            except NotFound:
                break
        raise NotFound("recreate")
    print(f"Synced table {synced_table_id} already exists ({state}).")
except NotFound:
    w.postgres.create_synced_table(
        synced_table_id=synced_table_id,
        synced_table=pg.SyncedTable(spec=pg.SyncedTableSyncedTableSpec(
            branch=f"{project_name}/branches/{baseline_branch}",
            source_table_full_name=synced_table_id.replace("support_articles_synced", "support_articles"),
            primary_key_columns=["article_id"],
            scheduling_policy=pg.SyncedTableSyncedTableSpecSyncedTableSchedulingPolicy.TRIGGERED,
            postgres_database="databricks_postgres",
            type_overrides=[pg.SyncedTableSyncedTableSpecTypeOverride(
                column_name="embedding", pg_type=pg.SyncedTableSyncedTableSpecPgSpecificType.PG_SPECIFIC_TYPE_VECTOR,
                size=embedding_dim)],
            new_pipeline_spec=pg.NewPipelineSpec(storage_catalog=catalog, storage_schema=schema),
        )),
    )
    print(f"Creating synced table {synced_table_id} ...")


def wait_for_sync(timeout_s=1200):
    online = {pg.SyncedTableState.SYNCED_TABLE_ONLINE, pg.SyncedTableState.SYNCED_TABLE_ONLINE_NO_PENDING_UPDATE}
    deadline = time.time() + timeout_s
    while True:
        status = w.postgres.get_synced_table(name=f"synced_tables/{synced_table_id}").status
        print(f"  {status.detailed_state.value if status.detailed_state else 'PENDING'}")
        if status.detailed_state in online:
            return status
        if status.detailed_state and "FAILED" in status.detailed_state.value:
            raise RuntimeError(status.message)
        if time.time() > deadline:
            raise TimeoutError("Synced table is not online yet; re-run this cell to keep waiting.")
        time.sleep(30)


sync_status = wait_for_sync()
delta_rows = spark.table(source_table).count()
pg_rows = query(f"SELECT count(*) FROM {pg_articles}", branch_id=baseline_branch)[0][0]
print(f"Delta rows: {delta_rows} | Lakebase rows on {baseline_branch}: {pg_rows}")
assert delta_rows == pg_rows, "Row counts differ; wait for the sync to finish and re-run."

if dbutils.widgets.get("stop_after") == "sync":
    dbutils.notebook.exit(f"Staged and synced {pg_rows} articles into {project_name}/branches/{baseline_branch}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Connect to a branch
# MAGIC After you create `search-dev` in VS Code (exercise 2), set the **branch** widget above to `search-dev`
# MAGIC and re-run this cell. Switching the widget is how the notebook "reconnects" (exercise 3); VS Code does the
# MAGIC same by rewriting `.env`.

# COMMAND ----------

branch_id = selected_branch()
ep = endpoint_for(branch_id)
rows = query(f"SELECT count(*) FROM {pg_articles}")[0][0]
tables = query("""
SELECT table_schema || '.' || table_name FROM information_schema.tables
WHERE table_schema NOT IN ('pg_catalog', 'information_schema') ORDER BY 1""")
print(f"Branch  : {branch_id}")
print(f"Host    : {ep.status.hosts.host}   (compare with LAKEBASE_HOST in your .env)")
print(f"Articles: {rows}")
print("Tables  :", ", ".join(t[0] for t in tables))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Search and query plans
# MAGIC Run this **before and after** applying your migrations to `search-dev` (exercise 5) and compare.

# COMMAND ----------

# Category filter: watch the plan switch from a Seq Scan to an index scan once V002 is applied.
# The table is small, so we discourage sequential scans to make the index choice visible.
with connect() as conn:
    conn.execute("SET enable_seqscan = off")
    plan = conn.execute(f"EXPLAIN SELECT article_id, title FROM {pg_articles} WHERE category = 'billing'").fetchall()
print("\n".join(r[0] for r in plan))

# COMMAND ----------

# Semantic search: embed the question with the same model used for the articles, then rank by cosine distance.
question = "I was charged twice this month"
question_embedding = spark.sql(
    "SELECT ai_query('databricks-gte-large-en', :q) AS e", args={"q": question}).first()["e"]
vector_literal = "[" + ",".join(str(x) for x in question_embedding) + "]"

with connect() as conn:
    conn.execute("SET enable_seqscan = off")
    plan = conn.execute(
        f"EXPLAIN SELECT article_id FROM {pg_articles} ORDER BY embedding <=> %s::vector LIMIT 5",
        (vector_literal,)).fetchall()
    results = conn.execute(
        f"""SELECT article_id, title, round((embedding <=> %s::vector)::numeric, 4)::float8 AS distance
            FROM {pg_articles} ORDER BY embedding <=> %s::vector LIMIT 5""",
        (vector_literal, vector_literal)).fetchall()
print("\n".join(r[0] for r in plan))
display(spark.createDataFrame(results, "article_id BIGINT, title STRING, distance DOUBLE"))

# COMMAND ----------

# After V001 is applied: record feedback for the top result in the application-owned table.
if query("SELECT to_regclass('public.search_feedback') IS NOT NULL")[0][0]:
    query("INSERT INTO public.search_feedback (article_id, query_text, helpful) VALUES (%s, %s, true)",
          (results[0][0], question))
    display(spark.createDataFrame(query(
        "SELECT feedback_id, article_id, query_text, helpful FROM public.search_feedback ORDER BY feedback_id DESC LIMIT 5"),
        "feedback_id BIGINT, article_id BIGINT, query_text STRING, helpful BOOLEAN"))
else:
    print(f"public.search_feedback does not exist on {selected_branch()} yet; apply your migrations first.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Scale up and down
# MAGIC Resize the **selected branch's** compute, inspect it, then put it back.
# MAGIC
# MAGIC - **Manual resizing:** set min = max to pin a fixed size.
# MAGIC - **Autoscaling:** set min < max; Lakebase moves between them with load.
# MAGIC - **Scale-to-zero:** a separate setting; compute suspends after the idle timeout and resumes on connect.

# COMMAND ----------

def show_compute(branch_id):
    s = endpoint_for(branch_id).status
    print(f"{branch_id}: min {s.autoscaling_limit_min_cu} CU, max {s.autoscaling_limit_max_cu} CU, "
          f"suspend after {s.suspend_timeout_duration}, state {s.current_state.value if s.current_state else '?'}")
    return s


def resize(branch_id, min_cu, max_cu):
    ep = endpoint_for(branch_id)
    w.postgres.update_endpoint(
        name=ep.name,
        endpoint=pg.Endpoint(name=ep.name, spec=pg.EndpointSpec(
            endpoint_type=ep.status.endpoint_type,
            autoscaling_limit_min_cu=min_cu, autoscaling_limit_max_cu=max_cu)),
        update_mask=FieldMask(field_mask=["spec.autoscaling_limit_min_cu", "spec.autoscaling_limit_max_cu"]),
    ).wait()
    return show_compute(branch_id)


branch_id = selected_branch()
assert branch_id != baseline_branch, "Select your development branch (search-dev) before resizing."
start = show_compute(branch_id)
starting_size = (start.autoscaling_limit_min_cu, start.autoscaling_limit_max_cu)

# COMMAND ----------

# Scale up: autoscale between 1 and 4 CU.
resize(branch_id, 1.0, 4.0)

# COMMAND ----------

# Scale back down to where you started.
resize(branch_id, *starting_size)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Confirm the baseline is unchanged
# MAGIC Run before deleting `search-dev` in VS Code (exercise 6). Your migrations only touched the dev branch.

# COMMAND ----------

def schema_objects(branch_id):
    return set(r[0] for r in query("""
        SELECT schemaname || '.' || tablename FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        UNION ALL
        SELECT schemaname || '.' || indexname FROM pg_indexes WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
    """, branch_id=branch_id))


baseline = schema_objects(baseline_branch)
dev = schema_objects(selected_branch())
print(f"Only on {selected_branch()}:", sorted(dev - baseline) or "nothing")
print(f"Baseline still has search_feedback? {'public.search_feedback' in baseline}")
print(f"Baseline article rows: {query(f'SELECT count(*) FROM {pg_articles}', branch_id=baseline_branch)[0][0]}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Optional: incremental ingestion
# MAGIC Add the second batch of articles to your Delta table, trigger the synced table, and watch the new rows
# MAGIC arrive in the baseline branch. Branches created earlier keep the data they were created with.

# COMMAND ----------

spark.sql(f"""
MERGE INTO {source_table} t
USING (SELECT * FROM {shared_table} WHERE batch = 2) s ON t.article_id = s.article_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
""")
pipeline_id = w.postgres.get_synced_table(name=f"synced_tables/{synced_table_id}").status.pipeline_id
w.pipelines.start_update(pipeline_id=pipeline_id)
time.sleep(30)
wait_for_sync()
print(f"Delta rows: {spark.table(source_table).count()} | "
      f"Lakebase rows on {baseline_branch}: {query(f'SELECT count(*) FROM {pg_articles}', branch_id=baseline_branch)[0][0]}")
