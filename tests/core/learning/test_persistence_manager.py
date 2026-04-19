#!/usr/bin/env python3
"""
持久化管理器单元测试
Unit Tests for Persistence Manager

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-28
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.learning.persistence_manager import (
    FileStorageBackend,
    LearningDataRecord,
    LearningPersistenceManager,
    RedisStorageBackend,
    StorageBackend,
)


@pytest.mark.unit
class TestLearningDataRecord:
    """学习数据记录测试"""

    def test_create_record(self):
        """测试创建记录"""
        record = LearningDataRecord(
            record_id="test_001",
            agent_id="agent_1",
            data_type="experience",
            content={"key": "value"},
            timestamp=datetime.now(),
        )
        assert record.record_id == "test_001"
        assert record.agent_id == "agent_1"
        assert record.data_type == "experience"

    def test_to_dict(self):
        """测试转换为字典"""
        record = LearningDataRecord(
            record_id="test_001",
            agent_id="agent_1",
            data_type="experience",
            content={"key": "value"},
            timestamp=datetime.now(),
        )
        data = record.to_dict()
        assert isinstance(data["timestamp"], str)
        assert data["record_id"] == "test_001"

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "record_id": "test_001",
            "agent_id": "agent_1",
            "data_type": "experience",
            "content": {"key": "value"},
            "timestamp": "2026-01-28T00:00:00",
            "metadata": {},
            "ttl": None,
        }
        record = LearningDataRecord.from_dict(data)
        assert record.record_id == "test_001"
        assert isinstance(record.timestamp, datetime)


@pytest.mark.unit
class TestFileStorageBackend:
    """文件存储后端测试"""

    @pytest.fixture
    async def file_backend(self, tmp_path):
        """创建临时文件后端"""
        backend = FileStorageBackend(base_path=str(tmp_path / "learning"))
        yield backend
        # 清理
        import shutil
        if tmp_path.exists():
            shutil.rmtree(tmp_path)

    @pytest.mark.asyncio
    async def test_save_and_load(self, file_backend):
        """测试保存和加载"""
        record = LearningDataRecord(
            record_id="test_001",
            agent_id="agent_1",
            data_type="experience",
            content={"test": "data"},
            timestamp=datetime.now(),
        )

        # 保存
        assert await file_backend.save(record) is True

        # 加载
        loaded = await file_backend.load("test_001", "agent_1")
        assert loaded is not None
        assert loaded.record_id == "test_001"
        assert loaded.content == {"test": "data"}

    @pytest.mark.asyncio
    async def test_load_nonexistent(self, file_backend):
        """测试加载不存在的记录"""
        result = await file_backend.load("nonexistent", "agent_1")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, file_backend):
        """测试删除记录"""
        record = LearningDataRecord(
            record_id="test_001",
            agent_id="agent_1",
            data_type="experience",
            content={"test": "data"},
            timestamp=datetime.now(),
        )

        await file_backend.save(record)
        assert await file_backend.delete("test_001", "agent_1") is True

        # 验证已删除
        result = await file_backend.load("test_001", "agent_1")
        assert result is None

    @pytest.mark.asyncio
    async def test_query(self, file_backend):
        """测试查询记录"""
        # 保存多条记录
        for i in range(5):
            record = LearningDataRecord(
                record_id=f"test_{i:03d}",
                agent_id="agent_1",
                data_type="experience",
                content={"index": i},
                timestamp=datetime.now(),
            )
            await file_backend.save(record)

        # 查询所有
        results = await file_backend.query("agent_1", "experience")
        assert len(results) == 5

        # 按数据类型过滤
        results = await file_backend.query("agent_1", "experience", limit=3)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_clear_all(self, file_backend):
        """测试清空所有记录"""
        # 保存记录
        record = LearningDataRecord(
            record_id="test_001",
            agent_id="agent_1",
            data_type="experience",
            content={"test": "data"},
            timestamp=datetime.now(),
        )
        await file_backend.save(record)

        # 清空
        assert await file_backend.clear_all("agent_1") is True

        # 验证已清空
        results = await file_backend.query("agent_1")
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_path_traversal_protection(self, file_backend):
        """测试路径遍历攻击防护"""
        # 尝试使用恶意agent_id
        with pytest.raises(ValueError, match="非法的agent_id"):
            file_backend._get_file_path("../../../etc/passwd")


@pytest.mark.integration
class TestRedisStorageBackend:
    """Redis存储后端测试（需要Redis）"""

    @pytest.fixture
    async def redis_backend(self):
        """创建Redis后端（如果可用）"""
        try:
            backend = RedisStorageBackend()
            await backend._ensure_initialized()
            yield backend
        except Exception:
            pytest.skip("Redis not available")

    @pytest.mark.asyncio
    async def test_save_and_load(self, redis_backend):
        """测试保存和加载"""
        record = LearningDataRecord(
            record_id="test_001",
            agent_id="agent_1",
            data_type="experience",
            content={"test": "data"},
            timestamp=datetime.now(),
        )

        # 保存
        assert await redis_backend.save(record) is True

        # 加载
        loaded = await redis_backend.load("test_001", "agent_1")
        assert loaded is not None
        assert loaded.record_id == "test_001"

    @pytest.mark.asyncio
    async def test_save_with_ttl(self, redis_backend):
        """测试保存带TTL的记录"""
        record = LearningDataRecord(
            record_id="test_ttl",
            agent_id="agent_1",
            data_type="experience",
            content={"test": "data"},
            timestamp=datetime.now(),
            ttl=1,  # 1秒过期
        )

        await redis_backend.save(record)

        # 立即加载应该成功
        loaded = await redis_backend.load("test_ttl", "agent_1")
        assert loaded is not None

        # 等待过期
        await asyncio.sleep(2)

        # 加载应该失败
        loaded = await redis_backend.load("test_ttl", "agent_1")
        assert loaded is None


@pytest.mark.unit
class TestLearningPersistenceManager:
    """持久化管理器测试"""

    @pytest.fixture
    async def persistence_manager(self, tmp_path):
        """创建持久化管理器"""
        manager = LearningPersistenceManager(StorageBackend.FILE)
        await manager.initialize(base_path=str(tmp_path / "learning"))
        yield manager
        # 清理
        import shutil
        if tmp_path.exists():
            shutil.rmtree(tmp_path)

    @pytest.mark.asyncio
    async def test_save_and_load_experience(self, persistence_manager):
        """测试保存和加载经验"""
        experience = {"task": "test", "action": "action1", "result": "success"}

        # 保存
        record_id = await persistence_manager.save_experience(
            agent_id="agent_1",
            experience=experience,
        )
        assert record_id != ""

        # 加载
        experiences = await persistence_manager.load_experiences("agent_1")
        assert len(experiences) == 1
        assert experiences[0]["task"] == "test"

    @pytest.mark.asyncio
    async def test_save_and_load_pattern(self, persistence_manager):
        """测试保存和加载模式"""
        pattern = {"type": "test_pattern", "confidence": 0.9}

        # 保存
        record_id = await persistence_manager.save_pattern(
            agent_id="agent_1",
            pattern=pattern,
        )
        assert record_id != ""

        # 加载
        patterns = await persistence_manager.load_patterns("agent_1")
        assert len(patterns) == 1
        assert patterns[0]["type"] == "test_pattern"

    @pytest.mark.asyncio
    async def test_save_and_load_knowledge(self, persistence_manager):
        """测试保存和加载知识"""
        knowledge = {"fact": "test_knowledge", "source": "test"}

        # 保存
        record_id = await persistence_manager.save_knowledge(
            agent_id="agent_1",
            knowledge=knowledge,
        )
        assert record_id != ""

        # 加载
        knowledge_list = await persistence_manager.load_knowledge("agent_1")
        assert len(knowledge_list) == 1
        assert knowledge_list[0]["fact"] == "test_knowledge"

    @pytest.mark.asyncio
    async def test_clear_agent_data(self, persistence_manager):
        """测试清空智能体数据"""
        # 保存一些数据
        await persistence_manager.save_experience(
            agent_id="agent_1",
            experience={"test": "data"},
        )

        # 清空
        assert await persistence_manager.clear_agent_data("agent_1") is True

        # 验证已清空
        experiences = await persistence_manager.load_experiences("agent_1")
        assert len(experiences) == 0

    @pytest.mark.asyncio
    async def test_get_statistics(self, persistence_manager):
        """测试获取统计信息"""
        # 保存一些数据
        await persistence_manager.save_experience(
            agent_id="agent_1",
            experience={"test": "data1"},
        )
        await persistence_manager.save_pattern(
            agent_id="agent_1",
            pattern={"type": "test"},
        )

        # 获取统计
        stats = await persistence_manager.get_statistics("agent_1")
        assert stats["agent_id"] == "agent_1"
        assert stats["total_experiences"] == 1
        assert stats["total_patterns"] == 1
        assert stats["backend_type"] == "file"


@pytest.mark.integration
class TestPersistenceIntegration:
    """持久化集成测试"""

    @pytest.mark.asyncio
    async def test_multiple_agents(self, tmp_path):
        """测试多智能体数据隔离"""
        manager = LearningPersistenceManager(StorageBackend.FILE)
        await manager.initialize(base_path=str(tmp_path / "learning"))

        # 为不同智能体保存数据
        await manager.save_experience(
            agent_id="agent_1",
            experience={"agent": "1"},
        )
        await manager.save_experience(
            agent_id="agent_2",
            experience={"agent": "2"},
        )

        # 验证数据隔离
        exp1 = await manager.load_experiences("agent_1")
        exp2 = await manager.load_experiences("agent_2")

        assert len(exp1) == 1
        assert len(exp2) == 1
        assert exp1[0]["agent"] == "1"
        assert exp2[0]["agent"] == "2"
