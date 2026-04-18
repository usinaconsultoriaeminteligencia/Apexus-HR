"""
Sistema de coleta de dados para fine-tuning futuro
Armazena prompts e respostas para análise e treinamento
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class FineTuningExample:
    """Exemplo de dados para fine-tuning"""
    prompt: str
    completion: str
    metadata: Dict[str, Any]
    timestamp: str
    quality_score: Optional[float] = None  # Score de qualidade (0-1) se revisado


class FineTuningDataCollector:
    """
    Coleta e armazena dados de interações com OpenAI para fine-tuning futuro
    """
    
    def __init__(self, data_dir: str = "data/finetuning"):
        """
        Args:
            data_dir: Diretório para armazenar dados coletados
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.enabled = True  # Pode ser desabilitado via env var
    
    def collect_response_analysis(
        self,
        question: str,
        response: str,
        position: str,
        ai_result: Dict[str, Any],
        prompt_used: Optional[str] = None
    ):
        """
        Coleta dados de análise de resposta individual
        
        Args:
            question: Pergunta da entrevista
            response: Resposta do candidato
            position: Posição
            ai_result: Resultado da análise da IA
            prompt_used: Prompt usado (opcional)
        """
        if not self.enabled:
            return
        
        try:
            example = FineTuningExample(
                prompt=prompt_used or f"Analise esta resposta para {position}: {question} | {response}",
                completion=json.dumps(ai_result, ensure_ascii=False),
                metadata={
                    "type": "response_analysis",
                    "position": position,
                    "question": question,
                    "response_length": len(response),
                    "model": "gpt-4o-mini"
                },
                timestamp=datetime.now().isoformat()
            )
            
            self._save_example(example, "response_analysis")
            
        except Exception as e:
            logger.warning(f"Erro ao coletar dados de análise de resposta: {e}")
    
    def collect_interview_analysis(
        self,
        interview_text: str,
        position: str,
        candidate_name: str,
        ai_result: Dict[str, Any],
        prompt_used: Optional[str] = None
    ):
        """
        Coleta dados de análise completa de entrevista
        
        Args:
            interview_text: Texto completo da entrevista
            position: Posição
            candidate_name: Nome do candidato
            ai_result: Resultado da análise da IA
            prompt_used: Prompt usado (opcional)
        """
        if not self.enabled:
            return
        
        try:
            example = FineTuningExample(
                prompt=prompt_used or f"Analise esta entrevista para {position} com {candidate_name}",
                completion=json.dumps(ai_result, ensure_ascii=False),
                metadata={
                    "type": "interview_analysis",
                    "position": position,
                    "candidate_name": candidate_name,
                    "interview_length": len(interview_text),
                    "model": "gpt-4o-mini"
                },
                timestamp=datetime.now().isoformat()
            )
            
            self._save_example(example, "interview_analysis")
            
        except Exception as e:
            logger.warning(f"Erro ao coletar dados de análise de entrevista: {e}")
    
    def mark_example_quality(
        self,
        example_id: str,
        quality_score: float,
        notes: Optional[str] = None
    ):
        """
        Marca qualidade de um exemplo (para revisão manual)
        
        Args:
            example_id: ID do exemplo
            quality_score: Score de qualidade (0-1)
            notes: Notas adicionais
        """
        # Implementação futura para marcar exemplos revisados
        pass
    
    def export_for_finetuning(
        self,
        output_file: str,
        min_quality: float = 0.7,
        max_examples: Optional[int] = None
    ) -> int:
        """
        Exporta dados coletados no formato para fine-tuning da OpenAI
        
        Args:
            output_file: Arquivo de saída (JSONL)
            min_quality: Score mínimo de qualidade (se aplicável)
            max_examples: Número máximo de exemplos a exportar
            
        Returns:
            Número de exemplos exportados
        """
        # Implementação futura para exportar em formato JSONL da OpenAI
        # Formato esperado: {"messages": [{"role": "system", "content": "..."}, ...]}
        logger.info(f"Exportação para fine-tuning ainda não implementada")
        return 0
    
    def _save_example(self, example: FineTuningExample, category: str):
        """Salva exemplo em arquivo"""
        try:
            category_dir = self.data_dir / category
            category_dir.mkdir(parents=True, exist_ok=True)
            
            # Salvar em arquivo JSON por data
            date_str = datetime.now().strftime("%Y-%m-%d")
            file_path = category_dir / f"{date_str}.jsonl"
            
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(example), ensure_ascii=False) + "\n")
            
            logger.debug(f"Exemplo salvo: {file_path}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar exemplo: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas sobre dados coletados"""
        stats = {
            "total_examples": 0,
            "by_category": {},
            "by_date": {}
        }
        
        try:
            for category_dir in self.data_dir.iterdir():
                if category_dir.is_dir():
                    category = category_dir.name
                    count = 0
                    
                    for file_path in category_dir.glob("*.jsonl"):
                        with open(file_path, "r", encoding="utf-8") as f:
                            count += sum(1 for _ in f)
                    
                    stats["by_category"][category] = count
                    stats["total_examples"] += count
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas: {e}")
        
        return stats


# Instância global (pode ser configurada via env)
_data_collector: Optional[FineTuningDataCollector] = None


def get_data_collector() -> Optional[FineTuningDataCollector]:
    """Retorna instância global do coletor de dados"""
    global _data_collector
    
    if _data_collector is None:
        import os
        data_dir = os.getenv("FINETUNING_DATA_DIR", "data/finetuning")
        enabled = os.getenv("ENABLE_FINETUNING_COLLECTION", "true").lower() == "true"
        
        _data_collector = FineTuningDataCollector(data_dir=data_dir)
        _data_collector.enabled = enabled
        
        if enabled:
            logger.info(f"Coletor de dados para fine-tuning ativado: {data_dir}")
    
    return _data_collector if _data_collector.enabled else None

