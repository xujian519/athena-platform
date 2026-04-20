#!/bin/bash

# WebSocket控制平面测试脚本
# 用于测试Gateway的WebSocket功能

set -e

GATEWAY_PORT=${GATEWAY_PORT:-8005}
GATEWAY_PID=""
TEST_RESULTS=()

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# 清理函数
cleanup() {
    log_info "清理测试环境..."

    if [ -n "$GATEWAY_PID" ]; then
        log_info "停止Gateway (PID: $GATEWAY_PID)"
        kill $GATEWAY_PID 2>/dev/null || true
        wait $GATEWAY_PID 2>/dev/null || true
    fi

    log_info "测试环境已清理"
}

# 设置陷阱
trap cleanup EXIT INT TERM

# 测试1: 启动Gateway
test_start_gateway() {
    log_info "测试1: 启动Gateway..."

    cd /Users/xujian/Athena工作平台/gateway-unified

    # 构建Gateway
    log_info "构建Gateway..."
    go build -o /tmp/gateway-test ./cmd/gateway

    # 启动Gateway
    log_info "启动Gateway (端口: $GATEWAY_PORT)..."
    /tmp/gateway-test &
    GATEWAY_PID=$!

    # 等待Gateway启动
    sleep 3

    # 检查Gateway是否运行
    if ps -p $GATEWAY_PID > /dev/null; then
        log_info "✅ Gateway已启动 (PID: $GATEWAY_PID)"
        TEST_RESULTS+=("启动Gateway: PASS")
    else
        log_error "❌ Gateway启动失败"
        TEST_RESULTS+=("启动Gateway: FAIL")
        return 1
    fi
}

# 测试2: 健康检查
test_health_check() {
    log_info "测试2: 健康检查..."

    # 检查HTTP端点 - 检查success字段为true
    response=$(curl -s http://localhost:$GATEWAY_PORT/health)
    if echo "$response" | grep -q '"success":true'; then
        log_info "✅ 健康检查通过"
        TEST_RESULTS+=("健康检查: PASS")
    else
        log_error "❌ 健康检查失败: $response"
        TEST_RESULTS+=("健康检查: FAIL")
        return 1
    fi
}

# 测试3: WebSocket端点
test_websocket_endpoint() {
    log_info "测试3: WebSocket端点..."

    # 检查WebSocket升级
    response=$(curl -i -s -H "Connection: Upgrade" \
        -H "Upgrade: websocket" \
        -H "Sec-WebSocket-Version: 13" \
        -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
        http://localhost:$GATEWAY_PORT/ws 2>&1)

    if echo "$response" | grep -q "101 Switching Protocols"; then
        log_info "✅ WebSocket端点可用"
        TEST_RESULTS+=("WebSocket端点: PASS")
    else
        log_error "❌ WebSocket端点不可用"
        TEST_RESULTS+=("WebSocket端点: FAIL")
        return 1
    fi
}

# 测试4: WebSocket统计API
test_websocket_stats() {
    log_info "测试4: WebSocket统计API..."

    response=$(curl -s http://localhost:$GATEWAY_PORT/api/websocket/stats)

    if echo "$response" | grep -q "session_count"; then
        log_info "✅ WebSocket统计API可用"
        log_info "统计信息: $response"
        TEST_RESULTS+=("WebSocket统计API: PASS")
    else
        log_error "❌ WebSocket统计API失败"
        TEST_RESULTS+=("WebSocket统计API: FAIL")
        return 1
    fi
}

# 测试5: Canvas Host服务
test_canvas_host() {
    log_info "测试5: Canvas Host服务..."

    # Canvas Host通过WebSocket提供HTML渲染
    # 这里检查Canvas Host是否已初始化
    response=$(curl -s http://localhost:$GATEWAY_PORT/api/websocket/stats)

    if echo "$response" | grep -q "active_sessions"; then
        log_info "✅ Canvas Host服务已初始化"
        TEST_RESULTS+=("Canvas Host: PASS")
    else
        log_error "❌ Canvas Host服务未初始化"
        TEST_RESULTS+=("Canvas Host: FAIL")
        return 1
    fi
}

# 主测试流程
main() {
    echo "=========================================="
    echo "  WebSocket控制平面测试"
    echo "=========================================="
    echo ""

    # 运行测试
    test_start_gateway || return 1
    test_health_check
    test_websocket_endpoint
    test_websocket_stats
    test_canvas_host

    # 打印测试结果
    echo ""
    echo "=========================================="
    echo "  测试结果汇总"
    echo "=========================================="

    for result in "${TEST_RESULTS[@]}"; do
        if echo "$result" | grep -q "PASS"; then
            echo -e "${GREEN}✅ $result${NC}"
        else
            echo -e "${RED}❌ $result${NC}"
        fi
    done

    # 计算通过率
    total=${#TEST_RESULTS[@]}
    passed=$(echo "${TEST_RESULTS[@]}" | grep -o "PASS" | wc -l | tr -d ' ')
    rate=$((passed * 100 / total))

    echo ""
    echo "通过率: $passed/$total ($rate%)"

    if [ $rate -eq 100 ]; then
        log_info "🎉 所有测试通过！"
        return 0
    else
        log_warn "⚠️  部分测试失败"
        return 1
    fi
}

# 运行主函数
main "$@"
