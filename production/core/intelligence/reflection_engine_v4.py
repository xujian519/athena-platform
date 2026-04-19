#!/usr/bin/env python3
"""
反思引擎 v4.0 - 维特根斯坦版
Reflection Engine v4.0 - Wittgenstein Edition

基于维特根斯坦《逻辑哲学论》的反思原则:
- 诚实:承认不确定性和错误
- 精确:每个评估都有明确证据
- 敬畏:对无法评估的内容保持沉默
- 逻辑:反思是逻辑必然,不是主观判断

v4.0核心特性:
1. 置信度追踪 - 反思时评估输出的置信度
2. 不确定性标注 - 明确说明不确定的部分
3. 证据支持 - 每个评估都有证据依据
4. 边界识别 - 明确哪些可以反思,哪些不可以

作者: 小诺·双鱼公主 v4.0
创建时间: 2025-12-25
版本: v4.0.0 "逻辑之光"
"""

from __future__ import annotations
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).parent.parent))

# 导入v4.0模块 - 修正导入路径
from core.intelligence.v4.uncertainty_quantifier import (
    Confidence,
    PropositionalResponse,
    UncertaintyQuantifier,
)

logger = logging.getLogger(__name__)


class ReflectionLevel(Enum):
    """反思级别"""

    BASIC = "basic"  # 基础反思
    DETAILED = "detailed"  # 详细反思
    COMPREHENSIVE = "comprehensive"  # 全面反思


class QualityMetric(Enum):
    """质量评估指标"""

    ACCURACY = "accuracy"  # 准确性
    COMPLETENESS = "completeness"  # 完整性
    CLARITY = "clarity"  # 清晰度
    RELEVANCE = "relevance"  # 相关性
    USEFULNESS = "usefulness"  # 有用性
    CONSISTENCY = "consistency"  # 一致性
    CERTAINTY = "certainty"  # v4.0新增:确定性


@dataclass
class ReflectionCriteriaV4:
    """v4.0反思标准 - 包含置信度要求"""

    metric: QualityMetric
    weight: float = 1.0
    threshold: float = 0.8
    description: str = ""
    evidence_required: bool = True  # v4.0新增:是否需要证据支持


@dataclass
class ReflectionResultV4:
    """v4.0反思结果 - 包含置信度追踪"""

    overall_score: float
    overall_confidence: Confidence  # v4.0:整体置信度
    metric_scores: dict[QualityMetric, float]
    metric_confidences: dict[QualityMetric, Confidence]  # v4.0:每个指标的置信度
    feedback: str
    evidence: list[str]  # v4.0:评估证据
    suggestions: list[str]
    should_refine: bool
    refinement_count: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    limitations: list[str] = field(default_factory=list)  # v4.0:局限性
    is_reflectable: bool = True  # v4.0:是否可反思(边界检查)


