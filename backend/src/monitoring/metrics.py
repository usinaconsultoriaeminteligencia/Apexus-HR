# backend/src/monitoring/metrics.py
"""
Sistema de métricas e monitoramento para produção
Implementa Prometheus metrics, APM e observabilidade
"""
import time
import functools
import psutil
import os
from datetime import datetime, timedelta, timezone
from collections import defaultdict, deque
from threading import Lock
from flask import request, g
import logging

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Coletor de métricas para monitoramento em produção"""
    
    def __init__(self):
        self.request_count = defaultdict(int)
        self.request_duration = defaultdict(list)
        self.error_count = defaultdict(int)
        self.active_connections = 0
        self.ai_processing_time = deque(maxlen=1000)
        self.audio_processing_time = deque(maxlen=1000)
        self.db_query_time = deque(maxlen=1000)
        self.lock = Lock()
        self.start_time = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Métricas de negócio
        self.interviews_completed = 0
        self.candidates_processed = 0
        self.ai_analysis_success_rate = deque(maxlen=100)
        
    def record_request(self, method, endpoint, status_code, duration):
        """Registra métricas de requisição HTTP"""
        with self.lock:
            key = f"{method}_{endpoint}"
            self.request_count[key] += 1
            self.request_duration[key].append(duration)
            
            if status_code >= 400:
                self.error_count[key] += 1
    
    def record_ai_processing(self, duration, success=True):
        """Registra tempo de processamento de IA"""
        with self.lock:
            self.ai_processing_time.append(duration)
            self.ai_analysis_success_rate.append(1 if success else 0)
    
    def record_audio_processing(self, duration):
        """Registra tempo de processamento de áudio"""
        with self.lock:
            self.audio_processing_time.append(duration)
    
    def record_db_query(self, duration):
        """Registra tempo de query no banco"""
        with self.lock:
            self.db_query_time.append(duration)
    
    def record_interview_completed(self):
        """Registra entrevista completada"""
        with self.lock:
            self.interviews_completed += 1
    
    def record_candidate_processed(self):
        """Registra candidato processado"""
        with self.lock:
            self.candidates_processed += 1
    
    def get_system_metrics(self):
        """Retorna métricas do sistema"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_usage_percent': cpu_percent,
                'memory_usage_percent': memory.percent,
                'memory_available_mb': memory.available / (1024 * 1024),
                'disk_usage_percent': disk.percent,
                'disk_free_gb': disk.free / (1024 * 1024 * 1024),
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
            }
        except Exception as e:
            logger.error(f"Erro ao coletar métricas do sistema: {e}")
            return {}
    
    def get_application_metrics(self):
        """Retorna métricas da aplicação"""
        with self.lock:
            uptime = (datetime.now(timezone.utc).replace(tzinfo=None) - self.start_time).total_seconds()
            
            # Calcular médias
            avg_ai_time = sum(self.ai_processing_time) / len(self.ai_processing_time) if self.ai_processing_time else 0
            avg_audio_time = sum(self.audio_processing_time) / len(self.audio_processing_time) if self.audio_processing_time else 0
            avg_db_time = sum(self.db_query_time) / len(self.db_query_time) if self.db_query_time else 0
            
            # Taxa de sucesso da IA
            ai_success_rate = sum(self.ai_analysis_success_rate) / len(self.ai_analysis_success_rate) if self.ai_analysis_success_rate else 1.0
            
            return {
                'uptime_seconds': uptime,
                'total_requests': sum(self.request_count.values()),
                'total_errors': sum(self.error_count.values()),
                'active_connections': self.active_connections,
                'interviews_completed': self.interviews_completed,
                'candidates_processed': self.candidates_processed,
                'avg_ai_processing_time_ms': avg_ai_time * 1000,
                'avg_audio_processing_time_ms': avg_audio_time * 1000,
                'avg_db_query_time_ms': avg_db_time * 1000,
                'ai_success_rate': ai_success_rate,
                'error_rate': sum(self.error_count.values()) / max(sum(self.request_count.values()), 1)
            }
    
    def get_endpoint_metrics(self):
        """Retorna métricas por endpoint"""
        with self.lock:
            endpoint_stats = {}
            
            for endpoint, count in self.request_count.items():
                durations = self.request_duration.get(endpoint, [])
                errors = self.error_count.get(endpoint, 0)
                
                if durations:
                    avg_duration = sum(durations) / len(durations)
                    p95_duration = sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 1 else durations[0]
                else:
                    avg_duration = 0
                    p95_duration = 0
                
                endpoint_stats[endpoint] = {
                    'request_count': count,
                    'error_count': errors,
                    'error_rate': errors / count if count > 0 else 0,
                    'avg_response_time_ms': avg_duration * 1000,
                    'p95_response_time_ms': p95_duration * 1000
                }
            
            return endpoint_stats
    
    def get_health_status(self):
        """Retorna status de saúde da aplicação"""
        system_metrics = self.get_system_metrics()
        app_metrics = self.get_application_metrics()
        
        # Determinar status baseado em thresholds
        status = "healthy"
        issues = []
        
        if system_metrics.get('cpu_usage_percent', 0) > 80:
            status = "warning"
            issues.append("High CPU usage")
        
        if system_metrics.get('memory_usage_percent', 0) > 85:
            status = "warning"
            issues.append("High memory usage")
        
        if app_metrics.get('error_rate', 0) > 0.05:  # 5% error rate
            status = "critical"
            issues.append("High error rate")
        
        if app_metrics.get('ai_success_rate', 1.0) < 0.9:  # 90% success rate
            status = "warning"
            issues.append("Low AI success rate")
        
        return {
            'status': status,
            'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            'issues': issues,
            'uptime_seconds': app_metrics.get('uptime_seconds', 0)
        }

