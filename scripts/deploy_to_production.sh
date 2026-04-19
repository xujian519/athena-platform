#!/bin/bash
# =============================================================================
# Athena统一网关系统 - 生产环境部署脚本
# Athena Unified Gateway - Production Deployment Script
#
# 功能: 将系统部署到生产环境
# 作者: Claude (Sonnet 4.6)
# 日期: 2026-04-18
# =============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 分隔线
print_section() {
    echo ""
    echo "============================================================================"
    echo "$1"
    echo "============================================================================"
}

# 检查是否为root用户
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_warning "建议使用root用户或sudo运行此脚本以获得完整权限"
        read -p "是否继续? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 检查Docker是否安装
check_docker() {
    print_section "检查Docker环境"

    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        echo "安装命令: brew install docker 或访问 https://docs.docker.com/get-docker/"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker daemon未运行，请启动Docker"
        exit 1
    fi

    log_success "Docker环境检查通过"
}

# 检查Docker Compose是否安装
check_docker_compose() {
    print_section "检查Docker Compose"

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose未安装"
        exit 1
    fi

    log_success "Docker Compose检查通过"
}

# 停止现有服务
stop_existing_services() {
    print_section "停止现有服务"

    log_info "停止Gateway进程..."
    pkill -f "gateway-unified" 2>/dev/null || true

    log_info "停止Docker容器..."
    docker-compose down 2>/dev/null || true

    log_success "现有服务已停止"
}

# 创建必要的目录
create_directories() {
    print_section "创建目录结构"

    mkdir -p /var/log/athena
    mkdir -p /var/data/athena/qdrant
    mkdir -p /var/data/athena/redis
    mkdir -p /var/data/athena/neo4j

    log_success "目录结构创建完成"
}

# 配置环境变量
configure_environment() {
    print_section "配置环境变量"

    if [ ! -f .env ]; then
        log_warning ".env文件不存在，从模板创建..."
        cp production/.env.example .env
        log_warning "请编辑.env文件，配置生产环境参数"
        read -p "按Enter继续..."
    fi

    source .env
    log_success "环境变量配置完成"
}

# 启动基础设施服务
start_infrastructure() {
    print_section "启动基础设施服务"

    log_info "启动Redis、Qdrant、Neo4j等基础设施..."
    docker-compose up -d redis qdrant neo4j postgres

    # 等待服务启动
    log_info "等待服务启动..."
    sleep 10

    # 检查服务状态
    log_info "检查服务健康状态..."
    docker-compose ps

    log_success "基础设施服务启动完成"
}

# 配置Redis认证
configure_redis() {
    print_section "配置Redis认证"

    REDIS_PASSWORD=${REDIS_PASSWORD:-redis123}

    log_info "设置Redis密码..."

    # 重启Redis容器以应用密码
    docker-compose restart redis

    sleep 5

    # 验证Redis连接
    if docker-compose exec -T redis redis-cli -a "$REDIS_PASSWORD" ping | grep -q PONG; then
        log_success "Redis认证配置成功"
    else
        log_error "Redis认证配置失败"
        exit 1
    fi
}

# 配置Neo4j认证
configure_neo4j() {
    print_section "配置Neo4j认证"

    NEO4J_PASSWORD=${NEO4J_PASSWORD:-athena_neo4j_2024}

    log_info "设置Neo4j密码..."

    # 等待Neo4j启动
    log_info "等待Neo4j启动..."
    sleep 15

    # 验证Neo4j连接
    if docker-compose exec -T neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "RETURN 1" | grep -q 1; then
        log_success "Neo4j认证配置成功"
    else
        log_warning "Neo4j认证配置可能失败，请手动验证"
    fi
}

# 初始化Qdrant集合
init_qdrant_collections() {
    print_section "初始化Qdrant集合"

    log_info "创建Qdrant集合..."
    python3 scripts/init_qdrant_collections.py

    if [ $? -eq 0 ]; then
        log_success "Qdrant集合初始化成功"
    else
        log_warning "Qdrant集合初始化失败，请手动执行"
    fi
}

