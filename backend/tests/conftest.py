# backend/tests/conftest.py
"""
Configuração de testes com fixtures e setup
"""
import json
import os
import tempfile
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from flask import Flask

from src.main import create_app
from src.models import db
from src.models.user import User
from src.models.candidate import Candidate
from src.models.interview import Interview

@pytest.fixture(scope='session')
def app():
    """Cria aplicação Flask para testes"""
    # Configurar banco de dados de teste
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'JWT_SECRET_KEY': 'test-secret-key',
        'OPENAI_API_KEY': 'test-openai-key',
        'REDIS_URL': 'redis://localhost:6379/1',  # DB diferente para testes
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """Cliente de teste Flask"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Runner CLI para testes"""
    return app.test_cli_runner()

@pytest.fixture
def db_session(app):
    """Sessão de banco de dados para testes"""
    with app.app_context():
        db.session.begin()
        yield db.session
        db.session.rollback()

@pytest.fixture
def sample_user(db_session):
    """Usuário de exemplo para testes"""
    user = User(
        email='test@example.com',
        full_name='Test User',
        role='recruiter',
        is_verified=True
    )
    user.set_password('test123')
    
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def admin_user(db_session):
    """Usuário administrador para testes"""
    user = User(
        email='admin@example.com',
        full_name='Admin User',
        role='admin',
        is_verified=True
    )
    user.set_password('admin123')
    
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def sample_candidate(db_session, sample_user):
    """Candidato de exemplo para testes"""
    candidate = Candidate(
        full_name='João Silva',
        email='joao@example.com',
        phone='11999999999',
        position_applied='Desenvolvedor Python',
        experience_years=3,
        current_company='Tech Corp',
        current_position='Desenvolvedor Jr',
        recruiter_id=sample_user.id,
        status='novo'
    )
    candidate.set_skills_list(['Python', 'Flask', 'PostgreSQL'])
    
    db_session.add(candidate)
    db_session.commit()
    return candidate

@pytest.fixture
def sample_interview(db_session, sample_candidate, sample_user):
    """Entrevista de exemplo para testes"""
    interview = Interview(
        candidate_id=sample_candidate.id,
        interviewer_id=sample_user.id,
        position='Desenvolvedor Python',
        interview_type='audio',
        status='agendada',
        total_questions=5
    )
    
    db_session.add(interview)
    db_session.commit()
    return interview

@pytest.fixture
def auth_headers(client, sample_user):
    """Headers de autenticação para testes"""
    token = sample_user.generate_token()
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def admin_auth_headers(client, admin_user):
    """Headers de autenticação de admin para testes"""
    token = admin_user.generate_token()
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def mock_openai():
    """Mock do cliente OpenAI (SDK v1+) para testes.

    Onda 2 — item 3.5: antes mockávamos `openai.ChatCompletion.create`,
    removido em `openai>=1.0`. Agora substituímos o singleton em
    `src.config.openai_config.get_openai_client` por um fake com shape
    compatível com `client.chat.completions.create(...)`, retornando um
    payload JSON que bate com `AIAnalyzer.normalize_analysis`.
    """
    def _fake_create(**_kwargs):
        payload = {
            'relevance': 80,
            'technical_accuracy': 75,
            'communication': 82,
            'score': 4,
            'confidence': 0.8,
            'evidence_excerpt': 'trecho curto da resposta',
            'summary': 'resumo mock',
        }
        return SimpleNamespace(
            model='gpt-4o-mini',
            id='test-completion-id',
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=json.dumps(payload))
                )
            ],
        )

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=_fake_create)
        ),
        audio=SimpleNamespace(
            speech=SimpleNamespace(create=lambda **kw: SimpleNamespace(content=b'MOCK_AUDIO')),
            transcriptions=SimpleNamespace(create=lambda **kw: 'transcrição mock'),
        ),
    )

    with patch('src.config.openai_config.get_openai_client', return_value=fake_client):
        yield fake_client

