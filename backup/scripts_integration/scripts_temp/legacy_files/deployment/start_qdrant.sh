#!/bin/bash
"""
启动Qdrant向量数据库服务
"""

echo "🔍 启动Qdrant向量数据库服务..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

# 检查docker-compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose未安装，请先安装docker-compose"
    exit 1
fi

# 设置工作目录
cd "$(dirname "$0")/.."

# 检查qdrant目录是否存在
if [ ! -d "services/qdrant" ]; then
    echo "❌ qdrant目录不存在"
    exit 1
fi

# 检查docker-compose.yml
if [ ! -f "services/qdrant/docker-compose.yml" ]; then
    echo "❌ docker-compose.yml文件不存在"
    exit 1
fi

cd services/qdrant

# 启动Qdrant服务
echo "🚀 启动Qdrant容器..."
docker-compose up -d

# 检查服务状态
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务是否成功启动
if docker-compose ps | grep -q "Up"; then
    echo "✅ Qdrant服务启动成功！"
    echo "   - 端口: 6333"
    echo "   - Web UI: http://localhost:6333/dashboard"
else
    echo "❌ Qdrant服务启动失败"
    echo "查看日志:"
    docker-compose logs
    exit 1
fi

# 检查API是否响应
echo "🔍 检查API响应..."
sleep 2

if curl -s http://localhost:6333/health | grep -q '"ok"'; then
    echo "✅ Qdrant API响应正常"
else
    echo "⚠️ Qdrant API暂时未响应，请稍等片刻"
fi

echo ""
echo "🎉 Qdrant向量数据库已成功启动！"
echo ""
echo "📋 常用命令："
echo "  查看状态: docker-compose ps"
echo "  查看日志: docker-compose logs"
echo "  停止服务: docker-compose down"
echo ""
echo "📊 检查向量数据库:"
echo "  python3 check_vector_databases.py"