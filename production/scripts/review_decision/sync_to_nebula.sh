#!/bin/bash
# NebulaGraph定时同步脚本
# 每小时自动同步新增的决定书数据到知识图谱

BASE_DIR="/Users/xujian/Athena工作平台"
LOG_DIR="$BASE_DIR/logs"
SYNC_INTERVAL=3600  # 1小时 = 3600秒

# 创建日志目录
mkdir -p "$LOG_DIR"

echo "=================================================="
echo "🚀 NebulaGraph定时同步服务启动"
echo "=================================================="
echo "同步间隔: $SYNC_INTERVAL 秒 ($(echo "$SYNC_INTERVAL/3600" | bc) 小时)"
echo "日志目录: $LOG_DIR"
echo "=================================================="
echo ""

while true; do
    TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
    LOG_FILE="$LOG_DIR/nebula_sync_$TIMESTAMP.log"

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始同步..."

    # 运行Python导入模块
    cd "$BASE_DIR"
    python3 -m production.scripts.review_decision.nebula_importer >> "$LOG_FILE" 2>&1

    # 检查执行结果
    if [ $? -eq 0 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 同步完成"

        # 提取统计信息
        if [ -f "$LOG_FILE" ]; then
            echo "📊 本次同步统计:"
            grep -E "(导入决定书|创建法律引用|创建关系)" "$LOG_FILE" | tail -5
        fi
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ 同步失败，查看日志: $LOG_FILE"
    fi

    echo ""
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 等待 $SYNC_INTERVAL 秒后进行下次同步..."
    echo "=================================================="
    echo ""

    sleep $SYNC_INTERVAL
done
