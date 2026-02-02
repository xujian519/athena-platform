#!/bin/bash
# 启动向量数据库监控服务
# 小诺的智能监控启动脚本

set -e

# 配置参数
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MONITOR_SCRIPT="$SCRIPT_DIR/vector_monitor_daemon.py"
PID_FILE="$PROJECT_ROOT/.runtime/vector_monitor.pid"
LOG_FILE="$PROJECT_ROOT/.runtime/vector_monitor.log"

# 检查是否已有监控进程在运行
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "⚠️  向量监控进程已在运行 (PID: $OLD_PID)"
        echo "如需重启，请先运行: $0 stop"
        exit 1
    else
        echo "🧹 清理过期的PID文件"
        rm -f "$PID_FILE"
    fi
fi

# 创建必要的目录
mkdir -p "$(dirname "$PID_FILE")"
mkdir -p "$(dirname "$LOG_FILE")"

# 检查Qdrant服务是否可用
echo "🔍 检查Qdrant服务状态..."
if curl -s http://localhost:6333/health > /dev/null; then
    echo "✅ Qdrant服务正常"
else
    echo "❌ Qdrant服务不可用，请先启动Qdrant"
    exit 1
fi

# 启动监控服务
echo "🚀 启动向量数据库监控服务..."
echo "   脚本: $MONITOR_SCRIPT"
echo "   PID文件: $PID_FILE"
echo "   日志文件: $LOG_FILE"

# 后台启动监控进程
nohup python3 "$MONITOR_SCRIPT" --interval 60 > "$LOG_FILE" 2>&1 &
MONITOR_PID=$!

# 保存PID
echo "$MONITOR_PID" > "$PID_FILE"

# 验证启动
sleep 2
if ps -p "$MONITOR_PID" > /dev/null 2>&1; then
    echo "✅ 向量监控服务启动成功 (PID: $MONITOR_PID)"
    echo "📊 监控数据将保存到: $PROJECT_ROOT/.runtime/"
    echo "📋 查看实时日志: tail -f $LOG_FILE"
    echo "🛑 停止服务: $0 stop"
else
    echo "❌ 向量监控服务启动失败"
    rm -f "$PID_FILE"
    exit 1
fi

# 显示当前状态
echo ""
echo "📈 当前监控状态:"
echo "   进程ID: $(cat $PID_FILE)"
echo "   检查间隔: 60秒"
echo "   服务地址: http://localhost:6333"
echo "   开始时间: $(date)"

# 检查最新指标
echo ""
echo "🔍 快速健康检查:"
curl -s http://localhost:6333/health | python3 -m json.tool 2>/dev/null || echo "无法获取健康状态"