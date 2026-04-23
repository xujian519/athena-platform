#!/usr/bin/env python3
from __future__ import annotations
"""
突变引擎
Mutation Engine

实现各种类型的系统突变:
- 参数突变: 微调系统参数
- 配置突变: 更新系统配置
- 结构突变: 调整系统结构
- 策略突变: 改变运行策略

作者: Athena平台团队
创建时间: 2026-02-06
版本: v1.0.0
"""

import asyncio
import json
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from .types import EvolutionStrategy, Mutation, MutationType, PerformanceMetrics

logger = logging.getLogger(__name__)


class MutationIntensity(Enum):
    """突变强度"""
    MINIMAL = "minimal"      # 最小突变
    MODERATE = "moderate"    # 适度突变
    AGGRESSIVE = "aggressive"  # 激进突变


@dataclass
class MutationResult:
    """突变结果"""
    success: bool
    mutation: Mutation
    actual_improvement: float = 0.0
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class MutationEngine:
    """
    突变引擎

    负责生成和执行各种类型的系统突变
    """

    def __init__(self):
        """初始化突变引擎"""
        self.mutation_history: list[MutationResult] = []
        self._config_manager = None
        logger.info("✅ 突变引擎初始化完成")

    async def initialize(self):
        """初始化引擎"""
        try:
            from core.config.unified_config_manager import get_config_manager
            self._config_manager = get_config_manager()
            logger.info("✅ 配置管理器已连接")
        except ImportError:
            logger.warning("⚠️ 配置管理器不可用")

    async def generate_mutation(
        self,
        mutation_type: MutationType,
        current_metrics: PerformanceMetrics | None = None,
        strategy: EvolutionStrategy = EvolutionStrategy.GRADIENT,
        intensity: MutationIntensity = MutationIntensity.MODERATE
    ) -> Mutation:
        """
        生成突变

        Args:
            mutation_type: 突变类型
            current_metrics: 当前性能指标
            strategy: 进化策略
            intensity: 突变强度

        Returns:
            Mutation: 突变定义
        """
        logger.info(f"🧬 生成{mutation_type.value}突变...")

        if mutation_type == MutationType.PARAMETER_TUNING:
            return await self._generate_parameter_mutation(current_metrics, intensity)
        elif mutation_type == MutationType.CONFIG_UPDATE:
            return await self._generate_config_mutation(current_metrics, intensity)
        elif mutation_type == MutationType.MODEL_SELECTION:
            return await self._generate_model_selection_mutation(current_metrics, intensity)
        elif mutation_type == MutationType.STRATEGY_CHANGE:
            return await self._generate_strategy_mutation(current_metrics, intensity)
        else:
            # 默认参数突变
            return await self._generate_parameter_mutation(current_metrics, intensity)

    async def _generate_parameter_mutation(
        self,
        metrics: PerformanceMetrics | None,
        intensity: MutationIntensity
    ) -> Mutation:
        """生成参数突变"""
        # 常见的可调参数
        param_options = {
            "temperature": {
                "range": (0.1, 1.0),
                "current": 0.7
            },
            "top_p": {
                "range": (0.5, 1.0),
                "current": 0.9
            },
            "max_tokens": {
                "range": (512, 4096),
                "current": 2000
            },
            "chunk_size": {
                "range": (100, 1000),
                "current": 500
            },
            "cache_size": {
                "range": (100, 10000),
                "current": 1000
            }
        }

        # 根据强度选择调整幅度
        intensity_factor = {
            MutationIntensity.MINIMAL: 0.05,
            MutationIntensity.MODERATE: 0.15,
            MutationIntensity.AGGRESSIVE: 0.30
        }[intensity]

        # 选择参数
        param_name = random.choice(list(param_options.keys()))
        param_config = param_options[param_name]

        # 计算新值
        min_val, max_val = param_config["range"]
        current_val = param_config["current"]
        range_size = max_val - min_val

        # 根据性能指标决定调整方向
        if metrics and metrics.accuracy < 0.7:
            # 性能较低，尝试降低温度（更确定性）
            if param_name == "temperature":
                new_val = max(min_val, current_val - range_size * intensity_factor)
            else:
                change = (random.random() - 0.5) * 2 * range_size * intensity_factor
                new_val = max(min_val, min(max_val, current_val + change))
        else:
            # 性能较好，可以探索
            change = (random.random() - 0.5) * 2 * range_size * intensity_factor
            new_val = max(min_val, min(max_val, current_val + change))

        # 预期改进
        expected_improvement = random.uniform(0.01, 0.1) * intensity_factor

        return Mutation(
            mutation_type=MutationType.PARAMETER_TUNING,
            target=param_name,
            before_value=current_val,
            after_value=new_val,
            expected_improvement=expected_improvement,
            confidence=0.7
        )

    async def _generate_config_mutation(
        self,
        metrics: PerformanceMetrics | None,
        intensity: MutationIntensity
    ) -> Mutation:
        """生成配置突变"""
        config_options = {
            "enable_cache": True,
            "cache_ttl": 3600,
            "log_level": "INFO",
            "max_concurrent_requests": 10,
            "request_timeout": 30
        }

        option_name = random.choice(list(config_options.keys()))
        current_value = config_options[option_name]

        # 根据类型生成新值
        if isinstance(current_value, bool):
            new_value = not current_value
        elif isinstance(current_value, int):
            factor = {MutationIntensity.MINIMAL: 1.1, MutationIntensity.MODERATE: 1.3, MutationIntensity.AGGRESSIVE: 1.5}[intensity]
            if metrics and metrics.efficiency < 0.7:
                new_value = int(current_value * factor)
            else:
                new_value = int(current_value * (2 - factor))
        elif isinstance(current_value, str):
            levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
            current_idx = levels.index(current_value) if current_value in levels else 1
            shift = 1 if intensity != MutationIntensity.MINIMAL else 0
            new_idx = max(0, min(len(levels) - 1, current_idx + shift))
            new_value = levels[new_idx]
        else:
            new_value = current_value

        return Mutation(
            mutation_type=MutationType.CONFIG_UPDATE,
            target=f"config.{option_name}",
            before_value=current_value,
            after_value=new_value,
            expected_improvement=0.05,
            confidence=0.6
        )

    async def _generate_model_selection_mutation(
        self,
        metrics: PerformanceMetrics | None,
        intensity: MutationIntensity
    ) -> Mutation:
        """生成模型选择突变"""
        # 可用模型列表
        available_models = [
            "qwen:7b",
            "qwen2.5-14b-xiaonuo",
            "qwen2.5-14b-local",
            "glm-4-flash",
            "deepseek-chat"
        ]

        current_model = "qwen:7b"
        new_model = random.choice(available_models)

        return Mutation(
            mutation_type=MutationType.MODEL_SELECTION,
            target="model",
            before_value=current_model,
            after_value=new_model,
            expected_improvement=0.1,
            confidence=0.5
        )

    async def _generate_strategy_mutation(
        self,
        metrics: PerformanceMetrics | None,
        intensity: MutationIntensity
    ) -> Mutation:
        """生成策略突变"""
        strategies = [
            "accuracy_first",    # 准确性优先
            "efficiency_first",  # 效率优先
            "cost_first",        # 成本优先
            "balanced"           # 平衡
        ]

        current_strategy = "balanced"
        new_strategy = random.choice(strategies)

        return Mutation(
            mutation_type=MutationType.STRATEGY_CHANGE,
            target="optimization_strategy",
            before_value=current_strategy,
            after_value=new_strategy,
            expected_improvement=0.08,
            confidence=0.6
        )

    async def apply_mutation(self, mutation: Mutation) -> MutationResult:
        """
        应用突变

        Args:
            mutation: 突变定义

        Returns:
            MutationResult: 突变结果
        """
        logger.info(f"🔧 应用突变: {mutation.target}")

        try:
            if mutation.mutation_type == MutationType.PARAMETER_TUNING:
                success = await self._apply_parameter_mutation(mutation)
            elif mutation.mutation_type == MutationType.CONFIG_UPDATE:
                success = await self._apply_config_mutation(mutation)
            elif mutation.mutation_type == MutationType.MODEL_SELECTION:
                success = await self._apply_model_mutation(mutation)
            elif mutation.mutation_type == MutationType.STRATEGY_CHANGE:
                success = await self._apply_strategy_mutation(mutation)
            else:
                success = False

            if success:
                result = MutationResult(
                    success=True,
                    mutation=mutation,
                    actual_improvement=mutation.expected_improvement
                )
                logger.info("✅ 突变应用成功")
            else:
                result = MutationResult(
                    success=False,
                    mutation=mutation,
                    error="应用失败"
                )
                logger.warning("⚠️ 突变应用失败")

            self.mutation_history.append(result)
            return result

        except Exception as e:
            logger.error(f"❌ 应用突变异常: {e}")
            return MutationResult(
                success=False,
                mutation=mutation,
                error=str(e)
            )

    async def _apply_parameter_mutation(self, mutation: Mutation) -> bool:
        """应用参数突变"""
        try:
            if self._config_manager:
                await self._config_manager.update_parameter(
                    mutation.target,
                    mutation.after_value
                )
                return True
            return False
        except Exception as e:
            logger.error(f"参数更新失败: {e}")
            return False

    async def _apply_config_mutation(self, mutation: Mutation) -> bool:
        """应用配置突变"""
        try:
            if self._config_manager:
                await self._config_manager.update_config(
                    mutation.target,
                    mutation.after_value
                )
                return True
            return False
        except Exception as e:
            logger.error(f"配置更新失败: {e}")
            return False

    async def _apply_model_mutation(self, mutation: Mutation) -> bool:
        """应用模型选择突变"""
        try:
            # 更新模型配置
            model_config_path = Path("/Users/xujian/Athena工作平台/config/llm_config.json")
            if model_config_path.exists():
                with open(model_config_path, 'r+', encoding='utf-8') as f:
                    config = json.load(f)
                    config["model"] = mutation.after_value
                    f.seek(0)
                    json.dump(config, f, indent=2, ensure_ascii=False)
                    f.truncate()
                return True
            return False
        except Exception as e:
            logger.error(f"模型更新失败: {e}")
            return False

    async def _apply_strategy_mutation(self, mutation: Mutation) -> bool:
        """应用策略突变"""
        try:
            strategy_config_path = Path("/Users/xujian/Athena工作平台/config/optimization_strategy.json")
            strategy_config_path.parent.mkdir(parents=True, exist_ok=True)

            strategy_config = {}
            if strategy_config_path.exists():
                with open(strategy_config_path, encoding='utf-8') as f:
                    strategy_config = json.load(f)

            strategy_config["current_strategy"] = mutation.after_value

            with open(strategy_config_path, 'w', encoding='utf-8') as f:
                json.dump(strategy_config, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            logger.error(f"策略更新失败: {e}")
            return False

    async def batch_mutate(
        self,
        count: int = 3,
        mutation_types: list[MutationType] | None = None,
        metrics: PerformanceMetrics | None = None
    ) -> list[MutationResult]:
        """
        批量生成和应用突变

        Args:
            count: 突变数量
            mutation_types: 突变类型列表
            metrics: 当前性能指标

        Returns:
            list[MutationResult]: 突变结果列表
        """
        logger.info(f"🧬 执行批量突变 ({count}个)...")

        if mutation_types is None:
            mutation_types = [
                MutationType.PARAMETER_TUNING,
                MutationType.CONFIG_UPDATE
            ]

        results = []
        for _i in range(count):
            # 选择突变类型
            mutation_type = random.choice(mutation_types)

            # 生成突变
            mutation = await self.generate_mutation(
                mutation_type,
                metrics,
                intensity=MutationIntensity.MODERATE
            )

            # 应用突变
            result = await self.apply_mutation(mutation)
            results.append(result)

            # 如果失败，尝试下一个
            if not result.success:
                continue

        success_count = sum(1 for r in results if r.success)
        logger.info(f"✅ 批量突变完成: {success_count}/{count} 成功")

        return results

    def get_mutation_stats(self) -> dict[str, Any]:
        """获取突变统计"""
        total = len(self.mutation_history)
        success = sum(1 for r in self.mutation_history if r.success)

        return {
            "total_mutations": total,
            "successful_mutations": success,
            "failed_mutations": total - success,
            "success_rate": success / total if total > 0 else 0,
            "total_improvement": sum(r.actual_improvement for r in self.mutation_history)
        }


# 全局实例
_mutation_engine: MutationEngine | None = None


def get_mutation_engine() -> MutationEngine:
    """获取突变引擎实例"""
    global _mutation_engine
    if _mutation_engine is None:
        _mutation_engine = MutationEngine()
    return _mutation_engine


if __name__ == "__main__":
    # 测试突变引擎
    async def test():
        print("🧪 测试突变引擎")
        print("=" * 60)

        engine = get_mutation_engine()
        await engine.initialize()

        # 测试生成突变
        print("\n📝 生成参数突变...")
        mutation = await engine.generate_mutation(
            MutationType.PARAMETER_TUNING,
            intensity=MutationIntensity.MODERATE
        )
        print(f"目标: {mutation.target}")
        print(f"变更: {mutation.before_value} → {mutation.after_value}")
        print(f"预期改进: {mutation.expected_improvement:.1%}")

        # 测试批量突变
        print("\n🧬 执行批量突变...")
        await engine.batch_mutate(count=3)

        stats = engine.get_mutation_stats()
        print("\n📊 统计:")
        print(f"  总突变数: {stats['total_mutations']}")
        print(f"  成功率: {stats['success_rate']:.1%}")

    asyncio.run(test())
