namespace LakebaseWorkshop.Migrations;

// Minimal reader for the .env file maintained by the Lakebase SCM extension.
public static class EnvFile
{
    public static Dictionary<string, string> Parse(IEnumerable<string> lines)
    {
        var values = new Dictionary<string, string>();
        foreach (var raw in lines)
        {
            var line = raw.Trim();
            if (line.Length == 0 || line.StartsWith('#'))
            {
                continue;
            }
            var eq = line.IndexOf('=');
            if (eq <= 0)
            {
                continue;
            }
            var key = line[..eq].Trim();
            var value = line[(eq + 1)..].Trim().Trim('"', '\'');
            values[key] = value;
        }
        return values;
    }

    public static Dictionary<string, string> Load(string path) =>
        File.Exists(path) ? Parse(File.ReadAllLines(path)) : new Dictionary<string, string>();
}
