#!/bin/bash
# ArangoDB部署脚本

echo "🚀 开始部署ArangoDB知识图谱数据库..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 创建数据目录
mkdir -p /Users/xujian/Athena工作平台/data/arangodb

# 停止现有容器（如果存在）
docker stop athena-arangodb 2>/dev/null || true
docker rm athena-arangodb 2>/dev/null || true

# 启动ArangoDB容器
echo "📦 启动ArangoDB容器..."
docker run -d \
    --name athena-arangodb \
    -p 8529:8529 \
    -p 8528:8528 \
    -e ARANGO_ROOT_PASSWORD="" \
    -e ARANGO_NO_AUTH=1 \
    -e ARANGO_ENABLE_IPV6=false \
    -v /Users/xujian/Athena工作平台/data/arangodb:/var/lib/arangodb3 \
    arangodb/arangodb:latest

echo "⏳ 等待ArangoDB启动..."
sleep 10

# 检查容器状态
if docker ps | grep athena-arangodb > /dev/null; then
    echo "✅ ArangoDB启动成功！"
    echo "📊 Web界面: http://localhost:8528"
    echo "🔌 API端点: http://localhost:8529"
else
    echo "❌ ArangoDB启动失败"
    docker logs athena-arangodb
    exit 1
fi

# 安装Python依赖
echo "📦 安装Python依赖..."
pip3 install python-arango > /dev/null 2>&1

echo "✅ ArangoDB部署完成！"