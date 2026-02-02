#!/bin/bash
# Docker容器化部署脚本
# Docker Containerized Deployment for Athena Production

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
PROJECT_NAME="athena-prod"
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.prod"
VERSION="2.0-prod"
REGISTRY="registry.cn-hangzhou.aliyuncs.com/athena"

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

# 检查依赖
check_dependencies() {
    log_info "检查Docker环境..."

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi

    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi

    # 检查Docker守护进程
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker守护进程未运行，请启动Docker"
        exit 1
    fi

    log_success "Docker环境检查完成"
}

# 创建环境变量文件
create_env_file() {
    log_info "创建环境变量文件..."

    if [ -f "$ENV_FILE" ]; then
        log_warning "环境变量文件已存在，跳过创建"
        return 0
    fi

    cat > "$ENV_FILE" << EOF
# Athena多模态文件系统生产环境配置
# Environment Variables for Athena Production

# 基础配置
COMPOSE_PROJECT_NAME=${PROJECT_NAME}
VERSION=${VERSION}
REGISTRY=${REGISTRY}

# 数据库配置
DB_PASSWORD=$(openssl rand -base64 32)
REPLICATION_PASSWORD=$(openssl rand -base64 32)
POSTGRES_DB=athena_production
POSTGRES_USER=athena_user

# Redis配置
REDIS_PASSWORD=${DB_PASSWORD}

# JWT配置
JWT_SECRET=$(openssl rand -base64 64)

# Grafana配置
GRAFANA_PASSWORD=$(openssl rand -base64 16)

# SSL证书路径
SSL_CERT_PATH=/etc/ssl/certs/athena.multimodal.ai.crt
SSL_KEY_PATH=/etc/ssl/private/athena.multimodal.ai.key

# API配置
API_RATE_LIMIT=1000
API_MAX_FILE_SIZE=200MB

# 监控配置
ALERT_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# 域名配置
DOMAIN=athena.multimodal.ai
API_DOMAIN=api.athena.multimodal.ai
ADMIN_DOMAIN=admin.athena.multimodal.ai

# 时区配置
TZ=Asia/Shanghai

# 日志级别
LOG_LEVEL=INFO

# 调试模式
DEBUG=false

# 性能配置
MAX_WORKERS=4
WORKER_TIMEOUT=60
KEEP_ALIVE=2

# 缓存配置
CACHE_TTL=3600
CACHE_MAX_SIZE=1000

# 文件存储配置
UPLOAD_PATH=/data/athena/multimodal/uploads
PROCESSED_PATH=/data/athena/multimodal/processed
BACKUP_PATH=/data/athena/backups

# 数据库连接池配置
DB_POOL_MIN=10
DB_POOL_MAX=100
DB_POOL_IDLE_TIMEOUT=300

# Redis连接池配置
REDIS_POOL_MIN=5
REDIS_POOL_MAX=50

# AI模型配置
GLM_MODEL_NAME=glm-4v-plus
GLM_MAX_CONCURRENT=10

# 向量数据库配置
VECTOR_DIM=768
VECTOR_INDEX_TYPE=ivfflat

# 备份配置
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=30
BACKUP_SCHEDULE=0 2 * * *

# 安全配置
CORS_ORIGINS=https://athena.multimodal.ai,https://api.athena.multimodal.ai,https://admin.athena.multimodal.ai
SSL_VERIFY=true

# 健康检查配置
HEALTH_CHECK_INTERVAL=30
HEALTH_CHECK_TIMEOUT=10
HEALTH_CHECK_RETRIES=3

# 限流配置
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=10000
RATE_LIMIT_BURST_SIZE=500

# 追踪配置
TRACING_ENABLED=true
JAEGER_ENDPOINT=http://jaeger:14268/api/traces
TRACE_SAMPLING_RATE=0.1

# 指标配置
METRICS_ENABLED=true
METRICS_PORT=9090
METRICS_PATH=/metrics

# 邮件配置（用于告警）
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=alerts@athena.multimodal.ai
SMTP_PASSWORD=your_smtp_password
SMTP_TLS=true

# 钉钉配置（用于告警）
DINGTALK_WEBHOOK_URL=
DINGTALK_SECRET=

# 加密配置
ENCRYPTION_KEY=$(openssl rand -hex 32)
ENCRYPTION_IV=$(openssl rand -hex 16)
EOF

    chmod 600 "$ENV_FILE"
    log_success "环境变量文件创建完成: $ENV_FILE"
    log_warning "请检查并修改 $ENV_FILE 中的配置"
}

