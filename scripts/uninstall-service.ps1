# uninstall-service.ps1
# Uninstall the Windows Screen Capture Service

param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$TaskName = "NanobotCaptureService"
$InstallDir = Join-Path $PSScriptRoot "..\install"

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "|  nanobot Capture Service - Uninstallation              |" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# Check if task exists
$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if (-not $task) {
    Write-Host "Service not found. Nothing to uninstall." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Press any key to exit..."
    [void][System.Console]::ReadKey($true)
    exit 0
}

# Stop the service if running
if ($task.State -eq "Running") {
    Write-Host "Stopping service..."
    Stop-ScheduledTask -TaskName $TaskName
    Start-Sleep -Seconds 2
}

# Remove scheduled task
if ($Force) {
    Write-Host "Removing scheduled task..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Task removed" -ForegroundColor Green
} else {
    Write-Host "Use -Force to remove the scheduled task" -ForegroundColor Yellow
}

# Remove installation directory
if (Test-Path $InstallDir) {
    if ($Force) {
        Write-Host "Removing installation directory: $InstallDir"
        Remove-Item -Path $InstallDir -Recurse -Force
        Write-Host "Directory removed" -ForegroundColor Green
    } else {
        Write-Host "Use -Force to remove installation files" -ForegroundColor Yellow
        Write-Host "Directory: $InstallDir"
    }
}

Write-Host ""

if ($Force) {
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host "|  Uninstallation Complete!                              |" -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Green
} else {
    Write-Host "Partial uninstallation complete." -ForegroundColor Yellow
    Write-Host "Use -Force for complete removal" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "Press any key to exit..."
[void][System.Console]::ReadKey($true)
