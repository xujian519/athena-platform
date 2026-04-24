#!/bin/bash
# ==============================================================================
# Athena平台 - Grafana追踪仪表板设置脚本
# ==============================================================================
# 功能：
#   1. 启动追踪环境 (OTEL Collector + Jaeger + Elasticsearch + Grafana)
#   2. 配置Grafana数据源
#   3. 导入追踪仪表板
#   4. 验证服务健康状态
#
# 使用方法：
#   ./scripts/setup_tracing_dashboard.sh [--skip-start] [--verify-only]
#
# 选项：
#   --skip-start     跳过Docker服务启动（假设服务已在运行）
#   --verify-only    仅验证服务状态，不进行配置
#
# 作者: Athena平台团队
# 更新: 2026-04-24
# ==============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.tracing.yml"
GRAFANA_URL="http://localhost:3001"
JAEGER_URL="http://localhost:16686"
ES_URL="http://localhost:9200"
ADMIN_USER="admin"
ADMIN_PASS="admin"

# 函数：打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 函数：打印分隔线
print_separator() {
    echo "=============================================================================================================="
}

# 函数：检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "$1 未安装，请先安装"
        exit 1
    fi
}

# 函数：等待服务启动
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=${3:-60}
    local attempt=0

    print_info "等待 $name 启动..."

    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            print_success "$name 已就绪"
            return 0
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done

    print_error "$name 启动超时"
    return 1
}

# 函数：启动Docker服务
start_services() {
    print_info "启动追踪环境..."

    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "Docker Compose文件不存在: $COMPOSE_FILE"
        exit 1
    fi

    cd "$PROJECT_ROOT"
    docker-compose -f "$COMPOSE_FILE" up -d

    print_info "等待服务启动..."
    wait_for_service "$ES_URL/_cluster/health" "Elasticsearch" 60
    wait_for_service "$JAEGER_URL" "Jaeger" 60
    wait_for_service "$GRAFANA_URL" "Grafana" 60

    print_success "所有服务已启动"
}

# 函数：验证服务状态
verify_services() {
    print_info "验证服务状态..."
    print_separator

    # 检查Elasticsearch
    if curl -s "$ES_URL/_cluster/health" | grep -q "green\|yellow"; then
        print_success "Elasticsearch: 健康"
        ES_HEALTH=$(curl -s "$ES_URL/_cluster/health" | jq -r '.status')
        echo "  状态: $ES_HEALTH"
    else
        print_error "Elasticsearch: 不健康"
    fi

    # 检查Jaeger
    if curl -s "$JAEGER_URL" > /dev/null; then
        print_success "Jaeger: 运行中"
    else
        print_error "Jaeger: 无法访问"
    fi

    # 检查Grafana
    if curl -s "$GRAFANA_URL" > /dev/null; then
        print_success "Grafana: 运行中"
    else
        print_error "Grafana: 无法访问"
    fi

    # 检查OTEL Collector
    if docker ps | grep -q "athena-otel-collector"; then
        print_success "OTEL Collector: 运行中"
    else
        print_error "OTEL Collector: 未运行"
    fi

    print_separator
}

# 函数：配置Grafana数据源
configure_datasources() {
    print_info "配置Grafana数据源..."

    # 检查数据源是否已存在
    EXISTING_DS=$(curl -s "${GRAFANA_URL}/api/datasources/name/Jaeger" \
        -u "${ADMIN_USER}:${ADMIN_PASS}" \
        -H "Content-Type: application/json")

    if echo "$EXISTING_DS" | grep -q "id"; then
        print_warning "Jaeger数据源已存在，跳过配置"
        return 0
    fi

    # 创建Jaeger数据源
    print_info "创建Jaeger数据源..."
    JAEGEN_DS_PAYLOAD='{
        "name": "Jaeger",
        "type": "jaeger",
        "url": "http://jaeger:16686",
        "access": "proxy",
        "isDefault": false,
        "jsonData": {
            "tracesToLogs": {
                "datasourceUid": "elasticsearch"
            }
        }
    }'

    DS_RESULT=$(curl -s -X POST "${GRAFANA_URL}/api/datasources" \
        -u "${ADMIN_USER}:${ADMIN_PASS}" \
        -H "Content-Type: application/json" \
        -d "$JAEGEN_DS_PAYLOAD")

    if echo "$DS_RESULT" | grep -q "id"; then
        print_success "Jaeger数据源创建成功"
    else
        print_warning "Jaeger数据源创建失败（可能已通过provisioning配置）"
    fi
}

