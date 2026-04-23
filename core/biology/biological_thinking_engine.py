#!/usr/bin/env python3
from __future__ import annotations
"""
生物学思维引擎
Biological Thinking Engine

整合王立铭《生命是什么》的核心思想,建立AI系统的生物学思维:
1. 系统演化 - 类似生物演化的智能体进化
2. 负熵优化 - 从混乱到有序的信息处理
3. 赫布学习 - 常用路径的神经强化
4. 环境感知 - 用户需求作为选择压力

作者: 小诺·双鱼公主
创建时间: 2025-12-24
版本: v0.1.2 "晨星初现"
"""

import json
import logging

# 导入子模块
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.biology.environment_sensor import PressureType, get_environment_sensor
from core.biology.evolutionary_memory_system import (
    EvolutionaryPressure,
    MutationType,
    get_evolutionary_memory,
)
from core.biology.hebbian_optimizer import get_hebbian_optimizer
from core.biology.negentropy_optimizer import NegentropyMetric, get_negentropy_optimizer

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


@dataclass
class BiologicalMetrics:
    """生物学指标"""

    evolutionary_fitness: float  # 演化适应度
    negentropy_score: float  # 负熵分数
    learning_efficiency: float  # 学习效率
    adaptation_success: float  # 适应成功率
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class BiologicalThinkingEngine:
    """
    生物学思维引擎

    核心理念:
    将AI系统视为一个"生命体",它能够:
    - 感知环境(用户需求)
    - 演化适应(系统优化)
    - 学习记忆(赫布强化)
    - 创造有序(负熵优化)
    """

    def __init__(self):
        """初始化生物学思维引擎"""
        self.name = "生物学思维引擎"
        self.version = "v0.1.2"

        # 初始化各子系统
        self.evolutionary_memory = get_evolutionary_memory()
        self.negentropy_optimizer = get_negentropy_optimizer()
        self.hebbian_optimizer = get_hebbian_optimizer()
        self.environment_sensor = get_environment_sensor()

        # 性能指标历史
        self.metrics_history: list[BiologicalMetrics] = []

        logger.info(f"🧬 {self.name} ({self.version}) 初始化完成")
        logger.info("   ✅ 系统演化记忆: 就绪")
        logger.info("   ✅ 负熵优化: 就绪")
        logger.info("   ✅ 赫布学习: 就绪")
        logger.info("   ✅ 环境感知: 就绪")

    async def process_user_interaction(
        self, user_input: str, system_response: str, context: Optional[dict[str, Any]] = None
    ) -> BiologicalMetrics:
        """
        处理用户交互(生物学思维模式)

        Args:
            user_input: 用户输入
            system_response: 系统响应
            context: 上下文

        Returns:
            生物学指标
        """
        context = context or {}

        # 1. 环境感知:检测用户需求压力
        pressure_id = self.environment_sensor.detect_pressure(
            pressure_type=PressureType.USER_REQUEST,
            description=user_input[:50],
            urgency=self.environment_sensor.evaluate_urgency(PressureType.USER_REQUEST, context),
            source="用户输入",
            metadata={"input_length": len(user_input)},
        )

        # 2. 赫布学习:记录协同激活
        involved_agents = context.get("agents", ["小诺"])
        self.hebbian_optimizer.record_activation(
            nodes=involved_agents, context={"interaction": user_input[:30]}
        )

        # 3. 负熵优化:测量信息熵减
        negentropy_score = self.negentropy_optimizer.measure_negentropy(
            input_data=list(user_input),  # 输入(相对混乱)
            output_data=list(system_response),  # 输出(相对有序)
            metric_type=NegentropyMetric.INFORMATION_ENTROPY,
        )

        # 4. 演化记忆:记录基因突变
        if context.get("preference_detected"):
            self.evolutionary_memory.record_mutation(
                agent_id="apps/apps/xiaonuo",
                mutation_type=MutationType.PREFERENCE_CHANGE,
                pressure=EvolutionaryPressure.USER_FEEDBACK,
                trait_name="用户偏好",
                trait_value=context["preference_detected"],
                description=f"检测到用户偏好: {context['preference_detected']}",
            )

        # 5. 计算综合指标
        metrics = BiologicalMetrics(
            evolutionary_fitness=self._calculate_fitness(context),
            negentropy_score=negentropy_score.negentropy,
            learning_efficiency=negentropy_score.efficiency,
            adaptation_success=self._calculate_adaptation_success(context),
        )

        self.metrics_history.append(metrics)

        # 6. 清理已解决的压力
        self.environment_sensor.resolve_pressure(pressure_id)

        return metrics

    async def optimize_system(self) -> dict[str, Any]:
        """
        系统自优化(生物学驱动)

        Returns:
            优化结果
        """
        results = {}

        # 1. 赫布优化:衰减弱连接
        self.hebbian_optimizer.decay_connections()
        results["hebbian_optimization"] = "弱连接已衰减"

        # 2. 负熵优化:找出最优路径
        strongest = self.hebbian_optimizer.get_strongest_connections(top_n=5)
        results["strongest_paths"] = [
            f"{c.source} -> {c.target} (强度: {c.strength:.2f})" for c in strongest
        ]

        # 3. 演化优化:自然选择
        selected = self.evolutionary_memory.natural_selection(
            pressure=EvolutionaryPressure.USER_FEEDBACK,
            environment_context={"user_satisfaction": 0.8},
        )
        results["evolutionary_selection"] = f"保留 {len(selected)} 个高适应度基因"

        # 4. 环境预测
        predictions = self.environment_sensor.predict_pressure()
        results["predictions"] = predictions

        return results

    def _calculate_fitness(self, context: dict[str, Any]) -> float:
        """计算演化适应度"""
        fitness = 0.5

        # 用户满意度提升适应度
        satisfaction = context.get("user_satisfaction", 0.5)
        fitness += (satisfaction - 0.5) * 0.3

        # 响应时间影响适应度
        response_time = context.get("response_time", 1.0)
        if response_time < 2:
            fitness += 0.1
        elif response_time > 5:
            fitness -= 0.1

        return max(0.0, min(1.0, fitness))

    def _calculate_adaptation_success(self, context: dict[str, Any]) -> float:
        """计算适应成功率"""
        # 基于历史适应行动的成功率
        adaptations = self.environment_sensor.adaptation_history

        if not adaptations:
            return 0.5

        # 统计成功执行的行动
        successful = sum(1 for a in adaptations if a.executed)

        return successful / len(adaptations)

    def get_system_status(self) -> dict[str, Any]:
        """获取系统状态"""
        return {
            "engine": {"name": self.name, "version": self.version},
            "evolutionary_memory": self.evolutionary_memory.get_system_status(),
            "negentropy_optimizer": self.negentropy_optimizer.get_optimization_summary(),
            "hebbian_optimizer": self.hebbian_optimizer.get_network_stats(),
            "environment_sensor": self.environment_sensor.get_environment_status(),
            "latest_metrics": (
                {
                    "fitness": (
                        self.metrics_history[-1].evolutionary_fitness if self.metrics_history else 0
                    ),
                    "negentropy": (
                        self.metrics_history[-1].negentropy_score if self.metrics_history else 0
                    ),
                    "efficiency": (
                        self.metrics_history[-1].learning_efficiency if self.metrics_history else 0
                    ),
                }
                if self.metrics_history
                else None
            ),
        }


