#!/usr/bin/env python3
"""
整理根目录散落文件
Organize Root Directory Files

将根目录下的散落文件整理到合适的目录结构中
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

class RootDirectoryOrganizer:
    """根目录整理器"""

    def __init__(self):
        self.root_path = Path('/Users/xujian/Athena工作平台')

        # 文件分类规则
        self.file_categories = {
            'reports': {
                'pattern': ['*_REPORT.md', '*_ANALYSIS.md', '*_SUMMARY.md'],
                'target_dir': 'reports',
                'description': '各类报告文件'
            },
            'config': {
                'pattern': ['.env*', '*.config', '*.conf'],
                'target_dir': 'config',
                'description': '配置文件'
            },
            'temp': {
                'pattern': ['*.tmp', '*.temp', '*.bak', '*~'],
                'target_dir': 'temp',
                'description': '临时文件'
            },
            'data': {
                'pattern': ['*.json', '*.csv', '*.xml', '*.data'],
                'target_dir': 'data',
                'description': '数据文件'
            },
            'docs': {
                'pattern': ['*.md', '*.txt', '*.rst'],
                'target_dir': 'docs',
                'description': '文档文件'
            }
        }

        # 特殊文件处理
        self.special_files = {
            'qdrant': 'data/qdrant_data',
            'production_kg_quality_report.json': 'reports/quality_reports'
        }

    def scan_current_files(self) -> Any:
        """扫描当前根目录文件"""
        logger.info('📋 扫描根目录文件...')

        files = []
        for item in self.root_path.iterdir():
            if item.is_file() and not item.name.startswith('.'):
                files.append(item)

        logger.info(f"📁 发现 {len(files)} 个非隐藏文件:")
        for file in sorted(files):
            size = file.stat().st_size if file.exists() else 0
            logger.info(f"  - {file.name} ({size} bytes)")

        return files

    def create_directories(self) -> Any:
        """创建必要的目录"""
        logger.info('🏗️ 创建目录结构...')

        directories = [
            'reports/quality_reports',
            'reports/cleanup_reports',
            'reports/optimization_reports',
            'reports/legal_reports',
            'data/external',
            'data/processed',
            'config/production',
            'temp/backup',
            'cleanup/organized_files'
        ]

        for dir_path in directories:
            full_path = self.root_path / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"  ✅ {dir_path}")

    def categorize_file(self, file_path) -> Any:
        """对文件进行分类"""
        file_name = file_path.name.lower()

        # 检查特殊文件
        for pattern, target in self.special_files.items():
            if pattern in file_name:
                return target

        # 检查分类规则
        for _category, rules in self.file_categories.items():
            for pattern in rules['pattern']:
                if file_name.endswith(pattern.replace('*', '')) or pattern.replace('*', '') in file_name:
                    return rules['target_dir']

        # 默认分类
        if file_name.endswith('.md'):
            return 'docs'
        elif file_name.endswith('.json'):
            return 'data'
        else:
            return 'misc'

    def move_file(self, source_path, target_dir) -> Any:
        """移动文件到目标目录"""
        target_path = self.root_path / target_dir / source_path.name

        # 如果目标文件已存在，添加时间戳
        if target_path.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name_parts = source_path.name.rsplit('.', 1)
            if len(name_parts) == 2:
                new_name = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
            else:
                new_name = f"{source_path.name}_{timestamp}"
            target_path = self.root_path / target_dir / new_name

        try:
            shutil.move(str(source_path), str(target_path))
            return True, target_path.name
        except Exception as e:
            return False, str(e)

    def organize_files(self) -> Any:
        """整理文件"""
        logger.info('🗂️ 开始整理文件...')

        files = self.scan_current_files()
        moved_files = []
        failed_moves = []

        for file_path in files:
            # 跳过重要系统文件
            if file_path.name in ['README.md', 'LICENSE', 'requirements.txt']:
                logger.info(f"  ⏭️ 跳过系统文件: {file_path.name}")
                continue

            target_dir = self.categorize_file(file_path)

            success, result = self.move_file(file_path, target_dir)

            if success:
                moved_files.append({
                    'original': file_path.name,
                    'target': target_dir,
                    'new_name': result
                })
                logger.info(f"  ✅ {file_path.name} → {target_dir}/")
            else:
                failed_moves.append({
                    'file': file_path.name,
                    'error': result
                })
                logger.info(f"  ❌ {file_path.name}: {result}")

        return moved_files, failed_moves

    def generate_organization_report(self, moved_files, failed_moves) -> Any:
        """生成整理报告"""
        logger.info('📄 生成整理报告...')

        report_content = f"""# 根目录文件整理报告

