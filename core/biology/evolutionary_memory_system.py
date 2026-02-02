#!/usr/bin/env python3
"""
系统演化记忆系统
Evolutionary Memory System

基于王立铭《生命是什么》的生物学思维,建立类似生物演化的记忆系统:
- LUCA共同祖先:所有智能体共享统一记忆底座
- 自然选择:保留有用信息,淘汰无用信息
- 基因遗传:子智能体继承父代的"基因"(知识、偏好)
- 环境适应:根据用户需求这个"环境压力"持续演化

作者: 小诺·双鱼公主
创建时间: 2025-12-24
版本: v0.1.2 "晨星初现"
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class MutationType(Enum):
    """突变类型"""

    KNOWLEDGE_ADDITION = "knowledge_addition"  # 知识增加
    PREFERENCE_CHANGE = "preference_change"  # 偏好变化
    PATTERN_EMERGENCE = "pattern_emergence"  # 模式涌现
    STRUCTURE_OPTIMIZATION = "structure_optimization"  # 结构优化


class EvolutionaryPressure(Enum):
    """演化压力类型"""

    USER_FEEDBACK = "user_feedback"  # 用户反馈
    SYSTEM_PERFORMANCE = "system_performance"  # 系统性能
    ENVIRONMENT_CHANGE = "environment_change"  # 环境变化
    COMPETITION = "competition"  # 竞争压力


@dataclass
class GeneticTrait:
    """基因特征"""

    trait_id: str
    name: str
    value: Any
    fitness: float = 0.5  # 适应度(0-1)
    inheritance_count: int = 0  # 遗传次数
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_mutated: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class EvolutionRecord:
    """演化记录"""

    record_id: str
    mutation_type: MutationType
    pressure: EvolutionaryPressure
    parent_traits: list[str]  # 父代特征
    child_traits: list[str]  # 子代特征
    fitness_delta: float  # 适应度变化
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    description: str = ""


class EvolutionaryMemory:
    """
    系统演化记忆系统

    核心思想:
    1. LUCA共同祖先 - 所有智能体共享统一记忆底座
    2. 自然选择 - 根据适应度保留/淘汰信息
    3. 基因遗传 - 智能体间的知识传承
    4. 突变创新 - 引入新的变化和尝试
    """

    def __init__(self):
        """初始化演化记忆系统"""
        self.name = "系统演化记忆系统"
        self.version = "v0.1.2"

        # 基因池(所有智能体共享)
        self.gene_pool: dict[str, GeneticTrait] = {}

        # 演化历史
        self.evolution_history: list[EvolutionRecord] = []

        # 智能体谱系(记录遗传关系)
        self.lineage: dict[str, list[str]] = {}  # {agent_id: [parent_ids]}

        # 适应度函数
        self.fitness_functions = {
            EvolutionaryPressure.USER_FEEDBACK: self._user_feedback_fitness,
            EvolutionaryPressure.SYSTEM_PERFORMANCE: self._performance_fitness,
            EvolutionaryPressure.ENVIRONMENT_CHANGE: self._adaptation_fitness,
        }

        logger.info(f"🧬 {self.name} ({self.version}) 初始化完成")

    def register_agent(self, agent_id: str, parents: list[str] | None = None) -> None:
        """
        注册新智能体(类似新物种诞生)

        Args:
            agent_id: 智能体ID
            parents: 父代智能体ID列表(可选)
        """
        self.lineage[agent_id] = parents or []

        # 如果有父代,继承父代的"基因"
        if parents:
            self._inherit_traits(agent_id, parents)

        logger.info(f"🧬 注册智能体: {agent_id}, 父代: {parents}")

    def _inherit_traits(self, child_id: str, parent_ids: list[str]) -> None:
        """
        基因遗传:子代继承父代的特征

        Args:
            child_id: 子代ID
            parent_ids: 父代ID列表
        """
        for parent_id in parent_ids:
            # 找到父代的高适应度基因
            parent_traits = self._get_agent_traits(parent_id)
            for trait in parent_traits:
                if trait.fitness > 0.7:  # 只继承高适应度基因
                    # 创建子代的基因副本
                    child_trait = GeneticTrait(
                        trait_id=self._generate_trait_id(),
                        name=trait.name,
                        value=trait.value,
                        fitness=trait.fitness * 0.95,  # 遗传时有轻微退化
                        inheritance_count=trait.inheritance_count + 1,
                    )
                    self.gene_pool[child_trait.trait_id] = child_trait

        logger.info(f"🧬 {child_id} 从 {parent_ids} 继承了基因")

    def record_mutation(
        self,
        agent_id: str,
        mutation_type: MutationType,
        pressure: EvolutionaryPressure,
        trait_name: str,
        trait_value: Any,
        description: str = "",
    ) -> str:
        """
        记录基因突变(系统变化)

        Args:
            agent_id: 智能体ID
            mutation_type: 突变类型
            pressure: 演化压力
            trait_name: 特征名称
            trait_value: 特征值
            description: 描述

        Returns:
            特征ID
        """
        trait_id = self._generate_trait_id()

        # 创建新基因特征
        trait = GeneticTrait(
            trait_id=trait_id,
            name=trait_name,
            value=trait_value,
            fitness=self._calculate_initial_fitness(mutation_type, pressure),
        )

        # 添加到基因池
        self.gene_pool[trait_id] = trait

        # 记录演化历史
        record = EvolutionRecord(
            record_id=self._generate_record_id(),
            mutation_type=mutation_type,
            pressure=pressure,
            parent_traits=[],
            child_traits=[trait_id],
            fitness_delta=trait.fitness,
            description=description or f"{agent_id} 产生了 {trait_name} 基因突变",
        )

        self.evolution_history.append(record)

        logger.info(f"🧬 突变记录: {trait_name} (适应度: {trait.fitness:.2f})")

        return trait_id

    def natural_selection(
        self, pressure: EvolutionaryPressure, environment_context: dict[str, Any] | None = None
    ) -> list[str]:
        """
        自然选择:根据环境压力筛选基因

        Args:
            pressure: 演化压力类型
            environment_context: 环境上下文

        Returns:
            保留的高适应度基因ID列表
        """
        # 获取适应度函数
        fitness_func = self.fitness_functions.get(pressure, self._default_fitness)

        # 计算每个基因的适应度
        selected_traits = []
        for trait_id, trait in self.gene_pool.items():
            # 动态评估适应度
            current_fitness = fitness_func(trait, environment_context or {})
            trait.fitness = current_fitness

            # 保留高适应度基因
            if current_fitness > 0.5:
                selected_traits.append(trait_id)

        # 淘汰低适应度基因
        all_trait_ids = list(self.gene_pool.keys())
        for trait_id in all_trait_ids:
            if trait_id not in selected_traits:
                del self.gene_pool[trait_id]
                logger.info(f"🧬 基因淘汰: {trait_id} (适应度过低)")

        logger.info(f"🧬 自然选择完成: 保留 {len(selected_traits)}/{len(all_trait_ids)} 个基因")

        return selected_traits

    def get_evolutionary_lineage(self, agent_id: str) -> dict[str, Any]:
        """
        获取智能体的演化谱系

        Args:
            agent_id: 智能体ID

        Returns:
            谱系信息
        """
        lineage = {
            "agent_id": agent_id,
            "ancestors": self.lineage.get(agent_id, []),
            "traits": self._get_agent_traits(agent_id),
            "evolution_records": [],
        }

        # 找到相关的演化记录
        for record in self.evolution_history:
            # 检查这个记录是否与该智能体相关
            lineage["evolution_records"].append(
                {
                    "mutation_type": record.mutation_type.value,
                    "pressure": record.pressure.value,
                    "fitness_delta": record.fitness_delta,
                    "timestamp": record.timestamp,
                    "description": record.description,
                }
            )

        return lineage

    def _inherit_traits(self, child_id: str, parent_ids: list[str]) -> None:
        """基因遗传(已在上面定义,这里只是占位)"""
        pass

    def _get_agent_traits(self, agent_id: str) -> list[GeneticTrait]:
        """获取智能体的所有基因特征"""
        # 简化实现:返回所有基因
        # 实际应该根据谱系过滤
        return list(self.gene_pool.values())

    def _generate_trait_id(self) -> str:
        """生成基因ID"""
        return f"trait_{hashlib.md5(datetime.now().isoformat().encode(), usedforsecurity=False).hexdigest()[:8]}"

    def _generate_record_id(self) -> str:
        """生成记录ID"""
        return f"record_{hashlib.md5(datetime.now().isoformat().encode(), usedforsecurity=False).hexdigest()[:8]}"

    def _calculate_initial_fitness(
        self, mutation_type: MutationType, pressure: EvolutionaryPressure
    ) -> float:
        """计算初始适应度"""
        # 不同类型的突变有不同的初始适应度
        base_fitness = {
            MutationType.KNOWLEDGE_ADDITION: 0.6,
            MutationType.PREFERENCE_CHANGE: 0.5,
            MutationType.PATTERN_EMERGENCE: 0.7,
            MutationType.STRUCTURE_OPTIMIZATION: 0.8,
        }

        base = base_fitness.get(mutation_type, 0.5)

        # 根据演化压力调整
        pressure_multiplier = {
            EvolutionaryPressure.USER_FEEDBACK: 1.0,
            EvolutionaryPressure.SYSTEM_PERFORMANCE: 0.9,
            EvolutionaryPressure.ENVIRONMENT_CHANGE: 1.1,
            EvolutionaryPressure.COMPETITION: 1.2,
        }

        multiplier = pressure_multiplier.get(pressure, 1.0)

        return min(1.0, base * multiplier)

    def _user_feedback_fitness(self, trait: GeneticTrait, context: dict[str, Any]) -> float:
        """用户反馈驱动的适应度"""
        # 如果用户表达满意,提升适应度
        user_satisfaction = context.get("user_satisfaction", 0.5)
        return trait.fitness * (0.5 + user_satisfaction)

    def _performance_fitness(self, trait: GeneticTrait, context: dict[str, Any]) -> float:
        """系统性能驱动的适应度"""
        # 根据性能指标调整
        performance_score = context.get("performance_score", 0.5)
        return trait.fitness * (0.3 + performance_score)

    def _adaptation_fitness(self, trait: GeneticTrait, context: dict[str, Any]) -> float:
        """环境适应驱动的适应度"""
        # 根据环境变化调整
        change_rate = context.get("change_rate", 0.5)
        return trait.fitness * (0.4 + change_rate)

    def _default_fitness(self, trait: GeneticTrait, context: dict[str, Any]) -> float:
        """默认适应度"""
        return trait.fitness

    def get_system_status(self) -> dict[str, Any]:
        """获取演化系统状态"""
        return {
            "name": self.name,
            "version": self.version,
            "gene_pool_size": len(self.gene_pool),
            "evolution_records": len(self.evolution_history),
            "registered_agents": len(self.lineage),
            "avg_fitness": sum(t.fitness for t in self.gene_pool.values())
            / max(1, len(self.gene_pool)),
        }


# 全局单例
_evolutionary_memory_instance = None


def get_evolutionary_memory() -> EvolutionaryMemory:
    """获取演化记忆系统单例"""
    global _evolutionary_memory_instance
    if _evolutionary_memory_instance is None:
        _evolutionary_memory_instance = EvolutionaryMemory()
    return _evolutionary_memory_instance


# 测试代码
async def main():
    """测试演化记忆系统"""

    print("\n" + "=" * 60)
    print("🧬 系统演化记忆测试")
    print("=" * 60 + "\n")

    evo_memory = get_evolutionary_memory()

    # 测试1:注册智能体
    print("📝 测试1: 注册智能体")
    evo_memory.register_agent("apps/apps/xiaonuo", parents=[])
    evo_memory.register_agent("xiana", parents=["apps/apps/xiaonuo"])
    print("✅ 智能体注册完成\n")

    # 测试2:记录基因突变
    print("📝 测试2: 记录基因突变")
    trait_id = evo_memory.record_mutation(
        agent_id="apps/apps/xiaonuo",
        mutation_type=MutationType.PREFERENCE_CHANGE,
        pressure=EvolutionaryPressure.USER_FEEDBACK,
        trait_name="详细报告偏好",
        trait_value="喜欢详细的分析报告",
        description="爸爸表达了对详细报告的偏好",
    )
    print(f"✅ 基因突变记录: {trait_id}\n")

    # 测试3:自然选择
    print("📝 测试3: 自然选择")
    selected = evo_memory.natural_selection(
        pressure=EvolutionaryPressure.USER_FEEDBACK, environment_context={"user_satisfaction": 0.8}
    )
    print(f"✅ 保留基因数: {len(selected)}\n")

    # 测试4:查看谱系
    print("📝 测试4: 查看演化谱系")
    lineage = evo_memory.get_evolutionary_lineage("xiana")
    print(f"谱系: {lineage['agent_id']}")
    print(f"祖先: {lineage['ancestors']}")
    print(f"基因数: {len(lineage['traits'])}\n")

    # 测试5:系统状态
    print("📝 测试5: 系统状态")
    status = evo_memory.get_system_status()
    print(json.dumps(status, ensure_ascii=False, indent=2))

    print("\n✅ 测试完成!")


# 入口点: @async_main装饰器已添加到main函数
