"""
Testes para o serviço de candidatos
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta, timezone
from src.services.candidate_service import CandidateService
from src.models import Candidate

class TestCandidateService:
    """Testes para CandidateService"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.service = CandidateService()
        self.mock_db = Mock()
    
    def test_create_candidate(self):
        """Testa criação de candidato"""
        candidate_data = {
            'full_name': 'João Silva',
            'email': 'joao@email.com',
            'phone': '11999999999',
            'position_applied': 'Desenvolvedor Python',
            'experience_years': 3,
            'skills': ['Python', 'Django', 'PostgreSQL'],
            'consent_given': True
        }
        
        # Mock para verificar se email já existe
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.service.create_candidate(self.mock_db, candidate_data, recruiter_id=1)
        
        # Verificações
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()
    
    def test_create_candidate_duplicate_email(self):
        """Testa criação de candidato com email duplicado"""
        candidate_data = {
            'full_name': 'João Silva',
            'email': 'joao@email.com',
            'position_applied': 'Desenvolvedor Python'
        }
        
        # Mock para simular email já existente
        existing_candidate = Mock()
        self.mock_db.query.return_value.filter.return_value.first.return_value = existing_candidate
        
        with pytest.raises(ValueError, match="Candidato com este email já existe"):
            self.service.create_candidate(self.mock_db, candidate_data, recruiter_id=1)
    
    def test_get_candidate(self):
        """Testa busca de candidato"""
        candidate = Mock()
        candidate.id = 1
        candidate.anonymized = False
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = candidate
        
        result = self.service.get_candidate(self.mock_db, 1)
        
        assert result == candidate
        self.mock_db.query.assert_called_once()
    
    def test_list_candidates_with_filters(self):
        """Testa listagem de candidatos com filtros"""
        # Mock dos candidatos
        candidates = [Mock(), Mock(), Mock()]
        
        # Mock da query — suporta múltiplos .filter() encadeados (fluent interface)
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 3
        mock_query.offset.return_value.limit.return_value.all.return_value = candidates

        self.mock_db.query.return_value.filter.return_value = mock_query
        
        filters = {
            'search': 'João',
            'status': 'novo',
            'position': 'Desenvolvedor Python'
        }
        
        result = self.service.list_candidates(self.mock_db, filters=filters)
        
        assert 'candidates' in result
        assert 'pagination' in result
        assert result['pagination']['total'] == 3
    
    def test_update_candidate(self):
        """Testa atualização de candidato"""
        candidate = Mock()
        candidate.id = 1
        candidate.anonymized = False
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = candidate
        
        update_data = {
            'full_name': 'João Silva Santos',
            'status': 'entrevista',
            'skills': ['Python', 'Django', 'React']
        }
        
        result = self.service.update_candidate(self.mock_db, 1, update_data)
        
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()
    
    def test_update_anonymized_candidate(self):
        """Testa tentativa de atualizar candidato anonimizado"""
        candidate = Mock()
        candidate.id = 1
        candidate.anonymized = True
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = candidate
        
        with pytest.raises(ValueError, match="Não é possível atualizar candidato anonimizado"):
            self.service.update_candidate(self.mock_db, 1, {'full_name': 'Novo Nome'})
    
    def test_delete_candidate_soft(self):
        """Testa exclusão lógica de candidato"""
        candidate = Mock()
        candidate.id = 1
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = candidate
        
        result = self.service.delete_candidate(self.mock_db, 1, soft_delete=True)
        
        assert result == True
        candidate.soft_delete.assert_called_once()
        self.mock_db.commit.assert_called_once()
    
    def test_delete_candidate_hard(self):
        """Testa exclusão física de candidato"""
        candidate = Mock()
        candidate.id = 1
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = candidate
        
        result = self.service.delete_candidate(self.mock_db, 1, soft_delete=False)
        
        assert result == True
        self.mock_db.delete.assert_called_once_with(candidate)
        self.mock_db.commit.assert_called_once()
    
    def test_anonymize_candidate(self):
        """Testa anonimização de candidato"""
        candidate = Mock()
        candidate.id = 1
        candidate.anonymized = False
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = candidate
        
        result = self.service.anonymize_candidate(self.mock_db, 1)
        
        assert result == True
        candidate.anonymize.assert_called_once()
        self.mock_db.commit.assert_called_once()
    
    def test_export_candidate_data(self):
        """Testa exportação de dados do candidato"""
        candidate = Mock()
        candidate.id = 1
        candidate.anonymized = False
        candidate.to_dict.return_value = {'id': 1, 'name': 'João'}
        candidate.get_retention_date.return_value = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=365)
        
        interviews = [Mock()]
        interviews[0].to_dict.return_value = {'id': 1, 'status': 'completed'}
        
        self.mock_db.query.return_value.filter.side_effect = [
            Mock(first=Mock(return_value=candidate)),  # Para candidato
            Mock(all=Mock(return_value=interviews))     # Para entrevistas
        ]
        
        result = self.service.export_candidate_data(self.mock_db, 1)
        
        assert 'candidate_data' in result
        assert 'interviews' in result
        assert 'export_date' in result
        assert 'data_retention_info' in result
    
    def test_get_candidate_statistics(self):
        """Testa estatísticas de candidatos"""
        # Mock da query base
        mock_query = Mock()
        mock_query.count.return_value = 100
        mock_query.filter.return_value = mock_query
        
        self.mock_db.query.return_value.filter.return_value = mock_query
        
        # Mock para posições distintas
        self.mock_db.query.return_value.filter.return_value.distinct.return_value.all.return_value = [
            ('Desenvolvedor Python',),
            ('Analista de Dados',)
        ]
        
        # Mock para scores médios
        mock_scores = Mock()
        mock_scores.overall = 75.5
        mock_scores.technical = 80.0
        mock_scores.behavioral = 70.0
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_scores
        
        result = self.service.get_candidate_statistics(self.mock_db)
        
        assert 'total_candidates' in result
        assert 'status_distribution' in result
        assert 'position_distribution' in result
        assert 'average_scores' in result
        assert 'monthly_trends' in result
    
    def test_schedule_anonymization_check(self):
        """Testa verificação automática de anonimização"""
        # Mock de candidatos que devem ser anonimizados
        candidate1 = Mock()
        candidate1.should_be_anonymized.return_value = True
        
        candidate2 = Mock()
        candidate2.should_be_anonymized.return_value = False
        
        candidates = [candidate1, candidate2]
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = candidates
        
        result = self.service.schedule_anonymization_check(self.mock_db)
        
        assert result == 1  # Apenas 1 candidato foi anonimizado
        candidate1.anonymize.assert_called_once()
        candidate2.anonymize.assert_not_called()
        self.mock_db.commit.assert_called_once()

if __name__ == '__main__':
    pytest.main([__file__])

