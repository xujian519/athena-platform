#!/usr/bin/env python3
from __future__ import annotations
"""
提示工程优化器 (Prompt Engineering Optimizer)
智能优化提示词,提升LLM输出质量

作者: 小诺·双鱼公主
版本: v3.0.0
优化目标: 提示词效果提升 30%+, 输出质量提升 25%+
"""

import logging
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class PromptTechnique(str, Enum):
    """提示技巧"""

    ZERO_SHOT = "zero_shot"  # 零样本
    FEW_SHOT = "few_shot"  # 少样本
    CHAIN_OF_THOUGHT = "chain_of_thought"  # 思维链
    SELF_CONSISTENCY = "self_consistency"  # 自我一致性
    REACT = "react"  # ReAct
    TREE_OF_THOUGHTS = "tree_of_thoughts"  # 思维树
    LEAST_TO_MOST = "least_to_most"  # 从简到繁
    DECOMPOSITION = "decomposition"  # 分解


class PromptElement(str, Enum):
    """提示元素"""

    SYSTEM_INSTRUCTION = "system_instruction"  # 系统指令
    TASK_DESCRIPTION = "task_description"  # 任务描述
    CONTEXT = "context"  # 上下文
    EXAMPLES = "examples"  # 示例
    CONSTRAINTS = "constraints"  # 约束
    OUTPUT_FORMAT = "output_format"  # 输出格式
    REASONING = "reasoning"  # 推理


@dataclass
class PromptTemplate:
    """提示模板"""

    template_id: str
    name: str
    description: str
    elements: dict[str, str]
    technique: PromptTechnique
    performance_score: float = 0.0
    usage_count: int = 0


@dataclass
class PromptVariant:
    """提示变体"""

    variant_id: str
    template_id: str
    content: str
    modifications: list[str]
    score: float = 0.0


@dataclass
class EvaluationResult:
    """评估结果"""

    prompt_id: str
    output: str
    quality_score: float
    relevance_score: float
    accuracy_score: float
    latency_ms: float
    token_count: int


@dataclass
class OptimizationSuggestion:
    """优化建议"""

    suggestion_id: str
    target_element: PromptElement
    current_content: str
    suggested_content: str
    reason: str
    expected_improvement: float


