#!/bin/bash

# Athena工作平台自动化部署脚本
# 作者: 徐健
# 创建日期: 2025-12-13

set -e  # 遇到错误立即退出

# 配置变量
ENVIRONMENT=${1:-staging}  # 默认部署到staging环境
VERSION=${2:-latest}       # 默认使用latest版本
PROJECT_NAME="athena-platform"
REGISTRY="ghcr.io/${USER:-athena}"

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

# 检查必要的工具
check_prerequisites() {
    log_info "检查部署环境..."

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

    # 检查kubectl（如果部署到K8s）
    if [[ "$ENVIRONMENT" == "production" ]]; then
        if ! command -v kubectl &> /dev/null; then
            log_error "kubectl未安装，生产环境部署需要kubectl"
            exit 1
        fi
    fi

    log_success "环境检查通过"
}

# 加载环境变量
load_env_vars() {
    log_info "加载环境变量..."

    # 根据环境加载不同的.env文件
    ENV_FILE=".env.${ENVIRONMENT}"
    if [[ -f "$ENV_FILE" ]]; then
        export $(cat $ENV_FILE | grep -v '^#' | xargs)
        log_success "已加载 $ENV_FILE"
    else
        log_warning "未找到 $ENV_FILE，使用默认环境变量"
        if [[ -f ".env" ]]; then
            export $(cat .env | grep -v '^#' | xargs)
        fi
    fi
}

# 构建镜像
build_images() {
    log_info "构建Docker镜像..."

    # 构建主应用镜像
    docker build -t ${REGISTRY}/${PROJECT_NAME}:${VERSION} .
    docker tag ${REGISTRY}/${PROJECT_NAME}:${VERSION} ${REGISTRY}/${PROJECT_NAME}:latest

    log_success "镜像构建完成"
}

# 推送镜像到仓库
push_images() {
    log_info "推送镜像到仓库..."

    docker push ${REGISTRY}/${PROJECT_NAME}:${VERSION}
    docker push ${REGISTRY}/${PROJECT_NAME}:latest

    log_success "镜像推送完成"
}

# 运行健康检查
health_check() {
    local service_name=$1
    local health_url=$2
    local max_attempts=30
    local attempt=1

    log_info "检查 ${service_name} 健康状态..."

    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s $health_url > /dev/null; then
            log_success "${service_name} 健康检查通过"
            return 0
        fi

        log_warning "${service_name} 健康检查失败 (尝试 $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done

    log_error "${service_name} 健康检查失败，部署可能存在问题"
    return 1
}

# 部署到Docker Compose环境
deploy_docker_compose() {
    log_info "部署到 $ENVIRONMENT 环境 (Docker Compose)..."

    # 根据环境选择compose文件
    COMPOSE_FILE="docker-compose.${ENVIRONMENT}.yml"
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        COMPOSE_FILE="docker-compose.yml"
    fi

    # 停止旧服务
    docker-compose -f $COMPOSE_FILE down

    # 启动新服务
    docker-compose -f $COMPOSE_FILE up -d

    # 等待服务启动
    sleep 30

    # 运行健康检查
    health_check "API Gateway" "http://localhost:8080/health"
    health_check "YunPat Agent" "http://localhost:8020/health"
    health_check "Unified Identity" "http://localhost:8010/health"

    log_success "Docker Compose部署完成"
}