# 创建网络
create_networks() {
    log_info "创建Docker网络..."

    # 创建应用网络
    docker network create athena-network \\
        --driver bridge \\
        --subnet=172.20.0.0/16 \\
        --gateway=172.20.0.1 \\
        --label "com.athena.network=athena-network" \\
        2>/dev/null || log_info "athena-network 已存在"

    # 创建监控网络
    docker network create athena-monitoring \\
        --driver bridge \\
        --subnet=172.21.0.0/16 \\
        --gateway=172.21.0.1 \\
        --label "com.athena.network=athena-monitoring" \\
        2>/dev/null || log_info "athena-monitoring 已存在"

    # 创建前端网络
    docker network create athena-frontend \\
        --driver bridge \\
        --subnet=172.22.0.0/16 \\
        --gateway=172.22.0.1 \\
        --label "com.athena.network=athena-frontend" \\
        2>/dev/null || log_info "athena-frontend 已存在"

    log_success "Docker网络创建完成"
}

# 创建存储卷
create_volumes() {
    log_info "创建Docker存储卷..."

    # 创建数据存储卷
    volumes=(
        "athena-data"
        "athena-uploads"
        "athena-processed"
        "athena-cache"
        "athena-backups"
        "athena-logs"
        "athena-ssl"
    )

    for volume in "${volumes[@]}"; do
        docker volume create "$volume" \\
            --label "com.athena.volume=true" \\
            --label "com.athena.project=$PROJECT_NAME" \\
            2>/dev/null || log_info "存储卷 $volume 已存在"
    done

    log_success "Docker存储卷创建完成"
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."

    # 启动数据库服务
    cd docker
    docker-compose -f docker-compose.database.yml up -d

    # 等待数据库就绪
    log_info "等待数据库服务就绪..."
    sleep 30

    # 检查数据库连接
    if docker exec athena-postgres-primary pg_isready -U athena_user -d athena_production; then
        log_success "数据库初始化完成"
    else
        log_error "数据库初始化失败"
        return 1
    fi
}

# 部署应用
deploy_application() {
    log_info "部署Athena应用..."

    cd docker

    # 拉取最新镜像
    log_info "拉取Docker镜像..."
    docker-compose -f "$COMPOSE_FILE" pull

    # 启动服务
    log_info "启动应用服务..."
    docker-compose -f "$COMPOSE_FILE" up -d

    # 等待服务启动
    log_info "等待服务启动..."
    sleep 60

    # 检查服务状态
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        log_success "应用部署完成"
    else
        log_error "应用部署失败"
        return 1
    fi
}

