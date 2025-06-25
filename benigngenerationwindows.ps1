param (
    [int]$MinPauseSeconds = 30,
    [int]$MaxPauseSeconds = 120
)

# List of websites to browse
$urls = @(
    "https://google.com",
    "https://mail.apttestbed.local",
    "https://news.ycombinator.com",
    "https://linkedin.com",
    "https://outlook.office.com",
    "https://docs.microsoft.com",
    "https://github.com",
    "https://stackoverflow.com",
    "https://intranet.apttestbed.local",
    "https://teams.microsoft.com"
)

# YouTube videos to watch
$videoUrls = @(
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://www.youtube.com/watch?v=3JZ_D3ELwOQ",
    "https://www.youtube.com/watch?v=l482T0yNkeo"
)

# RDP targets (hostname or IP)
$rdpTargets = @(
    "192.168.56.5"
)
# Credentials for RDP
$rdpUser = "Administrator@apttestbed.local"
$rdpPass = "!fearisthelittledeath5"

function Random-Sleep { Start-Sleep -Seconds (Get-Random -Minimum $MinPauseSeconds -Maximum $MaxPauseSeconds) }
function Short-Pause { Start-Sleep -Seconds (Get-Random -Minimum 5 -Maximum 15) }
function Maybe-Long-Idle { 
    if (Get-Random -Minimum 1 -Maximum 10 -le 2) { 
        Start-Sleep -Seconds (Get-Random -Minimum 300 -Maximum 900) 
    } 
}

$wshell = New-Object -ComObject WScript.Shell
$logFile = "$env:USERPROFILE\Documents\simuser_actions.log"

