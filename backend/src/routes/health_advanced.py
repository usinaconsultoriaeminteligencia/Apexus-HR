# backend/src/routes/health_advanced.py
"""
Health checks avançados para monitoramento de produção
Implementa verificações de dependências, métricas e alertas
"""
import os
import time
import psutil
from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify, request
from sqlalchemy import text
import redis
import requests
from src.models import db
from src.monitoring.metrics import metrics_collector, performance_monitor
from src.monitoring.logging_config import audit_logger, performance_logger
import logging

logger = logging.getLogger(__name__)

health_bp = Blueprint('health_advanced', __name__, url_prefix='/health')

class HealthChecker:
    """Classe para verificações de saúde da aplicação"""
    
    def __init__(self):
        self.checks = {
            'database': self.check_database,
            'redis': self.check_redis,
            'openai': self.check_openai_api,
            'disk_space': self.check_disk_space,
            'memory': self.check_memory,
            'cpu': self.check_cpu,
            'dependencies': self.check_dependencies
        }
    
    def check_database(self):
        """Verifica conectividade e performance do banco de dados"""
        try:
            start_time = time.time()
            
            # Teste de conectividade
            result = db.session.execute(text('SELECT 1'))
            result.fetchone()
            
            # Teste de performance - query simples
            db.session.execute(text('SELECT COUNT(*) FROM users'))
            
            duration = time.time() - start_time
            
            # Verificar se há conexões ativas demais
            active_connections = db.session.execute(
                text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
            ).scalar()
            
            status = 'healthy'
            issues = []
            
            if duration > 1.0:  # Mais de 1 segundo
                status = 'warning'
                issues.append(f'Slow database response: {duration:.2f}s')
            
            if active_connections > 50:  # Muitas conexões ativas
                status = 'warning'
                issues.append(f'High active connections: {active_connections}')
            
            return {
                'status': status,
                'response_time_ms': duration * 1000,
                'active_connections': active_connections,
                'issues': issues
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            error_type = type(e).__name__
            error_message = str(e)
            
            # Determinar tipo de erro para melhor diagnóstico
            if 'connection' in error_message.lower():
                issue = 'Database connection failed'
            elif 'timeout' in error_message.lower():
                issue = 'Database timeout'
            elif 'permission' in error_message.lower():
                issue = 'Database permission denied'
            else:
                issue = f'Database error: {error_type}'
            
            return {
                'status': 'critical',
                'error': error_message,
                'error_type': error_type,
                'issues': [issue]
            }
    
    def check_redis(self):
        """Verifica conectividade e performance do Redis"""
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            r = redis.from_url(redis_url)
            
            start_time = time.time()
            
            # Teste de conectividade
            r.ping()
            
            # Teste de escrita/leitura
            test_key = f'health_check_{int(time.time())}'
            r.set(test_key, 'test_value', ex=60)
            value = r.get(test_key)
            r.delete(test_key)
            
            duration = time.time() - start_time
            
            # Verificar uso de memória
            info = r.info('memory')
            memory_usage = info.get('used_memory', 0)
            max_memory = info.get('maxmemory', 0)
            
            status = 'healthy'
            issues = []
            
            if duration > 0.1:  # Mais de 100ms
                status = 'warning'
                issues.append(f'Slow Redis response: {duration:.3f}s')
            
            if max_memory > 0 and memory_usage / max_memory > 0.8:  # 80% da memória
                status = 'warning'
                issues.append(f'High Redis memory usage: {memory_usage/max_memory:.1%}')
            
            return {
                'status': status,
                'response_time_ms': duration * 1000,
                'memory_usage_bytes': memory_usage,
                'memory_usage_percent': (memory_usage / max_memory * 100) if max_memory > 0 else 0,
                'issues': issues
            }
            
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                'status': 'critical',
                'error': str(e),
                'issues': ['Redis connection failed']
            }
    
    def check_openai_api(self):
        """Verifica conectividade com a API da OpenAI"""
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return {
                    'status': 'warning',
                    'issues': ['OpenAI API key not configured']
                }
            
            start_time = time.time()
            
            # Teste simples de conectividade
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                'https://api.openai.com/v1/models',
                headers=headers,
                timeout=10
            )
            
            duration = time.time() - start_time
            
            status = 'healthy' if response.status_code == 200 else 'warning'
            issues = []
            
            if duration > 5.0:  # Mais de 5 segundos
                status = 'warning'
                issues.append(f'Slow OpenAI API response: {duration:.2f}s')
            
            if response.status_code != 200:
                issues.append(f'OpenAI API returned status {response.status_code}')
            
            return {
                'status': status,
                'response_time_ms': duration * 1000,
                'api_status_code': response.status_code,
                'issues': issues
            }
            
        except Exception as e:
            logger.error(f"OpenAI API health check failed: {e}")
            return {
                'status': 'critical',
                'error': str(e),
                'issues': ['OpenAI API connection failed']
            }
    
    def check_disk_space(self):
        """Verifica espaço em disco"""
        try:
            disk_usage = psutil.disk_usage('/')
            
            free_percent = (disk_usage.free / disk_usage.total) * 100
            used_percent = (disk_usage.used / disk_usage.total) * 100
            
            status = 'healthy'
            issues = []
            
            if free_percent < 10:  # Menos de 10% livre
                status = 'critical'
                issues.append(f'Very low disk space: {free_percent:.1f}% free')
            elif free_percent < 20:  # Menos de 20% livre
                status = 'warning'
                issues.append(f'Low disk space: {free_percent:.1f}% free')
            
            return {
                'status': status,
                'total_gb': disk_usage.total / (1024**3),
                'used_gb': disk_usage.used / (1024**3),
                'free_gb': disk_usage.free / (1024**3),
                'used_percent': used_percent,
                'free_percent': free_percent,
                'issues': issues
            }
            
        except Exception as e:
            logger.error(f"Disk space health check failed: {e}")
            return {
                'status': 'critical',
                'error': str(e),
                'issues': ['Disk space check failed']
            }
    
    def check_memory(self):
        """Verifica uso de memória"""
        try:
            memory = psutil.virtual_memory()
            
            status = 'healthy'
            issues = []
            
            if memory.percent > 90:  # Mais de 90% usado
                status = 'critical'
                issues.append(f'Very high memory usage: {memory.percent:.1f}%')
            elif memory.percent > 80:  # Mais de 80% usado
                status = 'warning'
                issues.append(f'High memory usage: {memory.percent:.1f}%')
            
            return {
                'status': status,
                'total_gb': memory.total / (1024**3),
                'used_gb': memory.used / (1024**3),
                'available_gb': memory.available / (1024**3),
                'used_percent': memory.percent,
                'issues': issues
            }
            
        except Exception as e:
            logger.error(f"Memory health check failed: {e}")
            return {
                'status': 'critical',
                'error': str(e),
                'issues': ['Memory check failed']
            }
    
    def check_cpu(self):
        """Verifica uso de CPU"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
            
            status = 'healthy'
            issues = []
            
            if cpu_percent > 90:  # Mais de 90% usado
                status = 'critical'
                issues.append(f'Very high CPU usage: {cpu_percent:.1f}%')
            elif cpu_percent > 80:  # Mais de 80% usado
                status = 'warning'
                issues.append(f'High CPU usage: {cpu_percent:.1f}%')
            
            # Verificar load average
            cpu_count = psutil.cpu_count()
            if load_avg[0] > cpu_count * 2:  # Load average muito alto
                status = 'warning'
                issues.append(f'High load average: {load_avg[0]:.2f}')
            
            return {
                'status': status,
                'cpu_percent': cpu_percent,
                'cpu_count': cpu_count,
                'load_average_1m': load_avg[0],
                'load_average_5m': load_avg[1],
                'load_average_15m': load_avg[2],
                'issues': issues
            }
            
        except Exception as e:
            logger.error(f"CPU health check failed: {e}")
            return {
                'status': 'critical',
                'error': str(e),
                'issues': ['CPU check failed']
            }
    
    def check_dependencies(self):
        """Verifica dependências críticas"""
        try:
            issues = []
            status = 'healthy'
            
            # Verificar variáveis de ambiente críticas
            required_env_vars = [
                'DATABASE_URL',
                'REDIS_URL',
                'OPENAI_API_KEY',
                'JWT_SECRET_KEY'
            ]
            
            missing_vars = []
            for var in required_env_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                status = 'critical'
                issues.append(f'Missing environment variables: {", ".join(missing_vars)}')
            
            # Verificar diretórios críticos
            critical_dirs = ['/app/uploads', '/app/logs']
            for directory in critical_dirs:
                if not os.path.exists(directory):
                    try:
                        os.makedirs(directory, exist_ok=True)
                    except Exception as e:
                        status = 'warning'
                        issues.append(f'Cannot create directory {directory}: {e}')
            
            return {
                'status': status,
                'environment_variables': {var: bool(os.getenv(var)) for var in required_env_vars},
                'directories': {d: os.path.exists(d) for d in critical_dirs},
                'issues': issues
            }
            
        except Exception as e:
            logger.error(f"Dependencies health check failed: {e}")
            return {
                'status': 'critical',
                'error': str(e),
                'issues': ['Dependencies check failed']
            }
    
    def run_all_checks(self):
        """Executa todas as verificações de saúde"""
        results = {}
        overall_status = 'healthy'
        all_issues = []
        
        for check_name, check_func in self.checks.items():
            try:
                result = check_func()
                results[check_name] = result
                
                # Determinar status geral
                if result['status'] == 'critical':
                    overall_status = 'critical'
                elif result['status'] == 'warning' and overall_status != 'critical':
                    overall_status = 'warning'
                
                # Coletar issues
                if 'issues' in result:
                    all_issues.extend(result['issues'])
                    
            except Exception as e:
                logger.error(f"Health check {check_name} failed: {e}")
                results[check_name] = {
                    'status': 'critical',
                    'error': str(e),
                    'issues': [f'{check_name} check failed']
                }
                overall_status = 'critical'
                all_issues.append(f'{check_name} check failed')
        
        return {
            'status': overall_status,
            'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z',
            'checks': results,
            'issues': all_issues,
            'summary': {
                'total_checks': len(self.checks),
                'healthy_checks': sum(1 for r in results.values() if r['status'] == 'healthy'),
                'warning_checks': sum(1 for r in results.values() if r['status'] == 'warning'),
                'critical_checks': sum(1 for r in results.values() if r['status'] == 'critical')
            }
        }

# Instância global do health checker
health_checker = HealthChecker()

@health_bp.route('/')
def health_simple():
    """Health check simples para load balancers"""
    try:
        # Verificação básica de banco
        db.session.execute(text('SELECT 1'))
        return {'status': 'healthy', 'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'}, 200
    except Exception as e:
        logger.error(f"Simple health check failed: {e}")
        return {'status': 'unhealthy', 'error': str(e)}, 503

@health_bp.route('/detailed')
def health_detailed():
    """Health check detalhado com todas as verificações"""
    result = health_checker.run_all_checks()
    
    # Log do resultado para auditoria
    audit_logger.log_user_action('health_check_detailed', details={
        'status': result['status'],
        'issues_count': len(result['issues'])
    })
    
    status_code = 200 if result['status'] == 'healthy' else 503
    return jsonify(result), status_code

@health_bp.route('/metrics')
def health_metrics():
    """Endpoint de métricas para monitoramento"""
    try:
        system_metrics = metrics_collector.get_system_metrics()
        app_metrics = metrics_collector.get_application_metrics()
        endpoint_metrics = metrics_collector.get_endpoint_metrics()
        health_status = metrics_collector.get_health_status()
        
        return jsonify({
            'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z',
            'system': system_metrics,
            'application': app_metrics,
            'endpoints': endpoint_metrics,
            'health': health_status
        }), 200
        
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
        return {'error': str(e)}, 500

@health_bp.route('/alerts')
def health_alerts():
    """Endpoint de alertas de performance"""
    try:
        alerts = performance_monitor.check_performance_alerts()
        
        return jsonify({
            'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z',
            'alerts': alerts,
            'alert_count': len(alerts),
            'has_critical_alerts': any(alert['severity'] == 'critical' for alert in alerts)
        }), 200
        
    except Exception as e:
        logger.error(f"Alerts endpoint failed: {e}")
        return {'error': str(e)}, 500

@health_bp.route('/readiness')
def health_readiness():
    """Readiness probe para Kubernetes"""
    try:
        # Verificar se a aplicação está pronta para receber tráfego
        checks = {
            'database': health_checker.check_database(),
            'redis': health_checker.check_redis(),
            'dependencies': health_checker.check_dependencies()
        }
        
        ready = all(check['status'] != 'critical' for check in checks.values())
        
        return jsonify({
            'ready': ready,
            'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z',
            'checks': checks
        }), 200 if ready else 503
        
    except Exception as e:
        logger.error(f"Readiness probe failed: {e}")
        return {'ready': False, 'error': str(e)}, 503

@health_bp.route('/liveness')
def health_liveness():
    """Liveness probe para Kubernetes"""
    try:
        # Verificação básica se a aplicação está viva
        return jsonify({
            'alive': True,
            'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z',
            'uptime_seconds': metrics_collector.get_application_metrics().get('uptime_seconds', 0)
        }), 200
        
    except Exception as e:
        logger.error(f"Liveness probe failed: {e}")
        return {'alive': False, 'error': str(e)}, 503

