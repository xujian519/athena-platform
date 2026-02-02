#!/usr/bin/env python3
"""
文档目录重组脚本
创建标准化的文档结构
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DocumentationRestructurer:
    """文档重组器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.doc_root = self.project_root / "documentation"
        self.moved_files = []

    def create_new_structure(self):
        """创建新的文档目录结构"""
        structure = {
            "api": {
                "_readme.md": "API文档说明",
                "openapi": "OpenAPI规范文件",
                "endpoints": "API端点说明",
                "examples": "API使用示例"
            },
            "architecture": {
                "_readme.md": "架构文档说明",
                "system-design": "系统设计文档",
                "components": "组件架构",
                "deployment": "部署架构",
                "diagrams": "架构图"
            },
            "guides": {
                "_readme.md": "指南文档说明",
                "getting-started": "快速开始",
                "installation": "安装指南",
                "configuration": "配置指南",
                "development": "开发指南",
                "deployment": "部署指南",
                "troubleshooting": "故障排除"
            },
            "reference": {
                "_readme.md": "参考文档说明",
                "glossary": "术语表",
                "adr": "架构决策记录",
                "faqs": "常见问题",
                "changelog": "更新日志"
            },
            "tutorials": {
                "_readme.md": "教程说明",
                "basic": "基础教程",
                "advanced": "高级教程",
                "examples": "示例代码",
                "workshops": "工作坊"
            },
            "security": {
                "_readme.md": "安全文档说明",
                "authentication": "认证机制",
                "authorization": "授权控制",
                "best-practices": "安全最佳实践",
                "vulnerabilities": "漏洞报告"
            },
            "database": {
                "_readme.md": "数据库文档",
                "schema": "数据库模式",
                "migrations": "迁移脚本",
                "queries": "查询示例"
            },
            "optimization": {
                "_readme.md": "优化文档",
                "performance": "性能优化",
                "code-quality": "代码质量",
                "refactoring": "重构记录"
            },
            "legacy": {
                "_readme.md": "旧版本文档",
                "old-docs": "历史文档",
                "archived": "已归档"
            }
        }

        # 创建目录结构
        for dir_name, contents in structure.items():
            dir_path = self.doc_root / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)

            # 创建README文件
            readme_path = dir_path / "_readme.md"
            if not readme_path.exists() and isinstance(contents, dict):
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(f"# {contents['_readme.md']}\n\n")

            # 创建子目录
            for sub_dir_name in contents:
                if sub_dir_name.startswith('_'):
                    continue
                (dir_path / sub_dir_name).mkdir(exist_ok=True)

        logger.info("✅ 新文档目录结构已创建")

    def migrate_existing_docs(self):
        """迁移现有文档到新结构"""
        # 定义迁移映射
        migration_map = {
            # API文档
            "docs/api": "api/endpoints",
            "api": "api",

            # 架构文档
            "core/architecture": "architecture/system-design",
            "architecture": "architecture",

            # 指南文档
            "core/guides": "guides",
            "guides": "guides",

            # 安全文档
            "security": "security",

            # 数据库文档
            "database": "database",

            # 优化文档
            "optimization": "optimization",

            # 研究文档
            "research": "legacy/old-docs/research",

            # 报告
            "reports": "legacy/old-docs/reports",
            "analysis": "legacy/old-docs/analysis",

            # 其他
            "fusion": "legacy/old-docs/fusion",
            "articles": "legacy/old-docs/articles",
            "notes": "legacy/old-docs/notes"
        }

        # 执行迁移
        for source, target in migration_map.items():
            source_path = self.doc_root / source
            target_path = self.doc_root / target

            if source_path.exists():
                # 移动文件
                if source_path.is_file():
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(source_path), str(target_path))
                    self.moved_files.append(f"{source} -> {target}")
                elif source_path.is_dir():
                    if target_path.exists():
                        # 合并目录
                        for item in source_path.iterdir():
                            shutil.move(str(item), str(target_path))
                        source_path.rmdir()
                    else:
                        shutil.move(str(source_path), str(target_path))
                    self.moved_files.append(f"{source} -> {target}")

        logger.info(f"✅ 迁移了 {len(self.moved_files)} 个文件/目录")

    def create_master_index(self):
        """创建文档主索引"""
        index_content = """# Athena工作平台文档

## 📚 文档导航

### [API文档](api/)
- [OpenAPI规范](api/openapi/)
- [API端点](api/endpoints/)
- [使用示例](api/examples/)

### [架构文档](architecture/)
- [系统设计](architecture/system-design/)
- [组件架构](architecture/components/)
- [部署架构](architecture/deployment/)

### [指南文档](guides/)
- [快速开始](guides/getting-started/)
- [安装指南](guides/installation/)
- [配置指南](guides/configuration/)
- [开发指南](guides/development/)

### [参考文档](reference/)
- [术语表](reference/glossary/)
- [架构决策记录](reference/adr/)
- [常见问题](reference/faqs/)

### [教程](tutorials/)
- [基础教程](tutorials/basic/)
- [高级教程](tutorials/advanced/)
- [示例代码](tutorials/examples/)

### [安全文档](security/)
- [认证机制](security/authentication/)
- [授权控制](security/authorization/)
- [安全最佳实践](security/best-practices/)

### [数据库文档](database/)
- [数据库模式](database/schema/)
- [迁移脚本](database/migrations/)

### [优化记录](optimization/)
- [性能优化](optimization/performance/)
- [代码质量](optimization/code-quality/)
- [重构记录](optimization/refactoring/)

## 📖 快速链接

### 核心系统
- [系统架构概览](architecture/system-design/overview.md)
- [API参考](api/endpoints/README.md)
- [部署指南](guides/deployment/production.md)

### 开发者指南
- [环境搭建](guides/getting-started/setup.md)
- [开发规范](guides/development/standards.md)
- [贡献指南](guides/development/contributing.md)

### 运维指南
- [监控告警](guides/deployment/monitoring.md)
- [故障排除](guides/troubleshooting/)
- [性能调优](optimization/performance/)

---

最后更新: {date}
维护者: Athena开发团队
""".format(date="2025-12-13")

        index_path = self.doc_root / "README.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)

        logger.info("✅ 文档主索引已创建")

    def create_api_docs_generator(self):
        """创建API文档生成工具"""
        generator_content = '''#!/usr/bin/env python3
"""
API文档自动生成工具
"""

import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

import uvicorn
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def generate_openapi_json(app: FastAPI, output_path: str):
    """生成OpenAPI JSON文件"""
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    import json
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(openapi_schema, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # 为每个服务生成OpenAPI文档
    services = [
        ("yunpat-agent", 8020, "YunPat专利代理服务"),
        ("browser-automation", 8030, "浏览器自动化服务"),
        ("autonomous-control", 8040, "自主控制服务"),
        # 添加更多服务...
    ]

    output_dir = Path(__file__).parent / "openapi"
    output_dir.mkdir(exist_ok=True)

    for service_name, port, description in services:
        # 这里需要导入实际的FastAPI应用
        # 暂时生成一个模板
        schema = {
            "openapi": "3.0.0",
            "info": {
                "title": description,
                "version": "1.0.0",
                "description": f"API documentation for {description}"
            },
            "paths": {}
        }

        output_file = output_dir / f"{service_name}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            import json
            json.dump(schema, f, ensure_ascii=False, indent=2)

        print(f"Generated API docs for {service_name}")
'''

        generator_path = self.doc_root / "api" / "generate_docs.py"
        with open(generator_path, 'w', encoding='utf-8') as f:
            f.write(generator_content)

        generator_path.chmod(0o755)
        logger.info("✅ API文档生成工具已创建")

    def run(self):
        """运行文档重组"""
        logger.info("🔧 开始文档目录重组...")

        # 1. 备份现有文档
        backup_path = self.doc_root.parent / "documentation_backup"
        if backup_path.exists():
            shutil.rmtree(backup_path)
        shutil.copytree(self.doc_root, backup_path)
        logger.info(f"📦 文档已备份到: {backup_path}")

        # 2. 创建新结构
        self.create_new_structure()

        # 3. 迁移现有文档
        self.migrate_existing_docs()

        # 4. 创建主索引
        self.create_master_index()

        # 5. 创建API文档生成工具
        self.create_api_docs_generator()

        logger.info("\n✅ 文档重组完成！")
        logger.info(f"📊 迁移了 {len(self.moved_files)} 个文件")
        logger.info(f"📁 新文档结构位于: {self.doc_root}")


def main():
    """主函数"""
    project_root = Path(__file__).parent.parent.parent
    restructurer = DocumentationRestructurer(str(project_root))

    try:
        restructurer.run()
    except Exception as e:
        logger.error(f"❌ 执行失败: {str(e)}")
        raise


if __name__ == "__main__":
    main()