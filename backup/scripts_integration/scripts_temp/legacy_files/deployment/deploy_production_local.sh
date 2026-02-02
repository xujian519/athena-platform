#!/bin/bash
# 生产环境本地部署脚本（不依赖远程Git）
# Local Production Deployment Script (No Remote Git Dependency)

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
PROJECT_ROOT="/Users/xujian/Athena工作平台"
DEPLOYMENT_LOG="${PROJECT_ROOT}/logs/deployment_$(date +%Y%m%d_%H%M%S).log"
ENVIRONMENT="production"
DOMAIN="athena.multimodal.ai"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1" >> "$DEPLOYMENT_LOG"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [SUCCESS] $1" >> "$DEPLOYMENT_LOG"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [WARNING] $1" >> "$DEPLOYMENT_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" >> "$DEPLOYMENT_LOG"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [STEP] $1" >> "$DEPLOYMENT_LOG"
}

# 显示部署横幅
show_banner() {
    echo -e "${CYAN}"
    echo "========================================================"
    echo "    🚀 Athena多模态文件系统生产环境部署"
    echo "========================================================"
    echo -e "${NC}"
    echo -e "${BLUE}部署信息:${NC}"
    echo -e "  📅 开始时间: $(date)"
    echo -e "  🌍 环境: ${YELLOW}${ENVIRONMENT}${NC}"
    echo -e "  🌐 域名: ${YELLOW}${DOMAIN}${NC}"
    echo -e "  📋 日志文件: ${YELLOW}${DEPLOYMENT_LOG}${NC}"
    echo ""
}

# 部署前检查
pre_deploy_check() {
    log_step "执行部署前检查..."

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        return 1
    fi

    # 检查Docker运行状态
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker守护进程未运行，请启动Docker"
        return 1
    fi

    log_success "Docker环境检查通过"
    return 0
}

# 创建必要目录
create_directories() {
    log_step "创建部署目录..."

    # 创建日志目录
    mkdir -p "${PROJECT_ROOT}/logs/{deployment,monitoring,backup}"

    # 创建数据目录（使用用户目录）
    mkdir -p "${PROJECT_ROOT}/data/athena/{multimodal,backups,ssl,monitoring}"
    mkdir -p "${PROJECT_ROOT}/data/athena/multimodal/{uploads,processed,cache}"
    mkdir -p "${PROJECT_ROOT}/data/athena/backups/{postgres,redis,config}"

    log_success "目录创建完成"
}

# 配置SSL证书
setup_ssl() {
    log_step "配置SSL证书..."

    if [ ! -f "/etc/ssl/certs/${DOMAIN}.crt" ]; then
        log_info "SSL证书不存在，开始生成..."
        if [ -f "${PROJECT_ROOT}/scripts/setup_ssl.sh" ]; then
            echo "1" | bash "${PROJECT_ROOT}/scripts/setup_ssl.sh"
        else
            log_error "SSL设置脚本不存在"
            return 1
        fi
    else
        log_info "SSL证书已存在，跳过生成"
    fi

    log_success "SSL配置完成"
}

# 部署数据库
setup_database() {
    log_step "配置数据库和缓存..."

    if [ -f "${PROJECT_ROOT}/scripts/setup_database.sh" ]; then
        bash "${PROJECT_ROOT}/scripts/setup_database.sh"
    else
        log_error "数据库配置脚本不存在"
        return 1
    fi

    log_success "数据库配置完成"
}

# 构建Docker镜像
build_images() {
    log_step "构建Docker镜像..."

    if [ -f "${PROJECT_ROOT}/scripts/build_docker_images.sh" ]; then
        bash "${PROJECT_ROOT}/scripts/build_docker_images.sh" --cleanup
    else
        log_error "Docker镜像构建脚本不存在"
        return 1
    fi

    log_success "Docker镜像构建完成"
}

# 部署应用
deploy_application() {
    log_step "部署应用服务..."

    cd "${PROJECT_ROOT}/docker"

    # 停止现有服务
    log_info "停止现有服务..."
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true

    # 创建.env.prod文件
    if [ ! -f ".env.prod" ]; then
        log_info "创建环境变量文件..."
        cat > .env.prod << 'EOF'
# Athena多模态文件系统生产环境配置
ENVIRONMENT=production
VERSION=2.0.0-prod
DOMAIN=athena.multimodal.ai

# 数据库配置
DB_PASSWORD=athena_prod_password_2024
POSTGRES_DB=athena_production
POSTGRES_USER=athena_user

# Redis配置
REDIS_PASSWORD=athena_prod_password_2024

# JWT配置
JWT_SECRET=athena_jwt_secret_2024_very_long_secure_key_for_production

# Grafana配置
GRAFANA_PASSWORD=athena_grafana_2024

# 其他配置
API_RATE_LIMIT=1000
LOG_LEVEL=INFO
DEBUG=false
EOF
        log_success "环境变量文件创建完成"
    fi

    # 部署数据库服务
    log_info "部署数据库服务..."
    if [ -f "docker-compose.database.yml" ]; then
        docker-compose -f docker-compose.database.yml up -d
    else
        log_warning "数据库Docker Compose文件不存在，跳过数据库部署"
    fi

    # 等待数据库就绪
    log_info "等待服务启动..."
    sleep 30

    # 部署应用服务
    log_info "部署应用服务..."
    docker-compose -f docker-compose.prod.yml up -d

    # 等待服务启动
    log_info "等待服务启动..."
    sleep 60

    log_success "应用部署完成"
}