# 函数：导入仪表板
import_dashboard() {
    print_info "导入追踪仪表板..."

    DASHBOARD_FILE="${PROJECT_ROOT}/config/grafana/dashboards/tracing-dashboard.json"

    if [ ! -f "$DASHBOARD_FILE" ]; then
        print_error "仪表板文件不存在: $DASHBOARD_FILE"
        return 1
    fi

    # 读取仪表板配置并包装
    DASHBOARD_JSON=$(cat "$DASHBOARD_FILE")
    IMPORT_PAYLOAD=$(jq -n \
        --argjson dashboard "$DASHBOARD_JSON" \
        --overwrite true \
        '{dashboard: $dashboard, overwrite: true, message: "通过setup_tracing_dashboard.sh导入"}')

    IMPORT_RESULT=$(curl -s -X POST "${GRAFANA_URL}/api/dashboards/import" \
        -u "${ADMIN_USER}:${ADMIN_PASS}" \
        -H "Content-Type: application/json" \
        -d "$IMPORT_PAYLOAD")

    if echo "$IMPORT_RESULT" | grep -q "slug\|url"; then
        print_success "仪表板导入成功"
        SLUG=$(echo "$IMPORT_RESULT" | jq -r '.slug // .url' 2>/dev/null || echo "athena-tracing-overview")
        echo "  访问URL: ${GRAFANA_URL}/d/${SLUG}"
    else
        print_warning "仪表板导入失败（可能已通过provisioning自动加载）"
        echo "  访问URL: ${GRAFANA_URL}/d/athena-tracing-overview"
    fi
}

# 函数：打印访问信息
print_access_info() {
    print_separator
    echo -e "${GREEN}🎨 Athena追踪可视化环境已就绪！${NC}"
    print_separator
    echo ""
    echo "📊 访问地址："
    echo "  • Grafana仪表板: ${GRAFANA_URL}/d/athena-tracing-overview"
    echo "  • Grafana首页:    ${GRAFANA_URL} (用户名: ${ADMIN_USER}, 密码: ${ADMIN_PASS})"
    echo "  • Jaeger UI:      ${JAEGER_URL}"
    echo "  • Elasticsearch:  ${ES_URL}"
    echo ""
    echo "📚 管理命令："
    echo "  • 查看日志: docker-compose -f ${COMPOSE_FILE} logs -f"
    echo "  • 停止服务: docker-compose -f ${COMPOSE_FILE} down"
    echo "  • 重启服务: docker-compose -f ${COMPOSE_FILE} restart"
    echo ""
    echo "🔍 快速验证："
    echo "  1. 打开Grafana仪表板"
    echo "  2. 选择时间范围（如最近1小时）"
    echo "  3. 查看Agent请求量和延迟趋势"
    echo ""
    print_separator
}

# 主函数
main() {
    print_separator
    echo -e "${BLUE}🎨 Athena平台 - Grafana追踪仪表板设置${NC}"
    print_separator

    # 检查依赖
    check_command docker
    check_command curl
    check_command jq || print_warning "jq未安装，部分功能可能受限"

    # 解析参数
    SKIP_START=false
    VERIFY_ONLY=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-start)
                SKIP_START=true
                shift
                ;;
            --verify-only)
                VERIFY_ONLY=true
                shift
                ;;
            *)
                print_error "未知参数: $1"
                exit 1
                ;;
        esac
    done

    # 仅验证模式
    if [ "$VERIFY_ONLY" = true ]; then
        verify_services
        exit 0
    fi

    # 启动服务
    if [ "$SKIP_START" = false ]; then
        start_services
    else
        print_info "跳过服务启动，假设服务已在运行..."
    fi

    # 配置Grafana
    configure_datasources
    import_dashboard

    # 验证服务
    verify_services

    # 打印访问信息
    print_access_info

    print_success "设置完成！"
}

# 执行主函数
main "$@"
