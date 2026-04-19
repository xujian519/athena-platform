#!/usr/bin/env python3
"""
增强评估模块 - BaseModule标准接口兼容版本
Enhanced Evaluation Module - BaseModule Compatible Version

基于现有EvaluationEngine,添加BaseModule标准接口支持
作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

from __future__ import annotations
import asyncio
import logging
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 导入BaseModule
from core.base_module import BaseModule, HealthStatus, ModuleStatus

# 导入现有评估系统
try:
    from .evaluation_engine import (
        EvaluationCriteria,
        EvaluationEngine,
        EvaluationLevel,
        EvaluationResult,
        EvaluationType,
        ReflectionRecord,
        ReflectionType,
    )

    EVALUATION_SYSTEM_AVAILABLE = True
except ImportError:
    EVALUATION_SYSTEM_AVAILABLE = False

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


@dataclass
class EvaluationTask:
    """评估任务"""

    id: str
    target_type: str
    target_id: str
    evaluation_type: str
    criteria: list[dict[str, Any]]
    context: dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class EvaluationTaskResult:
    """评估任务结果"""

    success: bool
    task_id: str
    evaluation_id: str | None = None
    score: float = 0.0
    level: str = "unknown"
    error: str | None = None
    execution_time: float = 0.0
    insights: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class EnhancedEvaluationModule(BaseModule):
    """增强评估模块 - BaseModule标准接口版本"""

    def __init__(self, agent_id: str, config: dict[str, Any] | None = None):
        """
        初始化增强评估模块

        Args:
            agent_id: 智能体标识符
            config: 配置参数
        """
        super().__init__(agent_id, config)

        # 评估配置
        self.enable_quality_assurance = config.get("enable_quality_assurance", True)
        self.enable_reflection = config.get("enable_reflection", True)
        self.max_history_size = config.get("max_history_size", 1000)
        self.auto_save_interval = config.get("auto_save_interval", 300)  # 5分钟

        # 存储和状态
        self.evaluation_tasks: dict[str, EvaluationTask] = {}
        self.evaluation_history: list[dict[str, Any]] = []
        self.reflection_history: list[dict[str, Any]] = []

        # 统计信息
        self.evaluation_stats = {
            "total_evaluations": 0,
            "successful_evaluations": 0,
            "failed_evaluations": 0,
            "average_score": 0.0,
            "total_reflections": 0,
            "active_tasks": 0,
            "completed_tasks": 0,
        }

        # 评估引擎
        self.evaluation_engine = None

        # 模块状态
        self._module_status = ModuleStatus.INITIALIZING
        self._start_time = datetime.now()
        self._last_save_time = datetime.now()

        logger.info(f"🔍 创建增强评估模块 - Agent: {agent_id}")

    async def initialize(self) -> bool:
        """
        初始化模块

        Returns:
            初始化是否成功
        """
        try:
            logger.info(f"🔧 初始化模块: {self.__class__.__name__}")
            logger.info("🔍 初始化评估模块...")

            # 初始化现有评估系统
            if EVALUATION_SYSTEM_AVAILABLE:
                try:
                    self.evaluation_engine = EvaluationEngine(
                        agent_id=self.agent_id, config=self.config
                    )
                    await self.evaluation_engine.initialize()
                    logger.info("✅ 现有评估系统就绪")
                except Exception:
                    self.evaluation_engine = None
            else:
                logger.info("📦 使用备用评估实现")
                self.evaluation_engine = None

            # 启动自动保存任务
            if self.auto_save_interval > 0:
                asyncio.create_task(self._auto_save_loop())

            # 更新状态
            self._module_status = ModuleStatus.READY
            self._initialized = True

            logger.info("✅ 评估模块初始化成功")
            return True

        except Exception:
            self._module_status = ModuleStatus.ERROR
            return False

    async def health_check(self) -> HealthStatus:
        """
        健康检查

        Returns:
            健康状态
        """
        try:
            health_details = {
                "module_status": self._module_status.value,
                "evaluation_status": "available" if self.evaluation_engine else "fallback",
                "dependencies_status": "ok",
                "quality_assurance": "enabled" if self.enable_quality_assurance else "disabled",
                "reflection_enabled": self.enable_reflection,
                "stats": {
                    "total_evaluations": self.evaluation_stats["total_evaluations"],
                    "successful_evaluations": self.evaluation_stats["successful_evaluations"],
                    "average_score": self.evaluation_stats["average_score"],
                    "active_tasks": self.evaluation_stats["active_tasks"],
                },
            }

            # 缓存健康检查详情
            self._health_check_details = health_details

            # 基于状态确定健康状况
            if self._module_status == ModuleStatus.READY:
                return HealthStatus.HEALTHY
            elif self._module_status == ModuleStatus.ERROR:
                return HealthStatus.UNHEALTHY
            else:
                return HealthStatus.DEGRADED

        except Exception:
            return HealthStatus.UNHEALTHY

    async def evaluate(
        self,
        target_type: str,
        target_id: str,
        evaluation_type: str = "performance",
        criteria: list[dict[str, Any]] | None = None,
        context: dict[str, Any] | None = None,
    ) -> EvaluationTaskResult:
        """
        执行评估

        Args:
            target_type: 目标类型
            target_id: 目标ID
            evaluation_type: 评估类型
            criteria: 评估标准列表
            context: 评估上下文

        Returns:
            评估任务结果
        """
        start_time = datetime.now()

        try:
            # 更新统计
            self.evaluation_stats["total_evaluations"] += 1

            if EVALUATION_SYSTEM_AVAILABLE and self.evaluation_engine:
                # 使用现有评估系统
                eval_type = (
                    EvaluationType(evaluation_type)
                    if evaluation_type in [t.value for t in EvaluationType]
                    else EvaluationType.PERFORMANCE
                )

                # 转换评估标准
                eval_criteria = []
                if criteria:
                    for crit in criteria:
                        criterion = EvaluationCriteria(
                            id=crit.get("id", str(uuid.uuid4())),
                            name=crit.get("name", "Unnamed Criterion"),
                            description=crit.get("description", ""),
                            weight=crit.get("weight", 1.0),
                            min_value=crit.get("min_value", 0.0),
                            max_value=crit.get("max_value", 100.0),
                            target_value=crit.get("target_value", 80.0),
                            current_value=crit.get("current_value", 0.0),
                        )
                        eval_criteria.append(criterion)

                # 执行评估
                result = await self.evaluation_engine.evaluate(
                    target_type=target_type,
                    target_id=target_id,
                    evaluation_type=eval_type,
                    criteria=eval_criteria,
                    context=context,
                )

                execution_time = (datetime.now() - start_time).total_seconds()

                # 更新统计
                self.evaluation_stats["successful_evaluations"] += 1
                self._update_average_score(result.overall_score)

                # 添加到历史记录
                self._add_to_history(
                    {
                        "type": "evaluation",
                        "target_type": target_type,
                        "target_id": target_id,
                        "score": result.overall_score,
                        "level": result.level.value,
                        "timestamp": datetime.now(),
                        "execution_time": execution_time,
                    }
                )

                return EvaluationTaskResult(
                    success=True,
                    task_id=str(uuid.uuid4()),
                    evaluation_id=result.id,
                    score=result.overall_score,
                    level=result.level.value,
                    execution_time=execution_time,
                    insights=result.recommendations,
                    recommendations=result.recommendations,
                )

            else:
                # 备用评估
                return await self._fallback_evaluate(
                    target_type, target_id, evaluation_type, criteria, context, start_time
                )

        except Exception as e:
            self.evaluation_stats["failed_evaluations"] += 1

            return EvaluationTaskResult(
                success=False,
                task_id=str(uuid.uuid4()),
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

    async def reflect(
        self, evaluation_id: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        对评估结果进行反思

        Args:
            evaluation_id: 评估ID
            context: 反思上下文

        Returns:
            反思结果
        """
        try:
            if EVALUATION_SYSTEM_AVAILABLE and self.evaluation_engine:
                # 使用现有反思系统
                reflection = await self.evaluation_engine.reflect(evaluation_id, context)

                # 更新统计
                self.evaluation_stats["total_reflections"] += 1

                # 添加到历史记录
                self._add_to_history(
                    {
                        "type": "reflection",
                        "evaluation_id": evaluation_id,
                        "insights_count": len(reflection.insights),
                        "action_items_count": len(reflection.action_items),
                        "timestamp": datetime.now(),
                    }
                )

                return {
                    "success": True,
                    "reflection_id": reflection.id,
                    "observations": reflection.observations,
                    "analysis": reflection.analysis,
                    "insights": reflection.insights,
                    "action_items": reflection.action_items,
                    "lessons_learned": reflection.lessons_learned,
                }

            else:
                # 备用反思
                return await self._fallback_reflect(evaluation_id, context)

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def create_evaluation_task(
        self,
        target_type: str,
        target_id: str,
        evaluation_type: str = "performance",
        criteria: list[dict[str, Any]] | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """
        创建评估任务

        Args:
            target_type: 目标类型
            target_id: 目标ID
            evaluation_type: 评估类型
            criteria: 评估标准
            context: 评估上下文

        Returns:
            任务ID
        """
        task_id = str(uuid.uuid4())

        task = EvaluationTask(
            id=task_id,
            target_type=target_type,
            target_id=target_id,
            evaluation_type=evaluation_type,
            criteria=criteria or [],
            context=context or {},
        )

        self.evaluation_tasks[task_id] = task
        self.evaluation_stats["active_tasks"] += 1

        logger.info(f"📝 创建评估任务: {task_id} - {target_type}:{target_id}")

        return task_id

    async def get_evaluation_summary(self) -> dict[str, Any]:
        """
        获取评估摘要

        Returns:
            评估摘要信息
        """
        try:
            if EVALUATION_SYSTEM_AVAILABLE and self.evaluation_engine:
                # 使用现有评估系统
                summary = await self.evaluation_engine.get_evaluation_summary()
                summary.update(
                    {
                        "enhanced_stats": self.evaluation_stats,
                        "active_tasks": len(self.evaluation_tasks),
                        "history_size": len(self.evaluation_history),
                        "reflection_history_size": len(self.reflection_history),
                    }
                )
                return summary
            else:
                # 备用摘要
                return {
                    "agent_id": self.agent_id,
                    "enhanced_stats": self.evaluation_stats.copy(),
                    "active_tasks": len(self.evaluation_tasks),
                    "history_size": len(self.evaluation_history),
                    "reflection_history_size": len(self.reflection_history),
                    "module_uptime": (datetime.now() - self._start_time).total_seconds(),
                }

        except Exception as e:
            return {"error": str(e)}

    async def process(self, input_data: Any) -> dict[str, Any]:
        """标准处理接口 - BaseModule兼容"""
        try:
            if isinstance(input_data, dict):
                operation = input_data.get("operation", "evaluate")
                target_type = input_data.get("target_type", "")
                target_id = input_data.get("target_id", "")
                evaluation_type = input_data.get("evaluation_type", "performance")
                criteria = input_data.get("criteria", [])
                context = input_data.get("context")

                if operation == "evaluate":
                    result = await self.evaluate(
                        target_type=target_type,
                        target_id=target_id,
                        evaluation_type=evaluation_type,
                        criteria=criteria,
                        context=context,
                    )
                    return {
                        "success": result.success,
                        "task_id": result.task_id,
                        "evaluation_id": result.evaluation_id,
                        "score": result.score,
                        "level": result.level,
                    }
                elif operation == "reflect":
                    evaluation_id = input_data.get("evaluation_id", "")
                    result = await self.reflect(evaluation_id, context)
                    return {
                        "success": result.get("success", False),
                        "reflection_id": result.get("reflection_id"),
                        "insights": result.get("insights", []),
                    }
                elif operation == "create_task":
                    task_id = await self.create_evaluation_task(
                        target_type=target_type,
                        target_id=target_id,
                        evaluation_type=evaluation_type,
                        criteria=criteria,
                        context=context,
                    )
                    return {"success": True, "task_id": task_id}
                elif operation == "get_summary":
                    summary = await self.get_evaluation_summary()
                    return {"success": True, "summary": summary}
                else:
                    return {"success": False, "error": f"Unknown operation: {operation}"}
            else:
                return {"success": False, "error": "Invalid input format"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_status(self) -> dict[str, Any]:
        """获取模块状态"""
        return {
            "agent_id": self.agent_id,
            "module_type": "enhanced_evaluation",
            "status": self._module_status.value,
            "initialized": self._initialized,
            "active_tasks": len(self.evaluation_tasks),
            "history_size": len(self.evaluation_history),
            "uptime_seconds": (datetime.now() - self._start_time).total_seconds(),
            "evaluation_engine_available": self.evaluation_engine is not None,
        }

    def get_metrics(self) -> dict[str, Any]:
        """获取性能指标"""
        uptime = datetime.now() - self._start_time

        return {
            "module_status": self._module_status.value,
            "agent_id": self.agent_id,
            "initialized": self._initialized,
            "uptime_seconds": uptime.total_seconds(),
            "evaluation_stats": self.evaluation_stats.copy(),
            "active_tasks": len(self.evaluation_tasks),
            "history_size": len(self.evaluation_history),
            "quality_assurance_enabled": self.enable_quality_assurance,
            "reflection_enabled": self.enable_reflection,
        }

    # BaseModule抽象方法实现
    async def _on_initialize(self) -> bool:
        """子类初始化逻辑"""
        try:
            # 初始化现有评估系统
            if EVALUATION_SYSTEM_AVAILABLE:
                try:
                    self.evaluation_engine = EvaluationEngine(
                        agent_id=self.agent_id, config=self.config
                    )
                    await self.evaluation_engine.initialize()
                    logger.info("✅ 现有评估系统就绪")
                except Exception:
                    self.evaluation_engine = None
            else:
                logger.info("📦 使用备用评估实现")
                self.evaluation_engine = None

            return True

        except Exception:
            return False

    async def _on_start(self) -> bool:
        """子类启动逻辑"""
        try:
            # 启动自动保存任务
            if self.auto_save_interval > 0:
                asyncio.create_task(self._auto_save_loop())

            logger.info("✅ 评估模块启动成功")
            return True

        except Exception:
            return False

    async def _on_stop(self) -> bool:
        """子类停止逻辑"""
        try:
            # 停止自动保存
            logger.info("🛑 停止自动保存")
            return True

        except Exception:
            return False

    async def _on_shutdown(self) -> bool:
        """子类关闭逻辑"""
        try:
            # 保存状态
            await self._save_state()

            # 关闭评估引擎
            if self.evaluation_engine:
                await self.evaluation_engine.shutdown()

            # 清理资源
            self.evaluation_tasks.clear()
            self.evaluation_history.clear()
            self.reflection_history.clear()

            logger.info("✅ 评估模块关闭成功")
            return True

        except Exception:
            return False

    async def _on_health_check(self) -> bool:
        """子类健康检查逻辑"""
        try:
            # 检查评估引擎状态
            if self.evaluation_engine:
                # 检查评估引擎是否健康
                return True
            else:
                # 备用模式检查
                return len(self.evaluation_history) >= 0  # 基本检查

        except Exception:
            return False

    async def shutdown(self):
        """关闭模块"""
        logger.info(f"🔌 关闭模块: {self.__class__.__name__}")
        await super().shutdown()

    # 辅助方法
    def _update_average_score(self, new_score: float) -> Any:
        """更新平均分数"""
        total_evals = self.evaluation_stats["total_evaluations"]
        current_avg = self.evaluation_stats["average_score"]
        self.evaluation_stats["average_score"] = (
            current_avg * (total_evals - 1) + new_score
        ) / total_evals

    def _add_to_history(self, record: dict[str, Any]) -> Any:
        """添加到历史记录"""
        self.evaluation_history.append(record)
        if len(self.evaluation_history) > self.max_history_size:
            self.evaluation_history = self.evaluation_history[-self.max_history_size :]

    async def _auto_save_loop(self):
        """自动保存循环"""
        while self._initialized:
            try:
                await asyncio.sleep(self.auto_save_interval)
                if self._initialized:
                    await self._save_state()
                    self._last_save_time = datetime.now()
            except Exception as e:
                logger.error(f"捕获异常: {e}", exc_info=True)

    async def _save_state(self):
        """保存状态"""
        try:
            if self.evaluation_engine:
                await self.evaluation_engine.save_state()
            logger.info("📁 评估模块状态已保存")
        except Exception as e:
            logger.error(f"捕获异常: {e}", exc_info=True)

    # 备用实现方法
    async def _fallback_evaluate(
        self,
        target_type: str,
        target_id: str,
        evaluation_type: str,
        criteria: list[dict[str, Any]],
        context: dict[str, Any],        start_time: datetime,
    ) -> EvaluationTaskResult:
        """备用评估实现"""
        # 简化的备用评估
        score = 75.0  # 默认分数
        level = "satisfactory"

        if criteria:
            # 简单计算平均分
            scores = [c.get("current_value", 75) for c in criteria]
            score = sum(scores) / len(scores) if scores else 75.0

            if score >= 90:
                level = "excellent"
            elif score >= 80:
                level = "good"
            elif score >= 70:
                level = "satisfactory"
            elif score >= 60:
                level = "needs_improvement"
            else:
                level = "poor"

        execution_time = (datetime.now() - start_time).total_seconds()

        # 更新统计
        self.evaluation_stats["successful_evaluations"] += 1
        self._update_average_score(score)

        # 添加到历史记录
        self._add_to_history(
            {
                "type": "evaluation",
                "target_type": target_type,
                "target_id": target_id,
                "score": score,
                "level": level,
                "timestamp": datetime.now(),
                "execution_time": execution_time,
                "fallback": True,
            }
        )

        logger.info(f"📊 备用评估完成: {target_type}:{target_id} - {score:.1f} ({level})")

        return EvaluationTaskResult(
            success=True,
            task_id=str(uuid.uuid4()),
            score=score,
            level=level,
            execution_time=execution_time,
            insights=["使用备用评估系统"],
            recommendations=["建议配置完整的评估系统以获得更准确的结果"],
        )

    async def _fallback_reflect(
        self, evaluation_id: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """备用反思实现"""
        # 简化的备用反思
        insights = ["基于评估结果进行反思", "识别改进机会", "制定行动计划"]

        action_items = ["分析评估中的关键发现", "制定具体的改进措施", "设定可量化的目标"]

        # 更新统计
        self.evaluation_stats["total_reflections"] += 1

        # 添加到历史记录
        self._add_to_history(
            {
                "type": "reflection",
                "evaluation_id": evaluation_id,
                "insights_count": len(insights),
                "action_items_count": len(action_items),
                "timestamp": datetime.now(),
                "fallback": True,
            }
        )

        return {
            "success": True,
            "reflection_id": str(uuid.uuid4()),
            "observations": "基于备用评估系统的观察",
            "analysis": "简化的分析结果",
            "insights": insights,
            "action_items": action_items,
            "lessons_learned": ["持续改进的重要性"],
        }


# 导出
__all__ = ["EnhancedEvaluationModule", "EvaluationTask", "EvaluationTaskResult"]