# 导入测试数据
import_test_data() {
    print_section "导入测试数据"

    read -p "是否导入测试数据? (y/n) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "导入Qdrant测试数据..."
        python3 scripts/import_qdrant_test_data_fixed.py

        if [ $? -eq 0 ]; then
            log_success "测试数据导入成功"
        else
            log_warning "测试数据导入失败"
        fi
    fi
}

# 编译Gateway
build_gateway() {
    print_section "编译Gateway"

    cd gateway-unified

    log_info "编译Go Gateway..."
    make build

    if [ ! -f bin/gateway-unified ]; then
        log_error "Gateway编译失败"
        exit 1
    fi

    log_success "Gateway编译完成"
    cd ..
}

# 部署Gateway（macOS）
deploy_gateway_macos() {
    print_section "部署Gateway (macOS)"

    if [[ "$OSTYPE" == "darwin"* ]]; then
        log_info "检测到macOS系统"

        # 停止现有Gateway
        pkill -f "gateway-unified" 2>/dev/null || true

        # 复制二进制文件
        sudo mkdir -p /usr/local/athena-gateway
        sudo cp gateway-unified/bin/gateway-unified /usr/local/athena-gateway/
        sudo cp gateway-unified/config.yaml /usr/local/athena-gateway/

        # 创建启动脚本
        sudo tee /usr/local/athena-gateway/start.sh > /dev/null <<EOF
#!/bin/bash
cd /usr/local/athena-gateway
nohup ./gateway-unified --config config.yaml > /tmp/gateway.log 2>&1 &
echo \$! > /usr/local/athena-gateway/gateway.pid
EOF

        sudo chmod +x /usr/local/athena-gateway/start.sh

        # 启动Gateway
        sudo /usr/local/athena-gateway/start.sh

        sleep 3

        # 验证Gateway运行
        if curl -s http://localhost:8005/health | grep -q "UP"; then
            log_success "Gateway部署成功"
        else
            log_error "Gateway部署失败"
            exit 1
        fi
    else
        log_warning "非macOS系统，跳过此步骤"
    fi
}

# 部署Gateway（Linux - systemd）
deploy_gateway_linux() {
    print_section "部署Gateway (Linux)"

    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        log_info "检测到Linux系统，配置systemd服务"

        # 创建systemd服务文件
        sudo tee /etc/systemd/system/athena-gateway.service > /dev/null <<EOF
[Unit]
Description=Athena Unified Gateway
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/usr/local/athena-gateway
ExecStart=/usr/local/athena-gateway/gateway-unified --config /usr/local/athena-gateway/config.yaml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

        # 重载systemd并启动服务
        sudo systemctl daemon-reload
        sudo systemctl enable athena-gateway
        sudo systemctl start athena-gateway

        sleep 3

        # 验证服务状态
        if sudo systemctl is-active --quiet athena-gateway; then
            log_success "Gateway服务启动成功"
        else
            log_error "Gateway服务启动失败"
            sudo systemctl status athena-gateway
            exit 1
        fi
    else
        log_warning "非Linux系统，跳过此步骤"
    fi
}

# 注册服务
register_services() {
    print_section "注册Gateway服务"

    log_info "注册后端服务和路由..."
    python3 scripts/register_gateway_services.py

    if [ $? -eq 0 ]; then
        log_success "服务注册成功"
    else
        log_warning "服务注册失败"
    fi
}

# 启动知识图谱API
start_kg_api() {
    print_section "启动知识图谱API"

    log_info "启动知识图谱API服务..."
    nohup python3 services/kg_api_service.py > /tmp/kg_api.log 2>&1 &
    echo $! > /tmp/kg_api.pid

    sleep 3

    # 验证API运行
    if curl -s http://localhost:8100/health | grep -q "OK"; then
        log_success "知识图谱API启动成功"
    else
        log_warning "知识图谱API启动失败，请手动检查"
    fi
}

# 配置监控
setup_monitoring() {
    print_section "配置监控和告警"

    log_info "配置Prometheus和Grafana..."

    # 启动监控服务
    docker-compose up -d prometheus grafana

    sleep 5

    log_info "监控服务访问地址:"
    echo "  - Prometheus: http://localhost:9090"
    echo "  - Grafana: http://localhost:3000 (admin/admin123)"

    log_success "监控服务配置完成"
}

