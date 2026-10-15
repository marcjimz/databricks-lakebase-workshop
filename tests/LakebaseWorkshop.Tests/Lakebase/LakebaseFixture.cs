using LakebaseWorkshop.Migrations;
using Npgsql;

namespace LakebaseWorkshop.Tests.Lakebase;

// Connects to whichever Lakebase branch .env currently points at (the extension rewrites
// .env when you switch branches in VS Code).
public sealed class LakebaseFixture : IDisposable
{
    public LakebaseSettings Settings { get; }
    public NpgsqlDataSource DataSource { get; }
    public string ArticlesTable => $"\"{Settings.WorkshopSchema}\".{WorkshopNaming.ArticlesTable}";

    public LakebaseFixture()
    {
        Settings = LakebaseSettings.Load();
        DataSource = NpgsqlDataSource.Create(Settings.ConnectionString(LakebaseCredential.Generate(Settings)));
    }

    public async Task<T?> ScalarAsync<T>(string sql, params object[] args)
    {
        await using var cmd = DataSource.CreateCommand(sql);
        foreach (var arg in args)
        {
            cmd.Parameters.Add(new NpgsqlParameter { Value = arg });
        }
        var result = await cmd.ExecuteScalarAsync();
        return result is null or DBNull ? default : (T)result;
    }

    public void Dispose() => DataSource.Dispose();
}

[CollectionDefinition("Lakebase")]
public class LakebaseCollection : ICollectionFixture<LakebaseFixture> { }
