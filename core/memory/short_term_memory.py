"""
短期记忆
Short Term Memory
"""

from datetime import datetime
from typing import Any


class ShortTermMemory:
    """短期记忆 - 存储临时信息"""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._memory = {}

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """设置短期记忆"""
        try:
            self._memory[key] = {"value": value, "expires_at": datetime.now().timestamp() + ttl}
            return True
        except Exception:
            logger.error("操作失败: e", exc_info=True)
            raise

    async def get(self, key: str) -> Any | None:
        """获取短期记忆"""
        if key not in self._memory:
            return None

        data = self._memory[key]
        if datetime.now().timestamp() > data["expires_at"]:
            del self._memory[key]
            return None

        return data["value"]

    async def clear_expired(self):
        """清理过期记忆"""
        now = datetime.now().timestamp()
        expired = [k for k, v in self._memory.items() if now > v["expires_at"]]
        for key in expired:
            del self._memory[key]
