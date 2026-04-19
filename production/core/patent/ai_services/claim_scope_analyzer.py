"""
权利要求保护范围测量系统 v1.0

基于论文"A novel approach to measuring the scope of patent claims based on
probabilities obtained from (large) language models"(2023)

核心原理:
- 信息论方法: Scope = 1 / Self-Information(claim)
- 自信息: I(x) = -log(P(x))
- LLM估算概率: P(claim) 表示权利要求文本的出现概率

关键发现:
- 越"惊喜"的权利要求(低概率) → 越窄的保护范围
- 越"常见"的权利要求(高概率) → 越宽的保护范围
- 字符数比词数更可靠
- LLM优于词频/字符统计模型

作者: Athena平台
版本: v1.0
日期: 2026-03-23
"""

from __future__ import annotations
import json
import logging
import math
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"           # 低风险: 保护范围宽，侵权风险低
    MEDIUM = "medium"     # 中风险: 保护范围适中
    HIGH = "high"         # 高风险: 保护范围窄，易被规避
    VERY_HIGH = "very_high"  # 极高风险: 范围过窄，几乎无保护


class AnalysisMode(Enum):
    """分析模式"""
    FAST = "fast"           # 快速模式: 使用本地模型
    BALANCED = "balanced"   # 平衡模式: 混合策略
    ACCURATE = "accurate"   # 精确模式: 使用高质量模型


@dataclass
class ScopeScore:
    """范围评分"""
    raw_score: float          # 原始得分 (0-100)
    normalized_score: float   # 归一化得分 (0-100)
    confidence: float         # 置信度 (0-1)

    def to_dict(self) -> dict:
        return {
            "raw_score": self.raw_score,
            "normalized_score": self.normalized_score,
            "confidence": self.confidence
        }


@dataclass
class ProbabilityEstimate:
    """概率估算结果"""
    probability: float        # LLM估算的概率
    log_probability: float    # log概率
    self_information: float   # 自信息 -log2(P)
    method: str               # 估算方法
    model_used: str           # 使用的模型

    def to_dict(self) -> dict:
        return {
            "probability": self.probability,
            "log_probability": self.log_probability,
            "self_information": self.self_information,
            "method": self.method,
            "model_used": self.model_used
        }


@dataclass
class ScopeAnalysisResult:
    """范围分析结果"""
    claim_text: str                           # 原始权利要求
    claim_number: int                         # 权利要求编号

    # 核心指标
    scope_score: ScopeScore                   # 范围得分
    probability_estimate: ProbabilityEstimate # 概率估算
    risk_level: RiskLevel                     # 风险等级

    # 辅助指标
    character_count: int                      # 字符数
    word_count: int                           # 词数
    technical_term_count: int                 # 技术术语数
    parameter_count: int                      # 参数限定数

    # 分析详情
    narrowing_factors: list[str] = field(default_factory=list)   # 缩小范围因素
    broadening_factors: list[str] = field(default_factory=list)  # 扩大范围因素
    recommendations: list[str] = field(default_factory=list)     # 优化建议

    # 对比信息
    baseline_comparison: dict[str, float] | None = None      # 与基准对比

    def to_dict(self) -> dict:
        return {
            "claim_text": self.claim_text,
            "claim_number": self.claim_number,
            "scope_score": self.scope_score.to_dict(),
            "probability_estimate": self.probability_estimate.to_dict(),
            "risk_level": self.risk_level.value,
            "character_count": self.character_count,
            "word_count": self.word_count,
            "technical_term_count": self.technical_term_count,
            "parameter_count": self.parameter_count,
            "narrowing_factors": self.narrowing_factors,
            "broadening_factors": self.broadening_factors,
            "recommendations": self.recommendations,
            "baseline_comparison": self.baseline_comparison
        }

    def get_summary(self) -> str:
        """获取分析摘要"""
        return (
            f"权利要求{self.claim_number}: 范围得分 {self.scope_score.normalized_score:.1f}/100, "
            f"风险等级: {self.risk_level.value}"
        )


@dataclass
class ScopeComparison:
    """范围比较结果"""
    claim_number: int
    scope_score: float
    relative_rank: int        # 在比较组中的排名
    is_broadest: bool         # 是否最宽
    is_narrowest: bool        # 是否最窄
    difference_from_average: float  # 与平均值的差异


