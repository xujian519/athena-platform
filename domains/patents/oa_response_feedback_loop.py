#!/usr/bin/env python3
from __future__ import annotations

"""
审查意见答复反馈闭环管理器
Office Action Response Feedback Loop Manager

建立从答复结果到系统优化的反馈闭环

功能:
1. 收集答复结果反馈
2. 分析成功/失败模式
3. 自动调整参数
4. 生成优化建议
5. 持续学习和改进

作者: 小诺·双鱼公主
创建时间: 2026-01-26
版本: v1.0.0
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging
from core.utils.error_handling import (
    WorkflowRecordError,
    timeout,
)

logger = setup_logging()


class FeedbackType(Enum):
    """反馈类型"""

    SUCCESS = "success"  # 答复成功，专利授权
    PARTIAL_SUCCESS = "partial_success"  # 部分成功，需要修改
    FAILURE = "failure"  # 答复失败，专利驳回
    QUALITY_ISSUE = "quality_issue"  # 质量问题


class OptimizationAction(Enum):
    """优化动作类型"""

    ADJUST_TIMEOUT = "adjust_timeout"  # 调整超时参数
    UPDATE_PATTERN = "update_pattern"  # 更新模式权重
    RETRY_FAILED = "retry_failed"  # 重试失败操作
    IMPROVE_QUALITY = "improve_quality"  # 改进质量控制
    ALERT_HUMAN = "alert_human"  # 告警需要人工介入


@dataclass
class FeedbackRecord:
    """反馈记录"""

    feedback_id: str
    trajectory_id: str
    oa_id: str
    patent_id: str
    feedback_type: FeedbackType
    outcome: str  # allowed, rejected, partial
    actual_outcome: str | None = None  # 实际审查结果
    quality_score: float = 0.0
    user_satisfaction: int = 0  # 1-5分
    comments: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    analyzed: bool = False
    optimization_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "feedback_id": self.feedback_id,
            "trajectory_id": self.trajectory_id,
            "oa_id": self.oa_id,
            "patent_id": self.patent_id,
            "feedback_type": self.feedback_type.value,
            "outcome": self.outcome,
            "actual_outcome": self.actual_outcome,
            "quality_score": self.quality_score,
            "user_satisfaction": self.user_satisfaction,
            "comments": self.comments,
            "timestamp": self.timestamp,
            "analyzed": self.analyzed,
            "optimization_actions": self.optimization_actions,
        }


@dataclass
class OptimizationSuggestion:
    """优化建议"""

    suggestion_id: str
    action_type: OptimizationAction
    priority: str  # high, medium, low
    description: str
    rationale: str
    parameters: dict[str, Any] = field(default_factory=dict)
    estimated_impact: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class FeedbackLoopManager:
    """反馈闭环管理器"""

    def __init__(
        self,
        feedback_dir: str = "data/oa_responses/feedback",
        optimization_dir: str = "data/oa_responses/optimizations",
    ):
        """初始化反馈闭环管理器"""
        self.feedback_dir = Path(feedback_dir)
        self.optimization_dir = Path(optimization_dir)

        # 创建目录
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
        self.optimization_dir.mkdir(parents=True, exist_ok=True)

        # 状态文件
        self.feedback_index_file = self.feedback_dir / "feedback_index.json"
        self.optimization_log_file = self.optimization_dir / "optimizations.jsonl"

        # 加载反馈索引
        self.feedback_index = self._load_feedback_index()

        logger.info("🔄 OA答复反馈闭环管理器初始化完成")

    def _load_feedback_index(self) -> dict[str, Any]:
        """加载反馈索引"""
        if self.feedback_index_file.exists():
            try:
                with open(self.feedback_index_file, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载反馈索引失败: {e}")

        return {
            "total_feedback": 0,
            "success_count": 0,
            "failure_count": 0,
            "last_analysis_time": None,
            "feedback_records": [],
        }

    def _save_feedback_index(self):
        """保存反馈索引"""
        try:
            with open(self.feedback_index_file, "w", encoding="utf-8") as f:
                json.dump(self.feedback_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存反馈索引失败: {e}")

    @timeout(seconds=5.0)
    async def collect_feedback(
        self,
        trajectory_id: str,
        oa_id: str,
        patent_id: str,
        outcome: str,
        quality_score: float = 0.0,
        user_satisfaction: int = 0,
        comments: str = "",
    ) -> FeedbackRecord:
        """
        收集答复反馈

        Args:
            trajectory_id: 轨迹ID
            oa_id: 审查意见ID
            patent_id: 专利ID
            outcome: 答复结果 (allowed/rejected/partial)
            quality_score: 质量分数
            user_satisfaction: 用户满意度 (1-5)
            comments: 用户评论

        Returns:
            反馈记录
        """
        feedback_id = f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{oa_id}"

        # 确定反馈类型
        if outcome == "allowed":
            feedback_type = FeedbackType.SUCCESS
        elif outcome == "rejected":
            feedback_type = FeedbackType.FAILURE
        else:
            feedback_type = FeedbackType.PARTIAL_SUCCESS

        # 创建反馈记录
        record = FeedbackRecord(
            feedback_id=feedback_id,
            trajectory_id=trajectory_id,
            oa_id=oa_id,
            patent_id=patent_id,
            feedback_type=feedback_type,
            outcome=outcome,
            quality_score=quality_score,
            user_satisfaction=user_satisfaction,
            comments=comments,
        )

        # 保存反馈记录
        feedback_file = self.feedback_dir / f"{feedback_id}.json"
        try:
            with open(feedback_file, "w", encoding="utf-8") as f:
                json.dump(record.to_dict(), f, ensure_ascii=False, indent=2)

            # 更新索引
            self.feedback_index["feedback_records"].append({
                "feedback_id": feedback_id,
                "trajectory_id": trajectory_id,
                "outcome": outcome,
                "timestamp": record.timestamp,
            })
            self.feedback_index["total_feedback"] += 1

            if outcome == "allowed":
                self.feedback_index["success_count"] += 1
            else:
                self.feedback_index["failure_count"] += 1

            self._save_feedback_index()

            logger.info(f"✅ 反馈已收集: {feedback_id}")

            # 异步分析反馈
            asyncio.create_task(self.analyze_feedback(record))

        except Exception as e:
            logger.error(f"保存反馈失败: {e}")
            raise WorkflowRecordError(
                message=f"保存反馈记录失败: {feedback_id}",
                context={"feedback_id": feedback_id}
            ) from e

        return record

    async def analyze_feedback(self, record: FeedbackRecord) -> list[OptimizationSuggestion]:
        """
        分析反馈并生成优化建议

        Args:
            record: 反馈记录

        Returns:
            优化建议列表
        """
        logger.info(f"🔍 分析反馈: {record.feedback_id}")

        suggestions = []

        # 分析失败的答复
        if record.feedback_type == FeedbackType.FAILURE:
            # 检查质量分数
            if record.quality_score < 0.6:
                suggestion = OptimizationSuggestion(
                    suggestion_id=f"suggest_{datetime.now().strftime('%Y%m%d%H%M%S')}_001",
                    action_type=OptimizationAction.IMPROVE_QUALITY,
                    priority="high",
                    description="提高答复质量控制阈值",
                    rationale=f"失败的答复质量分数过低 ({record.quality_score:.2f})",
                    parameters={"min_quality_threshold": 0.7},
                    estimated_impact="预期可减少20%的失败率",
                )
                suggestions.append(suggestion)

            # 检查是否需要人工介入
            if record.user_satisfaction <= 2:
                suggestion = OptimizationSuggestion(
                    suggestion_id=f"suggest_{datetime.now().strftime('%Y%m%d%H%M%S')}_002",
                    action_type=OptimizationAction.ALERT_HUMAN,
                    priority="high",
                    description="需要人工审查答复策略",
                    rationale=f"用户满意度低 ({record.user_satisfaction}/5)，答复策略可能不当",
                    estimated_impact="避免类似问题再次发生",
                )
                suggestions.append(suggestion)

        # 分析部分成功的答复
        elif record.feedback_type == FeedbackType.PARTIAL_SUCCESS:
            suggestion = OptimizationSuggestion(
                suggestion_id=f"suggest_{datetime.now().strftime('%Y%m%d%H%M%S')}_003",
                action_type=OptimizationAction.UPDATE_PATTERN,
                priority="medium",
                description="优化答复模式权重",
                rationale="部分成功说明现有模式有改进空间",
                parameters={"weight_adjustment_factor": 0.1},
                estimated_impact="预期可提高10-15%的成功率",
            )
            suggestions.append(suggestion)

        # 分析成功的答复
        elif record.feedback_type == FeedbackType.SUCCESS:
            if record.quality_score > 0.9:
                suggestion = OptimizationSuggestion(
                    suggestion_id=f"suggest_{datetime.now().strftime('%Y%m%d%H%M%S')}_004",
                    action_type=OptimizationAction.UPDATE_PATTERN,
                    priority="low",
                    description="记录高质量答复模式",
                    rationale=f"高质量成功答复 (分数: {record.quality_score:.2f})，值得学习",
                    parameters={"pattern_priority": "high"},
                    estimated_impact="可复用到类似案件",
                )
                suggestions.append(suggestion)

        # 保存优化建议
        if suggestions:
            await self._save_optimization_suggestions(record, suggestions)

        # 标记为已分析
        record.analyzed = True
        record.optimization_actions = [s.suggestion_id for s in suggestions]

        return suggestions

    async def _save_optimization_suggestions(
        self,
        record: FeedbackRecord,
        suggestions: list[OptimizationSuggestion],
    ):
        """保存优化建议"""
        try:
            with open(self.optimization_log_file, "a", encoding="utf-8") as f:
                for suggestion in suggestions:
                    log_entry = {
                        "feedback_id": record.feedback_id,
                        "suggestion": suggestion.__dict__,
                        "timestamp": datetime.now().isoformat(),
                    }
                    f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

            logger.info(f"💾 已保存 {len(suggestions)} 条优化建议")

        except Exception as e:
            logger.error(f"保存优化建议失败: {e}")

    async def get_recent_feedback(
        self,
        days: int = 7,
        feedback_type: FeedbackType | None = None,
    ) -> list[dict[str, Any]:
        """
        获取最近的反馈

        Args:
            days: 查询最近几天的反馈
            feedback_type: 筛选特定类型

        Returns:
            反馈记录列表
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        recent_feedback = []

        for record_info in self.feedback_index.get("feedback_records", []):
            try:
                record_time = datetime.fromisoformat(record_info["timestamp"])

                if record_time < cutoff_time:
                    continue

                if feedback_type and record_info.get("outcome") != feedback_type.value:
                    continue

                recent_feedback.append(record_info)

            except Exception as e:
                logger.warning(f"解析反馈记录失败: {e}")

        return recent_feedback

    async def generate_feedback_report(self) -> dict[str, Any]:
        """
        生成反馈分析报告

        Returns:
            分析报告
        """
        index = self.feedback_index

        total = index.get("total_feedback", 0)
        success = index.get("success_count", 0)
        failure = index.get("failure_count", 0)

        success_rate = success / total if total > 0 else 0.0

        report = {
            "summary": {
                "total_feedback": total,
                "success_count": success,
                "failure_count": failure,
                "success_rate": success_rate,
                "last_analysis_time": index.get("last_analysis_time"),
            },
            "trends": {
                "recent_7_days": await self.get_recent_feedback(days=7),
                "recent_30_days": await self.get_recent_feedback(days=30),
            },
            "recommendations": [],
        }

        # 生成建议
        if success_rate < 0.7:
            report["recommendations"].append({
                "type": "critical",
                "message": f"成功率过低 ({success_rate:.1%})，需要立即优化答复策略",
            })

        if total > 100 and failure > total * 0.3:
            report["recommendations"].append({
                "type": "warning",
                "message": "失败率超过30%，建议审查质量控制流程",
            })

        return report

    async def apply_optimization(
        self,
        suggestion: OptimizationSuggestion,
    ) -> bool:
        """
        应用优化建议

        Args:
            suggestion: 优化建议

        Returns:
            是否成功应用
        """
        logger.info(f"⚙️  应用优化建议: {suggestion.suggestion_id}")

        try:
            if suggestion.action_type == OptimizationAction.IMPROVE_QUALITY:
                # 更新质量控制参数
                logger.info(f"更新质量阈值为: {suggestion.parameters.get('min_quality_threshold')}")

            elif suggestion.action_type == OptimizationAction.UPDATE_PATTERN:
                # 更新模式权重
                logger.info(f"更新模式权重: {suggestion.parameters}")

            elif suggestion.action_type == OptimizationAction.ADJUST_TIMEOUT:
                # 调整超时参数
                logger.info(f"调整超时参数: {suggestion.parameters}")

            elif suggestion.action_type == OptimizationAction.ALERT_HUMAN:
                # 发送告警通知
                logger.warning(f"需要人工介入: {suggestion.description}")

            return True

        except Exception as e:
            logger.error(f"应用优化建议失败: {e}")
            return False


# ===== 全局单例 =====

_manager_instance: FeedbackLoopManager | None = None


def get_feedback_manager() -> FeedbackLoopManager:
    """获取反馈闭环管理器单例"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = FeedbackLoopManager()
    return _manager_instance


# ===== 示例使用 =====

async def example_feedback_workflow():
    """反馈闭环工作流示例"""

    manager = get_feedback_manager()

    # 模拟收集反馈
    await manager.collect_feedback(
        trajectory_id="traj_20260126_001",
        oa_id="OA_20260126_001",
        patent_id="PAT_20260126_001",
        outcome="allowed",
        quality_score=0.85,
        user_satisfaction=4,
        comments="答复质量很好，成功获得授权",
    )

    # 生成报告
    report = await manager.generate_feedback_report()
    print("\n📊 反馈分析报告:")
    print(f"   总反馈数: {report['summary']['total_feedback']}")
    print(f"   成功率: {report['summary']['success_rate']:.1%}")

    if report["recommendations"]:
        print("\n💡 优化建议:")
        for rec in report["recommendations"]:
            print(f"   [{rec['type'].upper()}] {rec['message']}")


if __name__ == "__main__":
    asyncio.run(example_feedback_workflow())
