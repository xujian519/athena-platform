#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小诺智能文件整理工具
Xiaonuo Intelligent File Organizer

使用小诺AI智能分析并整理项目根目录下的散落文件
"""

import json
import logging
import mimetypes
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class XiaonuoFileOrganizer:
    """小诺智能文件整理器"""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.organized_files = []
        self.skipped_files = []
        self.errors = []

        # 小诺的智能分类规则
        self.classification_rules = {
            # 文档类文件
            'docs': {
                'patterns': ['*.md', '*.rst', '*.txt', '*.pdf', '*.doc', '*.docx'],
                'description': '文档文件',
                'target_dir': 'documentation',
                'subdirs': {
                    'README*.md': 'docs',
                    'CHANGELOG*.md': 'docs',
                    'LICENSE*': 'docs',
                    '*.md': 'notes',
                    '*.rst': 'notes',
                    '*.pdf': 'references',
                    '*.doc*': 'references',
                    '*.txt': 'notes'
                }
            },

            # 配置类文件
            'config': {
                'patterns': ['*.json', '*.yaml', '*.yml', '*.ini', '*.cfg', '*.conf', '*.toml'],
                'description': '配置文件',
                'target_dir': 'config',
                'subdirs': {
                    'requirements*.txt': 'dependencies',
                    'package*.json': 'dependencies',
                    'pyproject.toml': 'dependencies',
                    'setup.py': 'dependencies',
                    'Dockerfile*': 'deployment',
                    'docker-compose*': 'deployment',
                    '*.env*': 'environment',
                    'config.*': 'app',
                    '*.yaml': 'app',
                    '*.yml': 'app',
                    '*.ini': 'system',
                    '*.conf': 'system'
                }
            },

            # 脚本类文件
            'scripts': {
                'patterns': ['*.sh', '*.bat', '*.cmd', '*.ps1'],
                'description': '脚本文件',
                'target_dir': 'scripts',
                'subdirs': {
                    'start*.sh': 'startup',
                    'deploy*.sh': 'deployment',
                    'build*.sh': 'build',
                    'test*.sh': 'testing',
                    '*.sh': 'utils'
                }
            },

            # 数据类文件
            'data': {
                'patterns': ['*.csv', '*.xlsx', '*.xls', '*.json', '*.xml', '*.sql', '*.db', '*.sqlite'],
                'description': '数据文件',
                'target_dir': 'data',
                'subdirs': {
                    '*.csv': 'datasets',
                    '*.xls*': 'datasets',
                    '*.sql': 'database',
                    '*.db*': 'database',
                    '*.json': 'structured',
                    '*.xml': 'structured'
                }
            },

            # 日志类文件
            'logs': {
                'patterns': ['*.log', '*.out', '*.err'],
                'description': '日志文件',
                'target_dir': 'logs',
                'subdirs': {
                    '*.log': 'application',
                    '*.out': 'output',
                    '*.err': 'error'
                }
            },

            # 测试类文件
            'tests': {
                'patterns': ['test_*.py', '*_test.py', 'spec_*.py', '*_spec.py', '*.test'],
                'description': '测试文件',
                'target_dir': 'tests',
                'subdirs': {
                    'test_*.py': 'unit',
                    '*_test.py': 'integration',
                    'spec_*.py': 'spec',
                    '*_spec.py': 'spec'
                }
            },

            # 模型类文件
            'models': {
                'patterns': ['*.pkl', '*.model', '*.h5', '*.pt', '*.pth', '*.onnx'],
                'description': '模型文件',
                'target_dir': 'models',
                'subdirs': {
                    '*.pkl': 'pickle',
                    '*.model': 'trained',
                    '*.h5': 'keras',
                    '*.pt*': 'pytorch',
                    '*.onnx': 'onnx'
                }
            },

            # 图像类文件
            'images': {
                'patterns': ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp', '*.svg', '*.ico'],
                'description': '图像文件',
                'target_dir': 'assets/images',
                'subdirs': {
                    '*.png': 'png',
                    '*.jpg': 'photos',
                    '*.jpeg': 'photos',
                    '*.gif': 'animations',
                    '*.svg': 'vector',
                    '*.ico': 'icons'
                }
            },

            # 备份类文件
            'backup': {
                'patterns': ['*.bak', '*.backup', '*.old', '*.save', '*.orig', '*~'],
                'description': '备份文件',
                'target_dir': 'backup',
                'subdirs': {
                    '*.bak': 'manual',
                    '*.backup': 'auto',
                    '*.old': 'old_version',
                    '*.save': 'save'
                }
            },

            # 构建产物类
            'build': {
                'patterns': ['build/', 'dist/', '*.egg-info/', '__pycache__/', '*.pyc'],
                'description': '构建产物',
                'target_dir': 'build',
                'subdirs': {
                    'build/': 'output',
                    'dist/': 'distribution',
                    '*.egg-info/': 'metadata',
                    '__pycache__/': 'cache',
                    '*.pyc': 'bytecode'
                }
            },

            # 临时类文件
            'temp': {
                'patterns': ['*.tmp', '*.temp', '*.swp', '*.swo', '*.lock'],
                'description': '临时文件',
                'target_dir': 'temp',
                'subdirs': {
                    '*.tmp': 'general',
                    '*.temp': 'general',
                    '*.swp': 'vim',
                    '*.swo': 'vim',
                    '*.lock': 'locks'
                }
            },

            # 综合类文件
            'misc': {
                'patterns': ['*'],
                'description': '其他文件',
                'target_dir': 'misc',
                'subdirs': {}
            }
        }

        # 小诺的智能分析功能
        self.intelligent_rules = {
            # 根据文件内容分析
            'content_analysis': {
                'python_file': {
                    'indicators': ['import ', 'def ', 'class ', 'from '],
                    'target': 'src'
                },
                'config_file': {
                    'indicators': ['{', '}', ''key'', ''value''],
                    'target': 'config'
                },
                'data_file': {
                    'indicators': [',', ''id':', ''name':'],
                    'target': 'data'
                }
            },

            # 根据文件名分析
            'name_analysis': {
                'pattern_keywords': {
                    'test': 'tests',
                    'spec': 'tests',
                    'demo': 'examples',
                    'example': 'examples',
                    'sample': 'examples',
                    'config': 'config',
                    'setting': 'config',
                    'env': 'environment',
                    'deploy': 'deployment',
                    'install': 'scripts',
                    'setup': 'scripts',
                    'build': 'build',
                    'run': 'scripts',
                    'start': 'scripts',
                    'doc': 'documentation',
                    'readme': 'documentation',
                    'log': 'logs',
                    'output': 'outputs',
                    'result': 'outputs',
                    'backup': 'backup',
                    'temp': 'temp',
                    'tmp': 'temp',
                    'cache': 'cache',
                    'model': 'models',
                    'data': 'data',
                    'dataset': 'data',
                    'api': 'api',
                    'service': 'services',
                    'util': 'utils',
                    'helper': 'utils',
                    'lib': 'libs'
                }
            }
        }

    def scan_project_root(self) -> List[Dict]:
        """扫描项目根目录下的散落文件"""
        logger.info('🔍 小诺正在扫描项目根目录...')

        scattered_files = []

        # 获取根目录下的所有文件和目录
        for item in self.project_root.iterdir():
            if item.name.startswith('.'):  # 跳过隐藏文件
                continue

            # 检查是否是重要目录，跳过
            important_dirs = {
                'core', 'scripts', 'services', 'domains', 'models', 'data', 'storage',
                'documentation', 'docs', 'config', 'tests', 'deployment', 'utils',
                'apps', 'patent-platform', 'monitoring', 'database', 'tools', 'outputs'
            }

            if item.is_dir() and item.name in important_dirs:
                continue

            # 记录散落的文件/目录
            scattered_files.append({
                'name': item.name,
                'path': item,
                'is_dir': item.is_dir(),
                'size': item.stat().st_size if item.is_file() else 0,
                'modified': datetime.fromtimestamp(item.stat().st_mtime)
            })

        logger.info(f"✅ 小诺发现了 {len(scattered_files)} 个散落的文件/目录")
        return scattered_files

    def classify_file(self, file_info: Dict) -> Dict:
        """小诺智能分类文件"""
        file_path = file_info['path']
        file_name = file_path.name.lower()

        # 1. 基于扩展名的基本分类
        for category, rule in self.classification_rules.items():
            if category in ['misc']:
                continue  # 最后处理

            for pattern in rule['patterns']:
                if file_path.match(pattern):
                    return {
                        'category': category,
                        'target_dir': rule['target_dir'],
                        'description': rule['description'],
                        'confidence': 0.8
                    }

        # 2. 智能内容分析（仅对文本文件）
        if file_path.is_file() and self._is_text_file(file_path):
            content_analysis = self._analyze_file_content(file_path)
            if content_analysis:
                return content_analysis

        # 3. 基于文件名的智能分析
        name_analysis = self._analyze_file_name(file_name)
        if name_analysis:
            return name_analysis

        # 4. 默认分类
        return {
            'category': 'misc',
            'target_dir': 'misc',
            'description': '其他文件',
            'confidence': 0.3
        }

    def _is_text_file(self, file_path: Path) -> bool:
        """判断是否是文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(1024)  # 尝试读取前1KB
            return True
        except (UnicodeDecodeError, PermissionError, OSError):
            return False

    def _analyze_file_content(self, file_path: Path) -> Dict | None:
        """分析文件内容进行智能分类"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(2048)  # 读取前2KB
                content_lower = content.lower()

                # Python文件检测
                if any(indicator in content_lower for indicator in
                       ['import ', 'def ', 'class ', 'from ', '__init__', 'if __name__']):
                    return {
                        'category': 'source',
                        'target_dir': 'src',
                        'description': 'Python源代码文件',
                        'confidence': 0.9
                    }

                # 配置文件检测
                if any(indicator in content for indicator in
                       ['{', '}', ''key'', ''value'', '=', '[', ']']):
                    return {
                        'category': 'config',
                        'target_dir': 'config',
                        'description': '配置文件',
                        'confidence': 0.8
                    }

                # 数据文件检测
                if any(indicator in content_lower for indicator in
                       [',', ''id':', ''name':', ''data'', ''items'']):
                    return {
                        'category': 'data',
                        'target_dir': 'data',
                        'description': '数据文件',
                        'confidence': 0.7
                    }

                # 文档文件检测
                if len(content.split('\n')) < 50 and not any(char in content for char in '{}[]()'):
                    return {
                        'category': 'docs',
                        'target_dir': 'docs',
                        'description': '文档文件',
                        'confidence': 0.6
                    }

        except (OSError, PermissionError):
            pass

        return None

    def _analyze_file_name(self, file_name: str) -> Dict | None:
        """基于文件名进行智能分析"""
        for keyword, target_dir in self.intelligent_rules['name_analysis']['pattern_keywords'].items():
            if keyword in file_name:
                return {
                    'category': 'derived',
                    'target_dir': target_dir,
                    'description': f'基于文件名推断的{keyword}类文件',
                    'confidence': 0.6
                }
        return None

    def suggest_target_location(self, file_info: Dict, classification: Dict) -> Path:
        """小诺建议目标位置"""
        target_dir = self.project_root / classification['target_dir']

        # 检查是否需要子目录
        category_rules = self.classification_rules.get(classification['category'], {})
        subdirs = category_rules.get('subdirs', {})

        for pattern, subdir in subdirs.items():
            if file_info['path'].match(pattern):
                target_dir = target_dir / subdir
                break

        # 智能子目录推断
        if classification['category'] == 'misc':
            file_name = file_info['name'].lower()
            if any(word in file_name for word in ['script', 'util', 'helper']):
                target_dir = self.project_root / 'utils'
            elif any(word in file_name for word in ['example', 'demo', 'sample']):
                target_dir = self.project_root / 'examples'
            elif any(word in file_name for word in ['playground', 'experiment']):
                target_dir = self.project_root / 'playground'

        return target_dir

    def create_directory_structure(self):
        """创建小诺建议的目录结构"""
        logger.info('🏗️ 小诺正在创建目录结构...')

        # 创建主要目录
        main_dirs = [
            'documentation', 'docs', 'config', 'scripts', 'data', 'logs', 'tests',
            'models', 'assets/images', 'backup', 'build', 'temp', 'misc',
            'src', 'utils', 'examples', 'outputs', 'playground'
        ]

        for dir_name in main_dirs:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"📁 创建目录: {dir_name}")

        # 创建子目录
        subdirs = {
            'config': ['app', 'system', 'environment', 'dependencies'],
            'scripts': ['startup', 'deployment', 'build', 'testing', 'utils'],
            'data': ['datasets', 'database', 'structured', 'exports'],
            'logs': ['application', 'error', 'output'],
            'tests': ['unit', 'integration', 'spec'],
            'models': ['pickle', 'trained', 'keras', 'pytorch', 'onnx'],
            'assets/images': ['png', 'photos', 'vector', 'icons'],
            'backup': ['manual', 'auto', 'old_version'],
            'documentation': ['api', 'tutorials', 'notes', 'references']
        }

        for main_dir, sub_list in subdirs.items():
            for sub_dir in sub_list:
                sub_path = self.project_root / main_dir / sub_dir
                if not sub_path.exists():
                    sub_path.mkdir(parents=True, exist_ok=True)

    def organize_files(self, scattered_files: List[Dict], dry_run: bool = True) -> Dict:
        """小诺执行文件整理"""
        logger.info('🧹 小诺正在整理文件...')

        results = {
            'organized': [],
            'skipped': [],
            'errors': [],
            'suggestions': []
        }

        for file_info in scattered_files:
            try:
                # 智能分类
                classification = self.classify_file(file_info)

                # 建议目标位置
                target_path = self.suggest_target_location(file_info, classification)

                # 创建目标目录
                if not dry_run and not target_path.exists():
                    target_path.mkdir(parents=True, exist_ok=True)

                # 生成新路径
                if file_info['is_dir']:
                    new_path = target_path / file_info['name']
                else:
                    new_path = target_path / file_info['name']

                # 处理重名冲突
                if new_path.exists():
                    base_name = new_path.stem
                    extension = new_path.suffix
                    counter = 1
                    while new_path.exists():
                        new_path = target_path / f"{base_name}_{counter}{extension}"
                        counter += 1

                # 执行移动
                if not dry_run:
                    if file_info['is_dir']:
                        shutil.move(str(file_info['path']), str(new_path))
                    else:
                        shutil.move(str(file_info['path']), str(new_path))

                    results['organized'].append({
                        'original': str(file_info['path']),
                        'new': str(new_path),
                        'category': classification['category'],
                        'description': classification['description']
                    })

                    logger.info(f"✅ 整理: {file_info['name']} → {classification['description']}")
                else:
                    results['organized'].append({
                        'original': str(file_info['path']),
                        'new': str(new_path),
                        'category': classification['category'],
                        'description': classification['description'],
                        'dry_run': True
                    })

                    logger.info(f"📋 建议: {file_info['name']} → {classification['description']}")

            except Exception as e:
                error_info = {
                    'file': str(file_info['path']),
                    'error': str(e)
                }
                results['errors'].append(error_info)
                logger.error(f"❌ 整理失败: {file_info['name']} - {e}")

        return results

    def generate_organization_report(self, scattered_files: List[Dict], results: Dict) -> str:
        """生成整理报告"""
        report = f"""
