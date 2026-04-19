#!/usr/bin/env python3
"""
统一工具注册表高级测试
Advanced Tests for Unified Tool Registry

包含并发测试、异常测试、边界测试等。

Author: Athena平台团队
Created: 2026-04-19
Version: v1.0.0
"""

import pytest
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.tools.unified_registry import (
    UnifiedToolRegistry,
    get_unified_registry,
    ToolHealthStatus,
)
from core.tools.base import ToolDefinition, ToolCategory


class TestConcurrency:
    """并发测试"""

    def test_concurrent_registration(self):
        """测试并发注册"""
        registry = get_unified_registry()
        errors = []
        registered_tools = []

        def register_tools(start_id):
            try:
                for i in range(100):
                    tool_id = f"concurrent_reg_{start_id + i}"
                    tool = ToolDefinition(
                        tool_id=tool_id,
                        name=f"并发注册工具{start_id + i}",
                        description="并发测试",
                        category=ToolCategory.PATENT_SEARCH,
                    )
                    registry.register(tool)
                    registered_tools.append(tool_id)
            except Exception as e:
                errors.append((start_id, e))

        # 启动10个线程，每个注册100个工具
        threads = []
        for i in range(10):
            t = threading.Thread(target=register_tools, args=(i * 100,))
            threads.append(t)
            t.start()

        # 等待所有线程完成
        for t in threads:
            t.join()

        # 验证无错误
        assert len(errors) == 0, f"注册过程中发生错误: {errors}"

        # 验证工具数量
        stats = registry.get_statistics()
        assert stats["total_tools"] >= 1000

    def test_concurrent_query(self):
        """测试并发查询"""
        registry = get_unified_registry()

        # 预先注册100个工具
        for i in range(100):
            tool = ToolDefinition(
                tool_id=f"concurrent_query_{i}",
                name=f"并发查询工具{i}",
                description="并发查询测试",
                category=ToolCategory.PATENT_SEARCH,
            )
            registry.register(tool)

        errors = []
        query_count = 0

        def query_worker():
            nonlocal query_count
            try:
                for i in range(1000):
                    tool_id = f"concurrent_query_{i % 100}"
                    tool = registry.get(tool_id)
                    if tool is None:
                        errors.append(f"工具未找到: {tool_id}")
                    query_count += 1
            except Exception as e:
                errors.append(str(e))

        # 启动10个线程，每个查询1000次
        threads = []
        for _ in range(10):
            t = threading.Thread(target=query_worker)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # 验证无错误
        assert len(errors) == 0, f"查询过程中发生错误: {errors}"
        assert query_count == 10000  # 10个线程 * 1000次查询

    def test_concurrent_health_status_updates(self):
        """测试并发健康状态更新"""
        registry = get_unified_registry()

        # 注册工具
        tool = ToolDefinition(
            tool_id="health_concurrent",
            name="并发健康测试",
            description="并发健康测试",
            category=ToolCategory.PATENT_SEARCH,
        )
        registry.register(tool)

        errors = []

        def update_health_status():
            try:
                for i in range(100):
                    if i % 2 == 0:
                        registry.mark_healthy("health_concurrent")
                    else:
                        registry.mark_unhealthy("health_concurrent", f"测试错误{i}")
            except Exception as e:
                errors.append(str(e))

        # 启动10个线程并发更新
        threads = []
        for _ in range(10):
            t = threading.Thread(target=update_health_status)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # 验证无错误
        assert len(errors) == 0, f"健康状态更新过程中发生错误: {errors}"

        # 验证最终状态
        status = registry.get_health_status("health_concurrent")
        assert status in [
            ToolHealthStatus.HEALTHY,
            ToolHealthStatus.UNHEALTHY,
        ]


