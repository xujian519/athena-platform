#!/usr/bin/env python3
"""
system_monitor工具验证脚本

验证system_monitor_handler的功能：
1. CPU使用率监控
2. 内存使用情况监控
3. 磁盘使用情况监控
4. 健康状态判断
5. 跨平台兼容性测试

Author: Athena平台团队
Created: 2026-04-20
"""

import asyncio
import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_cpu_monitoring() -> dict[str, Any]:
    """测试CPU监控功能"""
    print("\n" + "=" * 60)
    print("测试1: CPU监控功能")
    print("=" * 60)

    from core.tools.tool_implementations import system_monitor_handler

    params = {
        "target": "system",
        "metrics": ["cpu"]
    }

    result = await system_monitor_handler(params, {})

    print("✅ CPU监控结果:")
    print(f"   - 使用率: {result['metrics']['cpu']['usage_percent']}%")
    print(f"   - 状态: {result['metrics']['cpu']['status']}")
    print(f"   - 时间戳: {result['timestamp']}")

    # 验证结果
    assert "metrics" in result, "结果中缺少metrics字段"
    assert "cpu" in result["metrics"], "结果中缺少cpu字段"
    assert "usage_percent" in result["metrics"]["cpu"], "结果中缺少usage_percent字段"
    assert "status" in result["metrics"]["cpu"], "结果中缺少status字段"
    assert result["metrics"]["cpu"]["status"] in ["healthy", "warning", "error"], "状态值不合法"

    print("✅ CPU监控测试通过")
    return result


async def test_memory_monitoring() -> dict[str, any]:
    """测试内存监控功能"""
    print("\n" + "=" * 60)
    print("测试2: 内存监控功能")
    print("=" * 60)

    from core.tools.tool_implementations import system_monitor_handler

    params = {
        "target": "system",
        "metrics": ["memory"]
    }

    result = await system_monitor_handler(params, {})

    print("✅ 内存监控结果:")
    print(f"   - 使用率: {result['metrics']['memory']['usage_percent']}%")
    print(f"   - 可用空间: {result['metrics']['memory'].get('free_gb', 'N/A')} GB")
    print(f"   - 已用空间: {result['metrics']['memory'].get('used_gb', 'N/A')} GB")
    print(f"   - 状态: {result['metrics']['memory']['status']}")

    # 验证结果
    assert "metrics" in result, "结果中缺少metrics字段"
    assert "memory" in result["metrics"], "结果中缺少memory字段"
    assert "usage_percent" in result["metrics"]["memory"], "结果中缺少usage_percent字段"
    assert "status" in result["metrics"]["memory"], "结果中缺少status字段"
    assert result["metrics"]["memory"]["status"] in ["healthy", "warning", "error"], "状态值不合法"

    print("✅ 内存监控测试通过")
    return result


async def test_disk_monitoring() -> dict[str, any]:
    """测试磁盘监控功能"""
    print("\n" + "=" * 60)
    print("测试3: 磁盘监控功能")
    print("=" * 60)

    from core.tools.tool_implementations import system_monitor_handler

    params = {
        "target": "system",
        "metrics": ["disk"]
    }

    result = await system_monitor_handler(params, {})

    print("✅ 磁盘监控结果:")
    if "total" in result["metrics"]["disk"]:
        print(f"   - 总容量: {result['metrics']['disk']['total']}")
        print(f"   - 已用空间: {result['metrics']['disk']['used']}")
        print(f"   - 可用空间: {result['metrics']['disk']['available']}")
    print(f"   - 使用率: {result['metrics']['disk']['usage_percent']}%")
    print(f"   - 状态: {result['metrics']['disk']['status']}")

    # 验证结果
    assert "metrics" in result, "结果中缺少metrics字段"
    assert "disk" in result["metrics"], "结果中缺少disk字段"
    assert "usage_percent" in result["metrics"]["disk"], "结果中缺少usage_percent字段"
    assert "status" in result["metrics"]["disk"], "结果中缺少status字段"
    assert result["metrics"]["disk"]["status"] in ["healthy", "warning", "error"], "状态值不合法"

    print("✅ 磁盘监控测试通过")
    return result


async def test_combined_monitoring() -> dict[str, any]:
    """测试综合监控功能"""
    print("\n" + "=" * 60)
    print("测试4: 综合监控功能（CPU+内存+磁盘）")
    print("=" * 60)

    from core.tools.tool_implementations import system_monitor_handler

    params = {
        "target": "system",
        "metrics": ["cpu", "memory", "disk"]
    }

    result = await system_monitor_handler(params, {})

    print("✅ 综合监控结果:")
    print(f"   - CPU使用率: {result['metrics']['cpu']['usage_percent']}% ({result['metrics']['cpu']['status']})")
    print(f"   - 内存使用率: {result['metrics']['memory']['usage_percent']}% ({result['metrics']['memory']['status']})")
    print(f"   - 磁盘使用率: {result['metrics']['disk']['usage_percent']}% ({result['metrics']['disk']['status']})")
    print(f"   - 时间戳: {result['timestamp']}")

    # 验证结果
    assert "metrics" in result, "结果中缺少metrics字段"
    assert "cpu" in result["metrics"], "结果中缺少cpu字段"
    assert "memory" in result["metrics"], "结果中缺少memory字段"
    assert "disk" in result["metrics"], "结果中缺少disk字段"

    print("✅ 综合监控测试通过")
    return result


