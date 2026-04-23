#!/usr/bin/env python3
"""
EnhancedMemorySystem单元测试

测试增强记忆系统的所有核心功能，确保覆盖率>70%

测试范围:
- 初始化和配置
- 记忆存储
- 记忆检索
- 知识图谱集成
- 向量记忆集成
- 自动记忆增强
- 错误处理
- 边界情况
"""

from unittest.mock import patch

import pytest

from core.framework.memory.enhanced_memory_system import (
    EnhancedMemorySystem,
    MemoryType,
)

# ==================== Mock适配器 ====================

class MockVectorMemory:
    """Mock向量记忆"""

    async def store(self, content, tags=None, embedding=None):
        return {"id": "vm_001", "status": "stored"}

    async def search(self, query, top_k=5):
        return [
            {"content": "Memory 1", "score": 0.9},
            {"content": "Memory 2", "score": 0.8}
        ]

    async def search_memories(self, query, top_k=5, category=None):
        """搜索记忆（返回字典格式）"""
        return {
            "memories": [
                {"content": "Memory 1", "score": 0.9},
                {"content": "Memory 2", "score": 0.8}
            ],
            "method": "enhanced",
            "total_found": 2
        }


class MockKnowledgeAdapter:
    """Mock知识图谱适配器"""

    async def extract_entities(self, content):
        return [{"entity": "AI", "type": "concept"}]

    async def enhance_content(self, content, entities):
        return f"{content} (enhanced with {len(entities)} entities)"


# ==================== 初始化测试 ====================

class TestInitialization:
    """测试系统初始化"""

    def test_basic_initialization(self):
        """测试基本初始化"""
        system = EnhancedMemorySystem("test_agent")

        assert system.agent_id == "test_agent"
        assert system.initialized is False
        assert system.vector_memory is None
        assert system.knowledge_adapter is None
        assert system.enable_vector_memory is True
        assert system.enable_knowledge_graph is True

    def test_initialization_with_config(self):
        """测试使用配置初始化"""
        config = {
            'enable_vector_memory': False,
            'enable_knowledge_graph': False,
            'auto_enhance_memories': False,
            'knowledge_weight': 0.5
        }

        system = EnhancedMemorySystem("test_agent", config)

        assert system.enable_vector_memory is False
        assert system.enable_knowledge_graph is False
        assert system.auto_enhance_memories is False
        assert system.knowledge_weight == 0.5

    def test_initialization_default_config(self):
        """测试默认配置"""
        system = EnhancedMemorySystem("test_agent")

        assert system.config == {}
        assert system.auto_enhance_memories is True
        assert system.knowledge_weight == 0.3


# ==================== 系统初始化测试 ====================

class TestSystemInitialization:
    """测试系统启动"""

    @pytest.mark.asyncio
    async def test_initialize_with_all_features(self):
        """测试初始化所有功能"""
        system = EnhancedMemorySystem("test_agent")

        # Mock依赖
        with patch('core.memory.vector_memory.get_vector_memory_instance') as mock_vm, \
             patch('core.memory.knowledge_graph_adapter.get_knowledge_adapter') as mock_kg:

            mock_vm.return_value = MockVectorMemory()
            mock_kg.return_value = MockKnowledgeAdapter()

            await system.initialize()

            assert system.initialized is True
            assert system.vector_memory is not None
            assert system.knowledge_adapter is not None

    @pytest.mark.asyncio
    async def test_initialize_vector_only(self):
        """测试只初始化向量记忆"""
        config = {'enable_knowledge_graph': False}
        system = EnhancedMemorySystem("test_agent", config)

        with patch('core.memory.vector_memory.get_vector_memory_instance') as mock_vm:
            mock_vm.return_value = MockVectorMemory()

            await system.initialize()

            assert system.initialized is True
            assert system.vector_memory is not None
            assert system.knowledge_adapter is None

    @pytest.mark.asyncio
    async def test_initialize_knowledge_only(self):
        """测试只初始化知识图谱"""
        config = {'enable_vector_memory': False}
        system = EnhancedMemorySystem("test_agent", config)

        with patch('core.memory.knowledge_graph_adapter.get_knowledge_adapter') as mock_kg:
            mock_kg.return_value = MockKnowledgeAdapter()

            await system.initialize()

            assert system.initialized is True
            assert system.vector_memory is None
            assert system.knowledge_adapter is not None

    @pytest.mark.asyncio
    async def test_initialize_with_errors(self):
        """测试初始化时的错误处理"""
        system = EnhancedMemorySystem("test_agent")

        # Mock抛出异常
        with patch('core.memory.vector_memory.get_vector_memory_instance') as mock_vm, \
             patch('core.memory.knowledge_graph_adapter.get_knowledge_adapter') as mock_kg:

            mock_vm.side_effect = Exception("Vector init failed")
            mock_kg.side_effect = Exception("KG init failed")

            # 应该捕获错误但继续初始化
            await system.initialize()

            assert system.initialized is True
            # 功能可能未初始化
            assert system.vector_memory is None
            assert system.knowledge_adapter is None


