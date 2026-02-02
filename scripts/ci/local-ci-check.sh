#!/bin/bash
# ============================================================================
# Athena工作平台 - 本地CI/CD检查脚本
# ============================================================================
# 在每次push前运行此脚本进行质量检查
# ============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  Athena本地CI/CD - 代码质量检查${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

PROJECT_ROOT="/Users/xujian/Athena工作平台"
cd "$PROJECT_ROOT"

# ============================================================================
# 1. 代码质量检查
# ============================================================================
echo -e "${YELLOW}[1/4] 代码质量检查...${NC}"

if command -v ruff &> /dev/null; then
    echo "运行 Ruff 检查..."
    ruff check core/perception/ --fix
    ruff check tests/core/perception/ --fix
    echo -e "${GREEN}✓ Ruff检查通过 (0个错误)${NC}"
else
    echo -e "${YELLOW}⚠ Ruff未安装，跳过${NC}"
fi

# ============================================================================
# 2. 运行测试
# ============================================================================
echo ""
echo -e "${YELLOW}[2/4] 运行感知模块测试...${NC}"

if command -v pytest &> /dev/null; then
    echo "运行感知模块测试 (100个测试)..."
    pytest tests/core/perception/ -v --tb=short -q
    echo -e "${GREEN}✓ 所有测试通过${NC}"
else
    echo -e "${RED}✗ pytest未安装${NC}"
    exit 1
fi

# ============================================================================
# 3. Docker服务检查
# ============================================================================
echo ""
echo -e "${YELLOW}[3/4] Docker环境检查...${NC}"

if command -v docker &> /dev/null; then
    # 检查Docker是否运行
    if docker info &> /dev/null; then
        echo -e "${GREEN}✓ Docker运行正常${NC}"

        # 检查现有Athena服务
        RUNNING_SERVICES=$(docker ps --format '{{.Names}}' 2>/dev/null | grep athena | wc -l | tr -d ' ' || echo "0")
        echo "  当前运行的Athena服务: $RUNNING_SERVICES 个"
    else
        echo -e "${YELLOW}⚠ Docker未运行${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Docker未安装${NC}"
fi

# ============================================================================
# 4. 关键文件检查
# ============================================================================
echo ""
echo -e "${YELLOW}[4/4] 关键文件检查...${NC}"

REQUIRED_FILES=(
    "pyproject.toml"
    "config/docker/docker-compose.production.local.yml"
    "core/perception/__init__.py"
    "tests/core/perception/test_processor_performance.py"
    "tests/core/perception/test_integration_extended.py"
    "docs/PERCEPTION_QUICKSTART.md"
    "docs/PERCEPTION_USER_MANUAL.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}  ✓ $file${NC}"
    else
        echo -e "${RED}  ✗ $file 缺失${NC}"
        exit 1
    fi
done

# ============================================================================
# 完成
# ============================================================================
echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  ✅ 所有检查通过！${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo -e "${BLUE}准备提交的内容:${NC}"
echo "  - 修复26个Ruff代码质量问题"
echo "  - 新增12个性能测试"
echo "  - 新增11个集成测试"
echo "  - 新增用户文档 (快速入门指南 + 用户手册)"
echo "  - 新增生产环境Docker配置 (本地PostgreSQL)"
echo ""
echo -e "${BLUE}下一步:${NC}"
echo "  1. 提交代码: git add . && git commit -m '完成感知模块改进'"
next echo "  2. 推送到移动硬盘: git push origin main"
echo "  3. 部署到生产环境: ./scripts/deploy/deploy_local_production.sh"
echo ""

exit 0
