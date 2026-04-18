#!/usr/bin/env python3
"""
Script de setup para o Apexus HR
Gera chaves seguras e configura o ambiente
"""

import os
import secrets
import sys
from pathlib import Path

def generate_secret_key():
    """Gera uma chave secreta segura"""
    return secrets.token_urlsafe(64)

def create_env_file():
    """Cria arquivo .env com configurações padrão"""
    env_content = f"""# Configurações de Banco de Dados
POSTGRES_DB=apexus_hr
POSTGRES_USER=postgres
POSTGRES_PASSWORD={generate_secret_key()[:32]}

# Configurações de Cache
REDIS_PASSWORD={generate_secret_key()[:32]}

# Configurações de Segurança
SECRET_KEY={generate_secret_key()}
JWT_SECRET_KEY={generate_secret_key()}

# Configurações de IA
OPENAI_API_KEY=sk-sua_chave_openai_real_aqui
OPENAI_API_BASE=https://api.openai.com/v1

# Configurações de Ambiente
ENVIRONMENT=development
DEBUG=true
TESTING=false

# Configurações de CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Configurações de Upload
MAX_UPLOAD_SIZE=100
UPLOAD_FOLDER=/app/uploads

# Configurações de Banco de Dados (Pool)
DB_POOL_SIZE=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
DB_MAX_OVERFLOW=20

# Configurações de Logging
LOG_LEVEL=INFO
LOG_SQL=false

# Configurações de Migrações
RUN_MIGRATIONS=true
"""
    
    env_file = Path('.env')
    if env_file.exists():
        print("⚠️  Arquivo .env já existe. Backup criado como .env.backup")
        env_file.rename('.env.backup')
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Arquivo .env criado com sucesso!")
    print("📝 Lembre-se de configurar sua OPENAI_API_KEY no arquivo .env")

def install_dependencies():
    """Instala dependências do Python"""
    print("📦 Instalando dependências...")
    os.system(f"{sys.executable} -m pip install -r requirements.txt")
    print("✅ Dependências instaladas!")

def main():
    """Função principal"""
    print("🚀 Configurando Apexus HR...")
    print()
    
    # Verificar se estamos no diretório correto
    if not Path('requirements.txt').exists():
        print("❌ Execute este script no diretório backend/")
        sys.exit(1)
    
    # Criar arquivo .env
    create_env_file()
    
    # Instalar dependências
    install_dependencies()
    
    print()
    print("🎉 Setup concluído!")
    print()
    print("📋 Próximos passos:")
    print("1. Configure sua OPENAI_API_KEY no arquivo .env")
    print("2. Execute: python src/main.py")
    print("3. Acesse: http://localhost:5000")

if __name__ == "__main__":
    main()

