param([Parameter(Mandatory=$true)][string]$PackageZip,[Parameter(Mandatory=$true)][string]$SetupExe,[Parameter(Mandatory=$true)][string]$TestRoot)
$ErrorActionPreference='Stop'
$env:PSModulePath=(Join-Path $PSHOME 'Modules')+';'+$env:PSModulePath
$TestRoot=[IO.Path]::GetFullPath($TestRoot)
if (Test-Path -LiteralPath $TestRoot) { throw 'Test wymaga nowego folderu, aby zachowac poprzednie dane.' }
New-Item -ItemType Directory -Path $TestRoot | Out-Null
Expand-Archive -LiteralPath $PackageZip -DestinationPath $TestRoot
$source=Join-Path $TestRoot 'Nokturn-Bubble-Studio'
$target=Join-Path $TestRoot 'Instalacja probna Zażółć'
$winps=Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
function Install-ForTest([string]$Destination) {
    & $winps -NoProfile -ExecutionPolicy Bypass -File (Join-Path $source 'INSTALUJ.ps1') -TargetDirectory $Destination -NoShortcuts
    if ($LASTEXITCODE -ne 0) { throw 'Instalacja probna nie powiodla sie.' }
}
Install-ForTest $target
$sentinel=Join-Path $target 'WEJSCIE\zachowaj.txt'
[IO.File]::WriteAllText($sentinel,'user-input-must-survive')
$private=Join-Path $target 'tools\bubble_studio\.runtime'
New-Item -ItemType Directory -Force -Path $private | Out-Null
[IO.File]::WriteAllText((Join-Path $private 'keep.txt'),'runtime-must-survive')
[IO.File]::WriteAllText((Join-Path $target 'README.md'),'old-program-file')
Install-ForTest $target
if ([IO.File]::ReadAllText($sentinel) -ne 'user-input-must-survive') { throw 'Utrata pliku uzytkownika.' }
if ([IO.File]::ReadAllText((Join-Path $private 'keep.txt')) -ne 'runtime-must-survive') { throw 'Utrata runtime.' }
$backups=@(Get-ChildItem -LiteralPath (Join-Path $target '.updates') -Recurse -Filter README.md)
if (-not @($backups | Where-Object { [IO.File]::ReadAllText($_.FullName) -eq 'old-program-file' }).Count) { throw 'Brak kopii poprzedniego pliku.' }
if ((Get-FileHash -LiteralPath (Join-Path $target 'README.md')).Hash -ne (Get-FileHash -LiteralPath (Join-Path $source 'README.md')).Hash) { throw 'Niepelna aktualizacja.' }
$asset=Join-Path $source 'assets\bubble-studio.png'
$stream=[IO.File]::Open($asset,[IO.FileMode]::Append);$stream.WriteByte(0);$stream.Dispose()
$rejected=Join-Path $TestRoot 'Niepowinna-powstac'
$ErrorActionPreference='Continue'
& $winps -NoProfile -ExecutionPolicy Bypass -File (Join-Path $source 'INSTALUJ.ps1') -TargetDirectory $rejected -NoShortcuts *> (Join-Path $TestRoot 'expected-corruption-rejection.log')
$rejectionCode=$LASTEXITCODE
$ErrorActionPreference='Stop'
if ($rejectionCode -eq 0 -or (Test-Path -LiteralPath $rejected)) { throw 'Uszkodzona paczka nie zostala bezpiecznie odrzucona.' }
$env:TEMP=Join-Path $TestRoot 'exe-temp';$env:TMP=$env:TEMP
New-Item -ItemType Directory -Path $env:TEMP | Out-Null
$process=Start-Process -FilePath $SetupExe -ArgumentList '--verify-only' -PassThru -Wait -WindowStyle Hidden
if ($process.ExitCode -ne 0) { throw ('Blad testu EXE: '+(Get-Content -LiteralPath (Join-Path $env:TEMP 'NokturnSetup-verify.log') -Raw)) }
$summary=[ordered]@{zipExtraction=$true;unicodeDestination=$true;upgrade=$true;inputPreserved=$true;runtimePreserved=$true;backupCreated=$true;corruptionRejectedBeforeWriting=$true;selfExtractingExeVerified=$true}
$summary | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $TestRoot 'distribution-tests.json') -Encoding UTF8
$summary | ConvertTo-Json
