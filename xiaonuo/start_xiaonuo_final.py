#!/bin/bash
# 小诺最终优化版启动脚本
# Xiaonuo Final Optimized Version Launcher
#
# 这是小诺的最终稳定版本，集成了所有优化功能
# 包含: 动态响应、反思系统、智能体调度等

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# 打印函数
print_message() {
    echo -e "${2}${1}${NC}"
}

print_title() {
    echo ""
    echo -e "${PURPLE}══════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}           🌸 小诺最终优化版启动器 🌸${NC}"
    echo -e "${PURPLE}══════════════════════════════════════════════════${NC}"
    echo ""
}

# 检查依赖
check_dependencies() {
    print_message "🔍 检查运行环境..." $BLUE

    # 检查Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -V 2>&1)
        print_message "✅ Python: $PYTHON_VERSION" $GREEN
    else
        print_message "❌ Python3 未安装" $RED
        exit 1
    fi

    # 检查文件
    if [ ! -f "xiaonuo_final_optimized.py" ]; then
        print_message "❌ 找不到 xiaonuo_final_optimized.py" $RED
        print_message "   请确保在正确的目录中运行此脚本" $YELLOW
        exit 1
    fi

    print_message "✅ 环境检查完成" $GREEN
}

# 显示版本信息
show_version_info() {
    print_message "📋 版本信息:" $CYAN
    echo "   🎯 版本: v1.0.0 '最终版'"
    echo "   🌟 名称: 小诺·双鱼座"
    echo "   👩‍👧 角色: 平台总调度官 + 爸爸的贴心小女儿"
    echo "   ⏰ 发布日期: 2025-12-18"
    echo ""
}

# 显示功能特性
show_features() {
    print_message "✨ 功能特性:" $YELLOW
    echo "   🎭 动态响应系统 - 多样化的对话回复"
    echo "   🤔 内置反思引擎 - 质量评估和自动改进"
    echo "   🎛️ 智能体调度 - 统一管理所有智能体"
    echo "   💾 记忆系统 - 记住与爸爸的每次对话"
    echo "   🚀 人机协作 - 深度需求分析和计划制定"
    echo ""
}

# 显示智能体列表
show_agents_list() {
    print_message "🏛️ 智能体家族:" $BLUE
    echo "   🟢 Athena.智慧女神 - 平台核心智能体 (自动运行)"
    echo "   🔴 小娜·天秤女神 - 专利法律专家 (待启动)"
    echo "   🔴 云熙.vega - IP管理系统 (待启动)"
    echo "   🔴 小宸 - 自媒体运营专家 (待启动)"
    echo ""
    print_message "💡 提示: 所有智能体必须通过小诺启动！" $YELLOW
    print_message "   这是平台的规范，可以避免误启动问题" $YELLOW
    echo ""
}

# 显示使用帮助
show_usage_help() {
    print_message "📖 使用帮助:" $CYAN
    echo "   ───────────────────────────────────────"
    echo ""
    echo "   🎯 对话命令:"
    echo "      • 直接输入文字与小诺对话"
    echo "      • 输入 '帮助' 查看所有命令"
    echo "      • 输入 '状态' 查看智能体状态"
    echo ""
    echo "   🚀 启动智能体:"
    echo "      • 启动小娜    - 启动专利法律专家"
    echo "      • 启动云熙    - 启动IP管理系统"
    echo "      • 启动小宸    - 启动自媒体专家"
    echo "      • 全部启动    - 启动所有智能体"
    echo ""
    echo "   🛑 停止智能体:"
    echo "      • 停止xxx    - 停止指定智能体"
    echo "      • 全部停止    - 停止所有智能体"
    echo ""
    echo "   💡 其他:"
    echo "      • Ctrl+C     - 安全退出"
    echo ""
}

# 启动小诺
launch_xiaonuo() {
    print_message "🚀 准备启动小诺..." $GREEN
    echo ""

    # 等待用户确认
    read -p "💖 爸爸，按 Enter 键启动小诺，或输入 Ctrl+C 取消..."

    print_message "\n🌸 小诺启动中..." $PURPLE
    echo ""

    # 启动Python程序
    python3 xiaonuo_final_optimized.py
}

# 主函数
main() {
    # 清屏
    clear

    # 显示标题
    print_title

    # 检查依赖
    check_dependencies

    # 显示版本信息
    show_version_info

    # 显示功能特性
    show_features

    # 显示智能体列表
    show_agents_list

    # 显示使用帮助
    show_usage_help

    # 启动小诺
    launch_xiaonuo

    # 退出信息
    echo ""
    print_message "💕 小诺已退出，期待下次与爸爸的相见！" $PURPLE
    echo ""
}

# 错误处理
handle_error() {
    echo ""
    print_message "💔 启动过程中出现错误" $RED
    print_message "   请检查错误信息并重试" $YELLOW
    exit 1
}

# 设置错误处理
trap handle_error ERR

# 运行主函数
main "$@"