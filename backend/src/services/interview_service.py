"""
Serviço de entrevistas com IA e análise de áudio
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import openai
from sqlalchemy.orm import Session
from ..models import Interview, Candidate, User
from ..utils.audio_processor import AudioProcessor
from ..utils.ai_analyzer import AIAnalyzer
from ..utils.type_helpers import as_float, as_str, as_int, dt_iso, safe_bool

logger = logging.getLogger(__name__)

class InterviewService:
    """Serviço para gerenciar entrevistas"""
    
    def __init__(self):
        self.audio_processor = AudioProcessor()
        self.ai_analyzer = AIAnalyzer()
        
        # Configurar OpenAI
        openai.api_key = os.getenv('OPENAI_API_KEY')
        # if os.getenv('OPENAI_API_BASE'):
        #     openai.base_url = os.getenv('OPENAI_API_BASE')  # Use client configuration instead
    
    def create_interview(self, db: Session, candidate_id: int, interviewer_id: int, 
                        position: str, interview_type: str = 'audio') -> Interview:
        """Cria uma nova entrevista"""
        try:
            interview = Interview(
                candidate_id=candidate_id,
                interviewer_id=interviewer_id,
                position=position,
                interview_type=interview_type,
                status='agendada'
            )
            
            # Gerar perguntas baseadas na posição
            questions = self._generate_questions_for_position(position)
            interview.set_questions_list(questions)
            
            db.add(interview)
            db.commit()
            db.refresh(interview)
            
            logger.info(f"Entrevista criada: ID {interview.id} para candidato {candidate_id}")
            return interview
            
        except Exception as e:
            logger.error(f"Erro ao criar entrevista: {str(e)}")
            db.rollback()
            raise
    
    def start_interview(self, db: Session, interview_id: int) -> Dict:
        """Inicia uma entrevista"""
        try:
            interview = db.query(Interview).filter(Interview.id == interview_id).first()
            if not interview:
                raise ValueError("Entrevista não encontrada")
            
            if as_str(interview.status) != 'agendada':
                raise ValueError("Entrevista não pode ser iniciada")
            
            interview.start_interview()
            db.commit()
            
            # Retornar primeira pergunta
            questions = interview.get_questions_list()
            if questions:
                first_question = questions[0]
                
                # Gerar áudio da pergunta se necessário
                if as_str(interview.interview_type) == 'audio':
                    audio_path = self._generate_question_audio(first_question['question'], interview.id)
                    first_question['audio_path'] = audio_path
                
                return {
                    'interview_id': interview.id,
                    'question': first_question,
                    'question_index': 0,
                    'total_questions': len(questions),
                    'status': 'em_andamento'
                }
            
            raise ValueError("Nenhuma pergunta encontrada")
            
        except Exception as e:
            logger.error(f"Erro ao iniciar entrevista {interview_id}: {str(e)}")
            raise
    
    def get_next_question(self, db: Session, interview_id: int) -> Optional[Dict]:
        """Retorna a próxima pergunta da entrevista"""
        try:
            interview = db.query(Interview).filter(Interview.id == interview_id).first()
            if not interview:
                raise ValueError("Entrevista não encontrada")
            
            questions = interview.get_questions_list()
            current_index = interview.current_question_index
            
            current_idx = as_int(current_index)
            if current_idx >= len(questions):
                return None  # Entrevista finalizada
            
            question_data = questions[current_idx]
            
            # Gerar áudio da pergunta se necessário
            if as_str(interview.interview_type) == 'audio':
                audio_path = self._generate_question_audio(question_data['question'], interview.id, current_idx)
                question_data['audio_path'] = audio_path
            
            return {
                'interview_id': interview.id,
                'question': question_data,
                'question_index': current_idx,
                'total_questions': len(questions),
                'progress': (current_idx / len(questions)) * 100
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar próxima pergunta: {str(e)}")
            raise
    
    def process_response(self, db: Session, interview_id: int, response_text: str, 
                        audio_file_path: Optional[str] = None) -> Dict:
        """Processa resposta do candidato"""
        try:
            interview = db.query(Interview).filter(Interview.id == interview_id).first()
            if not interview:
                raise ValueError("Entrevista não encontrada")
            
            questions = interview.get_questions_list()
            current_index = interview.current_question_index
            
            current_idx = as_int(current_index)
            if current_idx >= len(questions):
                raise ValueError("Entrevista já finalizada")
            
            # Processar áudio se fornecido
            audio_analysis = {}
            if audio_file_path:
                audio_analysis = self.audio_processor.analyze_audio(audio_file_path)
                
                # Transcrever áudio se não há texto
                if not response_text:
                    response_text = self.audio_processor.transcribe_audio(audio_file_path)
            
            # Analisar resposta com IA
            question = questions[current_idx]['question']
            content_analysis = self.ai_analyzer.analyze_response(
                question=question,
                response=response_text,
                position=as_str(interview.position)
            )
            
            # Atualizar pergunta com resposta
            questions[current_idx].update({
                'response': response_text,
                'audio_path': audio_file_path,
                'audio_analysis': audio_analysis,
                'content_analysis': content_analysis,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            interview.set_questions_list(questions)
            interview.current_question_index = as_int(interview.current_question_index) + 1
            
            db.commit()
            
            # Verificar se é a última pergunta
            is_last_question = as_int(interview.current_question_index) >= len(questions)
            
            return {
                'success': True,
                'is_last_question': is_last_question,
                'next_question_index': as_int(interview.current_question_index),
                'progress': (as_int(interview.current_question_index) / len(questions)) * 100,
                'audio_analysis': audio_analysis,
                'content_analysis': content_analysis
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar resposta: {str(e)}")
            raise
    
    def finalize_interview(self, db: Session, interview_id: int) -> Dict:
        """Finaliza entrevista e gera análise completa"""
        try:
            interview = db.query(Interview).filter(Interview.id == interview_id).first()
            if not interview:
                raise ValueError("Entrevista não encontrada")
            
            # Finalizar entrevista
            interview.complete_interview()
            
            # Analisar todas as respostas
            questions = interview.get_questions_list()
            overall_analysis = self._analyze_complete_interview(questions, as_str(interview.position))
            
            # Atualizar scores
            interview.confidence_score = overall_analysis['behavioral_scores']['confidence']
            interview.enthusiasm_score = overall_analysis['behavioral_scores']['enthusiasm']
            interview.clarity_score = overall_analysis['behavioral_scores']['clarity']
            interview.nervousness_score = overall_analysis['behavioral_scores']['nervousness']
            
            interview.content_relevance = overall_analysis['content_scores']['relevance']
            interview.technical_accuracy = overall_analysis['content_scores']['technical_accuracy']
            interview.communication_skills = overall_analysis['content_scores']['communication']
            
            # Calcular score geral
            interview.calculate_overall_score()
            
            # Salvar insights da IA
            interview.set_ai_insights_dict(overall_analysis['insights'])
            
            # Atualizar candidato
            candidate = interview.candidate
            if candidate:
                candidate.overall_score = interview.overall_score
                candidate.behavioral_score = (
                    interview.confidence_score + interview.enthusiasm_score + interview.clarity_score
                ) / 3
                candidate.technical_score = interview.technical_accuracy
                candidate.ai_recommendation = interview.recommendation
                candidate.ai_confidence = interview.confidence_level
                candidate.status = 'entrevista_realizada'
                candidate.interview_completed = interview.completed_at
            
            db.commit()
            
            logger.info(f"Entrevista {interview_id} finalizada com score {interview.overall_score}")
            
            return {
                'interview_id': interview.id,
                'overall_score': interview.overall_score,
                'recommendation': interview.recommendation,
                'confidence_level': interview.confidence_level,
                'behavioral_scores': {
                    'confidence': interview.confidence_score,
                    'enthusiasm': interview.enthusiasm_score,
                    'clarity': interview.clarity_score,
                    'nervousness': interview.nervousness_score
                },
                'content_scores': {
                    'relevance': interview.content_relevance,
                    'technical_accuracy': interview.technical_accuracy,
                    'communication': interview.communication_skills
                },
                'insights': overall_analysis['insights'],
                'next_steps': self._generate_next_steps(as_str(interview.recommendation), as_float(interview.overall_score))
            }
            
        except Exception as e:
            logger.error(f"Erro ao finalizar entrevista {interview_id}: {str(e)}")
            raise
    
    def _generate_questions_for_position(self, position: str) -> List[Dict]:
        """Gera perguntas específicas para a posição"""
        
        # Base de perguntas por categoria
        question_templates = {
            'desenvolvedor': [
                "Conte-me sobre sua experiência com desenvolvimento de software.",
                "Como você aborda a resolução de problemas técnicos complexos?",
                "Descreva um projeto desafiador que você trabalhou recentemente.",
                "Como você se mantém atualizado com novas tecnologias?",
                "Qual sua experiência com trabalho em equipe e metodologias ágeis?"
            ],
            'analista': [
                "Descreva sua experiência com análise de dados.",
                "Como você aborda um problema de análise complexo?",
                "Conte sobre um insight importante que você descobriu através de dados.",
                "Qual sua experiência com ferramentas de visualização?",
                "Como você comunica resultados técnicos para stakeholders não-técnicos?"
            ],
            'gerente': [
                "Descreva sua experiência em liderança de equipes.",
                "Como você lida com conflitos dentro da equipe?",
                "Conte sobre um projeto que você gerenciou do início ao fim.",
                "Como você motiva sua equipe em momentos difíceis?",
                "Qual sua abordagem para definir e acompanhar metas?"
            ],
            'default': [
                "Conte-me sobre você e sua experiência profissional.",
                "Por que você se interessou por esta posição?",
                "Quais são seus principais pontos fortes?",
                "Como você lida com desafios e pressão no trabalho?",
                "Onde você se vê profissionalmente em 5 anos?"
            ]
        }
        
        # Determinar categoria baseada na posição
        position_lower = position.lower()
        category = 'default'
        
        for key in question_templates.keys():
            if key in position_lower:
                category = key
                break
        
        questions = question_templates[category]
        
        # Formatar perguntas
        formatted_questions = []
        for i, question in enumerate(questions):
            formatted_questions.append({
                'id': i + 1,
                'question': question,
                'category': category,
                'expected_duration': 120,  # 2 minutos
                'response': None,
                'audio_path': None
            })
        
        return formatted_questions
    
    def _generate_question_audio(self, question_text: str, interview_id: int, 
                                question_index: int = 0) -> str:
        """Gera áudio da pergunta usando TTS"""
        try:
            # Criar diretório se não existir
            audio_dir = f"/app/uploads/interviews/{interview_id}/questions"
            os.makedirs(audio_dir, exist_ok=True)
            
            # Caminho do arquivo de áudio
            audio_path = f"{audio_dir}/question_{question_index}.wav"
            
            # Gerar áudio usando OpenAI TTS
            response = openai.audio.speech.create(
                model="tts-1",
                voice="nova",
                input=question_text
            )
            
            # Salvar arquivo
            with open(audio_path, 'wb') as f:
                f.write(response.content)
            
            return audio_path
            
        except Exception as e:
            logger.error(f"Erro ao gerar áudio da pergunta: {str(e)}")
            return ""  # Return empty string instead of None
    
    def _analyze_complete_interview(self, questions: List[Dict], position: str) -> Dict:
        """Analisa entrevista completa"""
        try:
            # Compilar todas as respostas
            all_responses = []
            audio_analyses = []
            
            for q in questions:
                if q.get('response'):
                    all_responses.append({
                        'question': q['question'],
                        'response': q['response']
                    })
                
                if q.get('audio_analysis'):
                    audio_analyses.append(q['audio_analysis'])
            
            # Análise comportamental baseada em áudio
            behavioral_scores = self._calculate_behavioral_scores(audio_analyses)
            
            # Análise de conteúdo com IA
            content_scores = self._analyze_content_with_ai(all_responses, position)
            
            # Gerar insights
            insights = self._generate_insights(behavioral_scores, content_scores, position)
            
            return {
                'behavioral_scores': behavioral_scores,
                'content_scores': content_scores,
                'insights': insights
            }
            
        except Exception as e:
            logger.error(f"Erro na análise completa: {str(e)}")
            return {
                'behavioral_scores': {'confidence': 70, 'enthusiasm': 70, 'clarity': 70, 'nervousness': 30},
                'content_scores': {'relevance': 70, 'technical_accuracy': 70, 'communication': 70},
                'insights': {'summary': 'Análise não disponível devido a erro técnico.'}
            }
    
    def _calculate_behavioral_scores(self, audio_analyses: List[Dict]) -> Dict:
        """Calcula scores comportamentais baseados na análise de áudio"""
        if not audio_analyses:
            return {
                'confidence': 70.0,
                'enthusiasm': 70.0,
                'clarity': 70.0,
                'nervousness': 30.0
            }
        
        # Agregar métricas de áudio
        total_analyses = len(audio_analyses)
        
        avg_pitch = sum(a.get('pitch_mean', 150) for a in audio_analyses) / total_analyses
        avg_energy = sum(a.get('energy_mean', 0.5) for a in audio_analyses) / total_analyses
        avg_pace = sum(a.get('speech_rate', 150) for a in audio_analyses) / total_analyses
        avg_pauses = sum(a.get('pause_frequency', 0.1) for a in audio_analyses) / total_analyses
        
        # Calcular scores (0-100)
        confidence = min(100, max(0, (avg_energy * 100 + (200 - avg_pitch) / 2)))
        enthusiasm = min(100, max(0, (avg_energy * 80 + avg_pitch / 3)))
        clarity = min(100, max(0, 100 - (avg_pauses * 200)))
        nervousness = min(100, max(0, (avg_pauses * 150 + (avg_pitch - 150) / 2)))
        
        return {
            'confidence': round(confidence, 1),
            'enthusiasm': round(enthusiasm, 1),
            'clarity': round(clarity, 1),
            'nervousness': round(nervousness, 1)
        }
    
    def _analyze_content_with_ai(self, responses: List[Dict], position: str) -> Dict:
        """Analisa conteúdo das respostas com IA"""
        try:
            # Compilar contexto
            context = f"Posição: {position}\n\n"
            for i, resp in enumerate(responses, 1):
                context += f"Pergunta {i}: {resp['question']}\n"
                context += f"Resposta {i}: {resp['response']}\n\n"
            
            prompt = f"""
            Analise as seguintes respostas de entrevista para a posição de {position}.
            
            {context}
            
            Avalie em uma escala de 0-100:
            1. Relevância das respostas para a posição
            2. Precisão técnica (quando aplicável)
            3. Habilidades de comunicação
            
            Retorne apenas um JSON com as chaves: relevance, technical_accuracy, communication
            """
            
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            result = json.loads(content) if content else {}
            
            return {
                'relevance': float(result.get('relevance', 70)),
                'technical_accuracy': float(result.get('technical_accuracy', 70)),
                'communication': float(result.get('communication', 70))
            }
            
        except Exception as e:
            logger.error(f"Erro na análise de conteúdo: {str(e)}")
            return {
                'relevance': 70.0,
                'technical_accuracy': 70.0,
                'communication': 70.0
            }
    
    def _generate_insights(self, behavioral_scores: Dict, content_scores: Dict, position: str) -> Dict:
        """Gera insights da entrevista"""
        
        # Pontos fortes
        strengths = []
        if behavioral_scores['confidence'] >= 80:
            strengths.append("Demonstra alta confiança")
        if behavioral_scores['enthusiasm'] >= 80:
            strengths.append("Mostra entusiasmo pela posição")
        if content_scores['technical_accuracy'] >= 80:
            strengths.append("Conhecimento técnico sólido")
        if content_scores['communication'] >= 80:
            strengths.append("Excelentes habilidades de comunicação")
        
        # Áreas de melhoria
        improvements = []
        if behavioral_scores['nervousness'] >= 70:
            improvements.append("Trabalhar no controle do nervosismo")
        if behavioral_scores['clarity'] <= 60:
            improvements.append("Melhorar clareza na comunicação")
        if content_scores['relevance'] <= 60:
            improvements.append("Focar mais na relevância das respostas")
        
        # Resumo geral
        avg_score = (
            sum(behavioral_scores.values()) / len(behavioral_scores) +
            sum(content_scores.values()) / len(content_scores)
        ) / 2
        
        if avg_score >= 80:
            summary = "Candidato demonstrou excelente performance na entrevista."
        elif avg_score >= 60:
            summary = "Candidato teve performance satisfatória com alguns pontos de atenção."
        else:
            summary = "Candidato precisa de desenvolvimento em várias áreas."
        
        return {
            'summary': summary,
            'strengths': strengths,
            'improvements': improvements,
            'overall_impression': f"Score médio: {avg_score:.1f}/100"
        }
    
    def _generate_next_steps(self, recommendation: str, score: float) -> str:
        """Gera próximos passos baseados na recomendação"""
        
        if recommendation == 'CONTRATAR':
            return "Prosseguir com verificação de referências e proposta de contratação."
        elif recommendation == 'CONSIDERAR':
            return "Agendar segunda entrevista com gestor direto para avaliação adicional."
        else:
            return "Candidato não atende aos requisitos da posição no momento."

