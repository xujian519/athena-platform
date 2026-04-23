#!/usr/bin/env python3
"""
客户文件整理脚本
Organize Customer Files Script

功能：
1. 按文件类型分类整理
2. 删除临时和重复文件
3. 规范文件命名
4. 创建清晰的目录结构
5. 生成整理报告

Author: Athena Team
Date: 2026-02-25
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class CustomerFileOrganizer:
    """客户文件整理器"""

    def __init__(self, source_dir: str):
        self.source_dir = Path(source_dir)
        self.backup_dir = self.source_dir.parent / f"{self.source_dir.name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 统计信息
        self.stats = {
            "total_files": 0,
            "moved_files": 0,
            "deleted_files": 0,
            "created_dirs": 0,
            "errors": [],
        }

    def analyze(self) -> dict[str, list[Path]:
        """分析当前文件结构"""
        logger.info(f"📂 分析目录: {self.source_dir}")
        logger.info("=" * 60)

        categories = {
            "临时文件": [],
            "专利文档": [],
            "专利PDF": [],
            "分析报告": [],
            "项目文档": [],
            "存档文件": [],
            "合同文件": [],
            "数据文件": [],
            "脚本文件": [],
            "其他文档": [],
        }

        # 扫描所有文件
        for item in self.source_dir.rglob("*"):
            if item.is_file():
                self.stats["total_files"] += 1
                category = self._categorize_file(item)
                categories[category].append(item)

        # 打印分析结果
        for category, files in categories.items():
            if files:
                logger.info(f"\n{category} ({len(files)}个):")
                for f in sorted(files):
                    logger.info(f"  - {f.relative_to(self.source_dir)}")

        return categories

    def _categorize_file(self, file_path: Path) -> str:
        """分类文件"""
        name = file_path.name.lower()
        ext = file_path.suffix.lower()
        parent = file_path.parent.name

        # 临时文件
        if (name.startswith(".") or
            name.startswith("save") or
            ext in [".tmp", ".bak"] or
            "temp" in name.lower()):
            return "临时文件"

        # 专利PDF
        if parent == "专利原文PDF" and ext == ".pdf":
            return "专利PDF"

        # 专利文档
        if "专利" in name and ext in [".md", ".docx", ".doc"]:
            return "专利文档"

        # 分析报告
        if any(keyword in name for keyword in ["分析", "报告", "可行性", "深度分析"]):
            return "分析报告"

        # 项目文档
        if parent == "12.25" and ext in [".docx", ".pptx", ".doc"]:
            return "项目文档"

        # 存档文件
        if parent.startswith("存档_"):
            return "存档文件"

        # 合同文件
        if "合同" in name and ext == ".pdf":
            return "合同文件"

        # 数据文件
        if ext in [".json", ".txt"]:
            return "数据文件"

        # 脚本文件
        if ext == ".py" or name.endswith(".py"):
            return "脚本文件"

        # DWG和备份文件
        if ext in [".dwl", ".bak"]:
            return "临时文件"

        # 其他文档
        if ext in [".md", ".docx", ".doc", ".pdf"]:
            return "其他文档"

        return "其他文档"

    def create_target_structure(self) -> Path:
        """创建目标目录结构"""
        logger.info("\n🏗️  创建目录结构...")
        logger.info("-" * 60)

        # 创建新的目录结构
        target_structure = {
            "01_项目文档": {
                "项目背景": "",
                "可行性分析": "",
                "技术方案": "",
                "成本分析": "",
                "其他资料": "",
            },
            "02_专利管理": {
                "专利原文": "专利原文PDF",
                "专利撰写": {
                    "浅埋供热管道阳极地床装置": "",
                    "其他专利": "",
                },
                "专利分析": {
                    "对比分析": "",
                    "深度分析": "",
                    "可行性分析": "",
                },
                "专利检索": "",
                "存档资料": "存档_20260107_111436",
            },
            "03_合同文件": "",
            "04_数据文件": {
                "检索结果": "",
                "分析结果": "专利分析结果",
            },
            "05_工作脚本": "",
            "99_临时文件": "",
        }

        for dir_path, _description in self._flatten_structure(target_structure).items():
            full_path = self.source_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            self.stats["created_dirs"] += 1

        logger.info("✅ 目录结构创建完成")
        return self.source_dir

    def _flatten_structure(self, structure: dict, prefix: str = "") -> dict[str, str]:
        """展平嵌套结构"""
        result = {}

        for key, value in structure.items():
            full_path = f"{prefix}/{key}" if prefix else key

            if isinstance(value, dict):
                result.update(self._flatten_structure(value, full_path))
            elif isinstance(value, str) and value:
                result[full_path] = value
            else:
                result[full_path] = ""

        return result

    def organize(self, dry_run: bool = False) -> bool:
        """执行整理"""
        logger.info("\n" + "=" * 60)
        logger.info("🚀 开始整理文件")
        logger.info("=" * 60)

        # 1. 备份原目录
        if not dry_run:
            logger.info(f"\n📦 备份原目录到: {self.backup_dir}")
            try:
                shutil.copytree(self.source_dir, self.backup_dir, ignore=shutil.ignore_patterns('.DS_Store'))
            except Exception as e:
                logger.warning(f"⚠️ 备份失败: {e}")

        # 2. 扫描并分类文件
        categories = self.analyze()

        # 3. 创建目标结构
        self.create_target_structure()

        # 4. 移动和整理文件
        if dry_run:
            logger.info("\n🔍 预览模式 - 将执行以下操作:")
        else:
            logger.info("\n📁 开始移动文件...")

        self._organize_by_category(categories, dry_run)

        # 5. 删除临时文件
        self._cleanup_temp_files(dry_run)

        # 6. 创建索引文件
        if not dry_run:
            self._create_index_files()

        # 7. 生成报告
        self._generate_report(dry_run)

        return True

    def _organize_by_category(self, categories: dict[str, list[Path], dry_run: bool):
        """按分类整理文件"""

        # 临时文件 - 删除
        temp_files = categories.get("临时文件", [])
        for file in temp_files:
            if dry_run:
                logger.info(f"  🗑️ 删除: {file.relative_to(self.source_dir)}")
            else:
                try:
                    file.unlink()
                    self.stats["deleted_files"] += 1
                except Exception as e:
                    self.stats["errors"].append(f"删除失败 {file}: {e}")

        # 专利PDF - 移动到 02_专利管理/专利原文
        patent_pdfs = categories.get("专利PDF", [])
        for file in patent_pdfs:
            target = self.source_dir / "02_专利管理/专利原文" / file.name
            if dry_run:
                logger.info(f"  📄 移动: {file.relative_to(self.source_dir)} -> 02_专利管理/专利原文/")
            else:
                self._move_file(file, target)

        # 专利文档 - 按专利名分类
        patent_docs = categories.get("专利文档", [])
        self._organize_patent_documents(patent_docs, dry_run)

        # 分析报告
        analysis_reports = categories.get("分析报告", [])
        for file in analysis_reports:
            if "对比分析" in file.name or "专利对比" in file.name:
                target = self.source_dir / "02_专利管理/专利分析/对比分析" / file.name
            elif "深度分析" in file.name or "新颖性创造性" in file.name:
                target = self.source_dir / "02_专利管理/专利分析/深度分析" / file.name
            elif "可行性" in file.name:
                target = self.source_dir / "02_专利管理/专利分析/可行性分析" / file.name
            else:
                target = self.source_dir / "02_专利管理/专利分析/其他分析" / file.name

            if dry_run:
                logger.info(f"  📄 移动: {file.relative_to(self.source_dir)} -> {target.relative_to(self.source_dir).parent}")
            else:
                self._move_file(file, target)

        # 项目文档
        project_docs = categories.get("项目文档", [])
        for file in project_docs:
            if "成本核算" in file.name or "成本分析" in file.name:
                target = self.source_dir / "01_项目文档/成本分析" / file.name
            elif "创新创效" in file.name or "评比" in file.name:
                target = self.source_dir / "01_项目文档/其他资料" / file.name
            elif "技术方案" in file.name or "浅埋供热" in file.name:
                target = self.source_dir / "01_项目文档/技术方案" / file.name
            else:
                target = self.source_dir / "01_项目文档/项目背景" / file.name

            if dry_run:
                logger.info(f"  📄 移动: {file.relative_to(self.source_dir)} -> {target.relative_to(self.source_dir).parent}")
            else:
                self._move_file(file, target)

        # 存档文件 - 保持原结构
        archive_files = categories.get("存档文件", [])
        for file in archive_files:
            if "存档_20260107_111436" not in str(file.parent):
                target = self.source_dir / "02_专利管理/存档资料/存档_20260107_111436" / file.name
            else:
                target = None  # 已经在正确位置

            if target:
                if dry_run:
                    logger.info(f"  📄 移动: {file.relative_to(self.source_dir)} -> 存档资料/")
                else:
                    self._move_file(file, target)

        # 合同文件
        contracts = categories.get("合同文件", [])
        for file in contracts:
            target = self.source_dir / "03_合同文件" / file.name
            if dry_run:
                logger.info(f"  📄 移动: {file.relative_to(self.source_dir)} -> 03_合同文件/")
            else:
                self._move_file(file, target)

        # 数据文件
        data_files = categories.get("数据文件", [])
        for file in data_files:
            if "检索结果" in file.name or "patent_search" in file.name:
                target = self.source_dir / "04_数据文件/检索结果" / file.name
            elif "分析结果" in file.name or "专利分析" in file.name or "ocr" in file.name:
                target = self.source_dir / "04_数据文件/分析结果" / file.name
            else:
                target = self.source_dir / "04_数据文件/其他" / file.name

            if dry_run:
                logger.info(f"  📄 移动: {file.relative_to(self.source_dir)} -> 04_数据文件/")
            else:
                self._move_file(file, target)

        # 脚本文件
        scripts = categories.get("脚本文件", [])
        for file in scripts:
            target = self.source_dir / "05_工作脚本" / file.name
            if dry_run:
                logger.info(f"  📄 移动: {file.relative_to(self.source_dir)} -> 05_工作脚本/")
            else:
                self._move_file(file, target)

    def _organize_patent_documents(self, files: list[Path], dry_run: bool):
        """整理专利文档"""
        # 特殊处理浅埋供热管道专利
        device_patent_dir = self.source_dir / "02_专利管理/专利撰写/浅埋供热管道阳极地床装置"

        for file in files:
            if "浅埋供热管道" in file.name or "说明书附图" in file.name:
                target = device_patent_dir / file.name
            elif "专利1" in file.name:
                target = self.source_dir / "02_专利管理/专利撰写/其他专利/专利1" / file.name
            elif "专利2" in file.name:
                target = self.source_dir / "02_专利管理/专利撰写/其他专利/专利2" / file.name
            elif "专利3" in file.name:
                target = self.source_dir / "02_专利管理/专利撰写/其他专利/专利3" / file.name
            elif "专利4" in file.name:
                target = self.source_dir / "02_专利管理/专利撰写/其他专利/专利4" / file.name
            elif "专利5" in file.name:
                target = self.source_dir / "02_专利管理/专利撰写/其他专利/专利5" / file.name
            else:
                target = self.source_dir / "02_专利管理/专利撰写/其他专利" / file.name

            if dry_run:
                logger.info(f"  📄 移动: {file.relative_to(self.source_dir)} -> 02_专利管理/专利撰写/")
            else:
                self._move_file(file, target)

    def _cleanup_temp_files(self, dry_run: bool):
        """清理临时文件"""
        temp_patterns = [
            ".DS_Store",
            "*.tmp",
            "*.bak",
            "*.dwl",
            "save*.tmp",
        ]

        for pattern in temp_patterns:
            for file in self.source_dir.rglob(pattern):
                if file.is_file():
                    if dry_run:
                        logger.info(f"  🗑️ 删除: {file.relative_to(self.source_dir)}")
                    else:
                        try:
                            file.unlink()
                            self.stats["deleted_files"] += 1
                        except Exception as e:
                            self.stats["errors"].append(f"删除失败 {file}: {e}")

    def _move_file(self, source: Path, target: Path):
        """移动文件"""
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))
            self.stats["moved_files"] += 1
        except Exception as e:
            self.stats["errors"].append(f"移动失败 {source} -> {target}: {e}")

    def _create_index_files(self):
        """创建索引文件"""

        # 创建 README.md
        readme_content = f"""# 济南东盛热电有限公司 - 文件目录

