import json
import logging
from typing import Optional

from .assessment_helpers import (
    build_analysis_prompt,
    fallback_assessment,
    normalize_analysis,
    resolve_rubric,
    truncate_excerpt,
)
from .behavioral_rubrics import RUBRIC_VERSION

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """
    Análise auditável de respostas de entrevista.

    Onda 2 — item 3.4:
    - Retorna também rubric_id, rubric_version, dimension, confidence,
      evidence_excerpt, model_name, model_version, prompt_hash.
    - Fallback NÃO gera mais nota baseada em contagem de palavras: marca
      o assessment como pendente de revisão humana (confidence=0,
      score=None, model_name='fallback').
    """

    DEFAULT_MODEL_NAME = 'openai:gpt-4o-mini'

    def __init__(self, use_refiner: bool = True):
        self.use_refiner = use_refiner
        self.refiner = None

        if self.use_refiner:
            try:
                from .response_refiner import ResponseRefiner, RefinementConfig
                config = RefinementConfig(
                    max_retries=3,
                    enable_cache=True,
                    enable_few_shot=True,
                    validation_strict=False,
                )
                self.refiner = ResponseRefiner(config)
                logger.info("Sistema de refinamento ativado")
            except ImportError as e:
                logger.warning(f"Refinador indisponível: {e}")
                self.use_refiner = False

    def analyze_response(self, question: str, response: str, position: str,
                         rubric_id: str | None = None,
                         category: str | None = None) -> dict:
        """Analisa resposta do candidato.

        Args:
            question: pergunta feita.
            response: transcrição da resposta.
            position: cargo alvo da entrevista.
            rubric_id: rubrica canônica (ex.: 'competencies.ethical_judgment').
            category: categoria da pergunta (usada se rubric_id não vier).

        Returns:
            dict com campos legados (relevance/technical_accuracy/
            communication/summary) + campos auditáveis (rubric_id,
            rubric_version, dimension, score, confidence,
            evidence_excerpt, model_name, model_version, prompt_hash,
            human_review_status).
        """
        rubric_id_eff, dimension = resolve_rubric(rubric_id, category)

        if not response or not response.strip():
            return {
                'relevance': 0.0,
                'technical_accuracy': 0.0,
                'communication': 0.0,
                'summary': 'Nenhuma resposta fornecida pelo candidato.',
                'rubric_id': rubric_id_eff,
                'rubric_version': RUBRIC_VERSION,
                'dimension': dimension,
                'score': None,
                'confidence': 0.0,
                'evidence_excerpt': '',
                'model_name': 'none',
                'model_version': None,
                'prompt_hash': None,
                'human_review_status': 'pending',
            }

        prompt = build_analysis_prompt(
            question=question, response=response, position=position,
            rubric_id=rubric_id_eff, dimension=dimension,
        )

        if self.use_refiner and self.refiner:
            try:
                result = self.refiner.analyze_response(question, response, position)
                if result:
                    normalized = normalize_analysis(
                        {
                            'relevance': result.get('relevance'),
                            'technical_accuracy': result.get('technical_accuracy'),
                            'communication': result.get('communication'),
                            'score': result.get('score'),
                            'confidence': result.get('confidence', 0.6),
                            'evidence_excerpt': result.get(
                                'evidence_excerpt',
                                truncate_excerpt(response, 400),
                            ),
                            'summary': result.get('summary', ''),
                        },
                        rubric_id=rubric_id_eff,
                        dimension=dimension,
                        prompt_text=prompt,
                        model_name=self.DEFAULT_MODEL_NAME,
                        model_version=None,
                    )
                    return normalized
            except Exception as e:
                logger.warning(f"Refinador falhou, tentando chamada direta: {e}")

        return self._legacy_analysis(
            question=question, response=response, position=position,
            rubric_id=rubric_id_eff, dimension=dimension, prompt=prompt,
        )

    def _legacy_analysis(self, question: str, response: str, position: str,
                         rubric_id: str, dimension: str, prompt: str) -> dict:
        """Chamada direta à OpenAI; se falhar, cai no fallback seguro."""
        try:
            from ..config.openai_config import (
                OpenAIKeyMissingError,
                OpenAIConfig,
                get_openai_client,
            )
        except Exception as e:
            logger.error(f"Falha ao importar config OpenAI: {e}")
            return fallback_assessment(response, rubric_id, dimension)

        try:
            client = get_openai_client()
        except OpenAIKeyMissingError:
            logger.warning("OPENAI_API_KEY ausente — fallback seguro")
            return fallback_assessment(response, rubric_id, dimension)

        try:
            model = getattr(OpenAIConfig, 'ANALYSIS_MODEL', 'gpt-4o-mini')
            completion = client.chat.completions.create(
                model=model,
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.3,
                max_tokens=500,
                response_format={'type': 'json_object'},
            )
            raw = completion.choices[0].message.content
            payload = json.loads(raw) if isinstance(raw, str) else {}
            model_version = getattr(completion, 'model', None) or model
            return normalize_analysis(
                payload, rubric_id=rubric_id, dimension=dimension,
                prompt_text=prompt,
                model_name=f'openai:{model}',
                model_version=model_version,
            )
        except Exception as e:
            logger.error(f"Falha na análise OpenAI: {e}")
            return fallback_assessment(response, rubric_id, dimension)
