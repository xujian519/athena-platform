#!/usr/bin/env python3
"""
报告自动分类集成器

将报告生成系统与自动文档分类器集成,实现报告生成后自动归类。

Author: 小诺·双鱼公主 💖
Version: 1.0.0
Created: 2026-01-07
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union


# 导入自动文档分类器
from core.document_management.auto_document_classifier import (
    AutoDocumentClassifier,
    ClassificationResult,
    ClassificationRule,
    DocumentCategory,
)

logger = logging.getLogger(__name__)


@dataclass
class ReportMetadata:
    """报告元数据"""

    title: str  # 报告标题
    report_type: str  # 报告类型
    author: str  # 作者
    creation_date: datetime  # 创建日期
    tags: list = None  # 标签
    summary: str = ""  # 摘要
    category_hint: str | None = None  # 分类提示
    priority: int = 0  # 优先级


class ReportAutoClassifier:
    """
    报告自动分类集成器

    提供报告生成后的自动分类功能:
    1. 生成报告时自动添加元数据
    2. 根据元数据和内容自动分类
    3. 自动移动到正确的目录
    4. 记录分类历史
    """

    def __init__(self, docs_root: Path | None = None):
        """
        初始化报告自动分类器

        Args:
            docs_root: 文档根目录
        """
        if docs_root is None:
            docs_root = Path.cwd() / "docs"

        self.docs_root = Path(docs_root)
        self.classifier = AutoDocumentClassifier(docs_root=docs_root)
        self.classification_history = []

        logger.info(f"ReportAutoClassifier initialized with docs_root: {self.docs_root}")

    def generate_report_with_auto_classification(
        self,
        content: str,
        metadata: ReportMetadata,
        filename: str | None = None,
        auto_classify: bool = True,
        save_to_temp: bool = False,
    ) -> ClassificationResult:
        """
        生成报告并自动分类

        Args:
            content: 报告内容
            metadata: 报告元数据
            filename: 文件名 (如果为None,则自动生成)
            auto_classify: 是否自动分类
            save_to_temp: 是否先保存到临时目录

        Returns:
            ClassificationResult: 分类结果
        """
        # 生成文件名
        if filename is None:
            filename = self._generate_filename(metadata)

        # 添加元数据到内容
        full_content = self._add_metadata_to_content(content, metadata)

        # 确定保存路径
        if save_to_temp:
            save_path = self.docs_root / ".temp" / filename
        else:
            save_path = self.docs_root / filename

        # 保存文件
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(full_content)

        logger.info(f"Report saved to: {save_path}")

        # 自动分类
        if auto_classify:
            # 如果有分类提示,添加临时规则
            if metadata.category_hint:
                self._add_temporary_rule(metadata)

            result = self.classifier.classify_file(
                file_path=save_path, read_content=True, move_file=True
            )

            # 记录分类历史
            self.classification_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "filename": filename,
                    "metadata": metadata,
                    "result": result,
                }
            )

            return result
        else:
            return ClassificationResult(
                success=True,
                source_path=save_path,
                target_path=save_path,
                category=None,
                rule_name=None,
                confidence=1.0,
            )

    def _generate_filename(self, metadata: ReportMetadata) -> str:
        """
        根据元数据生成文件名

        Args:
            metadata: 报告元数据

        Returns:
            str: 生成的文件名
        """
        # 基础文件名
        base_name = metadata.title.upper().replace(" ", "_")

        # 添加日期
        date_str = metadata.creation_date.strftime("%Y%m%d")

        # 添加类型
        {
            "investigation": "INVESTIGATION_REPORT",
            "optimization": "OPTIMIZATION_REPORT",
            "integration": "INTEGRATION_REPORT",
            "deployment": "DEPLOYMENT_REPORT",
            "cleanup": "CLEANUP_REPORT",
            "analysis": "ANALYSIS_REPORT",
            "completion": "COMPLETION_REPORT",
        }.get(metadata.report_type.lower(), "REPORT")

        # 组合文件名
        filename = f"{base_name}_{date_str}.md"

        return filename

    def _add_metadata_to_content(self, content: str, metadata: ReportMetadata) -> str:
        """
        添加元数据到报告内容

        Args:
            content: 原始内容
            metadata: 元数据

        Returns:
            str: 添加了元数据的内容
        """
        metadata_md = f"""---
# 报告元数据

**标题**: {metadata.title}
**类型**: {metadata.report_type}
**作者**: {metadata.author}
**创建日期**: {metadata.creation_date.strftime('%Y-%m-%d %H:%M:%S')}
**标签**: {', '.join(metadata.tags) if metadata.tags else '无'}
**分类**: {metadata.category_hint or '自动分类'}

---

