def analyze_interview_audio(path: str) -> dict:
    """
    Stub de análise de voz.
    M2: substituir por extração real (librosa + métricas; biometria; detecção de leitura).
    """
    return {
        "scores": {
            "confidence": 0.72,
            "clarity": 0.76,
            "energy": 0.66,
            "final_score": 78
        },
        "insights": [
            "Boa articulação na maior parte das respostas.",
            "Pode trazer exemplos mais objetivos em perguntas técnicas."
        ],
        "recommendations": [
            "Reforçar storytelling com métricas de impacto.",
            "Treinar respostas de 60–90s com foco no problema/ação/resultado."
        ],
        "interview_simulation": {
            "follow_ups": [
                "Como você mediu o impacto?",
                "Quais riscos considerou e como mitigou?"
            ]
        }
    }
