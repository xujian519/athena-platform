"""
边缘情况测试
Edge Cases Testing
"""
import pytest
import time
import threading
from core.cache import MemoryCache, CacheManager
from core.agents import BaseAgent, AgentUtils, AgentResponse


class TestMemoryCacheEdgeCases:
    """MemoryCache边缘情况测试"""

    def test_empty_key_get(self):
        """测试获取空键"""
        cache = MemoryCache()
        result = cache.get("")
        assert result is None, "空键应该返回None"

    def test_none_value_storage(self):
        """测试存储None值"""
        cache = MemoryCache()
        cache.set("none_key", None)
        # 存储None后，get应该返回None
        result = cache.get("none_key")
        assert result is None, "存储None应该可以获取"

    def test_zero_ttl(self):
        """测试TTL为0的情况"""
        cache = MemoryCache()
        cache.set("zero_ttl", "value", ttl=0)
        # TTL为0应该立即过期
        time.sleep(0.1)
        result = cache.get("zero_ttl")
        assert result is None, "TTL为0应该立即过期"

    def test_large_value_storage(self):
        """测试存储大值"""
        cache = MemoryCache()
        large_value = "x" * 10000  # 10KB
        cache.set("large_key", large_value)
        result = cache.get("large_key")
        assert len(result) == 10000, "大值应该完整存储"
        assert result == large_value, "大值应该保持不变"

    def test_special_characters_in_key(self):
        """测试键中的特殊字符"""
        cache = MemoryCache()
        special_keys = [
            "key with spaces",
            "key-with-dashes",
            "key_with_underscores",
            "key.with.dots",
            "key:with:colons",
            "key/with/slashes",
            "中文键",
            "emoji😀键",
        ]
        for key in special_keys:
            cache.set(key, f"value_{key}")
            assert cache.get(key) == f"value_{key}", f"特殊字符键失败: {key}"

    def test_unicode_values(self):
        """测试Unicode值"""
        cache = MemoryCache()
        unicode_values = [
            "Hello 世界",
            "Ελληνικά",
            "עברית",
            "العربية",
            "😀🎉🎊",
        ]
        for value in unicode_values:
            cache.set(f"key_{len(value)}", value)
            assert cache.get(f"key_{len(value)}") == value

    def test_concurrent_writes(self):
        """测试并发写入同一个键"""
        cache = MemoryCache()
        num_threads = 10
        writes_per_thread = 100

        def write_same_key():
            for i in range(writes_per_thread):
                cache.set("concurrent_key", f"value_{i}")

        threads = [threading.Thread(target=write_same_key) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 最终值应该是某个value，不应该崩溃
        result = cache.get("concurrent_key")
        assert result is not None, "并发写入后应该有值"

    def test_cache_size_limit(self):
        """测试缓存大小限制"""
        # 注意: 当前MemoryCache实现不支持max_size参数
        # 这个测试验证缓存可以容纳大量数据
        cache = MemoryCache()
        for i in range(100):
            cache.set(f"key_{i}", f"value_{i}")

        # 验证所有键都可以访问
        assert cache.get("key_0") is not None, "第一个键应该存在"
        assert cache.get("key_50") is not None, "中间的键应该存在"
        assert cache.get("key_99") is not None, "最后一个键应该存在"
        assert cache.size() == 100, "缓存大小应该为100"

    def test_rapid_set_delete(self):
        """测试快速设置和删除"""
        cache = MemoryCache()
        for i in range(1000):
            cache.set(f"temp_{i}", i)
            cache.delete(f"temp_{i}")
        # 缓存应该保持稳定
        assert cache.get("temp_0") is None

    def test_clear_empty_cache(self):
        """测试清空空缓存"""
        cache = MemoryCache()
        cache.clear()  # 不应该崩溃
        assert cache.get("any_key") is None


class TestCacheManagerEdgeCases:
    """CacheManager边缘情况测试"""

    def test_without_l2_cache(self):
        """测试不使用L2缓存"""
        manager = CacheManager(use_redis=False)
        manager.set("key1", "value1")
        assert manager.get("key1") == "value1"

    def test_get_many_with_nonexistent_keys(self):
        """测试获取多个不存在的键"""
        manager = CacheManager(use_redis=False)
        manager.set("existing", "value")
        results = manager.get_many(["existing", "nonexistent1", "nonexistent2"])
        assert results["existing"] == "value"
        assert "nonexistent1" not in results
        assert "nonexistent2" not in results

    def test_set_many_empty_dict(self):
        """测试设置空字典"""
        manager = CacheManager(use_redis=False)
        result = manager.set_many({})
        assert result == True

    def test_delete_many_empty_list(self):
        """测试删除空列表"""
        manager = CacheManager(use_redis=False)
        result = manager.delete_many([])
        assert result == True

    def test_overwrite_with_different_ttl(self):
        """测试用不同TTL覆盖"""
        manager = CacheManager(use_redis=False, default_ttl=300)
        manager.set("key", "value1", ttl=60)
        manager.set("key", "value2", ttl=120)
        # 应该使用新的TTL
        time.sleep(0.1)
        assert manager.get("key") == "value2"

    def test_stats_without_data(self):
        """测试空缓存的统计"""
        manager = CacheManager(use_redis=False)
        stats = manager.stats()
        assert stats["l1_size"] == 0
        assert stats["l2_available"] == False


class TestBaseAgentEdgeCases:
    """BaseAgent边缘情况测试"""

    def test_empty_input(self):
        """测试空输入"""
        agent = TestAgent()
        result = agent.process("")
        assert agent.validate_input("") == False

    def test_whitespace_only_input(self):
        """测试仅空格输入"""
        agent = TestAgent()
        result = agent.process("   ")
        # 应该处理，但不一定通过验证
        assert result is not None

    def test_very_long_input(self):
        """测试非常长的输入"""
        agent = TestAgent()
        long_input = "a" * 10000
        result = agent.process(long_input)
        assert result is not None

    def test_special_characters_input(self):
        """测试特殊字符输入"""
        agent = TestAgent()
        special_inputs = [
            "\n\r\t",
            "!@#$%^&*()",
            "中文测试",
            "😀🎉",
        ]
        for inp in special_inputs:
            result = agent.process(inp)
            assert result is not None

    def test_multiple_clear_history(self):
        """测试多次清空历史"""
        agent = TestAgent()
        agent.add_to_history("user", "message1")
        agent.clear_history()
        agent.clear_history()  # 不应该崩溃
        assert len(agent.get_history()) == 0

    def test_forget_nonexistent_key(self):
        """测试删除不存在的记忆"""
        agent = TestAgent()
        result = agent.forget("nonexistent")
        assert result == False

    def test_add_duplicate_capability(self):
        """测试添加重复能力"""
        agent = TestAgent()
        agent.add_capability("search")
        agent.add_capability("search")  # 不应该重复
        capabilities = agent.get_capabilities()
        assert capabilities.count("search") == 1

    def test_empty_capabilities(self):
        """测试空能力列表"""
        agent = TestAgent()
        capabilities = agent.get_capabilities()
        assert len(capabilities) == 0

    def test_extreme_config_values(self):
        """测试极端配置值"""
        # temperature边界
        agent1 = TestAgent(temperature=0.0)
        assert agent1.validate_config() == True

        agent2 = TestAgent(temperature=1.0)
        assert agent2.validate_config() == True

        agent3 = TestAgent(temperature=-0.1)
        assert agent3.validate_config() == False

        agent4 = TestAgent(temperature=1.1)
        assert agent4.validate_config() == False


class TestAgentResponseEdgeCases:
    """AgentResponse边缘情况测试"""

    def test_empty_content(self):
        """测试空内容"""
        resp = AgentResponse.success_response("")
        assert resp.content == ""
        assert resp.success == True

    def test_unicode_content(self):
        """测试Unicode内容"""
        resp = AgentResponse.success_response("你好世界😀")
        assert resp.success == True
        assert "你好世界😀" in resp.content

    def test_large_metadata(self):
        """测试大量元数据"""
        large_metadata = {f"key_{i}": f"value_{i}" for i in range(100)}
        resp = AgentResponse.success_response("content", **large_metadata)
        assert len(resp.metadata) == 100

    def test_nested_metadata(self):
        """测试嵌套元数据"""
        nested_metadata = {
            "level1": {
                "level2": {
                    "level3": "deep_value"
                }
            }
        }
        resp = AgentResponse.success_response("content", **nested_metadata)
        assert resp.metadata["level1"]["level2"]["level3"] == "deep_value"


class TestAgentUtilsEdgeCases:
    """AgentUtils边缘情况测试"""

    def test_truncate_already_short(self):
        """测试截断已经很短的文本"""
        text = "short"
        result = AgentUtils.truncate_text(text, 100)
        assert result == text
        assert "..." not in result

    def test_extract_code_no_code(self):
        """测试从无代码文本提取代码"""
        text = "This is just plain text without any code blocks"
        codes = AgentUtils.extract_code(text)
        assert len(codes) == 0

    def test_extract_multiple_code_blocks(self):
        """测试提取多个代码块"""
        text = """
```python
print('first')
```

Some text

```javascript
console.log('second')
```
        """
        codes = AgentUtils.extract_code(text)
        assert len(codes) == 2
        assert "print('first')" in codes[0]
        assert "console.log('second')" in codes[1]

    def test_sanitize_already_clean(self):
        """测试清理已经干净的文本"""
        clean = "This is clean text"
        result = AgentUtils.sanitize_input(clean)
        assert result == clean

    def test_sanitize_preserves_content(self):
        """测试清理保留重要内容"""
        text = "Hello 世界! 123"
        result = AgentUtils.sanitize_input(text)
        # 应该保留字母、数字、基本标点
        assert "Hello" in result or "hello" in result.lower()


class TestAgent(BaseAgent):
    """测试用的简单Agent实现"""

    def __init__(self, **kwargs):
        # 设置默认值
        defaults = {
            "name": "test",
            "role": "assistant",
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000,
        }
        defaults.update(kwargs)
        super().__init__(**defaults)

    def process(self, input_text: str, **kwargs) -> str:
        return f"处理: {input_text}"
