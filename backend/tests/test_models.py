# backend/tests/test_models.py
"""
Testes unitários para modelos de dados
"""
import pytest
from datetime import datetime, timedelta
import json
from src.models.user import User
from src.models.candidate import Candidate
from src.models.interview import Interview

@pytest.mark.unit
class TestUserModel:
    """Testes para o modelo User"""
    
    def test_create_user(self, db_session):
        """Testa criação de usuário"""
        user = User(
            email='test@example.com',
            full_name='Test User',
            role='recruiter'
        )
        user.set_password('password123')
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == 'test@example.com'
        assert user.full_name == 'Test User'
        assert user.role == 'recruiter'
        assert user.check_password('password123')
        assert not user.check_password('wrong_password')
    
    def test_password_hashing(self):
        """Testa hash de senha"""
        user = User(email='test@example.com', full_name='Test')
        user.set_password('secret123')
        
        assert user.password_hash != 'secret123'
        assert user.check_password('secret123')
        assert not user.check_password('wrong')
    
    def test_token_generation(self, sample_user):
        """Testa geração de token JWT"""
        token = sample_user.generate_token()
        
        assert token is not None
        assert isinstance(token, str)
        
        # Verificar se o token pode ser decodificado
        payload = User.verify_token(token)
        assert payload is not None
        assert payload['user_id'] == sample_user.id
        assert payload['email'] == sample_user.email
    
    def test_token_expiration(self, sample_user):
        """Testa expiração de token"""
        # Token com expiração muito curta
        token = sample_user.generate_token(expires_in=1)
        
        # Token deve ser válido imediatamente
        payload = User.verify_token(token)
        assert payload is not None
        
        # Aguardar expiração (simulado)
        import time
        time.sleep(2)
        
        # Token deve estar expirado
        payload = User.verify_token(token)
        assert payload is None
    
    def test_user_permissions(self, db_session):
        """Testa sistema de permissões"""
        admin = User(email='admin@test.com', full_name='Admin', role='admin')
        recruiter = User(email='rec@test.com', full_name='Recruiter', role='recruiter')
        viewer = User(email='view@test.com', full_name='Viewer', role='viewer')
        
        # Admin deve ter todas as permissões
        assert admin.has_permission('create')
        assert admin.has_permission('delete')
        assert admin.has_permission('manage_users')
        
        # Recruiter deve ter permissões limitadas
        assert recruiter.has_permission('create')
        assert recruiter.has_permission('conduct_interviews')
        assert not recruiter.has_permission('manage_users')
        
        # Viewer deve ter apenas leitura
        assert viewer.has_permission('read')
        assert not viewer.has_permission('create')
        assert not viewer.has_permission('delete')
    
    def test_failed_login_attempts(self, sample_user, db_session):
        """Testa bloqueio por tentativas de login falhadas"""
        # Simular 5 tentativas falhadas
        for _ in range(5):
            sample_user.record_failed_login()
        
        db_session.commit()
        
        assert sample_user.is_locked
        assert sample_user.is_account_locked()
        assert sample_user.login_attempts == '5'
    
    def test_successful_login_reset(self, sample_user, db_session):
        """Testa reset de tentativas após login bem-sucedido"""
        # Simular tentativas falhadas
        sample_user.record_failed_login()
        sample_user.record_failed_login()
        
        # Login bem-sucedido
        sample_user.record_login()
        db_session.commit()
        
        assert sample_user.login_attempts == '0'
        assert not sample_user.is_locked
        assert sample_user.last_login is not None
    
    def test_user_to_dict(self, sample_user):
        """Testa serialização do usuário"""
        user_dict = sample_user.to_dict()
        
        assert 'id' in user_dict
        assert 'email' in user_dict
        assert 'full_name' in user_dict
        assert 'role' in user_dict
        assert 'password_hash' not in user_dict  # Não deve expor senha
        
        # Teste com dados sensíveis
        sensitive_dict = sample_user.to_dict(include_sensitive=True)
        assert 'is_locked' in sensitive_dict
        assert 'login_attempts' in sensitive_dict

