# backend/src/services/audio_interview_service.py
"""Serviço de entrevistas por áudio com persistência em banco.

Onda 2 — itens 3.2 e 3.4c:
- Sessões deixam de viver em memória e passam a ser registros em
  `interviews`. O `session_id` público retornado ao cliente é o
  `interview.interview_token` (UUID), o que permite restart do backend,
  múltiplos workers Gunicorn e auditoria completa.
- Ao finalizar, cada resposta respondida vira uma linha em
  `interview_assessments` com rubric_id, rubric_version, dimension,
  evidence_excerpt, model_name, prompt_hash e human_review_status, de
  modo que a trilha de auditoria exigida pela Onda 2 está íntegra.
- Fallback seguro: se TODAS as análises saírem via fallback (ex.: sem
  OPENAI_API_KEY), `interview.recommendation` permanece `None` e todos
  os assessments ficam `human_review_status='pending'`. Conformidade com
  LGPD art. 20 (decisão automática sem base).
"""
from __future__ import annotations

import io
import json
import logging
import math
import os
import struct
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..models import db
from ..models.assessment import InterviewAssessment
from ..models.candidate import Candidate
from ..models.interview import Interview
from ..models.user import User
from ..utils.assessment_helpers import resolve_rubric

logger = logging.getLogger(__name__)


@dataclass
class InterviewQuestion:
    """Template de pergunta do banco local.

    Onda 2: rubric_id/dimension anexados para permitir assessment
    auditável já no momento da criação da entrevista.
    """

    question_id: int
    text: str
    category: str
    expected_duration: int  # segundos
    rubric_id: Optional[str] = None
    dimension: Optional[str] = None


