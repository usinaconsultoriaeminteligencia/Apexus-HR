"""
Rotas WebSocket para notificações em tempo real
"""
from flask import Blueprint, request
from flask_socketio import emit
from src.routes.auth import require_auth
from src.services.websocket_service import get_socketio, emit_to_user, broadcast

bp = Blueprint("websocket", __name__, url_prefix="/api/ws")


@bp.route("/status")
def websocket_status():
    """Endpoint para verificar status do WebSocket"""
    socketio = get_socketio()
    return {
        'status': 'available' if socketio else 'unavailable',
        'connected_users': len(get_connected_users()) if socketio else 0
    }

