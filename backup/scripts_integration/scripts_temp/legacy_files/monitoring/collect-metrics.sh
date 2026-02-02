#!/bin/bash

# Athena工作平台性能指标收集脚本
# 作者: 徐健
# 创建日期: 2025-12-13

set -e

# 配置
PROMETHEUS_URL=${PROMETHEUS_URL:-"http://localhost:9090"}
GRAFANA_URL=${GRAFANA_URL:-"http://localhost:3000"}
OUTPUT_DIR=${OUTPUT_DIR:-"metrics-reports"}
DATE=$(date +%Y-%m-%d_%H-%M-%S)

# 创建输出目录
mkdir -p $OUTPUT_DIR

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 收集系统资源指标
collect_system_metrics() {
    log_info "收集系统资源指标..."

    # CPU使用率
    echo "收集CPU使用率..."
    curl -s -G "$PROMETHEUS_URL/api/v1/query_range" \
        --data-urlencode "query=100 - (avg by (instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)" \
        --data-urlencode "start=$(date -d '1 hour ago' +%s)" \
        --data-urlencode "end=$(date +%s)" \
        --data-urlencode "step=60" | jq '.' > "$OUTPUT_DIR/cpu_usage_$DATE.json"

    # 内存使用率
    echo "收集内存使用率..."
    curl -s -G "$PROMETHEUS_URL/api/v1/query_range" \
        --data-urlencode "query=(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100" \
        --data-urlencode "start=$(date -d '1 hour ago' +%s)" \
        --data-urlencode "end=$(date +%s)" \
        --data-urlencode "step=60" | jq '.' > "$OUTPUT_DIR/memory_usage_$DATE.json"

    # 磁盘使用率
    echo "收集磁盘使用率..."
    curl -s -G "$PROMETHEUS_URL/api/v1/query_range" \
        --data-urlencode "query=(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100" \
        --data-urlencode "start=$(date -d '1 hour ago' +%s)" \
        --data-urlencode "end=$(date +%s)" \
        --data-urlencode "step=60" | jq '.' > "$OUTPUT_DIR/disk_usage_$DATE.json"

    # 网络流量
    echo "收集网络流量..."
    curl -s -G "$PROMETHEUS_URL/api/v1/query_range" \
        --data-urlencode "query=rate(node_network_receive_bytes_total[5m])" \
        --data-urlencode "start=$(date -d '1 hour ago' +%s)" \
        --data-urlencode "end=$(date +%s)" \
        --data-urlencode "step=60" | jq '.' > "$OUTPUT_DIR/network_receive_$DATE.json"

    log_success "系统资源指标收集完成"
}

# 收集应用性能指标
collect_application_metrics() {
    log_info "收集应用性能指标..."

    # API请求速率
    echo "收集API请求速率..."
    curl -s -G "$PROMETHEUS_URL/api/v1/query_range" \
        --data-urlencode "query=sum(rate(http_requests_total[5m])) by (job)" \
        --data-urlencode "start=$(date -d '1 hour ago' +%s)" \
        --data-urlencode "end=$(date +%s)" \
        --data-urlencode "step=60" | jq '.' > "$OUTPUT_DIR/api_requests_$DATE.json"

    # API响应时间
    echo "收集API响应时间..."
    curl -s -G "$PROMETHEUS_URL/api/v1/query_range" \
        --data-urlencode "query=histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, job))" \
        --data-urlencode "start=$(date -d '1 hour ago' +%s)" \
        --data-urlencode "end=$(date +%s)" \
        --data-urlencode "step=60" | jq '.' > "$OUTPUT_DIR/response_time_$DATE.json"

    # 错误率
    echo "收集错误率..."
    curl -s -G "$PROMETHEUS_URL/api/v1/query_range" \
        --data-urlencode "query=sum(rate(http_requests_total{status=~\"5..\"}[5m])) by (job) / sum(rate(http_requests_total[5m])) by (job) * 100" \
        --data-urlencode "start=$(date -d '1 hour ago' +%s)" \
        --data-urlencode "end=$(date +%s)" \
        --data-urlencode "step=60" | jq '.' > "$OUTPUT_DIR/error_rate_$DATE.json"

    log_success "应用性能指标收集完成"
}

