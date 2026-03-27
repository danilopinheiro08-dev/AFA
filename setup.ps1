#Requires -Version 5.1
<#
.SYNOPSIS
    AFA - Anti-Fraud Agent | Instalador automático para Windows
.DESCRIPTION
    Instala Python, Node.js, Git (se necessário), clona/atualiza o repositório,
    configura o ambiente virtual, instala dependências e configura o .env.
#>

param(
    [string]$GroqKey = "",
    [switch]$Headless
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference    = "SilentlyContinue"   # winget progress bars break redirects

# ─── Constantes ────────────────────────────────────────────────────────────────
$REPO_URL   = "https://github.com/danilopinheiro08-dev/AFA.git"
$INSTALL_DIR = Join-Path $env:USERPROFILE "AFA"
$PYTHON_MIN  = [Version]"3.11"
$NODE_MIN    = [Version]"18.0"

# ─── Helpers de saída ──────────────────────────────────────────────────────────
function banner {
    Clear-Host
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════╗" -ForegroundColor DarkRed
    Write-Host "  ║    🛡  Anti-Fraud Agent (AFA) Setup      ║" -ForegroundColor Red
    Write-Host "  ╚══════════════════════════════════════════╝" -ForegroundColor DarkRed
    Write-Host ""
}

function step([int]$n, [string]$msg) {
    Write-Host "  [$n/7] $msg" -ForegroundColor Cyan
}

function ok([string]$msg)   { Write-Host "        ✔  $msg" -ForegroundColor Green }
function warn([string]$msg) { Write-Host "        ⚠  $msg" -ForegroundColor Yellow }
function err([string]$msg)  { Write-Host "        ✖  $msg" -ForegroundColor Red }
function info([string]$msg) { Write-Host "        →  $msg" -ForegroundColor Gray }

function Pause-OnError([string]$msg) {
    err $msg
    Write-Host ""
    Write-Host "  Pressione qualquer tecla para fechar..." -ForegroundColor DarkGray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# ─── Refresh PATH sem reiniciar o terminal ─────────────────────────────────────
function Refresh-Path {
    $machinePath = [System.Environment]::GetEnvironmentVariable("PATH", "Machine")
    $userPath    = [System.Environment]::GetEnvironmentVariable("PATH", "User")
    $env:PATH    = "$machinePath;$userPath"
}

# ─── Verifica versão de um executável ─────────────────────────────────────────
function Get-ExeVersion([string]$exe) {
    try {
        $raw = & $exe --version 2>&1 | Select-Object -First 1
        $m = [regex]::Match($raw, '\d+\.\d+[\.\d]*')
        if ($m.Success) { return [Version]$m.Value }
    } catch {}
    return $null
}

# ─── Instala pacote via winget ─────────────────────────────────────────────────
function Install-WingetPackage([string]$id, [string]$name) {
    info "Instalando $name via winget..."
    $result = winget install --id $id `
        --silent `
        --accept-package-agreements `
        --accept-source-agreements `
        --scope machine 2>&1

    if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne -1978335189) {
        # -1978335189 = APPINSTALLER_ERROR_ALREADY_INSTALLED
        warn "$name pode não ter instalado corretamente (código $LASTEXITCODE)."
        warn "Tente instalar manualmente e rode o setup novamente."
    }
    Refresh-Path
}

# ─── Verifica se winget está disponível ───────────────────────────────────────
function Assert-Winget {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Pause-OnError "winget não encontrado. Atualize o Windows (App Installer) e tente novamente."
    }
}

# ══════════════════════════════════════════════════════════════════════════════
# INÍCIO
# ══════════════════════════════════════════════════════════════════════════════

banner

