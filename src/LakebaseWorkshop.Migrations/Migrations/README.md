# Migrations

Add one SQL file per change, named `V###__short_description.sql` (for example `V001__create_search_feedback.sql`).

- Files run in name order, once per Lakebase branch. History is kept in `public.schema_versions`.
- Use `$schema$` to refer to your synced-table schema (for example `"$schema$".support_articles_synced`).
- Run them with **Terminal → Run Task → Lakebase: Migrate**, or `dotnet run --project src/LakebaseWorkshop.Migrations`.

Stuck? Reference versions live in `solutions/migrations/`.
