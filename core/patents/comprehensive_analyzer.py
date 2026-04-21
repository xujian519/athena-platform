#!/usr/bin/env python3
from __future__ import annotations
"""
综合专利分析系统
Comprehensive Patent Analysis System

整合钱学森"定性定量相结合"和王立铭"负熵优化"思想:
- 定性分析:基于专家规则的专利性判断
- 定量分析:基于数据统计的相似度计算
- 负熵优化:从混乱信息中提取有序结论
- 置信度量化:综合定性定量结果的置信度

作者: 小诺·双鱼公主
创建时间: 2025-12-24
版本: v0.1.2 "晨星初现"
"""

import logging

# 导入相关模块
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.biology.negentropy_optimizer import NegentropyMetric, get_negentropy_optimizer
from core.patents.negentropy_retrieval import RetrievalQuery, get_negentropy_retrieval_system
from core.patents.qualitative_rules import get_qualitative_rule_engine

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class AnalysisAspect(Enum):
    """分析维度"""

    NOVELTY = "novelty"  # 新颖性
    INVENTIVENESS = "inventiveness"  # 创造性
    UTILITY = "utility"  # 实用性
    VALIDITY = "validity"  # 有效性
    INFRINGEMENT = "infringement"  # 侵权风险


@dataclass
class QualitativeAnalysisResult:
    """定性分析结果"""

    aspect: AnalysisAspect
    applied_rules: list[dict[str, Any]]
    positive_score: float
    negative_score: float
    net_score: float
    conclusion: str
    confidence: float


@dataclass
class QuantitativeAnalysisResult:
    """定量分析结果"""

    aspect: AnalysisAspect
    similarity_scores: list[float]  # 相似度分数列表
    avg_similarity: float  # 平均相似度
    max_similarity: float  # 最大相似度
    similar_references: list[str]  # 相似参考
    statistical_significance: float  # 统计显著性


@dataclass
class PatentAnalysisReport:
    """综合分析报告"""

    patent_id: str
    patent_title: str
    analysis_time: str

    # 各维度分析结果
    novelty: dict[str, Any] | None = None
    inventiveness: dict[str, Any] | None = None
    utility: dict[str, Any] | None = None

    # 综合评估
    overall_assessment: str = ""
    overall_confidence: float = 0.0
    patentability_score: float = 0.0  # 专利性得分

    # 负熵指标
    information_negentropy: float = 0.0
    analysis_quality: float = 0.0

    # 建议
    recommendations: list[str] = field(default_factory=list)
    risk_warnings: list[str] = field(default_factory=list)


