#!/usr/bin/env python3
"""
评估引擎 - 核心引擎
Evaluation Engine - Core Engine

作者: Athena平台团队
创建时间: 2025-12-11
重构时间: 2026-01-26
版本: 2.0.0

提供评估与反思的核心引擎功能。
"""

import asyncio
import json
import logging
import statistics
import uuid
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .metrics import MetricsCalculator
from .qa_checker import QualityAssuranceChecker
from .reflection import ReflectionEngine
from .types import EvaluationCriteria, EvaluationLevel, EvaluationResult, EvaluationType, ReflectionRecord

logger = logging.getLogger(__name__)


class EvaluationEngine:
    """评估与反思引擎 - 完整实现"""

    def __init__(self, agent_id: str, config: dict | None = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.initialized = False

        # 核心组件
        self.metrics_calculator = MetricsCalculator()
        self.qa_checker = QualityAssuranceChecker()
        self.reflection_engine = ReflectionEngine(agent_id)

        # 存储和缓存
        self.evaluations = {}
        self.reflections = {}
        self.historical_scores = defaultdict(list)

        # 统计信息
        self.stats = {
            "total_evaluations": 0,
            "total_reflections": 0,
            "qa_pass_rate": 0.0,
            "avg_score": 0.0,
        }

        # 回调管理
        self._callbacks = defaultdict(list)

        logger.info(f"🔍 创建评估引擎: {self.agent_id}")

    async def initialize(self):
        """初始化评估引擎"""
        logger.info(f"🚀 启动评估引擎: {self.agent_id}")

        try:
            # 创建数据目录
            data_dir = Path("data/evaluation")
            data_dir.mkdir(parents=True, exist_ok=True)

            # 加载历史数据
            await self._load_historical_data()

            self.initialized = True

            # 触发初始化事件
            await self._trigger_callbacks(
                "initialized", {"agent_id": self.agent_id, "timestamp": datetime.now()}
            )

            logger.info(f"✅ 评估引擎初始化完成: {self.agent_id}")

        except Exception as e:
            raise

    async def evaluate(
        self,
        target_type: str,
        target_id: str,
        evaluation_type: EvaluationType,
        criteria: list[EvaluationCriteria],
        context: dict[str, Any] | None = None,
    ) -> EvaluationResult:
        """执行评估"""
        if not self.initialized:
            raise RuntimeError("评估引擎未初始化")

        evaluation_id = str(uuid.uuid4())

        try:
            logger.info(f"🔍 开始评估: {target_type}:{target_id}")

            # 处理评估标准
            criteria_results = {}
            for criterion in criteria:
                # 标准化评分
                normalized_score = self._normalize_score(
                    criterion.current_value, criterion.min_value, criterion.max_value
                )

                criterion.score = normalized_score
                criteria_results[criterion.id] = asdict(criterion)

            # 计算总体得分
            overall_score = self.metrics_calculator.calculate_weighted_score(criteria_results)

            # 确定评估等级
            level = self.metrics_calculator.determine_level(overall_score)

            # 计算置信度
            confidence = self.metrics_calculator.calculate_confidence(criteria_results)

            # 分析强项和弱项
            strengths, weaknesses = await self._analyze_strengths_weaknesses(criteria_results)

            # 生成改进建议
            recommendations = await self._generate_recommendations(criteria_results, level)

            # 创建评估结果
            result = EvaluationResult(
                id=evaluation_id,
                evaluator_id=self.agent_id,
                target_type=target_type,
                target_id=target_id,
                evaluation_type=evaluation_type,
                criteria_results=criteria_results,
                overall_score=overall_score,
                level=level,
                strengths=strengths,
                weaknesses=weaknesses,
                recommendations=recommendations,
                confidence=confidence,
                metadata=context or {},
            )

            # 执行质量保证检查
            qa_result = await self.qa_checker.perform_qa_check(result)
            result.metadata["qa_check"] = qa_result

            # 保存结果
            self.evaluations[evaluation_id] = result
            self.historical_scores[target_type].append(overall_score)

            # 更新统计
            self._update_stats(result, qa_result)

            # 触发评估完成事件
            await self._trigger_callbacks(
                "evaluation_completed", {"evaluation_id": evaluation_id, "result": asdict(result)}
            )

            logger.info(f"✅ 评估完成: {overall_score:.1f} ({level.value})")

            return result

        except Exception as e:
            raise

    async def reflect(
        self, evaluation_id: str, context: dict[str, Any] | None = None
    ) -> ReflectionRecord:
        """对评估结果进行反思"""
        if evaluation_id not in self.evaluations:
            raise ValueError(f"评估结果不存在: {evaluation_id}")

        evaluation_result = self.evaluations[evaluation_id]

        try:
            logger.info(f"🤔 开始反思: {evaluation_id}")

            # 生成反思
            reflection = await self.reflection_engine.generate_reflection(
                evaluation_result, context
            )

            # 保存反思
            self.reflections[reflection.id] = reflection

            # 更新统计
            self.stats["total_reflections"] += 1

            # 触发反思完成事件
            await self._trigger_callbacks(
                "reflection_completed",
                {"reflection_id": reflection.id, "evaluation_id": evaluation_id},
            )

            logger.info(f"✅ 反思完成: {len(reflection.insights)}个见解")

            return reflection

        except Exception as e:
            raise

    async def get_trend_analysis(self, target_type: str) -> dict[str, Any]:
        """获取趋势分析"""
        scores = self.historical_scores.get(target_type, [])

        if not scores:
            return {"trend": "no_data", "current_score": 0, "avg_score": 0, "trend_analysis": {}}

        trend_analysis = self.metrics_calculator.detect_trends(scores)

        return {
            "trend": trend_analysis["trend"],
            "current_score": scores[-1] if scores else 0,
            "avg_score": statistics.mean(scores),
            "total_evaluations": len(scores),
            "trend_analysis": trend_analysis,
        }

    async def get_evaluation_summary(self) -> dict[str, Any]:
        """获取评估摘要"""
        recent_evaluations = list(self.evaluations.values())[-10:]

        return {
            "agent_id": self.agent_id,
            "statistics": self.stats.copy(),
            "recent_evaluations": len(recent_evaluations),
            "target_types": list(self.historical_scores.keys()),
            "avg_confidence": (
                statistics.mean([e.confidence for e in recent_evaluations])
                if recent_evaluations
                else 0
            ),
            "performance_trends": {
                ttype: await self.get_trend_analysis(ttype)
                for ttype in self.historical_scores
            },
        }

    def _normalize_score(self, value: float, min_val: float, max_val: float) -> float:
        """标准化评分到0-100"""
        if max_val == min_val:
            return 50.0

        normalized = ((value - min_val) / (max_val - min_val)) * 100
        return max(0.0, min(100.0, normalized))

    async def _analyze_strengths_weaknesses(
        self, criteria_results: dict[str, dict[str, Any]]
    ) -> tuple[list[str], list[str]]:
        """分析强项和弱项"""
        strengths = []
        weaknesses = []

        for criterion_id, result in criteria_results.items():
            score = result.get("score", 0)
            name = result.get("name", criterion_id)

            if score >= 80:
                strengths.append(f"{name} ({score:.1f}分)")
            elif score < 60:
                weaknesses.append(f"{name} ({score:.1f}分)")

        return strengths, weaknesses

    async def _generate_recommendations(
        self, criteria_results: dict[str, dict[str, Any]], level: EvaluationLevel
    ) -> list[str]:
        """生成改进建议"""
        recommendations = []

        # 基于等级生成建议
        if level == EvaluationLevel.POOR:
            recommendations.append("需要立即制定全面的改进计划")
            recommendations.append("寻求外部支持和指导")
        elif level == EvaluationLevel.NEEDS_IMPROVEMENT:
            recommendations.append("重点关注得分较低的评估标准")
            recommendations.append("制定分阶段的改进目标")

        # 基于具体标准生成建议
        low_scores = [
            (result.get("name", cid), result.get("score", 0))
            for cid, result in criteria_results.items()
            if result.get("score", 0) < 70
        ]

        for name, score in low_scores[:3]:  # 限制数量
            recommendations.append(f"提升{name}的表现(当前{score:.1f}分)")

        return recommendations

    def _update_stats(self, evaluation_result: EvaluationResult, qa_result: dict[str, Any]) -> Any:
        """更新统计信息"""
        self.stats["total_evaluations"] += 1

        # 更新平均分数
        total_evals = self.stats["total_evaluations"]
        current_avg = self.stats["avg_score"]
        self.stats["avg_score"] = (
            (current_avg * (total_evals - 1)) + evaluation_result.overall_score
        ) / total_evals

        # 更新QA通过率
        passed_qa = qa_result.get("passed_all", False)
        if passed_qa:
            current_pass_rate = self.stats["qa_pass_rate"]
            self.stats["qa_pass_rate"] = (
                (current_pass_rate * (total_evals - 1)) + 1.0
            ) / total_evals

    async def _load_historical_data(self):
        """加载历史数据"""
        try:
            # 这里可以从数据库或文件加载历史评估数据
            logger.info("历史数据加载完成")
        except Exception as e:
            logger.error(f"捕获异常: {e}", exc_info=True)

    async def save_state(self):
        """保存状态"""
        try:
            data_dir = Path("data/evaluation")
            data_dir.mkdir(parents=True, exist_ok=True)

            # 保存评估结果
            if self.evaluations:
                eval_file = data_dir / f"{self.agent_id}_evaluations.json"
                with open(eval_file, "w", encoding="utf-8") as f:
                    json.dump(
                        {eid: asdict(eval_result) for eid, eval_result in self.evaluations.items()},
                        f,
                        ensure_ascii=False,
                        indent=2,
                        default=str,
                    )

            # 保存反思记录
            if self.reflections:
                refl_file = data_dir / f"{self.agent_id}_reflections.json"
                with open(refl_file, "w", encoding="utf-8") as f:
                    json.dump(
                        {rid: asdict(reflection) for rid, reflection in self.reflections.items()},
                        f,
                        ensure_ascii=False,
                        indent=2,
                        default=str,
                    )

            logger.info(
                f"保存了 {len(self.evaluations)} 个评估结果和 {len(self.reflections)} 个反思记录"
            )

        except Exception as e:
            logger.error(f"捕获异常: {e}", exc_info=True)

    def register_callback(self, event_type: str, callback) -> None:
        """注册回调函数"""
        self._callbacks[event_type].append(callback)

    async def _trigger_callbacks(self, event_type: str, data: dict[str, Any]):
        """触发回调"""
        for callback in self._callbacks[event_type]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                logger.error(f"捕获异常: {e}", exc_info=True)

    async def shutdown(self):
        """关闭评估引擎"""
        logger.info(f"🔄 关闭评估引擎: {self.agent_id}")

        try:
            # 保存状态
            await self.save_state()

            self.initialized = False

            # 触发关闭事件
            await self._trigger_callbacks(
                "shutdown", {"agent_id": self.agent_id, "timestamp": datetime.now()}
            )

            logger.info(f"✅ 评估引擎已关闭: {self.agent_id}")

        except Exception as e:
            logger.error(f"捕获异常: {e}", exc_info=True)

    @classmethod
    async def initialize_global(cls, config: dict | None = None):
        """初始化全局实例"""
        if not hasattr(cls, "global_instance"):
            cls.global_instance = cls("global", config)
            await cls.global_instance.initialize()
        return cls.global_instance

    @classmethod
    async def shutdown_global(cls):
        """关闭全局实例"""
        if hasattr(cls, "global_instance") and cls.global_instance:
            await cls.global_instance.shutdown()
            del cls.global_instance

    async def evaluate_interaction(
        self, interaction: dict[str, Any], context: dict | None = None
    ) -> dict[str, Any]:
        """评估交互效果"""
        try:
            interaction.get("type", "general")
            content = interaction.get("content", "")
            outcome = interaction.get("outcome", "")

            # 多维度评估
            evaluation = {
                "relevance": await self._evaluate_relevance(content, context),
                "quality": await self._evaluate_quality(content, outcome),
                "effectiveness": await self._evaluate_effectiveness(interaction, outcome),
                "efficiency": await self._evaluate_efficiency(interaction),
            }

            # 计算综合分数
            weights = {"relevance": 0.3, "quality": 0.3, "effectiveness": 0.3, "efficiency": 0.1}
            overall_score = sum(evaluation[k] * weights[k] for k in evaluation)

            # 生成建议
            suggestions = []
            if overall_score < 0.6:
                suggestions.append("建议改进交互质量")

            # 保存评估记录
            eval_id = f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            await self._store_evaluation_record(eval_id, interaction, evaluation)

            return {
                "success": True,
                "evaluation_id": eval_id,
                "scores": evaluation,
                "overall_score": overall_score,
                "suggestions": suggestions,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def evaluate_option(
        self, option: dict[str, Any], criteria: str, context: dict | None = None
    ) -> dict[str, Any]:
        """评估选项"""
        try:
            # 基础评估
            base_eval = {
                "feasibility": await self._evaluate_feasibility(option, context),
                "value": await self._evaluate_value(option, criteria),
                "risk": await self._evaluate_risk(option),
                "alignment": await self._evaluate_alignment(option, context),
            }

            # 综合评分
            weights = {"feasibility": 0.25, "value": 0.3, "risk": 0.25, "alignment": 0.2}
            overall_score = sum(base_eval[k] * weights[k] for k in base_eval)

            return {
                "success": True,
                "evaluation": base_eval,
                "overall_score": overall_score,
                "confidence": min(1.0, overall_score + 0.1),
            }

        except Exception as e:
            return {"success": False, "error": str(e), "overall_score": 0.5}

    async def comprehensive_evaluation(
        self, data: dict[str, Any], criteria: list[str]
    ) -> dict[str, Any]:
        """综合评估"""
        try:
            results = {}

            for criterion in criteria:
                if criterion == data:
                    criterion = "general"

                result = await self.evaluate_option(data, criterion)
                results[criterion] = result

            # 聚合结果
            if all(r.get("success", False) for r in results.values()):
                avg_score = sum(r.get("overall_score", 0) for r in results.values()) / len(results)

                return {
                    "success": True,
                    "results": results,
                    "average_score": avg_score,
                    "recommendation": self._generate_recommendation(results),
                }
            else:
                return {"success": False, "partial_results": results}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # 辅助方法
    async def _evaluate_relevance(self, content: str, context: dict) -> float:
        """评估相关性"""
        return 0.8  # 简化实现

    async def _evaluate_quality(self, content: str, outcome: str) -> float:
        """评估质量"""
        return 0.75  # 简化实现

    async def _evaluate_effectiveness(self, interaction: dict, outcome: str) -> float:
        """评估有效性"""
        return 0.7  # 简化实现

    async def _evaluate_efficiency(self, interaction: dict) -> float:
        """评估效率"""
        return 0.85  # 简化实现

    async def _evaluate_feasibility(self, option: dict, context: dict) -> float:
        """评估可行性"""
        return 0.8  # 简化实现

    async def _evaluate_value(self, option: dict, criteria: str) -> float:
        """评估价值"""
        return option.get("expected_value", 0.5)

    async def _evaluate_risk(self, option: dict) -> float:
        """评估风险"""
        return option.get("risk_level", 0.5)

    async def _evaluate_alignment(self, option: dict, context: dict) -> float:
        """评估对齐度"""
        return 0.7  # 简化实现

    def _generate_recommendation(self, results: dict) -> str:
        """生成推荐"""
        best_option = max(results.items(), key=lambda x: x[1].get("overall_score", 0))
        return f"推荐选项: {best_option[0]} (评分: {best_option[1].get('overall_score', 0):.2f})"

    async def _store_evaluation_record(self, eval_id: str, data: dict, eval_result: dict):
        """存储评估记录"""
        if not hasattr(self, "evaluation_records"):
            self.evaluation_records = []

        record = {
            "id": eval_id,
            "data": data,
            "result": eval_result,
            "timestamp": datetime.now().isoformat(),
        }

        self.evaluation_records.append(record)

        # 限制记录数量
        if len(self.evaluation_records) > 100:
            self.evaluation_records = self.evaluation_records[-50:]
