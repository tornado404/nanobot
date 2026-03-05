# build-windows-service.ps1
# Build the Windows Screen Capture Service

param(
    [string]$Release = "release",
    [switch]$Clean
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
    Write-Host "|  nanobot Windows Capture Service - Build Script        |" -ForegroundColor Cyan
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host ""

    # Get script directory
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $ProjectDir = Join-Path $ScriptDir "..\windows-service"

    Write-Host "Project directory: $ProjectDir"
    Write-Host "Build mode: $Release"
    Write-Host ""

    # Check if Rust is installed
    Write-Host "Checking Rust installation..." -NoNewline
    try {
        $rustVersion = rustc --version
        Write-Host " $rustVersion" -ForegroundColor Green
    } catch {
        Write-Host " FAILED" -ForegroundColor Red
        Write-Host ""
        Write-Host "Rust is not installed. Please install Rust from:" -ForegroundColor Yellow
        Write-Host "https://rustup.rs/" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Or run:" -ForegroundColor Yellow
        Write-Host "winget install Rustlang.Rustup" -ForegroundColor Yellow
        Write-Host ""
        exit 1
    }

    # Clean if requested
    if ($Clean) {
        Write-Host "Cleaning build artifacts..."
        Set-Location $ProjectDir
        cargo clean
        Write-Host ""
    }

    # Build
    Write-Host "Building Windows capture service..."
    Set-Location $ProjectDir

    if ($Release -eq "release") {
        Write-Host "Building in release mode (optimized)..." -ForegroundColor Cyan
        cargo build --release
    } else {
        Write-Host "Building in debug mode..." -ForegroundColor Cyan
        cargo build
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "Build FAILED!" -ForegroundColor Red
        Write-Host ""
        exit 1
    }

    # Find output
    if ($Release -eq "release") {
        $OutputPath = Join-Path $ProjectDir "target\release\nanobot-capture-service.exe"
    } else {
        $OutputPath = Join-Path $ProjectDir "target\debug\nanobot-capture-service.exe"
    }

    if (Test-Path $OutputPath) {
        $fileSize = (Get-Item $OutputPath).Length / 1MB
        $sizeStr = [math]::Round($fileSize, 2)
        Write-Host ""
        Write-Host "Build SUCCESSFUL!" -ForegroundColor Green
        Write-Host "Output: $OutputPath" -ForegroundColor Green
        Write-Host "Size: $sizeStr MB" -ForegroundColor Green
    } else {
        Write-Host "Output not found"
    }

    Write-Host ""
}
catch {
    Write-Host "An error occurred: $_" -ForegroundColor Red
}
finally {
    Pause-Script
}
