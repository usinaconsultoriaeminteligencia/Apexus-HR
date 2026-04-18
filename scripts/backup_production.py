#!/usr/bin/env python3
"""
Script de backup automático para produção
"""
import os
import sys
import subprocess
import datetime
import shutil
import gzip
import json
from pathlib import Path

class ProductionBackup:
    def __init__(self):
        self.backup_dir = Path("/backups")
        self.retention_days = int(os.getenv('BACKUP_RETENTION_DAYS', '30'))
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('POSTGRES_DB', 'assistente_rh'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD')
        }
    
    def create_backup_directory(self):
        """Cria diretório de backup se não existir"""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Diretório de backup: {self.backup_dir}")
    
    def backup_database(self):
        """Faz backup do banco de dados PostgreSQL"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"db_backup_{timestamp}.sql"
        
        # Comando pg_dump
        cmd = [
            'pg_dump',
            f"--host={self.db_config['host']}",
            f"--port={self.db_config['port']}",
            f"--username={self.db_config['user']}",
            f"--dbname={self.db_config['database']}",
            "--verbose",
            "--clean",
            "--if-exists",
            "--create",
            "--format=custom",
            f"--file={backup_file}"
        ]
        
        # Definir senha via variável de ambiente
        env = os.environ.copy()
        env['PGPASSWORD'] = self.db_config['password']
        
        try:
            print(f"🔄 Fazendo backup do banco de dados...")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Comprimir o backup
                compressed_file = f"{backup_file}.gz"
                with open(backup_file, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Remover arquivo não comprimido
                os.remove(backup_file)
                
                print(f"✅ Backup do banco salvo: {compressed_file}")
                return compressed_file
            else:
                print(f"❌ Erro no backup do banco: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao executar pg_dump: {e}")
            return None
    
    def backup_uploads(self):
        """Faz backup dos uploads"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        uploads_dir = Path("/app/uploads")
        backup_file = self.backup_dir / f"uploads_backup_{timestamp}.tar.gz"
        
        if not uploads_dir.exists():
            print("⚠️  Diretório de uploads não encontrado")
            return None
        
        try:
            print(f"🔄 Fazendo backup dos uploads...")
            subprocess.run([
                'tar', '-czf', str(backup_file), '-C', str(uploads_dir.parent), 'uploads'
            ], check=True)
            
            print(f"✅ Backup dos uploads salvo: {backup_file}")
            return backup_file
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro no backup dos uploads: {e}")
            return None
    
    def backup_logs(self):
        """Faz backup dos logs"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        logs_dir = Path("/app/logs")
        backup_file = self.backup_dir / f"logs_backup_{timestamp}.tar.gz"
        
        if not logs_dir.exists():
            print("⚠️  Diretório de logs não encontrado")
            return None
        
        try:
            print(f"🔄 Fazendo backup dos logs...")
            subprocess.run([
                'tar', '-czf', str(backup_file), '-C', str(logs_dir.parent), 'logs'
            ], check=True)
            
            print(f"✅ Backup dos logs salvo: {backup_file}")
            return backup_file
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro no backup dos logs: {e}")
            return None
    
    def cleanup_old_backups(self):
        """Remove backups antigos"""
        print(f"🧹 Limpando backups antigos (mais de {self.retention_days} dias)...")
        
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=self.retention_days)
        removed_count = 0
        
        for backup_file in self.backup_dir.glob("*"):
            if backup_file.is_file():
                file_time = datetime.datetime.fromtimestamp(backup_file.stat().st_mtime)
                if file_time < cutoff_date:
                    backup_file.unlink()
                    removed_count += 1
                    print(f"🗑️  Removido: {backup_file.name}")
        
        print(f"✅ {removed_count} backups antigos removidos")
    
    def create_backup_manifest(self, files):
        """Cria manifesto do backup"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        manifest_file = self.backup_dir / f"backup_manifest_{timestamp}.json"
        
        manifest = {
            'timestamp': timestamp,
            'backup_date': datetime.datetime.now().isoformat(),
            'files': [str(f) for f in files if f],
            'retention_days': self.retention_days,
            'total_size': sum(f.stat().st_size for f in files if f and Path(f).exists())
        }
        
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"✅ Manifesto criado: {manifest_file}")
        return manifest_file
    
    def run_full_backup(self):
        """Executa backup completo"""
        print("🚀 Iniciando backup de produção...")
        print("=" * 50)
        
        # Criar diretório de backup
        self.create_backup_directory()
        
        # Fazer backups
        db_backup = self.backup_database()
        uploads_backup = self.backup_uploads()
        logs_backup = self.backup_logs()
        
        # Criar manifesto
        backup_files = [db_backup, uploads_backup, logs_backup]
        manifest = self.create_backup_manifest(backup_files)
        
        # Limpeza de backups antigos
        self.cleanup_old_backups()
        
        print("=" * 50)
        print("✅ Backup completo finalizado!")
        print(f"📁 Localização: {self.backup_dir}")
        print(f"📊 Total de arquivos: {len([f for f in backup_files if f])}")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Uso: python backup_production.py")
        print("Variáveis de ambiente necessárias:")
        print("  POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD")
        print("  BACKUP_RETENTION_DAYS (opcional, padrão: 30)")
        return
    
    backup = ProductionBackup()
    backup.run_full_backup()

if __name__ == "__main__":
    main()
