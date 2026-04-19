#!/bin/bash
"""
启动minerU OCR服务

Athena平台集成的minerU服务启动脚本
"""

set -e

MINERU_DIR="/Users/xujian/MinerU"
COMPOSE_FILE="$MINERU_DIR/docker/compose.yaml"

echo "=================================================="
echo "🚀 启动minerU OCR服务"
echo "=================================================="
echo ""

# 检查目录是否存在
if [ ! -d "$MINERU_DIR" ]; then
    echo "❌ MinerU目录不存在: $MINERU_DIR"
    exit 1
fi

echo "✅ MinerU目录存在: $MINERU_DIR"
echo ""

# 进入MinerU目录
cd "$MINERU_DIR"

# 检查compose文件
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "❌ Compose文件不存在: $COMPOSE_FILE"
    exit 1
fi

echo "✅ 找到compose配置文件"
echo ""

# 检查docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装"
    exit 1
fi

echo "✅ Docker已安装"
echo ""

# 检查docker compose
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose未安装"
    exit 1
fi

echo "✅ Docker Compose已安装"
echo ""

# 启动minerU gradio服务
echo "📦 启动minerU Gradio服务 (端口7860)..."
echo ""

docker compose --file "$COMPOSE_FILE" up -d mineru-gradio

echo ""
echo "=================================================="
echo "⏳ 等待服务启动..."
echo "=================================================="
echo ""

# 等待服务启动
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
echo ""

if docker ps | grep -q "mineru-gradio"; then
    echo "✅ minerU Gradio服务已启动"
    echo ""
    echo "📍 服务地址:"
    echo "   - Gradio Web界面: http://localhost:7860"
    echo "   - API端点: http://localhost:7860/api/v1/general"
    echo ""
    echo "📋 查看日志:"
    echo "   docker logs -f mineru-gradio"
    echo ""
    echo "🛑 停止服务:"
    echo "   cd $MINERU_DIR && docker compose --file $COMPOSE_FILE down"
    echo ""
else
    echo "❌ minerU Gradio服务启动失败"
    echo ""
    echo "📋 查看日志:"
    echo "   docker logs mineru-gradio"
    echo ""
    exit 1
fi

# 健康检查
echo "🏥 健康检查..."
echo ""

sleep 5

if curl -s http://localhost:7860 > /dev/null 2>&1; then
    echo "✅ 服务健康检查通过"
else
    echo "⚠️  服务可能还在启动中，请稍等片刻"
    echo "   可以通过 http://localhost:7860 访问Gradio界面"
fi

echo ""
echo "=================================================="
echo "🎉 minerU OCR服务启动完成！"
echo "=================================================="
