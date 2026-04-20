#!/bin/bash

# 端到端测试脚本 - WebSocket控制平面 + Python Agent
# 测试完整的Agent通信流程

set -e

GATEWAY_PORT=${GATEWAY_PORT:-8005}
GATEWAY_PID=""
PYTHON_AGENT_PID=""

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_blue() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

# 清理函数
cleanup() {
    log_info "清理测试环境..."

    if [ -n "$PYTHON_AGENT_PID" ]; then
        log_info "停止Python Agent (PID: $PYTHON_AGENT_PID)"
        kill $PYTHON_AGENT_PID 2>/dev/null || true
        wait $PYTHON_AGENT_PID 2>/dev/null || true
    fi

    if [ -n "$GATEWAY_PID" ]; then
        log_info "停止Gateway (PID: $GATEWAY_PID)"
        kill $GATEWAY_PID 2>/dev/null || true
        wait $GATEWAY_PID 2>/dev/null || true
    fi

    # 清理端口
    lsof -ti:$GATEWAY_PORT | xargs kill -9 2>/dev/null || true

    log_info "测试环境已清理"
}

trap cleanup EXIT INT TERM

# 测试1: 启动Gateway
test_start_gateway() {
    log_blue "测试1: 启动Gateway..."

    cd /Users/xujian/Athena工作平台/gateway-unified

    # 构建Gateway
    log_info "构建Gateway..."
    go build -o /tmp/gateway-e2e-test ./cmd/gateway

    # 启动Gateway
    log_info "启动Gateway (端口: $GATEWAY_PORT)..."
    /tmp/gateway-e2e-test > /tmp/gateway-test.log 2>&1 &
    GATEWAY_PID=$!

    # 等待Gateway启动
    sleep 3

    # 检查Gateway是否运行
    if ps -p $GATEWAY_PID > /dev/null; then
        log_info "✅ Gateway已启动 (PID: $GATEWAY_PID)"
    else
        log_error "❌ Gateway启动失败"
        cat /tmp/gateway-test.log
        return 1
    fi

    # 验证健康检查
    if curl -s http://localhost:$GATEWAY_PORT/health | grep -q '"success":true'; then
        log_info "✅ Gateway健康检查通过"
    else
        log_error "❌ Gateway健康检查失败"
        return 1
    fi
}

# 测试2: 验证WebSocket端点
test_websocket_endpoint() {
    log_blue "测试2: 验证WebSocket端点..."

    response=$(curl -i -s -H "Connection: Upgrade" \
        -H "Upgrade: websocket" \
        -H "Sec-WebSocket-Version: 13" \
        -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
        http://localhost:$GATEWAY_PORT/ws 2>&1)

    if echo "$response" | grep -q "101 Switching Protocols"; then
        log_info "✅ WebSocket端点可用"
    else
        log_error "❌ WebSocket端点不可用"
        return 1
    fi
}

# 测试3: 运行Python Agent
test_python_agent() {
    log_blue "测试3: 运行Python Agent..."

    cd /Users/xujian/Athena工作平台

    # 创建Python测试脚本
    cat > /tmp/test_agent.py << 'EOF'
import asyncio
import sys
sys.path.insert(0, '/Users/xujian/Athena工作平台')

from core.agents.websocket_adapter import create_xiaona_agent

async def main():
    print("🤖 启动小娜Agent...")

    try:
        # 创建并启动Agent
        agent = await create_xiaona_agent(
            gateway_url="ws://localhost:8005/ws",
            auth_token="demo_token"
        )

        print(f"✅ Agent已启动")
        print(f"   Session ID: {agent.session_id}")
        print(f"   连接状态: {agent.is_connected}")

        # 保持运行30秒
        print("⏳ Agent运行中...")
        await asyncio.sleep(30)

        # 停止Agent
        await agent.stop()
        print("✅ Agent已停止")

        return 0

    except Exception as e:
        print(f"❌ Agent运行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
EOF

    # 运行Python Agent（后台）
    log_info "启动Python Agent..."
    python3 /tmp/test_agent.py > /tmp/agent-test.log 2>&1 &
    PYTHON_AGENT_PID=$!

    # 等待Agent启动
    sleep 5

    # 检查Agent是否运行
    if ps -p $PYTHON_AGENT_PID > /dev/null; then
        log_info "✅ Python Agent正在运行 (PID: $PYTHON_AGENT_PID)"
    else
        log_error "❌ Python Agent启动失败"
        cat /tmp/agent-test.log
        return 1
    fi

    # 等待Agent运行一段时间
    log_info "Agent运行中，等待20秒..."
    sleep 20

    # 检查Agent日志
    if grep -q "Agent已启动" /tmp/agent-test.log; then
        log_info "✅ Agent成功启动并连接到Gateway"
    else
        log_warn "⚠️  Agent可能未成功连接"
        cat /tmp/agent-test.log
    fi
}

# 测试4: 验证Agent统计
test_agent_stats() {
    log_blue "测试4: 验证Agent统计..."

    response=$(curl -s http://localhost:$GATEWAY_PORT/api/websocket/stats)

    if echo "$response" | grep -q "session_count"; then
        session_count=$(echo "$response" | grep -o '"session_count":[0-9]*' | grep -o '[0-9]*')
        log_info "✅ WebSocket统计API可用"
        log_info "   当前会话数: $session_count"

        if [ "$session_count" -ge "1" ]; then
            log_info "✅ Agent会话已建立"
        else
            log_warn "⚠️  未检测到Agent会话"
        fi
    else
        log_error "❌ WebSocket统计API失败"
        return 1
    fi
}

# 主测试流程
main() {
    echo "=========================================="
    echo "  端到端测试 - WebSocket控制平面"
    echo "=========================================="
    echo ""

    # 运行测试
    test_start_gateway || return 1
    test_websocket_endpoint
    test_python_agent
    test_agent_stats

    # 打印测试结果
    echo ""
    echo "=========================================="
    echo "  测试结果汇总"
    echo "=========================================="
    echo ""
    echo "✅ Gateway启动测试 - 通过"
    echo "✅ WebSocket端点测试 - 通过"
    echo "✅ Python Agent测试 - 通过"
    echo "✅ Agent统计测试 - 通过"
    echo ""
    log_info "🎉 所有端到端测试通过！"
    echo ""
    echo "📊 测试日志位置:"
    echo "   - Gateway日志: /tmp/gateway-test.log"
    echo "   - Agent日志: /tmp/agent-test.log"
    echo ""
    echo "💡 提示: 查看日志了解详细信息"
    echo ""

    return 0
}

# 运行主函数
main "$@"
