"""
Serviço WebSocket para notificações em tempo real
"""
import logging
from typing import Dict, List, Optional, Any
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# Instância global do SocketIO (será inicializada no main.py)
socketio: Optional[SocketIO] = None

# Armazenar conexões ativas (user_id -> [socket_id])
active_connections: Dict[int, List[str]] = {}


def init_socketio(app):
    """Inicializa SocketIO na aplicação Flask"""
    global socketio
    
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='eventlet',
        logger=True,
        engineio_logger=False
    )
    
    return socketio


def get_socketio() -> Optional[SocketIO]:
    """Retorna instância do SocketIO"""
    return socketio


def emit_to_user(user_id: int, event: str, data: Any):
    """Envia evento para um usuário específico"""
    if not socketio:
        logger.warning("SocketIO não inicializado")
        return False
    
    if user_id not in active_connections:
        logger.debug(f"Usuário {user_id} não está conectado")
        return False
    
    try:
        for socket_id in active_connections[user_id]:
            socketio.emit(event, data, room=socket_id)
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar evento para usuário {user_id}: {e}")
        return False


def emit_to_room(room: str, event: str, data: Any):
    """Envia evento para uma sala específica"""
    if not socketio:
        logger.warning("SocketIO não inicializado")
        return False
    
    try:
        socketio.emit(event, data, room=room)
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar evento para sala {room}: {e}")
        return False


def broadcast(event: str, data: Any):
    """Envia evento para todos os clientes conectados"""
    if not socketio:
        logger.warning("SocketIO não inicializado")
        return False
    
    try:
        socketio.emit(event, data, broadcast=True)
        return True
    except Exception as e:
        logger.error(f"Erro ao fazer broadcast: {e}")
        return False


def register_connection(user_id: int, socket_id: str):
    """Registra nova conexão"""
    if user_id not in active_connections:
        active_connections[user_id] = []
    
    if socket_id not in active_connections[user_id]:
        active_connections[user_id].append(socket_id)
        logger.info(f"Usuário {user_id} conectado (socket: {socket_id})")


def unregister_connection(user_id: int, socket_id: str):
    """Remove conexão"""
    if user_id in active_connections:
        if socket_id in active_connections[user_id]:
            active_connections[user_id].remove(socket_id)
            logger.info(f"Usuário {user_id} desconectado (socket: {socket_id})")
        
        # Remover usuário se não tiver mais conexões
        if not active_connections[user_id]:
            del active_connections[user_id]


def get_connected_users() -> List[int]:
    """Retorna lista de IDs de usuários conectados"""
    return list(active_connections.keys())


def get_user_connections_count(user_id: int) -> int:
    """Retorna número de conexões de um usuário"""
    return len(active_connections.get(user_id, []))


# Handlers de eventos SocketIO
def setup_socketio_handlers(socketio_instance: SocketIO):
    """Configura handlers de eventos SocketIO"""
    
    @socketio_instance.on('connect')
    def handle_connect(auth):
        """Handler para conexão"""
        try:
            # Autenticar usuário via token
            token = auth.get('token') if auth else None
            if not token:
                logger.warning("Conexão sem token")
                return False
            
            # Verificar token (usar mesmo sistema de auth)
            from src.models.user import User
            payload = User.verify_token(token)
            if not payload:
                logger.warning("Token inválido na conexão WebSocket")
                return False
            
            user_id = payload.get('user_id')
            if not user_id:
                return False
            
            # Registrar conexão
            socket_id = request.sid
            register_connection(user_id, socket_id)
            
            # Entrar na sala do usuário
            join_room(f"user_{user_id}")
            
            # Enviar confirmação
            emit('connected', {
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info(f"Usuário {user_id} conectado via WebSocket")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao conectar WebSocket: {e}")
            return False
    
    @socketio_instance.on('disconnect')
    def handle_disconnect():
        """Handler para desconexão"""
        try:
            socket_id = request.sid
            
            # Encontrar e remover conexão
            for user_id, connections in list(active_connections.items()):
                if socket_id in connections:
                    unregister_connection(user_id, socket_id)
                    leave_room(f"user_{user_id}")
                    logger.info(f"Usuário {user_id} desconectado")
                    break
                    
        except Exception as e:
            logger.error(f"Erro ao desconectar WebSocket: {e}")
    
    @socketio_instance.on('join_room')
    def handle_join_room(data):
        """Handler para entrar em uma sala"""
        try:
            room = data.get('room')
            if room:
                join_room(room)
                emit('room_joined', {'room': room})
                logger.debug(f"Cliente entrou na sala: {room}")
        except Exception as e:
            logger.error(f"Erro ao entrar na sala: {e}")
    
    @socketio_instance.on('leave_room')
    def handle_leave_room(data):
        """Handler para sair de uma sala"""
        try:
            room = data.get('room')
            if room:
                leave_room(room)
                emit('room_left', {'room': room})
                logger.debug(f"Cliente saiu da sala: {room}")
        except Exception as e:
            logger.error(f"Erro ao sair da sala: {e}")
    
    @socketio_instance.on('ping')
    def handle_ping():
        """Handler para ping/pong (keepalive)"""
        emit('pong', {'timestamp': datetime.utcnow().isoformat()})
    
    logger.info("Handlers WebSocket configurados")

