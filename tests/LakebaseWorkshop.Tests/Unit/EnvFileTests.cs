using LakebaseWorkshop.Migrations;

namespace LakebaseWorkshop.Tests.Unit;

public class EnvFileTests
{
    [Fact]
    public void Parse_ReadsKeysAndIgnoresCommentsAndBlanks()
    {
        var values = EnvFile.Parse(new[]
        {
            "# comment",
            "",
            "LAKEBASE_PROJECT_ID=my-project",
            "LAKEBASE_HOST = ep-123.database.cloud.databricks.com ",
            "DB_USERNAME=\"user@example.com\"",
            "# LAKEBASE_ENDPOINT=primary",
        });

        Assert.Equal("my-project", values["LAKEBASE_PROJECT_ID"]);
        Assert.Equal("ep-123.database.cloud.databricks.com", values["LAKEBASE_HOST"]);
        Assert.Equal("user@example.com", values["DB_USERNAME"]);
        Assert.False(values.ContainsKey("LAKEBASE_ENDPOINT"));
    }
}
