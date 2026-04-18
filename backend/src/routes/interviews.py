from flask import Blueprint, request, jsonify
import os, tempfile
import logging
logger = logging.getLogger(__name__)

from ..services.interview_service import InterviewService
from ..services.sharing_service import SharingService
from ..models import db, Interview, Candidate, User
from ..models.assessment import InterviewAssessment
from ..utils.db_retry import retry_db_operation
from ..utils.type_helpers import as_float, as_str, as_int, dt_iso, safe_bool
from .auth import require_auth

bp = Blueprint("interviews", __name__, url_prefix="/interviews")
# Alias sob /api/interviews/* para manter contrato com o frontend. Só
# expõe as rotas explicitamente re-registradas ao final do arquivo —
# não é um espelho completo do blueprint principal.
bp_api = Blueprint("interviews_api", __name__, url_prefix="/api/interviews")
svc = InterviewService()
sharing_svc = SharingService()

# Papéis autorizados a ver a trilha de auditoria dos assessments.
# 'viewer'/'analyst' enxergam a lista, mas sem evidências textuais (ver
# InterviewAssessment.to_dict(include_evidence=False)).
_ASSESSMENT_READ_ROLES = {"admin", "recruiter", "manager", "analyst", "viewer"}
_ASSESSMENT_EVIDENCE_ROLES = {"admin", "recruiter", "manager"}

@bp.get("")
@retry_db_operation(max_retries=3, delay=1)
def list_interviews():
    """Lista todas as entrevistas do sistema"""
    try:
        # Busca entrevistas com dados relacionados usando Flask-SQLAlchemy
        interviews = db.session.query(Interview)\
            .join(Candidate, Interview.candidate_id == Candidate.id)\
            .join(User, Interview.interviewer_id == User.id)\
            .filter(Interview.status.in_(['concluida', 'em_andamento', 'agendada']))\
            .order_by(Interview.created_at.desc())\
            .all()
        
        result = []
        for interview in interviews:
            candidate = interview.candidate
            interviewer = interview.interviewer
            
            # Converte dados para formato do frontend
            interview_data = {
                "id": interview.id,
                "candidate_name": candidate.full_name,
                "candidate_email": candidate.email,
                "position": interview.position,
                "interview_type": interview.interview_type,
                "status": interview.status,
                "scheduled_at": dt_iso(interview.scheduled_at),
                "started_at": dt_iso(interview.started_at),
                "completed_at": dt_iso(interview.completed_at),
                "duration_minutes": interview.duration_minutes,
                "overall_score": as_float(interview.overall_score),
                "recommendation": interview.recommendation,
                "confidence_level": as_float(interview.confidence_level),
                "interviewer_name": interviewer.full_name,
                
                # Scores detalhados (usando dados do candidato como fallback)
                "technical_score": as_float(candidate.technical_score),
                "behavioral_score": as_float(candidate.behavioral_score),
                "communication_score": as_float(interview.communication_skills),
                "confidence_score": as_float(interview.confidence_score),
                "enthusiasm_score": as_float(interview.enthusiasm_score),
                "clarity_score": as_float(interview.clarity_score),
                
                # Dados de áudio
                "audio_quality_score": as_float(interview.audio_quality_score),
                "speech_rate": as_float(interview.speech_rate),
                "voice_stability": as_float(interview.voice_stability),
                "transcription_available": safe_bool(interview.transcription),
                
                # Campos extras para compatibilidade
                "created_at": dt_iso(interview.created_at),
                "ai_insights": interview.ai_insights,
                "interviewer_notes": interview.interviewer_notes
            }
            result.append(interview_data)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Erro ao buscar entrevistas: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@bp.post("/start")
