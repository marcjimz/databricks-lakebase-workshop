using LakebaseWorkshop.Migrations;

namespace LakebaseWorkshop.Tests.Unit;

// The notebook derives the same schema name in Python; keep both rules in sync.
public class WorkshopNamingTests
{
    [Theory]
    [InlineData("marcin.jimenez@databricks.com", "lakebase_marcin_jimenez")]
    [InlineData("Jane-Doe@example.com", "lakebase_jane_doe")]
    [InlineData("a.b+c@example.com", "lakebase_a_b_c")]
    public void SchemaFor_DerivesPerUserSchema(string user, string expected)
    {
        Assert.Equal(expected, WorkshopNaming.SchemaFor(user));
    }

    [Fact]
    public void SchemaFor_RejectsEmptyUser()
    {
        Assert.Throws<ArgumentException>(() => WorkshopNaming.SchemaFor(""));
    }
}
