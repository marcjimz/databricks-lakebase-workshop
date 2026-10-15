# Databricks notebook source
# MAGIC %md
# MAGIC # Instructor: generate the shared training data
# MAGIC
# MAGIC Run **once per workspace** before the workshop. Creates `<catalog>.<shared_schema>.support_articles`:
# MAGIC synthetic support articles with precomputed embeddings. Attendees copy it into their own schema.
# MAGIC
# MAGIC - `batch = 1` rows are the initial load; `batch = 2` rows are used for the optional incremental-ingestion step.
# MAGIC - Safe to re-run: the table is rebuilt deterministically.
# MAGIC - Afterwards, grant attendees read access (last cell).

# COMMAND ----------

dbutils.widgets.text("catalog", "<CATALOG>")
dbutils.widgets.text("shared_schema", "lakebase_workshop_shared")
dbutils.widgets.text("embedding_endpoint", "databricks-gte-large-en")
dbutils.widgets.text("attendee_group", "account users")

catalog = dbutils.widgets.get("catalog")
shared_schema = dbutils.widgets.get("shared_schema")
embedding_endpoint = dbutils.widgets.get("embedding_endpoint")
attendee_group = dbutils.widgets.get("attendee_group")
assert not catalog.startswith("<"), "Set the catalog widget first."

shared_table = f"`{catalog}`.`{shared_schema}`.support_articles"
spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{shared_schema}`")

# COMMAND ----------

# MAGIC %md ## 1. Synthetic articles

# COMMAND ----------

import random
from datetime import datetime, timedelta

random.seed(42)

products = ["Mobile App", "Web Portal", "Billing", "Data Export", "Notifications", "Integrations"]
issues = {
    "account": ["reset a forgotten password", "enable two-factor authentication", "change the account email",
                "recover a locked account", "merge duplicate accounts"],
    "billing": ["update a payment method", "download an invoice", "dispute a duplicate charge",
                "change the billing cycle", "apply a promo code"],
    "performance": ["fix slow page loads", "resolve request timeouts", "reduce sync delays",
                    "speed up large exports", "troubleshoot high memory usage"],
    "connectivity": ["fix SSO login loops", "resolve webhook delivery failures", "configure a proxy",
                     "renew an expired API token", "allow-list IP addresses"],
    "data": ["restore deleted records", "export data to CSV", "schedule a recurring export",
             "fix missing fields after import", "correct timezone offsets"],
    "notifications": ["stop duplicate emails", "enable push notifications", "set quiet hours",
                      "fix delayed alerts", "route alerts to a team channel"],
}
steps = [
    "Sign in as an administrator.", "Open Settings and choose the relevant section.",
    "Confirm the change and wait for the success message.", "Clear the browser cache and retry.",
    "Check the audit log for the most recent event.", "Contact support with the request ID if the problem persists.",
]

rows, article_id = [], 1
start = datetime(2026, 1, 1)
for product in products:
    for category, topics in issues.items():
        for topic in topics:
            body = (f"This article explains how to {topic} in {product}. "
                    + " ".join(random.sample(steps, 3))
                    + f" Applies to all {product} plans.")
            rows.append((article_id, f"How to {topic} in {product}", category, product, body,
                         start + timedelta(days=article_id % 200), 2 if article_id % 9 == 0 else 1))
            article_id += 1

articles = spark.createDataFrame(
    rows, "article_id BIGINT, title STRING, category STRING, product STRING, body STRING, updated_at TIMESTAMP, batch INT")
articles.createOrReplaceTempView("synthetic_articles")
print(f"{len(rows)} articles ({sum(r[-1] == 2 for r in rows)} in batch 2)")

# COMMAND ----------

# MAGIC %md ## 2. Precompute embeddings and write the shared table

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE TABLE {shared_table} (
  article_id BIGINT NOT NULL, title STRING, category STRING, product STRING, body STRING,
  updated_at TIMESTAMP, batch INT, embedding ARRAY<FLOAT>
)
COMMENT 'Synthetic support articles with precomputed embeddings for the Lakebase workshop'
""")
spark.sql(f"""
INSERT INTO {shared_table}
SELECT *, ai_query('{embedding_endpoint}', concat(title, '. ', body)) AS embedding
FROM synthetic_articles
""")
display(spark.sql(f"SELECT batch, count(*) AS articles, max(size(embedding)) AS embedding_dim FROM {shared_table} GROUP BY batch"))

# COMMAND ----------

# MAGIC %md ## 3. Grant attendees read access

# COMMAND ----------

# Leave attendee_group blank to skip (for example when testing in a shared dev catalog).
if attendee_group:
    spark.sql(f"GRANT USE CATALOG ON CATALOG `{catalog}` TO `{attendee_group}`")
    spark.sql(f"GRANT USE SCHEMA, SELECT ON SCHEMA `{catalog}`.`{shared_schema}` TO `{attendee_group}`")
    # Attendees create their own schema (lakebase_<user>) in this catalog.
    spark.sql(f"GRANT CREATE SCHEMA ON CATALOG `{catalog}` TO `{attendee_group}`")
