# 📁 Arquivos .env - Qual está sendo utilizado?

## 🔍 Arquivos .env encontrados

Existem **3 arquivos .env** no projeto:

1. **`.env`** (raiz do projeto) - Criado pelo script de setup
2. **`backend/.env`** (diretório backend) - Arquivo existente
3. **`frontend/.env.local`** (diretório frontend) - Para configurações do frontend

## 🎯 Qual está sendo utilizado?

### Backend (Python/Flask)

O backend **NÃO está carregando automaticamente** arquivos `.env` atualmente. O código usa `os.getenv()` diretamente, que lê apenas variáveis de ambiente do sistema.

**Ordem de precedência:**
1. **Variáveis de ambiente do sistema** (mais alta prioridade)
2. Valores padrão no código

### Frontend (React/Vite)

O frontend usa **`frontend/.env.local`** que é carregado automaticamente pelo Vite.

## ⚠️ Problema Atual

Como o backend não está carregando o `.env` automaticamente, você precisa:

### Opção 1: Carregar manualmente (Recomendado)

Adicione no início de `backend/src/main.py`:

```python
from dotenv import load_dotenv
import os

# Carregar .env da raiz do projeto ou do diretório backend
load_dotenv()  # Tenta carregar .env na raiz
load_dotenv(dotenv_path='.env')  # Ou especifique o caminho
```

### Opção 2: Usar variáveis de ambiente do sistema

Configure as variáveis no sistema operacional ou no terminal antes de executar.

### Opção 3: Usar o .env do backend

Se você tem `backend/.env`, pode carregar especificamente ele:

```python
from dotenv import load_dotenv
load_dotenv(dotenv_path='backend/.env')
```

## 📋 Recomendação

### Para desenvolvimento local:

1. **Use `.env` na raiz** (criado pelo script de setup)
2. **Adicione `load_dotenv()` no `main.py`** para carregar automaticamente
3. **Mantenha `frontend/.env.local`** para o frontend

### Estrutura recomendada:

```
RH_Solution/
├── .env                    ← Backend (carregado por load_dotenv())
├── backend/
│   └── .env.example       ← Exemplo apenas
└── frontend/
    └── .env.local         ← Frontend (carregado pelo Vite)
```

## 🔧 Como corrigir

### Passo 1: Adicionar load_dotenv() no main.py

```python
# No início de backend/src/main.py, após os imports
from dotenv import load_dotenv

# Carregar .env da raiz do projeto
load_dotenv()
```

### Passo 2: Verificar qual .env usar

- Se você tem `.env` na raiz → use ele
- Se você tem `backend/.env` → pode usar ele também
- **Não use ambos** para evitar confusão

### Passo 3: Consolidar em um único .env

Recomendo manter apenas **`.env` na raiz** e remover `backend/.env` para evitar duplicação.

## 🧪 Como verificar qual está sendo usado

Execute no terminal Python:

```python
import os
from dotenv import load_dotenv

load_dotenv()
print("DATABASE_URL:", os.getenv('DATABASE_URL'))
print("OPENAI_API_KEY:", os.getenv('OPENAI_API_KEY')[:10] + "...")
```

## 📝 Resumo

| Arquivo | Localização | Usado por | Carregado automaticamente? |
|---------|-------------|-----------|---------------------------|
| `.env` | Raiz | Backend | ❌ Não (precisa `load_dotenv()`) |
| `backend/.env` | Backend | Backend | ❌ Não (precisa `load_dotenv()`) |
| `frontend/.env.local` | Frontend | Frontend | ✅ Sim (Vite) |

**Ação necessária:** Adicionar `load_dotenv()` no `main.py` para carregar o `.env` automaticamente.

