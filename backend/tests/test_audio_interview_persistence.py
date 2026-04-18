"""Testes para Onda 2 — itens 3.2, 3.4c, 3.4d.

Cobre:
- Persistência de sessões do AudioInterviewService em `interviews`.
- Geração de `interview_assessments` auditáveis ao finalizar a entrevista.
- Fallback seguro (todos fallback -> recommendation=None).
- Endpoint GET /interviews/<id>/assessments com filtragem por papel.
"""
from __future__ import annotations

import uuid

import pytest
from unittest.mock import patch

from src.models import db
from src.models.assessment import InterviewAssessment
from src.models.candidate import Candidate
from src.models.interview import Interview
from src.models.user import User
from src.services.audio_interview_service import AudioInterviewService


# --- fixtures ------------------------------------------------------------

@pytest.fixture
def bootstrap_admin(db_session):
    """Garante um admin para ser 'interviewer' default do serviço.

    Idempotente: o DB de testes é compartilhado entre testes (conftest
    usa scope='session' para o app), então criamos só se ainda não
    existir um admin.
    """
    admin = db.session.query(User).filter(User.role == 'admin').first()
    if admin is None:
        admin = User(
            email='admin.service@example.com',
            full_name='Admin Service',
            role='admin',
            is_verified=True,
        )
        admin.set_password('admin')
        db_session.add(admin)
        db_session.commit()
    return admin


@pytest.fixture
def service(bootstrap_admin):
    """Instância fresca do serviço, sem cache entre testes."""
    return AudioInterviewService()


# --- helpers -------------------------------------------------------------

def _mock_analysis(score=4, model='openai:gpt-4o-mini'):
    return {
        'relevance': 80.0,
        'technical_accuracy': 75.0,
        'communication': 82.0,
        'score': score,
        'confidence': 0.8,
        'evidence_excerpt': 'trecho literal da resposta',
        'summary': 'resumo mock',
        'rubric_id': 'competencies.data_driven_decision',
        'rubric_version': '2026.04-v1',
        'dimension': 'data_driven_decision',
        'model_name': model,
        'model_version': 'gpt-4o-mini-2025',
        'prompt_hash': 'abc123def456',
        'human_review_status': 'pending',
    }


def _fallback_analysis():
    return {
        'relevance': None,
        'technical_accuracy': None,
        'communication': None,
        'score': None,
        'confidence': 0.0,
        'evidence_excerpt': 'trecho curto',
        'summary': 'Modelo indisponível.',
        'rubric_id': 'competencies.customer_orientation',
        'rubric_version': '2026.04-v1',
        'dimension': 'customer_orientation',
        'model_name': 'fallback',
        'model_version': None,
        'prompt_hash': None,
        'human_review_status': 'pending',
    }


# --- 3.2: persistência --------------------------------------------------

@pytest.mark.integration
class TestPersistence:
    def test_start_interview_persists_record_with_token(self, service, db_session):
        name = f'Maria Persistence {uuid.uuid4().hex[:6]}'
        res = service.start_interview(name, 'Desenvolvedor Backend')
        assert res['success'] is True
        token = res['session_id']

        itv = db.session.query(Interview).filter(
            Interview.interview_token == token
        ).first()
        assert itv is not None
        assert itv.status == 'em_andamento'
        assert itv.interview_type == 'audio'
        qs = itv.get_questions_list()
        assert len(qs) == res['total_questions']
        # rubric_id deve ter sido anexado a cada pergunta (3.4c)
        assert all(q.get('rubric_id') for q in qs)

    def test_candidate_created_on_the_fly(self, service, db_session):
        name = f'Novo Candidato {uuid.uuid4().hex[:6]}'
        service.start_interview(name, 'Analista de Dados')
        cand = db.session.query(Candidate).filter(
            Candidate.full_name == name
        ).first()
        assert cand is not None
        assert cand.position_applied == 'Analista de Dados'

    def test_submit_then_restart_keeps_progress(self, service, db_session):
        """Simula reboot do backend no meio da entrevista (nova instância)."""
        name = f'Joana Restart {uuid.uuid4().hex[:6]}'
        res = service.start_interview(name, 'Desenvolvedora Python')
        token = res['session_id']

        fake_audio = b'\x00' * 60000
        with patch.object(
            AudioInterviewService, '_transcribe_audio',
            return_value='Tenho cinco anos de experiência'
        ), patch(
            'src.utils.ai_analyzer.AIAnalyzer.analyze_response',
            return_value=_mock_analysis(),
        ):
            service.submit_response(token, fake_audio, 'audio/webm')

        # "restart": outra instância do serviço acessa a MESMA entrevista
        new_service = AudioInterviewService()
        info = new_service.get_question_info(token)
        assert info['finished'] is False
        assert info['question_number'] == 2  # já avançou uma


