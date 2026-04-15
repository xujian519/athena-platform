#!/bin/bash
# 知识图谱同步服务启动脚本

echo "🔄 启动Athena知识图谱实时同步服务"
echo "======================================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装"
    exit 1
fi

# 检查依赖
echo "🔍 检查Python依赖..."

# 安装必要的Python包
pip3 install watchdog websockets aioredis gremlinpython 2>/dev/null

# 创建日志目录
mkdir -p /Users/xujian/Athena工作平台/logs

# 设置环境变量
export PYTHONPATH="/Users/xujian/Athena工作平台:$PYTHONPATH"

# 检查服务状态
check_service() {
    local service_name=$1
    local port=$2

    if nc -z localhost $port 2>/dev/null; then
        echo "✅ $service_name 运行正常 (端口 $port)"
        return 0
    else
        echo "⚠️  $service_name 未运行 (端口 $port)"
        return 1
    fi
}

# 启动选项
echo ""
echo "请选择启动模式:"
echo "1) 前台运行 (开发模式)"
echo "2) 后台运行 (生产模式)"
echo "3) 停止服务"
echo "4) 查看服务状态"
echo ""

read -p "请选择 (1-4): " choice

case $choice in
    1)
        echo "🔧 前台启动同步服务..."

        # 检查依赖服务
        echo "检查依赖服务..."
        janusgraph_ok=false
        qdrant_ok=false

        check_service "JanusGraph" 8182 && janusgraph_ok=true
        check_service "Qdrant" 6333 && qdrant_ok=true

        if ! $janusgraph_ok; then
            echo "❌ JanusGraph未运行，请先启动JanusGraph服务"
            echo "💡 提示: cd services/knowledge-graph-service && docker-compose up -d janusgraph"
            exit 1
        fi

        if ! $qdrant_ok; then
            echo "⚠️  Qdrant未运行，向量同步功能将受限"
        fi

        echo "✅ 依赖检查完成，启动同步服务..."
        python3 realtime_knowledge_graph_sync.py
        ;;

    2)
        echo "🚀 后台启动同步服务..."

        # 停止现有进程
        pkill -f "realtime_knowledge_graph_sync.py" 2>/dev/null || true

        # 使用nohup后台运行
        nohup python3 realtime_knowledge_graph_sync.py > /Users/xujian/Athena工作平台/logs/sync_service.out 2>&1 &
        sleep 2

        # 检查是否启动成功
        if pgrep -f "realtime_knowledge_graph_sync.py" > /dev/null; then
            echo "✅ 同步服务已后台启动"
            echo "📋 进程ID: $(pgrep -f realtime_knowledge_graph_sync.py")"
            echo "📄 日志位置: /Users/xujian/Athena工作平台/logs/sync_service.out"
            echo ""
            echo "💡 管理命令:"
            echo "  查看日志: tail -f /Users/xujian/Athena工作平台/logs/sync_service.out"
            echo "  停止服务: pkill -f realtime_knowledge_graph_sync.py"
        else
            echo "❌ 同步服务启动失败，请检查日志"
        fi
        ;;

    3)
        echo "⏹️  停止同步服务..."

        if pgrep -f "realtime_knowledge_graph_sync.py" > /dev/null; then
            pkill -f "realtime_knowledge_graph_sync.py"
            sleep 2

            if pgrep -f "realtime_knowledge_graph_sync.py" > /dev/null; then
                echo "⚠️  强制停止服务..."
                pkill -9 -f "realtime_knowledge_graph_sync.py"
            fi

            echo "✅ 同步服务已停止"
        else
            echo "ℹ️  同步服务未运行"
        fi
        ;;

    4)
        echo "📊 服务状态检查..."
        echo ""

        # 检查同步服务进程
        if pgrep -f "realtime_knowledge_graph_sync.py" > /dev/null; then
            pid=$(pgrep -f "realtime_knowledge_graph_sync.py")
            echo "✅ 同步服务运行中 (PID: $pid)"

            # 检查资源使用
            ps -p $pid -o pid,ppid,%cpu,%mem,cmd,etime
        else
            echo "❌ 同步服务未运行"
        fi

        echo ""
        echo "依赖服务状态:"
        check_service "JanusGraph" 8182
        check_service "Qdrant" 6333
        check_service "Redis" 6379
        check_service "WebSocket通知" 8081

        echo ""
        echo "最近的日志:"
        if [ -f "/Users/xujian/Athena工作平台/logs/kg_sync.log" ]; then
            tail -n 5 /Users/xujian/Athena工作平台/logs/kg_sync.log
        else
            echo "无日志文件"
        fi
        ;;

    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "✅ 操作完成"