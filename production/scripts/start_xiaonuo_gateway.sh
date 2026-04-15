#!/bin/bash
# 小诺模块化网关启动脚本

PROJECT_ROOT="/Users/xujian/Athena工作平台"
cd "$PROJECT_ROOT/services/api-gateway/src" || exit 1

# 日志目录
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

# PID文件
PID_FILE="$LOG_DIR/xiaonuo_gateway.pid"

# 端口配置
PORT=8100
HOST="0.0.0.0"

echo "🚀 启动小诺模块化网关..."

# 检查是否已运行
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "⚠️  网关已在运行 (PID: $OLD_PID)"
        exit 1
    fi
    rm -f "$PID_FILE"
fi

# 设置PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/services:$PYTHONPATH"

# 禁止生成字节码缓存
export PYTHONDONTWRITEBYTECODE=1

# 加载环境变量
ENV_FILE="$PROJECT_ROOT/production/config/env/.env"
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
    echo "✅ 环境变量已加载"
else
    echo "⚠️  环境变量文件未找到: $ENV_FILE"
fi

# 直接使用Python文件启动网关
nohup /opt/homebrew/bin/python3.11 main_enhanced.py \
    >> "$LOG_DIR/xiaonuo_gateway.log" 2>&1 &

PID=$!
echo $PID > "$PID_FILE"

echo "✅ 小诺模块化网关已启动"
echo "   PID: $PID"
echo "   端口: $PORT"
echo "   日志: $LOG_DIR/xiaonuo_gateway.log"
echo ""
echo "📋 健康检查: curl http://localhost:$PORT/health"
