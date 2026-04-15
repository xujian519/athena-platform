#!/usr/bin/env python3
"""
状态持久化管理器

统一管理workflow模式、工具性能指标、Hook状态的持久化。

Author: Athena平台团队
Created: 2026-01-20
Version: v1.0.0
"""

from __future__ import annotations
import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from core.hooks.base import HookRegistry, HookType
from core.tools.base import ToolRegistry

logger = logging.getLogger(__name__)


@dataclass
class CheckpointMetadata:
    """
    检查点元数据

    记录检查点的基本信息。
    """

    checkpoint_id: str  # 检查点ID
    timestamp: datetime  # 创建时间
    description: str  # 描述
    tags: list[str] = field(default_factory=list)

    # 统计信息
    workflow_patterns: int = 0  # workflow模式数量
    tools: int = 0  # 工具数量
    hooks: int = 0  # hooks数量

    # 文件路径
    checkpoint_dir: str = ""  # 检查点目录

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "checkpoint_id": self.checkpoint_id,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "tags": self.tags,
            "workflow_patterns": self.workflow_patterns,
            "tools": self.tools,
            "hooks": self.hooks,
            "checkpoint_dir": self.checkpoint_dir,
        }


class StatePersistenceManager:
    """
    状态持久化管理器

    统一管理所有系统状态的持久化。
    """

    def __init__(
        self,
        storage_path: str = "data/state_persistence",
        enable_auto_checkpoint: bool = True,
        checkpoint_interval: int = 300,  # 5分钟
    ):
        """
        初始化状态持久化管理器

        Args:
            storage_path: 存储路径
            enable_auto_checkpoint: 是否启用自动检查点
            checkpoint_interval: 自动检查点间隔(秒)
        """
        self.storage_path = Path(storage_path)
        self.enable_auto_checkpoint = enable_auto_checkpoint
        self.checkpoint_interval = checkpoint_interval

        # 创建目录结构
        self.storage_path.mkdir(parents=True, exist_ok=True)
        (self.storage_path / "checkpoints").mkdir(exist_ok=True)
        (self.storage_path / "tool_metrics").mkdir(exist_ok=True)
        (self.storage_path / "hook_states").mkdir(exist_ok=True)

        # 检查点索引
        self._checkpoints: dict[str, CheckpointMetadata] = {}
        self._load_checkpoint_index()

        logger.info(f"💾 StatePersistenceManager初始化完成 (路径: {storage_path})")

    def _load_checkpoint_index(self) -> Any:
        """加载检查点索引"""
        index_file = self.storage_path / "checkpoint_index.json"

        if index_file.exists():
            try:
                with open(index_file, encoding="utf-8") as f:
                    data = json.load(f)

                for cp_id, cp_data in data.items():
                    self._checkpoints[cp_id] = CheckpointMetadata(
                        checkpoint_id=cp_data["checkpoint_id"],
                        timestamp=datetime.fromisoformat(cp_data["timestamp"]),
                        description=cp_data["description"],
                        tags=cp_data.get("tags", []),
                        workflow_patterns=cp_data.get("workflow_patterns", 0),
                        tools=cp_data.get("tools", 0),
                        hooks=cp_data.get("hooks", 0),
                        checkpoint_dir=cp_data.get("checkpoint_dir", ""),
                    )

                logger.info(f"📂 已加载{len(self._checkpoints)}个检查点索引")

            except Exception as e:
                logger.error(f"❌ 加载检查点索引失败: {e}")
                self._checkpoints = {}

    def _save_checkpoint_index(self) -> Any:
        """保存检查点索引"""
        index_file = self.storage_path / "checkpoint_index.json"

        try:
            data = {cp_id: cp.to_dict() for cp_id, cp in self._checkpoints.items()}

            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug("💾 检查点索引已保存")

        except Exception as e:
            logger.error(f"❌ 保存检查点索引失败: {e}")

    async def create_checkpoint(
        self,
        workflow_memory: Any | None = None,
        tool_registry: ToolRegistry | None = None,
        hook_registry: HookRegistry | None = None,
        description: str = "",
        tags: list[str] | None = None,
    ) -> CheckpointMetadata:
        """
        创建系统状态检查点

        Args:
            workflow_memory: CrossTaskWorkflowMemory实例
            tool_registry: ToolRegistry实例
            hook_registry: HookRegistry实例
            description: 检查点描述
            tags: 检查点标签

        Returns:
            CheckpointMetadata对象
        """
        checkpoint_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_dir = self.storage_path / "checkpoints" / checkpoint_id
        checkpoint_dir.mkdir(exist_ok=True)

        metadata = CheckpointMetadata(
            checkpoint_id=checkpoint_id,
            timestamp=datetime.now(),
            description=description or f"Checkpoint {checkpoint_id}",
            tags=tags or [],
            checkpoint_dir=str(checkpoint_dir),
        )

        logger.info(f"📦 创建检查点: {checkpoint_id}")

        # 1. 持久化workflow模式
        if workflow_memory:
            await self._persist_workflow_patterns(
                workflow_memory, checkpoint_dir / "workflow_patterns"
            )
            metadata.workflow_patterns = len(workflow_memory.patterns)

        # 2. 持久化工具性能指标
        if tool_registry:
            await self._persist_tool_metrics(tool_registry, checkpoint_dir / "tool_metrics")
            metadata.tools = len(tool_registry._tools)

        # 3. 持久化Hook状态
        if hook_registry:
            await self._persist_hook_states(hook_registry, checkpoint_dir / "hook_states")
            metadata.hooks = len(hook_registry._hooks)

        # 4. 保存元数据
        metadata_file = checkpoint_dir / "metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata.to_dict(), f, ensure_ascii=False, indent=2)

        # 5. 更新索引
        self._checkpoints[checkpoint_id] = metadata
        self._save_checkpoint_index()

        logger.info(f"✅ 检查点已创建: {checkpoint_id}")

        return metadata

    async def restore_checkpoint(
        self,
        checkpoint_id: str,
        workflow_memory: Any | None = None,
        tool_registry: ToolRegistry | None = None,
        hook_registry: HookRegistry | None = None,
    ) -> bool:
        """
        从检查点恢复系统状态

        Args:
            checkpoint_id: 检查点ID
            workflow_memory: CrossTaskWorkflowMemory实例 (可选)
            tool_registry: ToolRegistry实例 (可选)
            hook_registry: HookRegistry实例 (可选)

        Returns:
            是否恢复成功
        """
        if checkpoint_id not in self._checkpoints:
            logger.error(f"❌ 检查点不存在: {checkpoint_id}")
            return False

        metadata = self._checkpoints[checkpoint_id]
        checkpoint_dir = Path(metadata.checkpoint_dir)

        if not checkpoint_dir.exists():
            logger.error(f"❌ 检查点目录不存在: {checkpoint_dir}")
            return False

        logger.info(f"🔄 恢复检查点: {checkpoint_id}")

        try:
            # 1. 恢复workflow模式
            if workflow_memory:
                await self._restore_workflow_patterns(
                    workflow_memory, checkpoint_dir / "workflow_patterns"
                )
                logger.info(f"✅ 已恢复{metadata.workflow_patterns}个workflow模式")

            # 2. 恢复工具性能指标
            if tool_registry:
                await self._restore_tool_metrics(tool_registry, checkpoint_dir / "tool_metrics")
                logger.info(f"✅ 已恢复{metadata.tools}个工具的性能指标")

            # 3. 恢复Hook状态
            if hook_registry:
                await self._restore_hook_states(hook_registry, checkpoint_dir / "hook_states")
                logger.info(f"✅ 已恢复{metadata.hooks}个hooks的状态")

            logger.info(f"✅ 检查点恢复完成: {checkpoint_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 恢复检查点失败: {e}")
            return False

    async def _persist_workflow_patterns(self, memory: Any, target_dir: Path):
        """持久化workflow模式"""
        # workflow模式已经由CrossTaskWorkflowMemory自行持久化
        # 这里只需要复制现有的模式文件
        import shutil

        source_dir = Path(memory.storage_path) / "patterns"
        if source_dir.exists():
            shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)

    async def _restore_workflow_patterns(self, memory: Any, source_dir: Path):
        """恢复workflow模式"""
        # workflow模式恢复由CrossTaskWorkflowMemory自行处理
        # 这里只需要确保文件存在
        pass

    async def _persist_tool_metrics(self, registry: ToolRegistry, target_dir: Path):
        """持久化工具性能指标"""
        target_dir.mkdir(exist_ok=True)

        metrics_data = {}

        for tool_id, tool in registry._tools.items():
            metrics_data[tool_id] = {
                "tool_id": tool_id,
                "performance": {
                    "total_calls": tool.performance.total_calls,
                    "successful_calls": tool.performance.successful_calls,
                    "failed_calls": tool.performance.failed_calls,
                    "avg_execution_time": tool.performance.avg_execution_time,
                    "min_execution_time": tool.performance.min_execution_time,
                    "max_execution_time": tool.performance.max_execution_time,
                    "success_rate": tool.performance.success_rate,
                },
                "last_used": (
                    tool.performance.last_used.isoformat() if tool.performance.last_used else None
                ),
            }

        # 保存为JSON
        metrics_file = target_dir / "tool_metrics.json"
        with open(metrics_file, "w", encoding="utf-8") as f:
            json.dump(metrics_data, f, ensure_ascii=False, indent=2)

        logger.debug(f"💾 工具性能指标已保存: {len(metrics_data)}个工具")

    async def _restore_tool_metrics(self, registry: ToolRegistry, source_dir: Path):
        """恢复工具性能指标"""
        metrics_file = source_dir / "tool_metrics.json"

        if not metrics_file.exists():
            logger.warning(f"⚠️ 工具性能指标文件不存在: {metrics_file}")
            return

        try:
            with open(metrics_file, encoding="utf-8") as f:
                metrics_data = json.load(f)

            for tool_id, data in metrics_data.items():
                tool = registry._tools.get(tool_id)
                if not tool:
                    continue

                perf_data = data["performance"]
                tool.performance.total_calls = perf_data["total_calls"]
                tool.performance.successful_calls = perf_data["successful_calls"]
                tool.performance.failed_calls = perf_data["failed_calls"]
                tool.performance.avg_execution_time = perf_data["avg_execution_time"]
                tool.performance.min_execution_time = perf_data["min_execution_time"]
                tool.performance.max_execution_time = perf_data["max_execution_time"]
                tool.performance.success_rate = perf_data["success_rate"]

                if data.get("last_used"):
                    tool.performance.last_used = datetime.fromisoformat(data["last_used"])

            logger.debug(f"✅ 工具性能指标已恢复: {len(metrics_data)}个工具")

        except Exception as e:
            logger.error(f"❌ 恢复工具性能指标失败: {e}")

    async def _persist_hook_states(self, registry: HookRegistry, target_dir: Path):
        """持久化Hook状态"""
        target_dir.mkdir(exist_ok=True)

        hooks_data = {}

        for hook_type, hooks in registry._hooks.items():
            hooks_data[hook_type.value] = [
                {
                    "name": hook.name,
                    "hook_type": hook.hook_type.value,
                    "priority": hook.priority,
                    "enabled": hook.enabled,
                }
                for hook in hooks
            ]

        # 保存为JSON
        hooks_file = target_dir / "hook_states.json"
        with open(hooks_file, "w", encoding="utf-8") as f:
            json.dump(hooks_data, f, ensure_ascii=False, indent=2)

        logger.debug(f"💾 Hook状态已保存: {sum(len(h) for h in hooks_data.values())}个hooks")

    async def _restore_hook_states(self, registry: HookRegistry, source_dir: Path):
        """恢复Hook状态"""
        hooks_file = source_dir / "hook_states.json"

        if not hooks_file.exists():
            logger.warning(f"⚠️ Hook状态文件不存在: {hooks_file}")
            return

        try:
            with open(hooks_file, encoding="utf-8") as f:
                hooks_data = json.load(f)

            for hook_type_value, hooks_list in hooks_data.items():
                hook_type = HookType(hook_type_value)

                for hook_data in hooks_list:
                    # 更新现有hooks的状态
                    for hook in registry._hooks.get(hook_type, []):
                        if hook.name == hook_data["name"]:
                            hook.priority = hook_data["priority"]
                            hook.enabled = hook_data["enabled"]

            logger.debug("✅ Hook状态已恢复")

        except Exception as e:
            logger.error(f"❌ 恢复Hook状态失败: {e}")

    def list_checkpoints(self, tag_filter: str | None = None) -> list[CheckpointMetadata]:
        """
        列出所有检查点

        Args:
            tag_filter: 标签过滤器 (可选)

        Returns:
            CheckpointMetadata列表,按时间倒序
        """
        checkpoints = list(self._checkpoints.values())

        if tag_filter:
            checkpoints = [cp for cp in checkpoints if tag_filter in cp.tags]

        checkpoints.sort(key=lambda cp: cp.timestamp, reverse=True)

        return checkpoints

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """
        删除检查点

        Args:
            checkpoint_id: 检查点ID

        Returns:
            是否删除成功
        """
        if checkpoint_id not in self._checkpoints:
            logger.warning(f"⚠️ 检查点不存在: {checkpoint_id}")
            return False

        metadata = self._checkpoints[checkpoint_id]
        checkpoint_dir = Path(metadata.checkpoint_dir)

        try:
            # 删除目录
            import shutil

            if checkpoint_dir.exists():
                shutil.rmtree(checkpoint_dir)

            # 从索引中移除
            del self._checkpoints[checkpoint_id]
            self._save_checkpoint_index()

            logger.info(f"🗑️ 检查点已删除: {checkpoint_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 删除检查点失败: {e}")
            return False

    async def auto_checkpoint(
        self,
        workflow_memory: Any | None = None,
        tool_registry: ToolRegistry | None = None,
        hook_registry: HookRegistry | None = None,
    ):
        """
        自动检查点(后台任务)

        Args:
            workflow_memory: CrossTaskWorkflowMemory实例
            tool_registry: ToolRegistry实例
            hook_registry: HookRegistry实例
        """
        if not self.enable_auto_checkpoint:
            return

        while True:
            try:
                await asyncio.sleep(self.checkpoint_interval)

                await self.create_checkpoint(
                    workflow_memory=workflow_memory,
                    tool_registry=tool_registry,
                    hook_registry=hook_registry,
                    description="Auto checkpoint",
                    tags=["auto"],
                )

                logger.debug("🔄 自动检查点已完成")

            except asyncio.CancelledError:
                logger.info("⏹️ 自动检查点任务已取消")
                break
            except Exception as e:
                logger.error(f"❌ 自动检查点失败: {e}")


__all__ = ["CheckpointMetadata", "StatePersistenceManager"]
