#!/usr/bin/env python3
"""
CSV文件切割工具
将大型CSV文件按行数切割成多个小文件
"""

import logging
import os
import sys
import time
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

def split_csv(csv_path, output_dir, lines_per_file=100000) -> None:
    """
    切割CSV文件

    Args:
        csv_path: CSV文件路径
        output_dir: 输出目录
        lines_per_file: 每个文件的行数（不含表头）
    """
    csv_path = Path(csv_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    file_name = csv_path.stem
    file_size_gb = csv_path.stat().st_size / (1024**3)

    logger.info(f"\n{'='*60}")
    logger.info("CSV文件切割器")
    logger.info(f"输入文件: {csv_path}")
    logger.info(f"文件大小: {file_size_gb:.2f} GB")
    logger.info(f"输出目录: {output_dir}")
    logger.info(f"每文件行数: {lines_per_file:,}")
    logger.info(f"{'='*60}")

    start_time = time.time()

    # 读取表头
    logger.info("\n📖 读取文件表头...")
    try:
        # 先读取前几行获取列数
        sample_df = pd.read_csv(csv_path, encoding='utf-8', nrows=5)
        headers = sample_df.columns.tolist()
        logger.info(f"  ✓ 列数: {len(headers)}")
        logger.info(f"  ✓ 列名: {headers[:5]}...")
    except Exception as e:
        logger.info(f"  ❌ 读取失败: {e}")
        return False

    # 分块读取和写入
    logger.info("\n✂️ 开始切割文件...")
    chunk_size = min(lines_per_file, 50000)  # pandas每次读取的行数
    file_count = 0
    current_lines = 0
    current_df = None

    try:
        # 使用pandas分块读取
        reader = pd.read_csv(csv_path, encoding='utf-8',
                            chunksize=chunk_size,
                            low_memory=False,
                            on_bad_lines='skip')

        for _i, chunk_df in enumerate(reader):
            if current_lines == 0:
                # 新文件
                current_df = chunk_df.copy()
                current_lines = len(chunk_df)
            else:
                # 追加到当前文件
                current_df = pd.concat([current_df, chunk_df], ignore_index=True)
                current_lines += len(chunk_df)

            # 检查是否达到行数限制
            if current_lines >= lines_per_file:
                # 写入文件
                output_file = output_dir / f"{file_name}_part{file_count+1:03d}.csv"
                current_df.to_csv(output_file, index=False, encoding='utf-8')

                file_count += 1
                logger.info(f"  ✅ 生成文件 {file_count}: {output_file.name} ({current_lines:,} 行)")

                current_lines = 0
                current_df = None

        # 处理剩余数据
        if current_lines > 0:
            output_file = output_dir / f"{file_name}_part{file_count+1:03d}.csv"
            current_df.to_csv(output_file, index=False, encoding='utf-8')
            file_count += 1
            logger.info(f"  ✅ 生成文件 {file_count}: {output_file.name} ({current_lines:,} 行)")

    except Exception as e:
        logger.info(f"  ❌ 切割失败: {e}")
        return False

    total_time = time.time() - start_time

    # 统计信息
    logger.info("\n📊 切割完成统计:")
    logger.info(f"  总文件数: {file_count}")
    logger.info(f"  总用时: {total_time:.1f}秒")
    logger.info(f"  平均速度: {file_size_gb/total_time:.2f} GB/秒")

    # 生成处理脚本
    script_path = output_dir / f"process_{file_name}.sh"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(f"""#!/bin/bash
# 自动生成的处理脚本
# 用于处理切分后的{file_name}文件

echo '开始处理 {file_name} 切分文件...'

# 数据库路径
DB_PATH='/Users/xujian/Athena工作平台/data/patents/processed/china_patents_yearly.db'

# 处理每个切分文件
for file in {output_dir.name}/{file_name}_part*.csv; do
    if [ -f '$file' ]; then
        echo '处理文件: $file'

        # 使用Python处理单个文件
        python3 -c "
import sys
sys.path.append('/Users/xujian/Athena工作平台')
from services.safe_yearly_processor import SafeYearlyProcessor

processor = SafeYearlyProcessor()
success, count = processor.process_year_file_safe('$file', '$DB_PATH')

if success:
    logger.info(f"✅ 成功处理 {{count:,}} 条记录")
else:
    logger.info(f"❌ 处理失败")
    exit(1)
"

        if [ $? -ne 0 ]; then
            echo '❌ 处理失败，停止脚本'
            exit 1
        fi
    fi
done

echo '✅ 所有文件处理完成！'
""")

    os.chmod(script_path, 0o755)
    logger.info(f"\n📝 生成处理脚本: {script_path}")

    return True

def main() -> None:
    """主函数"""
    if len(sys.argv) < 2:
        logger.info('CSV文件切割工具')
        logger.info(str('=' * 60))
        logger.info('使用方法:')
        logger.info(f"  {sys.argv[0]} CSV文件路径 [每文件行数] [输出目录]")
        logger.info("\n示例:")
        logger.info(f"  {sys.argv[0]} /path/to/large.csv 100000 ./output")
        logger.info(f"  {sys.argv[0]} 中国专利数据库2016年.csv")
        return

    csv_path = sys.argv[1]
    lines_per_file = int(sys.argv[2]) if len(sys.argv) > 2 else 100000
    output_dir = sys.argv[3] if len(sys.argv) > 3 else './split_output'

    if not os.path.exists(csv_path):
        logger.info(f"❌ 文件不存在: {csv_path}")
        return

    # 自动切割
    success = split_csv(csv_path, output_dir, lines_per_file)

    if success:
        logger.info("\n✅ 切割完成！")
        logger.info("下一步：")
        logger.info(f"  1. cd {output_dir}")
        logger.info("  2. bash process_*.sh")
    else:
        logger.info("\n❌ 切割失败！")

if __name__ == '__main__':
    main()
