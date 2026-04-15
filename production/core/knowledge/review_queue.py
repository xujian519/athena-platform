#!/usr/bin/env python3
"""
知识审核队列管理系统
Knowledge Review Queue Management System

实现严格的人工审核流程:
- 待审核知识入库
- 队列管理(提交、审批、拒绝)
- 状态流转(DRAFT → REVIEWED → APPROVED/EXCELLENT)

作者: 小诺·双鱼公主
创建时间: 2025-12-27
版本: v1.0.0 "审核队列"
"""

from __future__ import annotations
import json
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from unified_knowledge_item import (
    KnowledgeCategory,
    KnowledgeType,
    QualityLevel,
    UnifiedKnowledgeItem,
    create_knowledge_item,
)

logger = logging.getLogger(__name__)


class ReviewStatus(Enum):
    """审核状态"""

    PENDING = "pending"  # 待审核
    APPROVED = "approved"  # 已批准
    REJECTED = "rejected"  # 已拒绝
    IN_REVIEW = "in_review"  # 审核中


@dataclass
class ReviewTask:
    """审核任务"""

    item: UnifiedKnowledgeItem
    status: ReviewStatus = ReviewStatus.PENDING
    submitted_at: datetime = field(default_factory=datetime.now)
    reviewed_at: datetime | None = None
    reviewer: str = ""
    review_notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "item": self.item.to_summary_dict(),
            "status": self.status.value,
            "submitted_at": self.submitted_at.isoformat(),
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "reviewer": self.reviewer,
            "review_notes": self.review_notes,
        }