# 小诺智能文件整理报告

## 🤖 整理概览
**整理时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**整理者**: 小诺 (Xiaonuo AI Assistant)
**项目路径**: {self.project_root}

## 📊 发现的散落文件

### 文件统计
- **总数量**: {len(scattered_files)}
- **文件类型**: {len([f for f in scattered_files if not f['is_dir']])} 个文件
- **目录数量**: {len([f for f in scattered_files if f['is_dir']])} 个目录

### 文件大小分布
"""

        # 按大小分组
        size_groups = {
            '小文件 (< 1KB)': [],
            '中等文件 (1KB - 1MB)': [],
            '大文件 (> 1MB)': []
        }

        for file_info in scattered_files:
            if file_info['size'] < 1024:
                size_groups['小文件 (< 1KB)'].append(file_info['name'])
            elif file_info['size'] < 1024 * 1024:
                size_groups['中等文件 (1KB - 1MB)'].append(file_info['name'])
            else:
                size_groups['大文件 (> 1MB)'].append(file_info['name'])

        for group_name, files in size_groups.items():
            report += f"- **{group_name}**: {len(files)} 个\n"

        # 显示文件列表
        report += f"""
### 详细文件列表
| 文件名 | 类型 | 大小 | 修改时间 |
|--------|------|------|----------|
{chr(10).join([f"| {f['name'][:30]}{'...' if len(f['name']) > 30 else ''} | {'目录' if f['is_dir'] else '文件'} | {self._format_size(f['size'])} | {f['modified'].strftime('%Y-%m-%d')} |"
                for f in scattered_files[:20]])}