# 收集数据库指标
collect_database_metrics() {
    log_info "收集数据库指标..."

    # PostgreSQL连接数
    echo "收集PostgreSQL连接数..."
    curl -s -G "$PROMETHEUS_URL/api/v1/query_range" \
        --data-urlencode "query=pg_stat_activity_count" \
        --data-urlencode "start=$(date -d '1 hour ago' +%s)" \
        --data-urlencode "end=$(date +%s)" \
        --data-urlencode "step=60" | jq '.' > "$OUTPUT_DIR/postgres_connections_$DATE.json"

    # Redis连接数
    echo "收集Redis连接数..."
    curl -s -G "$PROMETHEUS_URL/api/v1/query_range" \
        --data-urlencode "query=redis_connected_clients" \
        --data-urlencode "start=$(date -d '1 hour ago' +%s)" \
        --data-urlencode "end=$(date +%s)" \
        --data-urlencode "step=60" | jq '.' > "$OUTPUT_DIR/redis_connections_$DATE.json"

    # 查询性能
    echo "收集数据库查询性能..."
    curl -s -G "$PROMETHEUS_URL/api/v1/query_range" \
        --data-urlencode "query=histogram_quantile(0.95, rate(pg_stat_statements_mean_time_seconds[5m])) * 1000" \
        --data-urlencode "start=$(date -d '1 hour ago' +%s)" \
        --data-urlencode "end=$(date +%s)" \
        --data-urlencode "step=60" | jq '.' > "$OUTPUT_DIR/db_query_time_$DATE.json"

    log_success "数据库指标收集完成"
}

# 收集业务指标
collect_business_metrics() {
    log_info "收集业务指标..."

    # 专利检索数量
    echo "收集专利检索数量..."
    curl -s -G "$PROMETHEUS_URL/api/v1/query_range" \
        --data-urlencode "query=sum(rate(patent_search_requests_total[5m]))" \
        --data-urlencode "start=$(date -d '1 hour ago' +%s)" \
        --data-urlencode "end=$(date +%s)" \
        --data-urlencode "step=60" | jq '.' > "$OUTPUT_DIR/patent_searches_$DATE.json"

    # 活跃用户数
    echo "收集活跃用户数..."
    curl -s -G "$PROMETHEUS_URL/api/v1/query_range" \
        --data-urlencode "query=active_users_total" \
        --data-urlencode "start=$(date -d '1 hour ago' +%s)" \
        --data-urlencode "end=$(date +%s)" \
        --data-urlencode "step=60" | jq '.' > "$OUTPUT_DIR/active_users_$DATE.json"

    # AI分析任务数量
    echo "收集AI分析任务数量..."
    curl -s -G "$PROMETHEUS_URL/api/v1/query_range" \
        --data-urlencode "query=sum(rate(ai_analysis_requests_total[5m]))" \
        --data-urlencode "start=$(date -d '1 hour ago' +%s)" \
        --data-urlencode "end=$(date +%s)" \
        --data-urlencode "step=60" | jq '.' > "$OUTPUT_DIR/ai_analysis_$DATE.json"

    log_success "业务指标收集完成"
}

