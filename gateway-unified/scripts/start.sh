#!/bin/bash
# Athena Gateway 启动脚本
set -e

cd "$(dirname "$0")/.."
GATEWAY_BIN="./gateway"
CONFIG_DIR="./configs"

echo "🚀 启动 Athena Gateway..."

# 检查二进制文件
if [ ! -f "$GATEWAY_BIN" ]; then
    echo "❌ 二进制文件不存在，请先执行: go build -o bin/gateway cmd/gateway/main.go"
    exit 1
fi

# 检查配置文件
if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
    echo "⚠️  配置文件不存在，使用默认配置"
    mkdir -p "$CONFIG_DIR"
    cat > "$CONFIG_DIR/config.yaml" <<EOF
server:
  port: 8085
  host: "127.0.0.1"
logging:
  level: info
EOF
fi

# 启动网关
echo "📡 监听地址: http://127.0.0.1:8085"
echo "📚 API文档: http://127.0.0.1:8085/swagger"
echo "💚 健康检查: http://127.0.0.1:8085/health"

exec $GATEWAY_BIN