# 健康检查
health_check() {
    log_info "执行健康检查..."

    services=(
        "nginx-lb:80"
        "api-gateway-1:8020"
        "api-gateway-2:8020"
        "api-gateway-3:8020"
        "dolphin-parser-1:8013"
        "glm-vision-1:8091"
        "multimodal-processor-1:8012"
        "xiao-nuo-control:9001"
        "athena-platform:9000"
        "platform-monitor:9090"
    )

    failed_services=()

    for service_info in "${services[@]}"; do
        service=$(echo $service_info | cut -d':' -f1)
        port=$(echo $service_info | cut -d':' -f2)
        container="athena-$service"

        # 检查容器状态
        if ! docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$container.*Up"; then
            log_error "容器 $container 未运行"
            failed_services+=("$service")
            continue
        fi

        # 检查端口连通性
        if ! docker exec "$container" curl -f "http://localhost:$port/health" >/dev/null 2>&1; then
            log_warning "服务 $service 健康检查失败"
            failed_services+=("$service")
        else
            log_success "服务 $service 健康检查通过"
        fi
    done

    if [ ${#failed_services[@]} -gt 0 ]; then
        log_error "以下服务健康检查失败: ${failed_services[*]}"
        return 1
    fi

    log_success "所有服务健康检查通过"
}

# 配置SSL证书
setup_ssl() {
    log_info "配置SSL证书..."

    # 创建SSL目录
    sudo mkdir -p /etc/ssl/certs /etc/ssl/private

    # 如果证书不存在，生成自签名证书
    if [ ! -f "/etc/ssl/certs/athena.multimodal.ai.crt" ]; then
        log_info "生成自签名SSL证书..."
        ./scripts/setup_ssl.sh <<< "1"
    fi

    log_success "SSL证书配置完成"
}

# 配置日志轮转
setup_log_rotation() {
    log_info "配置日志轮转..."

    sudo tee /etc/logrotate.d/athena-docker >/dev/null << 'EOF'
/var/lib/docker/containers/*/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        docker ps -q | xargs -r docker kill -s USR1
    endscript
}

/var/log/athena/*/*.log {
    daily
    missingok
    rotate 90
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF

    log_success "日志轮转配置完成"
}

# 创建管理脚本
create_management_scripts() {
    log_info "创建Docker管理脚本..."

    # 启动脚本
    cat > "/Users/xujian/Athena工作平台/scripts/start_athena.sh" << 'EOF'
#!/bin/bash
# 启动Athena服务

echo "启动Athena多模态文件系统..."

cd /Users/xujian/Athena工作平台/docker
docker-compose -f docker-compose.prod.yml up -d

echo "等待服务启动..."
sleep 30

echo "检查服务状态..."
docker-compose -f docker-compose.prod.yml ps

echo "Athena服务启动完成"
EOF

    # 停止脚本
    cat > "/Users/xujian/Athena工作平台/scripts/stop_athena.sh" << 'EOF'
#!/bin/bash
# 停止Athena服务

echo "停止Athena多模态文件系统..."

cd /Users/xujian/Athena工作平台/docker
docker-compose -f docker-compose.prod.yml down

echo "Athena服务已停止"
EOF

    # 重启脚本
    cat > "/Users/xujian/Athena工作平台/scripts/restart_athena.sh" << 'EOF'
#!/bin/bash
# 重启Athena服务

echo "重启Athena多模态文件系统..."

/Users/xujian/Athena工作平台/scripts/stop_athena.sh
sleep 10
/Users/xujian/Athena工作平台/scripts/start_athena.sh

echo "Athena服务重启完成"
EOF

    # 状态检查脚本
    cat > "/Users/xujian/Athena工作平台/scripts/status_athena.sh" << 'EOF'
#!/bin/bash
# 检查Athena服务状态

echo "============================================"
echo "     Athena多模态文件系统状态检查"
echo "     时间: $(date)"
echo "============================================"
echo ""

cd /Users/xujian/Athena工作平台/docker

echo "1. Docker容器状态:"
docker-compose -f docker-compose.prod.yml ps
echo ""

echo "2. 容器资源使用:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
echo ""

echo "3. 容器日志摘要:"
docker-compose -f docker-compose.prod.yml logs --tail=5
echo ""

echo "4. 磁盘使用情况:"
df -h | grep -E "/data/athena|/var/lib/docker"
echo ""

echo "============================================"
echo "状态检查完成"
echo "============================================"
EOF

    # 更新脚本
    cat > "/Users/xujian/Athena工作平台/scripts/update_athena.sh" << 'EOF'
#!/bin/bash
# 更新Athena服务

echo "更新Athena多模态文件系统..."

cd /Users/xujian/Athena工作平台/docker

# 拉取最新镜像
echo "拉取最新镜像..."
docker-compose -f docker-compose.prod.yml pull

# 重启服务
echo "重启服务..."
docker-compose -f docker-compose.prod.yml up -d

echo "等待服务启动..."
sleep 30

echo "检查服务状态..."
docker-compose -f docker-compose.prod.yml ps

echo "Athena服务更新完成"
EOF

    chmod +x /Users/xujian/Athena工作平台/scripts/*.sh

    log_success "管理脚本创建完成"
}

# 清理旧资源
cleanup_old_resources() {
    log_info "清理旧资源..."

    # 清理停止的容器
    docker container prune -f

    # 清理未使用的镜像
    docker image prune -f

    # 清理未使用的网络
    docker network prune -f

    # 清理未使用的卷
    docker volume prune -f

    log_success "资源清理完成"
}

# 主函数
main() {
    echo -e "${BLUE}🐳 Athena多模态文件系统Docker容器化部署${NC}"
    echo "============================================"
    echo -e "${CYAN}开始时间: $(date)${NC}"
    echo ""

    # 解析命令行参数
    SKIP_INIT=false
    SKIP_DEPLOY=false
    CLEANUP=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-init)
                SKIP_INIT=true
                shift
                ;;
            --skip-deploy)
                SKIP_DEPLOY=true
                shift
                ;;
            --cleanup)
                CLEANUP=true
                shift
                ;;
            *)
                echo "未知参数: $1"
                echo "用法: $0 [--skip-init] [--skip-deploy] [--cleanup]"
                exit 1
                ;;
        esac
    done

    echo -e "${BLUE}部署配置:${NC}"
    echo -e "  📦 项目名称: ${YELLOW}$PROJECT_NAME${NC}"
    echo -e "  📄 Compose文件: ${YELLOW}$COMPOSE_FILE${NC}"
    echo -e "  🔧 环境文件: ${YELLOW}$ENV_FILE${NC}"
    echo -e "  🏷️  版本: ${YELLOW}$VERSION${NC}"
    echo ""

    # 检查依赖
    check_dependencies

    # 创建环境文件
    create_env_file

    # 创建网络和卷
    create_networks
    create_volumes

    # 初始化数据库
    if [ "$SKIP_INIT" = false ]; then
        if init_database; then
            log_success "数据库初始化完成"
        else
            log_error "数据库初始化失败"
            exit 1
        fi
    else
        log_info "跳过数据库初始化"
    fi

    # 配置SSL
    setup_ssl

    # 部署应用
    if [ "$SKIP_DEPLOY" = false ]; then
        if deploy_application; then
            log_success "应用部署完成"
        else
            log_error "应用部署失败"
            exit 1
        fi
    else
        log_info "跳过应用部署"
    fi

    # 健康检查
    if health_check; then
        log_success "健康检查通过"
    else
        log_error "健康检查失败"
        exit 1
    fi

    # 配置日志轮转
    setup_log_rotation

    # 创建管理脚本
    create_management_scripts

    # 清理旧资源
    if [ "$CLEANUP" = true ]; then
        cleanup_old_resources
    fi

    echo ""
    echo -e "${GREEN}✅ Docker容器化部署完成！${NC}"
    echo ""
    echo -e "${BLUE}📋 服务访问地址:${NC}"
    echo -e "  🌐 主站: ${YELLOW}http://localhost${NC}"
    echo -e "  📡 API文档: ${YELLOW}http://localhost/docs${NC}"
    echo -e "  🤖 小诺控制: ${YELLOW}http://localhost:9001${NC}"
    echo -e "  🛡️ 平台管理: ${YELLOW}http://localhost:9000${NC}"
    echo -e "  📊 监控面板: ${YELLOW}http://localhost:3000${NC}"
    echo -e "  📈 指标端点: ${YELLOW}http://localhost:9090${NC}"
    echo ""
    echo -e "${BLUE}🔧 管理命令:${NC}"
    echo -e "  🚀 启动服务: ${YELLOW}/Users/xujian/Athena工作平台/scripts/start_athena.sh${NC}"
    echo -e "  🛑 停止服务: ${YELLOW}/Users/xujian/Athena工作平台/scripts/stop_athena.sh${NC}"
    echo -e "  🔄 重启服务: ${YELLOW}/Users/xujian/Athena工作平台/scripts/restart_athena.sh${NC}"
    echo -e "  📊 状态检查: ${YELLOW}/Users/xujian/Athena工作平台/scripts/status_athena.sh${NC}"
    echo -e "  ⬆️ 更新服务: ${YELLOW}/Users/xujian/Athena工作平台/scripts/update_athena.sh${NC}"
    echo ""
    echo -e "${PURPLE}✨ Docker容器化部署成功！${NC}"
}

# 执行主函数
main "$@"