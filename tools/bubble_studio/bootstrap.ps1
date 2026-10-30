param([ValidateSet('process', 'diagnostic', 'review', 'gui')][string]$Mode = 'gui')

function Repair-StudioEnvironment {
    param([Parameter(Mandatory = $true)][string]$RuntimeRoot)
    $environmentRoot = Join-Path $RuntimeRoot 'venv'
    $configuration = Join-Path $environmentRoot 'pyvenv.cfg'
    if (-not (Test-Path -LiteralPath $configuration)) { return }

    # Venv stores its base interpreter as an absolute path. Rebuild only its
    # launchers/configuration when the complete private runtime has been moved.
    # stdlib venv reuses site-packages without clearing or reinstalling them.
    $baseRoot = [System.IO.Path]::GetFullPath((Join-Path $RuntimeRoot 'python\cpython-3.12.10-windows-x86_64-none'))
    $configuredHome = [regex]::Match([System.IO.File]::ReadAllText($configuration), '(?m)^home\s*=\s*([^\r\n]+)')
    if ($configuredHome.Success -and [string]::Equals($configuredHome.Groups[1].Value.Trim().TrimEnd('\', '/'), $baseRoot.TrimEnd('\', '/'), [System.StringComparison]::OrdinalIgnoreCase) -and (Test-Path -LiteralPath (Join-Path $environmentRoot 'Scripts\python.exe'))) {
        return
    }
    $baseExe = Join-Path $baseRoot 'python.exe'
    if (-not (Test-Path -LiteralPath $baseExe)) {
        throw 'Brakuje prywatnego Python w .runtime\python. Przenies caly folder programu razem z .runtime albo rozpakuj czysta paczke do osobnego folderu.'
    }
    Write-Host 'Wykryto przeniesione srodowisko. Naprawiam sciezki Python; modele i zainstalowane biblioteki pozostaja.'
    $backup = $configuration + '.before-relocation'
    if (-not (Test-Path -LiteralPath $backup)) { Copy-Item -LiteralPath $configuration -Destination $backup }
    & $baseExe -I -m venv --without-pip --copies $environmentRoot
    if ($LASTEXITCODE -ne 0) { throw 'Nie udalo sie naprawic prywatnego Python po przeniesieniu. Zachowano biblioteki i modele; szczegoly w logu.' }
}

$ErrorActionPreference = 'Stop'
$studioRoot = $PSScriptRoot
$repoRoot = (Resolve-Path (Join-Path $studioRoot '..\..')).Path
$runtimeRoot = Join-Path $studioRoot '.runtime'
$venvRoot = Join-Path $runtimeRoot 'venv'
$pythonExe = Join-Path $venvRoot 'Scripts\python.exe'
$requirementsFile = Join-Path $studioRoot 'requirements.txt'
New-Item -ItemType Directory -Force -Path $runtimeRoot | Out-Null
$logPath = Join-Path $runtimeRoot ('run-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.log')
Start-Transcript -Path $logPath | Out-Null
$launcherLock = $null
try {
    try {
        $launcherLock = [System.IO.File]::Open((Join-Path $runtimeRoot 'launcher.lock'), [System.IO.FileMode]::OpenOrCreate, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
    } catch {
        throw 'Inne okno Bubble Studio juz pracuje. Zamknij je przed ponownym uruchomieniem.'
    }
    $env:UV_PYTHON_INSTALL_DIR = Join-Path $runtimeRoot 'python'
    $env:UV_PYTHON_BIN_DIR = Join-Path $runtimeRoot 'bin'
    $env:UV_CACHE_DIR = Join-Path $runtimeRoot 'cache'
    $env:HF_HOME = Join-Path $runtimeRoot 'models'
    $env:HF_HUB_DISABLE_TELEMETRY = '1'
    $env:DO_NOT_TRACK = '1'
    $env:PYTHONUTF8 = '1'
    $env:YOLO_CONFIG_DIR = Join-Path $runtimeRoot 'yolo'
    # Ultralytics sprawdza zapisywalność rodzica przed utworzeniem podfolderu.
    New-Item -ItemType Directory -Force -Path $env:YOLO_CONFIG_DIR | Out-Null
    $uvRoot = Join-Path $runtimeRoot 'uv'
    $uvExe = Join-Path $uvRoot 'uv.exe'
    if (-not (Test-Path -LiteralPath $uvExe)) {
        Write-Host 'Pierwsze uruchomienie: pobieranie lokalnego instalatora Python...'
        $uvZip = Join-Path $runtimeRoot 'uv-0.8.22.zip'
        Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/astral-sh/uv/releases/download/0.8.22/uv-x86_64-pc-windows-msvc.zip' -OutFile $uvZip
        $actualHash = (Get-FileHash -LiteralPath $uvZip -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualHash -ne '5049375aa2a5162f132b2c1cb992e25d42d47d934cab8c174dbe6f60973dcc12') {
            throw 'Nieprawidlowa suma kontrolna instalatora. Przerwano bez uruchamiania pobranego pliku.'
        }
        Expand-Archive -LiteralPath $uvZip -DestinationPath $uvRoot -Force
        if (-not (Test-Path -LiteralPath $uvExe)) { throw 'Brak uv.exe w oficjalnym archiwum' }
    }
    Repair-StudioEnvironment -RuntimeRoot $runtimeRoot
    if (-not (Test-Path -LiteralPath $pythonExe)) {
        & $uvExe venv --python 3.12.10 --python-preference only-managed $venvRoot
        if ($LASTEXITCODE -ne 0) { throw 'Nie udalo sie przygotowac prywatnego Python 3.12' }
    }
    $baseOutput = & $pythonExe -I -c 'import sys; print(sys.base_prefix)'
    if ($LASTEXITCODE -ne 0 -or -not $baseOutput) {
        throw 'Nie uruchomiono prywatnego Python. Sprawdz, czy przeniesiono caly folder .runtime. Szczegoly w logu.'
    }
    $pythonBase = ([string]($baseOutput | Select-Object -Last 1)).Trim()
    if ($Mode -in 'gui', 'review') {
        # Jawna lokalizacja Tcl/Tk zapobiega szukaniu skryptów w niewłaściwym venv.
        $tclRoot = Join-Path $pythonBase 'tcl\tcl8.6'
        $tkRoot = Join-Path $pythonBase 'tcl\tk8.6'
        if (Test-Path -LiteralPath (Join-Path $tclRoot 'init.tcl')) { $env:TCL_LIBRARY = $tclRoot }
        if (Test-Path -LiteralPath (Join-Path $tkRoot 'tk.tcl')) { $env:TK_LIBRARY = $tkRoot }
        & $pythonExe -c 'import tkinter; r=tkinter.Tk(); r.withdraw(); r.destroy()'
        if ($LASTEXITCODE -ne 0) { throw 'Nie dziala lokalny interfejs Tcl/Tk. Szczegoly w logu; PRZETWORZ.bat pozwala uruchomic kolejke bez panelu.' }
    }
    $stampFile = Join-Path $runtimeRoot 'dependencies.stamp'
    $stamp = 'torch-2.10.0-cu128|' + (Get-FileHash -LiteralPath $requirementsFile -Algorithm SHA256).Hash
    $previousStamp = if (Test-Path -LiteralPath $stampFile) { (Get-Content -LiteralPath $stampFile -Raw).Trim() } else { '' }
    if ($previousStamp -ne $stamp) {
        Write-Host 'Instalowanie zaleznosci GPU. Pierwszy start pobierze kilka GB; nie instalujemy CUDA Toolkit ani nic globalnie.'
        & $uvExe pip install --python $pythonExe torch==2.10.0 torchvision==0.25.0 --index-url https://download.pytorch.org/whl/cu128
        if ($LASTEXITCODE -ne 0) { throw 'Instalacja PyTorch CUDA nie powiodla sie' }
        & $uvExe pip install --python $pythonExe -r $requirementsFile
        if ($LASTEXITCODE -ne 0) { throw 'Instalacja modeli/zaleznosci nie powiodla sie' }
        Set-Content -LiteralPath $stampFile -Value $stamp -Encoding ASCII
    }
    Set-Location -LiteralPath $repoRoot
    # Pełny 7-Zip rozpakowujemy lokalnie z oficjalnego MSI, bez instalacji globalnej.
    $inputRoot = Join-Path $repoRoot 'WEJSCIE'
    $rarInput = if (Test-Path -LiteralPath $inputRoot) {
        Get-ChildItem -LiteralPath $inputRoot -Recurse -File | Where-Object { $_.Extension -in '.cbr', '.rar' } | Select-Object -First 1
    } else { $null }
    if (($rarInput -or $Mode -eq 'gui' -or $Mode -eq 'review') -and -not (Test-Path -LiteralPath 'C:\Program Files\7-Zip\7z.exe') -and -not (Get-Command 7z.exe -ErrorAction SilentlyContinue)) {
        $sevenRoot = Join-Path $runtimeRoot 'sevenzip'
        $sevenExe = Get-ChildItem -LiteralPath $sevenRoot -Filter 7z.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        if (-not $sevenExe) {
            $sevenMsi = Join-Path $runtimeRoot '7z2603-x64.msi'
            Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/ip7z/7zip/releases/download/26.03/7z2603-x64.msi' -OutFile $sevenMsi
            if ((Get-FileHash -LiteralPath $sevenMsi -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'c0680064d698a62dd4a5a47f403db356a6531a5473e4c4b1d090ea2590513926') {
                throw 'Nieprawidlowa suma kontrolna 7-Zip. Przerwano.'
            }
            $sevenProcess = Start-Process msiexec.exe -ArgumentList @('/a', ('"' + $sevenMsi + '"'), '/qn', ('TARGETDIR="' + $sevenRoot + '"')) -Wait -PassThru -WindowStyle Hidden
            if ($sevenProcess.ExitCode -ne 0) { throw 'Nie udalo sie lokalnie przygotowac 7-Zip. Zainstaluj oficjalny 7-Zip i ponow START.bat.' }
            $sevenExe = Get-ChildItem -LiteralPath $sevenRoot -Filter 7z.exe -Recurse | Select-Object -First 1
        }
        if (-not $sevenExe) { throw 'Brak 7z.exe po przygotowaniu MSI' }
        $env:NOKTURN_SEVENZIP = $sevenExe.FullName
    }
    if ($Mode -eq 'gui') {
        Write-Output '@@STUDIO_READY'
        & $pythonExe -m tools.bubble_studio.gui
    } elseif ($Mode -eq 'review') {
        & $pythonExe -m tools.bubble_studio.review
    } elseif ($Mode -eq 'diagnostic') {
        & $pythonExe -m tools.bubble_studio.runner --diagnostic
    } else {
        & $pythonExe -m tools.bubble_studio.runner
    }
    if ($LASTEXITCODE -ne 0) { throw "Praca zakonczona bledem. Szczegoly w: $logPath" }
    Write-Host "Gotowe. Log: $logPath"
} catch {
    Write-Host $_ -ForegroundColor Red
    exit 1
} finally {
    if ($launcherLock) { $launcherLock.Dispose() }
    Stop-Transcript | Out-Null
}