# 全局单例
_biological_engine_instance = None


def get_biological_thinking_engine() -> BiologicalThinkingEngine:
    """获取生物学思维引擎单例"""
    global _biological_engine_instance
    if _biological_engine_instance is None:
        _biological_engine_instance = BiologicalThinkingEngine()
    return _biological_engine_instance


# 测试代码
async def main():
    """测试生物学思维引擎"""

    print("\n" + "=" * 60)
    print("🧬 生物学思维引擎测试")
    print("=" * 60 + "\n")

    engine = get_biological_thinking_engine()

    # 测试1:处理用户交互
    print("📝 测试1: 处理用户交互")
    metrics = await engine.process_user_interaction(
        user_input="我喜欢详细的分析报告",
        system_response="好的爸爸,小诺会为您提供详细的分析报告。",
        context={
            "agents": ["小诺", "记忆系统"],
            "preference_detected": "喜欢详细报告",
            "user_satisfaction": 0.9,
            "response_time": 1.2,
        },
    )

    print(f"演化适应度: {metrics.evolutionary_fitness:.2f}")
    print(f"负熵分数: {metrics.negentropy_score:.2f}")
    print(f"学习效率: {metrics.learning_efficiency:.1%}")
    print(f"适应成功率: {metrics.adaptation_success:.1%}")
    print()

    # 测试2:系统自优化
    print("📝 测试2: 系统自优化")
    optimization_results = await engine.optimize_system()
    print(json.dumps(optimization_results, ensure_ascii=False, indent=2))
    print()

    # 测试3:系统状态
    print("📝 测试3: 系统状态")
    status = engine.get_system_status()
    print(json.dumps(status, ensure_ascii=False, indent=2))

    print("\n✅ 测试完成!")


# 入口点: @async_main装饰器已添加到main函数
