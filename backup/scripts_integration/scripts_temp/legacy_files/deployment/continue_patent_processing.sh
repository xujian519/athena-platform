#!/bin/bash
# 专利数据处理持续运行脚本
# 即使上下文窗口满了也能继续运行

# 设置工作目录
cd /Users/xujian/Athena工作平台

# 创建日志目录
mkdir -p logs

echo "========================================"
echo "专利数据处理持续运行脚本"
echo "开始时间: $(date)"
echo "========================================"

# 检查是否有正在运行的处理任务
check_running_tasks() {
    echo "检查运行中的任务..."
    running_count=$(ps aux | grep -E "(patent_batch_processor|safe_yearly_processor|yearly_processor)" | grep -v grep | wc -l)
    echo "当前运行中的处理任务数: $running_count"
}

# 显示当前状态
show_status() {
    echo "----------------------------------------"
    echo "当前状态 ($(date))"
    echo "----------------------------------------"

    # 使用监控脚本查看状态
    python3 services/patent_monitor.py status

    # 显示磁盘空间
    echo ""
    echo "磁盘空间使用情况:"
    df -h /Volumes/xujian
    df -h /Users/xujian/Athena工作平台/data
}

# 主处理循环
main_loop() {
    while true; do
        echo ""
        echo "========================================"
        echo "主处理循环 - $(date)"
        echo "========================================"

        # 检查运行中的任务
        check_running_tasks

        # 显示状态
        show_status

        # 查找并处理未完成的年份
        echo ""
        echo "检查未处理的年份..."

        # 使用监控脚本继续处理
        python3 services/patent_monitor.py continue

        # 等待一段时间再检查
        echo ""
        echo "等待10分钟后继续检查..."
        sleep 600  # 10分钟
    done
}

# 信号处理 - 优雅退出
cleanup() {
    echo ""
    echo "收到退出信号，清理中..."

    # 查找所有子进程
    pids=$(jobs -p)

    if [ -n "$pids" ]; then
        echo "停止后台进程..."
        kill $pids 2>/dev/null
        wait 2>/dev/null
    fi

    echo "脚本已停止"
    echo "结束时间: $(date)"
    exit 0
}

# 注册信号处理器
trap cleanup SIGINT SIGTERM

# 启动主循环
echo "启动持续处理..."
main_loop