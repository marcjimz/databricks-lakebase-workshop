namespace LakebaseWorkshop.Migrations;

public static class RepoPaths
{
    public static string Root { get; } = FindRoot();

    public static string EnvFile => Path.Combine(Root, ".env");
    public static string MigrationsFolder => Path.Combine(Root, "src", "LakebaseWorkshop.Migrations", "Migrations");
    public static string SolutionsMigrationsFolder => Path.Combine(Root, "solutions", "migrations");

    // Walks up from the working directory (or the build output) to the folder holding the .sln.
    private static string FindRoot()
    {
        foreach (var start in new[] { Directory.GetCurrentDirectory(), AppContext.BaseDirectory })
        {
            for (var dir = new DirectoryInfo(start); dir is not null; dir = dir.Parent)
            {
                if (File.Exists(Path.Combine(dir.FullName, "LakebaseWorkshop.sln")))
                {
                    return dir.FullName;
                }
            }
        }
        throw new DirectoryNotFoundException("Could not find LakebaseWorkshop.sln; run from inside the repository.");
    }
}
