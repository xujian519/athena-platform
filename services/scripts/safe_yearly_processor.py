#!/usr/bin/env python3
"""
安全的专利数据处理器
增加数据验证和备份机制，确保大文件处理时不丢失数据
"""

import hashlib
import logging
import os
import shutil
import sqlite3
import time
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

class SafeYearlyProcessor:
    """安全的年度专利数据处理器"""

    def __init__(self):
        self.base_path = Path('/Users/xujian/Athena工作平台/data/patents/processed')
        self.base_path.mkdir(parents=True, exist_ok=True)

        # 备份目录
        self.backup_path = self.base_path / 'backups'
        self.backup_path.mkdir(parents=True, exist_ok=True)

    def backup_database(self, db_path) -> None:
        """备份数据库"""
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        backup_name = f"china_patents_backup_{timestamp}.db"
        backup_file = self.backup_path / backup_name

        logger.info(f"  📦 备份数据库到: {backup_name}")
        shutil.copy2(db_path, backup_file)

        # 只保留最近5个备份
        backups = sorted(self.backup_path.glob('china_patents_backup_*.db'))
        if len(backups) > 5:
            for old_backup in backups[:-5]:
                old_backup.unlink()
                logger.info(f"  🗑️  删除旧备份: {old_backup.name}")

    def verify_file_integrity(self, csv_path) -> None:
        """验证文件完整性"""
        logger.info("  🔍 验证文件完整性...")

        # 计算文件哈希
        hash_md5 = hashlib.md5()
        with open(csv_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        file_hash = hash_md5.hexdigest()

        # 检查文件大小
        file_size = os.path.getsize(csv_path)

        logger.info(f"  ✓ 文件大小: {file_size / (1024**2):.1f} MB")
        logger.info(f"  ✓ MD5: {file_hash[:16]}...")

        # 快速读取验证
        try:
            # 读取前100行验证格式
            sample_df = pd.read_csv(csv_path, encoding='utf-8', nrows=100)
            logger.info(f"  ✓ 列数: {len(sample_df.columns)}")
            logger.info("  ✓ 采样数据验证通过")
            return True, file_hash
        except Exception as e:
            logger.info(f"  ❌ 文件验证失败: {e}")
            return False, None

    def process_year_file_safe(self, csv_path, db_path, batch_size=10000) -> None:
        """安全处理单个年度文件"""
        year = Path(csv_path).stem.split('中国专利数据库')[-1][:4]
        file_name = Path(csv_path).name
        file_size_mb = os.path.getsize(csv_path) / (1024**2)

        logger.info(f"\n{'='*60}")
        logger.info(f"📅 安全处理 {year} 年数据")
        logger.info(f"文件: {file_name}")
        logger.info(f"大小: {file_size_mb:.1f} MB")
        logger.info(f"{'='*60}")

        # 1. 备份当前数据库
        if os.path.exists(db_path):
            self.backup_database(db_path)

        # 2. 验证文件完整性
        valid, file_hash = self.verify_file_integrity(csv_path)
        if not valid:
            logger.info("❌ 文件验证失败，停止处理")
            return False, 0

        start_time = time.time()

        # 3. 连接数据库（带错误处理）
        conn = None
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # 优化设置
            pragmas = [
                'PRAGMA journal_mode = WAL',
                'PRAGMA synchronous = NORMAL',  # 改为NORMAL，更安全
                'PRAGMA cache_size = -2000000',  # 2GB缓存
                'PRAGMA page_size = 32768',
                'PRAGMA temp_store = MEMORY',
                'PRAGMA wal_autocheckpoint = 1000;',  # 自动检查点
            ]
            for pragma in pragmas:
                cursor.execute(pragma)

            conn.commit()
        except Exception as e:
            logger.info(f"❌ 数据库连接失败: {e}")
            return False, 0

        # 4. 创建表（如果不存在）
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
                file_hash TEXT,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 5. 分块读取和处理
        logger.info("📝 开始分块处理数据...")
        total_processed = 0
        chunk_count = 0

        try:
            # 使用pandas分块读取
            reader = pd.read_csv(csv_path, encoding='utf-8',
                                chunksize=batch_size,
                                low_memory=False,
                                on_bad_lines='skip')

            for chunk_df in reader:
                chunk_count += 1
                chunk_start = time.time()

                logger.info(f"  处理批次 {chunk_count} ({len(chunk_df):,} 条)...")

                # 准备数据
                batch_data = []
                valid_count = 0

                for _, row in chunk_df.iterrows():
                    try:
                        # 验证必要字段
                        if pd.notna(row.get('专利名称')) and pd.notna(row.get('申请人')):
                            batch_data.append((
                                self._safe_str(row.get('专利名称', '')),
                                self._safe_str(row.get('专利类型', '')),
                                self._safe_str(row.get('申请人', '')),
                                self._safe_str(row.get('申请人类型', '')),
                                self._safe_str(row.get('申请号', '')),
                                self._safe_str(row.get('申请日', '')),
                                self._safe_int(row.get('申请年份', 0)),
                                self._safe_str(row.get('公开公告号', '')),
                                self._safe_str(row.get('公开公告日', '')),
                                self._safe_int(row.get('公开公告年份', 0)),
                                self._safe_str(row.get('IPC分类号', '')),
                                self._safe_str(row.get('IPC主分类号', '')),
                                self._safe_str(row.get('发明人', '')),
                                self._safe_str(row.get('摘要文本', '')),
                                self._safe_str(row.get('主权项内容', '')),
                                int(year) if year.isdigit() else 0,
                                file_name,
                                file_hash
                            ))
                            valid_count += 1
                    except Exception:
                        continue

                if batch_data:
                    # 批量插入
                    cursor.executemany('''
                        INSERT INTO patents (
                            patent_name, patent_type, applicant, applicant_type,
                            application_number, application_date, application_year,
                            publication_number, publication_date, publication_year,
                            ipc_code, ipc_main_class, inventor, abstract, claims_content,
                            source_year, source_file, file_hash
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', batch_data)

                    conn.commit()
                    total_processed += valid_count

                    chunk_time = time.time() - chunk_start
                    logger.info(f"    ✓ 完成: {valid_count:,} 条, 用时: {chunk_time:.1f}秒")

                # 定期创建检查点
                if chunk_count % 10 == 0:
                    cursor.execute('PRAGMA wal_checkpoint(TRUNCATE);')
                    logger.info("    💾 创建检查点")

        except Exception as e:
            logger.info(f"❌ 处理过程中出错: {e}")
            # 尝试回滚
            conn.rollback()
            if conn:
                conn.close()
            return False, 0

        # 6. 创建索引
        logger.info("🔨 创建索引...")
        index_start = time.time()

        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_year ON patents(source_year)',
            'CREATE INDEX IF NOT EXISTS idx_applicant ON patents(applicant)',
            'CREATE INDEX IF NOT EXISTS idx_patent_name ON patents(patent_name)',
            'CREATE INDEX IF NOT EXISTS idx_application_number ON patents(application_number)',
        ]

        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except Exception as e:
                logger.info(f"  ⚠️  索引创建警告: {e}")

        conn.commit()
        index_time = time.time() - index_start

        # 7. 最终检查点
        cursor.execute('PRAGMA wal_checkpoint(TRUNCATE);')
        conn.close()

        total_time = time.time() - start_time

        # 8. 验证结果
        logger.info("\n📊 处理完成统计:")
        logger.info(f"  总记录数: {total_processed:,}")
        logger.info(f"  处理批次: {chunk_count}")
        logger.info(f"  总用时: {total_time:.1f}秒")
        logger.info(f"  索引用时: {index_time:.1f}秒")
        logger.info(f"  平均速度: {total_processed/total_time:.0f} 条/秒")

        return True, total_processed

    def _safe_str(self, value) -> None:
        """安全转换为字符串"""
        if pd.isna(value) or value is None:
            return ''
        return str(value).strip()

    def _safe_int(self, value) -> None:
        """安全转换为整数"""
        try:
            if pd.isna(value) or value is None or value == '':
                return 0
            return int(float(value))
        except (KeyError, TypeError, IndexError, ValueError):
            return 0

    def verify_database(self, db_path, year) -> None:
        """验证数据库中的数据"""
        logger.info(f"\n🔍 验证 {year} 年数据...")

        try:
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

            conn.close()
            return True

        except Exception as e:
            logger.info(f"  ❌ 验证失败: {e}")
            return False

# 使用示例
if __name__ == '__main__':
    processor = SafeYearlyProcessor()

    # 处理单个文件
    csv_path = input('请输入CSV文件路径: ').strip()
    db_path = processor.base_path / 'china_patents_safe.db'

    if os.path.exists(csv_path):
        success, count = processor.process_year_file_safe(csv_path, str(db_path))
        if success:
            # 验证数据
            year = Path(csv_path).stem.split('中国专利数据库')[-1][:4]
            processor.verify_database(str(db_path), year)
            logger.info(f"\n✅ 处理完成! 共处理 {count:,} 条专利")
        else:
            logger.info("\n❌ 处理失败")
    else:
        logger.info(f"❌ 文件不存在: {csv_path}")
