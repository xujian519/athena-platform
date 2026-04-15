#!/usr/bin/env python3
from __future__ import annotations
"""
统一记忆服务
Unified Memory Service

整合记忆系统的所有功能

作者: 小诺·双鱼公主 v4.0
创建时间: 2025-12-25
版本: 1.0.0
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class MemoryService:
    """统一记忆服务"""

    def __init__(self, config=None):
        self.config = config
        self._hot_memory = {}
        self._warm_memory = {}
        self._cold_memory = {}
        self._stats = {
            "hot_stores": 0,
            "warm_stores": 0,
            "cold_stores": 0,
            "retrievals": 0,
        }

    async def store(
        self,
        key: str,
        value: Any,
        memory_type: str = "hot",
        metadata: dict | None = None,
    ) -> bool:
        """
        存储记忆

        Args:
            key: 记忆键
            value: 记忆值
            memory_type: 记忆类型 (hot/warm/cold/eternal)
            metadata: 元数据

        Returns:
            是否成功
        """
        try:
            memory_entry = {
                "key": key,
                "value": value,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat(),
            }

            if memory_type == "hot":
                self._hot_memory[key] = memory_entry
                self._stats["hot_stores"] += 1
            elif memory_type == "warm":
                self._warm_memory[key] = memory_entry
                self._stats["warm_stores"] += 1
            elif memory_type == "cold":
                self._cold_memory[key] = memory_entry
                self._stats["cold_stores"] += 1
            else:
                logger.warning(f"未知的记忆类型: {memory_type}")
                return False

            logger.debug(f"记忆已存储: {key} ({memory_type})")
            return True

        except Exception as e:
            logger.error(f"记忆存储失败: {e}")
            return False

    async def retrieve(self, key: str, memory_type: str | None = None) -> Any | None:
        """
        检索记忆

        Args:
            key: 记忆键
            memory_type: 记忆类型,None表示搜索所有类型

        Returns:
            记忆值,如果不存在返回None
        """
        self._stats["retrievals"] += 1

        # 如果指定了类型,只在该类型中搜索
        if memory_type:
            memory_dict = getattr(self, f"_{memory_type}_memory", {})
            entry = memory_dict.get(key)
            return entry["value"] if entry else None

        # 按优先级搜索
        for memory_type_name in ["hot", "warm", "cold"]:
            memory_dict = getattr(self, f"_{memory_type_name}_memory", {})
            entry = memory_dict.get(key)
            if entry:
                return entry["value"]

        return None

    async def search(
        self,
        query: str,
        memory_type: str = "hot",
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        搜索记忆

        Args:
            query: 搜索查询
            memory_type: 记忆类型
            limit: 返回数量限制

        Returns:
            搜索结果列表
        """
        memory_dict = getattr(self, f"_{memory_type}_memory", {})

        results = []
        for key, entry in memory_dict.items():
            if query.lower() in str(entry["value"]).lower():
                results.append(
                    {
                        "key": key,
                        "value": entry["value"],
                        "metadata": entry["metadata"],
                        "created_at": entry["created_at"],
                    }
                )
                if len(results) >= limit:
                    break

        return results

    async def delete(self, key: str, memory_type: str | None = None) -> bool:
        """
        删除记忆

        Args:
            key: 记忆键
            memory_type: 记忆类型,None表示从所有类型中删除

        Returns:
            是否成功
        """
        if memory_type:
            memory_dict = getattr(self, f"_{memory_type}_memory", {})
            if key in memory_dict:
                del memory_dict[key]
                return True
            return False

        deleted = False
        for memory_type_name in ["hot", "warm", "cold"]:
            memory_dict = getattr(self, f"_{memory_type_name}_memory", {})
            if key in memory_dict:
                del memory_dict[key]
                deleted = True

        return deleted

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self._stats,
            "hot_memory_size": len(self._hot_memory),
            "warm_memory_size": len(self._warm_memory),
            "cold_memory_size": len(self._cold_memory),
        }

    def get_memory_summary(self) -> dict[str, Any]:
        """获取记忆摘要"""
        return {
            "hot_memory": {
                "count": len(self._hot_memory),
                "keys": list(self._hot_memory.keys()),
            },
            "warm_memory": {
                "count": len(self._warm_memory),
                "keys": list(self._warm_memory.keys()),
            },
            "cold_memory": {
                "count": len(self._cold_memory),
                "keys": list(self._cold_memory.keys()),
            },
        }


# 全局服务实例
_memory_service: MemoryService | None = None


def get_memory_service(config=None) -> MemoryService:
    """获取记忆服务实例"""
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService(config)
    return _memory_service


if __name__ == "__main__":
    # 测试记忆服务
    async def test():
        service = get_memory_service()

        print("🧠 记忆服务测试")
        print("=" * 60)

        # 存储记忆
        await service.store("test_key", {"data": "test_value"}, memory_type="hot")
        await service.store("user_pref", {"theme": "dark"}, memory_type="warm")
        print("✅ 记忆已存储")

        # 检索记忆
        value = await service.retrieve("test_key")
        print(f"📖 检索结果: {value}")

        # 搜索记忆
        results = await service.search("theme", memory_type="warm")
        print(f"🔍 搜索结果: {results}")

        # 获取统计
        stats = service.get_stats()
        print()
        print("📊 统计:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

    asyncio.run(test())
