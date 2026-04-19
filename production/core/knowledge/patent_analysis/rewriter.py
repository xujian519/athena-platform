from __future__ import annotations

#!/usr/bin/env python3
"""
专利重写器
Patent Rewriter

专利文档优化和重写功能

作者: Athena AI系统
创建时间: 2025-12-04
版本: 3.0.0
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class RewriteTarget(Enum):
    """重写目标"""

    CLAIMS = "claims"  # 权利要求
    SPECIFICATION = "specification"  # 说明书
    ABSTRACT = "abstract"  # 摘要
    TITLE = "title"  # 标题
    FULL_DOCUMENT = "full_document"  # 完整文档


class RewriteMode(Enum):
    """重写模式"""

    STANDARD = "standard"  # 标准重写
    ENHANCED = "enhanced"  # 增强重写
    OPTIMIZED = "optimized"  # 优化重写
    CUSTOM = "custom"  # 自定义重写


@dataclass
class RewriteResult:
    """重写结果"""

    target: RewriteTarget
    mode: RewriteMode
    original_text: str
    rewritten_text: str
    improvements: list[str]
    suggestions: list[str]
    confidence: float
    created_at: datetime = field(default_factory=datetime.now)


class PatentRewriter:
    """专利重写器"""

    _instance: PatentRewriter | None = None

    def __init__(self):
        self.rewrite_models = {}
        self.improvement_rules = {}
        self._initialized = False

    @classmethod
    async def initialize(cls):
        """初始化重写器"""
        if cls._instance is None:
            cls._instance = cls()
            await cls._instance._load_models()
            cls._instance._initialized = True
            logger.info("✅ 专利重写器初始化完成")
        return cls._instance

    @classmethod
    def get_instance(cls) -> PatentRewriter:
        """获取单例实例"""
        if cls._instance is None:
            raise RuntimeError("PatentRewriter未初始化,请先调用initialize()")
        return cls._instance

    async def _load_models(self):
        """加载重写模型"""
        self.rewrite_models = {
            RewriteTarget.CLAIMS: self._load_claims_model(),
            RewriteTarget.SPECIFICATION: self._load_specification_model(),
            RewriteTarget.ABSTRACT: self._load_abstract_model(),
            RewriteTarget.TITLE: self._load_title_model(),
            RewriteTarget.FULL_DOCUMENT: self._load_document_model(),
        }

    def _load_claims_model(self) -> Any:
        """加载权利要求重写模型"""
        return {
            "model_name": "patent_claims_rewriter",
            "version": "3.0.0",
            "parameters": {
                "claim_structure_optimization": True,
                "legal_terminology_enhancement": True,
                "scope_clarity_improvement": True,
            },
        }

    def _load_specification_model(self) -> Any:
        """加载说明书重写模型"""
        return {
            "model_name": "patent_specification_rewriter",
            "version": "3.0.0",
            "parameters": {
                "technical_detail_enhancement": True,
                "embodiment_optimization": True,
                "clarity_improvement": True,
            },
        }

    def _load_abstract_model(self) -> Any:
        """加载摘要重写模型"""
        return {
            "model_name": "patent_abstract_rewriter",
            "version": "3.0.0",
            "parameters": {
                "conciseness_optimization": True,
                "key_feature_highlight": True,
                "technical_summary": True,
            },
        }

    def _load_title_model(self) -> Any:
        """加载标题重写模型"""
        return {
            "model_name": "patent_title_rewriter",
            "version": "3.0.0",
            "parameters": {
                "clarity_enhancement": True,
                "keyword_optimization": True,
                "appeal_improvement": True,
            },
        }

    def _load_document_model(self) -> Any:
        """加载完整文档重写模型"""
        return {
            "model_name": "patent_document_rewriter",
            "version": "3.0.0",
            "parameters": {
                "comprehensive_optimization": True,
                "consistency_check": True,
                "quality_enhancement": True,
            },
        }

    async def rewrite_patent(
        self,
        patent_data: dict[str, Any],        target: RewriteTarget,
        mode: RewriteMode = RewriteMode.STANDARD,
    ) -> RewriteResult:
        """
        重写专利

        Args:
            patent_data: 专利数据
            target: 重写目标
            mode: 重写模式

        Returns:
            重写结果
        """
        logger.info(f"✏️ 开始重写专利: {target.value} ({mode.value})")

        # 获取原始文本
        original_text = self._extract_text(patent_data, target)
        if not original_text:
            raise ValueError(f"无法提取{target.value}的文本内容")

        # 执行重写
        rewritten_text = await self._perform_rewrite(original_text, target, mode)

        # 生成改进建议
        improvements = await self._generate_improvements(original_text, rewritten_text, target)
        suggestions = await self._generate_suggestions(patent_data, rewritten_text, target)

        # 计算置信度
        confidence = self._calculate_confidence(original_text, rewritten_text)

        result = RewriteResult(
            target=target,
            mode=mode,
            original_text=original_text,
            rewritten_text=rewritten_text,
            improvements=improvements,
            suggestions=suggestions,
            confidence=confidence,
        )

        logger.info(f"✅ 专利重写完成: 置信度{confidence:.1%}")
        return result

    def _extract_text(self, patent_data: dict[str, Any], target: RewriteTarget) -> str:
        """提取指定目标的文本"""
        if target == RewriteTarget.TITLE:
            return patent_data.get("title", "")
        elif target == RewriteTarget.ABSTRACT:
            return patent_data.get("abstract", "")
        elif target == RewriteTarget.CLAIMS:
            return patent_data.get("claims", "")
        elif target == RewriteTarget.SPECIFICATION:
            return patent_data.get("specification", "")
        elif target == RewriteTarget.FULL_DOCUMENT:
            return patent_data.get("full_text", "")
        else:
            return ""

    async def _perform_rewrite(self, text: str, target: RewriteTarget, mode: RewriteMode) -> str:
        """执行重写"""
        model = self.rewrite_models.get(target)
        if not model:
            raise ValueError(f"不支持的重写目标: {target}")

        # 模拟重写过程
        await asyncio.sleep(0.2)

        # 根据目标和模式执行不同的重写逻辑
        if target == RewriteTarget.TITLE:
            return await self._rewrite_title(text, mode)
        elif target == RewriteTarget.ABSTRACT:
            return await self._rewrite_abstract(text, mode)
        elif target == RewriteTarget.CLAIMS:
            return await self._rewrite_claims(text, mode)
        elif target == RewriteTarget.SPECIFICATION:
            return await self._rewrite_specification(text, mode)
        elif target == RewriteTarget.FULL_DOCUMENT:
            return await self._rewrite_document(text, mode)
        else:
            return text  # 默认返回原文本

    async def _rewrite_title(self, title: str, mode: RewriteMode) -> str:
        """重写标题"""
        # 模拟标题重写逻辑
        improvements = []

        if len(title) < 10:
            improvements.append("增加技术特征描述")
            title = f"一种{title}的技术方案"

        if "的" not in title and "一种" not in title:
            improvements.append("优化标题结构")
            title = f"基于{title}的装置和方法"

        if mode == RewriteMode.ENHANCED:
            title = f"[改进型]{title}"

        return title

    async def _rewrite_abstract(self, abstract: str, mode: RewriteMode) -> str:
        """重写摘要"""
        # 模拟摘要重写逻辑
        if len(abstract) < 100:
            abstract += "本发明通过创新的技术方案,解决了现有技术中的问题,具有良好的应用前景。"

        if mode == RewriteMode.ENHANCED:
            abstract = f"本发明公开了{abstract}通过上述技术方案,实现了技术效果的显著提升。"

        return abstract

    async def _rewrite_claims(self, claims: str, mode: RewriteMode) -> str:
        """重写权利要求"""
        # 模拟权利要求重写逻辑

        # 确保权利要求格式正确
        if not claims.startswith("1. "):
            claims = "1. " + claims

        # 优化权利要求语言
        if "其特征在于" not in claims:
            claims = claims.replace("。", ",其特征在于:")

        if mode == RewriteMode.ENHANCED:
            # 添加从属权利要求
            claims += "\n2. 根据权利要求1所述的方法,其特征在于,还包括优化步骤。"

        return claims

    async def _rewrite_specification(self, specification: str, mode: RewriteMode) -> str:
        """重写说明书"""
        # 模拟说明书重写逻辑

        # 确保包含技术领域
        if "技术领域" not in specification:
            specification = (
                "[技术领域]\n本发明涉及人工智能技术领域,具体涉及一种智能处理方法。\n\n"
                + specification
            )

        # 确保包含背景技术
        if "背景技术" not in specification:
            specification = specification.replace(
                "[技术领域]",
                "[技术领域]\n\n[背景技术]\n现有技术存在不足,需要改进。\n\n[发明内容]",
            )

        if mode == RewriteMode.ENHANCED:
            # 添加具体实施方式
            if "具体实施方式" not in specification:
                specification += "\n\n[具体实施方式]\n为了更清楚地说明本发明的技术方案,下面将结合具体实施例进行详细描述。"

        return specification

    async def _rewrite_document(self, document: str, mode: RewriteMode) -> str:
        """重写完整文档"""
        # 分段处理不同部分
        parts = {
            "title": self._extract_section(document, "title"),
            "abstract": self._extract_section(document, "abstract"),
            "claims": self._extract_section(document, "claims"),
            "specification": self._extract_section(document, "specification"),
        }

        # 分别重写各部分
        rewritten_parts = {}
        for part_name, part_text in parts.items():
            if part_text:
                if part_name == "title":
                    rewritten_parts[part_name] = await self._rewrite_title(part_text, mode)
                elif part_name == "abstract":
                    rewritten_parts[part_name] = await self._rewrite_abstract(part_text, mode)
                elif part_name == "claims":
                    rewritten_parts[part_name] = await self._rewrite_claims(part_text, mode)
                elif part_name == "specification":
                    rewritten_parts[part_name] = await self._rewrite_specification(part_text, mode)

        # 组合重写后的文档
        return self._combine_document(rewritten_parts)

    def _extract_section(self, document: str, section_name: str) -> str:
        """提取文档特定部分"""
        # 简化的提取逻辑
        if section_name == "title":
            lines = document.split("\n")[:5]
            return "\n".join(lines)
        elif section_name == "abstract":
            if "摘要" in document:
                start = document.find("摘要")
                end = document.find("权利要求", start)
                return document[start:end] if end > start else document[start:]
        elif section_name == "claims":
            if "权利要求" in document:
                start = document.find("权利要求")
                end = document.find("说明书", start)
                return document[start:end] if end > start else document[start:]
        elif section_name == "specification":
            if "说明书" in document:
                start = document.find("说明书")
                return document[start:]
        return ""

    def _combine_document(self, parts: dict[str, str]) -> str:
        """组合文档各部分"""
        document_parts = []

        if "title" in parts:
            document_parts.append(f"标题:\n{parts['title']}")

        if "abstract" in parts:
            document_parts.append(f"\n摘要:\n{parts['abstract']}")

        if "claims" in parts:
            document_parts.append(f"\n权利要求:\n{parts['claims']}")

        if "specification" in parts:
            document_parts.append(f"\n说明书:\n{parts['specification']}")

        return "\n".join(document_parts)

    async def _generate_improvements(
        self, original: str, rewritten: str, target: RewriteTarget
    ) -> list[str]:
        """生成改进点"""
        improvements = []

        # 分析改进点
        if len(rewritten) > len(original):
            improvements.append("内容更加丰富和详细")
        if rewritten.count(",") > original.count(","):
            improvements.append("逻辑结构更加清晰")
        if "优化" in rewritten and "优化" not in original:
            improvements.append("添加了优化描述")
        if "特征在于" in rewritten and "特征在于" not in original:
            improvements.append("权利要求结构更加规范")

        if not improvements:
            improvements.append("文本表达更加专业")

        return improvements

    async def _generate_suggestions(
        self, patent_data: dict[str, Any], rewritten_text: str, target: RewriteTarget
    ) -> list[str]:
        """生成建议"""
        suggestions = []

        # 根据重写目标生成建议
        if target == RewriteTarget.TITLE:
            suggestions.append("建议标题突出技术创新点")
            suggestions.append("确保标题简洁明了")
        elif target == RewriteTarget.ABSTRACT:
            suggestions.append("建议摘要包含技术问题、方案和效果")
            suggestions.append("控制摘要字数在150-300字")
        elif target == RewriteTarget.CLAIMS:
            suggestions.append("建议权利要求层次分明")
            suggestions.append("确保保护范围合理")
        elif target == RewriteTarget.SPECIFICATION:
            suggestions.append("建议详细描述技术方案")
            suggestions.append("提供具体实施例")
        elif target == RewriteTarget.FULL_DOCUMENT:
            suggestions.append("建议整体文档结构清晰")
            suggestions.append("确保各部分内容协调一致")

        return suggestions

    def _calculate_confidence(self, original: str, rewritten: str) -> float:
        """计算重写置信度"""
        # 简化的置信度计算
        if original == rewritten:
            return 0.0

        # 基于文本变化程度计算置信度
        length_ratio = len(rewritten) / max(len(original), 1)
        if length_ratio > 0.8 and length_ratio < 1.5:
            return 0.85  # 合理的变化范围
        elif length_ratio > 0.5 and length_ratio < 2.0:
            return 0.70  # 较大的变化
        else:
            return 0.50  # 变化过大

    async def batch_rewrite(
        self,
        patents: list[dict[str, Any]],        target: RewriteTarget,
        mode: RewriteMode = RewriteMode.STANDARD,
    ) -> list[RewriteResult]:
        """批量重写专利"""
        logger.info(f"✏️ 开始批量重写{len(patents)}项专利的{target.value}")

        tasks = [self.rewrite_patent(patent, target, mode) for patent in patents]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ 专利{i+1}重写失败: {result}")
                # 创建默认结果
                original_text = self._extract_text(patents[i], target)
                default_result = RewriteResult(
                    target=target,
                    mode=mode,
                    original_text=original_text,
                    rewritten_text=original_text,  # 返回原文
                    improvements=[],
                    suggestions=["重写失败,请检查输入"],
                    confidence=0.0,
                )
                processed_results.append(default_result)
            else:
                processed_results.append(result)

        logger.info("✅ 批量重写完成")
        return processed_results

    @classmethod
    async def shutdown(cls):
        """关闭重写器"""
        if cls._instance:
            cls._instance = None
            logger.info("✅ 专利重写器已关闭")
