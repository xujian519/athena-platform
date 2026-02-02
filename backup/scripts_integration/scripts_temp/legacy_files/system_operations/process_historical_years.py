#!/usr/bin/env python3
"""
处理1985-2012年的历史专利数据
每处理完一年立即验证并删除备份，节省存储空间
"""

import logging
import os
import shutil
import sqlite3
import sys
import time
from pathlib import Path

import psutil

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('documentation/logs/process_historical_years.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class HistoricalYearProcessor:
    """历史年份专利数据处理器"""

    def __init__(self):
        self.source_dir = '/Volumes/xujian/patent_data/china_patents'
        self.db_path = 'data/patents/processed/china_patents_enhanced.db'
        self.backup_dir = Path('data/patents/processed/backups')
        self.processed_years = []

    def get_disk_usage(self):
        """获取磁盘使用情况"""
        usage = psutil.disk_usage('/')
        return {
            'total': usage.total / (1024**3),  # GB
            'used': usage.used / (1024**3),
            'free': usage.free / (1024**3),
            'percent': (usage.used / usage.total) * 100
        }

    def check_disk_space(self):
        """检查磁盘空间"""
        disk = self.get_disk_usage()
        if disk['percent'] > 85:
            logger.warning(f"⚠️ 磁盘空间不足! 已用: {disk['percent']:.1f}%")
            return False
        logger.info(f"💾 磁盘空间充足: 已用 {disk['percent']:.1f}%, 剩余 {disk['free']:.1f}GB")
        return True

    def get_processed_years(self):
        """获取已处理的年份"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT source_year
                FROM patents
                WHERE source_year IS NOT NULL
                ORDER BY source_year
            """)
            years = [row[0] for row in cursor.fetchall()]
            conn.close()
            return years
        except:
            return []

    def process_year(self, year):
        """处理单个年份的数据"""
        csv_file = Path(self.source_dir) / f"中国专利数据库{year}年.csv"

        if not csv_file.exists():
            logger.warning(f"⚠️  {year}年文件不存在")
            return False, 0

        file_size_mb = csv_file.stat().st_size / (1024 * 1024)
        logger.info(f"\n{'='*60}")
        logger.info(f"处理 {year} 年数据")
        logger.info(f"文件大小: {file_size_mb:.1f} MB")

        # 检查磁盘空间
        if not self.check_disk_space():
            logger.error('❌ 磁盘空间不足，停止处理')
            return False, 0

        # 备份当前数据库（小备份）
        pre_backup = self.create_mini_backup(year)

        # 使用enhanced_patent_processor处理
        try:
            import sys
            from pathlib import Path
            sys.path.append(str(Path(__file__).parent.parent))
            from services.enhanced_patent_processor import EnhancedPatentProcessor
            processor = EnhancedPatentProcessor()

            start_time = time.time()
            success, count = processor.process_patent_file(
                csv_path=str(csv_file),
                db_path=self.db_path,
                batch_size=2000
            )
            elapsed = time.time() - start_time

            if success:
                logger.info(f"✅ {year}年处理成功!")
                logger.info(f"  导入记录: {count:,} 条")
                logger.info(f"  处理时间: {elapsed:.1f}秒")

                # 验证数据
                if self.verify_year_data(year, expected_min=count * 0.95):
                    logger.info(f"✅ {year}年数据验证通过")

                    # 删除备份
                    if pre_backup and os.path.exists(pre_backup):
                        os.remove(pre_backup)
                        logger.info(f"  🗑️  已删除处理前备份")

                    # 删除该年的其他备份
                    self.cleanup_year_backups(year)

                    self.processed_years.append(year)
                    return True, count
                else:
                    logger.error(f"❌ {year}年数据验证失败")
                    return False, 0
            else:
                logger.error(f"❌ {year}年处理失败")
                return False, 0

        except Exception as e:
            logger.error(f"❌ {year}年处理异常: {str(e)}")
            return False, 0

    def create_mini_backup(self, year):
        """创建小型备份"""
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f"mini_backup_{year}_{timestamp}.db"

        try:
            # 创建数据库连接并快速备份
            os.makedirs(self.backup_dir, exist_ok=True)
            shutil.copy2(self.db_path, backup_file)
            logger.info(f"  📦 创建迷你备份: {backup_file.name}")
            return str(backup_file)
        except Exception as e:
            logger.error(f"  ❌ 创建备份失败: {str(e)}")
            return None

    def verify_year_data(self, year, expected_min=0):
        """验证年份数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 检查该年份数据量
            cursor.execute(
                'SELECT COUNT(*) FROM patents WHERE source_year = ?',
                (year,)
            )
            count = cursor.fetchone()[0]

            logger.info(f"  📊 {year}年统计:")
            logger.info(f"    记录数: {count:,}")

            # 抽样检查
            cursor.execute("""
                SELECT patent_name, applicant, application_number
                FROM patents
                WHERE source_year = ?
                AND patent_name IS NOT NULL
                LIMIT 3
            """, (year,))

            samples = cursor.fetchall()
            if samples:
                logger.info(f"  📋 样本数据:")
                for i, (name, applicant, app_num) in enumerate(samples, 1):
                    logger.info(f"    {i}. {name[:50]}...")
                    if applicant:
                        logger.info(f"       申请人: {applicant[:30]}")
                    if app_num:
                        logger.info(f"       申请号: {app_num}")

            conn.close()

            # 验证数量是否合理
            if expected_min > 0 and count >= expected_min:
                return True

            return count > 0

        except Exception as e:
            logger.error(f"  ❌ 验证失败: {str(e)}")
            return False

    def cleanup_year_backups(self, year):
        """清理指定年份的所有备份"""
        backup_patterns = [
            f"*{year}*.db",
            f"mini_backup_{year}_*.db"
        ]

        total_saved = 0
        for pattern in backup_patterns:
            for backup in Path(self.backup_dir).glob(pattern):
                try:
                    size_mb = backup.stat().st_size / (1024 * 1024)
                    backup.unlink()
                    total_saved += size_mb
                    logger.info(f"  🗑️  删除备份: {backup.name} (节省 {size_mb:.1f} MB)")
                except Exception as e:
                    logger.error(f"  ⚠️  删除失败 {backup.name}: {str(e)}")

        if total_saved > 0:
            logger.info(f"  💾 总共节省空间: {total_saved:.1f} MB")

    def cleanup_all_backups(self):
        """清理所有旧备份，只保留最近的3个"""
        logger.info("\n清理旧备份文件...")

        all_backups = list(Path(self.backup_dir).glob('*.db'))
        if len(all_backups) <= 3:
            logger.info('  备份文件数量不多，保留所有')
            return

        # 按修改时间排序，删除旧备份
        all_backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        backups_to_delete = all_backups[3:]

        total_saved = 0
        for backup in backups_to_delete:
            try:
                size_mb = backup.stat().st_size / (1024 * 1024)
                backup.unlink()
                total_saved += size_mb
                logger.info(f"  🗑️  删除旧备份: {backup.name} (节省 {size_mb:.1f} MB)")
            except Exception as e:
                logger.error(f"  ⚠️  删除失败 {backup.name}: {str(e)}")

        if total_saved > 0:
            logger.info(f"  💾 清理旧备份共节省: {total_saved:.1f} MB")

    def get_available_years(self, start_year=1985, end_year=2012):
        """获取可处理的年份列表"""
        years = []
        for f in Path(self.source_dir).glob('中国专利数据库*.csv'):
            try:
                year = int(f.name.split('中国专利数据库')[1].split('年')[0])
                if start_year <= year <= end_year:
                    years.append(year)
            except:
                continue

        return sorted(years)

    def run(self):
        """主处理流程"""
        logger.info('='*60)
        logger.info('处理1985-2012年历史专利数据')
        logger.info(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info('='*60)

        # 检查源目录
        if not os.path.exists(self.source_dir):
            logger.error(f"❌ 源目录不存在: {self.source_dir}")
            return

        # 获取已处理的年份
        processed = self.get_processed_years()
        logger.info(f"\n已处理年份: {processed}")

        # 获取需要处理的年份
        available_years = self.get_available_years(1985, 2012)
        logger.info(f"\n需要处理的年份: {available_years}")

        if not available_years:
            logger.info('✅ 所有年份都已处理完成!')
            return

        # 过滤已处理的年份
        years_to_process = [y for y in available_years if y not in processed]
        logger.info(f"\n实际需要处理: {years_to_process}")

        # 清理旧备份
        self.cleanup_all_backups()

        # 统计信息
        total_processed = 0
        successful_years = []

        # 处理每一年
        for i, year in enumerate(years_to_process, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"[{i}/{len(years_to_process)}] 处理进度: {(i-1)/len(years_to_process)*100:.1f}%")
            logger.info(f"{'='*60}")

            success, count = self.process_year(year)

            if success:
                total_processed += count
                successful_years.append(year)

                # 显示进度
                logger.info(f"\n📊 当前进度:")
                logger.info(f"  成功年份: {len(successful_years)}/{len(years_to_process)}")
                logger.info(f"  总记录数: {total_processed:,}")
                logger.info(f"  成功率: {len(successful_years)/i*100:.1f}%")
            else:
                logger.error(f"\n❌ {year}年处理失败，继续下一年")

            # 强制垃圾回收
            if i % 3 == 0:
                import gc
                gc.collect()

        # 最终统计
        logger.info("\n" + '='*60)
        logger.info('处理完成!')
        logger.info('='*60)

        logger.info(f"\n处理结果:")
        logger.info(f"  成功年份: {successful_years}")
        logger.info(f"  总记录数: {total_processed:,}")

        # 检查最终磁盘使用
        disk = self.get_disk_usage()
        logger.info(f"\n磁盘使用情况:")
        logger.info(f"  总容量: {disk['total']:.1f} GB")
        logger.info(f"  已使用: {disk['used']:.1f} GB ({disk['percent']:.1f}%)")
        logger.info(f"  剩余: {disk['free']:.1f} GB")

        # 数据库最终统计
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM patents')
            total = cursor.fetchone()[0]

            cursor.execute("""
                SELECT source_year, COUNT(*)
                FROM patents
                WHERE source_year IS NOT NULL
                GROUP BY source_year
                ORDER BY source_year
            """)
            year_stats = cursor.fetchall()

            conn.close()

            logger.info(f"\n最终数据库统计:")
            logger.info(f"  总专利数: {total:,}")
            logger.info(f"\n按年份统计:")
            for year, count in year_stats:
                logger.info(f"  {year}年: {count:,} 条")

        except Exception as e:
            logger.error(f"\n获取数据库统计失败: {str(e)}")

        logger.info(f"\n完成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info('='*60)

def main():
    processor = HistoricalYearProcessor()
    processor.run()

if __name__ == '__main__':
    main()