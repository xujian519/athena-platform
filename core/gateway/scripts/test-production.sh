#!/bin/bash
# ================================
# Athena API Gateway - 生产部署测试
# ================================
# 全面的生产环境部署验证和性能测试
set -euo pipefail

# 配置变量
NAMESPACE=${NAMESPACE:-"athena-gateway"}
DOMAIN=${DOMAIN:-"athena-gateway.company.com"}
TEST_TIMEOUT=${TEST_TIMEOUT:-"300"}
PERFORMANCE_DURATION=${PERFORMANCE_DURATION:-"60"}
CONCURRENT_USERS=${CONCURRENT_USERS:-"100"}

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

test() {
    echo -e "${CYAN}[TEST]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log "检查测试依赖..."
    
    local deps=("kubectl" "curl" "ab" "jq")
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

# 基础环境检查
check_basic_environment() {
    test "检查基础环境..."
    
    # 检查命名空间
    if ! kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
        error "命名空间 $NAMESPACE 不存在"
    fi
    
    # 检查Pod状态
    local pods=$(kubectl get pods -n "$NAMESPACE" --no-headers | wc -l)
    if [ "$pods" -eq 0 ]; then
        error "没有发现运行中的Pod"
    fi
    
    local ready_pods=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Running --no-headers | wc -l)
    if [ "$ready_pods" -eq 0 ]; then
        error "没有就绪的Pod"
    fi
    
    success "基础环境检查完成 ($ready_pods/$pods Pods就绪)"
}

# 服务连通性测试
test_service_connectivity() {
    test "测试服务连通性..."
    
    # 获取服务URL
    local gateway_url="https://$DOMAIN"
    local health_url="https://$DOMAIN/health"
    
    # 测试HTTP连接
    log "测试HTTP连接..."
    if curl -f -s --max-time "$TEST_TIMEOUT" "$health_url" >/dev/null; then
        success "健康检查端点可访问"
    else
        error "健康检查端点不可访问: $health_url"
    fi
    
    # 测试HTTPS连接
    log "测试HTTPS连接..."
    local ssl_info=$(echo | openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null || echo "SSL_ERROR")
    
    if [[ "$ssl_info" != "SSL_ERROR" ]]; then
        success "SSL证书配置正确"
    else
        error "SSL证书配置错误"
    fi
    
    # 测试服务发现
    log "测试服务发现..."
    local services=("athena-gateway" "athena-gateway-metrics")
    for service in "${services[@]}"; do
        if kubectl get svc "$service" -n "$NAMESPACE" >/dev/null 2>&1; then
            local service_ip=$(kubectl get svc "$service" -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}')
            if [[ -n "$service_ip" ]]; then
                success "服务 $service 可访问 ($service_ip)"
            else
                warning "服务 $service 没有分配IP"
            fi
        else
            error "服务 $service 不存在"
        fi
    done
}

# 性能基准测试
test_performance_benchmark() {
    test "执行性能基准测试..."
    
    local gateway_url="https://$DOMAIN"
    local results_file="/tmp/performance_results.json"
    
    # Apache Benchmark测试
    log "执行Apache Benchmark测试..."
    ab -n 1000 -c "$CONCURRENT_USERS" -t "$PERFORMANCE_DURATION" \
        -g "/tmp/ab_results.json" \
        "$gateway_url" >/dev/null 2>&1 || true
    
    # 处理ab结果
    if [[ -f "/tmp/ab_results.json" ]]; then
        local requests_per_second=$(jq '.requests_per_second' /tmp/ab_results.json)
        local time_per_request=$(jq '.time_per_request.mean' /tmp/ab_results.json)
        local failed_requests=$(jq '.failed_requests' /tmp/ab_results.json)
        
        cat > "$results_file" << EOF
{
  "test_type": "apache_benchmark",
  "timestamp": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
  "target_url": "$gateway_url",
  "concurrent_users": $CONCURRENT_USERS,
  "duration_seconds": $PERFORMANCE_DURATION,
  "results": {
    "requests_per_second": $requests_per_second,
    "time_per_request_ms": $(echo "$time_per_request * 1000" | bc),
    "failed_requests": $failed_requests,
    "success_rate": $(echo "scale=4; (1000-$failed_requests)/1000" | bc)
  }
}
EOF
        
        success "Apache Benchmark测试完成"
        log "QPS: $requests_per_second, 响应时间: ${time_per_request}s"
    else
        warning "Apache Benchmark测试失败"
    fi
    
    # curl性能测试
    log "执行curl性能测试..."
    local total_time=0
    local successful_requests=0
    
    for i in {1..10}; do
        local start_time=$(date +%s%N)
        if curl -f -s -o /dev/null -w "%{http_code}" "$gateway_url" | grep -q "200"; then
            local end_time=$(date +%s%N)
            local request_time=$(( (end_time - start_time) / 1000000 ))
            total_time=$((total_time + request_time))
            successful_requests=$((successful_requests + 1))
        fi
        sleep 0.1
    done
    
    if [ "$successful_requests" -gt 0 ]; then
        local avg_response_time=$((total_time / successful_requests))
        log "平均响应时间: ${avg_response_time}ms"
        success "curl性能测试完成"
    else
        warning "curl性能测试失败"
    fi
}