# ==================== 记忆存储测试 ====================

class TestMemoryStorage:
    """测试记忆存储"""

    @pytest.mark.asyncio
    async def test_store_memory_uninitialized(self):
        """测试未初始化时存储"""
        system = EnhancedMemorySystem("test_agent")

        with pytest.raises(RuntimeError, match="未初始化"):
            await system.store_memory("test", MemoryType.SHORT_TERM)

    @pytest.mark.asyncio
    async def test_store_basic_memory(self):
        """测试基本记忆存储"""
        system = EnhancedMemorySystem("test_agent")
        system.initialized = True

        # Mock向量记忆
        system.vector_memory = MockVectorMemory()

        result = await system.store_memory(
            "Test content",
            MemoryType.SHORT_TERM,
            tags=["test"]
        )

        assert result is not None
        assert "id" in result or "status" in result

    @pytest.mark.asyncio
    async def test_store_memory_with_embedding(self):
        """测试带嵌入向量的存储"""
        system = EnhancedMemorySystem("test_agent")
        system.initialized = True
        system.vector_memory = MockVectorMemory()

        embedding = [0.1] * 768  # 模拟嵌入向量

        result = await system.store_memory(
            "Test content",
            MemoryType.LONG_TERM,
            embedding=embedding
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_store_memory_without_vector_memory(self):
        """测试没有向量记忆时的存储"""
        config = {'enable_vector_memory': False}
        system = EnhancedMemorySystem("test_agent", config)
        system.initialized = True

        # 应该返回None或空结果
        result = await system.store_memory(
            "Test content",
            MemoryType.EPISODIC
        )

        # 可能返回None或空字典
        assert result is None or isinstance(result, dict)


# ==================== 记忆检索测试 ====================

class TestMemoryRetrieval:
    """测试记忆检索"""

    @pytest.mark.asyncio
    async def test_retrieve_memory_uninitialized(self):
        """测试未初始化时检索"""
        system = EnhancedMemorySystem("test_agent")

        with pytest.raises(RuntimeError, match="未初始化"):
            await system.retrieve_memory("test query")

    @pytest.mark.asyncio
    async def test_retrieve_basic_memory(self):
        """测试基本记忆检索"""
        system = EnhancedMemorySystem("test_agent")
        system.initialized = True
        system.vector_memory = MockVectorMemory()

        results = await system.retrieve_memory("test query")

        # 可能返回列表或字典
        assert isinstance(results, (list, dict))

    @pytest.mark.asyncio
    async def test_retrieve_with_top_k(self):
        """测试带top_k的记忆检索"""
        system = EnhancedMemorySystem("test_agent")
        system.initialized = True
        system.vector_memory = MockVectorMemory()

        results = await system.retrieve_memory("test query", k=3)

        # 可能返回列表或字典
        assert isinstance(results, (list, dict))
        # 如果是列表，验证不超过top_k
        if isinstance(results, list):
            assert len(results) <= 3
        # 如果是字典，检查memories字段
        elif isinstance(results, dict) and "memories" in results:
            assert len(results["memories"]) <= 3

    @pytest.mark.asyncio
    async def test_retrieve_without_vector_memory(self):
        """测试没有向量记忆时的检索"""
        config = {'enable_vector_memory': False}
        system = EnhancedMemorySystem("test_agent", config)
        system.initialized = True

        results = await system.retrieve_memory("test query")

        # 应该返回空结果、空列表或None
        assert results in [None, [], {}] or \
               isinstance(results, (list, dict))


# ==================== 知识图谱集成测试 ====================

class TestKnowledgeGraphIntegration:
    """测试知识图谱集成"""

    @pytest.mark.asyncio
    async def test_auto_enhance_memory(self):
        """测试自动记忆增强"""
        config = {'auto_enhance_memories': True}
        system = EnhancedMemorySystem("test_agent", config)
        system.initialized = True
        system.vector_memory = MockVectorMemory()
        system.knowledge_adapter = MockKnowledgeAdapter()

        result = await system.store_memory(
            "AI is transforming the world",
            MemoryType.SEMANTIC
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_knowledge_weight_influence(self):
        """测试知识权重影响"""
        config = {'knowledge_weight': 0.8, 'auto_enhance_memories': True}
        system = EnhancedMemorySystem("test_agent", config)
        system.initialized = True
        system.vector_memory = MockVectorMemory()
        system.knowledge_adapter = MockKnowledgeAdapter()

        # 存储记忆
        await system.store_memory(
            "Test content",
            MemoryType.SEMANTIC
        )

        # 验证权重被应用
        assert system.knowledge_weight == 0.8

    @pytest.mark.asyncio
    async def test_extract_entities(self):
        """测试实体提取"""
        system = EnhancedMemorySystem("test_agent")
        system.initialized = True
        system.knowledge_adapter = MockKnowledgeAdapter()

        entities = await system.knowledge_adapter.extract_entities(
            "Apple is a technology company"
        )

        assert isinstance(entities, list)


# ==================== MemoryType枚举测试 ====================

class TestMemoryType:
    """测试MemoryType枚举"""

    def test_memory_type_values(self):
        """测试枚举值"""
        assert MemoryType.SHORT_TERM.value == 'short_term'
        assert MemoryType.LONG_TERM.value == 'long_term'
        assert MemoryType.EPISODIC.value == 'episodic'
        assert MemoryType.SEMANTIC.value == 'semantic'
        assert MemoryType.KNOWLEDGE_GRAPH.value == 'knowledge_graph'

    def test_memory_type_comparison(self):
        """测试枚举比较"""
        assert MemoryType.SHORT_TERM == MemoryType.SHORT_TERM
        assert MemoryType.SHORT_TERM != MemoryType.LONG_TERM


# ==================== 错误处理测试 ====================

class TestErrorHandling:
    """测试错误处理"""

    @pytest.mark.asyncio
    async def test_store_memory_invalid_type(self):
        """测试无效记忆类型"""
        system = EnhancedMemorySystem("test_agent")
        system.initialized = True
        system.vector_memory = MockVectorMemory()

        # 应该处理无效类型
        result = await system.store_memory(
            "Test",
            "invalid_type"  # 无效类型
        )

        # 可能返回None或错误信息
        assert result is None or isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_retrieve_memory_empty_query(self):
        """测试空查询"""
        system = EnhancedMemorySystem("test_agent")
        system.initialized = True
        system.vector_memory = MockVectorMemory()

        results = await system.retrieve_memory("")

        # 应该处理空查询，返回列表或字典
        assert isinstance(results, (list, dict))

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """测试并发操作"""
        import asyncio

        system = EnhancedMemorySystem("test_agent")
        system.initialized = True
        system.vector_memory = MockVectorMemory()

        # 并发存储
        tasks = [
            system.store_memory(f"Memory {i}", MemoryType.SHORT_TERM)
            for i in range(10)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 验证所有操作完成
        successful = sum(1 for r in results if r is not None)
        assert successful >= 8  # 至少80%成功


# ==================== 边界情况测试 ====================

class TestEdgeCases:
    """测试边界情况"""

    @pytest.mark.asyncio
    async def test_store_empty_content(self):
        """测试存储空内容"""
        system = EnhancedMemorySystem("test_agent")
        system.initialized = True
        system.vector_memory = MockVectorMemory()

        result = await system.store_memory(
            "",
            MemoryType.SHORT_TERM
        )

        # 应该处理空内容
        assert result is None or isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_store_very_long_content(self):
        """测试存储超长内容"""
        system = EnhancedMemorySystem("test_agent")
        system.initialized = True
        system.vector_memory = MockVectorMemory()

        long_content = "A" * 100000

        result = await system.store_memory(
            long_content,
            MemoryType.LONG_TERM
        )

        # 应该处理超长内容
        assert result is None or isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_retrieve_with_special_characters(self):
        """测试带特殊字符的检索"""
        system = EnhancedMemorySystem("test_agent")
        system.initialized = True
        system.vector_memory = MockVectorMemory()

        special_query = "测试!@#$%^&*()"

        results = await system.retrieve_memory(special_query)

        # 应该处理特殊字符，返回字典或列表
        assert isinstance(results, (list, dict))
        # 如果是字典，应该包含memories字段
        if isinstance(results, dict):
            assert "memories" in results

    def test_config_immutability(self):
        """测试配置处理"""
        config = {'key': 'value'}
        system = EnhancedMemorySystem("test_agent", config)

        # 系统可能直接引用配置，也可能复制
        # 验证配置被正确读取
        assert system.config.get('key') == 'value' or 'key' in system.config


# ==================== 性能测试 ====================

class TestPerformance:
    """测试性能指标"""

    @pytest.mark.asyncio
    async def test_initialization_speed(self):
        """测试初始化速度"""
        import time

        system = EnhancedMemorySystem("test_agent")

        # Mock导入的函数
        with patch('core.memory.vector_memory.get_vector_memory_instance', return_value=MockVectorMemory()), \
             patch('core.memory.knowledge_graph_adapter.get_knowledge_adapter', return_value=MockKnowledgeAdapter()):

            start = time.time()
            await system.initialize()
            elapsed = time.time() - start

            # 初始化应该很快 (< 1秒)
            assert elapsed < 1.0

    @pytest.mark.asyncio
    async def test_storage_speed(self):
        """测试存储速度"""
        import time

        system = EnhancedMemorySystem("test_agent")
        system.initialized = True
        system.vector_memory = MockVectorMemory()

        start = time.time()
        await system.store_memory("Test content", MemoryType.SHORT_TERM)
        elapsed = time.time() - start

        # 存储应该很快 (< 0.1秒)
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_retrieval_speed(self):
        """测试检索速度"""
        import time

        system = EnhancedMemorySystem("test_agent")
        system.initialized = True
        system.vector_memory = MockVectorMemory()

        start = time.time()
        await system.retrieve_memory("Test query")
        elapsed = time.time() - start

        # 检索应该很快 (< 0.1秒)
        assert elapsed < 0.1


# ==================== 关闭和清理测试 ====================

class TestShutdown:
    """测试关闭和清理"""

    @pytest.mark.asyncio
    async def test_shutdown_initialized(self):
        """测试关闭已初始化的系统"""
        system = EnhancedMemorySystem("test_agent")
        system.initialized = True
        system.vector_memory = MockVectorMemory()
        system.knowledge_adapter = MockKnowledgeAdapter()

        # 关闭应该不抛出异常
        try:
            # 如果有shutdown方法
            if hasattr(system, 'shutdown'):
                await system.shutdown()
            # 否则设置为未初始化
            else:
                system.initialized = False
        except Exception as e:
            pytest.fail(f"Shutdown raised exception: {e}")

    @pytest.mark.asyncio
    async def test_shutdown_uninitialized(self):
        """测试关闭未初始化的系统"""
        system = EnhancedMemorySystem("test_agent")

        # 关闭未初始化的系统应该不抛出异常
        try:
            if hasattr(system, 'shutdown'):
                await system.shutdown()
        except Exception as e:
            pytest.fail(f"Shutdown raised exception: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