# --- 3.4c: assessments e fallback seguro --------------------------------

@pytest.mark.integration
class TestAssessmentsOnFinalize:
    def test_finalize_generates_one_assessment_per_answered_question(
        self, service, db_session
    ):
        name = f'Carlos Assess {uuid.uuid4().hex[:6]}'
        res = service.start_interview(name, 'Desenvolvedor Backend')
        token = res['session_id']

        with patch.object(
            AudioInterviewService, '_transcribe_audio',
            return_value='Resposta completa do candidato'
        ), patch(
            'src.utils.ai_analyzer.AIAnalyzer.analyze_response',
            return_value=_mock_analysis(score=4),
        ):
            for _ in range(2):
                service.submit_response(token, b'\x00' * 60000, 'audio/webm')

            final = service.finalize_interview(token)

        assert final['success'] is True

        itv = db.session.query(Interview).filter(
            Interview.interview_token == token
        ).first()
        assessments = (
            db.session.query(InterviewAssessment)
            .filter(InterviewAssessment.interview_id == itv.id)
            .order_by(InterviewAssessment.question_index.asc())
            .all()
        )
        assert len(assessments) == 2
        for a in assessments:
            assert a.rubric_id
            assert a.rubric_version
            assert a.dimension
            assert a.confidence is not None
            assert a.answer_excerpt
            assert a.model_name == 'openai:gpt-4o-mini'
            assert a.prompt_hash == 'abc123def456'

        # score agregado: média(4) * 20 == 80
        assert itv.status == 'concluida'
        assert itv.overall_score == 80.0
        assert itv.recommendation == 'CONTRATAR'

    def test_all_fallback_leaves_recommendation_null(self, service, db_session):
        name = f'Lidia Fallback {uuid.uuid4().hex[:6]}'
        res = service.start_interview(name, 'Desenvolvedora Backend')
        token = res['session_id']

        with patch.object(
            AudioInterviewService, '_transcribe_audio',
            return_value='qualquer resposta'
        ), patch(
            'src.utils.ai_analyzer.AIAnalyzer.analyze_response',
            return_value=_fallback_analysis(),
        ):
            for _ in range(2):
                service.submit_response(token, b'\x00' * 60000, 'audio/webm')
            service.finalize_interview(token)

        itv = db.session.query(Interview).filter(
            Interview.interview_token == token
        ).first()
        assessments = db.session.query(InterviewAssessment).filter_by(
            interview_id=itv.id
        ).all()
        assert all(a.model_name == 'fallback' for a in assessments)
        assert all(a.human_review_status == 'pending' for a in assessments)
        assert itv.recommendation is None


# --- 3.4d: endpoint de assessments --------------------------------------