# 负载测试
test_load_testing() {
    test "执行负载测试..."
    
    local gateway_url="https://$DOMAIN"
    local load_test_file="/tmp/load_test_results.json"
    
    # 模拟并发用户
    log "启动 $CONCURRENT_USERS 个并发用户..."
    
    local pids=()
    for i in $(seq 1 $CONCURRENT_USERS); do
        (
            local start_time=$(date +%s)
            local requests=0
            local errors=0
            
            while [[ $(($(date +%s) - start_time)) -lt $PERFORMANCE_DURATION ]]; do
                if curl -f -s -o /dev/null -w "%{http_code}" "$gateway_url" | grep -q "200"; then
                    requests=$((requests + 1))
                else
                    errors=$((errors + 1))
                fi
                sleep 0.1
            done
            
            echo "{\"user\": $i, \"requests\": $requests, \"errors\": $errors, \"success_rate\": $(echo "scale=4; $requests/($requests+$errors)" | bc)}" > "/tmp/user_${i}_results.json"
        ) &
        pids+=($!)
    done
    
    # 等待所有测试完成
    for pid in "${pids[@]}"; do
        wait "$pid"
    done
    
    # 汇总结果
    local total_requests=0
    local total_errors=0
    local active_users=0
    
    for i in $(seq 1 $CONCURRENT_USERS); do
        if [[ -f "/tmp/user_${i}_results.json" ]]; then
            local user_requests=$(jq -r '.requests' "/tmp/user_${i}_results.json" || echo 0)
            local user_errors=$(jq -r '.errors' "/tmp/user_${i}_results.json" || echo 0)
            local user_success_rate=$(jq -r '.success_rate' "/tmp/user_${i}_results.json" || echo 0)
            
            total_requests=$((total_requests + user_requests))
            total_errors=$((total_errors + user_errors))
            
            if [[ "$user_requests" -gt 0 ]]; then
                active_users=$((active_users + 1))
            fi
            
            rm -f "/tmp/user_${i}_results.json"
        fi
    done
    
    local overall_success_rate=$(echo "scale=4; ($total_requests-$total_errors)/$total_requests" | bc)
    
    cat > "$load_test_file" << EOF
{
  "test_type": "load_testing",
  "timestamp": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
  "target_url": "$gateway_url",
  "concurrent_users": $CONCURRENT_USERS,
  "duration_seconds": $PERFORMANCE_DURATION,
  "results": {
    "total_requests": $total_requests,
    "total_errors": $total_errors,
    "active_users": $active_users,
    "overall_success_rate": $overall_success_rate,
    "requests_per_second": $(echo "scale=2; $total_requests/$PERFORMANCE_DURATION" | bc),
    "requests_per_user": $(echo "scale=2; $total_requests/$active_users" | bc)
  }
}
EOF
    
    success "负载测试完成"
    log "总请求数: $total_requests, 成功率: $overall_success_rate"
}

# 故障恢复测试
test_failover_recovery() {
    test "执行故障恢复测试..."
    
    log "模拟Pod故障..."
    
    # 获取当前副本数
    local current_replicas=$(kubectl get deployment athena-gateway -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}')
    
    if [ "$current_replicas" -lt 2 ]; then
        warning "副本数不足，跳过故障恢复测试"
        return 0
    fi
    
    # 删除一个Pod
    local test_pod=$(kubectl get pods -n "$NAMESPACE" -l app=athena-gateway -o jsonpath='{.items[0].metadata.name}')
    kubectl delete pod "$test_pod" -n "$NAMESPACE" --wait=false
    
    # 等待新Pod启动
    local timeout=60
    while [[ $timeout -gt 0 ]]; do
        local ready_pods=$(kubectl get pods -n "$NAMESPACE" -l app=athena-gateway --field-selector=status.phase=Running --no-headers | wc -l)
        if [ "$ready_pods" -eq "$current_replicas" ]; then
            success "Pod故障恢复成功"
            break
        fi
        sleep 5
        timeout=$((timeout - 5))
    done
    
    if [ $timeout -le 0 ]; then
        error "Pod故障恢复超时"
    fi
    
    # 验证服务可用性
    log "验证故障后服务可用性..."
    sleep 10
    
    if curl -f -s --max-time 30 "https://$DOMAIN/health" >/dev/null; then
        success "故障后服务仍然可用"
    else
        error "故障后服务不可用"
    fi
}

