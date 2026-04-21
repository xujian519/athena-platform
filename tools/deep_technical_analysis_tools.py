#!/usr/bin/env python3
"""
深度技术分析工具 - Deep Technical Analysis Tool

将 core/patent/xiaona_deep_technical_analyzer.py 的深度分析功能
封装为可通过工具系统调用的工具函数。

核心功能:
1. analyze_patent_text - 深度分析专利文本
2. compare_patents - 对比分析多个专利
3. extract_technical_features - 提取技术特征
4. build_knowledge_graph - 构建技术知识图谱
5. identify_innovations - 识别创新点
6. assess_complexity - 评估技术复杂度

Author: Athena Team
Date: 2026-02-24
Version: 1.0.0
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def analyze_patent_text(
    patent_text: str,
    patent_number: str = "",
    patent_title: str = "",
    patent_type: str = "target"
) -> dict[str, Any]:
    """
    深度分析专利文本

    Args:
        patent_text: 专利全文文本
        patent_number: 专利号/申请号
        patent_title: 专利标题
        patent_type: 专利类型 (target/prior_art)

    Returns:
        深度分析结果

    Example:
        >>> result = analyze_patent_text(
        ...     patent_text="权利要求书：...",
        ...     patent_number="CN123456789A",
        ...     patent_title="一种太阳能充电装置"
        ... )
        >>> print(f"技术领域: {result['technical_field']}")
        >>> print(f"技术特征数: {len(result['features'])}")
    """
    try:
        from patents.core.xiaona_deep_technical_analyzer import (
            PatentAnalysis,
            XiaonaDeepTechnicalAnalyzer,
        )

        # 创建分析器实例
        analyzer = XiaonaDeepTechnicalAnalyzer(
            output_dir="data/analysis_reports",
            use_dolphin=True,
            enable_visualization=False
        )

        # 创建专利信息字典

        # 执行分析
        analysis_result = PatentAnalysis(
            patent_number=patent_number or "UNKNOWN",
            patent_title=patent_title or "未命名专利",
            patent_type=patent_type
        )

        # 提取技术领域
        analysis_result.technical_field = analyzer._extract_technical_field(patent_text)
        analysis_result.field_keywords = analyzer._extract_field_keywords(patent_text)

        # 提取技术问题
        analysis_result.technical_problem = analyzer._extract_technical_problem(patent_text)
        analysis_result.problem_keywords = analyzer._extract_keywords(analysis_result.technical_problem)

        # 提取技术方案
        analysis_result.technical_solution = analyzer._extract_technical_solution(patent_text)
        analysis_result.solution_keywords = analyzer._extract_keywords(analysis_result.technical_solution)

        # 提取技术效果
        analysis_result.technical_effects = analyzer._extract_technical_effects(patent_text)
        analysis_result.effect_keywords = []
        for effect in analysis_result.technical_effects:
            analysis_result.effect_keywords.extend(analyzer._extract_keywords(effect))

        # 提取技术特征
        analysis_result.technical_features = analyzer._extract_technical_features(patent_text)

        # 分析权利要求
        claims_info = analyzer._analyze_claims(patent_text)
        analysis_result.independent_claims = claims_info.get("independent", 0)
        analysis_result.dependent_claims = claims_info.get("dependent", 0)
        analysis_result.total_claims = analysis_result.independent_claims + analysis_result.dependent_claims

        # 识别关键点
        analysis_result.key_technical_points = analyzer._identify_key_points(patent_text)

        # 识别创新点
        analysis_result.innovation_highlights = analyzer._identify_innovations(patent_text)

        # 评估复杂度
        complexity_info = analyzer._assess_complexity(patent_text)
        analysis_result.complexity_score = complexity_info.get("score", 0.0)
        analysis_result.complexity_factors = complexity_info.get("factors", [])

        # 分析实施方式
        implementation_info = analyzer._analyze_implementation(patent_text)
        analysis_result.implementation_details = implementation_info.get("details", "")
        analysis_result.embodiment_count = implementation_info.get("count", 0)

        # 计算置信度
        analysis_result.analysis_confidence = analyzer._calculate_confidence(analysis_result)

        # 转换为字典
        return {
            "success": True,
            "patent_number": patent_number,
            "patent_title": patent_title,
            "patent_type": patent_type,
            "analysis": analysis_result.to_dict(),
            "summary": {
                "technical_field": analysis_result.technical_field,
                "feature_count": len(analysis_result.technical_features),
                "independent_claims": analysis_result.independent_claims,
                "dependent_claims": analysis_result.dependent_claims,
                "complexity_score": analysis_result.complexity_score,
                "innovation_count": len(analysis_result.innovation_highlights)
            }
        }

    except Exception as e:
        logger.error(f"专利深度分析失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "patent_number": patent_number,
            "message": "专利深度分析失败"
        }


def compare_patents(
    target_patent: dict[str, Any],
    prior_arts: list[dict[str, Any]],
    target_text: str = "",
    prior_texts: dict[str, str] = None
) -> dict[str, Any]:
    """
    对比分析目标专利和对比文件

    Args:
        target_patent: 目标专利信息
        prior_arts: 对比文件列表
        target_text: 目标专利全文
        prior_texts: 对比文件全文映射

    Returns:
        对比分析结果

    Example:
        >>> result = compare_patents(
        ...     target_patent={"application_number": "CN123", "title": "装置A"},
        ...     prior_arts=[{"publication_number": "US456", "title": "装置B"}]
        ... )
        >>> print(f"相似度: {result['similarity_score']}")
        >>> print(f"差异点: {len(result['key_differences'])}")
    """
    try:
        from patents.core.xiaona_deep_technical_analyzer import XiaonaDeepTechnicalAnalyzer

        # 创建分析器
        analyzer = XiaonaDeepTechnicalAnalyzer(
            output_dir="data/analysis_reports",
            use_dolphin=True,
            enable_visualization=False
        )

        # 执行对比分析
        result = analyzer.analyze_target_and_prior_art(
            target_patent_info=target_patent,
            prior_art_references=prior_arts,
            target_patent_text=target_text,
            prior_art_texts=prior_texts
        )

        # 转换为字典格式
        return {
            "success": True,
            "target_patent": result.target_patent,
            "similarity_score": result.similarity_score,
            "feature_similarity": result.feature_similarity,
            "key_differences": result.key_differences,
            "potential_issues": result.potential_issues,
            "innovation_summary": result.innovation_summary,
            "analysis": result.to_dict()
        }

    except Exception as e:
        logger.error(f"对比分析失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "对比分析失败"
        }


def extract_technical_features(
    patent_text: str,
    include_graph_analysis: bool = False
) -> dict[str, Any]:
    """
    提取技术特征并构建知识图谱

    Args:
        patent_text: 专利文本
        include_graph_analysis: 是否包含图谱分析

    Returns:
        技术特征和图谱信息

    Example:
        >>> result = extract_technical_features(patent_text)
        >>> print(f"提取特征数: {len(result['features'])}")
        >>> print(f"核心特征: {result['core_features']}")
    """
    try:
        from patents.core.xiaona_deep_technical_analyzer import (
            PatentAnalysis,
            XiaonaDeepTechnicalAnalyzer,
        )

        analyzer = XiaonaDeepTechnicalAnalyzer()

        # 创建专利分析对象
        analysis = PatentAnalysis(
            patent_number="UNKNOWN",
            patent_title="特征提取",
            patent_type="extraction"
        )

        # 提取技术特征
        analysis.technical_features = analyzer._extract_technical_features(patent_text)

        # 构建知识图谱
        if include_graph_analysis:
            knowledge_graph = analyzer._build_technical_knowledge_graph(
                analysis,
                patent_text
            )
            analysis.knowledge_graph = knowledge_graph

        # 提取问题-特征-效果三元关系
        triples = analyzer._extract_problem_feature_effect_triples(
            analysis,
            patent_text
        )
        analysis.problem_effect_triples = triples

        # 提取特征关系
        relations = analyzer._identify_feature_relations(
            analysis,
            patent_text
        )
        analysis.feature_relations = relations

        # 计算图谱中心性
        if analysis.knowledge_graph:
            graph = analysis.knowledge_graph.to_networkx_graph()
            centrality = analyzer._calculate_graph_centrality(graph)
            analysis.graph_centrality_ranking = centrality

            # 识别核心创新特征
            core_features = analyzer._identify_core_innovations(
                graph,
                centrality
            )
            analysis.core_innovation_features = core_features

        # 转换为字典
        result_dict = analysis.to_dict()

        return {
            "success": True,
            "features": [
                {
                    "id": f.feature_id,
                    "name": f.feature_name,
                    "type": f.feature_type,
                    "description": f.description,
                    "importance": f.importance,
                    "novelty": f.novelty_level
                }
                for f in analysis.technical_features
            ],
            "feature_count": len(analysis.technical_features),
            "knowledge_graph": result_dict.get("knowledge_graph"),
            "problem_effect_triples": [
                {
                    "problem": t.technical_problem,
                    "feature": t.technical_feature,
                    "effect": t.technical_effect
                }
                for t in analysis.problem_effect_triples
            ],
            "feature_relations": [
                {
                    "from": r.source_feature,
                    "to": r.target_feature,
                    "type": r.relation_type
                }
                for r in analysis.feature_relations
            ],
            "core_features": analysis.core_innovation_features,
            "graph_centrality": analysis.graph_centrality_ranking[:10] if analysis.graph_centrality_ranking else []
        }

    except Exception as e:
        logger.error(f"技术特征提取失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "features": []
        }


def identify_innovations(
    patent_text: str,
    min_importance: float = 0.5
) -> dict[str, Any]:
    """
    识别专利创新点

    Args:
        patent_text: 专利文本
        min_importance: 最低重要性阈值

    Returns:
        创新点分析结果

    Example:
        >>> result = identify_innovations(patent_text)
        >>> print(f"创新点数: {len(result['innovations'])}")
        >>> for innovation in result['innovations']:
        ...     print(f"- {innovation}")
    """
    try:
        from patents.core.xiaona_deep_technical_analyzer import (
            PatentAnalysis,
            XiaonaDeepTechnicalAnalyzer,
        )

        analyzer = XiaonaDeepTechnicalAnalyzer()

        # 创建分析对象
        analysis = PatentAnalysis(
            patent_number="UNKNOWN",
            patent_title="创新点识别",
            patent_type="innovation_analysis"
        )

        # 识别创新点
        innovations = analyzer._identify_innovations(patent_text)

        # 过滤低重要性创新点
        filtered_innovations = [
            inv for inv in innovations
            if any(f.importance >= min_importance for f in analysis.technical_features)
        ]

        # 识别关键点
        key_points = analyzer._identify_key_points(patent_text)

        return {
            "success": True,
            "innovations": filtered_innovations,
            "innovation_count": len(filtered_innovations),
            "key_points": key_points,
            "min_importance_threshold": min_importance
        }

    except Exception as e:
        logger.error(f"创新点识别失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "innovations": [],
            "key_points": []
        }


def assess_complexity(
    patent_text: str
) -> dict[str, Any]:
    """
    评估专利技术复杂度

    Args:
        patent_text: 专利文本

    Returns:
        复杂度评估结果

    Example:
        >>> result = assess_complexity(patent_text)
        >>> print(f"复杂度得分: {result['complexity_score']}")
        >>> print(f"复杂因素: {result['complexity_factors']}")
    """
    try:
        from patents.core.xiaona_deep_technical_analyzer import XiaonaDeepTechnicalAnalyzer

        analyzer = XiaonaDeepTechnicalAnalyzer()

        # 评估复杂度
        complexity_info = analyzer._assess_complexity(patent_text)

        return {
            "success": True,
            **complexity_info
        }

    except Exception as e:
        logger.error(f"复杂度评估失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "complexity_score": 0.0,
            "complexity_factors": []
        }


# 导出函数列表
__all__ = [
    "analyze_patent_text",
    "compare_patents",
    "extract_technical_features",
    "identify_innovations",
    "assess_complexity"
]


# 测试代码
if __name__ == "__main__":
    print("=" * 80)
    print("🔬 深度技术分析工具测试")
    print("=" * 80)
    print()

    # 测试样本专利文本
    sample_patent = """
    权利要求书：
    1. 一种智能光伏充电控制系统，其特征在于包括：
        光伏板阵列，用于将太阳能转换为电能；
        MPPT控制器，与所述光伏板阵列电连接，用于实现最大功率点跟踪；
        蓄电池组，用于存储电能；
        智能控制单元，分别与所述MPPT控制器和蓄电池组电连接，
        所述智能控制单元包括：
        - 充电管理模块，用于根据电池状态动态调整充电策略；
        - 放电管理模块，用于优化放电效率；
        - 保护模块，用于监测和控制系统故障。

    2. 根据权利要求1所述的智能光伏充电控制系统，其特征在于：
        所述充电管理模块采用自适应充电算法，
        根据蓄电池的温度和荷电状态实时调整充电电流。

    说明书：
    技术领域：本发明涉及新能源技术领域，具体涉及一种光伏发电系统。

    技术问题：现有光伏充电系统存在充电效率低、电池寿命短的问题。

    技术方案：本发明通过引入MPPT技术和智能控制算法，
    实现了充电效率和电池寿命的双重提升。

    技术效果：充电效率提升25%，电池寿命延长30%。
    """.strip()

    # 测试1: 深度分析
    print("📊 测试1: 深度专利分析")
    result = analyze_patent_text(
        patent_text=sample_patent,
        patent_number="CN202310123456.7",
        patent_title="智能光伏充电控制系统",
        patent_type="target"
    )

    if result["success"]:
        summary = result["summary"]
        print("   成功: True")
        print(f"   技术领域: {summary['technical_field']}")
        print(f"   特征数: {summary['feature_count']}")
        print(f"   复杂度得分: {summary['complexity_score']:.2f}")
        print(f"   创新点数: {summary['innovation_count']}")
    else:
        print(f"   失败: {result.get('error')}")
    print()

    # 测试2: 技术特征提取
    print("🔧 测试2: 技术特征提取")
    result = extract_technical_features(sample_patent, include_graph_analysis=True)

    if result["success"]:
        print("   成功: True")
        print(f"   特征数: {result['feature_count']}")
        print(f"   核心特征: {len(result.get('core_features', []))}")
        print(f"   三元关系: {len(result.get('problem_effect_triples', []))}")
    else:
        print(f"   失败: {result.get('error')}")
    print()

    # 测试3: 创新点识别
    print("💡 测试3: 创新点识别")
    result = identify_innovations(sample_patent, min_importance=0.3)

    if result["success"]:
        print("   成功: True")
        print(f"   创新点数: {result['innovation_count']}")
        print(f"   关键点数: {len(result['key_points'])}")
        for innovation in result["innovations"][:3]:
            print(f"   - {innovation}")
    else:
        print(f"   失败: {result.get('error')}")
    print()

    # 测试4: 复杂度评估
    print("📈 测试4: 复杂度评估")
    result = assess_complexity(sample_patent)

    if result["success"]:
        print("   成功: True")
        print(f"   复杂度得分: {result['complexity_score']:.2f}")
        print(f"   复杂因素数: {len(result['complexity_factors'])}")
        for factor in result["complexity_factors"][:3]:
            print(f"   - {factor}")
    else:
        print(f"   失败: {result.get('error')}")
    print()

    print("=" * 80)
    print("✅ 测试完成")
    print("=" * 80)
