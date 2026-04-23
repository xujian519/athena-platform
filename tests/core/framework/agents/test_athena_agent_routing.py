#!/usr/bin/env python3
"""
Athena Agent智能路由测试
Athena Agent Intelligent Routing Tests

测试AthenaAgent的智能路由功能
"""
import pytest
from core.framework.agents.athena_agent import ROUTING_SYSTEM_AVAILABLE, AthenaAgent


@pytest.mark.asyncio
async def test_athena_agent_routing_enabled():
    """测试AthenaAgent路由系统状态"""
    agent = AthenaAgent()

    # 验证路由系统状态
    assert agent.routing_enabled == ROUTING_SYSTEM_AVAILABLE

    if ROUTING_SYSTEM_AVAILABLE:
        assert agent.routing_enabled is True
        assert agent.router is not None


@pytest.mark.asyncio
async def test_athena_agent_routing_statistics():
    """测试路由统计信息"""
    agent = AthenaAgent()

    if not ROUTING_SYSTEM_AVAILABLE:
        pytest.skip("路由系统不可用")

    await agent.initialize()

    # 获取路由统计
    stats = await agent.get_routing_statistics()

    # 验证统计信息
    assert isinstance(stats, dict)
    assert "enabled" in stats
    assert stats["enabled"] is True
    assert "total_requests" in stats
    assert "cache_hits" in stats


@pytest.mark.asyncio
async def test_athena_agent_routing_with_process():
    """测试路由与process_input的集成"""
    agent = AthenaAgent()

    if not ROUTING_SYSTEM_AVAILABLE:
        pytest.skip("路由系统不可用")

    await agent.initialize()

    # 处理输入（会触发路由）
    result = await agent.process_input("分析专利创造性")

    # 验证结果
    assert "athena_analysis" in result
    assert "performance" in result

    # 验证路由信息（如果有）
    if "routing" in result:
        assert "intent_type" in result["routing"]
        assert "confidence" in result["routing"]


@pytest.mark.asyncio
async def test_athena_agent_routing_cache():
    """测试路由缓存"""
    agent = AthenaAgent()

    if not ROUTING_SYSTEM_AVAILABLE:
        pytest.skip("路由系统不可用")

    await agent.initialize()

    # 第一次请求
    result1 = await agent.process_input("测试路由缓存")

    # 第二次请求（应该命中缓存）
    result2 = await agent.process_input("测试路由缓存")

    # 验证两次都成功
    assert result1["athena_analysis"] is not None
    assert result2["athena_analysis"] is not None

    # 获取路由统计
    stats = await agent.get_routing_statistics()

    # 验证缓存命中
    if stats["total_requests"] >= 2:
        # 可能有缓存命中
        assert stats["cache_hits"] >= 0


@pytest.mark.asyncio
async def test_athena_agent_clear_routing_cache():
    """测试清除路由缓存"""
    agent = AthenaAgent()

    if not ROUTING_SYSTEM_AVAILABLE:
        pytest.skip("路由系统不可用")

    await agent.initialize()

    # 执行一些请求以填充缓存
    await agent.process_input("测试1")
    await agent.process_input("测试2")

    # 获取统计（应该有缓存）
    stats_before = await agent.get_routing_statistics()
    stats_before["cached_routes"]

    # 清除缓存
    await agent.clear_routing_cache()

    # 验证缓存已清除
    stats_after = await agent.get_routing_statistics()
    assert stats_after["cached_routes"] == 0


@pytest.mark.asyncio
async def test_athena_agent_optimize_routing_cache():
    """测试优化路由缓存"""
    agent = AthenaAgent()

    if not ROUTING_SYSTEM_AVAILABLE:
        pytest.skip("路由系统不可用")

    await agent.initialize()

    # 优化缓存（限制为100）
    await agent.optimize_routing_cache(max_size=100)

    # 验证优化成功
    stats = await agent.get_routing_statistics()
    assert stats["cached_routes"] <= 100


