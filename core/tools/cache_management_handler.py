#!/usr/bin/env python3
"""
统一缓存管理Handler
"""

from typing import Any, Dict
from core.tools.decorators import tool

@tool(
    name="cache_management",
    category="cache_management",
    description="统一缓存管理系统 - 提供Redis缓存读写、批量操作、统计和清理功能",
    tags=["cache", "redis", "performance", "storage"]
)
async def cache_management_handler(
    action: str,
    key: str = None,
    value: Any = None,
    ttl: int = 3600,
    pattern: str = None,
    keys: list[str] = None
) -> dict[str, Any]:
    """
    统一缓存管理Handler

    参数:
        action: 操作类型 (get/set/delete/exists/clear/stats/multi_get/multi_set)
        key: 缓存键（用于get/set/delete/exists操作）
        value: 缓存值（用于set操作）
        ttl: 过期时间（秒，默认3600，用于set操作）
        pattern: 键模式（用于clear操作，如"test:*"）
        keys: 键列表（用于multi_get操作）

    返回:
        {
            "success": true,
            "action": "...",
            "result": {...}
        }
    """
    try:
        from core.cache.unified_cache import UnifiedCache

        # 参数验证
        if not action:
            return {
                "success": False,
                "error": "缺少必需参数: action"
            }

        # 创建缓存实例
        cache = UnifiedCache()

        # 执行相应的操作
        if action == "get":
            if not key:
                return {"success": False, "error": "get操作需要key参数"}
            result = await cache.get(key)
            return {
                "success": True,
                "action": "get",
                "key": key,
                "result": result,
                "exists": result is not None
            }

        elif action == "set":
            if not key or value is None:
                return {"success": False, "error": "set操作需要key和value参数"}
            success = await cache.set(key, value, ttl)
            return {
                "success": success,
                "action": "set",
                "key": key,
                "ttl": ttl
            }

        elif action == "delete":
            if not key:
                return {"success": False, "error": "delete操作需要key参数"}
            success = await cache.delete(key)
            return {
                "success": success,
                "action": "delete",
                "key": key
            }

        elif action == "exists":
            if not key:
                return {"success": False, "error": "exists操作需要key参数"}
            exists = await cache.exists(key)
            return {
                "success": True,
                "action": "exists",
                "key": key,
                "exists": exists
            }

        elif action == "clear":
            if not pattern:
                return {"success": False, "error": "clear操作需要pattern参数"}
            count = await cache.clear_pattern(pattern)
            return {
                "success": True,
                "action": "clear",
                "pattern": pattern,
                "deleted_count": count
            }

        elif action == "stats":
            stats = await cache.get_stats()
            return {
                "success": True,
                "action": "stats",
                "stats": stats
            }

        elif action == "multi_get":
            if not keys:
                return {"success": False, "error": "multi_get操作需要keys参数"}
            results = await cache.get_multi(keys)
            return {
                "success": True,
                "action": "multi_get",
                "keys": keys,
                "results": results
            }

        else:
            return {
                "success": False,
                "error": f"不支持的操作: {action}",
                "supported_actions": ["get", "set", "delete", "exists", "clear", "stats", "multi_get"]
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "action": action
        }
