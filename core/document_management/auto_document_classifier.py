#!/usr/bin/env python3
from __future__ import annotations
"""
自动文档分类器

根据文档类型、内容、日期等信息自动将文档归类到正确的目录。

Author: 小诺·双鱼公主 💖
Version: 1.0.0
Created: 2026-01-07
"""

import re
import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class DocumentType(Enum):
    """文档类型枚举"""

    ARCHITECTURE = "architecture"  # 架构设计
    IMPLEMENTATION = "implementation"  # 实施集成
    REPORT = "report"  # 报告文档
    GUIDE = "guide"  # 使用指南
    OPTIMIZATION = "optimization"  # 优化文档
    REFERENCE = "reference"  # 参考资料
    PROJECT = "project"  # 项目文档
    BUSINESS = "business"  # 业务文档
    ARCHIVE = "archive"  # 归档文档


class DocumentCategory(Enum):
    """文档分类枚举"""

    # 架构设计
    SYSTEM_ARCHITECTURE = "01-architecture"
    STORAGE_ARCHITECTURE = "01-architecture/storage"

    # 实施集成
    INTEGRATION = "02-implementation"
    DEPLOYMENT = "02-implementation/deployment"
    MIGRATION = "02-implementation/migration"

    # 报告文档
    REPORT_CURRENT = "03-reports/{year}-{month:02d}"
    REPORT_ARCHIVE = "03-reports/archive"

    # 使用指南
    USER_GUIDE = "04-guides/user-guides"
    INSTALLATION = "04-guides/installation"
    QUICK_START = "04-guides/quick-start"

    # 优化文档
    OPTIMIZATION_PHASE = "05-optimization/phases"
    OPTIMIZATION_DEPRECATED = "05-optimization/deprecated"

    # 参考资料
    API_REFERENCE = "06-reference/api"
    TECHNICAL = "06-reference/technical"
    STANDARDS = "06-reference/standards"

    # 项目文档
    PROJECT_PATENTS = "07-projects/patents"
    PROJECT_KG = "07-projects/knowledge-graph"
    PROJECT_NLP = "07-projects/nlp"
    PROJECT_TOOL_GOV = "07-projects/tool-governance"
    PROJECT_PRODUCTION = "07-projects/production"

    # 业务文档
    BUSINESS_CLIENT = "08-business/clients"
    BUSINESS_ARTICLE = "08-business/articles"

    # 归档
    ARCHIVE_DEPRECATED = "99-archive/deprecated"
    ARCHIVE_OLD_OPTIMIZATION = "99-archive/old-optimization"


@dataclass
class ClassificationRule:
    """分类规则"""

    name: str  # 规则名称
    description: str  # 规则描述
    category: DocumentCategory  # 目标分类
    priority: int = 0  # 优先级 (数字越大越优先)
    patterns: list[str] = field(default_factory=list)  # 文件名模式
    keywords: list[str] = field(default_factory=list)  # 内容关键词
    date_pattern: str | None = None  # 日期模式 (如: %Y%m%d)
    custom_classifier: Callable | None = None  # 自定义分类函数

    def matches_filename(self, filename: str) -> bool:
        """检查文件名是否匹配"""
        return any(re.match(pattern, filename, re.IGNORECASE) for pattern in self.patterns)

    def matches_content(self, content: str) -> bool:
        """检查内容是否匹配"""
        if not self.keywords:
            return True
        content_lower = content.lower()
        return any(keyword.lower() in content_lower for keyword in self.keywords)

    def extract_date(self, filename: str) -> datetime | None:
        """从文件名提取日期"""
        if not self.date_pattern:
            return None

        # 尝试从文件名中提取日期
        for pattern in self.patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match and match.groups():
                try:
                    date_str = match.group(1) if match.groups() else filename
                    return datetime.strptime(date_str, self.date_pattern)
                except (ValueError, IndexError):
                    continue
        return None


@dataclass
class ClassificationResult:
    """分类结果"""

    success: bool  # 是否成功
    source_path: Path  # 源文件路径
    target_path: Path | None  # 目标文件路径
    category: DocumentCategory | None  # 分类
    rule_name: str | None  # 使用的规则名称
    confidence: float = 0.0  # 置信度 (0.0-1.0)
    error_message: str | None = None  # 错误消息


