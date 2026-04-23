#!/usr/bin/env bash
# Athena工作平台 - 统一部署脚本
# Athena Platform - Unified Deployment Script
#
# 使用方法:
#   ./scripts/deploy-all.sh [command]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装"
        exit 1
    fi
    if ! docker compose version &> /dev/null && ! docker-compose version &> /dev/null; then
        log_error "Docker Compose未安装"
        exit 1
    fi
    log_success "Docker环境检查通过"
}

# 检查环境变量
check_env() {
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_info "已创建.env文件"
        fi
    fi
}

# 启动服务
start_services() {
    log_info "启动Athena平台基础设施..."
    check_docker
    check_env

    mkdir -p data/{redis,qdrant,neo4j,prometheus,grafana} logs

    docker compose up -d

    log_success "服务启动完成！"
    echo ""
    log_info "服务访问地址:"
    echo "  - Prometheus: http://localhost:9090"
    echo "  - Grafana:     http://localhost:3000 (admin/admin123)"
    echo "  - Redis:       localhost:6379"
    echo "  - Qdrant:      http://localhost:6333"
    echo "  - Neo4j:       http://localhost:7474"
}

# 停止服务
stop_services() {
    log_info "停止服务..."
    docker compose down
    log_success "服务已停止"
}

# 重启服务
restart_services() {
    stop_services
    sleep 2
    start_services
}

# 查看状态
show_status() {
    log_info "服务状态:"
    docker compose ps
}

# 查看日志
show_logs() {
    docker compose logs -f "${1:-}"
}

# 清理
clean_all() {
    log_warning "⚠️  这将删除所有容器和数据！"
    read -p "确定继续? (yes/no): " confirm
    [ "$confirm" = "yes" ] && docker compose down -v --remove-orphans
}

# 帮助
show_help() {
    cat << HELP
Athena工作平台 - 统一部署脚本

使用: $0 [command]

命令:
  start   - 启动所有基础设施
  stop    - 停止所有服务
  restart - 重启服务
  status  - 查看状态
  logs    - 查看日志 [service]
  clean   - 清理所有数据
  help    - 显示帮助

服务端口:
  Prometheus: 9090
  Grafana:     3000
  Redis:       6379
  Qdrant:      6333/6334
  Neo4j:       7474/7687

HELP
}

# 主函数
main() {
    case "${1:-help}" in
        start) start_services ;;
        stop) stop_services ;;
        restart) restart_services ;;
        status) show_status ;;
        logs) show_logs "$2" ;;
        clean) clean_all ;;
        help|--help|-h) show_help ;;
        *) log_error "未知命令: $1"; show_help; exit 1 ;;
    esac
}

main "$@"