@pytest.mark.unit
class TestCandidateModel:
    """Testes para o modelo Candidate"""
    
    def test_create_candidate(self, db_session, sample_user):
        """Testa criação de candidato"""
        candidate = Candidate(
            full_name='João Silva',
            email='joao@example.com',
            position_applied='Desenvolvedor',
            recruiter_id=sample_user.id
        )
        
        db_session.add(candidate)
        db_session.commit()
        
        assert candidate.id is not None
        assert candidate.full_name == 'João Silva'
        assert candidate.email == 'joao@example.com'
        assert candidate.status == 'novo'
        assert candidate.overall_score == 0.0
    
    def test_skills_management(self, sample_candidate):
        """Testa gerenciamento de habilidades"""
        skills = ['Python', 'Flask', 'PostgreSQL', 'Docker']
        sample_candidate.set_skills_list(skills)
        
        retrieved_skills = sample_candidate.get_skills_list()
        assert retrieved_skills == skills
        
        # Teste com string
        sample_candidate.set_skills_list('JavaScript, React, Node.js')
        assert isinstance(sample_candidate.skills, str)
    
    def test_ai_analysis_management(self, sample_candidate):
        """Testa gerenciamento de análise de IA"""
        analysis = {
            'confidence': 85,
            'technical_skills': 90,
            'communication': 80,
            'cultural_fit': 88,
            'recommendation': 'CONTRATAR'
        }
        
        sample_candidate.set_ai_analysis_dict(analysis)
        retrieved_analysis = sample_candidate.get_ai_analysis_dict()
        
        assert retrieved_analysis == analysis
        assert retrieved_analysis['confidence'] == 85
    
    def test_score_calculation(self, sample_candidate, db_session):
        """Testa cálculo de score geral"""
        sample_candidate.technical_score = 85.0
        sample_candidate.behavioral_score = 90.0
        sample_candidate.cultural_fit_score = 80.0
        
        overall_score = sample_candidate.calculate_overall_score()
        
        # Score deve ser média ponderada
        expected_score = (85 * 0.4) + (90 * 0.3) + (80 * 0.3)
        assert abs(overall_score - expected_score) < 0.1
        assert sample_candidate.overall_score == overall_score
    
    def test_anonymization(self, sample_candidate, db_session):
        """Testa anonimização de dados (LGPD)"""
        original_name = sample_candidate.full_name
        original_email = sample_candidate.email
        
        sample_candidate.anonymize()
        db_session.commit()
        
        assert sample_candidate.anonymized
        assert sample_candidate.full_name != original_name
        assert sample_candidate.email != original_email
        assert 'Candidato_' in sample_candidate.full_name
        assert sample_candidate.phone is None
    
    def test_retention_policy(self, sample_candidate):
        """Testa política de retenção de dados"""
        retention_date = sample_candidate.get_retention_date()
        expected_date = sample_candidate.created_at + timedelta(days=5*365)
        
        assert retention_date == expected_date
    
    def test_should_be_anonymized(self, db_session, sample_user):
        """Testa lógica de anonimização automática"""
        # Candidato rejeitado há mais de 2 anos
        old_candidate = Candidate(
            full_name='Candidato Antigo',
            email='antigo@example.com',
            position_applied='Dev',
            status='rejeitado',
            recruiter_id=sample_user.id
        )
        old_candidate.created_at = datetime.utcnow() - timedelta(days=800)  # Mais de 2 anos
        
        db_session.add(old_candidate)
        db_session.commit()
        
        assert old_candidate.should_be_anonymized()
        
        # Candidato aprovado não deve ser anonimizado
        approved_candidate = Candidate(
            full_name='Candidato Aprovado',
            email='aprovado@example.com',
            position_applied='Dev',
            status='aprovado',
            recruiter_id=sample_user.id
        )
        approved_candidate.created_at = datetime.utcnow() - timedelta(days=800)
        
        db_session.add(approved_candidate)
        db_session.commit()
        
        assert not approved_candidate.should_be_anonymized()
    
    def test_status_display(self, sample_candidate):
        """Testa exibição de status"""
        sample_candidate.status = 'novo'
        assert sample_candidate.get_status_display() == 'Novo'
        
        sample_candidate.status = 'entrevista_realizada'
        assert sample_candidate.get_status_display() == 'Entrevista Realizada'
        
        sample_candidate.status = 'status_inexistente'
        assert sample_candidate.get_status_display() == 'status_inexistente'
    
    def test_candidate_to_dict(self, sample_candidate):
        """Testa serialização do candidato"""
        candidate_dict = sample_candidate.to_dict()
        
        assert 'id' in candidate_dict
        assert 'full_name' in candidate_dict
        assert 'position_applied' in candidate_dict
        assert 'overall_score' in candidate_dict
        assert 'skills' in candidate_dict
        assert isinstance(candidate_dict['skills'], list)
        
        # Teste com dados sensíveis
        sensitive_dict = sample_candidate.to_dict(include_sensitive=True)
        assert 'phone' in sensitive_dict
        assert 'current_company' in sensitive_dict