**整理时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**整理人**: Athena 自动整理系统

## 📂 目录结构

### 01_项目文档
存放项目相关的文档，包括背景资料、可行性分析、技术方案、成本分析等。

- **项目背景**: 项目背景资料
- **可行性分析**: 项目可行性分析报告
- **技术方案**: 技术方案文档
- **成本分析**: 成本核算分析
- **其他资料**: 其他项目相关资料

### 02_专利管理
存放专利相关的所有文档和资料。

- **专利原文**: 专利原文PDF文件
- **专利撰写**:
  - **浅埋供热管道阳极地床装置**: 该专利的完整撰写文档
  - **其他专利**: 其他专利的撰写文档
- **专利分析**:
  - **对比分析**: 专利对比分析报告
  - **深度分析**: 专利深度分析报告
  - **可行性分析**: 专利可行性分析
- **专利检索**: 专利检索相关资料
- **存档资料**: 历史存档资料

### 03_合同文件
存放合同相关文档。

### 04_数据文件
存放各种数据文件，包括检索结果、分析结果等。

- **检索结果**: 专利检索结果数据
- **分析结果**: 专利分析结果数据

### 05_工作脚本
存放工作相关的脚本文件。

### 99_临时文件
临时文件，可定期清理。

---

## 📊 统计信息

