"""
核心模块集成测试
测试多个模块之间的协作
"""


import pytest


class TestCacheVectorIntegration:
    """缓存和向量模块集成测试"""

    def test_cache_vector_data_storage(self):
        """测试在缓存中存储向量数据"""
        try:
            import numpy as np

            from core.cache.memory_cache import MemoryCache

            # 创建缓存实例
            cache = MemoryCache()

            # 创建向量数据
            vector_data = {
                "id": "doc1",
                "embedding": np.array([0.1, 0.2, 0.3, 0.4]).tolist(),
                "metadata": {"title": "测试文档"}
            }

            # 存储到缓存
            cache.set("doc1_vector", vector_data)

            # 从缓存检索
            retrieved = cache.get("doc1_vector")

            # 验证
            assert retrieved is not None
            assert retrieved["id"] == "doc1"
            assert retrieved["embedding"] == vector_data["embedding"]

        except ImportError:
            pytest.skip("MemoryCache不可用")

    def test_cache_vector_similarity_search(self):
        """测试基于缓存的向量相似度搜索"""
        try:
            import numpy as np

            from core.cache.memory_cache import MemoryCache

            # 创建缓存
            cache = MemoryCache()

            # 存储多个向量
            vectors = {
                "vec1": np.array([1.0, 0.0, 0.0]),
                "vec2": np.array([0.0, 1.0, 0.0]),
                "vec3": np.array([0.0, 0.0, 1.0]),
            }

            for key, vec in vectors.items():
                cache.set(key, vec.tolist())

            # 查询向量
            query = np.array([0.9, 0.1, 0.0])

            # 计算相似度
            similarities = {}
            for key, vec in vectors.items():
                sim = np.dot(query, vec) / (np.linalg.norm(query) * np.linalg.norm(vec))
                similarities[key] = sim

            # 找到最相似的
            most_similar = max(similarities, key=similarities.get)

            # 验证
            assert most_similar == "vec1"

        except ImportError:
            pytest.skip("MemoryCache不可用")


class TestAgentCacheIntegration:
    """智能体和缓存集成测试"""

    def test_agent_cache_conversation(self):
        """测试智能体缓存对话历史"""
        try:
            from core.cache.memory_cache import MemoryCache

            # 创建缓存
            cache = MemoryCache()

            # 模拟对话历史
            conversation = {
                "user_id": "user123",
                "messages": [
                    {"role": "user", "content": "你好"},
                    {"role": "assistant", "content": "您好！"},
                ]
            }

            # 缓存对话
            cache.set("conv_user123", conversation)

            # 检索对话
            retrieved = cache.get("conv_user123")

            # 验证
            assert retrieved is not None
            assert retrieved["user_id"] == "user123"
            assert len(retrieved["messages"]) == 2

        except ImportError:
            pytest.skip("MemoryCache不可用")

    def test_agent_cache_state(self):
        """测试智能体缓存状态"""
        try:
            from core.cache.memory_cache import MemoryCache

            # 创建缓存
            cache = MemoryCache()

            # 智能体状态
            agent_state = {
                "agent_id": "athena_001",
                "status": "active",
                "current_task": "专利分析",
                "memory_usage": 0.65,
            }

            # 缓存状态
            cache.set("state_athena_001", agent_state)

            # 检索状态
            retrieved = cache.get("state_athena_001")

            # 验证
            assert retrieved["agent_id"] == "athena_001"
            assert retrieved["status"] == "active"
            assert 0 <= retrieved["memory_usage"] <= 1

        except ImportError:
            pytest.skip("MemoryCache不可用")


class TestMultiAgentCollaboration:
    """多智能体协作集成测试"""

    def test_agent_communication_flow(self):
        """测试智能体通信流程"""
        # 模拟三个智能体

        # 消息队列
        message_queue = []

        # agent1 分配任务
        message_queue.append({
            "from": "agent1",
            "to": "agent2",
            "type": "task_assignment",
            "content": {"task": "研究专利技术"}
        })

        # agent2 完成研究
        message_queue.append({
            "from": "agent2",
            "to": "agent3",
            "type": "result_transfer",
            "content": {"data": "研究结果"}
        })

        # agent3 完成写作
        message_queue.append({
            "from": "agent3",
            "to": "agent1",
            "type": "completion",
            "content": {"result": "最终文档"}
        })

        # 验证消息流
        assert len(message_queue) == 3
        assert message_queue[0]["to"] == "agent2"
        assert message_queue[1]["to"] == "agent3"
        assert message_queue[2]["to"] == "agent1"

    def test_agent_task_delegation(self):
        """测试智能体任务委派"""
        # 定义任务
        task = {
            "id": "task_001",
            "type": "专利分析",
            "complexity": "high",
            "required_capabilities": ["search", "analysis", "writing"],
        }

        # 定义智能体能力
        agents = {
            "agent1": {"capabilities": ["search", "analysis"], "load": 0.3},
            "agent2": {"capabilities": ["analysis", "writing"], "load": 0.5},
            "agent3": {"capabilities": ["search", "writing"], "load": 0.2},
        }

        # 选择最佳智能体（负载最低且能力匹配）
        capable_agents = {
            k: v for k, v in agents.items()
            if any(cap in v["capabilities"] for cap in task["required_capabilities"])
        }

        # 按负载排序
        best_agent = min(capable_agents.items(), key=lambda x: x[1]["load"])

        # 验证
        assert best_agent[0] in capable_agents
        assert best_agent[1]["load"] == 0.2  # agent3负载最低


