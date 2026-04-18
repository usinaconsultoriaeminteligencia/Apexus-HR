#!/usr/bin/env python3
"""
Script de Verificação Automática - Assistente RH
Verifica se todas as melhorias foram implementadas corretamente
"""

import os
import sys
import json
import time
import requests
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class SystemChecker:
    def __init__(self):
        self.results = []
        self.base_url = "http://localhost:5000"
        
    def log(self, message: str, status: str = "INFO"):
        color = Colors.GREEN if status == "PASS" else Colors.RED if status == "FAIL" else Colors.YELLOW
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{color}[{timestamp}] {status}: {message}{Colors.END}")
        
        self.results.append({
            "timestamp": timestamp,
            "status": status,
            "message": message
        })
    
    def run_command(self, command: str) -> Tuple[bool, str]:
        """Executa comando e retorna sucesso e output"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Timeout"
        except Exception as e:
            return False, str(e)
    
    def check_docker(self) -> bool:
        """Verifica se Docker está funcionando"""
        self.log("Verificando Docker...", "INFO")
        
        success, output = self.run_command("docker --version")
        if not success:
            self.log("Docker não está instalado ou não está funcionando", "FAIL")
            return False
        
        success, output = self.run_command("docker info")
        if not success:
            self.log("Docker não está rodando", "FAIL")
            return False
        
        self.log("Docker está funcionando corretamente", "PASS")
        return True
    
    def check_docker_compose(self) -> bool:
        """Verifica se Docker Compose está funcionando"""
        self.log("Verificando Docker Compose...", "INFO")
        
        success, output = self.run_command("docker-compose --version")
        if not success:
            self.log("Docker Compose não está instalado", "FAIL")
            return False
        
        self.log("Docker Compose está funcionando", "PASS")
        return True
    
    def check_env_file(self) -> bool:
        """Verifica se arquivo .env existe e tem variáveis obrigatórias"""
        self.log("Verificando arquivo .env...", "INFO")
        
        if not os.path.exists(".env"):
            self.log("Arquivo .env não encontrado", "FAIL")
            return False
        
        # Verificar variáveis obrigatórias
        required_vars = [
            "POSTGRES_PASSWORD",
            "REDIS_PASSWORD", 
            "SECRET_KEY",
            "JWT_SECRET_KEY",
            "OPENAI_API_KEY"
        ]
        
        missing_vars = []
        try:
            with open(".env", "r") as f:
                env_content = f.read()
                
            for var in required_vars:
                if f"{var}=" not in env_content or f"{var}=ALTERE" in env_content:
                    missing_vars.append(var)
        except Exception as e:
            self.log(f"Erro ao ler .env: {e}", "FAIL")
            return False
        
        if missing_vars:
            self.log(f"Variáveis não configuradas: {', '.join(missing_vars)}", "FAIL")
            return False
        
        self.log("Arquivo .env configurado corretamente", "PASS")
        return True
    
    def check_containers(self) -> bool:
        """Verifica se containers estão rodando"""
        self.log("Verificando containers...", "INFO")
        
        success, output = self.run_command("docker-compose -f docker-compose.production.yml ps")
        if not success:
            self.log("Erro ao verificar containers", "FAIL")
            return False
        
        # Verificar se containers principais estão "Up"
        required_containers = ["db", "redis", "backend"]
        containers_up = 0
        
        for container in required_containers:
            if container in output and "Up" in output:
                containers_up += 1
        
        if containers_up < len(required_containers):
            self.log(f"Apenas {containers_up}/{len(required_containers)} containers estão rodando", "FAIL")
            return False
        
        self.log("Todos os containers estão rodando", "PASS")
        return True
    
    def check_health_endpoint(self) -> bool:
        """Verifica se endpoint de health está funcionando"""
        self.log("Verificando health check...", "INFO")
        
        try:
            response = requests.get(f"{self.base_url}/health/", timeout=10)
            
            if response.status_code != 200:
                self.log(f"Health check retornou status {response.status_code}", "FAIL")
                return False
            
            data = response.json()
            if data.get("status") != "healthy":
                self.log(f"Health check status: {data.get('status')}", "FAIL")
                return False
            
            self.log("Health check está funcionando", "PASS")
            return True
            
        except requests.exceptions.RequestException as e:
            self.log(f"Erro ao acessar health check: {e}", "FAIL")
            return False
    
    def check_detailed_health(self) -> bool:
        """Verifica health check detalhado"""
        self.log("Verificando health check detalhado...", "INFO")
        
        try:
            response = requests.get(f"{self.base_url}/health/detailed", timeout=15)
            
            if response.status_code not in [200, 503]:
                self.log(f"Health detalhado retornou status {response.status_code}", "FAIL")
                return False
            
            data = response.json()
            checks = data.get("checks", {})
            
            # Verificar checks críticos
            critical_checks = ["database", "dependencies"]
            failed_checks = []
            
            for check_name in critical_checks:
                if check_name in checks and checks[check_name].get("status") == "critical":
                    failed_checks.append(check_name)
            
            if failed_checks:
                self.log(f"Checks críticos falharam: {', '.join(failed_checks)}", "FAIL")
                return False
            
            self.log("Health check detalhado está funcionando", "PASS")
            return True
            
        except requests.exceptions.RequestException as e:
            self.log(f"Erro ao acessar health detalhado: {e}", "FAIL")
            return False
    
    def check_metrics_endpoint(self) -> bool:
        """Verifica se endpoint de métricas está funcionando"""
        self.log("Verificando métricas...", "INFO")
        
        try:
            response = requests.get(f"{self.base_url}/health/metrics", timeout=10)
            
            if response.status_code != 200:
                self.log(f"Métricas retornaram status {response.status_code}", "FAIL")
                return False
            
            data = response.json()
            
            # Verificar se tem dados essenciais
            required_keys = ["system", "application", "timestamp"]
            missing_keys = [key for key in required_keys if key not in data]
            
            if missing_keys:
                self.log(f"Métricas faltando: {', '.join(missing_keys)}", "FAIL")
                return False
            
            self.log("Métricas estão funcionando", "PASS")
            return True
            
        except requests.exceptions.RequestException as e:
            self.log(f"Erro ao acessar métricas: {e}", "FAIL")
            return False
    
    def check_api_info(self) -> bool:
        """Verifica endpoint de informações da API"""
        self.log("Verificando API info...", "INFO")
        
        try:
            response = requests.get(f"{self.base_url}/info", timeout=10)
            
            if response.status_code != 200:
                self.log(f"API info retornou status {response.status_code}", "FAIL")
                return False
            
            data = response.json()
            
            if data.get("name") != "Assistente de RH":
                self.log("API info não retornou nome correto", "FAIL")
                return False
            
            self.log("API info está funcionando", "PASS")
            return True
            
        except requests.exceptions.RequestException as e:
            self.log(f"Erro ao acessar API info: {e}", "FAIL")
            return False
    
    def check_security_headers(self) -> bool:
        """Verifica se headers de segurança estão presentes"""
        self.log("Verificando headers de segurança...", "INFO")
        
        try:
            response = requests.get(f"{self.base_url}/health/", timeout=10)
            headers = response.headers
            
            security_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options", 
                "X-XSS-Protection",
                "Content-Security-Policy"
            ]
            
            missing_headers = [h for h in security_headers if h not in headers]
            
            if missing_headers:
                self.log(f"Headers de segurança faltando: {', '.join(missing_headers)}", "FAIL")
                return False
            
            self.log("Headers de segurança estão presentes", "PASS")
            return True
            
        except requests.exceptions.RequestException as e:
            self.log(f"Erro ao verificar headers: {e}", "FAIL")
            return False
    
    def check_files_structure(self) -> bool:
        """Verifica se arquivos importantes foram criados"""
        self.log("Verificando estrutura de arquivos...", "INFO")
        
        required_files = [
            "backend/src/monitoring/metrics.py",
            "backend/src/monitoring/logging_config.py",
            "backend/src/security/middleware.py",
            "backend/src/routes/health_advanced.py",
            "backend/tests/conftest.py",
            "backend/Dockerfile.production",
            "docker-compose.production.yml",
            "scripts/deploy.sh"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            self.log(f"Arquivos faltando: {', '.join(missing_files)}", "FAIL")
            return False
        
        self.log("Estrutura de arquivos está correta", "PASS")
        return True
    
    def performance_test(self) -> bool:
        """Teste básico de performance"""
        self.log("Executando teste de performance...", "INFO")
        
        try:
            # Fazer 5 requisições e medir tempo
            times = []
            for i in range(5):
                start = time.time()
                response = requests.get(f"{self.base_url}/health/", timeout=5)
                end = time.time()
                
                if response.status_code == 200:
                    times.append(end - start)
                else:
                    self.log(f"Requisição {i+1} falhou", "FAIL")
                    return False
            
            avg_time = sum(times) / len(times)
            
            if avg_time > 1.0:  # Mais de 1 segundo
                self.log(f"Performance ruim: {avg_time:.2f}s média", "FAIL")
                return False
            
            self.log(f"Performance OK: {avg_time:.3f}s média", "PASS")
            return True
            
        except Exception as e:
            self.log(f"Erro no teste de performance: {e}", "FAIL")
            return False
    
    def run_all_checks(self) -> Dict:
        """Executa todas as verificações"""
        print(f"{Colors.BOLD}{Colors.BLUE}")
        print("=" * 60)
        print("  VERIFICAÇÃO AUTOMÁTICA - ASSISTENTE RH")
        print("  Versão Enterprise Ready")
        print("=" * 60)
        print(f"{Colors.END}")
        
        checks = [
            ("Docker", self.check_docker),
            ("Docker Compose", self.check_docker_compose),
            ("Arquivo .env", self.check_env_file),
            ("Estrutura de Arquivos", self.check_files_structure),
            ("Containers", self.check_containers),
            ("Health Check", self.check_health_endpoint),
            ("Health Detalhado", self.check_detailed_health),
            ("Métricas", self.check_metrics_endpoint),
            ("API Info", self.check_api_info),
            ("Headers Segurança", self.check_security_headers),
            ("Performance", self.performance_test)
        ]
        
        passed = 0
        total = len(checks)
        
        for check_name, check_func in checks:
            print(f"\n{Colors.BLUE}Executando: {check_name}{Colors.END}")
            try:
                if check_func():
                    passed += 1
                time.sleep(1)  # Pequena pausa entre checks
            except Exception as e:
                self.log(f"Erro inesperado em {check_name}: {e}", "FAIL")
        
        # Resultado final
        print(f"\n{Colors.BOLD}{'=' * 60}{Colors.END}")
        
        if passed == total:
            print(f"{Colors.GREEN}{Colors.BOLD}✅ TODOS OS TESTES PASSARAM! ({passed}/{total}){Colors.END}")
            print(f"{Colors.GREEN}🚀 SISTEMA PRONTO PARA INVESTIDOR!{Colors.END}")
            status = "SUCCESS"
        elif passed >= total * 0.8:  # 80% ou mais
            print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  MAIORIA DOS TESTES PASSOU ({passed}/{total}){Colors.END}")
            print(f"{Colors.YELLOW}🔧 PEQUENOS AJUSTES NECESSÁRIOS{Colors.END}")
            status = "WARNING"
        else:
            print(f"{Colors.RED}{Colors.BOLD}❌ MUITOS TESTES FALHARAM ({passed}/{total}){Colors.END}")
            print(f"{Colors.RED}🛠️  CORREÇÕES NECESSÁRIAS{Colors.END}")
            status = "FAIL"
        
        print(f"{Colors.BOLD}{'=' * 60}{Colors.END}")
        
        return {
            "status": status,
            "passed": passed,
            "total": total,
            "percentage": (passed / total) * 100,
            "results": self.results,
            "timestamp": datetime.now().isoformat()
        }

def main():
    checker = SystemChecker()
    
    # Verificar se estamos no diretório correto
    if not os.path.exists("docker-compose.production.yml"):
        print(f"{Colors.RED}❌ Execute este script no diretório raiz do projeto!{Colors.END}")
        sys.exit(1)
    
    # Executar verificações
    result = checker.run_all_checks()
    
    # Salvar relatório
    with open("relatorio_verificacao.json", "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n{Colors.BLUE}📄 Relatório salvo em: relatorio_verificacao.json{Colors.END}")
    
    # Exit code baseado no resultado
    if result["status"] == "SUCCESS":
        sys.exit(0)
    elif result["status"] == "WARNING":
        sys.exit(1)
    else:
        sys.exit(2)

if __name__ == "__main__":
    main()

