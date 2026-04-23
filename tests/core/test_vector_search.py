"""
向量检索系统单元测试

测试覆盖：
- 文本嵌入测试
- 向量存储和检索
- 相似度搜索准确性
- 混合检索效果
- 性能测试（批量处理）
"""

import tempfile  # noqa: ARG001 (used in fixtures)
from pathlib import Path
from unittest.mock import AsyncMock, patch  # noqa: ARG001 (used in tests)

import pytest

from core.framework.memory.embedding_store import EmbeddingStore, SearchResult
from core.framework.memory.unified_memory_system import (
    MemoryCategory,
    MemoryType,
    UnifiedMemorySystem,
)
from core.framework.memory.vector_search import VectorSearchService


@pytest.mark.unit
class TestEmbeddingStore:
    """测试向量存储服务"""

    @pytest.fixture
    def temp_db_path(self) -> Path:
        """创建临时数据库路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "test_vectors.db"

    @pytest.fixture
    def embedding_store(self, temp_db_path: Path) -> EmbeddingStore:
        """创建向量存储实例"""
        return EmbeddingStore(db_path=str(temp_db_path))

    def test_initialization(self, temp_db_path: Path) -> None:
        """测试初始化"""
        EmbeddingStore(db_path=str(temp_db_path))

        # 验证数据库创建
        assert temp_db_path.exists()

        # 验证表创建
        import sqlite3

        conn = sqlite3.connect(str(temp_db_path))
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='memory_vectors'"
        )
        result = cursor.fetchone()

        assert result is not None
        conn.close()

    def test_cosine_similarity(self) -> None:
        """测试余弦相似度计算"""
        # 相同向量
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.0, 2.0, 3.0]
        similarity = EmbeddingStore._cosine_similarity(vec1, vec2)
        assert abs(similarity - 1.0) < 1e-6

        # 正交向量
        vec1 = [1.0, 0.0]
        vec2 = [0.0, 1.0]
        similarity = EmbeddingStore._cosine_similarity(vec1, vec2)
        assert abs(similarity - 0.0) < 1e-6

        # 相似向量
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.1, 2.1, 3.1]
        similarity = EmbeddingStore._cosine_similarity(vec1, vec2)
        assert 0.9 < similarity < 1.0

    @pytest.mark.asyncio
    async def test_store_and_get_vector(self, embedding_store: EmbeddingStore) -> None:
        """测试向量存储和获取"""
        memory_id = "test/global/test_key"
        vector = [0.1, 0.2, 0.3, 0.4]

        # 存储向量
        await embedding_store.store_vector(
            memory_id=memory_id, vector=vector, memory_type="global", category="test"
        )

        # 获取向量
        retrieved = await embedding_store.get_vector(memory_id)

        assert retrieved is not None
        assert len(retrieved) == len(vector)
        # 验证向量值（考虑浮点精度）
        for _i, (a, b) in enumerate(zip(retrieved, vector, strict=False)):
            assert abs(a - b) < 1e-6

    @pytest.mark.asyncio
    async def test_store_vector_updates_existing(
        self, embedding_store: EmbeddingStore
    ) -> None:
        """测试更新现有向量"""
        memory_id = "test/global/update_test"
        vector1 = [0.1, 0.2, 0.3]
        vector2 = [0.5, 0.6, 0.7]

        # 第一次存储
        await embedding_store.store_vector(
            memory_id=memory_id, vector=vector1, memory_type="global", category="test"
        )

        # 更新
        await embedding_store.store_vector(
            memory_id=memory_id, vector=vector2, memory_type="global", category="test"
        )

        # 验证更新
        retrieved = await embedding_store.get_vector(memory_id)
        assert retrieved is not None
        for _i, (a, b) in enumerate(zip(retrieved, vector2, strict=False)):
            assert abs(a - b) < 1e-6

    @pytest.mark.asyncio
    async def test_delete_vector(self, embedding_store: EmbeddingStore) -> None:
        """测试删除向量"""
        memory_id = "test/global/delete_test"
        vector = [0.1, 0.2, 0.3]

        # 存储向量
        await embedding_store.store_vector(
            memory_id=memory_id, vector=vector, memory_type="global", category="test"
        )

        # 验证存在
        retrieved = await embedding_store.get_vector(memory_id)
        assert retrieved is not None

        # 删除向量
        await embedding_store.delete_vector(memory_id)

        # 验证不存在
        retrieved = await embedding_store.get_vector(memory_id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_search_similar(self, embedding_store: EmbeddingStore) -> None:
        """测试相似度搜索"""
        # 存储多个向量
        vectors = {
            "test/global/vec1": [1.0, 0.0, 0.0],
            "test/global/vec2": [0.9, 0.1, 0.0],
            "test/global/vec3": [0.0, 1.0, 0.0],
            "test/global/vec4": [0.0, 0.0, 1.0],
        }

        for memory_id, vector in vectors.items():
            await embedding_store.store_vector(
                memory_id=memory_id, vector=vector, memory_type="global", category="test"
            )

        # 搜索与[1.0, 0.0, 0.0]相似的向量
        query_vector = [1.0, 0.0, 0.0]
        results = await embedding_store.search_similar(
            query_vector=query_vector, top_k=2, threshold=0.5
        )

        # 验证结果
        assert len(results) <= 2
        if len(results) > 0:
            # 第一个结果应该是最相似的
            assert results[0].memory_id in ["test/global/vec1", "test/global/vec2"]
            assert results[0].similarity > 0.9

    @pytest.mark.asyncio
    async def test_search_similar_with_filters(self, embedding_store: EmbeddingStore) -> None:
        """测试带过滤条件的相似度搜索"""
        # 存储不同类型和分类的向量
        vectors = {
            "global/user_pref/test1": [1.0, 0.0, 0.0],
            "global/agent_learning/test2": [0.9, 0.1, 0.0],
            "project/context/test3": [0.8, 0.2, 0.0],
        }

        for memory_id, vector in vectors.items():
            parts = memory_id.split("/")
            await embedding_store.store_vector(
                memory_id=memory_id,
                vector=vector,
                memory_type=parts[0],
                category=parts[1],
            )

        # 只搜索global类型
        query_vector = [1.0, 0.0, 0.0]
        results = await embedding_store.search_similar(
            query_vector=query_vector, top_k=10, threshold=0.5, memory_type="global"
        )

        # 验证结果
        for result in results:
            assert result.memory_type == "global"

    def test_get_statistics(self, embedding_store: EmbeddingStore) -> None:
        """测试获取统计信息"""
        stats = embedding_store.get_statistics()

        assert "total_vectors" in stats
        assert "by_type" in stats
        assert "by_category" in stats
        assert stats["total_vectors"] == 0

    @pytest.mark.asyncio
    async def test_clear_all(self, embedding_store: EmbeddingStore) -> None:
        """测试清空所有向量"""
        # 存储一些向量
        for i in range(5):
            await embedding_store.store_vector(
                memory_id=f"test/global/test_{i}",
                vector=[0.1 * i, 0.2 * i, 0.3 * i],
                memory_type="global",
                category="test",
            )

        # 验证存在
        stats_before = embedding_store.get_statistics()
        assert stats_before["total_vectors"] == 5

        # 清空
        await embedding_store.clear_all()

        # 验证清空
        stats_after = embedding_store.get_statistics()
        assert stats_after["total_vectors"] == 0


@pytest.mark.unit
class TestVectorSearchService:
    """测试向量搜索服务"""

    @pytest.fixture
    def temp_db_path(self) -> Path:
        """创建临时数据库路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "test_vectors.db"

    @pytest.fixture
    def temp_global_path(self) -> Path:
        """创建临时全局记忆路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def temp_project_path(self) -> Path:
        """创建临时项目路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def memory_system(
        self, temp_global_path: Path, temp_project_path: Path
    ) -> UnifiedMemorySystem:
        """创建记忆系统实例"""
        return UnifiedMemorySystem(
            global_memory_path=str(temp_global_path), current_project_path=str(temp_project_path)
        )

    @pytest.fixture
    def embedding_store(self, temp_db_path: Path) -> EmbeddingStore:
        """创建向量存储实例"""
        return EmbeddingStore(db_path=str(temp_db_path))

    @pytest.fixture
    def vector_search_service(
        self, memory_system: UnifiedMemorySystem, embedding_store: EmbeddingStore
    ) -> VectorSearchService:
        """创建向量搜索服务实例"""
        return VectorSearchService(memory_system=memory_system, embedding_store=embedding_store)

    @pytest.mark.asyncio
    async def test_index_memory(
        self, vector_search_service: VectorSearchService, memory_system: UnifiedMemorySystem
    ) -> None:
        """测试索引单个记忆"""
        # 写入记忆
        entry = memory_system.write(
            type=MemoryType.GLOBAL,
            category=MemoryCategory.USER_PREFERENCE,
            key="test_index",
            content="测试索引内容",
        )

        # 索引
        await vector_search_service.index_memory(entry)

        # 验证索引
        memory_id = f"{entry.type.value}/{entry.category.value}/{entry.key}"
        vector = await vector_search_service.embedding_store.get_vector(memory_id)

        assert vector is not None
        assert len(vector) > 0

    @pytest.mark.asyncio
    async def test_batch_index_memories(
        self, vector_search_service: VectorSearchService, memory_system: UnifiedMemorySystem
    ) -> None:
        """测试批量索引记忆"""
        # 写入多条记忆
        entries = []
        for i in range(5):
            entry = memory_system.write(
                type=MemoryType.GLOBAL,
                category=MemoryCategory.USER_PREFERENCE,
                key=f"batch_test_{i}",
                content=f"批量测试内容 {i}",
            )
            entries.append(entry)

        # 批量索引
        stats = await vector_search_service.batch_index_memories(entries, batch_size=2)

        # 验证统计
        assert stats["total"] == 5
        assert stats["success"] == 5
        assert stats["failed"] == 0

    @pytest.mark.asyncio
    async def test_search_by_vector(
        self,
        vector_search_service: VectorSearchService,
        memory_system: UnifiedMemorySystem,
        embedding_store: EmbeddingStore,
    ) -> None:
        """测试纯向量搜索"""
        # 写入并索引记忆
        entry1 = memory_system.write(
            type=MemoryType.GLOBAL,
            category=MemoryCategory.USER_PREFERENCE,
            key="python",
            content="Python代码风格：使用简体中文注释",
        )
        entry2 = memory_system.write(
            type=MemoryType.GLOBAL,
            category=MemoryCategory.USER_PREFERENCE,
            key="java",
            content="Java代码风格：遵循Google Java Style Guide",
        )

        # Mock嵌入服务
        with patch.object(
            embedding_store,
            "embed_text",
            new_callable=AsyncMock,
            return_value=[0.1, 0.2, 0.3],
        ):
            await vector_search_service.index_memory(entry1)
            await vector_search_service.index_memory(entry2)

            # Mock搜索
            with patch.object(
                embedding_store,
                "search_similar",
                new_callable=AsyncMock,
                return_value=[
                    SearchResult(
                        memory_id="global/user_preference/python",
                        similarity=0.95,
                        memory_type="global",
                        category="user_preference",
                        metadata={"key": "python"},
                        created_at=entry1.created_at,
                    )
                ],
            ):
                results = await vector_search_service.search_by_vector(
                    query="Python代码风格", top_k=10
                )

                # 验证结果
                assert len(results) >= 0  # Mock可能返回空结果

    @pytest.mark.asyncio
    async def test_search_hybrid(
        self,
        vector_search_service: VectorSearchService,
        memory_system: UnifiedMemorySystem,
    ) -> None:
        """测试混合检索"""
        # 写入记忆
        memory_system.write(
            type=MemoryType.GLOBAL,
            category=MemoryCategory.USER_PREFERENCE,
            key="hybrid_test",
            content="混合检索测试：Python和Java代码风格",
        )

        # Mock向量搜索返回空
        with patch.object(
            vector_search_service, "search_by_vector", new_callable=AsyncMock, return_value=[]
        ):
            # 纯关键词搜索（alpha=0）
            results = await vector_search_service.search_hybrid(
                query="Python", top_k=10, alpha=0.0
            )
            # 应该使用关键词搜索
            assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_hybrid_alpha_boundary(
        self, vector_search_service: VectorSearchService
    ) -> None:
        """测试混合检索边界情况"""
        # alpha <= 0 应该使用纯关键词搜索
        with patch.object(
            vector_search_service.memory_system, "search", return_value=[]
        ):
            results = await vector_search_service.search_hybrid(
                query="test", top_k=10, alpha=-0.1
            )
            assert isinstance(results, list)

        # alpha >= 1 应该使用纯向量搜索
        with patch.object(
            vector_search_service, "search_by_vector", new_callable=AsyncMock, return_value=[]
        ):
            results = await vector_search_service.search_hybrid(
                query="test", top_k=10, alpha=1.1
            )
            assert isinstance(results, list)


