"""
扩展中间件测试脚本

测试缓存、验证、监控中间件的功能。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "api-gateway" / "src"))


async def test_cache_middleware():
    """测试缓存中间件"""
    print("\n" + "="*50)
    print("测试缓存中间件")
    print("="*50)

    try:
        from middleware.cache import CacheMiddleware, InMemoryCache

        # 创建缓存中间件
        cache = CacheMiddleware(
            default_ttl=60,
            cacheable_methods=["GET"],
            cache_rules=[
                {
                    "path_pattern": "^/api/v1/patents",
                    "ttl": 300,
                    "methods": ["GET"],
                }
            ]
        )
        print("✓ 缓存中间件创建成功")

        # 测试内存缓存
        mem_cache = InMemoryCache()
        await mem_cache.setex("test_key", 60, "test_value")
        value = await mem_cache.get("test_key")
        assert value == "test_value", "缓存值不匹配"
        print("✓ 内存缓存测试通过")

        # 获取统计信息
        stats = cache.get_stats()
        print(f"✓ 缓存统计: {stats}")

        return True

    except Exception as e:
        print(f"✗ 缓存中间件测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_validation_middleware():
    """测试验证中间件"""
    print("\n" + "="*50)
    print("测试验证中间件")
    print("="*50)

    try:
        from middleware.validation import ValidationMiddleware

        # 创建验证中间件
        validation = ValidationMiddleware(
            max_body_size=1024 * 1024,
            enable_sql_injection_check=True,
            enable_xss_check=True,
            enable_path_traversal_check=True,
        )
        print("✓ 验证中间件创建成功")

        # 测试 SQL 注入检测
        sql_patterns = ValidationMiddleware.SQL_INJECTION_PATTERNS
        assert len(sql_patterns) > 0, "SQL 注入模式为空"
        print(f"✓ SQL 注入模式数量: {len(sql_patterns)}")

        # 测试 XSS 模式
        xss_patterns = ValidationMiddleware.XSS_PATTERNS
        assert len(xss_patterns) > 0, "XSS 模式为空"
        print(f"✓ XSS 模式数量: {len(xss_patterns)}")

        # 测试路径遍历模式
        path_patterns = ValidationMiddleware.PATH_TRAVERSAL_PATTERNS
        assert len(path_patterns) > 0, "路径遍历模式为空"
        print(f"✓ 路径遍历模式数量: {len(path_patterns)}")

        # 获取统计信息
        stats = validation.get_stats()
        print(f"✓ 验证统计: {stats}")

        return True

    except Exception as e:
        print(f"✗ 验证中间件测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_monitoring_middleware():
    """测试监控中间件"""
    print("\n" + "="*50)
    print("测试监控中间件")
    print("="*50)

    try:
        from middleware.monitoring import MetricsExporter, MonitoringMiddleware

        # 创建监控中间件
        monitoring = MonitoringMiddleware(
            slow_threshold=1.0,
            metrics_window_size=100,
        )
        print("✓ 监控中间件创建成功")

        # 模拟记录一些指标
        monitoring._record_metrics(
            path="/api/v1/test",
            method="GET",
            status_code=200,
            process_time=0.5,
            success=True
        )
        monitoring._record_metrics(
            path="/api/v1/test",
            method="GET",
            status_code=200,
            process_time=2.5,  # 慢请求
            success=True
        )
        monitoring._record_metrics(
            path="/api/v1/error",
            method="POST",
            status_code=500,
            process_time=0.3,
            success=False
        )
        print("✓ 指标记录成功")

        # 获取指标
        metrics = monitoring.get_metrics()
        print(f"✓ 指标摘要: {metrics['summary']}")
        print(f"✓ 慢请求数量: {len(metrics['slow_requests'])}")

        # 测试 Prometheus 导出
        prometheus = monitoring.get_prometheus_metrics()
        assert len(prometheus) > 0, "Prometheus 指标为空"
        print(f"✓ Prometheus 指标生成成功 ({len(prometheus)} 字符)")

        # 测试指标导出器
        exporter = MetricsExporter(monitoring)
        influx = exporter.export_influx()
        assert len(influx) > 0, "InfluxDB 指标为空"
        print(f"✓ InfluxDB 指标导出成功 ({len(influx)} 字符)")

        return True

    except Exception as e:
        print(f"✗ 监控中间件测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_middleware_pipeline():
    """测试中间件管道组合"""
    print("\n" + "="*50)
    print("测试中间件管道组合")
    print("="*50)

    try:
        from middleware.base import Pipeline
        from middleware.cache import CacheMiddleware
        from middleware.monitoring import MonitoringMiddleware
        from middleware.validation import ValidationMiddleware

        # 创建管道
        pipeline = Pipeline()

        # 添加中间件（指定顺序）
        pipeline.add(CacheMiddleware(name="cache"), order=1)
        pipeline.add(ValidationMiddleware(name="validation"), order=2)
        pipeline.add(MonitoringMiddleware(name="monitoring"), order=3)

        print(f"✓ 管道创建成功: {pipeline}")

        # 列出中间件
        middlewares = pipeline.list()
        print(f"✓ 中间件列表: {middlewares}")

        # 获取特定中间件
        cache = pipeline.get("cache")
        assert cache is not None, "缓存中间件未找到"
        print(f"✓ 获取中间件: {cache}")

        # 测试启用/禁用
        pipeline.disable("validation")
        cache_enabled = pipeline.get("validation")
        assert not cache_enabled.enabled, "禁用失败"
        print("✓ 中间件禁用成功")

        pipeline.enable("validation")
        cache_enabled = pipeline.get("validation")
        assert cache_enabled.enabled, "启用失败"
        print("✓ 中间件启用成功")

        return True

    except Exception as e:
        print(f"✗ 管道组合测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_validation_models():
    """测试 Pydantic 验证模型"""
    print("\n" + "="*50)
    print("测试 Pydantic 验证模型")
    print("="*50)

    try:
        from middleware.validation import PatentSearchRequest, SkillExecutionRequest

        # 测试专利搜索请求模型
        patent_search = PatentSearchRequest(
            query="人工智能",
            limit=10,
            offset=0
        )
        assert patent_search.query == "人工智能"
        assert patent_search.limit == 10
        print("✓ PatentSearchRequest 模型验证通过")

        # 测试技能执行请求模型
        skill_exec = SkillExecutionRequest(
            skill_name="patent_search",
            parameters={"query": "机器学习"}
        )
        assert skill_exec.skill_name == "patent_search"
        assert skill_exec.parameters["query"] == "机器学习"
        print("✓ SkillExecutionRequest 模型验证通过")

        return True

    except Exception as e:
        print(f"✗ 验证模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Athena 扩展中间件测试")
    print("="*60)

    results = {
        "缓存中间件": await test_cache_middleware(),
        "验证中间件": await test_validation_middleware(),
        "监控中间件": await test_monitoring_middleware(),
        "管道组合": await test_middleware_pipeline(),
        "验证模型": await test_validation_models(),
    }

    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)

    for name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name}: {status}")

    total = len(results)
    passed = sum(results.values())

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️ {total - passed} 个测试失败")


if __name__ == "__main__":
    asyncio.run(main())
