# 🧪 Guia de Teste Local - Assistente RH

Este guia explica como testar a plataforma localmente em ambiente de desenvolvimento.

## 📋 Pré-requisitos

### Obrigatórios
- **Python 3.11+** instalado
- **Node.js 18+** e npm instalados
- **PostgreSQL 15+** (ou Docker para usar o container)
- **Redis** (ou Docker para usar o container)
- **Git** para clonar o repositório

### Opcional mas Recomendado
- **Docker** e **Docker Compose** (para facilitar setup de banco e Redis)

## 🚀 Opção 1: Teste Completo com Docker (Recomendado)

### Passo 1: Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```bash
# Banco de Dados
POSTGRES_DB=assistente_rh
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis
REDIS_URL=redis://localhost:6379/0

# Segurança (gere chaves seguras)
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(64))")
JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(64))")

# OpenAI (OBRIGATÓRIO - substitua pela sua chave real)
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
```

### Passo 2: Iniciar Serviços com Docker

```bash
# Iniciar PostgreSQL e Redis
docker-compose up -d

# Verificar se os serviços estão rodando
docker-compose ps
```

### Passo 3: Configurar Backend

```bash
cd backend

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente do backend
# Copie as variáveis do .env da raiz ou crie um .env específico
```

### Passo 4: Configurar Banco de Dados

```bash
# Ainda no diretório backend com venv ativado

# Configurar DATABASE_URL
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/assistente_rh
# Windows PowerShell:
$env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/assistente_rh"

# Executar migrações
flask db upgrade
# ou
python -m flask db upgrade
```

### Passo 5: Iniciar Backend

```bash
# Ainda no diretório backend com venv ativado
python src/main.py
```

O backend deve iniciar em `http://localhost:8000` (ou porta configurada).

### Passo 6: Configurar Frontend

Em um novo terminal:

```bash
cd frontend

# Instalar dependências
npm install

# Criar arquivo .env.local
echo "VITE_API_URL=http://localhost:8000" > .env.local

# Iniciar servidor de desenvolvimento
npm run dev
```

O frontend deve iniciar em `http://localhost:5173` (Vite padrão).

### Passo 7: Acessar a Aplicação

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **Health Check**: http://localhost:8000/api/health
- **API Info**: http://localhost:8000/api/info

## 🛠️ Opção 2: Teste Manual (Sem Docker)

### Passo 1: Instalar PostgreSQL e Redis Localmente

#### PostgreSQL
```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql
brew services start postgresql

# Windows
# Baixe do site oficial: https://www.postgresql.org/download/windows/
```

Criar banco de dados:
```sql
CREATE DATABASE assistente_rh;
CREATE USER postgres WITH PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE assistente_rh TO postgres;
```

#### Redis
```bash
# Ubuntu/Debian
sudo apt install redis-server

# macOS
brew install redis
brew services start redis

# Windows
# Baixe do site oficial: https://redis.io/download
```

### Passo 2-7: Seguir os mesmos passos da Opção 1

Ajuste apenas a `DATABASE_URL` e `REDIS_URL` para apontar para suas instalações locais.

## 🧪 Testando Funcionalidades

### 1. Teste de Health Check

```bash
curl http://localhost:8000/api/health
```

Resposta esperada:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00"
}
```

### 2. Teste de Autenticação

```bash
# Criar usuário (se não existir)
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@test.com",
    "password": "senha123",
    "name": "Admin Test",
    "role": "admin"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@test.com",
    "password": "senha123"
  }'
```

### 3. Teste de Criação de Candidato

```bash
# Primeiro, faça login e copie o token JWT
TOKEN="seu_token_jwt_aqui"

curl -X POST http://localhost:8000/api/candidates \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "João Silva",
    "email": "joao@test.com",
    "phone": "11999999999",
    "position": "Desenvolvedor Backend",
    "resume": "Experiência em Python e Flask"
  }'
