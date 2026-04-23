#!/usr/bin/env python3
"""
Athena工作平台文档标准化工具
Documentation Standardizer for Athena Work Platform

用于统一各子系统文档格式，确保文档结构和风格的一致性

使用方法:
python3 documentation_standardizer.py --scan
python3 documentation_standardizer.py --standardize --target patent-platform/core
python3 documentation_standardizer.py --validate
python3 documentation_standardizer.py --generate-template

作者: Athena AI系统
创建时间: 2025-12-08
版本: 1.0.0
"""

import argparse
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# 添加项目路径
project_root = Path(__file__).parent.parent.parent

class DocumentationStandardizer:
    """文档标准化器"""

    def __init__(self):
        self.project_root = project_root
        self.docs_dir = self.project_root / 'docs'
        self.templates_dir = self.docs_dir / 'templates'

        # 确保目录存在
        self.templates_dir.mkdir(exist_ok=True)

        # 标准化模板
        self.readme_template = self._get_readme_template()
        self.api_doc_template = self._get_api_doc_template()

        # 验证规则
        self.validation_rules = self._get_validation_rules()

    def _get_readme_template(self) -> str:
        """获取README标准模板"""
        return """# {title}

> {description}

**创建时间**: {creation_date}
**版本**: {version}
**维护者**: {maintainer}

## 📋 目录

- [🎯 项目概述](#-项目概述)
- [📁 目录结构](#-目录结构)
- [🚀 快速开始](#-快速开始)
- [🔧 核心功能](#-核心功能)
- [📚 使用指南](#-使用指南)
- [🧪 测试](#-测试)
- [📊 配置](#-配置)
- [🔗 API参考](#api参考)
- [🤝 贡献指南](#-贡献指南)
- [📄 许可证](#-许可证)

---

## 🎯 项目概述

{overview}

### 🎯 核心价值

{value_proposition}

### 📊 主要特性

{features}

---

## 📁 目录结构

```
{directory_structure}
```

---

## 🚀 快速开始

### 📋 环境要求

{requirements}

### ⚡ 快速安装

```bash
# 安装步骤
{installation_steps}
```

### 🌐 基本使用

```bash
# 基本使用示例
{usage_example}
```

---

## 🔧 核心功能

{core_features}

---

## 📚 使用指南

{usage_guide}

---

## 🧪 测试

{testing}

---

## 📊 配置

{configuration}

---

## 🔗 API参考

{api_reference}

---

## 🤝 贡献指南

### 📝 开发流程

{development_workflow}

### 🧪 测试要求

{testing_requirements}

### 📋 代码规范

{code_standards}

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

<div align='center'>

**{project_name} - {tagline}**

*[文档链接](../README.md) • [API文档](api.md) • [贡献指南](contributing.md)*

</div>
"""

    def _get_api_doc_template(self) -> str:
        """获取API文档标准模板"""
        return """# {api_name} API文档

**创建时间**: {creation_date}
**版本**: {version}
**基础URL**: {base_url}

## 📋 目录

- [🔍 概述](#-概述)
- [🔐 认证](#-认证)
- [📊 API端点](#-api端点)
- [📝 请求格式](#-请求格式)
- [📋 响应格式](#-响应格式)
- [🚨 错误处理](#-错误处理)
- [📚 示例](#-示例)

---

## 🔍 概述

{overview}

---

## 🔐 认证

{authentication}

---

## 📊 API端点

{endpoints}

---

## 📝 请求格式

{request_format}

---

## 📋 响应格式

{response_format}

---

## 🚨 错误处理

{error_handling}

---

## 📚 示例

{examples}
"""

    def _get_validation_rules(self) -> dict[str, Any]:
        """获取文档验证规则"""
        return {
            'readme_required_sections': [
                '# 项目标题',
                '项目概述',
                '目录结构',
                '快速开始',
                '核心功能'
            ],
            'formatting_rules': {
                'title_pattern': r"^# .+$",
                'section_pattern': r"^## .+$",
                'subsection_pattern': r"^### .+$",
                'code_block_pattern': r"```",
                'emoji_usage': '鼓励在标题前使用emoji',
                'max_title_length': 60,
                'max_section_count': 20
            },
            'content_requirements': {
                'description_required': True,
                'installation_required': True,
                'usage_required': True,
                'license_required': True
            }
        }

    def scan_documentation(self) -> dict[str, Any]:
        """扫描项目中的所有文档"""
        logger.info('🔍 扫描项目文档...')

        scan_results = {
            'scan_time': datetime.now().isoformat(),
            'total_readmes': 0,
            'total_md_files': 0,
            'readmes': {},
            'other_docs': {},
            'directories_without_readme': [],
            'standardization_score': 0
        }

        # 查找所有README文件
        readme_files = list(self.project_root.rglob('README*'))
        readme_files = [f for f in readme_files if f.is_file() and not any(skip in str(f) for skip in ['node_modules', '.git', 'scripts_archive'])]

        scan_results['total_readmes'] = len(readme_files)

        # 分析每个README文件
        for readme_file in readme_files:
            relative_path = readme_file.relative_to(self.project_root)

            try:
                with open(readme_file, encoding='utf-8') as f:
                    content = f.read()

                file_info = {
                    'path': str(relative_path),
                    'size_bytes': readme_file.stat().st_size,
                    'line_count': len(content.splitlines()),
                    'last_modified': datetime.fromtimestamp(readme_file.stat().st_mtime).isoformat(),
                    'has_title': bool(re.search(r'^# .+$', content, re.MULTILINE)),
                    'has_toc': '## 📋 目录' in content or '## 目录' in content,
                    'has_installation': any(keyword in content.lower() for keyword in ['安装', 'install', '快速开始', 'quick start']),
                    'has_usage': any(keyword in content.lower() for keyword in ['使用', 'usage', '示例', 'example']),
                    'estimated_quality': self._estimate_quality(content)
                }

                scan_results['readmes'][str(relative_path)] = file_info

            except Exception as e:
                scan_results['readmes'][str(relative_path)] = {
                    'path': str(relative_path),
                    'error': str(e),
                    'estimated_quality': 0
                }

        # 查找其他文档文件
        other_md_files = []
        for pattern in ['*.md', '*.MD']:
            other_md_files.extend(self.project_root.rglob(pattern))

        # 过滤掉README文件
        other_md_files = [f for f in other_md_files if f.is_file() and 'README' not in f.name
                         and not any(skip in str(f) for skip in ['node_modules', '.git', 'scripts_archive'])]

        scan_results['total_md_files'] = len(other_md_files)

        # 分析其他文档
        for md_file in other_md_files:
            relative_path = md_file.relative_to(self.project_root)

            try:
                with open(md_file, encoding='utf-8') as f:
                    content = f.read()

                scan_results['other_docs'][str(relative_path)] = {
                    'path': str(relative_path),
                    'size_bytes': md_file.stat().st_size,
                    'line_count': len(content.splitlines()),
                    'last_modified': datetime.fromtimestamp(md_file.stat().st_mtime).isoformat()
                }

            except Exception as e:
                scan_results['other_docs'][str(relative_path)] = {
                    'path': str(relative_path),
                    'error': str(e)
                }

        # 查找缺少README的目录
        key_directories = ['patent-platform/core', 'academic_retrieval_system', 'patent-platform/agent',
                          'core', 'services', 'tools', 'workflows']

        for directory in key_directories:
            dir_path = self.project_root / directory
            if dir_path.exists() and dir_path.is_dir():
                readme_path = dir_path / 'README.md'
                if not readme_path.exists():
                    scan_results['directories_without_readme'].append(directory)

        # 计算标准化评分
        if scan_results['readmes']:
            qualities = [info.get('estimated_quality', 0) for info in scan_results['readmes'].values() if 'estimated_quality' in info]
            if qualities:
                scan_results['standardization_score'] = round(sum(qualities) / len(qualities), 1)

        return scan_results

    def _estimate_quality(self, content: str) -> float:
        """估算文档质量分数 (0-100)"""
        score = 0

        # 基础结构检查 (40分)
        if re.search(r'^# .+$', content, re.MULTILINE):
            score += 10  # 有标题

        if '##' in content:
            score += 10  # 有二级标题

        if '###' in content:
            score += 5   # 有三级标题

        if '```' in content:
            score += 5   # 有代码块

        if '```bash' in content or '```python' in content:
            score += 5   # 有代码示例

        if any(keyword in content.lower() for keyword in ['安装', 'install']):
            score += 5   # 有安装说明

        # 内容质量检查 (30分)
        if len(content) > 500:
            score += 10  # 内容充实

        if len(content.splitlines()) > 20:
            score += 10  # 结构详细

        if any(emoji in content for emoji in ['🎯', '📁', '🚀', '🔧', '📚']):
            score += 5   # 使用emoji美化

        if '## 📋 目录' in content or '## 目录' in content:
            score += 5   # 有目录

        # 完整性检查 (30分)
        required_keywords = ['使用', '功能', '配置', '示例']
        found_keywords = sum(1 for keyword in required_keywords if keyword in content)
        score += (found_keywords / len(required_keywords)) * 30

        return min(100, score)

    def validate_documentation(self) -> dict[str, Any]:
        """验证文档标准化程度"""
        logger.info('✅ 验证文档标准化程度...')

        validation_results = {
            'validation_time': datetime.now().isoformat(),
            'total_files_checked': 0,
            'valid_files': 0,
            'invalid_files': 0,
            'issues': [],
            'recommendations': [],
            'overall_score': 0
        }

        # 获取扫描结果
        scan_results = self.scan_documentation()

        # 验证README文件
        for path, info in scan_results['readmes'].items():
            validation_results['total_files_checked'] += 1

            if 'error' in info:
                validation_results['invalid_files'] += 1
                validation_results['issues'].append(f"❌ {path}: 文件读取失败 - {info['error']}")
                continue

            # 检查必需内容
            issues = []

            if not info.get('has_title', False):
                issues.append('缺少项目标题')

            if not info.get('has_installation', False):
                issues.append('缺少安装说明')

            if not info.get('has_usage', False):
                issues.append('缺少使用示例')

            if issues:
                validation_results['invalid_files'] += 1
                for issue in issues:
                    validation_results['issues'].append(f"⚠️ {path}: {issue}")
            else:
                validation_results['valid_files'] += 1

        # 生成改进建议
        if scan_results['directories_without_readme']:
            validation_results['recommendations'].append(
                f"📝 建议为以下目录添加README文件: {', '.join(scan_results['directories_without_readme'])}"
            )

        if scan_results['standardization_score'] < 70:
            validation_results['recommendations'].append(
                f"📈 文档标准化评分较低 ({scan_results['standardization_score']}/100)，建议运行标准化工具"
            )

        # 计算总体评分
        if validation_results['total_files_checked'] > 0:
            validation_results['overall_score'] = round(
                (validation_results['valid_files'] / validation_results['total_files_checked']) * 100, 1
            )

        return validation_results

    def standardize_readme(self, target_path: str, force: bool = False) -> bool:
        """标准化指定目录的README文件"""
        logger.info(f"📝 标准化 {target_path} 的README文件...")

        target_dir = self.project_root / target_path

        if not target_dir.exists():
            logger.info(f"❌ 目录不存在: {target_dir}")
            return False

        readme_path = target_dir / 'README.md'

        # 检查是否已存在
        if readme_path.exists() and not force:
            logger.info(f"⚠️ README文件已存在: {readme_path}")
            logger.info('   使用 --force 参数强制覆盖')
            return False

        # 收集信息
        project_name = self._extract_project_name(target_path)

        template_data = {
            'title': project_name,
            'description': f"Athena工作平台的{project_name}模块",
            'creation_date': datetime.now().strftime('%Y-%m-%d'),
            'version': '1.0.0',
            'maintainer': 'Athena AI系统',
            'project_name': project_name,
            'tagline': '智能化的解决方案',
            'overview': f"{project_name}是Athena工作平台的重要组成部分，提供专业的功能支持。",
            'value_proposition': "• 高效的处理能力\n• 优秀的用户体验\n• 完善的功能覆盖",
            'features': "• 🎯 核心功能模块\n• 🔧 灵活的配置选项\n• 📚 详细的文档支持",
            'directory_structure': self._generate_directory_structure(target_dir),
            'requirements': "- Python 3.11+\n- 相关依赖包",
            'installation_steps': 'pip install -r requirements.txt',
            'usage_example': "# 基本使用示例\npython main.py",
            'core_features': '待补充具体功能说明',
            'usage_guide': '待补充详细使用指南',
            'testing': "```bash\n# 运行测试\npython -m pytest tests/\n```",
            'configuration': '配置文件位于 config/ 目录',
            'api_reference': '详细的API文档请参考 api.md',
            'development_workflow': "1. Fork 项目\n2. 创建功能分支\n3. 提交更改\n4. 创建 Pull Request",
            'testing_requirements': "- 新功能需要包含测试\n- 测试覆盖率应达到 80%+",
            'code_standards': '遵循 PEP 8 规范'
        }

        # 生成README内容
        readme_content = self.readme_template.format(**template_data)

        # 备份现有文件
        if readme_path.exists():
            backup_path = readme_path.with_suffix(f".md.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            readme_path.rename(backup_path)
            logger.info(f"  📦 已备份原文件: {backup_path}")

        # 写入新内容
        try:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            logger.info(f"  ✅ README文件已生成: {readme_path}")
            return True
        except Exception as e:
            logger.info(f"  ❌ 写入失败: {e}")
            return False

    def _extract_project_name(self, path: str) -> str:
        """从路径提取项目名称"""
        path_parts = Path(path).parts
        if path_parts:
            return path_parts[-1].replace('_', ' ').replace('-', ' ').title()
        return 'Unknown Project'

    def _generate_directory_structure(self, target_dir: Path) -> str:
        """生成目录结构"""
        try:
            lines = [f"{target_dir.name}/"]

            for item in sorted(target_dir.iterdir()):
                if item.is_dir() and not item.name.startswith('.'):
                    lines.append(f"├── 📂 {item.name}/")
                elif item.is_file() and item.suffix in ['.py', '.js', '.yaml', '.yml', '.md']:
                    lines.append(f"├── 📄 {item.name}")

            # 修正最后一个符号
            if lines:
                lines[-1] = lines[-1].replace('├──', '└──')

            return "\n".join(lines)

        except Exception:
            return f"{target_dir.name}/\n├── 📄 README.md\n└── 📂 配置文件/"

    def generate_template(self, template_type: str = 'readme') -> str:
        """生成文档模板"""
        if template_type == 'readme':
            template = self.readme_template
            output_file = self.templates_dir / 'README_template.md'
        elif template_type == 'api':
            template = self.api_doc_template
            output_file = self.templates_dir / 'API_template.md'
        else:
            logger.info(f"❌ 不支持的模板类型: {template_type}")
            return ''

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(template)
            logger.info(f"✅ 模板已生成: {output_file}")
            return str(output_file)
        except Exception as e:
            logger.info(f"❌ 模板生成失败: {e}")
            return ''

    def print_scan_results(self, results: dict[str, Any]) -> Any:
        """打印扫描结果"""
        logger.info("\n📊 文档扫描结果")
        logger.info(f"🕐 扫描时间: {results['scan_time']}")
        logger.info(f"📄 README文件总数: {results['total_readmes']}")
        logger.info(f"📝 其他文档总数: {results['total_md_files']}")
        logger.info(f"📈 标准化评分: {results['standardization_score']}/100")

        if results['readmes']:
            logger.info("\n📋 README文件质量排行:")
            sorted_readmes = sorted(
                results['readmes'].items(),
                key=lambda x: x[1].get('estimated_quality', 0),
                reverse=True
            )

            for i, (path, info) in enumerate(sorted_readmes[:10], 1):
                quality = info.get('estimated_quality', 0)
                status_emoji = '🟢' if quality >= 80 else '🟡' if quality >= 60 else '🔴'
                logger.info(f"  {i:2d}. {status_emoji} {quality:3.0f}% {path}")

        if results['directories_without_readme']:
            logger.info("\n❌ 缺少README的目录:")
            for directory in results['directories_without_readme']:
                logger.info(f"  • {directory}")

    def print_validation_results(self, results: dict[str, Any]) -> Any:
        """打印验证结果"""
        logger.info("\n✅ 文档验证结果")
        logger.info(f"🕐 验证时间: {results['validation_time']}")
        logger.info(f"📊 检查文件数: {results['total_files_checked']}")
        logger.info(f"✅ 有效文件: {results['valid_files']}")
        logger.info(f"❌ 无效文件: {results['invalid_files']}")
        logger.info(f"📈 总体评分: {results['overall_score']}/100")

        if results['issues']:
            logger.info("\n🚨 发现的问题:")
            for issue in results['issues'][:10]:  # 只显示前10个问题
                logger.info(f"  {issue}")

        if results['recommendations']:
            logger.info("\n💡 改进建议:")
            for recommendation in results['recommendations']:
                logger.info(f"  {recommendation}")

def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(description='Athena文档标准化工具')
    parser.add_argument('--scan', action='store_true', help='扫描所有文档')
    parser.add_argument('--validate', action='store_true', help='验证文档标准化程度')
    parser.add_argument('--standardize', help='标准化指定目录的README文件')
    parser.add_argument('--force', action='store_true', help='强制覆盖现有文件')
    parser.add_argument('--generate-template', choices=['readme', 'api'], help='生成文档模板')

    args = parser.parse_args()

    standardizer = DocumentationStandardizer()

    if args.scan or not any(vars(args).values()):
        # 默认执行扫描
        results = standardizer.scan_documentation()
        standardizer.print_scan_results(results)

    elif args.validate:
        results = standardizer.validate_documentation()
        standardizer.print_validation_results(results)

    elif args.standardize:
        success = standardizer.standardize_readme(args.standardize, args.force)
        if success:
            logger.info('✅ README标准化完成')
        else:
            logger.info('❌ README标准化失败')

    elif args.generate_template:
        standardizer.generate_template(args.generate_template)

if __name__ == '__main__':
    main()
