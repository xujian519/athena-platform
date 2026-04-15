#!/bin/bash

# 任务管理系统依赖安装脚本
# Task Management System Dependencies Installation Script

echo "🚀 安装任务管理系统依赖..."

# 检查Python版本
python_version=$(python3 --version 2>&1)
echo "🐍 Python版本: $python_version"

# 安装必要的Python包
echo "📦 安装Python依赖包..."

# macOS系统通知支持
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 macOS系统 - 检查通知功能..."
    # macOS的osascript内置支持，无需额外安装
fi

# Linux系统通知支持
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "🐧 Linux系统 - 检查notify-send..."
    if ! command -v notify-send &> /dev/null; then
        echo "安装libnotify-bin..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y libnotify-bin
        elif command -v yum &> /dev/null; then
            sudo yum install -y libnotify
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y libnotify
        else
            echo "⚠️ 无法自动安装notify-send，请手动安装"
        fi
    else
        echo "✅ notify-send已安装"
    fi
fi

# Windows系统通知支持
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    echo "🪟 Windows系统 - 检查通知支持..."
    # Windows通知通过win10toast包实现
fi

# 安装Python依赖
echo "📚 安装Python依赖包..."

# 创建requirements.txt
cat > requirements.txt << EOF
# 任务管理系统依赖
schedule>=1.2.0
# macOS通知支持（内置）
# Linux通知支持通过系统notify-send
# Windows通知支持
win10toast>=0.9; sys_platform == "win32"
EOF

# 安装依赖
pip3 install -r requirements.txt

echo ""
echo "✅ 依赖安装完成！"
echo ""
echo "📋 任务管理系统功能:"
echo "• ✅ 定时提醒 (Python schedule)"
echo "• ✅ 系统通知 (osascript/notify-send/win10toast)"
echo "• ✅ 持久化存储 (JSON文件)"
echo "• ✅ 任务调度 (多线程)"
echo ""
echo "🚀 启动命令:"
echo "  python3 scripts/start_task_management_system.py"
echo ""
echo "🧪 测试命令:"
echo "  python3 scripts/start_task_management_system.py --test"
echo ""
echo "📊 统计命令:"
echo "  python3 scripts/start_task_management_system.py --stats"
echo ""
echo "🔄 守护进程模式:"
echo "  python3 scripts/start_task_management_system.py --daemon"