"""

        if len(scattered_files) > 20:
            report += f"\n... 还有 {len(scattered_files) - 20} 个文件\n"

        # 整理建议
        report += f"""
## 🧹 小诺的整理建议

### 智能分类结果
{chr(10).join([f"- **{item['description']}**: {item['category']} → {item['new'].replace(str(self.project_root), '.')}"
                for item in results['organized'][:10]])}
"""

        if len(results['organized']) > 10:
            report += f"\n... 还有 {len(results['organized']) - 10} 个整理项\n"

        # 错误信息
        if results['errors']:
            report += f"""
### ⚠️ 整理错误
{chr(10).join([f"- **{error['file']}**: {error['error']}" for error in results['errors']])}
"""

        report += f"""
## 💡 小诺的贴心建议

### 目录结构优化
1. **文档管理**: 所有文档文件都整理到 `documentation/` 目录
2. **配置集中**: 配置文件统一放在 `config/` 目录
3. **脚本归类**: 脚本文件分类放到 `scripts/` 的子目录
4. **数据分离**: 数据文件移动到 `data/` 目录
5. **日志归档**: 日志文件整理到 `logs/` 目录

### 维护建议
1. **定期整理**: 每周运行一次小诺整理工具
2. **命名规范**: 遵循统一的文件命名规范
3. **分类清晰**: 新建文件时直接放到正确目录
4. **及时清理**: 定期清理临时文件和备份