class TestExceptionHandling:
    """异常处理测试"""

    def test_empty_tool_id(self):
        """测试空工具ID"""
        registry = get_unified_registry()

        with pytest.raises((ValueError, TypeError)):
            registry.register(
                ToolDefinition(
                    tool_id="",
                    name="空ID工具",
                    description="测试空ID",
                    category=ToolCategory.PATENT_SEARCH,
                )
            )

    def test_none_tool_id(self):
        """测试None工具ID"""
        registry = get_unified_registry()

        with pytest.raises((ValueError, TypeError)):
            registry.register(
                ToolDefinition(
                    tool_id=None,  # type: ignore
                    name="None ID工具",
                    description="测试None ID",
                    category=ToolCategory.PATENT_SEARCH,
                )
            )

    def test_get_nonexistent_tool(self):
        """测试获取不存在的工具"""
        registry = get_unified_registry()

        tool = registry.get("nonexistent_tool")
        assert tool is None

    def test_require_nonexistent_tool(self):
        """测试require不存在的工具"""
        registry = get_unified_registry()

        with pytest.raises(ValueError):
            registry.require("nonexistent_tool")

    def test_import_failure(self):
        """测试导入失败处理"""
        registry = get_unified_registry()

        # 注册不存在的模块
        success = registry.register_lazy(
            tool_id="bad_import_tool",
            import_path="nonexistent.module.path",
            function_name="nonexistent_function",
            metadata={},
        )

        # 注册应该成功（懒加载）
        assert success is True

        # 尝试加载应该失败
        with pytest.raises((ModuleNotFoundError, ImportError)):
            registry.get("bad_import_tool")


class TestBoundaryConditions:
    """边界条件测试"""

    def test_large_scale_registration(self):
        """测试大规模注册"""
        registry = get_unified_registry()

        # 注册10000个工具
        count = 10000
        start_time = time.perf_counter()

        for i in range(count):
            tool = ToolDefinition(
                tool_id=f"large_scale_{i}",
                name=f"大规模工具{i}",
                description="大规模测试",
                category=ToolCategory.PATENT_SEARCH,
            )
            registry.register(tool)

        end_time = time.perf_counter()
        total_time = end_time - start_time

        # 验证工具数量
        stats = registry.get_statistics()
        assert stats["total_tools"] >= count

        # 验证性能（应该在10秒内完成）
        assert total_time < 10.0, f"注册{count}个工具耗时{total_time:.2f}秒，超过10秒"

        print(f"✅ 注册{count}个工具耗时{total_time:.2f}秒")

    def test_long_tool_name(self):
        """测试长工具名"""
        registry = get_unified_registry()

        long_name = "a" * 1000  # 1000个字符
        tool = ToolDefinition(
            tool_id=long_name,
            name=long_name,
            description="长名称测试",
            category=ToolCategory.PATENT_SEARCH,
        )

        registry.register(tool)

        # 验证可以获取
        retrieved = registry.get(long_name)
        assert retrieved is not None
        assert retrieved.name == long_name

    def test_special_characters_in_tool_id(self):
        """测试工具ID中的特殊字符"""
        registry = get_unified_registry()

        special_ids = [
            "tool-with-dashes",
            "tool_with_underscores",
            "tool.with.dots",
            "tool:with:colons",
            "tool/with/slashes",
        ]

        for tool_id in special_ids:
            tool = ToolDefinition(
                tool_id=tool_id,
                name=f"特殊字符工具{tool_id}",
                description="特殊字符测试",
                category=ToolCategory.PATENT_SEARCH,
            )
            registry.register(tool)

            # 验证可以获取
            retrieved = registry.get(tool_id)
            assert retrieved is not None
            assert retrieved.tool_id == tool_id

    def test_unicode_tool_name(self):
        """测试Unicode工具名"""
        registry = get_unified_registry()

        unicode_name = "工具名称测试-🚀-专利搜索"
        tool = ToolDefinition(
            tool_id=unicode_name,
            name=unicode_name,
            description="Unicode测试",
            category=ToolCategory.PATENT_SEARCH,
        )

        registry.register(tool)

        # 验证可以获取
        retrieved = registry.get(unicode_name)
        assert retrieved is not None
        assert retrieved.name == unicode_name


