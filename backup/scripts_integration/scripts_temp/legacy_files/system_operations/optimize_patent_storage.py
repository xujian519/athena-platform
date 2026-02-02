#!/usr/bin/env python3
"""
专利数据存储优化脚本
压缩数据库，只保留核心字段，减少存储空间占用
"""

import logging
import os
import shutil
import sqlite3
import time
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('documentation/logs/storage_optimization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PatentStorageOptimizer:
    """专利存储优化器"""

    def __init__(self):
        self.base_path = Path('/Users/xujian/Athena工作平台')
        self.data_dir = self.base_path / 'data/patents/processed'
        self.backup_dir = self.base_path / 'data/patents/backup/optimized'

        # 核心字段列表（保留最重要的字段）
        self.core_fields = [
            'id',  # 主键
            'patent_name',  # 专利名称
            'applicant',  # 申请人
            'application_number',  # 申请号
            'application_date',  # 申请日
            'application_year',  # 申请年份
            'publication_number',  # 公开号
            'publication_date',  # 公开日
            'authorization_number',  # 授权号
            'authorization_date',  # 授权日
            'ipc_code',  # IPC分类号
            'inventor',  # 发明人
            'abstract',  # 摘要
            'claims_content',  # 权利要求
            'source_year',  # 数据源年份
            'indexed_at'  # 索引时间
        ]

        # 创建备份目录
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def analyze_database_sizes(self):
        """分析各数据库大小和使用情况"""
        logger.info("\n📊 数据库存储分析:")
        logger.info('=' * 60)

        db_files = list(self.data_dir.glob('*.db'))
        total_size = 0

        for db_file in db_files:
            if db_file.stat().st_size > 0:
                size_gb = db_file.stat().st_size / (1024**3)
                total_size += size_gb

                # 获取记录数
                try:
                    conn = sqlite3.connect(str(db_file))
                    cursor = conn.cursor()
                    cursor.execute('SELECT COUNT(*) FROM patents')
                    count = cursor.fetchone()[0]
                    conn.close()

                    logger.info(f"{db_file.name:30} {size_gb:6.2f}GB  {count:,}条记录")
                except:
                    logger.info(f"{db_file.name:30} {size_gb:6.2f}GB  (无法读取)")

        logger.info('-' * 60)
        logger.info(f"{'总计':30} {total_size:6.2f}GB")

        return total_size

    def optimize_database(self, input_db_path: str, output_db_path: str):
        """优化单个数据库"""
        logger.info(f"\n🔧 优化数据库: {Path(input_db_path).name}")

        start_time = time.time()

        # 连接源数据库
        source_conn = sqlite3.connect(input_db_path)
        source_cursor = source_conn.cursor()

        # 创建目标数据库
        target_conn = sqlite3.connect(output_db_path)
        target_cursor = target_conn.cursor()

        # 创建优化后的表结构
        create_table_sql = f"""
            CREATE TABLE patents (
                id INTEGER PRIMARY KEY,
                patent_name TEXT,
                applicant TEXT,
                application_number TEXT,
                application_date TEXT,
                application_year INTEGER,
                publication_number TEXT,
                publication_date TEXT,
                authorization_number TEXT,
                authorization_date TEXT,
                ipc_code TEXT,
                inventor TEXT,
                abstract TEXT,
                claims_content TEXT,
                source_year INTEGER,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        target_cursor.execute(create_table_sql)

        # 获取源表的所有列名
        source_cursor.execute('PRAGMA table_info(patents)')
        columns_info = source_cursor.fetchall()
        source_columns = [col[1] for col in columns_info]

        # 构建SELECT语句，只选择核心字段
        select_fields = []
        for field in self.core_fields:
            if field in source_columns and field != 'id':
                select_fields.append(field)

        if not select_fields:
            logger.error('没有找到匹配的字段')
            return False

        select_sql = f"SELECT {', '.join(select_fields)} FROM patents"

        # 批量迁移数据
        batch_size = 10000
        offset = 0
        total_migrated = 0

        while True:
        # TODO: 检查SQL注入风险 - source_cursor.execute(f"{select_sql} LIMIT {batch_size} OFFSET {offset}")
                    source_cursor.execute(f"{select_sql} LIMIT {batch_size} OFFSET {offset}")
            rows = source_cursor.fetchall()

            if not rows:
                break

            # 插入到目标表
            target_cursor.executemany(
                f"INSERT INTO patents ({', '.join(select_fields)}) VALUES ({', '.join(['?']*len(select_fields))})",
                rows
            )

            target_conn.commit()
            total_migrated += len(rows)
            offset += batch_size

            if offset % 100000 == 0:
                logger.info(f"  已迁移 {total_migrated:,} 条记录")

        # 创建索引
        logger.info('  创建索引...')
        indexes = [
            'CREATE INDEX idx_opt_year ON patents(source_year)',
            'CREATE INDEX idx_opt_applicant ON patents(applicant)',
            'CREATE INDEX idx_opt_name ON patents(patent_name)',
            'CREATE INDEX idx_opt_abstract ON patents(abstract)',
            'CREATE INDEX idx_opt_application_number ON patents(application_number)'
        ]

        for idx_sql in indexes:
            try:
                target_cursor.execute(idx_sql)
            except Exception as e:
                logger.warning(f"    索引创建警告: {e}")

        target_conn.commit()

        # 关闭连接
        source_conn.close()
        target_conn.close()

        # 压缩数据库
        logger.info('  压缩数据库...')
        conn = sqlite3.connect(output_db_path)
        conn.execute('VACUUM')
        conn.close()

        # 计算节省的空间
        original_size = os.path.getsize(input_db_path) / (1024**3)
        optimized_size = os.path.getsize(output_db_path) / (1024**3)
        saved_space = original_size - optimized_size
        saved_percent = (saved_space / original_size) * 100 if original_size > 0 else 0

        elapsed_time = time.time() - start_time

        logger.info(f"✅ 优化完成!")
        logger.info(f"  原始大小: {original_size:.2f}GB")
        logger.info(f"  优化大小: {optimized_size:.2f}GB")
        logger.info(f"  节省空间: {saved_space:.2f}GB ({saved_percent:.1f}%)")
        logger.info(f"  迁移记录: {total_migrated:,}条")
        logger.info(f"  耗时: {elapsed_time:.1f}秒")

        return True

    def optimize_all_databases(self):
        """优化所有数据库"""
        logger.info("\n🚀 开始优化所有专利数据库...")

        # 先备份现有数据库
        logger.info("\n📦 备份现有数据库...")
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_dir / f"backup_before_optimization_{timestamp}"
        backup_path.mkdir(exist_ok=True)

        for db_file in self.data_dir.glob('*.db'):
            if db_file.stat().st_size > 0:
                shutil.copy2(db_file, backup_path / db_file.name)
                logger.info(f"  已备份: {db_file.name}")

        # 优化各个数据库
        total_saved = 0

        databases_to_optimize = [
            ('china_patents_batch.db', 'china_patents_batch_optimized.db'),
            ('china_patents_enhanced.db', 'china_patents_enhanced_optimized.db'),
            ('china_patents_yearly.db', 'china_patents_yearly_optimized.db'),
            ('china_patents_safe.db', 'china_patents_safe_optimized.db')
        ]

        for input_name, output_name in databases_to_optimize:
            input_path = self.data_dir / input_name
            output_path = self.data_dir / output_name

            if input_path.exists() and input_path.stat().st_size > 0:
                original_size = input_path.stat().st_size / (1024**3)

                if self.optimize_database(str(input_path), str(output_path)):
                    optimized_size = os.path.getsize(output_path) / (1024**3)
                    total_saved += (original_size - optimized_size)

        logger.info(f"\n📈 优化总结:")
        logger.info(f"总节省空间: {total_saved:.2f}GB")

        # 生成优化报告
        self.generate_optimization_report()

        return total_saved

    def generate_optimization_report(self):
        """生成优化报告"""
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'optimized_fields': self.core_fields,
            'databases_before': {},
            'databases_after': {},
            'total_space_saved': 0
        }

        # 统计优化前后的大小
        for db_file in self.data_dir.glob('*.db'):
            if db_file.stat().st_size > 0:
                size_gb = db_file.stat().st_size / (1024**3)

                if 'optimized' in db_file.name:
                    original_name = db_file.name.replace('_optimized', '')
                    if original_name not in report['databases_before']:
                        report['databases_before'][original_name] = 0
                    report['databases_after'][original_name] = size_gb
                else:
                    if db_file.name not in report['databases_before']:
                        report['databases_before'][db_file.name] = 0
                    report['databases_before'][db_file.name] = size_gb

        # 计算节省的空间
        for db_name in report['databases_before']:
            before = report['databases_before'].get(db_name, 0)
            after = report['databases_after'].get(db_name, 0)
            if after > 0:
                report['total_space_saved'] += (before - after)

        # 保存报告
        import json

# 导入标准化数据库工具
from shared.database.db_utils import DatabaseManager, build_safe_query
        report_file = self.data_dir / 'optimization_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"\n📄 优化报告已生成: {report_file}")

def main():
    """主函数"""
    optimizer = PatentStorageOptimizer()

    # 分析当前存储状况
    total_size = optimizer.analyze_database_sizes()

    # 询问是否继续
    logger.info(f"\n当前数据库总大小: {total_size:.2f}GB")
    logger.info('优化将:')
    logger.info('1. 只保留16个核心字段')
    logger.info('2. 删除冗余和低频使用字段')
    logger.info('3. 压缩数据库，节省50-70%空间')
    logger.info('4. 保留原始数据备份')

    response = input("\n是否继续优化? (y/n): ")

    if response.lower() == 'y':
        saved_space = optimizer.optimize_all_databases()
        logger.info(f"\n✅ 优化完成! 共节省 {saved_space:.2f}GB 空间")

        # 清理建议
        logger.info("\n💡 建议:")
        logger.info('1. 删除原始的未优化数据库文件')
        logger.info('2. 将优化后的数据库重命名为原始名称')
        logger.info('3. 考虑将部分历史数据归档到外接存储')
    else:
        logger.info('优化已取消')

if __name__ == '__main__':
    main()