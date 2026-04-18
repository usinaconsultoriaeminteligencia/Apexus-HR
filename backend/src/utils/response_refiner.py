"""
Sistema de refinamento e validação de respostas da OpenAI
Inclui validação, retry com refinamento e cache de respostas
"""
import json
import logging
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

from ..config.openai_config import get_openai_client, OpenAIConfig
from .prompt_templates import PromptTemplates

# Import opcional do coletor de dados
try:
    from .finetuning_data_collector import get_data_collector
    _DATA_COLLECTOR_AVAILABLE = True
except ImportError:
    _DATA_COLLECTOR_AVAILABLE = False
    get_data_collector = None

logger = logging.getLogger(__name__)


@dataclass
class RefinementConfig:
    """Configuração para refinamento de respostas"""
    max_retries: int = 3
    enable_cache: bool = True
    cache_ttl_hours: int = 24
    enable_few_shot: bool = True
    validation_strict: bool = True


class ResponseValidator:
    """Valida respostas da OpenAI antes de retornar"""
    
    @staticmethod
    def validate_response_analysis(response: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida análise de resposta individual
        
        Returns:
            Tupla (is_valid, errors)
        """
        errors = []
        required_fields = ["relevance", "technical_accuracy", "communication", "summary"]
        
        # Verificar campos obrigatórios
        for field in required_fields:
            if field not in response:
                errors.append(f"Campo obrigatório '{field}' ausente")
        
        # Validar tipos e ranges
        if "relevance" in response:
            val = response["relevance"]
            if not isinstance(val, (int, float)) or not (0 <= val <= 100):
                errors.append(f"relevance deve ser número entre 0-100, recebido: {val}")
        
        if "technical_accuracy" in response:
            val = response["technical_accuracy"]
            if not isinstance(val, (int, float)) or not (0 <= val <= 100):
                errors.append(f"technical_accuracy deve ser número entre 0-100, recebido: {val}")
        
        if "communication" in response:
            val = response["communication"]
            if not isinstance(val, (int, float)) or not (0 <= val <= 100):
                errors.append(f"communication deve ser número entre 0-100, recebido: {val}")
        
        if "summary" in response:
            summary = response["summary"]
            if not isinstance(summary, str) or len(summary.strip()) < 10:
                errors.append("summary deve ser string com pelo menos 10 caracteres")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_interview_analysis(response: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida análise completa de entrevista
        
        Returns:
            Tupla (is_valid, errors)
        """
        errors = []
        required_fields = [
            "pontuacao_tecnica", "pontuacao_comportamental", "perfil_disc",
            "descricao_perfil_disc", "pontos_fortes", "areas_desenvolvimento",
            "recomendacao", "resumo_executivo", "feedback_detalhado",
            "fit_cultural", "proximos_passos"
        ]
        
        # Verificar campos obrigatórios
        for field in required_fields:
            if field not in response:
                errors.append(f"Campo obrigatório '{field}' ausente")
        
        # Validar pontuações
        for field in ["pontuacao_tecnica", "pontuacao_comportamental", "fit_cultural"]:
            if field in response:
                val = response[field]
                if not isinstance(val, (int, float)) or not (0 <= val <= 10):
                    errors.append(f"{field} deve ser número entre 0-10, recebido: {val}")
        
        # Validar perfil DISC
        if "perfil_disc" in response:
            disc = response["perfil_disc"]
            if disc not in ["D", "I", "S", "C"]:
                errors.append(f"perfil_disc deve ser D, I, S ou C, recebido: {disc}")
        
        # Validar recomendação
        if "recomendacao" in response:
            rec = response["recomendacao"]
            if rec not in ["CONTRATAR", "CONSIDERAR", "NAO_CONTRATAR"]:
                errors.append(f"recomendacao deve ser CONTRATAR, CONSIDERAR ou NAO_CONTRATAR, recebido: {rec}")
        
        # Validar listas
        for field in ["pontos_fortes", "areas_desenvolvimento", "proximos_passos"]:
            if field in response:
                val = response[field]
                if not isinstance(val, list) or len(val) < 2:
                    errors.append(f"{field} deve ser lista com pelo menos 2 itens")
        
        # Validar strings
        for field in ["descricao_perfil_disc", "resumo_executivo", "feedback_detalhado"]:
            if field in response:
                val = response[field]
                if not isinstance(val, str) or len(val.strip()) < 20:
                    errors.append(f"{field} deve ser string com pelo menos 20 caracteres")
        
        return len(errors) == 0, errors


class ResponseCache:
    """Cache simples em memória para respostas similares"""
    
    def __init__(self, ttl_hours: int = 24):
        self.cache: Dict[str, Tuple[Dict[str, Any], datetime]] = {}
        self.ttl = timedelta(hours=ttl_hours)
    
    def _generate_key(self, question: str, response: str, position: str) -> str:
        """Gera chave de cache baseada no conteúdo"""
        content = f"{question}|{response}|{position}".lower().strip()
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, question: str, response: str, position: str) -> Optional[Dict[str, Any]]:
        """Recupera resposta do cache se ainda válida"""
        key = self._generate_key(question, response, position)
        
        if key in self.cache:
            cached_data, cached_time = self.cache[key]
            if datetime.now() - cached_time < self.ttl:
                logger.debug(f"Cache hit para análise de resposta")
                return cached_data
            else:
                # Expirou, remover
                del self.cache[key]
        
        return None
    
    def set(self, question: str, response: str, position: str, data: Dict[str, Any]):
        """Armazena resposta no cache"""
        key = self._generate_key(question, response, position)
        self.cache[key] = (data, datetime.now())
        logger.debug(f"Resposta armazenada no cache")
    
    def clear(self):
        """Limpa cache"""
        self.cache.clear()


