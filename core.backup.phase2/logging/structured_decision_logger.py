#!/usr/bin/env python3
from __future__ import annotations
"""
结构化决策日志记录器
Structured Decision Logger

为综合决策过程提供结构化日志记录,
支持决策过程追溯,无需可视化界面。

功能:
- 决策过程完整记录
- 关键指标控制台输出
- 结构化日志存储
- 可追溯和可分析

作者: 小诺·双鱼公主
创建时间: 2025-12-27
版本: v1.0.0 "结构化日志"
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


def _get_logger():
    """延迟获取logger，避免循环导入"""
    return logging.getLogger(__name__)


class LogLevel(Enum):
    """日志级别"""

    INFO = "INFO"
    DECISION = "DECISION"
    ITERATION = "ITERATION"
    CONFLICT = "CONFLICT"
    RESOLUTION = "RESOLUTION"


@dataclass
class DecisionLogEntry:
    """决策日志条目"""

    timestamp: str
    level: LogLevel
    task_id: str
    stage: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp,
            "level": self.level.value,
            "task_id": self.task_id,
            "stage": self.stage,
            "content": self.content,
            "metadata": self.metadata,
        }


class StructuredDecisionLogger:
    """
    结构化决策日志记录器
    """

    def __init__(self, log_dir: Path | None = None):
        """初始化日志记录器"""
        self.log_dir = log_dir or Path("/Users/xujian/Athena工作平台/logs/decisions")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.current_entries: list[DecisionLogEntry] = []

        _get_logger().info("📝 结构化决策日志记录器初始化完成")
        _get_logger().info(f"   日志目录: {self.log_dir}")

    def log_decision_start(self, task_id: str, task_description: str, context: dict | None = None) -> Any:
        """记录决策开始"""
        entry = DecisionLogEntry(
            timestamp=datetime.now().isoformat(),
            level=LogLevel.INFO,
            task_id=task_id,
            stage="DECISION_START",
            content=f"开始综合集成决策: {task_description}",
            metadata={"context": context or {}},
        )

        self._add_entry(entry)
        self._print_header(f"🎯 开始综合集成决策: {task_id}")

    def log_qualitative_assessment(
        self, task_id: str, direction: str, reasoning: str, confidence: float
    ):
        """记录定性评估"""
        entry = DecisionLogEntry(
            timestamp=datetime.now().isoformat(),
            level=LogLevel.DECISION,
            task_id=task_id,
            stage="QUALITATIVE_ASSESSMENT",
            content=f"[第1步]定性判断方向: {direction}",
            metadata={"reasoning": reasoning, "confidence": confidence},
        )

        self._add_entry(entry)
        self._print_step(
            "[第1步]定性判断方向",
            {"方向": direction, "理由": reasoning[:80] + "...", "置信度": f"{confidence:.1%}"},
        )

    def log_agent_opinions(self, task_id: str, opinions: list) -> Any:
        """记录智能体意见"""
        opinion_summary = [
            f"{op.get('agent_name', 'Unknown')}: {op.get('opinion', '')[:50]}..." for op in opinions
        ]

        entry = DecisionLogEntry(
            timestamp=datetime.now().isoformat(),
            level=LogLevel.DECISION,
            task_id=task_id,
            stage="AGENT_OPINIONS",
            content=f"[第2步]收集智能体意见: {len(opinions)}个",
            metadata={"opinions": opinions},
        )

        self._add_entry(entry)
        self._print_step(
            "[第2步]收集智能体意见", {"参与智能体": len(opinions), "意见": opinion_summary}
        )

    def log_conflict_detection(
        self, task_id: str, has_conflict: bool, conflict_type: str, conflict_details: dict | None = None
    ):
        """记录冲突检测"""
        entry = DecisionLogEntry(
            timestamp=datetime.now().isoformat(),
            level=LogLevel.CONFLICT if has_conflict else LogLevel.DECISION,
            task_id=task_id,
            stage="CONFLICT_DETECTION",
            content=f"[第3步]冲突检测: {conflict_type}",
            metadata={"has_conflict": has_conflict, "details": conflict_details or {}},
        )

        self._add_entry(entry)
        self._print_step(
            "[第3步]冲突检测", {"冲突状态": conflict_type, "详细信息": conflict_details or {}}
        )

    def log_iteration(
        self,
        task_id: str,
        iteration_num: int,
        consensus_level: str,
        confidence: float,
        conclusion: str,
    ):
        """记录迭代过程"""
        entry = DecisionLogEntry(
            timestamp=datetime.now().isoformat(),
            level=LogLevel.ITERATION,
            task_id=task_id,
            stage=f"ITERATION_{iteration_num}",
            content=f"[第4步]第{iteration_num}轮迭代: 共识{consensus_level}",
            metadata={
                "iteration": iteration_num,
                "consensus_level": consensus_level,
                "confidence": confidence,
                "conclusion": conclusion,
            },
        )

        self._add_entry(entry)
        self._print_step(
            f"   第{iteration_num}轮迭代",
            {
                "共识等级": consensus_level,
                "置信度": f"{confidence:.1%}",
                "结论": conclusion[:80] + "...",
            },
        )

    def log_arbitration(self, task_id: str, arbitration_result: str, resolution: str):
        """记录仲裁结果"""
        entry = DecisionLogEntry(
            timestamp=datetime.now().isoformat(),
            level=LogLevel.RESOLUTION,
            task_id=task_id,
            stage="ARBITRATION",
            content=f"冲突仲裁: {arbitration_result}",
            metadata={"resolution": resolution},
        )

        self._add_entry(entry)
        self._print_step(
            "⚖️ 冲突仲裁", {"仲裁结果": arbitration_result, "解决方案": resolution[:80] + "..."}
        )

    def log_final_decision(
        self, task_id: str, conclusion: str, confidence: float, decision_basis: str, iterations: int
    ):
        """记录最终决策"""
        entry = DecisionLogEntry(
            timestamp=datetime.now().isoformat(),
            level=LogLevel.RESOLUTION,
            task_id=task_id,
            stage="FINAL_DECISION",
            content=f"[最终决策]{conclusion}",
            metadata={"confidence": confidence, "basis": decision_basis, "iterations": iterations},
        )

        self._add_entry(entry)
        self._print_header(f"✅ 综合集成决策完成: {task_id}")
        self._print_step(
            "[最终决策]",
            {
                "结论": conclusion,
                "置信度": f"{confidence:.1%}",
                "决策依据": decision_basis,
                "迭代轮数": iterations,
            },
        )

    def save_to_file(self, task_id: str) -> None:
        """保存日志到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"decision_{task_id}_{timestamp}.jsonl"

        with open(log_file, "w", encoding="utf-8") as f:
            for entry in self.current_entries:
                f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")

        _get_logger().info(f"📄 决策日志已保存: {log_file}")
        self.current_entries.clear()

        return log_file

    def _add_entry(self, entry: DecisionLogEntry) -> Any:
        """添加日志条目"""
        self.current_entries.append(entry)

    def _print_header(self, message: str) -> Any:
        """打印标题"""
        border = "=" * 70
        _get_logger().info(f"\n{border}")
        _get_logger().info(f"{message}")
        _get_logger().info(f"{border}")

    def _print_step(self, title: str, content: Any) -> Any:
        """打印步骤"""
        _get_logger().info(f"{title}")
        if isinstance(content, dict):
            for key, value in content.items():
                if isinstance(value, list):
                    for i, item in enumerate(value, 1):
                        _get_logger().info(f"   {key} {i}: {item}")
                else:
                    _get_logger().info(f"   {key}: {value}")
        else:
            _get_logger().info(f"   {content}")


