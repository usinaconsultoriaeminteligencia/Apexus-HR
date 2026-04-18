import hashlib
import json
import logging

from ..utils.behavioral_rubrics import RUBRIC_VERSION

logger = logging.getLogger(__name__)


# Mapa rubric_id → (framework, dimension).
# Usado para preencher campos padronizados do assessment e para
# gerar o texto de guidance enviado ao modelo.
_RUBRIC_REGISTRY = {
    'disc.dominance': ('disc', 'dominance'),
    'disc.influence': ('disc', 'influence'),
    'disc.steadiness': ('disc', 'steadiness'),
    'disc.conscientiousness': ('disc', 'conscientiousness_disc'),
    'competencies.customer_orientation': ('competencies', 'customer_orientation'),
    'competencies.data_driven_decision': ('competencies', 'data_driven_decision'),
    'competencies.ethical_judgment': ('competencies', 'ethical_judgment'),
    'big_five.openness': ('big_five', 'openness'),
    'big_five.conscientiousness': ('big_five', 'conscientiousness'),
}


def _default_rubric_for_category(category: str) -> tuple[str, str]:
    """Mapeamento heurístico categoria da pergunta -> (rubric_id, dimension)."""
    cat = (category or '').lower()
    mapping = {
        'tecnico': ('competencies.data_driven_decision', 'data_driven_decision'),
        'tecnica': ('competencies.data_driven_decision', 'data_driven_decision'),
        'comportamental': ('disc.steadiness', 'steadiness'),
        'lideranca': ('disc.dominance', 'dominance'),
        'gestao': ('competencies.ethical_judgment', 'ethical_judgment'),
        'motivacao': ('disc.influence', 'influence'),
        'comunicacao': ('disc.influence', 'influence'),
        'apresentacao': ('disc.influence', 'influence'),
        'desafio': ('disc.dominance', 'dominance'),
        'aprendizado': ('big_five.openness', 'openness'),
        'analise': ('competencies.data_driven_decision', 'data_driven_decision'),
        'problema': ('competencies.data_driven_decision', 'data_driven_decision'),
        'impacto': ('competencies.customer_orientation', 'customer_orientation'),
        'desenvolvimento': ('big_five.openness', 'openness'),
        'experiencia': ('big_five.conscientiousness', 'conscientiousness'),
        'projeto': ('big_five.conscientiousness', 'conscientiousness'),
        'forças': ('disc.influence', 'influence'),
        'futuro': ('disc.dominance', 'dominance'),
        'ferramentas': ('competencies.data_driven_decision', 'data_driven_decision'),
    }
    return mapping.get(cat, ('competencies.customer_orientation', 'customer_orientation'))


def resolve_rubric(rubric_id: str | None, category: str | None) -> tuple[str, str]:
    """Retorna (rubric_id, dimension) normalizados.

    Aceita rubric_id explícito ou deriva da categoria da pergunta.
    """
    if rubric_id and rubric_id in _RUBRIC_REGISTRY:
        _, dim = _RUBRIC_REGISTRY[rubric_id]
        return rubric_id, dim
    return _default_rubric_for_category(category or '')


def truncate_excerpt(text: str, limit: int = 400) -> str:
    """Trunca o trecho-evidência mantendo palavra inteira."""
    if not text:
        return ''
    clean = ' '.join(text.split())
    if len(clean) <= limit:
        return clean
    cut = clean[:limit].rsplit(' ', 1)[0]
    return cut + '…'


def prompt_hash(prompt: str) -> str:
    """sha256 truncado do prompt para rastreamento (16 chars)."""
    return hashlib.sha256((prompt or '').encode('utf-8')).hexdigest()[:16]


def build_analysis_prompt(question: str, response: str, position: str,
                          rubric_id: str, dimension: str) -> str:
    """Monta o prompt que pede também rubric_id, evidência e confiança."""
    return (
        f"Você é analista sênior de RH auditável.\n"
        f"Posição: {position}\n"
        f"Rubrica alvo: {rubric_id} (dimensão: {dimension}).\n\n"
        f"Pergunta: {question}\n"
        f"Resposta do candidato: {response}\n\n"
        "Responda APENAS JSON com o schema:\n"
        "{\n"
        '  "relevance": <0-100>,\n'
        '  "technical_accuracy": <0-100>,\n'
        '  "communication": <0-100>,\n'
        '  "score": <1-5 na rubrica alvo>,\n'
        '  "confidence": <0.0-1.0>,\n'
        '  "evidence_excerpt": "<trecho curto e literal da resposta que '
        'sustenta a nota>",\n'
        '  "summary": "<1 frase>"\n'
        '}'
    )


def fallback_assessment(response: str, rubric_id: str, dimension: str) -> dict:
    """Fallback SEGURO: NÃO emite nota baseada em heurística de palavras.

    Regra (Onda 2): quando a IA não está disponível, marcamos o
    assessment como pendente de revisão humana com confidence=0 e
    score=None. Não produzimos recomendação automática.
    """
    excerpt = truncate_excerpt(response, 400)
    return {
        'relevance': None,
        'technical_accuracy': None,
        'communication': None,
        'score': None,
        'confidence': 0.0,
        'evidence_excerpt': excerpt,
        'summary': (
            'Modelo indisponível no momento da análise. '
            'Assessment aguarda revisão humana.'
        ),
        'rubric_id': rubric_id,
        'rubric_version': RUBRIC_VERSION,
        'dimension': dimension,
        'model_name': 'fallback',
        'model_version': None,
        'prompt_hash': None,
        'human_review_status': 'pending',
    }


def normalize_analysis(raw: dict, rubric_id: str, dimension: str,
                       prompt_text: str, model_name: str,
                       model_version: str | None) -> dict:
    """Normaliza a saída do LLM e acrescenta metadados auditáveis."""
    def _num(key, default=None, lo=None, hi=None):
        try:
            v = raw.get(key)
            if v is None:
                return default
            v = float(v)
            if lo is not None:
                v = max(lo, v)
            if hi is not None:
                v = min(hi, v)
            return v
        except Exception:
            return default

    score = _num('score', lo=1.0, hi=5.0)
    confidence = _num('confidence', default=0.5, lo=0.0, hi=1.0)

    evidence = truncate_excerpt(str(raw.get('evidence_excerpt') or ''), 400)

    return {
        'relevance': _num('relevance', default=0.0, lo=0.0, hi=100.0) or 0.0,
        'technical_accuracy': _num('technical_accuracy', default=0.0, lo=0.0, hi=100.0) or 0.0,
        'communication': _num('communication', default=0.0, lo=0.0, hi=100.0) or 0.0,
        'score': score,
        'confidence': confidence,
        'evidence_excerpt': evidence,
        'summary': str(raw.get('summary') or '').strip()[:500],
        'rubric_id': rubric_id,
        'rubric_version': RUBRIC_VERSION,
        'dimension': dimension,
        'model_name': model_name,
        'model_version': model_version,
        'prompt_hash': prompt_hash(prompt_text),
        'human_review_status': 'pending',
    }
