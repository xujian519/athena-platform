#!/usr/bin/env python3
"""
Saga事务处理器
Saga Transaction Coordinator

实现Saga模式处理分布式事务
目标将分布式事务成功率提升到95%以上
"""

import asyncio
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


class SagaStatus(Enum):
    """Saga状态"""

    PENDING = "pending"  # 待执行
    RUNNING = "running"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    COMPENSATING = "compensating"  # 补偿中
    COMPENSATED = "compensated"  # 已补偿


class StepStatus(Enum):
    """步骤状态"""

    PENDING = "pending"  # 待执行
    RUNNING = "running"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    COMPENSATED = "compensated"  # 已补偿
    SKIPPED = "skipped"  # 已跳过


@dataclass
class SagaStep:
    """Saga步骤"""

    step_id: str
    name: str
    action: Callable  # 正向操作
    compensate: Callable  # 补偿操作
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: str | None = None
    compensated: bool = False


@dataclass
class SagaResult:
    """Saga结果"""

    saga_id: str
    status: SagaStatus
    completed_steps: int
    total_steps: int
    success_rate: float
    total_duration: float
    results: dict[str, Any]
    compensated_steps: list[str]
    final_error: str | None = None


class SagaTransaction:
    """
    Saga事务

    核心功能:
    1. 正向操作执行
    2. 补偿操作执行
    3. 状态管理
    4. 错误处理
    """

    def __init__(self, saga_id: str | None = None):
        """
        初始化Saga事务

        Args:
            saga_id: Saga ID(自动生成)
        """
        self.saga_id = saga_id or f"saga_{uuid.uuid4().hex[:16]}"
        self.status = SagaStatus.PENDING
        self.steps: list[SagaStep] = []
        self.created_at = datetime.now()

    def add_step(self, name: str, action: Callable, compensate: Callable, *args, **kwargs) -> str:
        """
        添加步骤

        Args:
            name: 步骤名称
            action: 正向操作
            compensate: 补偿操作
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            步骤ID
        """
        step_id = f"step_{len(self.steps)}"
        step = SagaStep(
            step_id=step_id,
            name=name,
            action=action,
            compensate=compensate,
            args=args,
            kwargs=kwargs,
        )
        self.steps.append(step)
        return step_id

    async def execute(self) -> SagaResult:
        """
        执行Saga事务

        Returns:
            SagaResult: 执行结果
        """
        start_time = datetime.now()
        self.status = SagaStatus.RUNNING

        completed_steps = 0
        results = {}
        compensated_steps = []

        try:
            # 执行正向操作
            for step in self.steps:
                step.status = StepStatus.RUNNING

                try:
                    # 执行正向操作
                    if asyncio.iscoroutinefunction(step.action):
                        result = await step.action(*step.args, **step.kwargs)
                    else:
                        loop = asyncio.get_event_loop()
                        result = await loop.run_in_executor(
                            None, lambda: step.action(*step.args, **step.kwargs)
                        )

                    step.result = result
                    step.status = StepStatus.COMPLETED
                    results[step.step_id] = result
                    completed_steps += 1

                except Exception as e:
                    step.status = StepStatus.FAILED
                    step.error = str(e)
                    logger.error(f"Saga步骤失败: {step.name} - {e}")

                    # 执行补偿
                    self.status = SagaStatus.COMPENSATING
                    compensated_steps = await self._compensate(completed_steps)

                    self.status = SagaStatus.COMPENSATED
                    raise

            # 全部成功
            self.status = SagaStatus.COMPLETED

        except Exception as e:
            # 事务失败
            final_error = str(e)
        else:
            final_error = None

        duration = (datetime.now() - start_time).total_seconds()

        return SagaResult(
            saga_id=self.saga_id,
            status=self.status,
            completed_steps=completed_steps,
            total_steps=len(self.steps),
            success_rate=completed_steps / len(self.steps) if self.steps else 0,
            total_duration=duration,
            results=results,
            compensated_steps=compensated_steps,
            final_error=final_error,
        )

    async def _compensate(self, failed_step_index: int) -> list[str]:
        """
        执行补偿操作

        Args:
            failed_step_index: 失败步骤的索引

        Returns:
            已补偿的步骤ID列表
        """
        compensated = []

        # 从失败步骤的前一个开始,逆序补偿
        for i in range(failed_step_index - 1, -1, -1):
            step = self.steps[i]

            if step.status != StepStatus.COMPLETED:
                continue

            step.status = StepStatus.RUNNING

            try:
                logger.info(f"执行补偿: {step.name}")

                # 执行补偿操作
                if asyncio.iscoroutinefunction(step.compensate):
                    await step.compensate(step.result)
                else:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, lambda: step.compensate(step.result))

                step.status = StepStatus.COMPENSATED
                step.compensated = True
                compensated.append(step.step_id)

            except Exception as e:
                logger.error(f"补偿失败: {step.name} - {e}")
                step.status = StepStatus.FAILED
                # 继续补偿其他步骤

        return compensated

    def get_status(self) -> SagaStatus:
        """获取状态"""
        return self.status

    def get_step_status(self, step_id: str) -> StepStatus | None:
        """获取步骤状态"""
        for step in self.steps:
            if step.step_id == step_id:
                return step.status
        return None