class PromptEngineeringOptimizer:
    """
    提示工程优化器

    功能:
    1. 提示模板管理
    2. 多种提示技巧
    3. A/B测试
    4. 自动优化
    5. 性能评估
    """

    def __init__(self):
        self.name = "提示工程优化器"
        self.version = "3.0.0"

        # 提示模板库
        self.templates: dict[str, PromptTemplate] = {}

        # 提示变体
        self.variants: dict[str, PromptVariant] = {}

        # 评估历史
        self.evaluation_history: deque = deque(maxlen=10000)

        # 优化建议
        self.suggestions: list[OptimizationSuggestion] = []

        # 最佳实践
        self.best_practices: dict[str, str] = {}

        # 统计信息
        self.stats = {
            "total_evaluations": 0,
            "avg_quality_score": 0.0,
            "best_prompt": None,
            "improvement_rate": 0.0,
        }

        # 初始化内置模板
        self._initialize_builtin_templates()

        logger.info(f"✅ {self.name} 初始化完成")

    def _initialize_builtin_templates(self) -> Any:
        """初始化内置模板"""
        builtin_templates = [
            PromptTemplate(
                template_id="zero_shot_qa",
                name="零样本问答",
                description="基本的零样本问答模板",
                technique=PromptTechnique.ZERO_SHOT,
                elements={
                    "task": "请回答以下问题:",
                    "question": "{question}",
                    "output_format": "请直接给出答案,不需要解释。",
                },
            ),
            PromptTemplate(
                template_id="few_shot_qa",
                name="少样本问答",
                description="提供示例的少样本模板",
                technique=PromptTechnique.FEW_SHOT,
                elements={
                    "task": "请参考以下示例,回答问题:",
                    "examples": "{examples}",
                    "question": "{question}",
                    "output_format": "请按照示例的格式回答。",
                },
            ),
            PromptTemplate(
                template_id="cot_reasoning",
                name="思维链推理",
                description="逐步推理的模板",
                technique=PromptTechnique.CHAIN_OF_THOUGHT,
                elements={
                    "task": "请逐步思考并回答以下问题:",
                    "question": "{question}",
                    "reasoning": "让我们一步步来思考:",
                    "output_format": "请详细展示你的推理过程。",
                },
            ),
            PromptTemplate(
                template_id="react_agent",
                name="ReAct智能体",
                description="推理+行动的模板",
                technique=PromptTechnique.REACT,
                elements={
                    "task": "请使用推理和行动来解决问题:",
                    "question": "{question}",
                    "reasoning": "Thought: {thought}",
                    "action": "Action: {action}",
                    "output_format": "请按照Thought -> Action的格式循环执行。",
                },
            ),
        ]

        for template in builtin_templates:
            self.templates[template.template_id] = template

        logger.info(f"📚 已加载 {len(builtin_templates)} 个内置模板")

    def register_template(self, template: PromptTemplate) -> None:
        """注册提示模板"""
        self.templates[template.template_id] = template
        logger.info(f"📝 注册模板: {template.name}")

    async def generate_prompt(
        self,
        template_id: str,
        variables: dict[str, Any],        technique: PromptTechnique | None = None,
    ) -> str:
        """
        生成提示

        Args:
            template_id: 模板ID
            variables: 变量
            technique: 提示技巧

        Returns:
            完整提示
        """
        if template_id not in self.templates:
            raise ValueError(f"模板 {template_id} 不存在")

        template = self.templates[template_id]

        # 应用技巧
        if technique:
            template = await self._apply_technique(template, technique)

        # 填充变量
        prompt_parts = []
        for _element_key, element_value in template.elements.items():
            try:
                filled_value = element_value.format(**variables)
                prompt_parts.append(filled_value)
            except KeyError as e:
                logger.warning(f"⚠️ 变量缺失: {e}")
                prompt_parts.append(element_value)

        prompt = "\n\n".join(prompt_parts)

        # 更新使用计数
        template.usage_count += 1

        return prompt

    async def _apply_technique(
        self, template: PromptTemplate, technique: PromptTechnique
    ) -> PromptTemplate:
        """应用提示技巧"""
        # 简化版:根据技巧调整模板
        new_template = PromptTemplate(
            template_id=f"{template.template_id}_{technique.value}",
            name=f"{template.name} ({technique.value})",
            description=template.description,
            technique=technique,
            elements=template.elements.copy(),
        )

        if technique == PromptTechnique.CHAIN_OF_THOUGHT:
            new_template.elements["reasoning"] = "让我们一步步来思考:"

        elif technique == PromptTechnique.SELF_CONSISTENCY:
            new_template.elements["output_format"] = "请给出3个可能的答案,然后选择最佳的一个。"

        elif technique == PromptTechnique.TREE_OF_THOUGHTS:
            new_template.elements["reasoning"] = "请考虑多个可能的路径:"
            new_template.elements["exploration"] = "探索每个路径的可能性:"

        return new_template

    async def evaluate_prompt(
        self,
        prompt: str,
        model_call: callable,
        evaluation_criteria: dict[str, Any] | None = None,
    ) -> EvaluationResult:
        """
        评估提示

        Args:
            prompt: 提示内容
            model_call: 模型调用函数
            evaluation_criteria: 评估标准

        Returns:
            评估结果
        """
        self.stats["total_evaluations"] += 1

        start_time = datetime.now()

        # 调用模型
        try:
            output = await model_call(prompt)

            # 计算指标
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            token_count = len(output.split())

            # 简化版:计算质量分数
            quality_score = await self._compute_quality_score(output, evaluation_criteria)
            relevance_score = await self._compute_relevance_score(output, prompt)
            accuracy_score = await self._compute_accuracy_score(output, evaluation_criteria)

            result = EvaluationResult(
                prompt_id=f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                output=output,
                quality_score=quality_score,
                relevance_score=relevance_score,
                accuracy_score=accuracy_score,
                latency_ms=latency_ms,
                token_count=token_count,
            )

            self.evaluation_history.append(result)

            # 更新统计
            self.stats["avg_quality_score"] = (
                self.stats["avg_quality_score"] * (self.stats["total_evaluations"] - 1)
                + quality_score
            ) / self.stats["total_evaluations"]

            # 更新最佳提示
            if self.stats["best_prompt"] is None or quality_score > self.stats.get(
                "best_quality", 0
            ):
                self.stats["best_prompt"] = prompt
                self.stats["best_quality"] = quality_score

        except Exception as e:
            logger.error(f"❌ 评估失败: {e}")
            raise

        return result

    async def _compute_quality_score(
        self, output: str, criteria: dict[str, Any]
    ) -> float:
        """计算质量分数"""
        # 简化版:基于输出长度和结构
        score = 0.5

        # 长度适中
        if 100 <= len(output) <= 1000:
            score += 0.2

        # 有结构
        if any(marker in output for marker in ["1.", "2.", "首先", "其次", "结论"]):
            score += 0.2

        # 无重复
        sentences = output.split("。")
        unique_ratio = len(set(sentences)) / max(1, len(sentences))
        score += unique_ratio * 0.1

        return min(1.0, score)

    async def _compute_relevance_score(self, output: str, prompt: str) -> float:
        """计算相关性分数"""
        # 简化版:基于关键词重叠
        prompt_words = set(prompt.lower().split())
        output_words = set(output.lower().split())

        if not prompt_words:
            return 0.5

        overlap = len(prompt_words & output_words)
        relevance = min(1.0, overlap / len(prompt_words) * 2)

        return relevance

    async def _compute_accuracy_score(
        self, output: str, criteria: dict[str, Any]
    ) -> float:
        """计算准确性分数"""
        # 简化版:基于预定义标准
        if criteria and "expected_keywords" in criteria:
            expected = criteria["expected_keywords"]
            matched = sum(1 for kw in expected if kw.lower() in output.lower())
            return matched / len(expected) if expected else 0.5

        return 0.7  # 默认分数

    async def optimize_prompt(
        self,
        current_prompt: str,
        evaluation_history: list[EvaluationResult],
        optimization_goals: dict[str, float] | None = None,
    ) -> list[OptimizationSuggestion]:
        """
        优化提示

        Args:
            current_prompt: 当前提示
            evaluation_history: 评估历史
            optimization_goals: 优化目标

        Returns:
            优化建议列表
        """
        suggestions = []

        # 分析当前提示
        analysis = await self._analyze_prompt(current_prompt)

        # 生成建议
        for issue, improvement in analysis.items():
            suggestion = OptimizationSuggestion(
                suggestion_id=f"sugg_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                target_element=PromptElement(issue),
                current_content=current_prompt,
                suggested_content=improvement["suggestion"],
                reason=improvement["reason"],
                expected_improvement=improvement.get("improvement", 0.1),
            )
            suggestions.append(suggestion)

        self.suggestions.extend(suggestions)

        logger.info(f"💡 生成 {len(suggestions)} 条优化建议")

        return suggestions

    async def _analyze_prompt(self, prompt: str) -> dict[str, dict[str, str]]:
        """分析提示"""
        analysis = {}

        # 检查上下文
        if "上下文" not in prompt and "context" not in prompt.lower():
            analysis["context"] = {
                "suggestion": prompt + "\n\n上下文:{context}",
                "reason": "添加上下文可以提高理解",
                "improvement": 0.15,
            }

        # 检查示例
        if "示例" not in prompt and "example" not in prompt.lower():
            analysis["examples"] = {
                "suggestion": prompt + "\n\n示例:\n{examples}",
                "reason": "示例可以引导模型理解预期格式",
                "improvement": 0.2,
            }

        # 检查输出格式
        if "格式" not in prompt and "format" not in prompt.lower():
            analysis["output_format"] = {
                "suggestion": prompt + "\n\n输出格式:\n{output_format}",
                "reason": "明确输出格式可以提高结果可预测性",
                "improvement": 0.1,
            }

        # 检查约束
        if len(prompt) < 200:
            analysis["constraints"] = {
                "suggestion": prompt + "\n\n约束:\n- 不要使用无关信息\n- 保持简洁",
                "reason": "添加约束可以减少幻觉",
                "improvement": 0.1,
            }

        return analysis

    async def run_ab_test(
        self, prompt_a: str, prompt_b: str, model_call: callable, num_samples: int = 10
    ) -> dict[str, Any]:
        """
        运行A/B测试

        Args:
            prompt_a: 提示A
            prompt_b: 提示B
            model_call: 模型调用函数
            num_samples: 样本数量

        Returns:
            测试结果
        """
        logger.info(f"🧪 开始A/B测试 ({num_samples} 样本)")

        results_a = []
        results_b = []

        for _i in range(num_samples):
            # 测试提示A
            result_a = await self.evaluate_prompt(prompt_a, model_call)
            results_a.append(result_a)

            # 测试提示B
            result_b = await self.evaluate_prompt(prompt_b, model_call)
            results_b.append(result_b)

        # 计算统计
        avg_quality_a = sum(r.quality_score for r in results_a) / num_samples
        avg_quality_b = sum(r.quality_score for r in results_b) / num_samples

        avg_latency_a = sum(r.latency_ms for r in results_a) / num_samples
        avg_latency_b = sum(r.latency_ms for r in results_b) / num_samples

        improvement = (avg_quality_b - avg_quality_a) / max(avg_quality_a, 0.01)

        result = {
            "prompt_a": {"avg_quality": avg_quality_a, "avg_latency_ms": avg_latency_a},
            "prompt_b": {"avg_quality": avg_quality_b, "avg_latency_ms": avg_latency_b},
            "improvement": improvement,
            "recommendation": "prompt_b" if improvement > 0 else "prompt_a",
            "winner": "B" if avg_quality_b > avg_quality_a else "A",
        }

        logger.info(f"✅ A/B测试完成: 推荐 {result['recommendation']}")

        return result

    def get_status(self) -> dict[str, Any]:
        """获取优化器状态"""
        # 按技巧统计模板
        technique_stats = defaultdict(int)
        for template in self.templates.values():
            technique_stats[template.technique.value] += 1

        return {
            "name": self.name,
            "version": self.version,
            "templates": len(self.templates),
            "variants": len(self.variants),
            "technique_distribution": dict(technique_stats),
            "statistics": self.stats,
            "recent_suggestions": len(self.suggestions),
            "evaluation_history_size": len(self.evaluation_history),
        }


# 全局单例
_prompt_optimizer_instance: PromptEngineeringOptimizer | None = None


def get_prompt_optimizer() -> PromptEngineeringOptimizer:
    """获取提示工程优化器实例"""
    global _prompt_optimizer_instance
    if _prompt_optimizer_instance is None:
        _prompt_optimizer_instance = PromptEngineeringOptimizer()
    return _prompt_optimizer_instance
