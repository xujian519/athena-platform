#!/bin/bash
# 小娜自然语言交互系统 - 快速启动脚本
#
# 注意：生产环境请使用 start_xiaona_production.sh 启动API服务
# 此脚本仅用于开发环境的交互式对话

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║  🌟 小娜 - 专利法律AI助手 🌟                                  ║"
echo "║                                                              ║"
echo "║  自然语言交互系统 (开发模式)                                   ║"
echo "║  版本: v2.1                                                 ║"
echo "║  日期: 2025-12-26                                           ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# 检测启动模式
if [ "$1" = "--production" ] || [ "$1" = "-p" ]; then
    echo "🚀 启动生产API服务..."
    exec "$(dirname "$0")/start_xiaona_production.sh"
fi

echo "⚠️  交互式模式 (仅用于开发调试)"
echo "💡 生产环境请使用: bash start_xiaona.sh --production"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/services"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3"
    echo "请先安装 Python 3.7 或更高版本"
    exit 1
fi

# 检查必要文件
if [ ! -f "xiaona_natural_interface.py" ]; then
    echo "❌ 错误: 未找到 xiaona_natural_interface.py"
    echo "请确认文件在正确位置"
    exit 1
fi

# 检查是否在非交互式终端
if ! [ -t 0 ]; then
    echo "❌ 错误: 检测到非交互式环境"
    echo "交互式模式需要TTY终端"
    echo ""
    echo "💡 生产环境请使用:"
    echo "   bash start_xiaona.sh --production"
    echo "   或"
    echo "   bash start_xiaona_production.sh"
    exit 1
fi

echo "✅ 环境检查完成"
echo "🚀 正在启动小娜交互式界面..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 启动小娜
python3 xiaona_natural_interface.py

# 退出处理
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "👋 小娜已退出"
echo "💡 您可以随时重新运行此脚本启动小娜"
