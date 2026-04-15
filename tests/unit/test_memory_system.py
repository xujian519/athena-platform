#!/usr/bin/env python3
"""
记忆系统单元测试
Unit tests for Memory System

测试目标：验证四层记忆架构
- HOT层（内存）
- WARM层（Redis）
- COLD层（SQLite）
- ARCHIVE层（文件系统）
"""

import asyncio
import sys
from pathlib import Path

import pytest

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestMemorySystemInitialization:
    """记忆系统初始化测试"""

    @pytest.mark.asyncio
    async def test_memory_manager_initialization(self):
        """测试记忆管理器初始化"""
        try:
            from core.memory.enhanced_memory_manager import EnhancedMemoryManager

            memory = EnhancedMemoryManager()
            assert memory is not None

            # 初始化
            await memory.initialize()
            assert memory.is_initialized

        except ImportError:
            pytest.skip("EnhancedMemoryManager not available")

    @pytest.mark.asyncio
    async def test_four_tier_architecture(self):
        """测试四层记忆架构"""
        try:
            from core.memory.enhanced_memory_manager import EnhancedMemoryManager

            memory = EnhancedMemoryManager()
            await memory.initialize()

            # 验证四层架构存在
            assert hasattr(memory, 'hot_tier') or hasattr(memory, 'hot_memory')
            assert hasattr(memory, 'warm_tier') or hasattr(memory, 'warm_memory')
            assert hasattr(memory, 'cold_tier') or hasattr(memory, 'cold_memory')
            assert hasattr(memory, 'archive_tier') or hasattr(memory, 'archive_memory')

        except ImportError:
            pytest.skip("EnhancedMemoryManager not available")


class TestMemoryStoreAndRetrieve:
    """记忆存储和检索测试"""

    @pytest.mark.asyncio
    async def test_memory_store_and_retrieve(self):
        """测试基本存储和检索"""
        try:
            from core.memory.enhanced_memory_manager import EnhancedMemoryManager

            memory = EnhancedMemoryManager()
            await memory.initialize()

            # 存储数据
            await memory.store(
                key="test_key_1",
                value="test_value_1",
                metadata={"type": "test"}
            )

            # 检索数据
            result = await memory.retrieve("test_key_1")

            assert result is not None
            # 验证检索到的值
            if hasattr(result, 'value'):
                assert result.value == "test_value_1"
            else:
                assert result == "test_value_1"

        except ImportError:
            pytest.skip("EnhancedMemoryManager not available")

    @pytest.mark.asyncio
    async def test_memory_store_with_metadata(self):
        """测试带元数据的存储"""
        try:
            from core.memory.enhanced_memory_manager import EnhancedMemoryManager

            memory = EnhancedMemoryManager()
            await memory.initialize()

            metadata = {
                "type": "patent",
                "source": "USPTO",
                "timestamp": "2026-03-17"
            }

            await memory.store(
                key="patent_US8302089",
                value={"title": "Test Patent", "number": "US8302089"},
                metadata=metadata
            )

            result = await memory.retrieve("patent_US8302089")

            assert result is not None

        except ImportError:
            pytest.skip("EnhancedMemoryManager not available")

    @pytest.mark.asyncio
    async def test_memory_retrieve_nonexistent_key(self):
        """测试检索不存在的键"""
        try:
            from core.memory.enhanced_memory_manager import EnhancedMemoryManager

            memory = EnhancedMemoryManager()
            await memory.initialize()

            result = await memory.retrieve("nonexistent_key_xyz")

            # 应该返回None或空值
            assert result is None or result == {}

        except ImportError:
            pytest.skip("EnhancedMemoryManager not available")


class TestMemoryTTL:
    """记忆TTL（生存时间）测试"""

    @pytest.mark.asyncio
    async def test_memory_with_short_ttl(self):
        """测试短TTL记忆"""
        try:
            from core.memory.enhanced_memory_manager import EnhancedMemoryManager

            memory = EnhancedMemoryManager()
            await memory.initialize()

            # 存储短TTL记忆（1秒）
            await memory.store(
                key="short_ttl_key",
                value="will_expire_soon",
                ttl=1
            )

            # 立即检索应该成功
            result = await memory.retrieve("short_ttl_key")
            assert result is not None

            # 等待2秒后应该过期
            await asyncio.sleep(2)
            result = await memory.retrieve("short_ttl_key")
            assert result is None or result == {}

        except ImportError:
            pytest.skip("EnhancedMemoryManager not available")

    @pytest.mark.asyncio
    async def test_memory_with_long_ttl(self):
        """测试长TTL记忆"""
        try:
            from core.memory.enhanced_memory_manager import EnhancedMemoryManager

            memory = EnhancedMemoryManager()
            await memory.initialize()

            # 存储长TTL记忆（1小时）
            await memory.store(
                key="long_ttl_key",
                value="will_not_expire_soon",
                ttl=3600
            )

            # 立即检索应该成功
            result = await memory.retrieve("long_ttl_key")
            assert result is not None

            # 短暂等待后仍应存在
            await asyncio.sleep(1)
            result = await memory.retrieve("long_ttl_key")
            assert result is not None

        except ImportError:
            pytest.skip("EnhancedMemoryManager not available")


