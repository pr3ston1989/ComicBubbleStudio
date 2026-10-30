param([switch]$SmokeTest)
$ErrorActionPreference='Stop'
if ($PSVersionTable.PSEdition -eq 'Desktop') {
    $env:PSModulePath=(Join-Path $PSHOME 'Modules')+';'+$env:PSModulePath
}
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$repoRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$runtimeRoot=Join-Path $PSScriptRoot '.runtime'
New-Item -ItemType Directory -Force -Path $runtimeRoot | Out-Null
$stamp=Get-Date -Format 'yyyyMMdd-HHmmss-ffff'
$stdout=Join-Path $runtimeRoot ('startup-'+$stamp+'.log')
$stderr=Join-Path $runtimeRoot ('startup-'+$stamp+'-error.log')
$form=New-Object Windows.Forms.Form
$form.Text='Nokturn Bubble Studio'
$form.ClientSize=New-Object Drawing.Size(620,340)
$form.StartPosition='CenterScreen'
$form.FormBorderStyle='FixedDialog'
$form.MaximizeBox=$false
$form.MinimizeBox=$true
$form.BackColor=[Drawing.ColorTranslator]::FromHtml('#14101f')
$form.ForeColor=[Drawing.ColorTranslator]::FromHtml('#eee8fa')
$iconPath=Join-Path $repoRoot 'assets\bubble-studio.ico'
if (Test-Path -LiteralPath $iconPath) { $form.Icon=New-Object Drawing.Icon($iconPath) }
$picture=New-Object Windows.Forms.PictureBox
$picture.Location=New-Object Drawing.Point(28,26)
$picture.Size=New-Object Drawing.Size(108,108)
$picture.SizeMode='Zoom'
$imagePath=Join-Path $repoRoot 'assets\bubble-studio.png'
if (Test-Path -LiteralPath $imagePath) { $picture.Image=[Drawing.Image]::FromFile($imagePath) }
$form.Controls.Add($picture)
$title=New-Object Windows.Forms.Label
$title.Text="Nokturn`nBubble Studio"
$title.Font=New-Object Drawing.Font('Segoe UI',24,[Drawing.FontStyle]::Bold)
$title.Location=New-Object Drawing.Point(156,32)
$title.Size=New-Object Drawing.Size(420,100)
$form.Controls.Add($title)
$status=New-Object Windows.Forms.Label
$status.Font=New-Object Drawing.Font('Segoe UI',11)
$status.Text='Sprawdzam lokalne srodowisko programu…'
$status.Location=New-Object Drawing.Point(30,154)
$status.Size=New-Object Drawing.Size(560,38)
$form.Controls.Add($status)
$note=New-Object Windows.Forms.Label
$note.Text='Pierwsze uruchomienie pobierze kilka GB bibliotek. Kolejne starty korzystaja z zapisanych plikow.'
$note.Font=New-Object Drawing.Font('Segoe UI',10)
$note.ForeColor=[Drawing.ColorTranslator]::FromHtml('#bcaed0')
$note.Location=New-Object Drawing.Point(30,202)
$note.Size=New-Object Drawing.Size(560,48)
$form.Controls.Add($note)
$bar=New-Object Windows.Forms.ProgressBar
$bar.Style='Marquee'
$bar.Location=New-Object Drawing.Point(30,268)
$bar.Size=New-Object Drawing.Size(560,16)
$form.Controls.Add($bar)
$details=New-Object Windows.Forms.LinkLabel
$details.Text='Otworz szczegoly uruchamiania'
$details.LinkColor=[Drawing.ColorTranslator]::FromHtml('#6cddd1')
$details.Location=New-Object Drawing.Point(30,300)
$details.AutoSize=$true
$details.Add_LinkClicked({ if (Test-Path -LiteralPath $stdout) { Start-Process notepad.exe -ArgumentList @('"'+$stdout+'"') } })
$form.Controls.Add($details)
$script:ready=$false
$script:smokePassed=$false
$script:child=$null
$timer=New-Object Windows.Forms.Timer
$timer.Interval=500
$timer.Add_Tick({
    $log=if (Test-Path -LiteralPath $stdout) { Get-Content -LiteralPath $stdout -Raw -ErrorAction SilentlyContinue } else { '' }
    if ($log -match '@@STUDIO_READY') { $script:ready=$true; $timer.Stop(); $form.Close(); return }
    if ($log -match 'Instalowanie zaleznosci') { $status.Text='Przygotowuje biblioteki i obsluge karty graficznej…' }
    elseif ($log -match 'pobieranie lokalnego') { $status.Text='Pobieram prywatne srodowisko Python…' }
    elseif ($log -match 'Naprawiam sciezki') { $status.Text='Dostosowuje program do nowego folderu…' }
    if ($script:child -and $script:child.HasExited) {
        $script:ready=$true
        $timer.Stop()
        $errorText=if (Test-Path -LiteralPath $stderr) { Get-Content -LiteralPath $stderr -Tail 8 | Out-String } else { '' }
        [Windows.Forms.MessageBox]::Show("Nie udalo sie uruchomic programu.`n$errorText`nSzczegoly: $stdout",'Nokturn Bubble Studio','OK','Error') | Out-Null
        $form.Close()
    }
})
$form.Add_Shown({
    if ($SmokeTest) {
        $script:smokePassed=$true
        foreach ($control in $form.Controls) {
            if (-not $form.ClientRectangle.Contains($control.Bounds)) { $script:smokePassed=$false }
        }
        Write-Output 'Splash layout OK: 620x340, wszystkie elementy w oknie.'
        $script:ready=$true
        $form.Close()
        return
    }
    try {
        $script:child=Start-Process -FilePath (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe') -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"'+(Join-Path $PSScriptRoot 'bootstrap.ps1')+'"'),'-Mode','gui') -WorkingDirectory $repoRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
        $timer.Start()
    } catch { $script:ready=$true; [Windows.Forms.MessageBox]::Show([string]$_,'Nokturn Bubble Studio') | Out-Null; $form.Close() }
})
$form.Add_FormClosing({ param($sender,$event)
    if (-not $script:ready -and $script:child -and -not $script:child.HasExited) {
        $answer=[Windows.Forms.MessageBox]::Show('Przerwac przygotowanie? Kolejny start ponowi niedokonczony etap.','Nokturn Bubble Studio','YesNo','Question')
        if ($answer -eq 'No') { $event.Cancel=$true; return }
        Start-Process -FilePath (Join-Path $env:SystemRoot 'System32\taskkill.exe') -ArgumentList @('/PID',[string]$script:child.Id,'/T','/F') -WindowStyle Hidden -Wait
    }
    $timer.Stop()
})
[Windows.Forms.Application]::Run($form)
if ($picture.Image) { $picture.Image.Dispose() }
$timer.Dispose()
$form.Dispose()
if ($SmokeTest) {
    if (-not $script:smokePassed) { throw 'Element poza ekranem startowym.' }
    Write-Output 'Splash layout OK: 620x340, wszystkie elementy w oknie.'
}
