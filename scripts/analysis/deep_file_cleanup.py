#!/usr/bin/env python3
"""
深度文件清理系统
识别并处理过期、大文件和冗余数据
"""

import logging

logger = logging.getLogger(__name__)

import json
import shutil
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# 添加项目路径
sys.path.append('/Users/xujian/Athena工作平台')

class DeepFileCleaner:
    """深度文件清理器"""

    def __init__(self):
        self.base_path = Path("/Users/xujian/Athena工作平台")
        self.backup_path = Path("/Users/xujian/Athena工作平台/backup_files")
        self.logs_path = Path("/Users/xujian/Athena工作平台/logs")

        # 深度清理配置
        self.deep_cleanup_config = {
            'large_file_threshold_mb': 100,     # 大于100MB的文件
            'old_database_days': 90,            # 超过90天的数据库文件
            'log_file_days': 30,                # 超过30天的日志文件
            'cache_file_days': 7,               # 超过7天的缓存文件
            'temp_file_hours': 24,              # 超过24小时的临时文件
            'max_backup_size_gb': 2,            # 备份最大2GB
            'db_size_limit_mb': 1000,           # 数据库文件大小限制
        }

        self.cleanup_stats = {
            'large_files_found': 0,
            'large_files_size_mb': 0,
            'databases_cleaned': 0,
            'db_space_freed_mb': 0,
            'logs_archived': 0,
            'log_space_freed_mb': 0,
            'caches_cleared': 0,
            'cache_space_freed_mb': 0,
            'temp_files_removed': 0,
            'temp_space_freed_mb': 0,
            'total_space_freed_mb': 0
        }

    def start_deep_cleanup(self) -> Any:
        """启动深度清理流程"""
        print("🔬 启动深度文件清理系统...")
        print(f"📅 清理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        try:
            # 1. 分析大文件
            print("📊 第1步: 分析大文件...")
            self._analyze_large_files()

            # 2. 清理数据库文件
            print("🗄️ 第2步: 清理数据库文件...")
            self._cleanup_database_files()

            # 3. 归档和压缩日志文件
            print("📋 第3步: 归档和压缩日志文件...")
            self._archive_log_files()

            # 4. 清理缓存文件
            print("🗂️ 第4步: 清理缓存文件...")
            self._clear_cache_files()

            # 5. 清理临时文件
            print("🧹 第5步: 清理临时文件...")
            self._clear_temp_files()

            # 6. 优化存储结构
            print("⚡ 第6步: 优化存储结构...")
            self._optimize_storage_structure()

            # 7. 生成深度清理报告
            self._generate_deep_cleanup_report()

            print("\n🎉 深度文件清理完成!")
            self._display_deep_summary()

        except Exception as e:
            print(f"\n❌ 深度清理过程中出现错误: {e}")
            import traceback
            traceback.print_exc()

    def _analyze_large_files(self) -> Any:
        """分析大文件"""
        print("   🔍 扫描大文件...")

        large_files = []
        threshold_bytes = self.deep_cleanup_config['large_file_threshold_mb'] * 1024 * 1024

        # 扫描整个项目目录
        for file_path in self.base_path.rglob('*'):
            try:
                if file_path.is_file() and file_path.stat().st_size > threshold_bytes:
                    # 跳过一些重要的系统文件
                    if self._should_skip_large_file(file_path):
                        continue

                    file_info = {
                        'path': str(file_path),
                        'name': file_path.name,
                        'size_mb': round(file_path.stat().st_size / (1024 * 1024), 2),
                        'modified': datetime.fromtimestamp(file_path.stat().st_mtime)
                    }
                    large_files.append(file_info)
                    self.cleanup_stats['large_files_found'] += 1
                    self.cleanup_stats['large_files_size_mb'] += file_info['size_mb']

            except (OSError, PermissionError):
                continue

        # 按大小排序
        large_files.sort(key=lambda x: x['size_mb'], reverse=True)

        # 显示最大的文件
        print(f"   📊 发现 {len(large_files)} 个大文件 (> {self.deep_cleanup_config['large_file_threshold_mb']}MB):")
        for file_info in large_files[:10]:  # 显示前10个
            print(f"      - {file_info['name']}: {file_info['size_mb']} MB ({file_info['path']})")

        if len(large_files) > 10:
            print(f"      ... 还有 {len(large_files) - 10} 个大文件")

        # 分析哪些大文件可以压缩或移动
        for file_info in large_files:
            if self._should_compress_large_file(file_info):
                self._compress_large_file(file_info)

    def _should_skip_large_file(self, file_path: Path) -> bool:
        """判断是否应该跳过大文件分析"""
        skip_patterns = [
            '.git/', 'node_modules/', '__pycache__/',
            '.pyenv/', '.venv/', 'venv/', 'env/',
            'Applications/', 'Library/', 'Downloads/'
        ]

        return any(pattern in str(file_path) for pattern in skip_patterns)

    def _should_compress_large_file(self, file_info: dict[str, Any]) -> bool:
        """判断是否应该压缩大文件"""
        path = Path(file_info['path'])

        # 压缩日志文件
        if path.suffix in ['.log', '.out']:
            return True

        # 压缩备份数据库
        if 'backup' in path.name.lower() or path.suffix in ['.db', '.sqlite']:
            # 只压缩超过7天未修改的文件
            days_old = (datetime.now() - file_info['modified']).days
            return days_old > 7

        return False

    def _compress_large_file(self, file_info: dict[str, Any]) -> Any:
        """压缩大文件"""
        try:
            source_path = Path(file_info['path'])
            compressed_path = source_path.with_suffix(source_path.suffix + '.gz')

            if not compressed_path.exists():
                print(f"   🗜️ 压缩大文件: {file_info['name']}")

                # 使用gzip压缩
                import gzip
                with open(source_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

                # 获取压缩后的大小
                compressed_size_mb = round(compressed_path.stat().st_size / (1024 * 1024), 2)
                space_saved_mb = file_info['size_mb'] - compressed_size_mb

                # 删除原文件
                source_path.unlink()

                print(f"      ✅ 压缩完成: {file_info['size_mb']} MB → {compressed_size_mb} MB (节省 {space_saved_mb} MB)")

        except Exception as e:
            print(f"   ⚠️ 压缩文件失败 {file_info['path']}: {e}")

    def _cleanup_database_files(self) -> Any:
        """清理数据库文件"""
        print("   🗄️ 扫描数据库文件...")

        db_files = list(self.base_path.rglob('*.db')) + list(self.base_path.rglob('*.sqlite'))

        for db_file in db_files:
            try:
                db_info = {
                    'path': str(db_file),
                    'name': db_file.name,
                    'size_mb': round(db_file.stat().st_size / (1024 * 1024), 2),
                    'modified': datetime.fromtimestamp(db_file.stat().st_mtime)
                }

                # 检查数据库文件是否过期
                days_old = (datetime.now() - db_info['modified']).days

                if days_old > self.deep_cleanup_config['old_database_days']:
                    # 备份并删除过期数据库
                    self._backup_and_remove_old_database(db_info)

                elif db_info['size_mb'] > self.deep_cleanup_config['db_size_limit_mb']:
                    # 清理过大的数据库
                    self._vacuum_large_database(db_info)

            except Exception as e:
                print(f"   ⚠️ 处理数据库失败 {db_file}: {e}")

    def _backup_and_remove_old_database(self, db_info: dict[str, Any]) -> Any:
        """备份并删除过期数据库"""
        try:
            source_path = Path(db_info['path'])
            backup_dir = self.backup_path / datetime.now().strftime('%Y%m%d') / 'old_databases'
            backup_dir.mkdir(parents=True, exist_ok=True)

            backup_path = backup_dir / f"{db_info['name']}.old"

            # 移动到备份目录
            shutil.move(str(source_path), str(backup_path))

            self.cleanup_stats['databases_cleaned'] += 1
            self.cleanup_stats['db_space_freed_mb'] += db_info['size_mb']

            print(f"   📦 备份过期数据库: {db_info['name']} ({db_info['size_mb']} MB)")

        except Exception as e:
            print(f"   ⚠️ 备份数据库失败 {db_info['path']}: {e}")

    def _vacuum_large_database(self, db_info: dict[str, Any]) -> Any:
        """清理过大的数据库"""
        try:
            source_path = Path(db_info['path'])

            # 连接数据库并执行VACUUM
            conn = sqlite3.connect(str(source_path))
            cursor = conn.cursor()

            # 获取清理前的大小
            original_size = source_path.stat().st_size

            # 执行清理
            cursor.execute('VACUUM')
            conn.close()

            # 计算节省的空间
            new_size = source_path.stat().st_size
            space_saved_mb = round((original_size - new_size) / (1024 * 1024), 2)

            if space_saved_mb > 1:  # 只报告节省超过1MB的清理
                self.cleanup_stats['db_space_freed_mb'] += space_saved_mb
                print(f"   🧹 清理数据库: {db_info['name']} (节省 {space_saved_mb} MB)")

        except Exception as e:
            print(f"   ⚠️ 清理数据库失败 {db_info['path']}: {e}")

    def _archive_log_files(self) -> Any:
        """归档和压缩日志文件"""
        print("   📋 扫描日志文件...")

        log_files = list(self.base_path.rglob('*.log')) + list(self.base_path.rglob('*.out'))
        cutoff_date = datetime.now() - timedelta(days=self.deep_cleanup_config['log_file_days'])

        for log_file in log_files:
            try:
                modified_time = datetime.fromtimestamp(log_file.stat().st_mtime)

                if modified_time < cutoff_date:
                    log_info = {
                        'path': str(log_file),
                        'name': log_file.name,
                        'size_mb': round(log_file.stat().st_size / (1024 * 1024), 2)
                    }

                    self._archive_single_log(log_info)
                    self.cleanup_stats['logs_archived'] += 1
                    self.cleanup_stats['log_space_freed_mb'] += log_info['size_mb']

            except Exception as e:
                print(f"   ⚠️ 归档日志失败 {log_file}: {e}")

    def _archive_single_log(self, log_info: dict[str, Any]) -> Any:
        """归档单个日志文件"""
        try:
            source_path = Path(log_info['path'])
            archive_dir = self.backup_path / datetime.now().strftime('%Y%m') / 'archived_logs'
            archive_dir.mkdir(parents=True, exist_ok=True)

            # 添加时间戳到文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archived_name = f"{source_path.stem}_{timestamp}{source_path.suffix}"
            archive_path = archive_dir / archived_name

            # 移动文件到归档目录
            shutil.move(str(source_path), str(archive_path))

            print(f"   📦 归档日志: {log_info['name']} ({log_info['size_mb']} MB)")

        except Exception as e:
            print(f"   ⚠️ 归档日志失败 {log_info['path']}: {e}")

    def _clear_cache_files(self) -> Any:
        """清理缓存文件"""
        print("   🗂️ 清理缓存文件...")

        cache_patterns = [
            '**/.cache/**',
            '**/cache/**',
            '**/__pycache__/**',
            '**/*.pyc',
            '**/*.pyo',
            '**/.pytest_cache/**'
        ]

        for pattern in cache_patterns:
            try:
                for item in self.base_path.glob(pattern):
                    if item.exists():
                        size_before = self._get_directory_size(item) if item.is_dir() else item.stat().st_size

                        if item.is_file():
                            item.unlink()
                            file_count = 1
                        elif item.is_dir():
                            file_count = len(list(item.rglob('*')))
                            shutil.rmtree(item)

                        size_mb = round(size_before / (1024 * 1024), 2)
                        self.cleanup_stats['caches_cleared'] += file_count
                        self.cleanup_stats['cache_space_freed_mb'] += size_mb

            except Exception as e:
                print(f"   ⚠️ 清理缓存失败 {pattern}: {e}")

    def _get_directory_size(self, directory: Path) -> int:
        """获取目录大小"""
        total_size = 0
        try:
            for item in directory.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
        except Exception as e:

            # 记录异常但不中断流程

            logger.debug(f"[deep_file_cleanup] Exception: {e}")
        return total_size

    def _clear_temp_files(self) -> Any:
        """清理临时文件"""
        print("   🧹 清理临时文件...")

        temp_patterns = [
            '**/*.tmp',
            '**/*.temp',
            '**/*.swp',
            '**/*.swo',
            '**/.DS_Store',
            '**/Thumbs.db',
            '**/.AppleDouble'
        ]

        cutoff_time = datetime.now() - timedelta(hours=self.deep_cleanup_config['temp_file_hours'])

        for pattern in temp_patterns:
            try:
                for item in self.base_path.glob(pattern):
                    if item.is_file():
                        modified_time = datetime.fromtimestamp(item.stat().st_mtime)

                        if modified_time < cutoff_time:
                            size_mb = round(item.stat().st_size / (1024 * 1024), 2)
                            item.unlink()

                            self.cleanup_stats['temp_files_removed'] += 1
                            self.cleanup_stats['temp_space_freed_mb'] += size_mb

            except Exception as e:
                print(f"   ⚠️ 清理临时文件失败 {pattern}: {e}")

    def _optimize_storage_structure(self) -> Any:
        """优化存储结构"""
        print("   ⚡ 优化存储结构...")

        # 创建合理的目录结构
        recommended_dirs = [
            'temp', 'cache', 'logs/current', 'logs/archived',
            'backup/daily', 'backup/weekly', 'backup/monthly'
        ]

        for dir_name in recommended_dirs:
            dir_path = self.base_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)

        # 优化已知的性能问题
        self._optimize_known_issues()

    def _optimize_known_issues(self) -> Any:
        """优化已知的性能问题"""
        # 移动临时文件到temp目录
        temp_dir = self.base_path / 'temp'

        # 检查是否有散落的临时文件
        for item in self.base_path.glob('*.tmp'):
            try:
                if item.is_file():
                    shutil.move(str(item), str(temp_dir / item.name))
            except Exception as e:

                # 记录异常但不中断流程

                logger.debug(f"[deep_file_cleanup] Exception: {e}")
    def _generate_deep_cleanup_report(self) -> Any:
        """生成深度清理报告"""
        self.cleanup_stats['total_space_freed_mb'] = (
            self.cleanup_stats['db_space_freed_mb'] +
            self.cleanup_stats['log_space_freed_mb'] +
            self.cleanup_stats['cache_space_freed_mb'] +
            self.cleanup_stats['temp_space_freed_mb']
        )

        report = {
            'deep_cleanup_timestamp': datetime.now().isoformat(),
            'cleanup_statistics': self.cleanup_stats,
            'cleanup_configuration': self.deep_cleanup_config,
            'optimization_effectiveness': {
                'total_space_saved_mb': round(self.cleanup_stats['total_space_freed_mb'], 2),
                'files_processed': (
                    self.cleanup_stats['databases_cleaned'] +
                    self.cleanup_stats['logs_archived'] +
                    self.cleanup_stats['caches_cleared'] +
                    self.cleanup_stats['temp_files_removed']
                ),
                'optimization_areas': [
                    'Large file analysis',
                    'Database cleanup',
                    'Log archiving',
                    'Cache clearing',
                    'Temp file removal',
                    'Storage structure optimization'
                ]
            }
        }

        # 保存报告
        report_path = self.logs_path / f"deep_cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        print(f"   📋 深度清理报告已保存: {report_path}")

    def _display_deep_summary(self) -> Any:
        """显示深度清理摘要"""
        print("\n" + "=" * 60)
        print("🔬 深度文件清理摘要")
        print("=" * 60)

        print("📊 大文件分析:")
        print(f"   - 发现大文件: {self.cleanup_stats['large_files_found']:,} 个")
        print(f"   - 大文件总大小: {self.cleanup_stats['large_files_size_mb']:,} MB")

        print("\n🗄️ 数据库清理:")
        print(f"   - 清理数据库: {self.cleanup_stats['databases_cleaned']:,} 个")
        print(f"   - 释放空间: {round(self.cleanup_stats['db_space_freed_mb'], 2):,} MB")

        print("\n📋 日志归档:")
        print(f"   - 归档日志: {self.cleanup_stats['logs_archived']:,} 个")
        print(f"   - 释放空间: {round(self.cleanup_stats['log_space_freed_mb'], 2):,} MB")

        print("\n🗂️ 缓存清理:")
        print(f"   - 清理缓存: {self.cleanup_stats['caches_cleared']:,} 项")
        print(f"   - 释放空间: {round(self.cleanup_stats['cache_space_freed_mb'], 2):,} MB")

        print("\n🧹 临时文件:")
        print(f"   - 删除临时文件: {self.cleanup_stats['temp_files_removed']:,} 个")
        print(f"   - 释放空间: {round(self.cleanup_stats['temp_space_freed_mb'], 2):,} MB")

        total_freed = round(self.cleanup_stats['total_space_freed_mb'], 2)
        print("\n🎯 总体效果:")
        print(f"   - 总释放空间: {total_freed:,} MB")
        print(f"   - 处理文件总数: {self.cleanup_stats['large_files_found'] + self.cleanup_stats['databases_cleaned'] + self.cleanup_stats['logs_archived'] + self.cleanup_stats['caches_cleared'] + self.cleanup_stats['temp_files_removed']:,}")

        if total_freed > 500:
            print(f"   ✨ 深度清理效果显著! 释放了 {total_freed} MB 空间")
        elif total_freed > 100:
            print(f"   ✅ 深度清理效果良好! 释放了 {total_freed} MB 空间")
        else:
            print(f"   ℹ️ 深度清理完成，释放了 {total_freed} MB 空间")

def main() -> None:
    """主函数"""
    print("🔬 深度文件清理系统")
    print("=" * 40)
    print("识别并处理过期、大文件和冗余数据")
    print("=" * 40)

    # 确认操作
    try:
        response = input("\n🤔 确认要执行深度文件清理吗? 这将处理大文件和数据库 (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("❌ 操作已取消")
            return
    except KeyboardInterrupt:
        print("\n❌ 操作已取消")
        return

    # 执行深度清理
    cleaner = DeepFileCleaner()
    cleaner.start_deep_cleanup()

if __name__ == "__main__":
    main()