class AutoDocumentClassifier:
    """
    自动文档分类器

    功能:
    1. 根据文件名模式自动分类
    2. 根据内容关键词智能分类
    3. 提取日期信息进行时间归档
    4. 支持自定义分类规则
    5. 提供分类置信度评分
    """

    def __init__(self, docs_root: Path | None = None):
        """
        初始化分类器

        Args:
            docs_root: 文档根目录,默认为当前工作目录下的docs
        """
        if docs_root is None:
            docs_root = Path.cwd() / "docs"

        self.docs_root = Path(docs_root)
        self.rules: list[ClassificationRule] = []
        self.stats = {
            "total_processed": 0,
            "successfully_classified": 0,
            "failed": 0,
            "by_category": {},
        }

        # 初始化默认规则
        self._init_default_rules()

        logger.info(f"AutoDocumentClassifier initialized with docs_root: {self.docs_root}")

    def _init_default_rules(self) -> Any:
        """初始化默认分类规则"""
        datetime.now()

        # 1. 架构文档规则
        self.rules.extend(
            [
                ClassificationRule(
                    name="architecture_design",
                    description="系统架构设计文档",
                    category=DocumentCategory.SYSTEM_ARCHITECTURE,
                    priority=10,
                    patterns=[r".*architecture.*", r".*ARCHITECTURE.*"],
                    keywords=["architecture", "架构", "系统设计", "tech stack", "技术栈"],
                ),
                ClassificationRule(
                    name="storage_architecture",
                    description="存储架构文档",
                    category=DocumentCategory.STORAGE_ARCHITECTURE,
                    priority=9,
                    patterns=[r".*storage.*architecture.*", r"STORAGE_ARCHITECTURE"],
                    keywords=["storage", "存储", "数据库", "vector", "向量"],
                ),
            ]
        )

        # 2. 实施集成规则
        self.rules.extend(
            [
                ClassificationRule(
                    name="integration_guide",
                    description="集成指南",
                    category=DocumentCategory.INTEGRATION,
                    priority=8,
                    patterns=[r".*integration.*", r".*集成.*"],
                    keywords=["integration", "集成", "连接", "对接"],
                ),
                ClassificationRule(
                    name="deployment_guide",
                    description="部署指南",
                    category=DocumentCategory.DEPLOYMENT,
                    priority=8,
                    patterns=[r".*deployment.*", r".*部署.*"],
                    keywords=["deployment", "部署", "生产环境", "production"],
                ),
                ClassificationRule(
                    name="migration_guide",
                    description="迁移指南",
                    category=DocumentCategory.MIGRATION,
                    priority=8,
                    patterns=[r".*migration.*", r".*迁移.*"],
                    keywords=["migration", "迁移", "升级", "upgrade"],
                ),
            ]
        )

        # 3. 报告文档规则
        self.rules.extend(
            [
                ClassificationRule(
                    name="current_report",
                    description="当前月份报告",
                    category=DocumentCategory.REPORT_CURRENT,
                    priority=10,
                    patterns=[r".*_REPORT\.md$", r".*_report\.md$", r".*_SUMMARY\.md$"],
                    keywords=["report", "报告", "summary", "总结"],
                    date_pattern="%Y%m%d",
                ),
                ClassificationRule(
                    name="optimization_report",
                    description="优化报告",
                    category=DocumentCategory.OPTIMIZATION_PHASE,
                    priority=9,
                    patterns=[r".*optimization.*report.*", r".*优化.*报告.*"],
                    keywords=["optimization", "优化", "performance", "性能"],
                ),
            ]
        )

        # 4. 使用指南规则
        self.rules.extend(
            [
                ClassificationRule(
                    name="user_guide",
                    description="用户指南",
                    category=DocumentCategory.USER_GUIDE,
                    priority=7,
                    patterns=[r".*user.*guide.*", r".*用户.*指南.*", r".*usage.*guide.*"],
                    keywords=["user guide", "用户指南", "usage", "使用"],
                ),
                ClassificationRule(
                    name="installation_guide",
                    description="安装指南",
                    category=DocumentCategory.INSTALLATION,
                    priority=7,
                    patterns=[r".*setup.*", r".*installation.*", r".*安装.*"],
                    keywords=["setup", "installation", "安装", "environment", "环境"],
                ),
                ClassificationRule(
                    name="quick_start",
                    description="快速开始",
                    category=DocumentCategory.QUICK_START,
                    priority=7,
                    patterns=[r".*quick.*start.*", r".*quickstart.*"],
                    keywords=["quick start", "快速开始", "快速入门"],
                ),
            ]
        )

        # 5. 优化文档规则
        self.rules.extend(
            [
                ClassificationRule(
                    name="phase_optimization",
                    description="阶段优化文档",
                    category=DocumentCategory.OPTIMIZATION_PHASE,
                    priority=8,
                    patterns=[r"phase[0-9].*", r"PHASE[0-9].*"],
                    keywords=["phase", "阶段", "optimization", "优化"],
                ),
            ]
        )

        # 6. 参考资料规则
        self.rules.extend(
            [
                ClassificationRule(
                    name="api_reference",
                    description="API参考",
                    category=DocumentCategory.API_REFERENCE,
                    priority=6,
                    patterns=[r"api_.*", r"API_.*"],
                    keywords=["api", "接口", "endpoint"],
                ),
                ClassificationRule(
                    name="technical_reference",
                    description="技术参考",
                    category=DocumentCategory.TECHNICAL,
                    priority=6,
                    patterns=[r".*technical.*", r".*TECHNICAL.*"],
                    keywords=["technical", "技术", "standard", "标准"],
                ),
                ClassificationRule(
                    name="standards",
                    description="标准文档",
                    category=DocumentCategory.STANDARDS,
                    priority=6,
                    patterns=[r"CHECKLIST", r"TASKS", r"STANDARDS"],
                    keywords=["checklist", "标准", "规范", "guideline"],
                ),
            ]
        )

        # 7. 项目文档规则
        self.rules.extend(
            [
                ClassificationRule(
                    name="patent_project",
                    description="专利项目文档",
                    category=DocumentCategory.PROJECT_PATENTS,
                    priority=9,
                    patterns=[r".*专利.*", r".*patent.*"],
                    keywords=["patent", "专利", "检索", "分析"],
                ),
                ClassificationRule(
                    name="knowledge_graph_project",
                    description="知识图谱项目",
                    category=DocumentCategory.PROJECT_KG,
                    priority=9,
                    patterns=[r".*knowledge.*graph.*", r".*nebula.*"],
                    keywords=["knowledge graph", "知识图谱", "nebula", "图数据库"],
                ),
                ClassificationRule(
                    name="nlp_project",
                    description="NLP项目",
                    category=DocumentCategory.PROJECT_NLP,
                    priority=9,
                    patterns=[r".*nlp.*", r".*NLP.*", r".*intent.*"],
                    keywords=["nlp", "intent", "意图", "classification", "分类"],
                ),
                ClassificationRule(
                    name="tool_governance_project",
                    description="工具治理项目",
                    category=DocumentCategory.PROJECT_TOOL_GOV,
                    priority=9,
                    patterns=[r".*tool.*governance.*"],
                    keywords=["tool governance", "工具治理", "tool management"],
                ),
            ]
        )

        # 按优先级排序
        self.rules.sort(key=lambda r: r.priority, reverse=True)

        logger.info(f"Initialized {len(self.rules)} classification rules")

    def classify_file(
        self,
        file_path: Path,
        read_content: bool = True,
        move_file: bool = True,
        dry_run: bool = False,
    ) -> ClassificationResult:
        """
        分类单个文件

        Args:
            file_path: 文件路径
            read_content: 是否读取文件内容进行分类
            move_file: 是否移动文件
            dry_run: 是否为演练模式 (不实际移动文件)

        Returns:
            ClassificationResult: 分类结果
        """
        if not file_path.exists():
            return ClassificationResult(
                success=False,
                source_path=file_path,
                target_path=None,
                category=None,
                rule_name=None,
                error_message=f"File not found: {file_path}",
            )

        filename = file_path.name
        content = ""

        # 读取文件内容
        if read_content:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                logger.warning(f"Failed to read file {file_path}: {e}")
                content = ""

        # 尝试匹配规则
        matched_rule = None
        max_confidence = 0.0

        for rule in self.rules:
            # 检查文件名匹配
            if rule.matches_filename(filename):
                confidence = 0.8
                # 检查内容匹配,提高置信度
                if content and rule.matches_content(content):
                    confidence = 0.95

                if confidence > max_confidence:
                    matched_rule = rule
                    max_confidence = confidence

        # 如果没有匹配的规则,使用默认分类
        if not matched_rule:
            logger.warning(f"No matching rule for {filename}, using default")
            return ClassificationResult(
                success=False,
                source_path=file_path,
                target_path=None,
                category=None,
                rule_name=None,
                confidence=0.0,
                error_message="No matching classification rule found",
            )

        # 确定目标路径
        target_category = matched_rule.category.value

        # 如果是报告类别,需要替换日期占位符
        if "{year}" in target_category:
            current_date = datetime.now()
            target_category = target_category.format(
                year=current_date.year, month=current_date.month
            )

        target_path = self.docs_root / target_category / filename

        # 移动文件
        if move_file and not dry_run:
            try:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(file_path), str(target_path))
                logger.info(f"Moved {filename} to {target_category}/")
            except Exception as e:
                return ClassificationResult(
                    success=False,
                    source_path=file_path,
                    target_path=target_path,
                    category=matched_rule.category,
                    rule_name=matched_rule.name,
                    confidence=max_confidence,
                    error_message=str(e),
                )

        # 更新统计
        self.stats["total_processed"] += 1
        if matched_rule.category.name not in self.stats["by_category"]:
            self.stats["by_category"][matched_rule.category.name] = 0
        self.stats["by_category"][matched_rule.category.name] += 1

        return ClassificationResult(
            success=True,
            source_path=file_path,
            target_path=target_path,
            category=matched_rule.category,
            rule_name=matched_rule.name,
            confidence=max_confidence,
        )

    def classify_directory(
        self,
        source_dir: Path,
        pattern: str = "*.md",
        read_content: bool = False,
        move_files: bool = True,
        dry_run: bool = False,
    ) -> list[ClassificationResult]:
        """
        分类整个目录的文件

        Args:
            source_dir: 源目录
            pattern: 文件匹配模式
            read_content: 是否读取文件内容
            move_files: 是否移动文件
            dry_run: 是否为演练模式

        Returns:
            list[ClassificationResult]: 分类结果列表
        """
        source_dir = Path(source_dir)
        results = []

        for file_path in source_dir.glob(pattern):
            if file_path.is_file():
                result = self.classify_file(
                    file_path=file_path,
                    read_content=read_content,
                    move_file=move_files,
                    dry_run=dry_run,
                )
                results.append(result)

        return results

    def add_rule(self, rule: ClassificationRule) -> None:
        """添加自定义分类规则"""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        logger.info(f"Added new rule: {rule.name}")

    def get_statistics(self) -> dict:
        """获取分类统计信息"""
        return {
            "total_rules": len(self.rules),
            "total_processed": self.stats["total_processed"],
            "successfully_classified": sum(1 for r in self.stats.get("by_category", {}).values()),
            "by_category": self.stats.get("by_category", {}),
        }

    def print_statistics(self) -> Any:
        """打印分类统计信息"""
        stats = self.get_statistics()
        print("\n" + "=" * 50)
        print("📊 文档分类统计")
        print("=" * 50)
        print(f"总规则数: {stats['total_rules']}")
        print(f"已处理文件: {stats['total_processed']}")
        print(f"成功分类: {stats['successfully_classified']}")
        print("\n按分类统计:")
        for category, count in stats["by_category"].items():
            print(f"  {category}: {count} 个文件")
        print("=" * 50 + "\n")