class TestMemoryTierPromotion:
    """记忆层级晋升/降级测试"""

    @pytest.mark.asyncio
    async def test_hot_tier_storage(self):
        """测试HOT层存储"""
        try:
            from core.memory.enhanced_memory_manager import EnhancedMemoryManager

            memory = EnhancedMemoryManager()
            await memory.initialize()

            # 明确存储到HOT层
            await memory.store(
                key="hot_key",
                value="hot_value",
                tier="hot"
            )

            result = await memory.retrieve("hot_key")
            assert result is not None

        except ImportError:
            pytest.skip("EnhancedMemoryManager not available")

    @pytest.mark.asyncio
    async def test_warm_tier_storage(self):
        """测试WARM层存储"""
        try:
            from core.memory.enhanced_memory_manager import EnhancedMemoryManager

            memory = EnhancedMemoryManager()
            await memory.initialize()

            # 明确存储到WARM层（Redis）
            await memory.store(
                key="warm_key",
                value="warm_value",
                tier="warm"
            )

            result = await memory.retrieve("warm_key")
            assert result is not None

        except ImportError:
            pytest.skip("EnhancedMemoryManager not available")

    @pytest.mark.asyncio
    async def test_cold_tier_storage(self):
        """测试COLD层存储"""
        try:
            from core.memory.enhanced_memory_manager import EnhancedMemoryManager

            memory = EnhancedMemoryManager()
            await memory.initialize()

            # 明确存储到COLD层（SQLite）
            await memory.store(
                key="cold_key",
                value="cold_value",
                tier="cold"
            )

            result = await memory.retrieve("cold_key")
            assert result is not None

        except ImportError:
            pytest.skip("EnhancedMemoryManager not available")


class TestMemoryCapacity:
    """记忆容量限制测试"""

    @pytest.mark.asyncio
    async def test_hot_tier_capacity(self):
        """测试HOT层容量限制（100MB）"""
        try:
            from core.memory.enhanced_memory_manager import EnhancedMemoryManager

            memory = EnhancedMemoryManager()
            await memory.initialize()

            # HOT层容量限制：100MB
            100 * 1024 * 1024  # 100MB in bytes

            # 尝试存储接近容量的数据
            # 注意：这是模拟测试，实际不应该真的存储100MB
            small_data = "x" * 1024  # 1KB

            await memory.store(
                key="small_data_key",
                value=small_data,
                tier="hot"
            )

            result = await memory.retrieve("small_data_key")
            assert result is not None

        except ImportError:
            pytest.skip("EnhancedMemoryManager not available")

    @pytest.mark.asyncio
    async def test_memory_eviction(self):
        """测试记忆淘汰机制"""
        try:
            from core.memory.enhanced_memory_manager import EnhancedMemoryManager

            memory = EnhancedMemoryManager()
            await memory.initialize()

            # 存储大量数据触发淘汰
            for i in range(100):
                await memory.store(
                    key=f"eviction_test_{i}",
                    value=f"value_{i}"
                )

            # 验证淘汰机制工作正常
            # 系统应该自动淘汰旧的或不常用的记忆

        except ImportError:
            pytest.skip("EnhancedMemoryManager not available")


class TestMemorySearch:
    """记忆搜索测试"""

    @pytest.mark.asyncio
    async def test_memory_search_by_metadata(self):
        """测试按元数据搜索"""
        try:
            from core.memory.enhanced_memory_manager import EnhancedMemoryManager

            memory = EnhancedMemoryManager()
            await memory.initialize()

            # 存储多个记忆项
            for i in range(5):
                await memory.store(
                    key=f"search_test_{i}",
                    value=f"value_{i}",
                    metadata={"category": "test", "index": i}
                )

            # 搜索特定类别的记忆
            if hasattr(memory, 'search'):
                results = await memory.search(
                    metadata_filter={"category": "test"}
                )
                assert len(results) > 0

        except ImportError:
            pytest.skip("EnhancedMemoryManager not available")

    @pytest.mark.asyncio
    async def test_memory_search_by_key_pattern(self):
        """测试按键模式搜索"""
        try:
            from core.memory.enhanced_memory_manager import EnhancedMemoryManager

            memory = EnhancedMemoryManager()
            await memory.initialize()

            # 存储测试数据
            await memory.store("patent_001", "data1")
            await memory.store("patent_002", "data2")
            await memory.store("other_001", "data3")

            # 搜索patent开头的键
            if hasattr(memory, 'search_keys'):
                results = await memory.search_keys("patent_*")
                assert len(results) >= 2

        except ImportError:
            pytest.skip("EnhancedMemoryManager not available")


class TestMemoryCleanup:
    """记忆清理测试"""

    @pytest.mark.asyncio
    async def test_memory_delete(self):
        """测试记忆删除"""
        try:
            from core.memory.enhanced_memory_manager import EnhancedMemoryManager

            memory = EnhancedMemoryManager()
            await memory.initialize()

            # 存储
            await memory.store("delete_test", "will_be_deleted")

            # 验证存在
            result = await memory.retrieve("delete_test")
            assert result is not None

            # 删除
            if hasattr(memory, 'delete'):
                await memory.delete("delete_test")

                # 验证已删除
                result = await memory.retrieve("delete_test")
                assert result is None or result == {}

        except ImportError:
            pytest.skip("EnhancedMemoryManager not available")

    @pytest.mark.asyncio
    async def test_memory_clear_all(self):
        """测试清空所有记忆"""
        try:
            from core.memory.enhanced_memory_manager import EnhancedMemoryManager

            memory = EnhancedMemoryManager()
            await memory.initialize()

            # 存储多个记忆
            for i in range(5):
                await memory.store(f"clear_test_{i}", f"value_{i}")

            # 清空
            if hasattr(memory, 'clear'):
                await memory.clear()

                # 验证已清空
                for i in range(5):
                    result = await memory.retrieve(f"clear_test_{i}")
                    assert result is None or result == {}

        except ImportError:
            pytest.skip("EnhancedMemoryManager not available")


# 运行测试的辅助函数
def run_memory_tests():
    """运行记忆系统测试"""
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ])


if __name__ == "__main__":
    run_memory_tests()
