using System.Diagnostics;
using System.Text.Json;

namespace LakebaseWorkshop.Migrations;

// Mints a short-lived Lakebase OAuth token with the Databricks CLI, the same way the extension does.
// Honors DATABRICKS_CONFIG_PROFILE for profile selection.
public static class LakebaseCredential
{
    public static string Generate(LakebaseSettings settings)
    {
        var psi = new ProcessStartInfo("databricks")
        {
            RedirectStandardOutput = true,
            RedirectStandardError = true,
        };
        foreach (var arg in new[] { "postgres", "generate-database-credential", settings.EndpointName, "-o", "json" })
        {
            psi.ArgumentList.Add(arg);
        }

        using var process = Process.Start(psi)
            ?? throw new InvalidOperationException("Could not start the Databricks CLI. Is `databricks` on your PATH?");
        var stdout = process.StandardOutput.ReadToEnd();
        var stderr = process.StandardError.ReadToEnd();
        process.WaitForExit();

        if (process.ExitCode != 0)
        {
            throw new InvalidOperationException(
                $"databricks postgres generate-database-credential failed for {settings.EndpointName}: {stderr.Trim()}");
        }
        using var json = JsonDocument.Parse(stdout);
        return json.RootElement.GetProperty("token").GetString()
            ?? throw new InvalidOperationException("The credential response did not include a token.");
    }
}
