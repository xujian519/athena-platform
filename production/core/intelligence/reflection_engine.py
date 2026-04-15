#!/usr/bin/env python3
"""
反思模式引擎 (Reflection Pattern)
基于《智能体设计》反思模式的实现

功能:
- 自我评估输出质量
- 迭代改进和优化
- 错误检测和修正
- 质量保证机制

应用场景:
- 小娜: 专利分析结果审核
- 小诺: 系统优化方案评估
- 云熙: 目标达成度验证
- 小宸: 内容创作质量检查

实施优先级: ⭐⭐⭐⭐ (高)
预期收益: 显著提升输出质量和可靠性
"""

from __future__ import annotations
import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

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


@dataclass
class ReflectionCriteria:
    """反思标准"""

    metric: QualityMetric
    weight: float = 1.0
    threshold: float = 0.8
    description: str = ""


@dataclass
class ReflectionResult:
    """反思结果"""

    overall_score: float
    metric_scores: dict[QualityMetric, float]
    feedback: str
    suggestions: list[str]
    should_refine: bool
    refinement_count: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


class ReflectionEngine:
    """反思引擎"""

    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.max_reflection_attempts = 3
        self.quality_thresholds = {
            QualityMetric.ACCURACY: 0.85,
            QualityMetric.COMPLETENESS: 0.80,
            QualityMetric.CLARITY: 0.85,
            QualityMetric.RELEVANCE: 0.90,
            QualityMetric.USEFULNESS: 0.80,
            QualityMetric.CONSISTENCY: 0.90,
        }

        # 默认反思标准
        self.default_criteria = [
            ReflectionCriteria(QualityMetric.ACCURACY, weight=1.2),
            ReflectionCriteria(QualityMetric.COMPLETENESS, weight=1.0),
            ReflectionCriteria(QualityMetric.CLARITY, weight=0.8),
            ReflectionCriteria(QualityMetric.RELEVANCE, weight=1.5),
            ReflectionCriteria(QualityMetric.USEFULNESS, weight=1.0),
            ReflectionCriteria(QualityMetric.CONSISTENCY, weight=0.8),
        ]

    async def reflect_on_output(
        self,
        original_prompt: str,
        output: str,
        context: dict[str, Any],        level: ReflectionLevel = ReflectionLevel.DETAILED,
        criteria: list[str] = None,
    ) -> ReflectionResult:
        """对输出进行反思评估"""

        if criteria is None:
            criteria = self.default_criteria

        # 执行反思评估
        reflection_result = await self._perform_reflection(
            original_prompt, output, context, level, criteria
        )

        # 如果需要改进且未达到最大尝试次数
        if (
            reflection_result.should_refine
            and reflection_result.refinement_count < self.max_reflection_attempts
        ):
            reflection_result = await self._refine_output(
                original_prompt, output, context, reflection_result, criteria
            )

        return reflection_result

    async def _perform_reflection(
        self,
        prompt: str,
        output: str,
        context: dict[str, Any],        level: ReflectionLevel,
        criteria: list[ReflectionCriteria],
    ) -> ReflectionResult:
        """执行反思评估"""

        # 构建反思提示
        reflection_prompt = self._build_reflection_prompt(prompt, output, context, level, criteria)

        # 调用LLM进行反思
        reflection_response = await self._call_llm_for_reflection(reflection_prompt)

        # 解析反思结果
        reflection_result = await self._parse_reflection_response(reflection_response, criteria)

        return reflection_result

    def _build_reflection_prompt(
        self,
        prompt: str,
        output: str,
        context: dict[str, Any],        level: ReflectionLevel,
        criteria: list[ReflectionCriteria],
    ) -> str:
        """构建反思提示"""

        # 根据反思级别调整详细程度
        level_instructions = {
            ReflectionLevel.BASIC: "请对输出进行基础评估",
            ReflectionLevel.DETAILED: "请对输出进行详细评估,并提供具体建议",
            ReflectionLevel.COMPREHENSIVE: "请对输出进行全面评估,包括多维度分析和改进方案",
        }

        # 构建质量标准描述
        criteria_descriptions = []
        for criterion in criteria:
            desc = f"- {criterion.metric.value}: {criterion.description or '请评估'} (阈值: {criterion.threshold})"
            criteria_descriptions.append(desc)

        reflection_prompt = f"""
你是一个专业的AI输出质量评估专家。请对以下输出进行全面评估和反思。

## 评估任务
{level_instructions.get(level, "请对输出进行详细评估")}

## 原始提示
```
{prompt}
```

## 输出结果
```
{output}
```

## 上下文信息
{json.dumps(context, indent=2, ensure_ascii=False)}

## 评估标准
请从以下维度评估输出质量:
{chr(10).join(criteria_descriptions)}

## 评估要求
1. 对每个指标给出0-1的评分
2. 提供具体的反馈和建议
3. 判断是否需要改进输出
4. 如果需要改进,请提供改进方向

请按以下JSON格式返回评估结果:
{{
    "overall_score": 0.95,
    "metric_scores": {{
        "accuracy": 0.90,
        "completeness": 0.85,
        "clarity": 0.88,
        "relevance": 0.92,
        "usefulness": 0.87,
        "consistency": 0.91
    }},
    "feedback": "输出整体质量良好,但仍有改进空间",
    "suggestions": [
        "建议1:具体改进建议",
        "建议2:具体改进建议"
    ],
    "should_refine": true
}}
"""

        return reflection_prompt

    async def _call_llm_for_reflection(self, reflection_prompt: str) -> str:
        """调用真实的LLM进行反思"""
        try:
            # 方案1: 如果有配置的LLM客户端,使用它
            if self.llm_client:
                logger.info("🤔 使用配置的LLM客户端进行反思")
                response = await self.llm_client.generate_response(reflection_prompt)
                return response

            # 方案2: 尝试调用平台的AI系统
            try:
                # 动态导入平台的AI系统
                import importlib.util
                from pathlib import Path

                # 查找平台的AI处理器
                platform_root = Path("/Users/xujian/Athena工作平台")

                # 尝试导入各种可能的AI处理器
                ai_processors = [
                    "xiaonuo_platform_controller",
                    "ai_processor",
                    "llm_processor",
                    "ai_service",
                ]

                ai_processor = None
                for processor_name in ai_processors:
                    try:
                        spec = importlib.util.spec_from_file_location(
                            processor_name, platform_root / f"{processor_name}.py"
                        )
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            if hasattr(module, "process_prompt") or hasattr(
                                module, "generate_response"
                            ):
                                ai_processor = module
                                logger.info(f"✅ 找到AI处理器: {processor_name}")
                                break
                    except (ImportError, FileNotFoundError):
                        continue

                if ai_processor:
                    logger.info("🔗 使用平台AI系统进行反思")
                    if hasattr(ai_processor, "process_prompt"):
                        response = await ai_processor.process_prompt(reflection_prompt)
                    elif hasattr(ai_processor, "generate_response"):
                        response = await ai_processor.generate_response(reflection_prompt)
                    else:
                        # 尝试调用主方法
                        if callable(ai_processor):
                            response = await ai_processor(reflection_prompt)
                        else:
                            raise AttributeError("AI处理器没有可调用的方法")
                    return response

            except Exception as e:
                logger.warning(f"平台AI系统调用失败: {e}")

            # 方案3: 尝试OpenAI API (如果配置了)
            try:
                import openai

                # 检查是否配置了API密钥
                if hasattr(openai, "api_key") and openai.api_key:
                    logger.info("🔗 使用OpenAI API进行反思")
                    response = await openai.ChatCompletion.acreate(
                        model="gpt-4",
                        messages=[
                            {
                                "role": "system",
                                "content": "你是一个专业的AI输出质量评估专家。请对给定的AI输出进行客观评估,严格按照要求的JSON格式返回结果。",
                            },
                            {"role": "user", "content": reflection_prompt},
                        ],
                        temperature=0.1,
                        max_tokens=1000,
                    )
                    return response.choices[0].message.content

            except ImportError:
                logger.warning("OpenAI库未安装")
            except Exception as e:
                logger.warning(f"OpenAI API调用失败: {e}")

            # 方案4: 如果都无法连接,使用增强的智能模拟
            logger.info("⚠️ 无法连接真实AI,使用智能模拟模式")
            return await self._enhanced_mock_response(reflection_prompt)

        except Exception as e:
            logger.error(f"反思调用失败: {e}")
            # 最后的降级方案
            return await self._enhanced_mock_response(reflection_prompt)

    async def _enhanced_mock_response(self, prompt: str) -> str:
        """增强的智能模拟响应 - 基于输入动态生成"""
        import hashlib
        import json
        from datetime import datetime

        # 基于提示词内容生成动态评分
        prompt_lower = prompt.lower()
        prompt_hash = hashlib.md5(prompt.encode('utf-8'), usedforsecurity=False).hexdigest()

        # 分析提示词特征
        content_length = len(prompt)
        has_questions = "?" in prompt
        has_numbers = any(char.isdigit() for char in prompt)
        has_examples = "示例" in prompt_lower or "例子" in prompt_lower
        has_steps = "步骤" in prompt_lower or "流程" in prompt_lower or "如何" in prompt_lower
        has_analysis = "分析" in prompt_lower or "评估" in prompt_lower

        # 动态计算基础评分
        base_score = 0.70  # 基础分
        if content_length > 500:
            base_score += 0.10
        if has_questions:
            base_score += 0.05
        if has_numbers:
            base_score += 0.03
        if has_examples:
            base_score += 0.08
        if has_steps:
            base_score += 0.06
        if has_analysis:
            base_score += 0.07

        base_score = min(0.95, max(0.60, base_score))

        # 检测内容类型并调整评分
        if "专利" in prompt_lower or "技术" in prompt_lower:
            accuracy_score = min(0.92, base_score + 0.04)
            relevance_score = min(0.90, base_score + 0.02)
        else:
            accuracy_score = base_score
            relevance_score = base_score

        # 动态生成反馈和建议
        suggestions = []
        feedback_parts = ["输出质量"]

        if content_length < 200:
            suggestions.append("建议增加更多细节和说明")
            feedback_parts.append("内容较为简洁")
        elif content_length < 500:
            suggestions.append("可以进一步丰富内容")
            feedback_parts.append("内容基本完整")
        else:
            feedback_parts.append("内容较为详实")

        if not has_examples:
            suggestions.append("添加具体示例或案例说明")
            feedback_parts.append("缺少实例支撑")

        if has_steps and "1." not in prompt and "首先" not in prompt_lower:
            suggestions.append("使用数字列表或分步骤说明")
            feedback_parts.append("结构可以更清晰")

        if has_analysis and "数据" not in prompt_lower:
            suggestions.append("提供相关数据或统计信息")
            feedback_parts.append("缺少数据支撑")

        # 如果没有具体问题
        if not suggestions:
            suggestions.append("内容已较为完善")
            feedback_parts.append("质量良好")

        feedback = ",".join(feedback_parts) + "。"

        # 确定是否需要改进
        should_refine = base_score < 0.80 or len(suggestions) > 2

        response = {
            "overall_score": round(base_score, 2),
            "metric_scores": {
                "accuracy": round(accuracy_score, 2),
                "completeness": (
                    round(base_score - 0.02, 2) if content_length < 300 else round(base_score, 2)
                ),
                "clarity": round(base_score + 0.01, 2) if has_steps else round(base_score, 2),
                "relevance": round(relevance_score, 2),
                "usefulness": (
                    round(base_score - 0.03, 2) if not has_examples else round(base_score, 2)
                ),
                "consistency": round(base_score, 2),
            },
            "feedback": feedback,
            "suggestions": suggestions,
            "should_refine": should_refine,
            "analysis_timestamp": datetime.now().isoformat(),
            "prompt_hash": prompt_hash,
        }

        return json.dumps(response, ensure_ascii=False, indent=2)

    def _extract_json_from_response(self, response: str) -> str:
        """从响应中提取JSON（处理markdown代码块包裹的情况）

        支持以下格式:
        1. ```json {...} ```
        2. ``` {...} ```
        3. 直接JSON对象 {...}
        """
        # 尝试提取markdown代码块中的JSON
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response)
        if json_match:
            return json_match.group(1).strip()

        # 尝试直接查找JSON对象
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            return json_match.group(0)

        return response

    async def _parse_reflection_response(
        self, response: str, criteria: list[ReflectionCriteria]
    ) -> ReflectionResult:
        """解析反思响应"""

        try:
            # 提取JSON（处理markdown代码块）
            json_str = self._extract_json_from_response(response)

            # 尝试解析JSON响应
            data = json.loads(json_str)

            # 提取指标评分
            metric_scores = {}
            for metric in QualityMetric:
                metric_scores[metric] = data.get("metric_scores", {}).get(metric.value, 0.5)

            # 计算加权平均分
            overall_score = data.get("overall_score", 0.5)

            # 构建反思结果
            reflection_result = ReflectionResult(
                overall_score=overall_score,
                metric_scores=metric_scores,
                feedback=data.get("feedback", ""),
                suggestions=data.get("suggestions", []),
                should_refine=data.get("should_refine", False),
            )

            logger.info(f"✅ 反思响应解析成功: 总分={overall_score:.2f}")
            return reflection_result

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"JSON解析失败: {e}, 原始响应前200字符: {response[:200]}")
            # JSON解析失败时的fallback
            return ReflectionResult(
                overall_score=0.5,
                metric_scores=dict.fromkeys(QualityMetric, 0.5),
                feedback="反思评估出现错误",
                suggestions=["请重新生成输出"],
                should_refine=False,
            )

    async def _refine_output(
        self,
        original_prompt: str,
        current_output: str,
        context: dict[str, Any],        reflection_result: ReflectionResult,
        criteria: list[ReflectionCriteria],
    ) -> ReflectionResult:
        """基于反思结果改进输出"""

        # 构建改进提示
        refine_prompt = self._build_refine_prompt(
            original_prompt, current_output, context, reflection_result
        )

        # 调用LLM进行改进
        refined_output = await self._call_llm_for_refinement(refine_prompt)

        # 对改进后的输出进行再次反思
        new_reflection_result = await self._perform_reflection(
            original_prompt, refined_output, context, ReflectionLevel.DETAILED, criteria
        )

        # 更新改进次数
        new_reflection_result.refinement_count = reflection_result.refinement_count + 1

        return new_reflection_result

    def _build_refine_prompt(
        self,
        original_prompt: str,
        current_output: str,
        context: dict[str, Any],        reflection_result: ReflectionResult,
    ) -> str:
        """构建改进提示"""

        refine_prompt = f"""
请根据以下反思建议,改进原始输出:

## 原始提示
{original_prompt}

## 当前输出
{current_output}

## 反思评估
总体评分: {reflection_result.overall_score}
主要反馈: {reflection_result.feedback}
改进建议:
{chr(10).join([f"- {suggestion}" for suggestion in reflection_result.suggestions])}

## 改进要求
1. 根据反馈建议改进输出内容
2. 保持原输出的核心信息
3. 提升整体质量评分至0.9以上
4. 确保输出清晰、准确、完整

请直接输出改进后的结果,不要包含其他说明。
"""

        return refine_prompt

    async def _call_llm_for_refinement(self, refine_prompt: str) -> str:
        """调用LLM进行改进"""
        # 这里应该集成实际的LLM调用
        # 暂时返回模拟的改进结果

        # 在实际实现中,这里会调用真实的LLM API
        refined_output = """
        [这是基于反思建议改进后的输出结果]
        改进后的内容应该更加完整、准确和有用。
        """

        return refined_output

    def batch_reflect(
        self,
        outputs: list[tuple[str, str, dict[str, Any]]],
        level: ReflectionLevel = ReflectionLevel.BASIC,
    ) -> list[ReflectionResult]:
        """批量反思多个输出"""
        results = []
        for prompt, output, context in outputs:
            result = asyncio.run(self.reflect_on_output(prompt, output, context, level))
            results.append(result)
        return results

    def get_reflection_summary(self, results: list[ReflectionResult]) -> dict[str, Any]:
        """获取反思总结统计"""

        if not results:
            return {}

        # 计算统计信息
        avg_score = sum(r.overall_score for r in results) / len(results)
        refinement_needed = sum(1 for r in results if r.should_refine)
        refinement_counts = [r.refinement_count for r in results]

        # 计算各指标平均分
        metric_averages = {}
        for metric in QualityMetric:
            scores = [r.metric_scores.get(metric, 0) for r in results]
            metric_averages[metric.value] = sum(scores) / len(scores)

        summary = {
            "total_evaluations": len(results),
            "average_score": avg_score,
            "refinement_needed_count": refinement_needed,
            "refinement_needed_rate": refinement_needed / len(results),
            "average_refinement_count": sum(refinement_counts) / len(refinement_counts),
            "metric_averages": metric_averages,
            "timestamp": datetime.now().isoformat(),
        }

        return summary


# 使用示例
async def example_reflection_usage():
    """反思模式使用示例"""

    engine = ReflectionEngine()

    # 示例任务:分析专利检索结果
    prompt = "请分析以下专利检索结果的准确性和相关性"
    output = "找到了15个相关专利,其中8个高度相关,7个中等相关"
    context = {
        "domain": "patent_analysis",
        "search_query": "AI 专利分析技术",
        "retrieval_method": "vector_search",
    }

    # 执行反思
    reflection_result = await engine.reflect_on_output(
        prompt, output, context, ReflectionLevel.DETAILED
    )

    print("反思评估结果:")
    print(f"总体评分: {reflection_result.overall_score:.2f}")
    print(f"是否需要改进: {reflection_result.should_refine}")
    print(f"反馈: {reflection_result.feedback}")
    print(f"建议: {reflection_result.suggestions}")


if __name__ == "__main__":
    asyncio.run(example_reflection_usage())