# ─── Elevação de privilégio ────────────────────────────────────────────────────
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
        ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    warn "Elevando privilégios de administrador..."
    $args_str = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    if ($GroqKey)  { $args_str += " -GroqKey `"$GroqKey`"" }
    if ($Headless) { $args_str += " -Headless" }
    Start-Process powershell -ArgumentList $args_str -Verb RunAs
    exit
}

$Host.UI.RawUI.WindowTitle = "AFA Setup"

Assert-Winget

# ══════════════════════════════════════════════════════════════════════════════
# PASSO 1 — GIT
# ══════════════════════════════════════════════════════════════════════════════
step 1 "Verificando Git..."

$gitVer = Get-ExeVersion "git"
if ($gitVer) {
    ok "Git $gitVer já instalado."
} else {
    Install-WingetPackage "Git.Git" "Git"
    Refresh-Path
    $gitVer = Get-ExeVersion "git"
    if (-not $gitVer) { Pause-OnError "Git não encontrado após instalação. Reinicie e tente novamente." }
    ok "Git $gitVer instalado."
}

# ══════════════════════════════════════════════════════════════════════════════
# PASSO 2 — PYTHON
# ══════════════════════════════════════════════════════════════════════════════
step 2 "Verificando Python $PYTHON_MIN+..."

Refresh-Path
$pyVer = Get-ExeVersion "python"
if ($pyVer -and $pyVer -ge $PYTHON_MIN) {
    ok "Python $pyVer já instalado."
} else {
    if ($pyVer) { warn "Python $pyVer encontrado, mas precisa de $PYTHON_MIN+. Instalando versão correta..." }
    Install-WingetPackage "Python.Python.3.11" "Python 3.11"
    Refresh-Path
    Start-Sleep -Seconds 2
    $pyVer = Get-ExeVersion "python"
    if (-not $pyVer) { Pause-OnError "Python não encontrado após instalação. Reinicie o PC e rode o setup novamente." }
    ok "Python $pyVer instalado."
}

# ══════════════════════════════════════════════════════════════════════════════
# PASSO 3 — NODE.JS
# ══════════════════════════════════════════════════════════════════════════════
step 3 "Verificando Node.js $NODE_MIN+..."

Refresh-Path
$nodeVer = Get-ExeVersion "node"
if ($nodeVer -and $nodeVer -ge $NODE_MIN) {
    ok "Node.js $nodeVer já instalado."
} else {
    if ($nodeVer) { warn "Node.js $nodeVer encontrado, mas precisa de $NODE_MIN+. Instalando versão correta..." }
    Install-WingetPackage "OpenJS.NodeJS.LTS" "Node.js LTS"
    Refresh-Path
    Start-Sleep -Seconds 2
    $nodeVer = Get-ExeVersion "node"
    if (-not $nodeVer) { Pause-OnError "Node.js não encontrado após instalação. Reinicie o PC e rode o setup novamente." }
    ok "Node.js $nodeVer instalado."
}

# ══════════════════════════════════════════════════════════════════════════════
# PASSO 4 — REPOSITÓRIO
# ══════════════════════════════════════════════════════════════════════════════
step 4 "Configurando repositório em $INSTALL_DIR..."

if (Test-Path (Join-Path $INSTALL_DIR ".git")) {
    info "Repositório já existe. Atualizando..."
    Push-Location $INSTALL_DIR
    try {
        git pull origin main 2>&1 | Out-Null
        ok "Repositório atualizado."
    } catch {
        warn "Não foi possível atualizar. Usando versão local."
    }
    Pop-Location
} else {
    if (Test-Path $INSTALL_DIR) {
        warn "Pasta $INSTALL_DIR existe mas não é um repositório git. Removendo..."
        Remove-Item -Recurse -Force $INSTALL_DIR
    }
    info "Clonando repositório..."
    git clone $REPO_URL $INSTALL_DIR 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { Pause-OnError "Falha ao clonar repositório. Verifique a conexão com a internet." }
    ok "Repositório clonado em $INSTALL_DIR."
}

Set-Location $INSTALL_DIR

# ══════════════════════════════════════════════════════════════════════════════
# PASSO 5 — BACKEND (venv + pip)
# ══════════════════════════════════════════════════════════════════════════════
step 5 "Configurando backend Python..."

Set-Location "$INSTALL_DIR\backend"

if (-not (Test-Path "venv")) {
    info "Criando ambiente virtual..."
    python -m venv venv 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { Pause-OnError "Falha ao criar ambiente virtual Python." }
}
ok "Ambiente virtual pronto."

info "Instalando dependências Python (pode demorar alguns minutos)..."
$pip = "$INSTALL_DIR\backend\venv\Scripts\pip.exe"
& $pip install -r requirements.txt -q --no-warn-script-location 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { Pause-OnError "Falha ao instalar dependências Python. Verifique a conexão." }
ok "Dependências Python instaladas."

# ─── .env ─────────────────────────────────────────────────────────────────────
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    ok ".env criado a partir do .env.example."
} else {
    ok ".env já existe."
}

Set-Location $INSTALL_DIR

# ══════════════════════════════════════════════════════════════════════════════
# PASSO 6 — FRONTEND (npm)
# ══════════════════════════════════════════════════════════════════════════════
step 6 "Configurando frontend Node.js..."

Set-Location "$INSTALL_DIR\frontend"
info "Instalando dependências npm..."
npm install --silent 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { Pause-OnError "Falha ao instalar dependências npm." }
ok "Frontend configurado."

Set-Location $INSTALL_DIR

# ─── Pastas de dados ──────────────────────────────────────────────────────────
$null = New-Item -ItemType Directory -Force "$INSTALL_DIR\backend\data\csv"
$null = New-Item -ItemType Directory -Force "$INSTALL_DIR\backend\data\chroma"
$null = New-Item -ItemType Directory -Force "$INSTALL_DIR\backend\data\reports"
$null = New-Item -ItemType Directory -Force "$INSTALL_DIR\backend\data\blacklist"

# ══════════════════════════════════════════════════════════════════════════════
# PASSO 7 — GROQ API KEY
# ══════════════════════════════════════════════════════════════════════════════
step 7 "Configurando chave Groq API..."

$envFile = "$INSTALL_DIR\backend\.env"
$envContent = Get-Content $envFile -Raw

# Verifica se já tem chave configurada
$currentKey = ""
if ($envContent -match 'GROQ_API_KEY=(.+)') {
    $currentKey = $Matches[1].Trim()
}

$hasValidKey = $currentKey -and $currentKey -ne "gsk_your_key_here" -and $currentKey.StartsWith("gsk_")

if ($GroqKey -and $GroqKey.StartsWith("gsk_")) {
    # Chave passada como parâmetro
    $envContent = $envContent -replace 'GROQ_API_KEY=.*', "GROQ_API_KEY=$GroqKey"
    Set-Content -Path $envFile -Value $envContent -NoNewline
    ok "Chave Groq configurada."
} elseif ($hasValidKey) {
    ok "Chave Groq já configurada ($($currentKey.Substring(0,12))...)."
} elseif (-not $Headless) {
    Write-Host ""
    Write-Host "  ┌─────────────────────────────────────────────┐" -ForegroundColor DarkYellow
    Write-Host "  │  Obtenha sua chave GRATUITA em:             │" -ForegroundColor Yellow
    Write-Host "  │  https://console.groq.com                   │" -ForegroundColor Yellow
    Write-Host "  └─────────────────────────────────────────────┘" -ForegroundColor DarkYellow
    Write-Host ""
    $inputKey = Read-Host "  Cole sua GROQ_API_KEY (ou Enter para pular)"
    $inputKey = $inputKey.Trim()

    if ($inputKey -and $inputKey.StartsWith("gsk_")) {
        $envContent = $envContent -replace 'GROQ_API_KEY=.*', "GROQ_API_KEY=$inputKey"
        Set-Content -Path $envFile -Value $envContent -NoNewline
        ok "Chave Groq configurada."
    } else {
        warn "Chave não configurada. Configure manualmente em: backend\.env"
    }
} else {
    warn "Chave Groq não configurada. Configure em backend\.env antes de iniciar."
}

# ══════════════════════════════════════════════════════════════════════════════
# ATALHO NA ÁREA DE TRABALHO
# ══════════════════════════════════════════════════════════════════════════════
try {
    $desktop  = [System.Environment]::GetFolderPath("Desktop")
    $lnkPath  = Join-Path $desktop "AFA - Anti-Fraud Agent.lnk"
    $startBat = Join-Path $INSTALL_DIR "start.bat"

    $wsh = New-Object -ComObject WScript.Shell
    $lnk = $wsh.CreateShortcut($lnkPath)
    $lnk.TargetPath       = $startBat
    $lnk.WorkingDirectory = $INSTALL_DIR
    $lnk.Description      = "Iniciar Anti-Fraud Agent"
    $lnk.Save()
    ok "Atalho criado na Área de Trabalho."
} catch {
    warn "Não foi possível criar atalho na Área de Trabalho."
}

# ══════════════════════════════════════════════════════════════════════════════
# RESUMO FINAL
# ══════════════════════════════════════════════════════════════════════════════
Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════╗" -ForegroundColor DarkGreen
Write-Host "  ║        Instalação concluída com sucesso!     ║" -ForegroundColor Green
Write-Host "  ╚══════════════════════════════════════════════╝" -ForegroundColor DarkGreen
Write-Host ""
Write-Host "  Instalado em : $INSTALL_DIR" -ForegroundColor White
Write-Host "  Frontend     : http://localhost:5173" -ForegroundColor White
Write-Host "  API Docs     : http://localhost:8000/docs" -ForegroundColor White
Write-Host ""

if (-not $hasValidKey -and -not ($GroqKey -and $GroqKey.StartsWith("gsk_"))) {
    Write-Host "  ⚠  Configure sua GROQ_API_KEY em:" -ForegroundColor Yellow
    Write-Host "     $INSTALL_DIR\backend\.env" -ForegroundColor Yellow
    Write-Host ""
}

if (-not $Headless) {
    $start = Read-Host "  Deseja iniciar o AFA agora? (S/n)"
    if ($start -ne 'n' -and $start -ne 'N') {
        Start-Process cmd -ArgumentList "/k cd /d `"$INSTALL_DIR`" && start.bat" -WorkingDirectory $INSTALL_DIR
    }
}

Write-Host "  Para iniciar depois: duplo clique em start.bat ou no atalho da Área de Trabalho." -ForegroundColor Gray
Write-Host ""
