# Prerequisites

Install these before the workshop.

| Tool | Version | Install (macOS) |
|---|---|---|
| VS Code | 1.85+ | <https://code.visualstudio.com> |
| Lakebase SCM extension | latest | Download the `.vsix` from the [latest release](https://github.com/databricks-solutions/lakebase-scm-extension/releases/latest), then *Extensions → … → Install from VSIX* |
| .NET SDK | 8.0+ | `brew install dotnet@8` |
| Databricks CLI | 0.285+ | `brew install databricks` |
| PostgreSQL client (`psql`) | any | `brew install libpq` (used by the extension's schema diff) |
| Git | 2.30+ | `brew install git` |

The C# Dev Kit VS Code extension is recommended (VS Code offers it when you open the repo).

## Sign in

```bash
databricks auth login --host https://<HOSTNAME>
```

## You will be given

- A **workspace URL** (`<HOSTNAME>`)
- A **catalog** (`<CATALOG>`); your own schema `lakebase_<your_name>` is created for you by the notebook
- A **Lakebase project** that is already created and assigned to you (`<LAKEBASE_PROJECT_ID>`)