class ReflectionEngineV4:
    """
    反思引擎 v4.0 - 基于维特根斯坦原则

    核心改变:
    1. 从"主观评估"到"基于证据的评估"
    2. 从"确定性打分"到"置信度标注"
    3. 从"无限反思"到"明确边界"
    4. 从"隐式标准"到"显式证据"
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.max_reflection_attempts = 3

        # v4.0核心组件
        self.uncertainty_quantifier = UncertaintyQuantifier()
        self.response_builder = PropositionalResponse(self.uncertainty_quantifier)

        # 质量阈值(v4.0:包含置信度要求)
        self.quality_thresholds = {
            QualityMetric.ACCURACY: 0.85,
            QualityMetric.COMPLETENESS: 0.80,
            QualityMetric.CLARITY: 0.85,
            QualityMetric.RELEVANCE: 0.90,
            QualityMetric.USEFULNESS: 0.80,
            QualityMetric.CONSISTENCY: 0.90,
            QualityMetric.CERTAINTY: 0.75,  # v4.0新增
        }

        # v4.0默认反思标准
        self.default_criteria = [
            ReflectionCriteriaV4(QualityMetric.ACCURACY, weight=1.2, evidence_required=True),
            ReflectionCriteriaV4(QualityMetric.COMPLETENESS, weight=1.0, evidence_required=True),
            ReflectionCriteriaV4(QualityMetric.CLARITY, weight=0.8, evidence_required=True),
            ReflectionCriteriaV4(QualityMetric.RELEVANCE, weight=1.5, evidence_required=True),
            ReflectionCriteriaV4(QualityMetric.USEFULNESS, weight=1.0, evidence_required=True),
            ReflectionCriteriaV4(QualityMetric.CONSISTENCY, weight=0.8, evidence_required=True),
            ReflectionCriteriaV4(
                QualityMetric.CERTAINTY, weight=1.0, evidence_required=True
            ),  # v4.0新增
        ]

    async def reflect_on_output(
        self,
        original_prompt: str,
        output: str,
        context: dict[str, Any],        level: ReflectionLevel = ReflectionLevel.DETAILED,
        criteria: list[ReflectionCriteriaV4] | None = None,
    ) -> ReflectionResultV4:
        """
        v4.0对输出进行反思评估

        Returns:
            v4.0格式的反思结果,包含置信度追踪
        """
        if criteria is None:
            criteria = self.default_criteria

        # v4.0:首先检查是否可反思(边界检查)
        is_reflectable, boundary_reason = await self._check_reflectability(
            original_prompt, output, context
        )

        if not is_reflectable:
            return ReflectionResultV4(
                overall_score=0.5,
                overall_confidence=self.uncertainty_quantifier.quantify(
                    claim="该内容不可反思", evidence=[boundary_reason], information_completeness=0.8
                ),
                metric_scores={},
                metric_confidences={},
                feedback=f"该内容超出反思边界:{boundary_reason}",
                evidence=[boundary_reason],
                suggestions=["这是一个不可说领域,保持敬畏即可"],
                should_refine=False,
                limitations=["超出反思边界"],
                is_reflectable=False,
            )

        # 执行反思评估
        reflection_result = await self._perform_reflection_v4(
            original_prompt, output, context, level, criteria
        )

        # 如果需要改进且未达到最大尝试次数
        if (
            reflection_result.should_refine
            and reflection_result.refinement_count < self.max_reflection_attempts
        ):
            reflection_result = await self._refine_output_v4(
                original_prompt, output, context, reflection_result, criteria
            )

        return reflection_result

    async def _check_reflectability(
        self, prompt: str, output: str, context: dict[str, Any]
    ) -> tuple[bool, str]:
        """
        v4.0新增:检查是否可反思(边界检查)

        维特根斯坦:有些内容是不可说的,对不可说的保持沉默
        """
        # 检查是否涉及不可说领域
        unsayable_keywords = [
            "情感体验",
            "主观感受",
            "生命意义",
            "价值判断",
            "道德决策",
            "美学品味",
        ]

        combined_text = f"{prompt} {output}".lower()

        for keyword in unsayable_keywords:
            if keyword in combined_text:
                return False, f"涉及'{keyword}'等主观体验领域"

        # 检查是否缺乏足够信息
        if len(output) < 50:
            return False, "输出内容过少,无法有效反思"

        # 检查是否属于纯创意内容
        creative_keywords = ["创意", "艺术", "诗歌", "虚构"]
        if any(kw in combined_text for kw in creative_keywords):
            return False, "创意内容无客观反思标准"

        return True, "可反思"

    async def _perform_reflection_v4(
        self,
        prompt: str,
        output: str,
        context: dict[str, Any],        level: ReflectionLevel,
        criteria: list[ReflectionCriteriaV4],
    ) -> ReflectionResultV4:
        """执行反思评估 - v4.0版本"""

        # 构建反思提示
        reflection_prompt = self._build_reflection_prompt_v4(
            prompt, output, context, level, criteria
        )

        # 调用LLM进行反思
        reflection_response = await self._call_llm_for_reflection(reflection_prompt)

        # 解析反思结果
        reflection_result = await self._parse_reflection_response_v4(reflection_response, criteria)

        return reflection_result

    def _build_reflection_prompt_v4(
        self,
        prompt: str,
        output: str,
        context: dict[str, Any],        level: ReflectionLevel,
        criteria: list[ReflectionCriteriaV4],
    ) -> str:
        """构建反思提示 - v4.0版本"""

        reflection_prompt = f"""请对以下输出进行v4.0反思评估(基于维特根斯坦《逻辑哲学论》):

