#!/usr/bin/env python3
"""
学习数据持久化管理器
Learning Data Persistence Manager

提供统一的数据持久化接口，支持多种存储后端：
1. JSON文件存储（本地开发）
2. Redis缓存（生产环境）
3. PostgreSQL数据库（长期存储）
4. Neo4j图数据库（知识图谱）

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-28
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class StorageBackend(str, Enum):
    """存储后端类型"""

    FILE = "file"  # JSON文件存储
    REDIS = "redis"  # Redis缓存
    POSTGRESQL = "postgresql"  # PostgreSQL数据库
    NEO4J = "neo4j"  # Neo4j图数据库


@dataclass
class LearningDataRecord:
    """学习数据记录"""

    record_id: str
    agent_id: str
    data_type: str  # experience, pattern, knowledge, etc.
    content: dict[str, Any]
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)
    ttl: int | None = None  # 过期时间(秒)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LearningDataRecord":
        """从字典创建"""
        if isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class StorageBackendInterface(ABC):
    """存储后端接口"""

    @abstractmethod
    async def save(self, record: LearningDataRecord) -> bool:
        """保存记录"""
        pass

    @abstractmethod
    async def load(self, record_id: str, agent_id: str) -> LearningDataRecord | None:
        """加载记录"""
        pass

    @abstractmethod
    async def delete(self, record_id: str, agent_id: str) -> bool:
        """删除记录"""
        pass

    @abstractmethod
    async def query(
        self, agent_id: str, data_type: str | None = None, limit: int = 100
    ) -> list[LearningDataRecord]:
        """查询记录"""
        pass

    @abstractmethod
    async def clear_all(self, agent_id: str) -> bool:
        """清空所有记录"""
        pass


class FileStorageBackend(StorageBackendInterface):
    """文件存储后端（使用JSON格式）"""

    def __init__(self, base_path: str = "data/learning"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 文件存储后端初始化: {self.base_path}")

    def _get_file_path(self, agent_id: str) -> Path:
        """获取文件路径"""
        # 首先检查原始输入是否包含路径遍历字符
        path_traversal_chars = ["..", "~", "/", "\\"]
        if any(char in agent_id for char in path_traversal_chars):
            raise ValueError(f"非法的agent_id: {agent_id}")

        # 验证agent_id，防止路径遍历
        # 只保留字母数字和部分安全字符
        safe_agent_id = "".join(c for c in agent_id if c.isalnum() or c in "_-")
        if not safe_agent_id:
            safe_agent_id = "default"

        # 确保路径在base_path范围内
        file_name = f"{safe_agent_id}_learning_data.jsonl"
        file_path = (self.base_path / file_name).resolve()

        # 验证解析后的路径仍然在base_path内
        if not str(file_path).startswith(str(self.base_path.resolve())):
            raise ValueError(f"非法的agent_id: {agent_id}")

        return file_path

    async def save(self, record: LearningDataRecord) -> bool:
        """保存记录（追加到JSONL文件）"""
        try:
            file_path = self._get_file_path(record.agent_id)

            # 使用异步文件IO
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._save_sync, file_path, record)

            return True
        except Exception as e:
            logger.error(f"保存记录失败: {e}")
            return False

    def _save_sync(self, file_path: Path, record: LearningDataRecord) -> None:
        """同步保存"""
        with open(file_path, "a", encoding="utf-8") as f:
            json.dump(record.to_dict(), f, ensure_ascii=False)
            f.write("\n")

    async def load(self, record_id: str, agent_id: str) -> LearningDataRecord | None:
        """加载记录"""
        try:
            file_path = self._get_file_path(agent_id)
            if not file_path.exists():
                return None

            # 异步读取文件
            loop = asyncio.get_event_loop()
            records = await loop.run_in_executor(None, self._load_all_sync, file_path)

            for record in records:
                if record.record_id == record_id:
                    return record

            return None
        except Exception as e:
            logger.error(f"加载记录失败: {e}")
            return None

    def _load_all_sync(self, file_path: Path) -> list[LearningDataRecord]:
        """同步加载所有记录"""
        records = []
        with open(file_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    records.append(LearningDataRecord.from_dict(data))
        return records

    async def delete(self, record_id: str, agent_id: str) -> bool:
        """删除记录"""
        try:
            file_path = self._get_file_path(agent_id)
            if not file_path.exists():
                return False

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._delete_sync, file_path, record_id)

            return True
        except Exception as e:
            logger.error(f"删除记录失败: {e}")
            return False

    def _delete_sync(self, file_path: Path, record_id: str) -> None:
        """同步删除"""
        records = self._load_all_sync(file_path)
        records = [r for r in records if r.record_id != record_id]

        # 重写文件
        with open(file_path, "w", encoding="utf-8") as f:
            for record in records:
                json.dump(record.to_dict(), f, ensure_ascii=False)
                f.write("\n")

    async def query(
        self, agent_id: str, data_type: str | None = None, limit: int = 100
    ) -> list[LearningDataRecord]:
        """查询记录"""
        try:
            file_path = self._get_file_path(agent_id)
            if not file_path.exists():
                return []

            loop = asyncio.get_event_loop()
            records = await loop.run_in_executor(None, self._load_all_sync, file_path)

            # 过滤和排序
            if data_type:
                records = [r for r in records if r.data_type == data_type]

            # 按时间倒序排序
            records.sort(key=lambda x: x.timestamp, reverse=True)

            return records[:limit]
        except Exception as e:
            logger.error(f"查询记录失败: {e}")
            return []

    async def clear_all(self, agent_id: str) -> bool:
        """清空所有记录"""
        try:
            file_path = self._get_file_path(agent_id)
            if file_path.exists():
                file_path.unlink()
            return True
        except Exception as e:
            logger.error(f"清空记录失败: {e}")
            return False


class RedisStorageBackend(StorageBackendInterface):
    """Redis存储后端"""

    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """确保Redis已初始化"""
        if self._initialized:
            return

        try:
            # 尝试导入redis
            import redis.asyncio as aioredis

            if not self.redis_client:
                # 创建默认连接
                self.redis_client = await aioredis.from_url(
                    "redis://localhost:6379/0", encoding="utf-8", decode_responses=True
                )

            # 测试连接
            await self.redis_client.ping()
            self._initialized = True
            logger.info("✅ Redis存储后端连接成功")

        except ImportError:
            logger.warning("Redis模块未安装，回退到文件存储")
            raise
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            raise

    def _make_key(self, agent_id: str, record_id: str) -> str:
        """生成Redis键"""
        # 验证输入，防止Redis注入
        safe_agent_id = "".join(c for c in agent_id if c.isalnum() or c in "_-")
        safe_record_id = "".join(c for c in record_id if c.isalnum() or c in "_-")
        return f"learning:{safe_agent_id}:{safe_record_id}"

    async def save(self, record: LearningDataRecord) -> bool:
        """保存记录"""
        try:
            await self._ensure_initialized()

            key = self._make_key(record.agent_id, record.record_id)
            value = json.dumps(record.to_dict(), ensure_ascii=False)

            # 设置过期时间
            if record.ttl:
                await self.redis_client.setex(key, record.ttl, value)
            else:
                await self.redis_client.set(key, value)

            # 添加到类型索引
            type_key = f"learning:index:{record.agent_id}:{record.data_type}"
            await self.redis_client.sadd(type_key, record.record_id)

            return True
        except Exception as e:
            logger.error(f"Redis保存失败: {e}")
            return False

    async def load(self, record_id: str, agent_id: str) -> LearningDataRecord | None:
        """加载记录"""
        try:
            await self._ensure_initialized()

            key = self._make_key(agent_id, record_id)
            value = await self.redis_client.get(key)

            if value:
                data = json.loads(value)
                return LearningDataRecord.from_dict(data)

            return None
        except Exception as e:
            logger.error(f"Redis加载失败: {e}")
            return None

    async def delete(self, record_id: str, agent_id: str) -> bool:
        """删除记录"""
        try:
            await self._ensure_initialized()

            key = self._make_key(agent_id, record_id)

            # 获取数据类型（用于清理索引）
            value = await self.redis_client.get(key)
            if value:
                data = json.loads(value)
                data_type = data.get("data_type")
                type_key = f"learning:index:{agent_id}:{data_type}"
                await self.redis_client.srem(type_key, record_id)

            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis删除失败: {e}")
            return False

    async def query(
        self, agent_id: str, data_type: str | None = None, limit: int = 100
    ) -> list[LearningDataRecord]:
        """查询记录"""
        try:
            await self._ensure_initialized()

            records = []

            if data_type:
                # 使用类型索引查询
                type_key = f"learning:index:{agent_id}:{data_type}"
                record_ids = await self.redis_client.smembers(type_key)

                for record_id in list(record_ids)[:limit]:
                    record = await self.load(record_id, agent_id)
                    if record:
                        records.append(record)
            else:
                # 扫描所有键
                pattern = f"learning:{agent_id}:*"
                async for key in self.redis_client.scan_iter(match=pattern, count=limit):
                    value = await self.redis_client.get(key)
                    if value:
                        data = json.loads(value)
                        records.append(LearningDataRecord.from_dict(data))

            # 按时间倒序排序
            records.sort(key=lambda x: x.timestamp, reverse=True)
            return records[:limit]
        except Exception as e:
            logger.error(f"Redis查询失败: {e}")
            return []

    async def clear_all(self, agent_id: str) -> bool:
        """清空所有记录"""
        try:
            await self._ensure_initialized()

            pattern = f"learning:{agent_id}:*"
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                await self.redis_client.delete(*keys)

            return True
        except Exception as e:
            logger.error(f"Redis清空失败: {e}")
            return False


class LearningPersistenceManager:
    """
    学习数据持久化管理器

    提供统一的持久化接口，支持多种存储后端自动切换。
    """

    def __init__(self, backend: StorageBackend = StorageBackend.FILE):
        self.backend_type = backend
        self.backend: StorageBackendInterface | None = None
        self._initialized = False

    async def initialize(self, **kwargs) -> bool:
        """初始化持久化后端"""
        try:
            if self.backend_type == StorageBackend.FILE:
                base_path = kwargs.get("base_path", "data/learning")
                self.backend = FileStorageBackend(base_path)

            elif self.backend_type == StorageBackend.REDIS:
                redis_client = kwargs.get("redis_client")
                self.backend = RedisStorageBackend(redis_client)

            else:
                logger.warning(f"不支持的存储后端: {self.backend_type}")
                return False

            self._initialized = True
            logger.info(f"✅ 持久化管理器初始化成功: {self.backend_type.value}")
            return True

        except Exception as e:
            logger.error(f"持久化管理器初始化失败: {e}")
            # 回退到文件存储
            if self.backend_type != StorageBackend.FILE:
                logger.info("回退到文件存储...")
                self.backend_type = StorageBackend.FILE
                return await self.initialize(**kwargs)
            return False


    def _ensure_backend(self) -> StorageBackendInterface:
        """确保后端已初始化"""
        assert self.backend is not None, "Backend not initialized"
        return self.backend

    async def save_experience(
        self,
        agent_id: str,
        experience: dict[str, Any],        metadata: dict[str, Any] | None = None,
        ttl: int | None = None,
    ) -> str:
        """保存学习经验"""
        if not self._initialized:
            await self.initialize()

        record = LearningDataRecord(
            record_id=f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            agent_id=agent_id,
            data_type="experience",
            content=experience,
            timestamp=datetime.now(),
            metadata=metadata or {},
            ttl=ttl,
        )

        success = await self._ensure_backend().save(record)
        if success:
            logger.debug(f"保存学习经验: {record.record_id}")
            return record.record_id
        else:
            logger.error("保存学习经验失败")
            return ""

    async def save_pattern(
        self,
        agent_id: str,
        pattern: dict[str, Any],        metadata: dict[str, Any] | None = None,
    ) -> str:
        """保存学习模式"""
        if not self._initialized:
            await self.initialize()

        record = LearningDataRecord(
            record_id=f"pattern_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            agent_id=agent_id,
            data_type="pattern",
            content=pattern,
            timestamp=datetime.now(),
            metadata=metadata or {},
            ttl=None,  # 模式长期保存
        )

        success = await self._ensure_backend().save(record)
        if success:
            logger.debug(f"保存学习模式: {record.record_id}")
            return record.record_id
        else:
            logger.error("保存学习模式失败")
            return ""

    async def save_knowledge(
        self,
        agent_id: str,
        knowledge: dict[str, Any],        metadata: dict[str, Any] | None = None,
    ) -> str:
        """保存知识"""
        if not self._initialized:
            await self.initialize()

        record = LearningDataRecord(
            record_id=f"knowledge_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            agent_id=agent_id,
            data_type="knowledge",
            content=knowledge,
            timestamp=datetime.now(),
            metadata=metadata or {},
            ttl=None,  # 知识长期保存
        )

        success = await self._ensure_backend().save(record)
        if success:
            logger.debug(f"保存知识: {record.record_id}")
            return record.record_id
        else:
            logger.error("保存知识失败")
            return ""

    async def load_experiences(
        self, agent_id: str, limit: int = 1000
    ) -> list[dict[str, Any]]:
        """加载学习经验"""
        if not self._initialized:
            await self.initialize()

        records = await self._ensure_backend().query(agent_id, "experience", limit)
        return [r.content for r in records]

    async def load_patterns(self, agent_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """加载学习模式"""
        if not self._initialized:
            await self.initialize()

        records = await self._ensure_backend().query(agent_id, "pattern", limit)
        return [r.content for r in records]

    async def load_knowledge(self, agent_id: str, limit: int = 1000) -> list[dict[str, Any]]:
        """加载知识"""
        if not self._initialized:
            await self.initialize()

        records = await self._ensure_backend().query(agent_id, "knowledge", limit)
        return [r.content for r in records]

    async def clear_agent_data(self, agent_id: str) -> bool:
        """清空智能体数据"""
        if not self._initialized:
            await self.initialize()

        return await self._ensure_backend().clear_all(agent_id)

    async def get_statistics(self, agent_id: str) -> dict[str, Any]:
        """获取统计信息"""
        if not self._initialized:
            await self.initialize()

        experiences = await self._ensure_backend().query(agent_id, "experience")
        patterns = await self._ensure_backend().query(agent_id, "pattern")
        knowledge = await self._ensure_backend().query(agent_id, "knowledge")

        return {
            "agent_id": agent_id,
            "total_experiences": len(experiences),
            "total_patterns": len(patterns),
            "total_knowledge": len(knowledge),
            "backend_type": self.backend_type.value,
        }


# 全局单例
_global_persistence_manager: LearningPersistenceManager | None = None


async def get_persistence_manager(
    backend: StorageBackend = StorageBackend.FILE,
) -> LearningPersistenceManager:
    """获取持久化管理器单例"""
    global _global_persistence_manager

    if _global_persistence_manager is None:
        _global_persistence_manager = LearningPersistenceManager(backend)
        await _global_persistence_manager.initialize()

    return _global_persistence_manager


__all__ = [
    "StorageBackend",
    "LearningDataRecord",
    "StorageBackendInterface",
    "FileStorageBackend",
    "RedisStorageBackend",
    "LearningPersistenceManager",
    "get_persistence_manager",
]
