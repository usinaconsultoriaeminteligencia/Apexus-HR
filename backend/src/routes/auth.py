# backend/src/routes/auth.py
"""
Rotas de autenticação e autorização
"""
from functools import wraps
from flask import request, jsonify, Blueprint, g
from datetime import datetime, timezone
import os
import logging

import jwt  # pyjwt
from jwt import InvalidTokenError, ExpiredSignatureError
from src.models import db
from src.models.user import User

# Lê do compose: JWT_SECRET_KEY (com fallback seguro para dev)
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
JWT_ALG = "HS256"


def _decode_token(token: str):
    """
    Tenta decodificar o token. Se o modelo User tiver verify_token, usa-o.
    Caso contrário, usa pyjwt diretamente.
    """
    # Caminho preferencial: método do modelo (quando implementado)
    if hasattr(User, "verify_token") and callable(getattr(User, "verify_token")):
        try:
            payload = User.verify_token(token)
            if payload is None:
                return None, {"message": "Token inválido"}
            
            # verify_token retorna o payload, preciso buscar o usuário
            user_id = payload.get("user_id")
            if not user_id:
                return None, {"message": "Token sem user_id"}
            
            user = User.query.get(user_id)
            if not user or (hasattr(user, "is_active") and not user.is_active):
                return None, {"message": "Usuário inválido/inativo"}
            
            return user, None
        except Exception as e:
            logging.exception("Falha ao verificar token via User.verify_token")
            return None, {"message": "Token inválido"}

    # Fallback: pyjwt
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except ExpiredSignatureError:
        return None, {"message": "Token expirado"}
    except InvalidTokenError:
        return None, {"message": "Token inválido"}

    user_id = payload.get("user_id")
    if not user_id:
        return None, {"message": "Token sem user_id"}

    # Busca usuário ativo
    user = User.query.get(user_id)
    if not user or (hasattr(user, "is_active") and not user.is_active):
        return None, {"message": "Usuário inválido/inativo"}

    return user, None


def require_auth(fn):
    """
    Decorator que exige Authorization: Bearer <token>
    Injeta `current_user` no handler:
        @require_auth
        def rota(current_user):
            ...
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Reutiliza autenticação feita pelo middleware global, se houver.
        user = getattr(g, "current_user", None)

        if user is None:
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return jsonify({"success": False, "message": "Credenciais ausentes"}), 401

            token = auth.replace("Bearer ", "").strip()
            user, err = _decode_token(token)
            if err:
                return jsonify({"success": False, "message": err["message"]}), 401

        # Opcional: política de lock/consent/etc.
        if hasattr(user, "is_account_locked") and callable(user.is_account_locked) and user.is_account_locked():
            return jsonify({"success": False, "message": "Conta temporariamente bloqueada"}), 423

        try:
            # injeta current_user como 1º argumento nomeado
            return fn(current_user=user, *args, **kwargs)
        except Exception:
            logging.exception("Erro interno em rota protegida")
            return jsonify({"success": False, "message": "Erro interno do servidor"}), 500

    return wrapper


def generate_jwt_for_user(user, expires_in: int = 86400) -> str:
    """
    Utilitário para gerar token quando o modelo não oferece generate_token.
    Preferencialmente use user.generate_token(expires_in).
    """
    if hasattr(user, "generate_token") and callable(getattr(user, "generate_token")):
        return user.generate_token(expires_in=expires_in)

    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": str(user.id),
        "email": getattr(user, "email", None),
        "role": getattr(user, "role", "user"),
        "iat": int(now.timestamp()),
        "exp": int(now.timestamp()) + int(expires_in),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


# =========================
# ✅ Blueprint público aqui
# =========================
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.get("/health")
def health():
    return jsonify(success=True, status="ok")


@auth_bp.post("/login")
def login():
    """
    Endpoint de login - autentica usuário e retorna JWT token
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400
        
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        
        if not email or not password:
            return jsonify({"success": False, "message": "Email e senha são obrigatórios"}), 400
        
        # Buscar usuário por email
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"success": False, "message": "Credenciais inválidas"}), 401
        
        # Verificar se conta está bloqueada
        if user.is_account_locked():
            return jsonify({"success": False, "message": "Conta temporariamente bloqueada"}), 423
        
        # Verificar senha
        if not user.check_password(password):
            user.record_failed_login()
            db.session.commit()
            return jsonify({"success": False, "message": "Credenciais inválidas"}), 401
        
        # Verificar se usuário está ativo
        if not getattr(user, "is_active", True):
            return jsonify({"success": False, "message": "Conta desativada"}), 401
        
        # Login bem-sucedido
        user.record_login()
        db.session.commit()
        
        # Gerar token JWT
        token = user.generate_token(expires_in=86400)  # 24 horas
        
        return jsonify({
            "success": True,
            "message": "Login realizado com sucesso",
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "timezone": user.timezone,
                "language": user.language
            }
        }), 200
        
    except Exception as e:
        logging.exception("Erro no login")
        return jsonify({"success": False, "message": "Erro interno do servidor"}), 500


@auth_bp.post("/logout")
@require_auth
def logout(current_user):
    """
    Endpoint de logout - invalida token (se implementado blacklist)
    """
    # Por simplicidade, o logout é feito no frontend removendo o token
    # Em produção, considere implementar blacklist de tokens
    return jsonify({"success": True, "message": "Logout realizado com sucesso"}), 200


@auth_bp.get("/me")
@require_auth
def me(current_user):
    # Retorna um payload simples do usuário autenticado
    return jsonify(
        success=True,
        user={
            "id": getattr(current_user, "id", None),
            "email": getattr(current_user, "email", None),
            "full_name": getattr(current_user, "full_name", None),
            "role": getattr(current_user, "role", None),
            "active": getattr(current_user, "is_active", True),
            "last_login": getattr(current_user, "last_login", None),
            "timezone": getattr(current_user, "timezone", None),
            "language": getattr(current_user, "language", None),
        },
    )