### 执行整理
如果确认无误，可以执行实际整理：
```bash
# 预览模式（已执行）
python3 scripts/xiaonuo_file_organizer.py --dry-run

# 执行实际整理
python3 scripts/xiaonuo_file_organizer.py --organize
```

## 🎯 总结
小诺发现了 {len(scattered_files)} 个散落的文件/目录，并提供了智能的整理建议。
通过小诺的整理，项目结构将更加清晰，文件管理更加高效！

---
**整理完成**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**整理工具**: 小诺智能文件整理器
**状态**: 预览完成，等待确认执行
"""

        return report

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='小诺智能文件整理工具')
    parser.add_argument('--project-root', default='.', help='项目根目录')
    parser.add_argument('--dry-run', action='store_true', default=True, help='预览模式（默认）')
    parser.add_argument('--organize', action='store_true', help='执行实际整理')
    parser.add_argument('--create-dirs', action='store_true', help='创建目录结构')

    args = parser.parse_args()

    # 小诺启动问候
    logger.info('💖 小诺智能文件整理工具')
    logger.info(str('=' * 50))
    logger.info("🤖 小诺: '爸爸，我来帮你整理项目里的散落文件！'")
    print()

    organizer = XiaonuoFileOrganizer(args.project_root)

    try:
        # 创建目录结构（如果需要）
        if args.create_dirs:
            logger.info('🏗️ 小诺正在创建目录结构...')
            organizer.create_directory_structure()
            logger.info('✅ 目录结构创建完成！')
            print()

        # 扫描散落文件
        scattered_files = organizer.scan_project_root()

        if not scattered_files:
            logger.info("🎉 小诺: '爸爸，项目目录已经很整洁了，没有散落的文件需要整理！'")
            return

        logger.info(f"📁 小诺发现了 {len(scattered_files)} 个散落的文件/目录")
        print()

        # 执行整理
        if args.organize:
            logger.info('🧹 小诺正在整理文件...')
            results = organizer.organize_files(scattered_files, dry_run=False)

            logger.info(f"\n🎉 小诺整理完成！")
            logger.info(f"✅ 成功整理: {len(results['organized'])} 个文件")
            if results['errors']:
                logger.info(f"❌ 整理错误: {len(results['errors'])} 个")
        else:
            # 预览模式
            logger.info('👀 小诺正在进行智能分析和预览...')
            results = organizer.organize_files(scattered_files, dry_run=True)

        # 生成报告
        report = organizer.generate_organization_report(scattered_files, results)

        # 保存报告
        report_file = Path('XIAONUO_ORGANIZATION_REPORT.md')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"\n📄 整理报告已保存: {report_file}")

        if args.dry_run:
            logger.info("\n💡 小诺建议: 使用 --organize 参数执行实际整理")

    except Exception as e:
        logger.info(f"❌ 小诺: '哎呀，整理过程中出现了问题: {e}'")
        logger.error(f"❌ 整理失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()