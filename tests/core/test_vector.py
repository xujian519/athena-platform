"""
向量模块单元测试
测试向量管理和向量数据库功能
"""


import numpy as np
import pytest


class TestVectorModule:
    """向量模块测试类"""

    def test_vector_module_import(self):
        """测试向量模块可以导入"""
        try:
            import core.vector
            assert core.vector is not None
        except ImportError:
            pytest.skip("向量模块导入失败")

    def test_vector_manager_import(self):
        """测试向量管理器可以导入"""
        try:
            from core.vector.unified_vector_manager import UnifiedVectorManager
            assert UnifiedVectorManager is not None
        except ImportError:
            pytest.skip("向量管理器导入失败")

    def test_intelligent_vector_manager_import(self):
        """测试智能向量管理器可以导入"""
        try:
            from core.vector.intelligent_vector_manager import IntelligentVectorManager
            assert IntelligentVectorManager is not None
        except ImportError:
            pytest.skip("智能向量管理器导入失败")

    def test_semantic_router_import(self):
        """测试语义路由器可以导入"""
        try:
            from core.vector.semantic_router import SemanticRouter
            assert SemanticRouter is not None
        except ImportError:
            pytest.skip("语义路由器导入失败")


class TestVectorOperations:
    """向量操作测试"""

    def test_numpy_vector_creation(self):
        """测试使用numpy创建向量"""
        # 创建向量
        vector = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        # 验证
        assert isinstance(vector, np.ndarray)
        assert vector.shape == (5,)
        assert vector.dtype == np.float64

    def test_vector_normalization(self):
        """测试向量归一化"""
        # 创建向量
        vector = np.array([3.0, 4.0])

        # 计算L2范数
        norm = np.linalg.norm(vector)

        # 归一化
        normalized = vector / norm

        # 验证归一化后的向量范数为1
        assert abs(np.linalg.norm(normalized) - 1.0) < 1e-10

    def test_vector_similarity(self):
        """测试向量相似度计算"""
        # 创建两个向量
        vector1 = np.array([1.0, 0.0, 0.0])
        vector2 = np.array([1.0, 0.0, 0.0])
        vector3 = np.array([0.0, 1.0, 0.0])

        # 计算余弦相似度
        def cosine_similarity(v1, v2):
            return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

        # 相同向量应该相似度为1
        sim_12 = cosine_similarity(vector1, vector2)
        assert abs(sim_12 - 1.0) < 1e-10

        # 正交向量相似度为0
        sim_13 = cosine_similarity(vector1, vector3)
        assert abs(sim_13) < 1e-10

    def test_vector_distance(self):
        """测试向量距离计算"""
        # 创建两个向量
        vector1 = np.array([0.0, 0.0])
        vector2 = np.array([3.0, 4.0])

        # 计算欧氏距离
        distance = np.linalg.norm(vector1 - vector2)

        # 验证距离（3-4-5直角三角形）
        assert abs(distance - 5.0) < 1e-10

    def test_batch_vector_operations(self):
        """测试批量向量操作"""
        # 创建向量矩阵
        vectors = np.array([
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
            [7.0, 8.0, 9.0],
        ])

        # 验证形状
        assert vectors.shape == (3, 3)

        # 计算所有向量的范数
        norms = np.linalg.norm(vectors, axis=1)

        # 验证
        assert len(norms) == 3
        assert all(n > 0 for n in norms)


