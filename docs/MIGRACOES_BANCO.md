# 🗄️ Como Executar Migrações do Banco de Dados

## ⚠️ Problema Comum

Ao tentar executar `flask db upgrade`, você pode encontrar:

```
Error: Could not locate a Flask application.
Error: No such command 'db'.
```

## ✅ Solução

### Passo 1: Ativar o ambiente virtual

```powershell
cd backend
.\venv\Scripts\Activate.ps1
```

### Passo 2: Configurar variáveis de ambiente

```powershell
# Configurar DATABASE_URL
$env:DATABASE_URL='postgresql://postgres:postgres@localhost:5432/assistente_rh'

# Configurar FLASK_APP para o Flask encontrar a aplicação
$env:FLASK_APP='src.main:app'

# Opcional: Configurar PYTHONPATH
$env:PYTHONPATH='.'
```

### Passo 3: Executar migrações

```powershell
# Verificar se Flask-Migrate está instalado
pip show flask-migrate

# Se não estiver, instalar
pip install flask-migrate

# Executar migrações
flask db upgrade
```

## 🔧 Alternativa: Usar Python diretamente

Se o comando `flask db` não funcionar, você pode executar as migrações diretamente:

```powershell
# Ainda no diretório backend com venv ativado
python -m flask db upgrade
```

Ou criar um script Python:

```python
# migrate_db.py
import os
from src.main import create_app

os.environ['DATABASE_URL'] = 'postgresql://postgres:postgres@localhost:5432/assistente_rh'
app, _ = create_app()

with app.app_context():
    from flask_migrate import upgrade
    upgrade()
```

Execute:
```powershell
python migrate_db.py
```

## 📋 Comandos Úteis

### Verificar status das migrações

```powershell
flask db current
flask db history
```

### Criar nova migração

```powershell
flask db migrate -m "Descrição da migração"
```

### Aplicar migrações

```powershell
flask db upgrade
```

### Reverter migração

```powershell
flask db downgrade
```

## 🐛 Solução de Problemas

### Erro: "No such command 'db'"

**Causa:** Flask-Migrate não está instalado ou não está no PATH.

**Solução:**
```powershell
pip install flask-migrate
```

### Erro: "Could not locate a Flask application"

**Causa:** FLASK_APP não está configurado.

**Solução:**
```powershell
$env:FLASK_APP='src.main:app'
```

### Erro: "ModuleNotFoundError: No module named 'src'"

**Causa:** PYTHONPATH não está configurado.

**Solução:**
```powershell
$env:PYTHONPATH='.'
# Ou execute do diretório backend
cd backend
```

### Erro: "Connection refused" ou "could not connect"

**Causa:** PostgreSQL não está rodando ou DATABASE_URL está incorreto.

**Solução:**
```powershell
# Verificar se Docker está rodando
docker-compose ps

# Verificar DATABASE_URL
$env:DATABASE_URL='postgresql://postgres:postgres@localhost:5432/assistente_rh'
```

## 🚀 Script Completo (Copiar e Colar)

```powershell
# Ativar venv
cd backend
.\venv\Scripts\Activate.ps1

# Configurar variáveis
$env:DATABASE_URL='postgresql://postgres:postgres@localhost:5432/assistente_rh'
$env:FLASK_APP='src.main:app'
$env:PYTHONPATH='.'

# Verificar instalação
pip show flask-migrate

# Executar migrações
python -m flask db upgrade
```

## 📝 Notas

- Sempre execute migrações com o ambiente virtual ativado
- Certifique-se de que o PostgreSQL está rodando antes de executar
- O arquivo `.env` será carregado automaticamente se você configurou `load_dotenv()` no `main.py`