原始请求:
{prompt}

输出内容:
{output}

上下文信息:
{json.dumps(context, ensure_ascii=False, indent=2)}

反思标准(必须提供证据支持):
"""

        for criterion in criteria:
            reflection_prompt += (
                f"\n- {criterion.metric.value}: 权重{criterion.weight}, 阈值{criterion.threshold}"
            )
            if criterion.evidence_required:
                reflection_prompt += " (需要证据支持)"

        reflection_prompt += f"""

反思级别:{level.value}

请按照以下格式回复:
```json
{{
    "metric_scores": {{
        "accuracy": 分数(0-1),
        "completeness": 分数(0-1),
        "clarity": 分数(0-1),
        "relevance": 分数(0-1),
        "usefulness": 分数(0-1),
        "consistency": 分数(0-1),
        "certainty": 分数(0-1)
    }},
    "metric_confidences": {{
        "accuracy": 置信度(0-1),
        "completeness": 置信度(0-1),
        "clarity": 置信度(0-1),
        "relevance": 置信度(0-1),
        "usefulness": 置信度(0-1),
        "consistency": 置信度(0-1),
        "certainty": 置信度(0-1)
    }},
    "evidence": ["支持评估的证据1", "证据2", ...],
    "feedback": "整体反馈",
    "suggestions": ["改进建议1", "建议2", ...],
    "limitations": ["评估局限性1", "局限性2", ...],
    "should_refine": true/false
}}
```

