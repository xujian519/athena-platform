#!/bin/bash
# Athena任务管理系统守护进程启动脚本
# Task Management System Daemon Startup Script

# 设置Python路径
export PYTHONPATH="/Users/xujian/Athena工作平台:$PYTHONPATH"
export ATHENA_HOME="/Users/xujian/Athena工作平台"

# 日志文件
LOG_FILE="/Users/xujian/Athena工作平台/logs/task_daemon.log"
PID_FILE="/Users/xujian/Athena工作平台/logs/task_daemon.pid"

echo "🚀 启动Athena任务管理系统守护进程..."
echo "PID文件: $PID_FILE"
echo "日志文件: $LOG_FILE"

# 检查是否已在运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "⚠️ 任务管理系统已在运行 (PID: $PID)"
        exit 1
    else
        echo "🗑️ 清理旧的PID文件"
        rm -f "$PID_FILE"
    fi
fi

# 创建日志目录
mkdir -p "$(dirname "$LOG_FILE")"

# 启动守护进程
cd "$ATHENA_HOME"
nohup python3 scripts/start_task_management_system.py --daemon > "$LOG_FILE" 2>&1 &

# 保存PID
echo $! > "$PID_FILE"

echo "✅ 任务管理系统守护进程已启动"
echo "PID: $(cat $PID_FILE)"
echo "日志: $LOG_FILE"
echo ""
echo "📊 查看状态:"
echo "  python3 scripts/start_task_management_system.py --stats"
echo ""
echo "🛑 停止服务:"
echo "  kill \"$(cat $PID_FILE)\""
echo "  bash scripts/start_task_daemon.sh stop"
