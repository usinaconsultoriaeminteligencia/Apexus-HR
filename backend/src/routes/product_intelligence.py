"""Product intelligence endpoints for valuation and auditability roadmap."""

from flask import Blueprint, jsonify

from src.utils.behavioral_rubrics import get_rubric_catalog

bp = Blueprint("product_intelligence", __name__, url_prefix="/api/product")


@bp.get("/intelligence")
def get_product_intelligence():
    payload = {
        "positioning": {
            "company": "USINA I.A. Tecnologia e Inovacao",
            "product_thesis": (
                "Sistema auditavel de inteligencia comportamental para recrutamento, "
                "com rubricas versionadas, evidencias por score e validacao humana."
            ),
            "valuation_driver": "Transformar entrevista com IA em ativo de dados, governanca e ROI.",
        },
        "maturity": {
            "current_stage": "MVP funcional com base para auditoria comportamental",
            "target_stage": "plataforma multi-cliente auditavel com metricas de fairness e ROI",
            "readiness_score": 62,
        },
        "valuation": {
            "currency": "USD",
            "estimated_range": {
                "conservative": 180000,
                "base": 420000,
                "upside": 950000,
            },
            "assumptions": [
                "rubricas comportamentais versionadas",
                "pipeline de evidencias por score",
                "validacao humana antes de decisao sensivel",
                "dataset anonimizado para melhoria continua",
                "relatorios de fairness e ROI por cliente",
            ],
        },
        "roadmap": [
            {
                "phase": "0-30 dias",
                "objective": "Auditabilidade minima",
                "deliverables": [
                    "catalogo de rubricas versionado",
                    "score com evidencia e confianca",
                    "log de decisao do modelo",
                ],
            },
            {
                "phase": "31-60 dias",
                "objective": "Governanca e validacao humana",
                "deliverables": [
                    "fila de revisao humana",
                    "motivos de ajuste de score",
                    "painel de divergencia IA vs avaliador",
                ],
            },
            {
                "phase": "61-90 dias",
                "objective": "Ativo de dados e fairness",
                "deliverables": [
                    "dataset anonimizado",
                    "metricas de consistencia por cargo",
                    "relatorio de fairness por cliente",
                ],
            },
            {
                "phase": "91-180 dias",
                "objective": "Prova economica",
                "deliverables": [
                    "dashboard de ROI",
                    "benchmark de tempo de recrutamento",
                    "modelo de pricing por uso e modulo",
                ],
            },
        ],
    }
    return jsonify({"success": True, "data": payload})


@bp.get("/rubrics")
def get_product_rubrics():
    return jsonify({"success": True, "data": get_rubric_catalog()})
