#!/bin/bash

# Athena工作平台健康检查脚本
# 用途：全面检查Athena平台各组件的健康状态
# 作者：Athena平台运维团队
# 版本：1.0.0

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
ENVIRONMENT=${1:-"production"}
NAMESPACE="athena-${ENVIRONMENT}"
HEALTH_CHECK_TIMEOUT=${2:-"60"}

# 健康检查结果统计
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# 检查结果记录
check_result() {
    local test_name="$1"
    local result="$2"
    local message="$3"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [[ "$result" == "PASS" ]]; then
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        echo -e "  ${GREEN}✓${NC} $test_name: $message"
    else
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        echo -e "  ${RED}✗${NC} $test_name: $message"
    fi
}

# 检查Kubernetes集群连接
check_kubernetes_cluster() {
    log_info "检查Kubernetes集群连接..."
    
    if kubectl cluster-info &> /dev/null; then
        local cluster_info=$(kubectl cluster-info | head -1)
        check_result "Kubernetes集群连接" "PASS" "$cluster_info"
    else
        check_result "Kubernetes集群连接" "FAIL" "无法连接到集群"
    fi
}

# 检查命名空间
check_namespaces() {
    log_info "检查命名空间..."
    
    local namespaces=("athena-production" "athena-monitoring" "athena-logging")
    
    for ns in "${namespaces[@]}"; do
        if kubectl get namespace "$ns" &> /dev/null; then
            local status=$(kubectl get namespace "$ns" -o jsonpath='{.status.phase}')
            check_result "命名空间 $ns" "PASS" "状态: $status"
        else
            check_result "命名空间 $ns" "FAIL" "命名空间不存在"
        fi
    done
}

# 检查Pod健康状态
check_pods() {
    log_info "检查Pod健康状态..."
    
    local all_pods=$(kubectl get pods -n "$NAMESPACE" --no-headers 2>/dev/null || true)
    if [[ -z "$all_pods" ]]; then
        check_result "Pod检查" "FAIL" "无法获取Pod列表"
        return
    fi
    
    while IFS= read -r pod_line; do
        if [[ -n "$pod_line" ]]; then
            local pod_name=$(echo "$pod_line" | awk '{print $1}')
            local pod_status=$(echo "$pod_line" | awk '{print $3}')
            local pod_ready=$(echo "$pod_line" | awk '{print $2}')
            
            if [[ "$pod_status" == "Running" && "$pod_ready" == "1/1" ]]; then
                check_result "Pod $pod_name" "PASS" "状态: $pod_status, 就绪: $pod_ready"
            else
                check_result "Pod $pod_name" "FAIL" "状态: $pod_status, 就绪: $pod_ready"
            fi
        fi
    done <<< "$all_pods"
}

# 检查服务状态
check_services() {
    log_info "检查服务状态..."
    
    local services=$(kubectl get services -n "$NAMESPACE" --no-headers 2>/dev/null || true)
    if [[ -z "$services" ]]; then
        check_result "服务检查" "FAIL" "无法获取服务列表"
        return
    fi
    
    while IFS= read -r service_line; do
        if [[ -n "$service_line" ]]; then
            local service_name=$(echo "$service_line" | awk '{print $1}')
            local service_type=$(echo "$service_line" | awk '{print $2}')
            local cluster_ip=$(echo "$service_line" | awk '{print $3}')
            
            if [[ -n "$cluster_ip" && "$cluster_ip" != "<none>" ]]; then
                check_result "服务 $service_name" "PASS" "类型: $service_type, IP: $cluster_ip"
            else
                check_result "服务 $service_name" "WARN" "类型: $service_type, 无集群IP"
            fi
        fi
    done <<< "$services"
}

