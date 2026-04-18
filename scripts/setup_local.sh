#!/usr/bin/env bash
# Script de setup rápido para teste local
# Uso: ./scripts/setup_local.sh

set -e

echo "🚀 Configurando ambiente de teste local..."
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar pré-requisitos
echo "📋 Verificando pré-requisitos..."

command -v python3 >/dev/null 2>&1 || { echo -e "${RED}❌ Python 3 não encontrado. Instale Python 3.11+${NC}" >&2; exit 1; }
command -v node >/dev/null 2>&1 || { echo -e "${RED}❌ Node.js não encontrado. Instale Node.js 18+${NC}" >&2; exit 1; }
command -v npm >/dev/null 2>&1 || { echo -e "${RED}❌ npm não encontrado. Instale npm${NC}" >&2; exit 1; }

echo -e "${GREEN}✅ Pré-requisitos OK${NC}"
echo ""

# Verificar Docker (opcional)
if command -v docker >/dev/null 2>&1 && command -v docker-compose >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker encontrado - será usado para PostgreSQL e Redis${NC}"
    USE_DOCKER=true
else
    echo -e "${YELLOW}⚠️  Docker não encontrado - você precisará instalar PostgreSQL e Redis manualmente${NC}"
    USE_DOCKER=false
fi
echo ""

# Criar arquivo .env se não existir
if [ ! -f .env ]; then
    echo "📝 Criando arquivo .env..."
    
    # Gerar chaves seguras
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
    JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
    
    cat > .env << EOF
# Configurações de Banco de Dados
POSTGRES_DB=assistente_rh
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis
REDIS_URL=redis://localhost:6379/0

# Segurança
SECRET_KEY=${SECRET_KEY}
JWT_SECRET_KEY=${JWT_SECRET_KEY}

# OpenAI (IMPORTANTE: Configure sua chave real!)
OPENAI_API_KEY=sk-sua_chave_openai_aqui

# Ambiente
ENVIRONMENT=development
DEBUG=true
TESTING=false

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173

# Upload
MAX_UPLOAD_SIZE=100
UPLOAD_FOLDER=./uploads

# Pool de conexões
DB_POOL_SIZE=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800
DB_MAX_OVERFLOW=20

# Refinamento OpenAI
ENABLE_RESPONSE_REFINEMENT=true
REFINEMENT_MAX_RETRIES=3
REFINEMENT_ENABLE_CACHE=true
REFINEMENT_ENABLE_FEW_SHOT=true
EOF
    
    echo -e "${GREEN}✅ Arquivo .env criado${NC}"
    echo -e "${YELLOW}⚠️  IMPORTANTE: Configure sua OPENAI_API_KEY no arquivo .env${NC}"
else
    echo -e "${YELLOW}⚠️  Arquivo .env já existe, pulando criação${NC}"
fi
echo ""

# Setup Backend
echo "🐍 Configurando backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual Python..."
    python3 -m venv venv
    echo -e "${GREEN}✅ Ambiente virtual criado${NC}"
fi

echo "📦 Instalando dependências Python..."
source venv/bin/activate 2>/dev/null || venv/Scripts/activate
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✅ Dependências Python instaladas${NC}"

cd ..
echo ""

# Setup Frontend
echo "⚛️  Configurando frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "📦 Instalando dependências Node.js..."
    npm install
    echo -e "${GREEN}✅ Dependências Node.js instaladas${NC}"
else
    echo -e "${YELLOW}⚠️  node_modules já existe, pulando instalação${NC}"
fi

# Criar .env.local se não existir
if [ ! -f .env.local ]; then
    echo "📝 Criando arquivo .env.local..."
    echo "VITE_API_URL=http://localhost:8000" > .env.local
    echo -e "${GREEN}✅ Arquivo .env.local criado${NC}"
fi

cd ..
echo ""

# Setup Docker (se disponível)
if [ "$USE_DOCKER" = true ]; then
    echo "🐳 Configurando serviços Docker..."
    
    # Verificar se docker-compose.yml existe
    if [ -f "docker-compose.yml" ]; then
        echo "🚀 Iniciando PostgreSQL e Redis..."
        docker-compose up -d
        
        echo "⏳ Aguardando serviços iniciarem..."
        sleep 5
        
        # Verificar saúde dos serviços
        if docker-compose ps | grep -q "Up"; then
            echo -e "${GREEN}✅ Serviços Docker iniciados${NC}"
        else
            echo -e "${YELLOW}⚠️  Alguns serviços podem não estar prontos ainda${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  docker-compose.yml não encontrado${NC}"
    fi
    echo ""
fi

# Criar diretórios necessários
echo "📁 Criando diretórios necessários..."
mkdir -p uploads
mkdir -p data/finetuning
mkdir -p logs
echo -e "${GREEN}✅ Diretórios criados${NC}"
echo ""

# Resumo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ TESTE_LOCAL.md
