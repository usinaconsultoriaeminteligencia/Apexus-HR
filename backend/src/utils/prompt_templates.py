"""
Sistema de templates de prompts otimizados para análise de entrevistas
Inclui few-shot examples e técnicas de prompt engineering avançadas
"""
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class PromptExample:
    """Exemplo few-shot para melhorar qualidade das respostas"""
    question: str
    response: str
    position: str
    analysis: Dict[str, Any]


class PromptTemplates:
    """Templates de prompts otimizados com few-shot learning"""
    
    # Exemplos few-shot para análise de respostas individuais
    RESPONSE_ANALYSIS_EXAMPLES = [
        PromptExample(
            question="Conte-me sobre sua experiência com Python",
            response="Trabalho com Python há 5 anos, principalmente em desenvolvimento web com Django e Flask. Já desenvolvi APIs RESTful e trabalhei com processamento de dados usando pandas e numpy.",
            position="Desenvolvedor Backend",
            analysis={
                "relevance": 95.0,
                "technical_accuracy": 90.0,
                "communication": 85.0,
                "summary": "Resposta muito relevante, demonstra experiência sólida com a tecnologia mencionada e conhecimento prático de frameworks e bibliotecas."
            }
        ),
        PromptExample(
            question="Como você lida com prazos apertados?",
            response="Eu organizo minhas tarefas por prioridade e me comunico proativamente com a equipe sobre possíveis atrasos.",
            position="Gerente de Projetos",
            analysis={
                "relevance": 88.0,
                "technical_accuracy": 75.0,
                "communication": 92.0,
                "summary": "Boa resposta comportamental, demonstra organização e comunicação, mas poderia ser mais específica com exemplos concretos."
            }
        ),
        PromptExample(
            question="Qual sua maior fraqueza?",
            response="Às vezes sou muito perfeccionista e demoro mais tempo do que deveria em algumas tarefas.",
            position="Analista de Dados",
            analysis={
                "relevance": 70.0,
                "technical_accuracy": 60.0,
                "communication": 75.0,
                "summary": "Resposta genérica e clichê. Não demonstra autocrítica genuína ou plano de desenvolvimento."
            }
        )
    ]
    
    # Exemplos few-shot para análise completa de entrevista
    INTERVIEW_ANALYSIS_EXAMPLES = [
        {
            "position": "Desenvolvedor Full Stack",
            "candidate_name": "João Silva",
            "summary": "Candidato com experiência sólida em React e Node.js, demonstrou conhecimento técnico adequado mas precisa melhorar comunicação de ideias complexas.",
            "analysis": {
                "pontuacao_tecnica": 8.5,
                "pontuacao_comportamental": 7.0,
                "perfil_disc": "C",
                "descricao_perfil_disc": "Analítico e metódico, focado em qualidade técnica",
                "pontos_fortes": ["Conhecimento técnico sólido", "Experiência com tecnologias modernas", "Capacidade de resolver problemas complexos"],
                "areas_desenvolvimento": ["Comunicação interpessoal", "Trabalho em equipe", "Apresentação de ideias"],
                "recomendacao": "CONTRATAR",
                "fit_cultural": 7.5
            }
        }
    ]
    
    @staticmethod
    def build_response_analysis_prompt(
        question: str,
        response: str,
        position: str,
        use_few_shot: bool = True
    ) -> str:
        """
        Constrói prompt otimizado para análise de resposta individual
        
        Args:
            question: Pergunta da entrevista
            response: Resposta do candidato
            position: Posição para qual está se candidatando
            use_few_shot: Se deve incluir exemplos few-shot
            
        Returns:
            Prompt formatado
        """
        base_prompt = """Você é um analista sênior de RH especializado em avaliação técnica e comportamental de candidatos.

Sua tarefa é analisar respostas de entrevistas de forma objetiva, justa e profissional.

INSTRUÇÕES:
1. Avalie a RELEVÂNCIA: A resposta está diretamente relacionada à pergunta e à posição?
2. Avalie a PRECISÃO TÉCNICA: Quando aplicável, a informação técnica está correta?
3. Avalie a COMUNICAÇÃO: A resposta é clara, estruturada e bem articulada?

ESCALA DE AVALIAÇÃO:
- 90-100: Excepcional, supera expectativas
- 70-89: Bom, atende expectativas
- 50-69: Adequado, mas com lacunas
- 30-49: Insuficiente, precisa melhorar significativamente
- 0-29: Muito fraco, não atende requisitos

"""
        
        if use_few_shot and PromptTemplates.RESPONSE_ANALYSIS_EXAMPLES:
            base_prompt += "EXEMPLOS DE ANÁLISE:\n\n"
            for i, example in enumerate(PromptTemplates.RESPONSE_ANALYSIS_EXAMPLES[:2], 1):
                base_prompt += f"""Exemplo {i}:
Pergunta: {example.question}
Resposta: {example.response}
Posição: {example.position}
Análise: {json.dumps(example.analysis, ensure_ascii=False, indent=2)}

"""
        
        base_prompt += f"""
ANÁLISE SOLICITADA:
Posição: {position}
Pergunta: {question}
Resposta do candidato: {response}

Retorne APENAS um JSON válido com a seguinte estrutura:
{{
  "relevance": <número 0-100>,
  "technical_accuracy": <número 0-100>,
  "communication": <número 0-100>,
  "summary": "<resumo objetivo e profissional da análise em 2-3 frases>"
}}

Seja específico e objetivo. Evite generalizações."""
        
        return base_prompt
    
    @staticmethod
    def build_interview_analysis_prompt(
        interview_text: str,
        position: str,
        candidate_name: str,
        use_few_shot: bool = True
    ) -> tuple[str, str]:
        """
        Constrói prompt otimizado para análise completa de entrevista
        
        Returns:
            Tupla (system_message, user_message)
        """
        system_message = """Você é um analista sênior de RH com mais de 15 anos de experiência em recrutamento e seleção.

Sua especialidade é avaliar candidatos de forma objetiva, justa e baseada em evidências.

DIRETRIZES DE AVALIAÇÃO:
- Seja objetivo e baseado em fatos, não em impressões subjetivas
- Considere o contexto da posição e nível esperado
- Identifique tanto pontos fortes quanto áreas de desenvolvimento
- Forneça feedback construtivo e acionável
- Use critérios DISC de forma precisa e justificada

CRITÉRIOS DISC:
- D (Dominância): Assertivo, direto, focado em resultados, toma decisões rápidas
- I (Influência): Comunicativo, entusiasta, persuasivo, trabalha bem em equipe
- S (Estabilidade): Paciente, leal, trabalhador em equipe, valoriza estabilidade
- C (Conformidade): Analítico, preciso, metódico, focado em qualidade e processos

ESCALAS:
- Pontuações (0-10): 9-10 Excepcional, 7-8 Bom, 5-6 Adequado, 3-4 Insuficiente, 0-2 Muito fraco
- Recomendação: CONTRATAR (9+), CONSIDERAR (6-8), NAO_CONTRATAR (<6)

Sempre responda em JSON válido, sem texto adicional."""
        
        user_prompt = f"""Analise esta entrevista completa para a posição de {position} com o candidato {candidate_name}.

TRANSCRIÇÃO DA ENTREVISTA:
{interview_text}

Forneça uma análise completa e detalhada em formato JSON com a seguinte estrutura EXATA:

{{
  "pontuacao_tecnica": <número 0-10 com uma casa decimal>,
  "pontuacao_comportamental": <número 0-10 com uma casa decimal>,
  "perfil_disc": "<D, I, S ou C>",
  "descricao_perfil_disc": "<descrição de 2-3 frases justificando o perfil>",
  "pontos_fortes": ["ponto forte 1", "ponto forte 2", "ponto forte 3"],
  "areas_desenvolvimento": ["área 1", "área 2", "área 3"],
  "recomendacao": "<CONTRATAR, CONSIDERAR ou NAO_CONTRATAR>",
  "resumo_executivo": "<parágrafo de 4-5 frases com resumo completo da avaliação>",
  "feedback_detalhado": "<feedback construtivo de 3-4 frases para o candidato>",
  "fit_cultural": <número 0-10 com uma casa decimal>,
  "proximos_passos": ["próximo passo 1", "próximo passo 2", "próximo passo 3"]
}}

IMPORTANTE:
- Base suas avaliações nas respostas reais do candidato
- Seja específico e cite exemplos da entrevista quando possível
- Pontuações devem refletir o desempenho real, não apenas ser generosas
- Recomendação deve ser consistente com as pontuações"""
        
        return system_message, user_prompt
    
    @staticmethod
    def build_refinement_prompt(
        original_response: str,
        validation_errors: List[str],
        context: Optional[str] = None
    ) -> str:
        """
        Constrói prompt para refinamento iterativo de resposta
        
        Args:
            original_response: Resposta original da IA
            validation_errors: Lista de erros de validação encontrados
            context: Contexto adicional se necessário
            
        Returns:
            Prompt para refinamento
        """
        prompt = f"""A resposta anterior da análise não atendeu aos critérios de qualidade.

RESPOSTA ORIGINAL:
{original_response}

ERROS ENCONTRADOS:
{chr(10).join(f"- {error}" for error in validation_errors)}

"""
        
        if context:
            prompt += f"CONTEXTO ADICIONAL:\n{context}\n\n"
        
        prompt += """Por favor, forneça uma resposta corrigida que:
1. Atenda todos os critérios de validação
2. Mantenha a qualidade e objetividade da análise original
3. Seja um JSON válido e bem formatado
4. Inclua todos os campos obrigatórios

Responda APENAS com o JSON corrigido, sem texto adicional."""
        
        return prompt

