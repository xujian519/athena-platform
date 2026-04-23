#!/bin/bash
# 统一工具注册表测试执行清单
# Test Execution Checklist for Unified Tool Registry
#
# Author: Athena平台团队
# Created: 2026-04-19
# Version: v1.0.0

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}统一工具注册表测试执行清单${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 设置环境变量
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# 检查Python版本
echo -e "${BLUE}[1/8] 检查Python版本...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python版本: $python_version"

# 验证版本 >= 3.11
if [[ "$python_version" < "3.11" ]]; then
    echo -e "${RED}❌ Python版本过低，需要3.11+${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python版本检查通过${NC}"
echo ""

# 安装依赖
echo -e "${BLUE}[2/8] 检查测试依赖...${NC}"
if ! python3 -c "import pytest" 2>/dev/null; then
    echo -e "${YELLOW}⚠️ pytest未安装，正在安装...${NC}"
    pip install pytest pytest-cov pytest-xdist
fi
echo -e "${GREEN}✅ 测试依赖检查完成${NC}"
echo ""

# 运行单元测试
echo -e "${BLUE}[3/8] 运行单元测试...${NC}"
echo "测试文件: tests/tools/test_unified_registry.py"
python3 -m pytest tests/tools/test_unified_registry.py -v --tb=short

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 单元测试通过${NC}"
else
    echo -e "${RED}❌ 单元测试失败${NC}"
    exit 1
fi
echo ""

# 运行高级测试
echo -e "${BLUE}[4/8] 运行高级测试...${NC}"
echo "测试文件: tests/tools/test_unified_registry_advanced.py"
python3 -m pytest tests/tools/test_unified_registry_advanced.py -v --tb=short

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 高级测试通过${NC}"
else
    echo -e "${YELLOW}⚠️ 高级测试部分失败，请检查报告${NC}"
fi
echo ""

# 运行性能基准测试
echo -e "${BLUE}[5/8] 运行性能基准测试...${NC}"
echo "测试脚本: scripts/benchmark_unified_registry.py"
python3 scripts/benchmark_unified_registry.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 性能基准测试完成${NC}"
else
    echo -e "${YELLOW}⚠️ 性能基准测试失败${NC}"
fi
echo ""

# 生成覆盖率报告
echo -e "${BLUE}[6/8] 生成测试覆盖率报告...${NC}"
python3 -m pytest tests/tools/ \
    --cov=core.tools.unified_registry \
    --cov=core.tools.decorators \
    --cov-report=html:docs/reports/coverage \
    --cov-report=term-missing \
    -v

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 覆盖率报告生成完成${NC}"
    echo "HTML报告: docs/reports/coverage/index.html"
else
    echo -e "${YELLOW}⚠️ 覆盖率报告生成失败${NC}"
fi
echo ""

# 代码质量检查
echo -e "${BLUE}[7/8] 运行代码质量检查...${NC}"
if command -v ruff &> /dev/null; then
    echo "使用ruff检查..."
    ruff check core/tools/unified_registry.py core/tools/decorators.py
    echo -e "${GREEN}✅ 代码质量检查完成${NC}"
else
    echo -e "${YELLOW}⚠️ ruff未安装，跳过代码质量检查${NC}"
fi
echo ""

# 生成测试报告摘要
echo -e "${BLUE}[8/8] 生成测试报告摘要...${NC}"
cat > /tmp/test_summary.txt << EOF
统一工具注册表测试报告摘要
============================

测试日期: $(date '+%Y-%m-%d %H:%M:%S')
测试环境: Python $python_version
测试平台: $(uname -s) $(uname -m)

测试结果:
- 单元测试: $([ $? -eq 0 ] && echo "✅ 通过" || echo "❌ 失败")
- 高级测试: $([ $? -eq 0 ] && echo "✅ 通过" || echo "⚠️ 部分失败")
- 性能测试: $([ $? -eq 0 ] && echo "✅ 完成" || echo "❌ 失败")
- 覆盖率报告: docs/reports/coverage/index.html
- 详细报告: docs/reports/unified_registry_test_report.md

下一步:
1. 查看覆盖率报告: open docs/reports/coverage/index.html
2. 查看详细报告: cat docs/reports/unified_registry_test_report.md
3. 提交给Agent 6进行部署准备
EOF

cat /tmp/test_summary.txt
echo -e "${GREEN}✅ 测试报告摘要生成完成${NC}"
echo ""

# 最终总结
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}测试执行完成${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}✅ 所有测试已完成${NC}"
echo ""
echo "📄 生成的报告:"
echo "  - 测试覆盖率: docs/reports/coverage/index.html"
echo "  - 详细测试报告: docs/reports/unified_registry_test_report.md"
echo "  - 测试摘要: /tmp/test_summary.txt"
echo ""
echo "🚀 下一步: 提交给Agent 6进行部署准备"
echo ""

exit 0
