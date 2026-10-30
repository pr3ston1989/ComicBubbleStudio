using System;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Diagnostics;
using System.Windows.Forms;
class Installer {
 [STAThread] static int Main(string[] args) {
  bool verify=Array.IndexOf(args,"--verify-only")>=0;
  string tempBase=Path.GetFullPath(Path.GetTempPath()).TrimEnd(Path.DirectorySeparatorChar);
  string work=Path.GetFullPath(Path.Combine(tempBase,"NokturnSetup-"+Guid.NewGuid().ToString("N")));
  string prefix=work+Path.DirectorySeparatorChar;
  try {
   Directory.CreateDirectory(work);
   Assembly assembly=Assembly.GetExecutingAssembly(); string resource=null;
   foreach(string name in assembly.GetManifestResourceNames()) if(name.EndsWith(".zip")) resource=name;
   if(resource==null) throw new Exception("Brak paczki programu w instalatorze.");
   using(Stream stream=assembly.GetManifestResourceStream(resource))
   using(ZipArchive zip=new ZipArchive(stream,ZipArchiveMode.Read)) {
    foreach(ZipArchiveEntry entry in zip.Entries) {
     string dest=Path.GetFullPath(Path.Combine(work,entry.FullName.Replace('/',Path.DirectorySeparatorChar)));
     if(!dest.StartsWith(prefix,StringComparison.OrdinalIgnoreCase)) throw new Exception("Plik poza paczka programu.");
     if(entry.FullName.EndsWith("/")) { Directory.CreateDirectory(dest); continue; }
     Directory.CreateDirectory(Path.GetDirectoryName(dest));
     using(Stream input=entry.Open()) using(FileStream output=File.Create(dest)) input.CopyTo(output);
    }
   }
   string root=Path.Combine(work,"Nokturn-Bubble-Studio"),script=Path.Combine(root,"INSTALUJ.ps1");
   if(!File.Exists(script)) throw new Exception("Niepelna paczka programu.");
   ProcessStartInfo info=new ProcessStartInfo(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System),@"WindowsPowerShell\v1.0\powershell.exe"));
   info.Arguments="-NoProfile -ExecutionPolicy Bypass -File \""+script+"\""+(verify?" -UseSource -NoShortcuts":"");
   info.UseShellExecute=false; info.CreateNoWindow=true;
   // A caller running PowerShell 7 may export only its own module paths.
   // The embedded installer deliberately uses Windows PowerShell 5.1.
   info.EnvironmentVariables["PSModulePath"]=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System),@"WindowsPowerShell\v1.0\Modules")+";"+Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles),@"WindowsPowerShell\Modules");
   if(verify) { info.RedirectStandardOutput=true; info.RedirectStandardError=true; }
   using(Process child=Process.Start(info)) {
    string output=verify?child.StandardOutput.ReadToEnd()+child.StandardError.ReadToEnd():"";
    child.WaitForExit();
    if(verify) File.WriteAllText(Path.Combine(tempBase,"NokturnSetup-verify.log"),output+"\nExitCode: "+child.ExitCode);
    return child.ExitCode;
   }
  } catch(Exception error) {
   if(!verify) MessageBox.Show(error.Message,"Nokturn Bubble Studio",MessageBoxButtons.OK,MessageBoxIcon.Error);
   if(verify) File.WriteAllText(Path.Combine(tempBase,"NokturnSetup-verify.log"),error.ToString());
   return 1;
  } finally {
   // Only this process's freshly generated extraction directory may be removed.
   if(work.StartsWith(tempBase+Path.DirectorySeparatorChar+"NokturnSetup-",StringComparison.OrdinalIgnoreCase)) {
    try { if(Directory.Exists(work)) Directory.Delete(work,true); } catch { }
   }
  }
 }
}