class ReviewQueue:
    """
    知识审核队列

    管理待审核的知识条目,实现严格的质量控制流程。
    """

    def __init__(self, storage_path: Path | None = None):
        """初始化审核队列

        Args:
            storage_path: 存储路径
        """
        self.storage_path = storage_path or Path(
            "/Users/xujian/Athena工作平台/knowledge_review_queue"
        )
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # 队列存储
        self.pending_queue: deque[ReviewTask] = deque()
        self.approved_items: list[UnifiedKnowledgeItem] = []
        self.rejected_items: list[UnifiedKnowledgeItem] = []

        # 加载已有队列
        self._load_queue()

        logger.info("📝 知识审核队列初始化完成")
        logger.info(f"   存储路径: {self.storage_path}")
        logger.info(f"   待审核: {len(self.pending_queue)}条")
        logger.info(f"   已批准: {len(self.approved_items)}条")
        logger.info(f"   已拒绝: {len(self.rejected_items)}条")

    def _load_queue(self) -> Any:
        """加载已有队列"""
        # 加载待审核队列
        pending_file = self.storage_path / "pending_queue.json"
        if pending_file.exists():
            try:
                with open(pending_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for task_data in data:
                        item = self._dict_to_item(task_data["item"])
                        task = ReviewTask(
                            item=item,
                            status=ReviewStatus(task_data["status"]),
                            submitted_at=datetime.fromisoformat(task_data["submitted_at"]),
                            reviewer=task_data.get("reviewer", ""),
                            review_notes=task_data.get("review_notes", ""),
                        )
                        if task_data.get("reviewed_at"):
                            task.reviewed_at = datetime.fromisoformat(task_data["reviewed_at"])
                        self.pending_queue.append(task)
            except Exception as e:
                logger.warning(f"加载待审核队列失败: {e}")

        # 加载已批准列表
        approved_file = self.storage_path / "approved_items.json"
        if approved_file.exists():
            try:
                with open(approved_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for item_data in data:
                        item = self._dict_to_item(item_data)
                        self.approved_items.append(item)
            except Exception as e:
                logger.warning(f"加载已批准列表失败: {e}")

    def _dict_to_item(self, data: dict[str, Any]) -> UnifiedKnowledgeItem:
        """从字典恢复知识条目"""
        from unified_knowledge_item import QualityMetrics

        # 恢复质量指标
        quality_metrics_data = data.get("quality_metrics", {})
        quality_metrics = QualityMetrics(
            completeness=quality_metrics_data.get("completeness", 0.0),
            accuracy=quality_metrics_data.get("accuracy", 0.0),
            usefulness=quality_metrics_data.get("usefulness", 0.0),
            clarity=quality_metrics_data.get("clarity", 0.0),
        )

        # 恢复知识条目
        item = UnifiedKnowledgeItem(
            id=data["id"],
            type=KnowledgeType(data["type"]),
            category=KnowledgeCategory(data["category"]),
            title=data["title"],
            description=data["description"],
            content=data["content"],
            quality_level=QualityLevel(data["quality_level"]),
            quality_metrics=quality_metrics,
            ai_quality_score=data.get("ai_quality_score", 0.0),
            reviewed_by=data.get("reviewed_by", ""),
            reviewed_at=(
                datetime.fromisoformat(data["reviewed_at"]) if data.get("reviewed_at") else None
            ),
            review_notes=data.get("review_notes", ""),
            confidence=data.get("confidence", 1.0),
            tags=data.get("tags", []),
            source=data.get("source", "manual"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            usage_count=data.get("usage_count", 0),
            effectiveness_score=data.get("effectiveness_score", 0.0),
            last_accessed_at=(
                datetime.fromisoformat(data["last_accessed_at"])
                if data.get("last_accessed_at")
                else None
            ),
            nebula_node_id=data.get("nebula_node_id"),
            qdrant_point_id=data.get("qdrant_point_id"),
        )

        return item

    def submit_for_review(
        self,
        title: str,
        description: str,
        content: dict[str, Any],        knowledge_type: KnowledgeType,
        category: KnowledgeCategory,
        tags: list[str] | None = None,
        source: str = "manual",
    ) -> ReviewTask:
        """提交知识到审核队列

        Args:
            title: 标题
            description: 描述
            content: 内容
            knowledge_type: 知识类型
            category: 知识分类
            tags: 标签
            source: 来源

        Returns:
            ReviewTask: 审核任务
        """
        # 创建知识条目
        item = create_knowledge_item(
            title=title,
            description=description,
            content=content,
            knowledge_type=knowledge_type,
            category=category,
            tags=tags,
            source=source,
        )

        # 创建审核任务
        task = ReviewTask(item=item, status=ReviewStatus.PENDING)

        # 添加到队列
        self.pending_queue.append(task)

        # 保存队列
        self._save_queue()

        logger.info(f"✅ 知识已提交到审核队列: {item.id} - {title}")
        return task

    def get_pending_tasks(self, limit: int | None = None) -> list[ReviewTask]:
        """获取待审核任务

        Args:
            limit: 数量限制

        Returns:
            待审核任务列表
        """
        tasks = list(self.pending_queue)
        if limit:
            tasks = tasks[:limit]
        return tasks

    def approve(
        self, task_index: int, reviewer: str, quality_level: QualityLevel, notes: str = ""
    ) -> UnifiedKnowledgeItem:
        """批准知识

        Args:
            task_index: 任务索引
            reviewer: 审核人(如"爸爸")
            quality_level: 质量等级
            notes: 审核意见

        Returns:
            批准的知识条目
        """
        if task_index >= len(self.pending_queue):
            raise IndexError(f"任务索引超出范围: {task_index}")

        # 获取任务
        task = self.pending_queue[task_index]

        # 批准知识
        task.item.approve(reviewer, quality_level, notes)

        # 更新任务状态
        task.status = ReviewStatus.APPROVED
        task.reviewed_at = datetime.now()
        task.reviewer = reviewer
        task.review_notes = notes

        # 从待审核队列移除
        self.pending_queue.remove(task)

        # 添加到已批准列表
        self.approved_items.append(task.item)

        # 保存队列
        self._save_queue()

        logger.info(f"✅ 知识已批准: {task.item.id} - {task.item.title}")
        logger.info(f"   审核人: {reviewer}")
        logger.info(f"   质量等级: {quality_level.get_label()}")

        return task.item

    def reject(self, task_index: int, reviewer: str, notes: str = "") -> Any:
        """拒绝知识

        Args:
            task_index: 任务索引
            reviewer: 审核人
            notes: 拒绝原因
        """
        if task_index >= len(self.pending_queue):
            raise IndexError(f"任务索引超出范围: {task_index}")

        # 获取任务
        task = self.pending_queue[task_index]

        # 拒绝知识
        task.item.reject(reviewer, notes)

        # 更新任务状态
        task.status = ReviewStatus.REJECTED
        task.reviewed_at = datetime.now()
        task.reviewer = reviewer
        task.review_notes = notes

        # 从待审核队列移除
        self.pending_queue.remove(task)

        # 添加到已拒绝列表
        self.rejected_items.append(task.item)

        # 保存队列
        self._save_queue()

        logger.info(f"❌ 知识已拒绝: {task.item.id} - {task.item.title}")
        logger.info(f"   审核人: {reviewer}")
        logger.info(f"   拒绝原因: {notes}")

    def get_statistics(self) -> dict[str, Any]:
        """获取队列统计

        Returns:
            统计信息字典
        """
        return {
            "pending_count": len(self.pending_queue),
            "approved_count": len(self.approved_items),
            "rejected_count": len(self.rejected_items),
            "total_reviewed": len(self.approved_items) + len(self.rejected_items),
            "approval_rate": len(self.approved_items)
            / max(1, len(self.approved_items) + len(self.rejected_items)),
        }

    def _save_queue(self) -> Any:
        """保存队列到文件"""
        # 保存待审核队列
        pending_file = self.storage_path / "pending_queue.json"
        with open(pending_file, "w", encoding="utf-8") as f:
            data = [task.to_dict() for task in self.pending_queue]
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 保存已批准列表
        approved_file = self.storage_path / "approved_items.json"
        with open(approved_file, "w", encoding="utf-8") as f:
            data = [item.to_dict() for item in self.approved_items]
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 保存已拒绝列表
        rejected_file = self.storage_path / "rejected_items.json"
        with open(rejected_file, "w", encoding="utf-8") as f:
            data = [item.to_dict() for item in self.rejected_items]
            json.dump(data, f, ensure_ascii=False, indent=2)


# 全局实例
_review_queue: ReviewQueue = None


def get_review_queue() -> ReviewQueue:
    """获取审核队列单例"""
    global _review_queue
    if _review_queue is None:
        _review_queue = ReviewQueue()
    return _review_queue


# 便捷函数
def submit_knowledge(
    title: str,
    description: str,
    content: dict[str, Any],    knowledge_type: KnowledgeType,
    category: KnowledgeCategory,
    tags: list[str] | None = None,
) -> str:
    """便捷函数:提交知识到审核队列

    Args:
        title: 标题
        description: 描述
        content: 内容
        knowledge_type: 知识类型
        category: 知识分类
        tags: 标签

    Returns:
        任务ID(知识ID)
    """
    queue = get_review_queue()
    task = queue.submit_for_review(
        title=title,
        description=description,
        content=content,
        knowledge_type=knowledge_type,
        category=category,
        tags=tags,
    )
    return task.item.id


if __name__ == "__main__":
    # 测试审核队列
    print("🧪 测试知识审核队列")
    print("=" * 80)

    queue = get_review_queue()

    # 提交一些测试知识
    print("\n📝 提交测试知识到审核队列...")

    test_knowledges = [
        {
            "title": "四层系统架构模式",
            "description": "Athena平台采用的四层架构",
            "content": {"layers": ["决策层", "应用层", "服务层", "基础设施层"]},
            "type": KnowledgeType.ARCHITECTURE_PATTERN,
            "category": KnowledgeCategory.SYSTEM_ARCHITECTURE,
            "tags": ["architecture", "design"],
        },
        {
            "title": "从定性到定量的综合集成法",
            "description": "基于钱学森系统工程思想的决策方法",
            "content": {"steps": ["定性判断", "专家会诊", "综合集成", "明确决策"]},
            "type": KnowledgeType.BEST_PRACTICE,
            "category": KnowledgeCategory.DECISION_MAKING,
            "tags": ["decision", "systems_engineering"],
        },
        {
            "title": "智能体协同模式选择指南",
            "description": "根据任务特点选择合适的协同模式",
            "content": {"modes": ["PARALLEL", "SEQUENTIAL", "PIPELINE", "COLLABORATIVE"]},
            "type": KnowledgeType.BEST_PRACTICE,
            "category": KnowledgeCategory.AGENT_COORDINATION,
            "tags": ["collaboration", "agents"],
        },
    ]

    for knowledge in test_knowledges:
        task_id = submit_knowledge(
            title=knowledge["title"],
            description=knowledge["description"],
            content=knowledge["content"],
            knowledge_type=knowledge["type"],
            category=knowledge["category"],
            tags=knowledge["tags"],
        )
        print(f"   ✅ 已提交: {task_id} - {knowledge['title']}")

    # 查看队列统计
    print("\n📊 队列统计:")
    stats = queue.get_statistics()
    print(f"   待审核: {stats['pending_count']}条")
    print(f"   已批准: {stats['approved_count']}条")
    print(f"   已拒绝: {stats['rejected_count']}条")
    print(f"   批准率: {stats['approval_rate']:.1%}")

    # 查看待审核任务
    print("\n📋 待审核任务:")
    pending_tasks = queue.get_pending_tasks()
    for i, task in enumerate(pending_tasks):
        print(f"   [{i}] {task.item.title}")
        print(f"       描述: {task.item.description[:50]}...")
        print(f"       类型: {task.item.type.value}")
        print(f"       提交时间: {task.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}")

    # 模拟审核
    if len(pending_tasks) > 0:
        print("\n✅ 模拟审核:")
        print(f"   批准第1个任务: {pending_tasks[0].item.title}")
        queue.approve(
            task_index=0,
            reviewer="爸爸",
            quality_level=QualityLevel.EXCELLENT,
            notes="核心架构知识,质量优秀!",
        )

        # 更新统计
        stats = queue.get_statistics()
        print("\n📊 审核后统计:")
        print(f"   待审核: {stats['pending_count']}条")
        print(f"   已批准: {stats['approved_count']}条")
        print(f"   批准率: {stats['approval_rate']:.1%}")

    print("\n✅ 测试完成!")
