#!/usr/bin/env python3
from __future__ import annotations
"""
自适应学习率优化器 (Adaptive Learning Rate Optimizer)
智能学习率调整,优化模型收敛速度和性能

作者: 小诺·双鱼公主
版本: v3.0.0
优化目标: 收敛速度提升 50%+, 最终性能提升 5%+
"""

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class LRScheduleType(str, Enum):
    """学习率调度类型"""

    CONSTANT = "constant"  # 常数学习率
    STEP = "step"  # 阶梯衰减
    EXPONENTIAL = "exponential"  # 指数衰减
    COSINE = "cosine"  # 余弦退火
    WARMUP_COSINE = "warmup_cosine"  # 预热+余弦退火
    CYCLIC = "cyclic"  # 循环学习率
    ONECYCLE = "onecycle"  # OneCycle策略
    ADAPTIVE = "adaptive"  # 自适应(基于性能)


class LRAdjustmentTrigger(str, Enum):
    """学习率调整触发条件"""

    EPOCH_END = "epoch_end"  # 每个epoch结束
    PLATEAU = "plateau"  # 性能平台期
    GRADIENT_NORM = "gradient_norm"  # 梯度范数
    LOSS_SPIKE = "loss_spike"  # 损失突增
    CUSTOM = "custom"  # 自定义触发


@dataclass
class LRState:
    """学习率状态"""

    current_lr: float
    initial_lr: float
    min_lr: float
    max_lr: float
    step: int = 0
    best_metric: float = 0.0
    patience_counter: int = 0
    history: list[float] = field(default_factory=list)


@dataclass
class LREvent:
    """学习率事件"""

    event_id: str
    trigger: LRAdjustmentTrigger
    old_lr: float
    new_lr: float
    reason: str
    metric_value: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ConvergenceMetrics:
    """收敛指标"""

    loss: float
    gradient_norm: float
    metric_value: float
    learning_rate: float
    step: int
    timestamp: datetime = field(default_factory=datetime.now)


