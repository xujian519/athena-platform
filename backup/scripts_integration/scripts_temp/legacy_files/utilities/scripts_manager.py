#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scripts文件夹管理器
Athena Scripts Directory Manager

用于管理和监控scripts目录的工具
自动执行健康检查、统计分析和维护任务

使用方法:
python3 scripts_manager.py --scan
python3 scripts_manager.py --health-check
python3 scripts_manager.py --stats
python3 scripts_manager.py --cleanup

作者: Athena AI系统
创建时间: 2025-12-08
版本: 1.0.0
"""

import argparse
import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

class ScriptsManager:
    """Scripts文件夹管理器"""

    def __init__(self, scripts_dir: str = '/Users/xujian/Athena工作平台/scripts'):
        self.scripts_dir = Path(scripts_dir)
        self.stats_file = self.scripts_dir / 'scripts_stats.json'
        self.health_report_file = self.scripts_dir / 'health_report.json'

    def scan_scripts(self) -> Dict[str, Any]:
        """扫描所有脚本并统计"""
        logger.info('🔍 扫描scripts目录...')

        stats = {
            'scan_date': datetime.now().isoformat(),
            'total_files': 0,
            'python_files': 0,
            'shell_files': 0,
            'other_files': 0,
            'categories': {},
            'large_files': [],
            'empty_files': [],
            'recent_files': [],
            'total_size': 0
        }

        # 扫描文件
        for file_path in self.scripts_dir.rglob('*'):
            if file_path.is_file() and not file_path.name.startswith('.'):
                stats['total_files'] += 1
                file_size = file_path.stat().st_size
                stats['total_size'] += file_size

                if file_path.suffix == '.py':
                    stats['python_files'] += 1
                elif file_path.suffix == '.sh':
                    stats['shell_files'] += 1
                else:
                    stats['other_files'] += 1

                # 统计分类
                category = file_path.parent.name
                if category not in stats['categories']:
                    stats['categories'][category] = {'count': 0, 'size': 0}
                stats['categories'][category]['count'] += 1
                stats['categories'][category]['size'] += file_size

                # 记录大文件 (>50KB)
                if file_size > 50 * 1024:
                    stats['large_files'].append({
                        'file': str(file_path.relative_to(self.scripts_dir)),
                        'size': file_size,
                        'size_kb': round(file_size / 1024, 2)
                    })

                # 记录空文件
                if file_size == 0:
                    stats['empty_files'].append(str(file_path.relative_to(self.scripts_dir)))

                # 记录最近修改的文件(7天内)
                days_since_modified = (datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)).days
                if days_since_modified <= 7:
                    stats['recent_files'].append({
                        'file': str(file_path.relative_to(self.scripts_dir)),
                        'days_ago': days_since_modified
                    })

        # 转换大小为KB
        stats['total_size_kb'] = round(stats['total_size'] / 1024, 2)

        # 保存统计信息
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        # 打印统计结果
        self._print_stats(stats)
        return stats

    def _print_stats(self, stats: Dict[str, Any]):
        """打印统计结果"""
        logger.info(f"\n📊 Scripts目录统计报告")
        logger.info(f"📅 扫描时间: {stats['scan_date']}")
        logger.info(f"📁 总文件数: {stats['total_files']}")
        logger.info(f"🐍 Python脚本: {stats['python_files']}")
        logger.info(f"🐚 Shell脚本: {stats['shell_files']}")
        logger.info(f"📄 其他文件: {stats['other_files']}")
        logger.info(f"💾 总大小: {stats['total_size_kb']} KB")

        logger.info(f"\n📂 分类统计:")
        for category, info in sorted(stats['categories'].items()):
            logger.info(f"  {category}: {info['count']} 个文件, {round(info['size']/1024, 2)} KB")

        if stats['large_files']:
            logger.info(f"\n⚠️ 大文件 (>50KB): {len(stats['large_files'])} 个")
            for file_info in stats['large_files'][:5]:  # 只显示前5个
                logger.info(f"  - {file_info['file']} ({file_info['size_kb']} KB)")

        if stats['empty_files']:
            logger.info(f"\n🗑️ 空文件: {len(stats['empty_files'])} 个")
            for file_path in stats['empty_files']:
                logger.info(f"  - {file_path}")

        if stats['recent_files']:
            logger.info(f"\n🕐 最近修改文件 (7天内): {len(stats['recent_files'])} 个")
            for file_info in stats['recent_files']:
                logger.info(f"  - {file_info['file']} ({file_info['days_ago']} 天前)")

    def health_check(self) -> List[str]:
        """执行健康检查"""
        logger.info("\n🏥 执行脚本健康检查...")

        issues = []
        warnings = []

        # 检查Python语法
        logger.info('  检查Python语法...')
        for py_file in self.scripts_dir.rglob('*.py'):
            if py_file.stat().st_size == 0:  # 跳过空文件
                continue
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    compile(f.read(), str(py_file), 'exec')
            except SyntaxError as e:
                issues.append(f"❌ Python语法错误 {py_file.relative_to(self.scripts_dir)}: {e}")
            except UnicodeDecodeError:
                warnings.append(f"⚠️ 文件编码问题 {py_file.relative_to(self.scripts_dir)}")

        # 检查Shell脚本权限
        logger.info('  检查Shell脚本权限...')
        for sh_file in self.scripts_dir.rglob('*.sh'):
            if not os.access(sh_file, os.X_OK):
                issues.append(f"❌ 缺少执行权限 {sh_file.relative_to(self.scripts_dir)}")
                # 尝试修复权限
                try:
                    os.chmod(sh_file, 0o755)
                    logger.info(f"  ✅ 已修复权限: {sh_file.relative_to(self.scripts_dir)}")
                except:
                    pass

        # 检查孤儿文件（没有在正确分类中的文件）
        logger.info('  检查文件分类...')
        valid_categories = {
            'import_export', 'services', 'legal_intelligence',
            'system_operations', 'utils', 'experimental', 'legacy'
        }

        for file_path in self.scripts_dir.rglob('*.py'):
            category = file_path.parent.name
            if category not in valid_categories:
                warnings.append(f"⚠️ 文件分类异常 {file_path.relative_to(self.scripts_dir)} (分类: {category})")

        # 保存健康报告
        health_report = {
            'check_date': datetime.now().isoformat(),
            'issues': issues,
            'warnings': warnings,
            'total_checked': len(list(self.scripts_dir.rglob('*.py'))) + len(list(self.scripts_dir.rglob('*.sh'))),
            'issues_count': len(issues),
            'warnings_count': len(warnings)
        }

        with open(self.health_report_file, 'w', encoding='utf-8') as f:
            json.dump(health_report, f, indent=2, ensure_ascii=False)

        # 打印结果
        if issues:
            logger.info(f"\n❌ 发现 {len(issues)} 个问题:")
            for issue in issues:
                logger.info(f"  {issue}")

        if warnings:
            logger.info(f"\n⚠️ 发现 {len(warnings)} 个警告:")
            for warning in warnings:
                logger.info(f"  {warning}")

        if not issues and not warnings:
            logger.info("\n✅ 所有检查通过，scripts目录健康状态良好！")

        return issues + warnings

    def cleanup_empty_files(self) -> int:
        """清理空文件"""
        logger.info("\n🧹 清理空文件...")

        cleaned_count = 0
        for file_path in self.scripts_dir.rglob('*'):
            if file_path.is_file() and file_path.stat().st_size == 0:
                logger.info(f"  删除空文件: {file_path.relative_to(self.scripts_dir)}")
                file_path.unlink()
                cleaned_count += 1

        logger.info(f"✅ 已清理 {cleaned_count} 个空文件")
        return cleaned_count

    def generate_report(self) -> str:
        """生成综合报告"""
        logger.info("\n📋 生成综合报告...")

        # 扫描和健康检查
        stats = self.scan_scripts()
        issues = self.health_check()

        # 生成报告
        report = f"""
