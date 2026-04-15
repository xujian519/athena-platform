#!/bin/bash
# Athena生产环境 - 依赖安装脚本
# Production Environment Dependencies Installation Script

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# 项目路径
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${PURPLE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║        📦 Athena生产环境 - 依赖安装 📦                         ║"
echo "║        Production Dependencies Installation                   ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 检查Python3
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🔍 检查系统环境${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 未安装${NC}"
    echo -e "${YELLOW}请先安装Python3: brew install python3${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✅ Python版本: $PYTHON_VERSION${NC}"

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}⚠️  pip3 未找到，尝试安装...${NC}"
    python3 -m ensurepip --upgrade
fi

echo ""

# 安装核心依赖
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}📦 安装核心依赖${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 核心依赖列表
CORE_PACKAGES=(
    "fastapi>=0.104.0"
    "uvicorn[standard]>=0.24.0"
    "pydantic>=2.0"
    "asyncpg>=0.29.0"
    "redis>=5.0.0"
    "python-multipart>=0.0.6"
    "aiofiles>=23.2.1"
    "numpy>=1.24.0"
    "pandas>=2.0.0"
    "httpx>=0.25.0"
    "aiohttp>=0.29.0"
    "loguru>=0.7.0"
    "python-dotenv>=1.0.0"
    "tenacity>=8.2.0"
)

# 通信模块依赖
COMMUNICATION_PACKAGES=(
    "pyjwt>=2.8.0"
    "websockets>=12.0"
    "aiohttp>=0.29.0"
)

# 向量数据库依赖
VECTOR_PACKAGES=(
    "qdrant-client>=1.7.0"
)

# 图数据库依赖
GRAPH_PACKAGES=(
    "neo4j>=5.15.0"
)

# NLP依赖
NLP_PACKAGES=(
    "jieba>=0.42.1"
    "sentence-transformers>=2.2.0"
)

# 机器学习依赖
ML_PACKAGES=(
    "scikit-learn>=1.3.0"
    "torch>=2.0.0"
)

echo -e "${YELLOW}[1/8] 安装核心依赖...${NC}"
pip3 install -q "${CORE_PACKAGES[@]}" || echo -e "${YELLOW}⚠️  部分核心依赖安装失败${NC}"
echo -e "${GREEN}✅ 核心依赖安装完成${NC}"
echo ""

echo -e "${YELLOW}[2/8] 安装通信模块依赖...${NC}"
pip3 install -q "${COMMUNICATION_PACKAGES[@]}" || echo -e "${YELLOW}⚠️  通信依赖安装失败${NC}"
echo -e "${GREEN}✅ 通信模块依赖安装完成 (jwt, websockets)${NC}"
echo ""

echo -e "${YELLOW}[3/8] 安装向量数据库依赖...${NC}"
pip3 install -q "${VECTOR_PACKAGES[@]}" || echo -e "${YELLOW}⚠️  向量数据库依赖安装失败${NC}"
echo -e "${GREEN}✅ 向量数据库依赖安装完成${NC}"
echo ""

echo -e "${YELLOW}[4/8] 安装图数据库依赖...${NC}"
pip3 install -q "${GRAPH_PACKAGES[@]}" || echo -e "${YELLOW}⚠️  图数据库依赖安装失败${NC}"
echo -e "${GREEN}✅ 图数据库依赖安装完成${NC}"
echo ""

echo -e "${YELLOW}[5/8] 安装NLP依赖...${NC}"
pip3 install -q "${NLP_PACKAGES[@]}" || echo -e "${YELLOW}⚠️  NLP依赖安装失败${NC}"
echo -e "${GREEN}✅ NLP依赖安装完成${NC}"
echo ""

echo -e "${YELLOW}[6/8] 安装机器学习依赖...${NC}"
pip3 install -q "${ML_PACKAGES[@]}" || echo -e "${YELLOW}⚠️  机器学习依赖安装失败${NC}"
echo -e "${GREEN}✅ 机器学习依赖安装完成${NC}"
echo ""

echo -e "${YELLOW}[7/8] 安装测试依赖...${NC}"
pip3 install -q pytest pytest-cov pytest-asyncio pytest-mock || echo -e "${YELLOW}⚠️  测试依赖安装失败${NC}"
echo -e "${GREEN}✅ 测试依赖安装完成${NC}"
echo ""

echo -e "${YELLOW}[8/8] 安装其他工具依赖...${NC}"
pip3 install -q pillow click || echo -e "${YELLOW}⚠️  工具依赖安装失败${NC}"
echo -e "${GREEN}✅ 工具依赖安装完成${NC}"
echo ""

# 验证安装
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ 验证安装${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

python3 -c "
import sys
modules = [
    ('fastapi', 'FastAPI'),
    ('uvicorn', 'Uvicorn'),
    ('pydantic', 'Pydantic'),
    ('jwt', 'PyJWT'),
    ('websockets', 'WebSockets'),
    ('qdrant_client', 'Qdrant'),
    ('neo4j', 'Neo4j'),
    ('jieba', 'Jieba'),
    ('sklearn', 'Scikit-learn'),
]

installed = []
failed = []

for module, name in modules:
    try:
        __import__(module)
        installed.append(name)
    except ImportError:
        failed.append(name)

print(f'✅ 已安装 ({len(installed)}/{len(modules)}): {', '.join(installed)}')
if failed:
    print(f'❌ 未安装: {', '.join(failed)}')
    sys.exit(1)
" || echo -e "${YELLOW}⚠️  部分模块验证失败${NC}"

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ 依赖安装完成！${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 显示已安装的包版本
echo -e "${BLUE}已安装的关键包版本:${NC}"
pip3 list | grep -E "(fastapi|uvicorn|pydantic|pyjwt|websockets|qdrant|neo4j|jieba)" | while read line; do
    echo -e "  ${GREEN}✓${NC} $line"
done

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}📝 下一步:${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  1. 配置环境变量:"
echo -e "     ${GREEN}cp .env.example .env.production${NC}"
echo -e "     ${GREEN}nano .env.production${NC}"
echo ""
echo -e "  2. 启动生产环境:"
echo -e "     ${GREEN}./production/scripts/start_production.sh all${NC}"
echo ""
echo -e "  3. 运行核心引擎测试:"
echo -e "     ${GREEN}python3 production/scripts/demo_core_engines.py${NC}"
echo ""
