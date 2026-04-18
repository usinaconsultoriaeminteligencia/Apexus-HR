"""
Modelo de entrevista com análise de áudio e IA
"""
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta, timezone
import json
import uuid
from . import BaseModel
from ..utils.type_helpers import as_float, as_str, as_int, dt_iso, safe_bool

class Interview(BaseModel):
    """Modelo de entrevista"""
    __tablename__ = 'interviews'
    
    # Relacionamentos
    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=False)
    interviewer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Dados da entrevista
    interview_type = Column(String(50), default='audio')  # audio, video, presencial
    position = Column(String(255), nullable=False)
    scheduled_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_minutes = Column(Integer, default=0)
    
    # Status
    status = Column(String(50), default='agendada')  # agendada, em_andamento, concluida, cancelada
    
    # Dados de áudio
    audio_file_path = Column(String(500))
    transcription = Column(Text)
    audio_quality_score = Column(Float, default=0.0)
    
    # Perguntas e respostas
    questions_data = Column(Text)  # JSON com perguntas e respostas
    current_question_index = Column(Integer, default=0)
    total_questions = Column(Integer, default=5)
    
    # Análise comportamental
    confidence_score = Column(Float, default=0.0)
    enthusiasm_score = Column(Float, default=0.0)
    clarity_score = Column(Float, default=0.0)
    nervousness_score = Column(Float, default=0.0)
    
    # Análise técnica de voz
    voice_analysis = Column(Text)  # JSON com análise detalhada de voz
    speech_rate = Column(Float, default=0.0)  # palavras por minuto
    pause_frequency = Column(Float, default=0.0)
    voice_stability = Column(Float, default=0.0)
    
    # Análise de conteúdo
    content_relevance = Column(Float, default=0.0)
    technical_accuracy = Column(Float, default=0.0)
    communication_skills = Column(Float, default=0.0)
    
    # Scores finais
    overall_score = Column(Float, default=0.0)
    recommendation = Column(String(50))  # CONTRATAR, CONSIDERAR, REJEITAR
    confidence_level = Column(Float, default=0.0)
    
    # Observações
    interviewer_notes = Column(Text)
    ai_insights = Column(Text)  # JSON com insights da IA
    next_steps = Column(Text)
    
    # Campos para compartilhamento de entrevista
    interview_token = Column(String(36), unique=True, index=True)  # UUID para acesso público
    token_expires_at = Column(DateTime)  # Data de expiração do token
    invitation_sent_at = Column(DateTime)  # Quando o convite foi enviado
    invitation_channel = Column(String(20))  # email, sms, whatsapp, link
    invitation_status = Column(String(20), default='pending')  # pending, sent, opened, started, completed
    invitation_phone = Column(String(20))  # Telefone do candidato para SMS/WhatsApp
    invitation_message = Column(Text)  # Mensagem personalizada do convite
    token_accessed_at = Column(DateTime)  # Quando o token foi acessado pela primeira vez
    token_access_count = Column(Integer, default=0)  # Número de vezes que o token foi acessado
    
    # Relacionamentos
    candidate = relationship("Candidate", foreign_keys=[candidate_id])
    interviewer = relationship("User", foreign_keys=[interviewer_id])
    
    def get_questions_list(self):
        """Retorna lista de perguntas e respostas"""
        if self.questions_data is None or as_str(self.questions_data) == "":
            return []
        try:
            return json.loads(str(self.questions_data))
        except:
            return []
    
    def set_questions_list(self, questions_list):
        """Define lista de perguntas e respostas"""
        self.questions_data = json.dumps(questions_list, ensure_ascii=False)
        self.total_questions = len(questions_list)
    
    def add_question_response(self, question, response, audio_path=None):
        """Adiciona pergunta e resposta à entrevista"""
        questions = self.get_questions_list()
        
        question_data = {
            'question': question,
            'response': response,
            'audio_path': audio_path,
            'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            'question_index': len(questions)
        }
        
        questions.append(question_data)
        self.set_questions_list(questions)
        self.current_question_index = len(questions)
    
    def get_voice_analysis_dict(self):
        """Retorna análise de voz como dicionário"""
        if self.voice_analysis is None or as_str(self.voice_analysis) == "":
            return {}
        try:
            return json.loads(str(self.voice_analysis))
        except:
            return {}
    
    def set_voice_analysis_dict(self, analysis_dict):
        """Define análise de voz"""
        self.voice_analysis = json.dumps(analysis_dict, ensure_ascii=False)
    
    def get_ai_insights_dict(self):
        """Retorna insights da IA como dicionário"""
        if self.ai_insights is None or as_str(self.ai_insights) == "":
            return {}
        try:
            return json.loads(str(self.ai_insights))
        except:
            return {}
    
    def set_ai_insights_dict(self, insights_dict):
        """Define insights da IA"""
        self.ai_insights = json.dumps(insights_dict, ensure_ascii=False)
    
    def calculate_overall_score(self):
        """Calcula score geral da entrevista"""
        weights = {
            'behavioral': 0.3,  # confiança, entusiasmo, clareza
            'technical': 0.4,   # precisão técnica, relevância
            'communication': 0.3  # habilidades de comunicação
        }
        
        # Score comportamental
        behavioral_score = (
            as_float(self.confidence_score) * 0.4 +
            as_float(self.enthusiasm_score) * 0.3 +
            as_float(self.clarity_score) * 0.3
        )
        
        # Score técnico
        technical_score = (
            as_float(self.technical_accuracy) * 0.6 +
            as_float(self.content_relevance) * 0.4
        )
        
        # Score de comunicação
        communication_score = as_float(self.communication_skills)
        
        # Score geral
        self.overall_score = (
            behavioral_score * weights['behavioral'] +
            technical_score * weights['technical'] +
            communication_score * weights['communication']
        )
        
        # Determinar recomendação
        score_val = as_float(self.overall_score)
        if score_val >= 80:
            self.recommendation = 'CONTRATAR'
            self.confidence_level = 0.9
        elif score_val >= 60:
            self.recommendation = 'CONSIDERAR'
            self.confidence_level = 0.7
        else:
            self.recommendation = 'REJEITAR'
            self.confidence_level = 0.8
        
        return self.overall_score
    
    def start_interview(self):
        """Inicia a entrevista"""
        self.started_at = datetime.now(timezone.utc).replace(tzinfo=None)
        self.status = 'em_andamento'
    
    def complete_interview(self):
        """Finaliza a entrevista"""
        self.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        self.status = 'concluida'
        
        if self.started_at is not None and self.completed_at is not None:
            if isinstance(self.started_at, datetime) and isinstance(self.completed_at, datetime):
                duration = self.completed_at - self.started_at
                self.duration_minutes = int(duration.total_seconds() / 60)
        
        # Calcular score final
        self.calculate_overall_score()
    
    def get_progress_percentage(self):
        """Retorna progresso da entrevista em porcentagem"""
        total_q = as_int(self.total_questions)
        if total_q == 0:
            return 0
        current_idx = as_int(self.current_question_index)
        return min(100, (current_idx / total_q) * 100)
    
    def get_status_display(self):
        """Retorna status em formato legível"""
        status_map = {
            'agendada': 'Agendada',
            'em_andamento': 'Em Andamento',
            'concluida': 'Concluída',
            'cancelada': 'Cancelada'
        }
        return status_map.get(as_str(self.status), as_str(self.status))
    
    def generate_interview_token(self, expiration_hours=48):
        """Gera token único para acesso público à entrevista"""
        self.interview_token = str(uuid.uuid4())
        self.token_expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=expiration_hours)
        self.invitation_status = 'pending'
        return self.interview_token
    
    def is_token_valid(self):
        """Verifica se o token ainda é válido"""
        if self.interview_token is None or self.token_expires_at is None:
            return False
        if isinstance(self.token_expires_at, datetime):
            return datetime.now(timezone.utc).replace(tzinfo=None) < self.token_expires_at
        return False
    
    def record_token_access(self):
        """Registra acesso ao token"""
        if self.token_accessed_at is None:
            self.token_accessed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            self.invitation_status = 'opened'
        self.token_access_count = as_int(self.token_access_count) + 1
    
    def get_public_url(self, base_url):
        """Retorna URL pública para acesso à entrevista"""
        if self.interview_token is None:
            self.generate_interview_token()
        return f"{base_url}/interview/{as_str(self.interview_token)}"
    
    def to_dict(self, include_detailed=False):
        """Converte entrevista para dicionário"""
        data = {
            'id': self.id,
            'candidate_id': self.candidate_id,
            'interviewer_id': self.interviewer_id,
            'position': self.position,
            'interview_type': self.interview_type,
            'status': self.status,
            'status_display': self.get_status_display(),
            'scheduled_at': dt_iso(self.scheduled_at),
            'started_at': dt_iso(self.started_at),
            'completed_at': dt_iso(self.completed_at),
            'duration_minutes': self.duration_minutes,
            'current_question_index': self.current_question_index,
            'total_questions': self.total_questions,
            'progress_percentage': self.get_progress_percentage(),
            'overall_score': round(as_float(self.overall_score), 1),
            'recommendation': self.recommendation,
            'confidence_level': round(as_float(self.confidence_level), 2),
            'created_at': self.created_at.isoformat(),
            # Campos de compartilhamento
            'interview_token': self.interview_token,
            'invitation_status': self.invitation_status,
            'invitation_channel': self.invitation_channel,
            'invitation_sent_at': dt_iso(self.invitation_sent_at),
            'token_expires_at': dt_iso(self.token_expires_at),
            'is_token_valid': self.is_token_valid()
        }
        
        if include_detailed:
            data.update({
                'questions_data': self.get_questions_list(),
                'confidence_score': round(as_float(self.confidence_score), 1),
                'enthusiasm_score': round(as_float(self.enthusiasm_score), 1),
                'clarity_score': round(as_float(self.clarity_score), 1),
                'nervousness_score': round(as_float(self.nervousness_score), 1),
                'content_relevance': round(as_float(self.content_relevance), 1),
                'technical_accuracy': round(as_float(self.technical_accuracy), 1),
                'communication_skills': round(as_float(self.communication_skills), 1),
                'voice_analysis': self.get_voice_analysis_dict(),
                'ai_insights': self.get_ai_insights_dict(),
                'interviewer_notes': self.interviewer_notes,
                'next_steps': self.next_steps,
                'transcription': self.transcription
            })
        
        return data