class TestLazyLoading:
    """懒加载高级测试"""

    def test_lazy_load_caching(self):
        """测试懒加载缓存"""
        registry = get_unified_registry()

        # 注册懒加载工具
        registry.register_lazy(
            tool_id="cache_test_tool",
            import_path="os.path",
            function_name="join",
            metadata={},
        )

        # 第一次加载
        tool1 = registry.get("cache_test_tool")
        assert tool1 is not None

        # 第二次加载（应该使用缓存）
        tool2 = registry.get("cache_test_tool")
        assert tool2 is not None

        # 验证是同一个对象（缓存）
        assert tool1 is tool2

    def test_lazy_load_error_handling(self):
        """测试懒加载错误处理"""
        registry = get_unified_registry()

        # 注册错误的懒加载工具
        registry.register_lazy(
            tool_id="error_tool",
            import_path="os.path",
            function_name="nonexistent_function",
            metadata={},
        )

        # 尝试加载应该失败
        with pytest.raises(AttributeError):
            registry.get("error_tool")

        # 验证健康状态
        status = registry.get_health_status("error_tool")
        assert status == ToolHealthStatus.UNHEALTHY


class TestPerformance:
    """性能测试"""

    def test_registration_speed(self):
        """测试注册速度"""
        registry = get_unified_registry()

        count = 1000
        start_time = time.perf_counter()

        for i in range(count):
            tool = ToolDefinition(
                tool_id=f"speed_test_{i}",
                name=f"速度测试{i}",
                description="速度测试",
                category=ToolCategory.PATENT_SEARCH,
            )
            registry.register(tool)

        end_time = time.perf_counter()
        total_time = end_time - start_time
        avg_time = total_time / count

        # 验证性能（平均每次注册应该<1ms）
        assert avg_time < 0.001, f"平均注册时间{avg_time*1000:.2f}ms，超过1ms"

        print(f"✅ 注册{count}个工具，平均耗时{avg_time*1000:.4f}ms")

    def test_query_speed(self):
        """测试查询速度"""
        registry = get_unified_registry()

        # 预先注册1000个工具
        for i in range(1000):
            tool = ToolDefinition(
                tool_id=f"query_speed_{i}",
                name=f"查询速度{i}",
                description="查询速度测试",
                category=ToolCategory.PATENT_SEARCH,
            )
            registry.register(tool)

        # 测试查询速度
        count = 10000
        start_time = time.perf_counter()

        for i in range(count):
            tool_id = f"query_speed_{i % 1000}"
            tool = registry.get(tool_id)
            assert tool is not None

        end_time = time.perf_counter()
        total_time = end_time - start_time
        avg_time = total_time / count

        # 验证性能（平均每次查询应该<0.1ms）
        assert avg_time < 0.0001, f"平均查询时间{avg_time*1000:.2f}ms，超过0.1ms"

        print(f"✅ 查询{count}次，平均耗时{avg_time*1000:.4f}ms")


class TestHealthStatus:
    """健康状态高级测试"""

    def test_health_status_persistence(self):
        """测试健康状态持久化"""
        registry = get_unified_registry()

        # 注册工具
        tool = ToolDefinition(
            tool_id="health_persistence",
            name="健康状态持久化",
            description="测试健康状态持久化",
            category=ToolCategory.PATENT_SEARCH,
        )
        registry.register(tool)

        # 标记为不健康
        registry.mark_unhealthy("health_persistence", "测试原因1")

        # 多次标记
        for i in range(10):
            registry.mark_unhealthy("health_persistence", f"测试原因{i+1}")

        # 验证状态
        status = registry.get_health_status("health_persistence")
        assert status == ToolHealthStatus.UNHEALTHY

        # 恢复健康
        registry.mark_healthy("health_persistence")

        # 验证状态
        status = registry.get_health_status("health_persistence")
        assert status == ToolHealthStatus.HEALTHY

    def test_health_status_report(self):
        """测试健康状态报告"""
        registry = get_unified_registry()

        # 注册多个工具
        for i in range(10):
            tool = ToolDefinition(
                tool_id=f"health_report_{i}",
                name=f"健康报告{i}",
                description="健康报告测试",
                category=ToolCategory.PATENT_SEARCH,
            )
            registry.register(tool)

        # 标记不同状态
        registry.mark_healthy("health_report_0")
        registry.mark_unhealthy("health_report_1", "错误1")
        registry.mark_unhealthy("health_report_2", "错误2")

        # 获取健康报告
        report = registry.get_health_report()

        # 验证报告
        assert "healthy" in report
        assert "unhealthy" in report
        assert "unknown" in report

        # 验证数量
        assert len(report["healthy"]) >= 1
        assert len(report["unhealthy"]) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
