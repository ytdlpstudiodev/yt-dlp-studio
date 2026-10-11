// Shared by the launcher, setup and uninstaller. Written for the C# 5 compiler that ships with Windows.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Management;
using System.Reflection;
using Microsoft.Win32;

static class Studio
{
    public const string Name = "yt-dlp Studio";
    public const string Version = "2.0.0";
    public const string LauncherExe = "yt-dlp Studio.exe";
    public const string UninstallExe = "Uninstall yt-dlp Studio.exe";
    public const string UninstallKey = @"Software\Microsoft\Windows\CurrentVersion\Uninstall\yt-dlp-studio";

    public static string DefaultInstallDir
    {
        get { return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", Name); }
    }

    public static string StartMenuShortcut
    {
        get { return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Programs), Name + ".lnk"); }
    }

    public static string DesktopShortcut
    {
        get { return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), Name + ".lnk"); }
    }

    /// <summary>Where an earlier install lives, or null.</summary>
    public static string InstalledDir()
    {
        using (RegistryKey k = Registry.CurrentUser.OpenSubKey(UninstallKey))
        {
            if (k == null) return null;
            string dir = k.GetValue("InstallLocation") as string;
            return string.IsNullOrEmpty(dir) ? null : dir;
        }
    }

    /// <summary>Create a Windows shortcut through the WScript.Shell COM object.</summary>
    public static void CreateShortcut(string lnkPath, string target, string workDir, string iconPath, string description)
    {
        Type shellType = Type.GetTypeFromProgID("WScript.Shell");
        object shell = Activator.CreateInstance(shellType);
        object lnk = shellType.InvokeMember("CreateShortcut", BindingFlags.InvokeMethod, null, shell, new object[] { lnkPath });
        Type t = lnk.GetType();
        t.InvokeMember("TargetPath", BindingFlags.SetProperty, null, lnk, new object[] { target });
        t.InvokeMember("WorkingDirectory", BindingFlags.SetProperty, null, lnk, new object[] { workDir });
        t.InvokeMember("IconLocation", BindingFlags.SetProperty, null, lnk, new object[] { iconPath + ",0" });
        t.InvokeMember("Description", BindingFlags.SetProperty, null, lnk, new object[] { description });
        t.InvokeMember("Save", BindingFlags.InvokeMethod, null, lnk, null);
    }

    /// <summary>Stop Studio (its Python server and its private Edge windows) running from this folder.</summary>
    public static int StopRunningCopies(string installDir)
    {
        string needle = installDir.TrimEnd('\\').ToLowerInvariant();
        int killed = 0;
        string query = "SELECT ProcessId, CommandLine FROM Win32_Process WHERE Name='python.exe' OR Name='pythonw.exe' OR Name='msedge.exe' OR Name='chrome.exe' OR Name='yt-dlp.exe' OR Name='ffmpeg.exe'";
        try
        {
            using (ManagementObjectSearcher s = new ManagementObjectSearcher(query))
            {
                foreach (ManagementObject p in s.Get())
                {
                    string cmd = (p["CommandLine"] as string ?? "").ToLowerInvariant();
                    if (cmd.IndexOf(needle, StringComparison.Ordinal) < 0) continue;
                    try
                    {
                        Process.GetProcessById(Convert.ToInt32(p["ProcessId"])).Kill();
                        killed++;
                    }
                    catch (Exception) { }
                }
            }
        }
        catch (Exception) { }
        if (killed > 0) System.Threading.Thread.Sleep(1500);
        return killed;
    }

    /// <summary>pythonw.exe for Python 3.10+, newest first; null if none is installed.</summary>
    public static string FindPythonW(out string version)
    {
        version = null;
        List<KeyValuePair<System.Version, string>> found = new List<KeyValuePair<System.Version, string>>();
        RegistryHive[] hives = { RegistryHive.CurrentUser, RegistryHive.LocalMachine };
        RegistryView[] views = { RegistryView.Registry64, RegistryView.Registry32 };
        foreach (RegistryHive hive in hives)
        {
            foreach (RegistryView view in views)
            {
                try
                {
                    using (RegistryKey root = RegistryKey.OpenBaseKey(hive, view))
                    using (RegistryKey core = root.OpenSubKey(@"Software\Python\PythonCore"))
                    {
                        if (core == null) continue;
                        foreach (string name in core.GetSubKeyNames())
                        {
                            System.Version v;
                            if (!System.Version.TryParse(name.Split('-')[0], out v) || v < new System.Version(3, 10)) continue;
                            using (RegistryKey ip = core.OpenSubKey(name + @"\InstallPath"))
                            {
                                if (ip == null) continue;
                                string w = ip.GetValue("WindowedExecutablePath") as string;
                                if (string.IsNullOrEmpty(w))
                                {
                                    string d = ip.GetValue("") as string;
                                    if (d != null) w = Path.Combine(d, "pythonw.exe");
                                }
                                if (w != null && File.Exists(w)) found.Add(new KeyValuePair<System.Version, string>(v, w));
                            }
                        }
                    }
                }
                catch (Exception) { }
            }
        }
        found.Sort(delegate (KeyValuePair<System.Version, string> a, KeyValuePair<System.Version, string> b) { return b.Key.CompareTo(a.Key); });
        if (found.Count > 0)
        {
            version = found[0].Key.ToString();
            return found[0].Value;
        }
        foreach (string dir in (Environment.GetEnvironmentVariable("PATH") ?? "").Split(';'))
        {
            if (dir.Length == 0 || dir.IndexOf("WindowsApps", StringComparison.OrdinalIgnoreCase) >= 0) continue;
            try
            {
                string p = Path.Combine(dir.Trim(), "pythonw.exe");
                if (File.Exists(p)) { version = "3"; return p; }
            }
            catch (Exception) { }
        }
        return null;
    }
}
