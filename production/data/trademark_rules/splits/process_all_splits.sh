#!/bin/bash
# 商标审查指南切割文件批量处理脚本
# 生成时间: 2025-12-26 22:22:03
# 生成者: 小诺·双鱼座

BASE_DIR="/Users/xujian/Athena工作平台"
SPLIT_DIR="$BASE_DIR/production/data/trademark_rules/splits"
LOG_DIR="$BASE_DIR/logs"
LOG_FILE="$LOG_DIR/trademark_split_process_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "$LOG_DIR"

echo "========================================"
echo "商标审查指南切割文件批量处理"
echo "========================================"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 处理每个切割文件
count=0
total=20

for split_file in "$SPLIT_DIR"/*.pdf; do
    if [ -f "$split_file" ]; then
        count=$((count + 1))
        filename=$(basename "$split_file")
        echo "[$count/$total] 处理文件: $filename"
        echo "========================================"

        # 调用full_laws_processor处理单个文件
        # 注意: 需要修改full_laws_processor支持单文件模式
        python3 "$BASE_DIR/production/scripts/patent_guideline/full_laws_processor.py" \
            --single-file "$split_file" \
            --collection "trademark_laws" \
            --space "trademark_rules" \
            >> "$LOG_FILE" 2>&1

        if [ $? -eq 0 ]; then
            echo "   ✅ 处理成功: $filename"
        else
            echo "   ❌ 处理失败: $filename"
            echo "   查看日志: $LOG_FILE"
        fi
        echo ""
    fi
done

echo "========================================"
echo "处理完成！"
echo "结束时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "日志文件: $LOG_FILE"
echo "========================================"
