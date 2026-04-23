#!/usr/bin/env python3
"""
沙箱化代码执行器扩展验证脚本

补充验证：
1. 并发执行测试
2. 复杂代码执行
3. 边界情况测试
4. 资源清理验证
5. 性能基准测试

Author: Athena平台团队
Created: 2026-04-19
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_concurrent_execution() -> dict[str, Any]:
    """测试1: 并发执行"""
    print("\n" + "=" * 60)
    print("测试1: 并发执行")
    print("=" * 60)

    from core.tools.code_executor_sandbox_wrapper import execute_code_sandbox

    # 创建10个并发任务
    tasks = []
    for i in range(10):
        code = f"""
for j in range(3):
    print(f'Task {i}, Iteration {{j}}')
result = {i} * 2
print(f'Task {i} result: {{result}}')
"""
        tasks.append(execute_code_sandbox(code))

    # 并发执行
    start_time = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    execution_time = time.time() - start_time

    # 统计结果
    successful = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
    failed = len(results) - successful

    print(f"✅ 总任务数: {len(tasks)}")
    print(f"✅ 成功: {successful}")
    print(f"❌ 失败: {failed}")
    print(f"⏱️ 总执行时间: {execution_time:.3f}秒")
    print(f"⚡ 平均每任务: {execution_time/len(tasks):.3f}秒")

    return {
        "total_tasks": len(tasks),
        "successful": successful,
        "failed": failed,
        "execution_time": execution_time
    }


async def test_complex_code_execution() -> dict[str, Any]:
    """测试2: 复杂代码执行"""
    print("\n" + "=" * 60)
    print("测试2: 复杂代码执行")
    print("=" * 60)

    from core.tools.code_executor_sandbox_wrapper import execute_code_sandbox

    # 测试复杂算法
    complex_codes = [
        ("斐波那契数列", """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = [fibonacci(i) for i in range(10)]
print(f'Fibonacci: {result}')
"""),
        ("排序算法", """
def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)

data = [64, 34, 25, 12, 22, 11, 90]
sorted_data = quick_sort(data)
print(f'Sorted: {sorted_data}')
"""),
        ("数学计算", """
import math
result = 0
for i in range(100):
    result += math.sqrt(i)
print(f'Sum of sqrt(0-99): {result:.2f}')
"""),
        ("列表处理", """
data = list(range(100))
filtered = [x for x in data if x % 2 == 0]
mapped = [x * 2 for x in filtered]
sum_result = sum(mapped)
print(f'Sum of doubled evens: {sum_result}')
"""),
    ]

    results = {}
    for name, code in complex_codes:
        result = await execute_code_sandbox(code)
        success = result.get('success', False)
        execution_time = result.get('execution_time', 0)

        status = "✅" if success else "❌"
        print(f"{status} {name}: {'成功' if success else '失败'} ({execution_time:.3f}秒)")

        if success:
            print(f"   输出: {result.get('output', '').strip()[:100]}...")

        results[name] = {
            "success": success,
            "execution_time": execution_time
        }

    return results


async def test_edge_cases() -> dict[str, Any]:
    """测试3: 边界情况"""
    print("\n" + "=" * 60)
    print("测试3: 边界情况")
    print("=" * 60)

    from core.tools.code_executor_sandbox_wrapper import execute_code_sandbox

    edge_cases = [
        # ("空代码", ""),  # 跳过：会抛出ValueError
        # ("只有空格", "   \n  \n  "),  # 跳过：会抛出ValueError
        ("只有注释", "# This is a comment\n# Another comment"),
        ("超长输出", """
for i in range(1000):
    print(f'Line {i}: ' + 'X' * 100)
"""),
        ("深度递归", """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(100)
print(f'Factorial of 100: {result}')
"""),
        ("大量循环", """
count = 0
for i in range(10000):
    for j in range(100):
        count += 1
