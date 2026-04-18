"""
ai_service.py — Serviço de análise de IA para entrevistas.

A função analyze_interview_response é o ponto de entrada mockável pelos testes.
Em produção, delega para o AIAnalyzer (OpenAI). Em ambiente sem chave configurada,
retorna scores de fallback para não bloquear o fluxo.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def analyze_interview_response(
    question: str,
    response: str,
    position: str = "",
) -> dict:
    """Analisa uma resposta de entrevista e retorna scores comportamentais.

    Retorna um dict com as chaves:
        confidence_score    float  0–10
        enthusiasm_score    float  0–10
        clarity_score       float  0–10
        technical_accuracy  float  0–10
        communication_score float  0–10
        recommendation      str    'contratar' | 'aguardar' | 'não contratar'
        summary             str    resumo da análise
    """
    try:
        from src.utils.ai_analyzer import AIAnalyzer

        analyzer = AIAnalyzer()
        result = analyzer.analyze_response(
            question=question,
            response=response,
            position=position,
        )
        return result
    except Exception as exc:
        logger.warning("AI análise indisponível, usando fallback: %s", exc)
        return _fallback_scores(response)


def calculate_overall_score(questions_data: list) -> float:
    """Calcula score geral a partir de uma lista de Q&A analisados."""
    if not questions_data:
        return 0.0

    scored = [
        q for q in questions_data
        if isinstance(q.get("analysis"), dict)
    ]
    if not scored:
        return 5.0  # score neutro sem análise

    keys = ("confidence_score", "enthusiasm_score", "clarity_score",
            "technical_accuracy", "communication_score")
    totals = []
    for q in scored:
        analysis = q["analysis"]
        scores = [float(analysis.get(k, 5.0)) for k in keys]
        totals.append(sum(scores) / len(scores))

    return round(sum(totals) / len(totals), 2)


def _fallback_scores(response: str) -> dict:
    """Scores de fallback baseados em heurística simples (sem IA)."""
    length = len(response.strip())
    base = min(10.0, max(4.0, length / 50))
    return {
        "confidence_score": round(base, 1),
        "enthusiasm_score": round(base * 0.95, 1),
        "clarity_score": round(base * 0.9, 1),
        "technical_accuracy": round(base * 0.85, 1),
        "communication_score": round(base * 0.92, 1),
        "recommendation": "aguardar",
        "summary": "Análise de IA indisponível — score estimado por heurística.",
    }
