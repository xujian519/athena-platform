#!/usr/bin/env python3
"""
分年度专利数据处理器
逐个处理年度文件，每处理完一个就验证
"""

import glob
import logging
import os
import sqlite3
import time
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

def process_year_file(csv_path, db_path) -> None:
    """处理单个年度文件"""
    year = Path(csv_path).stem.split('中国专利数据库')[-1][:4]
    file_name = Path(csv_path).name
    file_size_mb = os.path.getsize(csv_path) / (1024**2)

    logger.info(f"\n{'='*60}")
    logger.info(f"📅 处理 {year} 年数据")
    logger.info(f"文件: {file_name}")
    logger.info(f"大小: {file_size_mb:.1f} MB")
    logger.info(f"{'='*60}")

    start_time = time.time()

    # 读取CSV数据
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
        logger.info(f"✓ 读取完成: {len(df):,} 条记录")
    except Exception as e:
        logger.info(f"❌ 读取失败: {e}")
        return False

    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 优化设置
    cursor.execute('PRAGMA journal_mode = WAL')
    cursor.execute('PRAGMA synchronous = OFF')
    cursor.execute('PRAGMA cache_size = -1000000')

    # 创建表（如果不存在）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patent_name TEXT,
            patent_type TEXT,
            applicant TEXT,
            applicant_type TEXT,
            application_number TEXT,
            application_date TEXT,
            application_year INTEGER,
            publication_number TEXT,
            publication_date TEXT,
            publication_year INTEGER,
            ipc_code TEXT,
            ipc_main_class TEXT,
            inventor TEXT,
            abstract TEXT,
            claims_content TEXT,
            source_year INTEGER,
            source_file TEXT,
            indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 准备数据
    logger.info("📝 准备数据...")
    data = []
    invalid_count = 0

    for _, row in df.iterrows():
        # 验证必要字段
        if not pd.isna(row.get('专利名称')) and not pd.isna(row.get('申请人')):
            data.append((
                row.get('专利名称', ''),
                row.get('专利类型', ''),
                row.get('申请人', ''),
                row.get('申请人类型', ''),
                row.get('申请号', ''),
                row.get('申请日', ''),
                row.get('申请年份', 0),
                row.get('公开公告号', ''),
                row.get('公开公告日', ''),
                row.get('公开公告年份', 0),
                row.get('IPC分类号', ''),
                row.get('IPC主分类号', ''),
                row.get('发明人', ''),
                row.get('摘要文本', ''),
                row.get('主权项内容', ''),
                int(year) if year.isdigit() else 0,
                file_name
            ))
        else:
            invalid_count += 1

    if invalid_count > 0:
        logger.info(f"⚠️  跳过无效记录: {invalid_count:,} 条")

    logger.info(f"✓ 有效记录: {len(data):,} 条")

    # 插入数据
    logger.info("💾 插入数据库...")
    batch_size = 5000
    inserted = 0

    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        cursor.executemany('''
            INSERT INTO patents (
                patent_name, patent_type, applicant, applicant_type,
                application_number, application_date, application_year,
                publication_number, publication_date, publication_year,
                ipc_code, ipc_main_class, inventor, abstract, claims_content,
                source_year, source_file
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', batch)
        conn.commit()
        inserted += len(batch)
        logger.info(f"  进度: {inserted:,}/{len(data):,}")

    # 创建索引
    logger.info("🔨 创建索引...")
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_year ON patents(source_year)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_applicant ON patents(applicant)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_patent_name ON patents(patent_name)')
    conn.commit()

    conn.close()

    total_time = time.time() - start_time
    db_size = os.path.getsize(db_path) / (1024**2)

    logger.info(f"\n✅ {year} 年处理完成!")
    logger.info(f"  有效记录: {inserted:,}")
    logger.info(f"  用时: {total_time:.1f}秒")
    logger.info(f"  速度: {inserted/total_time:.0f} 条/秒")
    logger.info(f"  数据库大小: {db_size:.1f} MB")

    return True, inserted

def verify_database(db_path, year) -> None:
    """验证数据库"""
    logger.info(f"\n🔍 验证 {year} 年数据...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 总记录数
    cursor.execute('SELECT COUNT(*) FROM patents WHERE source_year = ?', (int(year),))
    total_count = cursor.fetchone()[0]

    # 有申请号的记录数
    cursor.execute("""
        SELECT COUNT(*)
        FROM patents
        WHERE source_year = ? AND application_number != ''
    """, (int(year),))
    has_app_number = cursor.fetchone()[0]

    # 有摘要的记录数
    cursor.execute("""
        SELECT COUNT(*)
        FROM patents
        WHERE source_year = ? AND abstract != ''
    """, (int(year),))
    has_abstract = cursor.fetchone()[0]

    logger.info(f"  总记录数: {total_count:,}")
    logger.info(f"  有申请号: {has_app_number:,}")
    logger.info(f"  有摘要: {has_abstract:,}")

    # 显示前3条示例
    cursor.execute("""
        SELECT patent_name, applicant, application_date
        FROM patents
        WHERE source_year = ?
        LIMIT 3
    """, (int(year),))

    logger.info("\n示例专利:")
    for i, (title, applicant, _date) in enumerate(cursor.fetchall(), 1):
        logger.info(f"  {i}. {title[:50]}... ({applicant})")

    # 测试搜索
    test_keywords = ['装置', '方法', '系统']
    logger.info("\n测试搜索:")
    for keyword in test_keywords:
        cursor.execute("""
            SELECT COUNT(*)
            FROM patents
            WHERE source_year = ? AND patent_name LIKE ?
        """, (int(year), f'%{keyword}%'))

        count = cursor.fetchone()[0]
        if count > 0:
            logger.info(str(f"  \"{keyword}\": {count} 条"))

    conn.close()

def interactive_process() -> Any:
    """交互式处理"""
    data_path = '/Volumes/xujian/patent_data/china_patents'
    output_dir = Path('/Users/xujian/Athena工作平台/data/patents/processed')
    output_dir.mkdir(parents=True, exist_ok=True)

    # 查找所有CSV文件
    csv_files = sorted(glob.glob(f"{data_path}/*.csv"))

    if not csv_files:
        logger.info(f"❌ 在 {data_path} 未找到CSV文件")
        return

    logger.info('专利数据分年度处理器')
    logger.info(str('='*60))
    logger.info(f"找到 {len(csv_files)} 个年度文件\n")

    # 显示文件列表
    for i, f in enumerate(csv_files, 1):
        year = Path(f).stem.split('中国专利数据库')[-1][:4]
        size_mb = os.path.getsize(f) / (1024**2)
        logger.info(f"{i}. {year}年 - {size_mb:.1f} MB")

    # 选择处理方式
    logger.info("\n处理选项:")
    logger.info('1. 从小到大处理（推荐用于验证）')
    logger.info('2. 从大到小处理')
    logger.info('3. 选择特定年份')
    logger.info('4. 处理所有文件')

    choice = input("\n请选择 (1-4): ").strip()

    if choice == '1':
        # 按文件大小从小到大
        csv_files = sorted(csv_files, key=lambda x: os.path.getsize(x))
    elif choice == '2':
        # 按文件大小从大到小
        csv_files = sorted(csv_files, key=lambda x: os.path.getsize(x), reverse=True)
    elif choice == '3':
        # 选择年份
        year_input = input('请输入年份（多个用空格分隔，如：1985 1986 1987）: ').strip()
        selected_years = year_input.split()
        csv_files = [f for f in csv_files
                    if any(year in Path(f).stem for year in selected_years)]

    logger.info(f"\n将处理 {len(csv_files)} 个文件")

    # 创建数据库
    db_path = output_dir / 'china_patents_yearly.db'

    # 确认处理
    confirm = input(f"\n确定要开始处理吗？数据将保存到: {db_path} (y/n): ").strip().lower()
    if confirm != 'y':
        logger.info('已取消')
        return

    # 处理每个文件
    total_patents = 0
    processed_years = []

    for csv_file in csv_files:
        year = Path(csv_file).stem.split('中国专利数据库')[-1][:4]

        # 询问是否处理
        if len(csv_files) > 1:
            proceed = input(f"\n是否处理 {year} 年？(y/n): ").strip().lower()
            if proceed != 'y':
                logger.info(f"跳过 {year} 年")
                continue

        # 处理文件
        success, count = process_year_file(csv_file, str(db_path))

        if success:
            # 验证数据
            verify_database(str(db_path), year)

            total_patents += count
            processed_years.append(year)

            # 询问是否继续
            if len(csv_files) > 1:
                continue_process = input("\n是否继续处理下一年？(y/n): ").strip().lower()
                if continue_process != 'y':
                    break

    # 显示汇总
    logger.info(f"\n{'='*60}")
    logger.info('📊 处理汇总')
    logger.info(f"{'='*60}")
    logger.info(f"已处理年份: {', '.join(processed_years)}")
    logger.info(f"总专利数: {total_patents:,}")
    logger.info(f"数据库路径: {db_path}")

    if total_patents > 0:
        # 创建搜索脚本
        create_search_script(str(db_path))

        # 提供使用说明
        logger.info("\n📝 使用说明:")
        logger.info(f"1. 搜索专利: python3 {output_dir}/search.py 关键词")
        logger.info("2. 查询特定年份:")
        logger.info(f"   sqlite3 {db_path}")
        logger.info("   SELECT patent_name, applicant FROM patents WHERE source_year = 2025 LIMIT 10;")

def create_search_script(db_path) -> None:
    """创建搜索脚本"""
    script_path = Path(db_path).parent / 'search_yearly.py'

    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(f'''#!/usr/bin/env python3
"""
专利搜索工具 - 年度数据库
"""

import sqlite3
import sys

def search(keyword, year=None, limit=20):
    conn = sqlite3.connect('{db_path}')
    cursor = conn.cursor()

    sql = """
        SELECT patent_name, applicant, application_date, source_year
        FROM patents
        WHERE (patent_name LIKE ? OR applicant LIKE ? OR abstract LIKE ?)
    """
    params = [f"%{{keyword}}%', f'%{{keyword}}%', f'%{{keyword}}%"]

    if year:
        sql += ' AND source_year = ?'
        params.append(int(year))

    sql += ' LIMIT ?'
    params.append(limit)

    cursor.execute(sql, params)
    results = cursor.fetchall()

    logger.info(f"\\n找到 {{len(results)}} 条结果:")
    logger.info(str('='*80))

    for i, (title, applicant, date, year) in enumerate(results, 1):
        logger.info(f"\\n{{i}}. 【{{year}}年】{{title}}")
        logger.info(f"   申请人: {{applicant}}")
        logger.info(f"   申请日: {{date}}")

    # 按年份统计
    cursor.execute("""
        SELECT source_year, COUNT(*)
        FROM patents
        WHERE patent_name LIKE ? OR applicant LIKE ? OR abstract LIKE ?
        GROUP BY source_year
        ORDER BY source_year
    """, [f"%{{keyword}}%", f"%{{keyword}}%", f"%{{keyword}}%"])

    year_stats = cursor.fetchall()
    if year_stats:
        logger.info(f"\\n按年份统计:")
        for year, count in year_stats:
            logger.info(f"  {{year}}年: {{count}}条")

    conn.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        keyword = input('请输入搜索关键词: ')
        year = input('请输入年份（回车搜索所有年份）: ').strip()
        year = int(year) if year else None
    else:
        keyword = sys.argv[1]
        year = int(sys.argv[2]) if len(sys.argv) > 2 else None

    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    search(keyword, year, limit)
''')

    os.chmod(script_path, 0o755)

if __name__ == '__main__':
    interactive_process()