# 检查Ingress状态
check_ingress() {
    log_info "检查Ingress状态..."
    
    local ingresses=$(kubectl get ingress -n "$NAMESPACE" --no-headers 2>/dev/null || true)
    if [[ -z "$ingresses" ]]; then
        check_result "Ingress检查" "FAIL" "无法获取Ingress列表"
        return
    fi
    
    while IFS= read -r ingress_line; do
        if [[ -n "$ingress_line" ]]; then
            local ingress_name=$(echo "$ingress_line" | awk '{print $1}')
            local ingress_class=$(echo "$ingress_line" | awk '{print $2}')
            local ingress_hosts=$(echo "$ingress_line" | awk '{print $3}')
            local ingress_address=$(echo "$ingress_line" | awk '{print $4}')
            
            if [[ -n "$ingress_address" && "$ingress_address" != "<none>" ]]; then
                check_result "Ingress $ingress_name" "PASS" "类: $ingress_class, 主机: $ingress_hosts, 地址: $ingress_address"
            else
                check_result "Ingress $ingress_name" "WARN" "类: $ingress_class, 主机: $ingress_hosts, 无外部地址"
            fi
        fi
    done <<< "$ingresses"
}

# 检查API服务健康端点
check_api_health() {
    log_info "检查API服务健康端点..."
    
    local api_url=$(kubectl get ingress athena-ingress -n "$NAMESPACE" -o jsonpath='{.spec.rules[0].host}' 2>/dev/null || echo "")
    
    if [[ -z "$api_url" ]]; then
        check_result "API健康检查" "FAIL" "无法获取API URL"
        return
    fi
    
    # 检查健康端点
    if curl -s --max-time 10 "https://$api_url/health" | grep -q "healthy\|ok"; then
        check_result "API健康端点" "PASS" "https://$api_url/health 响应正常"
    else
        check_result "API健康端点" "FAIL" "https://$api_url/health 无响应或异常"
    fi
    
    # 检查状态端点
    if curl -s --max-time 10 "https://$api_url/api/v1/status" | grep -q "status\|healthy"; then
        check_result "API状态端点" "PASS" "https://$api_url/api/v1/status 响应正常"
    else
        check_result "API状态端点" "FAIL" "https://$api_url/api/v1/status 无响应或异常"
    fi
}

# 检查数据库连接
check_database() {
    log_info "检查数据库连接..."
    
    # 检查PostgreSQL Pod
    local postgres_pod=$(kubectl get pods -n "$NAMESPACE" -l component=postgres --no-headers | awk 'NR==1{print $1}')
    
    if [[ -n "$postgres_pod" ]]; then
        # 检查PostgreSQL连接
        if kubectl exec -n "$NAMESPACE" "$postgres_pod" -- pg_isready -U athena_user -d athena_prod &> /dev/null; then
            check_result "PostgreSQL连接" "PASS" "数据库连接正常"
            
            # 检查数据库大小
            local db_size=$(kubectl exec -n "$NAMESPACE" "$postgres_pod" -- psql -U athena_user -d athena_prod -tAc "SELECT pg_size_pretty(pg_database_size('athena_prod'));")
            check_result "PostgreSQL状态" "PASS" "数据库大小: $db_size"
        else
            check_result "PostgreSQL连接" "FAIL" "无法连接到数据库"
        fi
    else
        check_result "PostgreSQL检查" "FAIL" "PostgreSQL Pod未找到"
    fi
}

