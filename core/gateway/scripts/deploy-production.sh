#!/bin/bash
# ================================
# Athena API Gateway - 生产部署脚本
# ================================
# 一键部署企业级生产环境
set -euo pipefail

# 配置变量
NAMESPACE=${NAMESPACE:-"athena-gateway"}
ENVIRONMENT=${ENVIRONMENT:-"production"}
REGISTRY=${REGISTRY:-"your-registry.com"}
VERSION=${VERSION:-"v2.0.0"}
POSTGRES_HOST=${POSTGRES_HOST:-"your-postgres-host.local"}

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

info() {
    echo -e "${PURPLE}[INFO]${NC} $1"
}

# 显示Banner
show_banner() {
    echo -e "${PURPLE}"
    echo "=========================================="
    echo "    Athena API Gateway 生产部署器"
    echo "=========================================="
    echo "    版本: ${VERSION}"
    echo "    环境: ${ENVIRONMENT}"
    echo "    命名空间: ${NAMESPACE}"
    echo "=========================================="
    echo -e "${NC}"
}

# 检查依赖
check_dependencies() {
    log "检查部署依赖..."
    
    local deps=("kubectl" "docker" "openssl")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" >/dev/null 2>&1; then
            error "依赖 $dep 未安装"
        fi
    done
    
    # 检查Kubernetes集群连接
    if ! kubectl cluster-info >/dev/null 2>&1; then
        error "无法连接到Kubernetes集群"
    fi
    
    success "依赖检查完成"
}

# 创建命名空间
create_namespaces() {
    log "创建命名空间..."
    
    local namespaces=("athena-gateway" "observability" "cache" "database")
    for ns in "${namespaces[@]}"; do
        if ! kubectl get namespace "$ns" >/dev/null 2>&1; then
            kubectl create namespace "$ns"
            success "命名空间 $ns 创建完成"
        else
            info "命名空间 $ns 已存在"
        fi
    done
}

# 部署基础设施组件
deploy_infrastructure() {
    log "部署基础设施组件..."
    
    # 部署Redis集群
    info "部署Redis缓存集群..."
    kubectl apply -f deployments/production/11-redis.yaml -n cache
    kubectl wait --for=condition=ready pod -l app=redis -n cache --timeout=300s
    
    # 部署Prometheus监控
    info "部署Prometheus监控系统..."
    kubectl apply -f deployments/production/20-prometheus.yaml -n observability
    kubectl wait --for=condition=ready pod -l app=prometheus -n observability --timeout=300s
    
    # 部署Grafana
    info "部署Grafana可视化..."
    kubectl apply -f deployments/production/21-grafana.yaml -n observability
    kubectl wait --for=condition=ready pod -l app=grafana -n observability --timeout=300s
    
    # 部署AlertManager
    info "部署AlertManager告警系统..."
    kubectl apply -f deployments/production/22-alertmanager.yaml -n observability
    kubectl wait --for=condition=ready pod -l app=alertmanager -n observability --timeout=300s
    
    # 部署Loki日志系统
    info "部署Loki日志聚合..."
    kubectl apply -f deployments/production/23-loki.yaml -n observability
    kubectl wait --for=condition=ready pod -l app=loki -n observability --timeout=300s
    
    success "基础设施组件部署完成"
}

# 生成密钥
generate_secrets() {
    log "生成生产密钥..."
    
    # 创建数据库凭据密钥
    if ! kubectl get secret external-postgres-credentials -n observability >/dev/null 2>&1; then
        kubectl create secret generic external-postgres-credentials \
            --from-literal=password="${POSTGRES_PASSWORD}" \
            --from-literal=user="athena_user" \
            -n observability
        success "PostgreSQL凭据密钥创建完成"
    fi
    
    # 创建Grafana凭据
    if ! kubectl get secret grafana-credentials -n observability >/dev/null 2>&1; then
        kubectl create secret generic grafana-credentials \
            --from-literal=admin-user="admin" \
            --from-literal=admin-password="${GRAFANA_PASSWORD}" \
            --from-literal=smtp-user="alerts@company.com" \
            --from-literal=smtp-password="${SMTP_PASSWORD}" \
            -n observability
        success "Grafana凭据密钥创建完成"
    fi
    
    # 运行密钥生成脚本
    ./scripts/manage-secrets.sh create
    
    success "密钥生成完成"
}

# 部署应用
deploy_application() {
    log "部署Athena API Gateway..."
    
    # 更新配置中的PostgreSQL主机地址
    sed -i.bak "s/your-postgres-host.local/${POSTGRES_HOST}/g" deployments/production/01-configmap.yaml
    
    # 部署应用组件
    kubectl apply -f deployments/production/00-namespace.yaml
    kubectl apply -f deployments/production/01-configmap.yaml
    kubectl apply -f deployments/production/02-secrets.yaml
    kubectl apply -f deployments/production/03-deployment.yaml
    kubectl apply -f deployments/production/04-service.yaml
    kubectl apply -f deployments/production/05-hpa.yaml
    
    # 等待部署完成
    kubectl wait --for=condition=available deployment/athena-gateway -n athena-gateway --timeout=600s
    
    # 恢复配置文件
    mv deployments/production/01-configmap.yaml.bak deployments/production/01-configmap.yaml
    
    success "应用部署完成"
}

