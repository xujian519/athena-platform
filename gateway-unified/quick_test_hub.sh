#!/bin/bash

# Athena Gateway WebSocket Hub 快速测试脚本

set -e

GATEWAY_BIN="./bin/gateway"
GATEWAY_PID=""
TEST_RESULTS=()

echo "🌸 Athena Gateway WebSocket Hub 快速测试"
echo "=========================================="
echo ""

# 清理函数
cleanup() {
    echo ""
    echo "🧹 清理资源..."

    if [ -n "$GATEWAY_PID" ]; then
        echo "停止Gateway (PID: $GATEWAY_PID)..."
        kill $GATEWAY_PID 2>/dev/null || true
        wait $GATEWAY_PID 2>/dev/null || true
    fi

    echo "✅ 清理完成"
}

# 设置退出时清理
trap cleanup EXIT INT TERM

# 检查二进制文件
if [ ! -f "$GATEWAY_BIN" ]; then
    echo "❌ Gateway二进制文件不存在: $GATEWAY_BIN"
    echo "请先运行: go build -o bin/gateway cmd/gateway/main.go"
    exit 1
fi

echo "✅ Gateway二进制文件已找到"
echo ""

# 启动Gateway
echo "🚀 启动Gateway..."
$GATEWAY_BIN > /tmp/gateway_test.log 2>&1 &
GATEWAY_PID=$!
echo "Gateway已启动 (PID: $GATEWAY_PID)"

# 等待Gateway启动
echo "⏳ 等待Gateway启动..."
sleep 3

# 检查Gateway是否运行
if ! kill -0 $GATEWAY_PID 2>/dev/null; then
    echo "❌ Gateway启动失败"
    echo "日志内容:"
    cat /tmp/gateway_test.log
    exit 1
fi

echo "✅ Gateway启动成功"
echo ""

# 测试1: 健康检查
echo "🧪 测试1: 健康检查"
if curl -s http://localhost:8005/health > /dev/null 2>&1; then
    echo "✅ 健康检查通过"
    TEST_RESULTS+=("健康检查: ✅ 通过")
else
    echo "❌ 健康检查失败"
    TEST_RESULTS+=("健康检查: ❌ 失败")
fi
echo ""

# 测试2: Hub统计API
echo "🧪 测试2: Hub统计API"
HUB_STATS=$(curl -s http://localhost:8005/api/hub/stats 2>/dev/null || echo "{}")
if echo "$HUB_STATS" | grep -q "success"; then
    echo "✅ Hub统计API正常"
    echo "响应: $HUB_STATS"
    TEST_RESULTS+=("Hub统计API: ✅ 通过")
else
    echo "❌ Hub统计API失败"
    TEST_RESULTS+=("Hub统计API: ❌ 失败")
fi
echo ""

# 测试3: WebSocket连接测试
echo "🧪 测试3: WebSocket连接测试"
if command -v wscat &> /dev/null; then
    echo "使用wscat测试WebSocket连接..."
    timeout 3 wscat -c "ws://localhost:8005/ws/hub?session_id=test_123" > /tmp/wscat_output.log 2>&1 || true

    if grep -q "Connected" /tmp/wscat_output.log 2>/dev/null; then
        echo "✅ WebSocket连接成功"
        TEST_RESULTS+=("WebSocket连接: ✅ 通过")
    else
        echo "⚠️  WebSocket连接测试不确定"
        echo "输出: $(cat /tmp/wscat_output.log)"
        TEST_RESULTS+=("WebSocket连接: ⚠️  不确定")
    fi
else
    echo "⚠️  wscat未安装，跳过WebSocket连接测试"
    echo "安装方法: npm install -g wscat"
    TEST_RESULTS+=("WebSocket连接: ⏭️  跳过")
fi
echo ""

# 测试4: 检查Gateway日志
echo "🧪 测试4: 检查Gateway日志"
if grep -q "WebSocket Hub已启动" /tmp/gateway_test.log 2>/dev/null; then
    echo "✅ WebSocket Hub已正确启动"
    TEST_RESULTS+=("Hub启动: ✅ 通过")
else
    echo "⚠️  未找到WebSocket Hub启动日志"
    TEST_RESULTS+=("Hub启动: ⚠️  警告")
fi
echo ""

# 打印测试结果摘要
echo "=========================================="
echo "📊 测试结果摘要"
echo "=========================================="
for result in "${TEST_RESULTS[@]}"; do
    echo "  $result"
done
echo ""

# 计算通过率
TOTAL=${#TEST_RESULTS[@]}
PASSED=$(echo "${TEST_RESULTS[@]}" | grep -o "✅ 通过" | wc -l | tr -d ' ')
PERCENT=$((PASSED * 100 / TOTAL))

echo "通过率: $PASSED/$TOTAL ($PERCENT%)"
echo ""

if [ $PERCENT -ge 75 ]; then
    echo "🎉 测试结果良好！"
    echo ""
    echo "📋 下一步操作:"
    echo "  1. 在浏览器中打开测试页面:"
    echo "     open file://$PWD/test_websocket_hub.html"
    echo ""
    echo "  2. 使用wscat进行交互式测试:"
    echo "     wscat -c \"ws://localhost:8005/ws/hub?session_id=test_$(date +%s)\""
    echo ""
    echo "  3. 查看Gateway日志:"
    echo "     tail -f /tmp/gateway_test.log"
else
    echo "⚠️  部分测试失败，请检查Gateway日志:"
    echo "   cat /tmp/gateway_test.log"
fi

echo ""
echo "💡 提示: Gateway将在脚本退出时自动停止"
echo ""