# 检查Redis连接
check_redis() {
    log_info "检查Redis连接..."
    
    local redis_pod=$(kubectl get pods -n "$NAMESPACE" -l component=redis --no-headers | awk 'NR==1{print $1}')
    
    if [[ -n "$redis_pod" ]]; then
        # 检查Redis连接
        if kubectl exec -n "$NAMESPACE" "$redis_pod" -- redis-cli ping &> /dev/null; then
            check_result "Redis连接" "PASS" "Redis服务响应正常"
            
            # 检查Redis内存使用
            local redis_memory=$(kubectl exec -n "$NAMESPACE" "$redis_pod" -- redis-cli info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
            check_result "Redis状态" "PASS" "内存使用: $redis_memory"
        else
            check_result "Redis连接" "FAIL" "无法连接到Redis"
        fi
    else
        check_result "Redis检查" "FAIL" "Redis Pod未找到"
    fi
}

# 检查Qdrant向量数据库
check_qdrant() {
    log_info "检查Qdrant向量数据库..."
    
    local qdrant_pod=$(kubectl get pods -n "$NAMESPACE" -l component=qdrant --no-headers | awk 'NR==1{print $1}')
    
    if [[ -n "$qdrant_pod" ]]; then
        # 检查Qdrant健康端点
        local qdrant_health=$(kubectl exec -n "$NAMESPACE" "$qdrant_pod" -- curl -s http://localhost:6333/health 2>/dev/null || echo "")
        
        if echo "$qdrant_health" | grep -q "ok\|true"; then
            check_result "Qdrant健康" "PASS" "Qdrant服务响应正常"
            
            # 检查集合状态
            local collections=$(kubectl exec -n "$NAMESPACE" "$qdrant_pod" -- curl -s http://localhost:6333/collections 2>/dev/null | jq -r '.result.collections | length' 2>/dev/null || echo "0")
            check_result "Qdrant集合" "PASS" "集合数量: $collections"
        else
            check_result "Qdrant健康" "FAIL" "Qdrant服务无响应"
        fi
    else
        check_result "Qdrant检查" "FAIL" "Qdrant Pod未找到"
    fi
}

# 检查监控系统
check_monitoring() {
    log_info "检查监控系统..."
    
    # 检查Prometheus
    local prometheus_pod=$(kubectl get pods -n athena-monitoring -l app.kubernetes.io/name=prometheus --no-headers | awk 'NR==1{print $1}')
    
    if [[ -n "$prometheus_pod" ]]; then
        # 端口转发到本地进行测试
        kubectl port-forward -n athena-monitoring "$prometheus_pod" 9090:9090 &> /dev/null &
        local port_forward_pid=$!
        
        sleep 5
        
        if curl -s http://localhost:9090/-/healthy | grep -q "Prometheus"; then
            check_result "Prometheus监控" "PASS" "Prometheus服务正常"
        else
            check_result "Prometheus监控" "FAIL" "Prometheus服务异常"
        fi
        
        # 清理端口转发
        kill $port_forward_pid 2>/dev/null || true
    else
        check_result "Prometheus检查" "WARN" "Prometheus Pod未找到"
    fi
    
    # 检查Grafana
    local grafana_pod=$(kubectl get pods -n athena-monitoring -l app.kubernetes.io/name=grafana --no-headers | awk 'NR==1{print $1}')
    
    if [[ -n "$grafana_pod" ]]; then
        kubectl port-forward -n athena-monitoring "$grafana_pod" 3000:3000 &> /dev/null &
        local port_forward_pid=$!
        
        sleep 5
        
        if curl -s http://localhost:3000/api/health | grep -q "ok"; then
            check_result "Grafana监控" "PASS" "Grafana服务正常"
        else
            check_result "Grafana监控" "FAIL" "Grafana服务异常"
        fi
        
        # 清理端口转发
        kill $port_forward_pid 2>/dev/null || true
    else
        check_result "Grafana检查" "WARN" "Grafana Pod未找到"
    fi
}

# 检查资源使用情况
check_resource_usage() {
    log_info "检查资源使用情况..."
    
    # 检查节点资源
    local nodes_info=$(kubectl top nodes --no-headers 2>/dev/null || true)
    if [[ -n "$nodes_info" ]]; then
        while IFS= read -r node_line; do
            if [[ -n "$node_line" ]]; then
                local node_name=$(echo "$node_line" | awk '{print $1}')
                local cpu_usage=$(echo "$node_line" | awk '{print $2}')
                local memory_usage=$(echo "$node_line" | awk '{print $4}')
                
                check_result "节点 $node_name 资源" "INFO" "CPU: $cpu_usage, 内存: $memory_usage"
            fi
        done <<< "$nodes_info"
    fi
    
    # 检查Pod资源
    local pods_info=$(kubectl top pods -n "$NAMESPACE" --no-headers 2>/dev/null || true)
    if [[ -n "$pods_info" ]]; then
        while IFS= read -r pod_line; do
            if [[ -n "$pod_line" ]]; then
                local pod_name=$(echo "$pod_line" | awk '{print $1}')
                local cpu_usage=$(echo "$pod_line" | awk '{print $2}')
                local memory_usage=$(echo "$pod_line" | awk '{print $3}')
                
                check_result "Pod $pod_name 资源" "INFO" "CPU: $cpu_usage, 内存: $memory_usage"
            fi
        done <<< "$pods_info"
    fi
}

# 检查日志错误
check_logs() {
    log_info "检查最近日志错误..."
    
    local pods=$(kubectl get pods -n "$NAMESPACE" --no-headers | awk '{print $1}')
    
    while IFS= read -r pod_name; do
        if [[ -n "$pod_name" ]]; then
            # 检查最近5分钟内的错误日志
            local error_count=$(kubectl logs -n "$NAMESPACE" "$pod_name" --since=5m 2>&1 | grep -c "ERROR\|FATAL\|CRITICAL" || echo "0")
            
            if (( error_count > 5 )); then
                check_result "Pod $pod_name 日志" "WARN" "发现 $error_count 个错误日志"
            else
                check_result "Pod $pod_name 日志" "PASS" "错误日志数量正常 ($error_count)"
            fi
        fi
    done <<< "$pods"
}

# 生成健康检查报告
generate_report() {
    log_info "生成健康检查报告..."
    
    echo ""
    echo "==================================="
    echo "Athena工作平台健康检查报告"
    echo "==================================="
    echo "检查时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "环境: $ENVIRONMENT"
    echo "命名空间: $NAMESPACE"
    echo ""
    echo "检查统计:"
    echo "- 总检查项: $TOTAL_CHECKS"
    echo "- 通过检查: $PASSED_CHECKS"
    echo "- 失败检查: $FAILED_CHECKS"
    echo "- 成功率: $(( PASSED_CHECKS * 100 / TOTAL_CHECKS ))%"
    echo ""
    
    if (( FAILED_CHECKS == 0 )); then
        echo -e "${GREEN}✅ 系统状态良好！${NC}"
        exit 0
    elif (( FAILED_CHECKS <= 3 )); then
        echo -e "${YELLOW}⚠️  系统存在轻微问题，建议关注${NC}"
        exit 1
    else
        echo -e "${RED}❌ 系统存在严重问题，需要立即处理${NC}"
        exit 2
    fi
}

# 主函数
main() {
    local start_time=$(date +%s)
    
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  Athena工作平台健康检查                                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    log_info "开始健康检查..."
    echo ""
    
    # 执行各项检查
    check_kubernetes_cluster
    check_namespaces
    check_pods
    check_services
    check_ingress
    check_api_health
    check_database
    check_redis
    check_qdrant
    check_monitoring
    check_resource_usage
    check_logs
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo ""
    log_info "健康检查完成！总用时：${duration}秒"
    
    # 生成报告
    generate_report
}

# 显示使用帮助
show_help() {
    echo "Athena工作平台健康检查脚本"
    echo ""
    echo "用法: $0 [选项] [环境] [超时秒数]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -v, --verbose  详细输出"
    echo ""
    echo "参数:"
    echo "  环境          deployment 或 production (默认: production)"
    echo "  超时秒数      健康检查超时时间 (默认: 60)"
    echo ""
    echo "示例:"
    echo "  $0                 # 检查生产环境"
    echo "  $0 development     # 检查开发环境"
    echo "  $0 production 120 # 检查生产环境，超时120秒"
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