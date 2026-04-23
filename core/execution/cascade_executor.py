#!/usr/bin/env python3
from __future__ import annotations
"""
级联调用执行器 - 第一阶段优化
Cascade Executor - Phase 1 Optimization

优化重点:
1. 调用链路验证
2. 级联调用重试机制
3. 上下文传递优化
4. 调用链路监控

作者: 小诺·双鱼公主
版本: v1.0.0 "级联优化"
创建: 2026-01-12
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ChainStatus(Enum):
    """链路状态"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"


@dataclass
class ChainStep:
    """链路步骤"""

    step_id: str
    tool_name: str
    action: str
    input_data: dict[str, Any]
    output_data: Optional[dict[str, Any]] = None
    status: ChainStatus = ChainStatus.PENDING
    error: Optional[str] = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    execution_time: float = 0.0
    retry_count: int = 0
    depends_on: list[str] = field(default_factory=list)  # 依赖的步骤ID


@dataclass
class ChainResult:
    """链路执行结果"""

    success: bool
    completed_steps: list[ChainStep]
    failed_steps: list[ChainStep]
    total_execution_time: float
    final_output: dict[str, Any]
    error_summary: list[str]
    retry_summary: dict[str, int]


@dataclass
class ChainCheckpoint:
    """链路检查点"""

    checkpoint_id: str
    step_id: str
    state: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