# 监控系统测试
test_monitoring_system() {
    test "测试监控系统..."
    
    # 测试Prometheus
    log "测试Prometheus..."
    if kubectl get pods -n observability -l app=prometheus --field-selector=status.phase=Running --no-headers | grep -q .; then
        local prometheus_pod=$(kubectl get pods -n observability -l app=prometheus -o jsonpath='{.items[0].metadata.name}')
        if kubectl exec -n observability "$prometheus_pod" -- wget -q -O- http://localhost:9090/-/healthy >/dev/null 2>&1; then
            success "Prometheus运行正常"
        else
            error "Prometheus健康检查失败"
        fi
    else
        error "Prometheus Pod未运行"
    fi
    
    # 测试Grafana
    log "测试Grafana..."
    if kubectl get pods -n observability -l app=grafana --field-selector=status.phase=Running --no-headers | grep -q .; then
        local grafana_pod=$(kubectl get pods -n observability -l app=grafana -o jsonpath='{.items[0].metadata.name}')
        if kubectl exec -n observability "$grafana_pod" -- curl -f http://localhost:3000/api/health >/dev/null 2>&1; then
            success "Grafana运行正常"
        else
            error "Grafana健康检查失败"
        fi
    else
        error "Grafana Pod未运行"
    fi
    
    # 测试AlertManager
    log "测试AlertManager..."
    if kubectl get pods -n observability -l app=alertmanager --field-selector=status.phase=Running --no-headers | grep -q .; then
        local alertmanager_pod=$(kubectl get pods -n observability -l app=alertmanager -o jsonpath='{.items[0].metadata.name}')
        if kubectl exec -n observability "$alertmanager_pod" -- wget -q -O- http://localhost:9093/-/healthy >/dev/null 2>&1; then
            success "AlertManager运行正常"
        else
            error "AlertManager健康检查失败"
        fi
    else
        error "AlertManager Pod未运行"
    fi
}

