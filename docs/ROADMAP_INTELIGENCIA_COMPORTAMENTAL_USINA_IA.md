# Roadmap de Inteligencia Comportamental

## 0-30 dias: auditabilidade minima

- Publicar catalogo de rubricas versionadas.
- Persistir evidencias por score.
- Registrar versao da rubrica e versao do modelo em cada avaliacao.
- Expor endpoint interno para rubricas e tese de produto.
- Padronizar linguagem de feedback para RH e candidato.

## 31-60 dias: validacao humana

- Criar fila de revisao de avaliacoes.
- Permitir ajuste de score com motivo obrigatorio.
- Medir divergencia entre IA e avaliador humano.
- Bloquear decisoes automaticas sem revisao em cargos sensiveis.

## 61-90 dias: dataset e fairness

- Anonimizar respostas para dataset de melhoria continua.
- Criar indicadores de consistencia por cargo.
- Medir distribuicao de scores por grupo permitido e juridicamente adequado.
- Criar relatorio de fairness por cliente.

## 91-180 dias: ROI e defensibilidade

- Medir reducao de tempo de triagem.
- Comparar qualidade de shortlist antes e depois da plataforma.
- Medir correlacao entre aderencia comportamental e desempenho/retencao quando o cliente permitir.
- Criar pricing por modulo: entrevista, auditoria, fairness, analytics e API.

## Norte de arquitetura

Cada avaliacao deve ser tratada como um objeto auditavel:

- resposta original;
- rubrica aplicada;
- evidencia extraida;
- score;
- confianca;
- versao do modelo;
- versao da rubrica;
- revisao humana;
- metricas agregadas de fairness e ROI.