# Scripts目录综合报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 基本统计

- **总文件数**: {stats['total_files']}
- **Python脚本**: {stats['python_files']}
- **Shell脚本**: {stats['shell_files']}
- **总大小**: {stats['total_size_kb']} KB

## 🏂 健康状态

- **检查文件数**: {len(list(self.scripts_dir.rglob('*.py'))) + len(list(self.scripts_dir.rglob('*.sh')))}
- **发现问题**: {len(issues)}
- **状态**: {'✅ 健康' if not issues else '⚠️ 需要关注'}

## 📈 建议

{self._generate_suggestions(stats, issues)}

---
报告生成工具: ScriptsManager v1.0.0
"""

        report_file = self.scripts_dir / 'weekly_report.md'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"✅ 报告已生成: {report_file}")
        return str(report_file)

    def _generate_suggestions(self, stats: Dict[str, Any], issues: List[str]) -> str:
        """生成优化建议"""
        suggestions = []

        if stats['empty_files']:
            suggestions.append(f"- 清理 {stats['empty_files']} 个空文件")

        if stats['large_files']:
            suggestions.append(f"- 检查 {len(stats['large_files'])} 个大文件是否可以优化")

        if issues:
            suggestions.append(f"- 修复 {len(issues)} 个发现的问题")

        if not suggestions:
            suggestions.append('- Scripts目录状态良好，继续保持')

        return '\n'.join(suggestions)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Scripts文件夹管理器')
    parser.add_argument('--scan', action='store_true', help='扫描并统计scripts目录')
    parser.add_argument('--health-check', action='store_true', help='执行健康检查')
    parser.add_argument('--stats', action='store_true', help='显示统计信息')
    parser.add_argument('--cleanup', action='store_true', help='清理空文件')
    parser.add_argument('--report', action='store_true', help='生成综合报告')
    parser.add_argument('--all', action='store_true', help='执行所有检查')

    args = parser.parse_args()

    manager = ScriptsManager()

    if args.all or not any(vars(args).values()):
        # 默认执行所有检查
        manager.scan_scripts()
        manager.health_check()
        manager.generate_report()
    else:
        if args.scan or args.stats:
            manager.scan_scripts()
        if args.health_check:
            manager.health_check()
        if args.cleanup:
            manager.cleanup_empty_files()
        if args.report:
            manager.generate_report()

if __name__ == '__main__':
    main()