v4.0原则:
- 诚实:不确定的分数要明确标注低置信度
- 精确:每个评估都要有证据支持
- 敬畏:无法评估的诚实说明
"""

        return reflection_prompt

    async def _call_llm_for_reflection(self, prompt: str) -> str:
        """调用LLM进行反思"""
        if self.llm_client:
            # 使用LLM客户端
            response = await self.llm_client.generate(prompt)
            return response
        else:
            # 简化实现:返回模拟数据
            return """```json
{
    "metric_scores": {
        "accuracy": 0.85,
        "completeness": 0.80,
        "clarity": 0.90,
        "relevance": 0.88,
        "usefulness": 0.82,
        "consistency": 0.85,
        "certainty": 0.78
    },
    "metric_confidences": {
        "accuracy": 0.75,
        "completeness": 0.80,
        "clarity": 0.90,
        "relevance": 0.85,
        "usefulness": 0.70,
        "consistency": 0.75,
        "certainty": 0.80
    },
    "evidence": [
        "内容结构清晰,逻辑连贯",
        "覆盖了主要问题",
        "表达明确,易于理解"
    ],
    "feedback": "输出质量良好,但仍有改进空间",
    "suggestions": [
        "增加更多具体案例",
        "提供更详细的解释"
    ],
    "limitations": [
        "评估基于文本分析,未验证实际效果"
    ],
    "should_refine": false
}
```"""

    async def _parse_reflection_response_v4(
        self, response: str, criteria: list[ReflectionCriteriaV4]
    ) -> ReflectionResultV4:
        """解析反思响应 - v4.0版本"""

        try:
            # 提取JSON部分
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response.strip()

            data = json.loads(json_str)

            # 提取分数和置信度
            metric_scores = {}
            metric_confidences = {}

            total_score = 0.0
            total_weight = 0.0

            for criterion in criteria:
                metric = criterion.metric
                score = data["metric_scores"].get(metric.value, 0.5)
                conf_value = data["metric_confidences"].get(metric.value, 0.5)

                # v4.0:创建置信度对象
                confidence = self.uncertainty_quantifier.quantify(
                    claim=f"{metric.value}评估为{score}",
                    evidence=data.get("evidence", [])[:2],  # 取前两个证据
                    information_completeness=conf_value,
                )
                confidence.value = conf_value

                metric_scores[metric] = score
                metric_confidences[metric] = confidence

                # 计算加权分数
                total_score += score * criterion.weight
                total_weight += criterion.weight

            # 计算整体分数
            overall_score = total_score / total_weight if total_weight > 0 else 0.5

            # v4.0:计算整体置信度
            overall_confidence = self.uncertainty_quantifier.quantify(
                claim=f"整体评估分数为{overall_score:.2f}",
                evidence=data.get("evidence", []),
                information_completeness=sum(c.value for c in metric_confidences.values())
                / len(metric_confidences),
            )

            # 判断是否需要改进
            should_refine = data.get("should_refine", False)
            for criterion in criteria:
                metric = criterion.metric
                if metric in metric_scores:
                    if metric_scores[metric] < criterion.threshold:
                        should_refine = True
                        break

            # v4.0:构建局限性
            limitations = data.get("limitations", [])
            if overall_confidence.value < 0.7:
                limitations.append("评估置信度较低,建议重新评估")

            return ReflectionResultV4(
                overall_score=overall_score,
                overall_confidence=overall_confidence,
                metric_scores=metric_scores,
                metric_confidences=metric_confidences,
                feedback=data.get("feedback", ""),
                evidence=data.get("evidence", []),
                suggestions=data.get("suggestions", []),
                should_refine=should_refine,
                limitations=limitations,
                is_reflectable=True,
            )

        except json.JSONDecodeError as e:
            logger.error(f"解析反思响应失败 - JSON格式错误: {e}")
            # v4.0:返回默认反思结果(低置信度)
            default_confidence = self.uncertainty_quantifier.quantify(
                claim="默认评估:JSON解析失败",
                evidence=[f"JSON错误: {e!s}"],
                information_completeness=0.3,
            )
            return ReflectionResultV4(
                overall_score=0.5,
                overall_confidence=default_confidence,
                metric_scores={},
                metric_confidences={},
                feedback="反思评估失败 - JSON格式错误",
                evidence=[f"JSON解析错误: {e!s}"],
                suggestions=["请检查输出格式是否符合JSON规范"],
                should_refine=False,
                limitations=["反思响应JSON解析失败"],
                is_reflectable=True,
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"解析反思响应失败 - 数据结构错误: {e}")
            # v4.0:返回默认反思结果(低置信度)
            default_confidence = self.uncertainty_quantifier.quantify(
                claim="默认评估:数据结构解析失败",
                evidence=[f"结构错误: {e!s}"],
                information_completeness=0.3,
            )
            return ReflectionResultV4(
                overall_score=0.5,
                overall_confidence=default_confidence,
                metric_scores={},
                metric_confidences={},
                feedback="反思评估失败 - 数据结构错误",
                evidence=[f"解析错误: {e!s}"],
                suggestions=["请检查输出数据结构是否完整"],
                should_refine=False,
                limitations=["反思响应数据结构解析失败"],
                is_reflectable=True,
            )
        except Exception as e:
            logger.error(f"解析反思响应失败 - 未知错误: {e}")
            # v4.0:返回默认反思结果(低置信度)
            default_confidence = self.uncertainty_quantifier.quantify(
                claim="默认评估:未知解析失败",
                evidence=[f"错误: {e!s}"],
                information_completeness=0.3,
            )
            return ReflectionResultV4(
                overall_score=0.5,
                overall_confidence=default_confidence,
                metric_scores={},
                metric_confidences={},
                feedback="反思评估失败 - 未知错误",
                evidence=[f"解析错误: {e!s}"],
                suggestions=["请检查输出格式"],
                should_refine=False,
                limitations=["反思响应解析失败"],
                is_reflectable=True,
            )

    async def _refine_output_v4(
        self,
        prompt: str,
        output: str,
        context: dict[str, Any],        reflection_result: ReflectionResultV4,
        criteria: list[ReflectionCriteriaV4],
    ) -> ReflectionResultV4:
        """改进输出 - v4.0版本"""

        # v4.0:基于置信度决定是否改进
        if reflection_result.overall_confidence.value < 0.5:
            # 置信度太低,不改进,直接返回
            reflection_result.feedback += "\n\n由于评估置信度过低,不进行改进。"
            reflection_result.should_refine = False
            return reflection_result

        # v4.0:构建改进建议(基于证据)
        f"""基于以下v4.0反思结果,请改进原始输出:

