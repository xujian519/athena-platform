#!/usr/bin/env python3
"""
学习数据持久化管理器单元测试
Persistence Manager Unit Tests

测试LearningPersistenceManager的功能：
1. 文件存储后端
2. 数据记录保存/加载
3. 查询功能
4. 清空功能

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-28
"""

import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.learning.persistence_manager import (
    FileStorageBackend,
    LearningDataRecord,
    LearningPersistenceManager,
    StorageBackend,
    get_persistence_manager,
)


class TestLearningDataRecord:
    """学习数据记录测试"""

    def test_create_record(self):
        """测试创建记录"""
        record = LearningDataRecord(
            record_id="test_001",
            agent_id="agent_1",
            data_type="experience",
            content={"action": "test", "reward": 0.5},
            timestamp=datetime.now(),
        )

        assert record.record_id == "test_001"
        assert record.agent_id == "agent_1"
        assert record.data_type == "experience"
        assert record.content == {"action": "test", "reward": 0.5}

    def test_to_dict(self):
        """测试转换为字典"""
        record = LearningDataRecord(
            record_id="test_002",
            agent_id="agent_1",
            data_type="pattern",
            content={"pattern": "test"},
            timestamp=datetime(2026, 1, 28, 12, 0, 0),
        )

        data = record.to_dict()
        assert data["record_id"] == "test_002"
        assert isinstance(data["timestamp"], str)

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "record_id": "test_003",
            "agent_id": "agent_1",
            "data_type": "knowledge",
            "content": {"knowledge": "test"},
            "timestamp": "2026-01-28T12:00:00",
            "metadata": {},
            "ttl": None,
        }

        record = LearningDataRecord.from_dict(data)
        assert record.record_id == "test_003"
        assert isinstance(record.timestamp, datetime)


