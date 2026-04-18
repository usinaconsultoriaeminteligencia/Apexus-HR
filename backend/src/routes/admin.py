from flask import Blueprint, jsonify

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Funcionalidade de seed removida - sistema usa apenas dados reais

@admin_bp.get("/health")  
def health():
    """Health check básico para admin"""
    return jsonify({"status": "ok", "message": "Admin API funcionando"})
