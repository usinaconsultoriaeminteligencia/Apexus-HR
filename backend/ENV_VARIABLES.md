# Variáveis de Ambiente Necessárias

## Configurações Obrigatórias

### Banco de Dados
```bash
POSTGRES_DB=assistente_rh
POSTGRES_USER=postgres
POSTGRES_PASSWORD=sua_senha_super_segura_aqui
```

### Cache
```bash
REDIS_PASSWORD=sua_senha_redis_segura_aqui
```

### Segurança
```bash
SECRET_KEY=sua_chave_secreta_muito_longa_e_aleatoria_aqui
JWT_SECRET_KEY=sua_chave_jwt_muito_longa_e_aleatoria_aqui
```

### IA
```bash
OPENAI_API_KEY=sk-sua_chave_openai_real_aqui
OPENAI_API_BASE=https://api.openai.com/v1
```

## Configurações Opcionais

### Ambiente
```bash
ENVIRONMENT=production
DEBUG=false
TESTING=false
```

### CORS
```bash
ALLOWED_ORIGINS=https://seudominio.com,https://www.seudominio.com
```

### Upload
```bash
MAX_UPLOAD_SIZE=100
UPLOAD_FOLDER=/app/uploads
```

### Banco de Dados (Pool)
```bash
DB_POOL_SIZE=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
DB_MAX_OVERFLOW=30
```

### Logging
```bash
LOG_LEVEL=INFO
LOG_SQL=false
```

### Migrações
```bash
RUN_MIGRATIONS=true
```

### Monitoramento (Opcional)
```bash
GRAFANA_PASSWORD=senha_grafana_segura_aqui
SENTRY_DSN=sua_sentry_dsn_aqui
```

### Email (Opcional)
```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=seu_email@gmail.com
MAIL_PASSWORD=sua_senha_de_app
MAIL_DEFAULT_SENDER=noreply@assistenterh.com
```

## Como Gerar Chaves Seguras

### SECRET_KEY e JWT_SECRET_KEY
```python
import secrets
print("SECRET_KEY:", secrets.token_urlsafe(64))
print("JWT_SECRET_KEY:", secrets.token_urlsafe(64))
```

### Senhas do Banco e Redis
Use senhas complexas com pelo menos 32 caracteres, incluindo letras maiúsculas, minúsculas, números e símbolos.

