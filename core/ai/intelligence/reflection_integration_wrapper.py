#!/usr/bin/env python3

"""
反思引擎集成包装器
Reflection Engine Integration Wrapper

将反思引擎无缝集成到现有AI处理流程中,实现AI输出质量的自动提升

主要功能:
- 包装现有AI调用,添加反思评估
- 自动质量检测和改进建议
- 多种AI系统自动连接
- 性能监控和统计

作者: Athena AI团队
创建时间: 2025-12-17 05:55:00
版本: v1.0.0 "智能升级"
"""

import asyncio
import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from typing import Any, Optional

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

# 导入修改后的反思引擎
try:
    from .reflection_engine import ReflectionEngine, ReflectionLevel, ReflectionResult
except ImportError:
    from reflection_engine import ReflectionEngine, ReflectionLevel, ReflectionResult


@dataclass
class ReflectionConfig:
    """反思配置"""

    enable_reflection: bool = True
    reflection_level: ReflectionLevel = ReflectionLevel.DETAILED
    auto_improve: bool = False  # 是否自动改进输出
    cache_reflections: bool = True  # 缓存反思结果
    quality_threshold: float = 0.80  # 质量阈值
    max_reflection_time: float = 5.0  # 最大反思时间(秒)


class ReflectionIntegrationWrapper:
    """反思引擎集成包装器"""

    def __init__(
        self, ai_processor: Optional[Any] = None, config: Optional[ReflectionConfig] = None
    ):
        """
        初始化反思集成包装器

        Args:
            ai_processor: 现有的AI处理器
            config: 反思配置
        """
        self.ai_processor = ai_processor
        self.config = config or ReflectionConfig()
        self.reflection_engine = ReflectionEngine(llm_client=ai_processor)
        self.reflection_cache = {}  # 反思结果缓存
        self.stats = {
            "total_calls": 0,
            "reflections_performed": 0,
            "improvements_suggested": 0,
            "average_quality_score": 0.0,
            "total_reflection_time": 0.0,
        }

        logger.info("🤔 反思引擎集成包装器已初始化")
        if self.ai_processor:
            logger.info(f"✅ 已连接到AI处理器: {type(self.ai_processor).__name__}")
        else:
            logger.info("🔗 将自动检测平台AI系统")

    async def process_with_reflection(
        self, prompt: str, context: Optional[dict[str, Any]] = None, **kwargs
    ) -> dict[str, Any]:
        """
        带反思的AI处理流程

        Args:
            prompt: 输入提示
            context: 上下文信息
            **kwargs: 其他AI调用参数

        Returns:
            包含原始输出、反思结果和改进输出的字典
        """
        start_time = time.time()
        self.stats["total_calls"] += 1

        logger.info("🚀 开始处理AI请求(带反思)")

        # 第一步:调用原始AI处理器生成响应
        original_output = await self._call_original_ai(prompt, context, **kwargs)

        # 第二步:使用反思引擎评估质量
        if self.config.enable_reflection:
            reflection_result = await self._perform_reflection(prompt, original_output, context)
        else:
            reflection_result = None

        # 第三步:根据反思结果决定是否改进
        improved_output = None
        if self.config.auto_improve and reflection_result and reflection_result.should_refine:
            improved_output = await self._improve_output(prompt, original_output, reflection_result)

        # 第四步:构建返回结果
        processing_time = time.time() - start_time

        result = {
            "success": True,
            "original_output": original_output,
            "reflection_result": reflection_result,
            "improved_output": improved_output,
            "processing_time": processing_time,
            "reflection_enabled": self.config.enable_reflection,
            "timestamp": datetime.now().isoformat(),
        }

        # 更新统计信息
        self._update_stats(reflection_result, processing_time)

        # 记录处理结果
        if reflection_result:
            logger.info(f"✅ AI处理完成,质量评分: {reflection_result.overall_score:.2f}")
            if reflection_result.should_refine:
                logger.info(f"🔧 建议改进: {len(reflection_result.suggestions)}项")

        return result

    async def _call_original_ai(
        self, prompt: str, context: dict[str, Any], **kwargs
    ) -> str:
        """调用原始AI处理器"""
        try:
            # 优先使用配置的AI处理器
            if self.ai_processor:
                if hasattr(self.ai_processor, "query_athena_agent"):
                    # YunPat AI集成服务
                    result = await self.ai_processor.query_athena_agent(prompt, context)
                    if "error" not in result:
                        return json.dumps(result, ensure_ascii=False)
                    else:
                        return f"AI调用失败: {result['error']}"

                elif hasattr(self.ai_processor, "process_prompt"):
                    # 通用处理器
                    result = await self.ai_processor.process_prompt(prompt)
                    return str(result)

                elif callable(self.ai_processor):
                    # 可调用对象
                    result = await self.ai_processor(prompt, **kwargs)
                    return str(result)

                else:
                    logger.warning("⚠️ AI处理器没有标准调用接口")
                    return "AI处理器接口不兼容"

            else:
                # 使用增强的模拟响应
                return await self._simulate_ai_response(prompt, context)

        except Exception as e:
            logger.error(f"❌ AI调用失败: {e}")
            return f"AI处理出错: {e!s}"

    async def _simulate_ai_response(self, prompt: str, context: dict[str, Any]) -> str:
        """模拟AI响应(当没有AI处理器时)"""
        # 基于提示词生成合理的模拟响应
        prompt_lower = prompt.lower()

        if "专利" in prompt_lower or "权利要求" in prompt_lower:
            return """基于您提供的专利信息,我分析如下:

1. 专利权利要求结构清晰
2. 保护范围定义合理
3. 建议进一步优化技术特征描述

具体建议:
- 补充技术效果的具体数据
- 明确技术问题的解决方案
- 增加实施例的详细说明"""

        elif "分析" in prompt_lower:
            return """根据您的问题,我的分析如下:

## 主要发现
- 系统运行状态良好
- 存在优化空间

## 建议措施
1. 加强质量控制
2. 优化处理流程
3. 增强系统稳定性

## 预期效果
通过以上措施,可以显著提升系统性能和用户体验。"""

        else:
            return f"根据您的询问:{prompt[:50]}...,我已理解您的问题并提供相应的解答和建议。"

    async def _perform_reflection(
        self, prompt: str, output: str, context: dict[str, Any]]
    ) -> ReflectionResult:
        """执行反思评估"""
        try:
            # 检查缓存
            if self.config.cache_reflections:
                cache_key = hash(prompt + output + str(context))
                if cache_key in self.reflection_cache:
                    logger.debug("📋 使用缓存的反思结果")
                    return self.reflection_cache[cache_key]

            # 执行反思
            self.stats["reflections_performed"] += 1
            logger.info("🤔 正在进行AI输出质量反思...")

            reflection_start = time.time()
            result = await self.reflection_engine.reflect_on_output(
                original_prompt=prompt,
                output=output,
                context=context or {},
                level=self.config.reflection_level,
            )
            reflection_time = time.time() - reflection_start

            # 限制反思时间
            if reflection_time > self.config.max_reflection_time:
                logger.warning(f"⏰ 反思时间过长: {reflection_time:.2f}秒")

            # 缓存结果
            if self.config.cache_reflections:
                self.reflection_cache[cache_key] = result
                # 限制缓存大小
                if len(self.reflection_cache) > 100:
                    self.reflection_cache.clear()

            return result

        except Exception as e:
            logger.error(f"❌ 反思评估失败: {e}")
            # 返回默认结果
            return ReflectionResult(
                overall_score=0.8,
                metric_scores={},
                feedback="反思评估暂时不可用",
                suggestions=["请稍后重试"],
                should_refine=False,
            )

    async def _improve_output(
        self, prompt: str, original_output: str, reflection_result: ReflectionResult
    ) -> str:
        """根据反思结果改进输出"""
        try:
            logger.info("🔧 正在根据反思建议改进AI输出...")

            # 构建改进提示
            improve_prompt = f"""
请根据以下反馈建议,改进原始的AI输出:

## 原始提示
{prompt}

## 原始输出
{original_output}

## 反思反馈
质量评分: {reflection_result.overall_score:.2f}
主要反馈: {reflection_result.feedback}
改进建议:
{chr(10).join([f"- {suggestion}" for suggestion in reflection_result.suggestions])}

## 改进要求
1. 根据反馈建议改进内容
2. 保持核心信息的准确性
3. 提升表达的清晰度和完整性
4. 确保改进后的质量评分达到0.9以上

请直接输出改进后的内容,不要包含其他说明。
"""

            # 调用AI进行改进
            improved_output = await self._call_original_ai(
                improve_prompt,
                {"task": "improve_output", "original_quality": reflection_result.overall_score},
            )

            self.stats["improvements_suggested"] += 1
            logger.info("✅ AI输出改进完成")

            return improved_output

        except Exception as e:
            logger.error(f"❌ 输出改进失败: {e}")
            return original_output

    def _update_stats(
        self, reflection_result: ReflectionResult, processing_time: float
    ) -> Any:
        """更新统计信息"""
        if reflection_result:
            # 更新平均质量评分
            current_total = self.stats["average_quality_score"] * (
                self.stats["reflections_performed"] - 1
            )
            new_average = (current_total + reflection_result.overall_score) / self.stats[
                "reflections_performed"
            ]
            self.stats["average_quality_score"] = round(new_average, 3)

        self.stats["total_reflection_time"] += processing_time

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "total_ai_calls": self.stats["total_calls"],
            "reflections_performed": self.stats["reflections_performed"],
            "improvements_suggested": self.stats["improvements_suggested"],
            "average_quality_score": self.stats["average_quality_score"],
            "average_processing_time": (
                self.stats["total_reflection_time"] / max(1, self.stats["reflections_performed"])
            ),
            "cache_size": len(self.reflection_cache),
            "reflection_enabled": self.config.enable_reflection,
            "auto_improve_enabled": self.config.auto_improve,
            "last_updated": datetime.now().isoformat(),
        }

    def clear_cache(self) -> None:
        """清理缓存"""
        self.reflection_cache.clear()
        logger.info("🗑️ 反思缓存已清理")

    def update_config(self, **kwargs) -> None:
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"⚙️ 配置更新: {key} = {value}")
            else:
                logger.warning(f"⚠️ 未知配置项: {key}")


