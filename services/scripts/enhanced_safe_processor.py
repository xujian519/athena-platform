#!/usr/bin/env python3
"""
增强版安全专利数据处理器
针对超大文件优化，支持断点续传
"""

import json
import logging
import os
import shutil
import sqlite3
import sys
import time
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

class EnhancedSafeProcessor:
    """增强版安全处理器"""

    def __init__(self):
        self.base_path = Path('/Users/xujian/Athena工作平台/data/patents/processed')
        self.base_path.mkdir(parents=True, exist_ok=True)

        # 备份目录
        self.backup_path = self.base_path / 'backups'
        self.backup_path.mkdir(parents=True, exist_ok=True)

        # 进度目录
        self.progress_path = self.base_path / 'progress'
        self.progress_path.mkdir(parents=True, exist_ok=True)

    def get_progress_file(self, csv_path) -> None:
        """获取进度文件路径"""
        csv_name = Path(csv_path).stem
        return self.progress_path / f"{csv_name}_progress.json"

    def save_progress(self, csv_path, processed_rows, total_rows, batch_num) -> None:
        """保存处理进度"""
        progress_file = self.get_progress_file(csv_path)
        progress_data = {
            'csv_path': str(csv_path),
            'processed_rows': processed_rows,
            'total_rows': total_rows,
            'batch_num': batch_num,
            'timestamp': time.time()
        }

        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)

    def load_progress(self, csv_path) -> None:
        """加载处理进度"""
        progress_file = self.get_progress_file(csv_path)

        if progress_file.exists():
            with open(progress_file, encoding='utf-8') as f:
                return json.load(f)
        return None

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

    def process_large_file_safe(self, csv_path, db_path, batch_size=5000) -> None:
        """安全处理大文件（小批次）"""
        year = Path(csv_path).stem.split('中国专利数据库')[-1][:4]
        file_name = Path(csv_path).name
        file_size_gb = os.path.getsize(csv_path) / (1024**3)

        logger.info(f"\n{'='*60}")
        logger.info(f"📅 安全处理 {year} 年大文件数据")
        logger.info(f"文件: {file_name}")
        logger.info(f"大小: {file_size_gb:.2f} GB")
        logger.info(f"批次大小: {batch_size:,}")
        logger.info(f"{'='*60}")

        # 检查是否有未完成的进度
        progress = self.load_progress(csv_path)
        if progress:
            logger.info("\n⚠️  发现未完成的进度:")
            logger.info(f"  已处理: {progress['processed_rows']:,} 行")
            logger.info(f"  总计: {progress['total_rows']:,} 行")
            logger.info(f"  进度: {progress['processed_rows']/progress['total_rows']*100:.1f}%")

            choice = input('是否继续处理？(y/n): ').strip().lower()
            if choice != 'y':
                logger.info('已取消处理')
                return False, 0

        # 1. 备份当前数据库
        if os.path.exists(db_path):
            self.backup_database(db_path)

        # 2. 连接数据库
        conn = None
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # 优化设置（更保守）
            pragmas = [
                'PRAGMA journal_mode = WAL',
                'PRAGMA synchronous = NORMAL',  # 保证数据安全
                'PRAGMA cache_size = -1000000',  # 1GB缓存
                'PRAGMA page_size = 32768',
                'PRAGMA temp_store = MEMORY',
                'PRAGMA wal_autocheckpoint = 1000',
            ]
            for pragma in pragmas:
                cursor.execute(pragma)

            conn.commit()
        except Exception as e:
            logger.info(f"❌ 数据库连接失败: {e}")
            return False, 0

        # 3. 创建表（如果不存在）
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

        # 4. 分块读取和处理
        logger.info("\n📝 开始分块处理数据...")
        total_processed = progress['processed_rows'] if progress else 0
        batch_count = progress['batch_num'] if progress else 0
        skip_rows = progress['processed_rows'] if progress else 0

        try:
            # 使用pandas分块读取，跳过已处理的行
            reader = pd.read_csv(csv_path,
                                encoding='utf-8',
                                chunksize=batch_size,
                                low_memory=False,
                                on_bad_lines='warn',  # 警告而不是跳过
                                skiprows=skip_rows)

            for chunk_df in reader:
                batch_count += 1
                chunk_start = time.time()

                logger.info(f"\n  处理批次 {batch_count} (原始: {len(chunk_df):,} 行)...")

                # 清理数据
                valid_count = 0
                batch_data = []

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
                                ''  # file_hash
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
                    logger.info(f"    ✓ 有效记录: {valid_count:,}/{len(chunk_df):,}")
                    logger.info(f"    ✓ 用时: {chunk_time:.1f}秒")
                    logger.info(f"    ✓ 累计: {total_processed:,}")

                # 每10个批次保存进度
                if batch_count % 10 == 0:
                    # 估算总行数（基于已处理的部分）
                    estimated_total = (total_processed / skip_rows) * os.path.getsize(csv_path) if skip_rows > 0 else total_processed * 10
                    self.save_progress(csv_path, total_processed, estimated_total, batch_count)
                    logger.info("    💾 进度已保存")

                # 定期创建检查点
                if batch_count % 20 == 0:
                    cursor.execute('PRAGMA wal_checkpoint(TRUNCATE);')
                    logger.info("    💾 创建检查点")

        except KeyboardInterrupt:
            logger.info("\n\n⚠️  用户中断处理")
            logger.info(f"  已处理: {total_processed:,} 行")
            self.save_progress(csv_path, total_processed, total_processed * 2, batch_count)
            logger.info("  进度已保存，可以稍后继续")

            if conn:
                conn.close()
            return False, 0

        except Exception as e:
            logger.info(f"\n❌ 处理过程中出错: {e}")
            # 尝试回滚
            conn.rollback()
            if conn:
                conn.close()
            return False, 0

        # 5. 创建索引
        logger.info("\n🔨 创建索引...")
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
        time.time() - index_start

        # 6. 最终检查点
        cursor.execute('PRAGMA wal_checkpoint(TRUNCATE);')
        conn.close()

        # 7. 清理进度文件
        progress_file = self.get_progress_file(csv_path)
        if progress_file.exists():
            progress_file.unlink()
            logger.info("  🗑️  清理进度文件")

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

            logger.info(f"  总记录数: {total_count:,}")

            # 显示前3条示例
            cursor.execute('''
                SELECT patent_name, applicant, application_date
                FROM patents
                WHERE source_year = ?
                LIMIT 3
            ''', (int(year),))

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
    processor = EnhancedSafeProcessor()

    # 处理大文件
    if len(sys.argv) < 2:
        logger.info('增强版安全处理器')
        logger.info('使用方法: python enhanced_safe_processor.py CSV文件路径')
        sys.exit(1)

    csv_path = sys.argv[1]
    db_path = processor.base_path / 'china_patents_enhanced.db'

    if os.path.exists(csv_path):
        success, count = processor.process_large_file_safe(csv_path, str(db_path))
        if success:
            year = Path(csv_path).stem.split('中国专利数据库')[-1][:4]
            processor.verify_database(str(db_path), year)
            logger.info(f"\n✅ 处理完成! 共处理 {count:,} 条专利")
        else:
            logger.info("\n❌ 处理失败")
    else:
        logger.info(f"❌ 文件不存在: {csv_path}")
