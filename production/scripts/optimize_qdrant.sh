#!/bin/bash
# Qdrant配置优化脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔧 Qdrant配置优化开始...${NC}"
echo -e "${BLUE}时间: $(date)${NC}"

# 1. 停止不健康的容器
echo ""
echo -e "${YELLOW}🛑 停止不健康的Qdrant容器...${NC}"

UNHEALTHY_CONTAINERS=("athena_qdrant_legal" "phoenix-qdrant")

for container in "${UNHEALTHY_CONTAINERS[@]}"; do
    if docker ps -q --filter "name=$container" | grep -q .; then
        echo -e "   停止容器: $container"
        docker stop $container
    else
        echo -e "   容器 $container 未运行"
    fi
done

# 2. 保留主要的Qdrant容器
MAIN_CONTAINER="determined_ishizaka"
if docker ps -q --filter "name=$MAIN_CONTAINER" | grep -q .; then
    echo -e "${GREEN}✅ 主要Qdrant容器 ($MAIN_CONTAINER) 正在运行${NC}"
else
    echo -e "${YELLOW}⚠️  主要Qdrant容器未运行，将启动新容器${NC}"

    # 启动新的Qdrant容器
    docker run -d \
        --name athena_qdrant_main \
        -p 6333:6333 \
        -p 6334:6334 \
        -v $(pwd)/qdrant_storage:/qdrant/storage \
        qdrant/qdrant:latest

    echo -e "${GREEN}✅ 新的Qdrant容器已启动: athena_qdrant_main${NC}"
fi

# 3. 清理不需要的容器
echo ""
echo -e "${YELLOW}🗑️ 清理不需要的容器...${NC}"

UNUSED_CONTAINERS=("qdrant" "qdrant_patent" "legal_qdrant")

for container in "${UNUSED_CONTAINERS[@]}"; do
    if docker ps -q --filter "name=$container" | grep -q .; then
        echo -e "   停止并删除: $container"
        docker stop $container
        docker rm $container
    fi
done

# 4. 创建Qdrant存储目录
echo ""
echo -e "${YELLOW}📁 创建Qdrant存储目录...${NC}"

STORAGE_DIR="$(pwd)/modules/storage/qdrant_storage"
mkdir -p $STORAGE_DIR
echo -e "${GREEN}✅ 存储目录创建: $STORAGE_DIR${NC}"

# 5. 等待容器启动
echo ""
echo -e "${YELLOW}⏳ 等待Qdrant服务启动...${NC}"
sleep 10

# 6. 验证Qdrant状态
echo ""
echo -e "${BLUE}🔍 验证Qdrant状态...${NC}"

# 检查容器状态
if docker ps --filter "name=athena_qdrant_main" --format "{{.Status}}" | grep -q "Up"; then
    echo -e "${GREEN}✅ Qdrant容器运行正常${NC}"
else
    echo -e "${RED}❌ Qdrant容器启动失败${NC}"
    exit 1
fi

# 检查API响应
for port in 6333 6334; do
    echo -e "   测试端口 $port..."
    if curl -s http://localhost:$port/collections > /dev/null 2>&1; then
        collections=$(curl -s http://localhost:$port/collections | jq '.result.collections | length' 2>/dev/null || echo "N/A")
        echo -e "   ${GREEN}✅ 端口 $port 响应正常 (集合数: $collections)${NC}"
    else
        echo -e "   ${RED}❌ 端口 $port 无响应${NC}"
    fi
done

echo ""
echo -e "${GREEN}🎯 Qdrant配置优化完成！${NC}"
echo -e "${BLUE}📋 主要服务端口: 6333 (REST API), 6334 (gRPC)${NC}"
echo -e "${BLUE}📁 存储位置: $STORAGE_DIR${NC}"
echo -e "${BLUE}🏷️  容器名称: athena_qdrant_main${NC}"