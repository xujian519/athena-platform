#!/bin/bash
# 生产环境部署执行脚本
# Production Environment Deployment Execution Script

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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
    echo -e "${PURPLE}[STEP]${NC} $1"
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

    # 检查系统要求
    log_info "检查系统要求..."

    # 检查操作系统
    if [[ "$OSTYPE" == "darwin"* ]]; then
        log_info "macOS系统检测"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        log_info "Linux系统检测"
    else
        log_error "不支持的操作系统: $OSTYPE"
        return 1
    fi

    # 检查磁盘空间
    available_space=$(df -h "${PROJECT_ROOT}" | awk 'NR==2 {print $4}' | sed 's/[^0-9.]//g' | cut -d'.' -f1)
    if [ -z "$available_space" ] || [ "$available_space" -lt 10 ]; then
        log_error "磁盘空间不足，至少需要10GB可用空间"
        return 1
    fi

    # 检查内存
    if [[ "$OSTYPE" == "darwin"* ]]; then
        memory_gb=$(sysctl -n hw.memsize | awk '{print int($1/1024/1024/1024)}')
    else
        memory_gb=$(free -g | awk '/^Mem:/{print $2}')
    fi
    if [ "$memory_gb" -lt 8 ]; then
        log_warning "内存可能不足，建议至少8GB，当前${memory_gb}GB"
    fi

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

    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        return 1
    fi

    # 检查Git
    if ! command -v git &> /dev/null; then
        log_error "Git未安装，请先安装Git"
        return 1
    fi

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3未安装，请先安装Python3"
        return 1
    fi

    log_success "系统要求检查通过"
    return 0
}

# 检查代码状态
check_code_status() {
    log_step "检查代码状态..."

    cd "$PROJECT_ROOT"

    # 检查是否有未提交的更改
    if [ -n "$(git status --porcelain)" ]; then
        log_warning "检测到未提交的代码更改:"
        git status --porcelain
        read -p "是否继续部署? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "部署已取消"
            exit 0
        fi
    fi

    # 检查当前分支
    current_branch=$(git rev-parse --abbrev-ref HEAD)
    log_info "当前分支: $current_branch"

    # 获取最新代码
    log_info "拉取最新代码..."
    git fetch origin
    git pull origin "$current_branch"

    # 获取版本信息
    COMMIT_HASH=$(git rev-parse HEAD)
    COMMIT_DATE=$(git log -1 --format="%ci" HEAD)

    log_info "部署版本: $COMMIT_HASH"
    log_info "提交日期: $COMMIT_DATE"

    log_success "代码状态检查完成"
}

# 创建必要目录
create_directories() {
    log_step "创建部署目录..."

    # 创建日志目录
    mkdir -p "${PROJECT_ROOT}/logs/{deployment,monitoring,backup}"

    # 创建数据目录
    sudo mkdir -p /data/athena/{multimodal,backups,ssl,monitoring}
    sudo mkdir -p /data/athena/multimodal/{uploads,processed,cache}
    sudo mkdir -p /data/athena/backups/{postgres,redis,config}

    # 设置权限
    sudo chown -R $(whoami):$(whoami) /data/athena
    chmod 755 /data/athena

    # 创建配置目录
    mkdir -p "${PROJECT_ROOT}/config/ssl"
    mkdir -p "${PROJECT_ROOT}/config/nginx"

    log_success "目录创建完成"
}

