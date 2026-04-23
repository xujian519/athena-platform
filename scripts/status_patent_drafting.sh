#!/bin/bash
###############################################################################
# PatentDraftingProxy状态检查脚本
# PatentDraftingProxy Status Check Script
#
# 功能: 检查PatentDraftingProxy服务运行状态
# 使用: bash scripts/status_patent_drafting.sh [environment]
# 参数:
#   environment - 环境名称(dev/test/prod)，默认prod
#   --verbose    - 显示详细状态信息
#
# 示例:
#   bash scripts/status_patent_drafting.sh prod
#   bash scripts/status_patent_drafting.sh prod --verbose
###############################################################################

set -e

# ==================== 配置 ====================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENVIRONMENT="${1:-prod}"
VERBOSE=false
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.patent-drafting.yml"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ==================== 解析参数 ====================
if [ "$2" == "--verbose" ]; then
    VERBOSE=true
fi

# ==================== 打印函数 ====================
print_header() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  PatentDraftingProxy 服务状态${NC}"
    echo -e "${CYAN}  环境: ${ENVIRONMENT}${NC}"
    echo -e "${CYAN}  时间: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_section() {
    echo ""
    echo -e "${BLUE}▶ $1${NC}"
    echo ""
}

print_status() {
    local service=$1
    local status=$2
    local message=$3
    
    case $status in
        "running")
            echo -e "  ${GREEN}✓${NC} ${service}: ${GREEN}运行中${NC} ${message}"
            ;;
        "stopped")
            echo -e "  ${RED}✗${NC} ${service}: ${RED}已停止${NC} ${message}"
            ;;
        "warning")
            echo -e "  ${YELLOW}⚠${NC} ${service}: ${YELLOW}警告${NC} ${message}"
            ;;
        *)
            echo -e "  ${service}: ${message}"
            ;;
    esac
}

# ==================== 检查Docker容器 ====================
check_containers() {
    print_section "Docker容器状态"
    
    cd "${PROJECT_ROOT}"
    
    if ! docker compose -f "${COMPOSE_FILE}" --profile "${ENVIRONMENT}" ps 2>/dev/null | grep -q .; then
        print_status "Docker Compose" "stopped" "没有运行的服务"
        return 1
    fi
    
    docker compose -f "${COMPOSE_FILE}" --profile "${ENVIRONMENT}" ps | while read line; do
        if echo "$line" | grep -q "Up"; then
            local service=$(echo "$line" | awk '{print $1}')
            local uptime=$(echo "$line" | awk '{print $4, $5, $6}')
            print_status "$service" "running" "(${uptime})"
        elif echo "$line" | grep -q "Exited"; then
            local service=$(echo "$line" | awk '{print $1}')
            local exit_code=$(echo "$line" | grep -o "Exited ([0-9]*)" | awk '{print $2}')
            print_status "$service" "stopped" "(退出码: ${exit_code})"
        fi
    done
}

