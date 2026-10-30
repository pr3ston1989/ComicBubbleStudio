param([Parameter(Mandatory=$true)][string]$PythonPath)
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
& $PythonPath (Join-Path $PSScriptRoot 'build_release.py')
if ($LASTEXITCODE -ne 0) { throw 'Budowanie ZIP nie powiodlo sie.' }
$version=(Get-Content -LiteralPath (Join-Path $root 'release-manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json).version
$zip=Join-Path $root ('dist\Nokturn-Bubble-Studio-'+$version+'-windows-x64.zip')
$output=Join-Path $root ('dist\Nokturn-Bubble-Studio-'+$version+'-Setup.exe')
if (Test-Path -LiteralPath $output) { throw 'Instalator juz istnieje. Przenies poprzedni plik przed przebudowa.' }
$parameters=New-Object CodeDom.Compiler.CompilerParameters
$parameters.GenerateExecutable=$true
$parameters.OutputAssembly=$output
$parameters.CompilerOptions='/target:winexe /win32icon:"'+(Join-Path $root 'assets\bubble-studio.ico')+'"'
$parameters.EmbeddedResources.Add($zip) | Out-Null
foreach ($reference in @('System.dll','System.Core.dll','System.Windows.Forms.dll','System.IO.Compression.dll','System.IO.Compression.FileSystem.dll')) {
 $parameters.ReferencedAssemblies.Add($reference) | Out-Null
}
$provider=New-Object Microsoft.CSharp.CSharpCodeProvider
$result=$provider.CompileAssemblyFromFile($parameters,(Join-Path $PSScriptRoot 'Installer.cs'))
if ($result.Errors.HasErrors) { throw (($result.Errors | Out-String)) }
$hash=(Get-FileHash -LiteralPath $output -Algorithm SHA256).Hash.ToLowerInvariant()
[IO.File]::WriteAllText($output+'.sha256',$hash+'  '+[IO.Path]::GetFileName($output)+[Environment]::NewLine)
Write-Output $output