class ClaimScopeAnalyzer:
    """
    权利要求保护范围测量系统

    基于信息论原理，使用LLM计算权利要求文本的概率，
    从而量化评估保护范围。

    使用模型:
    - 快速模式: qwen3.5 (本地)
    - 精确模式: deepseek-reasoner (云端)
    """

    # 模型配置
    MODEL_CONFIG = {
        "fast": {
            "model": "qwen3.5",
            "temperature": 0.1,
            "description": "本地模型快速分析"
        },
        "accurate": {
            "model": "deepseek-reasoner",
            "temperature": 0.1,
            "description": "云端模型精确分析"
        }
    }

    # 风险等级阈值 (基于论文测试结果)
    RISK_THRESHOLDS = {
        # 范围得分 -> 风险等级
        70: RiskLevel.LOW,        # >70: 低风险 (宽保护)
        50: RiskLevel.MEDIUM,     # 50-70: 中风险
        30: RiskLevel.HIGH,       # 30-50: 高风险 (窄保护)
        0: RiskLevel.VERY_HIGH    # <30: 极高风险
    }

    def __init__(self, llm_manager=None):
        """
        初始化范围分析器

        Args:
            llm_manager: LLM管理器实例
        """
        self.llm_manager = llm_manager
        self._init_patterns()

    def _init_patterns(self):
        """初始化匹配模式"""
        # 缩小范围的模式
        self.narrowing_patterns = [
            (r'至少[一二三四五六七八九十\d]+[个项]', '数量下限限定'),
            (r'不大于[一二三四五六七八九十\d]+', '数值上限限定'),
            (r'不小于[一二三四五六七八九十\d]+', '数值下限限定'),
            (r'\d+[-~]\d+', '数值范围限定'),
            (r'优选地?', '优选方案限定'),
            (r'具体地?', '具体实施限定'),
            (r'所述\w+包括', '从属限定'),
            (r'其中.*为', '属性限定'),
            (r'由\.\.\.组成', '封闭式表达'),
        ]

        # 扩大范围的模式
        self.broadening_patterns = [
            (r'包括但不限于', '开放式表达'),
            (r'例如', '示例性表达'),
            (r'等', '概括性表达'),
            (r'和/或', '选择性表达'),
            (r'至少一个', '最小化限定'),
            (r'或多个', '弹性限定'),
        ]

        # 技术术语模式
        self.tech_term_patterns = [
            r'[^\s]{2,}(?:装置|系统|方法|设备|组件|模块|单元|部件)',
            r'[^\s]{2,}(?:器|件|体|管|板|架|套)',
        ]

    async def analyze_scope(
        self,
        claim_text: str,
        claim_number: int = 1,
        mode: Literal["fast", "balanced", "accurate"] = "balanced"
    ) -> ScopeAnalysisResult:
        """
        分析单个权利要求的保护范围

        Args:
            claim_text: 权利要求文本
            claim_number: 权利要求编号
            mode: 分析模式 (fast/balanced/accurate)

        Returns:
            ScopeAnalysisResult: 分析结果
        """
        logger.info(f"开始分析权利要求{claim_number}, 模式: {mode}")

        # 1. 基础文本统计
        char_count = len(claim_text.replace(" ", "").replace("\n", ""))
        word_count = len(claim_text.split())
        tech_term_count = self._count_technical_terms(claim_text)
        param_count = self._count_parameters(claim_text)

        # 2. 识别范围影响因素
        narrowing_factors = self._identify_narrowing_factors(claim_text)
        broadening_factors = self._identify_broadening_factors(claim_text)

        # 3. 使用LLM估算概率
        probability_estimate = await self._estimate_probability(claim_text, mode)

        # 4. 计算范围得分
        scope_score = self._calculate_scope_score(
            probability_estimate=probability_estimate,
            character_count=char_count,
            narrowing_count=len(narrowing_factors),
            broadening_count=len(broadening_factors)
        )

        # 5. 确定风险等级
        risk_level = self._determine_risk_level(scope_score.normalized_score)

        # 6. 生成优化建议
        recommendations = self._generate_recommendations(
            scope_score=scope_score,
            risk_level=risk_level,
            narrowing_factors=narrowing_factors,
            broadening_factors=broadening_factors
        )

        return ScopeAnalysisResult(
            claim_text=claim_text,
            claim_number=claim_number,
            scope_score=scope_score,
            probability_estimate=probability_estimate,
            risk_level=risk_level,
            character_count=char_count,
            word_count=word_count,
            technical_term_count=tech_term_count,
            parameter_count=param_count,
            narrowing_factors=narrowing_factors,
            broadening_factors=broadening_factors,
            recommendations=recommendations
        )

    async def compare_claims(
        self,
        claims: list[str],
        mode: Literal["fast", "balanced", "accurate"] = "balanced"
    ) -> list[ScopeComparison]:
        """
        批量比较多个权利要求的保护范围

        Args:
            claims: 权利要求文本列表
            mode: 分析模式

        Returns:
            List[ScopeComparison]: 比较结果列表
        """
        results = []
        scope_scores = []

        # 分析每个权利要求
        for i, claim_text in enumerate(claims):
            result = await self.analyze_scope(claim_text, i + 1, mode)
            scope_scores.append(result.scope_score.normalized_score)
            results.append(result)

        # 计算统计量
        avg_score = sum(scope_scores) / len(scope_scores) if scope_scores else 0
        max_score = max(scope_scores) if scope_scores else 0
        min_score = min(scope_scores) if scope_scores else 0

        # 排序并创建比较结果
        sorted_indices = sorted(range(len(scope_scores)), key=lambda i: scope_scores[i], reverse=True)

        comparisons = []
        for rank, idx in enumerate(sorted_indices):
            score = scope_scores[idx]
            comparisons.append(ScopeComparison(
                claim_number=idx + 1,
                scope_score=score,
                relative_rank=rank + 1,
                is_broadest=(score == max_score),
                is_narrowest=(score == min_score),
                difference_from_average=score - avg_score
            ))

        return comparisons

    async def analyze_claims_set(
        self,
        claims: list[dict[str, Any]],
        mode: Literal["fast", "balanced", "accurate"] = "balanced"
    ) -> dict[str, Any]:
        """
        分析权利要求集合

        Args:
            claims: 权利要求列表 [{"text": "...", "number": 1, "type": "independent"}, ...]
            mode: 分析模式

        Returns:
            完整分析报告
        """
        results = []

        for claim_data in claims:
            claim_text = claim_data.get("text", "")
            claim_number = claim_data.get("number", len(results) + 1)

            result = await self.analyze_scope(claim_text, claim_number, mode)
            results.append(result)

        # 计算总体统计
        independent_results = [
            r for i, r in enumerate(results)
            if i < len(claims) and claims[i].get("type") == "independent"
        ]

        return {
            "total_claims": len(results),
            "analysis_mode": mode,
            "individual_results": [r.to_dict() for r in results],
            "summary": {
                "average_scope": sum(r.scope_score.normalized_score for r in results) / len(results),
                "independent_average": (
                    sum(r.scope_score.normalized_score for r in independent_results) / len(independent_results)
                    if independent_results else 0
                ),
                "risk_distribution": self._calculate_risk_distribution(results),
                "broadest_claim": max(results, key=lambda r: r.scope_score.normalized_score).claim_number,
                "narrowest_claim": min(results, key=lambda r: r.scope_score.normalized_score).claim_number
            },
            "recommendations": self._generate_set_recommendations(results)
        }

    # ==================== 私有方法 ====================

    def _count_technical_terms(self, text: str) -> int:
        """计算技术术语数量"""
        count = 0
        for pattern in self.tech_term_patterns:
            matches = re.findall(pattern, text)
            count += len(matches)
        return count

    def _count_parameters(self, text: str) -> int:
        """计算参数限定数量"""
        # 匹配数值参数
        patterns = [
            r'\d+\.?\d*\s*(?:mm|cm|m|kg|g|°|℃|%|V|A|W|Hz|kHz|MHz)',
            r'\d+\s*[-~]\s*\d+',
        ]
        count = 0
        for pattern in patterns:
            matches = re.findall(pattern, text)
            count += len(matches)
        return count

    def _identify_narrowing_factors(self, text: str) -> list[str]:
        """识别缩小范围的因素"""
        factors = []
        for pattern, description in self.narrowing_patterns:
            if re.search(pattern, text):
                factors.append(description)
        return factors

    def _identify_broadening_factors(self, text: str) -> list[str]:
        """识别扩大范围的因素"""
        factors = []
        for pattern, description in self.broadening_patterns:
            if re.search(pattern, text):
                factors.append(description)
        return factors

    async def _estimate_probability(
        self,
        claim_text: str,
        mode: str
    ) -> ProbabilityEstimate:
        """
        使用LLM估算权利要求文本的出现概率

        论文方法: 通过LLM计算P(claim)
        """
        if self.llm_manager is None:
            # 无LLM时使用启发式方法
            return self._heuristic_probability(claim_text)

        # 选择模型
        model_key = "accurate" if mode == "accurate" else "fast"
        model_config = self.MODEL_CONFIG.get(model_key, self.MODEL_CONFIG["fast"])
        model_id = model_config["model"]

        # 构建概率估算prompt
        prompt = self._build_probability_prompt(claim_text)

        try:
            response = await self.llm_manager.generate(
                message=prompt,
                task_type="patent_scope_analysis",
                model_id=model_id,
                temperature=model_config.get("temperature", 0.1)
            )

            # 解析响应
            response_text = response.content if hasattr(response, 'content') else str(response)

            # 尝试解析JSON
            try:
                # 提取JSON部分
                json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    probability = float(data.get("probability", 0.5))
                else:
                    # 尝试提取数值
                    prob_match = re.search(r'(\d+\.?\d*)', response_text)
                    probability = float(prob_match.group(1)) / 100 if prob_match else 0.5
            except (json.JSONDecodeError, ValueError):
                probability = 0.5  # 默认值

            # 确保概率在有效范围内
            probability = max(0.001, min(0.999, probability))
            log_prob = math.log(probability)
            self_info = -math.log2(probability)

            return ProbabilityEstimate(
                probability=probability,
                log_probability=log_prob,
                self_information=self_info,
                method="llm_estimation",
                model_used=model_id
            )

        except Exception as e:
            logger.warning(f"LLM概率估算失败: {e}, 使用启发式方法")
            return self._heuristic_probability(claim_text)

    def _heuristic_probability(self, claim_text: str) -> ProbabilityEstimate:
        """
        启发式概率估算 (无LLM时的备选方案)

        基于论文发现: 字符数与概率相关
        """
        # 清理文本
        clean_text = claim_text.replace(" ", "").replace("\n", "")
        char_count = len(clean_text)

        # 基于字符数的简单概率估算
        # 论文发现: 字符数越多 -> 概率越低 -> 范围越窄
        # 使用指数衰减模型
        base_prob = 0.5
        decay_factor = 0.002  # 每个字符降低的概率因子

        probability = base_prob * math.exp(-decay_factor * char_count)
        probability = max(0.001, min(0.999, probability))

        log_prob = math.log(probability)
        self_info = -math.log2(probability)

        return ProbabilityEstimate(
            probability=probability,
            log_probability=log_prob,
            self_information=self_info,
            method="heuristic_character_count",
            model_used="rule_based"
        )

    def _build_probability_prompt(self, claim_text: str) -> str:
        """构建概率估算prompt"""
        return f"""你是一位专利技术专家。请评估以下权利要求文本在专利文献中的"常见程度"。

权利要求:
{claim_text}

评估说明:
- 常见程度表示这类表述在专利文献中出现的频率
- 越常见 -> 概率越高 -> 保护范围可能越宽
- 越独特 -> 概率越低 -> 保护范围可能越窄

请分析并返回一个JSON对象:
{{
    "probability": <0到1之间的数值>,
    "reasoning": "<简短分析>"
}}

注意: probability 应该反映这个权利要求的"惊喜程度"
- 0.8-1.0: 非常见，标准表述
- 0.5-0.8: 较常见
- 0.2-0.5: 较独特
- 0.0-0.2: 非常独特/罕见"""

    def _calculate_scope_score(
        self,
        probability_estimate: ProbabilityEstimate,
        character_count: int,
        narrowing_count: int,
        broadening_count: int
    ) -> ScopeScore:
        """
        计算范围得分

        基于论文公式: Scope ∝ 1/Self-Information
        结合多种因素进行调整
        """
        # 基础得分: 基于自信息的倒数
        # 自信息越高 -> 概率越低 -> 范围越窄
        self_info = probability_estimate.self_information

        # 归一化: 将自信息映射到0-100
        # 论文测试: 自信息通常在2-20之间
        raw_score = 100 / (1 + self_info * 5)

        # 调整因子
        # 1. 字符数调整 (论文发现: 字符数越多，范围通常越窄)
        char_factor = max(0.7, min(1.0, 1 - character_count / 1000))

        # 2. 限定词调整
        narrowing_factor = max(0.5, 1 - narrowing_count * 0.05)
        broadening_factor = min(1.3, 1 + broadening_count * 0.03)

        # 综合得分
        adjusted_score = raw_score * char_factor * narrowing_factor * broadening_factor
        adjusted_score = max(0, min(100, adjusted_score))

        # 计算置信度 (基于方法的可靠性)
        confidence = 0.9 if probability_estimate.method == "llm_estimation" else 0.6

        return ScopeScore(
            raw_score=raw_score,
            normalized_score=adjusted_score,
            confidence=confidence
        )

    def _determine_risk_level(self, scope_score: float) -> RiskLevel:
        """确定风险等级"""
        for threshold, level in sorted(self.RISK_THRESHOLDS.items(), reverse=True):
            if scope_score >= threshold:
                return level
        return RiskLevel.VERY_HIGH

    def _generate_recommendations(
        self,
        scope_score: ScopeScore,
        risk_level: RiskLevel,
        narrowing_factors: list[str],
        broadening_factors: list[str]
    ) -> list[str]:
        """生成优化建议"""
        recommendations = []
        score = scope_score.normalized_score

        # 基于风险等级和具体得分
        if risk_level == RiskLevel.VERY_HIGH:
            recommendations.append("保护范围极窄，建议重新撰写，减少具体限定")
            recommendations.append("考虑删除部分参数范围限定")
        elif risk_level == RiskLevel.HIGH:
            recommendations.append("保护范围较窄，易被规避")
            if narrowing_factors:
                recommendations.append(f"考虑放宽限定: {', '.join(narrowing_factors[:2])}")
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.append("保护范围适中，可考虑适度扩大")
        else:
            recommendations.append("保护范围较宽，注意确保技术特征清晰")

        # 基于限定因素
        if len(narrowing_factors) > 5:
            recommendations.append("限定过多，建议将部分限定移至从属权利要求")

        if not broadening_factors:
            recommendations.append("可考虑添加'包括但不限于'等开放式表述")

        # 基于具体得分范围
        if score < 30:
            recommendations.append(f"当前得分{score:.1f}分，保护范围过窄")
        elif score > 80:
            recommendations.append(f"当前得分{score:.1f}分，确保技术特征充分公开")

        return recommendations

    def _calculate_risk_distribution(self, results: list[ScopeAnalysisResult]) -> dict[str, int]:
        """计算风险分布"""
        distribution = {level.value: 0 for level in RiskLevel}
        for result in results:
            distribution[result.risk_level.value] += 1
        return distribution

    def _generate_set_recommendations(self, results: list[ScopeAnalysisResult]) -> list[str]:
        """生成权利要求集的整体建议"""
        recommendations = []

        # 检查独立权利要求
        high_risk_count = sum(1 for r in results if r.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH])

        if high_risk_count > len(results) * 0.5:
            recommendations.append("超过50%的权利要求保护范围过窄，建议重新审视撰写策略")

        # 检查范围一致性
        scores = [r.scope_score.normalized_score for r in results]
        if scores:
            variance = sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores)
            if variance > 400:  # 标准差 > 20
                recommendations.append("权利要求保护范围差异较大，建议调整结构使其更均衡")

        if not recommendations:
            recommendations.append("权利要求整体结构合理，保护范围分布均衡")

        return recommendations