def start():
    data = request.json or {}
    candidate_id = data.get("candidate_id")
    interviewer_id = data.get("interviewer_id", 1)
    position = data.get("position")
    if not candidate_id or not position:
        return jsonify({"error": "candidate_id e position são obrigatórios"}), 400

    try:
        interview = svc.create_interview(db.session, candidate_id, interviewer_id, position, interview_type="audio")
        payload = svc.start_interview(db.session, interview.id)
        return jsonify(payload), 201
    except Exception as e:
        logger.error(f"Erro ao iniciar entrevista: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@bp.get("/<int:interview_id>/next")
def next_question(interview_id: int):
    try:
        payload = svc.get_next_question(db.session, interview_id)
        if not payload:
            return jsonify({"finished": True, "message": "Entrevista finalizada"}), 200
        return jsonify(payload)
    except Exception as e:
        logger.error(f"Erro ao buscar próxima pergunta: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@bp.post("/<int:interview_id>/respond")
def respond(interview_id: int):
    response_text = request.form.get("text", "")
    audio_path = None
    if "audio" in request.files:
        f = request.files["audio"]
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        f.save(tmp.name)
        tmp.close()
        audio_path = tmp.name

    try:
        payload = svc.process_response(db.session, interview_id, response_text=response_text, audio_file_path=audio_path)
        return jsonify(payload)
    finally:
        if audio_path and os.path.exists(audio_path):
            try:
                os.unlink(audio_path)
            except Exception:
                pass

@bp.post("/<int:interview_id>/finalize")
def finalize(interview_id: int):
    try:
        payload = svc.finalize_interview(db.session, interview_id)
        return jsonify(payload)
    except Exception as e:
        logger.error(f"Erro ao finalizar entrevista: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@bp.get("/<int:interview_id>/status")
def status(interview_id: int):
    try:
        itv = db.session.query(Interview).filter(Interview.id == interview_id).first()
        if not itv:
            return jsonify({"error": "Entrevista não encontrada"}), 404
        qs = itv.get_questions_list() or []
        return jsonify({
            "interview_id": interview_id,
            "position": itv.position,
            "current_index": itv.current_question_index,
            "total_questions": len(qs),
            "status": itv.status,
        })
    except Exception as e:
        logger.error(f"Erro ao buscar status da entrevista: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@bp.get("/<int:interview_id>")
@retry_db_operation(max_retries=3, delay=1)
def get_interview(interview_id: int):
    """Busca uma entrevista específica com todos os detalhes"""
    try:
        interview = db.session.query(Interview)\
            .join(Candidate, Interview.candidate_id == Candidate.id)\
            .join(User, Interview.interviewer_id == User.id)\
            .filter(Interview.id == interview_id)\
            .first()
        
        if not interview:
            return jsonify({"error": "Entrevista não encontrada"}), 404
        
        candidate = interview.candidate
        interviewer = interview.interviewer
        
        # Retorna dados completos da entrevista
        result = {
            "id": interview.id,
            "candidate_name": candidate.full_name,
            "candidate_email": candidate.email,
            "position": interview.position,
            "interview_type": interview.interview_type,
            "status": interview.status,
            "scheduled_at": interview.scheduled_at.isoformat() if interview.scheduled_at is not None else None,
            "started_at": interview.started_at.isoformat() if interview.started_at is not None else None,
            "completed_at": interview.completed_at.isoformat() if interview.completed_at is not None else None,
            "duration_minutes": interview.duration_minutes,
            "overall_score": as_float(interview.overall_score),
            "recommendation": interview.recommendation,
            "confidence_level": as_float(interview.confidence_level),
            "interviewer_name": interviewer.full_name,
            
            # Dados completos da análise
            "technical_score": as_float(candidate.technical_score),
            "behavioral_score": as_float(candidate.behavioral_score),
            "communication_score": as_float(interview.communication_skills),
            "confidence_score": as_float(interview.confidence_score),
            "enthusiasm_score": as_float(interview.enthusiasm_score),
            "clarity_score": as_float(interview.clarity_score),
            "content_relevance": as_float(interview.content_relevance),
            "technical_accuracy": as_float(interview.technical_accuracy),
            
            # Análise de áudio
            "audio_quality_score": as_float(interview.audio_quality_score),
            "speech_rate": as_float(interview.speech_rate),
            "voice_stability": as_float(interview.voice_stability),
            "pause_frequency": as_float(interview.pause_frequency),
            "nervousness_score": as_float(interview.nervousness_score),
            
            # Dados textuais
            "transcription": interview.transcription,
            "transcription_available": bool(interview.transcription if interview.transcription is not None else False),
            "ai_insights": interview.ai_insights,
            "interviewer_notes": interview.interviewer_notes,
            "next_steps": interview.next_steps,
            
            # Perguntas e respostas
            "questions_data": interview.questions_data,
            "current_question_index": interview.current_question_index,
            "total_questions": interview.total_questions,
            
            # Metadados
            "created_at": interview.created_at.isoformat() if interview.created_at is not None else None,
            "audio_file_path": interview.audio_file_path
        }
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Erro ao buscar entrevista: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@bp.post("/create-and-share")
@retry_db_operation(max_retries=3, delay=1)
def create_and_share():
    """Cria nova entrevista e envia convite ao candidato"""
    try:
        data = request.json or {}
        
        # Dados obrigatórios
        candidate_id = data.get("candidate_id")
        interviewer_id = data.get("interviewer_id", 1)
        position = data.get("position")
        channel = data.get("channel", "email")  # email, sms, whatsapp, link
        
        # Dados opcionais
        email = data.get("email")
        phone = data.get("phone")
        custom_message = data.get("custom_message")
        expiration_hours = data.get("expiration_hours", 48)
        
        # Validações
        if not candidate_id or not position:
            return jsonify({"error": "candidate_id e position são obrigatórios"}), 400
        
        if channel == "email" and not email:
            return jsonify({"error": "Email é obrigatório para envio por email"}), 400
        
        if channel in ["sms", "whatsapp"] and not phone:
            return jsonify({"error": "Telefone é obrigatório para envio por SMS/WhatsApp"}), 400
        
        # Criar entrevista
        interview = svc.create_interview(
            db.session,
            candidate_id=candidate_id,
            interviewer_id=interviewer_id,
            position=position,
            interview_type="audio"
        )
        
        # Compartilhar entrevista
        success, message, share_link = sharing_svc.create_and_share_interview(
            db=db.session,
            interview_id=interview.id,
            channel=channel,
            email=email,
            phone=phone,
            custom_message=custom_message,
            expiration_hours=expiration_hours
        )
        
        if not success:
            return jsonify({"error": message}), 400
        
        # Retornar resposta com dados da entrevista e link
        response_data = {
            "success": True,
            "message": message,
            "interview_id": interview.id,
            "share_link": share_link,
            "channel": channel,
            "token": interview.interview_token,
            "expires_at": dt_iso(interview.token_expires_at)
        }
        
        # Se for WhatsApp, retornar o link do WhatsApp
        if channel == "whatsapp":
            response_data["whatsapp_link"] = message
        
        return jsonify(response_data), 201
        
    except Exception as e:
        logger.error(f"Erro ao criar e compartilhar entrevista: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@bp.get("/public/<token>")
def get_public_interview(token: str):
    """Acessa entrevista via token público (sem autenticação)"""
    try:
        # Validar token
        is_valid, interview, message = sharing_svc.validate_token_access(
            db=db.session,
            token=token
        )
        
        if not is_valid:
            return jsonify({"error": message}), 403
        
        # Buscar dados do candidato
        if interview is None:
            return jsonify({"error": "Entrevista inválida"}), 404
        candidate = interview.candidate if interview else None
        
        # Retornar dados públicos da entrevista
        result = {
            "success": True,
            "interview": {
                "id": interview.id,
                "position": interview.position,
                "candidate_name": candidate.full_name if candidate else "Candidato",
                "status": interview.status,
                "interview_type": interview.interview_type,
                "total_questions": interview.total_questions,
                "current_question_index": interview.current_question_index,
                "progress_percentage": interview.get_progress_percentage(),
                "questions_data": interview.get_questions_list() if as_str(interview.status) == "em_andamento" else None,
                "scheduled_at": dt_iso(interview.scheduled_at)
            },
            "token_info": {
                "expires_at": dt_iso(interview.token_expires_at),
                "access_count": as_int(interview.token_access_count),
                "first_accessed_at": dt_iso(interview.token_accessed_at)
            },
            "can_start": as_str(interview.status) == "agendada" if interview else False,
            "can_continue": as_str(interview.status) == "em_andamento" if interview else False,
            "is_completed": as_str(interview.status) == "concluida" if interview else False
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Erro ao acessar entrevista pública: {e}")
        return jsonify({"error": "Erro ao acessar entrevista"}), 500

@bp.post("/<int:interview_id>/resend")
@retry_db_operation(max_retries=3, delay=1)
def resend_invitation(interview_id: int):
    """Reenvia convite de entrevista"""
    try:
        success, message = sharing_svc.resend_invitation(
            db=db.session,
            interview_id=interview_id
        )
        
        if not success:
            return jsonify({"error": message}), 400
        
        return jsonify({
            "success": True,
            "message": message
        })
        
    except Exception as e:
        logger.error(f"Erro ao reenviar convite: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@bp.get("/<int:interview_id>/share-link")
@retry_db_operation(max_retries=3, delay=1)
def get_share_link(interview_id: int):
    """Obtém link compartilhável da entrevista"""
    try:
        interview = db.session.query(Interview).filter(Interview.id == interview_id).first()
        
        if not interview:
            return jsonify({"error": "Entrevista não encontrada"}), 404
        
        # Gerar token se não existir
        if interview.interview_token is None:
            interview.generate_interview_token()
            db.session.commit()
        
        # Verificar validade do token
        if safe_bool(interview.is_token_valid()) == False:
            # Regenerar se expirado
            interview.generate_interview_token()
            db.session.commit()
        
        # Obter URL pública
        base_url = os.environ.get('APP_BASE_URL', 'http://localhost:5000')
        public_url = interview.get_public_url(base_url)
        
        return jsonify({
            "success": True,
            "share_link": public_url,
            "token": interview.interview_token,
            "expires_at": dt_iso(interview.token_expires_at),
            "is_valid": interview.is_token_valid()
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter link compartilhável: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

def _list_assessments_payload(current_user, interview_id: int):
    """Implementação compartilhada pelas rotas de listagem de assessments.

    - admin/recruiter/manager: payload completo com evidência textual
      (question_text, answer_excerpt, human_review_notes).
    - analyst/viewer: lista reduzida, sem evidência textual.
    - outros papéis: 403.
    """
    role = getattr(current_user, "role", None)
    if role not in _ASSESSMENT_READ_ROLES:
        return jsonify({"success": False, "error": "forbidden"}), 403

    interview = db.session.query(Interview).filter(Interview.id == interview_id).first()
    if interview is None:
        return jsonify({"success": False, "error": "Entrevista não encontrada"}), 404

    include_evidence = role in _ASSESSMENT_EVIDENCE_ROLES

    assessments = (
        db.session.query(InterviewAssessment)
        .filter(InterviewAssessment.interview_id == interview_id)
        .order_by(InterviewAssessment.question_index.asc())
        .all()
    )

    return jsonify({
        "success": True,
        "interview_id": interview_id,
        "overall_score": as_float(interview.overall_score),
        "recommendation": interview.recommendation,
        "assessments": [
            a.to_dict(include_evidence=include_evidence) for a in assessments
        ],
    })


@bp.get("/<int:interview_id>/assessments")
@require_auth
def list_assessments(current_user, interview_id: int):
    """Lista assessments auditáveis de uma entrevista (Onda 2 — 3.4d)."""
    return _list_assessments_payload(current_user, interview_id)


@bp_api.get("/<int:interview_id>/assessments")
@require_auth
def list_assessments_api(current_user, interview_id: int):
    """Alias sob /api/interviews/<id>/assessments (mesma semântica de
    list_assessments). Mantido para compatibilidade com o frontend que
    consome /api/*."""
    return _list_assessments_payload(current_user, interview_id)


@bp.post("/<int:interview_id>/share")
@retry_db_operation(max_retries=3, delay=1)
def share_interview(interview_id: int):
    """Compartilha entrevista existente com candidato"""
    try:
        data = request.json or {}
        
        channel = data.get("channel", "email")
        email = data.get("email")
        phone = data.get("phone")
        custom_message = data.get("custom_message")
        
        # Validações
        if channel == "email" and not email:
            return jsonify({"error": "Email é obrigatório para envio por email"}), 400
        
        if channel in ["sms", "whatsapp"] and not phone:
            return jsonify({"error": "Telefone é obrigatório para envio por SMS/WhatsApp"}), 400
        
        # Compartilhar entrevista
        success, message, share_link = sharing_svc.create_and_share_interview(
            db=db.session,
            interview_id=interview_id,
            channel=channel,
            email=email,
            phone=phone,
            custom_message=custom_message
        )
        
        if not success:
            return jsonify({"error": message}), 400
        
        # Retornar resposta
        response_data = {
            "success": True,
            "message": message,
            "share_link": share_link,
            "channel": channel
        }
        
        # Se for WhatsApp, retornar o link do WhatsApp
        if channel == "whatsapp":
            response_data["whatsapp_link"] = message
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Erro ao compartilhar entrevista: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500


# ---------------------------------------------------------------------------
# Rotas adicionais — criação simplificada, ciclo de vida e upload de áudio
# ---------------------------------------------------------------------------

@bp.post("")
@retry_db_operation(max_retries=3, delay=1)
def create_interview():
    """Cria uma nova entrevista agendada.

    Body JSON: {candidate_id, position, interview_type?, scheduled_at?}
    Retorna 201 com os dados da entrevista criada.
    """
    data = request.json or {}
    candidate_id = data.get("candidate_id")
    position = data.get("position")

    if not candidate_id or not position:
        return jsonify({"error": "candidate_id e position são obrigatórios"}), 400

    try:
        from datetime import datetime, timezone
        from ..utils.type_helpers import dt_iso

        candidate = db.session.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            return jsonify({"error": "Candidato não encontrado"}), 404

        scheduled_raw = data.get("scheduled_at")
        scheduled_at = None
        if scheduled_raw:
            try:
                scheduled_at = datetime.fromisoformat(scheduled_raw.replace("Z", "+00:00"))
                scheduled_at = scheduled_at.replace(tzinfo=None)
            except ValueError:
                return jsonify({"error": "scheduled_at inválido — use ISO 8601"}), 400

        interview = Interview(
            candidate_id=candidate_id,
            interviewer_id=data.get("interviewer_id", 1),
            interview_type=data.get("interview_type", "audio"),
            position=position,
            scheduled_at=scheduled_at,
            status="agendada",
            is_active=True,
            consent_given=True,
        )
        db.session.add(interview)
        db.session.commit()

        return jsonify({
            "id": interview.id,
            "candidate_id": interview.candidate_id,
            "position": interview.position,
            "interview_type": interview.interview_type,
            "status": interview.status,
            "scheduled_at": dt_iso(interview.scheduled_at),
            "created_at": dt_iso(interview.created_at),
        }), 201

    except Exception as e:
        logger.error(f"Erro ao criar entrevista: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500


@bp.post("/<int:interview_id>/start")
@retry_db_operation(max_retries=3, delay=1)
def start_interview(interview_id: int):
    """Inicia uma entrevista agendada (status → em_andamento)."""
    try:
        from datetime import datetime, timezone
        from ..utils.type_helpers import dt_iso

        interview = db.session.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            return jsonify({"error": "Entrevista não encontrada"}), 404

        interview.status = "em_andamento"
        interview.started_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.session.commit()

        return jsonify({
            "id": interview.id,
            "status": interview.status,
            "started_at": dt_iso(interview.started_at),
        })

    except Exception as e:
        logger.error(f"Erro ao iniciar entrevista {interview_id}: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500


@bp.post("/<int:interview_id>/questions")
@retry_db_operation(max_retries=3, delay=1)
def add_question_response(interview_id: int):
    """Adiciona um par pergunta/resposta à entrevista.

    Body JSON: {question, response}
    Retorna 201 com {question, response, index}.
    """
    data = request.json or {}
    question_text = data.get("question", "").strip()
    response_text = data.get("response", "").strip()

    if not question_text or not response_text:
        return jsonify({"error": "question e response são obrigatórios"}), 400

    try:
        import json as _json
        from src.services.ai_service import analyze_interview_response

        interview = db.session.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            return jsonify({"error": "Entrevista não encontrada"}), 404

        questions = interview.get_questions_list() or []
        analysis = analyze_interview_response(
            question=question_text,
            response=response_text,
            position=as_str(interview.position),
        )
        entry = {
            "index": len(questions),
            "question": question_text,
            "response": response_text,
            "analysis": analysis,
        }
        questions.append(entry)
        interview.questions_data = _json.dumps(questions, ensure_ascii=False)
        interview.current_question_index = len(questions)
        db.session.commit()

        return jsonify({
            "question": question_text,
            "response": response_text,
            "index": entry["index"],
        }), 201

    except Exception as e:
        logger.error(f"Erro ao adicionar pergunta na entrevista {interview_id}: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500


@bp.post("/<int:interview_id>/complete")
@retry_db_operation(max_retries=3, delay=1)
def complete_interview(interview_id: int):
    """Finaliza uma entrevista (status → concluida) e calcula o score geral."""
    try:
        from datetime import datetime, timezone
        from src.services.ai_service import calculate_overall_score
        from ..utils.type_helpers import dt_iso

        interview = db.session.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            return jsonify({"error": "Entrevista não encontrada"}), 404

        questions = interview.get_questions_list() or []
        overall = calculate_overall_score(questions)

        interview.status = "concluida"
        interview.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        interview.overall_score = overall if overall > 0 else 5.0
        interview.recommendation = (
            "contratar" if overall >= 7.5
            else "aguardar" if overall >= 5.5
            else "não contratar"
        )
        db.session.commit()

        return jsonify({
            "id": interview.id,
            "status": interview.status,
            "completed_at": dt_iso(interview.completed_at),
            "overall_score": interview.overall_score,
            "recommendation": interview.recommendation,
        })

    except Exception as e:
        logger.error(f"Erro ao completar entrevista {interview_id}: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500


_ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg", ".webm", ".m4a", ".flac"}
_MAX_AUDIO_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


@bp.post("/<int:interview_id>/upload-audio")
def upload_audio(interview_id: int):
    """Recebe upload de arquivo de áudio para uma entrevista.

    Valida extensão e tamanho; salva em UPLOAD_FOLDER.
    Retorna {file_path, size_bytes}.
    """
    import uuid
    from pathlib import Path as _Path
    from flask import current_app

    interview = db.session.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        return jsonify({"error": "Entrevista não encontrada"}), 404

    if "audio" not in request.files:
        return jsonify({"error": "Arquivo 'audio' não enviado"}), 400

    file = request.files["audio"]
    original_name = file.filename or ""
    ext = _Path(original_name).suffix.lower()

    if ext not in _ALLOWED_AUDIO_EXTENSIONS:
        return jsonify({
            "error": f"Tipo de arquivo inválido '{ext}'. "
                     f"Permitidos: {', '.join(_ALLOWED_AUDIO_EXTENSIONS)}"
        }), 400

    # Lê em memória para verificar tamanho antes de gravar
    audio_bytes = file.read()
    if len(audio_bytes) > _MAX_AUDIO_SIZE_BYTES:
        return jsonify({
            "error": f"Arquivo muito grande ({len(audio_bytes) // (1024*1024)} MB). "
                     f"Limite: {_MAX_AUDIO_SIZE_BYTES // (1024*1024)} MB"
        }), 413

    upload_dir = _Path(current_app.config.get("UPLOAD_FOLDER", "/tmp/uploads"))
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = f"interview_{interview_id}_{uuid.uuid4().hex}{ext}"
    file_path = upload_dir / filename
    file_path.write_bytes(audio_bytes)

    interview.audio_file_path = str(file_path)
    db.session.commit()

    return jsonify({
        "file_path": str(file_path),
        "size_bytes": len(audio_bytes),
    })
