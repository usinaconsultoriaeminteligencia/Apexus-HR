# LGPD Operacional

Este documento descreve como utilizar os novos recursos de privacidade e proteção
de dados adicionados à aplicação, em conformidade com a Lei Geral de
Proteção de Dados (LGPD) e regulamentações similares.

## 1. Consentimento

O endpoint `/api/privacy/consent` permite registrar ou revogar o consentimento
de um usuário ou candidato. Envie uma requisição `POST` com JSON no formato:

```json
{
  "subject_type": "user" | "candidate",
  "subject_id": 1,
  "consent": true
}
```

Quando `consent` for `true`, os campos `consent_given` e `consent_date`
dos modelos serão atualizados (caso existam). Quando `false`, o
consentimento será revogado.

## 2. Portabilidade de dados

Para exportar todos os dados relacionados a um usuário ou candidato, faça
uma requisição `GET` para:

```
/api/privacy/export/<subject_type>/<subject_id>
```

Por exemplo, `/api/privacy/export/candidate/42`. O resultado conterá um
JSON com todos os campos (inclusive sensíveis) retornados pelo método
`to_dict(include_sensitive=True)` do modelo correspondente.

## 3. Anonimização/Exclusão lógica

Para anonimizar ou desativar um registro, envie uma requisição `POST` para:

```
/api/privacy/delete/<subject_type>/<subject_id>
```

Se o modelo implementar o método `anonymize()`, ele será chamado para
sobrescrever ou limpar dados pessoais. Caso contrário, o registro terá o
campo `is_active` definido como `False`. Após executar a operação, o
registro não aparecerá mais em listagens ativas, mas permanecerá no
banco de dados para fins de auditoria.

## 4. Considerações

* As rotas de privacidade estão disponíveis apenas em ambientes
  autenticados e controlados. É recomendável protegê‑las com checagens de
  permissão específicas para administradores ou responsáveis pelo
  tratamento de dados.
* Antes de entrar em produção, revise as políticas de retenção de dados
  da sua organização e ajuste a lógica de anonimização conforme
  necessário.