class AudioInterviewService:
    """Gerenciador de entrevistas por áudio persistido em banco."""

    def __init__(self):
        self.question_bank = self._load_question_bank()

    # ------------------------------------------------------------------
    # Banco local de perguntas (templates)
    # ------------------------------------------------------------------
    def _load_question_bank(self) -> Dict[str, List[InterviewQuestion]]:
        def _q(qid, text, category, duration):
            rubric_id, dimension = resolve_rubric(None, category)
            return InterviewQuestion(
                question_id=qid,
                text=text,
                category=category,
                expected_duration=duration,
                rubric_id=rubric_id,
                dimension=dimension,
            )

        return {
            'developer': [
                _q(1, "Conte-me sobre sua experiência em desenvolvimento de software", "experiencia", 120),
                _q(2, "Como você aborda a resolução de problemas técnicos complexos?", "tecnico", 90),
                _q(3, "Descreva um projeto desafiador em que trabalhou recentemente", "projeto", 120),
                _q(4, "Como você se mantém atualizado com novas tecnologias?", "aprendizado", 90),
                _q(5, "Qual é sua abordagem para trabalhar em equipe?", "comportamental", 90),
            ],
            'manager': [
                _q(1, "Descreva sua experiência em liderança de equipes", "lideranca", 120),
                _q(2, "Como você lida com conflitos entre membros da equipe?", "gestao", 90),
                _q(3, "Conte sobre um momento difícil que enfrentou como gestor", "desafio", 120),
                _q(4, "Como você motiva sua equipe em períodos de alta pressão?", "motivacao", 90),
                _q(5, "Qual é sua estratégia para desenvolver talentos?", "desenvolvimento", 90),
            ],
            'analyst': [
                _q(1, "Descreva sua experiência com análise de dados", "analise", 120),
                _q(2, "Como você aborda um problema de negócio complexo?", "problema", 90),
                _q(3, "Conte sobre uma análise que gerou impacto significativo", "impacto", 120),
                _q(4, "Quais ferramentas de análise você domina?", "ferramentas", 90),
                _q(5, "Como você comunica insights para stakeholders?", "comunicacao", 90),
            ],
            'default': [
                _q(1, "Conte-me sobre você e sua trajetória profissional", "apresentacao", 120),
                _q(2, "Por que você tem interesse nesta posição?", "motivacao", 90),
                _q(3, "Quais são seus principais pontos fortes?", "forças", 90),
                _q(4, "Descreva um desafio profissional que superou", "desafio", 120),
                _q(5, "Onde você se vê daqui a 5 anos?", "futuro", 90),
            ],
        }

    def _get_position_key(self, position: str) -> str:
        p = (position or '').lower()
        if any(k in p for k in ['dev', 'programador', 'engineer', 'software']):
            return 'developer'
        if any(k in p for k in ['manager', 'gestor', 'coordenador', 'líder']):
            return 'manager'
        if any(k in p for k in ['analyst', 'analista', 'data']):
            return 'analyst'
        return 'default'

    # ------------------------------------------------------------------
    # Helpers de persistência
    # ------------------------------------------------------------------
    def _load_interview(self, session_id: str) -> Optional[Interview]:
        """Busca entrevista pelo interview_token (session_id público)."""
        if not session_id:
            return None
        interview = (
            db.session.query(Interview)
            .filter(Interview.interview_token == session_id)
            .first()
        )
        return interview

    def _ensure_candidate(self, candidate_name: str, position: str) -> Candidate:
        """Busca candidato por full_name; cria com email temporário se necessário.

        Mantém paridade com `routes/assessments.py::save_assessment` para
        não divergir a geração de candidatos.
        """
        candidate = (
            db.session.query(Candidate)
            .filter(Candidate.full_name == candidate_name)
            .first()
        )
        if candidate:
            return candidate

        import re
        import unicodedata

        normalized = unicodedata.normalize('NFKD', candidate_name)
        ascii_name = normalized.encode('ASCII', 'ignore').decode('ASCII')
        safe_name = re.sub(r'[^a-zA-Z0-9\s]', '', ascii_name.lower())
        safe_name = re.sub(r'\s+', '.', safe_name.strip()) or 'candidato'

        base_email = f"{safe_name}@temp.com"
        email = base_email
        counter = 1
        while db.session.query(Candidate).filter(Candidate.email == email).first():
            email = f"{safe_name}.{counter}@temp.com"
            counter += 1

        candidate = Candidate(
            full_name=candidate_name,
            email=email,
            phone=None,
            position_applied=position,
            status='em_processo',
        )
        db.session.add(candidate)
        db.session.flush()
        logger.info("Novo candidato criado on-the-fly: %s (id=%s)", candidate_name, candidate.id)
        return candidate

    def _default_interviewer(self) -> Optional[User]:
        """Primeiro admin como interviewer default (fallback: qualquer user)."""
        interviewer = (
            db.session.query(User).filter(User.role == 'admin').first()
        )
        if interviewer is None:
            interviewer = db.session.query(User).first()
        return interviewer

    # ------------------------------------------------------------------
    # API pública — equivalente à antiga, mas persistida
    # ------------------------------------------------------------------
    def start_interview(self, candidate_name: str, position: str) -> Dict[str, Any]:
        """Cria nova entrevista persistida e devolve session_id = token."""
        try:
            candidate_name = (candidate_name or '').strip()
            position = (position or '').strip()
            if not candidate_name or not position:
                return {"success": False, "error": "candidate_name e position obrigatórios"}

            interviewer = self._default_interviewer()
            if interviewer is None:
                return {
                    "success": False,
                    "error": "Nenhum usuário cadastrado para atuar como entrevistador",
                }

            candidate = self._ensure_candidate(candidate_name, position)

            position_key = self._get_position_key(position)
            questions = self.question_bank.get(position_key, self.question_bank['default'])

            questions_payload = [
                {
                    'question_index': idx,
                    'question_id': q.question_id,
                    'text': q.text,
                    'category': q.category,
                    'expected_duration': q.expected_duration,
                    'rubric_id': q.rubric_id,
                    'dimension': q.dimension,
                    'response': None,
                    'transcription': None,
                    'audio_path': None,
                    'analysis': None,
                    'answered_at': None,
                }
                for idx, q in enumerate(questions)
            ]

            interview = Interview(
                candidate_id=candidate.id,
                interviewer_id=interviewer.id,
                interview_type='audio',
                position=position,
                status='em_andamento',
                current_question_index=0,
                total_questions=len(questions),
            )
            interview.started_at = datetime.now(timezone.utc).replace(tzinfo=None)
            interview.set_questions_list(questions_payload)
            token = interview.generate_interview_token(expiration_hours=48)

            db.session.add(interview)
            db.session.commit()

            logger.info("Entrevista iniciada token=%s candidate=%s", token, candidate_name)

            return {
                "success": True,
                "session_id": token,
                "interview_id": interview.id,
                "total_questions": len(questions),
                "estimated_duration": sum(q.expected_duration for q in questions) // 60,
            }

        except Exception as e:
            db.session.rollback()
            logger.error("Erro ao iniciar entrevista: %s", e, exc_info=True)
            return {"success": False, "error": str(e)}

    def get_question_info(self, session_id: str) -> Dict[str, Any]:
        """Retorna informações da pergunta atual sem vazar rubric_id interno."""
        interview = self._load_interview(session_id)
        if interview is None:
            return {"error": "Sessão não encontrada", "finished": True}

        questions = interview.get_questions_list() or []
        idx = int(interview.current_question_index or 0)
        if idx >= len(questions):
            return {"finished": True}

        q = questions[idx]
        return {
            "finished": False,
            "question_number": idx + 1,
            "total_questions": len(questions),
            "question_text": q.get('text', ''),
            "category": q.get('category', ''),
            "expected_duration": q.get('expected_duration', 90),
        }

    def get_question_audio(self, session_id: str) -> Optional[bytes]:
        """Gera áudio TTS da pergunta corrente."""
        interview = self._load_interview(session_id)
        if interview is None:
            return None

        questions = interview.get_questions_list() or []
        idx = int(interview.current_question_index or 0)
        if idx >= len(questions):
            return None

        text = questions[idx].get('text', '')
        try:
            return self._generate_question_audio_tts(text)
        except Exception as e:
            logger.error("Erro ao gerar TTS: %s", e)
            return self._generate_audio_placeholder()

    def submit_response(self, session_id: str, audio_data: bytes,
                        content_type: str) -> Dict[str, Any]:
        """Transcreve + analisa áudio e registra em `questions_data`."""
        interview = self._load_interview(session_id)
        if interview is None:
            return {"success": False, "error": "Sessão não encontrada"}

        questions = interview.get_questions_list() or []
        idx = int(interview.current_question_index or 0)
        if idx >= len(questions):
            return {"success": False, "error": "Entrevista já finalizada"}

        try:
            current = questions[idx]

            transcript = self._transcribe_audio(audio_data, content_type)
            if not transcript or not transcript.strip():
                logger.warning("Transcrição vazia para token=%s", session_id)
                return {
                    "success": False,
                    "error": "Áudio sem conteúdo de fala detectado",
                    "detail": (
                        "Por favor, grave novamente garantindo que sua voz "
                        "seja capturada claramente"
                    ),
                }

            from ..utils.ai_analyzer import AIAnalyzer

            analyzer = AIAnalyzer()
            analysis = analyzer.analyze_response(
                question=current.get('text', ''),
                response=transcript,
                position=interview.position,
                rubric_id=current.get('rubric_id'),
                category=current.get('category'),
            )

            current['response'] = transcript
            current['transcription'] = transcript
            current['audio_size_bytes'] = len(audio_data)
            current['content_type'] = content_type
            current['answered_at'] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
            current['analysis'] = analysis
            questions[idx] = current

            interview.set_questions_list(questions)
            interview.current_question_index = idx + 1
            db.session.commit()

            logger.info(
                "Resposta registrada token=%s idx=%s chars=%s",
                session_id, idx, len(transcript),
            )

            return {
                "success": True,
                "question_completed": True,
                "next_question_available": (idx + 1) < len(questions),
                "transcript": transcript,
                "analysis": analysis,
            }
        except Exception as e:
            db.session.rollback()
            logger.error("Erro ao processar resposta token=%s: %s", session_id, e, exc_info=True)
            return {"success": False, "error": str(e)}

    def finalize_interview(self, session_id: str) -> Dict[str, Any]:
        """Gera assessments, recalcula score e marca entrevista concluída."""
        interview = self._load_interview(session_id)
        if interview is None:
            return {"success": False, "error": "Sessão não encontrada"}

        try:
            questions = interview.get_questions_list() or []

            self._materialize_assessments(interview, questions)
            self._apply_aggregate_score(interview)

            interview.complete_interview()
            # complete_interview() chama calculate_overall_score (legado);
            # preservamos o score agregado via rubricas.
            self._apply_aggregate_score(interview)

            db.session.commit()

            report = self._build_report(interview, questions)
            logger.info("Entrevista finalizada token=%s score=%s rec=%s",
                        session_id, interview.overall_score, interview.recommendation)

            return {"success": True, "completed": True, "report": report}
        except Exception as e:
            db.session.rollback()
            logger.error("Erro ao finalizar entrevista token=%s: %s", session_id, e, exc_info=True)
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Geração de assessments auditáveis (Onda 2 — 3.4c)
    # ------------------------------------------------------------------
    def _materialize_assessments(self, interview: Interview,
                                 questions: List[Dict[str, Any]]) -> None:
        """Cria uma linha `interview_assessments` por pergunta respondida."""
        existing = {
            a.question_index
            for a in db.session.query(InterviewAssessment)
            .filter_by(interview_id=interview.id).all()
        }

        for q in questions:
            idx = int(q.get('question_index', 0))
            if idx in existing:
                continue
            analysis = q.get('analysis') or {}
            if not analysis:
                continue

            rubric_id = analysis.get('rubric_id') or q.get('rubric_id') \
                or 'competencies.customer_orientation'
            dimension = analysis.get('dimension') or q.get('dimension') \
                or 'customer_orientation'
            rubric_version = analysis.get('rubric_version') or 'unversioned'

            assess = InterviewAssessment(
                interview_id=interview.id,
                question_index=idx,
                question_text=q.get('text', ''),
                answer_excerpt=analysis.get('evidence_excerpt', ''),
                rubric_id=rubric_id,
                rubric_version=rubric_version,
                dimension=dimension,
                score=analysis.get('score'),
                confidence=analysis.get('confidence') or 0.0,
                model_name=analysis.get('model_name'),
                model_version=analysis.get('model_version'),
                prompt_hash=analysis.get('prompt_hash'),
                human_review_status=analysis.get('human_review_status', 'pending'),
            )
            db.session.add(assess)

        db.session.flush()

    def _apply_aggregate_score(self, interview: Interview) -> None:
        """Recalcula `overall_score`/`recommendation` a partir dos assessments.

        Score da rubrica: 1..5. Conversão: média * 20 → escala 0..100.
        Fallback seguro: se TODOS os assessments têm model_name='fallback',
        não atribuímos `recommendation`.
        """
        assessments = (
            db.session.query(InterviewAssessment)
            .filter_by(interview_id=interview.id)
            .all()
        )

        if not assessments:
            interview.overall_score = 0.0
            interview.recommendation = None
            interview.confidence_level = 0.0
            return

        all_fallback = all(
            (a.model_name or '') == 'fallback' for a in assessments
        )

        scored = [float(a.score) for a in assessments if a.score is not None]
        if scored:
            interview.overall_score = float(round((sum(scored) / len(scored)) * 20.0, 2))
        else:
            interview.overall_score = 0.0

        if all_fallback:
            # LGPD art. 20: sem decisão automática quando não há base
            interview.recommendation = None
            interview.confidence_level = 0.0
            return

        score_val = float(interview.overall_score or 0.0)
        if score_val >= 75:
            interview.recommendation = 'CONTRATAR'
            interview.confidence_level = 0.9
        elif score_val >= 50:
            interview.recommendation = 'CONSIDERAR'
            interview.confidence_level = 0.7
        else:
            interview.recommendation = 'REJEITAR'
            interview.confidence_level = 0.8

    # ------------------------------------------------------------------
    # Relatórios (mantidos, adaptados ao novo payload)
    # ------------------------------------------------------------------
    def _build_report(self, interview: Interview,
                      questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        answered = [q for q in questions if (q.get('transcription') or '').strip()]
        assessments = (
            db.session.query(InterviewAssessment)
            .filter_by(interview_id=interview.id)
            .order_by(InterviewAssessment.question_index.asc())
            .all()
        )

        scores_detail = []
        for a in assessments:
            scores_detail.append({
                'question_index': a.question_index,
                'rubric_id': a.rubric_id,
                'dimension': a.dimension,
                'score': a.score,
                'confidence': a.confidence,
                'model_name': a.model_name,
                'human_review_status': a.human_review_status,
            })

        candidate_name = (
            interview.candidate.full_name if interview.candidate else 'Candidato'
        )

        return {
            'candidate_name': candidate_name,
            'position': interview.position,
            'interview_date': interview.started_at.isoformat()
                if interview.started_at else None,
            'interview_id': interview.id,
            'interview_token': interview.interview_token,
            'total_questions': len(questions),
            'questions_answered': len(answered),
            'completion_rate': round(
                (len(answered) / len(questions) * 100) if questions else 0.0, 1
            ),
            'score_final': round(float(interview.overall_score or 0.0), 1),
            'recomendacao': interview.recommendation,
            'confidence_level': float(interview.confidence_level or 0.0),
            'assessments': scores_detail,
        }

    # ------------------------------------------------------------------
    # TTS / STT (inalterados)
    # ------------------------------------------------------------------
    def _generate_audio_placeholder(self) -> bytes:
        """Gera WAV sintético curto — fallback quando TTS falha."""
        sample_rate = 22050
        duration = 3.0
        channels = 1
        bits_per_sample = 16
        num_samples = int(sample_rate * duration)

        frequencies = [200, 400, 600]
        audio_samples = []
        for i in range(num_samples):
            t = i / sample_rate
            fade = min(1.0, t * 5) * min(1.0, (duration - t) * 5)
            sample = 0.0
            for j, freq in enumerate(frequencies):
                amp = 0.15 / (j + 1) * fade
                sample += amp * math.sin(2 * math.pi * freq * t)
            modulation = 0.02 * math.sin(2 * math.pi * 4 * t)
            sample *= (1 + modulation)
            sample_int = max(-32767, min(32767, int(sample * 32767)))
            audio_samples.append(sample_int)

        audio_data = b''.join(struct.pack('<h', s) for s in audio_samples)
        data_size = len(audio_data)
        chunk_size = 36 + data_size

        wav_header = struct.pack(
            '<4sI4s4sIHHIIHH4sI',
            b'RIFF', chunk_size, b'WAVE',
            b'fmt ', 16, 1, channels, sample_rate,
            sample_rate * channels * bits_per_sample // 8,
            channels * bits_per_sample // 8, bits_per_sample,
            b'data', data_size,
        )
        return wav_header + audio_data

    def _generate_question_audio_tts(self, question_text: str) -> bytes:
        """Gera áudio via OpenAI TTS; fallback em gTTS."""
        logger.info("TTS: '%s...'", (question_text or '')[:50])
        try:
            from ..config.openai_config import (
                OpenAIConfig,
                OpenAIKeyMissingError,
                get_openai_client,
            )
            try:
                client = get_openai_client()
                response = client.audio.speech.create(
                    model=OpenAIConfig.TTS_MODEL,
                    voice=OpenAIConfig.TTS_VOICE,
                    input=question_text,
                    response_format='mp3',
                )
                return response.content
            except OpenAIKeyMissingError as e:
                logger.warning("OpenAI key ausente: %s", e)
                raise Exception("OpenAI key missing")
        except Exception as openai_error:
            logger.warning("TTS OpenAI indisponível: %s — tentando gTTS", openai_error)
            try:
                from gtts import gTTS
                tts = gTTS(text=question_text, lang='pt-br', slow=False)
                buf = io.BytesIO()
                tts.write_to_fp(buf)
                buf.seek(0)
                return buf.read()
            except Exception as gtts_error:
                logger.error("gTTS falhou: %s", gtts_error)
                raise Exception(
                    f"Falha ao gerar áudio: OpenAI ({openai_error}), gTTS ({gtts_error})"
                )

    def _transcribe_audio(self, audio_data: bytes, content_type: str) -> str:
        """Transcreve áudio via OpenAI Whisper; fallback simulado por tamanho."""
        logger.info("STT: %s bytes, content_type=%s", len(audio_data), content_type)
        try:
            from ..config.openai_config import (
                OpenAIConfig,
                OpenAIKeyMissingError,
                get_openai_client,
            )
            try:
                client = get_openai_client()
            except OpenAIKeyMissingError as e:
                logger.warning("OpenAI key ausente: %s", e)
                return self._simulate_transcription(len(audio_data))

            extension = '.mp3'
            ct = (content_type or '').lower()
            if 'wav' in ct:
                extension = '.wav'
            elif 'webm' in ct:
                extension = '.webm'
            elif 'ogg' in ct:
                extension = '.ogg'

            with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as tmp:
                tmp.write(audio_data)
                temp_path = tmp.name
            try:
                with open(temp_path, 'rb') as f:
                    transcript = client.audio.transcriptions.create(
                        model=OpenAIConfig.TRANSCRIPTION_MODEL,
                        file=f,
                        language='pt',
                        response_format='text',
                    )
                text = transcript.strip() if isinstance(transcript, str) else str(transcript).strip()
                return text
            finally:
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
        except Exception as e:
            logger.error("Falha Whisper: %s", e, exc_info=True)
            return self._simulate_transcription(len(audio_data))

    def _simulate_transcription(self, audio_size: int) -> str:
        """Texto sintético proporcional ao tamanho quando Whisper falha."""
        logger.warning("Transcrição simulada para %s bytes", audio_size)
        if audio_size < 5000:
            return ""
        if audio_size < 50000:
            return "Sim, entendo. Tenho experiência com isso."
        return (
            "Sim, tenho experiência trabalhando com essas tecnologias. "
            "Já desenvolvi diversos projetos utilizando essas ferramentas "
            "e me sinto confortável para contribuir com a equipe."
        )


# Instância global do serviço
audio_service = AudioInterviewService()
