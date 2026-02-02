#!/usr/bin/env python3
"""
法律提示词增强服务 - 基于向量检索的提示词动态生成
Legal Prompt Enhancer - Dynamic Prompt Generation Based on Vector Retrieval

将法律向量检索结果集成到提示词系统中,为AI提供准确的法律依据

作者: Athena平台团队
创建时间: 2026-01-11
版本: v1.0.0-production
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.logging_config import setup_logging

try:
    from core.legal.legal_vector_retrieval_service import (
        LegalRetrievalResponse,
        LegalVectorRetrievalService,
        SearchResult,
        get_legal_vector_service,
        search_legal_rules,
        search_legal_vector,
        search_patent_cases,
    )

    VECTOR_SERVICE_AVAILABLE = True
except ImportError:
    VECTOR_SERVICE_AVAILABLE = False
    search_legal_rules = None
    search_patent_cases = None
    SearchResult = None
    logging.warning("法律向量检索服务未找到")

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


@dataclass
class PromptEnhancementRequest:
    """提示词增强请求"""

    user_query: str  # 用户查询
    base_prompt: str  # 基础提示词
    domain: str = "patent_legal"  # 业务领域
    include_laws: bool = True  # 是否包含法律条款
    include_cases: bool = True  # 是否包含案例
    max_laws: int = 5  # 最大法律条款数
    max_cases: int = 5  # 最大案例数
    score_threshold: float = 0.75  # 相似度阈值


@dataclass
class PromptEnhancementResult:
    """提示词增强结果"""

    success: bool
    enhanced_prompt: str
    original_prompt: str
    retrieval_results: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    processing_time: float = 0.0


class LegalPromptEnhancer:
    """
    法律提示词增强器

    核心功能:
    1. 向量检索 - 获取相关法律条款和案例
    2. 提示词增强 - 将检索结果注入到提示词中
    3. 模板渲染 - 生成增强后的提示词
    4. 质量保证 - 确保检索结果的准确性和相关性
    """

    # 提示词模板
    PROMPT_TEMPLATE = """
# 角色定义
你是一个专业的{domain}专家,基于权威法律数据提供准确的法律分析和建议。

# 可用数据源
- 法律条款库: 106,832条法律条文(宪法、民法典、刑法、行政法、经济法、诉讼法、司法解释等)
- 专利判决库: 12,712份专利判决书
- 法律文档库: 6,814个法律文档

# 检索到的法律依据
{legal_basis_section}

# 检索到的相关案例
{cases_section}

# 分析要求
1. 基于以上法律依据和案例进行分析
2. 明确标注数据来源(法条编号、案例编号)
3. 提供具体的法律适用建议
4. 引用相似案例的处理方式
5. 确保分析的准确性和权威性

# 原始提示词
{base_prompt}

# 当前问题
{user_query}

# 响应要求
基于检索到的权威法律数据,请提供专业、准确的法律分析和建议。
"""

    LEGAL_BASIS_TEMPLATE = """
{laws_count}条相关法律条款:

{laws_content}
"""

    CASES_TEMPLATE = """
{cases_count}个相关案例:

{cases_content}
"""

    LAW_ITEM_TEMPLATE = """
**{index}. {law_title}** (相似度: {score:.1%})
- **来源**: {source}
- **内容**: {content}
- **相关度**: {relevance}
"""

    CASE_ITEM_TEMPLATE = """