class ComprehensivePatentAnalyzer:
    """
    综合专利分析系统

    核心思想:
    1. 定性分析:专家规则判断(30%权重)
    2. 定量分析:数据统计计算(50%权重)
    3. 负熵优化:信息熵减度量(20%权重)
    4. 综合判断:加权融合结果
    """

    def __init__(self):
        """初始化分析系统"""
        self.name = "综合专利分析系统"
        self.version = "v0.1.2"

        # 子系统
        self.qualitative_engine = get_qualitative_rule_engine()
        self.retrieval_system = get_negentropy_retrieval_system()
        self.negentropy_optimizer = get_negentropy_optimizer()

        logger.info(f"📊 {self.name} ({self.version}) 初始化完成")

    async def analyze_patent(
        self, patent_info: dict[str, Any], aspects: list[AnalysisAspect] | None = None
    ) -> PatentAnalysisReport:
        """
        综合分析专利

        Args:
            patent_info: 专利信息,包含:
                - patent_id: 专利号
                - title: 标题
                - abstract: 摘要
                - claims: 权利要求
                - description: 说明书
                - technical_field: 技术领域
            aspects: 分析维度列表(默认全部)

        Returns:
            分析报告
        """
        aspects = aspects or [
            AnalysisAspect.NOVELTY,
            AnalysisAspect.INVENTIVENESS,
            AnalysisAspect.UTILITY,
        ]

        start_time = datetime.now()

        # 初始化报告
        report = PatentAnalysisReport(
            patent_id=patent_info.get("patent_id", "UNKNOWN"),
            patent_title=patent_info.get("title", ""),
            analysis_time=start_time.isoformat(),
        )

        # 分析各维度
        for aspect in aspects:
            if aspect == AnalysisAspect.NOVELTY:
                report.novelty = await self._analyze_novelty(patent_info)
            elif aspect == AnalysisAspect.INVENTIVENESS:
                report.inventiveness = await self._analyze_inventiveness(patent_info)
            elif aspect == AnalysisAspect.UTILITY:
                report.utility = await self._analyze_utility(patent_info)

        # 计算综合评估
        self._calculate_overall_assessment(report)

        # 生成建议和警告
        self._generate_recommendations(report)

        analysis_time = (datetime.now() - start_time).total_seconds()

        logger.info(
            f"📊 专利分析完成: {report.patent_title} "
            f"(专利性得分: {report.patentability_score:.2f}, "
            f"置信度: {report.overall_confidence:.2f}, "
            f"耗时: {analysis_time:.2f}秒)"
        )

        return report

    async def _analyze_novelty(self, patent_info: dict[str, Any]) -> dict[str, Any]:
        """分析新颖性"""
        # 1. 定性分析
        qualitative_context = {
            "invention": patent_info.get("abstract", ""),
            "technical_field": patent_info.get("technical_field", ""),
            "differences": patent_info.get("differences", []),
            "prior_art_contains_all": False,
        }

        qualitative_result = self.qualitative_engine.analyze_novelty(qualitative_context)

        # 2. 定量分析:检索现有技术
        query = RetrievalQuery(
            query_text=patent_info.get("title", ""),
            technical_field=patent_info.get("technical_field", ""),
            keywords=self._extract_keywords(patent_info),
            retrieval_method="hybrid",
        )

        retrieval_result = self.retrieval_system.retrieve(query)

        quantitative_result = QuantitativeAnalysisResult(
            aspect=AnalysisAspect.NOVELTY,
            similarity_scores=[p.relevance_score for p in retrieval_result.results[:10]],
            avg_similarity=retrieval_result.avg_relevance,
            max_similarity=(
                retrieval_result.results[0].relevance_score if retrieval_result.results else 0
            ),
            similar_references=[p.patent_id for p in retrieval_result.results[:5]],
            statistical_significance=self._calculate_significance(retrieval_result.results),
        )

        # 3. 负熵分析
        if retrieval_result.results:
            input_entropies = [p.information_entropy for p in retrieval_result.results]
            negentropy = self.negentropy_optimizer.measure_negentropy(
                input_data=input_entropies,
                output_data=sorted(input_entropies),
                metric_type=NegentropyMetric.INFORMATION_ENTROPY,
            )
        else:
            negentropy = None

        # 4. 综合判断
        novelty_score = (
            qualitative_result.net_score * 0.3
            + (1 - quantitative_result.avg_similarity) * 0.5
            + (negentropy.negentropy if negentropy else 0) * 0.2
        )

        return {
            "qualitative": {
                "net_score": qualitative_result.net_score,
                "conclusion": qualitative_result.conclusion,
                "confidence": qualitative_result.confidence,
            },
            "quantitative": {
                "avg_similarity": quantitative_result.avg_similarity,
                "max_similarity": quantitative_result.max_similarity,
                "similar_references": quantitative_result.similar_references,
            },
            "negentropy": negentropy.negentropy if negentropy else 0,
            "novelty_score": max(0, min(1, novelty_score)),
            "conclusion": self._generate_novelty_conclusion(novelty_score),
        }

    async def _analyze_inventiveness(self, patent_info: dict[str, Any]) -> dict[str, Any]:
        """分析创造性"""
        # 1. 定性分析
        qualitative_context = {
            "invention": patent_info.get("abstract", ""),
            "technical_field": patent_info.get("technical_field", ""),
            "technical_effect": patent_info.get("advantages", ""),
            "obviousness": patent_info.get("obviousness", False),
        }

        qualitative_result = self.qualitative_engine.analyze_inventiveness(qualitative_context)

        # 2. 定量分析:技术效果量化
        advantages = patent_info.get("advantages", "")
        performance_improvement = self._extract_performance_improvement(advantages)

        # 3. 综合判断
        inventiveness_score = (
            qualitative_result.net_score * 0.6 + min(1.0, performance_improvement / 100) * 0.4
        )

        return {
            "qualitative": {
                "net_score": qualitative_result.net_score,
                "conclusion": qualitative_result.conclusion,
                "confidence": qualitative_result.confidence,
            },
            "quantitative": {"performance_improvement": performance_improvement},
            "inventiveness_score": max(0, min(1, inventiveness_score)),
            "conclusion": self._generate_inventiveness_conclusion(inventiveness_score),
        }

    async def _analyze_utility(self, patent_info: dict[str, Any]) -> dict[str, Any]:
        """分析实用性"""
        # 1. 定性分析
        qualitative_context = {
            "invention": patent_info.get("abstract", ""),
            "manufacturability": bool(patent_info.get("embodiments")),
            "usability": bool(patent_info.get("application")),
            "beneficial_effect": bool(patent_info.get("advantages")),
        }

        qualitative_result = self.qualitative_engine.analyze_utility(qualitative_context)

        # 2. 定量分析:实施可行性
        embodiments_detail = len(patent_info.get("embodiments", ""))
        description_length = len(patent_info.get("description", ""))

        feasibility_score = min(
            1.0, (embodiments_detail / 1000 * 0.5 + description_length / 5000 * 0.5)
        )

        # 3. 综合判断
        utility_score = qualitative_result.net_score * 0.7 + feasibility_score * 0.3

        return {
            "qualitative": {
                "net_score": qualitative_result.net_score,
                "conclusion": qualitative_result.conclusion,
                "confidence": qualitative_result.confidence,
            },
            "quantitative": {
                "embodiments_detail": embodiments_detail,
                "description_length": description_length,
                "feasibility_score": feasibility_score,
            },
            "utility_score": max(0, min(1, utility_score)),
            "conclusion": self._generate_utility_conclusion(utility_score),
        }

    def _calculate_overall_assessment(self, report: PatentAnalysisReport) -> None:
        """计算综合评估"""
        # 加权计算专利性得分
        weights = {"novelty": 0.4, "inventiveness": 0.4, "utility": 0.2}

        patentability = 0.0
        total_weight = 0.0

        if report.novelty:
            patentability += report.novelty["novelty_score"] * weights["novelty"]
            total_weight += weights["novelty"]

        if report.inventiveness:
            patentability += report.inventiveness["inventiveness_score"] * weights["inventiveness"]
            total_weight += weights["inventiveness"]

        if report.utility:
            patentability += report.utility["utility_score"] * weights["utility"]
            total_weight += weights["utility"]

        report.patentability_score = patentability / total_weight if total_weight > 0 else 0

        # 计算负熵质量
        negentropy_sum = 0
        count = 0
        for aspect in [report.novelty, report.inventiveness, report.utility]:
            if aspect and "negentropy" in aspect:
                negentropy_sum += aspect["negentropy"]
                count += 1

        report.information_negentropy = negentropy_sum / count if count > 0 else 0

        # 计算综合置信度
        confidences = []
        for aspect in [report.novelty, report.inventiveness, report.utility]:
            if aspect and "qualitative" in aspect:
                confidences.append(aspect["qualitative"]["confidence"])

        report.overall_confidence = sum(confidences) / len(confidences) if confidences else 0.5

        # 生成综合评估结论
        if report.patentability_score >= 0.7:
            report.overall_assessment = "建议申请:具备较高的专利性"
        elif report.patentability_score >= 0.5:
            report.overall_assessment = "可以考虑申请:专利性中等,建议优化"
        else:
            report.overall_assessment = "不建议申请:专利性较低,需要重大改进"

        # 分析质量(负熵质量)
        report.analysis_quality = min(1.0, report.information_negentropy * 2)

    def _generate_recommendations(self, report: PatentAnalysisReport) -> None:
        """生成建议和警告"""
        # 基于各维度分析生成建议

        if report.novelty and report.novelty["novelty_score"] < 0.5:
            report.recommendations.append("建议强化区别技术特征的描述,提高新颖性")

        if report.inventiveness and report.inventiveness["inventiveness_score"] < 0.5:
            report.recommendations.append("建议强调技术效果和非显而易见性,提高创造性")

        if report.utility and report.utility["utility_score"] < 0.5:
            report.recommendations.append("建议补充具体实施方式,提高实用性")

        if report.overall_confidence < 0.7:
            report.risk_warnings.append("分析置信度较低,建议进一步检索现有技术")

        if report.novelty and report.novelty["quantitative"]["max_similarity"] > 0.8:
            report.risk_warnings.append("存在高度相似的现有技术,请注意新颖性风险")

    def _extract_keywords(self, patent_info: dict[str, Any]) -> list[str]:
        """提取关键词"""
        keywords = []

        # 从标题中提取
        title = patent_info.get("title", "")
        keywords.extend(title.split())

        # 从摘要中提取高频词(简化)
        abstract = patent_info.get("abstract", "")
        words = abstract.split()
        from collections import Counter

        word_counts = Counter(words)
        keywords.extend([w for w, c in word_counts.most_common(10)])

        return list(set(keywords))

    def _extract_performance_improvement(self, advantages: str) -> float:
        """从有益效果中提取性能提升百分比"""
        import re

        # 查找百分比数字
        matches = re.findall(r"(\d+(?:\.\d+)?)\s*%", advantages)

        if matches:
            # 取最大的提升百分比
            return max(float(m) for m in matches)

        return 0.0

    def _calculate_significance(self, results: list[Any]) -> float:
        """计算统计显著性"""
        if not results:
            return 0.0

        # 简化实现:基于结果数量和平均相似度
        count = len(results)
        avg_score = sum(r.relevance_score for r in results) / count if count > 0 else 0

        # 结果越多且相似度越高,显著性越高
        return min(1.0, (count / 20) * avg_score)

    def _generate_novelty_conclusion(self, score: float) -> str:
        """生成新颖性结论"""
        if score >= 0.7:
            return "具备新颖性"
        elif score >= 0.4:
            return "新颖性一般,建议优化区别特征描述"
        else:
            return "新颖性不足,存在被驳回风险"

    def _generate_inventiveness_conclusion(self, score: float) -> str:
        """生成创造性结论"""
        if score >= 0.7:
            return "具备创造性"
        elif score >= 0.4:
            return "创造性一般,建议强调技术效果"
        else:
            return "创造性不足,可能被视为显而易见"

    def _generate_utility_conclusion(self, score: float) -> str:
        """生成实用性结论"""
        if score >= 0.7:
            return "具备实用性"
        elif score >= 0.4:
            return "实用性基本满足,建议补充实施细节"
        else:
            return "实用性不足,缺乏具体实施方式"

    def format_report(self, report: PatentAnalysisReport) -> str:
        """格式化报告输出"""
        output = []

        output.append("=" * 60)
        output.append("📊 专利综合分析报告")
        output.append("=" * 60)
        output.append(f"\n专利号: {report.patent_id}")
        output.append(f"标题: {report.patent_title}")
        output.append(f"分析时间: {report.analysis_time}\n")

        output.append("-" * 60)
        output.append("[综合评估]")
        output.append("-" * 60)
        output.append(f"专利性得分: {report.patentability_score:.2f}")
        output.append(f"综合评估: {report.overall_assessment}")
        output.append(f"置信度: {report.overall_confidence:.2f}")
        output.append(f"分析质量: {report.analysis_quality:.2f}\n")

        if report.novelty:
            output.append("-" * 60)
            output.append("[新颖性分析]")
            output.append("-" * 60)
            output.append(f"新颖性得分: {report.novelty['novelty_score']:.2f}")
            output.append(f"结论: {report.novelty['conclusion']}")
            output.append(f"平均相似度: {report.novelty['quantitative']['avg_similarity']:.2f}")
            output.append(
                f"相似参考: {', '.join(report.novelty['quantitative']['similar_references'])}\n"
            )

        if report.inventiveness:
            output.append("-" * 60)
            output.append("[创造性分析]")
            output.append("-" * 60)
            output.append(f"创造性得分: {report.inventiveness['inventiveness_score']:.2f}")
            output.append(f"结论: {report.inventiveness['conclusion']}\n")

        if report.utility:
            output.append("-" * 60)
            output.append("[实用性分析]")
            output.append("-" * 60)
            output.append(f"实用性得分: {report.utility['utility_score']:.2f}")
            output.append(f"结论: {report.utility['conclusion']}\n")

        if report.recommendations:
            output.append("-" * 60)
            output.append("[改进建议]")
            output.append("-" * 60)
            for rec in report.recommendations:
                output.append(f"• {rec}")
            output.append("")

        if report.risk_warnings:
            output.append("-" * 60)
            output.append("[风险警告]")
            output.append("-" * 60)
            for warning in report.risk_warnings:
                output.append(f"⚠️ {warning}")
            output.append("")

        return "\n".join(output)