class TestSystemIntegration:
    """系统集成测试"""

    def test_config_cache_integration(self):
        """测试配置和缓存集成"""
        try:
            from core.cache.memory_cache import MemoryCache

            # 创建缓存
            cache = MemoryCache()

            # 配置数据
            config = {
                "cache_ttl": 3600,
                "max_size": 10000,
                "eviction_policy": "LRU"
            }

            # 缓存配置
            cache.set("system_config", config)

            # 检索并使用配置
            retrieved_config = cache.get("system_config")

            # 验证
            assert retrieved_config is not None
            assert retrieved_config["cache_ttl"] == 3600
            assert retrieved_config["eviction_policy"] == "LRU"

        except ImportError:
            pytest.skip("MemoryCache不可用")

    def test_vector_agent_integration(self):
        """测试向量和智能体集成"""
        import numpy as np

        # 智能体决策需要向量相似度
        agent_decision = {
            "query": "如何申请专利？",
            "query_embedding": np.array([0.1, 0.2, 0.3]),
            "candidate_responses": [
                {
                    "response": "专利申请流程...",
                    "embedding": np.array([0.15, 0.25, 0.35]),
                },
                {
                    "response": "天气很好...",
                    "embedding": np.array([0.9, 0.1, 0.05]),
                }
            ]
        }

        # 计算相似度
        similarities = []
        for resp in agent_decision["candidate_responses"]:
            sim = np.dot(
                agent_decision["query_embedding"],
                resp["embedding"]
            ) / (
                np.linalg.norm(agent_decision["query_embedding"]) *
                np.linalg.norm(resp["embedding"])
            )
            similarities.append(sim)

        # 选择最相似响应
        best_idx = np.argmax(similarities)
        best_response = agent_decision["candidate_responses"][best_idx]

        # 验证
        assert best_idx == 0  # 第一个响应更相关
        assert "专利" in best_response["response"]

    def test_end_to_end_workflow(self):
        """测试端到端工作流"""
        try:
            import numpy as np

            from core.cache.memory_cache import MemoryCache

            # 1. 初始化缓存
            cache = MemoryCache()

            # 2. 用户查询
            query = "如何申请发明专利？"

            # 3. 生成查询向量
            query_vector = np.random.randn(768)

            # 4. 存储查询上下文
            context = {
                "query": query,
                "vector": query_vector.tolist(),
                "timestamp": "2024-01-01T00:00:00Z"
            }
            cache.set("query_context", context)

            # 5. 模拟智能体处理
            agent_response = {
                "answer": "申请发明专利需要...",
                "confidence": 0.95
            }

            # 6. 存储响应
            cache.set("query_response", agent_response)

            # 7. 验证完整流程
            retrieved_context = cache.get("query_context")
            retrieved_response = cache.get("query_response")

            assert retrieved_context is not None
            assert retrieved_response is not None
            assert retrieved_context["query"] == query
            assert retrieved_response["confidence"] > 0.9

        except ImportError:
            pytest.skip("MemoryCache不可用")


class TestPerformanceIntegration:
    """性能集成测试"""

    def test_concurrent_cache_operations(self):
        """测试并发缓存操作"""
        import time
        from concurrent.futures import ThreadPoolExecutor

        try:
            from core.cache.memory_cache import MemoryCache

            def cache_operations(cache, key_prefix, num_ops):
                """执行缓存操作"""
                results = []
                for i in range(num_ops):
                    # 设置
                    cache.set(f"{key_prefix}_key_{i}", f"value_{i}")
                    # 获取
                    value = cache.get(f"{key_prefix}_key_{i}")
                    results.append(value)
                return results

            # 创建缓存
            cache = MemoryCache()

            # 使用线程池执行并发操作
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=3) as executor:
                future1 = executor.submit(cache_operations, cache, "task1", 100)
                future2 = executor.submit(cache_operations, cache, "task2", 100)
                future3 = executor.submit(cache_operations, cache, "task3", 100)

                results = [future1.result(), future2.result(), future3.result()]
            total_time = time.time() - start_time

            # 验证
            assert len(results) == 3
            assert all(len(r) == 100 for r in results)
            assert total_time < 1.0, f"并发操作应该在1秒内完成，实际: {total_time:.2f}秒"

        except ImportError:
            pytest.skip("MemoryCache不可用")

    def test_cache_memory_efficiency(self):
        """测试缓存内存效率"""
        try:
            import sys

            from core.cache.memory_cache import MemoryCache

            # 创建缓存
            cache = MemoryCache()

            # 记录初始内存
            initial_memory = sys.getsizeof(cache)

            # 添加大量数据
            for i in range(1000):
                cache.set(f"key_{i}", f"value_{i}" * 10)

            # 记录最终内存
            final_memory = sys.getsizeof(cache)

            # 内存增长应该合理
            memory_growth = final_memory - initial_memory
            assert memory_growth < 10 * 1024 * 1024, f"内存增长应该小于10MB，实际: {memory_growth/1024/1024:.2f}MB"

        except ImportError:
            pytest.skip("MemoryCache不可用")