# 便捷函数
def classify_document(
    file_path: str | None = None, docs_root: str | None = None, move_file: bool = True, dry_run: bool = False
) -> ClassificationResult:
    """
    便捷函数:分类单个文档

    Args:
        file_path: 文件路径
        docs_root: 文档根目录
        move_file: 是否移动文件
        dry_run: 是否为演练模式

    Returns:
        ClassificationResult: 分类结果
    """
    classifier = AutoDocumentClassifier(docs_root=Path(docs_root) if docs_root else None)
    return classifier.classify_file(file_path=Path(file_path), move_file=move_file, dry_run=dry_run)


def classify_documents_in_directory(
    source_dir: str,
    docs_root: str | None = None,
    pattern: str = "*.md",
    move_files: bool = True,
    dry_run: bool = False,
) -> list[ClassificationResult]:
    """
    便捷函数:分类目录中的所有文档

    Args:
        source_dir: 源目录
        docs_root: 文档根目录
        pattern: 文件匹配模式
        move_files: 是否移动文件
        dry_run: 是否为演练模式

    Returns:
        list[ClassificationResult]: 分类结果列表
    """
    classifier = AutoDocumentClassifier(docs_root=Path(docs_root) if docs_root else None)
    results = classifier.classify_directory(
        source_dir=Path(source_dir),
        pattern=pattern,
        read_content=False,
        move_files=move_files,
        dry_run=dry_run,
    )
    classifier.print_statistics()
    return results


# 示例用法
if __name__ == "__main__":
    # 示例1: 分类单个文件
    result = classify_document(
        file_path="/Users/xujian/Athena工作平台/docs/SYSTEM_ARCHITECTURE.md",
        move_file=False,  # 不实际移动,只是测试
        dry_run=True,
    )
    print(f"分类结果: {result.category}, 置信度: {result.confidence}")

    # 示例2: 分类整个目录
    results = classify_documents_in_directory(
        source_dir="/Users/xujian/Athena工作平台/docs",
        pattern="*.md",
        move_files=False,
        dry_run=True,
    )
