# Instructor setup

## Before the session

1. **Workspace and catalog.** Pick the workspace (`<HOSTNAME>`) and a Unity Catalog catalog (`<CATALOG>`).
2. **Configure the bundle.** In `databricks.yml`, fill in the `lakebase_workshop` target's `<HOSTNAME>`, `<CATALOG>`
   and (for your own dry run) `<LAKEBASE_PROJECT_ID>`.
3. **Generate the shared data** (once per workspace):

   ```bash
   databricks bundle deploy -t lakebase_workshop
   databricks bundle run -t lakebase_workshop generate_shared_data
   ```

   Creates `<CATALOG>.lakebase_workshop_shared.support_articles` (180 synthetic articles, 1024-dim
   `databricks-gte-large-en` embeddings; 160 in batch 1, 20 in batch 2). To grant attendees access, run the
   notebook `docs/instructor/generate_shared_data` with `attendee_group` set (default job run skips grants).
   Attendees need `USE CATALOG`, `CREATE SCHEMA` on the catalog and `SELECT` on the shared schema.
4. **Lakebase projects.** Create one Lakebase project per attendee and make the attendee its owner.
   Send each attendee their `<LAKEBASE_PROJECT_ID>`.
5. **Template repo.** Mark the GitHub repo as a template. Attendees don't need GitHub Actions for this workshop;
   if the extension adds `.github/workflows/`, those runs can be ignored or Actions disabled on their copy.

## Dry run checklist

Run the exercises end to end with one attendee account before the session. These steps involve the extension UI:

- [ ] **Lakebase: Set Up Existing Project** adopts the project in this C# repo and doesn't overwrite
      `.vscode/settings.json` (`lakebaseSync.migrationPath`) or other repo files. If it asks for a language,
      note which choice adds the fewest files and put it in exercise 1.
- [ ] Creating `search-dev` in the extension writes `LAKEBASE_BRANCH_ID`, `LAKEBASE_HOST`, `DB_USERNAME` to `.env`.
- [ ] The branch diff shows `public.search_feedback` as new after exercise 5.

## After the session

Per attendee (or let projects expire): delete the `search-dev` branches, the synced table
`<CATALOG>.lakebase_<user>.support_articles_synced`, and the schema `<CATALOG>.lakebase_<user>`.
