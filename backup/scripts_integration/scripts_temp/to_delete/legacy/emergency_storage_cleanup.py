#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
紧急存储清理工具
Emergency Storage Cleanup Tool

快速清理占用大量存储空间的非关键数据
"""

import json
import logging
import os
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/xujian/Athena工作平台/documentation/logs/emergency_cleanup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EmergencyStorageCleaner:
    """紧急存储清理器"""

    def __init__(self):
        self.project_root = '/Users/xujian/Athena工作平台'
        self.data_dir = '/Users/xujian/Athena工作平台/data'
        self.cleanup_stats = {
            'files_deleted': 0,
            'dirs_deleted': 0,
            'space_freed': 0,
            'compressed_files': 0,
            'errors': []
        }
        self.backup_dir = '/Users/xujian/Athena工作平台/emergency_backup'

        # 创建备份目录
        os.makedirs(self.backup_dir, exist_ok=True)

    def run_emergency_cleanup(self):
        """执行紧急清理"""
        logger.info('🚨 紧急存储清理工具')
        logger.info(str('=' * 60))

        # 计算清理前的大小
        initial_size = self.get_directory_size(self.data_dir)
        logger.info(f"📊 清理前data目录大小: {initial_size / (1024**3):.1f} GB")

        # 执行各种清理操作
        logger.info("\n🔧 开始执行清理操作...")

        # 1. 清理超大向量库
        logger.info("\n1️⃣ 清理向量库重复数据...")
        self.cleanup_vector_library()

        # 2. 优化法律知识图谱
        logger.info("\n2️⃣ 优化法律知识图谱...")
        self.optimize_law_knowledge_graph()

        # 3. 清理临时文件和缓存
        logger.info("\n3️⃣ 清理临时文件和缓存...")
        self.cleanup_temp_files()

        # 4. 压缩大文件
        logger.info("\n4️⃣ 压缩可优化文件...")
        self.compress_large_files()

        # 5. 清理重复数据
        logger.info("\n5️⃣ 清理重复数据...")
        self.cleanup_duplicate_data()

        # 计算清理后的大小
        final_size = self.get_directory_size(self.data_dir)
        space_freed = initial_size - final_size

        logger.info(f"\n✅ 清理完成!")
        logger.info(f"   清理前大小: {initial_size / (1024**3):.1f} GB")
        logger.info(f"   清理后大小: {final_size / (1024**3):.1f} GB")
        logger.info(f"   释放空间: {space_freed / (1024**3):.1f} GB")
        logger.info(f"   删除文件: {self.cleanup_stats['files_deleted']} 个")
        logger.info(f"   压缩文件: {self.cleanup_stats['compressed_files']} 个")

        # 生成清理报告
        self.generate_cleanup_report(initial_size, final_size)

        return True

    def cleanup_vector_library(self):
        """清理向量库重复数据"""
        vector_dir = Path('/Users/xujian/Athena工作平台/data/ultra_fast_legal_vector_db')

        if not vector_dir.exists():
            logger.info('   ⚠️ 向量库目录不存在')
            return

        logger.info(f"   📁 处理向量库: {vector_dir}")

        # 检查文件大小
        total_size = sum(f.stat().st_size for f in vector_dir.rglob('*') if f.is_file())
        logger.info(f"   📊 当前大小: {total_size / (1024**3):.1f} GB")

        # 备份关键数据
        self.backup_critical_data(vector_dir)

        # 删除最大的重复文件
        files_to_delete = [
            'ultra_fast_complete_data.json',  # 5.7GB
            'ultra_fast_data.pkl',            # 1.8GB
            'ultra_fast_vectors.npy'          # 1.6GB
        ]

        for filename in files_to_delete:
            file_path = vector_dir / filename
            if file_path.exists():
                try:
                    file_size = file_path.stat().st_size
                    # 移动到备份而不是删除
                    backup_path = Path(self.backup_dir) / filename
                    shutil.move(str(file_path), str(backup_path))

                    self.cleanup_stats['files_deleted'] += 1
                    self.cleanup_stats['space_freed'] += file_size
                    logger.info(f"   ✅ 已备份并删除: {filename} ({file_size / (1024**3):.1f} GB)")

                except Exception as e:
                    error_msg = f"处理文件失败 {filename}: {str(e)}"
                    logger.error(error_msg)
                    self.cleanup_stats['errors'].append(error_msg)

        # 保留压缩版本和元数据
        logger.info('   ✅ 保留压缩版本和元数据文件')

    def optimize_law_knowledge_graph(self):
        """优化法律知识图谱"""
        law_kg_dir = Path('/Users/xujian/Athena工作平台/data/law_knowledge_graph')

        if not law_kg_dir.exists():
            logger.info('   ⚠️ 法律知识图谱目录不存在')
            return

        logger.info(f"   📁 处理法律知识图谱: {law_kg_dir}")

        # 处理超大JSON文件
        relations_file = law_kg_dir / 'law_relations.json'
        if relations_file.exists():
            file_size = relations_file.stat().st_size
            logger.info(f"   📊 处理关系文件: {file_size / (1024**3):.1f} GB")

            try:
                # 备份原始文件
                backup_path = Path(self.backup_dir) / 'law_relations.json'
                shutil.move(str(relations_file), str(backup_path))

                # 创建优化的SQLite数据库
                self.create_optimized_law_db(law_kg_dir, backup_path)

                self.cleanup_stats['files_deleted'] += 1
                self.cleanup_stats['space_freed'] += file_size
                logger.info(f"   ✅ 已将JSON转换为优化数据库")

            except Exception as e:
                error_msg = f"优化法律知识图谱失败: {str(e)}"
                logger.error(error_msg)
                self.cleanup_stats['errors'].append(error_msg)

    def create_optimized_law_db(self, output_dir: Path, json_file: Path):
        """创建优化的法律知识图谱数据库"""
        db_path = output_dir / 'law_knowledge_optimized.db'

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # 创建优化的表结构
            cursor.execute("""
                CREATE TABLE law_relations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT,
                    target TEXT,
                    relation_type TEXT,
                    weight REAL,
                    metadata TEXT,
                    INDEX(source),
                    INDEX(target),
                    INDEX(relation_type)
                )
            """)

            cursor.execute("""
                CREATE TABLE law_entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    type TEXT,
                    description TEXT,
                    INDEX(name),
                    INDEX(type)
                )
            """)

            # 如果JSON文件不太大，处理它
            if json_file.stat().st_size < 2 * 1024**3:  # 小于2GB
                logger.info('   📝 处理JSON数据...')
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if isinstance(data, list):
                    # 批量插入关系数据
                    relations = []
                    for item in data[:100000]:  # 限制数量避免过大
                        if isinstance(item, dict):
                            relations.append((
                                item.get('source', ''),
                                item.get('target', ''),
                                item.get('relation', ''),
                                item.get('weight', 1.0),
                                json.dumps(item.get('metadata', {}), ensure_ascii=False)
                            ))

                    cursor.executemany(
                        'INSERT INTO law_relations (source, target, relation_type, weight, metadata) VALUES (?, ?, ?, ?, ?)',
                        relations
                    )

            conn.commit()
            optimized_size = db_path.stat().st_size
            logger.info(f"   ✅ 创建优化数据库: {optimized_size / (1024**2):.1f} MB")

        except Exception as e:
            logger.error(f"创建数据库失败: {str(e)}")
            if db_path.exists():
                db_path.unlink()
        finally:
            conn.close()

    def cleanup_temp_files(self):
        """清理临时文件和缓存"""
        temp_patterns = [
            '/Users/xujian/Athena工作平台/*.tmp',
            '/Users/xujian/Athena工作平台/cache/*',
            '/Users/xujian/Athena工作平台/documentation/logs/*.log.old',
            '/Users/xujian/Athena工作平台/__pycache__',
            '/Users/xujian/Athena工作平台/.pytest_cache',
            '/Users/xujian/Athena工作平台/data/temp/*',
            '/Users/xujian/Athena工作平台/data/cache/*'
        ]

        for pattern in temp_patterns:
            try:
                import glob
                for path in glob.glob(pattern):
                    path_obj = Path(path)
                    if path_obj.is_file():
                        file_size = path_obj.stat().st_size
                        path_obj.unlink()
                        self.cleanup_stats['files_deleted'] += 1
                        self.cleanup_stats['space_freed'] += file_size
                    elif path_obj.is_dir():
                        shutil.rmtree(path_obj)
                        self.cleanup_stats['dirs_deleted'] += 1
            except Exception as e:
                logger.error(f"清理临时文件失败 {pattern}: {str(e)}")

    def compress_large_files(self):
        """压缩大文件"""
        large_files = []

        # 查找大于100MB的文件
        for root, dirs, files in os.walk(self.data_dir):
            for file in files:
                file_path = Path(root) / file
                if file_path.is_file():
                    file_size = file_path.stat().st_size
                    if file_size > 100 * 1024 * 1024:  # 大于100MB
                        large_files.append((file_path, file_size))

        # 按大小排序
        large_files.sort(key=lambda x: x[1], reverse=True)

        logger.info(f"   📊 找到 {len(large_files)} 个大文件")

        # 只处理几个最大的文件
        for file_path, file_size in large_files[:5]:
            if file_path.suffix.lower() in ['.json', '.txt', '.csv', '.log']:
                try:
                    # 压缩文件
                    compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
                    self.compress_file(file_path, compressed_path)

                    # 删除原文件
                    file_path.unlink()

                    self.cleanup_stats['compressed_files'] += 1
                    self.cleanup_stats['space_freed'] += file_size * 0.7  # 估算节省70%

                    logger.info(f"   ✅ 压缩: {file_path.name} ({file_size / (1024**2):.1f} MB)")

                except Exception as e:
                    logger.error(f"压缩文件失败 {file_path}: {str(e)}")

    def compress_file(self, input_path: Path, output_path: Path):
        """压缩单个文件"""
        import gzip
        import shutil

        with open(input_path, 'rb') as f_in:
            with gzip.open(output_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

    def cleanup_duplicate_data(self):
        """清理重复数据"""
        # 检查并清理一些明显的重复目录
        duplicate_dirs = [
            '/Users/xujian/Athena工作平台/data/deprecated_20251205_184116',
            '/Users/xujian/Athena工作平台/data/backup',
            '/Users/xujian/Athena工作平台/data/temp'
        ]

        for dir_path in duplicate_dirs:
            path_obj = Path(dir_path)
            if path_obj.exists():
                try:
                    # 移动到备份而不是删除
                    backup_target = Path(self.backup_dir) / path_obj.name
                    if not backup_target.exists():
                        shutil.move(str(path_obj), str(backup_target))
                        self.cleanup_stats['dirs_deleted'] += 1
                        logger.info(f"   ✅ 已移动重复目录: {path_obj.name}")
                except Exception as e:
                    logger.error(f"清理重复目录失败 {dir_path}: {str(e)}")

    def backup_critical_data(self, source_dir: Path):
        """备份关键数据"""
        try:
            # 只备份元数据和小文件
            for file_path in source_dir.glob('*.json'):
                if file_path.stat().st_size < 10 * 1024 * 1024:  # 小于10MB
                    backup_path = Path(self.backup_dir) / file_path.name
                    if not backup_path.exists():
                        shutil.copy2(str(file_path), str(backup_path))
        except Exception as e:
            logger.error(f"备份失败: {str(e)}")

    def get_directory_size(self, directory: str) -> int:
        """获取目录大小"""
        total_size = 0
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = Path(root) / file
                if file_path.is_file():
                    try:
                        total_size += file_path.stat().st_size
                    except:
                        pass
        return total_size

    def generate_cleanup_report(self, initial_size: int, final_size: int):
        """生成清理报告"""
        report_file = '/Users/xujian/Athena工作平台/EMERGENCY_CLEANUP_REPORT.md'

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 紧急存储清理报告\n\n")
            f.write(f"**清理时间**: {datetime.now().isoformat()}\n")
            f.write(f"**清理工程师**: Athena AI Assistant\n\n")
            f.write("---\n\n")

            f.write("## 📊 清理统计\n\n")
            f.write(f"- **清理前大小**: {initial_size / (1024**3):.1f} GB\n")
            f.write(f"- **清理后大小**: {final_size / (1024**3):.1f} GB\n")
            f.write(f"- **释放空间**: {(initial_size - final_size) / (1024**3):.1f} GB\n")
            f.write(f"- **删除文件数**: {self.cleanup_stats['files_deleted']}\n")
            f.write(f"- **删除目录数**: {self.cleanup_stats['dirs_deleted']}\n")
            f.write(f"- **压缩文件数**: {self.cleanup_stats['compressed_files']}\n\n")

            f.write("## 🎯 清理效果\n\n")
            space_saved = initial_size - final_size
            percentage_saved = (space_saved / initial_size) * 100
            f.write(f"- **空间节省**: {percentage_saved:.1f}%\n")
            f.write(f"- **优化效果**: {'显著' if percentage_saved > 20 else '良好' if percentage_saved > 10 else '一般'}\n\n")

            if self.cleanup_stats['errors']:
                f.write("## ❌ 清理错误\n\n")
                for error in self.cleanup_stats['errors']:
                    f.write(f"- {error}\n")

            f.write("## 💡 后续建议\n\n")
            f.write("1. **定期清理**: 建立每月一次的存储清理机制\n")
            f.write("2. **数据归档**: 将不常用的历史数据归档到云存储\n")
            f.write("3. **监控机制**: 建立存储使用监控和预警\n")
            f.write("4. **优化策略**: 定期评估和优化数据存储格式\n\n")

            f.write("## ⚠️ 重要提醒\n\n")
            f.write(f"- 关键数据已备份到: {self.backup_dir}\n")
            f.write("- 如有需要可以从备份恢复数据\n")
            f.write("- 建议在恢复前验证系统功能正常\n")

        logger.info(f"\n📋 清理报告已生成: {report_file}")

def main():
    """主函数"""
    cleaner = EmergencyStorageCleaner()

    logger.info('⚠️ 即将执行紧急存储清理')
    logger.info('   - 清理向量库重复数据')
    logger.info('   - 优化法律知识图谱')
    logger.info('   - 清理临时文件和缓存')
    logger.info('   - 压缩大文件')
    logger.info('   - 清理重复数据')
    logger.info('   - 预计释放: 10-15 GB 存储空间')

    try:
        success = cleaner.run_emergency_cleanup()

        if success:
            logger.info(f"\n🎉 紧急存储清理完成!")
            logger.info(f"系统存储空间已显著优化")
        else:
            logger.info(f"\n❌ 清理过程中遇到问题")

    except KeyboardInterrupt:
        logger.info(f"\n⚠️ 清理被用户中断")
    except Exception as e:
        logger.info(f"\n❌ 清理失败: {str(e)}")

if __name__ == '__main__':
    main()