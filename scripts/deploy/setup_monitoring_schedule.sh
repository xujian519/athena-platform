#!/bin/bash
# 设置存储系统监控调度
# 使用 cron 实现定期检查

echo "🔧 设置存储系统定期监控调度..."
echo "=" * 50

# 获取当前脚本的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CHECK_SCRIPT="$SCRIPT_DIR/simple_performance_check.py"

echo "项目目录: $PROJECT_DIR"
echo "检查脚本: $CHECK_SCRIPT"

# 创建 cron 任务
create_cron_job() {
    local schedule="$1"
    local description="$2"
    local log_file="$PROJECT_DIR/logs/monitoring_cron.log"

    echo "📅 设置调度: $description"
    echo "   调度频率: $schedule"
    echo "   日志文件: $log_file"

    # 创建 cron 任务行
    local cron_job="$schedule cd $PROJECT_DIR && python3 $CHECK_SCRIPT >> $log_file 2>&1"

    # 将任务添加到 crontab
    (crontab -l 2>/dev/null; echo "$cron_job") | crontab -

    echo "   ✅ 调度任务已添加"
}

# 确保日志目录存在
mkdir -p "$PROJECT_DIR/logs"

# 设置不同频率的监控任务
echo ""
echo "🕐 设置监控调度..."

# 每小时的健康检查 (每小时第0分钟执行)
create_cron_job "0 * * * *" "每小时健康检查"

# 每日详细检查 (每天凌晨3点执行)
create_cron_job "0 3 * * *" "每日深度检查"

# 每周综合优化 (每周日凌晨4点执行)
create_cron_job "0 4 * * 0" "每周综合优化"

# 每月系统清理 (每月1号凌晨5点执行)
create_cron_job "0 5 1 * *" "每月系统清理"

echo ""
echo "📋 当前 crontab 任务:"
crontab -l | grep -v "^#" | grep "$CHECK_SCRIPT"

echo ""
echo "📝 监控日志位置:"
echo "   实时日志: $PROJECT_DIR/logs/monitoring_cron.log"
echo "   详细报告: $PROJECT_DIR/logs/storage_performance_check_*.json"

echo ""
echo "🔍 手动执行命令:"
echo "   立即检查: python3 $CHECK_SCRIPT"
echo "   查看日志: tail -f $PROJECT_DIR/logs/monitoring_cron.log"

echo ""
echo "💡 提醒:"
echo "   - 确保系统在调度时间处于运行状态"
echo "   - 可以通过 'crontab -e' 编辑或删除任务"
echo "   - 监控结果会自动保存到 logs 目录"

echo ""
echo "🎉 监控调度设置完成!"