class CascadeExecutor:
    """级联调用执行器"""

    def __init__(self):
        self.name = "级联调用执行器 v1.0"
        self.version = "1.0.0"

        # 检查点存储
        self.checkpoints: dict[str, ChainCheckpoint] = {}

        # 重试配置
        self.max_retries = 3
        self.retry_delay = 1.0  # 秒
        self.retry_backoff = 2.0  # 指数退避系数

        # 超时配置
        self.default_timeout = 30.0  # 秒
        self.step_timeout = 10.0  # 秒

        # 统计信息
        self.stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_retries": 0,
            "avg_execution_time": 0.0,
            "checkpoint_hits": 0,
        }

        logger.info(f"⛓️ {self.name} 初始化完成")

    async def execute_chain(
        self,
        steps: list[ChainStep],
        context: dict[str, Any],        enable_checkpoint: bool = True,
        enable_retry: bool = True,
    ) -> ChainResult:
        """
        执行级联调用链路

        Args:
            steps: 调用链路步骤
            context: 执行上下文
            enable_checkpoint: 是否启用检查点
            enable_retry: 是否启用重试

        Returns:
            ChainResult: 执行结果
        """
        start_time = time.time()

        # 1. 验证链路
        validation_error = self._validate_chain(steps)
        if validation_error:
            return ChainResult(
                success=False,
                completed_steps=[],
                failed_steps=steps,
                total_execution_time=time.time() - start_time,
                final_output=None,
                error_summary=[validation_error],
                retry_summary={},
            )

        # 2. 检查检查点
        if enable_checkpoint:
            checkpoint = self._load_checkpoint(steps)
            if checkpoint:
                self.stats["checkpoint_hits"] += 1
                logger.info(f"📌 从检查点恢复: {checkpoint.checkpoint_id}")
                # 从检查点恢复状态
                context.update(checkpoint.state)

        # 3. 执行链路
        completed_steps = []
        failed_steps = []
        retry_summary = {}

        for step in steps:
            # 检查依赖
            if not self._check_dependencies(step, completed_steps):
                logger.warning(f"⚠️ 步骤{step.step_id}依赖未满足,跳过")
                step.status = ChainStatus.SKIPPED
                failed_steps.append(step)
                continue

            # 执行步骤
            try:
                step_result = await self._execute_step(step, context, enable_retry)

                if step_result["success"]:
                    step.status = ChainStatus.COMPLETED
                    step.output_data = step_result["output"]
                    completed_steps.append(step)

                    # 更新上下文
                    context[f"step_{step.step_id}_output"] = step_result["output"]

                    # 保存检查点
                    if enable_checkpoint:
                        self._save_checkpoint(step, context)

                else:
                    # 执行失败
                    if enable_retry and step.retry_count < self.max_retries:
                        step.status = ChainStatus.RETRYING
                        step.retry_count += 1
                        retry_summary[step.step_id] = step.retry_count

                        # 重试逻辑
                        await asyncio.sleep(
                            self.retry_delay * (self.retry_backoff**step.retry_count)
                        )

                        # 重新加入队列重试
                        steps.append(step)

                        logger.info(f"🔄 重试步骤 {step.step_id} (第{step.retry_count}次)")
                    else:
                        step.status = ChainStatus.FAILED
                        step.error = step_result.get("error", "Unknown error")
                        failed_steps.append(step)

                        # 失败后是否继续?
                        if not self._can_continue_after_failure(step, steps):
                            logger.error(f"❌ 关键步骤失败,终止链路: {step.step_id}")
                            break

            except Exception as e:
                logger.error(f"❌ 步骤执行异常: {step.step_id}, 错误: {e}")
                step.status = ChainStatus.FAILED
                step.error = str(e)
                failed_steps.append(step)

                if not self._can_continue_after_failure(step, steps):
                    break

        # 4. 计算结果
        total_time = time.time() - start_time
        success = len(failed_steps) == 0

        result = ChainResult(
            success=success,
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            total_execution_time=total_time,
            final_output=self._extract_final_output(completed_steps),
            error_summary=[s.error for s in failed_steps if s.error],
            retry_summary=retry_summary,
        )

        # 5. 更新统计
        self._update_stats(result)

        return result

    def _validate_chain(self, steps: list[ChainStep]) -> Optional[str]:
        """验证链路"""
        if not steps:
            return "链路为空"

        # 检查步骤ID唯一性
        step_ids = [s.step_id for s in steps]
        if len(step_ids) != len(set(step_ids)):
            return "步骤ID重复"

        # 检查依赖关系
        for step in steps:
            for dep_id in step.depends_on:
                if dep_id not in step_ids:
                    return f"步骤{step.step_id}依赖的步骤{dep_id}不存在"

        # 检查循环依赖
        if self._has_circular_dependency(steps):
            return "检测到循环依赖"

        return None

    def _has_circular_dependency(self, steps: list[ChainStep]) -> bool:
        """检测循环依赖"""
        step_map = {s.step_id: s for s in steps}
        visited = set()
        rec_stack = set()

        def has_cycle(step_id: str) -> bool:
            visited.add(step_id)
            rec_stack.add(step_id)

            step = step_map.get(step_id)
            if step:
                for dep_id in step.depends_on:
                    if dep_id not in visited:
                        if has_cycle(dep_id):
                            return True
                    elif dep_id in rec_stack:
                        return True

            rec_stack.remove(step_id)
            return False

        return any(step_id not in visited and has_cycle(step_id) for step_id in step_map)

    def _check_dependencies(self, step: ChainStep, completed_steps: list[ChainStep]) -> bool:
        """检查依赖是否满足"""
        if not step.depends_on:
            return True

        completed_ids = {s.step_id for s in completed_steps}
        return all(dep_id in completed_ids for dep_id in step.depends_on)

    async def _execute_step(
        self, step: ChainStep, context: dict[str, Any], enable_retry: bool
    ) -> dict[str, Any]:
        """执行单个步骤"""
        step.start_time = datetime.now()
        step.status = ChainStatus.IN_PROGRESS

        # 初始化 timeout 变量,确保在异常处理中可用
        timeout = context.get(f"step_{step.step_id}_timeout", self.step_timeout)

        try:

            # 模拟工具执行(实际应该调用真实的工具)
            # 这里使用asyncio.sleep模拟
            await asyncio.sleep(0.1)  # 模拟执行时间

            # 实际实现中,这里应该调用:
            # result = await tool_registry[step.tool_name].execute(
            #     action=step.action,
            #     input_data=step.input_data,
            #     context=context
            # )

            # 模拟成功结果
            result = {
                "success": True,
                "output": {
                    "step_id": step.step_id,
                    "tool": step.tool_name,
                    "action": step.action,
                    "result": "执行成功",
                },
            }

            step.end_time = datetime.now()
            step.execution_time = (step.end_time - step.start_time).total_seconds()

            return result

        except asyncio.TimeoutError:
            step.end_time = datetime.now()
            step.execution_time = (step.end_time - step.start_time).total_seconds()
            return {"success": False, "error": f"步骤超时: {timeout}秒"}

        except Exception as e:
            step.end_time = datetime.now()
            step.execution_time = (step.end_time - step.start_time).total_seconds()
            return {"success": False, "error": str(e)}

    def _can_continue_after_failure(
        self, failed_step: ChainStep, all_steps: list[ChainStep]
    ) -> bool:
        """失败后是否可以继续"""
        # 简单策略: 如果后续步骤依赖失败的步骤,则不能继续
        return all(failed_step.step_id not in step.depends_on for step in all_steps)

    def _save_checkpoint(self, step: ChainStep, context: dict[str, Any]) -> Any:
        """保存检查点"""
        checkpoint = ChainCheckpoint(
            checkpoint_id=f"{step.step_id}_{int(time.time())}",
            step_id=step.step_id,
            state=context.copy(),
        )

        self.checkpoints[checkpoint.checkpoint_id] = checkpoint
        logger.info(f"💾 保存检查点: {checkpoint.checkpoint_id}")

    def _load_checkpoint(self, steps: list[ChainStep]) -> ChainCheckpoint | None:
        """加载检查点"""
        # 简化实现: 返回最新的检查点
        if not self.checkpoints:
            return None

        latest = max(self.checkpoints.values(), key=lambda c: c.timestamp)
        return latest

    def _extract_final_output(self, completed_steps: list[ChainStep]) -> Optional[dict[str, Any]]:
        """提取最终输出"""
        if not completed_steps:
            return None

        # 使用最后一个步骤的输出
        last_step = completed_steps[-1]
        return last_step.output_data

    def _update_stats(self, result: ChainResult) -> Any:
        """更新统计信息"""
        self.stats["total_executions"] += 1

        if result.success:
            self.stats["successful_executions"] += 1
        else:
            self.stats["failed_executions"] += 1

        self.stats["total_retries"] += sum(result.retry_summary.values())

        # 更新平均执行时间
        n = self.stats["total_executions"]
        old_avg = self.stats["avg_execution_time"]
        self.stats["avg_execution_time"] = (old_avg * (n - 1) + result.total_execution_time) / n

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()

    def clear_checkpoints(self) -> None:
        """清除检查点"""
        self.checkpoints.clear()
        logger.info("🗑️ 检查点已清除")


# 全局实例
_executor_instance: CascadeExecutor | None = None


def get_cascade_executor() -> CascadeExecutor:
    """获取级联执行器单例"""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = CascadeExecutor()
    return _executor_instance


# 工具函数
def create_step(
    step_id: str,
    tool_name: str,
    action: str,
    input_data: dict[str, Any],    depends_on: Optional[list[str]] = None,
) -> ChainStep:
    """创建链路步骤"""
    return ChainStep(
        step_id=step_id,
        tool_name=tool_name,
        action=action,
        input_data=input_data,
        depends_on=depends_on or [],
    )
