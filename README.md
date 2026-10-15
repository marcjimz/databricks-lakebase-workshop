# AI-DLC with Lakebase Search

A 90-minute hands-on workshop: build an AI-assisted database change on an isolated **Lakebase branch**,
validate it with migrations and tests, inspect the differences, and clean up. VS Code (with the
**Lakebase SCM extension**) manages branches; one Databricks notebook handles data, search and compute sizing.

## Get started

1. **Make your own copy** of this repository (GitHub → *Use this template*, or fork), then clone it.
2. **Check the prerequisites:** [docs/prerequisites.md](docs/prerequisites.md).
3. **Add the repo to your workspace** as a Git folder (*Workspace → Create → Git folder*) and open
   `notebooks/lakebase_search_workshop`.
4. **Follow the exercises:** [docs/exercises.md](docs/exercises.md).

## What's in the repo

| Path | What it is |
|---|---|
| `notebooks/lakebase_search_workshop.py` | The one workshop notebook (run in your Databricks workspace) |
| `src/LakebaseWorkshop.Migrations/` | C# migration runner ([DbUp](https://dbup.readthedocs.io)); your `V###__*.sql` files go in `Migrations/` |
| `tests/LakebaseWorkshop.Tests/` | xUnit tests that run against the Lakebase branch you have selected |
| `solutions/migrations/` | Reference migrations if you get stuck |
| `databricks.yml`, `resources/` | Databricks Asset Bundle: deploys the notebook and jobs |
| `docs/` | Prerequisites, exercises, and instructor setup |

## Everyday commands (VS Code → *Terminal → Run Task*)

| Task | Command |
|---|---|
| **Lakebase: Migrate** | `dotnet run --project src/LakebaseWorkshop.Migrations` |
| **Lakebase: Test** | `dotnet test` |

Both use the branch the Lakebase SCM extension wrote to `.env`.

Instructors: see [docs/instructor/setup.md](docs/instructor/setup.md).
