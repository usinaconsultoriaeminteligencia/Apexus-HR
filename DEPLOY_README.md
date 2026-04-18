# Guia de Deploy para Produção - Assistente de RH

## 🚀 Visão Geral

Este guia fornece instruções completas para deploy do Sistema de Entrevistas por Áudio com IA em ambiente de produção. O sistema foi otimizado para alta disponibilidade, segurança e performance.

## 📋 Pré-requisitos

### Requisitos de Sistema

- **Sistema Operacional**: Ubuntu 20.04+ ou CentOS 8+
- **RAM**: Mínimo 8GB (Recomendado 16GB+)
- **CPU**: Mínimo 4 cores (Recomendado 8+ cores)
- **Armazenamento**: Mínimo 100GB SSD
- **Rede**: Conexão estável com internet

### Software Necessário

```bash
# Docker e Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Utilitários
sudo apt update
sudo apt install -y curl wget git nginx certbot python3-certbot-nginx
```

## 🔧 Configuração Inicial

### 1. Clonar o Repositório

```bash
git clone https://github.com/Fagnerpro/Recursos-Humanos.git
cd Recursos-Humanos
```

### 2. Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar configurações
nano .env
```

#### Variáveis Obrigatórias

```env
# Banco de dados
POSTGRES_DB=assistente_rh
POSTGRES_USER=postgres
POSTGRES_PASSWORD=sua_senha_super_segura

# Redis
REDIS_PASSWORD=sua_senha_redis_segura

# Segurança
SECRET_KEY=sua_chave_secreta_muito_longa_e_aleatoria
JWT_SECRET_KEY=sua_chave_jwt_muito_longa_e_aleatoria

# OpenAI
OPENAI_API_KEY=sk-sua_chave_openai_aqui
OPENAI_API_BASE=https://api.openai.com/v1

# Domínio e CORS
ALLOWED_ORIGINS=https://seudominio.com,https://www.seudominio.com

# Monitoramento (opcional)
GRAFANA_PASSWORD=senha_grafana_segura
```

#### Gerar Chaves Seguras

```bash
# Gerar SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# Gerar JWT_SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 3. Configurar SSL/TLS (Recomendado)

```bash
# Obter certificado Let's Encrypt
sudo certbot --nginx -d seudominio.com -d www.seudominio.com

# Configurar renovação automática
sudo crontab -e
# Adicionar linha:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🚀 Deploy

### Deploy Automatizado (Recomendado)

```bash
# Executar deploy completo
./scripts/deploy.sh deploy

# Ou executar etapas individualmente
./scripts/deploy.sh backup    # Backup do banco
./scripts/deploy.sh test      # Executar testes
./scripts/deploy.sh deploy    # Deploy
./scripts/deploy.sh monitor   # Monitorar por 5 minutos
```

### Deploy Manual

```bash
# 1. Construir imagens
docker-compose -f docker-compose.production.yml build --no-cache

# 2. Iniciar serviços
docker-compose -f docker-compose.production.yml up -d

# 3. Verificar status
docker-compose -f docker-compose.production.yml ps

# 4. Verificar logs
docker-compose -f docker-compose.production.yml logs -f backend
```

## 📊 Monitoramento

### Health Checks

```bash
# Verificar saúde da aplicação
curl http://localhost:5000/health/

# Verificar métricas detalhadas
curl http://localhost:5000/health/detailed

# Verificar métricas de performance
curl http://localhost:5000/health/metrics
```

### Logs

```bash
# Logs da aplicação
docker-compose -f docker-compose.production.yml logs -f backend

# Logs do banco de dados
docker-compose -f docker-compose.production.yml logs -f db

# Logs do Redis
docker-compose -f docker-compose.production.yml logs -f redis

# Logs do Nginx
docker-compose -f docker-compose.production.yml logs -f nginx
```

### Monitoramento com Grafana (Opcional)

```bash
# Iniciar stack de monitoramento
docker-compose -f docker-compose.production.yml --profile monitoring up -d

# Acessar Grafana
# URL: http://localhost:3001
# Usuário: admin
# Senha: definida em GRAFANA_PASSWORD
```

## 🔒 Segurança

### Configurações de Firewall

```bash
# UFW (Ubuntu)
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Ou iptables
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -j DROP
```

### Hardening do Sistema

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Configurar fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Desabilitar root login SSH
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart ssh
```

### Backup Automatizado