$commands = @(
    { 
        $p = Start-Process notepad.exe -PassThru; 
        Start-Sleep 2; 
        $wshell.AppActivate($p.Id); 
        $wshell.SendKeys("Meeting notes: {ENTER}"); 
        Short-Pause; 
        $wshell.SendKeys("Discussed project updates and next steps.{ENTER}"); 
        Short-Pause; 
        $wshell.SendKeys("^s"); 
        Short-Pause;
        $filename = "$env:USERPROFILE\Documents\meeting_notes_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
        $wshell.SendKeys($filename)
        Short-Pause;
        $wshell.SendKeys("{ENTER}")
        Short-Pause; 
        $wshell.SendKeys("%{F4}");
        "[$(Get-Date)] Created meeting notes in Notepad." | Out-File -Append $logFile
    },

    {
        $video = $videoUrls | Get-Random
        $p = Start-Process "msedge.exe" -ArgumentList "--new-window", $video -PassThru
        Start-Sleep (Get-Random -Minimum 15 -Maximum 30)
        Stop-Process -Id $p.Id -Force
        "[$(Get-Date)] Watched YouTube video: $video" | Out-File -Append $logFile
    },

    { 
        $p = Start-Process mspaint.exe -PassThru; 
        Start-Sleep 2; 
        $wshell.AppActivate($p.Id); 
        $wshell.SendKeys("^s"); 
        $wshell.SendKeys("$env:USERPROFILE\Pictures\pic_$(Get-Date -Format 'HHmmss').png"); 
        Short-Pause; 
        $wshell.SendKeys("{ENTER}"); 
        Short-Pause; 
        $wshell.SendKeys("%{F4}");
        Short-Pause;
        Stop-Process -Id $p.Id -Force;
        "[$(Get-Date)] Performed Paint image save." | Out-File -Append $logFile
    },

    { 
        $p = Start-Process write.exe -PassThru; 
        Start-Sleep 2; 
        $wshell.AppActivate($p.Id); 
        $wshell.SendKeys("Status report: OK{ENTER}"); 
        Short-Pause; 
        $wshell.SendKeys("^s"); 
        $wshell.SendKeys("$env:USERPROFILE\Documents\report_$(Get-Date -Format 'HHmmss').rtf"); 
        Short-Pause; 
        $wshell.SendKeys("{ENTER}"); 
        Short-Pause; 
        $wshell.SendKeys("%{F4}");
        "[$(Get-Date)] Performed WordPad report saved." | Out-File -Append $logFile
    },

    { 
        $selection = $urls | Get-Random -Count (Get-Random -Minimum 2 -Maximum 3); 
        foreach ($site in $selection) {
            $p = Start-Process $site -PassThru;
            Start-Sleep (Get-Random -Minimum 5 -Maximum 10);
            Stop-Process -Id $p.Id -Force;
        }
        "[$(Get-Date)] Performed Browsed websites: $($selection -join ', ')." | Out-File -Append $logFile
    },

    { 
        $tmp = "$env:TEMP\mail_$(Get-Date -Format 'HHmmss').txt"; 
        "Hello, please see the attached report." | Out-File $tmp; 
        Try { 
            Send-MailMessage -From "johncena@apttestbed.local" -To "manager@apttestbed.local" -Subject "Weekly Report" -Body (Get-Content $tmp) -SmtpServer "exchangeserver1.local" 
        } Catch {} 
        "[$(Get-Date)] Sent a report email to manager." | Out-File -Append $logFile
    },

    { 
        Add-Content -Path "$env:USERPROFILE\Documents\activity.log" -Value "Edited at $(Get-Date)" 
        "[$(Get-Date)] Performed Activity log updated." | Out-File -Append $logFile
    },

    { 
        $p = Start-Process calc.exe -PassThru; 
        Short-Pause; 
        Stop-Process -Id $p.Id -Force;
        "[$(Get-Date)] Performed Calculator opened and closed." | Out-File -Append $logFile
    },

    { 
        Start-Process cmd.exe -ArgumentList '/c echo Hello World & timeout /t 2' -NoNewWindow -Wait;
        "[$(Get-Date)] Performed Command prompt echo." | Out-File -Append $logFile
    },

    { 
        powershell.exe -NoProfile -Command "$PSVersionTable"; 
        Start-Sleep (Get-Random -Minimum 2 -Maximum 5);
        "[$(Get-Date)] Performed PowerShell version check." | Out-File -Append $logFile
    },

    { 
        New-Item -Path "HKCU:\Software\SimUser" -Force | Out-Null; 
        Set-ItemProperty -Path "HKCU:\Software\SimUser" -Name "LastCheck" -Value (Get-Date);
        "[$(Get-Date)] Performed Registry key set." | Out-File -Append $logFile
    },

    { 
        $target = $rdpTargets | Get-Random; 
        cmdkey /generic:"TERMSRV/$target" /user:"$rdpUser" /pass:"$rdpPass"; 
        $p = Start-Process mstsc.exe -ArgumentList "/v:$target" -PassThru; 
        Start-Sleep (Get-Random -Minimum 10 -Maximum 30); 
        Stop-Process -Id $p.Id -Force; 
        cmdkey /delete:"TERMSRV/$target";
        "[$(Get-Date)] Accessed remote work system $target." | Out-File -Append $logFile
    },

    {
        $p = Start-Process write.exe -PassThru;
        Start-Sleep 2;
        $wshell.AppActivate($p.Id);
        $wshell.SendKeys("Project Status Report{ENTER}"); 
        Short-Pause;
        $wshell.SendKeys("All tasks are on schedule. No issues reported.{ENTER}");
        Short-Pause;
        $wshell.SendKeys("^s");
        $wshell.SendKeys("$env:USERPROFILE\Documents\project_status_$(Get-Date -Format 'HHmmss').rtf");
        Short-Pause;
        $wshell.SendKeys("{ENTER}");
        Short-Pause;
        $wshell.SendKeys("%{F4}");
        "[$(Get-Date)] Created project status report in WordPad." | Out-File -Append $logFile
    }
)

while ($true) {
    $clusterSize = Get-Random -Minimum 1 -Maximum 3
    for ($i = 1; $i -le $clusterSize; $i++) {
        $command = $commands | Get-Random
        & $command
        Short-Pause
    }
    Random-Sleep
    Maybe-Long-Idle
}