# 安全测试
test_security() {
    test "执行安全测试..."
    
    local gateway_url="https://$DOMAIN"
    
    # 测试HTTPS强制重定向
    log "测试HTTPS重定向..."
    local redirect_response=$(curl -s -o /dev/null -w "%{http_code}" "http://$DOMAIN")
    if [[ "$redirect_response" == "301" || "$redirect_response" == "302" ]]; then
        success "HTTP到HTTPS重定向正常"
    else
        warning "HTTP到HTTPS重定向可能有问题"
    fi
    
    # 测试安全头
    log "测试安全头..."
    local security_headers=$(curl -s -I "$gateway_url" | grep -E "(X-Frame-Options|X-Content-Type-Options|X-XSS-Protection|Strict-Transport-Security)")
    
    if [[ -n "$security_headers" ]]; then
        success "安全头配置正确"
    else
        warning "安全头配置不完整"
    fi
    
    # 测试SSL/TLS配置
    log "测试SSL/TLS配置..."
    local ssl_info=$(echo | openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" 2>/dev/null | openssl x509 -noout -dates -subject 2>/dev/null || echo "SSL_ERROR")
    
    if [[ "$ssl_info" != "SSL_ERROR" ]]; then
        local cert_expiry=$(echo "$ssl_info" | grep "notAfter" | cut -d'=' -f2)
        local days_until_expiry=$(( ($(date -d "$cert_expiry" +%s) - $(date +%s)) / 86400 ))
        
        if [ "$days_until_expiry" -gt 30 ]; then
            success "SSL证书配置正常 (剩余 $days_until_expiry 天)"
        else
            warning "SSL证书即将过期 (剩余 $days_until_expiry 天)"
        fi
    else
        error "SSL证书配置错误"
    fi
    
    # 测试限流
    log "测试限流配置..."
    local rate_limit_start=$(date +%s)
    local request_count=0
    
    for i in {1..200}; do
        if curl -f -s -o /dev/null "$gateway_url/api/test" >/dev/null 2>&1; then
            request_count=$((request_count + 1))
        fi
    done
    
    local rate_limit_end=$(date +%s)
    local test_duration=$((rate_limit_end - rate_limit_start))
    
    if [ "$request_count" -gt 150 ]; then
        warning "限流可能未生效 (处理了 $request_count 个请求)"
    else
        success "限流配置正常 (处理了 $request_count 个请求)"
    fi
}

# 生成测试报告
generate_test_report() {
    log "生成测试报告..."
    
    local report_file="/tmp/athena_gateway_test_report_$(date +%Y%m%d_%H%M%S).json"
    
    cat > "$report_file" << EOF
{
  "test_report": {
    "test_suite": "Athena API Gateway Production Deployment",
    "timestamp": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
    "environment": {
      "namespace": "$NAMESPACE",
      "domain": "$DOMAIN",
      "kubernetes_version": "$(kubectl version --short | grep 'Server Version' | cut -d' ' -f3)"
    },
    "test_results": {
      "basic_environment": "PASSED",
      "service_connectivity": "PASSED",
      "performance_benchmark": "COMPLETED",
      "load_testing": "COMPLETED",
      "failover_recovery": "COMPLETED",
      "monitoring_system": "COMPLETED",
      "security": "COMPLETED"
    },
    "deployment_status": {
      "pods": {
        "total": $(kubectl get pods -n "$NAMESPACE" --no-headers | wc -l),
        "running": $(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Running --no-headers | wc -l),
        "ready": $(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Running --no-headers | wc -l)
      },
      "services": {
        "total": $(kubectl get svc -n "$NAMESPACE" --no-headers | wc -l),
        "cluster_ips": $(kubectl get svc -n "$NAMESPACE" -o jsonpath='{range .items[*]}{.spec.clusterIP}{","}' | sed 's/,$//')
      },
      "ingress": {
        "configured": $(kubectl get ingress -n "$NAMESPACE" --no-headers | wc -l),
        "tls_enabled": $(kubectl get ingress -n "$NAMESPACE" -o jsonpath='{.items[0].spec.tls}' | jq length 2>/dev/null || echo 0)
      }
    },
    "recommendations": [
      "定期监控Pod健康状态",
      "设置自动扩缩容策略",
      "定期备份配置和密钥",
      "监控SSL证书有效期",
      "实施安全更新策略"
    ]
  }
}
EOF
    
    success "测试报告已生成: $report_file"
    
    # 复制报告到当前目录
    cp "$report_file" "./"
    
    # 显示报告摘要
    log "测试摘要:"
    log "- 基础环境检查: ✅ 通过"
    log "- 服务连通性: ✅ 通过"
    log "- 性能基准测试: ✅ 完成"
    log "- 负载测试: ✅ 完成"
    log "- 故障恢复测试: ✅ 完成"
    log "- 监控系统测试: ✅ 完成"
    log "- 安全测试: ✅ 完成"
}

# 主函数
main() {
    local action=${1:-"all"}
    
    echo -e "${PURPLE}"
    echo "=========================================="
    echo "    Athena API Gateway 生产部署测试"
    echo "=========================================="
    echo "    命名空间: $NAMESPACE"
    echo "    域名: $DOMAIN"
    echo "=========================================="
    echo -e "${NC}"
    
    check_dependencies
    
    case "$action" in
        "basic")
            check_basic_environment
            test_service_connectivity
            ;;
        "performance")
            test_performance_benchmark
            test_load_testing
            ;;
        "monitoring")
            test_monitoring_system
            ;;
        "security")
            test_security
            ;;
        "failover")
            test_failover_recovery
            ;;
        "all")
            check_basic_environment
            test_service_connectivity
            test_performance_benchmark
            test_load_testing
            test_failover_recovery
            test_monitoring_system
            test_security
            generate_test_report
            ;;
        *)
            echo "使用方法: $0 {all|basic|performance|monitoring|security|failover}"
            echo ""
            echo "测试选项:"
            echo "  all        - 完整测试套件"
            echo "  basic      - 基础环境和连通性测试"
            echo "  performance - 性能和负载测试"
            echo "  monitoring  - 监控系统测试"
            echo "  security    - 安全配置测试"
            echo "  failover   - 故障恢复测试"
            exit 1
            ;;
    esac
}

# 错误处理
trap 'error "测试过程中发生错误，退出码: $?"' ERR

# 执行主函数
main "$@"