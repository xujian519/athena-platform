#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能项目清理工具
Smart Project Cleaner

安全地扫描和清理项目中的冗余文件、无用文件和过期文件

作者: Athena AI系统
创建时间: 2025-12-08
版本: 1.0.0
"""

import hashlib
import json
import logging
import os
import shutil
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('documentation/logs/project_cleaning.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class FileInfo:
    """文件信息"""
    path: str
    size: int
    modified_time: datetime
    created_time: datetime
    file_hash: str
    extension: str
    is_duplicate: bool = False
    duplicate_of: str | None = None
    usage_score: float = 0.0
    deletion_risk: str = 'low'  # low, medium, high

class SmartProjectCleaner:
    """智能项目清理器"""

    def __init__(self, project_path: str = None):
        self.project_path = project_path or '/Users/xujian/Athena工作平台'
        self.backup_dir = os.path.join(self.project_path, '.backup', f"cleanup_{int(time.time())}")
        self.file_registry: Dict[str, FileInfo] = {}
        self.duplicate_groups: List[List[str]] = []
        self.cleanup_candidates: List[FileInfo] = []

        # 安全设置
        self.safe_extensions = {'.py', '.js', '.html', '.css', '.md', '.txt', '.json', '.yml', '.yaml', '.sh'}
        self.important_dirs = {'.git', 'node_modules', 'venv', '.venv', '__pycache__', '.idea', '.vscode'}
        self.max_file_age_days = 365  # 1年以上的文件可能过期
        self.duplicate_threshold = 100 * 1024  # 100KB以上的文件才检查重复

        # 统计信息
        self.stats = {
            'total_files_scanned': 0,
            'duplicates_found': 0,
            'unused_files': 0,
            'expired_files': 0,
            'space_freed': 0,
            'files_deleted': 0
        }

        logger.info(f"🧹 初始化智能项目清理器")
        logger.info(f"项目路径: {self.project_path}")
        logger.info(f"备份目录: {self.backup_dir}")

    async def scan_project(self) -> Dict[str, any]:
        """扫描项目并识别冗余文件"""
        logger.info('🔍 开始扫描项目文件...')
        logger.info(str('=' * 60))
        logger.info('🔍 智能项目扫描分析')
        logger.info(str('=' * 60))

        try:
            # 第一步：创建备份目录
            await self._create_backup_directory()

            # 第二步：扫描所有文件
            await self._scan_all_files()

            # 第三步：查找重复文件
            await self._find_duplicates()

            # 第四步：识别无用文件
            await self._identify_unused_files()

            # 第五步：识别过期文件
            await self._identify_expired_files()

            # 第六步：评估删除风险
            await self._assess_deletion_risk()

            # 生成扫描报告
            report = await self._generate_scan_report()

            logger.info('✅ 项目扫描完成')
            return report

        except Exception as e:
            logger.error(f"❌ 扫描过程中出错: {str(e)}")
            raise

    async def _create_backup_directory(self):
        """创建备份目录"""
        os.makedirs(self.backup_dir, exist_ok=True)
        logger.info(f"📁 创建备份目录: {self.backup_dir}")

    async def _scan_all_files(self):
        """扫描所有文件"""
        logger.info('📁 扫描项目文件结构...')

        scanned_count = 0
        for root, dirs, files in os.walk(self.project_path):
            # 跳过重要的系统目录
            dirs[:] = [d for d in dirs if d not in self.important_dirs]

            # 跳过备份目录
            if '.backup' in root:
                continue

            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_info = await self._analyze_file(file_path)
                    if file_info:
                        self.file_registry[file_path] = file_info
                        scanned_count += 1

                        if scanned_count % 100 == 0:
                            logger.info(f"   已扫描 {scanned_count} 个文件...")

                except Exception as e:
                    logger.warning(f"⚠️ 无法分析文件 {file_path}: {str(e)}")

        self.stats['total_files_scanned'] = scanned_count
        logger.info(f"✅ 扫描完成，共分析 {scanned_count} 个文件")

    async def _analyze_file(self, file_path: str) -> FileInfo | None:
        """分析单个文件"""
        try:
            stat_info = os.stat(file_path)

            # 跳过太大的文件（可能是重要的数据文件）
            if stat_info.st_size > 100 * 1024 * 1024:  # 100MB
                return None

            file_info = FileInfo(
                path=file_path,
                size=stat_info.st_size,
                modified_time=datetime.fromtimestamp(stat_info.st_mtime),
                created_time=datetime.fromtimestamp(stat_info.st_ctime),
                file_hash=await self._calculate_file_hash(file_path),
                extension=os.path.splitext(file_path)[1].lower()
            )

            return file_info

        except Exception as e:
            logger.warning(f"⚠️ 分析文件失败 {file_path}: {str(e)}")
            return None

    async def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希值"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ''

    async def _find_duplicates(self):
        """查找重复文件"""
        logger.info('🔍 查找重复文件...')

        # 按哈希值分组
        hash_groups: Dict[str, List[str]] = {}
        for file_path, file_info in self.file_registry.items():
            if file_info.file_hash and file_info.size > self.duplicate_threshold:
                if file_info.file_hash not in hash_groups:
                    hash_groups[file_info.file_hash] = []
                hash_groups[file_info.file_hash].append(file_path)

        # 找出重复的文件组
        duplicate_count = 0
        for file_hash, file_list in hash_groups.items():
            if len(file_list) > 1:
                self.duplicate_groups.append(file_list)
                duplicate_count += len(file_list) - 1

                # 标记重复文件
                sorted_files = sorted(file_list, key=lambda x: self.file_registry[x].modified_time, reverse=True)
                original_file = sorted_files[0]
                duplicate_files = sorted_files[1:]

                for duplicate_file in duplicate_files:
                    self.file_registry[duplicate_file].is_duplicate = True
                    self.file_registry[duplicate_file].duplicate_of = original_file

        self.stats['duplicates_found'] = duplicate_count
        logger.info(f"🔄 找到 {duplicate_count} 个重复文件，分为 {len(self.duplicate_groups)} 个重复组")

    async def _identify_unused_files(self):
        """识别无用文件"""
        logger.info('🗑️ 识别无用文件...')

        unused_count = 0

        for file_path, file_info in self.file_registry.items():
            if file_info.is_duplicate:
                continue

            unused_score = await self._calculate_usage_score(file_info)
            file_info.usage_score = unused_score

            # 使用评分低于阈值的文件被认为是无用的
            if unused_score < 0.3:
                self.cleanup_candidates.append(file_info)
                unused_count += 1

        self.stats['unused_files'] = unused_count
        logger.info(f"🗑️ 识别出 {unused_count} 个潜在无用文件")

    async def _calculate_usage_score(self, file_info: FileInfo) -> float:
        """计算文件使用评分"""
        score = 0.5  # 基础分数

        # 文件大小评分（小文件更可能是临时文件）
        if file_info.size < 1024:  # < 1KB
            score -= 0.2
        elif file_info.size > 1024 * 1024:  # > 1MB
            score += 0.2

        # 修改时间评分（很久没修改的文件可能不再使用）
        days_since_modified = (datetime.now() - file_info.modified_time).days
        if days_since_modified > 180:  # 6个月
            score -= 0.3
        elif days_since_modified < 7:  # 7天内
            score += 0.2

        # 文件扩展名评分
        if file_info.extension in {'.tmp', '.log', '.bak', '.cache'}:
            score -= 0.4
        elif file_info.extension in self.safe_extensions:
            score += 0.1

        # 路径评分
        if any(keyword in file_info.path.lower() for keyword in ['temp', 'cache', 'backup', 'test']):
            score -= 0.3
        elif any(keyword in file_info.path.lower() for keyword in ['src', 'core', 'main', 'app']):
            score += 0.2

        return max(0.0, min(1.0, score))

    async def _identify_expired_files(self):
        """识别过期文件"""
        logger.info('📅 识别过期文件...')

        expired_count = 0
        cutoff_date = datetime.now() - timedelta(days=self.max_file_age_days)

        for file_path, file_info in self.file_registry.items():
            if file_info.is_duplicate:
                continue

            if (file_info.modified_time < cutoff_date and
                file_info.extension in {'.log', '.tmp', '.cache', '.bak'}):
                if file_info not in self.cleanup_candidates:
                    self.cleanup_candidates.append(file_info)
                    expired_count += 1

        self.stats['expired_files'] = expired_count
        logger.info(f"📅 识别出 {expired_count} 个过期文件")

    async def _assess_deletion_risk(self):
        """评估删除风险"""
        logger.info('⚠️ 评估删除风险...')

        for file_info in self.cleanup_candidates:
            risk_score = 0.0

            # 重要文件路径检查
            if any(keyword in file_info.path.lower() for keyword in ['readme', 'license', 'config', 'init', 'main']):
                risk_score += 0.6

            # 重要扩展名检查
            if file_info.extension in {'.py', '.js', '.sh', '.yml', '.yaml'}:
                risk_score += 0.4

            # 文件大小检查（大文件删除风险高）
            if file_info.size > 1024 * 1024:  # > 1MB
                risk_score += 0.3

            # 使用评分检查（经常使用的文件删除风险高）
            if file_info.usage_score > 0.7:
                risk_score += 0.3

            # 设置风险等级
            if risk_score > 0.7:
                file_info.deletion_risk = 'high'
            elif risk_score > 0.4:
                file_info.deletion_risk = 'medium'
            else:
                file_info.deletion_risk = 'low'

    async def _generate_scan_report(self) -> Dict[str, any]:
        """生成扫描报告"""
        logger.info('📊 生成扫描报告...')

        # 统计信息
        total_candidates = len(self.cleanup_candidates)
        high_risk_files = [f for f in self.cleanup_candidates if f.deletion_risk == 'high']
        medium_risk_files = [f for f in self.cleanup_candidates if f.deletion_risk == 'medium']
        low_risk_files = [f for f in self.cleanup_candidates if f.deletion_risk == 'low']

        # 计算可释放空间
        total_space = sum(f.size for f in self.cleanup_candidates)
        safe_space = sum(f.size for f in low_risk_files)

        report = {
            'scan_summary': {
                'total_files_scanned': self.stats['total_files_scanned'],
                'cleanup_candidates': total_candidates,
                'duplicates_found': self.stats['duplicates_found'],
                'unused_files': self.stats['unused_files'],
                'expired_files': self.stats['expired_files'],
                'total_space_releasable': total_space,
                'safe_space_releasable': safe_space
            },
            'risk_analysis': {
                'high_risk_files': len(high_risk_files),
                'medium_risk_files': len(medium_risk_files),
                'low_risk_files': len(low_risk_files)
            },
            'duplicate_groups': len(self.duplicate_groups),
            'backup_directory': self.backup_dir,
            'recommendations': self._generate_recommendations()
        }

        # 保存详细报告
        await self._save_detailed_report(report)

        return report

    def _generate_recommendations(self) -> List[str]:
        """生成清理建议"""
        recommendations = []

        if self.stats['duplicates_found'] > 0:
            recommendations.append(f"建议删除 {self.stats['duplicates_found']} 个重复文件")

        if self.stats['expired_files'] > 0:
            recommendations.append(f"建议清理 {self.stats['expired_files']} 个过期文件")

        if self.stats['unused_files'] > 0:
            recommendations.append(f"谨慎处理 {self.stats['unused_files']} 个潜在无用文件")

        recommendations.append('建议先备份，再执行删除操作')
        recommendations.append('建议分批处理，避免一次性删除过多文件')

        return recommendations

    async def _save_detailed_report(self, report: Dict[str, any]):
        """保存详细报告"""
        report_file = os.path.join(self.backup_dir, 'cleanup_report.json')

        detailed_report = {
            'timestamp': datetime.now().isoformat(),
            'summary': report,
            'cleanup_candidates': [
                {
                    'path': f.path,
                    'size': f.size,
                    'modified_time': f.modified_time.isoformat(),
                    'risk_level': f.deletion_risk,
                    'usage_score': f.usage_score,
                    'is_duplicate': f.is_duplicate,
                    'duplicate_of': f.duplicate_of
                }
                for f in self.cleanup_candidates
            ],
            'duplicate_groups': self.duplicate_groups
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(detailed_report, f, indent=2, ensure_ascii=False)

        logger.info(f"📄 详细报告已保存到: {report_file}")

    async def safe_cleanup(self, delete_high_risk: bool = False, delete_medium_risk: bool = False) -> Dict[str, any]:
        """安全清理文件"""
        logger.info('🧹 开始安全清理...')
        logger.info(str('=' * 60))
        logger.info('🧹 执行安全清理操作')
        logger.info(str('=' * 60))

        # 筛选要删除的文件
        files_to_delete = []

        # 低风险文件（默认删除）
        low_risk_files = [f for f in self.cleanup_candidates if f.deletion_risk == 'low']
        files_to_delete.extend(low_risk_files)

        # 中等风险文件（可选）
        if delete_medium_risk:
            medium_risk_files = [f for f in self.cleanup_candidates if f.deletion_risk == 'medium']
            files_to_delete.extend(medium_risk_files)

        # 高风险文件（需要明确确认）
        if delete_high_risk:
            high_risk_files = [f for f in self.cleanup_candidates if f.deletion_risk == 'high']
            files_to_delete.extend(high_risk_files)

        logger.info(f"📋 准备删除 {len(files_to_delete)} 个文件")

        # 执行清理
        deleted_files = []
        failed_files = []
        space_freed = 0

        for file_info in files_to_delete:
            try:
                # 先移动到备份目录
                backup_path = os.path.join(self.backup_dir, 'deleted_files', os.path.basename(file_info.path))
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)

                shutil.move(file_info.path, backup_path)

                deleted_files.append({
                    'original_path': file_info.path,
                    'backup_path': backup_path,
                    'size': file_info.size,
                    'risk_level': file_info.deletion_risk
                })

                space_freed += file_info.size
                self.stats['files_deleted'] += 1

                logger.info(f"   ✅ 已删除: {file_info.path}")

            except Exception as e:
                logger.error(f"❌ 删除文件失败 {file_info.path}: {str(e)}")
                failed_files.append({'path': file_info.path, 'error': str(e)})

        self.stats['space_freed'] = space_freed

        # 保存删除记录
        await self._save_deletion_record(deleted_files, failed_files)

        logger.info(f"\n🎉 清理完成！")
        logger.info(f"   ✅ 成功删除: {len(deleted_files)} 个文件")
        logger.info(f"   ❌ 删除失败: {len(failed_files)} 个文件")
        logger.info(f"   💾 释放空间: {self._format_size(space_freed)}")
        logger.info(f"   📁 备份位置: {self.backup_dir}")

        return {
            'deleted_count': len(deleted_files),
            'failed_count': len(failed_files),
            'space_freed': space_freed,
            'backup_directory': self.backup_dir,
            'deleted_files': deleted_files,
            'failed_files': failed_files
        }

    async def _save_deletion_record(self, deleted_files: List[Dict], failed_files: List[Dict]):
        """保存删除记录"""
        record_file = os.path.join(self.backup_dir, 'deletion_record.json')

        record = {
            'timestamp': datetime.now().isoformat(),
            'deleted_files': deleted_files,
            'failed_files': failed_files,
            'statistics': self.stats
        }

        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump(record, f, indent=2, ensure_ascii=False)

        logger.info(f"📄 删除记录已保存到: {record_file}")

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    async def restore_from_backup(self):
        """从备份恢复文件"""
        backup_files_dir = os.path.join(self.backup_dir, 'deleted_files')
        if not os.path.exists(backup_files_dir):
            logger.info('❌ 没有找到备份文件')
            return

        logger.info(f"🔄 从备份恢复文件...")
        restored_count = 0

        for root, dirs, files in os.walk(backup_files_dir):
            for file in files:
                backup_path = os.path.join(root, file)
                # 这里需要根据实际的备份结构来恢复文件
                # 简化实现，实际需要更复杂的路径映射
                try:
                    # 示例恢复逻辑（需要根据实际情况调整）
                    original_path = backup_path.replace(f"{self.backup_dir}/deleted_files/', '")
                    os.makedirs(os.path.dirname(original_path), exist_ok=True)
                    shutil.move(backup_path, original_path)
                    restored_count += 1
                    logger.info(f"   ✅ 已恢复: {original_path}")
                except Exception as e:
                    logger.info(f"   ❌ 恢复失败: {file} - {str(e)}")

        logger.info(f"🎉 恢复完成，共恢复 {restored_count} 个文件")


# 主函数
async def main():
    """主函数"""
    logger.info('🧠 Athena智能项目清理系统')
    logger.info('基于超级思维链的安全文件清理工具')
    logger.info(str('=' * 60))

    # 创建清理器
    cleaner = SmartProjectCleaner()

    try:
        # 第一步：扫描项目
        scan_report = await cleaner.scan_project()

        logger.info("\n📊 扫描摘要:")
        logger.info(f"   📁 总文件数: {scan_report['scan_summary']['total_files_scanned']}")
        logger.info(f"   🗑️ 清理候选: {scan_report['scan_summary']['cleanup_candidates']} 个文件")
        logger.info(f"   🔄 重复文件: {scan_report['scan_summary']['duplicates_found']} 个")
        logger.info(f"   💾 可释放空间: {cleaner._format_size(scan_report['scan_summary']['total_space_releasable'])}")
        logger.info(f"   ⚠️ 高风险文件: {scan_report['risk_analysis']['high_risk_files']} 个")

        logger.info("\n💡 建议:")
        for i, rec in enumerate(scan_report['recommendations'], 1):
            logger.info(f"   {i}. {rec}")

        # 询问用户是否继续
        logger.info(str("\n" + '=' * 60))
        response = input('🤔 是否继续执行清理操作？(y/N): ').lower().strip()

        if response == 'y':
            # 第二步：安全清理
            logger.info("\n⚠️ 安全清理选项:")
            delete_medium = input('   删除中等风险文件吗？(y/N): ').lower().strip() == 'y'
            delete_high = input('   删除高风险文件吗？(需要谨慎确认) (y/N): ').lower().strip() == 'y'

            cleanup_result = await cleaner.safe_cleanup(delete_medium_risk=delete_medium, delete_high_risk=delete_high)

            logger.info(f"\n📋 清理结果:")
            logger.info(f"   ✅ 成功删除: {cleanup_result['deleted_count']} 个文件")
            logger.info(f"   ❌ 删除失败: {cleanup_result['failed_count']} 个文件")
            logger.info(f"   💾 释放空间: {cleaner._format_size(cleanup_result['space_freed'])}")

        else:
            logger.info("\n❌ 用户取消清理操作")
            logger.info('💡 扫描报告已保存，您可以稍后手动清理')

    except Exception as e:
        logger.info(f"\n❌ 清理过程中出现错误: {str(e)}")
        logger.error(f"清理失败: {str(e)}")


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())