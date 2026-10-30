param([string]$TargetDirectory, [switch]$NoShortcuts, [switch]$UseSource, [switch]$Quiet)
$ErrorActionPreference='Stop'
if ($PSVersionTable.PSEdition -eq 'Desktop') {
    $env:PSModulePath=(Join-Path $PSHOME 'Modules')+';'+$env:PSModulePath
}
Add-Type -AssemblyName System.Windows.Forms
$sourceRoot=[IO.Path]::GetFullPath($PSScriptRoot)
try {
    if ($UseSource) { $TargetDirectory=$sourceRoot }
    if (-not $TargetDirectory) {
        $dialog=New-Object System.Windows.Forms.FolderBrowserDialog
        $dialog.Description='Wybierz folder dla Nokturn Bubble Studio. Program utworzy w nim folder Nokturn-Bubble-Studio.'
        $dialog.SelectedPath=[Environment]::GetFolderPath('LocalApplicationData')
        if ($dialog.ShowDialog() -ne 'OK') { exit 0 }
        $TargetDirectory=Join-Path $dialog.SelectedPath 'Nokturn-Bubble-Studio'
    }
    $targetRoot=[IO.Path]::GetFullPath($TargetDirectory)
    $manifestPath=Join-Path $sourceRoot 'release-manifest.json'
    if (-not (Test-Path -LiteralPath $manifestPath)) { throw 'Brakuje manifestu wydania. Rozpakuj ponownie cala paczke programu.' }
    $manifest=Get-Content -Raw -LiteralPath $manifestPath -Encoding UTF8 | ConvertFrom-Json
    if ($manifest.format -ne 'nokturn-bubble-studio-release-v1') { throw 'Nieprawidlowy manifest wydania.' }
    # Validate every path and every source hash before touching the installation.
    $files=@()
    foreach ($item in $manifest.files) {
        $relative=[string]$item.path
        if ([IO.Path]::IsPathRooted($relative) -or $relative -match '(^|[\/])\.\.([\/]|$)' -or $relative.Contains(':')) { throw 'Nieprawidlowa sciezka w paczce.' }
        $src=[IO.Path]::GetFullPath((Join-Path $sourceRoot $relative))
        $dst=[IO.Path]::GetFullPath((Join-Path $targetRoot $relative))
        if (-not $src.StartsWith($sourceRoot.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase) -or -not $dst.StartsWith($targetRoot.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Plik poza folderem programu.' }
        if (-not (Test-Path -LiteralPath $src) -or (Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.sha256) { throw "Uszkodzony plik paczki: $relative" }
        $files+=@{Source=$src;Destination=$dst;Relative=$relative}
    }
    $backupRoot=Join-Path $targetRoot ('.updates\'+(Get-Date -Format 'yyyyMMdd-HHmmss-ffff'))
    if (-not [string]::Equals($sourceRoot,$targetRoot,[StringComparison]::OrdinalIgnoreCase)) {
        foreach ($file in $files) {
            if (Test-Path -LiteralPath $file.Destination) {
                $backup=Join-Path $backupRoot $file.Relative
                New-Item -ItemType Directory -Force -Path (Split-Path -Parent $backup) | Out-Null
                Copy-Item -LiteralPath $file.Destination -Destination $backup
            }
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $file.Destination) | Out-Null
            Copy-Item -LiteralPath $file.Source -Destination $file.Destination -Force
        }
        Copy-Item -LiteralPath $manifestPath -Destination (Join-Path $targetRoot 'release-manifest.json') -Force
    }
    foreach ($folder in @('WEJSCIE\Komiksy','WEJSCIE\Manga','WEJSCIE\Manhua','GOTOWE','PRACA')) {
        New-Item -ItemType Directory -Force -Path (Join-Path $targetRoot $folder) | Out-Null
    }
    if (-not $NoShortcuts) {
        $shell=New-Object -ComObject WScript.Shell
        foreach ($directory in @([Environment]::GetFolderPath('Desktop'),(Join-Path ([Environment]::GetFolderPath('Programs')) 'Nokturn'))) {
            New-Item -ItemType Directory -Force -Path $directory | Out-Null
            $link=$shell.CreateShortcut((Join-Path $directory 'Nokturn Bubble Studio.lnk'))
            $link.TargetPath=Join-Path $env:SystemRoot 'System32\wscript.exe'
            $link.Arguments='"'+(Join-Path $targetRoot 'START.vbs')+'"'
            $link.WorkingDirectory=$targetRoot
            $link.IconLocation=(Join-Path $targetRoot 'assets\bubble-studio.ico')+',0'
            $link.Description='Przygotowanie dymkow i wypowiedzi do Nokturna'
            $link.Save()
        }
    }
    Write-Output "Zainstalowano: $targetRoot"
    if (-not $NoShortcuts -and -not $Quiet) {
        [System.Windows.Forms.MessageBox]::Show("Gotowe. Skrot Nokturn Bubble Studio jest na pulpicie i w menu Start.`nPierwszy start sam przygotuje Python i biblioteki. Wymagany internet oraz karta NVIDIA z minimum 10 GB pamieci.", 'Nokturn Bubble Studio') | Out-Null
    }
} catch {
    if ($NoShortcuts) { Write-Error $_; exit 1 }
    [System.Windows.Forms.MessageBox]::Show([string]$_,'Instalacja nie powiodla sie','OK','Error') | Out-Null
    exit 1
}