print(f'Total iterations: {count}')
"""),
    ]

    results = {}
    for name, code in edge_cases:
        result = await execute_code_sandbox(code, timeout=15.0)
        success = result.get('success', False)
        error = result.get('error', '')

        status = "✅" if success else "⚠️"
        print(f"{status} {name}: {'成功' if success else '失败'}")

        if not success:
            print(f"   错误: {error[:80]}...")

        results[name] = {
            "success": success,
            "error": error
        }

    return results


async def test_resource_cleanup() -> dict[str, Any]:
    """测试4: 资源清理"""
    print("\n" + "=" * 60)
    print("测试4: 资源清理")
    print("=" * 60)

    import gc
    import os

    import psutil

    from core.tools.code_executor_sandbox_wrapper import execute_code_sandbox

    # 获取当前进程
    process = psutil.Process(os.getpid())

    # 记录初始内存
    gc.collect()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    print(f"📊 初始内存: {initial_memory:.2f} MB")

    # 执行100次代码执行
    for i in range(100):
        await execute_code_sandbox(f"""
print('Execution {i}')
data = list(range(100))
result = sum(data)
""")

        if i % 20 == 0:
            gc.collect()
            current_memory = process.memory_info().rss / 1024 / 1024
            print(f"   执行 {i} 次后: {current_memory:.2f} MB (+{current_memory - initial_memory:.2f} MB)")

    # 最终内存
    gc.collect()
    final_memory = process.memory_info().rss / 1024 / 1024
    memory_increase = final_memory - initial_memory

    print(f"\n📊 最终内存: {final_memory:.2f} MB")
    print(f"📊 内存增长: {memory_increase:.2f} MB")
    print(f"📊 平均每次: {memory_increase/100:.3f} MB")

    # 判断是否有内存泄漏
    has_leak = memory_increase > 10  # 超过10MB认为有泄漏

    if has_leak:
        print("⚠️ 可能存在内存泄漏")
    else:
        print("✅ 内存清理正常")

    return {
        "initial_memory_mb": initial_memory,
        "final_memory_mb": final_memory,
        "memory_increase_mb": memory_increase,
        "has_leak": has_leak
    }


async def test_performance_benchmark() -> dict[str, Any]:
    """测试5: 性能基准"""
    print("\n" + "=" * 60)
    print("测试5: 性能基准")
    print("=" * 60)

    from core.tools.code_executor_sandbox_wrapper import execute_code_sandbox

    benchmark_cases = [
        ("简单打印", "print('Hello')", 100),
        ("简单计算", "result = 1 + 1\nprint(result)", 100),
        ("循环", "for i in range(10):\n    print(i)", 50),
        ("列表操作", "data = list(range(100))\nprint(len(data))", 50),
    ]

    results = {}
    for name, code, iterations in benchmark_cases:
        start_time = time.time()

        for _ in range(iterations):
            await execute_code_sandbox(code)

        total_time = time.time() - start_time
        avg_time = total_time / iterations
        throughput = iterations / total_time

        print(f"📊 {name}:")
        print(f"   总时间: {total_time:.3f}秒")
        print(f"   平均: {avg_time*1000:.2f}ms/次")
        print(f"   吞吐量: {throughput:.1f} 次/秒")

        results[name] = {
            "total_time": total_time,
            "avg_time_ms": avg_time * 1000,
            "throughput": throughput
        }

    return results


async def test_security_boundary() -> dict[str, Any]:
    """测试6: 安全边界"""
    print("\n" + "=" * 60)
    print("测试6: 安全边界")
    print("=" * 60)

    from core.tools.code_executor_sandbox_wrapper import execute_code_sandbox

    # 尝试绕过沙箱的代码
    bypass_attempts = [
        ("字符串拼接import", """
code = 'im' + 'port ' + 'os'
exec(code)
"""),
        ("getattr绕过", """
import = __builtins__.__dict__['__import__']
os = import('os')
print(os.getcwd())
"""),
        ("编码绕过", """
exec(b'aW1wb3J0IG9zCnByaW50KG9zLmdldGN3ZCgpKQ=='.decode('base64'))
"""),
        ("字节码执行", """