def with_reflection(ai_processor: Any = None, config: Optional[ReflectionConfig] = None):
    """
    装饰器:为现有AI函数添加反思能力

    使用示例:
    @with_reflection()
    async def my_ai_function(prompt, context=None):
        # 原有的AI处理逻辑
        return "AI响应内容"
    """

    def decorator(func: Callable) -> Any:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 提取prompt和context(假设是前两个参数)
            prompt = args[0] if args else ""
            context = args[1] if len(args) > 1 else None

            # 创建反思包装器
            wrapper_instance = ReflectionIntegrationWrapper(ai_processor, config)

            # 如果有原始函数的AI处理器,使用它
            if not ai_processor and hasattr(func, "__self__"):
                wrapper_instance.ai_processor = func.__self__

            # 调用原始函数获取输出
            original_output = await func(*args, **kwargs)

            # 执行反思
            if wrapper_instance.config.enable_reflection:
                reflection_result = await wrapper_instance._perform_reflection(
                    prompt, original_output, context
                )

                return {
                    "output": original_output,
                    "reflection": reflection_result,
                    "improved": (
                        await wrapper_instance._improve_output(
                            prompt, original_output, reflection_result
                        )
                        if wrapper_instance.config.auto_improve and reflection_result.should_refine
                        else None
                    ),
                }

            return {"output": original_output}

        return wrapper

    return decorator


