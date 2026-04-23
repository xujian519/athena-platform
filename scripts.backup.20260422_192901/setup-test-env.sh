#!/bin/bash
# Athena 测试环境设置脚本
# Test Environment Setup Script

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# 检查Docker是否安装
check_docker() {
    print_header "检查Docker环境"

    if ! command -v docker &> /dev/null; then
        print_error "Docker未安装，请先安装Docker"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi

    print_success "Docker环境检查通过"

    # 检查Docker是否运行
    if ! docker info &> /dev/null; then
        print_error "Docker守护进程未运行，请启动Docker"
        exit 1
    fi

    print_success "Docker守护进程运行中"
}

# 创建必要的目录
create_directories() {
    print_header "创建必要的目录"

    directories=(
        "data/postgres/test"
        "data/redis/test"
        "data/qdrant/test"
        "data/neo4j/test"
        "data/minio/test"
        "logs/test"
        "prometheus"
        "grafana/provisioning"
        "grafana/dashboards"
    )

    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_success "创建目录: $dir"
        else
            print_info "目录已存在: $dir"
        fi
    done

    # 设置权限
    chmod -R 755 data/test 2>/dev/null || true
    chmod -R 755 logs/test 2>/dev/null || true
}

# 创建Prometheus配置
create_prometheus_config() {
    print_header "创建Prometheus配置"

    cat > prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9091']

  - job_name: 'athena-api'
    static_configs:
      - targets: ['host.docker.internal:8000']
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-test:5432']
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-test:6379']
    scrape_interval: 30s

  - job_name: 'qdrant'
    static_configs:
      - targets: ['qdrant-test:6333']
    scrape_interval: 30s

  - job_name: 'neo4j'
    static_configs:
      - targets: ['neo4j-test:7474']
    scrape_interval: 30s
EOF

    print_success "Prometheus配置创建完成"
}

# 创建Grafana配置
create_grafana_config() {
    print_header "创建Grafana配置"

    # 数据源配置
    mkdir -p grafana/provisioning/datasources
    cat > grafana/provisioning/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus-test:9090
    isDefault: true
    editable: true
EOF

    # 仪表板配置
    mkdir -p grafana/provisioning/dashboards
    cat > grafana/provisioning/dashboards/default.yml << 'EOF'
apiVersion: 1

providers:
  - name: 'Default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF

    print_success "Grafana配置创建完成"
}

# 启动测试服务
start_services() {
    print_header "启动测试服务"

    print_info "启动核心测试服务..."
    docker-compose -f docker-compose.unified.yml --profile test up -d postgres-test redis-test qdrant-test neo4j-test minio-test

    print_success "测试服务已启动"
}

# 等待服务就绪
wait_for_services() {
    print_header "等待服务就绪"

    print_info "等待PostgreSQL启动..."
    for i in {1..30}; do
        if docker exec athena_postgres_test pg_isready -U athena_test -d athena_test_db &> /dev/null; then
            print_success "PostgreSQL已就绪"
            break
        fi
        sleep 2
    done

    print_info "等待Redis启动..."
    for i in {1..15}; do
        if docker exec athena_redis_test redis-cli ping &> /dev/null; then
            print_success "Redis已就绪"
            break
        fi
        sleep 2
    done

    print_info "等待Qdrant启动..."
    for i in {1..15}; do
        if curl -s http://localhost:6334/health &> /dev/null; then
            print_success "Qdrant已就绪"
            break
        fi
        sleep 2
    done

    print_info "等待Neo4j启动..."
    for i in {1..30}; do
        if curl -s http://localhost:7475 &> /dev/null; then
            print_success "Neo4j已就绪"
            break
        fi
        sleep 2
    done
}

# 显示服务信息
show_service_info() {
    print_header "测试服务信息"

    echo ""
    echo -e "${GREEN}服务连接信息:${NC}"
    echo ""
    echo -e "${BLUE}PostgreSQL:${NC}"
    echo "  Host: localhost"
    echo "  Port: 5433"
    echo "  User: athena_test"
    echo "  Password: athena_test_password_2024"
    echo "  Database: athena_test_db"
    echo ""
    echo -e "${BLUE}Redis:${NC}"
    echo "  Host: localhost"
    echo "  Port: 6380"
    echo ""
    echo -e "${BLUE}Qdrant:${NC}"
    echo "  URL: http://localhost:6334"
    echo "  Dashboard: http://localhost:6334/dashboard"
    echo ""
    echo -e "${BLUE}Neo4j:${NC}"
    echo "  HTTP: http://localhost:7475"
    echo "  Bolt: bolt://localhost:7688"
    echo "  User: neo4j"
    echo "  Password: athena_test_2024"
    echo ""
    echo -e "${BLUE}MinIO:${NC}"
    echo "  Endpoint: http://localhost:9001"
    echo "  Console: http://localhost:9002"
    echo "  Access Key: minioadmin"
    echo "  Secret Key: minioadmin123"
    echo ""
}

# 显示管理命令
show_management_commands() {
    print_header "常用管理命令"

    echo ""
    echo -e "${GREEN}服务管理:${NC}"
    echo "  启动服务:     docker-compose -f docker-compose.unified.yml --profile test up -d"
    echo "  停止服务:     docker-compose -f docker-compose.unified.yml --profile test down"
    echo "  重启服务:     docker-compose -f docker-compose.test.yml restart"
    echo "  查看状态:     docker-compose -f docker-compose.test.yml ps"
    echo "  查看日志:     docker-compose -f docker-compose.test.yml logs -f [service_name]"
    echo ""
    echo -e "${GREEN}数据管理:${NC}"
    echo "  清理数据:     docker-compose -f docker-compose.unified.yml --profile test down -v"
    echo "  备份数据:     ./scripts/backup-test-data.sh"
    echo "  恢复数据:     ./scripts/restore-test-data.sh"
    echo ""
    echo -e "${GREEN}测试命令:${NC}"
    echo "  运行所有测试: pytest tests/ -v"
    echo "  运行单元测试: pytest tests/unit/ -v"
    echo "  运行集成测试: pytest tests/integration/ -v"
    echo "  生成覆盖率报告: pytest --cov=core --cov-report=html"
    echo ""
}

# 主函数
main() {
    print_header "Athena 测试环境设置"
    echo ""
    echo "此脚本将:"
    echo "  1. 检查Docker环境"
    echo "  2. 创建必要的目录"
    echo "  3. 创建配置文件"
    echo "  4. 启动测试服务"
    echo "  5. 等待服务就绪"
    echo ""
    read -p "是否继续? (y/n) " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "操作已取消"
        exit 0
    fi

    # 执行设置步骤
    check_docker
    create_directories
    create_prometheus_config
    create_grafana_config
    start_services
    wait_for_services
    show_service_info
    show_management_commands

    print_header "设置完成!"
    print_success "测试环境已成功设置并启动"

    echo ""
    print_info "下一步:"
    echo "  1. 运行测试: pytest tests/ -v"
    echo "  2. 查看服务状态: docker-compose -f docker-compose.test.yml ps"
    echo "  3. 查看服务日志: docker-compose -f docker-compose.test.yml logs -f"
    echo ""
}

# 执行主函数
main "$@"
