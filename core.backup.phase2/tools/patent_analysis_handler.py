#!/usr/bin/env python3
"""
专利分析工具Handler
Patent Analysis Tool Handler

提供专利内容分析、创造性评估、新颖性判断等功能。

Author: Athena平台团队
Created: 2026-04-19
Version: 1.0.0
"""

from __future__ import annotations

import logging
import time
from typing import Any

from core.logging_config import setup_logging

logger = setup_logging()


def patent_analysis_handler(
    patent_id: str,
    title: str,
    abstract: str,
    claims: list[str] | None = None,
    description: str | None = None,
    analysis_type: str = "comprehensive",
    **kwargs: Any,
) -> dict[str, Any]:
    """
    专利分析工具处理函数

    功能：
    1. 专利内容分析（技术特征提取）
    2. 创造性评估（基于知识图谱）
    3. 新颖性判断（基于向量检索）
    4. 专利性评分（定性定量结合）

    Args:
        patent_id: 专利号/申请号
        title: 专利标题
        abstract: 专利摘要
        claims: 权利要求列表（可选）
        description: 说明书（可选）
        analysis_type: 分析类型
            - "basic": 基础分析（技术特征提取）
            - "creativity": 创造性评估
            - "novelty": 新颖性判断
            - "comprehensive": 综合分析（默认）
        **kwargs: 其他参数

    Returns:
        分析结果字典，包含：
        - success: 是否成功
        - patent_id: 专利号
        - analysis_type: 分析类型
        - execution_time: 执行时间（秒）
        - results: 分析结果
        - error: 错误信息（如果失败）
    """
    start_time = time.time()
    logger.info(f"🔬 开始专利分析: patent_id={patent_id}, type={analysis_type}")

    try:
        # 根据分析类型选择分析器
        if analysis_type == "basic":
            result = _basic_analysis(
                patent_id=patent_id,
                title=title,
                abstract=abstract,
                claims=claims,
                description=description,
            )
        elif analysis_type == "creativity":
            result = _creativity_analysis(
                patent_id=patent_id,
                title=title,
                abstract=abstract,
                claims=claims,
                description=description,
            )
        elif analysis_type == "novelty":
            result = _novelty_analysis(
                patent_id=patent_id,
                title=title,
                abstract=abstract,
                claims=claims,
                description=description,
            )
        elif analysis_type == "comprehensive":
            result = _comprehensive_analysis(
                patent_id=patent_id,
                title=title,
                abstract=abstract,
                claims=claims,
                description=description,
            )
        else:
            raise ValueError(f"不支持的分析类型: {analysis_type}")

        execution_time = time.time() - start_time
        logger.info(f"✅ 专利分析完成: 耗时 {execution_time:.2f}秒")

        return {
            "success": True,
            "patent_id": patent_id,
            "analysis_type": analysis_type,
            "execution_time": round(execution_time, 2),
            "results": result,
        }

    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = f"专利分析失败: {str(e)}"
        logger.error(f"❌ {error_msg}")
        import traceback

        logger.error(traceback.format_exc())

        return {
            "success": False,
            "patent_id": patent_id,
            "analysis_type": analysis_type,
            "execution_time": round(execution_time, 2),
            "error": error_msg,
            "results": None,
        }