# 全局实例
_logger: StructuredDecisionLogger = None


def get_decision_logger() -> StructuredDecisionLogger:
    """获取决策日志记录器单例"""
    global _logger
    if _logger is None:
        _logger = StructuredDecisionLogger()
    return _logger


# 便捷函数
def log_decision_process(task_id: str, decision_data: dict[str, Any]) -> Path | None:
    """
    便捷函数:记录完整决策过程

    Args:
        task_id: 任务ID
        decision_data: 决策数据字典

    Returns:
        日志文件路径
    """
    logger_instance = get_decision_logger()

    # 记录开始
    logger_instance.log_decision_start(
        task_id, decision_data.get("task_description", ""), decision_data.get("context")
    )

    # 记录定性评估
    if "qualitative" in decision_data:
        q = decision_data["qualitative"]
        logger_instance.log_qualitative_assessment(
            task_id, q.get("direction", ""), q.get("reasoning", ""), q.get("confidence", 0.0)
        )

    # 记录智能体意见
    if "opinions" in decision_data:
        logger_instance.log_agent_opinions(task_id, decision_data["opinions"])

    # 记录冲突检测
    if "conflict" in decision_data:
        c = decision_data["conflict"]
        logger_instance.log_conflict_detection(
            task_id, c.get("has_conflict", False), c.get("type", ""), c.get("details")
        )

    # 记录迭代
    if "iterations" in decision_data:
        for iter_data in decision_data["iterations"]:
            logger_instance.log_iteration(
                task_id,
                iter_data.get("iteration", 0),
                iter_data.get("consensus", ""),
                iter_data.get("confidence", 0.0),
                iter_data.get("conclusion", ""),
            )

    # 记录最终决策
    if "final_decision" in decision_data:
        f = decision_data["final_decision"]
        logger_instance.log_final_decision(
            task_id,
            f.get("conclusion", ""),
            f.get("confidence", 0.0),
            f.get("basis", ""),
            f.get("iterations", 0),
        )

    # 保存到文件
    return logger_instance.save_to_file(task_id)


if __name__ == "__main__":
    # 测试日志记录器
    print("🧪 测试结构化决策日志记录器")
    print("=" * 70)

    # 模拟决策过程
    decision_data = {
        "task_description": "选择向量数据库方案",
        "context": {"priority": "high"},
        "qualitative": {
            "direction": "技术分析",
            "reasoning": "需要考虑性能和可维护性",
            "confidence": 0.8,
        },
        "opinions": [
            {"agent_name": "小娜", "opinion": "建议Qdrant,性能更好"},
            {"agent_name": "云熙", "opinion": "建议PostgreSQL,技术栈统一"},
        ],
        "conflict": {
            "has_conflict": True,
            "type": "方案分歧",
            "details": {"conflicting_parties": ["小娜", "云熙"]},
        },
        "iterations": [
            {
                "iteration": 1,
                "consensus": "兼容",
                "confidence": 0.75,
                "conclusion": "两种方案各有优劣",
            },
            {
                "iteration": 2,
                "consensus": "共识",
                "confidence": 0.82,
                "conclusion": "建议分阶段实施",
            },
        ],
        "final_decision": {
            "conclusion": "采用分阶段方案:先PostgreSQL,后迁移Qdrant",
            "confidence": 0.82,
            "basis": "经过2轮迭代达成共识",
            "iterations": 2,
        },
    }

    # 记录决策过程
    log_file = log_decision_process("test_001", decision_data)

    print("\n✅ 测试完成")
    print(f"   日志文件: {log_file}")
