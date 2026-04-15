#!/usr/bin/env python3
"""
生产环境反思引擎
Production Reflection Engine

集成统一LLM管理器，支持MLX qwen3.5等本地模型
用于生产环境的AI输出质量评估和改进

作者: 徐健 (xujian519@gmail.com)
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import json
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ReflectionLevel(Enum):
    """反思级别"""
    BASIC = "basic"          # 基础反思
    DETAILED = "detailed"    # 详细反思
    COMPREHENSIVE = "comprehensive"  # 全面反思


class QualityMetric(Enum):
    """质量评估指标"""
    ACCURACY = "accuracy"        # 准确性
    COMPLETENESS = "completeness"  # 完整性
    CLARITY = "clarity"          # 清晰度
    RELEVANCE = "relevance"      # 相关性
    USEFULNESS = "usefulness"    # 有用性
    CONSISTENCY = "consistency"  # 一致性


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
    model_used: str = ""
    processing_time: float = 0.0


class ProductionReflectionEngine:
    """
    生产环境反思引擎

    特点:
    - 支持多种LLM后端（MLX、OpenAI等）
    - 自动JSON提取（处理markdown代码块）
    - 质量阈值配置
    - 迭代改进支持
    """

    def __init__(
        self,
        llm_client: Any | None = None,
        llm_generate_func: Callable | None = None,
        default_model: str = "qwen3.5:latest",
        max_reflection_attempts: int = 3,
    ):
        """
        初始化生产环境反思引擎

        Args:
            llm_client: LLM客户端实例
            llm_generate_func: LLM生成函数（异步），签名: async def(prompt: str) -> str
            default_model: 默认模型名称
            max_reflection_attempts: 最大改进尝试次数
        """
        self.llm_client = llm_client
        self.llm_generate_func = llm_generate_func
        self.default_model = default_model
        self.max_reflection_attempts = max_reflection_attempts

        # 质量阈值
        self.quality_thresholds = {
            QualityMetric.ACCURACY: 0.85,
            QualityMetric.COMPLETENESS: 0.80,
            QualityMetric.CLARITY: 0.85,
            QualityMetric.RELEVANCE: 0.90,
            QualityMetric.USEFULNESS: 0.80,
            QualityMetric.CONSISTENCY: 0.90,
        }

        # 统计信息
        self.stats = {
            "total_reflections": 0,
            "successful_reflections": 0,
            "failed_reflections": 0,
            "refinements_triggered": 0,
            "average_score": 0.0,
        }

    async def reflect(
        self,
        prompt: str,
        output: str,
        context: dict[str, Any] | None = None,
        level: ReflectionLevel = ReflectionLevel.DETAILED,
    ) -> ReflectionResult:
        """
        执行反思评估

        Args:
            prompt: 原始提示
            output: AI输出
            context: 上下文信息
            level: 反思级别

        Returns:
            ReflectionResult: 反思结果
        """
        import time
        start_time = time.time()

        self.stats["total_reflections"] += 1

        try:
            # 构建反思提示
            reflection_prompt = self._build_reflection_prompt(prompt, output, context or {}, level)

            # 调用LLM
            response = await self._call_llm(reflection_prompt)

            # 解析结果
            result = self._parse_response(response)
            result.model_used = self.default_model
            result.processing_time = time.time() - start_time

            # 更新统计
            self.stats["successful_reflections"] += 1
            self._update_average_score(result.overall_score)

            if result.should_refine:
                self.stats["refinements_triggered"] += 1

            logger.info(f"✅ 反思完成: 总分={result.overall_score:.2f}, 耗时={result.processing_time:.2f}s")
            return result

        except Exception as e:
            self.stats["failed_reflections"] += 1
            logger.error(f"❌ 反思失败: {e}")
            return ReflectionResult(
                overall_score=0.5,
                metric_scores=dict.fromkeys(QualityMetric, 0.5),
                feedback=f"反思评估出现错误: {str(e)}",
                suggestions=["请重新生成输出"],
                should_refine=False,
                model_used=self.default_model,
                processing_time=time.time() - start_time,
            )

    def _build_reflection_prompt(
        self,
        prompt: str,
        output: str,
        context: dict[str, Any],
        level: ReflectionLevel,
    ) -> str:
        """构建反思提示"""

        level_instructions = {
            ReflectionLevel.BASIC: "请对输出进行基础评估",
            ReflectionLevel.DETAILED: "请对输出进行详细评估，并提供具体建议",
            ReflectionLevel.COMPREHENSIVE: "请对输出进行全面评估，包括多维度分析和改进方案",
        }

        context_str = json.dumps(context, indent=2, ensure_ascii=False) if context else "{}"

        return f'''你是一个专业的AI输出质量评估专家。请对以下AI输出进行评估。

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
{context_str}

## 评估标准 (0-1分)
- accuracy: 准确性 (阈值: 0.85)
- completeness: 完整性 (阈值: 0.80)
- clarity: 清晰度 (阈值: 0.85)
- relevance: 相关性 (阈值: 0.90)
- usefulness: 有用性 (阈值: 0.80)
- consistency: 一致性 (阈值: 0.90)

## 评估要求
1. 对每个指标给出0-1的评分
2. 提供具体的反馈和建议
3. 判断是否需要改进输出

请严格按以下JSON格式返回（不要添加其他内容）:
{{
    "overall_score": 0.85,
    "metric_scores": {{
        "accuracy": 0.9,
        "completeness": 0.8,
        "clarity": 0.88,
        "relevance": 0.92,
        "usefulness": 0.85,
        "consistency": 0.9
    }},
    "feedback": "输出整体质量评估反馈",
    "suggestions": ["改进建议1", "改进建议2"],
    "should_refine": true
}}'''

    async def _call_llm(self, prompt: str) -> str:
        """调用LLM"""
        # 方式1: 使用提供的生成函数
        if self.llm_generate_func:
            return await self.llm_generate_func(prompt)

        # 方式2: 使用llm_client的generate_response方法
        if self.llm_client and hasattr(self.llm_client, 'generate_response'):
            return await self.llm_client.generate_response(prompt)

        # 方式3: 尝试使用统一LLM管理器
        try:
            from core.llm.unified_llm_manager import UnifiedLLMManager
            manager = UnifiedLLMManager()
            response = await manager.generate(
                message=prompt,
                task_type="reflection",
                preferred_model=self.default_model,
            )
            return response.content
        except Exception as e:
            logger.warning(f"统一LLM管理器调用失败: {e}")

        # 降级：返回模拟响应
        logger.warning("⚠️ 无法连接LLM，返回模拟响应")
        return self._mock_response(prompt)

    def _mock_response(self, prompt: str) -> str:
        """模拟响应（降级方案）"""
        return json.dumps({
            "overall_score": 0.75,
            "metric_scores": {
                "accuracy": 0.80,
                "completeness": 0.75,
                "clarity": 0.78,
                "relevance": 0.82,
                "usefulness": 0.70,
                "consistency": 0.76,
            },
            "feedback": "模拟评估：输出质量中等，建议进行实际LLM评估",
            "suggestions": ["请配置有效的LLM后端"],
            "should_refine": True,
        })

    def _extract_json(self, response: str) -> str:
        """从响应中提取JSON"""
        # 尝试markdown代码块
        match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response)
        if match:
            return match.group(1).strip()

        # 尝试直接JSON对象
        match = re.search(r'\{[\s\S]*\}', response)
        if match:
            return match.group(0)

        return response

    def _parse_response(self, response: str) -> ReflectionResult:
        """解析LLM响应"""
        try:
            json_str = self._extract_json(response)
            data = json.loads(json_str)

            metric_scores = {}
            for metric in QualityMetric:
                metric_scores[metric] = data.get("metric_scores", {}).get(metric.value, 0.5)

            return ReflectionResult(
                overall_score=data.get("overall_score", 0.5),
                metric_scores=metric_scores,
                feedback=data.get("feedback", ""),
                suggestions=data.get("suggestions", []),
                should_refine=data.get("should_refine", False),
            )

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return ReflectionResult(
                overall_score=0.5,
                metric_scores=dict.fromkeys(QualityMetric, 0.5),
                feedback="反思评估解析错误",
                suggestions=["请重新生成输出"],
                should_refine=False,
            )

    def _update_average_score(self, score: float):
        """更新平均分统计"""
        n = self.stats["successful_reflections"]
        old_avg = self.stats["average_score"]
        self.stats["average_score"] = (old_avg * (n - 1) + score) / n

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "quality_thresholds": {m.value: t for m, t in self.quality_thresholds.items()},
            "default_model": self.default_model,
        }

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_reflections": 0,
            "successful_reflections": 0,
            "failed_reflections": 0,
            "refinements_triggered": 0,
            "average_score": 0.0,
        }


# 便捷工厂函数
def create_mlx_reflection_engine(
    model_id: str = "qwen3.5:latest",
    base_url: str = "http://127.0.0.1:8765",
) -> ProductionReflectionEngine:
    """
    创建基于MLX的反思引擎

    Args:
        model_id: MLX模型ID
        base_url: MLX服务地址

    Returns:
        ProductionReflectionEngine实例
    """
    from core.llm.adapters.ollama_adapter import OllamaAdapter, create_ollama_capabilities
    from core.llm.base import LLMRequest

    class MLXClient:
        def __init__(self, model_id: str, base_url: str):
            capabilities = create_ollama_capabilities()
            capability = capabilities.get(model_id, capabilities.get('qwen3.5'))

            self.adapter = OllamaAdapter(
                model_id=model_id,
                capability=capability,
                base_url=base_url
            )
            self._initialized = False

        async def initialize(self):
            self._initialized = await self.adapter.initialize()
            return self._initialized

        async def generate_response(self, prompt: str) -> str:
            if not self._initialized:
                await self.initialize()

            request = LLMRequest(
                message=prompt,
                task_type="reflection",
                temperature=0.1,
                max_tokens=2000
            )
            response = await self.adapter.generate(request)
            return response.content

        async def close(self):
            if self.adapter:
                await self.adapter.close()

    client = MLXClient(model_id, base_url)

    engine = ProductionReflectionEngine(
        llm_client=client,
        default_model=model_id,
    )

    # 存储client引用以便后续关闭
    engine._mlx_client = client

    return engine


# 使用示例
async def example_usage():
    """使用示例"""
    # 创建反思引擎
    engine = create_mlx_reflection_engine("qwen3.5:latest")

    try:
        # 执行反思
        result = await engine.reflect(
            prompt="请分析专利的技术特征",
            output="该专利涉及深度学习图像识别技术...",
            context={"domain": "patent_analysis"},
            level=ReflectionLevel.DETAILED,
        )

        print(f"总体评分: {result.overall_score:.2f}")
        print(f"反馈: {result.feedback}")
        print(f"建议: {result.suggestions}")

    finally:
        # 关闭客户端
        if hasattr(engine, '_mlx_client'):
            await engine._mlx_client.close()


if __name__ == "__main__":
    asyncio.run(example_usage())