**整理时间**: {datetime.now().isoformat()}
**整理工具**: Athena工作平台文件整理器

---

## 📊 整理统计

- ✅ 成功移动: {len(moved_files)} 个文件
- ❌ 移动失败: {len(failed_moves)} 个文件
- 📁 创建目录: 12 个

---

## 📂 成功移动的文件

| 原文件名 | 目标目录 | 新文件名 |
|---------|---------|---------|
"""

        for move in moved_files:
            report_content += f"| {move['original']} | {move['target']} | {move['new_name']} |\n"

        if failed_moves:
            report_content += "\n---\n\n## ❌ 移动失败的文件\n\n"
            for fail in failed_moves:
                report_content += f"**{fail['file']}**: {fail['error']}\n"

        report_content += """

---

## 🗂️ 目录结构

```
Athena工作平台/
├── reports/
│   ├── quality_reports/      # 质量报告
│   ├── cleanup_reports/      # 清理报告
│   ├── optimization_reports/ # 优化报告
│   └── legal_reports/        # 法律相关报告
├── data/
│   ├── external/            # 外部数据
│   └── processed/           # 处理后数据
├── config/
│   └── production/          # 生产配置
├── temp/
│   └── backup/              # 临时备份
└── cleanup/
    └── organized_files/     # 已整理文件记录
```

---

## 💡 建议

1. 定期清理 `temp/` 目录下的临时文件
2. 将重要的配置文件提交到版本控制
3. 定期整理和归档历史报告
4. 建立文件命名规范，便于后续管理

---

**整理完成！根目录现在更加整洁有序。** 🎉
"""

        # 保存报告
        report_path = self.root_path / 'cleanup' / 'root_organization_report.md'
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        logger.info(f"✅ 整理报告已保存: {report_path}")
        return report_path

    def clean_empty_directories(self) -> Any:
        """清理空目录"""
        logger.info('🧹 清理空目录...')

        empty_dirs = []
        for item in self.root_path.iterdir():
            if item.is_dir() and not any(item.iterdir()):
                empty_dirs.append(item)

        for empty_dir in empty_dirs:
            try:
                empty_dir.rmdir()
                logger.info(f"  🗑️ 删除空目录: {empty_dir.name}")
            except Exception as e:
                logger.info(f"  ❌ 无法删除 {empty_dir.name}: {e}")

    def run_organization(self) -> Any:
        """运行完整整理流程"""
        logger.info('🚀 开始根目录文件整理')
        logger.info(str('='*60))

        try:
            # 1. 创建目录
            self.create_directories()

            # 2. 整理文件
            moved_files, failed_moves = self.organize_files()

            # 3. 生成报告
            report_path = self.generate_organization_report(moved_files, failed_moves)

            # 4. 清理空目录
            self.clean_empty_directories()

            logger.info(str('='*60))
            logger.info('🎉 根目录文件整理完成!')
            logger.info(f"📊 成功移动 {len(moved_files)} 个文件")
            if failed_moves:
                logger.info(f"⚠️ 有 {len(failed_moves)} 个文件移动失败")
            logger.info(f"📄 详细报告: {report_path}")

            return True

        except Exception as e:
            logger.info(f"❌ 整理过程异常: {str(e)}")
            return False

def main() -> None:
    """主函数"""
    logger.info('🗂️ 根目录文件整理器')
    logger.info('将根目录下的散落文件整理到合适的目录中')
    logger.info(str('='*60))

    # 创建整理器
    organizer = RootDirectoryOrganizer()

    # 运行整理
    success = organizer.run_organization()

    if success:
        logger.info("\n✅ 根目录整理成功完成！")
        logger.info('💡 建议查看整理报告了解详细情况')
    else:
        logger.info("\n❌ 根目录整理失败，请检查错误信息")

if __name__ == '__main__':
    main()