@pytest.fixture
def mock_redis():
    """Mock do Redis para testes"""
    with patch('redis.from_url') as mock:
        redis_mock = Mock()
        redis_mock.ping.return_value = True
        redis_mock.set.return_value = True
        redis_mock.get.return_value = b'test_value'
        redis_mock.delete.return_value = 1
        redis_mock.info.return_value = {'used_memory': 1024, 'maxmemory': 10240}
        mock.return_value = redis_mock
        yield redis_mock

@pytest.fixture
def sample_audio_file():
    """Arquivo de áudio de exemplo para testes"""
    # Criar arquivo temporário simulando áudio
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        f.write(b'fake_audio_data' * 1000)  # Simular dados de áudio
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def mock_file_upload():
    """Mock de upload de arquivo para testes"""
    from werkzeug.datastructures import FileStorage
    from io import BytesIO
    
    return FileStorage(
        stream=BytesIO(b'fake_audio_data'),
        filename='test_audio.wav',
        content_type='audio/wav'
    )

# Fixtures para testes de performance
@pytest.fixture
def performance_data():
    """Dados de performance para testes"""
    return {
        'ai_processing_times': [0.5, 1.2, 0.8, 2.1, 1.5],
        'audio_processing_times': [0.3, 0.7, 0.4, 1.1, 0.6],
        'db_query_times': [0.05, 0.12, 0.08, 0.15, 0.09],
        'request_counts': {'GET_/candidates': 100, 'POST_/interviews': 50},
        'error_counts': {'GET_/candidates': 2, 'POST_/interviews': 1}
    }

# Fixtures para testes de segurança
@pytest.fixture
def malicious_payloads():
    """Payloads maliciosos para testes de segurança"""
    return {
        'sql_injection': ["'; DROP TABLE users; --", "1' OR '1'='1"],
        'xss': ["<script>alert('xss')</script>", "javascript:alert('xss')"],
        'path_traversal': ["../../../etc/passwd", "..\\..\\..\\windows\\system32\\config\\sam"],
        'command_injection': ["; ls -la", "| cat /etc/passwd"],
        'ldap_injection': ["*)(uid=*))(|(uid=*", "*)(|(password=*)"]
    }

# Configuração de logging para testes
@pytest.fixture(autouse=True)
def configure_test_logging():
    """Configura logging para testes"""
    import logging
    logging.getLogger().setLevel(logging.CRITICAL)  # Suprimir logs durante testes

# Fixture para limpar cache entre testes
@pytest.fixture(autouse=True)
def clear_cache():
    """Limpa cache entre testes"""
    yield
    # Limpar qualquer cache global se necessário
    pass

# Marcadores personalizados para categorizar testes
def pytest_configure(config):
    """Configuração de marcadores personalizados"""
    config.addinivalue_line("markers", "unit: marca testes unitários")
    config.addinivalue_line("markers", "integration: marca testes de integração")
    config.addinivalue_line("markers", "e2e: marca testes end-to-end")
    config.addinivalue_line("markers", "slow: marca testes lentos")
    config.addinivalue_line("markers", "security: marca testes de segurança")
    config.addinivalue_line("markers", "performance: marca testes de performance")

# Fixture para métricas de teste
@pytest.fixture
def test_metrics():
    """Coleta métricas durante os testes"""
    import time
    start_time = time.time()
    
    yield
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Log das métricas do teste (pode ser usado para análise)
    if duration > 1.0:  # Teste lento
        print(f"Slow test detected: {duration:.2f}s")

# Fixture para simulação de diferentes ambientes
@pytest.fixture(params=['development', 'staging', 'production'])
def environment(request):
    """Simula diferentes ambientes"""
    original_env = os.environ.get('ENVIRONMENT')
    os.environ['ENVIRONMENT'] = request.param
    
    yield request.param
    
    if original_env:
        os.environ['ENVIRONMENT'] = original_env
    else:
        os.environ.pop('ENVIRONMENT', None)

