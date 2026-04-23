#!/usr/bin/env python3
from __future__ import annotations
"""
增量更新机制
Incremental Update Mechanism

支持知识图谱的增量更新、版本控制和数据同步
作者: 小诺·双鱼座
创建时间: 2025-12-21
版本: v1.0.0 "实时同步"
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ..knowledge.patent_analysis.enhanced_knowledge_graph import EnhancedPatentKnowledgeGraph

logger = logging.getLogger(__name__)


class UpdateType(Enum):
    """更新类型"""

    CREATE = "create"  # 创建节点/边
    UPDATE = "update"  # 更新节点
    DELETE = "delete"  # 删除节点/边
    BATCH_CREATE = "batch_create"  # 批量创建
    BATCH_UPDATE = "batch_update"  # 批量更新
    BATCH_DELETE = "batch_delete"  # 批量删除


class UpdateStatus(Enum):
    """更新状态"""

    PENDING = "pending"  # 待处理
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    ROLLED_BACK = "rolled_back"  # 已回滚


@dataclass
class UpdateRecord:
    """更新记录"""

    update_id: str
    update_type: UpdateType
    target_type: str  # 'node' or 'edge'
    target_id: str
    data: dict[str, Any]
    timestamp: datetime
    status: UpdateStatus = UpdateStatus.PENDING
    checksum: str | None = None
    dependencies: list[str] = field(default_factory=list)
    error_message: str | None = None
    rollback_data: dict[str, Any] | None = None


@dataclass
class UpdateBatch:
    """更新批次"""

    batch_id: str
    updates: list[UpdateRecord]
    created_at: datetime = field(default_factory=datetime.now)
    status: UpdateStatus = UpdateStatus.PENDING
    processed_count: int = 0
    failed_count: int = 0


class IncrementalUpdater:
    """增量更新器"""

    def __init__(self, knowledge_graph: EnhancedPatentKnowledgeGraph | None = None):
        self.knowledge_graph = knowledge_graph
        self.name = "增量更新机制"
        self.version = "1.0.0"
        self._initialized = False
        self.logger = logging.getLogger(self.name)

        # 更新记录存储
        self.update_records: dict[str, UpdateRecord] = {}
        self.pending_updates: list[UpdateRecord] = []

        # 批次管理
        self.batches: dict[str, UpdateBatch] = {}
        self.batch_size = 50

        # 配置
        self.config = {
            "auto_process": True,  # 自动处理更新
            "max_retry_attempts": 3,  # 最大重试次数
            "retry_delay": 1.0,  # 重试延迟(秒)
            "enable_rollback": True,  # 启用回滚
            "checksum_validation": True,  # 校验和验证
            "auto_batch": True,  # 自动批次处理
            "batch_timeout": 30.0,  # 批次超时(秒)
        }

        # 统计信息
        self.stats = {
            "total_updates": 0,
            "successful_updates": 0,
            "failed_updates": 0,
            "rollback_count": 0,
            "last_update_time": None,
        }

    async def initialize(self):
        """初始化增量更新器"""
        try:
            # 如果没有提供知识图谱,创建一个
            if self.knowledge_graph is None:
                self.knowledge_graph = await EnhancedPatentKnowledgeGraph.initialize()

            # 加载历史更新记录
            await self._load_update_history()

            # 启动自动处理器
            if self.config["auto_process"]:
                _task_20_7f0f22 = asyncio.create_task(self._auto_processor())

            self._initialized = True
            self.logger.info("✅ IncrementalUpdater 初始化完成")
            return True

        except Exception as e:
            self.logger.error(f"❌ IncrementalUpdater 初始化失败: {e}")
            return False

    async def add_update(
        self,
        update_type: UpdateType,
        target_type: str,
        target_id: str,
        data: dict[str, Any],        dependencies: list[str] | None = None,
    ) -> str:
        """
        添加更新记录

        Args:
            update_type: 更新类型
            target_type: 目标类型 (node/edge)
            target_id: 目标ID
            data: 更新数据
            dependencies: 依赖的更新ID列表

        Returns:
            str: 更新ID
        """
        update_id = self._generate_update_id()

        # 创建更新记录
        update_record = UpdateRecord(
            update_id=update_id,
            update_type=update_type,
            target_type=target_type,
            target_id=target_id,
            data=data,
            timestamp=datetime.now(),
            dependencies=dependencies or [],
        )

        # 计算校验和
        if self.config["checksum_validation"]:
            update_record.checksum = self._calculate_checksum(data)

        # 存储更新记录
        self.update_records[update_id] = update_record
        self.pending_updates.append(update_record)

        # 自动批次处理
        if self.config["auto_batch"] and len(self.pending_updates) >= self.batch_size:
            await self._process_batch()

        self.logger.info(f"✅ 添加更新记录: {update_id} ({update_type.value})")
        return update_id

    async def add_node(self, node_data: dict[str, Any]) -> str:
        """添加节点更新"""
        return await self.add_update(
            UpdateType.CREATE, "node", node_data.get("node_id", ""), node_data
        )

    async def update_node(self, node_id: str, node_data: dict[str, Any]) -> str:
        """更新节点"""
        return await self.add_update(UpdateType.UPDATE, "node", node_id, node_data)

    async def delete_node(self, node_id: str) -> str:
        """删除节点"""
        # 获取当前节点数据用于回滚
        rollback_data = await self._get_node_data(node_id)

        update_id = await self.add_update(
            UpdateType.DELETE,
            "node",
            node_id,
            {"node_id": node_id},
            rollback_data={"original_data": rollback_data} if rollback_data else None,
        )

        if rollback_data:
            self.update_records[update_id].rollback_data = rollback_data

        return update_id

    async def _process_batch(self) -> str | None:
        """处理批次更新"""
        if not self.pending_updates:
            return None

        batch_id = self._generate_batch_id()
        batch_updates = self.pending_updates[: self.batch_size]

        # 创建批次
        batch = UpdateBatch(batch_id=batch_id, updates=batch_updates)
        self.batches[batch_id] = batch

        # 从待处理列表中移除
        self.pending_updates = self.pending_updates[self.batch_size :]

        # 处理批次
        await self._process_batch_updates(batch)

        return batch_id

    async def _process_batch_updates(self, batch: UpdateBatch):
        """处理批次更新"""
        batch.status = UpdateStatus.PROCESSING
        processed_count = 0
        failed_count = 0

        try:
            # 按依赖关系排序
            sorted_updates = self._sort_updates_by_dependencies(batch.updates)

            for update in sorted_updates:
                try:
                    await self._process_single_update(update)
                    update.status = UpdateStatus.COMPLETED
                    processed_count += 1

                except Exception as e:
                    self.logger.error(f"❌ 处理更新失败 {update.update_id}: {e}")
                    update.status = UpdateStatus.FAILED
                    update.error_message = str(e)
                    failed_count += 1

                    # 尝试回滚
                    if self.config["enable_rollback"]:
                        await self._rollback_update(update)

            # 更新批次状态
            batch.status = UpdateStatus.COMPLETED
            batch.processed_count = processed_count
            batch.failed_count = failed_count

            self.logger.info(
                f"✅ 批次处理完成: {batch.batch_id} ({processed_count} 成功, {failed_count} 失败)"
            )

        except Exception as e:
            self.logger.error(f"❌ 批次处理失败 {batch.batch_id}: {e}")
            batch.status = UpdateStatus.FAILED

    async def _process_single_update(self, update: UpdateRecord):
        """处理单个更新"""
        update.status = UpdateStatus.PROCESSING

        # 验证校验和
        if self.config["checksum_validation"] and update.checksum:
            current_checksum = self._calculate_checksum(update.data)
            if current_checksum != update.checksum:
                raise ValueError(f"数据校验和验证失败: {current_checksum} != {update.checksum}")

        # 检查依赖
        await self._check_dependencies(update)

        # 处理不同类型的更新
        if update.target_type == "node":
            if update.update_type in [UpdateType.CREATE, UpdateType.UPDATE]:
                await self.knowledge_graph.add_node(update.data)
            elif update.update_type == UpdateType.DELETE:
                await self._delete_node_from_graph(update.target_id)

        # 更新统计
        self.stats["total_updates"] += 1
        self.stats["last_update_time"] = datetime.now()

        # 保存更新历史
        await self._save_update_record(update)

    async def _delete_node_from_graph(self, node_id: str):
        """从图中删除节点"""
        # 这里需要实现实际的节点删除逻辑
        # 由于现有的知识图谱可能没有删除方法,这里模拟实现
        self.logger.info(f"🗑️ 删除节点: {node_id}")

    async def _check_dependencies(self, update: UpdateRecord):
        """检查依赖关系"""
        for dep_id in update.dependencies:
            if dep_id in self.update_records:
                dep_update = self.update_records[dep_id]
                if dep_update.status in [UpdateStatus.FAILED, UpdateStatus.ROLLED_BACK]:
                    raise ValueError(f"依赖更新失败: {dep_id}")

    async def _rollback_update(self, update: UpdateRecord):
        """回滚更新"""
        try:
            if update.update_type == UpdateType.CREATE:
                # 创建回滚 = 删除
                await self._delete_node_from_graph(update.target_id)

            elif update.update_type == UpdateType.DELETE:
                # 删除回滚 = 重新创建
                if update.rollback_data and "original_data" in update.rollback_data:
                    await self.knowledge_graph.add_node(update.rollback_data["original_data"])

            elif update.update_type == UpdateType.UPDATE:
                # 更新回滚 = 恢复原始数据
                if update.rollback_data:
                    await self.knowledge_graph.add_node(update.rollback_data)

            update.status = UpdateStatus.ROLLED_BACK
            self.stats["rollback_count"] += 1

            self.logger.info(f"🔄 更新已回滚: {update.update_id}")

        except Exception as e:
            self.logger.error(f"❌ 回滚失败 {update.update_id}: {e}")

    def _sort_updates_by_dependencies(self, updates: list[UpdateRecord]) -> list[UpdateRecord]:
        """根据依赖关系排序更新"""
        # 使用拓扑排序
        sorted_updates = []
        visited = set()
        temp_visited = set()

        def visit(update: UpdateRecord) -> Any:
            if update.update_id in temp_visited:
                raise ValueError(f"检测到循环依赖: {update.update_id}")

            if update.update_id in visited:
                return

            temp_visited.add(update.update_id)

            # 访问依赖
            for dep_id in update.dependencies:
                if dep_id in self.update_records:
                    visit(self.update_records[dep_id])

            temp_visited.remove(update.update_id)
            visited.add(update.update_id)
            sorted_updates.append(update)

        for update in updates:
            if update.update_id not in visited:
                visit(update)

        return sorted_updates

    async def _auto_processor(self):
        """自动处理器"""
        while True:
            try:
                if self.pending_updates:
                    if len(self.pending_updates) >= self.batch_size:
                        await self._process_batch()

                await asyncio.sleep(1.0)  # 每秒检查一次

            except Exception as e:
                self.logger.error(f"❌ 自动处理器错误: {e}")
                await asyncio.sleep(5.0)  # 错误后等待5秒

    def _generate_update_id(self) -> str:
        """生成更新ID"""
        import uuid

        return f"update_{uuid.uuid4().hex[:8]}"

    def _generate_batch_id(self) -> str:
        """生成批次ID"""
        import uuid

        return f"batch_{uuid.uuid4().hex[:8]}"

    def _calculate_checksum(self, data: dict[str, Any]) -> str:
        """计算数据校验和"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(data_str.encode('utf-8'), usedforsecurity=False).hexdigest()

    async def _get_node_data(self, node_id: str) -> dict[str, Any] | None:
        """获取节点数据"""
        try:
            # 从知识图谱获取节点数据
            node_context = await self.knowledge_graph.get_node_with_context(node_id)
            if node_context and "node" in node_context:
                return node_context["node"]
        except Exception as e:
            self.logger.warning(f"⚠️ 获取节点数据失败 {node_id}: {e}")

        return None

    async def _load_update_history(self):
        """加载更新历史"""
        try:
            # 这里应该从持久化存储加载历史记录
            # 目前使用内存存储
            pass
        except Exception as e:
            self.logger.warning(f"⚠️ 加载更新历史失败: {e}")

    async def _save_update_record(self, update: UpdateRecord):
        """保存更新记录"""
        try:
            # 这里应该保存到持久化存储
            # 目前使用内存存储
            pass
        except Exception as e:
            self.logger.warning(f"⚠️ 保存更新记录失败: {e}")

    def get_pending_count(self) -> int:
        """获取待处理更新数量"""
        return len(self.pending_updates)

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()

    def get_update_status(self, update_id: str) -> UpdateStatus | None:
        """获取更新状态"""
        if update_id in self.update_records:
            return self.update_records[update_id].status
        return None

    async def close(self):
        """关闭增量更新器"""
        # 等待所有待处理更新完成
        while self.pending_updates:
            await self._process_batch()
            await asyncio.sleep(0.5)

        self._initialized = False
        self.logger.info("✅ IncrementalUpdater 已关闭")


# 便捷函数
async def create_incremental_updater(
    knowledge_graph: EnhancedPatentKnowledgeGraph | None = None,
) -> IncrementalUpdater:
    """创建增量更新器实例"""
    updater = IncrementalUpdater(knowledge_graph)
    await updater.initialize()
    return updater