class TestFileStorageBackend:
    """文件存储后端测试"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def storage(self, temp_dir):
        """创建存储后端"""
        return FileStorageBackend(temp_dir)

    @pytest.fixture
    def sample_record(self):
        """创建示例记录"""
        return LearningDataRecord(
            record_id="test_001",
            agent_id="test_agent",
            data_type="experience",
            content={"action": "test", "reward": 0.8},
            timestamp=datetime.now(),
        )

    @pytest.mark.asyncio
    async def test_save_record(self, storage, sample_record):
        """测试保存记录"""
        success = await storage.save(sample_record)
        assert success is True

    @pytest.mark.asyncio
    async def test_load_record(self, storage, sample_record):
        """测试加载记录"""
        # 先保存
        await storage.save(sample_record)

        # 再加载
        loaded = await storage.load(sample_record.record_id, sample_record.agent_id)
        assert loaded is not None
        assert loaded.record_id == sample_record.record_id
        assert loaded.content == sample_record.content

    @pytest.mark.asyncio
    async def test_load_nonexistent_record(self, storage):
        """测试加载不存在的记录"""
        loaded = await storage.load("nonexistent", "test_agent")
        assert loaded is None

    @pytest.mark.asyncio
    async def test_delete_record(self, storage, sample_record):
        """测试删除记录"""
        # 保存记录
        await storage.save(sample_record)

        # 删除记录
        success = await storage.delete(sample_record.record_id, sample_record.agent_id)
        assert success is True

        # 验证已删除
        loaded = await storage.load(sample_record.record_id, sample_record.agent_id)
        assert loaded is None

    @pytest.mark.asyncio
    async def test_query_records(self, storage):
        """测试查询记录"""
        # 保存多个记录
        for i in range(5):
            record = LearningDataRecord(
                record_id=f"test_{i}",
                agent_id="test_agent",
                data_type="experience",
                content={"index": i},
                timestamp=datetime.now(),
            )
            await storage.save(record)

        # 查询所有记录
        records = await storage.query("test_agent")
        assert len(records) == 5

        # 查询限制数量
        records = await storage.query("test_agent", limit=3)
        assert len(records) == 3

    @pytest.mark.asyncio
    async def test_query_by_type(self, storage):
        """测试按类型查询"""
        # 保存不同类型的记录
        exp_record = LearningDataRecord(
            record_id="exp_1",
            agent_id="test_agent",
            data_type="experience",
            content={"type": "exp"},
            timestamp=datetime.now(),
        )
        pattern_record = LearningDataRecord(
            record_id="pat_1",
            agent_id="test_agent",
            data_type="pattern",
            content={"type": "pattern"},
            timestamp=datetime.now(),
        )

        await storage.save(exp_record)
        await storage.save(pattern_record)

        # 查询特定类型
        exp_records = await storage.query("test_agent", "experience")
        assert len(exp_records) == 1
        assert exp_records[0].data_type == "experience"

    @pytest.mark.asyncio
    async def test_clear_all(self, storage):
        """测试清空所有记录"""
        # 保存记录
        for i in range(3):
            record = LearningDataRecord(
                record_id=f"test_{i}",
                agent_id="test_agent",
                data_type="experience",
                content={},
                timestamp=datetime.now(),
            )
            await storage.save(record)

        # 清空
        success = await storage.clear_all("test_agent")
        assert success is True

        # 验证已清空
        records = await storage.query("test_agent")
        assert len(records) == 0

    def test_path_traversal_protection(self, temp_dir):
        """测试路径遍历保护"""
        storage = FileStorageBackend(temp_dir)

        # 尝试使用恶意agent_id - 应该被清理
        safe_path = storage._get_file_path("../../../etc/passwd")
        # 路径应该被清理，不包含父目录引用
        assert "../" not in str(safe_path)
        assert "passwd" in str(safe_path)  # 文件名会被保留但安全化

        safe_path2 = storage._get_file_path("test/../../agent")
        assert "../" not in str(safe_path2)
        # 验证路径在temp_dir范围内（使用resolve处理符号链接）
        resolved_temp = Path(temp_dir).resolve()
        resolved_safe = safe_path2.resolve()
        assert str(resolved_safe).startswith(str(resolved_temp))


class TestLearningPersistenceManager:
    """持久化管理器测试"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    async def manager(self, temp_dir):
        """创建持久化管理器"""
        mgr = LearningPersistenceManager(StorageBackend.FILE)
        await mgr.initialize(base_path=temp_dir)
        return mgr

    @pytest.mark.asyncio
    async def test_save_experience(self, manager):
        """测试保存经验"""
        exp_id = await manager.save_experience(
            agent_id="test_agent",
            experience={"action": "test", "reward": 0.9},
            metadata={"source": "test"},
        )

        assert exp_id != ""
        assert exp_id.startswith("exp_")

    @pytest.mark.asyncio
    async def test_save_pattern(self, manager):
        """测试保存模式"""
        pattern_id = await manager.save_pattern(
            agent_id="test_agent",
            pattern={"type": "test", "confidence": 0.8},
        )

        assert pattern_id != ""
        assert pattern_id.startswith("pattern_")

    @pytest.mark.asyncio
    async def test_save_knowledge(self, manager):
        """测试保存知识"""
        knowledge_id = await manager.save_knowledge(
            agent_id="test_agent",
            knowledge={"fact": "test", "confidence": 0.95},
        )

        assert knowledge_id != ""
        assert knowledge_id.startswith("knowledge_")

    @pytest.mark.asyncio
    async def test_load_experiences(self, manager):
        """测试加载经验"""
        # 保存经验
        await manager.save_experience(
            agent_id="test_agent",
            experience={"action": "test1", "reward": 0.5},
        )
        await manager.save_experience(
            agent_id="test_agent",
            experience={"action": "test2", "reward": 0.7},
        )

        # 加载经验
        experiences = await manager.load_experiences("test_agent")
        assert len(experiences) == 2

    @pytest.mark.asyncio
    async def test_load_patterns(self, manager):
        """测试加载模式"""
        # 保存模式
        await manager.save_pattern(
            agent_id="test_agent",
            pattern={"type": "pattern1"},
        )
        await manager.save_pattern(
            agent_id="test_agent",
            pattern={"type": "pattern2"},
        )

        # 加载模式
        patterns = await manager.load_patterns("test_agent")
        assert len(patterns) == 2

    @pytest.mark.asyncio
    async def test_get_statistics(self, manager):
        """测试获取统计信息"""
        # 保存数据
        await manager.save_experience(agent_id="test_agent", experience={})
        await manager.save_pattern(agent_id="test_agent", pattern={})
        await manager.save_knowledge(agent_id="test_agent", knowledge={})

        # 获取统计
        stats = await manager.get_statistics("test_agent")
        assert stats["total_experiences"] == 1
        assert stats["total_patterns"] == 1
        assert stats["total_knowledge"] == 1
        assert stats["agent_id"] == "test_agent"

    @pytest.mark.asyncio
    async def test_clear_agent_data(self, manager):
        """测试清空智能体数据"""
        # 保存数据
        await manager.save_experience(agent_id="test_agent", experience={})

        # 清空数据
        success = await manager.clear_agent_data("test_agent")
        assert success is True

        # 验证已清空
        experiences = await manager.load_experiences("test_agent")
        assert len(experiences) == 0


@pytest.mark.asyncio
async def test_global_persistence_manager():
    """测试全局持久化管理器"""
    manager = await get_persistence_manager()
    assert manager is not None
    assert isinstance(manager, LearningPersistenceManager)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
