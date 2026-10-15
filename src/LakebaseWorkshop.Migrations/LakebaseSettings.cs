using Npgsql;

namespace LakebaseWorkshop.Migrations;

// Connection metadata for the current Lakebase branch. The Lakebase SCM extension writes these
// keys to .env and rewrites them when you switch branches; environment variables override .env.
public sealed record LakebaseSettings(
    string ProjectId,
    string BranchId,
    string EndpointId,
    string Host,
    string Username,
    string Database,
    string WorkshopSchema)
{
    public string EndpointName => $"projects/{ProjectId}/branches/{BranchId}/endpoints/{EndpointId}";

    public static LakebaseSettings Load()
    {
        var file = EnvFile.Load(RepoPaths.EnvFile);

        string? Get(string key) =>
            Environment.GetEnvironmentVariable(key) is { Length: > 0 } v ? v
            : file.TryGetValue(key, out var f) && f.Length > 0 ? f
            : null;

        string Require(string key) =>
            Get(key) ?? throw new InvalidOperationException(
                $"{key} is not set. Open the repo in VS Code with the Lakebase SCM extension and switch to a branch " +
                "so it writes .env, or copy .env.example to .env.");

        var username = Require("DB_USERNAME");
        return new LakebaseSettings(
            ProjectId: Require("LAKEBASE_PROJECT_ID"),
            BranchId: Require("LAKEBASE_BRANCH_ID"),
            EndpointId: Get("LAKEBASE_ENDPOINT") ?? "primary",
            Host: Require("LAKEBASE_HOST"),
            Username: username,
            Database: Get("LAKEBASE_DATABASE") ?? "databricks_postgres",
            WorkshopSchema: Get("WORKSHOP_SCHEMA") ?? WorkshopNaming.SchemaFor(username));
    }

    public string ConnectionString(string password) => new NpgsqlConnectionStringBuilder
    {
        Host = Host,
        Port = 5432,
        Database = Database,
        Username = Username,
        Password = password,
        SslMode = SslMode.Require,
    }.ConnectionString;
}