# 配置SSL证书
setup_ssl() {
    log_step "配置SSL证书..."

    if [ ! -f "/etc/ssl/certs/${DOMAIN}.crt" ]; then
        log_info "SSL证书不存在，开始生成..."
        if [ -f "${PROJECT_ROOT}/scripts/setup_ssl.sh" ]; then
            # 使用非交互式方式生成自签名证书
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

# 配置负载均衡
setup_load_balancer() {
    log_step "配置负载均衡..."

    if [ -f "${PROJECT_ROOT}/scripts/setup_load_balancer.sh" ]; then
        bash "${PROJECT_ROOT}/scripts/setup_load_balancer.sh"
    else
        log_error "负载均衡配置脚本不存在"
        return 1
    fi

    log_success "负载均衡配置完成"
}

# 配置数据库
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

# 配置监控系统
setup_monitoring() {
    log_step "配置监控系统..."

    if [ -f "${PROJECT_ROOT}/scripts/setup_monitoring.sh" ]; then
        bash "${PROJECT_ROOT}/scripts/setup_monitoring.sh"
    else
        log_error "监控系统配置脚本不存在"
        return 1
    fi

    log_success "监控系统配置完成"
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

    # 部署数据库服务
    log_info "部署数据库服务..."
    docker-compose -f docker-compose.database.yml up -d

    # 等待数据库就绪
    log_info "等待数据库服务就绪..."
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
        services=("api-gateway:8020" "xiao-nuo-control:9001" "athena-platform:9000" "platform-monitor:9090")
        services_up=true

        for service_info in "${services[@]}"; do
            service=$(echo $service_info | cut -d':' -f1)
            port=$(echo $service_info | cut -d':' -f2)

            if ! curl -f "http://localhost:$port/health" >/dev/null 2>&1; then
                log_warning "服务 $service 健康检查失败 (端口: $port)"
                services_up=false
            else
                log_success "服务 $service 健康检查通过"
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

# 配置备份
setup_backup() {
    log_step "配置自动备份..."

    # 创建备份脚本
    cat > "${PROJECT_ROOT}/scripts/automated_backup.sh" << 'EOF'
#!/bin/bash
# 自动备份脚本

BACKUP_DIR="/data/athena/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 数据库备份
docker exec athena-postgres-primary pg_dump -U athenu_user athena_production > "${BACKUP_DIR}/postgres/db_backup_${DATE}.sql"

# 配置文件备份
tar -czf "${BACKUP_DIR}/config/config_backup_${DATE}.tar.gz" \
    /Users/xujian/Athena工作平台/deploy \
    /Users/xujian/Athena工作平台/docker \
    /Users/xujian/Athena工作平台/monitoring

# 清理旧备份（保留30天）
find "${BACKUP_DIR}" -name "*backup_*" -mtime +30 -delete

echo "备份完成: ${DATE}"
EOF

    chmod +x "${PROJECT_ROOT}/scripts/automated_backup.sh"

    # 添加到crontab
    (crontab -l 2>/dev/null; echo "0 2 * * * ${PROJECT_ROOT}/scripts/automated_backup.sh") | crontab -

    log_success "自动备份配置完成"
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

    # 检查日志
    log_info "检查应用日志..."
    for service in api-gateway xiao-nuo-control athena-platform platform-monitor; do
        echo "--- $service 日志 (最近10行) ---"
        docker logs "athena-$service" --tail 10 2>/dev/null || echo "无法获取日志"
        echo ""
    done

    log_success "部署后验证完成"
}

# 生成部署报告
generate_deployment_report() {
    log_step "生成部署报告..."

    report_file="${PROJECT_ROOT}/logs/deployment_report_$(date +%Y%m%d_%H%M%S).json"

    cat > "$report_file" << EOF
{
    "deployment": {
        "timestamp": "$(date -Iseconds)",
        "environment": "${ENVIRONMENT}",
        "domain": "${DOMAIN}",
        "commit_hash": "${COMMIT_HASH}",
        "status": "success",
        "duration": "$(date -d@$SECONDS -u +%T)"
    },
    "services": {
        "api_gateway": {
            "status": "$(docker ps --format "table {{.Names}}" | grep athena-api-gateway | wc -l > /dev/null && echo "running" || echo "stopped")",
            "url": "http://localhost:8020",
            "health": "http://localhost:8020/health"
        },
        "xiao_nuo_control": {
            "status": "$(docker ps --format "table {{.Names}}" | grep athena-xiao-nuo-control | wc -l > /dev/null && echo "running" || echo "stopped")",
            "url": "http://localhost:9001",
            "health": "http://localhost:9001/health"
        },
        "athena_platform": {
            "status": "$(docker ps --format "table {{.Names}}" | grep athena-platform-manager | wc -l > /dev/null && echo "running" || echo "stopped")",
            "url": "http://localhost:9000",
            "health": "http://localhost:9000/health"
        },
        "platform_monitor": {
            "status": "$(docker ps --format "table {{.Names}}" | grep athena-platform-monitor | wc -l > /dev/null && echo "running" || echo "stopped")",
            "url": "http://localhost:9090",
            "health": "http://localhost:9090/health"
        }
    },
    "monitoring": {
        "prometheus": {
            "url": "http://localhost:9090",
            "status": "$(curl -f http://localhost:9090/-/healthy >/dev/null 2>&1 && echo "healthy" || echo "unhealthy")"
        },
        "grafana": {
            "url": "http://localhost:3000",
            "status": "$(curl -f http://localhost:3000/api/health >/dev/null 2>&1 && echo "healthy" || echo "unhealthy")"
        }
    },
    "access_points": {
        "main_api": "http://localhost:8020",
        "api_docs": "http://localhost:8020/docs",
        "control_center": "http://localhost:9001",
        "platform_management": "http://localhost:9000",
        "monitoring": "http://localhost:9090"
    },
    "next_steps": [
        "配置域名解析",
        "设置SSL证书（如果使用真实域名）",
        "配置监控告警",
        "设置日志轮转",
        "配置自动备份",
        "执行性能测试",
        "配置负载均衡"
    ]
}
EOF

    log_success "部署报告生成完成: $report_file"
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
    echo -e "  📈 Prometheus: ${YELLOW}http://localhost:9090${NC}"
    echo ""
    echo -e "${CYAN}🔧 管理命令:${NC}"
    echo -e "  📊 查看状态: ${YELLOW}cd ${PROJECT_ROOT}/docker && docker-compose -f docker-compose.prod.yml ps${NC}"
    echo -e "  📋 查看日志: ${YELLOW}cd ${PROJECT_ROOT}/docker && docker-compose -f docker-compose.prod.yml logs -f${NC}"
    echo -e "  🔄 重启服务: ${YELLOW}cd ${PROJECT_ROOT}/docker && docker-compose -f docker-compose.prod.yml restart${NC}"
    echo -e "  🛑 停止服务: ${YELLOW}cd ${PROJECT_ROOT}/docker && docker-compose -f docker-compose.prod.yml down${NC}"
    echo ""
    echo -e "${CYAN}📊 监控信息:${NC}"
    echo -e "  📈 Grafana用户名/密码: ${YELLOW}admin/admin123${NC}"
    echo -e "  📋 部署日志: ${YELLOW}${DEPLOYMENT_LOG}${NC}"
    echo ""
    echo -e "${YELLOW}📌 重要提示:${NC}"
    echo -e "  1. 访问Grafana配置监控仪表板"
    echo -e "  2. 配置告警通知方式（Slack/邮件）"
    echo -e "  3. 检查SSL证书配置"
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

    check_code_status
    create_directories
    setup_ssl
    setup_load_balancer
    setup_database
    setup_monitoring
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

    setup_backup
    post_deploy_verification
    generate_deployment_report

    show_deployment_results

    log_success "生产环境部署成功完成！"
}

# 错误处理
trap 'log_error "部署过程中发生错误，请检查日志: $DEPLOYMENT_LOG"; exit 1' ERR

# 执行主函数
main "$@"