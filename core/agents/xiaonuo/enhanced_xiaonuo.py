#!/usr/bin/env python3
from __future__ import annotations
"""
小诺增强智能体 - Enhanced Xiaonuo
整合改进后的学习和反思能力

核心改进:
1. 记忆整合系统 - 短期记忆转化为长期知识
2. 元学习引擎 - 自动优化学习策略
3. v5.0反思引擎 - 完整反思循环
4. 自适应改进 - 自动应用反思建议

作者: Athena平台团队
版本: v2.0.0 "智慧进化"
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from core.async_main import async_main
from core.logging_config import setup_logging

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入基础智能体
from core.agents.xiaonuo.unified_xiaonuo_agent import XiaonuoUnifiedAgent

# 导入记忆系统
try:
    from core.memory.unified_agent_memory_system import (
        MemoryTier,
        MemoryType,
        UnifiedAgentMemorySystem,
    )
except ImportError:
    # 如果导入失败,使用备用导入
    UnifiedAgentMemorySystem = None

# 导入改进模块
from core.intelligence.reflection_engine_v5 import (
    ActionStatus,
    ReflectionEngineV5,
    ReflectionType,
    ThoughtStep,
)
from core.learning.enhanced_meta_learning import (
    EnhancedMetaLearningEngine,
    MetaLearningTask,
)
from core.learning.memory_consolidation_system import MemoryConsolidationSystem

logger = setup_logging()


class EnhancedXiaonuo(XiaonuoUnifiedAgent):
    """
    增强版小诺智能体

    继承原有能力,新增:
    - 记忆整合能力
    - 元学习能力
    - 高级反思能力
    """

    def __init__(self):
        super().__init__()

        # 升级版本信息
        self.version = "v2.0.0_enhanced"
        self.agent_id = "xiaonuo_enhanced"

        # 记忆整合系统
        self.memory_consolidation = MemoryConsolidationSystem(agent_id=self.agent_id)

        # 元学习引擎
        self.meta_learning = EnhancedMetaLearningEngine(agent_id=self.agent_id)

        # v5.0反思引擎
        self.reflection_engine_v5 = ReflectionEngineV5(agent_id=self.agent_id)

        # 增强能力列表
        self.enhanced_capabilities = [
            "记忆整合",
            "元学习优化",
            "因果推理",
            "自我反思循环",
            "自适应改进",
        ]

        # 性能追踪
        self.performance_tracker = {
            "interactions": 0,
            "learning_cycles": 0,
            "reflections_performed": 0,
            "improvements_applied": 0,
            "memory_consolidations": 0,
        }

        # 配置
        self.config = {
            "enable_reflection": True,
            "enable_learning": True,
            "enable_consolidation": True,
            "consolidation_interval_hours": 6,
            "reflection_threshold": 0.8,
            "learning_sample_size": 5,
        }

        logger.info("🚀 小诺增强智能体v2.0初始化完成")

    async def initialize(self, memory_system=None):
        """初始化增强小诺"""
        # 调用父类初始化
        try:
            await super().initialize(memory_system)
        except Exception as e:
            logger.warning(f"父类初始化失败: {e}")

        # 初始化记忆整合系统(连接到记忆系统)
        self.memory_consolidation.memory_system = memory_system

        # 执行初始记忆整合
        if self.config["enable_consolidation"]:
            try:
                await self._perform_initial_consolidation()
            except Exception as e:
                logger.warning(f"初始记忆整合失败: {e}")

        logger.info("✅ 增强小诺初始化完成,新增记忆整合和元学习能力")

    async def process_input(
        self,
        user_input: str,
        enable_reflection: bool = True,
        enable_learning: bool = True,
        **kwargs,
    ) -> str:
        """
        处理用户输入(增强版)

        Args:
            user_input: 用户输入
            enable_reflection: 是否启用反思
            enable_learning: 是否启用学习

        Returns:
            智能体响应
        """
        # 使用配置值作为默认值
        if not enable_reflection:
            enable_reflection = self.config["enable_reflection"]
        if not enable_learning:
            enable_learning = self.config["enable_learning"]

        # 记录交互开始
        interaction_start = datetime.now()

        # 构建思维链追踪
        thought_chain = []

        # 1. 感知阶段 - 记录思维步骤
        thought_chain.append(
            ThoughtStep(
                step_id="perception",
                timestamp=datetime.now(),
                content=f"感知输入: {user_input[:50]}...",
                reasoning_type="perception",
                confidence=0.95,
            )
        )

        # 2. 调用父类处理
        try:
            response = await super().process_input(user_input, **kwargs)
        except Exception as e:
            logger.error(f"父类处理失败: {e}")
            response = f"抱歉,处理过程中出现了问题: {e!s}"

        # 3. 记录响应思维步骤
        thought_chain.append(
            ThoughtStep(
                step_id="response_generation",
                timestamp=datetime.now(),
                content=f"生成响应: {response[:50]}...",
                reasoning_type="response_generation",
                confidence=0.85,
            )
        )

        # 4. 反思阶段(如果启用)
        if enable_reflection:
            try:
                await self._perform_post_interaction_reflection(
                    user_input, response, kwargs, thought_chain
                )
            except Exception as e:
                logger.warning(f"反思失败: {e}")

        # 5. 学习阶段(如果启用)
        if enable_learning:
            try:
                await self._perform_learning_from_interaction(user_input, response, kwargs)
            except Exception as e:
                logger.warning(f"学习失败: {e}")

        # 6. 定期记忆整合
        if self.config["enable_consolidation"]:
            try:
                await self._schedule_memory_consolidation()
            except Exception as e:
                logger.warning(f"记忆整合调度失败: {e}")

        # 更新性能追踪
        self.performance_tracker["interactions"] += 1

        interaction_time = (datetime.now() - interaction_start).total_seconds()

        # 返回响应(可选:添加性能信息)
        if kwargs.get("include_performance"):
            performance_info = f"\n\n⏱️ 处理时间: {interaction_time:.2f}s"
            response += performance_info

        return response

    async def _perform_post_interaction_reflection(
        self, user_input: str, response: str, context: dict[str, Any], thought_chain: list
    ):
        """执行交互后反思"""
        try:
            # 执行反思循环
            reflection_loop = await self.reflection_engine_v5.reflect_with_loop(
                original_input=user_input,
                output=response,
                context=context,
                thought_chain=thought_chain,
                reflection_types=[ReflectionType.OUTPUT, ReflectionType.PROCESS],
            )

            # 记录反思统计
            self.performance_tracker["reflections_performed"] += 1

            logger.info(f"🤔 反思完成: {reflection_loop.loop_id}")

        except Exception as e:
            logger.error(f"反思执行失败: {e}")

    async def _perform_learning_from_interaction(
        self, user_input: str, response: str, context: dict[str, Any]
    ):
        """从交互中学习"""
        try:
            # 创建学习经验
            task = MetaLearningTask(
                task_id=f"interaction_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                task_type="interaction_learning",
                support_set=[
                    {
                        "input": user_input,
                        "output": response,
                        "context": context,
                        "timestamp": datetime.now().isoformat(),
                    }
                ],
                query_set=[],
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "interaction_type": context.get("interaction_type", "general"),
                },
            )

            await self.meta_learning.learn_from_few_shots(task)

            self.performance_tracker["learning_cycles"] += 1

            logger.info("📚 学习完成")

        except Exception as e:
            logger.error(f"学习执行失败: {e}")

    async def _perform_initial_consolidation(self):
        """执行初始记忆整合"""
        try:
            report = await self.memory_consolidation.consolidate_memories(force=True)
            if report.get("status") == "completed":
                logger.info(f"🧠 初始记忆整合完成: {report.get('consolidated_count', 0)}项")
        except Exception as e:
            logger.warning(f"初始整合失败: {e}")

    async def _schedule_memory_consolidation(self):
        """调度记忆整合(每6小时执行一次)"""
        # 检查是否需要执行整合
        if self.memory_consolidation._should_consolidate():
            try:
                report = await self.memory_consolidation.consolidate_memories()
                if report.get("status") == "completed":
                    self.performance_tracker["memory_consolidations"] += 1
                    logger.info(
                        f"🧠 定期记忆整合: {report.get('consolidated_count', 0)}项, "
                        f"模式: {report.get('patterns_discovered', 0)}个"
                    )
            except Exception as e:
                logger.error(f"定期整合失败: {e}")

    async def optimize_self(self) -> dict[str, Any]:
        """自我优化 - 整合所有改进能力"""
        logger.info("🔧 开始自我优化...")

        optimization_report = {
            "timestamp": datetime.now().isoformat(),
            "memory_consolidation": None,
            "hyperparameter_optimization": None,
            "reflection_improvements": None,
        }

        # 1. 记忆整合
        try:
            consolidation_report = await self.memory_consolidation.consolidate_memories(force=True)
            optimization_report["memory_consolidation"] = consolidation_report
        except Exception as e:
            logger.error(f"记忆整合失败: {e}")
            optimization_report["memory_consolidation"] = {"error": str(e)}

        # 2. 超参数优化(如果有历史任务)
        if self.meta_learning.task_history:
            try:
                sample_tasks = self.meta_learning.task_history[-10:]
                optimized_params = await self.meta_learning.optimize_hyperparameters(
                    validation_tasks=sample_tasks, max_iterations=5
                )
                optimization_report["hyperparameter_optimization"] = optimized_params
            except Exception as e:
                logger.error(f"超参数优化失败: {e}")
                optimization_report["hyperparameter_optimization"] = {"error": str(e)}

        # 3. 应用反思改进
        try:
            applied_improvements = await self._apply_reflection_improvements()
            optimization_report["reflection_improvements"] = applied_improvements
        except Exception as e:
            logger.error(f"应用反思改进失败: {e}")
            optimization_report["reflection_improvements"] = {"error": str(e)}

        logger.info("✅ 自我优化完成")

        return optimization_report

    async def _apply_reflection_improvements(self) -> dict[str, Any]:
        """应用反思改进"""
        applied_count = 0

        # 获取待处理的行动项
        pending_actions = [
            action
            for action in self.reflection_engine_v5.action_tracker.values()
            if action.status.value == "pending"
        ]

        # 按优先级应用
        for action in pending_actions[:5]:  # 限制每次应用数量
            try:
                await self.reflection_engine_v5._execute_action(action)
                action.status = ActionStatus.COMPLETED
                action.completed_at = datetime.now()
                applied_count += 1
            except Exception as e:
                logger.error(f"应用行动项失败 {action.action_id}: {e}")

        return {"total_pending": len(pending_actions), "applied": applied_count}

    async def get_enhanced_stats(self) -> dict[str, Any]:
        """获取增强统计信息"""
        # 获取基础统计
        try:
            base_stats = await self.get_unified_overview()
        except Exception as e:
            logger.warning(f"获取基础统计失败: {e}")
            base_stats = {"agent_name": "EnhancedXiaonuo", "version": self.version}

        # 获取各模块统计
        consolidation_stats = await self.memory_consolidation.get_statistics()
        meta_learning_stats = await self.meta_learning.get_statistics()
        reflection_stats = await self.reflection_engine_v5.get_statistics()

        enhanced_stats = {
            "version": self.version,
            "agent_id": self.agent_id,
            "performance": self.performance_tracker,
            "memory_consolidation": {
                "total_consolidations": consolidation_stats["stats"]["total_consolidations"],
                "patterns_discovered": consolidation_stats["stats"]["patterns_discovered"],
                "knowledge_created": consolidation_stats["stats"]["knowledge_items_created"],
            },
            "meta_learning": {
                "tasks_processed": meta_learning_stats["stats"]["total_tasks"],
                "strategies_used": dict(meta_learning_stats["stats"]["strategies_tried"]),
                "avg_accuracy": meta_learning_stats.get("avg_accuracy", 0),
            },
            "reflection": {
                "total_reflections": reflection_stats["stats"]["total_reflections"],
                "causal_analyses": reflection_stats["stats"]["causal_analyses"],
                "action_items_completed": reflection_stats["stats"]["action_items_completed"],
                "avg_improvement": reflection_stats["stats"]["avg_improvement_score"],
            },
            "enhanced_capabilities": self.enhanced_capabilities,
            "config": self.config,
        }

        # 合并基础统计和增强统计
        base_stats.update(enhanced_stats)

        return base_stats

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        return {
            "status": "healthy",
            "version": self.version,
            "timestamp": datetime.now().isoformat(),
            "components": {
                "memory_consolidation": "active",
                "meta_learning": "active",
                "reflection_engine": "active",
            },
            "performance": self.performance_tracker,
        }


# 测试和实用函数
async def test_enhanced_xiaonuo():
    """测试增强小诺"""
    print("🚀 测试增强小诺智能体...")

    # 创建增强小诺
    xiaonuo = EnhancedXiaonuo()

    try:
        # 初始化(不传递记忆系统以避免依赖)
        await xiaonuo.initialize(memory_system=None)
        print("✅ 增强小诺初始化成功")

        # 测试交互(带反思和学习)
        print("\n💬 测试交互...")

        test_inputs = [
            "小诺真乖!",
            "帮我分析这个专利的创造性",
            "今天工作太累了",
            "帮我规划下周的内容策略",
        ]

        for user_input in test_inputs:
            print(f"\n👤 用户: {user_input}")
            response = await xiaonuo.process_input(
                user_input, enable_reflection=True, enable_learning=True
            )
            print(f"🤖 小诺: {response[:200]}...")

        # 获取增强统计
        print("\n📊 增强统计:")
        stats = await xiaonuo.get_enhanced_stats()

        print(f"  版本: {stats.get('version', 'N/A')}")
        print(f"  交互次数: {stats['performance']['interactions']}")
        print(f"  反思次数: {stats['reflection']['total_reflections']}")
        print(f"  学习周期: {stats['performance']['learning_cycles']}")
        print(f"  平均改进: {stats['reflection']['avg_improvement']:.3f}")
        print(f"  记忆整合: {stats['memory_consolidation']['total_consolidations']}次")

        # 执行自我优化
        print("\n🔧 执行自我优化...")
        await xiaonuo.optimize_self()
        print("优化报告完成")

        # 健康检查
        print("\n🏥 健康检查:")
        health = await xiaonuo.health_check()
        print(f"  状态: {health['status']}")
        print(f"  组件: {list(health['components'].keys())}")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()

    finally:
        print("\n✅ 测试完成")


# CLI入口函数
@async_main
async def main():
    """主函数 - CLI入口"""
    import argparse

    parser = argparse.ArgumentParser(description="小诺增强智能体v2.0")
    parser.add_argument("--test", action="store_true", help="运行测试")
    parser.add_argument("--interactive", action="store_true", help="交互模式")
    parser.add_argument("--stats", action="store_true", help="显示统计信息")

    args = parser.parse_args()

    # 创建增强小诺
    xiaonuo = EnhancedXiaonuo()

    # 初始化
    await xiaonuo.initialize(memory_system=None)

    if args.test:
        # 运行测试
        await test_enhanced_xiaonuo()

    elif args.stats:
        # 显示统计信息
        stats = await xiaonuo.get_enhanced_stats()
        print(json.dumps(stats, indent=2, ensure_ascii=False))

    elif args.interactive:
        # 交互模式
        print("💝 小诺增强智能体v2.0 - 交互模式")
        print("输入'quit'退出\n")

        while True:
            try:
                user_input = input("👤 您: ")
                if user_input.lower() in ["quit", "exit", "退出"]:
                    break

                response = await xiaonuo.process_input(
                    user_input, enable_reflection=True, enable_learning=True
                )

                print(f"🤖 小诺: {response}\n")

            except KeyboardInterrupt:
                print("\n\n👋 再见!")
                break
            except Exception as e:
                print(f"❌ 错误: {e}\n")

    else:
        # 默认运行测试
        await test_enhanced_xiaonuo()


if __name__ == "__main__":
    # 配置日志
    # setup_logging()  # 日志配置已移至模块导入

    # 运行主函数
    asyncio.run(main())