def _basic_analysis(
    patent_id: str,
    title: str,
    abstract: str,
    claims: list[str] | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """
    基础分析：技术特征提取
    """
    logger.info(f"📝 执行基础分析: {patent_id}")

    # 构建完整文本
    full_text = f"{title}\n{abstract}"
    if claims:
        full_text += f"\n{' '.join(claims)}"
    if description:
        full_text += f"\n{description}"

    # 简单特征提取（基于关键词）
    features = _extract_technical_features(full_text)

    return {
        "analysis_level": "basic",
        "patent_id": patent_id,
        "title": title,
        "technical_features": features,
        "feature_count": len(features),
        "analysis_summary": f"从专利文本中提取了 {len(features)} 个技术特征",
    }


def _creativity_analysis(
    patent_id: str,
    title: str,
    abstract: str,
    claims: list[str] | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """
    创造性评估：基于知识图谱和技术对比
    """
    logger.info(f"💡 执行创造性评估: {patent_id}")

    # 尝试使用知识图谱增强分析器
    try:
        from core.patents.patent_knowledge_graph_analyzer import PatentKnowledgeGraphAnalyzer

        with PatentKnowledgeGraphAnalyzer() as analyzer:
            # 构建分析对象
            patent_text = f"{title}\n{abstract}"
            if claims:
                patent_text += f"\n{' '.join(claims)}"

            # 执行知识图谱分析
            analysis_result = analyzer.analyze_patent_text(
                application_number=patent_id, patent_name=title, patent_text=patent_text
            )

            return {
                "analysis_level": "creativity",
                "patent_id": patent_id,
                "title": title,
                "creativity_score": analysis_result.get("creativity_score", 0.0),
                "technical_strength": analysis_result.get("technical_strength", "medium"),
                "innovation_insights": analysis_result.get("innovation_insights", []),
                "kg_entities_matched": analysis_result.get("kg_entities_matched", 0),
                "analysis_summary": f"创造性评分: {analysis_result.get('creativity_score', 0.0):.2f}",
            }

    except Exception as e:
        logger.warning(f"⚠️  知识图谱分析失败，使用简化评估: {e}")

        # 简化创造性评估
        creativity_score = _calculate_simple_creativity_score(title, abstract, claims)

        return {
            "analysis_level": "creativity",
            "patent_id": patent_id,
            "title": title,
            "creativity_score": creativity_score,
            "technical_strength": "medium",
            "innovation_insights": ["基于简化算法评估"],
            "kg_entities_matched": 0,
            "analysis_summary": f"创造性评分（简化）: {creativity_score:.2f}",
            "note": "知识图谱不可用，使用简化评估方法",
        }


def _novelty_analysis(
    patent_id: str,
    title: str,
    abstract: str,
    claims: list[str] | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """
    新颖性判断：基于向量检索
    """
    logger.info(f"🔍 执行新颖性判断: {patent_id}")

    # 尝试使用向量检索
    try:
        from core.tools.unified_registry import get_unified_registry

        registry = get_unified_registry()
        vector_search = registry.get("vector_search")

        if vector_search:
            # 构建查询文本
            query_text = f"{title} {abstract}"

            # 执行向量搜索
            search_results = vector_search.function(query=query_text, top_k=10)

            # 计算新颖性评分
            if search_results.get("success") and search_results.get("results"):
                similar_patents = search_results["results"]
                max_similarity = max(
                    [r.get("score", 0.0) for r in similar_patents], default=0.0
                )
                novelty_score = 1.0 - max_similarity

                return {
                    "analysis_level": "novelty",
                    "patent_id": patent_id,
                    "title": title,
                    "novelty_score": novelty_score,
                    "similar_patents_count": len(similar_patents),
                    "max_similarity": max_similarity,
                    "similar_references": [
                        {
                            "patent_id": r.get("id", "unknown"),
                            "similarity": r.get("score", 0.0),
                        }
                        for r in similar_patents[:5]
                    ],
                    "analysis_summary": f"新颖性评分: {novelty_score:.2f} (基于{len(similar_patents)}篇对比文献)",
                }
            else:
                raise Exception("向量搜索未返回有效结果")

        else:
            raise Exception("向量搜索工具不可用")

    except Exception as e:
        logger.warning(f"⚠️  向量检索失败，使用简化新颖性判断: {e}")

        # 简化新颖性判断
        novelty_score = _calculate_simple_novelty_score(title, abstract)

        return {
            "analysis_level": "novelty",
            "patent_id": patent_id,
            "title": title,
            "novelty_score": novelty_score,
            "similar_patents_count": 0,
            "max_similarity": 0.0,
            "similar_references": [],
            "analysis_summary": f"新颖性评分（简化）: {novelty_score:.2f}",
            "note": "向量检索不可用，使用简化判断方法",
        }


def _comprehensive_analysis(
    patent_id: str,
    title: str,
    abstract: str,
    claims: list[str] | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """
    综合分析：整合基础、创造性、新颖性分析
    """
    logger.info(f"📊 执行综合分析: {patent_id}")

    # 执行各维度分析
    basic_result = _basic_analysis(patent_id, title, abstract, claims, description)
    creativity_result = _creativity_analysis(patent_id, title, abstract, claims, description)
    novelty_result = _novelty_analysis(patent_id, title, abstract, claims, description)

    # 计算综合专利性评分
    patentability_score = (
        basic_result.get("feature_count", 0) * 0.1  # 技术特征数量
        + creativity_result.get("creativity_score", 0.5) * 0.5  # 创造性权重50%
        + novelty_result.get("novelty_score", 0.5) * 0.4  # 新颖性权重40%
    )

    # 归一化到0-1范围
    patentability_score = min(max(patentability_score, 0.0), 1.0)

    return {
        "analysis_level": "comprehensive",
        "patent_id": patent_id,
        "title": title,
        "patentability_score": patentability_score,
        "basic_analysis": basic_result,
        "creativity_analysis": creativity_result,
        "novelty_analysis": novelty_result,
        "recommendations": _generate_recommendations(patentability_score),
        "analysis_summary": f"综合专利性评分: {patentability_score:.2f}/1.0",
    }


# ==================== 辅助函数 ====================


def _extract_technical_features(text: str) -> list[dict[str, Any]]:
    """
    从专利文本中提取技术特征（简化版本）

    Args:
        text: 专利文本

    Returns:
        技术特征列表
    """
    features = []

    # 技术领域关键词
    field_keywords = [
        "算法",
        "系统",
        "装置",
        "方法",
        "模型",
        "网络",
        "数据",
        "处理",
        "控制",
        "分析",
    ]

    # 技术效果关键词
    effect_keywords = [
        "提高",
        "降低",
        "优化",
        "改善",
        "增强",
        "减少",
        "节约",
        "实现",
        "达到",
        "获得",
    ]

    # 简单特征提取（基于句子分割）
    sentences = text.split("。")
    for i, sentence in enumerate(sentences[:20]):  # 最多处理20个句子
        sentence = sentence.strip()
        if len(sentence) < 5:
            continue

        # 检查是否包含技术领域关键词
        has_field = any(keyword in sentence for keyword in field_keywords)

        # 检查是否包含技术效果关键词
        has_effect = any(keyword in sentence for keyword in effect_keywords)

        if has_field or has_effect:
            features.append(
                {
                    "feature_id": f"F{i+1}",
                    "text": sentence[:100],  # 限制长度
                    "type": "technical_feature",
                    "importance": "high" if has_field and has_effect else "medium",
                }
            )

    return features


def _calculate_simple_creativity_score(
    title: str, abstract: str, claims: list[str] | None = None
) -> float:
    """
    计算简化创造性评分（0-1）

    基于以下因素：
    1. 技术复杂度（关键词数量）
    2. 技术效果（效果关键词数量）
    3. 权利要求数量（如果提供）
    """
    score = 0.5  # 基础分

    text = f"{title} {abstract}"

    # 技术复杂度关键词
    complexity_keywords = [
        "创新",
        "新颖",
        "突破",
        "独特",
        "优化",
        "改进",
        "增强",
        "智能",
        "自适应",
    ]
    complexity_count = sum(1 for kw in complexity_keywords if kw in text)
    score += min(complexity_count * 0.05, 0.3)

    # 技术效果关键词
    effect_keywords = ["提高", "降低", "优化", "改善", "增强", "减少", "节约"]
    effect_count = sum(1 for kw in effect_keywords if kw in text)
    score += min(effect_count * 0.03, 0.15)

    # 权利要求数量
    if claims:
        score += min(len(claims) * 0.01, 0.05)

    return min(max(score, 0.0), 1.0)


def _calculate_simple_novelty_score(title: str, abstract: str) -> float:
    """
    计算简化新颖性评分（0-1）

    基于以下因素：
    1. 标题独特性（长度和关键词）
    2. 摘要技术细节丰富度
    """
    score = 0.5  # 基础分

    # 标题独特性
    if len(title) > 10:
        score += 0.1

    # 摘要技术细节
    technical_terms = [
        "算法",
        "系统",
        "装置",
        "方法",
        "模型",
        "网络",
        "数据",
        "处理",
        "控制",
        "分析",
    ]
    term_count = sum(1 for term in technical_terms if term in abstract)
    score += min(term_count * 0.04, 0.3)

    # 摘要长度（技术细节丰富度）
    if len(abstract) > 200:
        score += 0.1

    return min(max(score, 0.0), 1.0)


def _generate_recommendations(patentability_score: float) -> list[str]:
    """
    根据专利性评分生成建议

    Args:
        patentability_score: 专利性评分（0-1）

    Returns:
        建议列表
    """
    if patentability_score >= 0.8:
        return [
            "✅ 专利性评分优秀，建议申请专利",
            "✅ 创造性和新颖性表现良好",
            "建议：尽快完善申请文件并提交",
        ]
    elif patentability_score >= 0.6:
        return [
            "⚠️  专利性评分良好，可以申请",
            "⚠️  建议补充技术效果数据",
            "建议：进行更深入的现有技术检索",
        ]
    elif patentability_score >= 0.4:
        return [
            "❌ 专利性评分一般，需要改进",
            "❌ 创造性或新颖性不足",
            "建议：重新评估技术方案，增加创新点",
        ]
    else:
        return [
            "❌ 专利性评分较低，不建议申请",
            "❌ 缺乏足够的创造性或新颖性",
            "建议：重新设计技术方案或考虑其他保护方式",
        ]


# 导出Handler
__all__ = ["patent_analysis_handler"]
