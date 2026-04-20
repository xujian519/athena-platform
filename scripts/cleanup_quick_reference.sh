#!/bin/bash

################################################################################
# Athena工作平台 - 快速清理脚本
# 功能：使用默认配置快速清理项目，无需交互确认
# 作者：Claude Code
# 日期：2026-04-20
# 版本：v1.0
################################################################################

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="/Users/xujian/Athena工作平台"
cd "$PROJECT_ROOT" || exit 1

# 快速清理模式标志
QUICK_MODE=true

# 导入主清理脚本
# source ./scripts/cleanup_project.sh

################################################################################
# 快速清理函数
################################################################################

quick_cleanup() {
    echo -e "${BLUE}快速清理模式${NC}"
    echo "========================================"

    local start_time=$(date +%s)
    local deleted_count=0

    # 1. 清理备份文件（无确认）
    echo -e "\n${YELLOW}[1/4]${NC} 清理备份文件..."
    find . -name "*.bak" -o -name "*.backup" | while read -r file; do
        [ -f "$file" ] && rm -f "$file" && echo "  ✓ 删除: $file" && ((deleted_count++))
    done
    [ -f "requirements_backup.txt" ] && rm -f "requirements_backup.txt" && ((deleted_count++))

    # 2. 清理Python缓存（无确认）
    echo -e "\n${YELLOW}[2/4]${NC} 清理Python缓存..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete 2>/dev/null || true
    echo "  ✓ Python缓存已清理"

    # 3. 清理临时文件
    echo -e "\n${YELLOW}[3/4]${NC} 清理临时文件..."
    [ -d "data/trademark_rules/temp" ] && rm -rf "data/trademark_rules/temp" && ((deleted_count++))
    find . -name "*.tmp" -type f -delete 2>/dev/null || true

    # 4. 清理过期测试报告（30天前）
    echo -e "\n${YELLOW}[4/4]${NC} 清理过期测试报告..."
    find tests/results/ -name "*.json" -type f -mtime +30 2>/dev/null | while read -r report; do
        rm -f "$report" && echo "  ✓ 删除: $report" && ((deleted_count++))
    done

    # 计算耗时
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # 显示统计
    echo ""
    echo "========================================"
    echo -e "${GREEN}✅ 快速清理完成！${NC}"
    echo "清理文件数: $deleted_count"
    echo "耗时: ${duration}秒"
    echo ""
    echo "提示: 运行 './scripts/cleanup_project.sh' 进行完整清理"
}

# 执行快速清理
quick_cleanup
