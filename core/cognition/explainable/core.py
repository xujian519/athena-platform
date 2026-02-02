#!/usr/bin/env python3
"""
可解释认知模块 - 核心功能
Explainable Cognition Module - Core Functionality

核心认知处理逻辑和推理管理

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-26
版本: 2.1.0
"""

import uuid
from datetime import datetime
from typing import Any

from core.base_module import BaseModule
from core.logging_config import setup_logging
from core.cognition.explainable.types import (
    DecisionFactor,
    FactorImportance,
    ReasoningPath,
    ReasoningStep,
    ReasoningStepType,
)
from core.cognition.explainable.visualizer import ReasoningPathVisualizer

logger = setup_logging()


class ExplainableCognitionModule(BaseModule):
    """可解释认知模块 - 重构版本"""

    def __init__(self, agent_id: str, config: dict[str, Any] | None = None):
        super().__init__(agent_id, config)

        # 可解释性配置
        self.explainability_config = {
            "track_reasoning_path": True,
            "capture_decision_factors": True,
            "enable_visualization": True,
            "max_reasoning_depth": 10,
            "factor_analysis_enabled": True,
            "explanation_level": "detailed",
            "counterfactual_analysis": True,
            **self.config,
        }

        # 初始化组件
        self.reasoning_paths: dict[str, ReasoningPath] = {}
        self.path_visualizer = ReasoningPathVisualizer(self.explainability_config)

        # 统计信息
        self.explainability_stats = {
            "total_reasoning_paths": 0,
            "average_path_length": 0.0,
            "factor_analysis_count": 0,
            "visualization_count": 0,
            "explanation_requests": 0,
            "counterfactual_analysis_count": 0,
        }

        logger.info("🧠 可解释认知模块初始化完成")

    async def _on_initialize(self) -> bool:
        """初始化可解释认知模块"""
        try:
            logger.info("✅ 可解释认知模块初始化成功")
            return True
        except Exception as e:
            logger.error(f"❌ 可解释认知模块初始化失败: {e}")
            return False

    async def _on_start(self) -> bool:
        """启动可解释认知模块"""
        logger.info("🚀 可解释认知模块启动")
        return True

    async def _on_stop(self) -> bool:
        """停止可解释认知模块"""
        logger.info("✅ 可解释认知模块停止成功")
        return True

    async def _on_shutdown(self) -> bool:
        """关闭可解释认知模块"""
        logger.info("✅ 可解释认知模块关闭成功")
        return True

    async def _on_health_check(self) -> bool:
        """健康检查"""
        try:
            checks = {
                "visualization_enabled": self.explainability_config.get("enable_visualization"),
                "path_tracking_active": self.explainability_config.get("track_reasoning_path"),
                "memory_usage_ok": self._check_memory_usage(),
                "statistics_available": len(self.explainability_stats) > 0,
            }

            overall_healthy = all(checks.values())
            return overall_healthy
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return False

    def create_reasoning_path(self, query: str) -> ReasoningPath:
        """创建新的推理路径"""
        path_id = str(uuid.uuid4())
        path = ReasoningPath(
            path_id=path_id,
            query=query,
            start_time=datetime.now(),
        )
        self.reasoning_paths[path_id] = path
        self.explainability_stats["total_reasoning_paths"] += 1
        return path

    def add_reasoning_step(
        self,
        path_id: str,
        step_type: ReasoningStepType,
        description: str,
        input_data: dict[str, Any],        output_data: dict[str, Any],        confidence: float,
        execution_time: float,
    ) -> ReasoningStep:
        """添加推理步骤"""
        if path_id not in self.reasoning_paths:
            logger.error(f"推理路径 {path_id} 不存在")
            raise ValueError(f"推理路径 {path_id} 不存在")

        step = ReasoningStep(
            step_id=str(uuid.uuid4()),
            step_type=step_type,
            description=description,
            input_data=input_data,
            output_data=output_data,
            confidence=confidence,
            timestamp=datetime.now(),
            execution_time=execution_time,
        )

        self.reasoning_paths[path_id].add_step(step)
        return step

    def add_decision_factor(
        self,
        path_id: str,
        step_id: str,
        name: str,
        description: str,
        importance: FactorImportance,
        weight: float,
        value: Any,
        source: str,
        uncertainty: float = 0.0,
    ) -> DecisionFactor:
        """添加决策因子"""
        if path_id not in self.reasoning_paths:
            logger.error(f"推理路径 {path_id} 不存在")
            raise ValueError(f"推理路径 {path_id} 不存在")

        factor = DecisionFactor(
            factor_id=str(uuid.uuid4()),
            name=name,
            description=description,
            importance=importance,
            weight=weight,
            value=value,
            source=source,
            uncertainty=uncertainty,
        )

        # 查找对应的步骤并添加因子
        for step in self.reasoning_paths[path_id].steps:
            if step.step_id == step_id:
                step.factors.append(factor)
                break

        self.explainability_stats["factor_analysis_count"] += 1
        return factor

    def complete_reasoning_path(
        self,
        path_id: str,
        final_decision: dict[str, Any],        overall_confidence: float,
        explanation: str,
    ) -> ReasoningPath:
        """完成推理路径"""
        if path_id not in self.reasoning_paths:
            logger.error(f"推理路径 {path_id} 不存在")
            raise ValueError(f"推理路径 {path_id} 不存在")

        path = self.reasoning_paths[path_id]
        path.end_time = datetime.now()
        path.final_decision = final_decision
        path.overall_confidence = overall_confidence
        path.explanation = explanation

        # 更新统计
        avg_length = sum(len(p.steps) for p in self.reasoning_paths.values()) / len(
            self.reasoning_paths
        )
        self.explainability_stats["average_path_length"] = avg_length

        return path

    def generate_path_visualization(self, path_id: str) -> str:
        """生成推理路径可视化"""
        if path_id not in self.reasoning_paths:
            logger.error(f"推理路径 {path_id} 不存在")
            return ""

        if not self.explainability_config.get("enable_visualization"):
            logger.warning("可视化功能未启用")
            return ""

        path = self.reasoning_paths[path_id]
        image_base64 = self.path_visualizer.generate_path_diagram(path)

        if image_base64:
            self.explainability_stats["visualization_count"] += 1

        return image_base64

    def get_reasoning_path(self, path_id: str) -> ReasoningPath | None:
        """获取推理路径"""
        return self.reasoning_paths.get(path_id)

    def get_all_reasoning_paths(self) -> dict[str, ReasoningPath]:
        """获取所有推理路径"""
        return self.reasoning_paths.copy()

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return self.explainability_stats.copy()

    def _check_memory_usage(self) -> bool:
        """检查内存使用情况"""
        try:
            import psutil

            process = psutil.Process()
            memory_percent = process.memory_info().rss / 1024 / 1024  # MB
            return memory_percent < 1000  # 小于1GB
        except Exception:
            return True  # 如果无法检查，假设正常
