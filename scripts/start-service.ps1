# start-service.ps1
# Start the Windows Screen Capture Service

$ErrorActionPreference = "Stop"

$TaskName = "NanobotCaptureService"

Write-Host ""
Write-Host "Starting nanobot capture service..." -NoNewline

try {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
    
    if ($task.State -eq "Running") {
        Write-Host " Already running" -ForegroundColor Green
    } else {
        Start-ScheduledTask -TaskName $TaskName
        Start-Sleep -Seconds 1
        
        $task = Get-ScheduledTask -TaskName $TaskName
        if ($task.State -eq "Running") {
            Write-Host " Started successfully" -ForegroundColor Green
        } else {
            Write-Host " Task state: $($task.State)" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host " FAILED" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Make sure the service is installed:" -ForegroundColor Yellow
    Write-Host "  .\install-service.ps1" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press any key to exit..."
[void][System.Console]::ReadKey($true)
