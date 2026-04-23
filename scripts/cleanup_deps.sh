#!/bin/bash
# 依赖文件清理脚本
# Dependency Cleanup Script
#
# 清理已整合到主pyproject.toml的冗余依赖文件

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "Athena依赖文件清理脚本"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 要清理的文件列表
declare -a FILES_TO_CLEAN=(
    "services/xiaonuo-agent-api/requirements.txt"
    "services/tool-registry-api/requirements.txt"
    "services/browser_automation_service/requirements.txt"
    "services/article-writer-service/requirements.txt"
    "deploy/requirements-multimodal.txt"
)

# 备份目录
BACKUP_DIR="$PROJECT_ROOT/.backup/requirements_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo -e "${YELLOW}备份目录: $BACKUP_DIR${NC}"
echo ""

# 1. 备份文件
echo -e "${GREEN}步骤 1/3: 备份现有文件${NC}"
echo "----------------------------------------"
for file in "${FILES_TO_CLEAN[@]}"; do
    filepath="$PROJECT_ROOT/$file"
    if [ -f "$filepath" ]; then
        mkdir -p "$BACKUP_DIR/$(dirname "$file")"
        cp "$filepath" "$BACKUP_DIR/$file"
        echo "✓ 已备份: $file"
    else
        echo "⚠ 跳过（不存在）: $file"
    fi
done
echo ""

# 2. 删除文件
echo -e "${GREEN}步骤 2/3: 删除冗余文件${NC}"
echo "----------------------------------------"
for file in "${FILES_TO_CLEAN[@]}"; do
    filepath="$PROJECT_ROOT/$file"
    if [ -f "$filepath" ]; then
        rm "$filepath"
        echo "✓ 已删除: $file"
    else
        echo "⚠ 跳过（不存在）: $file"
    fi
done
echo ""

# 3. 验证Poetry配置
echo -e "${GREEN}步骤 3/3: 验证Poetry配置${NC}"
echo "----------------------------------------"
cd "$PROJECT_ROOT"

if command -v poetry &> /dev/null; then
    echo "✓ Poetry已安装: $(poetry --version)"

    # 检查pyproject.toml语法
    if poetry check --no-interaction 2>/dev/null; then
        echo "✓ pyproject.toml语法正确"
    else
        echo -e "${RED}✗ pyproject.toml语法错误${NC}"
        echo "请运行: poetry check"
    fi

    # 显示依赖统计
    echo ""
    echo "依赖统计:"
    echo "  核心依赖: $(poetry show --no-dev | wc -l | tr -d ' ') 个"
    echo "  开发依赖: $(poetry show --only dev | wc -l | tr -d ' ') 个"
else
    echo -e "${YELLOW}⚠ Poetry未安装，跳过验证${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}清理完成！${NC}"
echo "=========================================="
echo ""
echo "备份位置: $BACKUP_DIR"
echo ""
echo "后续步骤:"
echo "  1. 运行 'poetry install' 安装依赖"
echo "  2. 运行 'poetry check' 验证配置"
echo "  3. 查看迁移指南: docs/guides/DEPENDENCY_MIGRATION_GUIDE.md"
echo ""
echo "如需回滚，从备份目录恢复文件。"
