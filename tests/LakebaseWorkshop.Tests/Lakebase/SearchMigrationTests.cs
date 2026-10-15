namespace LakebaseWorkshop.Tests.Lakebase;

// Exercise 5: these fail until the search migrations are applied to the selected branch.
[Collection("Lakebase")]
[Trait("Category", "Lakebase")]
public class SearchMigrationTests(LakebaseFixture db)
{
    private Task<bool> IndexExistsAsync(string schema, string table, string usingClause) =>
        db.ScalarAsync<bool>(
            """
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = $1 AND tablename = $2 AND indexdef ILIKE $3)
            """,
            schema, table, $"%{usingClause}%");

    [Fact]
    public async Task SearchFeedback_AcceptsFeedbackForAnArticle()
    {
        await using var conn = await db.DataSource.OpenConnectionAsync();
        await using var tx = await conn.BeginTransactionAsync();
        await using var cmd = conn.CreateCommand();
        cmd.Transaction = tx;
        cmd.CommandText =
            $"""
            INSERT INTO public.search_feedback (article_id, query_text, helpful)
            SELECT article_id, 'reset my password', true FROM {db.ArticlesTable} LIMIT 1
            RETURNING feedback_id
            """;

        var id = await cmd.ExecuteScalarAsync();

        Assert.NotNull(id);
        await tx.RollbackAsync();
    }

    [Fact]
    public async Task Articles_HaveSecondaryIndexOnCategory()
    {
        Assert.True(await IndexExistsAsync(
            db.Settings.WorkshopSchema, Migrations.WorkshopNaming.ArticlesTable, "(category)"));
    }

    [Fact]
    public async Task Articles_HaveHnswVectorIndex()
    {
        Assert.True(await IndexExistsAsync(
            db.Settings.WorkshopSchema, Migrations.WorkshopNaming.ArticlesTable, "USING hnsw"));
    }

    [Fact]
    public async Task VectorSearch_ReturnsTheQueryArticleFirst()
    {
        var anchor = await db.ScalarAsync<long>($"SELECT min(article_id) FROM {db.ArticlesTable}");

        var nearest = await db.ScalarAsync<long>(
            $"""
            SELECT article_id FROM {db.ArticlesTable}
            ORDER BY embedding <=> (SELECT embedding FROM {db.ArticlesTable} WHERE article_id = $1)
            LIMIT 1
            """,
            anchor);

        Assert.Equal(anchor, nearest);
    }
}
