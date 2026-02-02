#!/usr/bin/env python3
"""
智能体协同机制
Agent Collaboration Mechanism

实现智能体之间的协同工作:
- 并行任务处理
- 协作协议
- 结果合并
- 冲突解决

作者: 小诺·双鱼公主
创建时间: 2025-12-27
版本: v1.0.0 "智能体协同"
"""

import asyncio
import concurrent.futures
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


class CollaborationMode(Enum):
    """协同模式"""

    PARALLEL = "parallel"  # 并行执行
    SEQUENTIAL = "sequential"  # 顺序执行
    PIPELINE = "pipeline"  # 流水线
    COLLABORATIVE = "collaborative"  # 协作执行


class AgentStatus(Enum):
    """智能体状态"""

    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class AgentTask:
    """智能体任务"""

    task_id: str
    agent_name: str
    task_data: dict[str, Any]
    priority: int = 5
    dependencies: list[str] = field(default_factory=list)
    status: str = "pending"
    result: Any | None = None
    error: str | None = None
    started_at: str | None = None
    completed_at: str | None = None


@dataclass
class CollaborationResult:
    """协同结果"""

    task_id: str
    mode: CollaborationMode
    agent_results: dict[str, Any]
    merged_result: Any
    total_time: float
    success: bool
    errors: list[str] = field(default_factory=list)