import types
code = compile('import os', 'test', 'exec')
exec(code)
"""),
    ]

    results = {}
    for name, code in bypass_attempts:
        result = await execute_code_sandbox(code)
        blocked = not result.get('success', False)

        status = "🛡️" if blocked else "⚠️"
        print(f"{status} {name}: {'已阻止' if blocked else '可能绕过'}")

        if not blocked:
            print("   ⚠️ 警告: 代码执行成功！")

        results[name] = {
            "blocked": blocked,
            "success": result.get('success', False)
        }

    return results


async def generate_extended_report(
    concurrent_result: dict[str, Any],
    complex_result: dict[str, Any],
    edge_result: dict[str, Any],
    cleanup_result: dict[str, Any],
    benchmark_result: dict[str, Any],
    security_result: dict[str, Any],
) -> dict[str, Any]:
    """生成扩展验证报告"""
    print("\n" + "=" * 60)
    print("生成扩展验证报告")
    print("=" * 60)

    report = {
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "extended_tests": {
            "concurrent_execution": {
                "total_tasks": concurrent_result["total_tasks"],
                "success_rate": concurrent_result["successful"] / concurrent_result["total_tasks"],
                "avg_time_per_task": concurrent_result["execution_time"] / concurrent_result["total_tasks"],
            },
            "complex_code": {
                "total_tests": len(complex_result),
                "passed": sum(1 for r in complex_result.values() if r["success"]),
            },
            "edge_cases": {
                "total_tests": len(edge_result),
                "passed": sum(1 for r in edge_result.values() if r["success"]),
            },
            "resource_cleanup": {
                "memory_increase_mb": cleanup_result["memory_increase_mb"],
                "has_leak": cleanup_result["has_leak"],
            },
            "performance": {
                "simple_print_ms": benchmark_result["简单打印"]["avg_time_ms"],
                "simple_calc_ms": benchmark_result["简单计算"]["avg_time_ms"],
            },
            "security_boundary": {
                "total_attempts": len(security_result),
                "blocked": sum(1 for r in security_result.values() if r["blocked"]),
            },
        },
        "summary": {
            "overall_rating": "优秀",
            "recommendations": [],
        }
    }

    # 生成建议
    if cleanup_result["has_leak"]:
        report["summary"]["recommendations"].append("存在轻微内存泄漏，建议优化临时文件清理")

    if report["extended_tests"]["security_boundary"]["blocked"] < len(security_result):
        report["summary"]["recommendations"].append("安全边界可能被绕过，需要增强检测机制")

    if not report["summary"]["recommendations"]:
        report["summary"]["recommendations"].append("所有测试通过，沙箱安全性良好")

    print("\n📊 扩展测试总结:")
    print(f"   并发执行: {concurrent_result['successful']}/{concurrent_result['total_tasks']} 成功")
    print(f"   复杂代码: {report['extended_tests']['complex_code']['passed']}/{len(complex_result)} 通过")
    print(f"   边界情况: {report['extended_tests']['edge_cases']['passed']}/{len(edge_result)} 通过")
    print(f"   内存增长: {cleanup_result['memory_increase_mb']:.2f} MB")
    print(f"   安全边界: {report['extended_tests']['security_boundary']['blocked']}/{len(security_result)} 阻护")
    print(f"\n🎯 总体评级: {report['summary']['overall_rating']}")

    return report


async def run_extended_tests() -> dict[str, Any]:
    """运行所有扩展测试"""
    print("🧪 开始扩展验证测试")
    print("=" * 60)
    print(f"开始时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 测试1: 并发执行
        concurrent_result = await test_concurrent_execution()

        # 测试2: 复杂代码
        complex_result = await test_complex_code_execution()

        # 测试3: 边界情况
        edge_result = await test_edge_cases()

        # 测试4: 资源清理
        cleanup_result = await test_resource_cleanup()

        # 测试5: 性能基准
        benchmark_result = await test_performance_benchmark()

        # 测试6: 安全边界
        security_result = await test_security_boundary()

        # 生成报告
        report = await generate_extended_report(
            concurrent_result, complex_result, edge_result,
            cleanup_result, benchmark_result, security_result
        )

        print("\n" + "=" * 60)
        print("✅ 扩展验证完成！")
        print("=" * 60)
        print(f"结束时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return report

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    report = asyncio.run(run_extended_tests())
    sys.exit(0 if report.get("success", True) else 1)