- 总文件数: {self.stats['total_files']}
- 移动文件数: {self.stats['moved_files']}
- 删除文件数: {self.stats['deleted_files']}
- 创建目录数: {self.stats['created_dirs']}

---

💡 **提示**: 请保持目录结构整洁，新增文件请按分类放置。
"""

        readme_path = self.source_dir / "README.md"
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)

        logger.info("✅ README.md 已创建")

    def _generate_report(self, dry_run: bool):
        """生成整理报告"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 整理报告")
        logger.info("=" * 60)

        logger.info(f"\n总文件数: {self.stats['total_files']}")
        logger.info(f"移动文件数: {self.stats['moved_files']}")
        logger.info(f"删除文件数: {self.stats['deleted_files']}")
        logger.info(f"创建目录数: {self.stats['created_dirs']}")

        if self.stats['errors']:
            logger.info(f"\n⚠️ 错误 ({len(self.stats['errors'])}个):")
            for error in self.stats['errors']:
                logger.info(f"  - {error}")

        if dry_run:
            logger.info("\n🔍 预览模式 - 未执行实际操作")
            logger.info("\n💡 执行实际整理请运行:")
            logger.info(f"   python3 {__file__} organize --execute")
        else:
            logger.info("\n✅ 整理完成!")
            logger.info(f"\n💾 备份位置: {self.backup_dir}")
            logger.info("\n💡 如需恢复，请运行:")
            logger.info(f"   rm -rf {self.source_dir}")
            logger.info(f"   mv {self.backup_dir} {self.source_dir}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="整理客户文件")
    parser.add_argument("source", help="源目录路径")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不执行实际操作")
    parser.add_argument("--execute", action="store_true", help="执行整理")

    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        parser.print_help()
        return

    organizer = CustomerFileOrganizer(args.source)

    if args.dry_run:
        organizer.organize(dry_run=True)
    elif args.execute:
        organizer.organize(dry_run=False)


if __name__ == "__main__":
    main()
