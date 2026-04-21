#!/usr/bin/env python3
from __future__ import annotations
"""
审查意见文档完整性检查器
Office Action Document Completeness Checker

在步骤2（智能分析）之前，检查目标专利和对比文件是否齐备

作者: 小诺·双鱼公主
创建时间: 2026-01-24
版本: v0.1.2 "晨星初现"
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logger = setup_logging()


@dataclass
class DocumentStatus:
    """文档状态"""

    document_type: str  # "target_patent" 或 "prior_art"
    patent_number: str
    exists: bool
    has_full_text: bool = False
    has_pdf: bool = False
    pdf_path: str = ""
    source: str = ""  # "database" 或 "local_file"
    missing_reason: str = ""


@dataclass
class CompletenessReport:
    """完整性报告"""

    target_application_number: str
    is_complete: bool

    # 目标专利状态
    target_patent_status: DocumentStatus | None = None

    # 对比文件状态
    prior_art_status: list[DocumentStatus] = field(default_factory=list)

    # 统计
    total_prior_art: int = 0
    complete_prior_art: int = 0
    missing_prior_art: int = 0

    # 建议
    download_recommendations: list[dict[str, Any]] = field(default_factory=list)

    # 元数据
    checked_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_markdown(self) -> str:
        """生成Markdown格式的报告"""
        md = []

        # 标题和完整性状态
        if self.is_complete:
            md.append("# ✅ 文档完整性检查通过\n")
            md.append(f"**检查时间**: {self.checked_at}\n")
        else:
            md.append("# ⚠️ 文档完整性检查\n")
            md.append(f"**检查时间**: {self.checked_at}\n")

        # 目标专利信息
        md.append("## 🎯 目标专利\n")
        if self.target_patent_status:
            status = self.target_patent_status
            if status.exists and status.has_full_text:
                md.append(f"**申请号**: `{self.target_application_number}`\n")
                md.append("**状态**: ✅ 已有全文\n")
                if status.has_pdf:
                    md.append(f"**PDF路径**: `{status.pdf_path}`\n")
            else:
                md.append(f"**申请号**: `{self.target_application_number}`\n")
                md.append("**状态**: ❌ 缺失全文\n")
                if status.missing_reason:
                    md.append(f"**原因**: {status.missing_reason}\n")
        md.append("")

        # 对比文件信息
        md.append(f"## 📄 对比文件 ({self.complete_prior_art}/{self.total_prior_art})\n")

        if self.prior_art_status:
            for i, status in enumerate(self.prior_art_status, 1):
                if status.exists and status.has_full_text:
                    md.append(f"### D{i}: `{status.patent_number}` ✅\n")
                    if status.has_pdf:
                        md.append(f"- **PDF**: `{status.pdf_path}`\n")
                else:
                    md.append(f"### D{i}: `{status.patent_number}` ❌\n")
                    md.append("- **状态**: 缺失全文\n")
                    if status.missing_reason:
                        md.append(f"- **原因**: {status.missing_reason}\n")
                md.append("")

        # 下载建议
        if self.download_recommendations:
            md.append("## 📥 下载建议\n")
            for rec in self.download_recommendations:
                md.append(f"- **{rec['patent_number']}**: {rec['action']}\n")
            md.append("")

        # 交互选项
        md.append("---\n")
        if self.is_complete:
            md.append("## ✅ 文档已齐备\n\n")
            md.append("**下一步**: 步骤2 - 智能分析\n\n")
            md.append("**分析计划**:\n")
            md.append("1. 法律条款分析\n")
            md.append("2. 对比文件差异分析\n")
            md.append("3. 答复策略制定\n")
            md.append("4. 争辩点梳理\n\n")
            md.append("- ✅ 回复 `确认` 或 `confirm` 继续\n")
            md.append("- ❌ 回复 `修改` 重新检查\n")
        else:
            md.append("## ⚠️ 文档未完全齐备\n\n")
            md.append("**是否使用平台工具下载缺失文档？**\n\n")
            md.append("- ✅ 回复 `下载` 自动下载缺失文档\n")
            md.append("- ⏭️  回复 `跳过` 使用现有文档继续\n")
            md.append("- ❌ 回复 `取消` 中止流程\n")

        return "".join(md)


class DocumentCompletenessChecker:
    """
    文档完整性检查器

    功能:
    1. 检查目标专利全文是否存在
    2. 检查对比文件是否全部齐备
    3. 生成完整性报告
    4. 提供下载建议
    """

    def __init__(
        self,
        patent_data_dir: str = "data/patents",
        pdf_dir: str = "data/patents/PDF",
    ):
        """
        初始化检查器

        Args:
            patent_data_dir: 专利数据目录
            pdf_dir: PDF文件目录
        """
        self.patent_data_dir = Path(patent_data_dir)
        self.pdf_dir = Path(pdf_dir)
        self.pdf_dir.mkdir(parents=True, exist_ok=True)

        # 初始化专利检索器
        self.retriever = None
        try:
            from core.patents.enhanced_patent_retriever import (
                EnhancedPatentRetriever,
            )

            self.retriever = EnhancedPatentRetriever()
            self.retriever.connect()
            logger.info("✅ 专利检索器初始化成功")
        except ImportError:
            logger.warning("⚠️ 专利检索器模块未找到")
        except Exception as e:
            logger.warning(f"⚠️ 专利检索器初始化失败: {e}")

        logger.info(f"📂 数据目录: {self.patent_data_dir}")
        logger.info(f"📄 PDF目录: {self.pdf_dir}")

    def check_completeness(
        self,
        target_application_number: str,
        prior_art_references: list[dict[str, Any]],    ) -> CompletenessReport:
        """
        检查文档完整性

        Args:
            target_application_number: 目标专利申请号
            prior_art_references: 对比文件列表 (从审查意见解析获取)

        Returns:
            CompletenessReport: 完整性报告
        """
        logger.info("🔍 开始检查文档完整性")
        logger.info(f"   目标专利: {target_application_number}")
        logger.info(f"   对比文件数: {len(prior_art_references)}")

        report = CompletenessReport(
            target_application_number=target_application_number,
            is_complete=False,
            total_prior_art=len(prior_art_references),
        )

        # 1. 检查目标专利
        report.target_patent_status = self._check_target_patent(
            target_application_number
        )

        # 2. 检查对比文件
        for prior_art in prior_art_references:
            pub_number = prior_art.get("publication_number", "")
            status = self._check_prior_art(pub_number)
            report.prior_art_status.append(status)

            if status.has_full_text:
                report.complete_prior_art += 1
            else:
                report.missing_prior_art += 1

        # 3. 生成下载建议
        report.download_recommendations = self._generate_download_recommendations(
            report
        )

        # 4. 判断整体完整性
        target_complete = (
            report.target_patent_status.exists
            and report.target_patent_status.has_full_text
        )
        prior_art_complete = report.missing_prior_art == 0

        report.is_complete = target_complete and prior_art_complete

        logger.info(
            f"✅ 检查完成: 完整性={'通过' if report.is_complete else '未通过'}"
        )
        logger.info(f"   目标专利: {'✅' if target_complete else '❌'}")
        logger.info(f"   对比文件: {report.complete_prior_art}/{report.total_prior_art} ✅")

        return report

    def _check_target_patent(self, application_number: str) -> DocumentStatus:
        """检查目标专利"""
        status = DocumentStatus(
            document_type="target_patent",
            patent_number=application_number,
            exists=False,
        )

        # 1. 检查数据库
        if self.retriever:
            try:
                patent_info = self.retriever.search_by_application_number(application_number)
                if patent_info:
                    status.exists = True
                    status.source = "database"
                    status.has_pdf = patent_info.pdf_downloaded
                    status.pdf_path = patent_info.pdf_path or ""

                    # 检查是否有全文内容
                    if patent_info.abstract or patent_info.claims_content:
                        status.has_full_text = True
                    elif status.pdf_path and Path(status.pdf_path).exists():
                        status.has_full_text = True
                    else:
                        status.missing_reason = "数据库中无全文内容，PDF未下载"

                    return status
            except Exception as e:
                logger.warning(f"⚠️ 数据库查询失败: {e}")

        # 2. 检查本地PDF文件
        pdf_patterns = [
            self.pdf_dir / f"{application_number}.pdf",
            self.pdf_dir / f"CN{application_number}.pdf",
            self.patent_data_dir / f"{application_number}.pdf",
        ]

        for pattern in pdf_patterns:
            if pattern.exists():
                status.exists = True
                status.has_full_text = True
                status.has_pdf = True
                status.pdf_path = str(pattern)
                status.source = "local_file"
                return status

        # 3. 未找到
        status.missing_reason = "数据库和本地文件中均未找到"
        return status

    def _check_prior_art(self, publication_number: str) -> DocumentStatus:
        """检查对比文件"""
        # 清理专利号
        pub_number = publication_number.strip().upper()
        if not pub_number.startswith("CN") and not pub_number.startswith("US"):
            # 可能需要添加CN前缀
            if pub_number.isdigit() or len(pub_number.split(" ")[0]) == 12:
                pub_number = f"CN{pub_number}"

        status = DocumentStatus(
            document_type="prior_art",
            patent_number=pub_number,
            exists=False,
        )

        # 1. 检查本地PDF文件
        pdf_patterns = [
            self.pdf_dir / f"{pub_number}.pdf",
            self.pdf_dir / f"{pub_number.replace('CN', '')}.pdf",
        ]

        for pattern in pdf_patterns:
            if pattern.exists():
                status.exists = True
                status.has_full_text = True
                status.has_pdf = True
                status.pdf_path = str(pattern)
                status.source = "local_file"
                return status

        # 2. 检查数据库（如果有检索器）
        if self.retriever:
            try:
                # 尝试用公开号检索
                patent_info = self.retriever.search_by_application_number(pub_number)
                if patent_info:
                    status.exists = True
                    status.source = "database"
                    status.has_pdf = patent_info.pdf_downloaded
                    status.pdf_path = patent_info.pdf_path or ""

                    if patent_info.abstract or patent_info.claims_content:
                        status.has_full_text = True
                    elif status.pdf_path and Path(status.pdf_path).exists():
                        status.has_full_text = True
                    else:
                        status.missing_reason = "数据库中无全文内容，PDF未下载"
                    return status
            except Exception as e:
                logger.debug(f"数据库查询 {pub_number} 失败: {e}")

        # 3. 未找到
        status.missing_reason = "本地文件中未找到"
        return status

    def _generate_download_recommendations(
        self, report: CompletenessReport
    ) -> list[dict[str, Any]]:
        """生成下载建议"""
        recommendations = []

        # 目标专利缺失
        if report.target_patent_status and not report.target_patent_status.has_full_text:
            recommendations.append(
                {
                    "patent_number": report.target_application_number,
                    "type": "target_patent",
                    "action": "下载目标专利全文",
                    "priority": "high",
                }
            )

        # 对比文件缺失
        for status in report.prior_art_status:
            if not status.has_full_text:
                recommendations.append(
                    {
                        "patent_number": status.patent_number,
                        "type": "prior_art",
                        "action": "下载对比文件",
                        "priority": "medium",
                    }
                )

        return recommendations


# 全局单例
_completeness_checker_instance: DocumentCompletenessChecker | None = None


def get_document_completeness_checker(
    patent_data_dir: str = "data/patents",
    pdf_dir: str = "data/patents/PDF",
) -> DocumentCompletenessChecker:
    """获取检查器单例"""
    global _completeness_checker_instance
    if _completeness_checker_instance is None:
        _completeness_checker_instance = DocumentCompletenessChecker(
            patent_data_dir=patent_data_dir, pdf_dir=pdf_dir
        )
    return _completeness_checker_instance


# 测试代码
async def main():
    """测试检查器"""

    print("\n" + "=" * 70)
    print("📋 文档完整性检查器测试")
    print("=" * 70 + "\n")

    checker = get_document_completeness_checker()

    # 模拟测试数据
    target_application_number = "CN202310000001.X"
    prior_art_references = [
        {
            "reference_id": "D1",
            "publication_number": "CN112345678A",
            "title": "图像识别方法及装置",
        },
        {
            "reference_id": "D2",
            "publication_number": "US2023001234A1",
            "title": "Image Processing Method",
        },
    ]

    # 执行检查
    report = checker.check_completeness(
        target_application_number=target_application_number,
        prior_art_references=prior_art_references,
    )

    # 输出结果
    print(checker.export_result(report, format="markdown"))

    # 输出JSON
    print("\n" + "=" * 70)
    print("📊 JSON格式:")
    print("=" * 70 + "\n")

    import json

    print(
        json.dumps(
            {
                "target_application_number": report.target_application_number,
                "is_complete": report.is_complete,
                "target_patent_status": (
                    report.target_patent_status.__dict__ if report.target_patent_status else None
                ),
                "prior_art_status": [s.__dict__ for s in report.prior_art_status],
                "statistics": {
                    "total": report.total_prior_art,
                    "complete": report.complete_prior_art,
                    "missing": report.missing_prior_art,
                },
                "download_recommendations": report.download_recommendations,
            },
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )

    print("\n✅ 测试完成!")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
