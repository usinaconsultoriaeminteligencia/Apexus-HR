# backend/src/routes/audio_interview.py
import os
import uuid
import logging
from flask import Blueprint, request, jsonify, Response
from src.services.audio_interview_service import audio_service

bp = Blueprint("audio_interview", __name__, url_prefix="/api/audio-interview")
log = logging.getLogger(__name__)


@bp.route("/start", methods=["POST"])
def start():
    """Inicia uma nova entrevista por áudio"""
    try:
        data = request.get_json(silent=True) or {}
        candidate_name = data.get('candidate_name', '').strip()
        position = data.get('position', '').strip()
        
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
        
        result = audio_service.start_interview(candidate_name, position)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        log.error(f"Erro ao iniciar entrevista: {e}")
        return jsonify({
            "success": False,
            "error": "Erro interno do servidor"
        }), 500


@bp.route("/<session_id>/question/info", methods=["GET"])
def question_info(session_id):
    """Retorna informações da pergunta atual"""
    try:
        result = audio_service.get_question_info(session_id)
        return jsonify(result), 200
    except Exception as e:
        log.error(f"Erro ao buscar informações da pergunta: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500


@bp.route("/<session_id>/question", methods=["GET"])
def question_audio(session_id):
    """Retorna áudio da pergunta atual"""
    try:
        audio_data = audio_service.get_question_audio(session_id)
        
        if audio_data is None:
            return jsonify({"error": "Pergunta não encontrada"}), 404
        
        # Detecta formato do áudio
        content_type = 'audio/wav'
        if audio_data.startswith(b'ID3') or audio_data.startswith(b'\xff\xfb'):
            content_type = 'audio/mpeg'  # MP3
        
        return Response(
            audio_data,
            mimetype=content_type,
            headers={
                'Content-Type': content_type,
                'Content-Length': str(len(audio_data))
            }
        )
    except Exception as e:
        log.error(f"Erro ao buscar áudio da pergunta: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500


@bp.route("/<session_id>/respond", methods=["POST"])
def respond(session_id):
    """Processa resposta em áudio do candidato"""
    try:
        # Obtém dados de áudio do request
        raw = request.get_data()
        
        # Validação de tamanho do arquivo (máximo 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if len(raw) > max_size:
            return jsonify({
                "error": "Arquivo de áudio muito grande",
                "detail": f"Tamanho máximo permitido: {max_size // (1024*1024)}MB"
            }), 413
        
        # Validação de tipo de conteúdo
        content_type = request.headers.get("Content-Type", "")
        if not content_type.startswith("audio/") and content_type != "application/octet-stream":
            return jsonify({
                "error": "Tipo de conteúdo inválido",
                "detail": "Esperado: audio/* ou application/octet-stream"
            }), 400
        
        if len(raw) == 0:
            return jsonify({
                "error": "Arquivo de áudio vazio"
            }), 400
        
        result = audio_service.submit_response(session_id, raw, content_type)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        log.error(f"Erro ao processar resposta: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500


@bp.route("/<session_id>/finalize", methods=["POST"])
def finalize(session_id):
    """Finaliza a entrevista e gera relatório"""
    try:
        result = audio_service.finalize_interview(session_id)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        log.error(f"Erro ao finalizar entrevista: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500
