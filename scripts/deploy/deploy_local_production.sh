#!/bin/bash
# ============================================================================
# Athena工作平台 - 本地生产环境部署脚本
# ============================================================================
# 用途：在本地Mac上部署认知与决策模块到生产环境
# 特点：
#   - 使用本地PostgreSQL 17.7（Homebrew）
#   - 使用已有Docker镜像（避免重复下载）
#   - 完整的健康检查和验证
# ============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}🚀 Athena工作平台 - 本地生产环境部署${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# ============================================================================
# 1. 环境检查
# ============================================================================
echo -e "${YELLOW}📋 步骤 1/6: 环境检查${NC}"

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker: $(docker --version)${NC}"

# 检查Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose: 可用${NC}"

# 检查PostgreSQL 17.7
if ! command -v psql &> /dev/null; then
    echo -e "${RED}❌ PostgreSQL未安装${NC}"
    exit 1
fi

# 检查PostgreSQL版本
PG_VERSION=$(psql --version | awk '{print $3}' | cut -d'.' -f1,2)
if [[ "$PG_VERSION" != "17.7" ]]; then
    echo -e "${YELLOW}⚠️  PostgreSQL版本: $PG_VERSION (建议使用17.7)${NC}"
else
    echo -e "${GREEN}✅ PostgreSQL 17.7: 已安装${NC}"
fi

# 检查PostgreSQL服务状态
if ! brew services list | grep postgresql@17 | grep -q started; then
    echo -e "${YELLOW}⚠️  PostgreSQL服务未运行，正在启动...${NC}"
    brew services start postgresql@17
    sleep 3
fi
echo -e "${GREEN}✅ PostgreSQL 17.7: 运行中${NC}"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python: $(python3 --version)${NC}"

echo ""

# ============================================================================
# 2. 网络配置
# ============================================================================
echo -e "${YELLOW}📋 步骤 2/6: 网络配置${NC}"

# 创建Docker网络（如果不存在）
if ! docker network inspect athena-prod-network &> /dev/null; then
    echo "创建Docker网络: athena-prod-network"
    docker network create athena-prod-network
    echo -e "${GREEN}✅ 网络创建成功${NC}"
else
    echo -e "${GREEN}✅ 网络已存在: athena-prod-network${NC}"
fi

echo ""

# ============================================================================
# 3. 数据库初始化
# ============================================================================
echo -e "${YELLOW}📋 步骤 3/6: 数据库初始化${NC}"

# 检查数据库是否存在
DB_EXISTS=$(psql -h localhost -p 5432 -U xujian -lqt | cut -d \| -f 1 | grep -w athena_production | wc -l)

if [ "$DB_EXISTS" -eq 0 ]; then
    echo "创建生产数据库: athena_production"
    createdb -U xujian athena_production
    echo -e "${GREEN}✅ 数据库创建成功${NC}"
else
    echo -e "${GREEN}✅ 数据库已存在: athena_production${NC}"
fi

echo ""

# ============================================================================
# 4. 启动Docker服务
# ============================================================================
echo -e "${YELLOW}📋 步骤 4/6: 启动Docker服务${NC}"

# 停止旧的容器（如果存在）
echo "清理旧容器..."
docker-compose -f config/docker/docker-compose.production.local.yml down 2>/dev/null || true

# 启动所有服务
echo "启动生产环境服务..."
docker-compose -f config/docker/docker-compose.production.local.yml up -d

echo -e "${GREEN}✅ Docker服务启动完成${NC}"
echo ""

# ============================================================================
# 5. 等待服务健康
# ============================================================================
echo -e "${YELLOW}📋 步骤 5/6: 等待服务健康${NC}"

# 等待服务启动
echo "等待服务启动和健康检查..."
sleep 10

# 检查服务健康状态
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    ALL_HEALTHY=true

    # 检查Qdrant
    if ! curl -s http://localhost:6333/ > /dev/null 2>&1; then
        ALL_HEALTHY=false
    fi

    # 检查Neo4j
    if ! curl -s http://localhost:7474 > /dev/null 2>&1; then
        ALL_HEALTHY=false
    fi

    # 检查Redis
    if ! redis-cli -h localhost -p 6379 ping > /dev/null 2>&1; then
        ALL_HEALTHY=false
    fi

    # 检查Prometheus
    if ! curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
        ALL_HEALTHY=false
    fi

    # 检查Grafana
    if ! curl -s http://localhost:13000/api/health > /dev/null 2>&1; then
        ALL_HEALTHY=false
    fi

    if [ "$ALL_HEALTHY" = true ]; then
        echo -e "${GREEN}✅ 所有服务健康${NC}"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "等待服务健康... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}❌ 部分服务未能在预期时间内启动${NC}"
    echo "请检查日志: docker-compose -f config/docker/docker-compose.production.local.yml logs"
    exit 1
fi

echo ""

# ============================================================================
# 6. 运行验证测试
# ============================================================================
echo -e "${YELLOW}📋 步骤 6/6: 运行验证测试${NC}"

echo "运行生产环境就绪性检查..."
if python3 tests/integration/test_agents_production_readiness.py; then
    echo -e "${GREEN}✅ 生产环境验证通过${NC}"
else
    echo -e "${RED}❌ 生产环境验证失败${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${GREEN}🎉 本地生产环境部署完成！${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""
echo -e "${GREEN}📍 服务访问地址：${NC}"
echo -e "  • PostgreSQL: localhost:5432 (本地)"
echo -e "  • Qdrant:     http://localhost:6333"
echo -e "  • Neo4j:      http://localhost:7474"
echo -e "  • Redis:      localhost:6379"
echo -e "  • Prometheus: http://localhost:9090"
echo -e "  • Grafana:    http://localhost:13000 (admin/athena_grafana_2024)"
echo ""
echo -e "${GREEN}📊 查看服务状态：${NC}"
echo -e "  docker-compose -f config/docker/docker-compose.production.local.yml ps"
echo ""
echo -e "${GREEN}📋 查看服务日志：${NC}"
echo -e "  docker-compose -f config/docker/docker-compose.production.local.yml logs -f"
echo ""
echo -e "${GREEN}🛑 停止所有服务：${NC}"
echo -e "  docker-compose -f config/docker/docker-compose.production.local.yml down"
echo ""
echo -e "${BLUE}============================================================${NC}"
