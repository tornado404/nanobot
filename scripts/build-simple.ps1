$ErrorActionPreference = "Stop"

try {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $ProjectDir = Join-Path $ScriptDir "..\windows-service"

    Write-Host "Building in: $ProjectDir"

    Set-Location $ProjectDir
    cargo build --release

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Build success"
    } else {
        Write-Host "Build failed"
    }
}
catch {
    Write-Host "An error occurred: $_" -ForegroundColor Red
}

Write-Host "Press Enter to exit..."
Read-Host
