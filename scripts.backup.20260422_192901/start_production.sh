#!/bin/bash
# Athena工作平台 - 生产环境启动脚本
# Production Start Script

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "======================================================"
echo "🚀 Athena工作平台 - 生产环境"
echo "======================================================"
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

echo "✅ Python版本: $(python3 --version)"

# 设置环境变量
export PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}"
export ENVIRONMENT=production
export DEBUG=false
export GATEWAY_PORT=8005

# 检查端口占用
if lsof -Pi :$GATEWAY_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️ 端口 $GATEWAY_PORT 已被占用"
    echo "正在尝试停止现有服务..."
    pkill -f athena_gateway || true
    sleep 2
fi

# 创建日志目录
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/data"

# 启动服务
echo ""
echo "🚀 启动服务..."
cd "$SCRIPT_DIR"

# 后台启动网关
nohup python3 -m uvicorn services.api_gateway.athena_gateway:app \
    --host 0.0.0.0 \
    --port $GATEWAY_PORT \
    --log-level info \
    --access-log \
    --reload > "$PROJECT_ROOT/logs/gateway.log" 2>&1 &

GATEWAY_PID=$!
echo $GATEWAY_PID > "$PROJECT_ROOT/data/gateway.pid"

echo "✅ 网关服务启动中..."
sleep 5

# 检查服务状态
if ps -p $GATEWAY_PID > /dev/null 2>&1; then
    echo "✅ 网关服务启动成功 (PID: $GATEWAY_PID)"
    echo ""
    echo "======================================================"
    echo "🎉 部署完成！"
    echo "======================================================"
    echo ""
    echo "📱 服务访问地址:"
    echo "  • API网关:   http://localhost:$GATEWAY_PORT"
    echo "  • API文档:   http://localhost:$GATEWAY_PORT/docs"
    echo "  • 健康检查: http://localhost:$GATEWAY_PORT/health"
    echo ""
    echo "📋 管理命令:"
    echo "  • 查看日志: tail -f $PROJECT_ROOT/logs/gateway.log"
    echo "  • 停止服务: kill $GATEWAY_PID"
    echo "  • 重启服务: $0 restart"
    echo ""
    echo "💡 提示: 使用 Python 脚本进行完整部署: python3 scripts/deploy_production.py"
else
    echo "❌ 网关服务启动失败"
    echo "请查看日志: tail -20 $PROJECT_ROOT/logs/gateway.log"
    exit 1
fi
