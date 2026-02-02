#!/bin/bash
# 生产环境验证脚本
# Production Environment Verification Script

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
VERIFICATION_REPORT="${PROJECT_ROOT}/logs/verification_report_$(date +%Y%m%d_%H%M%S).json"
DOMAIN="athena.multimodal.ai"
TEST_TIMEOUT=30

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

log_test() {
    echo -e "${PURPLE}[TEST]${NC} $1"
}

# 验证结果记录
declare -A VERIFICATION_RESULTS
TEST_COUNT=0
PASS_COUNT=0
FAIL_COUNT=0

# 记录测试结果
record_result() {
    local test_name=$1
    local status=$2
    local details=$3

    TEST_COUNT=$((TEST_COUNT + 1))
    VERIFICATION_RESULTS["$test_name"]="$status|$details"

    if [ "$status" = "PASS" ]; then
        PASS_COUNT=$((PASS_COUNT + 1))
        log_success "✓ $test_name - $details"
    else
        FAIL_COUNT=$((FAIL_COUNT + 1))
        log_error "✗ $test_name - $details"
    fi
}

# 显示验证横幅
show_banner() {
    echo -e "${CYAN}"
    echo "========================================================"
    echo "    🔍 Athena多模态文件系统生产环境验证"
    echo "========================================================"
    echo -e "${NC}"
    echo -e "${BLUE}验证信息:${NC}"
    echo -e "  📅 开始时间: $(date)"
    echo -e "  🌐 域名: ${YELLOW}${DOMAIN}${NC}"
    echo -e "  📋 报告文件: ${YELLOW}${VERIFICATION_REPORT}${NC}"
    echo ""
}

# 系统环境验证
verify_system_environment() {
    log_test "系统环境验证"

    # 检查操作系统
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macOS"
        VERSION=$(sw_vers -productVersion)
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="Linux"
        VERSION=$(uname -r)
    else
        OS="Unknown"
        VERSION="Unknown"
    fi

    # 检查Docker
    if docker info >/dev/null 2>&1; then
        DOCKER_VERSION=$(docker --version | awk '{print $3}')
        DOCKER_STATUS="running"
    else
        DOCKER_VERSION="Not Available"
        DOCKER_STATUS="stopped"
    fi

    # 检查磁盘空间
    DISK_AVAILABLE=$(df -BG "$PROJECT_ROOT" | awk 'NR==2 {print $4}' | sed 's/G//')
    DISK_TOTAL=$(df -BG "$PROJECT_ROOT" | awk 'NR==2 {print $2}' | sed 's/G//')

    # 检查内存
    if [[ "$OSTYPE" == "darwin"* ]]; then
        MEMORY_TOTAL=$(sysctl -n hw.memsize | awk '{print int($1/1024/1024/1024)}')
    else
        MEMORY_TOTAL=$(free -g | awk '/^Mem:/{print $2}')
    fi

    details="OS: $OS $VERSION, Docker: $DOCKER_VERSION ($DOCKER_STATUS), Disk: ${DISK_AVAILABLE}GB/${DISK_TOTAL}GB, Memory: ${MEMORY_TOTAL}GB"

    if [ "$DOCKER_STATUS" = "running" ] && [ "$DISK_AVAILABLE" -gt 5 ]; then
        record_result "system_environment" "PASS" "$details"
    else
        record_result "system_environment" "FAIL" "$details"
    fi
}