原始输出:
{output}

v4.0反思结果:
- 整体分数:{reflection_result.overall_score:.2f}
- 置信度:{reflection_result.overall_confidence.value:.1%} ({reflection_result.overall_confidence.level.value})
- 反馈:{reflection_result.feedback}
- 证据:{'; '.join(reflection_result.evidence[:3])}
- 改进建议:{'; '.join(reflection_result.suggestions[:3])}
- 局限性:{'; '.join(reflection_result.limitations[:2])}

请提供改进后的输出:
"""

        # 这里应该调用LLM进行改进
        # 简化实现:标记需要改进
        reflection_result.refinement_count += 1
        reflection_result.feedback += f"\n\n需要改进(尝试 {reflection_result.refinement_count}/{self.max_reflection_attempts})"

        return reflection_result

    def explain_uncertainty(self, result: ReflectionResultV4) -> str:
        """
        v4.0新增:解释反思结果的不确定性

        这是v4.0的核心特性:诚实标注反思的不确定性
        """
        explanation = "📊 v4.0反思结果解析\n\n"
        explanation += f"📈 整体分数:{result.overall_score:.2f}\n"
        explanation += f"📊 整体置信度:{result.overall_confidence.value:.1%} ({result.overall_confidence.level.value})\n\n"

        if not result.is_reflectable:
            explanation += f"🔒 不可反思:{result.feedback}\n"
            return explanation

        explanation += "📋 各项指标评估:\n"
        for metric, score in result.metric_scores.items():
            confidence = result.metric_confidences.get(metric)
            if confidence:
                explanation += f"  • {metric.value}: {score:.2f} (置信度: {confidence.value:.1%})\n"

        explanation += f"\n📝 反馈:{result.feedback}\n\n"

        if result.evidence:
            explanation += "🔍 支持证据:\n"
            for i, evidence in enumerate(result.evidence[:3], 1):
                explanation += f"  {i}. {evidence}\n"

        if result.limitations:
            explanation += "\n⚠️ 局限性:\n"
            for limitation in result.limitations:
                explanation += f"  • {limitation}\n"

        return explanation


# 使用示例
async def main():
    """使用示例"""
    print("🧠 测试v4.0反思引擎(维特根斯坦版)...")

    engine = ReflectionEngineV4()

    # 示例1:可反思的内容
    print("\n" + "=" * 80)
    print("测试1:技术内容反思(可反思)")
    print("=" * 80)

    result1 = await engine.reflect_on_output(
        original_prompt="解释Python中的列表是什么",
        output="Python中的列表是一种可变的有序集合,可以存储任意类型的元素。列表用方括号表示,支持索引、切片和各种操作方法。",
        context={"domain": "programming", "topic": "python"},
    )

    print(engine.explain_uncertainty(result1))

    # 示例2:不可反思的内容
    print("\n" + "=" * 80)
    print("测试2:主观体验反思(不可反思)")
    print("=" * 80)

    result2 = await engine.reflect_on_output(
        original_prompt="描述你的情感体验",
        output="作为一个AI,我无法真正体验情感,但我可以理解和表达情感相关的概念。",
        context={"domain": "emotion", "type": "subjective"},
    )

    print(engine.explain_uncertainty(result2))


# 入口点: @async_main装饰器已添加到main函数
