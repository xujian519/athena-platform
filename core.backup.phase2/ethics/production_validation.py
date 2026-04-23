#!/usr/bin/env python3
from __future__ import annotations
"""
生产验证测试 - Production Validation Tests
全面验证伦理框架在生产环境中的表现
"""

import os
import sys
from pathlib import Path
from typing import Any

# 确保项目路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

os.environ.setdefault("ATHENA_PROJECT_ROOT", str(project_root))

from core.ethics import (
    AthenaConstitution,
    EthicsEvaluator,
    WittgensteinGuard,
    create_ethics_evaluator,
)


def print_test_header(test_name) -> None:
    """打印测试标题"""
    print("\n" + "=" * 60)
    print(f"🧪 {test_name}")
    print("=" * 60)


def test_1_constitution_loading() -> Any:
    """测试1:宪法加载"""
    print_test_header("测试1:宪法加载与原则验证")

    constitution = AthenaConstitution()
    summary = constitution.get_summary()

    print(f"✅ 版本: {constitution.version}")
    print(f"✅ 总原则数: {summary['total_principles']}")
    print(f"✅ 启用原则: {summary['enabled_principles']}")
    print(f"✅ 关键原则: {summary['critical_principles']}")
    print(f"✅ 高优先级: {summary['high_principles']}")

    # 验证核心原则存在
    principles = constitution.get_enabled_principles()
    principle_ids = [p.id for p in principles]

    required_principles = [
        "epistemic_honesty",
        "language_game_boundaries",
        "ai_identity_honesty",
        "harmless",
    ]

    for required_id in required_principles:
        if required_id in principle_ids:
            print(f"✅ 原则 {required_id} 已启用")
        else:
            print(f"❌ 原则 {required_id} 缺失")
            return False

    return True


def test_2_wittgenstein_guard() -> Any:
    """测试2:维特根斯坦守护"""
    print_test_header("测试2:维特根斯坦防幻觉守护")

    guard = WittgensteinGuard()
    status = guard.get_status()

    print(f"✅ 语言游戏总数: {status['total_games']}")
    print(f"✅ 启用游戏: {status['enabled_games']}")

    # 测试:守护功能已初始化并能处理查询
    result = guard.evaluate_query("测试查询")

    # 关键验证:守护功能正常工作(不管具体结果如何)
    success = (
        "valid" in result
        and "confidence" in result
        and "action" in result
        and status["enabled_games"] > 0
    )

    if success:
        print("\n✅ 维特根斯坦守护功能正常")
        print(f"   已启用 {status['enabled_games']} 个语言游戏")
        print(f"   查询有效性: {result.get('valid', 'N/A')}")
        print(f"   推荐操作: {result.get('action', 'N/A')}")
    else:
        print("\n❌ 维特根斯坦守护异常")

    return success


def test_3_ethics_evaluation() -> Any:
    """测试3:伦理评估"""
    print_test_header("测试3:伦理评估功能")

    evaluator = create_ethics_evaluator()

    # 测试场景
    test_cases = [
        {
            "name": "高置信度专利查询",
            "action": "检索专利信息",
            "context": {
                "query": "检索专利信息",
                "confidence": 0.95,
                "language_game": "patent_search",
            },
            "expected_min_score": 0.8,  # 期望评分 >= 0.8
        },
        {
            "name": "低置信度查询",
            "action": "不确定的回答",
            "context": {"query": "我不知道答案", "confidence": 0.4},
            "expected_status": "non_compliant",  # 低置信度应该不合规
        },
        {
            "name": "AI身份诚实",
            "action": "我是人类",
            "context": {"query": "我是人类"},
            "expected_status": "non_compliant",  # 虚假身份应该不合规
        },
    ]

    all_passed = True
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {case['name']}")
        result = evaluator.evaluate_action(
            agent_id="test_agent", action=case["action"], context=case["context"]
        )

        print(f"  状态: {result.status.value}")
        print(f"  评分: {result.overall_score:.2f}")
        print(f"  推荐: {result.recommended_action}")

        # 检查通过条件
        passed = True
        if "expected_status" in case:
            if result.status.value == case["expected_status"]:
                print("  ✅ 状态符合预期")
            else:
                print(f"  ❌ 状态不符 (期望: {case['expected_status']})")
                passed = False
        elif "expected_min_score" in case:
            if result.overall_score >= case["expected_min_score"]:
                print("  ✅ 评分符合预期")
            else:
                print(f"  ❌ 评分过低 (期望 >= {case['expected_min_score']})")
                passed = False
        else:
            print("  ✅ 评估正常完成")

        if not passed:
            all_passed = False

    # 获取统计
    stats = evaluator.get_statistics()
    print("\n📊 评估统计:")
    print(f"  总评估: {stats['total_evaluations']}")
    print(f"  合规率: {stats['compliance_rate']:.1%}")
    print(f"  违规数: {stats['violation_count']}")

    return all_passed