@pytest.mark.unit
class TestInterviewModel:
    """Testes para o modelo Interview"""
    
    def test_create_interview(self, db_session, sample_candidate, sample_user):
        """Testa criação de entrevista"""
        interview = Interview(
            candidate_id=sample_candidate.id,
            interviewer_id=sample_user.id,
            position='Desenvolvedor Python',
            interview_type='audio'
        )
        
        db_session.add(interview)
        db_session.commit()
        
        assert interview.id is not None
        assert interview.candidate_id == sample_candidate.id
        assert interview.interviewer_id == sample_user.id
        assert interview.status == 'agendada'
        assert interview.current_question_index == 0
    
    def test_questions_management(self, sample_interview):
        """Testa gerenciamento de perguntas"""
        questions = [
            {'question': 'Qual sua experiência com Python?', 'response': 'Trabalho há 3 anos'},
            {'question': 'Conhece Flask?', 'response': 'Sim, uso em projetos'}
        ]
        
        sample_interview.set_questions_list(questions)
        retrieved_questions = sample_interview.get_questions_list()
        
        assert len(retrieved_questions) == 2
        assert retrieved_questions[0]['question'] == 'Qual sua experiência com Python?'
        assert sample_interview.total_questions == 2
    
    def test_add_question_response(self, sample_interview):
        """Testa adição de pergunta e resposta"""
        sample_interview.add_question_response(
            question='Como você resolve problemas complexos?',
            response='Analiso o problema, divido em partes menores...',
            audio_path='/uploads/response_1.wav'
        )
        
        questions = sample_interview.get_questions_list()
        assert len(questions) == 1
        assert questions[0]['question'] == 'Como você resolve problemas complexos?'
        assert questions[0]['audio_path'] == '/uploads/response_1.wav'
        assert sample_interview.current_question_index == 1
    
    def test_voice_analysis_management(self, sample_interview):
        """Testa gerenciamento de análise de voz"""
        analysis = {
            'speech_rate': 150,  # palavras por minuto
            'pause_frequency': 0.3,
            'voice_stability': 0.85,
            'emotional_tone': 'confident'
        }
        
        sample_interview.set_voice_analysis_dict(analysis)
        retrieved_analysis = sample_interview.get_voice_analysis_dict()
        
        assert retrieved_analysis == analysis
        assert retrieved_analysis['speech_rate'] == 150
    
    def test_ai_insights_management(self, sample_interview):
        """Testa gerenciamento de insights de IA"""
        insights = {
            'key_strengths': ['Experiência técnica sólida', 'Boa comunicação'],
            'areas_for_improvement': ['Liderança de equipe'],
            'cultural_fit_indicators': ['Colaborativo', 'Proativo'],
            'red_flags': []
        }
        
        sample_interview.set_ai_insights_dict(insights)
        retrieved_insights = sample_interview.get_ai_insights_dict()
        
        assert retrieved_insights == insights
        assert len(retrieved_insights['key_strengths']) == 2
    
    def test_interview_lifecycle(self, sample_interview, db_session):
        """Testa ciclo de vida da entrevista"""
        # Iniciar entrevista
        sample_interview.start_interview()
        assert sample_interview.status == 'em_andamento'
        assert sample_interview.started_at is not None
        
        # Simular duração
        import time
        time.sleep(0.1)  # Pequena pausa para simular duração
        
        # Finalizar entrevista
        sample_interview.complete_interview()
        assert sample_interview.status == 'concluida'
        assert sample_interview.completed_at is not None
        assert sample_interview.duration_minutes >= 0
    
    def test_score_calculation(self, sample_interview, db_session):
        """Testa cálculo de scores da entrevista"""
        # Definir scores individuais
        sample_interview.confidence_score = 85.0
        sample_interview.enthusiasm_score = 90.0
        sample_interview.clarity_score = 88.0
        sample_interview.technical_accuracy = 82.0
        sample_interview.content_relevance = 86.0
        sample_interview.communication_skills = 87.0
        
        overall_score = sample_interview.calculate_overall_score()
        
        assert overall_score > 0
        assert sample_interview.overall_score == overall_score
        assert sample_interview.recommendation in ['CONTRATAR', 'CONSIDERAR', 'REJEITAR']
        assert 0 <= sample_interview.confidence_level <= 1
    
    def test_recommendation_logic(self, sample_interview):
        """Testa lógica de recomendação baseada nos limiares de score"""
        def _set_all_components(itv, value):
            itv.confidence_score = value
            itv.enthusiasm_score = value
            itv.clarity_score = value
            itv.technical_accuracy = value
            itv.content_relevance = value
            itv.communication_skills = value

        # Componentes altos (score geral >= 80) → CONTRATAR
        _set_all_components(sample_interview, 85.0)
        sample_interview.calculate_overall_score()
        assert sample_interview.recommendation == 'CONTRATAR'

        # Componentes médios (60 <= score geral < 80) → CONSIDERAR
        _set_all_components(sample_interview, 65.0)
        sample_interview.calculate_overall_score()
        assert sample_interview.recommendation == 'CONSIDERAR'

        # Componentes baixos (score geral < 60) → REJEITAR
        _set_all_components(sample_interview, 45.0)
        sample_interview.calculate_overall_score()
        assert sample_interview.recommendation == 'REJEITAR'
    
    def test_progress_calculation(self, sample_interview):
        """Testa cálculo de progresso"""
        sample_interview.total_questions = 10
        sample_interview.current_question_index = 0
        assert sample_interview.get_progress_percentage() == 0
        
        sample_interview.current_question_index = 5
        assert sample_interview.get_progress_percentage() == 50
        
        sample_interview.current_question_index = 10
        assert sample_interview.get_progress_percentage() == 100
        
        # Teste com mais perguntas que o total (não deve passar de 100%)
        sample_interview.current_question_index = 15
        assert sample_interview.get_progress_percentage() == 100
    
    def test_status_display(self, sample_interview):
        """Testa exibição de status"""
        sample_interview.status = 'agendada'
        assert sample_interview.get_status_display() == 'Agendada'
        
        sample_interview.status = 'em_andamento'
        assert sample_interview.get_status_display() == 'Em Andamento'
        
        sample_interview.status = 'concluida'
        assert sample_interview.get_status_display() == 'Concluída'
    
    def test_interview_to_dict(self, sample_interview):
        """Testa serialização da entrevista"""
        interview_dict = sample_interview.to_dict()
        
        assert 'id' in interview_dict
        assert 'candidate_id' in interview_dict
        assert 'interviewer_id' in interview_dict
        assert 'status' in interview_dict
        assert 'progress_percentage' in interview_dict
        assert 'overall_score' in interview_dict
        
        # Teste com dados detalhados
        detailed_dict = sample_interview.to_dict(include_detailed=True)
        assert 'questions_data' in detailed_dict
        assert 'voice_analysis' in detailed_dict
        assert 'ai_insights' in detailed_dict

