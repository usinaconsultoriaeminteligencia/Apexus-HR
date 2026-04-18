from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from src.models import db
from src.models.user import User

bp = Blueprint("users", __name__, url_prefix="/users")  # <-- sem strict_slashes

@bp.get("/ping")
def ping_users():
    return jsonify({"message": "users blueprint ativo"}), 200

def _user_from_json(data):
    user = User(
        email=data["email"],
        full_name=data.get("full_name", ""),
        role=data.get("role", "viewer"),
        is_verified=bool(data.get("is_verified", False)),
    )
    if "password" in data and data["password"]:
        user.set_password(data["password"])
    return user

@bp.post("")
def create_user():
    data = request.get_json(force=True, silent=True) or {}
    required = ["email", "full_name", "password"]
    missing = [k for k in required if not data.get(k)]
    if missing:
        return jsonify({"error": f"Missing: {', '.join(missing)}"}), 400
    user = _user_from_json(data)
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "email already exists"}), 409
    return jsonify(user.to_dict(include_sensitive=True)), 201

@bp.get("")
def list_users():
    q = User.query.filter_by(is_active=True)
    return jsonify([u.to_dict() for u in q.order_by(User.id.desc()).all()])

@bp.get("/<int:user_id>")
def get_user(user_id):
    u = User.query.get_or_404(user_id)
    return jsonify(u.to_dict(include_sensitive=True))

@bp.patch("/<int:user_id>")
def update_user(user_id):
    u = User.query.get_or_404(user_id)
    data = request.get_json(force=True, silent=True) or {}
    for field in ["full_name", "role", "is_verified", "timezone", "language"]:
        if field in data:
            setattr(u, field, data[field])
    if "password" in data and data["password"]:
        u.set_password(data["password"])
    db.session.commit()
    return jsonify(u.to_dict(include_sensitive=True))

@bp.delete("/<int:user_id>")
def delete_user(user_id):
    u = User.query.get_or_404(user_id)
    # soft delete
    u.soft_delete()
    db.session.commit()
    return jsonify({"status": "deleted", "id": u.id})

