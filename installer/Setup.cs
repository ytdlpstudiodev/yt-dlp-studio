// "yt-dlp Studio Setup.exe": installs for the current user (no admin needed).
using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Threading;
using System.Windows.Forms;
using Microsoft.Win32;

[assembly: AssemblyTitle("yt-dlp Studio Setup")]
[assembly: AssemblyProduct("yt-dlp Studio")]
[assembly: AssemblyDescription("Installs yt-dlp Studio (AI-generated app)")]
[assembly: AssemblyVersion("2.1.1.0")]

class SetupForm : Form
{
    static readonly Color Green = Color.FromArgb(0x32, 0xB4, 0x5C);
    static readonly Color Dark = Color.FromArgb(0x24, 0x20, 0x20);

    TextBox dirBox;
    CheckBox desktopBox, launchBox;
    Button installBtn, cancelBtn, browseBtn;
    ProgressBar bar;
    Label status, intro, pyLabel;
    Panel body;
    bool done;

    SetupForm()
    {
        Text = Studio.Name + " Setup";
        Font = new Font("Segoe UI", 9.75f);
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        StartPosition = FormStartPosition.CenterScreen;
        ClientSize = new Size(560, 420);
        BackColor = Color.White;
        Stream ico = Assembly.GetExecutingAssembly().GetManifestResourceStream("icon.ico");
        Icon appIcon = ico != null ? new Icon(ico) : null;
        if (appIcon != null) Icon = appIcon;

        Panel header = new Panel { Dock = DockStyle.Top, Height = 92, BackColor = Dark };
        PictureBox pic = new PictureBox { Location = new Point(24, 18), Size = new Size(56, 56), SizeMode = PictureBoxSizeMode.Zoom };
        if (appIcon != null) pic.Image = new Icon(appIcon, 64, 64).ToBitmap();
        Label title = new Label { Text = Studio.Name, ForeColor = Color.White, Font = new Font("Segoe UI Semibold", 17f), AutoSize = true, Location = new Point(94, 18) };
        Label sub = new Label { Text = "Setup  ·  version " + Studio.Version, ForeColor = Color.FromArgb(190, 190, 190), AutoSize = true, Location = new Point(97, 56) };
        header.Controls.AddRange(new Control[] { pic, title, sub });

        body = new Panel { Location = new Point(0, 92), Size = new Size(560, 268) };
        intro = new Label
        {
            Text = "This installs yt-dlp Studio, a friendly app for downloading videos and audio with yt-dlp, for your Windows account. No administrator rights are needed.",
            Location = new Point(28, 20), Size = new Size(504, 44)
        };
        Label dirLabel = new Label { Text = "Install location", Location = new Point(28, 74), AutoSize = true, Font = new Font("Segoe UI Semibold", 9.75f) };
        string existing = Studio.InstalledDir();
        dirBox = new TextBox { Text = existing ?? Studio.DefaultInstallDir, Location = new Point(28, 98), Size = new Size(410, 26) };
        browseBtn = new Button { Text = "Browse…", Location = new Point(446, 96), Size = new Size(86, 30), FlatStyle = FlatStyle.System };
        browseBtn.Click += delegate { Browse(); };
        desktopBox = new CheckBox { Text = "Create a desktop shortcut", Checked = true, Location = new Point(28, 140), AutoSize = true };
        launchBox = new CheckBox { Text = "Start yt-dlp Studio when setup finishes", Checked = true, Location = new Point(28, 168), AutoSize = true };
        pyLabel = new Label { Location = new Point(28, 202), Size = new Size(504, 22) };
        bar = new ProgressBar { Location = new Point(28, 230), Size = new Size(504, 14), Visible = false };
        status = new Label { Location = new Point(28, 248), Size = new Size(504, 20), ForeColor = Color.DimGray };
        body.Controls.AddRange(new Control[] { intro, dirLabel, dirBox, browseBtn, desktopBox, launchBox, pyLabel, bar, status });

        Panel footer = new Panel { Dock = DockStyle.Bottom, Height = 60, BackColor = Color.FromArgb(245, 245, 245) };
        Label ai = new Label { Text = "AI-generated app", ForeColor = Color.Gray, AutoSize = true, Location = new Point(24, 22) };
        cancelBtn = new Button { Text = "Cancel", Size = new Size(96, 34), Location = new Point(336, 13), FlatStyle = FlatStyle.System };
        installBtn = new Button
        {
            Text = existing != null ? "Reinstall" : "Install", Size = new Size(104, 34), Location = new Point(440, 13),
            FlatStyle = FlatStyle.Flat, BackColor = Green, ForeColor = Color.White, Font = new Font("Segoe UI Semibold", 9.75f)
        };
        installBtn.FlatAppearance.BorderSize = 0;
        cancelBtn.Click += delegate { Close(); };
        installBtn.Click += delegate { if (done) Finish(); else StartInstall(); };
        footer.Controls.AddRange(new Control[] { ai, cancelBtn, installBtn });
        AcceptButton = installBtn;
        CancelButton = cancelBtn;

        Controls.Add(body);
        Controls.Add(footer);
        Controls.Add(header);
        CheckPython();
    }