class SagaCoordinator:
    """
    Saga协调器

    管理多个Saga事务
    """

    def __init__(self):
        """初始化协调器"""
        self.name = "Saga协调器 v1.0"
        self.version = "1.0.0"

        # 活跃的Saga
        self.active_sagas: dict[str, SagaTransaction] = {}

        # Saga历史
        self.saga_history: list[SagaResult] = []

        # 统计信息
        self.stats = {
            "total_sagas": 0,
            "completed_sagas": 0,
            "failed_sagas": 0,
            "compensated_sagas": 0,
            "total_steps": 0,
            "successful_steps": 0,
            "avg_saga_duration": 0.0,
        }

    def create_saga(self, saga_id: str | None = None) -> SagaTransaction:
        """
        创建新Saga

        Args:
            saga_id: Saga ID

        Returns:
            SagaTransaction: Saga实例
        """
        saga = SagaTransaction(saga_id)
        self.active_sagas[saga.saga_id] = saga
        return saga

    async def execute_saga(self, saga: SagaTransaction) -> SagaResult:
        """
        执行Saga

        Args:
            saga: Saga实例

        Returns:
            SagaResult: 执行结果
        """
        # 更新统计
        self.stats["total_sagas"] += 1
        self.stats["total_steps"] += len(saga.steps)

        # 执行
        result = await saga.execute()

        # 更新统计
        if result.status == SagaStatus.COMPLETED:
            self.stats["completed_sagas"] += 1
            self.stats["successful_steps"] += result.completed_steps
        elif result.status == SagaStatus.COMPENSATED:
            self.stats["compensated_sagas"] += 1
        else:
            self.stats["failed_sagas"] += 1

        # 更新平均时长
        if self.stats["completed_sagas"] > 0:
            self.stats["avg_saga_duration"] = (
                self.stats["avg_saga_duration"] * (self.stats["completed_sagas"] - 1)
                + result.total_duration
            ) / self.stats["completed_sagas"]

        # 记录历史
        self.saga_history.append(result)

        # 从活跃列表移除
        if saga.saga_id in self.active_sagas:
            del self.active_sagas[saga.saga_id]

        return result

    def get_saga(self, saga_id: str) -> SagaTransaction | None:
        """获取Saga实例"""
        return self.active_sagas.get(saga_id)

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        total = self.stats["total_sagas"]
        return {
            **self.stats,
            "success_rate": self.stats["completed_sagas"] / total if total > 0 else 0,
            "active_sagas": len(self.active_sagas),
        }


# 单例实例
_coordinator_instance: SagaCoordinator | None = None


async def get_saga_coordinator() -> SagaCoordinator:
    """获取Saga协调器单例(异步版本)"""
    global _coordinator_instance
    if _coordinator_instance is None:
        _coordinator_instance = SagaCoordinator()
        logger.info("Saga协调器已初始化")
    return _coordinator_instance


def get_saga_coordinator_sync() -> SagaCoordinator:
    """获取Saga协调器单例(同步版本,用于向后兼容)"""
    global _coordinator_instance
    if _coordinator_instance is None:
        _coordinator_instance = SagaCoordinator()
        logger.info("Saga协调器已初始化")
    return _coordinator_instance


async def main():
    """测试主函数"""
    coordinator = get_saga_coordinator()

    print("=== Saga事务测试 ===\n")

    # 创建测试数据
    test_data = {"value": 0}

    # 定义操作
    async def action1(data):
        data["value"] += 10
        print(f"  步骤1: value = {data['value']}")
        return data

    async def compensate1(data):
        data["value"] -= 10
        print(f"  补偿1: value = {data['value']}")

    async def action2(data):
        data["value"] *= 2
        print(f"  步骤2: value = {data['value']}")
        return data

    async def compensate2(data):
        data["value"] //= 2
        print(f"  补偿2: value = {data['value']}")

    async def action3(data):
        data["value"] += 5
        print(f"  步骤3: value = {data['value']}")
        if data["value"] > 0:
            raise ValueError("模拟失败")
        return data

    async def compensate3(data):
        data["value"] -= 5
        print(f"  补偿3: value = {data['value']}")

    # 创建Saga
    saga = coordinator.create_saga()
    saga.add_step("步骤1", action1, compensate1, test_data)
    saga.add_step("步骤2", action2, compensate2, test_data)
    saga.add_step("步骤3", action3, compensate3, test_data)

    print("执行Saga(预期失败并补偿)...")
    result = await coordinator.execute_saga(saga)

    print("\n=== 执行结果 ===")
    print(f"状态: {result.status.value}")
    print(f"完成步骤: {result.completed_steps}/{result.total_steps}")
    print(f"补偿步骤: {result.compensated_steps}")
    print(f"最终错误: {result.final_error}")

    # 显示统计
    stats = coordinator.get_stats()
    print("\n=== 统计信息 ===")
    print(f"总Saga数: {stats['total_sagas']}")
    print(f"成功: {stats['completed_sagas']}")
    print(f"失败: {stats['failed_sagas']}")
    print(f"已补偿: {stats['compensated_sagas']}")
    print(f"成功率: {stats['success_rate']:.1%}")


# 入口点: @async_main装饰器已添加到main函数