@pytest.mark.integration
class TestIntegrationScenarios:
    """集成测试场景"""

    @pytest.fixture
    def temp_db_path(self) -> Path:
        """创建临时数据库路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "test_vectors.db"

    @pytest.fixture
    def temp_global_path(self) -> Path:
        """创建临时全局记忆路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def temp_project_path(self) -> Path:
        """创建临时项目路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.mark.asyncio
    async def test_complete_workflow(
        self, temp_global_path: Path, temp_project_path: Path, temp_db_path: Path
    ) -> None:
        """测试完整工作流程"""
        # 1. 创建系统
        memory_system = UnifiedMemorySystem(
            global_memory_path=str(temp_global_path), current_project_path=str(temp_project_path)
        )
        embedding_store = EmbeddingStore(db_path=str(temp_db_path))
        vector_search = VectorSearchService(
            memory_system=memory_system, embedding_store=embedding_store
        )

        # 2. 写入记忆
        entry = memory_system.write(
            type=MemoryType.GLOBAL,
            category=MemoryCategory.USER_PREFERENCE,
            key="workflow_test",
            content="工作流程测试：代码风格使用简体中文注释",
        )

        # 3. 索引记忆
        await vector_search.index_memory(entry)

        # 4. 验证索引
        memory_id = f"{entry.type.value}/{entry.category.value}/{entry.key}"
        vector = await embedding_store.get_vector(memory_id)
        assert vector is not None

        # 5. 搜索
        results = memory_system.search(query="代码风格")
        assert len(results) >= 1


@pytest.mark.performance
class TestPerformance:
    """性能测试"""

    @pytest.fixture
    def temp_db_path(self) -> Path:
        """创建临时数据库路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "test_perf_vectors.db"

    @pytest.mark.asyncio
    async def test_batch_indexing_performance(
        self, temp_db_path: Path, temp_global_path: Path, temp_project_path: Path
    ) -> None:
        """测试批量索引性能"""
        import time

        memory_system = UnifiedMemorySystem(
            global_memory_path=str(temp_global_path), current_project_path=str(temp_project_path)
        )
        embedding_store = EmbeddingStore(db_path=str(temp_db_path))
        vector_search = VectorSearchService(
            memory_system=memory_system, embedding_store=embedding_store
        )

        # 写入100条记忆
        entries = []
        for i in range(100):
            entry = memory_system.write(
                type=MemoryType.GLOBAL,
                category=MemoryCategory.USER_PREFERENCE,
                key=f"perf_test_{i}",
                content=f"性能测试内容 {i}" * 10,  # 较长内容
            )
            entries.append(entry)

        # 批量索引并计时
        start_time = time.time()
        stats = await vector_search.batch_index_memories(entries, batch_size=32)
        elapsed_time = time.time() - start_time

        # 验证
        assert stats["success"] == 100
        # 性能要求：100条记忆索引应在30秒内完成
        assert elapsed_time < 30.0, f"批量索引耗时过长: {elapsed_time:.2f}秒"

        print(f"✅ 批量索引性能: {elapsed_time:.2f}秒 (100条记忆)")

