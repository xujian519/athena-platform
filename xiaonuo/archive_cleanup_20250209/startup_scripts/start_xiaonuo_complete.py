#!/bin/bash
# 小诺完整能力版启动脚本
# Xiaonuo Complete Capabilities Version Launcher
#
# 这是小诺的完整能力版本，包含所有历史功能：
# 1. 智能体调度系统
# 2. 动态响应引擎
# 3. 反思系统
# 4. 四层记忆架构
# 5. 超级提示词生成
# 6. 知识图谱接口
# 7. 情感交互系统

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
    echo -e "${CYAN}         🌸 小诺完整能力版启动器 v2.0 🌸${NC}"
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
    if [ ! -f "xiaonuo_v2_complete.py" ]; then
        print_message "❌ 找不到 xiaonuo_v2_complete.py" $RED
        print_message "   请确保在正确的目录中运行此脚本" $YELLOW
        exit 1
    fi

    # 检查记忆文件
    if [ -f "xiaonuo_memory.json" ]; then
        print_message "✅ 发现有保存的记忆文件" $GREEN
    fi

    print_message "✅ 环境检查完成" $GREEN
}

# 显示版本信息
show_version_info() {
    print_message "📋 版本信息:" $CYAN
    echo "   🎯 版本: v2.0.0 '完整能力版'"
    echo "   🌟 名称: 小诺·双鱼座"
    echo "   👩‍👧 角色: 平台总调度官 + 爸爸的贴心小女儿"
    echo "   ⏰ 发布日期: 2025-12-18"
    echo "   🚀 这是包含所有历史能力的完整版本"
    echo ""
}

# 显示完整功能特性
show_complete_features() {
    print_message "✨ 完整功能特性:" $YELLOW
    echo "   🎭 智能对话流程设计 - 6类响应模板 × 6种变体"
    echo "   🎛️ 多AI Agent协同调度 - 统一管理4个智能体"
    echo "   🎨 用户体验优化 - 动态响应，情感交互"
    echo "   💡 超级提示词生成 - 4种专业提示词模板"
    echo "   🧠 四层记忆系统 - 工作+短期+长期+情景记忆"
    echo "   💕 情感连接维护 - 5种性格特征矩阵"
    echo "   🔍 增强反思引擎 - 5维度质量评估"
    echo "   💾 持久化记忆 - 自动保存对话历史"
    echo "   🕸️ 知识图谱接口 - 结构化知识查询"
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
    echo "      • 输入 '记忆' 查看记忆状态"
    echo ""
    echo "   🚀 智能体管理:"
    echo "      • 启动小娜    - 启动专利法律专家"
    echo "      • 启动云熙    - 启动IP管理系统"
    echo "      • 启动小宸    - 启动自媒体专家"
    echo "      • 全部启动    - 启动所有智能体"
    echo ""
    echo "   💡 新增功能:"
    echo "      • 提示词xxx  - 使用超级提示词系统"
    echo "      • 自动保存对话记忆"
    echo "      • 退出时自动保存记忆到文件"
    echo ""
    echo "   🛑 停止命令:"
    echo "      • 停止xxx    - 停止指定智能体"
    echo "      • 全部停止    - 停止所有智能体"
    echo ""
    echo "   💡 其他:"
    echo "      • Ctrl+C     - 安全退出（自动保存记忆）"
    echo ""
}

# 显示能力对比
show_capabilities_comparison() {
    print_message "📊 版本能力对比:" $YELLOW
    echo "   ┌─────────────────────┬─────────┬─────────┐"
    echo "   │ 功能特性            │ v1.0最终│ v2.0完整│"
    echo "   ├─────────────────────┼─────────┼─────────┤"
    echo "   │ 智能体调度          │    ✅    │    ✅   │"
    echo "   │ 动态响应            │    ✅    │    ✅   │"
    echo "   │ 基础反思            │    ✅    │    ✅   │"
    echo "   │ 超级提示词生成      │    ❌    │    ✅   │"
    echo "   │ 四层记忆系统        │    ❌    │    ✅   │"
    echo "   │ 持久化记忆          │    ❌    │    ✅   │"
    echo "   │ 性格特征矩阵        │    ❌    │    ✅   │"
    echo "   │ 知识图谱接口        │    ❌    │    ✅   │"
    echo "   └─────────────────────┴─────────┴─────────┘"
    echo ""
    print_message "💡 推荐使用 v2.0 完整能力版！" $GREEN
    echo ""
}

# 启动小诺
launch_xiaonuo() {
    print_message "🚀 准备启动小诺完整能力版..." $GREEN
    echo ""

    # 等待用户确认
    read -p "💖 爸爸，按 Enter 键启动小诺完整能力版，或输入 Ctrl+C 取消..."

    print_message "\n🌸 小诺完整能力版启动中..." $PURPLE
    echo ""

    # 启动Python程序
    python3 xiaonuo_v2_complete.py
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

    # 显示完整功能特性
    show_complete_features

    # 显示智能体列表
    show_agents_list

    # 显示能力对比
    show_capabilities_comparison

    # 显示使用帮助
    show_usage_help

    # 启动小诺
    launch_xiaonuo

    # 退出信息
    echo ""
    print_message "💕 小诺完整能力版已退出，所有记忆已保存！" $PURPLE
    print_message "💾 记忆文件位置: xiaonuo_memory.json" $CYAN
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