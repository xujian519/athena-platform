#!/bin/bash
# 曹新乐语音提醒脚本

# 显示通知
osascript -e 'display notification "现在是上午9点，请立即联系曹新乐，约他周四见面" with title "🎤 小诺提醒" sound name "Glass"'

# 语音提醒序列
say -v Ting-Ting "滴、滴、滴"
sleep 0.5
say -v Ting-Ting "重要提醒"
sleep 0.5
say -v Ting-Ting "现在是上午9点"
sleep 0.5
say -v Mei-Jia "请立即联系曹新乐"
sleep 0.5
say -v Ting-Ting "约他周四见面"

# 打开提醒事项
open -a "Reminders"

# 记录执行时间
echo "$(date): 曹新乐语音提醒已执行" >> /tmp/caoxinle_reminder.log
