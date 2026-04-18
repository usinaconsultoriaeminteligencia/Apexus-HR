"""
Rotas para salvar avaliações de entrevistas
"""
from flask import Blueprint, request, jsonify
from ..models import db, Interview, Candidate, User
from datetime import datetime, timezone
import logging
import json

bp = Blueprint("assessments", __name__, url_prefix="/api/assessments")
logger = logging.getLogger(__name__)


@bp.route("/save", methods=["POST"])
def save_assessment():
    """
    Salva resultado de avaliação de entrevista por áudio
    
    Expected payload:
    {
        "candidateName": "João Silva",
        "position": "Desenvolvedor Backend",
        "seniority": "Pleno",
        "sessionId": "uuid-da-sessao",
        "result": {
            "pontuacao_tecnica": 8,
            "pontuacao_comportamental": 7,
            "perfil_disc": "D - Dominância",
            "pontos_fortes": [...],
            "areas_desenvolvimento": [...],
            "recomendacao": "CONTRATAR",
            "score_final": 85,
            "feedback_detalhado": "..."
        },
        "transcript": ["pergunta 1", "resposta 1", ...]
    }
    """
    try:
        data = request.get_json(silent=True) or {}
        
        candidate_name = data.get('candidateName', '').strip()
        position = data.get('position', '').strip()
        seniority = data.get('seniority', 'Pleno')
        session_id = data.get('sessionId')
        result = data.get('result', {})
        transcript_list = data.get('transcript', [])
        
        # Validações
        if not candidate_name:
            return jsonify({
                "success": False,
                "error": "Nome do candidato é obrigatório"
            }), 400
            
        if not position:
            return jsonify({
                "success": False,
                "error": "Posição é obrigatória"
            }), 400
        
        if not result:
            return jsonify({
                "success": False,
                "error": "Resultado da avaliação é obrigatório"
            }), 400
        
        # Busca ou cria candidato
        candidate = db.session.query(Candidate).filter(
            Candidate.full_name == candidate_name
        ).first()
        
        if not candidate:
            # Gera email temporário seguro (remove acentos e caracteres especiais)
            import unicodedata
            import re
            
            # Normaliza nome removendo acentos
            normalized = unicodedata.normalize('NFKD', candidate_name)
            ascii_name = normalized.encode('ASCII', 'ignore').decode('ASCII')
            # Remove caracteres não alfanuméricos e substitui espaços por pontos
            safe_name = re.sub(r'[^a-zA-Z0-9\s]', '', ascii_name.lower())
            safe_name = re.sub(r'\s+', '.', safe_name.strip())
            
            # Gera email único com timestamp se necessário
            base_email = f"{safe_name}@temp.com"
            email = base_email
            counter = 1
            
            while db.session.query(Candidate).filter(Candidate.email == email).first():
                email = f"{safe_name}.{counter}@temp.com"
                counter += 1
            
            # Cria novo candidato
            candidate = Candidate(
                full_name=candidate_name,
                email=email,
                phone="",
                position=position,
                status='em_processo'
            )
            db.session.add(candidate)
            db.session.flush()  # Obtém ID do candidato
            logger.info(f"Novo candidato criado: {candidate_name} (ID: {candidate.id})")
        
        # Busca usuário admin/system como interviewer
        interviewer = db.session.query(User).filter(
            User.role == 'admin'
        ).first()
        
        if not interviewer:
            # Se não encontrar admin, pega o primeiro usuário
            interviewer = db.session.query(User).first()
            
        if not interviewer:
            return jsonify({
                "success": False,
                "error": "Nenhum usuário encontrado no sistema"
            }), 500
        
        # Cria ou atualiza entrevista
        interview = None
        if session_id:
            # Tenta encontrar entrevista existente pelo session_id (pode estar no interview_token)
            interview = db.session.query(Interview).filter(
                Interview.interview_token == session_id
            ).first()
        
        if not interview:
            # Cria nova entrevista
            interview = Interview(
                candidate_id=candidate.id,
                interviewer_id=interviewer.id,
                position=position,
                interview_type='audio',
                status='concluida',
                interview_token=session_id
            )
            db.session.add(interview)
            logger.info(f"Nova entrevista criada para candidato {candidate_name}")
        
        # Atualiza dados da entrevista com resultados
        interview.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Scores
        interview.overall_score = float(result.get('score_final', 0))
        interview.confidence_score = float(result.get('pontuacao_comportamental', 0))
        
        # Recomendação
        recomendacao = result.get('recomendacao', '').upper()
        if recomendacao == 'CONTRATAR':
            interview.recommendation = 'CONTRATAR'
        elif recomendacao == 'CONSIDERAR':
            interview.recommendation = 'CONSIDERAR'
        else:
            interview.recommendation = 'REJEITAR'
        
        # Confidence level baseado no score
        if interview.overall_score >= 80:
            interview.confidence_level = 0.9
        elif interview.overall_score >= 60:
            interview.confidence_level = 0.7
        else:
            interview.confidence_level = 0.5
        
        # Análise de IA usando método do modelo (já faz json.dumps internamente)
        ai_insights_data = {
            'perfil_disc': result.get('perfil_disc', ''),
            'pontos_fortes': result.get('pontos_fortes', []),
            'areas_desenvolvimento': result.get('areas_desenvolvimento', []),
            'feedback_detalhado': result.get('feedback_detalhado', ''),
            'pontuacao_tecnica': result.get('pontuacao_tecnica', 0),
            'pontuacao_comportamental': result.get('pontuacao_comportamental', 0),
            'seniority': seniority,
            'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
        }
        
        # Usa método do modelo Interview para salvar (já faz json.dumps)
        interview.set_ai_insights_dict(ai_insights_data)
        
        # Transcrição
        if transcript_list:
            interview.transcription = '\n'.join([
                str(item) for item in transcript_list if item
            ])
        
        # Atualiza scores do candidato
        candidate.technical_score = float(result.get('pontuacao_tecnica', 0))
        candidate.behavioral_score = float(result.get('pontuacao_comportamental', 0))
        
        # Define status do candidato baseado na recomendação
        if interview.recommendation == 'CONTRATAR':
            candidate.status = 'aprovado'
        elif interview.recommendation == 'CONSIDERAR':
            candidate.status = 'em_processo'
        else:
            candidate.status = 'reprovado'
        
        # Salva no banco
        db.session.commit()
        
        logger.info(f"Avaliação salva com sucesso - Candidato: {candidate_name}, "
                   f"Score: {interview.overall_score}, Recomendação: {interview.recommendation}")
        
        return jsonify({
            "success": True,
            "message": "Avaliação salva com sucesso",
            "interview_id": interview.id,
            "candidate_id": candidate.id,
            "recommendation": interview.recommendation,
            "overall_score": interview.overall_score
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao salvar avaliação: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "Erro interno ao salvar avaliação"
        }), 500
