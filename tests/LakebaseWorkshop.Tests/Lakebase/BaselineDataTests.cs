namespace LakebaseWorkshop.Tests.Lakebase;

// Passes on the baseline branch and on any branch created from it.
[Collection("Lakebase")]
[Trait("Category", "Lakebase")]
public class BaselineDataTests(LakebaseFixture db)
{
    [Fact]
    public async Task SyncedArticles_ArePresentOnThisBranch()
    {
        var rows = await db.ScalarAsync<long>($"SELECT count(*) FROM {db.ArticlesTable}");
        Assert.True(rows > 0, $"{db.ArticlesTable} is empty on branch {db.Settings.BranchId}");
    }

    [Fact]
    public async Task SyncedArticles_HaveVectorEmbeddings()
    {
        var type = await db.ScalarAsync<string>(
            """
            SELECT format_type(a.atttypid, a.atttypmod)
            FROM pg_attribute a
            JOIN pg_class c ON c.oid = a.attrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = $1 AND c.relname = $2 AND a.attname = 'embedding'
            """,
            db.Settings.WorkshopSchema, Migrations.WorkshopNaming.ArticlesTable);
        Assert.NotNull(type);
        Assert.StartsWith("vector", type);
    }
}
