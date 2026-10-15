# Exercises

**VS Code** = your cloned repo with the Lakebase SCM extension. **Notebook** = `notebooks/lakebase_search_workshop`
in your workspace Git folder. Fill in the notebook widgets once: `catalog`, `lakebase_project`.

---

## 1. Link your Lakebase project to the repo (10 min)

**VS Code**

1. Open your cloned repo folder.
2. Copy `.env.example` to `.env` and set `DATABRICKS_HOST` and `LAKEBASE_PROJECT_ID` to the values you were given.
3. `Cmd/Ctrl+Shift+P` → **Lakebase: Set Up Existing Project**. Sign in to your workspace when asked.
   The extension adopts your existing project (it keeps the project id from `.env`).
4. Click the **Lakebase** icon in the activity bar. You should see your project and its `production` branch.

## Prepare synthetic data and create a synced table (15 min)

**Notebook** — run sections **0, 1 and 2**.

- Section 1 copies the shared support articles and embeddings into **your** schema, `lakebase_<your_name>`.
- Section 2 syncs that table into your project's `production` (baseline) branch and checks the row counts match.

Safe to re-run at any time.

## 2. Create a Git branch and its paired Lakebase branch (10 min)

**VS Code**

1. In the Lakebase view, click the branch icon on your project → **Create New Branch…** → `search-dev`.
2. The extension creates the Git branch **and** a Lakebase branch with the same name, then updates `.env`.
3. Expand `search-dev` in the Lakebase view: the synced articles table is there, copied from `production`.

**Notebook** — set the **branch** widget to `search-dev` and run section **3**. The article count matches production.

## 3. Switch branches and reconnect (5 min)

**VS Code**

1. Switch to `main`, then back to `search-dev` (status bar branch picker, or the Lakebase view).
2. Open `.env` after each switch: `LAKEBASE_BRANCH_ID` and `LAKEBASE_HOST` change.

**Notebook** — change the **branch** widget and re-run section **3**. The host matches `LAKEBASE_HOST` in `.env`.

## 4. Branch status and schema comparison (5 min)

**VS Code** — on `search-dev`, expand the database node in the Lakebase view (or run **Lakebase: Show Branch Diff**).
No markers yet: `search-dev` is identical to `production`. Come back to this after exercise 5.

## 5. Migrations and tests on `search-dev` (25 min)

**VS Code** (on `search-dev`)

1. Run **Terminal → Run Task → Lakebase: Test**. Three tests fail. That is the goal you are working toward.
2. Ask your AI assistant to write migrations in `src/LakebaseWorkshop.Migrations/Migrations/` that:
   - `V001__create_search_feedback.sql`: create `public.search_feedback` (`article_id`, `query_text`, `helpful`, `created_at`)
   - `V002__index_articles_category.sql`: add an index on `category` of `"$schema$".support_articles_synced`
   - `V003__vector_index_articles.sql`: add an HNSW index on `embedding` (`vector_cosine_ops`)

   Review the SQL before running it. `$schema$` is replaced with your schema. Stuck? Copy from `solutions/migrations/`.
3. Run **Lakebase: Migrate**, then **Lakebase: Test**. All tests pass.
4. Revisit the branch diff (exercise 4): `public.search_feedback` and `public.schema_versions` show as new (`+`),
   and the articles table shows its new indexes.

**Notebook** — with branch = `search-dev`, run section **4**:

- The category query plan changes from `Seq Scan` to `Bitmap Heap Scan` (index).
- The vector search plan uses the HNSW index and returns the closest articles to *"I was charged twice this month"*.
- Your feedback is saved in `search_feedback`.

Set the branch widget to `production` and run section 4 again: no indexes, and no `search_feedback` table.

Commit your migrations in VS Code.

## Scale up and scale down (15 min)

**Notebook** — branch = `search-dev`, run section **5**: show the current size → scale up to 1–4 CU → return to
the starting size.

- **Manual resizing:** min = max pins a fixed size.
- **Autoscaling:** min < max; compute moves within the range as load changes.
- **Scale-to-zero:** separate idle-timeout setting; compute suspends and resumes on the next connection.

## 6. Delete the Lakebase branch (5 min)

1. **Notebook** — run section **6**: the baseline is unchanged; only `search-dev` has your changes.
2. **VS Code** — keep your reviewed migrations committed (push them if you want to keep them), switch to `main`,
   then right-click `search-dev` in the Lakebase view → **Delete Branch** (database only) or
   **Delete Branch Everywhere** (database, local and remote Git branches).

## Optional: incremental ingestion

**Notebook** — run section **7**. A second batch of articles is merged into your Delta table and the synced table
picks it up in `production`. Branches you created earlier keep the data they started with.
