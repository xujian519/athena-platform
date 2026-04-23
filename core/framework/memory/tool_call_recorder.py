#!/usr/bin/env python3

"""
工具调用轨迹记录器

记录Agent执行过程中的工具调用轨迹，用于后续分析和workflow模式提取。

Author: Athena平台团队
Created: 2026-01-20
Version: v1.0.0
"""

import json
import logging
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ToolCallRecord:
    """
    工具调用记录

    记录单个工具调用的完整信息。
    """
    call_id: str
    tool_name: str
    timestamp: datetime
    input_data: dict[str, Any]
    output_data: Optional[Any] = None
    execution_time: float = 0.0
    success: bool = True
    error_message: Optional[str] = None

    # 额外元数据
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "call_id": self.call_id,
            "tool_name": self.tool_name,
            "timestamp": self.timestamp.isoformat(),
            "input_data": self.input_data,
            "output_data": self.output_data,
            "execution_time": self.execution_time,
            "success": self.success,
            "error_message": self.error_message,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToolCallRecord:
        """从字典创建实例"""
        return cls(
            call_id=data["call_id"],
            tool_name=data["tool_name"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            input_data=data.get("input_data", {}),
            output_data=data.get("output_data"),
            execution_time=data.get("execution_time", 0.0),
            success=data.get("success", True),
            error_message=data.get("error_message"),
            metadata=data.get("metadata", {})
        )


class ToolCallTrajectory:
    """
    工具调用轨迹

    管理一次任务执行中的所有工具调用记录。
    """

    def __init__(self, task_id: str):
        """
        初始化工具调用轨迹

        Args:
            task_id: 任务ID
        """
        self.task_id = task_id
        self.start_time = datetime.now()
        self.calls: OrderedDict[str, ToolCallRecord] = OrderedDict()
        self.call_counter = 0
        self._current_call_id: Optional[str] = None

    def start_call(
        self,
        tool_name: str,
        input_data: Optional[dict[str, Any],        metadata: dict[str, Any] = None
    ) -> str:
        """
        开始记录工具调用

        Args:
            tool_name: 工具名称
            input_data: 输入数据
            metadata: 额外元数据

        Returns:
            调用ID
        """
        self.call_counter += 1
        call_id = f"{self.task_id}_call_{self.call_counter:04d}"

        record = ToolCallRecord(
            call_id=call_id,
            tool_name=tool_name,
            timestamp=datetime.now(),
            input_data=input_data,
            metadata=metadata or {}
        )

        self.calls[call_id] = record
        self._current_call_id = call_id

        logger.debug(f"📍 工具调用开始: {tool_name} (call_id: {call_id})")

        return call_id

    def end_call(
        self,
        call_id: str,
        output_data: Any,
        execution_time: float,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """
        结束工具调用记录

        Args:
            call_id: 调用ID
            output_data: 输出数据
            execution_time: 执行时间（秒）
            success: 是否成功
            error_message: 错误消息
        """
        if call_id not in self.calls:
            logger.warning(f"⚠️ 未找到调用记录: {call_id}")
            return

        record = self.calls[call_id]
        record.output_data = output_data
        record.execution_time = execution_time
        record.success = success
        record.error_message = error_message

        logger.debug(
            f"✅ 工具调用完成: {record.tool_name} "
            f"(耗时: {execution_time*1000:.2f}ms, 成功: {success})"
        )

        self._current_call_id = None

    def add_call(self, record: ToolCallRecord) -> None:
        """
        添加已完成的工具调用记录

        Args:
            record: 工具调用记录
        """
        self.calls[record.call_id] = record
        self.call_counter += 1

    def get_calls(self) -> list[ToolCallRecord]:
        """获取所有工具调用记录"""
        return list(self.calls.values())

    def get_successful_calls(self) -> list[ToolCallRecord]:
        """获取成功的工具调用"""
        return [c for c in self.calls.values() if c.success]

    def get_failed_calls(self) -> list[ToolCallRecord]:
        """获取失败的工具调用"""
        return [c for c in self.calls.values() if not c.success]

    def get_calls_by_tool(self, tool_name: str) -> list[ToolCallRecord]:
        """按工具名称获取调用记录"""
        return [c for c in self.calls.values() if c.tool_name == tool_name]

    def get_statistics(self) -> dict[str, Any]:
        """
        获取轨迹统计信息

        Returns:
            统计信息字典
        """
        calls = self.get_calls()
        successful = self.get_successful_calls()
        failed = self.get_failed_calls()

        # 按工具统计
        tool_stats = {}
        for call in calls:
            if call.tool_name not in tool_stats:
                tool_stats[call.tool_name]] = {
                    "total": 0,
                    "successful": 0,
                    "failed": 0,
                    "total_time": 0.0
                }

            stats = tool_stats[call.tool_name]
            stats["total"] += 1
            stats["total_time"] += call.execution_time

            if call.success:
                stats["successful"] += 1
            else:
                stats["failed"] += 1

        # 计算平均时间
        for stats in tool_stats.values():
            if stats["total"] > 0:
                stats["avg_time"] = stats["total_time"] / stats["total"]

        total_time = sum(c.execution_time for c in calls)
        elapsed = (datetime.now() - self.start_time).total_seconds()

        return {
            "task_id": self.task_id,
            "total_calls": len(calls),
            "successful_calls": len(successful),
            "failed_calls": len(failed),
            "success_rate": len(successful) / len(calls) if calls else 0.0,
            "total_execution_time": total_time,
            "elapsed_time": elapsed,
            "tool_statistics": tool_stats
        }

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "start_time": self.start_time.isoformat(),
            "calls": [record.to_dict() for record in self.get_calls()],
            "statistics": self.get_statistics()
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToolCallTrajectory:
        """从字典创建实例"""
        trajectory = cls(task_id=data["task_id"])
        trajectory.start_time = datetime.fromisoformat(data["start_time"])

        for call_data in data.get("calls", []):
            record = ToolCallRecord.from_dict(call_data)
            trajectory.add_call(record)

        return trajectory

    def save_to_file(self, file_path: str) -> None:
        """保存到文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

        logger.debug(f"💾 轨迹已保存: {file_path}")

    @classmethod
    def load_from_file(cls, file_path: str) -> ToolCallTrajectory:
        """从文件加载"""
        with open(file_path, encoding='utf-8') as f:
            data = json.load(f)

        logger.debug(f"📂 轨迹已加载: {file_path}")
        return cls.from_dict(data)


class ToolCallRecorder:
    """
    工具调用记录器

    管理多个任务的工具调用轨迹。
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        初始化工具调用记录器

        Args:
            storage_path: 轨迹存储路径
        """
        self.storage_path = storage_path
        self.trajectories: dict[str, ToolCallTrajectory] = {}

    def create_trajectory(self, task_id: str) -> ToolCallTrajectory:
        """
        创建新的工具调用轨迹

        Args:
            task_id: 任务ID

        Returns:
            新创建的轨迹对象
        """
        trajectory = ToolCallTrajectory(task_id=task_id)
        self.trajectories[task_id] = trajectory

        logger.info(f"📍 创建工具调用轨迹: {task_id}")

        return trajectory

    def get_trajectory(self, task_id: str) -> Optional[ToolCallTrajectory]:
        """获取指定任务的轨迹"""
        return self.trajectories.get(task_id)

    def remove_trajectory(self, task_id: str) -> bool:
        """
        移除指定任务的轨迹

        Args:
            task_id: 任务ID

        Returns:
            是否成功移除
        """
        if task_id in self.trajectories:
            del self.trajectories[task_id]
            logger.info(f"🗑️ 移除轨迹: {task_id}")
            return True
        return False

    def get_all_trajectories(self) -> list[ToolCallTrajectory]:
        """获取所有轨迹"""
        return list(self.trajectories.values())

    def save_trajectory(self, task_id: str, file_path: Optional[str] = None) -> None:
        """
        保存轨迹到文件

        Args:
            task_id: 任务ID
            file_path: 文件路径，如果为None则使用默认路径
        """
        trajectory = self.get_trajectory(task_id)
        if not trajectory:
            logger.warning(f"⚠️ 未找到轨迹: {task_id}")
            return

        if file_path is None:
            if self.storage_path is None:
                logger.warning("⚠️ 未设置存储路径")
                return
            file_path = f"{self.storage_path}/{task_id}_trajectory.json"

        trajectory.save_to_file(file_path)

    def get_global_statistics(self) -> dict[str, Any]:
        """获取全局统计信息"""
        all_trajectories = self.get_all_trajectories()

        total_calls = 0
        successful_calls = 0
        tool_usage = {}

        for trajectory in all_trajectories:
            stats = trajectory.get_statistics()
            total_calls += stats["total_calls"]
            successful_calls += stats["successful_calls"]

            # 合并工具统计
            for tool, tool_stats in stats["tool_statistics"].items():
                if tool not in tool_usage:
                    tool_usage[tool]] = {
                        "total": 0,
                        "successful": 0,
                        "failed": 0
                    }

                tool_usage[tool]["total"] += tool_stats["total"]
                tool_usage[tool]["successful"] += tool_stats["successful"]
                tool_usage[tool]["failed"] += tool_stats["failed"]

        return {
            "total_trajectories": len(all_trajectories),
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "overall_success_rate": successful_calls / total_calls if total_calls > 0 else 0.0,
            "tool_usage": tool_usage
        }


__all__ = [
    'ToolCallRecord',
    'ToolCallRecorder',
    'ToolCallTrajectory'
]