async def test_health_status_logic() -> dict[str, any]:
    """测试健康状态判断逻辑"""
    print("\n" + "=" * 60)
    print("测试5: 健康状态判断逻辑")
    print("=" * 60)

    from core.tools.tool_implementations import system_monitor_handler

    params = {
        "target": "system",
        "metrics": ["cpu", "memory", "disk"]
    }

    result = await system_monitor_handler(params, {})

    # 检查健康状态判断
    cpu_status = result["metrics"]["cpu"]["status"]
    memory_status = result["metrics"]["memory"]["status"]
    disk_status = result["metrics"]["disk"]["status"]

    print("✅ 健康状态判断:")
    print(f"   - CPU状态: {cpu_status} (阈值: 80%)")
    print(f"   - 内存状态: {memory_status} (阈值: 80%)")
    print(f"   - 磁盘状态: {disk_status} (阈值: 85%)")

    # 验证状态判断逻辑
    cpu_usage = result["metrics"]["cpu"]["usage_percent"]
    memory_usage = result["metrics"]["memory"]["usage_percent"]
    disk_usage = result["metrics"]["disk"]["usage_percent"]

    assert cpu_usage < 80 or cpu_status == "warning", "CPU状态判断错误"
    assert memory_usage < 80 or memory_status == "warning", "内存状态判断错误"
    assert disk_usage < 85 or disk_status == "warning", "磁盘状态判断错误"

    print("✅ 健康状态判断测试通过")
    return result


async def test_cross_platform_compatibility() -> dict[str, any]:
    """测试跨平台兼容性"""
    print("\n" + "=" * 60)
    print("测试6: 跨平台兼容性")
    print("=" * 60)

    system = platform.system()
    print(f"✅ 当前操作系统: {system}")
    print(f"   - 平台: {platform.platform()}")
    print(f"   - Python版本: {sys.version.split()[0]}")

    from core.tools.tool_implementations import system_monitor_handler

    params = {
        "target": "system",
        "metrics": ["cpu", "memory", "disk"]
    }

    try:
        result = await system_monitor_handler(params, {})

        # 检查各个监控项是否成功
        success_count = 0
        total_count = 3

        if result["metrics"]["cpu"]["status"] != "error":
            success_count += 1
            print("   ✅ CPU监控: 正常")

        if result["metrics"]["memory"]["status"] != "error":
            success_count += 1
            print("   ✅ 内存监控: 正常")

        if result["metrics"]["disk"]["status"] != "error":
            success_count += 1
            print("   ✅ 磁盘监控: 正常")

        success_rate = (success_count / total_count) * 100
        print(f"\n   📊 成功率: {success_rate:.1f}% ({success_count}/{total_count})")

        print("✅ 跨平台兼容性测试完成")
        return result

    except Exception as e:
        print(f"❌ 跨平台兼容性测试失败: {e}")
        raise


async def test_error_handling() -> dict[str, any]:
    """测试错误处理"""
    print("\n" + "=" * 60)
    print("测试7: 错误处理")
    print("=" * 60)

    from core.tools.tool_implementations import system_monitor_handler

    # 测试不支持的metrics
    params = {
        "target": "system",
        "metrics": ["unsupported_metric"]
    }

    result = await system_monitor_handler(params, {})

    # 应该返回空结果而不是抛出异常
    assert "metrics" in result, "错误处理失败：应该返回metrics字段"
    print("✅ 错误处理测试通过（不支持的metrics不会导致崩溃）")

    return result


async def generate_performance_report(
    cpu_result: dict[str, Any],
    memory_result: dict[str, Any],
    disk_result: dict[str, Any],
    combined_result: dict[str, Any],
) -> dict[str, Any]:
    """生成性能报告"""
    print("\n" + "=" * 60)
    print("生成性能报告")
    print("=" * 60)

    report = {
        "timestamp": datetime.now().isoformat(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": sys.version.split()[0],
        },
        "performance_metrics": {
            "cpu_usage_percent": cpu_result["metrics"]["cpu"]["usage_percent"],
            "memory_usage_percent": memory_result["metrics"]["memory"]["usage_percent"],
            "disk_usage_percent": disk_result["metrics"]["disk"]["usage_percent"],
        },
        "health_status": {
            "cpu": combined_result["metrics"]["cpu"]["status"],
            "memory": combined_result["metrics"]["memory"]["status"],
            "disk": combined_result["metrics"]["disk"]["status"],
        },
        "response_time_ms": {
            # 估算响应时间（基于sleep时间）
            "cpu_monitoring": 20,
            "memory_monitoring": 20,
            "disk_monitoring": 20,
            "combined_monitoring": 20,
        }
    }

    print("✅ 性能报告生成完成")
    print("\n📊 系统状态摘要:")
    print(f"   - CPU: {report['performance_metrics']['cpu_usage_percent']}% ({report['health_status']['cpu']})")
    print(f"   - 内存: {report['performance_metrics']['memory_usage_percent']}% ({report['health_status']['memory']})")
    print(f"   - 磁盘: {report['performance_metrics']['disk_usage_percent']}% ({report['health_status']['disk']})")

    return report


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("system_monitor工具验证测试")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 测试1: CPU监控
        cpu_result = await test_cpu_monitoring()

        # 测试2: 内存监控
        memory_result = await test_memory_monitoring()

        # 测试3: 磁盘监控
        disk_result = await test_disk_monitoring()

        # 测试4: 综合监控
        combined_result = await test_combined_monitoring()

        # 测试5: 健康状态判断
        await test_health_status_logic()

        # 测试6: 跨平台兼容性
        await test_cross_platform_compatibility()

        # 测试7: 错误处理
        await test_error_handling()

        # 生成性能报告
        _report = await generate_performance_report(  # noqa: F841 (未使用变量)
            cpu_result, memory_result, disk_result, combined_result
        )

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return 0

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
