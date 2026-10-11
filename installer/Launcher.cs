// "yt-dlp Studio.exe": starts the app (Python server + its window) without a console.
using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Windows.Forms;

[assembly: AssemblyTitle("yt-dlp Studio")]
[assembly: AssemblyProduct("yt-dlp Studio")]
[assembly: AssemblyDescription("A friendly front end for yt-dlp (AI-generated)")]
[assembly: AssemblyVersion("2.1.1.0")]

static class Launcher
{
    [STAThread]
    static int Main()
    {
        string dir = AppDomain.CurrentDomain.BaseDirectory;
        string app = Path.Combine(dir, "app.py");
        if (!File.Exists(app))
        {
            MessageBox.Show("yt-dlp Studio's files are missing. Please run the installer again.", Studio.Name,
                            MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
        string version;
        string pythonw = Studio.FindPythonW(out version);
        if (pythonw == null)
        {
            DialogResult r = MessageBox.Show(
                "yt-dlp Studio needs Python 3.10 or newer, and it isn't installed.\n\nOpen python.org to download it?",
                Studio.Name, MessageBoxButtons.YesNo, MessageBoxIcon.Warning);
            if (r == DialogResult.Yes) Process.Start("https://www.python.org/downloads/windows/");
            return 2;
        }
        ProcessStartInfo psi = new ProcessStartInfo(pythonw, "\"" + app + "\"");
        psi.WorkingDirectory = dir;
        psi.UseShellExecute = false;
        psi.CreateNoWindow = true;
        Process.Start(psi);
        return 0;
    }
}
