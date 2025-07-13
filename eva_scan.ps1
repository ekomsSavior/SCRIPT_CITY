# Set log path
$logPath = "$env:USERPROFILE\Desktop\eva_scan_report.txt"
Start-Transcript -Path $logPath -Force

Write-Host "`nEVA SCAN – Starting Threat Hunt..." -ForegroundColor Cyan

# 1. Active network connections
Write-Host "`n[+] Active Network Connections:" -ForegroundColor Yellow
Get-NetTCPConnection | Where-Object {$_.State -eq "Established"} | Format-Table -AutoSize

# 2. Top CPU processes
Write-Host "`n[+] Top Running Processes:" -ForegroundColor Yellow
Get-Process | Sort-Object CPU -Descending | Select-Object -First 15 Name, Id, CPU, Path | Format-Table -AutoSize

# 3. Unsigned processes
Write-Host "`n[+] Unsigned Executables:" -ForegroundColor Yellow
Get-Process | ForEach-Object {
    try {
        $sig = Get-AuthenticodeSignature $_.Path
        if ($sig.Status -ne "Valid") {
            "$($_.Name): $($_.Path) => $($sig.Status)"
        }
    } catch {}
}

# 4. Startup entries
Write-Host "`n[+] Startup Programs:" -ForegroundColor Yellow
Get-CimInstance Win32_StartupCommand | Select-Object Name, Command, Location | Format-Table -AutoSize

# 5. Suspicious Scheduled Tasks
Write-Host "`n[+] Non-Microsoft Scheduled Tasks:" -ForegroundColor Yellow
Get-ScheduledTask | Where-Object {$_.TaskPath -notlike "\Microsoft*"} | Select-Object TaskName, TaskPath, State | Format-Table -AutoSize

# 6. Local user accounts
Write-Host "`n[+] Enabled Local Users:" -ForegroundColor Yellow
Get-LocalUser | Where-Object {$_.Enabled -eq $true} | Select-Object Name, Enabled, LastLogon | Format-Table -AutoSize

# 7. RDP logins (Event ID 4624 - RemoteInteractive)
Write-Host "`n[+] RDP Logins Detected (if any):" -ForegroundColor Yellow
Get-EventLog -LogName Security -InstanceId 4624 -Newest 50 | Where-Object {$_.Message -like "*RemoteInteractive*"} | Select-Object TimeGenerated, Message | Format-Table -Wrap

# 8. Suspicious services
Write-Host "`n[+] Suspicious Auto-Start Services:" -ForegroundColor Yellow
Get-Service | Where-Object {$_.StartType -eq "Automatic"} | ForEach-Object {
    $svc = Get-WmiObject -Class Win32_Service -Filter "Name='$($_.Name)'"
    "$($_.Name): $($svc.PathName)"
} | Where-Object {$_ -notmatch "Microsoft"}

# 9. EXEs in TEMP and APPDATA
Write-Host "`n[+] EXEs in TEMP and APPDATA:" -ForegroundColor Yellow
Get-ChildItem "$env:TEMP","$env:APPDATA" -Recurse -Include *.exe -ErrorAction SilentlyContinue | Select-Object FullName, Length | Format-Table -AutoSize

# 10. PowerShell history
Write-Host "`n[+] PowerShell History (suspicious lines):" -ForegroundColor Yellow
Get-Content (Get-PSReadlineOption).HistorySavePath | Select-String -Pattern "Invoke|Download|IEX|New-Object" | Sort-Object -Unique

# 11. Defender quick scan
Write-Host "`n[+] Running Windows Defender Quick Scan..." -ForegroundColor Cyan
Start-MpScan -ScanType QuickScan

# 12. Defender threat history
Write-Host "`n[+] Recent Windows Defender Detections:" -ForegroundColor Yellow
Get-MpThreatDetection | Select-Object DetectionID, ThreatName, ActionSuccess, InitialDetectionTime | Format-Table -AutoSize

# Done
Write-Host "`nEVA SCAN COMPLETE. Stay safe, frend." -ForegroundColor Green

Stop-Transcript