@pytest.mark.integration
class TestAssessmentsEndpoint:
    def _seed_candidate_and_user(self, db_session, role):
        suffix = uuid.uuid4().hex[:6]
        user = User(
            email=f'user.{suffix}@example.com',
            full_name=f'User {suffix}',
            role=role,
            is_verified=True,
        )
        user.set_password('x')
        db_session.add(user)
        db_session.flush()

        candidate = Candidate(
            full_name=f'Candidate {suffix}',
            email=f'cand.{suffix}@example.com',
            position_applied='Desenvolvedor',
            status='em_processo',
        )
        db_session.add(candidate)
        db_session.commit()
        return user, candidate

    def _seed_interview_with_assessments(self, db_session, user, candidate):
        interview = Interview(
            candidate_id=candidate.id,
            interviewer_id=user.id,
            interview_type='audio',
            position='Dev',
            status='concluida',
            total_questions=1,
        )
        db_session.add(interview)
        db_session.flush()

        a = InterviewAssessment(
            interview_id=interview.id,
            question_index=0,
            question_text='Como você resolve um conflito técnico?',
            answer_excerpt='Chamo o time para discutir dados.',
            rubric_id='competencies.data_driven_decision',
            rubric_version='2026.04-v1',
            dimension='data_driven_decision',
            score=4.0,
            confidence=0.8,
            model_name='openai:gpt-4o-mini',
            prompt_hash='hash',
            human_review_status='pending',
            human_review_notes='nota confidencial',
        )
        db_session.add(a)
        db_session.commit()
        return interview

    def test_admin_sees_full_evidence(self, client, db_session):
        admin, candidate = self._seed_candidate_and_user(db_session, 'admin')
        itv = self._seed_interview_with_assessments(db_session, admin, candidate)

        rv = client.get(
            f'/interviews/{itv.id}/assessments',
            headers={'Authorization': f'Bearer {admin.generate_token()}'},
        )
        assert rv.status_code == 200
        body = rv.get_json()
        assert body['success'] is True
        assert len(body['assessments']) == 1
        a = body['assessments'][0]
        assert a['question_text']
        assert a['answer_excerpt']
        assert a['human_review_notes'] == 'nota confidencial'

    def test_viewer_gets_redacted_assessment(self, client, db_session):
        admin, candidate = self._seed_candidate_and_user(db_session, 'admin')
        itv = self._seed_interview_with_assessments(db_session, admin, candidate)

        viewer = User(
            email=f'viewer.{uuid.uuid4().hex[:6]}@example.com',
            full_name='Viewer',
            role='viewer', is_verified=True,
        )
        viewer.set_password('x')
        db_session.add(viewer)
        db_session.commit()

        rv = client.get(
            f'/interviews/{itv.id}/assessments',
            headers={'Authorization': f'Bearer {viewer.generate_token()}'},
        )
        assert rv.status_code == 200
        body = rv.get_json()
        assert len(body['assessments']) == 1
        a = body['assessments'][0]
        assert 'question_text' not in a
        assert 'answer_excerpt' not in a
        assert 'human_review_notes' not in a
        # metadados seguem visíveis
        assert a['rubric_id'] == 'competencies.data_driven_decision'
        assert a['score'] == 4.0

    def test_no_auth_returns_401(self, client, db_session):
        admin, candidate = self._seed_candidate_and_user(db_session, 'admin')
        itv = self._seed_interview_with_assessments(db_session, admin, candidate)
        rv = client.get(f'/interviews/{itv.id}/assessments')
        assert rv.status_code == 401

    def test_missing_interview_returns_404(self, client, db_session):
        admin, _ = self._seed_candidate_and_user(db_session, 'admin')
        rv = client.get(
            '/interviews/99999/assessments',
            headers={'Authorization': f'Bearer {admin.generate_token()}'},
        )
        assert rv.status_code == 404


@pytest.mark.integration
class TestAssessmentsEndpointApiAlias:
    """Mesmo contrato do endpoint, mas sob /api/interviews/*.

    Reutiliza os mesmos helpers de seed de TestAssessmentsEndpoint para
    garantir paridade entre as duas rotas (legacy e alias sob /api).
    """

    _seed_candidate_and_user = TestAssessmentsEndpoint._seed_candidate_and_user
    _seed_interview_with_assessments = TestAssessmentsEndpoint._seed_interview_with_assessments

    def test_admin_sees_full_evidence_api(self, client, db_session):
        admin, candidate = self._seed_candidate_and_user(db_session, 'admin')
        itv = self._seed_interview_with_assessments(db_session, admin, candidate)
        rv = client.get(
            f'/api/interviews/{itv.id}/assessments',
            headers={'Authorization': f'Bearer {admin.generate_token()}'},
        )
        assert rv.status_code == 200
        body = rv.get_json()
        assert body['success'] is True
        a = body['assessments'][0]
        assert a['question_text']
        assert a['answer_excerpt']
        assert a['human_review_notes'] == 'nota confidencial'

    def test_viewer_redacted_api(self, client, db_session):
        admin, candidate = self._seed_candidate_and_user(db_session, 'admin')
        itv = self._seed_interview_with_assessments(db_session, admin, candidate)
        viewer = User(
            email=f'viewer.api.{uuid.uuid4().hex[:6]}@example.com',
            full_name='Viewer API', role='viewer', is_verified=True,
        )
        viewer.set_password('x')
        db_session.add(viewer)
        db_session.commit()

        rv = client.get(
            f'/api/interviews/{itv.id}/assessments',
            headers={'Authorization': f'Bearer {viewer.generate_token()}'},
        )
        assert rv.status_code == 200
        a = rv.get_json()['assessments'][0]
        assert 'question_text' not in a
        assert 'human_review_notes' not in a

    def test_no_auth_returns_401_api(self, client, db_session):
        admin, candidate = self._seed_candidate_and_user(db_session, 'admin')
        itv = self._seed_interview_with_assessments(db_session, admin, candidate)
        rv = client.get(f'/api/interviews/{itv.id}/assessments')
        assert rv.status_code == 401

    def test_missing_interview_returns_404_api(self, client, db_session):
        admin, _ = self._seed_candidate_and_user(db_session, 'admin')
        rv = client.get(
            '/api/interviews/99999/assessments',
            headers={'Authorization': f'Bearer {admin.generate_token()}'},
        )
        assert rv.status_code == 404