class ResponseRefiner:
    """
    Sistema de refinamento de respostas da OpenAI
    Inclui validação, retry com refinamento e cache
    """
    
    def __init__(self, config: Optional[RefinementConfig] = None):
        # Usar configurações do OpenAIConfig se não fornecidas
        if config is None:
            config = RefinementConfig(
                max_retries=OpenAIConfig.REFINEMENT_MAX_RETRIES,
                enable_cache=OpenAIConfig.REFINEMENT_ENABLE_CACHE,
                cache_ttl_hours=OpenAIConfig.REFINEMENT_CACHE_TTL_HOURS,
                enable_few_shot=OpenAIConfig.REFINEMENT_ENABLE_FEW_SHOT,
                validation_strict=False  # Permite fallback se validação falhar
            )
        self.config = config
        self.validator = ResponseValidator()
        self.cache = ResponseCache(self.config.cache_ttl_hours) if self.config.enable_cache else None
    
    def analyze_response(
        self,
        question: str,
        response: str,
        position: str
    ) -> Dict[str, Any]:
        """
        Analisa resposta com refinamento e validação
        
        Args:
            question: Pergunta da entrevista
            response: Resposta do candidato
            position: Posição para qual está se candidatando
            
        Returns:
            Análise validada e refinada
        """
        # Verificar cache
        if self.cache:
            cached = self.cache.get(question, response, position)
            if cached:
                return cached
        
        client = get_openai_client()
        prompt = PromptTemplates.build_response_analysis_prompt(
            question, response, position, use_few_shot=self.config.enable_few_shot
        )
        
        for attempt in range(self.config.max_retries):
            try:
                logger.debug(f"Tentativa {attempt + 1} de análise de resposta")
                
                completion = client.chat.completions.create(
                    model=OpenAIConfig.ANALYSIS_MODEL,
                    messages=[
                        {"role": "system", "content": "Você é um analista de RH experiente. Responda sempre em JSON válido."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=500,
                    response_format={"type": "json_object"}
                )
                
                ai_response = completion.choices[0].message.content
                if not ai_response:
                    raise ValueError("Resposta vazia da OpenAI")
                
                result = json.loads(ai_response)
                
                # Validar resposta
                is_valid, errors = self.validator.validate_response_analysis(result)
                
                if is_valid:
                    # Armazenar no cache
                    if self.cache:
                        self.cache.set(question, response, position, result)
                    
                    # Coletar dados para fine-tuning (se habilitado)
                    if _DATA_COLLECTOR_AVAILABLE and OpenAIConfig.ENABLE_FINETUNING_COLLECTION:
                        try:
                            collector = get_data_collector()
                            if collector:
                                collector.collect_response_analysis(
                                    question=question,
                                    response=response,
                                    position=position,
                                    ai_result=result,
                                    prompt_used=prompt
                                )
                        except Exception as e:
                            logger.debug(f"Erro ao coletar dados para fine-tuning: {e}")
                    
                    logger.info("Análise de resposta concluída com sucesso")
                    return result
                else:
                    if attempt < self.config.max_retries - 1:
                        # Refinar prompt com erros
                        logger.warning(f"Validação falhou, refinando: {errors}")
                        prompt = PromptTemplates.build_refinement_prompt(
                            ai_response, errors, context=f"Posição: {position}"
                        )
                    else:
                        # Última tentativa, retornar mesmo com erros (mas logar)
                        logger.error(f"Validação falhou após {self.config.max_retries} tentativas: {errors}")
                        if self.config.validation_strict:
                            raise ValueError(f"Resposta não passou na validação: {errors}")
                        return result
                        
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao fazer parse do JSON: {e}")
                if attempt < self.config.max_retries - 1:
                    prompt = PromptTemplates.build_refinement_prompt(
                        ai_response or "", ["Resposta não é um JSON válido"]
                    )
                else:
                    raise
            except Exception as e:
                logger.error(f"Erro na análise (tentativa {attempt + 1}): {e}")
                if attempt == self.config.max_retries - 1:
                    raise
        
        raise RuntimeError("Falha ao analisar resposta após todas as tentativas")
    
    def analyze_interview(
        self,
        interview_text: str,
        position: str,
        candidate_name: str
    ) -> Dict[str, Any]:
        """
        Analisa entrevista completa com refinamento e validação
        
        Args:
            interview_text: Texto completo da entrevista
            position: Posição para qual está se candidatando
            candidate_name: Nome do candidato
            
        Returns:
            Análise completa validada e refinada
        """
        client = get_openai_client()
        system_msg, user_msg = PromptTemplates.build_interview_analysis_prompt(
            interview_text, position, candidate_name, use_few_shot=self.config.enable_few_shot
        )
        
        for attempt in range(self.config.max_retries):
            try:
                logger.debug(f"Tentativa {attempt + 1} de análise de entrevista")
                
                completion = client.chat.completions.create(
                    model=OpenAIConfig.ANALYSIS_MODEL,
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg}
                    ],
                    temperature=OpenAIConfig.TEMPERATURE,
                    max_tokens=OpenAIConfig.MAX_TOKENS,
                    response_format={"type": "json_object"}
                )
                
                ai_response = completion.choices[0].message.content
                if not ai_response:
                    raise ValueError("Resposta vazia da OpenAI")
                
                result = json.loads(ai_response)
                
                # Validar resposta
                is_valid, errors = self.validator.validate_interview_analysis(result)
                
                if is_valid:
                    # Coletar dados para fine-tuning (se habilitado)
                    if _DATA_COLLECTOR_AVAILABLE and OpenAIConfig.ENABLE_FINETUNING_COLLECTION:
                        try:
                            collector = get_data_collector()
                            if collector:
                                collector.collect_interview_analysis(
                                    interview_text=interview_text,
                                    position=position,
                                    candidate_name=candidate_name,
                                    ai_result=result,
                                    prompt_used=user_msg
                                )
                        except Exception as e:
                            logger.debug(f"Erro ao coletar dados para fine-tuning: {e}")
                    
                    logger.info("Análise de entrevista concluída com sucesso")
                    return result
                else:
                    if attempt < self.config.max_retries - 1:
                        # Refinar prompt com erros
                        logger.warning(f"Validação falhou, refinando: {errors}")
                        user_msg = PromptTemplates.build_refinement_prompt(
                            ai_response, errors, context=f"Posição: {position}, Candidato: {candidate_name}"
                        )
                    else:
                        # Última tentativa
                        logger.error(f"Validação falhou após {self.config.max_retries} tentativas: {errors}")
                        if self.config.validation_strict:
                            raise ValueError(f"Resposta não passou na validação: {errors}")
                        return result
                        
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao fazer parse do JSON: {e}")
                if attempt < self.config.max_retries - 1:
                    user_msg = PromptTemplates.build_refinement_prompt(
                        ai_response or "", ["Resposta não é um JSON válido"]
                    )
                else:
                    raise
            except Exception as e:
                logger.error(f"Erro na análise (tentativa {attempt + 1}): {e}")
                if attempt == self.config.max_retries - 1:
                    raise
        
        raise RuntimeError("Falha ao analisar entrevista após todas as tentativas")

