#!/bin/bash
# 批量处理中国专利数据脚本

# 设置变量
SOURCE_DIR="/Volumes/xujian/patent_data/china_patents"
DB_PATH="/Users/xujian/Athena工作平台/data/patents/processed/china_patents_enhanced.db"
LOG_DIR="/Users/xujian/Athena工作平台/logs"
BACKUP_DIR="/Users/xujian/Athena工作平台/data/patents/processed/backups"

# 创建必要目录
mkdir -p $LOG_DIR
mkdir -p $BACKUP_DIR

echo "========================================"
echo "中国专利数据批量处理脚本"
echo "开始时间: $(date)"
echo "========================================"

# 检查源目录
if [ ! -d "$SOURCE_DIR" ]; then
    echo "❌ 错误: 源目录不存在 $SOURCE_DIR"
    exit 1
fi

# 检查数据盘是否挂载
if [ ! -f "$SOURCE_DIR/中国专利数据库2023年.csv" ]; then
    echo "⚠️  警告: 数据盘可能未正确挂载"
    echo "请检查 /Volumes/xujian 是否可访问"
    echo "当前可访问的卷:"
    ls -la /Volumes/
    read -p "是否继续? (y/n): " confirm
    if [ "$confirm" != "y" ]; then
        exit 1
    fi
fi

# 函数：处理单个年份
process_year() {
    local year=$1
    local csv_file="$SOURCE_DIR/中国专利数据库${year}年.csv"

    if [ ! -f "$csv_file" ]; then
        echo "⚠️  ${year}年数据文件不存在"
        return 1
    fi

    echo ""
    echo "----------------------------------------"
    echo "处理 ${year} 年数据"
    echo "文件: $(basename $csv_file)"
    echo "大小: $(du -h $csv_file | cut -f1)"
    echo "----------------------------------------"

    # 运行批处理器
    python3 services/safe_yearly_processor.py --year $year \
        --input "$csv_file" \
        --output "$DB_PATH" \
        --batch-size 2000 \
        --log-dir "$LOG_DIR"

    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        echo "✅ ${year}年数据处理成功"

        # 备份数据库（每5年备份一次）
        if [ $((year % 5)) -eq 0 ]; then
            backup_file="$BACKUP_DIR/china_patents_${year}_$(date +%Y%m%d_%H%M%S).db"
            echo "📦 创建备份: $backup_file"
            cp "$DB_PATH" "$backup_file"
        fi
    else
        echo "❌ ${year}年数据处理失败"
        return $exit_code
    fi
}

# 主处理函数
main() {
    local start_year=$1
    local end_year=$2

    # 如果没有指定年份，获取所有可用年份
    if [ -z "$start_year" ]; then
        echo "检测可用年份..."
        years=($(ls "$SOURCE_DIR"/中国专利数据库*.csv | sed -E 's/.*中国专利数据库([0-9]{4})年\.csv/\1/' | sort -n))
        echo "找到 ${#years[@]} 年的数据: ${years[@]}"
        start_year=${years[0]}
        end_year=${years[-1]}
    fi

    echo "处理范围: $start_year 年 - $end_year 年"

    # 处理指定年份范围
    for (( year=$start_year; year<=$end_year; year++ )); do
        process_year $year

        # 检查是否需要暂停（避免系统过载）
        local load=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',')
        if (( $(echo "$load > 3.0" | bc -l) )); then
            echo "⚠️  系统负载过高 ($load)，暂停60秒..."
            sleep 60
        fi
    done

    # 最终验证
    echo ""
    echo "========================================"
    echo "处理完成验证"
    echo "========================================"

    python3 -c "
import sqlite3
conn = sqlite3.connect('$DB_PATH')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM patents')
total = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(DISTINCT year) FROM patents')
years_count = cursor.fetchone()[0]
print(f'📊 数据库统计:')
print(f'  - 总专利数: {total:,}')
print(f'  - 涉及年数: {years_count}')
cursor.execute('SELECT year, COUNT(*) FROM patents GROUP BY year ORDER BY year DESC LIMIT 10')
print('\\n最近10年统计:')
for year, count in cursor.fetchall():
    print(f'  - {year}年: {count:,}条')
conn.close()
"
}

# 交互式选择
echo ""
echo "请选择处理方式:"
echo "1. 处理所有年份"
echo "2. 指定年份范围"
echo "3. 处理单个年份"
echo "4. 继续未完成的处理"
echo ""
read -p "请选择 (1-4): " choice

case $choice in
    1)
        main
        ;;
    2)
        read -p "开始年份: " start_year
        read -p "结束年份: " end_year
        main $start_year $end_year
        ;;
    3)
        read -p "年份: " year
        process_year $year
        ;;
    4)
        echo "检查未完成的处理..."
        python3 -c "
import sqlite3
conn = sqlite3.connect('$DB_PATH')
cursor = conn.cursor()
cursor.execute('SELECT DISTINCT year FROM patents ORDER BY year DESC')
processed_years = [row[0] for row in cursor.fetchall()]
print(f'已处理年份: {processed_years}')

# 查找未处理的年份
import os
source_files = os.listdir('$SOURCE_DIR')
available_years = set()
for f in source_files:
    if '中国专利数据库' in f and f.endswith('.csv'):
        year = int(f.split('年')[0].split('数据库')[-1])
        available_years.add(year)

unprocessed = sorted(available_years - set(processed_years))
print(f'未处理年份: {unprocessed}')

if unprocessed:
    print(f'将继续处理 {unprocessed[0]} 年...')
"
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac

echo ""
echo "========================================"
echo "处理完成!"
echo "结束时间: $(date)"
echo "========================================"