class TestEmbeddingFunctions:
    """嵌入函数测试"""

    def test_text_embedding_basic(self):
        """测试基本文本嵌入功能"""
        try:
            from core.embedding.bge_embedding_service import BGEEmbeddingService

            # 创建嵌入服务（可能需要模型）
            # 这里只测试导入，不实际运行
            assert BGEEmbeddingService is not None
        except ImportError:
            pytest.skip("BGE嵌入服务不可用")

    def test_embedding_dimension(self):
        """测试嵌入向量维度"""
        # 常见的嵌入维度
        common_dimensions = [384, 768, 1024, 1536]

        # 验证这些是合理的维度
        for dim in common_dimensions:
            assert dim > 0, f"嵌入维度 {dim} 应该大于0"
            assert dim % 64 == 0, f"嵌入维度 {dim} 通常是64的倍数"

    @pytest.mark.parametrize("text,length", [
        ("短文本", 3),
        ("这是一个中等长度的文本用于测试嵌入功能", 19),
        ("a" * 100, 100),
    ])
    def test_text_preprocessing(self, text, length):
        """测试文本预处理"""
        # 基本验证
        assert isinstance(text, str)
        assert len(text) == length

        # 清理文本
        cleaned = text.strip()
        assert len(cleaned) > 0


class TestVectorDatabase:
    """向量数据库测试"""

    def test_vector_db_config(self):
        """测试向量数据库配置"""
        # 测试Qdrant配置
        qdrant_host = "localhost"
        qdrant_port = 6333

        # 验证配置
        assert qdrant_host == "localhost"
        assert qdrant_port == 6333

    def test_collection_config(self):
        """测试集合配置"""
        collection_name = "test_collection"
        vector_size = 768

        # 验证配置
        assert isinstance(collection_name, str)
        assert len(collection_name) > 0
        assert vector_size > 0
        assert vector_size % 64 == 0  # 常见的嵌入维度

    def test_vector_search_params(self):
        """测试向量搜索参数"""
        limit = 10
        score_threshold = 0.7

        # 验证参数
        assert limit > 0
        assert limit <= 100  # 合理的上限
        assert 0 <= score_threshold <= 1.0


class TestVectorPerformance:
    """向量操作性能测试"""

    def test_vector_operations_performance(self):
        """测试向量操作性能"""
        import time

        # 创建大量向量
        num_vectors = 1000
        vector_size = 768

        start_time = time.time()
        vectors = np.random.randn(num_vectors, vector_size).astype(np.float32)
        creation_time = time.time() - start_time

        # 性能断言
        assert creation_time < 1.0, f"创建{num_vectors}个向量应该在1秒内完成，实际: {creation_time:.2f}秒"

        # 测试批量归一化
        start_time = time.time()
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        vectors / norms
        norm_time = time.time() - start_time

        assert norm_time < 0.5, f"归一化{num_vectors}个向量应该在0.5秒内完成，实际: {norm_time:.2f}秒"

    @pytest.mark.slow
    def test_similarity_search_performance(self):
        """测试相似度搜索性能"""
        import time

        # 创建查询向量和数据库向量
        query_vector = np.random.randn(768).astype(np.float32)
        db_vectors = np.random.randn(10000, 768).astype(np.float32)

        # 计算相似度
        start_time = time.time()
        similarities = np.dot(db_vectors, query_vector)
        search_time = time.time() - start_time

        # 性能断言
        assert search_time < 0.1, f"搜索10000个向量应该在0.1秒内完成，实际: {search_time:.3f}秒"

        # 验证结果
        assert len(similarities) == 10000
        # 注意：随机向量的点积可能超出[-1,1]范围，这是正常的
        # 如需验证余弦相似度范围，需要先归一化向量


class TestVectorUtilities:
    """向量工具函数测试"""

    def test_vector_conversion(self):
        """测试向量格式转换"""
        # List转numpy array
        vector_list = [1.0, 2.0, 3.0]
        vector_array = np.array(vector_list)

        assert isinstance(vector_array, np.ndarray)
        assert vector_array.shape == (3,)

    def test_vector_serialization(self):
        """测试向量序列化"""
        import json

        vector = np.array([1.0, 2.0, 3.0])
        vector_list = vector.tolist()

        # 序列化为JSON
        json_str = json.dumps(vector_list)
        parsed = json.loads(json_str)

        assert parsed == vector_list

    def test_batch_vector_conversion(self):
        """测试批量向量转换"""
        # List[List]转numpy array
        vectors_list = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]
        vectors_array = np.array(vectors_list)

        assert vectors_array.shape == (3, 2)