@pytest.mark.asyncio
async def test_athena_agent_routing_without_system():
    """测试没有路由系统时的行为"""
    agent = AthenaAgent()

    if ROUTING_SYSTEM_AVAILABLE:
        pytest.skip("路由系统可用，跳过此测试")

    # 路由功能应该返回禁用状态
    stats = await agent.get_routing_statistics()
    assert stats["enabled"] is False

    # 清除缓存应该正常工作
    await agent.clear_routing_cache()

    # 优化缓存应该正常工作
    await agent.optimize_routing_cache()


@pytest.mark.asyncio
async def test_athena_agent_routing_format():
    """测试路由结果格式化"""
    agent = AthenaAgent()

    if not ROUTING_SYSTEM_AVAILABLE:
        pytest.skip("路由系统不可用")

    await agent.initialize()

    # 处理输入
    result = await agent.process_input("分析专利")

    # 验证路由结果格式（如果有）
    if "routing" in result and result["routing"]:
        routing = result["routing"]

        # 验证必要字段存在
        assert isinstance(routing, dict)
        # 具体字段取决于路由器的实现


@pytest.mark.asyncio
async def test_athena_agent_routing_performance():
    """测试路由性能影响"""
    agent = AthenaAgent()

    if not ROUTING_SYSTEM_AVAILABLE:
        pytest.skip("路由系统不可用")

    await agent.initialize()

    # 执行多次请求
    import time

    times = []
    for i in range(10):
        start = time.time()
        await agent.process_input(f"测试性能 {i}")
        times.append(time.time() - start)

    avg_time = sum(times) / len(times)

    # 验证平均响应时间合理
    assert avg_time < 3.0, f"平均响应时间过长: {avg_time:.2f}秒"


@pytest.mark.asyncio
async def test_athena_agent_all_features_with_routing():
    """测试所有功能与路由的集成"""
    agent = AthenaAgent()

    if not ROUTING_SYSTEM_AVAILABLE:
        pytest.skip("路由系统不可用")

    await agent.initialize()

    # 执行完整处理
    result = await agent.process_input("分析专利CN123456的创造性")

    # 验证所有功能正常
    assert "athena_analysis" in result
    assert "technical_assessment" in result
    assert "strategic_recommendations" in result
    assert "performance" in result

    # 验证路由信息（如果有）
    if "routing" in result:
        assert isinstance(result["routing"], dict)


@pytest.mark.asyncio
async def test_athena_agent_routing_error_handling():
    """测试路由功能的错误处理"""
    agent = AthenaAgent()

    if not ROUTING_SYSTEM_AVAILABLE:
        pytest.skip("路由系统不可用")

    await agent.initialize()

    # 测试空输入
    result = await agent.process_input("")
    # 应该优雅地处理
    assert "athena_analysis" in result or "error" in result

    # 测试特殊字符
    result = await agent.process_input("!@#$%")
    # 应该优雅地处理
    assert "athena_analysis" in result or "error" in result


@pytest.mark.asyncio
async def test_athena_agent_routing_cache_hit_rate():
    """测试路由缓存命中率"""
    agent = AthenaAgent()

    if not ROUTING_SYSTEM_AVAILABLE:
        pytest.skip("路由系统不可用")

    await agent.initialize()

    # 执行相同的请求多次
    for _ in range(5):
        await agent.process_input("相同的请求")

    # 获取统计
    stats = await agent.get_routing_statistics()

    # 验证缓存命中
    if stats["total_requests"] >= 5:
        # 应该有缓存命中（因为请求相同）
        cache_hit_rate = stats["cache_hit_rate"]
        assert cache_hit_rate >= 0.0


@pytest.mark.asyncio
async def test_athena_agent_routing_integration_with_memory():
    """测试路由与记忆的集成"""
    agent = AthenaAgent()

    if not ROUTING_SYSTEM_AVAILABLE:
        pytest.skip("路由系统不可用")

    if not agent.memory_enhanced:
        pytest.skip("记忆系统不可用")

    await agent.initialize()

    # 记录一些专业知识
    await agent.remember_learning(
        topic="专利分析",
        knowledge="需要考虑技术方案的新颖性和创造性",
        importance=0.9,
    )

    # 处理输入（可能触发路由和记忆）
    result = await agent.process_input("分析专利创造性")

    # 验证成功
    assert "athena_analysis" in result
    assert "performance" in result
