#!/bin/bash
# 深度技术分析进度监控脚本

LOG_FILE="/Users/xujian/Nutstore Files/02无效诉讼/济南力邦/201921401279.9无效材料/深度技术分析输出/分析日志.txt"

echo "📊 深度技术分析进度监控"
echo "=================================="
echo ""

while true; do
    # 获取最新进度
    LATEST_PROGRESS=$(tail -20 "$LOG_FILE" | grep "📊 进度" | tail -1)

    if [ -n "$LATEST_PROGRESS" ]; then
        CURRENT_TIME=$(date "+%H:%M:%S")
        echo "[$CURRENT_TIME] $LATEST_PROGRESS"

        # 计算预计剩余时间
        PROGRESS_NUM=$(echo "$LATEST_PROGRESS" | grep -oE "[0-9]+/169" | cut -d'/' -f1)
        if [ -n "$PROGRESS_NUM" ]; then
            REMAINING=$((169 - PROGRESS_NUM))
            PERCENTAGE=$(echo "scale=1; $PROGRESS_NUM * 100 / 169" | bc)
            ESTIMATED_TIME=$((REMAINING * 90 / 60))  # 假设每个文件90秒

            echo "   已完成: $PROGRESS_NUM/169 (${PERCENTAGE}%)"
            echo "   剩余: $REMAINING 个"
            echo "   预计剩余时间: ${ESTIMATED_TIME} 分钟"
        fi

        echo ""
        echo "----------------------------------"

        # 检查是否完成
        if tail -5 "$LOG_FILE" | grep -q "✅ 深度技术分析完成"; then
            echo "🎉 分析已完成！"
            break
        fi
    fi

    # 每2分钟检查一次
    sleep 120
done
