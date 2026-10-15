using System.Text.RegularExpressions;
using LakebaseWorkshop.Migrations;

namespace LakebaseWorkshop.Tests.Unit;

// Enforcement test: the Lakebase SCM extension lists migrations matching V{N}__{desc}.sql,
// and DbUp applies scripts in file-name order, so versions must be zero-padded to 3 digits.
public class MigrationScriptConventionTests
{
    private static readonly Regex Convention = new(@"^V\d{3}__[a-z0-9_]+\.sql$");

    public static IEnumerable<object[]> ScriptFolders() => new[]
    {
        new object[] { RepoPaths.MigrationsFolder },
        new object[] { RepoPaths.SolutionsMigrationsFolder },
    };

    [Theory]
    [MemberData(nameof(ScriptFolders))]
    public void EveryScript_FollowsNamingConvention(string folder)
    {
        foreach (var file in Directory.GetFiles(folder, "*.sql"))
        {
            Assert.Matches(Convention, Path.GetFileName(file));
        }
    }

    [Fact]
    public void SolutionScripts_HaveUniqueVersions()
    {
        var versions = Directory.GetFiles(RepoPaths.SolutionsMigrationsFolder, "*.sql")
            .Select(f => Path.GetFileName(f)[..4])
            .ToList();
        Assert.NotEmpty(versions);
        Assert.Equal(versions.Count, versions.Distinct().Count());
    }
}
