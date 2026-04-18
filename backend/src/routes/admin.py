from flask import Blueprint, jsonify

from ..models import db
from ..models.user import User
from .auth import require_auth

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/health")
def health():
    """Health check básico para admin"""
    return jsonify({"status": "ok", "message": "Admin API funcionando"})


@admin_bp.get("/users")
@require_auth
def list_users(current_user):
    """Lista todos os usuários do sistema (somente admin).

    Retorna 403 para qualquer papel que não seja 'admin'.
    """
    if getattr(current_user, "role", None) != "admin":
        return jsonify({"error": "Acesso negado — requer papel admin"}), 403

    users = db.session.query(User).filter(User.is_active == True).all()
    return jsonify([
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "is_active": u.is_active,
            "is_verified": u.is_verified,
            "last_login": u.last_login.isoformat() if u.last_login else None,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ])