# 部署入口控制器
deploy_ingress() {
    log "部署入口控制器..."
    
    # 创建TLS证书
    if ! kubectl get secret athena-gateway-tls -n athena-gateway >/dev/null 2>&1; then
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout /tmp/tls.key -out /tmp/tls.crt \
            -subj "/CN=athena-gateway.company.com"
        
        kubectl create secret tls athena-gateway-tls \
            --cert=/tmp/tls.crt \
            --key=/tmp/tls.key \
            -n athena-gateway
            
        rm -f /tmp/tls.key /tmp/tls.crt
        success "TLS证书创建完成"
    fi
    
    # 部署Ingress
    kubectl apply -f deployments/production/30-ingress.yaml
    
    success "入口控制器部署完成"
}

# 验证部署
verify_deployment() {
    log "验证部署状态..."
    
    # 检查Pod状态
    info "检查Pod状态..."
    kubectl get pods -n athena-gateway
    kubectl get pods -n observability
    kubectl get pods -n cache
    
    # 检查服务状态
    info "检查服务状态..."
    kubectl get svc -n athena-gateway
    kubectl get svc -n observability
    kubectl get svc -n cache
    
    # 健康检查
    info "执行健康检查..."
    
    # 检查API网关
    local gateway_pod=$(kubectl get pods -n athena-gateway -l app=athena-gateway -o jsonpath='{.items[0].metadata.name}')
    kubectl exec -n athena-gateway "$gateway_pod" -- curl -f http://localhost:8080/health
    
    # 检查Redis
    local redis_pod=$(kubectl get pods -n cache -l app=redis,role=master -o jsonpath='{.items[0].metadata.name}')
    kubectl exec -n cache "$redis_pod" -- redis-cli ping
    
    # 检查Prometheus
    local prometheus_pod=$(kubectl get pods -n observability -l app=prometheus -o jsonpath='{.items[0].metadata.name}')
    kubectl exec -n observability "$prometheus_pod" -- wget -q -O- http://localhost:9090/-/healthy
    
    success "部署验证完成"
}

# 显示部署信息
show_deployment_info() {
    log "部署信息汇总..."
    
    echo "=========================================="
    echo "🎉 Athena API Gateway 部署完成!"
    echo "=========================================="
    echo ""
    echo "📊 监控面板:"
    echo "  Grafana: https://grafana.company.com"
    echo "  Prometheus: https://prometheus.company.com"
    echo "  AlertManager: https://alertmanager.company.com"
    echo ""
    echo "🌐 访问地址:"
    echo "  API Gateway: https://athena-gateway.company.com"
    echo ""
    echo "🔧 管理命令:"
    echo "  查看日志: kubectl logs -f deployment/athena-gateway -n athena-gateway"
    echo "  扩容: kubectl scale deployment athena-gateway --replicas=5 -n athena-gateway"
    echo "  更新: kubectl set image deployment/athena-gateway athena-gateway=${REGISTRY}/athena-gateway:${VERSION} -n athena-gateway"
    echo ""
    echo "📈 性能指标:"
    echo "  副本数: $(kubectl get deployment athena-gateway -n athena-gateway -o jsonpath='{.status.readyReplicas}')"
    echo "  CPU限制: 500m"
    echo "  内存限制: 1Gi"
    echo ""
    echo "=========================================="
}

# 清理函数
cleanup() {
    log "清理临时文件..."
    # 清理可能的临时文件
    rm -f deployments/production/*.bak
}

# 主函数
main() {
    local action=${1:-"deploy"}
    
    show_banner
    
    case "$action" in
        "deploy")
            check_dependencies
            create_namespaces
            generate_secrets
            deploy_infrastructure
            deploy_application
            deploy_ingress
            verify_deployment
            show_deployment_info
            ;;
        "secrets")
            generate_secrets
            ;;
        "verify")
            verify_deployment
            ;;
        "cleanup")
            kubectl delete namespace athena-gateway observability cache database --ignore-not-found=true
            ;;
        *)
            echo "使用方法: $0 {deploy|secrets|verify|cleanup}"
            echo ""
            echo "命令说明:"
            echo "  deploy   - 完整生产部署"
            echo "  secrets  - 仅生成密钥"
            echo "  verify   - 验证部署状态"
            echo "  cleanup  - 清理部署"
            exit 1
            ;;
    esac
    
    cleanup
}

# 错误处理
trap 'error "部署过程中发生错误，退出码: $?"' ERR
trap cleanup EXIT

# 执行主函数
main "$@"