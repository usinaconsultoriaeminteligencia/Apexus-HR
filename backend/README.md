# Apexus HR - Backend

Plataforma de entrevistas por áudio com IA, assessments auditáveis e conformidade LGPD.

## 🚀 Início Rápido

### 1. Configuração Automática
```bash
# Execute o script de setup
python setup.py
```

### 2. Configuração Manual
```bash
# Copie o arquivo de exemplo
cp ENV_VARIABLES.md .env

# Edite as variáveis de ambiente
nano .env

# Instale as dependências
pip install -r requirements.txt
```

### 3. Executar a Aplicação
```bash
# Desenvolvimento
python src/main.py

# Produção com Docker
docker-compose -f ../docker-compose.production.yml up -d
```

## 🧪 Testes

### Executar Testes
```bash
# Testes unitários
pytest

# Testes com cobertura
pytest --cov=src

# Teste de setup
python test_setup.py
```

### Testes Específicos
```bash
# Apenas testes unitários
pytest -m unit

# Apenas testes de integração
pytest -m integration

# Apenas testes de segurança
pytest -m security
```

## 📁 Estrutura do Projeto

```
backend/
├── src/
│   ├── config/          # Configurações
│   ├── models/          # Modelos de dados
│   ├── routes/          # Rotas da API
│   ├── services/        # Lógica de negócio
│   ├── utils/           # Utilitários
│   ├── security/        # Middleware de segurança
│   └── monitoring/      # Logging e métricas
├── tests/               # Testes automatizados
├── migrations/          # Migrações do banco
├── requirements.txt     # Dependências Python
├── setup.py            # Script de configuração
└── test_setup.py       # Script de teste
```

## 🔧 Configuração

### Variáveis de Ambiente Obrigatórias

```bash
# Banco de Dados
POSTGRES_DB=apexus_hr
POSTGRES_USER=postgres
POSTGRES_PASSWORD=sua_senha_super_segura

# Cache
REDIS_PASSWORD=sua_senha_redis_segura

# Segurança
SECRET_KEY=sua_chave_secreta_muito_longa
JWT_SECRET_KEY=sua_chave_jwt_muito_longa

# IA
OPENAI_API_KEY=sk-sua_chave_openai_real
```

### Gerar Chaves Seguras

```python
import secrets
print("SECRET_KEY:", secrets.token_urlsafe(64))
print("JWT_SECRET_KEY:", secrets.token_urlsafe(64))
```

## 🐳 Docker

### Desenvolvimento
```bash
docker-compose up -d
```

### Produção
```bash
docker-compose -f docker-compose.production.yml up -d
```

## 📊 Monitoramento

### Health Checks
```bash
# Health check simples
curl http://localhost:5000/health/

# Health check detalhado
curl http://localhost:5000/health/detailed

# Métricas
curl http://localhost:5000/health/metrics
```

### Logs
```bash
# Logs da aplicação
docker-compose logs -f backend

# Logs de auditoria
tail -f logs/audit.log

# Logs de performance
tail -f logs/performance.log
```

## 🔒 Segurança

### Rate Limiting
- Login: 5 tentativas por 5 minutos
- API: 100 requests por minuto
- Upload: 10 uploads por minuto
- IA: 20 análises por 5 minutos

### Headers de Segurança
- Content Security Policy
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- HSTS (em produção)

## 🐛 Troubleshooting

### Problemas Comuns

#### 1. Erro de Import
```bash
# Instalar dependências
pip install -r requirements.txt

# Verificar Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

#### 2. Erro de Banco de Dados
```bash
# Verificar se PostgreSQL está rodando
docker-compose ps db

# Verificar logs
docker-compose logs db
```

#### 3. Erro de Redis
```bash
# Verificar se Redis está rodando
docker-compose ps redis

# Testar conexão
docker-compose exec redis redis-cli ping
```

#### 4. Erro de OpenAI
```bash
# Verificar chave da API
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```

## 📈 Performance

### Métricas Importantes
- Response Time: < 200ms
- Error Rate: < 1%
- CPU Usage: < 70%
- Memory Usage: < 80%

### Otimizações
- Pool de conexões do banco
- Cache Redis
- Compressão de áudio
- Processamento assíncrono

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

MIT License - veja o arquivo LICENSE para detalhes.

## 🆘 Suporte

- **Documentação**: [docs/](./docs/)
- **Issues**: [GitHub Issues](https://github.com/Fagnerpro/Recursos-Humanos/issues)
- **Email**: suporte@apexushr.com