    void CheckPython()
    {
        string version;
        string py = Studio.FindPythonW(out version);
        if (py != null)
        {
            pyLabel.Text = "✓  Python " + version + " found. Studio will use it.";
            pyLabel.ForeColor = Color.FromArgb(0x1E, 0x8E, 0x45);
        }
        else
        {
            pyLabel.Text = "⚠  Python 3.10 or newer is needed to run Studio. You can install it from python.org afterwards.";
            pyLabel.ForeColor = Color.FromArgb(0xB3, 0x6B, 0x00);
        }
    }

    void Browse()
    {
        using (FolderBrowserDialog d = new FolderBrowserDialog())
        {
            d.Description = "Choose where to install yt-dlp Studio. A \"yt-dlp Studio\" folder will be created inside it.";
            if (d.ShowDialog(this) == DialogResult.OK)
                dirBox.Text = d.SelectedPath.TrimEnd('\\').EndsWith(Studio.Name) ? d.SelectedPath : Path.Combine(d.SelectedPath, Studio.Name);
        }
    }

    void StartInstall()
    {
        string dir = dirBox.Text.Trim();
        if (dir.Length == 0 || !Path.IsPathRooted(dir))
        {
            MessageBox.Show(this, "Please choose a full folder path.", Text, MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }
        bool desktop = desktopBox.Checked;
        foreach (Control c in new Control[] { dirBox, browseBtn, desktopBox, launchBox, installBtn, cancelBtn }) c.Enabled = false;
        bar.Visible = true;
        Thread t = new Thread(delegate ()
        {
            try
            {
                Install(dir, desktop);
                BeginInvoke((MethodInvoker)delegate { Done(dir); });
            }
            catch (Exception ex)
            {
                BeginInvoke((MethodInvoker)delegate
                {
                    MessageBox.Show(this, "Setup couldn't finish:\n\n" + ex.Message, Text, MessageBoxButtons.OK, MessageBoxIcon.Error);
                    foreach (Control c in new Control[] { dirBox, browseBtn, desktopBox, launchBox, installBtn, cancelBtn }) c.Enabled = true;
                    bar.Visible = false;
                    status.Text = "";
                });
            }
        });
        t.IsBackground = true;
        t.Start();
    }

    void Report(string text, int pct)
    {
        if (!IsHandleCreated) return;   // silent install
        BeginInvoke((MethodInvoker)delegate { status.Text = text; bar.Value = Math.Max(0, Math.Min(100, pct)); });
    }

    void Install(string dir, bool desktop)
    {
        Report("Closing yt-dlp Studio if it's running…", 2);
        Studio.StopRunningCopies(dir);

        Directory.CreateDirectory(dir);
        using (Stream s = Assembly.GetExecutingAssembly().GetManifestResourceStream("payload.zip"))
        using (ZipArchive zip = new ZipArchive(s, ZipArchiveMode.Read))
        {
            int n = 0, total = zip.Entries.Count;
            string root = Path.GetFullPath(dir).TrimEnd('\\') + "\\";
            foreach (ZipArchiveEntry e in zip.Entries)
            {
                n++;
                if (e.FullName.EndsWith("/")) continue;
                string dest = Path.GetFullPath(Path.Combine(dir, e.FullName.Replace('/', '\\')));
                if (!dest.StartsWith(root, StringComparison.OrdinalIgnoreCase)) continue;   // never write outside the folder
                Directory.CreateDirectory(Path.GetDirectoryName(dest));
                for (int attempt = 0; ; attempt++)
                {
                    try
                    {
                        using (Stream src = e.Open())
                        using (FileStream f = new FileStream(dest, FileMode.Create, FileAccess.Write))
                            src.CopyTo(f);
                        break;
                    }
                    catch (IOException)
                    {
                        if (attempt >= 5) throw;
                        Thread.Sleep(600);
                    }
                }
                Report("Copying " + e.Name, 5 + 80 * n / total);
            }
        }

        Report("Creating shortcuts…", 88);
        string exe = Path.Combine(dir, Studio.LauncherExe);
        string icon = Path.Combine(dir, "icon.ico");
        Studio.CreateShortcut(Studio.StartMenuShortcut, exe, dir, icon, "Download videos and audio with yt-dlp");
        if (desktop)
            Studio.CreateShortcut(Studio.DesktopShortcut, exe, dir, icon, "Download videos and audio with yt-dlp");
        else if (File.Exists(Studio.DesktopShortcut))
            File.Delete(Studio.DesktopShortcut);

        Report("Registering with Windows…", 95);
        long kb = 0;
        foreach (string f in Directory.GetFiles(dir, "*", SearchOption.AllDirectories))
        {
            try { kb += new FileInfo(f).Length / 1024; } catch (Exception) { }
        }
        using (RegistryKey k = Registry.CurrentUser.CreateSubKey(Studio.UninstallKey))
        {
            string uninst = Path.Combine(dir, Studio.UninstallExe);
            k.SetValue("DisplayName", Studio.Name);
            k.SetValue("DisplayVersion", Studio.Version);
            k.SetValue("Publisher", "yt-dlp Studio");
            k.SetValue("Comments", "A friendly front end for yt-dlp (AI-generated app)");
            k.SetValue("DisplayIcon", exe);
            k.SetValue("InstallLocation", dir);
            k.SetValue("UninstallString", "\"" + uninst + "\"");
            k.SetValue("QuietUninstallString", "\"" + uninst + "\" /quiet");
            k.SetValue("InstallDate", DateTime.Now.ToString("yyyyMMdd"));
            k.SetValue("EstimatedSize", (int)Math.Min(kb, int.MaxValue), RegistryValueKind.DWord);
            k.SetValue("NoModify", 1, RegistryValueKind.DWord);
            k.SetValue("NoRepair", 1, RegistryValueKind.DWord);
        }
        Report("Done", 100);
    }

    void Done(string dir)
    {
        done = true;
        bar.Visible = false;
        status.Text = "";
        foreach (Control c in body.Controls) c.Visible = false;
        intro.Visible = true;
        intro.Size = new Size(504, 140);
        intro.Font = new Font("Segoe UI", 10.5f);
        intro.Text = "yt-dlp Studio is installed.\n\nYou'll find it in the Start menu" + (desktopBox.Checked ? " and on your desktop" : "") +
                     ".\n\nTo remove it later, use Settings › Apps › Installed apps, or run \"Uninstall yt-dlp Studio\" in:\n" + dir;
        installBtn.Text = "Finish";
        installBtn.Enabled = true;
        cancelBtn.Visible = false;
        installBtn.Focus();
        installDir = dir;
    }

    string installDir;

    void Finish()
    {
        if (launchBox.Checked && installDir != null)
        {
            try { Process.Start(new ProcessStartInfo(Path.Combine(installDir, Studio.LauncherExe)) { WorkingDirectory = installDir }); }
            catch (Exception) { }
        }
        Close();
    }

    static string Arg(string[] args, string name)
    {
        foreach (string a in args)
            if (a.StartsWith(name + "=", StringComparison.OrdinalIgnoreCase)) return a.Substring(name.Length + 1).Trim('"');
        return null;
    }

    /// Command line (for scripted installs and testing):
    ///   /silent [/dir=PATH] [/nodesktop]     install without showing a window
    ///   /screenshot=FILE.png [/done]         save a picture of the window and exit
    [STAThread]
    static int Main(string[] args)
    {
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        bool has = false;
        foreach (string a in args) if (a.Equals("/silent", StringComparison.OrdinalIgnoreCase)) has = true;
        if (has)
        {
            SetupForm f = new SetupForm();
            string dir = Arg(args, "/dir") ?? f.dirBox.Text;
            try { f.Install(dir, Array.IndexOf(args, "/nodesktop") < 0); return 0; }
            catch (Exception ex) { Console.Error.WriteLine(ex); return 1; }
        }
        string shot = Arg(args, "/screenshot");
        if (shot != null)
        {
            SetupForm f = new SetupForm();
            f.StartPosition = FormStartPosition.Manual;
            f.Location = new Point(-4000, -4000);
            f.ShowInTaskbar = false;
            f.Shown += delegate
            {
                if (Array.IndexOf(args, "/done") >= 0) f.Done(f.dirBox.Text);
                Application.DoEvents();
                using (Bitmap bmp = new Bitmap(f.Width, f.Height))
                {
                    f.DrawToBitmap(bmp, new Rectangle(0, 0, f.Width, f.Height));
                    bmp.Save(shot, System.Drawing.Imaging.ImageFormat.Png);
                }
                f.Close();
            };
            Application.Run(f);
            return 0;
        }
        Application.Run(new SetupForm());
        return 0;
    }
}