```bash
# Criar script de backup
cat > /usr/local/bin/backup-assistente-rh.sh << 'EOF'
#!/bin/bash
cd /path/to/Recursos-Humanos
./scripts/deploy.sh backup
find ./backups -name "*.gz" -mtime +30 -delete
EOF

chmod +x /usr/local/bin/backup-assistente-rh.sh

# Configurar cron para backup diário
sudo crontab -e
# Adicionar linha:
# 0 2 * * * /usr/local/bin/backup-assistente-rh.sh
```

## 📈 Otimização de Performance

### Configurações de Banco de Dados

O PostgreSQL já está otimizado no docker-compose.production.yml:

- `max_connections=200`
- `shared_buffers=256MB`
- `effective_cache_size=1GB`
- `work_mem=4MB`

### Configurações de Redis

Redis configurado para:

- Persistência com AOF
- Política de eviction LRU
- Limite de memória: 512MB

### Configurações do Gunicorn

Backend configurado com:

- 4 workers
- Worker class: gevent
- 1000 conexões por worker
- Timeout: 30 segundos

## 🔄 Atualizações

### Atualização com Zero Downtime

```bash
# 1. Backup
./scripts/deploy.sh backup

# 2. Atualizar código
git pull origin main

# 3. Deploy
./scripts/deploy.sh deploy

# 4. Verificar saúde
./scripts/deploy.sh health
```

### Rollback

```bash
# Em caso de problemas
./scripts/deploy.sh rollback
```

## 🐛 Troubleshooting

### Problemas Comuns

#### 1. Container não inicia

```bash
# Verificar logs
docker-compose -f docker-compose.production.yml logs backend

# Verificar recursos
docker stats

# Verificar conectividade
docker-compose -f docker-compose.production.yml exec backend ping db
```

#### 2. Banco de dados não conecta

```bash
# Verificar se o banco está rodando
docker-compose -f docker-compose.production.yml ps db

# Testar conexão
docker-compose -f docker-compose.production.yml exec db psql -U postgres -d assistente_rh -c "SELECT 1;"
```

#### 3. Redis não conecta

```bash
# Verificar Redis
docker-compose -f docker-compose.production.yml exec redis redis-cli ping

# Com senha
docker-compose -f docker-compose.production.yml exec redis redis-cli -a $REDIS_PASSWORD ping
```

#### 4. OpenAI API não funciona

```bash
# Testar API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models

# Verificar logs
docker-compose -f docker-compose.production.yml logs backend | grep -i openai
```

### Comandos Úteis

```bash
# Reiniciar serviço específico
docker-compose -f docker-compose.production.yml restart backend

# Executar comando no container
docker-compose -f docker-compose.production.yml exec backend bash

# Limpar volumes (CUIDADO!)
docker-compose -f docker-compose.production.yml down --volumes

# Verificar uso de recursos
docker system df
docker stats
```

## 📞 Suporte

### Logs Importantes

- **Aplicação**: `/app/logs/application.log`
- **Auditoria**: `/app/logs/audit.log`
- **Performance**: `/app/logs/performance.log`
- **Nginx**: `/var/log/nginx/`

### Métricas de Monitoramento

- **CPU**: < 80%
- **Memória**: < 85%
- **Disco**: > 20% livre
- **Response Time**: < 2s
- **Error Rate**: < 5%

### Contatos

- **Equipe de Desenvolvimento**: dev@assistente-rh.com
- **Suporte Técnico**: suporte@assistente-rh.com
- **Emergências**: +55 11 99999-9999

## 📚 Documentação Adicional

- [API Documentation](./backend/docs/API.md)
- [Architecture Overview](./docs/ARCHITECTURE.md)
- [Security Guidelines](./docs/SECURITY.md)
- [Performance Tuning](./docs/PERFORMANCE.md)

---

## ⚠️ Notas Importantes

1. **Sempre faça backup antes de atualizações**
2. **Teste em ambiente de staging primeiro**
3. **Monitore logs após deploy**
4. **Mantenha as chaves de API seguras**
5. **Atualize dependências regularmente**

## 🎯 Próximos Passos

Após o deploy bem-sucedido:

1. ✅ Configurar monitoramento contínuo
2. ✅ Implementar alertas automáticos
3. ✅ Configurar backup automático
4. ✅ Documentar procedimentos operacionais
5. ✅ Treinar equipe de suporte

---

**Versão**: 1.0.0  
**Última Atualização**: Dezembro 2024  
**Autor**: Equipe Assistente RH