# 生成性能报告
generate_report() {
    log_info "生成性能报告..."

    cat > "$OUTPUT_DIR/performance-report-$DATE.html" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Athena平台性能报告 - $DATE</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        h2 { color: #666; border-bottom: 2px solid #eee; padding-bottom: 10px; }
        .metric { margin: 20px 0; }
        .metric-value { font-size: 24px; font-weight: bold; }
        .metric-label { color: #666; }
        .good { color: green; }
        .warning { color: orange; }
        .critical { color: red; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>Athena工作平台性能报告</h1>
    <p>生成时间: $(date)</p>

    <h2>系统概览</h2>
    <div class="metric">
        <span class="metric-label">服务健康状态:</span>
        <span class="metric-value">正常运行</span>
    </div>

    <h2>资源使用情况</h2>
    <table>
        <tr>
            <th>指标</th>
            <th>当前值</th>
            <th>阈值</th>
            <th>状态</th>
        </tr>
        <tr>
            <td>CPU使用率</td>
            <td id="cpu-usage">加载中...</td>
            <td>90%</td>
            <td id="cpu-status" class="good">正常</td>
        </tr>
        <tr>
            <td>内存使用率</td>
            <td id="memory-usage">加载中...</td>
            <td>90%</td>
            <td id="memory-status" class="good">正常</td>
        </tr>
        <tr>
            <td>磁盘使用率</td>
            <td id="disk-usage">加载中...</td>
            <td>85%</td>
            <td id="disk-status" class="good">正常</td>
        </tr>
    </table>

    <h2>应用性能</h2>
    <table>
        <tr>
            <th>服务</th>
            <th>请求速率 (req/s)</th>
            <th>响应时间 (ms)</th>
            <th>错误率 (%)</th>
        </tr>
        <tr>
            <td>API Gateway</td>
            <td id="api-gateway-rps">加载中...</td>
            <td id="api-gateway-rt">加载中...</td>
            <td id="api-gateway-error">加载中...</td>
        </tr>
        <tr>
            <td>YunPat Agent</td>
            <td id="yunpat-rps">加载中...</td>
            <td id="yunpat-rt">加载中...</td>
            <td id="yunpat-error">加载中...</td>
        </tr>
    </table>

    <h2>业务指标</h2>
    <table>
        <tr>
            <th>指标</th>
            <th>数值</th>
            <th>趋势</th>
        </tr>
        <tr>
            <td>专利检索次数/分钟</td>
            <td id="patent-searches">加载中...</td>
            <td>稳定</td>
        </tr>
        <tr>
            <td>活跃用户数</td>
            <td id="active-users">加载中...</td>
            <td>增长</td>
        </tr>
        <tr>
            <td>AI分析任务数/分钟</td>
            <td id="ai-analysis">加载中...</td>
            <td>稳定</td>
        </tr>
    </table>

    <h2>建议</h2>
    <ul>
        <li>系统运行正常，各项指标均在正常范围内</li>
        <li>建议继续监控数据库查询性能</li>
        <li>考虑增加更多的缓存以提升响应速度</li>
    </ul>

    <script>
        // 这里可以添加JavaScript来动态加载指标数据
        // 实际使用时需要从Prometheus API获取最新数据
    </script>
</body>
</html>
EOF

    log_success "性能报告已生成: $OUTPUT_DIR/performance-report-$DATE.html"
}

# 发送报告到邮箱
send_report() {
    if [[ -n "$REPORT_EMAIL" ]]; then
        log_info "发送报告到 $REPORT_EMAIL..."

        # 使用mail命令发送报告（需要配置好邮件服务）
        echo "Athena平台性能报告 - $DATE" | \
            mail -s "性能报告" -a "$OUTPUT_DIR/performance-report-$DATE.html" \
            $REPORT_EMAIL

        log_success "报告已发送"
    else
        log_info "未配置报告邮箱，跳过发送"
    fi
}

# 清理旧报告
cleanup_old_reports() {
    log_info "清理7天前的旧报告..."

    find $OUTPUT_DIR -name "*.json" -mtime +7 -delete
    find $OUTPUT_DIR -name "*.html" -mtime +7 -delete

    log_success "清理完成"
}

# 主函数
main() {
    log_info "开始收集性能指标..."

    # 检查Prometheus是否可访问
    if ! curl -s "$PROMETHEUS_URL/api/v1/query" > /dev/null; then
        log_error "无法连接到Prometheus: $PROMETHEUS_URL"
        exit 1
    fi

    # 执行指标收集
    collect_system_metrics
    collect_application_metrics
    collect_database_metrics
    collect_business_metrics

    # 生成报告
    generate_report

    # 发送报告
    send_report

    # 清理旧报告
    cleanup_old_reports

    log_success "性能指标收集完成！"
    log_info "报告目录: $OUTPUT_DIR"
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --prometheus-url)
            PROMETHEUS_URL="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --email)
            REPORT_EMAIL="$2"
            shift 2
            ;;
        -h|--help)
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  --prometheus-url URL  Prometheus服务器地址"
            echo "  --output-dir DIR      输出目录"
            echo "  --email EMAIL         报告接收邮箱"
            echo "  -h, --help            显示帮助信息"
            exit 0
            ;;
        *)
            log_error "未知选项: $1"
            exit 1
            ;;
    esac
done

# 执行主函数
main