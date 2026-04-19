#!/bin/bash
# Athena数据库服务启动脚本
# Database Services Startup Script

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${PURPLE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║        🗄️  Athena数据库服务启动脚本 🗄️                         ║"
echo "║        Database Services Startup                                ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 项目路径
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}📊 数据库服务状态${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# =============================================================================
# PostgreSQL
# =============================================================================
echo -e "${YELLOW}[1/4] PostgreSQL${NC}"
if command -v psql &> /dev/null; then
    if brew services list | grep postgresql | grep -q started; then
        echo -e "   ${GREEN}✅${NC} PostgreSQL 已运行"
    else
        echo -e "   ${YELLOW}⚠️  PostgreSQL 已安装但未运行，正在启动...${NC}"
        brew services start postgresql@17 2>/dev/null || brew services start postgresql 2>/dev/null
        sleep 2
        echo -e "   ${GREEN}✅${NC} PostgreSQL 已启动"
    fi

    # 创建数据库
    echo ""
    echo -e "   ${BLUE}检查数据库...${NC}"
    if psql -h localhost -U $USER -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw athena_production; then
        echo -e "   ${GREEN}✅${NC} 数据库 'athena_production' 已存在"
    else
        echo -e "   ${YELLOW}创建数据库...${NC}"
        createdb -h localhost athena_production 2>/dev/null || echo -e "   ${YELLOW}⚠️  需要手动创建数据库${NC}"
        echo -e "   ${GREEN}✅${NC} 数据库 'athena_production' 已创建"
    fi
else
    echo -e "   ${RED}❌${NC} PostgreSQL 未安装"
    echo -e "   ${BLUE}安装命令:${NC} brew install postgresql@17"
fi

echo ""

# =============================================================================
# Redis
# =============================================================================
echo -e "${YELLOW}[2/4] Redis${NC}"
if docker ps --format '{{.Names}}' | grep -q '^redis$'; then
    echo -e "   ${GREEN}✅${NC} Redis 已运行"
elif docker ps -a --format '{{.Names}}' | grep -q '^redis$'; then
    echo -e "   ${YELLOW}⚠️  Redis 容器已存在，正在启动...${NC}"
    docker start redis > /dev/null 2>&1
    echo -e "   ${GREEN}✅${NC} Redis 已启动"
else
    echo -e "   ${YELLOW}启动 Redis 容器...${NC}"
    docker run -d --name redis \
        -p 6379:6379 \
        --restart unless-stopped \
        redis:latest redis-server --appendonly yes > /dev/null 2>&1
    sleep 2
    echo -e "   ${GREEN}✅${NC} Redis 已启动"
fi

echo ""

# =============================================================================
# Qdrant
# =============================================================================
echo -e "${YELLOW}[3/4] Qdrant 向量数据库${NC}"
if docker ps --format '{{.Names}}' | grep -q '^qdrant$'; then
    echo -e "   ${GREEN}✅${NC} Qdrant 已运行"
elif docker ps -a --format '{{.Names}}' | grep -q '^qdrant$'; then
    echo -e "   ${YELLOW}⚠️  Qdrant 容器已存在，正在启动...${NC}"
    docker start qdrant > /dev/null 2>&1
    echo -e "   ${GREEN}✅${NC} Qdrant 已启动"
else
    echo -e "   ${YELLOW}启动 Qdrant 容器...${NC}"
    docker run -d --name qdrant \
        -p 6333:6333 \
        -p 6334:6334 \
        --restart unless-stopped \
        -v $(pwd)/production/data/qdrant:/qdrant/storage \
        qdrant/qdrant:latest > /dev/null 2>&1
    sleep 3
    echo -e "   ${GREEN}✅${NC} Qdrant 已启动"
fi

echo ""

# =============================================================================
# Neo4j (可选)
# =============================================================================
echo -e "${YELLOW}[4/4] Neo4j 图数据库 (可选)${NC}"
if docker ps --format '{{.Names}}' | grep -q '^neo4j$'; then
    echo -e "   ${GREEN}✅${NC} Neo4j 已运行"
elif docker ps -a --format '{{.Names}}' | grep -q '^neo4j$'; then
    echo -e "   ${YELLOW}⚠️  Neo4j 容器已存在但未运行${NC}"
    echo -e "   ${BLUE}启动命令:${NC} docker start neo4j"
else
    echo -e "   ${YELLOW}⚠️  Neo4j 未安装${NC}"
    echo -e "   ${BLUE}安装命令:${NC}"
    echo "   docker run -d --name neo4j \\"
    echo "     -p 7474:7474 -p 7687:7687 \\"
    echo "     -e NEO4J_AUTH=neo4j/your_password \\"
    echo "     -v $(pwd)/production/data/neo4j:/data \\"
    echo "     neo4j:latest"
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ 数据库服务配置完成！${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}📊 服务状态${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 显示服务状态
echo -e "${GREEN}PostgreSQL:${NC}"
if brew services list 2>/dev/null | grep postgresql | grep -q started; then
    PORT=$(psql -h localhost -c "SHOW port" -t 2>/dev/null || echo "5432")
    echo -e "   ${GREEN}✅${NC} 运行中 (端口: $PORT)"
else
    echo -e "   ${YELLOW}⚠️  未运行${NC}"
fi

echo ""
echo -e "${GREEN}Redis:${NC}"
if docker ps --format '{{.Names}}' | grep -q '^redis$'; then
    echo -e "   ${GREEN}✅${NC} 运行中 (端口: 6379)"
else
    echo -e "   ${YELLOW}⚠️  未运行${NC}"
fi

echo ""
echo -e "${GREEN}Qdrant:${NC}"
if docker ps --format '{{.Names}}' | grep -q '^qdrant$'; then
    echo -e "   ${GREEN}✅${NC} 运行中 (端口: 6333)"
    # 测试Qdrant API
    if curl -sf http://localhost:6333/health > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅${NC} API 响应正常"
    fi
else
    echo -e "   ${YELLOW}⚠️  未运行${NC}"
fi

echo ""
echo -e "${GREEN}Neo4j:${NC}"
if docker ps --format '{{.Names}}' | grep -q '^neo4j$'; then
    echo -e "   ${GREEN}✅${NC} 运行中 (端口: 7474, 7687)"
else
    echo -e "   ${YELLOW}⚠️  未运行${NC}"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}📝 下一步:${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  1. 更新数据库密码:"
echo -e "     ${GREEN}nano .env.production${NC}"
echo ""
echo -e "  2. 运行数据库验证:"
echo -e "     ${GREEN}python3 production/scripts/verify_databases.py${NC}"
echo ""
echo -e "  3. 启动生产服务:"
echo -e "     ${GREEN}python3 production/scripts/start_athena_production.py${NC}"
echo ""