# 执行健康检查
health_check() {
    log_step "执行健康检查..."

    local max_attempts=30
    local attempt=0
    local services_up=true

    while [ $attempt -lt $max_attempts ]; do
        attempt=$((attempt + 1))
        log_info "健康检查尝试 $attempt/$max_attempts"

        # 检查核心服务
        services=("8020" "9001" "9000" "9090")
        services_up=true

        for port in "${services[@]}"; do
            if ! curl -f "http://localhost:$port/health" >/dev/null 2>&1; then
                log_warning "端口 $port 服务未就绪"
                services_up=false
            fi
        done

        if [ "$services_up" = true ]; then
            log_success "所有核心服务健康检查通过"
            break
        else
            log_warning "部分服务未就绪，等待10秒后重试..."
            sleep 10
        fi
    done

    if [ $attempt -eq $max_attempts ]; then
        log_error "健康检查超时，服务可能未正常启动"
        return 1
    fi

    return 0
}

# 运行烟雾测试
smoke_test() {
    log_step "运行烟雾测试..."

    # 测试API网关
    if curl -f "http://localhost:8020/health" >/dev/null 2>&1; then
        log_success "API网关测试通过"
    else
        log_error "API网关测试失败"
        return 1
    fi

    # 测试小诺控制中心
    if curl -f "http://localhost:9001/health" >/dev/null 2>&1; then
        log_success "小诺控制中心测试通过"
    else
        log_error "小诺控制中心测试失败"
        return 1
    fi

    # 测试Athena平台管理
    if curl -f "http://localhost:9000/health" >/dev/null 2>&1; then
        log_success "Athena平台管理测试通过"
    else
        log_error "Athena平台管理测试失败"
        return 1
    fi

    # 测试平台监控
    if curl -f "http://localhost:9090/health" >/dev/null 2>&1; then
        log_success "平台监控测试通过"
    else
        log_error "平台监控测试失败"
        return 1
    fi

    log_success "烟雾测试通过"
    return 0
}

# 部署后验证
post_deploy_verification() {
    log_step "执行部署后验证..."

    # 检查容器状态
    log_info "检查容器状态..."
    cd "${PROJECT_ROOT}/docker"
    docker-compose -f docker-compose.prod.yml ps

    # 检查资源使用
    log_info "检查资源使用..."
    docker stats --no-stream

    log_success "部署后验证完成"
}

# 显示部署结果
show_deployment_results() {
    echo ""
    echo -e "${GREEN}🎉 部署完成！${NC}"
    echo ""
    echo -e "${CYAN}📋 访问地址:${NC}"
    echo -e "  🌐 主站: ${YELLOW}http://localhost:8020${NC}"
    echo -e "  📚 API文档: ${YELLOW}http://localhost:8020/docs${NC}"
    echo -e "  🤖 小诺控制: ${YELLOW}http://localhost:9001${NC}"
    echo -e "  🛡️ 平台管理: ${YELLOW}http://localhost:9000${NC}"
    echo -e "  📊 监控面板: ${YELLOW}http://localhost:3000${NC}"
    echo ""
    echo -e "${CYAN}📋 容器状态:${NC}"
    cd "${PROJECT_ROOT}/docker" && docker-compose -f docker-compose.prod.yml ps
    echo ""
    echo -e "${CYAN}📋 部署日志:${NC}"
    echo -e "  📄 详细日志: ${YELLOW}${DEPLOYMENT_LOG}${NC}"
    echo ""
    echo -e "${YELLOW}📌 下一步操作:${NC}"
    echo -e "  1. 访问系统并测试功能"
    echo -e "  2. 配置Grafana监控仪表板"
    echo -e "  3. 设置监控告警通知"
    echo -e "  4. 配置域名解析（生产环境）"
    echo -e "  5. 设置防火墙规则"
    echo ""
}

# 主函数
main() {
    # 记录开始时间
    SECONDS=0

    show_banner

    # 执行部署步骤
    if ! pre_deploy_check; then
        log_error "部署前检查失败，部署终止"
        exit 1
    fi

    create_directories
    setup_ssl
    setup_database
    build_images
    deploy_application

    # 验证部署
    if ! health_check; then
        log_error "健康检查失败，部署终止"
        exit 1
    fi

    if ! smoke_test; then
        log_error "烟雾测试失败，部署终止"
        exit 1
    fi

    post_deploy_verification
    show_deployment_results

    log_success "生产环境部署成功完成！"
}

# 错误处理
trap 'log_error "部署过程中发生错误，请检查日志: $DEPLOYMENT_LOG"; exit 1' ERR

# 执行主函数
main "$@"