# 部署到Kubernetes环境
deploy_kubernetes() {
    log_info "部署到 $ENVIRONMENT 环境 (Kubernetes)..."

    # 设置命名空间
    kubectl create namespace $ENVIRONMENT --dry-run=client -o yaml | kubectl apply -f -

    # 应用配置
    kubectl apply -f k8s/${ENVIRONMENT}/ -n $ENVIRONMENT

    # 等待部署完成
    kubectl rollout status deployment/${PROJECT_NAME} -n $ENVIRONMENT --timeout=300s

    # 获取服务URL
    SERVICE_URL=$(kubectl get svc ${PROJECT_NAME} -n $ENVIRONMENT -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    if [[ -z "$SERVICE_URL" ]]; then
        SERVICE_URL=$(kubectl get svc ${PROJECT_NAME} -n $ENVIRONMENT -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    fi

    # 运行健康检查
    if [[ -n "$SERVICE_URL" ]]; then
        health_check "Kubernetes Service" "http://${SERVICE_URL}/health"
    else
        log_warning "无法获取服务URL，跳过健康检查"
    fi

    log_success "Kubernetes部署完成"
}

# 部署监控服务
deploy_monitoring() {
    log_info "部署监控服务..."

    # 部署Prometheus、Grafana等
    if [[ -f "monitoring/docker-compose.monitoring.yml" ]]; then
        docker-compose -f monitoring/docker-compose.monitoring.yml up -d
        log_success "监控服务部署完成"
    else
        log_warning "未找到监控配置文件，跳过监控部署"
    fi
}

# 运行数据库迁移
run_migrations() {
    log_info "运行数据库迁移..."

    # 检查是否有迁移脚本
    if [[ -d "migrations" ]]; then
        docker-compose exec -T athena-main python manage.py migrate
        log_success "数据库迁移完成"
    else
        log_info "未找到迁移脚本，跳过数据库迁移"
    fi
}

# 验证部署
verify_deployment() {
    log_info "验证部署..."

    # 检查服务状态
    if command -v docker-compose &> /dev/null; then
        docker-compose ps
    fi

    # 运行集成测试
    if [[ -d "tests/integration" ]]; then
        log_info "运行集成测试..."
        python -m pytest tests/integration/ -v
        if [[ $? -eq 0 ]]; then
            log_success "集成测试通过"
        else
            log_error "集成测试失败"
            exit 1
        fi
    fi

    log_success "部署验证完成"
}

# 清理旧镜像
cleanup() {
    log_info "清理旧镜像..."

    # 删除未使用的Docker镜像
    docker image prune -f

    # 删除超过7天的旧镜像
    docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}" | \
        grep ${PROJECT_NAME} | \
        awk '$3 < "'$(date -d '7 days ago' '+%Y-%m-%d')'" {print $3}' | \
        xargs -r docker rmi

    log_success "清理完成"
}

# 发送部署通知
send_notification() {
    local status=$1
    local message="Athena平台部署到 ${ENVIRONMENT} 环境${status}"

    # 发送邮件通知
    if [[ -n "$SMTP_SERVER" && -n "$NOTIFICATION_EMAIL" ]]; then
        echo "$message" | mail -s "Athena部署通知" $NOTIFICATION_EMAIL
    fi

    # 发送Slack通知
    if [[ -n "$SLACK_WEBHOOK_URL" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$message\"}" \
            $SLACK_WEBHOOK_URL
    fi
}

# 主函数
main() {
    log_info "开始自动化部署..."
    log_info "环境: $ENVIRONMENT"
    log_info "版本: $VERSION"

    # 检查前置条件
    check_prerequisites

    # 加载环境变量
    load_env_vars

    # 执行部署步骤
    if [[ "$ENVIRONMENT" == "production" ]]; then
        # 生产环境使用Kubernetes
        build_images
        push_images
        deploy_kubernetes
    else
        # 测试环境使用Docker Compose
        deploy_docker_compose
    fi

    # 部署后任务
    deploy_monitoring
    run_migrations
    verify_deployment
    cleanup

    # 发送成功通知
    send_notification "成功"

    log_success "自动化部署完成！"
    log_info "部署时间: $(date)"
    log_info "环境: $ENVIRONMENT"
    log_info "版本: $VERSION"
}

# 错误处理
trap 'log_error "部署过程中发生错误，请检查日志"; send_notification "失败"; exit 1' ERR

# 执行主函数
main "$@"