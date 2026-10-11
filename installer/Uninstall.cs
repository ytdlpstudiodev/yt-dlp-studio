// "Uninstall yt-dlp Studio.exe": removes every trace of the app. Downloaded videos are never touched.
//
// Running files can't delete their own folder, so the uninstaller copies itself to %TEMP%,
// relaunches from there, cleans up, and finally deletes that temporary copy too.
using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Threading;
using System.Web.Script.Serialization;
using System.Windows.Forms;
using Microsoft.Win32;

[assembly: AssemblyTitle("Uninstall yt-dlp Studio")]
[assembly: AssemblyProduct("yt-dlp Studio")]
[assembly: AssemblyVersion("2.1.0.0")]

static class Uninstaller
{
    [STAThread]
    static int Main(string[] args)
    {
        bool quiet = Array.IndexOf(args, "/quiet") >= 0;
        int runAt = Array.IndexOf(args, "/run");
        string self = Assembly.GetExecutingAssembly().Location;

        if (runAt < 0)
        {
            string dir = Path.GetDirectoryName(self);
            if (!quiet)
            {
                DialogResult r = MessageBox.Show(
                    "Remove yt-dlp Studio from this computer?\n\n" +
                    "This deletes the app, its settings, saved logins and browser profiles, shortcuts and leftover temporary download files.\n\n" +
                    "Videos and music you downloaded are NOT deleted.",
                    "Uninstall yt-dlp Studio", MessageBoxButtons.YesNo, MessageBoxIcon.Question, MessageBoxDefaultButton.Button2);
                if (r != DialogResult.Yes) return 1;
            }
            string temp = Path.Combine(Path.GetTempPath(), "yt-dlp-studio-uninstall-" + Guid.NewGuid().ToString("N").Substring(0, 8) + ".exe");
            File.Copy(self, temp, true);
            string a = "/run \"" + dir + "\"" + (quiet ? " /quiet" : "");
            Process.Start(new ProcessStartInfo(temp, a) { UseShellExecute = false, WorkingDirectory = Path.GetTempPath() });
            return 0;
        }

        string installDir = runAt + 1 < args.Length ? args[runAt + 1] : Studio.InstalledDir();
        List<string> problems = new List<string>();
        if (!string.IsNullOrEmpty(installDir) && Directory.Exists(installDir) && LooksLikeStudio(installDir))
        {
            Studio.StopRunningCopies(installDir);
            CleanStagingFolders(installDir, problems);
            DeleteTree(installDir, problems);
        }
        TryDelete(Studio.StartMenuShortcut, problems);
        TryDelete(Studio.DesktopShortcut, problems);
        try { Registry.CurrentUser.DeleteSubKeyTree(Studio.UninstallKey, false); }
        catch (Exception ex) { problems.Add("registry entry: " + ex.Message); }

        if (!quiet)
        {
            if (problems.Count == 0)
                MessageBox.Show("yt-dlp Studio was removed from your computer.", "Uninstall yt-dlp Studio", MessageBoxButtons.OK, MessageBoxIcon.Information);
            else
                MessageBox.Show("yt-dlp Studio was removed, but a few items couldn't be deleted (they may be in use):\n\n" +
                                string.Join("\n", problems.ToArray()), "Uninstall yt-dlp Studio", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
        // Delete this temporary copy once it has exited.
        Process.Start(new ProcessStartInfo("cmd.exe", "/c ping 127.0.0.1 -n 3 >nul & del /f /q \"" + self + "\"")
        {
            CreateNoWindow = true, UseShellExecute = false, WindowStyle = ProcessWindowStyle.Hidden
        });
        return 0;
    }

    /// <summary>Safety check so a bad path can never wipe an unrelated folder.</summary>
    static bool LooksLikeStudio(string dir)
    {
        return File.Exists(Path.Combine(dir, "app.py")) && File.Exists(Path.Combine(dir, "ytdlp_core.py"))
               || File.Exists(Path.Combine(dir, Studio.LauncherExe));
    }

    /// <summary>Remove ".yt-dlp-studio-tmp" (unfinished downloads) from every folder Studio saved into.</summary>
    static void CleanStagingFolders(string installDir, List<string> problems)
    {
        string settings = Path.Combine(installDir, "data", "settings.json");
        if (!File.Exists(settings)) return;
        HashSet<string> folders = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        try
        {
            Dictionary<string, object> s = new JavaScriptSerializer().Deserialize<Dictionary<string, object>>(File.ReadAllText(settings));
            object o;
            if (s.TryGetValue("options", out o) && o is Dictionary<string, object>)
            {
                object f;
                if (((Dictionary<string, object>)o).TryGetValue("folder", out f) && f is string) folders.Add((string)f);
            }
            if (s.TryGetValue("recent_folders", out o) && o is IEnumerable)
                foreach (object f in (IEnumerable)o) if (f is string) folders.Add((string)f);
        }
        catch (Exception) { return; }
        foreach (string f in folders)
        {
            try
            {
                string staging = Path.Combine(f, ".yt-dlp-studio-tmp");
                if (Directory.Exists(staging)) DeleteTree(staging, problems);
            }
            catch (Exception) { }
        }
    }

    static void DeleteTree(string dir, List<string> problems)
    {
        for (int attempt = 0; attempt < 6; attempt++)
        {
            try
            {
                foreach (string f in Directory.GetFiles(dir, "*", SearchOption.AllDirectories))
                    File.SetAttributes(f, FileAttributes.Normal);
                Directory.Delete(dir, true);
                return;
            }
            catch (DirectoryNotFoundException) { return; }
            catch (Exception ex)
            {
                if (attempt == 5) problems.Add(dir + " (" + ex.Message + ")");
                else Thread.Sleep(800);
            }
        }
    }

    static void TryDelete(string file, List<string> problems)
    {
        try { if (File.Exists(file)) File.Delete(file); }
        catch (Exception ex) { problems.Add(file + " (" + ex.Message + ")"); }
    }
}