class AgentCollaborationManager:
    """
    智能体协同管理器

    管理多个智能体的协同工作
    """

    def __init__(self):
        """初始化协同管理器"""
        self.name = "智能体协同管理器"
        self.version = "v1.0.0"

        # 智能体注册
        self.agents: dict[str, Any] = {}
        self.agent_status: dict[str, AgentStatus] = {}

        # 任务队列
        self.task_queue: list[AgentTask] = []
        self.completed_tasks: list[AgentTask] = []

        # 协作协议
        self.collaboration_protocols = self._init_protocols()

        logger.info(f"🤝 {self.name} ({self.version}) 初始化完成")
        logger.info("   ✅ 并行处理: 就绪")
        logger.info("   ✅ 协作协议: 就绪")
        logger.info("   ✅ 结果合并: 就绪")

    def _init_protocols(self) -> dict[str, Any]:
        """初始化协作协议"""
        return {
            "max_parallel_tasks": 5,
            "task_timeout": 300,  # 5分钟
            "retry_attempts": 3,
            "result_merge_strategy": "weighted_average",
        }

    def register_agent(self, agent_name: str, agent_instance: Any) -> Any:
        """注册智能体"""
        self.agents[agent_name] = agent_instance
        self.agent_status[agent_name] = AgentStatus.IDLE
        logger.info(f"   ✅ 注册智能体: {agent_name}")

    async def collaborate(
        self,
        task_id: str,
        agents: list[str],
        task_data: dict[str, Any],        mode: CollaborationMode = CollaborationMode.PARALLEL,
    ) -> CollaborationResult:
        """
        执行协同任务

        Args:
            task_id: 任务ID
            agents: 参与的智能体列表
            task_data: 任务数据
            mode: 协同模式

        Returns:
            CollaborationResult: 协同结果
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"🤝 启动协同任务: {task_id}")
        logger.info(f"   参与智能体: {agents}")
        logger.info(f"   协同模式: {mode.value}")
        logger.info(f"{'='*70}\n")

        start_time = datetime.now()

        try:
            if mode == CollaborationMode.PARALLEL:
                result = await self._parallel_collaborate(task_id, agents, task_data)
            elif mode == CollaborationMode.SEQUENTIAL:
                result = await self._sequential_collaborate(task_id, agents, task_data)
            elif mode == CollaborationMode.PIPELINE:
                result = await self._pipeline_collaborate(task_id, agents, task_data)
            elif mode == CollaborationMode.COLLABORATIVE:
                result = await self._collaborative_execute(task_id, agents, task_data)
            else:
                raise ValueError(f"未知的协同模式: {mode}")

        except Exception as e:
            logger.error(f"协同任务执行失败: {e}")
            result = CollaborationResult(
                task_id=task_id,
                mode=mode,
                agent_results={},
                merged_result=None,
                total_time=0,
                success=False,
                errors=[str(e)],
            )

        # 计算总时间
        total_time = (datetime.now() - start_time).total_seconds()
        result.total_time = total_time

        logger.info(f"\n{'='*70}")
        logger.info(f"✅ 协同任务完成: {task_id}")
        logger.info(f"   耗时: {total_time:.2f}秒")
        logger.info(f"   成功: {result.success}")
        logger.info(f"{'='*70}\n")

        return result

    async def _parallel_collaborate(
        self, task_id: str, agents: list[str], task_data: dict[str, Any]
    ) -> CollaborationResult:
        """并行协同执行"""
        logger.info("🔄 执行并行协同...")

        # 创建任务
        tasks = []
        for agent_name in agents:
            task = AgentTask(
                task_id=f"{task_id}_{agent_name}", agent_name=agent_name, task_data=task_data
            )
            tasks.append(task)

        # 并行执行
        agent_results = {}
        errors = []

        async def execute_single_task(task: AgentTask):
            try:
                task.status = "processing"
                task.started_at = datetime.now().isoformat()

                # 模拟智能体执行(实际应该调用真实智能体)
                result = await self._simulate_agent_execution(task)

                task.result = result
                task.status = "completed"
                task.completed_at = datetime.now().isoformat()

                return task.agent_name, result

            except Exception as e:
                task.status = "error"
                task.error = str(e)
                errors.append(f"{task.agent_name}: {e!s}")
                raise

        # 并发执行
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.collaboration_protocols["max_parallel_tasks"]
        ) as executor:
            loop = asyncio.get_event_loop()
            futures = [loop.run_in_executor(executor, execute_single_task, task) for task in tasks]

            for future in asyncio.as_completed(futures):
                agent_name, result = await future
                agent_results[agent_name] = result
                logger.info(f"   ✓ {agent_name} 完成")

        # 合并结果
        merged_result = self._merge_results(agent_results, mode="parallel")

        return CollaborationResult(
            task_id=task_id,
            mode=CollaborationMode.PARALLEL,
            agent_results=agent_results,
            merged_result=merged_result,
            total_time=0,  # 会在外层设置
            success=len(errors) == 0,
            errors=errors,
        )

    async def _sequential_collaborate(
        self, task_id: str, agents: list[str], task_data: dict[str, Any]
    ) -> CollaborationResult:
        """顺序协同执行"""
        logger.info("🔄 执行顺序协同...")

        agent_results = {}
        errors = []
        accumulated_data = task_data.copy()

        for i, agent_name in enumerate(agents):
            logger.info(f"   执行第{i+1}个智能体: {agent_name}")

            try:
                task = AgentTask(
                    task_id=f"{task_id}_{agent_name}",
                    agent_name=agent_name,
                    task_data=accumulated_data,
                )

                task.status = "processing"
                task.started_at = datetime.now().isoformat()

                # 执行任务
                result = await self._simulate_agent_execution(task)

                task.result = result
                task.status = "completed"
                task.completed_at = datetime.now().isoformat()

                agent_results[agent_name] = result

                # 将结果传递给下一个智能体
                accumulated_data.update(result)

            except Exception as e:
                task.status = "error"
                task.error = str(e)
                errors.append(f"{agent_name}: {e!s}")
                logger.error(f"   ✗ {agent_name} 失败: {e}")

        # 合并结果
        merged_result = self._merge_results(agent_results, mode="sequential")

        return CollaborationResult(
            task_id=task_id,
            mode=CollaborationMode.SEQUENTIAL,
            agent_results=agent_results,
            merged_result=merged_result,
            total_time=0,
            success=len(errors) == 0,
            errors=errors,
        )

    async def _pipeline_collaborate(
        self, task_id: str, agents: list[str], task_data: dict[str, Any]
    ) -> CollaborationResult:
        """流水线协同执行"""
        logger.info("🔄 执行流水线协同...")

        # 流水线是顺序执行的一种特殊形式
        # 每个智能体的输出是下一个的输入
        return await self._sequential_collaborate(task_id, agents, task_data)

    async def _collaborative_execute(
        self, task_id: str, agents: list[str], task_data: dict[str, Any]
    ) -> CollaborationResult:
        """协作执行(智能体之间可以互相调用)"""
        logger.info("🔄 执行协作协同...")

        # 简化实现:先用并行,然后协作调整
        initial_result = await self._parallel_collaborate(task_id, agents, task_data)

        # 协作调整:让智能体互相查看结果并调整
        logger.info("   执行协作调整...")
        adjusted_results = initial_result.agent_results.copy()

        for agent_name, result in initial_result.agent_results.items():
            # 模拟智能体看到其他人的结果后调整
            adjusted_results[agent_name] = {
                **result,
                "adjusted": True,
                "adjustment_note": f"{agent_name}看到其他智能体的结果后进行了调整",
            }

        merged_result = self._merge_results(adjusted_results, mode="collaborative")

        return CollaborationResult(
            task_id=task_id,
            mode=CollaborationMode.COLLABORATIVE,
            agent_results=adjusted_results,
            merged_result=merged_result,
            total_time=initial_result.total_time,
            success=True,
            errors=[],
        )

    async def _simulate_agent_execution(self, task: AgentTask) -> dict[str, Any]:
        """模拟智能体执行(实际应该调用真实智能体)"""
        # 模拟处理时间
        await asyncio.sleep(0.5)

        # 模拟不同智能体的返回结果
        agent_responses = {
            "小娜": {
                "opinion": "从法律角度分析",
                "confidence": 0.85,
                "recommendation": "建议采用保守方案",
            },
            "云熙": {
                "opinion": "从数据管理角度分析",
                "confidence": 0.75,
                "recommendation": "建议采用统一技术栈",
            },
            "小宸": {
                "opinion": "从运营角度分析",
                "confidence": 0.80,
                "recommendation": "考虑用户体验",
            },
            "小诺": {
                "opinion": "综合协调分析",
                "confidence": 0.90,
                "recommendation": "平衡各方因素",
            },
        }

        return agent_responses.get(
            task.agent_name,
            {"opinion": "分析完成", "confidence": 0.70, "recommendation": "建议进一步分析"},
        )

    def _merge_results(self, agent_results: dict[str, Any], mode: str) -> dict[str, Any]:
        """合并智能体结果"""
        if not agent_results:
            return {}

        # 简化的合并策略
        if mode == "parallel":
            # 并行:平均加权
            avg_confidence = sum(r.get("confidence", 0.5) for r in agent_results.values()) / len(
                agent_results
            )

            return {
                "merge_mode": "parallel",
                "average_confidence": avg_confidence,
                "all_recommendations": [
                    r.get("recommendation", "") for r in agent_results.values()
                ],
                "agent_count": len(agent_results),
            }

        elif mode == "sequential":
            # 顺序:取最后一个结果
            last_result = list(agent_results.values())[-1]
            return {
                "merge_mode": "sequential",
                "final_result": last_result,
                "chain_length": len(agent_results),
            }

        elif mode == "collaborative":
            # 协作:综合所有结果
            return {
                "merge_mode": "collaborative",
                "synthesized": True,
                "agent_count": len(agent_results),
                "all_results": agent_results,
            }

        return {}

    def get_status(self) -> dict[str, Any]:
        """获取协同管理器状态"""
        return {
            "registered_agents": list(self.agents.keys()),
            "agent_status": {k: v.value for k, v in self.agent_status.items()},
            "pending_tasks": len(self.task_queue),
            "completed_tasks": len(self.completed_tasks),
            "protocols": self.collaboration_protocols,
        }


# 全局实例
_collaboration_manager: AgentCollaborationManager = None


def get_collaboration_manager() -> AgentCollaborationManager:
    """获取协同管理器单例"""
    global _collaboration_manager
    if _collaboration_manager is None:
        _collaboration_manager = AgentCollaborationManager()
        # 注册默认智能体
        for agent in ["小诺", "小娜", "云熙", "小宸"]:
            _collaboration_manager.register_agent(agent, f"Agent_{agent}")
    return _collaboration_manager


# 便捷函数
async def collaborate_agents(
    task_id: str,
    agents: list[str],
    task_data: dict[str, Any],    mode: CollaborationMode = CollaborationMode.PARALLEL,
) -> CollaborationResult:
    """便捷函数:执行智能体协同"""
    manager = get_collaboration_manager()
    return await manager.collaborate(task_id, agents, task_data, mode)


if __name__ == "__main__":

    async def test():
        """测试智能体协同"""
        print("🧪 测试智能体协同机制")
        print("=" * 70)

        manager = get_collaboration_manager()

        # 测试1:并行协同
        print("\n📋 测试1: 并行协同")
        result1 = await collaborate_agents(
            task_id="test_parallel",
            agents=["小娜", "云熙", "小宸"],
            task_data={"question": "选择技术方案"},
            mode=CollaborationMode.PARALLEL,
        )

        print(f"成功: {result1.success}")
        print(f"耗时: {result1.total_time:.2f}秒")
        print(f"合并结果: {result1.merged_result}")

        # 测试2:顺序协同
        print("\n📋 测试2: 顺序协同")
        result2 = await collaborate_agents(
            task_id="test_sequential",
            agents=["小娜", "小诺"],
            task_data={"question": "法律合规检查"},
            mode=CollaborationMode.SEQUENTIAL,
        )

        print(f"成功: {result2.success}")
        print(f"耗时: {result2.total_time:.2f}秒")
        print(f"合并结果: {result2.merged_result}")

        # 查看状态
        print("\n📊 协同管理器状态:")
        status = manager.get_status()
        print(f"   注册智能体: {status['registered_agents']}")
        print(f"   智能体状态: {status['agent_status']}")
        print(f"   已完成任务: {status['completed_tasks']}")

    asyncio.run(test())
