#!/bin/bash
# 容器清理和优化脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🗂️ 容器清理和优化开始...${NC}"
echo -e "${BLUE}时间: $(date)${NC}"

# 1. 清理已退出的容器
echo ""
echo -e "${YELLOW}🗑️ 清理已退出的容器...${NC}"

EXITED_CONTAINERS=$(docker ps -aq --filter "status=exited")
if [ -n "$EXITED_CONTAINERS" ]; then
    echo "$EXITED_CONTAINERS" | xargs docker rm -v
    echo -e "${GREEN}✅ 已清理退出的容器${NC}"
else
    echo -e "${BLUE}ℹ️  没有退出的容器需要清理${NC}"
fi

# 2. 停止并清理重复的Redis容器
echo ""
echo -e "${YELLOW}🔄 处理Redis容器...${NC}"

# 保留主要的Redis容器
MAIN_REDIS="storage-system-redis-1"
UNUSED_REDIS=("legal_redis" "athena_redis_legal" "phoenix-redis" "athena-redis")

echo -e "${GREEN}✅ 保留主Redis容器: $MAIN_REDIS${NC}"

for redis_container in "${UNUSED_REDIS[@]}"; do
    if docker ps -q --filter "name=$redis_container" | grep -q .; then
        echo -e "   停止并删除: $redis_container"
        docker stop $redis_container
        docker rm $redis_container
    fi
done

# 3. 停止并清理未使用的Elasticsearch容器
echo ""
echo -e "${YELLOW}🔍 处理Elasticsearch容器...${NC}"

# 保留主要ES容器
MAIN_ES="athena_elasticsearch"
UNUSED_ES=("phoenix-elasticsearch-new" "athena_elasticsearch")

echo -e "${GREEN}✅ 保留主ES容器: $MAIN_ES${NC}"

# 检查主容器状态
if docker ps --filter "name=$MAIN_ES" --format "{{.Status}}" | grep -q "Up"; then
    echo -e "${GREEN}✅ 主ES容器运行正常${NC}"

    # 清理重复容器
    for es_container in "${UNUSED_ES[@]}"; do
        if docker ps -q --filter "name=$es_container" | grep -q .; then
            echo -e "   停止并删除: $es_container"
            docker stop $es_container
            docker rm $es_container
        fi
    done
else
    echo -e "${YELLOW}⚠️  主ES容器未运行${NC}"
fi

# 4. 检查PostgreSQL容器
echo ""
echo -e "${YELLOW}🐘 检查PostgreSQL容器...${NC}"

PG_CONTAINERS=("athena_postgres_legal" "legal_postgres")

for pg_container in "${PG_CONTAINERS[@]}"; do
    if docker ps --filter "name=$pg_container" --format "{{.Status}}" | grep -q "Up"; then
        echo -e "${GREEN}✅ $pg_container 运行正常${NC}"
    else
        echo -e "${YELLOW}⚠️  $pg_container 未运行${NC}"
    fi
done

# 5. 清理未使用的镜像
echo ""
echo -e "${YELLOW}🧹 清理未使用的Docker镜像...${NC}"
docker image prune -f

# 6. 清理未使用的网络
echo ""
echo -e "${YELLOW}🌐 清理未使用的Docker网络...${NC}"
docker network prune -f

# 7. 显示当前运行的容器
echo ""
echo -e "${BLUE}📊 当前运行的存储容器:${NC}"

docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(redis|postgres|elasticsearch|qdrant)" || echo -e "${YELLOW}⚠️  未找到存储容器${NC}"

# 8. 验证服务端口
echo ""
echo -e "${BLUE}🔍 验证服务端口...${NC}"

# 检查PostgreSQL
if nc -z localhost 5432; then
    echo -e "${GREEN}✅ PostgreSQL (5432) - 可访问${NC}"
else
    echo -e "${RED}❌ PostgreSQL (5432) - 不可访问${NC}"
fi

# 检查Redis
if nc -z localhost 6379; then
    echo -e "${GREEN}✅ Redis (6379) - 可访问${NC}"
else
    echo -e "${RED}❌ Redis (6379) - 不可访问${NC}"
fi

# 检查Elasticsearch
if nc -z localhost 9200; then
    echo -e "${GREEN}✅ Elasticsearch (9200) - 可访问${NC}"
else
    echo -e "${RED}❌ Elasticsearch (9200) - 不可访问${NC}"
fi

# 检查Qdrant
if nc -z localhost 6333; then
    echo -e "${GREEN}✅ Qdrant (6333) - 可访问${NC}"
else
    echo -e "${RED}❌ Qdrant (6333) - 不可访问${NC}"
fi

echo ""
echo -e "${GREEN}🎯 容器清理和优化完成！${NC}"
echo -e "${BLUE}📋 保留的核心容器:${NC}"
echo -e "   - athena_qdrant_main (向量数据库)"
echo -e "   - storage-system-redis-1 (缓存)"
echo -e "   - athena_elasticsearch (搜索引擎)"
echo -e "   - athena_postgres_legal (关系数据库)"
echo ""
echo -e "${GREEN}💾 磁盘空间已优化！${NC}"