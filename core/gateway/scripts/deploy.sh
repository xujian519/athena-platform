#!/bin/bash

# Athena API Gateway - 部署脚本

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-ghcr.io/athena-workspace}"
IMAGE_NAME="gateway"
VERSION="${VERSION:-latest}"

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查环境
check_environment() {
    log_info "检查部署环境..."
    
    local required_vars=("ENVIRONMENT")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "环境变量 $var 未设置"
            exit 1
        fi
    done
    
    log_success "环境检查通过"
}

# 构建Docker镜像
build_image() {
    log_info "构建Docker镜像..."
    
    cd "$PROJECT_ROOT"
    
    # 构建镜像
    docker build \
        --build-arg VERSION="$VERSION" \
        --build-arg BUILD_TIME="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        -t "${DOCKER_REGISTRY}/${IMAGE_NAME}:${VERSION}" \
        -t "${DOCKER_REGISTRY}/${IMAGE_NAME}:latest" \
        .
    
    log_success "Docker镜像构建完成"
}

# 推送Docker镜像
push_image() {
    log_info "推送Docker镜像..."
    
    docker push "${DOCKER_REGISTRY}/${IMAGE_NAME}:${VERSION}"
    docker push "${DOCKER_REGISTRY}/${IMAGE_NAME}:latest"
    
    log_success "Docker镜像推送完成"
}

# 部署到Kubernetes
deploy_kubernetes() {
    log_info "部署到Kubernetes..."
    
    local namespace="${ENVIRONMENT}"
    local kubeconfig="${KUBECONFIG:-$HOME/.kube/config}"
    
    # 创建命名空间（如果不存在）
    kubectl create namespace "$namespace" --dry-run=client -o yaml | kubectl apply -f -
    
    # 应用配置
    kubectl apply -f "$PROJECT_ROOT/deployments/k8s/" -n "$namespace"
    
    # 等待部署完成
    kubectl rollout status deployment/gateway -n "$namespace" --timeout=300s
    
    log_success "Kubernetes部署完成"
}

# 部署到Docker Swarm
deploy_docker_swarm() {
    log_info "部署到Docker Swarm..."
    
    local stack_name="athena-gateway"
    local env_file="$PROJECT_ROOT/.env.${ENVIRONMENT}"
    
    if [[ ! -f "$env_file" ]]; then
        log_error "环境配置文件不存在: $env_file"
        exit 1
    fi
    
    # 部署stack
    docker stack deploy \
        --compose-file "$PROJECT_ROOT/docker-compose.yml" \
        --env-file "$env_file" \
        "$stack_name"
    
    log_success "Docker Swarm部署完成"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    local service_url="${SERVICE_URL:-http://localhost:8080}"
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f "$service_url/health" &>/dev/null; then
            log_success "健康检查通过"
            return 0
        fi
        
        log_info "健康检查尝试 $attempt/$max_attempts 失败，重试中..."
        sleep 10
        ((attempt++))
    done
    
    log_error "健康检查失败"
    return 1
}

# 回滚部署
rollback() {
    log_info "回滚部署..."
    
    case "${DEPLOYMENT_TYPE:-kubernetes}" in
        kubernetes)
            local namespace="${ENVIRONMENT}"
            kubectl rollout undo deployment/gateway -n "$namespace"
            kubectl rollout status deployment/gateway -n "$namespace" --timeout=300s
            ;;
        docker-swarm)
            local stack_name="athena-gateway"
            docker stack rm "$stack_name"
            # 重新部署上一个版本
            docker stack deploy \
                --compose-file "$PROJECT_ROOT/docker-compose.previous.yml" \
                "$stack_name"
            ;;
        *)
            log_error "未知的部署类型: ${DEPLOYMENT_TYPE}"
            exit 1
            ;;
    esac
    
    log_success "回滚完成"
}

# 清理资源
cleanup() {
    log_info "清理部署资源..."
    
    case "${DEPLOYMENT_TYPE:-kubernetes}" in
        kubernetes)
            local namespace="${ENVIRONMENT}"
            kubectl delete -f "$PROJECT_ROOT/deployments/k8s/" -n "$namespace" --ignore-not-found=true
            ;;
        docker-swarm)
            local stack_name="athena-gateway"
            docker stack rm "$stack_name"
            ;;
    esac
    
    log_success "资源清理完成"
}

# 显示部署状态
show_status() {
    log_info "部署状态:"
    echo ""
    
    case "${DEPLOYMENT_TYPE:-kubernetes}" in
        kubernetes)
            local namespace="${ENVIRONMENT}"
            echo "📊 Kubernetes Pods:"
            kubectl get pods -n "$namespace" -l app=gateway
            echo ""
            echo "🌐 Services:"
            kubectl get services -n "$namespace" -l app=gateway
            echo ""
            echo "📈 Deployments:"
            kubectl get deployments -n "$namespace" -l app=gateway
            ;;
        docker-swarm)
            echo "🐳 Docker Services:"
            docker service ls --filter label=com.docker.stack.namespace=athena-gateway
            ;;
    esac
    
    echo ""
}

# 主函数
main() {
    echo "🚀 Athena API Gateway - 部署脚本"
    echo ""
    
    local command=${1:-deploy}
    
    case $command in
        deploy)
            check_environment
            build_image
            push_image
            
            case "${DEPLOYMENT_TYPE:-kubernetes}" in
                kubernetes)
                    deploy_kubernetes
                    ;;
                docker-swarm)
                    deploy_docker_swarm
                    ;;
                *)
                    log_error "未知的部署类型: ${DEPLOYMENT_TYPE:-kubernetes}"
                    exit 1
                    ;;
            esac
            
            # 健康检查
            sleep 10
            if health_check; then
                show_status
            else
                log_warning "健康检查失败，可能需要手动排查"
                show_status
            fi
            ;;
        
        rollback)
            rollback
            ;;
        
        status)
            show_status
            ;;
        
        cleanup)
            cleanup
            ;;
        
        build-only)
            check_environment
            build_image
            ;;
        
        push-only)
            push_image
            ;;
        
        help)
            echo "用法: $0 [command]"
            echo ""
            echo "命令:"
            echo "  deploy     完整部署 (构建 + 推送 + 部署)"
            echo "  rollback   回滚到上一个版本"
            echo "  status     显示部署状态"
            echo "  cleanup    清理部署资源"
            echo "  build-only 仅构建Docker镜像"
            echo "  push-only  仅推送Docker镜像"
            echo "  help       显示帮助信息"
            echo ""
            echo "环境变量:"
            echo "  ENVIRONMENT    部署环境 (dev/staging/prod)"
            echo "  DOCKER_REGISTRY Docker镜像仓库地址"
            echo "  VERSION        镜像版本 (默认: latest)"
            echo "  DEPLOYMENT_TYPE 部署类型 (kubernetes/docker-swarm)"
            echo "  KUBECONFIG    Kubernetes配置文件路径"
            echo "  SERVICE_URL    服务地址 (用于健康检查)"
            echo ""
            echo "示例:"
            echo "  ENVIRONMENT=staging VERSION=v1.2.3 $0 deploy"
            echo "  ENVIRONMENT=prod DEPLOYMENT_TYPE=kubernetes $0 status"
            echo "  ENVIRONMENT=dev $0 cleanup"
            ;;
        
        *)
            log_error "未知命令: $command"
            main help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"