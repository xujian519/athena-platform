#!/usr/bin/env python3
from __future__ import annotations
"""
长链执行器
Long Chain Executor

执行包含多个步骤的复杂任务链
支持检查点、恢复和容错,目标将长链成功率从65%提升到80%
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    """步骤状态"""

    PENDING = "pending"  # 待执行
    RUNNING = "running"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    SKIPPED = "skipped"  # 已跳过
    RETRYING = "retrying"  # 重试中


class ChainStatus(Enum):
    """链状态"""

    PENDING = "pending"  # 待执行
    RUNNING = "running"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    PAUSED = "paused"  # 已暂停


@dataclass
class ExecutionStep:
    """执行步骤"""

    step_id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: float = 30.0
    is_checkpoint: bool = False  # 是否为检查点
    start_time: datetime | None = None
    end_time: datetime | None = None


@dataclass
class ChainResult:
    """链执行结果"""

    chain_id: str
    status: ChainStatus
    completed_steps: int
    total_steps: int
    success_rate: float
    total_duration: float
    results: dict[str, Any]
    errors: dict[str, str]
    checkpoint_data: dict[str, Any]
class LongChainExecutor:
    """
    长链执行器

    核心功能:
    1. 依赖管理
    2. 检查点机制
    3. 故障恢复
    4. 进度跟踪
    """

    def __init__(self):
        """初始化执行器"""
        self.name = "长链执行器 v1.0"
        self.version = "1.0.0"

        # 执行链
        self.chains: dict[str, list[ExecutionStep]] = {}

        # 链状态
        self.chain_statuses: dict[str, ChainStatus] = {}

        # 检查点数据
        self.checkpoints: dict[str, dict[str, Any]] = {}

        # 执行历史
        self.execution_history: list[dict[str, Any]] = []

        # 统计信息
        self.stats = {
            "total_chains": 0,
            "successful_chains": 0,
            "failed_chains": 0,
            "total_steps": 0,
            "successful_steps": 0,
            "failed_steps": 0,
            "avg_chain_duration": 0.0,
            "checkpoint_recoveries": 0,
        }

    def create_chain(self, chain_id: str, steps: list[ExecutionStep]):
        """
        创建执行链

        Args:
            chain_id: 链ID
            steps: 步骤列表
        """
        # 验证依赖
        self._validate_dependencies(steps)

        self.chains[chain_id] = steps
        self.chain_statuses[chain_id] = ChainStatus.PENDING

        # 初始化检查点
        self.checkpoints[chain_id] = {}

        logger.info(f"创建执行链: {chain_id}, 包含{len(steps)}个步骤")

    def _validate_dependencies(self, steps: list[ExecutionStep]) -> Any:
        """验证依赖关系"""
        step_ids = {step.step_id for step in steps}

        for step in steps:
            for dep in step.dependencies:
                if dep not in step_ids:
                    raise ValueError(f"无效依赖: {step.step_id} 依赖 {dep}, 但 {dep} 不存在")

        # 检查循环依赖
        self._check_circular_dependencies(steps)

    def _check_circular_dependencies(self, steps: list[ExecutionStep]) -> Any:
        """检查循环依赖"""
        step_map = {step.step_id: step for step in steps}

        def visit(step_id: str, visited: set[str], rec_stack: set[str]) -> bool:
            visited.add(step_id)
            rec_stack.add(step_id)

            step = step_map.get(step_id)
            if step:
                for dep in step.dependencies:
                    if dep not in visited:
                        if visit(dep, visited, rec_stack):
                            return True
                    elif dep in rec_stack:
                        return True

            rec_stack.remove(step_id)
            return False

        visited: set[str] = set()
        for step in steps:
            if step.step_id not in visited and visit(step.step_id, visited, set()):
                raise ValueError(f"检测到循环依赖涉及步骤: {step.step_id}")

    async def execute_chain(self, chain_id: str, from_checkpoint: bool = False) -> ChainResult:
        """
        执行链

        Args:
            chain_id: 链ID
            from_checkpoint: 是否从检查点恢复

        Returns:
            ChainResult: 执行结果
        """
        if chain_id not in self.chains:
            raise ValueError(f"链不存在: {chain_id}")

        steps = self.chains[chain_id]
        start_time = datetime.now()

        # 更新状态
        self.chain_statuses[chain_id] = ChainStatus.RUNNING
        self.stats["total_chains"] += 1

        # 从检查点恢复
        if from_checkpoint and chain_id in self.checkpoints:
            last_checkpoint = self.checkpoints[chain_id].get("last_checkpoint")
            if last_checkpoint:
                logger.info(f"从检查点恢复: {last_checkpoint}")
                self.stats["checkpoint_recoveries"] += 1

        results = {}
        errors = {}
        completed_steps = 0

        try:
            for step in steps:
                # 跳过已完成或无需执行的步骤
                if step.status == StepStatus.COMPLETED:
                    completed_steps += 1
                    results[step.step_id] = step.result
                    continue

                # 检查依赖
                if not self._check_dependencies(step, steps):
                    logger.warning(f"跳过步骤(依赖未满足): {step.step_id}")
                    step.status = StepStatus.SKIPPED
                    continue

                # 执行步骤
                try:
                    step.status = StepStatus.RUNNING
                    step.start_time = datetime.now()

                    # 执行(带超时)
                    result = await asyncio.wait_for(self._execute_step(step), timeout=step.timeout)

                    step.result = result
                    step.status = StepStatus.COMPLETED
                    step.end_time = datetime.now()

                    results[step.step_id] = result
                    completed_steps += 1
                    self.stats["successful_steps"] += 1

                    # 保存检查点
                    if step.is_checkpoint:
                        self._save_checkpoint(chain_id, step.step_id, results)

                except asyncio.TimeoutError:
                    step.status = StepStatus.FAILED
                    step.error = f"超时({step.timeout}秒)"
                    errors[step.step_id] = step.error
                    self.stats["failed_steps"] += 1

                    # 重试
                    if step.retry_count < step.max_retries:
                        step.status = StepStatus.RETRYING
                        step.retry_count += 1
                        # 重新加入队列末尾
                        steps.append(step)
                        steps.remove(step)
                        continue

                except Exception as e:
                    step.error = str(e)
                    step.status = StepStatus.FAILED
                    errors[step.step_id] = step.error
                    self.stats["failed_steps"] += 1

                    # 重试
                    if step.retry_count < step.max_retries:
                        step.status = StepStatus.RETRYING
                        step.retry_count += 1
                        steps.append(step)
                        steps.remove(step)
                        continue

                    # 严重错误,停止执行
                    logger.error(f"步骤执行失败(已达最大重试次数): {step.step_id} - {e}")
                    raise

            # 链执行完成
            self.chain_statuses[chain_id] = ChainStatus.COMPLETED
            self.stats["successful_chains"] += 1

        except Exception as e:
            self.chain_statuses[chain_id] = ChainStatus.FAILED
            self.stats["failed_chains"] += 1
            logger.error(f"链执行失败: {chain_id} - {e}")

        # 计算结果
        duration = (datetime.now() - start_time).total_seconds()
        success_rate = completed_steps / len(steps) if steps else 0

        result = ChainResult(
            chain_id=chain_id,
            status=self.chain_statuses[chain_id],
            completed_steps=completed_steps,
            total_steps=len(steps),
            success_rate=success_rate,
            total_duration=duration,
            results=results,
            errors=errors,
            checkpoint_data=self.checkpoints.get(chain_id, {}),
        )

        # 更新平均时长
        self.stats["total_steps"] += len(steps)
        if self.stats["successful_chains"] > 0:
            self.stats["avg_chain_duration"] = (
                self.stats["avg_chain_duration"] * (self.stats["successful_chains"] - 1) + duration
            ) / self.stats["successful_chains"]

        return result

    def _check_dependencies(self, step: ExecutionStep, all_steps: list[ExecutionStep]) -> bool:
        """检查依赖是否满足"""
        for dep_id in step.dependencies:
            dep_step = next((s for s in all_steps if s.step_id == dep_id), None)
            if not dep_step or dep_step.status != StepStatus.COMPLETED:
                return False
        return True

    async def _execute_step(self, step: ExecutionStep) -> Any:
        """执行单个步骤"""
        if asyncio.iscoroutinefunction(step.func):
            return await step.func(*step.args, **step.kwargs)
        else:
            # 在executor中运行同步函数
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: step.func(*step.args, **step.kwargs))

    def _save_checkpoint(self, chain_id: str, step_id: str, results: dict[str, Any]) -> Any:
        """保存检查点"""
        if chain_id not in self.checkpoints:
            self.checkpoints[chain_id] = {}

        self.checkpoints[chain_id]["last_checkpoint"] = step_id
        self.checkpoints[chain_id][step_id] = {
            "results": results.copy(),
            "timestamp": datetime.now().isoformat(),
        }

        logger.debug(f"保存检查点: {chain_id}/{step_id}")

    def pause_chain(self, chain_id: str) -> Any:
        """暂停链执行"""
        if chain_id in self.chain_statuses:
            self.chain_statuses[chain_id] = ChainStatus.PAUSED
            logger.info(f"暂停执行链: {chain_id}")

    async def resume_chain(self, chain_id: str) -> ChainResult:
        """恢复链执行"""
        return await self.execute_chain(chain_id, from_checkpoint=True)

    def get_chain_status(self, chain_id: str) -> ChainStatus | None:
        """获取链状态"""
        return self.chain_statuses.get(chain_id)

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()


# 单例实例
_executor_instance: LongChainExecutor | None = None


def get_long_chain_executor() -> LongChainExecutor:
    """获取长链执行器单例"""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = LongChainExecutor()
        logger.info("长链执行器已初始化")
    return _executor_instance


async def main():
    """测试主函数"""
    executor = get_long_chain_executor()

    print("=== 长链执行测试 ===\n")

    # 创建测试步骤
    steps = [
        ExecutionStep(
            step_id="step1", name="初始化", func=lambda: {"initialized": True}, is_checkpoint=True
        ),
        ExecutionStep(
            step_id="step2",
            name="处理数据",
            func=lambda x: {"processed": True, "data": x},
            dependencies=["step1"],
        ),
        ExecutionStep(
            step_id="step3",
            name="验证结果",
            func=lambda: {"validated": True},
            dependencies=["step2"],
            is_checkpoint=True,
        ),
        ExecutionStep(
            step_id="step4",
            name="生成输出",
            func=lambda: {"output": "done"},
            dependencies=["step3"],
        ),
    ]

    # 创建链
    chain_id = "test_chain"
    executor.create_chain(chain_id, steps)

    # 执行
    print("执行链...")
    result = await executor.execute_chain(chain_id)

    print("\n=== 执行结果 ===")
    print(f"状态: {result.status.value}")
    print(f"完成步骤: {result.completed_steps}/{result.total_steps}")
    print(f"成功率: {result.success_rate:.1%}")
    print(f"执行时长: {result.total_duration:.2f}秒")

    # 显示统计
    stats = executor.get_stats()
    print("\n=== 统计信息 ===")
    print(f"总链数: {stats['total_chains']}")
    print(f"成功链: {stats['successful_chains']}")
    print(f"失败链: {stats['failed_chains']}")
    print(f"平均时长: {stats['avg_chain_duration']:.2f}秒")


# 入口点: @async_main装饰器已添加到main函数