class AdaptiveLROptimizer:
    """
    自适应学习率优化器

    功能:
    1. 多种学习率调度策略
    2. 自适应学习率调整
    3. 收敛监控
    4. 性能平台期检测
    5. 梯度分析
    """

    def __init__(
        self,
        initial_lr: float = 0.001,
        min_lr: float = 1e-7,
        max_lr: float = 1.0,
        schedule_type: LRScheduleType = LRScheduleType.WARMUP_COSINE,
    ):
        self.name = "自适应学习率优化器"
        self.version = "3.0.0"

        self.initial_lr = initial_lr
        self.min_lr = min_lr
        self.max_lr = max_lr
        self.schedule_type = schedule_type

        # 学习率状态
        self.lr_state = LRState(
            current_lr=initial_lr, initial_lr=initial_lr, min_lr=min_lr, max_lr=max_lr
        )

        # 学习率历史
        self.lr_history: deque = deque(maxlen=10000)

        # 收敛指标历史
        self.convergence_history: list[ConvergenceMetrics] = []

        # 学习率事件
        self.lr_events: list[LREvent] = []

        # 统计信息
        self.stats = {
            "total_adjustments": 0,
            "increases": 0,
            "decreases": 0,
            "plateau_detections": 0,
            "current_lr": initial_lr,
            "best_lr": initial_lr,
        }

        # Warmup配置
        self.warmup_steps = 1000
        self.warmup_start_lr = initial_lr * 0.1

        logger.info(
            f"✅ {self.name} 初始化完成 (初始LR: {initial_lr}, 策略: {schedule_type.value})"
        )

    async def compute_lr(self, step: int, metric_value: float | None = None) -> float:
        """
        计算当前学习率

        Args:
            step: 当前步数
            metric_value: 指标值(用于自适应调整)

        Returns:
            学习率
        """
        self.lr_state.step = step

        if self.schedule_type == LRScheduleType.CONSTANT:
            lr = self._constant_lr()
        elif self.schedule_type == LRScheduleType.STEP:
            lr = self._step_lr(step)
        elif self.schedule_type == LRScheduleType.EXPONENTIAL:
            lr = self._exponential_lr(step)
        elif self.schedule_type == LRScheduleType.COSINE:
            lr = self._cosine_lr(step)
        elif self.schedule_type == LRScheduleType.WARMUP_COSINE:
            lr = self._warmup_cosine_lr(step)
        elif self.schedule_type == LRScheduleType.CYCLIC:
            lr = self._cyclic_lr(step)
        elif self.schedule_type == LRScheduleType.ONECYCLE:
            lr = self._onecycle_lr(step)
        elif self.schedule_type == LRScheduleType.ADAPTIVE:
            lr = await self._adaptive_lr(step, metric_value)
        else:
            lr = self.initial_lr

        # 确保在范围内
        lr = max(self.min_lr, min(self.max_lr, lr))

        # 检查学习率变化
        if abs(lr - self.lr_state.current_lr) > 1e-9:
            await self._record_lr_change(self.lr_state.current_lr, lr, step)

        self.lr_state.current_lr = lr
        self.lr_history.append(lr)
        self.stats["current_lr"] = lr

        return lr

    def _constant_lr(self) -> float:
        """常数学习率"""
        return self.initial_lr

    def _step_lr(self, step: int, step_size: int = 10000, gamma: float = 0.1) -> float:
        """阶梯衰减"""
        return self.initial_lr * (gamma ** (step // step_size))

    def _exponential_lr(self, step: int, decay_rate: float = 0.96) -> float:
        """指数衰减"""
        return self.initial_lr * (decay_rate ** (step / 1000))

    def _cosine_lr(self, step: int, total_steps: int = 100000) -> float:
        """余弦退火"""
        return self.min_lr + 0.5 * (self.initial_lr - self.min_lr) * (
            1 + np.cos(np.pi * step / total_steps)
        )

    def _warmup_cosine_lr(self, step: int, total_steps: int = 100000) -> float:
        """预热+余弦退火"""
        if step < self.warmup_steps:
            # Warmup阶段
            return (
                self.warmup_start_lr
                + (self.initial_lr - self.warmup_start_lr) * step / self.warmup_steps
            )
        else:
            # 余弦退火阶段
            progress = (step - self.warmup_steps) / (total_steps - self.warmup_steps)
            return self.min_lr + 0.5 * (self.initial_lr - self.min_lr) * (
                1 + np.cos(np.pi * progress)
            )

    def _cyclic_lr(
        self, step: int, step_size_up: int = 2000, step_size_down: int | None = None
    ) -> float:
        """循环学习率"""
        step_size_down = step_size_down or step_size_up
        step // (step_size_up + step_size_down)
        step_in_cycle = step % (step_size_up + step_size_down)

        if step_in_cycle < step_size_up:
            # 上升阶段
            scale = step_in_cycle / step_size_up
        else:
            # 下降阶段
            scale = (step_size_up + step_size_down - step_in_cycle) / step_size_down

        return self.min_lr + (self.max_lr - self.min_lr) * scale

    def _onecycle_lr(self, step: int, total_steps: int = 100000, pct_start: float = 0.3) -> float:
        """OneCycle策略"""
        if step < total_steps * pct_start:
            # 上升阶段
            scale = step / (total_steps * pct_start)
            return self.min_lr + (self.max_lr - self.min_lr) * scale
        else:
            # 下降阶段
            remaining_steps = total_steps - total_steps * pct_start
            current_step = step - total_steps * pct_start
            scale = 1 - current_step / remaining_steps
            return self.min_lr + (self.max_lr - self.min_lr) * max(0, scale)

    async def _adaptive_lr(self, step: int, metric_value: float | None = None) -> float:
        """自适应学习率"""
        if metric_value is None:
            return self.lr_state.current_lr

        # 更新最佳指标
        if metric_value > self.lr_state.best_metric:
            self.lr_state.best_metric = metric_value
            self.lr_state.patience_counter = 0
            self.stats["best_lr"] = self.lr_state.current_lr
        else:
            self.lr_state.patience_counter += 1

        # 检测平台期
        if self.lr_state.patience_counter > 10:  # patience阈值
            self.stats["plateau_detections"] += 1

            # 降低学习率
            new_lr = self.lr_state.current_lr * 0.5

            await self._record_lr_event(
                LRAdjustmentTrigger.PLATEAU,
                self.lr_state.current_lr,
                new_lr,
                f"性能平台期 (patience={self.lr_state.patience_counter})",
                metric_value,
            )

            self.lr_state.patience_counter = 0
            return new_lr

        return self.lr_state.current_lr

    async def _record_lr_change(self, old_lr: float, new_lr: float, step: int):
        """记录学习率变化"""
        if new_lr > old_lr:
            self.stats["increases"] += 1
        else:
            self.stats["decreases"] += 1

        self.stats["total_adjustments"] += 1

        logger.debug(f"📊 LR变化: {old_lr:.6f} → {new_lr:.6f} (步数: {step})")

    async def _record_lr_event(
        self,
        trigger: LRAdjustmentTrigger,
        old_lr: float,
        new_lr: float,
        reason: str,
        metric_value: float = 0.0,
    ):
        """记录学习率事件"""
        event = LREvent(
            event_id=f"lr_event_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            trigger=trigger,
            old_lr=old_lr,
            new_lr=new_lr,
            reason=reason,
            metric_value=metric_value,
        )

        self.lr_events.append(event)

        logger.info(
            f"🎯 LR调整: {old_lr:.6f} → {new_lr:.6f} " f"(触发: {trigger.value}, 原因: {reason})"
        )

    async def update_with_gradient(
        self, step: int, loss: float, gradient_norm: float, metric_value: float | None = None
    ):
        """
        基于梯度更新学习率

        Args:
            step: 当前步数
            loss: 损失值
            gradient_norm: 梯度范数
            metric_value: 指标值
        """
        # 记录收敛指标
        metrics = ConvergenceMetrics(
            loss=loss,
            gradient_norm=gradient_norm,
            metric_value=metric_value or 0.0,
            learning_rate=self.lr_state.current_lr,
            step=step,
        )

        self.convergence_history.append(metrics)

        # 检测异常情况
        await self._detect_anomalies(metrics)

        # 更新学习率
        await self.compute_lr(step, metric_value)

    async def _detect_anomalies(self, metrics: ConvergenceMetrics):
        """检测异常情况"""
        if len(self.convergence_history) < 10:
            return

        recent = self.convergence_history[-10:]

        # 检测损失突增
        avg_loss = sum(m.loss for m in recent[:-1]) / (len(recent) - 1)
        if metrics.loss > avg_loss * 2:
            # 损失突增,降低学习率
            new_lr = self.lr_state.current_lr * 0.5

            await self._record_lr_event(
                LRAdjustmentTrigger.LOSS_SPIKE,
                self.lr_state.current_lr,
                new_lr,
                f"损失突增 ({metrics.loss:.4f} > {avg_loss:.4f})",
                metrics.metric_value,
            )

            self.lr_state.current_lr = new_lr

        # 检测梯度消失/爆炸
        avg_grad_norm = sum(m.gradient_norm for m in recent[:-1]) / (len(recent) - 1)

        if metrics.gradient_norm < avg_grad_norm * 0.1:
            # 梯度消失,增加学习率
            new_lr = min(self.max_lr, self.lr_state.current_lr * 1.5)

            await self._record_lr_event(
                LRAdjustmentTrigger.GRADIENT_NORM,
                self.lr_state.current_lr,
                new_lr,
                f"梯度消失 (范数: {metrics.gradient_norm:.6f})",
                metrics.metric_value,
            )

            self.lr_state.current_lr = new_lr

        elif metrics.gradient_norm > avg_grad_norm * 10:
            # 梯度爆炸,降低学习率
            new_lr = max(self.min_lr, self.lr_state.current_lr * 0.5)

            await self._record_lr_event(
                LRAdjustmentTrigger.GRADIENT_NORM,
                self.lr_state.current_lr,
                new_lr,
                f"梯度爆炸 (范数: {metrics.gradient_norm:.6f})",
                metrics.metric_value,
            )

            self.lr_state.current_lr = new_lr

    def get_lr_schedule(self, total_steps: int) -> list[float]:
        """
        获取完整学习率调度(同步版本)

        注意:此方法提供同步接口,直接计算调度而不依赖asyncio
        """
        schedule = []
        for step in range(total_steps):
            # 直接调用同步版本的LR计算
            self.lr_state.step = step

            if self.schedule_type == LRScheduleType.CONSTANT:
                lr = self._constant_lr()
            elif self.schedule_type == LRScheduleType.STEP:
                lr = self._step_lr(step)
            elif self.schedule_type == LRScheduleType.EXPONENTIAL:
                lr = self._exponential_lr(step)
            elif self.schedule_type == LRScheduleType.COSINE:
                lr = self._cosine_lr(step)
            elif self.schedule_type == LRScheduleType.WARMUP_COSINE:
                lr = self._warmup_cosine_lr(step)
            elif self.schedule_type == LRScheduleType.CYCLIC:
                lr = self._cyclic_lr(step)
            elif self.schedule_type == LRScheduleType.ONECYCLE:
                lr = self._onecycle_lr(step)
            else:
                # ADAPTIVE类型需要异步支持,这里使用当前LR
                lr = self.lr_state.current_lr

            # 确保在范围内
            lr = max(self.min_lr, min(self.max_lr, lr))
            schedule.append(lr)

        return schedule

    async def get_lr_schedule_async(self, total_steps: int) -> list[float]:
        """
        获取完整学习率调度(异步版本)

        支持ADAPTIVE类型的调度,需要在异步上下文中调用
        """
        schedule = []
        for step in range(total_steps):
            lr = await self.compute_lr(step)
            schedule.append(lr)
        return schedule

    def get_status(self) -> dict[str, Any]:
        """获取优化器状态"""
        # 计算最近趋势
        recent_lr = (
            list(self.lr_history)[-100:] if len(self.lr_history) >= 100 else list(self.lr_history)
        )

        return {
            "name": self.name,
            "version": self.version,
            "schedule_type": self.schedule_type.value,
            "current_lr": self.lr_state.current_lr,
            "lr_range": {"min": self.min_lr, "max": self.max_lr, "initial": self.initial_lr},
            "state": {
                "step": self.lr_state.step,
                "best_metric": self.lr_state.best_metric,
                "patience_counter": self.lr_state.patience_counter,
            },
            "statistics": self.stats,
            "recent_trend": {
                "mean": np.mean(recent_lr) if recent_lr else 0,
                "std": np.std(recent_lr) if recent_lr else 0,
                "min": min(recent_lr) if recent_lr else 0,
                "max": max(recent_lr) if recent_lr else 0,
            },
            "recent_events": [
                {
                    "trigger": e.trigger.value,
                    "old_lr": e.old_lr,
                    "new_lr": e.new_lr,
                    "reason": e.reason,
                }
                for e in self.lr_events[-10:]
            ],
            "convergence_info": {
                "history_size": len(self.convergence_history),
                "current_loss": (
                    self.convergence_history[-1].loss if self.convergence_history else None
                ),
                "current_gradient_norm": (
                    self.convergence_history[-1].gradient_norm if self.convergence_history else None
                ),
            },
        }


# 全局单例
_lr_optimizer_instance: AdaptiveLROptimizer | None = None


def get_adaptive_lr_optimizer() -> AdaptiveLROptimizer:
    """获取自适应学习率优化器实例"""
    global _lr_optimizer_instance
    if _lr_optimizer_instance is None:
        _lr_optimizer_instance = AdaptiveLROptimizer()
    return _lr_optimizer_instance
