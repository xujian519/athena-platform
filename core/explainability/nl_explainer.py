#!/usr/bin/env python3
"""
自然语言解释器
Natural Language Explainer

将模型的决策过程转换为自然语言解释
目标实现>90%的决策解释覆盖率
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from core.async_main import async_main

logger = logging.getLogger(__name__)


class ExplanationType(Enum):
    """解释类型"""

    INTENT = "intent"  # 意图识别
    TOOL_SELECTION = "tool_selection"  # 工具选择
    PARAMETER_EXTRACTION = "param_extraction"  # 参数提取
    CONFIDENCE = "confidence"  # 置信度
    ERROR = "error"  # 错误


@dataclass
class DecisionExplanation:
    """决策解释"""

    explanation_id: str
    decision_type: ExplanationType
    decision: str
    reasoning: list[str]  # 推理过程
    confidence: float
    key_factors: dict[str, Any]  # 关键因素
    alternatives: list[str]  # 替代方案
    natural_language: str  # 自然语言解释


class NLExplainer:
    """
    自然语言解释器

    核心功能:
    1. 决策解释生成
    2. 推理过程可视化
    3. 关键因素提取
    4. 自然语言模板
    """

    def __init__(self):
        """初始化解释器"""
        self.name = "自然语言解释器 v1.0"
        self.version = "1.0.0"

        # 解释模板
        self.templates = {
            ExplanationType.INTENT: {
                "high_confidence": "根据您的表述'{input}',我判断您的意图是{intent},置信度为{confidence:.1%}。主要依据是:{reasons}",
                "medium_confidence": "您说的'{input}'让我想到您可能想要{intent},但我不完全确定(置信度{confidence:.1%})。可能的原因包括:{reasons}",
                "low_confidence": "对于'{input}',我猜测您的意图是{intent},但置信度较低({confidence:.1%})。您能否提供更多细节?",
            },
            ExplanationType.TOOL_SELECTION: {
                "single": "我选择使用{tool}来处理您的请求,因为它最擅长处理{task}这类任务。",
                "multiple": "考虑到{reasons},我将同时使用{tools}来更全面地处理您的请求。",
            },
            ExplanationType.PARAMETER_EXTRACTION: {
                "success": "我从您的描述中提取了以下参数:{params}。",
                "partial": "我提取了部分参数:{params}。但{missing}似乎没有提供,您能补充一下吗?",
                "failed": "抱歉,我无法从您的描述中提取所需的参数。请提供{required}。",
            },
            ExplanationType.CONFIDENCE: {
                "high": "我对这个结果非常有信心(置信度{confidence:.1%}),因为{reasons}。",
                "medium": "这个结果的置信度为{confidence:.1%},主要基于{reasons}。",
                "low": "这个结果的置信度较低({confidence:.1%}),因为{reasons}。建议您提供更多信息。",
            },
            ExplanationType.ERROR: {
                "general": "处理您的请求时遇到了问题:{error}。",
                "fallback": "由于{error},我将使用备用方案:{fallback}。",
            },
        }

        # 统计信息
        self.stats = {
            "total_explanations": 0,
            "explained_decisions": 0,
            "explanation_coverage": 0.0,
            "avg_explanation_length": 0.0,
        }

    def explain_intent(
        self, input_text: str, intent: str, confidence: float, key_factors: dict[str, Any]
    ) -> DecisionExplanation:
        """
        解释意图识别决策

        Args:
            input_text: 输入文本
            intent: 识别的意图
            confidence: 置信度
            key_factors: 关键因素

        Returns:
            DecisionExplanation: 决策解释
        """
        # 生成推理过程
        reasoning = []
        if "keywords" in key_factors:
            reasoning.append(f"检测到关键词: {', '.join(key_factors['keywords'])}")
        if "pattern_match" in key_factors:
            reasoning.append(f"匹配模式: {key_factors['pattern_match']}")
        if "similarity" in key_factors:
            reasoning.append(f"相似度: {key_factors['similarity']:.1%}")

        # 选择模板
        if confidence >= 0.8:
            template = self.templates[ExplanationType.INTENT]["high_confidence"]
        elif confidence >= 0.5:
            template = self.templates[ExplanationType.INTENT]["medium_confidence"]
        else:
            template = self.templates[ExplanationType.INTENT]["low_confidence"]

        # 生成自然语言解释
        natural_language = template.format(
            input=input_text[:50] + "..." if len(input_text) > 50 else input_text,
            intent=intent,
            confidence=confidence,
            reasons="; ".join(reasoning),
        )

        return DecisionExplanation(
            explanation_id=f"expl_{int(datetime.now().timestamp())}",
            decision_type=ExplanationType.INTENT,
            decision=f"识别意图为: {intent}",
            reasoning=reasoning,
            confidence=confidence,
            key_factors=key_factors,
            alternatives=[],
            natural_language=natural_language,
        )

    def explain_tool_selection(
        self, tools: list[str], task: str, reasons: list[str], confidence: float = 0.9
    ) -> DecisionExplanation:
        """
        解释工具选择决策

        Args:
            tools: 选择的工具列表
            task: 任务描述
            reasons: 选择原因
            confidence: 置信度

        Returns:
            DecisionExplanation: 决策解释
        """
        if len(tools) == 1:
            template = self.templates[ExplanationType.TOOL_SELECTION]["single"]
            natural_language = template.format(tool=tools[0], task=task)
        else:
            template = self.templates[ExplanationType.TOOL_SELECTION]["multiple"]
            natural_language = template.format(reasons="; ".join(reasons), tools="、".join(tools))

        return DecisionExplanation(
            explanation_id=f"expl_{int(datetime.now().timestamp())}",
            decision_type=ExplanationType.TOOL_SELECTION,
            decision=f"选择工具: {', '.join(tools)}",
            reasoning=reasons,
            confidence=confidence,
            key_factors={"tools": tools, "task": task},
            alternatives=[],
            natural_language=natural_language,
        )

    def explain_parameter_extraction(
        self, extracted: dict[str, Any], missing: list[str], required: list[str]
    ) -> DecisionExplanation:
        """
        解释参数提取决策

        Args:
            extracted: 已提取的参数
            missing: 缺失的参数
            required: 必需的参数

        Returns:
            DecisionExplanation: 决策解释
        """
        if not missing:
            template = self.templates[ExplanationType.PARAMETER_EXTRACTION]["success"]
            natural_language = template.format(
                params=f"{', '.join(f'{k}={v}' for k, v in extracted.items())}"
            )
        elif set(missing) < set(required):
            template = self.templates[ExplanationType.PARAMETER_EXTRACTION]["partial"]
            natural_language = template.format(
                params=f"{', '.join(f'{k}={v}' for k, v in extracted.items())}",
                missing=f"{', '.join(missing)}",
            )
        else:
            template = self.templates[ExplanationType.PARAMETER_EXTRACTION]["failed"]
            natural_language = template.format(required=f"{', '.join(required)}")

        return DecisionExplanation(
            explanation_id=f"expl_{int(datetime.now().timestamp())}",
            decision_type=ExplanationType.PARAMETER_EXTRACTION,
            decision="参数提取" + ("成功" if not missing else "部分成功" if extracted else "失败"),
            reasoning=[f"已提取: {list(extracted.keys())}", f"缺失: {missing}"],
            confidence=1.0 if not missing else 0.5,
            key_factors={"extracted": extracted, "missing": missing},
            alternatives=[],
            natural_language=natural_language,
        )

    def explain_confidence(self, confidence: float, reasons: list[str]) -> DecisionExplanation:
        """
        解释置信度

        Args:
            confidence: 置信度
            reasons: 原因列表

        Returns:
            DecisionExplanation: 决策解释
        """
        if confidence >= 0.8:
            template = self.templates[ExplanationType.CONFIDENCE]["high"]
        elif confidence >= 0.5:
            template = self.templates[ExplanationType.CONFIDENCE]["medium"]
        else:
            template = self.templates[ExplanationType.CONFIDENCE]["low"]

        natural_language = template.format(confidence=confidence, reasons="; ".join(reasons))

        return DecisionExplanation(
            explanation_id=f"expl_{int(datetime.now().timestamp())}",
            decision_type=ExplanationType.CONFIDENCE,
            decision=f"置信度: {confidence:.1%}",
            reasoning=reasons,
            confidence=confidence,
            key_factors={},
            alternatives=[],
            natural_language=natural_language,
        )

    def explain_error(self, error: str, fallback: str | None = None) -> DecisionExplanation:
        """
        解释错误

        Args:
            error: 错误信息
            fallback: 备用方案

        Returns:
            DecisionExplanation: 决策解释
        """
        if fallback:
            template = self.templates[ExplanationType.ERROR]["fallback"]
            natural_language = template.format(error=error, fallback=fallback)
        else:
            template = self.templates[ExplanationType.ERROR]["general"]
            natural_language = template.format(error=error)

        return DecisionExplanation(
            explanation_id=f"expl_{int(datetime.now().timestamp())}",
            decision_type=ExplanationType.ERROR,
            decision=f"错误: {error}",
            reasoning=[f"遇到错误: {error}"],
            confidence=0.0,
            key_factors={"error": error, "fallback": fallback},
            alternatives=[fallback] if fallback else [],
            natural_language=natural_language,
        )

    def generate_explanation(self, decision_type: ExplanationType, **kwargs) -> DecisionExplanation:
        """
        生成解释(通用方法)

        Args:
            decision_type: 决策类型
            **kwargs: 决策相关参数

        Returns:
            DecisionExplanation: 决策解释
        """
        self.stats["total_explanations"] += 1

        if decision_type == ExplanationType.INTENT:
            explanation = self.explain_intent(
                kwargs.get("input_text", ""),
                kwargs.get("intent", ""),
                kwargs.get("confidence", 0.0),
                kwargs.get("key_factors", {}),
            )
        elif decision_type == ExplanationType.TOOL_SELECTION:
            explanation = self.explain_tool_selection(
                kwargs.get("tools", []),
                kwargs.get("task", ""),
                kwargs.get("reasons", []),
                kwargs.get("confidence", 0.9),
            )
        elif decision_type == ExplanationType.PARAMETER_EXTRACTION:
            explanation = self.explain_parameter_extraction(
                kwargs.get("extracted", {}), kwargs.get("missing", []), kwargs.get("required", [])
            )
        elif decision_type == ExplanationType.CONFIDENCE:
            explanation = self.explain_confidence(
                kwargs.get("confidence", 0.0), kwargs.get("reasons", [])
            )
        elif decision_type == ExplanationType.ERROR:
            explanation = self.explain_error(kwargs.get("error", ""), kwargs.get("fallback"))
        else:
            explanation = DecisionExplanation(
                explanation_id=f"expl_{int(datetime.now().timestamp())}",
                decision_type=decision_type,
                decision="未知决策",
                reasoning=[],
                confidence=0.0,
                key_factors={},
                alternatives=[],
                natural_language="无法生成解释",
            )

        # 更新统计
        self.stats["explained_decisions"] += 1
        self.stats["explanation_coverage"] = (
            self.stats["explained_decisions"] / self.stats["total_explanations"]
        )
        self.stats["avg_explanation_length"] = (
            self.stats["avg_explanation_length"] * (self.stats["explained_decisions"] - 1)
            + len(explanation.natural_language)
        ) / self.stats["explained_decisions"]

        return explanation

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()


# 单例实例
_explainer_instance: NLExplainer | None = None


async def get_nl_explainer() -> NLExplainer:
    """获取自然语言解释器单例(异步版本)"""
    global _explainer_instance
    if _explainer_instance is None:
        _explainer_instance = NLExplainer()
        logger.info("自然语言解释器已初始化")
    return _explainer_instance


def get_nl_explainer_sync() -> NLExplainer:
    """获取自然语言解释器单例(同步版本,用于向后兼容)"""
    global _explainer_instance
    if _explainer_instance is None:
        _explainer_instance = NLExplainer()
        logger.info("自然语言解释器已初始化")
    return _explainer_instance


@async_main
async def main():
    """测试主函数"""
    explainer = get_nl_explainer()

    print("=== 自然语言解释测试 ===\n")

    # 测试1: 意图识别解释
    print("测试1: 意图识别解释")
    explanation = explainer.explain_intent(
        input_text="帮我查一下专利CN123456789A",
        intent="patent_analysis",
        confidence=0.95,
        key_factors={
            "keywords": ["专利", "查"],
            "pattern_match": "patent_number_pattern",
            "similarity": 0.95,
        },
    )
    print(f"  自然语言: {explanation.natural_language}")

    # 测试2: 工具选择解释
    print("\n测试2: 工具选择解释")
    explanation = explainer.explain_tool_selection(
        tools=["专利检索工具", "BERT模型"],
        task="专利分析",
        reasons=["需要检索专利信息", "需要理解专利内容"],
    )
    print(f"  自然语言: {explanation.natural_language}")

    # 测试3: 参数提取解释
    print("\n测试3: 参数提取解释")
    explanation = explainer.explain_parameter_extraction(
        extracted={"patent_number": "CN123456789A"},
        missing=["analysis_depth"],
        required=["patent_number"],
    )
    print(f"  自然语言: {explanation.natural_language}")

    # 测试4: 置信度解释
    print("\n测试4: 置信度解释")
    explanation = explainer.explain_confidence(
        confidence=0.85, reasons=["关键词匹配度高", "上下文一致", "历史模式符合"]
    )
    print(f"  自然语言: {explanation.natural_language}")

    # 显示统计
    stats = explainer.get_stats()
    print("\n=== 统计信息 ===")
    print(f"总解释数: {stats['total_explanations']}")
    print(f"解释覆盖率: {stats['explanation_coverage']:.1%}")
    print(f"平均解释长度: {stats['avg_explanation_length']:.0f}字符")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
