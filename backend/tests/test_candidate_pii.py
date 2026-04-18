"""
Testes para filtro de PII por papel (Onda 2 — item 3.3).

Cobre o critério de aceite:
- GET/serialização para 'viewer'/'analyst' não retorna phone, linkedin_url,
  ai_analysis, interview_notes; email chega mascarado.
- 'admin'/'recruiter'/'manager' continuam enxergando tudo.
"""
import pytest

from src.models.candidate import Candidate


def _make_candidate():
    c = Candidate(
        full_name='João Silva',
        email='joao.silva@example.com',
        phone='11999999999',
        position_applied='Desenvolvedor Python',
        current_company='Tech Corp',
        current_position='Sr. Engineer',
        linkedin_url='https://linkedin.com/in/joaosilva',
        interview_notes='Notas confidenciais do recrutador',
        status='novo',
    )
    c.set_ai_analysis_dict({'perfil_disc': 'D', 'resumo': 'bom candidato'})
    return c


@pytest.mark.unit
class TestCandidatePIIFilter:
    """Garante que papeis não-privilegiados não vejam PII sensível."""

    def test_admin_sees_full_sensitive_data(self):
        c = _make_candidate()
        data = c.to_dict(include_sensitive=True, role='admin')

        assert data['email'] == 'joao.silva@example.com'
        assert data['phone'] == '11999999999'
        assert data['linkedin_url'] == 'https://linkedin.com/in/joaosilva'
        assert data['interview_notes'] == 'Notas confidenciais do recrutador'
        assert isinstance(data['ai_analysis'], dict)
        assert data['ai_analysis'].get('perfil_disc') == 'D'

    def test_recruiter_sees_full_sensitive_data(self):
        c = _make_candidate()
        data = c.to_dict(include_sensitive=True, role='recruiter')

        assert data['email'] == 'joao.silva@example.com'
        assert 'phone' in data
        assert 'ai_analysis' in data

    def test_manager_sees_full_sensitive_data(self):
        c = _make_candidate()
        data = c.to_dict(include_sensitive=True, role='manager')
        assert 'linkedin_url' in data
        assert 'interview_notes' in data

    def test_viewer_gets_no_sensitive_pii(self):
        c = _make_candidate()
        data = c.to_dict(include_sensitive=True, role='viewer')

        # email mascarado
        assert data['email'] == 'j***@example.com'
        # PII sensível omitida mesmo com include_sensitive=True
        assert 'phone' not in data
        assert 'linkedin_url' not in data
        assert 'interview_notes' not in data
        assert 'ai_analysis' not in data
        # dados públicos continuam
        assert data['full_name'] == 'João Silva'
        assert data['position_applied'] == 'Desenvolvedor Python'

    def test_analyst_gets_no_sensitive_pii(self):
        c = _make_candidate()
        data = c.to_dict(include_sensitive=True, role='analyst')

        assert data['email'] == 'j***@example.com'
        assert 'phone' not in data
        assert 'ai_analysis' not in data

    def test_listing_without_sensitive_masks_email_for_viewer(self):
        c = _make_candidate()
        data = c.to_dict(role='viewer')
        assert data['email'] == 'j***@example.com'
        assert 'phone' not in data

    def test_listing_for_admin_without_sensitive_keeps_email(self):
        c = _make_candidate()
        data = c.to_dict(role='admin')
        # sem include_sensitive: email continua visível para admin
        assert data['email'] == 'joao.silva@example.com'
        # mas PII sensível só sai com include_sensitive=True
        assert 'phone' not in data

    def test_no_role_defaults_to_privileged_backwards_compat(self):
        """Chamadas antigas sem role= não devem quebrar nem mascarar."""
        c = _make_candidate()
        data = c.to_dict(include_sensitive=True)
        assert data['email'] == 'joao.silva@example.com'
        assert data['phone'] == '11999999999'

    def test_anonymized_candidate_hides_email_regardless_of_role(self):
        c = _make_candidate()
        c.id = 42
        c.anonymize()
        for role in ('admin', 'recruiter', 'viewer', 'analyst', None):
            data = c.to_dict(include_sensitive=True, role=role)
            assert data['email'] is None
            # PII sensível não sai para ninguém quando anonimizado
            assert 'phone' not in data
            assert 'linkedin_url' not in data

    def test_mask_email_preserves_domain(self):
        assert Candidate._mask_email('ana.costa@empresa.com.br') == 'a***@empresa.com.br'
        assert Candidate._mask_email('') == ''
        assert Candidate._mask_email(None) is None
        assert Candidate._mask_email('sem-arroba') == 'sem-arroba'
