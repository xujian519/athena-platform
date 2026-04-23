#!/usr/bin/env python3

"""
模式索引管理器

管理workflow模式的索引,支持快速查找和统计。

Author: Athena平台团队
Created: 2026-01-20
Version: v1.0.0
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from core.framework.memory.workflow_pattern import WorkflowPattern

logger = logging.getLogger(__name__)


class PatternIndex:
    """模式索引条目"""

    def __init__(
        self,
        pattern_id: str,
        name: str,
        domain: str,
        task_type: str,
        success_rate: float,
        usage_count: int,
        created_at: str,
        updated_at: str,
    ):
        self.pattern_id = pattern_id
        self.name = name
        self.domain = domain
        self.task_type = task_type
        self.success_rate = success_rate
        self.usage_count = usage_count
        self.created_at = created_at
        self.updated_at = updated_at


class PatternIndexManager:
    """
    模式索引管理器

    维护workflow模式的索引,支持快速查找、统计和查询。
    """

    def __init__(self, index_file: str = "data/workflow_memory/pattern_index.json"):
        """
        初始化索引管理器

        Args:
            index_file: 索引文件路径
        """
        self.index_file = Path(index_file)
        self.index_file.parent.mkdir(parents=True, exist_ok=True)

        self.indexes: dict[str, PatternIndex] = {}

        # 加载已有索引
        self._load_index()

        logger.info(f"📇 PatternIndexManager初始化 (索引数: {len(self.indexes)})")

    def _load_index(self) -> Any:
        """加载索引文件"""

        if not self.index_file.exists():
            logger.info("📄 索引文件不存在,创建新索引")
            return

        try:
            with open(self.index_file, encoding="utf-8") as f:
                data = json.load(f)

            for pattern_id, pattern_data in data.get("patterns", {}).items():
                self.indexes[pattern_id] = PatternIndex(
                    pattern_id=pattern_id,
                    name=pattern_data["name"],
                    domain=pattern_data["domain"],
                    task_type=pattern_data["task_type"],
                    success_rate=pattern_data["success_rate"],
                    usage_count=pattern_data["usage_count"],
                    created_at=pattern_data["created_at"],
                    updated_at=pattern_data["updated_at"],
                )

            logger.info(f"📂 已加载{len(self.indexes)}个索引")

        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise
    async def update_index(self, pattern: WorkflowPattern):
        """
        更新索引

        Args:
            pattern: WorkflowPattern对象
        """
        # 处理domain类型
        domain_value = pattern.domain if isinstance(pattern.domain, str) else pattern.domain.value

        index = PatternIndex(
            pattern_id=pattern.pattern_id,
            name=pattern.name,
            domain=domain_value,
            task_type=pattern.task_type,
            success_rate=pattern.success_rate,
            usage_count=pattern.usage_count,
            created_at=pattern.created_at.isoformat(),
            updated_at=pattern.updated_at.isoformat(),
        )

        self.indexes[pattern.pattern_id] = index

        # 保存到文件
        await self._save_index()

        logger.debug(f"📝 索引已更新: {pattern.pattern_id}")

    async def _save_index(self):
        """保存索引到文件"""

        data = {
            "patterns": {
                pattern_id: {
                    "name": index.name,
                    "domain": index.domain,
                    "task_type": index.task_type,
                    "success_rate": index.success_rate,
                    "usage_count": index.usage_count,
                    "created_at": index.created_at,
                    "updated_at": index.updated_at,
                }
                for pattern_id, index in self.indexes.items()
            },
            "last_updated": datetime.now().isoformat(),
        }

        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.debug(f"💾 索引已保存: {len(self.indexes)}个条目")

    def find_by_domain(self, domain: str) -> list[PatternIndex]:
        """
        按领域查找模式

        Args:
            domain: 领域名称

        Returns:
            匹配的模式索引列表
        """
        return [index for index in self.indexes.values() if index.domain == domain]

    def find_by_task_type(self, task_type: str) -> list[PatternIndex]:
        """
        按任务类型查找模式

        Args:
            task_type: 任务类型

        Returns:
            匹配的模式索引列表
        """
        return [index for index in self.indexes.values() if index.task_type == task_type]

    def find_by_success_rate(self, min_success_rate: float = 0.0) -> list[PatternIndex]:
        """
        按成功率查找模式

        Args:
            min_success_rate: 最小成功率

        Returns:
            匹配的模式索引列表
        """
        return [index for index in self.indexes.values() if index.success_rate >= min_success_rate]

    def get_most_used(self, limit: int = 10) -> list[PatternIndex]:
        """
        获取最常用的模式

        Args:
            limit: 返回数量限制

        Returns:
            按使用次数排序的模式列表
        """
        return sorted(self.indexes.values(), key=lambda x: x.usage_count, reverse=True)[:limit]

    def get_statistics(self) -> dict[str, Any]:
        """
        获取索引统计信息

        Returns:
            统计信息字典
        """
        if not self.indexes:
            return {
                "total_patterns": 0,
                "domains": {},
                "task_types": {},
                "avg_success_rate": 0.0,
                "total_usage": 0,
            }

        # 按领域统计
        domain_stats: dict[str, dict] = {}
        task_type_stats: dict[str, dict] = {}

        total_success_rate = 0.0
        total_usage = 0

        for index in self.indexes.values():
            # 领域统计
            if index.domain not in domain_stats:
                domain_stats[index.domain] = {"count": 0, "total_success": 0.0, "total_usage": 0}

            domain_stats[index.domain]["count"] += 1
            domain_stats[index.domain]["total_success"] += index.success_rate
            domain_stats[index.domain]["total_usage"] += index.usage_count

            # 任务类型统计
            if index.task_type not in task_type_stats:
                task_type_stats[index.task_type] = {"count": 0, "total_success": 0.0}

            task_type_stats[index.task_type]["count"] += 1
            task_type_stats[index.task_type]["total_success"] += index.success_rate

            total_success_rate += index.success_rate
            total_usage += index.usage_count

        return {
            "total_patterns": len(self.indexes),
            "domains": {
                domain: {
                    "count": stats["count"],
                    "avg_success_rate": stats["total_success"] / stats["count"],
                    "total_usage": stats["total_usage"],
                }
                for domain, stats in domain_stats.items()
            },
            "task_types": {
                task_type: {
                    "count": stats["count"],
                    "avg_success_rate": stats["total_success"] / stats["count"],
                }
                for task_type, stats in task_type_stats.items()
            },
            "avg_success_rate": total_success_rate / len(self.indexes),
            "total_usage": total_usage,
        }


__all__ = ["PatternIndex", "PatternIndexManager"]

