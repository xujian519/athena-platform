#!/bin/bash
# 检查所有专利处理任务的状态

echo "========================================"
echo "专利处理任务状态检查"
echo "时间: $(date)"
echo "========================================"

# 检查正在运行的Python处理进程
echo -e "\n🔍 正在运行的专利处理任务:"
ps aux | grep -E "python3.*patent.*processor|python3.*patent.*batch" | grep -v grep | while read line; do
    pid=$(echo $line | awk '{print $2}')
    cmd=$(echo $line | awk '{$1=$2=$3=""; print $0}' | sed 's/^ *//')
    echo "  PID: $pid"
    echo "  命令: $cmd"
    echo "  ---"
done

# 检查数据库文件大小
echo -e "\n📊 数据库文件大小:"
ls -lh /Users/xujian/Athena工作平台/data/patents/processed/*.db | while read line; do
    size=$(echo $line | awk '{print $5}')
    file=$(echo $line | awk '{print $9}')
    echo "  $(basename $file): $size"
done

# 使用监控脚本查看统计
echo -e "\n📈 使用监控脚本查看详细统计:"
python3 services/patent_monitor.py status