# Instância global do coletor
metrics_collector = MetricsCollector()

def monitor_request(f):
    """Decorator para monitorar requisições HTTP"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = f(*args, **kwargs)
            status_code = getattr(result, 'status_code', 200)
        except Exception as e:
            status_code = 500
            raise
        finally:
            duration = time.time() - start_time
            endpoint = request.endpoint or 'unknown'
            method = request.method
            
            metrics_collector.record_request(method, endpoint, status_code, duration)
        
        return result
    
    return decorated_function

def monitor_ai_processing(f):
    """Decorator para monitorar processamento de IA"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        success = True
        
        try:
            result = f(*args, **kwargs)
            return result
        except Exception as e:
            success = False
            raise
        finally:
            duration = time.time() - start_time
            metrics_collector.record_ai_processing(duration, success)
    
    return decorated_function

def monitor_audio_processing(f):
    """Decorator para monitorar processamento de áudio"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = f(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            metrics_collector.record_audio_processing(duration)
    
    return decorated_function

def monitor_db_query(f):
    """Decorator para monitorar queries de banco"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = f(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            metrics_collector.record_db_query(duration)
    
    return decorated_function

class PerformanceMonitor:
    """Monitor de performance para operações críticas"""
    
    def __init__(self):
        self.thresholds = {
            'ai_processing_max_time': 30.0,  # 30 segundos
            'audio_processing_max_time': 10.0,  # 10 segundos
            'db_query_max_time': 5.0,  # 5 segundos
            'memory_usage_max': 85.0,  # 85%
            'cpu_usage_max': 80.0,  # 80%
            'error_rate_max': 0.05  # 5%
        }
    
    def check_performance_alerts(self):
        """Verifica se há alertas de performance"""
        alerts = []
        
        system_metrics = metrics_collector.get_system_metrics()
        app_metrics = metrics_collector.get_application_metrics()
        
        # Verificar CPU
        if system_metrics.get('cpu_usage_percent', 0) > self.thresholds['cpu_usage_max']:
            alerts.append({
                'type': 'cpu_high',
                'message': f"CPU usage is {system_metrics['cpu_usage_percent']:.1f}%",
                'severity': 'warning',
                'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
            })
        
        # Verificar memória
        if system_metrics.get('memory_usage_percent', 0) > self.thresholds['memory_usage_max']:
            alerts.append({
                'type': 'memory_high',
                'message': f"Memory usage is {system_metrics['memory_usage_percent']:.1f}%",
                'severity': 'warning',
                'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
            })
        
        # Verificar taxa de erro
        if app_metrics.get('error_rate', 0) > self.thresholds['error_rate_max']:
            alerts.append({
                'type': 'error_rate_high',
                'message': f"Error rate is {app_metrics['error_rate']:.2%}",
                'severity': 'critical',
                'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
            })
        
        # Verificar tempo de processamento de IA
        if app_metrics.get('avg_ai_processing_time_ms', 0) > self.thresholds['ai_processing_max_time'] * 1000:
            alerts.append({
                'type': 'ai_processing_slow',
                'message': f"AI processing time is {app_metrics['avg_ai_processing_time_ms']:.0f}ms",
                'severity': 'warning',
                'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
            })
        
        return alerts

# Instância global do monitor de performance
performance_monitor = PerformanceMonitor()

