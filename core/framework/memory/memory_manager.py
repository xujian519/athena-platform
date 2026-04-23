
"""
记忆管理器
Memory Manager
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MemoryManager:
    """记忆管理器 - 统一管理各类记忆"""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("/tmp/athena_memories")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.short_term = {}
        self.long_term = {}
        self.episodic = []

        self._load_memories()

    def _load_memories(self) -> None:
        """加载已保存的记忆"""
        try:
            memory_file = self.storage_path / "memories.json"
            if memory_file.exists():
                with open(memory_file, encoding='utf-8') as f:
                    data = json.load(f)
                    self.short_term = data.get("short_term", {})
                    self.long_term = data.get("long_term", {})
                    self.episodic = data.get("episodic", [])
        except FileNotFoundError as e:
            logger.debug(f"记忆文件不存在，使用空记忆开始: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"记忆文件格式错误，使用空记忆开始: {e}")
        except Exception as e:
            logger.error(f"加载记忆失败: {e}", exc_info=True)
            raise

    async def store(self, key: str, value: Any, memory_type: str = "short_term") -> bool:
        """存储记忆"""
        try:
            if memory_type == "short_term":
                self.short_term[key]] = {
                    "value": value,
                    "timestamp": datetime.now().isoformat()
                }
            elif memory_type == "long_term":
                self.long_term[key]] = {
                    "value": value,
                    "timestamp": datetime.now().isoformat()
                }
            elif memory_type == "episodic":
                self.episodic.append({
                    "key": key,
                    "value": value,
                    "timestamp": datetime.now().isoformat()
                })

            await self._save_memories()
            return True
        except OSError as e:
            logger.error(f"存储记忆失败(文件错误): {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"存储记忆失败(未知错误): {e}", exc_info=True)
            return False

    async def retrieve(self, key: str, memory_type: str = "short_term") -> Optional[Any]:
        """检索记忆"""
        try:
            if memory_type == "short_term":
                return self.short_term.get(key, {}).get("value")
            elif memory_type == "long_term":
                return self.long_term.get(key, {}).get("value")
            elif memory_type == "episodic":
                for episode in reversed(self.episodic):
                    if episode["key"] == key:
                        return episode["value"]
        except Exception as e:
            logger.error(f"检索记忆失败: {e}", exc_info=True)
        return None

    async def search(self, query: str) -> list[dict[str, Any]]:
        """搜索记忆"""
        results = []
        query_lower = query.lower()

        # 搜索短期记忆
        for key, data in self.short_term.items():
            if query_lower in key.lower() or query_lower in str(data.get("value", "")).lower():
                results.append({
                    "key": key,
                    "value": data.get("value"),
                    "type": "short_term",
                    "timestamp": data.get("timestamp")
                })

        # 搜索长期记忆
        for key, data in self.long_term.items():
            if query_lower in key.lower() or query_lower in str(data.get("value", "")).lower():
                results.append({
                    "key": key,
                    "value": data.get("value"),
                    "type": "long_term",
                    "timestamp": data.get("timestamp")
                })

        return results

    async def _save_memories(self) -> None:
        """保存记忆到磁盘"""
        try:
            memory_file = self.storage_path / "memories.json"
            data = {
                "short_term": self.short_term,
                "long_term": self.long_term,
                "episodic": self.episodic
            }
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            logger.error(f"保存记忆失败(文件错误): {e}", exc_info=True)
        except Exception as e:
            logger.error(f"保存记忆失败(未知错误): {e}", exc_info=True)

