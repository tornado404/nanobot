# install-service.ps1
# Install Windows Screen Capture Service as a scheduled task

param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

function Pause-Script {
    Write-Host ""
    Write-Host "Press Enter to exit..."
    Read-Host
}

try {
    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host "|  nanobot Capture Service - Installation                |" -ForegroundColor Cyan
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host ""

    # Check for administrator privileges
    if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Write-Host "ERROR: This script requires Administrator privileges." -ForegroundColor Red
        Write-Host "Please right-click the script and select 'Run with PowerShell as Administrator'." -ForegroundColor Yellow
        exit 1
    }

    # Configuration
    $TaskName = "NanobotCaptureService"
    $TaskDescription = "Windows Screen Capture Service for nanobot using Windows.Graphics.Capture API"
    $InstallDir = Join-Path $PSScriptRoot "..\install"
    $ExeName = "nanobot-capture-service.exe"
    $LogDir = Join-Path $InstallDir "logs"

    # Find the executable
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $ReleaseExe = Join-Path $ScriptDir "..\windows-service\target\release\$ExeName"
    $DebugExe = Join-Path $ScriptDir "..\windows-service\target\debug\$ExeName"

    if (Test-Path $ReleaseExe) {
        $SourceExe = $ReleaseExe
        Write-Host "Found release build: $SourceExe" -ForegroundColor Green
    } elseif (Test-Path $DebugExe) {
        $SourceExe = $DebugExe
        Write-Host "Found debug build: $SourceExe" -ForegroundColor Yellow
    } else {
        Write-Host "ERROR: Executable not found!" -ForegroundColor Red
        Write-Host "Please run build-windows-service.ps1 first" -ForegroundColor Yellow
        exit 1
    }

    # Check if already installed
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

    if ($existingTask) {
        if ($Force) {
            Write-Host "Existing task found, removing..." -ForegroundColor Yellow
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        } else {
            Write-Host "Existing task found. Use -Force to reinstall." -ForegroundColor Yellow
            Write-Host "Task status: $($existingTask.State)"
            exit 0
        }
    }

    # Create installation directory
    Write-Host ""
    Write-Host "Creating installation directory: $InstallDir"
    if (-not (Test-Path $InstallDir)) {
        New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    }

    # Create log directory
    if (-not (Test-Path $LogDir)) {
        New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    }

    # Copy executable
    $DestExe = Join-Path $InstallDir $ExeName
    Write-Host "Copying executable to: $DestExe"
    Copy-Item -Path $SourceExe -Destination $DestExe -Force

    # Create configuration file
    $ConfigPath = Join-Path $InstallDir "config.json"
    if (-not (Test-Path $ConfigPath)) {
        $Config = @{
            socket_path = "\\.\pipe\nanobot-capture"
            jpeg_quality = 85
            log_level = "info"
        }
        $Config | ConvertTo-Json | Set-Content -Path $ConfigPath
        Write-Host "Created default configuration: $ConfigPath"
    }

    # Create scheduled task
    Write-Host ""
    Write-Host "Creating scheduled task: $TaskName"

    $Action = New-ScheduledTaskAction `
        -Execute $DestExe `
        -WorkingDirectory $InstallDir

    $Trigger = New-ScheduledTaskTrigger `
        -AtLogon

    # Use current user instead of SYSTEM to ensure access to desktop session
    # This is required for Windows.Graphics.Capture API
    $Principal = New-ScheduledTaskPrincipal `
        -UserId $env:USERNAME `
        -RunLevel Highest `
        -LogonType Interactive

    $Settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -ExecutionTimeLimit 0 `
        -MultipleInstances IgnoreNew `
        -Priority 4

    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Principal $Principal `
        -Settings $Settings `
        -Description $TaskDescription | Out-Null

    Write-Host "Task created successfully" -ForegroundColor Green
    Write-Host "Note: This task runs as user '$env:USERNAME' to access the screen." -ForegroundColor Yellow
    Write-Host ""
    
    # Try to start the task immediately
    Write-Host "Starting task..."
    Start-ScheduledTask -TaskName $TaskName
    
    Start-Sleep -Seconds 2
    $taskState = (Get-ScheduledTask -TaskName $TaskName).State
    Write-Host "Current task state: $taskState" -ForegroundColor Cyan
    
    if ($taskState -eq "Running") {
        Write-Host "Service started successfully!" -ForegroundColor Green
    } else {
        Write-Host "Service may have failed to start or exited immediately." -ForegroundColor Yellow
        Write-Host "Please check logs in: $LogDir"
    }
    
    Write-Host ""
    Write-Host "To manage the service manually:"
    Write-Host "  Start-ScheduledTask -TaskName $TaskName"
    Write-Host "  Stop-ScheduledTask -TaskName $TaskName"
    Write-Host ""
}
catch {
    Write-Host "An error occurred: $_" -ForegroundColor Red
}
finally {
    Pause-Script
}