# Docker容器验证
verify_docker_containers() {
    log_test "Docker容器状态验证"

    cd "$PROJECT_ROOT/docker"

    # 检查容器状态
    containers=(
        "athena-api-gateway-1"
        "athena-api-gateway-2"
        "athena-api-gateway-3"
        "athena-dolphin-parser-1"
        "athena-dolphin-parser-2"
        "athena-glm-vision-1"
        "athena-glm-vision-2"
        "athena-multimodal-processor-1"
        "athena-xiao-nuo-control"
        "athena-athena-platform-manager"
        "athena-platform-monitor"
        "athena-nginx-lb"
        "athena-postgres-primary"
        "athena-postgres-replica"
        "athena-redis-cluster"
        "athena-redis-cache"
        "athena-qdrant"
    )

    running_containers=0
    total_containers=${#containers[@]}

    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "$container"; then
            running_containers=$((running_containers + 1))
        fi
    done

    details="运行容器: $running_containers/$total_containers"

    if [ "$running_containers" -eq $total_containers ]; then
        record_result "docker_containers" "PASS" "$details"
    else
        record_result "docker_containers" "FAIL" "$details"
    fi
}

# 服务健康检查
verify_service_health() {
    log_test "服务健康状态验证"

    services=(
        "API网关:8020:/health"
        "Dolphin解析器:8013:/health"
        "GLM视觉:8091:/health"
        "多模态处理器:8012:/"
        "小诺控制:9001:/health"
        "Athena平台:9000:/health"
        "平台监控:9090:/health"
    )

    healthy_services=0
    total_services=${#services[@]}

    for service_info in "${services[@]}"; do
        service_name=$(echo $service_info | cut -d':' -f1)
        port=$(echo $service_info | cut -d':' -f2)
        path=$(echo $service_info | cut -d':' -f3)

        if curl -f --max-time "$TEST_TIMEOUT" "http://localhost:$port$path" >/dev/null 2>&1; then
            healthy_services=$((healthy_services + 1))
        fi
    done

    details="健康服务: $healthy_services/$total_services"

    if [ "$healthy_services" -eq $total_services ]; then
        record_result "service_health" "PASS" "$details"
    else
        record_result "service_health" "FAIL" "$details"
    fi
}

# 数据库连接验证
verify_database_connection() {
    log_test "数据库连接验证"

    # 检查PostgreSQL主节点
    if docker exec athena-postgres-primary pg_isready -U athenu_user -d athena_production >/dev/null 2>&1; then
        postgres_primary_status="connected"
    else
        postgres_primary_status="disconnected"
    fi

    # 检查PostgreSQL从节点
    if docker exec athena-postgres-replica pg_isready -U athenu_user -d athena_production >/dev/null 2>&1; then
        postgres_replica_status="connected"
    else
        postgres_replica_status="disconnected"
    fi

    # 检查Redis集群
    if docker exec athena-redis-cluster redis-cli ping | grep -q PONG; then
        redis_cluster_status="connected"
    else
        redis_cluster_status="disconnected"
    fi

    # 检查Redis缓存
    if docker exec athena-redis-cache redis-cli ping | grep -q PONG; then
        redis_cache_status="connected"
    else
        redis_cache_status="disconnected"
    fi

    details="PostgreSQL主节点: $postgres_primary_status, PostgreSQL从节点: $postgres_replica_status, Redis集群: $redis_cluster_status, Redis缓存: $redis_cache_status"

    if [[ "$postgres_primary_status" == "connected" && "$redis_cluster_status" == "connected" ]]; then
        record_result "database_connection" "PASS" "$details"
    else
        record_result "database_connection" "FAIL" "$details"
    fi
}

# 监控系统验证
verify_monitoring_system() {
    log_test "监控系统验证"

    # 检查Prometheus
    if curl -f "http://localhost:9090/-/healthy" >/dev/null 2>&1; then
        prometheus_status="healthy"
    else
        prometheus_status="unhealthy"
    fi

    # 检查Grafana
    if curl -f "http://localhost:3000/api/health" >/dev/null 2>&1; then
        grafana_status="healthy"
    else
        grafana_status="unhealthy"
    fi

    # 检查AlertManager
    if curl -f "http://localhost:9093/-/healthy" >/dev/null 2>&1; then
        alertmanager_status="healthy"
    else
        alertmanager_status="unhealthy"
    fi

    # 检查Prometheus目标
    prometheus_targets=$(curl -s "http://localhost:9090/api/v1/targets" 2>/dev/null | jq -r '.data.activeTargets | length' || echo "0")

    details="Prometheus: $prometheus_status, Grafana: $grafana_status, AlertManager: $alertmanager_status, Targets: $prometheus_targets"

    if [[ "$prometheus_status" == "healthy" && "$grafana_status" == "healthy" ]]; then
        record_result "monitoring_system" "PASS" "$details"
    else
        record_result "monitoring_system" "FAIL" "$details"
    fi
}

# SSL证书验证
verify_ssl_certificate() {
    log_test "SSL证书验证"

    if [ -f "/etc/ssl/certs/${DOMAIN}.crt" ]; then
        cert_info=$(openssl x509 -in "/etc/ssl/certs/${DOMAIN}.crt" -noout -dates 2>/dev/null)
        if [ $? -eq 0 ]; then
            ssl_status="valid"
            ssl_details=$(echo "$cert_info" | tr '\n' ', ')
        else
            ssl_status="invalid"
            ssl_details="证书格式错误"
        fi
    else
        ssl_status="missing"
        ssl_details="证书文件不存在"
    fi

    details="SSL证书: $ssl_status, 详情: $ssl_details"

    if [ "$ssl_status" = "valid" ]; then
        record_result "ssl_certificate" "PASS" "$details"
    else
        record_result "ssl_certificate" "FAIL" "$details"
    fi
}

# API功能验证
verify_api_functionality() {
    log_test "API功能验证"

    # 测试API网关健康检查
    api_gateway_health=$(curl -s "http://localhost:8020/health" 2>/dev/null || echo "failed")

    # 测试小诺控制中心API
    xiaonuo_health=$(curl -s "http://localhost:9001/health" 2>/dev/null || echo "failed")

    # 测试Athena平台管理API
    athena_health=$(curl -s "http://localhost:9000/health" 2>/dev/null || echo "failed")

    # 测试平台监控API
    monitor_health=$(curl -s "http://localhost:9090/health" 2>/dev/null || echo "failed")

    # 测试API文档可访问性
    api_docs_status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8020/docs" 2>/dev/null || echo "000")

    details="API网关: $api_gateway_health, 小诺控制: $xiaonuo_health, Athena平台: $athena_health, 监控: $monitor_health, API文档: HTTP $api_docs_status"

    if [[ "$api_gateway_health" != "failed" && "$xiaonuo_health" != "failed" && "$athena_health" != "failed" && "$monitor_health" != "failed" ]]; then
        record_result "api_functionality" "PASS" "$details"
    else
        record_result "api_functionality" "FAIL" "$details"
    fi
}

# 性能基准验证
verify_performance_benchmark() {
    log_test "性能基准验证"

    # API响应时间测试
    api_response_time=$(curl -o /dev/null -s -w "%{time_total}" "http://localhost:8020/health" 2>/dev/null || echo "999")

    # 内存使用检查
    memory_usage=$(docker stats --no-stream --format "table {{.MemUsage}}" | grep athena | awk '{sum+=$1} END {print sum}' 2>/dev/null || echo "0")

    # CPU使用检查
    cpu_usage=$(docker stats --no-stream --format "table {{.CPUPerc}}" | grep athena | awk '{sum+=$1} END {print sum}' 2>/dev/null || echo "0")

    # 转换为数字
    api_response_time_num=$(echo "$api_response_time" | bc -l 2>/dev/null || echo "999")

    details="API响应时间: ${api_response_time}s, 内存使用: ${memory_usage}, CPU使用: ${cpu_usage}%"

    # API响应时间应该小于1秒
    if (( $(echo "$api_response_time_num < 1.0" | bc -l) )); then
        record_result "performance_benchmark" "PASS" "$details"
    else
        record_result "performance_benchmark" "FAIL" "$details"
    fi
}

# 安全配置验证
verify_security_configuration() {
    log_test "安全配置验证"

    # 检查防火墙状态
    if command -v ufw >/dev/null 2>&1; then
        firewall_status=$(ufw status | head -1)
    elif command -v firewall-cmd >/dev/null 2>&1; then
        firewall_status=$(firewall-cmd --state)
    else
        firewall_status="unknown"
    fi

    # 检查开放端口
    open_ports=$(netstat -tuln 2>/dev/null | grep LISTEN | grep -E ":(80|443|8020|9000|9001|9090)" | wc -l)

    # 检查SSL配置
    ssl_config=$(curl -s -o /dev/null -w "%{url_effective}" "http://localhost:8020/health" 2>/dev/null | grep -c "https" || echo "0")

    details="防火墙: $firewall_status, 开放端口: $open_ports, HTTPS重定向: $ssl_config"

    # 至少应该有基本的安全配置
    if [ "$open_ports" -gt 0 ]; then
        record_result "security_configuration" "PASS" "$details"
    else
        record_result "security_configuration" "FAIL" "$details"
    fi
}

# 日志系统验证
verify_logging_system() {
    log_test "日志系统验证"

    # 检查日志目录
    if [ -d "${PROJECT_ROOT}/logs" ]; then
        log_dir_status="exists"
        log_dir_size=$(du -sh "${PROJECT_ROOT}/logs" | cut -f1)
    else
        log_dir_status="missing"
        log_dir_size="0B"
    fi

    # 检查Docker日志
    docker_logs_size=$(docker system df --format "table {{.Type}}\t{{.Size}}" | grep "Local Volumes" | awk '{print $2}' 2>/dev/null || echo "0B")

    # 检查应用日志
    app_logs=0
    for service in api-gateway xiao-nuo-control athena-platform platform-monitor; do
        if docker logs "athena-$service" 2>/dev/null | grep -q "."; then
            app_logs=$((app_logs + 1))
        fi
    done

    details="日志目录: $log_dir_status ($log_dir_size), Docker日志: $docker_logs_size, 应用日志: $app_logs/4"

    if [ "$log_dir_status" = "exists" ] && [ "$app_logs" -gt 0 ]; then
        record_result "logging_system" "PASS" "$details"
    else
        record_result "logging_system" "FAIL" "$details"
    fi
}

# 备份系统验证
verify_backup_system() {
    log_test "备份系统验证"

    # 检查备份目录
    if [ -d "/data/athena/backups" ]; then
        backup_dir_status="exists"
        backup_count=$(find /data/athena/backups -name "*backup*" -type f 2>/dev/null | wc -l)
    else
        backup_dir_status="missing"
        backup_count=0
    fi

    # 检查备份脚本
    backup_script="${PROJECT_ROOT}/scripts/automated_backup.sh"
    if [ -f "$backup_script" ]; then
        backup_script_status="exists"
    else
        backup_script_status="missing"
    fi

    # 检查crontab
    if crontab -l 2>/dev/null | grep -q "automated_backup.sh"; then
        cron_status="configured"
    else
        cron_status="not configured"
    fi

    details="备份目录: $backup_dir_status, 备份文件: $backup_count, 备份脚本: $backup_script_status, 定时任务: $cron_status"

    if [ "$backup_dir_status" = "exists" ] && [ "$backup_script_status" = "exists" ]; then
        record_result "backup_system" "PASS" "$details"
    else
        record_result "backup_system" "FAIL" "$details"
    fi
}

# 生成验证报告
generate_verification_report() {
    log_test "生成验证报告"

    # 计算成功率
    if [ $TEST_COUNT -gt 0 ]; then
        success_rate=$((PASS_COUNT * 100 / TEST_COUNT))
    else
        success_rate=0
    fi

    # 生成JSON报告
    cat > "$VERIFICATION_REPORT" << EOF
{
    "verification": {
        "timestamp": "$(date -Iseconds)",
        "environment": "production",
        "domain": "$DOMAIN",
        "total_tests": $TEST_COUNT,
        "passed_tests": $PASS_COUNT,
        "failed_tests": $FAIL_COUNT,
        "success_rate": $success_rate,
        "status": "$([ $FAIL_COUNT -eq 0 ] && echo "PASS" || echo "FAIL")"
    },
    "results": {
EOF

    # 添加测试结果
    first=true
    for test_name in "${!VERIFICATION_RESULTS[@]}"; do
        if [ "$first" = false ]; then
            echo "," >> "$VERIFICATION_REPORT"
        fi
        first=false

        status=$(echo "${VERIFICATION_RESULTS[$test_name]}" | cut -d'|' -f1)
        details=$(echo "${VERIFICATION_RESULTS[$test_name]}" | cut -d'|' -f2-)

        cat >> "$VERIFICATION_REPORT" << EOF
        "$test_name": {
            "status": "$status",
            "details": "$details"
        }
EOF
    done

    cat >> "$VERIFICATION_REPORT" << EOF
    },
    "recommendations": [
        $([ $FAIL_COUNT -gt 0 ] && echo '"修复失败的测试项",')
        "配置监控告警通知",
        "设置定期备份验证",
        "实施性能监控",
        "配置安全扫描",
        "建立运维文档"
    ],
    "next_steps": [
        "部署到生产域名",
        "配置负载均衡",
        "设置SSL证书",
        "配置DNS解析",
        "配置监控告警",
        "执行压力测试",
        "建立运维流程"
    ]
}
EOF

    log_success "验证报告生成完成: $VERIFICATION_REPORT"
}

# 显示验证结果
show_verification_results() {
    echo ""
    echo -e "${CYAN}📊 验证结果汇总${NC}"
    echo "========================================"
    echo -e "总测试数: ${YELLOW}$TEST_COUNT${NC}"
    echo -e "通过测试: ${GREEN}$PASS_COUNT${NC}"
    echo -e "失败测试: ${RED}$FAIL_COUNT${NC}"

    if [ $TEST_COUNT -gt 0 ]; then
        success_rate=$((PASS_COUNT * 100 / TEST_COUNT))
        echo -e "成功率: ${YELLOW}${success_rate}%${NC}"
    fi
    echo ""

    # 显示详细结果
    echo -e "${CYAN}📋 详细测试结果${NC}"
    echo "----------------------------------------"
    for test_name in "${!VERIFICATION_RESULTS[@]}"; do
        status=$(echo "${VERIFICATION_RESULTS[$test_name]}" | cut -d'|' -f1)
        details=$(echo "${VERIFICATION_RESULTS[$test_name]}" | cut -d'|' -f2-)

        if [ "$status" = "PASS" ]; then
            echo -e "✅ ${GREEN}$test_name${NC}: $details"
        else
            echo -e "❌ ${RED}$test_name${NC}: $details"
        fi
    done
    echo ""

    # 显示建议
    echo -e "${CYAN}💡 改进建议${NC}"
    echo "----------------------------------------"
    if [ $FAIL_COUNT -gt 0 ]; then
        echo -e "1. ${RED}修复失败的测试项${NC}"
    fi
    echo "2. 配置监控告警通知"
    echo "3. 设置定期备份验证"
    echo "4. 实施性能监控"
    echo "5. 配置安全扫描"
    echo "6. 建立运维文档"
    echo ""

    # 显示报告文件位置
    echo -e "${CYAN}📄 报告文件${NC}"
    echo "----------------------------------------"
    echo -e "详细报告: ${YELLOW}$VERIFICATION_REPORT${NC}"
    echo ""
}

# 主函数
main() {
    show_banner

    # 执行所有验证测试
    verify_system_environment
    verify_docker_containers
    verify_service_health
    verify_database_connection
    verify_monitoring_system
    verify_ssl_certificate
    verify_api_functionality
    verify_performance_benchmark
    verify_security_configuration
    verify_logging_system
    verify_backup_system

    # 生成报告
    generate_verification_report
    show_verification_results

    # 返回适当的退出码
    if [ $FAIL_COUNT -eq 0 ]; then
        echo -e "${GREEN}🎉 所有验证测试通过！${NC}"
        exit 0
    else
        echo -e "${RED}❌ $FAIL_COUNT 个测试失败，请检查并修复${NC}"
        exit 1
    fi
}

# 执行主函数
main "$@"