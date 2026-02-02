#!/bin/bash
# 停止向量数据库监控服务
# 小诺的智能监控停止脚本

set -e

# 配置参数
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PID_FILE="$PROJECT_ROOT/.runtime/vector_monitor.pid"

# 检查PID文件
if [ ! -f "$PID_FILE" ]; then
    echo "⚠️  没有找到向量监控进程PID文件"
    echo "可能监控进程未启动"
    exit 0
fi

# 读取PID
MONITOR_PID=$(cat "$PID_FILE")

# 检查进程是否存在
if ! ps -p "$MONITOR_PID" > /dev/null 2>&1; then
    echo "⚠️  向量监控进程不存在 (PID: $MONITOR_PID)"
    echo "清理PID文件..."
    rm -f "$PID_FILE"
    exit 0
fi

# 停止进程
echo "🛑 正在停止向量监控服务 (PID: $MONITOR_PID)..."

# 发送TERM信号
kill -TERM "$MONITOR_PID"

# 等待进程优雅退出
for i in {1..10}; do
    if ! ps -p "$MONITOR_PID" > /dev/null 2>&1; then
        echo "✅ 向量监控服务已优雅停止"
        rm -f "$PID_FILE"
        exit 0
    fi
    echo "   等待进程停止... ($i/10)"
    sleep 1
done

# 如果进程仍在运行，强制停止
echo "⚠️  进程未响应TERM信号，强制停止..."
kill -KILL "$MONITOR_PID" 2>/dev/null || true

# 最后检查
if ps -p "$MONITOR_PID" > /dev/null 2>&1; then
    echo "❌ 无法停止向量监控进程"
    exit 1
else
    echo "✅ 向量监控服务已强制停止"
    rm -f "$PID_FILE"
fi

# 显示监控数据状态
echo ""
echo "📊 监控数据状态:"
if [ -f "$PROJECT_ROOT/.runtime/latest_metrics.json" ]; then
    echo "   最新指标: ✅ 存在"
    echo "   文件大小: $(du -h "$PROJECT_ROOT/.runtime/latest_metrics.json" | cut -f1)"
    echo "   最后更新: $(stat -f "%Sm" "$PROJECT_ROOT/.runtime/latest_metrics.json")"
else
    echo "   最新指标: ❌ 不存在"
fi

if [ -f "$PROJECT_ROOT/.runtime/performance_history.json" ]; then
    echo "   历史记录: ✅ 存在"
    echo "   文件大小: $(du -h "$PROJECT_ROOT/.runtime/performance_history.json" | cut -f1)"
else
    echo "   历史记录: ❌ 不存在"
fi

echo ""
echo "💡 提示:"
echo "   - 查看监控历史: cat $PROJECT_ROOT/.runtime/performance_history.json"
echo "   - 重新启动服务: $SCRIPT_DIR/start_monitoring.sh"
echo "   - 查看最新指标: cat $PROJECT_ROOT/.runtime/latest_metrics.json"