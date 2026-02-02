#!/bin/bash
# 小诺系统快速启动脚本

echo "🌸 小诺系统快速启动器"
echo "======================="

# 进入deploy目录
cd "$(dirname "$0")"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3"
    exit 1
fi

# 创建必要目录
mkdir -p logs data

# 直接启动修复版启动器
echo "🚀 启动小诺系统..."
python3 start_xiaonuo_fixed.py "$@"

echo "✅ 小诺系统已退出"