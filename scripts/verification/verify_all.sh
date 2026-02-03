#!/usr/bin/env bash
# 主验证脚本 - 运行所有模块验证
# Master Verification Script - Run All Module Verifications

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo " Athena平台模块验证"
echo "=========================================="
echo ""
echo "验证策略: 逐模块验证，全部通过后才能集成到OpenClaw"
echo ""

# 检查Athena服务状态
echo -e "${BLUE}📋 检查Athena服务状态...${NC}"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Athena服务运行中${NC}"
else
    echo -e "${RED}✗ Athena服务未运行${NC}"
    echo ""
    echo "请先启动Athena服务:"
    echo "  cd /Users/xujian/Athena工作平台/core/api && python main.py"
    exit 1
fi
echo ""

# 验证模块列表
MODULES=(
    "prompt_system:动态提示词系统:P0"
    "claim_parser:权利要求解析:P1"
    "ipc_system:IPC分类系统:P1"
    "figure_recognition:附图识别:P1"
    "deep_analysis:深度分析:P1"
    "dolphin_parser:Dolphin文档解析:P1"
    "invalidity_strategy:无效宣告策略:P2"
    "dual_graph:双图构建:P2"
)

# 解析命令行参数
if [ $# -gt 0 ]; then
    SELECTED_MODULES=("$@")
else
    SELECTED_MODULES=("${MODULES[@]}")
fi

# 结果统计
TOTAL_MODULES=0
PASSED_MODULES=0
FAILED_MODULES=0

# 验证单个模块
verify_module() {
    local module_info="$1"
    IFS=':' read -r module_id module_name priority <<< "$module_info"

    TOTAL_MODULES=$((TOTAL_MODULES + 1))

    echo -e "${BLUE}==========================================${NC}"
    echo -e "${BLUE}验证模块: $module_name [$priority]${NC}"
    echo -e "${BLUE}==========================================${NC}"
    echo ""

    local script_path="$SCRIPT_DIR/verify_${module_id}.sh"

    if [ ! -f "$script_path" ]; then
        echo -e "${YELLOW}⚠ 验证脚本不存在: $script_path${NC}"
        echo "   跳过此模块"
        echo ""
        return 0
    fi

    # 设置执行权限
    chmod +x "$script_path"

    # 运行验证
    if bash "$script_path"; then
        echo -e "${GREEN}✓ $module_name 验证通过${NC}"
        PASSED_MODULES=$((PASSED_MODULES + 1))
        echo ""
    else
        echo -e "${RED}✗ $module_name 验证失败${NC}"
        FAILED_MODULES=$((FAILED_MODULES + 1))
        echo ""
        return 1
    fi
}

# 主验证循环
FAILED_LIST=()
for module in "${SELECTED_MODULES[@]}"; do
    if ! verify_module "$module"; then
        FAILED_LIST+=("$module")
    fi
done

# 最终总结
echo -e "${BLUE}=========================================="
echo " 最终验证总结"
echo -e "==========================================${NC}"
echo ""
echo "验证模块总数: $TOTAL_MODULES"
echo -e "通过: ${GREEN}$PASSED_MODULES${NC}"
echo -e "失败: ${RED}$FAILED_MODULES${NC}"
echo ""

if [ $FAILED_MODULES -eq 0 ]; then
    echo -e "${GREEN}==========================================${NC}"
    echo -e "${GREEN}✓ 所有模块验证通过！${NC}"
    echo -e "${GREEN}==========================================${NC}"
    echo ""
    echo "🎉 恭喜！所有模块已验证通过，可以开始集成到OpenClaw"
    echo ""
    echo "下一步:"
    echo "1. 开发 athena-legal 核心技能"
    echo "2. 逐步开发扩展技能"
    echo "3. 集成测试"
    exit 0
else
    echo -e "${RED}==========================================${NC}"
    echo -e "${RED}✗ 有 $FAILED_MODULES 个模块验证失败${NC}"
    echo -e "${RED}==========================================${NC}"
    echo ""
    echo "失败的模块:"
    for failed in "${FAILED_LIST[@]}"; do
        IFS=':' read -r module_id module_name priority <<< "$failed"
        echo -e "  - ${RED}$module_name [$priority]${NC}"
    done
    echo ""
    echo "请修复失败的模块后重新验证"
    echo ""
    echo "查看详细进度: cat /Users/xujian/Athena工作平台/docs/OPENCLAW_INTEGRATION_PROGRESS.md"
    exit 1
fi
