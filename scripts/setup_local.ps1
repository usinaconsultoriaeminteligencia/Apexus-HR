# Script de setup rapido para teste local (Windows PowerShell)
# Uso: .\scripts\setup_local.ps1

Write-Host "Configurando ambiente de teste local..." -ForegroundColor Cyan
Write-Host ""

# Verificar pre-requisitos
Write-Host "Verificando pre-requisitos..."

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERRO: Python nao encontrado. Instale Python 3.11+" -ForegroundColor Red
    exit 1
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "ERRO: Node.js nao encontrado. Instale Node.js 18+" -ForegroundColor Red
    exit 1
}

Write-Host "OK: Pre-requisitos atendidos" -ForegroundColor Green
Write-Host ""

# Verificar Docker
$useDocker = $false
if ((Get-Command docker -ErrorAction SilentlyContinue) -and (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "OK: Docker encontrado" -ForegroundColor Green
    $useDocker = $true
} else {
    Write-Host "AVISO: Docker nao encontrado" -ForegroundColor Yellow
}
Write-Host ""

# Criar .env se nao existir
if (-not (Test-Path .env)) {
    Write-Host "Criando arquivo .env..."
    
    $secretKeyOutput = python -c "import secrets; print(secrets.token_urlsafe(64))" 2>&1
    if ($LASTEXITCODE -eq 0) {
        $secretKey = $secretKeyOutput.Trim()
    } else {
        Write-Host "AVISO: Erro ao gerar SECRET_KEY" -ForegroundColor Yellow
        $secretKey = "change-me-secret-key-" + (-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_}))
    }
    
    $jwtKeyOutput = python -c "import secrets; print(secrets.token_urlsafe(64))" 2>&1
    if ($LASTEXITCODE -eq 0) {
        $jwtKey = $jwtKeyOutput.Trim()
    } else {
        Write-Host "AVISO: Erro ao gerar JWT_SECRET_KEY" -ForegroundColor Yellow
        $jwtKey = "change-me-jwt-key-" + (-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_}))
    }
    
    $lines = @(
        "# Configuracoes de Banco de Dados",
        "POSTGRES_DB=assistente_rh",
        "POSTGRES_USER=postgres",
        "POSTGRES_PASSWORD=postgres",
        "",
        "# Redis",
        "REDIS_URL=redis://localhost:6379/0",
        "",
        "# Seguranca",
        "SECRET_KEY=$secretKey",
        "JWT_SECRET_KEY=$jwtKey",
        "",
        "# OpenAI (IMPORTANTE: Configure sua chave real!)",
        "OPENAI_API_KEY=sk-sua_chave_openai_aqui",
        "",
        "# Ambiente",
        "ENVIRONMENT=development",
        "DEBUG=true",
        "TESTING=false",
        "",
        "# CORS",
        "CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173",
        "",
        "# Upload",
        "MAX_UPLOAD_SIZE=100",
        "UPLOAD_FOLDER=./uploads",
        "",
        "# Pool de conexoes",
        "DB_POOL_SIZE=10",
        "DB_POOL_TIMEOUT=30",
        "DB_POOL_RECYCLE=1800",
        "DB_MAX_OVERFLOW=20",
        "",
        "# Refinamento OpenAI",
        "ENABLE_RESPONSE_REFINEMENT=true",
        "REFINEMENT_MAX_RETRIES=3",
        "REFINEMENT_ENABLE_CACHE=true",
        "REFINEMENT_ENABLE_FEW_SHOT=true"
    )
    
    $lines | Out-File -FilePath .env -Encoding utf8
    
    Write-Host "OK: Arquivo .env criado" -ForegroundColor Green
    Write-Host "IMPORTANTE: Configure sua OPENAI_API_KEY no arquivo .env" -ForegroundColor Yellow
} else {
    Write-Host "AVISO: Arquivo .env ja existe" -ForegroundColor Yellow
}
Write-Host ""

# Setup Backend
Write-Host "Configurando backend..."
Push-Location backend

if (-not (Test-Path venv)) {
    Write-Host "Criando ambiente virtual Python..."
    python -m venv venv
    Write-Host "OK: Ambiente virtual criado" -ForegroundColor Green
}

Write-Host "Instalando dependencias Python..."
& .\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
Write-Host "OK: Dependencias Python instaladas" -ForegroundColor Green

Pop-Location
Write-Host ""

# Setup Frontend
Write-Host "Configurando frontend..."
Push-Location frontend

if (-not (Test-Path node_modules)) {
    Write-Host "Instalando dependencias Node.js..."
    npm install
    Write-Host "OK: Dependencias Node.js instaladas" -ForegroundColor Green
} else {
    Write-Host "AVISO: node_modules ja existe" -ForegroundColor Yellow
}

if (-not (Test-Path .env.local)) {
    Write-Host "Criando arquivo .env.local..."
    "VITE_API_URL=http://localhost:8000" | Out-File -FilePath .env.local -Encoding utf8
    Write-Host "OK: Arquivo .env.local criado" -ForegroundColor Green
}

Pop-Location
Write-Host ""

# Setup Docker
if ($useDocker -and (Test-Path docker-compose.yml)) {
    Write-Host "Iniciando servicos Docker..."
    docker-compose up -d
    Start-Sleep -Seconds 5
    Write-Host "OK: Servicos Docker iniciados" -ForegroundColor Green
    Write-Host ""
}

# Criar diretorios
Write-Host "Criando diretorios necessarios..."
New-Item -ItemType Directory -Force -Path uploads | Out-Null
New-Item -ItemType Directory -Force -Path data/finetuning | Out-Null
New-Item -ItemType Directory -Force -Path logs | Out-Null
Write-Host "OK: Diretorios criados" -ForegroundColor Green
Write-Host ""

# Resumo
$separator = "=" * 80
Write-Host $separator -ForegroundColor Cyan
Write-Host "Setup concluido com sucesso!" -ForegroundColor Green
Write-Host ""
Write-Host "Proximos passos:" -ForegroundColor Yellow
Write-Host "1. Configure sua OPENAI_API_KEY no arquivo .env"
Write-Host "2. Configure o banco de dados:"
Write-Host "   cd backend"
Write-Host "   .\venv\Scripts\Activate.ps1"
Write-Host "   `$env:DATABASE_URL='postgresql://postgres:postgres@localhost:5432/assistente_rh'"
Write-Host "   flask db upgrade"
Write-Host "3. Inicie o backend: python src/main.py"
Write-Host "4. Em outro terminal, inicie o frontend:"
Write-Host "   cd frontend"
Write-Host "   npm run dev"
Write-Host ""
Write-Host "URLs:" -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost:5173"
Write-Host "   Backend:  http://localhost:8000"
Write-Host $separator -ForegroundColor Cyan
