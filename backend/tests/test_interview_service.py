"""
Testes para o serviço de entrevistas
"""
import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime
from src.services.interview_service import InterviewService
from src.models import Interview, Candidate, User

class TestInterviewService:
    """Testes para InterviewService"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.service = InterviewService()
        self.mock_db = Mock()
    
    def test_create_interview(self):
        """Testa criação de entrevista"""
        # Mock do candidato
        candidate = Mock()
        candidate.id = 1
        
        # Mock do entrevistador
        interviewer = Mock()
        interviewer.id = 1
        
        # Mock da entrevista
        interview = Mock()
        interview.id = 1
        interview.candidate_id = 1
        interview.interviewer_id = 1
        interview.position = "Desenvolvedor Python"
        interview.status = "agendada"
        
        self.mock_db.add.return_value = None
        self.mock_db.commit.return_value = None
        self.mock_db.refresh.return_value = None
        
        with patch.object(self.service, '_generate_questions_for_position') as mock_questions:
            mock_questions.return_value = [
                {"id": 1, "question": "Teste?", "category": "technical"}
            ]
            
            result = self.service.create_interview(
                self.mock_db, 
                candidate_id=1, 
                interviewer_id=1, 
                position="Desenvolvedor Python"
            )
            
            # Verificações
            self.mock_db.add.assert_called_once()
            self.mock_db.commit.assert_called_once()
            mock_questions.assert_called_once_with("Desenvolvedor Python")
    
    def test_generate_questions_for_position(self):
        """Testa geração de perguntas por posição"""
        # Teste para desenvolvedor
        questions = self.service._generate_questions_for_position("Desenvolvedor Python")
        
        assert len(questions) == 5
        assert all('question' in q for q in questions)
        assert all('id' in q for q in questions)
        assert all('category' in q for q in questions)
        
        # Teste para posição genérica
        questions_default = self.service._generate_questions_for_position("Cargo Inexistente")
        
        assert len(questions_default) == 5
        assert questions_default[0]['category'] == 'default'
    
    def test_start_interview(self):
        """Testa início de entrevista"""
        # Mock da entrevista
        interview = Mock()
        interview.id = 1
        interview.status = "agendada"
        interview.interview_type = "audio"
        interview.get_questions_list.return_value = [
            {"id": 1, "question": "Primeira pergunta?", "category": "technical"}
        ]
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = interview
        
        with patch.object(self.service, '_generate_question_audio') as mock_audio:
            mock_audio.return_value = "/path/to/audio.wav"
            
            result = self.service.start_interview(self.mock_db, 1)
            
            assert result['interview_id'] == 1
            assert result['status'] == 'em_andamento'
            assert 'question' in result
            assert result['question_index'] == 0
            assert result['total_questions'] == 1
    
    def test_process_response(self):
        """Testa processamento de resposta"""
        # Mock da entrevista
        interview = Mock()
        interview.id = 1
        interview.position = "Desenvolvedor Python"
        interview.current_question_index = 0
        interview.get_questions_list.return_value = [
            {"id": 1, "question": "Primeira pergunta?", "category": "technical"}
        ]
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = interview
        
        with patch.object(self.service.audio_processor, 'analyze_audio') as mock_audio:
            with patch.object(self.service.ai_analyzer, 'analyze_response') as mock_ai:
                mock_audio.return_value = {"confidence": 0.8}
                mock_ai.return_value = {"relevance": 85}
                
                result = self.service.process_response(
                    self.mock_db, 
                    1, 
                    "Minha resposta aqui",
                    "/path/to/audio.wav"
                )
                
                assert result['success'] == True
                assert 'audio_analysis' in result
                assert 'content_analysis' in result
                assert 'progress' in result
    
    def test_calculate_behavioral_scores(self):
        """Testa cálculo de scores comportamentais"""
        audio_analyses = [
            {
                'pitch_mean': 150,
                'energy_mean': 0.7,
                'speech_rate': 160,
                'pause_frequency': 0.05
            },
            {
                'pitch_mean': 140,
                'energy_mean': 0.6,
                'speech_rate': 150,
                'pause_frequency': 0.08
            }
        ]
        
        scores = self.service._calculate_behavioral_scores(audio_analyses)
        
        assert 'confidence' in scores
        assert 'enthusiasm' in scores
        assert 'clarity' in scores
        assert 'nervousness' in scores
        
        # Verificar se os scores estão no range correto
        for score in scores.values():
            assert 0 <= score <= 100
    
    def test_analyze_content_with_ai(self):
        """Testa análise de conteúdo com IA"""
        responses = [
            {
                'question': 'Qual sua experiência com Python?',
                'response': 'Tenho 3 anos de experiência com Python...'
            }
        ]
        
        with patch('openai.chat.completions.create') as mock_openai:
            mock_response = Mock()
            mock_response.choices[0].message.content = json.dumps({
                'relevance': 85,
                'technical_accuracy': 80,
                'communication': 90
            })
            mock_openai.return_value = mock_response
            
            scores = self.service._analyze_content_with_ai(responses, "Desenvolvedor Python")
            
            assert scores['relevance'] == 85
            assert scores['technical_accuracy'] == 80
            assert scores['communication'] == 90
    
    def test_finalize_interview(self):
        """Testa finalização de entrevista"""
        # Mock da entrevista
        interview = Mock()
        interview.id = 1
        interview.position = "Desenvolvedor Python"
        interview.get_questions_list.return_value = [
            {
                "id": 1, 
                "question": "Pergunta 1?", 
                "response": "Resposta 1",
                "audio_analysis": {"confidence": 0.8}
            }
        ]
        interview.candidate = Mock()
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = interview
        
        with patch.object(self.service, '_analyze_complete_interview') as mock_analyze:
            mock_analyze.return_value = {
                'behavioral_scores': {
                    'confidence': 80,
                    'enthusiasm': 75,
                    'clarity': 85,
                    'nervousness': 20
                },
                'content_scores': {
                    'relevance': 85,
                    'technical_accuracy': 80,
                    'communication': 90
                },
                'insights': {
                    'summary': 'Bom candidato',
                    'strengths': ['Comunicação clara'],
                    'improvements': []
                }
            }
            
            result = self.service.finalize_interview(self.mock_db, 1)
            
            assert 'interview_id' in result
            assert 'overall_score' in result
            assert 'recommendation' in result
            assert 'behavioral_scores' in result
            assert 'content_scores' in result
            assert 'insights' in result
            assert 'next_steps' in result
    
    def test_generate_next_steps(self):
        """Testa geração de próximos passos"""
        # Teste para recomendação CONTRATAR
        steps = self.service._generate_next_steps('CONTRATAR', 85)
        assert 'verificação de referências' in steps.lower()
        
        # Teste para recomendação CONSIDERAR
        steps = self.service._generate_next_steps('CONSIDERAR', 70)
        assert 'segunda entrevista' in steps.lower()
        
        # Teste para recomendação REJEITAR
        steps = self.service._generate_next_steps('REJEITAR', 45)
        assert 'não atende' in steps.lower()

if __name__ == '__main__':
    pytest.main([__file__])