"""

        return metadata_md + content

    def _add_temporary_rule(self, metadata: ReportMetadata) -> Any:
        """
        根据元数据添加临时分类规则

        Args:
            metadata: 报告元数据
        """
        # 根据分类提示创建临时规则
        category_map = {
            "architecture": DocumentCategory.SYSTEM_ARCHITECTURE,
            "implementation": DocumentCategory.INTEGRATION,
            "report": DocumentCategory.REPORT_CURRENT,
            "guide": DocumentCategory.USER_GUIDE,
            "optimization": DocumentCategory.OPTIMIZATION_PHASE,
            "reference": DocumentCategory.TECHNICAL,
            "project": DocumentCategory.PROJECT_PATENTS,
        }

        target_category = category_map.get(metadata.category_hint.lower())
        if target_category:
            temp_rule = ClassificationRule(
                name=f"temp_{metadata.title}",
                description=f"Temporary rule for {metadata.title}",
                category=target_category,
                priority=100,  # 最高优先级
                patterns=[re.escape(metadata.title)],
            )
            self.classifier.add_rule(temp_rule)

    def classify_existing_reports(
        self, source_dir: Path | None = None, pattern: str = "*.md", dry_run: bool = False
    ) -> list[ClassificationResult]:
        """
        分类已存在的报告

        Args:
            source_dir: 源目录
            pattern: 文件匹配模式
            dry_run: 是否为演练模式

        Returns:
            list[ClassificationResult]: 分类结果列表
        """
        if source_dir is None:
            source_dir = self.docs_root

        results = self.classifier.classify_directory(
            source_dir=source_dir,
            pattern=pattern,
            read_content=True,
            move_files=not dry_run,
            dry_run=dry_run,
        )

        return results

    def get_classification_history(self) -> list:
        """获取分类历史记录"""
        return self.classification_history

    def get_statistics(self) -> dict:
        """获取统计信息"""
        return self.classifier.get_statistics()


# 便捷函数
def create_report_with_auto_classification(
    content: str,
    title: str,
    report_type: str,
    author: str = "小诺·双鱼公主",
    tags: list | None = None,
    category_hint: str | None = None,
    docs_root: str | None = None,
) -> ClassificationResult:
    """
    便捷函数:创建报告并自动分类

    Args:
        content: 报告内容
        title: 报告标题
        report_type: 报告类型
        author: 作者
        tags: 标签
        category_hint: 分类提示
        docs_root: 文档根目录

    Returns:
        ClassificationResult: 分类结果
    """
    metadata = ReportMetadata(
        title=title,
        report_type=report_type,
        author=author,
        creation_date=datetime.now(),
        tags=tags or [],
        category_hint=category_hint,
    )

    classifier = ReportAutoClassifier(docs_root=Path(docs_root) if docs_root else None)

    return classifier.generate_report_with_auto_classification(content=content, metadata=metadata)


# 装饰器:用于报告生成函数
def auto_classify_report(
    title: str | None = None,
    report_type: str = "report",
    author: str = "小诺·双鱼公主",
    category_hint: str | None = None,
    docs_root: str | None = None,
):
    """
    装饰器:自动分类报告

    用法:
    @auto_classify_report(
        title="文档清理完成报告",
        report_type="cleanup",
        category_hint="report"
    )
    def generate_cleanup_report():
        return "# 清理报告\\n\\n清理完成!"
    """

    def decorator(func) -> None:
        def wrapper(*args, **kwargs) -> Any:
            # 调用原函数生成内容
            content = func(*args, **kwargs)

            # 使用函数名作为标题(如果没有提供)
            report_title = title or func.__name__.replace("_", " ").title()

            # 创建报告并自动分类
            result = create_report_with_auto_classification(
                content=content,
                title=report_title,
                report_type=report_type,
                author=author,
                category_hint=category_hint,
                docs_root=docs_root,
            )

            logger.info(f"Report '{report_title}' auto-classified to: {result.target_path}")

            return content, result

        return wrapper

    return decorator


# 示例用法
if __name__ == "__main__":
    # 示例1: 使用便捷函数
    content = """
# 文档清理完成报告

## 清理成果
- 清理率: 96.2%
- 归档文件: 172个
    """

    result = create_report_with_auto_classification(
        content=content,
        title="DOCS_CLEANUP_COMPLETED",
        report_type="cleanup",
        category_hint="report",
        docs_root="/Users/xujian/Athena工作平台/docs",
    )

    print(f"报告已保存并分类到: {result.target_path}")

    # 示例2: 使用装饰器
    @auto_classify_report(
        title="系统优化报告", report_type="optimization", category_hint="optimization"
    )
    def generate_optimization_report() -> Any:
        return "# 优化报告\\n\\n系统优化完成!"

    content, result = generate_optimization_report()
    print(f"报告已保存并分类到: {result.target_path}")
