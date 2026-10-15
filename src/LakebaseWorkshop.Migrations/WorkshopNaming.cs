using System.Text.RegularExpressions;

namespace LakebaseWorkshop.Migrations;

// Naming shared with notebooks/lakebase_search_workshop.py; keep both rules in sync.
public static class WorkshopNaming
{
    public const string ArticlesTable = "support_articles_synced";

    // marcin.jimenez@databricks.com -> lakebase_marcin_jimenez
    public static string SchemaFor(string user)
    {
        if (string.IsNullOrWhiteSpace(user))
        {
            throw new ArgumentException("A user name is required to derive the workshop schema.", nameof(user));
        }
        var local = user.Split('@')[0].ToLowerInvariant();
        return "lakebase_" + Regex.Replace(local, "[^a-z0-9]+", "_").Trim('_');
    }
}
