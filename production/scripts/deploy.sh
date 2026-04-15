#!/bin/bash

# Athena工作平台Kubernetes生产环境部署脚本
# 用途：一键部署Athena工作平台到Kubernetes生产环境
# 作者：Athena平台运维团队
# 版本：2.0.0

set -euo pipefail

# 颜色和日志配置
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 脚本配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
K8S_DIR="${PROJECT_ROOT}/production/k8s"
ENVIRONMENT=${1:-"production"}
NAMESPACE="athena-${ENVIRONMENT}"

# 验证前置条件
validate_prerequisites() {
    log_info "验证部署前置条件..."
    
    # 检查kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl未安装，请先安装kubectl"
        exit 1
    fi
    
    # 检查集群连接
    if ! kubectl cluster-info &> /dev/null; then
        log_error "无法连接到Kubernetes集群"
        exit 1
    fi
    
    # 检查helm（可选）
    if command -v helm &> /dev/null; then
        log_info "Helm已安装，版本：$(helm version --template='{{.Version}}')"
    else
        log_warn "Helm未安装，将使用kubectl部署"
    fi
    
    # 检查配置文件
    if [[ ! -d "$K8S_DIR" ]]; then
        log_error "Kubernetes配置目录不存在：$K8S_DIR"
        exit 1
    fi
    
    log_info "前置条件验证通过"
}

# 创建命名空间
create_namespaces() {
    log_info "创建命名空间..."
    
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warn "命名空间 $NAMESPACE 已存在"
    else
        kubectl apply -f "${K8S_DIR}/namespaces/production-namespaces.yaml"
        log_info "命名空间创建完成"
    fi
}

# 应用配置映射
apply_configmaps() {
    log_info "应用配置映射..."
    
    kubectl apply -f "${K8S_DIR}/configmaps/production-configmaps.yaml" -n "$NAMESPACE"
    
    # 等待配置映射就绪
    kubectl wait --for=condition=complete configmap --all -n "$NAMESPACE" --timeout=60s
    
    log_info "配置映射应用完成"
}

# 应用密钥
apply_secrets() {
    log_info "应用密钥..."
    
    # 检查是否存在外部密钥文件
    if [[ -f "${K8S_DIR}/secrets/production-secrets.yaml" ]]; then
        kubectl apply -f "${K8S_DIR}/secrets/production-secrets.yaml" -n "$NAMESPACE"
    else
        log_warn "生产密钥文件不存在，使用默认配置"
        log_warn "请确保在生产环境中手动配置密钥"
    fi
    
    log_info "密钥应用完成"
}

# 部署应用
deploy_applications() {
    log_info "部署应用服务..."
    
    # 按顺序部署：数据库 -> 缓存 -> 应用
    local deployment_order=("postgres-deployment" "redis-deployment" "qdrant-deployment" "athena-api-deployment")
    
    for deployment in "${deployment_order[@]}"; do
        log_info "部署 $deployment..."
        kubectl apply -f "${K8S_DIR}/deployments/production-deployments.yaml" -n "$NAMESPACE" --selector=app.kubernetes.io/name="$deployment"
        
        # 等待部署完成
        if [[ "$deployment" == "athena-api-deployment" ]]; then
            kubectl rollout status "deployment/$deployment" -n "$NAMESPACE" --timeout=600s
        else
            kubectl rollout status "deployment/$deployment" -n "$NAMESPACE" --timeout=300s
        fi
        
        log_info "$deployment 部署完成"
    done
}

# 创建服务
create_services() {
    log_info "创建服务..."
    
    kubectl apply -f "${K8S_DIR}/services/production-services.yaml" -n "$NAMESPACE"
    
    # 等待服务就绪
    sleep 10
    
    log_info "服务创建完成"
}

# 配置Ingress
configure_ingress() {
    log_info "配置Ingress..."
    
    kubectl apply -f "${K8S_DIR}/ingress/production-ingress.yaml" -n "$NAMESPACE"
    
    # 等待Ingress就绪
    kubectl wait --for=condition=ready ingress --all -n "$NAMESPACE" --timeout=120s
    
    log_info "Ingress配置完成"
}

# 应用网络策略
apply_network_policies() {
    log_info "应用网络策略..."
    
    kubectl apply -f "${K8S_DIR}/network-policies/production-network-policies.yaml" -n "$NAMESPACE"
    
    log_info "网络策略应用完成"
}

