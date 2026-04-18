# 📦 Guia de Instalação - Assistente RH Inteligente

## 🎯 Pré-requisitos

### Obrigatórios
- **Docker** 20.10+ e **Docker Compose** 2.0+
- **Git** para clonagem do repositório
- **Chave da OpenAI API** para funcionalidades de IA

### Recomendados para Desenvolvimento
- **Python** 3.11+
- **Node.js** 18+
- **PostgreSQL** 15+ (se não usar Docker)

## 🚀 Instalação Rápida (Recomendada)

### 1. Clone o Repositório
```bash
git clone <repository-url>
cd ASSISTENTE_RH_FINAL
```

### 2. Execute o Setup Automatizado
```bash
./scripts/setup.sh
```

### 3. Configure as Variáveis de Ambiente
Edite o arquivo `.env` criado automaticamente:
```bash
# Substitua pela sua chave real da OpenAI
OPENAI_API_KEY=sk-your-actual-openai-key-here
```

### 4. Inicie os Serviços
```bash
cd docker
docker-compose up -d
```

### 5. Acesse o Sistema
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **Documentação**: http://localhost:5000/docs

## 🛠️ Instalação Manual

### Backend (Python/Flask)

1. **Criar ambiente virtual**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

2. **Instalar dependências**
```bash
pip install -r requirements.txt
```

3. **Configurar banco de dados**
```bash
export DATABASE_URL=postgresql://user:password@localhost:5432/assistente_rh
flask db upgrade
```

4. **Iniciar servidor**
```bash
python src/main.py
```

### Frontend (React)

1. **Instalar dependências**
```bash
cd frontend
npm install
```

2. **Configurar variáveis de ambiente**
```bash
echo "REACT_APP_API_URL=http://localhost:5000" > .env
```

3. **Iniciar servidor de desenvolvimento**
```bash
npm run dev
```

### Banco de Dados (PostgreSQL)

1. **Instalar PostgreSQL**
```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql
```

2. **Criar banco e usuário**
```sql
CREATE DATABASE assistente_rh;
CREATE USER assistente_rh_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE assistente_rh TO assistente_rh_user;
```

## 🔧 Configuração Avançada

### Variáveis de Ambiente Completas

Crie um arquivo `.env` na raiz do projeto:

```bash
# Banco de Dados
DATABASE_URL=postgresql://assistente_rh_user:secure_password@localhost:5432/assistente_rh
DB_PASSWORD=secure_password

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=redis_password

# OpenAI
OPENAI_API_KEY=sk-your-openai-key-here

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key

# Flask
FLASK_ENV=development
FLASK_DEBUG=True

# Frontend
REACT_APP_API_URL=http://localhost:5000
```

### Configuração de Produção

Para ambiente de produção, ajuste as seguintes configurações:

1. **Segurança**
```bash
FLASK_ENV=production
FLASK_DEBUG=False
JWT_SECRET_KEY=generate-a-strong-random-key
```

2. **Performance**
```bash
# Usar Gunicorn com múltiplos workers
gunicorn --bind 0.0.0.0:5000 --workers 4 src.main:app
```

3. **SSL/HTTPS**
Configure certificados SSL no Nginx ou use um proxy reverso.

## 🧪 Verificação da Instalação

### Teste do Backend
```bash
curl http://localhost:5000/health
# Resposta esperada: "Backend funcionando!"
```

### Teste do Frontend
Acesse http://localhost:3000 e verifique se a interface carrega corretamente.

### Teste da Integração
1. Acesse a página de "Entrevista por Áudio"
2. Preencha os dados do candidato
3. Inicie uma entrevista de teste

## 🐛 Solução de Problemas

### Erro de Conexão com Banco
```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Verificar conectividade
psql -h localhost -U assistente_rh_user -d assistente_rh
```

### Erro de Permissão de Áudio
- Certifique-se de que o navegador tem permissão para acessar o microfone
- Use HTTPS em produção (obrigatório para WebRTC)

### Erro da OpenAI API
- Verifique se a chave da API está correta
- Confirme se há créditos disponíveis na conta OpenAI
- Teste a conectividade: `curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models`

### Problemas de Performance
- Aumente o número de workers do Gunicorn
- Configure cache Redis adequadamente
- Otimize queries do banco de dados

## 📞 Suporte

Para problemas não resolvidos:
1. Consulte os logs: `docker-compose logs -f`
2. Verifique a documentação em `/docs/`
3. Entre em contato com a equipe de desenvolvimento

## 🔄 Atualizações

Para atualizar o sistema:
```bash
git pull origin main
docker-compose down
docker-compose up --build -d
```

