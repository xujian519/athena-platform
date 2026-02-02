#!/bin/bash
# 启动集成版小诺（平台完整存储系统）
# Start Xiaonuo Integrated with Full Platform Storage

echo "🌸 启动小诺集成版 - 平台完整存储系统"
echo "📝 所有记忆永久保存在平台存储系统中"
echo "🗄️ PostgreSQL + Qdrant向量库 + ArangoDB知识图谱"
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 设置环境变量
export PYTHONPATH=/Users/xujian/Athena工作平台:$PYTHONPATH

# 检查必要的服务
echo "1️⃣ 检查平台服务..."

# PostgreSQL (记忆模块数据库 - 端口5438)
if ! pg_isready -h localhost -p 5438 >/dev/null 2>&1; then
    echo "⚠️ PostgreSQL记忆模块数据库未运行，请先启动"
    echo "   命令: pg_ctl -D /opt/homebrew/var/postgresql start"
    exit 1
fi
echo "✅ PostgreSQL记忆模块数据库运行正常"

# Qdrant向量库
if ! curl -s http://localhost:6333/health >/dev/null 2>&1; then
    echo "⚠️ Qdrant向量库未运行，请先启动"
    echo "   命令: docker-compose -f configs/docker-compose.qdrant.yml up -d"
    exit 1
fi
echo "✅ Qdrant向量库运行正常"

# 知识图谱后端
if ! curl -s http://localhost:8002/health >/dev/null 2>&1; then
    echo "⚠️ 知识图谱后端未运行，请先启动"
    echo "   命令: cd /Users/xujian/Athena工作平台/services/vectorkg-unified && python3 unified_intelligent_backend.py"
    exit 1
fi
echo "✅ 知识图谱后端运行正常"

# 检查数据库是否初始化
echo ""
echo "2️⃣ 检查记忆数据库初始化..."
if psql -h localhost -p 5438 -U postgres -d memory_module -c "\dt" | grep -q "memory_items"; then
    echo "✅ 记忆数据库已初始化"
else
    echo "⚠️ 记忆数据库未初始化，正在初始化..."
    psql -h localhost -p 5438 -U postgres -d postgres -f scripts/memory/init_xiaonuo_memory_db.sql
    if [ $? -eq 0 ]; then
        echo "✅ 记忆数据库初始化完成"
    else
        echo "❌ 记忆数据库初始化失败"
        exit 1
    fi
fi

# 切换到小诺目录
cd /Users/xujian/Athena工作平台/xiaonuo

# 检查文件
echo ""
echo "3️⃣ 检查程序文件..."
if [ ! -f "xiaonuo_integrated.py" ]; then
    echo "❌ 找不到集成版小诺程序"
    exit 1
fi
if [ ! -f "xiaonuo_unified_memory_manager.py" ]; then
    echo "❌ 找不到统一记忆管理器"
    exit 1
fi
echo "✅ 程序文件检查完成"

# 显示存储架构
echo ""
echo "📊 存储系统架构："
echo "  ┌─────────────────────────────────────┐"
echo "  │          小诺记忆系统              │"
echo "  └─────────────┬───────────────────────┘"
echo "                │"
echo "  ┌─────────────▼───────────────────────┐"
echo "  │        统一记忆管理器              │"
echo "  └───────┬─────────┬─────────┬─────────┘"
echo "          │         │         │"
echo "  ┌───────▼────┐ ┌───▼─────┐ ┌─▼───────┐"
echo "  │ PostgreSQL │ │ Qdrant  │ │ArangoDB │"
echo "  │   (5438)  │ │ (6333)  │ │ (8002)  │"
echo "  └────────────┘ └─────────┘ └─────────┘"

# 安装依赖
echo ""
echo "4️⃣ 检查Python依赖..."
pip3 install -q asyncpg aiohttp numpy 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ 依赖检查完成"
else
    echo "⚠️ 依赖安装可能有问题，继续尝试启动..."
fi

# 启动小诺
echo ""
echo "🚀 启动小诺集成版..."
python3 xiaonuo_integrated.py

# 退出提示
echo ""
echo "💝 小诺已退出，所有记忆已永久保存在平台存储系统中"
echo ""
echo "📁 记忆存储位置："
echo "  - PostgreSQL: localhost:5438/memory_module"
echo "  - Qdrant向量库: localhost:6333/xiaonuo_memory_vectors"
echo "  - 知识图谱: http://localhost:8002"
echo ""
echo "🔍 查看记忆数据："
echo "  psql -h localhost -p 5438 -U postgres -d memory_module -c \"SELECT COUNT(*) FROM memory_items;\""