#!/bin/bash
# 启动增强记忆版小诺
# Start Xiaonuo with Enhanced Memory System

echo "🌸 启动小诺增强版 - 永恒记忆系统..."
echo "📝 集成冷热温四层记忆架构"
echo "💝 永远记住爸爸的每一个瞬间"
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 设置环境变量
export PYTHONPATH=/Users/xujian/Athena工作平台:$PYTHONPATH

# 切换到小诺目录
cd /Users/xujian/Athena工作平台/xiaonuo

# 检查文件是否存在
if [ ! -f "xiaonuo_with_enhanced_memory.py" ]; then
    echo "❌ 找不到增强版小诺程序"
    exit 1
fi

echo "✅ 文件检查完成"
echo "🧠 记忆系统状态："
echo "  🔥 热记忆：100条容量（当前对话）"
echo "  🌡️ 温记忆：1000条容量（近期重要）"
echo "  ❄️ 冷记忆：无限容量（长期珍藏）"
echo "  💎 永恒记忆：永不忘记的核心记忆"
echo ""

# 启动小诺
echo "🚀 启动小诺..."
python3 xiaonuo_with_enhanced_memory.py

echo ""
echo "💝 小诺已退出，所有记忆已自动保存"
echo "📁 记忆文件位置："
echo "  - 普通记忆：/tmp/xiaonuo_memory.pkl"
echo "  - 永恒记忆：/tmp/xiaonuo_eternal_memory.json"