# ==================== 检查健康状态 ====================
check_health() {
    print_section "健康检查"
    
    # 主应用健康检查
    if curl -sf http://localhost:8010/health > /dev/null 2>&1; then
        local health=$(curl -s http://localhost:8010/health)
        print_status "主应用健康检查" "running"
        
        if [ "$VERBOSE" = true ]; then
            echo "    响应: ${health}"
        fi
    else
        print_status "主应用健康检查" "stopped" "无法连接"
    fi
    
    # Prometheus指标检查
    if curl -sf http://localhost:9090/metrics > /dev/null 2>&1; then
        print_status "Prometheus指标" "running"
    else
        print_status "Prometheus指标" "warning" "指标端点不可用"
    fi
}

# ==================== 检查资源使用 ====================
check_resources() {
    if [ "$VERBOSE" != true ]; then
        return
    fi
    
    print_section "资源使用"
    
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" \
        $(docker compose -f "${COMPOSE_FILE}" --profile "${ENVIRONMENT}" ps -q) 2>/dev/null || echo "  无法获取资源使用信息"
}

# ==================== 检查日志 ====================
check_logs() {
    if [ "$VERBOSE" != true ]; then
        return
    fi
    
    print_section "最近日志(最后10行)"
    
    if docker ps | grep -q patent-drafting-api; then
        echo "  === 主应用日志 ==="
        docker logs --tail 10 patent-drafting-api 2>&1 | sed 's/^/    /'
    fi
}

# ==================== 检查端口占用 ====================
check_ports() {
    print_section "端口占用"
    
    local ports=(8010 9090 5432 6379 7687 6333)
    
    for port in "${ports[@]}"; do
        if lsof -i :"${port}" > /dev/null 2>&1; then
            local process=$(lsof -i :"${port}" | tail -1 | awk '{print $1}')
            print_status "端口 ${port}" "running" "(${process})"
        else
            print_status "端口 ${port}" "stopped" "未占用"
        fi
    done
}

# ==================== 检查数据库连接 ====================
check_databases() {
    print_section "数据库连接"
    
    # PostgreSQL
    if docker ps | grep -q patent-drafting-postgres; then
        if docker exec patent-drafting-postgres pg_isready -U "${POSTGRES_USER:-athena}" > /dev/null 2>&1; then
            local db_size=$(docker exec patent-drafting-postgres psql -U "${POSTGRES_USER:-athena}" -d "${POSTGRES_DB:-athena}" -t -c "SELECT pg_size_pretty(pg_database_size('${POSTGRES_DB:-athena}'));" 2>/dev/null | xargs)
            print_status "PostgreSQL" "running" "(大小: ${db_size})"
        else
            print_status "PostgreSQL" "stopped" "连接失败"
        fi
    else
        print_status "PostgreSQL" "stopped" "容器未运行"
    fi
    
    # Redis
    if docker ps | grep -q patent-drafting-redis; then
        if docker exec patent-drafting-redis redis-cli -a "${REDIS_PASSWORD:-redis123}" ping > /dev/null 2>&1; then
            local redis_memory=$(docker exec patent-drafting-redis redis-cli -a "${REDIS_PASSWORD:-redis123}" INFO memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
            print_status "Redis" "running" "(内存: ${redis_memory})"
        else
            print_status "Redis" "stopped" "连接失败"
        fi
    else
        print_status "Redis" "stopped" "容器未运行"
    fi
    
    # Neo4j
    if docker ps | grep -q patent-drafting-neo4j; then
        if curl -sf http://localhost:7474 > /dev/null 2>&1; then
            print_status "Neo4j" "running"
        else
            print_status "Neo4j" "stopped" "Web界面不可用"
        fi
    else
        print_status "Neo4j" "stopped" "容器未运行"
    fi
    
    # Qdrant
    if docker ps | grep -q patent-drafting-qdrant; then
        if curl -sf http://localhost:6333/health > /dev/null 2>&1; then
            print_status "Qdrant" "running"
        else
            print_status "Qdrant" "stopped" "健康检查失败"
        fi
    else
        print_status "Qdrant" "stopped" "容器未运行"
    fi
}

# ==================== 检查监控服务 ====================
check_monitoring() {
    print_section "监控服务"
    
    # Prometheus
    if docker ps | grep -q patent-drafting-prometheus; then
        print_status "Prometheus" "running"
    else
        print_status "Prometheus" "stopped" "容器未运行"
    fi
    
    # Grafana
    if docker ps | grep -q patent-drafting-grafana; then
        print_status "Grafana" "running" "(http://localhost:3000)"
    else
        print_status "Grafana" "stopped" "容器未运行"
    fi
    
    # Alertmanager
    if docker ps | grep -q patent-drafting-alertmanager; then
        print_status "Alertmanager" "running"
    else
        print_status "Alertmanager" "stopped" "容器未运行"
    fi
}

# ==================== 显示访问地址 ====================
show_endpoints() {
    print_section "服务访问地址"
    
    echo "  主应用:      http://localhost:8010"
    echo "  健康检查:    http://localhost:8010/health"
    echo "  API文档:     http://localhost:8010/docs"
    echo "  Prometheus:  http://localhost:9090"
    echo "  Grafana:     http://localhost:3000 (admin/admin123)"
    echo "  Alertmanager: http://localhost:9093"
    echo "  PostgreSQL:  localhost:5432"
    echo "  Redis:       localhost:6379"
    echo "  Neo4j:       http://localhost:7474"
    echo "  Qdrant:      http://localhost:6333"
}

# ==================== 显示命令提示 ====================
show_commands() {
    print_section "管理命令"
    
    echo "  查看日志:"
    echo "    docker logs -f patent-drafting-api"
    echo ""
    echo "  重启服务:"
    echo "    cd ${PROJECT_ROOT}"
    echo "    docker compose -f docker-compose.patent-drafting.yml --profile ${ENVIRONMENT} restart"
    echo ""
    echo "  停止服务:"
    echo "    cd ${PROJECT_ROOT}"
    echo "    docker compose -f docker-compose.patent-drafting.yml --profile ${ENVIRONMENT} down"
    echo ""
    echo "  查看详细状态:"
    echo "    bash scripts/status_patent_drafting.sh ${ENVIRONMENT} --verbose"
}

# ==================== 主流程 ====================
main() {
    print_header
    
    check_containers
    check_health
    check_resources
    check_logs
    check_ports
    check_databases
    check_monitoring
    show_endpoints
    show_commands
    
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# ==================== 执行 ====================
main "$@"