# ==================== 便捷函数 ====================

async def analyze_claim_scope(
    claim_text: str,
    llm_manager=None,
    mode: str = "balanced"
) -> ScopeAnalysisResult:
    """
    便捷函数: 分析单个权利要求的保护范围

    Args:
        claim_text: 权利要求文本
        llm_manager: LLM管理器 (可选)
        mode: 分析模式

    Returns:
        ScopeAnalysisResult: 分析结果
    """
    analyzer = ClaimScopeAnalyzer(llm_manager=llm_manager)
    return await analyzer.analyze_scope(claim_text, mode=mode)


def format_scope_report(result: ScopeAnalysisResult) -> str:
    """
    格式化范围分析报告

    Args:
        result: 分析结果

    Returns:
        str: 格式化报告
    """
    lines = [
        "=" * 60,
        f"权利要求 {result.claim_number} 保护范围分析报告",
        "=" * 60,
        "",
        f"【范围得分】 {result.scope_score.normalized_score:.1f}/100",
        f"【风险等级】 {result.risk_level.value.upper()}",
        f"【置信度】 {result.confidence:.0%}",
        "",
        "【文本统计】",
        f"  字符数: {result.character_count}",
        f"  词数: {result.word_count}",
        f"  技术术语数: {result.technical_term_count}",
        f"  参数限定数: {result.parameter_count}",
        "",
        "【范围影响因素】",
    ]

    if result.narrowing_factors:
        lines.append("  缩小因素:")
        for factor in result.narrowing_factors:
            lines.append(f"    - {factor}")

    if result.broadening_factors:
        lines.append("  扩大因素:")
        for factor in result.broadening_factors:
            lines.append(f"    + {factor}")

    if result.recommendations:
        lines.append("")
        lines.append("【优化建议】")
        for rec in result.recommendations:
            lines.append(f"  • {rec}")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


# 添加confidence属性到ScopeAnalysisResult
ScopeAnalysisResult.confidence = property(
    lambda self: self.scope_score.confidence
)
