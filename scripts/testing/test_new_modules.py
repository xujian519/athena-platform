#!/usr/bin/env python3
"""
测试新创建的模块
Test newly created modules
"""

import sys
import os
import time

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_cache_module():
    """测试core/cache模块"""
    print("=" * 60)
    print("测试 core/cache 模块")
    print("=" * 60)

    # 1. 测试模块导入
    print("\n1. 测试模块导入...")
    try:
        from core.cache import MemoryCache, RedisCache, CacheManager
        print("   ✓ 所有类导入成功")
    except ImportError as e:
        print(f"   ✗ 导入失败: {e}")
        return False

    # 2. 测试MemoryCache
    print("\n2. 测试 MemoryCache...")
    try:
        cache = MemoryCache(default_ttl=300)

        # 基本操作
        cache.set('test_key', 'test_value')
        value = cache.get('test_key')
        assert value == 'test_value', '值不匹配'
        print("   ✓ 基本set/get操作正常")

        # exists方法
        assert cache.exists('test_key') == True
        assert cache.exists('nonexistent') == False
        print("   ✓ exists方法正常")

        # TTL测试
        cache.set('ttl_key', 'ttl_value', ttl=1)
        time.sleep(1.1)
        expired = cache.get('ttl_key')
        assert expired is None, 'TTL过期失败'
        print("   ✓ TTL过期机制正常")

        # 删除操作
        cache.set('del_key', 'del_value')
        assert cache.exists('del_key') == True
        cache.delete('del_key')
        assert cache.exists('del_key') == False
        print("   ✓ 删除操作正常")

        # 批量操作
        test_data = {'k1': 'v1', 'k2': 'v2', 'k3': 'v3'}
        cache.set_many(test_data)
        values = cache.get_many(['k1', 'k2', 'k3', 'k_nonexist'])
        assert values['k1'] == 'v1', '批量获取失败'
        assert len(values) == 3, f'批量获取数量不对，期望3个存在的键，实际{len(values)}个'
        assert 'k_nonexist' not in values, '不存在的键不应该出现在结果中'
        print("   ✓ 批量操作正常")

        # clear操作
        cache.clear()
        assert cache.exists('k1') == False
        print("   ✓ clear操作正常")

    except Exception as e:
        print(f"   ✗ MemoryCache测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 3. 测试CacheManager
    print("\n3. 测试 CacheManager...")
    try:
        manager = CacheManager(use_redis=False, default_ttl=300)

        # 基本操作
        manager.set('mgr_key', 'mgr_value')
        value = manager.get('mgr_key')
        assert value == 'mgr_value', 'CacheManager获取失败'
        print("   ✓ CacheManager基本操作正常")

        # L1缓存测试
        assert manager._l1_cache.exists('mgr_key'), 'L1缓存未设置'
        print("   ✓ L1缓存正常")

        # 批量操作
        manager.set_many({'m1': 'v1', 'm2': 'v2'})
        values = manager.get_many(['m1', 'm2'])
        assert values['m1'] == 'v1', '批量获取失败'
        print("   ✓ 批量操作正常")

        # 统计信息
        stats = manager.stats()  # stats是方法，需要调用
        assert 'l1_size' in stats, '统计信息缺失'
        print(f"   ✓ 统计功能正常: L1大小={stats['l1_size']}")

        # 清理
        manager.cleanup()
        print("   ✓ 清理功能正常")

    except Exception as e:
        print(f"   ✗ CacheManager测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 4. 测试RedisCache (可选)
    print("\n4. 测试 RedisCache (可选依赖)...")
    try:
        from core.cache import RedisCache
        redis_cache = RedisCache.__new__(RedisCache)
        # 不初始化Redis连接，只测试类存在
        print("   ✓ RedisCache类可用 (需要Redis服务才能完全测试)")
    except Exception as e:
        print(f"   ⚠ RedisCache不可用 (预期): {e}")

    print("\n✓ core/cache 模块所有测试通过")
    return True


def test_agents_module():
    """测试core/agents模块"""
    print("\n" + "=" * 60)
    print("测试 core/agents 模块")
    print("=" * 60)

    # 1. 测试模块导入
    print("\n1. 测试模块导入...")
    try:
        from core.agents import BaseAgent, AgentUtils, AgentResponse
        print("   ✓ 所有类导入成功")
    except ImportError as e:
        print(f"   ✗ 导入失败: {e}")
        return False

    # 2. 测试BaseAgent抽象类
    print("\n2. 测试 BaseAgent...")
    try:
        from abc import ABC

        # 创建一个具体的Agent实现
        class TestAgent(BaseAgent):
            def process(self, input_text: str, **kwargs) -> str:
                return f"处理: {input_text}"

            async def health_check(self) -> dict:
                return {"status": "healthy"}

            async def initialize(self) -> None:
                pass

            @property
            def agent_name(self) -> str:
                return self.name

            async def shutdown(self) -> None:
                pass

        # 测试初始化
        agent = TestAgent(
            name="test_agent",
            role="assistant",
            model="gpt-4",
            temperature=0.7,
            max_tokens=2000
        )
        print("   ✓ Agent初始化正常")

        # 测试process方法
        response = agent.process("测试输入")
        assert "测试输入" in response, "process方法失败"
        print("   ✓ process方法正常")

        # 测试对话历史
        agent.add_to_history("user", "你好")
        agent.add_to_history("assistant", "您好！")
        history = agent.get_history()
        assert len(history) == 2, "历史记录不对"
        print("   ✓ 对话历史管理正常")

        # 测试清空历史
        agent.clear_history()
        assert len(agent.get_history()) == 0, "清空失败"
        print("   ✓ 清空历史正常")

        # 测试记忆系统
        agent.remember("key1", "value1")
        value = agent.recall("key1")
        assert value == "value1", "记忆存储失败"
        print("   ✓ 记忆系统正常")

        # 测试遗忘
        result = agent.forget("key1")
        assert result == True, "遗忘失败"
        assert agent.recall("key1") is None, "应该被遗忘"
        print("   ✓ 遗忘功能正常")

        # 测试能力系统
        agent.add_capability("search")
        agent.add_capability("analysis")
        assert agent.has_capability("search"), "能力检查失败"
        capabilities = agent.get_capabilities()
        assert len(capabilities) == 2, "能力数量不对"
        print("   ✓ 能力系统正常")

        # 测试验证方法
        assert agent.validate_input("test") == True, "输入验证失败"
        assert agent.validate_input("") == False, "空输入应该无效"
        assert agent.validate_config() == True, "配置验证失败"
        print("   ✓ 验证方法正常")

        # 测试get_info
        info = agent.get_info()
        assert info['name'] == "test_agent", "信息不对"
        assert 'capabilities' in info, "缺少capabilities"
        print("   ✓ get_info方法正常")

    except Exception as e:
        print(f"   ✗ BaseAgent测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 3. 测试AgentUtils工具类
    print("\n3. 测试 AgentUtils...")
    try:
        # 测试format_message
        msg = AgentUtils.format_message("user", "hello")
        assert msg['role'] == "user", "角色不对"
        assert msg['content'] == "hello", "内容不对"
        print("   ✓ format_message正常")

        # 测试truncate_text
        long_text = "a" * 2000
        truncated = AgentUtils.truncate_text(long_text, 100)
        assert len(truncated) <= 103, "截断失败"  # 100 + "..."
        print("   ✓ truncate_text正常")

        # 测试extract_code
        text_with_code = "```python\nprint('hello')\n```"
        codes = AgentUtils.extract_code(text_with_code)
        assert len(codes) == 1, "代码提取失败"
        assert "print('hello')" in codes[0], "代码内容不对"
        print("   ✓ extract_code正常")

        # 测试sanitize_input
        dirty = "test\x00\x1f string"
        clean = AgentUtils.sanitize_input(dirty)
        assert "\x00" not in clean, "控制字符未清理"
        print("   ✓ sanitize_input正常")

    except Exception as e:
        print(f"   ✗ AgentUtils测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 4. 测试AgentResponse类
    print("\n4. 测试 AgentResponse...")
    try:
        # 测试成功响应
        success_resp = AgentResponse.success_response("成功", confidence=0.95)
        assert success_resp.success == True, "应该是成功"
        assert success_resp.content == "成功", "内容不对"
        assert success_resp.metadata['confidence'] == 0.95, "元数据不对"
        print("   ✓ 成功响应创建正常")

        # 测试错误响应
        error_resp = AgentResponse.error("出错了")
        assert error_resp.success == False, "应该是失败"
        assert "出错了" in error_resp.content, "错误信息不对"
        assert error_resp.metadata.get('error') == True, "错误标志不对"
        print("   ✓ 错误响应创建正常")

        # 测试to_dict
        resp_dict = success_resp.to_dict()
        assert 'content' in resp_dict, "缺少content"
        assert 'success' in resp_dict, "缺少success"
        print("   ✓ to_dict方法正常")

    except Exception as e:
        print(f"   ✗ AgentResponse测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n✓ core/agents 模块所有测试通过")
    return True


def test_integration_fixes():
    """测试修复的集成测试"""
    print("\n" + "=" * 60)
    print("测试修复的集成测试")
    print("=" * 60)

    print("\n1. 测试并发缓存操作...")
    try:
        from core.cache import MemoryCache
        from concurrent.futures import ThreadPoolExecutor
        import time

        def cache_operations(cache, key_prefix, num_ops):
            """执行缓存操作"""
            results = []
            for i in range(num_ops):
                cache.set(f"{key_prefix}_key_{i}", f"value_{i}")
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
        assert len(results) == 3, "结果数量不对"
        assert all(len(r) == 100 for r in results), "每个任务应该有100个结果"
        assert total_time < 1.0, f"并发操作应该在1秒内完成，实际: {total_time:.2f}秒"

        print(f"   ✓ 并发操作测试通过 (耗时: {total_time:.3f}秒)")

    except Exception as e:
        print(f"   ✗ 并发操作测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n✓ 集成测试修复验证通过")
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("开始测试新修改的代码")
    print("=" * 60)

    results = {
        "core/cache模块": False,
        "core/agents模块": False,
        "集成测试修复": False,
    }

    # 测试各个模块
    results["core/cache模块"] = test_cache_module()
    results["core/agents模块"] = test_agents_module()
    results["集成测试修复"] = test_integration_fixes()

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    all_passed = True
    for module, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{module:20s} {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n✓✓✓ 所有测试通过！新代码可以安全集成 ✓✓✓\n")
        return 0
    else:
        print("\n✗✗✗ 部分测试失败，需要修复后再集成 ✗✗✗\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