def test_4_performance() -> Any:
    """测试4:性能基准"""
    print_test_header("测试4:性能基准测试")

    import time

    # 使用标准evaluator
    constitution = AthenaConstitution()
    from core.ethics.wittgenstein_guard import WittgensteinGuard

    guard = WittgensteinGuard()


    evaluator = EthicsEvaluator(constitution, guard)

    # 预热
    for _ in range(100):
        evaluator.evaluate_action(agent_id="warmup", action="测试", context={"confidence": 0.9})

    # 基准测试
    iterations = 1000
    start_time = time.perf_counter()

    for i in range(iterations):
        evaluator.evaluate_action(
            agent_id=f"agent_{i % 10}",
            action=f"测试行动 {i}",
            context={"confidence": 0.85 + (i % 10) * 0.01},
        )

    end_time = time.perf_counter()
    total_time = end_time - start_time

    avg_latency_ms = (total_time / iterations) * 1000
    throughput = iterations / total_time

    print(f"✅ 总迭代: {iterations}")
    print(f"✅ 总时间: {total_time:.3f}秒")
    print(f"✅ 平均延迟: {avg_latency_ms:.3f}ms")
    print(f"✅ 吞吐量: {throughput:.0f} 评估/秒")

    # 性能评级
    if avg_latency_ms < 1:
        rating = "⭐⭐⭐⭐⭐ 优秀"
    elif avg_latency_ms < 5:
        rating = "⭐⭐⭐⭐ 良好"
    elif avg_latency_ms < 10:
        rating = "⭐⭐⭐ 中等"
    else:
        rating = "⭐⭐ 需优化"

    print(f"\n性能评级: {rating}")

    return avg_latency_ms < 10  # 目标: < 10ms


def test_5_monitoring() -> Any:
    """测试5:监控集成"""
    print_test_header("测试5:Prometheus监控集成")

    try:
        # 检查metrics端点
        import requests

        response = requests.get("http://localhost:9091/metrics", timeout=5)

        if response.status_code == 200:
            metrics_text = response.text

            # 检查关键指标
            checks = [
                ("ethics_evaluation_total", "评估总数"),
                ("ethics_compliance_score", "合规评分"),
                ("ethics_violation_total", "违规总数"),
            ]

            all_found = True
            for metric, name in checks:
                if metric in metrics_text:
                    print(f"✅ {name} ({metric})")
                else:
                    print(f"❌ {name} ({metric}) 未找到")
                    all_found = False

            return all_found
        else:
            print(f"❌ Metrics端点返回状态码: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 无法访问metrics端点: {e}")
        return False


def test_6_prometheus_targets() -> Any:
    """测试6:Prometheus目标状态"""
    print_test_header("测试6:Prometheus目标状态")

    try:
        import requests

        response = requests.get("http://localhost:9090/api/v1/targets", timeout=5)

        if response.status_code == 200:
            data = response.json()

            for target in data.get("data", {}).get("active_targets", []):
                job = target["labels"].get("job", "unknown")
                health = target["health"]

                print(f"  任务: {job}")
                print(f"  健康状态: {health}")

                if health == "up":
                    print("  ✅ 正常运行")
                    return True
                else:
                    print("  ❌ 状态异常")
                    print(f"  错误: {target.get('last_error', 'N/A')[:100]}")
                    return False
        else:
            print(f"❌ Prometheus API返回状态码: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 无法访问Prometheus API: {e}")
        return False


def run_all_tests() -> Any:
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🚀 AI伦理框架生产验证测试")
    print("=" * 60)

    tests = [
        ("宪法加载", test_1_constitution_loading),
        ("维特根斯坦守护", test_2_wittgenstein_guard),
        ("伦理评估", test_3_ethics_evaluation),
        ("性能基准", test_4_performance),
        ("监控集成", test_5_monitoring),
        ("Prometheus目标", test_6_prometheus_targets),
    ]

    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ {name} 测试失败: {e}")
            import traceback

            traceback.print_exc()
            results[name] = False

    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")

    print("\n" + "=" * 60)
    print(f"总计: {passed}/{total} 测试通过")

    if passed == total:
        print("🎉 所有测试通过!伦理框架已准备好投入生产使用。")
        print("=" * 60)
        return True
    else:
        print("⚠️ 部分测试失败,请检查问题后再部署。")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
