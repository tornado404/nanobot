# stop-service.ps1
# Stop the Windows Screen Capture Service

$ErrorActionPreference = "Stop"

$TaskName = "NanobotCaptureService"

Write-Host ""
Write-Host "Stopping nanobot capture service..." -NoNewline

try {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
    
    if ($task.State -eq "Running") {
        Stop-ScheduledTask -TaskName $TaskName
        Start-Sleep -Seconds 1
        
        $task = Get-ScheduledTask -TaskName $TaskName
        if ($task.State -eq "Stopped") {
            Write-Host " Stopped successfully" -ForegroundColor Green
        } else {
            Write-Host " Task state: $($task.State)" -ForegroundColor Yellow
        }
    } else {
        Write-Host " Not running (state: $($task.State))" -ForegroundColor Yellow
    }
} catch {
    Write-Host " FAILED" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Press any key to exit..."
[void][System.Console]::ReadKey($true)
