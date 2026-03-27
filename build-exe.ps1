#Requires -Version 5.1
<#
.SYNOPSIS
    Converte setup.ps1 em setup.exe usando PS2EXE
.DESCRIPTION
    Execute este script UMA VEZ na máquina do desenvolvedor para gerar o instalador .exe.
    O .exe gerado pode ser distribuído para os analistas.

    Uso:
        .\build-exe.ps1
#>

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "  AFA - Gerador de Instalador .exe" -ForegroundColor Cyan
Write-Host ""

# Instala PS2EXE se necessário
if (-not (Get-Module -ListAvailable -Name ps2exe)) {
    Write-Host "  Instalando ps2exe..." -ForegroundColor Yellow
    Install-Module -Name ps2exe -Scope CurrentUser -Force -AllowClobber
}
Import-Module ps2exe

$scriptPath = Join-Path $PSScriptRoot "setup.ps1"
$outputPath = Join-Path $PSScriptRoot "AFA-Setup.exe"

Write-Host "  Gerando AFA-Setup.exe..." -ForegroundColor Cyan

Invoke-ps2exe `
    -InputFile  $scriptPath `
    -OutputFile $outputPath `
    -Title      "AFA - Anti-Fraud Agent Setup" `
    -Description "Instalador automático do Anti-Fraud Agent" `
    -Company    "AFA" `
    -Version    "1.0.0" `
    -RequireAdmin `
    -NoConsole:$false

if (Test-Path $outputPath) {
    $sizeMB = [math]::Round((Get-Item $outputPath).Length / 1MB, 1)
    Write-Host ""
    Write-Host "  ✔  AFA-Setup.exe gerado com sucesso! ($sizeMB MB)" -ForegroundColor Green
    Write-Host "     Localização: $outputPath" -ForegroundColor White
    Write-Host ""
    Write-Host "  Distribuição:" -ForegroundColor Yellow
    Write-Host "    1. Envie AFA-Setup.exe para o analista" -ForegroundColor Gray
    Write-Host "    2. Analista dá duplo clique e aguarda ~5 minutos" -ForegroundColor Gray
    Write-Host "    3. Sistema inicia automaticamente" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "  ✖  Falha ao gerar .exe" -ForegroundColor Red
    exit 1
}