# 部署监控系统
deploy_monitoring() {
    log_info "部署监控系统..."
    
    # 部署Prometheus
    if ! kubectl get namespace athena-monitoring &> /dev/null; then
        kubectl create namespace athena-monitoring
    fi
    
    # 这里可以集成Helm部署Prometheus和Grafana
    if command -v helm &> /dev/null; then
        helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
        helm repo update
        
        # 部署Prometheus
        helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
            --namespace athena-monitoring \
            --create-namespace \
            --values "${PROJECT_ROOT}/production/monitoring/prometheus/values.yaml" \
            --wait
    else
        log_warn "Helm未安装，跳过Prometheus部署"
    fi
    
    log_info "监控系统部署完成"
}

# 验证部署
verify_deployment() {
    log_info "验证部署状态..."
    
    # 检查Pod状态
    local failed_pods=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase!=Running,status.phase!=Succeeded --no-headers | wc -l)
    if [[ $failed_pods -gt 0 ]]; then
        log_error "发现 $failed_pods 个异常Pod"
        kubectl get pods -n "$NAMESPACE" --field-selector=status.phase!=Running,status.phase!=Succeeded
        return 1
    fi
    
    # 检查服务状态
    log_info "服务状态："
    kubectl get services -n "$NAMESPACE"
    
    # 检查Ingress状态
    log_info "Ingress状态："
    kubectl get ingress -n "$NAMESPACE"
    
    # 运行健康检查
    log_info "运行健康检查..."
    local api_url=$(kubectl get ingress athena-ingress -n "$NAMESPACE" -o jsonpath='{.spec.rules[0].host}')
    if curl -f "https://$api_url/health" &> /dev/null; then
        log_info "API健康检查通过"
    else
        log_error "API健康检查失败"
        return 1
    fi
    
    log_info "部署验证完成"
}

# 显示部署信息
show_deployment_info() {
    log_info "部署完成！"
    
    echo ""
    echo "==================================="
    echo "Athena工作平台部署信息"
    echo "==================================="
    echo "环境: $ENVIRONMENT"
    echo "命名空间: $NAMESPACE"
    echo ""
    
    # 获取服务URL
    local api_url=$(kubectl get ingress athena-ingress -n "$NAMESPACE" -o jsonpath='{.spec.rules[0].host}' 2>/dev/null || echo "未配置")
    local grafana_url="monitoring.athena-patent.com"
    
    echo "服务访问地址："
    echo "- API服务: https://$api_url"
    echo "- API文档: https://$api_url/docs"
    echo "- 监控面板: https://$grafana_url"
    echo ""
    
    echo "管理命令："
    echo "- 查看Pod: kubectl get pods -n $NAMESPACE"
    echo "- 查看日志: kubectl logs -f deployment/athena-api-deployment -n $NAMESPACE"
    echo "- 进入Pod: kubectl exec -it deployment/athena-api-deployment -n $NAMESPACE -- bash"
    echo ""
    
    echo "验证命令："
    echo "- 健康检查: curl -f https://$api_url/health"
    echo "- 状态检查: curl -f https://$api_url/api/v1/status"
    echo "==================================="
}

# 清理函数
cleanup_on_error() {
    log_error "部署过程中发生错误，开始清理..."
    
    # 显示当前状态用于调试
    kubectl get pods -n "$NAMESPACE" || true
    kubectl get events -n "$NAMESPACE" --sort-by='.lastTimestamp' || true
    
    log_error "清理完成，请检查错误信息并修复后重试"
}

# 主函数
main() {
    local start_time=$(date +%s)
    
    log_info "开始部署Athena工作平台到 $ENVIRONMENT 环境"
    log_info "项目根目录: $PROJECT_ROOT"
    log_info "Kubernetes配置目录: $K8S_DIR"
    
    # 设置错误处理
    trap cleanup_on_error ERR
    
    # 执行部署步骤
    validate_prerequisites
    create_namespaces
    apply_configmaps
    apply_secrets
    deploy_applications
    create_services
    configure_ingress
    apply_network_policies
    deploy_monitoring
    verify_deployment
    show_deployment_info
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log_info "部署完成！总用时：${duration}秒"
}

# 显示使用帮助
show_help() {
    echo "Athena工作平台Kubernetes部署脚本"
    echo ""
    echo "用法: $0 [选项] [环境]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -v, --verbose  详细输出"
    echo ""
    echo "环境:"
    echo "  development   开发环境"
    echo "  production    生产环境 (默认)"
    echo ""
    echo "示例:"
    echo "  $0 production     # 部署到生产环境"
    echo "  $0 development    # 部署到开发环境"
    echo ""
}

# 解析命令行参数
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    -v|--verbose)
        set -x
        shift
        ;;
esac

# 执行主函数
main "$@"