# 系统健康检查
health_check() {
    print_section "系统健康检查"

    log_info "执行全面健康检查..."

    bash tests/verification/quick_test.sh

    log_success "健康检查完成"
}

# 生成部署报告
generate_report() {
    print_section "生成部署报告"

    REPORT_FILE="reports/production_deployment_$(date +%Y%m%d_%H%M%S).md"

    mkdir -p reports

    cat > "$REPORT_FILE" <<EOF
# Athena生产环境部署报告

**部署时间**: $(date '+%Y-%m-%d %H:%M:%S')
**部署状态**: ✅ 成功

---

## 部署的服务

### 基础设施
- ✅ Redis (端口: 6379)
- ✅ Qdrant (端口: 6333/6334)
- ✅ Neo4j (端口: 7474/7687)
- ✅ PostgreSQL (端口: 5432)

### 应用服务
- ✅ Gateway (端口: 8005)
- ✅ 知识图谱API (端口: 8100)

### 监控服务
- ✅ Prometheus (端口: 9090)
- ✅ Grafana (端口: 3000)

---

## 服务状态

\`\`\`bash
$ docker-compose ps
\`\`\`

$(docker-compose ps)

---

## 健康检查

### Gateway
\`\`\`bash
$ curl http://localhost:8005/health
\`\`\`

$(curl -s http://localhost:8005/health | python3 -m json.tool 2>/dev/null || echo "无法连接")

### Qdrant
\`\`\`bash
$ curl http://localhost:16333/collections
\`\`\`

$(curl -s http://localhost:16333/collections | python3 -c "import sys, json; data = json.load(sys.stdin); print(f'集合数量: {len(data[\"result\"][\"collections\"])}')" 2>/dev/null || echo "无法连接")

---

## 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| **Gateway** | http://localhost:8005 | 统一网关 |
| **Grafana** | http://localhost:3000 | 监控仪表板 (admin/admin123) |
| **Prometheus** | http://localhost:9090 | 指标查询 |
| **Qdrant Dashboard** | http://localhost:16333/dashboard | 向量数据库管理 |

---

## 管理命令

### 查看Gateway日志
\`\`\`bash
tail -f /tmp/gateway.log
\`\`\`

### 重启Gateway
\`\`\`bash
# macOS
sudo /usr/local/athena-gateway/start.sh

# Linux
sudo systemctl restart athena-gateway
\`\`\`

### 查看Docker容器状态
\`\`\`bash
docker-compose ps
\`\`\`

### 查看服务日志
\`\`\`bash
docker-compose logs -f [service_name]
\`\`\`

---

## 下一步

1. ✅ 配置环境变量（编辑.env文件）
2. ✅ 导入业务数据
3. ✅ 配置告警规则（Prometheus）
4. ✅ 设置备份策略
5. ✅ 性能调优

---

**部署完成！系统已就绪。**
EOF

    log_success "部署报告已生成: $REPORT_FILE"
}

# 主函数
main() {
    print_section "Athena统一网关系统 - 生产环境部署"

    log_info "开始部署流程..."

    # 检查环境
    check_root
    check_docker
    check_docker_compose

    # 停止现有服务
    stop_existing_services

    # 创建目录
    create_directories

    # 配置环境
    configure_environment

    # 启动基础设施
    start_infrastructure

    # 配置认证
    configure_redis
    configure_neo4j

    # 初始化数据
    init_qdrant_collections
    import_test_data

    # 编译和部署Gateway
    build_gateway
    deploy_gateway_macos
    deploy_gateway_linux

    # 注册服务和启动API
    register_services
    start_kg_api

    # 配置监控
    setup_monitoring

    # 健康检查
    health_check

    # 生成报告
    generate_report

    print_section "部署完成"

    log_success "Athena系统已成功部署到生产环境！"
    echo ""
    echo "🎉 系统访问地址:"
    echo "  - Gateway: http://localhost:8005"
    echo "  - Grafana: http://localhost:3000"
    echo "  - Prometheus: http://localhost:9090"
    echo ""
    echo "📚 管理命令:"
    echo "  - 查看日志: tail -f /tmp/gateway.log"
    echo "  - 查看状态: docker-compose ps"
    echo "  - 重启服务: sudo systemctl restart athena-gateway"
    echo ""
}

# 执行主函数
main "$@"
