#!/usr/bin/env python3
"""
Script para executar migrações do banco de dados
Uso: python migrate.py
"""
import os
import sys
from pathlib import Path

# Adicionar o diretório backend ao PYTHONPATH
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Carregar variáveis de ambiente (opcional)
try:
    from dotenv import load_dotenv
    
    # Tentar carregar .env da raiz primeiro, depois do backend
    env_path_root = backend_dir.parent / '.env'
    env_path_backend = backend_dir / '.env'
    
    if env_path_root.exists():
        load_dotenv(dotenv_path=env_path_root)
        print(f"✓ Carregando .env da raiz: {env_path_root}")
    elif env_path_backend.exists():
        load_dotenv(dotenv_path=env_path_backend)
        print(f"✓ Carregando .env do backend: {env_path_backend}")
    else:
        load_dotenv()
        print("⚠️  Nenhum arquivo .env encontrado, usando variáveis de ambiente do sistema")
except ImportError:
    print("⚠️  python-dotenv não instalado, usando apenas variáveis de ambiente do sistema")

# Configurar DATABASE_URL se não estiver definido
if not os.getenv('DATABASE_URL'):
    # Tentar construir DATABASE_URL a partir das variáveis individuais
    postgres_user = os.getenv('POSTGRES_USER', 'postgres')
    postgres_password = os.getenv('POSTGRES_PASSWORD', 'postgres')
    postgres_db = os.getenv('POSTGRES_DB', 'apexus_hr')
    postgres_host = os.getenv('POSTGRES_HOST', 'localhost')
    postgres_port = os.getenv('POSTGRES_PORT', '5432')
    
    db_url = f'postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}'
    os.environ['DATABASE_URL'] = db_url
    print(f"✓ DATABASE_URL construido: postgresql://{postgres_user}:***@{postgres_host}:{postgres_port}/{postgres_db}")
else:
    db_url = os.getenv('DATABASE_URL')
    # Mascarar senha para exibição
    if '@' in db_url and ':' in db_url.split('@')[0]:
        masked_url = db_url.split('@')[0].split(':')[0] + ':***@' + '@'.join(db_url.split('@')[1:])
        print(f"✓ DATABASE_URL do ambiente: {masked_url}")
    else:
        print(f"✓ DATABASE_URL do ambiente configurado")

# Importar e criar a aplicação
from src.main import create_app

app, _ = create_app()

# Executar migrações
if __name__ == '__main__':
    import sys
    from flask_migrate import upgrade, current, history
    
    with app.app_context():
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == 'upgrade':
                print("Executando migracoes...")
                upgrade()
                print("OK: Migracoes aplicadas com sucesso!")
                
            elif command == 'current':
                print("Versao atual do banco:")
                current()
                
            elif command == 'history':
                print("Historico de migracoes:")
                history()
                
            else:
                print(f"ERRO: Comando desconhecido: {command}")
                print("Comandos disponiveis: upgrade, current, history")
        else:
            # Padrão: executar upgrade
            print("Executando migracoes...")
            upgrade()
            print("OK: Migracoes aplicadas com sucesso!")

