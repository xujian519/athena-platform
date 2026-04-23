#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能文件清理系统
基于优化后的存储系统，自动备份过期文件和删除冗余文件
"""

import os
import shutil
import json
import sys
import time
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Set
from collections import defaultdict

# 添加项目路径
sys.path.append('/Users/xujian/Athena工作平台')

class IntelligentFileCleaner:
    """智能文件清理器"""

    def __init__(self):
        self.base_path = Path("/Users/xujian/Athena工作平台")
        self.backup_path = Path("/Users/xujian/Athena工作平台/backup_files")
        self.logs_path = Path("/Users/xujian/Athena工作平台/logs")

        # 清理策略配置
        self.cleanup_config = {
            'days_for_backup': 30,      # 超过30天未访问的文件备份
            'days_for_delete': 90,      # 超过90天未访问的文件删除
            'max_backup_size_gb': 5,    # 备份文件夹最大5GB
            'file_types_to_backup': ['.log', '.tmp', '.cache', '.old', '.bak'],
            'file_types_to_delete': ['.tmp', '.cache', '.pyc', '.DS_Store'],
            'directories_to_scan': [
                'logs', 'temp', 'cache', 'data', 'core', 'services'
            ],
            'excluded_patterns': [
                '__pycache__', 'node_modules', '.git', '.env'
            ]
        }

        # 统计数据
        self.scan_stats = {
            'total_files': 0,
            'total_size_mb': 0,
            'files_backed_up': 0,
            'files_deleted': 0,
            'space_freed_mb': 0,
            'backup_size_mb': 0,
            'duplicate_files': 0,
            'processing_time': 0
        }

    def start_intelligent_cleanup(self) -> Any:
        """启动智能清理流程"""
        print("🧹 启动智能文件清理系统...")
        print(f"📅 清理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        start_time = time.time()

        try:
            # 1. 创建备份目录
            self._ensure_backup_directory()

            # 2. 扫描和分析文件
            print("🔍 第1步: 扫描和分析文件...")
            file_analysis = self._scan_and_analyze_files()

            # 3. 识别过期文件
            print("📋 第2步: 识别过期和冗余文件...")
            expired_files, duplicate_files = self._identify_cleanup_candidates(file_analysis)

            # 4. 备份过期文件
            print("💾 第3步: 备份过期文件...")
            self._backup_expired_files(expired_files)

            # 5. 删除冗余文件
            print("🗑️ 第4步: 删除冗余文件...")
            self._delete_redundant_files(duplicate_files)

            # 6. 清理临时文件
            print("🧹 第5步: 清理临时和缓存文件...")
            self._cleanup_temp_files()

            # 7. 验证清理效果
            print("✅ 第6步: 验证清理效果...")
            self._verify_cleanup_results()

            # 8. 生成清理报告
            self._generate_cleanup_report()

            self.scan_stats['processing_time'] = time.time() - start_time

            print("\n🎉 智能文件清理完成!")
            self._display_summary()

        except Exception as e:
            print(f"\n❌ 清理过程中出现错误: {e}")
            import traceback
            traceback.print_exc()

    def _ensure_backup_directory(self) -> Any:
        """确保备份目录存在"""
        self.backup_path.mkdir(exist_ok=True)

        # 按日期创建子目录
        date_dir = self.backup_path / datetime.now().strftime('%Y%m%d')
        date_dir.mkdir(exist_ok=True)

        print(f"✅ 备份目录已准备: {date_dir}")

    def _scan_and_analyze_files(self) -> Dict[str, Any]:
        """扫描和分析文件"""
        file_analysis = {
            'files_by_age': defaultdict(list),
            'files_by_type': defaultdict(list),
            'files_by_size': defaultdict(list),
            'file_hashes': {},
            'duplicates': []
        }

        print("   📁 扫描文件系统...")

        for directory in self.cleanup_config['directories_to_scan']:
            dir_path = self.base_path / directory
            if not dir_path.exists():
                continue

            print(f"   📂 扫描目录: {directory}")
            self._scan_directory(dir_path, file_analysis)

        self.scan_stats['total_files'] = len(file_analysis['file_hashes'])
        total_size = sum(info['size'] for info in file_analysis['file_hashes'].values())
        self.scan_stats['total_size_mb'] = round(total_size / (1024 * 1024), 2)

        print(f"   📊 扫描完成: {self.scan_stats['total_files']} 个文件, {self.scan_stats['total_size_mb']} MB")

        return file_analysis

    def _scan_directory(self, dir_path: Path, file_analysis: Dict[str, Any]) -> Any:
        """扫描单个目录"""
        try:
            for item in dir_path.rglob('*'):
                if item.is_file() and not self._should_exclude_file(item):
                    file_info = self._analyze_file(item)
                    if file_info:
                        self._categorize_file(file_info, file_analysis)
        except Exception as e:
            print(f"   ⚠️ 扫描目录失败 {dir_path}: {e}")

    def _should_exclude_file(self, file_path: Path) -> bool:
        """判断是否应该排除文件"""
        # 检查排除模式
        for pattern in self.cleanup_config['excluded_patterns']:
            if pattern in str(file_path):
                return True

        # 检查文件大小限制（跳过过大的文件）
        try:
            if file_path.stat().st_size > 100 * 1024 * 1024:  # 100MB
                return True
        except:
            return True

        return False

    def _analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """分析单个文件"""
        try:
            stat = file_path.stat()

            # 计算文件哈希（用于重复文件检测）
            file_hash = None
            if stat.st_size < 10 * 1024 * 1024:  # 只为小于10MB的文件计算哈希
                file_hash = self._calculate_file_hash(file_path)

            file_info = {
                'path': str(file_path),
                'name': file_path.name,
                'size': stat.st_size,
                'modified_time': datetime.fromtimestamp(stat.st_mtime),
                'access_time': datetime.fromtimestamp(stat.st_atime),
                'extension': file_path.suffix.lower(),
                'hash': file_hash
            }

            return file_info

        except Exception as e:
            print(f"   ⚠️ 分析文件失败 {file_path}: {e}")
            return None

    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希值"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except:
            return None

    def _categorize_file(self, file_info: Dict[str, Any], file_analysis: Dict[str, Any]) -> Any:
        """将文件分类"""
        # 按年龄分类
        days_old = (datetime.now() - file_info['access_time']).days
        if days_old < 7:
            file_analysis['files_by_age']['recent'].append(file_info)
        elif days_old < 30:
            file_analysis['files_by_age']['week_old'].append(file_info)
        elif days_old < 90:
            file_analysis['files_by_age']['month_old'].append(file_info)
        else:
            file_analysis['files_by_age']['old'].append(file_info)

        # 按类型分类
        file_analysis['files_by_type'][file_info['extension']].append(file_info)

        # 按大小分类
        size_kb = file_info['size'] / 1024
        if size_kb < 10:
            file_analysis['files_by_size']['small'].append(file_info)
        elif size_kb < 100:
            file_analysis['files_by_size']['medium'].append(file_info)
        elif size_kb < 1024:
            file_analysis['files_by_size']['large'].append(file_info)
        else:
            file_analysis['files_by_size']['huge'].append(file_info)

        # 检测重复文件
        if file_info['hash']:
            if file_info['hash'] in file_analysis['file_hashes']:
                file_analysis['duplicates'].append({
                    'original': file_analysis['file_hashes'][file_info['hash']],
                    'duplicate': file_info
                })
                self.scan_stats['duplicate_files'] += 1
            else:
                file_analysis['file_hashes'][file_info['hash']] = file_info

    def _identify_cleanup_candidates(self, file_analysis: Dict[str, Any]) -> Tuple[List[Dict], List[Dict]]:
        """识别需要清理的文件"""
        expired_files = []
        duplicate_files = file_analysis['duplicates']

        # 识别过期文件（超过30天未访问且属于备份类型）
        for file_info in file_analysis['files_by_age']['old']:
            if self._should_backup_file(file_info):
                expired_files.append(file_info)

        # 识别中等过期文件（30-90天，特定类型）
        for file_info in file_analysis['files_by_age']['month_old']:
            if self._should_delete_file(file_info):
                expired_files.append(file_info)

        print(f"   📋 识别过期文件: {len(expired_files)} 个")
        print(f"   📋 识别重复文件: {len(duplicate_files)} 组")

        return expired_files, duplicate_files

    def _should_backup_file(self, file_info: Dict[str, Any]) -> bool:
        """判断是否应该备份文件"""
        # 检查文件扩展名
        if file_info['extension'] in self.cleanup_config['file_types_to_backup']:
            return True

        # 检查文件名模式
        name_lower = file_info['name'].lower()
        if any(pattern in name_lower for pattern in ['old', 'backup', 'archive', 'log']):
            return True

        return False

    def _should_delete_file(self, file_info: Dict[str, Any]) -> bool:
        """判断是否应该删除文件"""
        # 检查文件扩展名
        if file_info['extension'] in self.cleanup_config['file_types_to_delete']:
            return True

        # 检查文件名模式
        name_lower = file_info['name'].lower()
        if any(pattern in name_lower for pattern in ['temp', 'tmp', 'cache']):
            return True

        return False

    def _backup_expired_files(self, expired_files: List[Dict]) -> Any:
        """备份过期文件"""
        if not expired_files:
            print("   ℹ️ 没有需要备份的过期文件")
            return

        backup_dir = self.backup_path / datetime.now().strftime('%Y%m%d') / 'expired_files'
        backup_dir.mkdir(parents=True, exist_ok=True)

        print(f"   💾 备份 {len(expired_files)} 个过期文件...")

        for file_info in expired_files:
            try:
                source_path = Path(file_info['path'])
                if source_path.exists():
                    # 创建相对路径的备份目录结构
                    relative_path = source_path.relative_to(self.base_path)
                    backup_file_path = backup_dir / relative_path
                    backup_file_path.parent.mkdir(parents=True, exist_ok=True)

                    # 复制文件
                    shutil.copy2(source_path, backup_file_path)
                    self.scan_stats['files_backed_up'] += 1
                    self.scan_stats['backup_size_mb'] += file_info['size'] / (1024 * 1024)

            except Exception as e:
                print(f"   ⚠️ 备份文件失败 {file_info['path']}: {e}")

        print(f"   ✅ 备份完成: {self.scan_stats['files_backed_up']} 个文件, {round(self.scan_stats['backup_size_mb'], 2)} MB")

    def _delete_redundant_files(self, duplicate_files: List[Dict]) -> Any:
        """删除冗余文件"""
        if not duplicate_files:
            print("   ℹ️ 没有发现重复文件")
            return

        print(f"   🗑️ 删除 {len(duplicate_files)} 个重复文件...")

        for duplicate_group in duplicate_files:
            try:
                original_file = Path(duplicate_group['original']['path'])
                duplicate_file = Path(duplicate_group['duplicate']['path'])

                # 保留修改时间较新的文件
                if original_file.exists() and duplicate_file.exists():
                    if duplicate_file.stat().st_mtime > original_file.stat().st_mtime:
                        # 删除较旧的文件
                        file_to_delete = original_file
                        keep_file = duplicate_file
                    else:
                        file_to_delete = duplicate_file
                        keep_file = original_file

                    # 删除重复文件
                    file_to_delete.unlink()
                    self.scan_stats['files_deleted'] += 1
                    self.scan_stats['space_freed_mb'] += duplicate_group['duplicate']['size'] / (1024 * 1024)

            except Exception as e:
                print(f"   ⚠️ 删除重复文件失败: {e}")

        print(f"   ✅ 重复文件删除完成: {self.scan_stats['files_deleted']} 个文件")

    def _cleanup_temp_files(self) -> Any:
        """清理临时和缓存文件"""
        print("   🧹 清理临时和缓存文件...")

        # 清理 Python 缓存文件
        for pattern in ['**/*.pyc', '**/__pycache__', '**/.pytest_cache']:
            for item in self.base_path.glob(pattern):
                try:
                    if item.is_file():
                        item.unlink()
                        self.scan_stats['files_deleted'] += 1
                    elif item.is_dir():
                        shutil.rmtree(item)
                except Exception as e:
                    print(f"   ⚠️ 清理 {item} 失败: {e}")

        # 清理 mac_os 系统文件
        for pattern in ['**/.DS_Store', '**/._*']:
            for item in self.base_path.glob(pattern):
                try:
                    if item.exists():
                        item.unlink()
                        self.scan_stats['files_deleted'] += 1
                except Exception as e:
                    print(f"   ⚠️ 清理系统文件 {item} 失败: {e}")

        print(f"   ✅ 临时文件清理完成")

    def _verify_cleanup_results(self) -> Any:
        """验证清理结果"""
        print("   ✅ 验证清理结果...")

        # 检查备份目录
        if self.backup_path.exists():
            backup_size = sum(f.stat().st_size for f in self.backup_path.rglob('*') if f.is_file())
            backup_size_mb = round(backup_size / (1024 * 1024), 2)
            print(f"   💾 备份文件总大小: {backup_size_mb} MB")

        # 检查当前项目大小
        current_size = sum(f.stat().st_size for f in self.base_path.rglob('*') if f.is_file())
        current_size_mb = round(current_size / (1024 * 1024), 2)
        space_freed = round(self.scan_stats['total_size_mb'] - current_size_mb, 2)

        print(f"   📊 项目当前大小: {current_size_mb} MB")
        print(f"   📉 释放空间: {space_freed} MB")

    def _generate_cleanup_report(self) -> Any:
        """生成清理报告"""
        report = {
            'cleanup_timestamp': datetime.now().isoformat(),
            'cleanup_statistics': self.scan_stats,
            'cleanup_configuration': self.cleanup_config,
            'backup_location': str(self.backup_path),
            'cleanup_effectiveness': {
                'files_processed': self.scan_stats['files_backed_up'] + self.scan_stats['files_deleted'],
                'space_freed_mb': round(self.scan_stats['space_freed_mb'], 2),
                'processing_efficiency': f"{self.scan_stats['total_files'] / max(self.scan_stats['processing_time'], 1):.1f} files/sec"
            }
        }

        # 保存报告
        report_path = self.logs_path / f"file_cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        print(f"   📋 清理报告已保存: {report_path}")

    def _display_summary(self) -> Any:
        """显示清理摘要"""
        print("\n" + "=" * 60)
        print("📊 智能文件清理摘要")
        print("=" * 60)

        print(f"📁 扫描统计:")
        print(f"   - 总文件数: {self.scan_stats['total_files']:,}")
        print(f"   - 总大小: {self.scan_stats['total_size_mb']:,} MB")

        print(f"\n💾 备份操作:")
        print(f"   - 备份文件数: {self.scan_stats['files_backed_up']:,}")
        print(f"   - 备份大小: {round(self.scan_stats['backup_size_mb'], 2):,} MB")
        print(f"   - 备份位置: {self.backup_path}")

        print(f"\n🗑️ 删除操作:")
        print(f"   - 删除文件数: {self.scan_stats['files_deleted']:,}")
        print(f"   - 释放空间: {round(self.scan_stats['space_freed_mb'], 2):,} MB")
        print(f"   - 重复文件: {self.scan_stats['duplicate_files']:,}")

        print(f"\n⏱️ 性能指标:")
        print(f"   - 处理时间: {round(self.scan_stats['processing_time'], 2)} 秒")
        print(f"   - 处理效率: {self.scan_stats['total_files'] / max(self.scan_stats['processing_time'], 1):.1f} 文件/秒")

        print(f"\n🎯 清理效果:")
        files_processed = self.scan_stats['files_backed_up'] + self.scan_stats['files_deleted']
        print(f"   - 处理文件总数: {files_processed:,}")
        print(f"   - 空间优化率: {round((self.scan_stats['space_freed_mb'] / max(self.scan_stats['total_size_mb'], 1)) * 100, 2)}%")

        if self.scan_stats['space_freed_mb'] > 100:
            print(f"   ✨ 清理效果显著! 释放了 {round(self.scan_stats['space_freed_mb'], 2)} MB 空间")
        elif self.scan_stats['space_freed_mb'] > 10:
            print(f"   ✅ 清理效果良好! 释放了 {round(self.scan_stats['space_freed_mb'], 2)} MB 空间")
        else:
            print(f"   ℹ️ 清理完成，释放了 {round(self.scan_stats['space_freed_mb'], 2)} MB 空间")

        print(f"\n💡 建议:")
        print(f"   - 定期执行清理: 建议每周运行一次")
        print(f"   - 监控备份大小: 当前备份 {round(self.scan_stats['backup_size_mb'], 2)} MB")
        print(f"   - 检查重复文件: 发现了 {self.scan_stats['duplicate_files']} 个重复文件")

def main() -> None:
    """主函数"""
    print("🧹 智能文件清理系统")
    print("=" * 40)
    print("基于优化存储系统的高效文件管理")
    print("自动备份过期文件，删除冗余文件")
    print("=" * 40)

    # 确认操作
    try:
        response = input("\n🤔 确认要执行文件清理吗? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("❌ 操作已取消")
            return
    except KeyboardInterrupt:
        print("\n❌ 操作已取消")
        return

    # 执行清理
    cleaner = IntelligentFileCleaner()
    cleaner.start_intelligent_cleanup()

if __name__ == "__main__":
    main()