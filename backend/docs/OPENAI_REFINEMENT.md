# Sistema de Refinamento de Respostas OpenAI

Este documento descreve o sistema de refinamento implementado para melhorar a qualidade das saídas das chamadas de API da OpenAI.

## Visão Geral

O sistema de refinamento inclui:

1. **Templates de Prompts Otimizados**: Prompts estruturados com few-shot examples
2. **Validação de Respostas**: Validação automática das respostas da IA
3. **Refinamento Iterativo**: Retry automático com prompts refinados em caso de erro
4. **Cache de Respostas**: Cache em memória para respostas similares
5. **Coleta de Dados**: Estrutura para coleta de dados para fine-tuning futuro

## Componentes

### 1. Prompt Templates (`prompt_templates.py`)

Sistema de templates de prompts otimizados com:

- **Few-shot Examples**: Exemplos de análises bem-sucedidas para guiar a IA
- **Instruções Detalhadas**: Critérios claros de avaliação
- **Estrutura Consistente**: Formato padronizado para respostas JSON

**Exemplo de uso:**

```python
from src.utils.prompt_templates import PromptTemplates

prompt = PromptTemplates.build_response_analysis_prompt(
    question="Conte-me sobre sua experiência",
    response="Trabalho há 5 anos com Python...",
    position="Desenvolvedor Backend",
    use_few_shot=True
)
```

### 2. Response Refiner (`response_refiner.py`)

Sistema principal de refinamento que:

- Valida respostas automaticamente
- Faz retry com prompts refinados em caso de erro
- Usa cache para respostas similares
- Coleta dados para fine-tuning (opcional)

**Exemplo de uso:**

```python
from src.utils.response_refiner import ResponseRefiner, RefinementConfig

config = RefinementConfig(
    max_retries=3,
    enable_cache=True,
    enable_few_shot=True
)

refiner = ResponseRefiner(config)

# Análise de resposta individual
result = refiner.analyze_response(
    question="Pergunta da entrevista",
    response="Resposta do candidato",
    position="Desenvolvedor Backend"
)

# Análise completa de entrevista
result = refiner.analyze_interview(
    interview_text="Texto completo da entrevista",
    position="Desenvolvedor Backend",
    candidate_name="João Silva"
)
```

### 3. Validação de Respostas

O sistema valida automaticamente:

- **Campos obrigatórios**: Todos os campos necessários estão presentes
- **Tipos de dados**: Valores são do tipo correto
- **Ranges**: Valores estão dentro dos limites esperados
- **Formato**: Estrutura JSON válida

### 4. Cache de Respostas

Cache em memória que:

- Armazena respostas para perguntas/respostas similares
- Reduz chamadas à API OpenAI
- TTL configurável (padrão: 24 horas)

### 5. Coleta de Dados para Fine-tuning

Sistema opcional que:

- Coleta prompts e respostas da IA
- Armazena em formato JSONL
- Permite exportação para fine-tuning futuro

## Configuração

### Variáveis de Ambiente

Adicione ao seu arquivo `.env`:

```bash
# Habilitar sistema de refinamento (padrão: true)
ENABLE_RESPONSE_REFINEMENT=true

# Número máximo de tentativas de refinamento (padrão: 3)
REFINEMENT_MAX_RETRIES=3

# Habilitar cache (padrão: true)
REFINEMENT_ENABLE_CACHE=true

# Habilitar few-shot examples (padrão: true)
REFINEMENT_ENABLE_FEW_SHOT=true

# TTL do cache em horas (padrão: 24)
REFINEMENT_CACHE_TTL_HOURS=24

# Habilitar coleta de dados para fine-tuning (padrão: false)
ENABLE_FINETUNING_COLLECTION=false

# Diretório para dados de fine-tuning (padrão: data/finetuning)
FINETUNING_DATA_DIR=data/finetuning
```

## Integração

O sistema já está integrado nos seguintes arquivos:

- `src/utils/ai_analyzer.py`: Usa `ResponseRefiner` automaticamente
- `src/services/audio_interview_service.py`: Usa `ResponseRefiner` para análises completas

### Uso Automático

O sistema é usado automaticamente quando disponível. Se houver erro, faz fallback para o método legado.

### Uso Manual

Para usar diretamente:

```python
from src.utils.response_refiner import ResponseRefiner
from src.config.openai_config import OpenAIConfig

# O ResponseRefiner usa as configurações do OpenAIConfig automaticamente
refiner = ResponseRefiner()

result = refiner.analyze_response(question, response, position)
```

## Fine-tuning Futuro

### Coleta de Dados

Para habilitar coleta de dados:

```bash
ENABLE_FINETUNING_COLLECTION=true
```

Os dados serão salvos em `data/finetuning/` organizados por categoria e data.

### Exportação para Fine-tuning

A exportação para formato JSONL da OpenAI será implementada futuramente. O formato esperado é:

```json
{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

### Processo de Fine-tuning

1. **Coletar dados**: Habilitar `ENABLE_FINETUNING_COLLECTION=true`
2. **Revisar dados**: Marcar qualidade dos exemplos
3. **Exportar**: Converter para formato JSONL da OpenAI
4. **Treinar**: Usar API de fine-tuning da OpenAI
5. **Deploy**: Usar modelo fine-tuned nas análises

## Melhorias Implementadas

### Antes

- Prompts simples e genéricos
- Sem validação de respostas
- Sem retry em caso de erro
- Sem cache
- Sem estrutura para fine-tuning

### Depois

- ✅ Prompts estruturados com few-shot examples
- ✅ Validação automática de respostas
- ✅ Retry com refinamento iterativo
- ✅ Cache para respostas similares
- ✅ Estrutura completa para fine-tuning
- ✅ Configuração flexível via variáveis de ambiente

## Métricas de Qualidade

O sistema melhora a qualidade das respostas através de:

1. **Consistência**: Validação garante formato consistente
2. **Precisão**: Few-shot examples guiam a IA para respostas melhores
3. **Confiabilidade**: Retry automático reduz falhas
4. **Performance**: Cache reduz latência e custos

## Troubleshooting

### Respostas não passam na validação

- Verifique os logs para ver erros específicos
- Ajuste `validation_strict=False` para permitir fallback
- Revise os prompts em `prompt_templates.py`

### Cache não está funcionando

- Verifique se `REFINEMENT_ENABLE_CACHE=true`
- Limpe o cache: `refiner.cache.clear()`

### Coleta de dados não está salvando

- Verifique se `ENABLE_FINETUNING_COLLECTION=true`
- Verifique permissões do diretório `FINETUNING_DATA_DIR`
- Veja logs para erros específicos

## Próximos Passos

1. **Fine-tuning Real**: Implementar exportação e treinamento
2. **A/B Testing**: Comparar modelos fine-tuned vs base
3. **Feedback Loop**: Sistema de feedback para melhorar prompts
4. **Métricas Avançadas**: Tracking de qualidade das respostas
5. **Multi-modelo**: Suporte para diferentes modelos da OpenAI

