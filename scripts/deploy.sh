#!/bin/bash

# Script de Deploy Automatizado - Assistente de RH
# Versão: 1.0.0
# Descrição: Script para deploy seguro em produção

set -euo pipefail  # Parar em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_ROOT/backups"
LOG_FILE="$PROJECT_ROOT/deploy.log"
DOCKER_COMPOSE_FILE="docker-compose.production.yml"

# Funções utilitárias
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

# Verificar pré-requisitos
check_prerequisites() {
    log "Verificando pré-requisitos..."
    
    # Verificar se Docker está instalado e rodando
    if ! command -v docker &> /dev/null; then
        error "Docker não está instalado"
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker não está rodando"
    fi
    
    # Verificar se Docker Compose está instalado
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose não está instalado"
    fi
    
    # Verificar se arquivo .env existe
    if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
        error "Arquivo .env não encontrado. Copie .env.example para .env e configure as variáveis."
    fi
    
    # Verificar variáveis críticas
    source "$PROJECT_ROOT/.env"
    
    local required_vars=(
        "POSTGRES_PASSWORD"
        "REDIS_PASSWORD"
        "SECRET_KEY"
        "JWT_SECRET_KEY"
        "OPENAI_API_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error "Variável de ambiente $var não está definida no arquivo .env"
        fi
    done
    
    log "Pré-requisitos verificados com sucesso"
}

# Criar backup do banco de dados
backup_database() {
    log "Criando backup do banco de dados..."
    
    mkdir -p "$BACKUP_DIR"
    
    local backup_file="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
    
    # Verificar se container do banco está rodando
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps db | grep -q "Up"; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T db pg_dump \
            -U "${POSTGRES_USER:-postgres}" \
            -d "${POSTGRES_DB:-assistente_rh}" \
            --no-owner --no-privileges > "$backup_file"
        
        if [[ -s "$backup_file" ]]; then
            log "Backup criado: $backup_file"
            
            # Comprimir backup
            gzip "$backup_file"
            log "Backup comprimido: $backup_file.gz"
        else
            warn "Backup está vazio, removendo arquivo"
            rm -f "$backup_file"
        fi
    else
        warn "Container do banco não está rodando, pulando backup"
    fi
}

# Executar testes
run_tests() {
    log "Executando testes..."
    
    # Construir imagem de teste
    docker-compose -f docker-compose.test.yml build --no-cache
    
    # Executar testes
    if docker-compose -f docker-compose.test.yml run --rm backend pytest; then
        log "Todos os testes passaram"
    else
        error "Testes falharam. Deploy cancelado."
    fi
    
    # Limpar containers de teste
    docker-compose -f docker-compose.test.yml down --volumes --remove-orphans
}

# Verificar saúde dos serviços
health_check() {
    log "Verificando saúde dos serviços..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        info "Tentativa $attempt/$max_attempts"
        
        # Verificar backend
        if curl -f -s http://localhost:5000/health/ > /dev/null; then
            log "Backend está saudável"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            error "Backend não respondeu após $max_attempts tentativas"
        fi
        
        sleep 10
        ((attempt++))
    done
    
    # Verificar outros serviços
    local services=("db:5432" "redis:6379")
    
    for service in "${services[@]}"; do
        local host="${service%:*}"
        local port="${service#*:}"
        
        if nc -z localhost "$port"; then
            log "Serviço $host:$port está disponível"
        else
            warn "Serviço $host:$port não está disponível"
        fi
    done
}

# Deploy principal
deploy() {
    log "Iniciando deploy..."
    
    cd "$PROJECT_ROOT"
    
    # Parar serviços existentes
    log "Parando serviços existentes..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans
    
    # Limpar imagens antigas (opcional)
    if [[ "${CLEAN_IMAGES:-false}" == "true" ]]; then
        log "Limpando imagens antigas..."
        docker system prune -f
        docker image prune -a -f
    fi
    
    # Construir imagens
    log "Construindo imagens..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" build --no-cache
    
    # Iniciar serviços
    log "Iniciando serviços..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    
    # Aguardar serviços ficarem prontos
    log "Aguardando serviços ficarem prontos..."
    sleep 30
    
    # Verificar saúde
    health_check
    
    log "Deploy concluído com sucesso!"
}

# Rollback para versão anterior
rollback() {
    log "Iniciando rollback..."
    
    # Parar serviços atuais
    docker-compose -f "$DOCKER_COMPOSE_FILE" down
    
    # Restaurar backup mais recente
    local latest_backup=$(ls -t "$BACKUP_DIR"/*.sql.gz 2>/dev/null | head -n1)
    
    if [[ -n "$latest_backup" ]]; then
        log "Restaurando backup: $latest_backup"
        
        # Iniciar apenas o banco
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d db
        sleep 10
        
        # Restaurar backup
        gunzip -c "$latest_backup" | docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T db \
            psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-assistente_rh}"
        
        log "Backup restaurado"
    else
        warn "Nenhum backup encontrado para rollback"
    fi
    
    # Iniciar versão anterior (assumindo que as imagens ainda existem)
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    
    log "Rollback concluído"
}

# Monitoramento pós-deploy
monitor() {
    log "Iniciando monitoramento pós-deploy..."
    
    local duration=${1:-300}  # 5 minutos por padrão
    local end_time=$((SECONDS + duration))
    
    while [[ $SECONDS -lt $end_time ]]; do
        # Verificar status dos containers
        local unhealthy_containers=$(docker-compose -f "$DOCKER_COMPOSE_FILE" ps --filter "health=unhealthy" -q)
        
        if [[ -n "$unhealthy_containers" ]]; then
            error "Containers não saudáveis detectados: $unhealthy_containers"
        fi
        
        # Verificar logs de erro
        local error_count=$(docker-compose -f "$DOCKER_COMPOSE_FILE" logs --since=1m backend 2>&1 | grep -i error | wc -l)
        
        if [[ $error_count -gt 5 ]]; then
            warn "Muitos erros detectados nos logs ($error_count)"
        fi
        
        info "Monitoramento OK - $(date)"
        sleep 30
    done
    
    log "Monitoramento concluído"
}

# Função principal
main() {
    local command=${1:-deploy}
    
    case $command in
        "deploy")
            check_prerequisites
            backup_database
            run_tests
            deploy
            monitor
            ;;
        "rollback")
            rollback
            ;;
        "health")
            health_check
            ;;
        "backup")
            backup_database
            ;;
        "test")
            run_tests
            ;;
        "monitor")
            monitor "${2:-300}"
            ;;
        *)
            echo "Uso: $0 {deploy|rollback|health|backup|test|monitor}"
            echo ""
            echo "Comandos:"
            echo "  deploy   - Deploy completo (padrão)"
            echo "  rollback - Rollback para versão anterior"
            echo "  health   - Verificar saúde dos serviços"
            echo "  backup   - Criar backup do banco"
            echo "  test     - Executar testes"
            echo "  monitor  - Monitorar serviços (opcional: duração em segundos)"
            exit 1
            ;;
    esac
}

# Capturar sinais para limpeza
trap 'error "Deploy interrompido pelo usuário"' INT TERM

# Executar função principal
main "$@"