# 全局单例
_comprehensive_analyzer_instance = None


def get_comprehensive_patent_analyzer() -> ComprehensivePatentAnalyzer:
    """获取综合专利分析器单例"""
    global _comprehensive_analyzer_instance
    if _comprehensive_analyzer_instance is None:
        _comprehensive_analyzer_instance = ComprehensivePatentAnalyzer()
    return _comprehensive_analyzer_instance


# 测试代码
async def main():
    """测试综合专利分析系统"""

    print("\n" + "=" * 60)
    print("📊 综合专利分析系统测试")
    print("=" * 60 + "\n")

    analyzer = get_comprehensive_patent_analyzer()

    # 测试专利信息
    patent_info = {
        "patent_id": "CN202310000001",
        "title": "基于深度学习的图像识别方法",
        "abstract": "本发明公开了一种基于深度学习的图像识别方法,采用改进的卷积神经网络结构,引入注意力机制和特征金字塔,解决了现有技术中识别准确率不高的问题。",
        "claims": [
            "1. 一种基于深度学习的图像识别方法,其特征在于,包括:构建卷积神经网络模型;引入注意力机制;使用特征金字塔融合多尺度特征。"
        ],
        "description": "本发明涉及计算机视觉技术领域...",
        "technical_field": "计算机视觉",
        "advantages": "识别准确率提升30%,处理速度提升50%",
        "embodiments": "实施例1:使用PyTorch实现...具体步骤包括...",
        "obviousness": False,
    }

    print("📝 测试1: 综合专利分析")

    report = await analyzer.analyze_patent(patent_info)

    # 打印格式化报告
    print(analyzer.format_report(report))

    print("✅ 测试完成!")


# 入口点: @async_main装饰器已添加到main函数