```

### 4. Teste de Entrevista por Áudio

1. Acesse http://localhost:5173
2. Faça login
3. Vá para "Entrevistas por Áudio"
4. Crie uma nova entrevista
5. Teste a gravação de áudio

## 🔍 Verificando Logs

### Backend
```bash
# Logs do backend (se rodando com Python)
# Os logs aparecem no terminal onde você iniciou o servidor

# Ou verifique arquivos de log se configurados
tail -f logs/assistente_rh.log
```

### Docker
```bash
# Logs do PostgreSQL
docker-compose logs -f db

# Logs do Redis
docker-compose logs -f redis
```

## 🐛 Solução de Problemas Comuns

### Erro: "Connection refused" no banco de dados

```bash
# Verificar se PostgreSQL está rodando
docker-compose ps

# Ou se usando instalação local
sudo systemctl status postgresql  # Linux
brew services list  # macOS
```

### Erro: "Module not found" no Python

```bash
# Certifique-se de que o venv está ativado
# E que todas as dependências foram instaladas
pip install -r requirements.txt
```

### Erro: "Port already in use"

```bash
# Verificar qual processo está usando a porta
# Windows:
netstat -ano | findstr :8000
# Linux/Mac:
lsof -i :8000

# Parar o processo ou mudar a porta no código
```

### Erro: "OpenAI API key not found"

```bash
# Verificar se OPENAI_API_KEY está configurada no .env
# E se o arquivo .env está sendo carregado
```

### Erro: CORS no frontend

```bash
# Verificar se CORS_ORIGINS no .env inclui a URL do frontend
# Exemplo: http://localhost:5173
```

## 📊 Verificando Funcionalidades Específicas

### Sistema de Refinamento OpenAI

Para testar o sistema de refinamento:

1. Certifique-se de que `ENABLE_RESPONSE_REFINEMENT=true` no `.env`
2. Crie uma entrevista e analise uma resposta
3. Verifique os logs para ver o refinamento em ação:

```bash
# Os logs mostrarão tentativas de refinamento
grep "refinamento" logs/assistente_rh.log
```

### Cache de Respostas

Para verificar o cache:

1. Faça uma análise de resposta
2. Faça a mesma análise novamente
3. Verifique nos logs: "Cache hit para análise de resposta"

### Coleta de Dados para Fine-tuning

Para habilitar coleta:

```bash
# Adicione ao .env
ENABLE_FINETUNING_COLLECTION=true
FINETUNING_DATA_DIR=./data/finetuning
```

Os dados serão salvos em `data/finetuning/` organizados por categoria.

## 🧹 Limpeza

### Parar Serviços Docker

```bash
docker-compose down

# Para remover volumes também (apaga dados)
docker-compose down -v
```

### Limpar Ambiente Python

```bash
# Desativar venv
deactivate

# Remover venv (opcional)
rm -rf venv
```

## 📝 Próximos Passos

Após testar localmente:

1. ✅ Verificar todas as funcionalidades básicas
2. ✅ Testar integração com OpenAI
3. ✅ Verificar sistema de refinamento
4. ✅ Testar criação de candidatos e entrevistas
5. ✅ Verificar logs e métricas

## 🔗 Links Úteis

- **Documentação da API**: http://localhost:8000/docs (se disponível)
- **Health Check Avançado**: http://localhost:8000/api/health/advanced
- **Frontend**: http://localhost:5173

## 💡 Dicas

1. **Use variáveis de ambiente**: Nunca commite arquivos `.env`
2. **Mantenha logs**: Configure logging adequado para debug
3. **Teste incrementalmente**: Teste uma funcionalidade por vez
4. **Use Postman/Insomnia**: Para testar APIs facilmente
5. **Monitore recursos**: Use `docker stats` para ver uso de recursos

---

**Problemas?** Consulte a documentação em `/docs/` ou verifique os logs.

