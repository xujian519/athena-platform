#!/usr/bin/env python3
"""
性能测试 - 多级权限系统

测试权限系统的性能指标。

作者: Athena平台团队
创建时间: 2026-04-20
"""

import logging
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def benchmark_permission_check():
    """基准测试：单次权限检查"""
    from core.tools.permissions_v2.manager import get_global_permission_manager
    from core.tools.permissions_v2.modes import PermissionMode

    manager = get_global_permission_manager()
    manager.initialize(mode=PermissionMode.DEFAULT)

    print("\n=== 基准测试：单次权限检查 ===")

    # 预热
    for _ in range(100):
        manager.check_permission("file:read", {"path": "/tmp/test.txt"})

    # 测试不同场景
    scenarios = [
        ("file:read", {"path": "/tmp/test.txt"}, "文件读取"),
        ("file:write", {"path": "/tmp/test.txt"}, "文件写入"),
        ("bash:execute", {"command": "ls -la"}, "命令执行"),
        ("web_search", {"query": "test"}, "网络搜索"),
    ]

    results = {}

    for tool_name, parameters, description in scenarios:
        times = []
        for _ in range(1000):
            start = time.perf_counter()
            manager.check_permission(tool_name, parameters)
            end = time.perf_counter()
            times.append((end - start) * 1000)  # 转换为毫秒

        avg = statistics.mean(times)
        p50 = statistics.median(times)
        p95 = statistics.quantiles(times, n=20)[18]  # 95th percentile
        p99 = statistics.quantiles(times, n=100)[98]  # 99th percentile

        results[description] = {
            "avg": avg,
            "p50": p50,
            "p95": p95,
            "p99": p99,
        }

        print(f"\n{description}:")
        print(f"  平均延迟: {avg:.3f}ms")
        print(f"  P50: {p50:.3f}ms")
        print(f"  P95: {p95:.3f}ms")
        print(f"  P99: {p99:.3f}ms")

    # 验证性能目标
    print("\n=== 性能目标验证 ===")
    targets = {
        "平均延迟": 1.0,  # <1ms
        "P95": 1.0,  # <1ms
        "P99": 2.0,  # <2ms
    }

    all_pass = True
    for desc, metrics in results.items():
        if metrics["avg"] > targets["平均延迟"]:
            print(f"❌ {desc}: 平均延迟 {metrics['avg']:.3f}ms > {targets['平均延迟']}ms")
            all_pass = False
        if metrics["p95"] > targets["P95"]:
            print(f"❌ {desc}: P95 {metrics['p95']:.3f}ms > {targets['P95']}ms")
            all_pass = False
        if metrics["p99"] > targets["P99"]:
            print(f"❌ {desc}: P99 {metrics['p99']:.3f}ms > {targets['P99']}ms")
            all_pass = False

    if all_pass:
        print("✅ 所有性能目标达成！")

    return results


def benchmark_concurrent():
    """并发性能测试"""
    from core.tools.permissions_v2.manager import get_global_permission_manager
    from core.tools.permissions_v2.modes import PermissionMode

    manager = get_global_permission_manager()
    manager.initialize(mode=PermissionMode.DEFAULT)

    print("\n=== 并发性能测试 ===")

    # 测试不同并发级别
    concurrency_levels = [1, 10, 50, 100, 500]

    for concurrency in concurrency_levels:
        # 预热
        for _ in range(100):
            manager.check_permission("file:read", {"path": "/tmp/test.txt"})

        # 并发测试
        start = time.perf_counter()

        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = []
            for _ in range(1000):
                future = executor.submit(
                    manager.check_permission, "file:read", {"path": "/tmp/test.txt"}
                )
                futures.append(future)

            results = [f.result() for f in as_completed(futures)]

        end = time.perf_counter()
        total_time = end - start
        qps = len(results) / total_time

        print(f"并发级别 {concurrency:3d}: {qps:8.0f} QPS, 平均延迟: {total_time/len(results)*1000:.3f}ms")

    print("✅ 并发性能测试完成")


def benchmark_large_rules():
    """大量规则场景测试"""
    from core.tools.permissions_v2.manager import get_global_permission_manager
    from core.tools.permissions_v2.modes import PermissionMode
    from core.tools.permissions_v2.path_rules import PathRule

    manager = get_global_permission_manager()

    print("\n=== 大量规则场景测试 ===")

    # 测试不同数量的规则
    rule_counts = [10, 50, 100, 500, 1000]

    for rule_count in rule_counts:
        # 创建指定数量的规则
        rules = []
        for i in range(rule_count):
            rules.append(
                PathRule(
                    rule_id=f"rule-{i}",
                    pattern=f"/tmp/dir{i}/**",
                    allow=True,
                    priority=i % 100,
                )
            )

        # 重新初始化管理器
        manager = get_global_permission_manager()
        manager.initialize(mode=PermissionMode.DEFAULT, path_rules=rules)

        # 测试性能
        times = []
        for _ in range(100):
            start = time.perf_counter()
            manager.check_permission("file:read", {"path": "/tmp/test.txt"})
            end = time.perf_counter()
            times.append((end - start) * 1000)

        avg = statistics.mean(times)

        print(f"规则数量 {rule_count:4d}: 平均延迟 {avg:.3f}ms")

    print("✅ 大量规则场景测试完成")


def benchmark_memory():
    """内存占用测试"""
    import tracemalloc

    from core.tools.permissions_v2.manager import get_global_permission_manager
    from core.tools.permissions_v2.modes import PermissionMode
    from core.tools.permissions_v2.path_rules import PathRule

    print("\n=== 内存占用测试 ===")

    # 启动内存跟踪
    tracemalloc.start()

    # 基线内存
    snapshot1 = tracemalloc.take_snapshot()

    # 创建权限管理器
    manager = get_global_permission_manager()
    manager.initialize(mode=PermissionMode.DEFAULT)

    snapshot2 = tracemalloc.take_snapshot()

    # 计算内存增长
    top_stats = snapshot2.compare_to(snapshot1, 'lineno')
    total_memory = sum(stat.size_diff for stat in top_stats) / 1024  # KB

    print(f"初始化内存增长: {total_memory:.1f} KB")

    # 添加大量规则
    rules = []
    for i in range(1000):
        rules.append(
            PathRule(
                rule_id=f"rule-{i}",
                pattern=f"/tmp/dir{i}/**",
                allow=True,
                priority=i % 100,
            )
        )

    manager.initialize(mode=PermissionMode.DEFAULT, path_rules=rules)

    snapshot3 = tracemalloc.take_snapshot()
    top_stats = snapshot3.compare_to(snapshot2, 'lineno')
    total_memory = sum(stat.size_diff for stat in top_stats) / 1024  # KB

    print(f"1000 条规则内存增长: {total_memory:.1f} KB")

    tracemalloc.stop()

    if total_memory < 5000:  # <5MB
        print("✅ 内存占用符合目标（<5MB）")
    else:
        print(f"⚠️ 内存占用超过目标: {total_memory:.1f} KB")

    print("✅ 内存占用测试完成")


def main():
    """主函数"""
    print("⚡ 开始性能测试...")

    benchmark_permission_check()
    benchmark_concurrent()
    benchmark_large_rules()
    benchmark_memory()

    print("\n🎉 所有性能测试完成！")


if __name__ == "__main__":
    main()

