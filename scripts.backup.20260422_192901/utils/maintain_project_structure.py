#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目结构维护脚本
Project Structure Maintenance Script

定期检查和维护项目目录结构，保持根目录整洁
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

class ProjectStructureMaintainer:
    """项目结构维护器"""

    def __init__(self):
        self.root_path = Path('/Users/xujian/Athena工作平台')

        # 期望的根目录文件（这些文件应该保留在根目录）
        self.expected_root_files = {
            'README.md', 'LICENSE', '.gitignore', 'requirements.txt',
            '.env.example', 'setup.py', 'pyproject.toml', 'Dockerfile',
            'docker-compose.yml', '.env.production'
        }

        # 文件分类规则
        self.file_patterns = {
            'docs': {
                'patterns': ['*.md', '*.txt', '*.rst'],
                'target_dir': 'docs',
                'exceptions': ['README.md', 'LICENSE']  # 这些文件保留在根目录
            },
            'reports': {
                'patterns': ['*_REPORT.md', '*_REPORT.json', '*_SUMMARY.md', '*_ANALYSIS.md'],
                'target_dir': 'reports',
                'description': '各类分析报告'
            },
            'data': {
                'patterns': ['*.json', '*.csv', '*.xml', '*.data', '*.db', '*.sqlite'],
                'target_dir': 'data',
                'exceptions': ['requirements.txt']
            },
            'config': {
                'patterns': ['.env*', '*.config', '*.conf', '*.ini', '*.yml', '*.yaml'],
                'target_dir': 'config',
                'exceptions': ['.env.production', 'docker-compose.yml']
            },
            'binaries': {
                'patterns': ['*', '.*'],
                'target_dir': 'binaries',
                'condition': lambda f: f.is_file() and os.access(f, os.X_OK)  # 可执行文件
            },
            'temp': {
                'patterns': ['*.tmp', '*.temp', '*.bak', '*~', '*.swp', '*.log'],
                'target_dir': 'temp',
                'description': '临时文件和日志'
            }
        }

    def scan_root_directory(self) -> Any:
        """扫描根目录，识别散落文件"""
        logger.info('🔍 扫描根目录...')

        all_items = list(self.root_path.iterdir())
        scattered_files = []
        expected_found = set()
        directories = []

        for item in all_items:
            if item.name.startswith('.'):  # 跳过隐藏文件和目录
                continue

            if item.is_file():
                if item.name in self.expected_root_files:
                    expected_found.add(item.name)
                else:
                    scattered_files.append(item)
            elif item.is_dir() and item.name not in [
                'api', 'apps', 'backup', 'binaries', 'cleanup', 'config', 'data',
                'deploy', 'deployment', 'deployments', 'docs', 'frontend', 'infrastructure',
                'logs', 'models', 'monitoring', 'nginx', 'patent-platform/agent', 'patent-platform/workspace',
                'projects', 'scripts', 'services', 'src', 'storage', 'tasks', 'tests', 'tools'
            ]:
                directories.append(item)

        logger.info(f"📄 发现 {len(scattered_files)} 个散落文件")
        logger.info(f"📁 发现 {len(directories)} 个可能需要整理的目录")
        logger.info(f"✅ 找到 {len(expected_found)} 个预期的根目录文件")

        return scattered_files, directories, expected_found

    def categorize_file(self, file_path) -> Any:
        """对文件进行分类"""
        file_name = file_path.name.lower()

        # 检查是否为预期的根目录文件
        if file_path.name in self.expected_root_files:
            return 'keep_in_root', '保留在根目录'

        # 检查各种分类规则
        for category, rules in self.file_patterns.items():
            # 检查例外
            if 'exceptions' in rules and file_path.name in rules['exceptions']:
                continue

            # 检查条件（如可执行文件）
            if 'condition' in rules:
                if rules['condition'](file_path):
                    return category, rules.get('description', category)
                continue

            # 检查模式匹配
            for pattern in rules['patterns']:
                if self._match_pattern(file_name, pattern):
                    return category, rules.get('description', category)

        return 'misc', '其他文件'

    def _match_pattern(self, filename, pattern) -> Any:
        """简单的模式匹配"""
        if pattern.startswith('*') and filename.endswith(pattern[1:]):
            return True
        elif pattern.endswith('*') and filename.startswith(pattern[:-1]):
            return True
        elif '*' in pattern:
            # 简单的通配符匹配
            parts = pattern.split('*')
            if len(parts) == 2:
                return filename.startswith(parts[0]) and filename.endswith(parts[1])
        elif filename == pattern:
            return True
        return False

    def suggest_cleanup_actions(self, scattered_files, directories) -> Any:
        """建议清理操作"""
        logger.info('💡 分析清理建议...')

        suggestions = {
            'move_files': [],
            'review_directories': [],
            'delete_candidates': []
        }

        # 分析文件
        for file_path in scattered_files:
            category, description = self.categorize_file(file_path)
            if category != 'keep_in_root':
                suggestions['move_files'].append({
                    'file': file_path,
                    'category': category,
                    'description': description,
                    'target_dir': self.file_patterns[category]['target_dir']
                })

        # 分析目录
        for dir_path in directories:
            try:
                item_count = len(list(dir_path.iterdir()))
                if item_count == 0:
                    suggestions['delete_candidates'].append({
                        'path': dir_path,
                        'reason': '空目录'
                    })
                else:
                    suggestions['review_directories'].append({
                        'path': dir_path,
                        'item_count': item_count,
                        'suggestion': '检查是否可以合并到其他目录'
                    })
            except:
                pass

        return suggestions

    def generate_maintenance_report(self, scattered_files, directories, suggestions) -> Any:
        """生成维护报告"""
        logger.info('📄 生成维护报告...')

        report_content = f"""# 项目结构维护报告

**检查时间**: {datetime.now().isoformat()}
**维护工具**: Athena工作平台结构维护器

---

## 📊 当前状态统计

- 📄 散落文件: {len(scattered_files)} 个
- 📁 待检查目录: {len(directories)} 个
- 💡 建议操作: {len(suggestions['move_files']) + len(suggestions['review_directories']) + len(suggestions['delete_candidates'])} 个

---

## 🗂️ 建议的文件移动操作

| 文件名 | 类型 | 目标目录 | 说明 |
|--------|------|---------|------|
"""

        for suggestion in suggestions['move_files']:
            report_content += f"| {suggestion['file'].name} | {suggestion['category']} | {suggestion['target_dir']}/ | {suggestion['description']} |\n"

        if suggestions['review_directories']:
            report_content += "\n---\n\n## 📁 建议检查的目录\n\n"
            for suggestion in suggestions['review_directories']:
                report_content += f"**{suggestion['path'].name}** ({suggestion['item_count']} 项)\n"
                report_content += f"- 建议: {suggestion['suggestion']}\n\n"

        if suggestions['delete_candidates']:
            report_content += "---\n\n## 🗑️ 建议删除的空目录\n\n"
            for candidate in suggestions['delete_candidates']:
                report_content += f"- `{candidate['path'].name}` ({candidate['reason']})\n"

        report_content += """

---

## 🛠️ 自动化维护建议

1. **定期执行**: 建议每周运行一次结构维护检查
2. **文件命名**: 遵循统一的文件命名规范
3. **目录分类**: 将文件及时移动到对应的功能目录
4. **清理临时文件**: 定期清理 temp/ 目录下的临时文件

---

## 📋 维护检查清单

- [ ] 检查根目录是否有新的散落文件
- [ ] 将报告文件移动到 reports/ 目录
- [ ] 将文档文件移动到 documentation/ 目录
- [ ] 清理临时文件和日志
- [ ] 删除空目录
- [ ] 更新项目文档结构说明

---

**保持项目结构整洁有助于提高开发效率和代码维护性！** 🎯
"""

        # 保存报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = self.root_path / 'cleanup' / f"structure_maintenance_{timestamp}.md"
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        logger.info(f"✅ 维护报告已保存: {report_path}")
        return report_path

    def auto_cleanup_temp_files(self) -> Any:
        """自动清理临时文件"""
        logger.info('🧹 自动清理临时文件...')

        temp_dirs = [
            self.root_path / 'temp',
            self.root_path / 'logs',
            self.root_path / 'temp_results'
        ]

        cleaned_count = 0
        cutoff_date = datetime.now() - timedelta(days=7)  # 7天前的文件

        for temp_dir in temp_dirs:
            if temp_dir.exists():
                for item in temp_dir.iterdir():
                    if item.is_file():
                        try:
                            file_time = datetime.fromtimestamp(item.stat().st_mtime)
                            if file_time < cutoff_date:
                                item.unlink()
                                cleaned_count += 1
                        except:
                            pass

        logger.info(f"  🗑️ 清理了 {cleaned_count} 个过期临时文件")
        return cleaned_count

    def run_maintenance(self, auto_cleanup=False) -> Any:
        """运行完整维护流程"""
        logger.info('🔧 开始项目结构维护')
        logger.info(str('='*60))

        try:
            # 1. 扫描当前状态
            scattered_files, directories, expected_found = self.scan_root_directory()

            # 2. 自动清理临时文件
            if auto_cleanup:
                self.auto_cleanup_temp_files()

            # 3. 生成建议
            suggestions = self.suggest_cleanup_actions(scattered_files, directories)

            # 4. 生成报告
            report_path = self.generate_maintenance_report(scattered_files, directories, suggestions)

            logger.info(str('='*60))
            logger.info('🎉 项目结构维护完成!')
            logger.info(f"📄 详细报告: {report_path}")

            total_issues = len(scattered_files) + len(directories)
            if total_issues == 0:
                logger.info('✅ 项目结构非常整洁，无需维护')
            else:
                logger.info(f"⚠️ 发现 {total_issues} 个需要关注的项目")
                logger.info('💡 请查看维护报告了解详细建议')

            return True, total_issues

        except Exception as e:
            logger.info(f"❌ 维护过程异常: {str(e)}")
            return False, 0

def main() -> None:
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='项目结构维护脚本')
    parser.add_argument('--auto-cleanup', action='store_true',
                       help='自动清理7天前的临时文件')

    args = parser.parse_args()

    logger.info('🛠️ 项目结构维护器')
    logger.info('检查和维护项目目录结构，保持根目录整洁')
    logger.info(str('='*60))

    # 创建维护器
    maintainer = ProjectStructureMaintainer()

    # 运行维护
    success, issues = maintainer.run_maintenance(auto_cleanup=args.auto_cleanup)

    if success:
        if issues == 0:
            logger.info("\n✅ 项目结构维护完成！结构非常整洁")
        else:
            logger.info(f"\n✅ 项目结构维护完成！发现 {issues} 个需要关注的项目")
        logger.info('💡 建议定期运行此脚本保持项目整洁')
    else:
        logger.info("\n❌ 项目结构维护失败")

if __name__ == '__main__':
    main()