**{index}. {case_title}** (相似度: {score:.1%})
- **来源**: {source}
- **争议焦点**: {focus}
- **裁判要旨**: {ruling}
- **相关度**: {relevance}
"""

    def __init__(self):
        """初始化法律提示词增强器"""
        logger.info("🎨 法律提示词增强器初始化")

        if not VECTOR_SERVICE_AVAILABLE:
            logger.warning("⚠️ 向量检索服务不可用,增强功能受限")

        # 统计信息
        self.stats = {
            "total_enhancements": 0,
            "successful_enhancements": 0,
            "failed_enhancements": 0,
            "total_retrievals": 0,
        }

        logger.info("✅ 法律提示词增强器初始化完成")

    async def enhance_prompt(
        self,
        user_query: str,
        base_prompt: str,
        domain: str = "patent_legal",
        include_laws: bool = True,
        include_cases: bool = True,
        max_laws: int = 5,
        max_cases: int = 5,
        score_threshold: float = 0.75,
    ) -> PromptEnhancementResult:
        """
        增强提示词

        Args:
            user_query: 用户查询
            base_prompt: 基础提示词
            domain: 业务领域
            include_laws: 是否包含法律条款
            include_cases: 是否包含案例
            max_laws: 最大法律条款数
            max_cases: 最大案例数
            score_threshold: 相似度阈值

        Returns:
            PromptEnhancementResult: 增强结果
        """
        start_time = datetime.now()
        self.stats["total_enhancements"] += 1

        logger.info(f"🔧 增强提示词: {user_query[:50]}...")
        logger.info(f"   领域: {domain}, 法律: {include_laws}, 案例: {include_cases}")

        try:
            # 检查向量服务可用性
            if not VECTOR_SERVICE_AVAILABLE:
                return PromptEnhancementResult(
                    success=False,
                    enhanced_prompt=base_prompt,
                    original_prompt=base_prompt,
                    retrieval_results={},
                    error="向量检索服务不可用",
                    processing_time=(datetime.now() - start_time).total_seconds(),
                )

            # 步骤1: 向量检索
            retrieval_results = {}
            legal_basis_content = ""
            cases_content = ""

            if include_laws and search_legal_rules is not None:
                # 检索法律条款
                laws_response = await search_legal_rules(query=user_query, limit=max_laws)

                if laws_response.success:
                    retrieval_results["laws"] = laws_response
                    legal_basis_content = self._format_legal_basis(laws_response.results)
                    logger.info(f"   ✓ 检索到 {len(laws_response.results)} 条法律条款")

            if include_cases and search_patent_cases is not None:
                # 检索案例
                cases_response = await search_patent_cases(query=user_query, limit=max_cases)

                if cases_response.success:
                    retrieval_results["cases"] = cases_response
                    cases_content = self._format_cases(cases_response.results)
                    logger.info(f"   ✓ 检索到 {len(cases_response.results)} 个案例")

            # 步骤2: 生成增强提示词
            enhanced_prompt = self._generate_enhanced_prompt(
                user_query=user_query,
                base_prompt=base_prompt,
                domain=domain,
                legal_basis_content=legal_basis_content,
                cases_content=cases_content,
                retrieval_results=retrieval_results,
            )

            processing_time = (datetime.now() - start_time).total_seconds()

            # 更新统计
            self.stats["successful_enhancements"] += 1
            self.stats["total_retrievals"] += len(retrieval_results)

            # 计算统计数据
            laws_count = 0
            cases_count = 0
            if "laws" in retrieval_results:
                laws_response = retrieval_results["laws"]
                if hasattr(laws_response, "results"):
                    laws_count = len(laws_response.results)
            if "cases" in retrieval_results:
                cases_response = retrieval_results["cases"]
                if hasattr(cases_response, "results"):
                    cases_count = len(cases_response.results)

            result = PromptEnhancementResult(
                success=True,
                enhanced_prompt=enhanced_prompt,
                original_prompt=base_prompt,
                retrieval_results={
                    "laws_count": laws_count,
                    "cases_count": cases_count,
                    "avg_score": self._calculate_avg_score(retrieval_results),
                },
                metadata={
                    "domain": domain,
                    "included_laws": include_laws,
                    "included_cases": include_cases,
                    "score_threshold": score_threshold,
                },
                processing_time=processing_time,
            )

            logger.info(f"✅ 提示词增强完成, 耗时 {processing_time:.3f}秒")

            return result

        except Exception as e:
            logger.error(f"❌ 提示词增强失败: {e}")
            self.stats["failed_enhancements"] += 1

            return PromptEnhancementResult(
                success=False,
                enhanced_prompt=base_prompt,
                original_prompt=base_prompt,
                retrieval_results={},
                error=str(e),
                processing_time=(datetime.now() - start_time).total_seconds(),
            )

    def _format_legal_basis(self, results: list[Any]) -> str:
        """格式化法律条款"""
        if not results:
            return "未检索到相关法律条款"

        items = []
        for i, result in enumerate(results[:5], 1):
            payload = result.payload
            score = result.score

            # 提取关键字段
            title = (
                payload.get("title") or payload.get("law_name") or payload.get("article_id", "未知")
            )
            source = payload.get("source") or payload.get("law_name", "未知来源")
            content = (
                payload.get("content") or payload.get("article_text") or payload.get("text", "")
            )

            # 截断过长内容
            if len(content) > 200:
                content = content[:200] + "..."

            # 相关系度描述
            if score >= 0.90:
                relevance = "高度相关"
            elif score >= 0.80:
                relevance = "相关"
            else:
                relevance = "一般相关"

            item = self.LAW_ITEM_TEMPLATE.format(
                index=i,
                law_title=title,
                score=score,
                source=source,
                content=content,
                relevance=relevance,
            )
            items.append(item)

        return self.LEGAL_BASIS_TEMPLATE.format(
            laws_count=len(results), laws_content="\n".join(items)
        )

    def _format_cases(self, results: list[Any]) -> str:
        """格式化案例"""
        if not results:
            return "未检索到相关案例"

        items = []
        for i, result in enumerate(results[:5], 1):
            payload = result.payload
            score = result.score

            # 提取关键字段
            title = (
                payload.get("title")
                or payload.get("case_name")
                or payload.get("decision_number", f"案例#{i}")
            )
            source = payload.get("source") or payload.get("decision_number", "未知来源")
            focus = (
                payload.get("focus") or payload.get("dispute_focus") or payload.get("争议焦点", "")
            )
            ruling = (
                payload.get("ruling")
                or payload.get("ruling_essence")
                or payload.get("裁判要旨", "")
            )

            # 截断过长内容
            if len(focus) > 100:
                focus = focus[:100] + "..."
            if len(ruling) > 200:
                ruling = ruling[:200] + "..."

            # 相关系度描述
            if score >= 0.90:
                relevance = "高度相似"
            elif score >= 0.80:
                relevance = "相似"
            else:
                relevance = "一般相似"

            item = self.CASE_ITEM_TEMPLATE.format(
                index=i,
                case_title=title,
                score=score,
                source=source,
                focus=focus,
                ruling=ruling,
                relevance=relevance,
            )
            items.append(item)

        return self.CASES_TEMPLATE.format(cases_count=len(results), cases_content="\n".join(items))

    def _generate_enhanced_prompt(
        self,
        user_query: str,
        base_prompt: str,
        domain: str,
        legal_basis_content: str,
        cases_content: str,
        retrieval_results: dict[str, Any],    ) -> str:
        """生成增强提示词"""
        # 确定领域名称
        domain_names = {
            "patent_legal": "专利法律",
            "trademark_legal": "商标法律",
            "general_legal": "法律",
        }
        domain_name = domain_names.get(domain, "法律")

        # 生成增强提示词
        enhanced_prompt = self.PROMPT_TEMPLATE.format(
            domain=domain_name,
            legal_basis_section=legal_basis_content or "无相关法律条款",
            cases_section=cases_content or "无相关案例",
            base_prompt=base_prompt,
            user_query=user_query,
        )

        return enhanced_prompt.strip()

    def _calculate_avg_score(self, retrieval_results: dict[str, Any]) -> float:
        """计算平均相似度"""
        all_scores = []

        laws_response = retrieval_results.get("laws")
        if laws_response and hasattr(laws_response, "results"):
            for result in laws_response.results:
                all_scores.append(result.score)

        cases_response = retrieval_results.get("cases")
        if cases_response and hasattr(cases_response, "results"):
            for result in cases_response.results:
                all_scores.append(result.score)

        if all_scores:
            return sum(all_scores) / len(all_scores)
        return 0.0

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "statistics": self.stats,
            "service_available": VECTOR_SERVICE_AVAILABLE,
            "generated_at": datetime.now().isoformat(),
        }


# ============================================================================
# 全局服务实例
# ============================================================================

_enhancer_instance: LegalPromptEnhancer | None = None


def get_legal_prompt_enhancer() -> LegalPromptEnhancer:
    """获取法律提示词增强器单例"""
    global _enhancer_instance
    if _enhancer_instance is None:
        _enhancer_instance = LegalPromptEnhancer()
    return _enhancer_instance


# ============================================================================
# 便捷函数
# ============================================================================


async def enhance_legal_prompt(
    user_query: str, base_prompt: str, domain: str = "patent_legal"
) -> PromptEnhancementResult:
    """便捷函数:增强法律提示词"""
    enhancer = get_legal_prompt_enhancer()
    return await enhancer.enhance_prompt(
        user_query=user_query, base_prompt=base_prompt, domain=domain
    )


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "LegalPromptEnhancer",
    "PromptEnhancementRequest",
    "PromptEnhancementResult",
    "enhance_legal_prompt",
    "get_legal_prompt_enhancer",
]
