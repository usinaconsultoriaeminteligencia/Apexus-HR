"""
Configurações da API OpenAI para serviços de áudio e análise
"""
import os
import logging
from openai import OpenAI
from typing import Optional

logger = logging.getLogger(__name__)


class OpenAIKeyMissingError(Exception):
    """Exceção customizada quando a chave da OpenAI não está configurada"""
    pass


class OpenAIConfig:
    """Gerencia configurações e cliente da OpenAI"""
    
    _client: Optional[OpenAI] = None
    
    # Modelos
    TTS_MODEL = "tts-1"
    TTS_VOICE = "nova"
    TRANSCRIPTION_MODEL = "whisper-1"
    ANALYSIS_MODEL = "gpt-4o-mini"
    
    # Parâmetros de geração
    TEMPERATURE = 0.7
    MAX_TOKENS = 1500
    
    # Configurações de refinamento (novo)
    ENABLE_RESPONSE_REFINEMENT = os.getenv('ENABLE_RESPONSE_REFINEMENT', 'true').lower() == 'true'
    REFINEMENT_MAX_RETRIES = int(os.getenv('REFINEMENT_MAX_RETRIES', '3'))
    REFINEMENT_ENABLE_CACHE = os.getenv('REFINEMENT_ENABLE_CACHE', 'true').lower() == 'true'
    REFINEMENT_ENABLE_FEW_SHOT = os.getenv('REFINEMENT_ENABLE_FEW_SHOT', 'true').lower() == 'true'
    REFINEMENT_CACHE_TTL_HOURS = int(os.getenv('REFINEMENT_CACHE_TTL_HOURS', '24'))
    
    # Fine-tuning data collection (novo)
    ENABLE_FINETUNING_COLLECTION = os.getenv('ENABLE_FINETUNING_COLLECTION', 'false').lower() == 'true'
    FINETUNING_DATA_DIR = os.getenv('FINETUNING_DATA_DIR', 'data/finetuning')
    
    @classmethod
    def get_client(cls) -> OpenAI:
        """
        Retorna cliente OpenAI singleton
        
        Raises:
            OpenAIKeyMissingError: Se OPENAI_API_KEY não estiver configurada
        """
        if cls._client is None:
            api_key = os.getenv('OPENAI_API_KEY')
            
            if not api_key:
                logger.warning("OPENAI_API_KEY não configurada - fallbacks serão usados")
                raise OpenAIKeyMissingError(
                    "OPENAI_API_KEY não encontrada nas variáveis de ambiente"
                )
            
            cls._client = OpenAI(api_key=api_key)
            logger.info("Cliente OpenAI inicializado com sucesso")
        
        return cls._client
    
    @classmethod
    def reset_client(cls):
        """Reseta cliente (útil para testes)"""
        cls._client = None
        logger.info("Cliente OpenAI resetado")


def get_openai_client() -> OpenAI:
    """
    Função helper para obter cliente OpenAI
    
    Raises:
        OpenAIKeyMissingError: Se OPENAI_API_KEY não estiver configurada
    """
    return OpenAIConfig.get_client()
