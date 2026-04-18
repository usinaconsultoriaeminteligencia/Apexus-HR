# Incidente de segurança — vazamento de credenciais no repositório

Data de identificação: 2026-04-17
Status: **credenciais ainda no histórico do git; rotação obrigatória pendente.**

## Resumo

Uma auditoria do repositório identificou que segredos de produção estavam
rastreados pelo git e, portanto, acessíveis no histórico a qualquer pessoa
com acesso de leitura ao repositório (ou a um fork/clone antigo).

## Segredos expostos

| Arquivo | Segredo | Commit que introduziu |
| --- | --- | --- |
| `backend/.env` | `OPENAI_API_KEY`, `SECRET_KEY`, `JWT_SECRET_KEY`, senhas Postgres/Redis de dev | `f0739fb3` (2025-09-14) |
| `.env.txt` | `OPENAI_API_KEY` real | `f0739fb3` (2025-09-14) |
| `.env.production.example` | `OPENAI_API_KEY` real | `f0739fb3` (2025-09-14) |
| `env.production.example` | mesmos valores do `.env.production.example` | (dup) |

A mesma `OPENAI_API_KEY` (prefixo `sk-proj-V0wIpv4ihIDsl6Zixmu5K...`) aparece
nos três arquivos.

## Ações já aplicadas neste commit

1. Os arquivos foram removidos do índice com `git rm --cached` (continuam no
   working tree local para não perder configuração pessoal, mas deixaram de
   ser versionados).
2. `.gitignore` foi endurecido para cobrir `*.env.*`, `.env.txt`,
   `*.env.production.example`, `runtime-*.log` e `**/.venv/`.
3. `.env.example` (raiz) e `backend/.env.example` foram reescritos com
   apenas placeholders; são agora a fonte canônica de documentação de
   variáveis.

## Ações **obrigatórias** a executar manualmente

### 1. Rotacionar imediatamente

- [ ] Revogar a chave `sk-proj-V0wIpv4ihIDsl6Zixmu5K...` no painel da
      OpenAI (https://platform.openai.com/api-keys).
- [ ] Gerar uma nova `OPENAI_API_KEY` e injetá-la via secret manager ou
      variável de ambiente — **nunca** em arquivo versionado.
- [ ] Regenerar `SECRET_KEY` e `JWT_SECRET_KEY`:
      `python -c "import secrets; print(secrets.token_urlsafe(64))"`.
      Ao regenerar JWT_SECRET_KEY, todos os tokens ativos serão
      invalidados; comunicar usuários.
- [ ] Trocar senhas de Postgres e Redis em qualquer ambiente que usou os
      valores do `backend/.env` como base (dev/staging, ao menos).

### 2. Limpar o histórico do git (decisão da equipe)

Mesmo com `git rm --cached`, os valores continuam acessíveis em commits
antigos. Opções:

- **Opção A (recomendada)**: reescrever o histórico com
  [`git-filter-repo`](https://github.com/newren/git-filter-repo) para remover
  os arquivos:

  ```bash
  git filter-repo --invert-paths \
    --path .env.production.example \
    --path .env.txt \
    --path backend/.env \
    --path env.production.example
  ```

  Depois, force push e exigir que todos os colaboradores re-clonem. Quem já
  tem clones antigos guarda uma cópia do histórico sujo, por isso a
  rotação do passo 1 é obrigatória independentemente desta limpeza.

- **Opção B**: assumir a chave como pública, garantir rotação e deixar
  claro em `README` que o histórico contém segredos obsoletos.

### 3. Auditoria de uso

- [ ] Verificar logs da OpenAI pela chave revogada (uso anômalo, custos).
- [ ] Verificar logs de acesso ao banco (logins bem-sucedidos/falhos) no
      período em que as senhas de dev estavam expostas.

## Medidas preventivas

- Integrar [`gitleaks`](https://github.com/gitleaks/gitleaks) como pre-commit
  hook e no pipeline de CI.
- Usar um secret manager (AWS Secrets Manager / Doppler / Vault). O
  `docker-compose.production.yml` deve ler do ambiente do host, não de
  `.env` commitado.
- Revisões de PR devem ter checklist explícito: "nenhum arquivo `.env*`
  com valores reais foi adicionado?".
