using DbUp;
using LakebaseWorkshop.Migrations;

// Applies the V###__*.sql scripts in ./Migrations to the Lakebase branch selected in .env.
// Scripts can use $schema$ for the attendee's synced-table schema.
var settings = LakebaseSettings.Load();
Console.WriteLine($"Lakebase branch : {settings.BranchId} ({settings.EndpointName})");
Console.WriteLine($"Workshop schema : {settings.WorkshopSchema}");

var upgrader = DeployChanges.To
    .PostgresqlDatabase(settings.ConnectionString(LakebaseCredential.Generate(settings)))
    .WithScriptsFromFileSystem(RepoPaths.MigrationsFolder)
    .WithVariable("schema", settings.WorkshopSchema)
    .JournalToPostgresqlTable("public", "schema_versions")
    .WithTransactionPerScript()
    .LogToConsole()
    .Build();

var pending = upgrader.GetScriptsToExecute();
Console.WriteLine(pending.Count == 0
    ? "No pending migrations."
    : $"Pending: {string.Join(", ", pending.Select(s => s.Name))}");

var result = upgrader.PerformUpgrade();
if (!result.Successful)
{
    Console.Error.WriteLine(result.Error);
    return 1;
}
Console.WriteLine("Migrations applied.");
return 0;