@pytest.mark.unit
class TestModelRelationships:
    """Testes para relacionamentos entre modelos"""
    
    def test_user_candidate_relationship(self, db_session, sample_user):
        """Testa relacionamento User-Candidate"""
        candidate = Candidate(
            full_name='Test Candidate',
            email='candidate@test.com',
            position_applied='Developer',
            recruiter_id=sample_user.id
        )
        
        db_session.add(candidate)
        db_session.commit()
        
        assert candidate.recruiter == sample_user
        assert candidate.recruiter.email == sample_user.email
    
    def test_candidate_interview_relationship(self, db_session, sample_candidate, sample_user):
        """Testa relacionamento Candidate-Interview"""
        interview = Interview(
            candidate_id=sample_candidate.id,
            interviewer_id=sample_user.id,
            position='Test Position'
        )
        
        db_session.add(interview)
        db_session.commit()
        
        assert interview.candidate == sample_candidate
        assert interview.interviewer == sample_user
        assert interview.candidate.full_name == sample_candidate.full_name
    
    def test_cascade_operations(self, db_session, sample_user):
        """Testa operações em cascata"""
        candidate = Candidate(
            full_name='Test Cascade',
            email='cascade@test.com',
            position_applied='Developer',
            recruiter_id=sample_user.id
        )
        
        db_session.add(candidate)
        db_session.commit()
        
        candidate_id = candidate.id
        
        # Verificar se o candidato existe
        found_candidate = db_session.query(Candidate).filter_by(id=candidate_id).first()
        assert found_candidate is not None
        
        # Deletar candidato
        db_session.delete(candidate)
        db_session.commit()
        
        # Verificar se foi deletado
        found_candidate = db_session.query(Candidate).filter_by(id=candidate_id).first()
        assert found_candidate is None