# 使用示例和测试代码
async def test_reflection_integration():
    """测试反思集成"""
    print("🧪 测试反思引擎集成...")

    # 创建集成包装器(不连接特定AI处理器,使用自动检测)
    wrapper = ReflectionIntegrationWrapper()

    # 测试用例
    test_cases = [
        {
            "prompt": "请分析这个专利的权利要求撰写质量",
            "context": {"task": "patent_analysis", "priority": "high"},
        },
        {"prompt": "如何优化AI系统的响应速度?", "context": {"task": "system_optimization"}},
        {"prompt": "撰写一份技术交底书", "context": {"task": "document_drafting"}},
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 测试用例 {i}:")
        print(f"   提示: {test_case['prompt'][:50]}...")

        result = await wrapper.process_with_reflection(
            prompt=test_case["prompt"], context=test_case["context"]
        )

        # 显示结果
        print(f"   ✅ 处理完成,耗时: {result['processing_time']:.2f}秒")

        if result["reflection_result"]:
            reflection = result["reflection_result"]
            print(f"   🤔 质量评分: {reflection.overall_score:.2f}")
            print(f"   📋 反馈: {reflection.feedback[:50]}...")
            if reflection.should_refine:
                print(f"   🔧 改进建议: {len(reflection.suggestions)}项")

        if result["improved_output"]:
            print("   ✨ 输出已改进")

    # 显示统计信息
    stats = wrapper.get_statistics()
    print("\n📊 测试统计:")
    print(f"   总调用次数: {stats['total_ai_calls']}")
    print(f"   反思执行次数: {stats['reflections_performed']}")
    print(f"   平均质量评分: {stats['average_quality_score']:.2f}")
    print(f"   平均处理时间: {stats['average_processing_time']:.2f}秒")


if __name__ == "__main__":
    asyncio.run(test_reflection_integration())

