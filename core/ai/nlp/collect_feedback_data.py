#!/usr/bin/env python3

"""
反馈数据收集脚本
Feedback Data Collection Script

用于收集智能选择器的反馈数据,支持A/B测试分析

作者: Athena平台团队
版本: v1.0.0
"""

import time
from typing import Any

import requests

# 配置
GATEWAY_URL = "http://localhost:8100"
CHAT_ENDPOINT = f"{GATEWAY_URL}/api/v1/chat"
AB_CONFIG_ENDPOINT = f"{GATEWAY_URL}/api/v1/ab-test/config"
FEEDBACK_ENDPOINT = f"{GATEWAY_URL}/api/v1/feedback"

# 测试查询列表(覆盖18种能力)
TEST_QUERIES = [
    # 基础能力
    {"message": "你好,今天心情不错", "expected": "daily_chat", "category": "基础能力"},
    {"message": "启动系统监控服务", "expected": "platform_controller", "category": "基础能力"},
    {"message": "帮我分析这段Python代码", "expected": "coding_assistant", "category": "基础能力"},
    {"message": "提醒我明天开会", "expected": "life_assistant", "category": "基础能力"},
    # 专业能力
    {"message": "搜索专利信息", "expected": "patent", "category": "专业能力"},
    {"message": "查询法律规定", "expected": "legal", "category": "专业能力"},
    # 高级能力
    {"message": "分析这段文本的情感", "expected": "nlp", "category": "高级能力"},
    {"message": "查询知识图谱", "expected": "knowledge_graph", "category": "高级能力"},
    {"message": "记住这个信息", "expected": "memory", "category": "高级能力"},
    {"message": "优化系统性能", "expected": "optimization", "category": "高级能力"},
    # Phase 3能力
    {"message": "识别这张图片", "expected": "multimodal", "category": "Phase 3能力"},
    {"message": "启动多智能体协作", "expected": "agent_fusion", "category": "Phase 3能力"},
    {"message": "自主学习新知识", "expected": "autonomous", "category": "Phase 3能力"},
    # Phase 4能力
    {"message": "企业管理系统", "expected": "enterprise", "category": "Phase 4能力"},
    {"message": "模型量化优化", "expected": "quantization", "category": "Phase 4能力"},
    {"message": "联邦学习训练", "expected": "federated", "category": "Phase 4能力"},
    # 智能体能力
    {"message": "小晨智能体对话", "expected": "xiaochen", "category": "智能体能力"},
]


def set_ab_test_config(enabled: bool, ratio: float = 0.5) -> bool:
    """设置A/B测试配置"""
    try:
        params = {"enabled": enabled, "smart_selector_ratio": ratio}
        response = requests.post(f"{AB_CONFIG_ENDPOINT}", params=params, timeout=10)
        result = response.json()

        if result.get("success"):
            print(f"✅ A/B测试配置已更新: enabled={enabled}, ratio={ratio}")
            return True
        else:
            print(f"❌ 更新A/B测试配置失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 更新A/B测试配置异常: {e}")
        return False


def send_chat_request(
    message: str, user_id: str, selector_type: str
) -> tuple[bool, dict[str, Any]]:
    """
    发送聊天请求

    Args:
        message: 用户消息
        user_id: 用户ID
        selector_type: 选择器类型("smart" 或 "simple")

    Returns:
        (成功标志, 响应数据)
    """
    try:
        payload = {"message": message, "user_id": user_id}
        start_time = time.time()
        response = requests.post(CHAT_ENDPOINT, json=payload, timeout=30)
        elapsed_time = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return True, {"response": data, "elapsed_time": elapsed_time}
            else:
                return False, {"error": "API返回success=false", "data": data}
        else:
            return False, {"error": f"HTTP {response.status_code}", "response": response.text}

    except Exception as e:
        return False, {"error": str(e)}


def submit_feedback(
    user_id: str,
    query: str,
    expected_capability: str,
    actual_capability: str,
    success: bool,
    satisfaction: float,
    execution_time: float,
    selector_type: str,
) -> bool:
    """
    提交反馈数据

    Args:
        user_id: 用户ID
        query: 查询文本
        expected_capability: 预期能力
        actual_capability: 实际能力
        success: 是否成功
        satisfaction: 满意度
        execution_time: 执行时间
        selector_type: 选择器类型

    Returns:
        是否成功
    """
    try:
        payload = {
            "query": query,
            "expected_capability": expected_capability,
            "actual_capability": actual_capability,
            "success": success,
            "satisfaction": satisfaction,
            "execution_time": execution_time,
            "selector_type": selector_type,
        }

        response = requests.post(f"{FEEDBACK_ENDPOINT}/{user_id}", json=payload, timeout=10)
        result = response.json()

        return result.get("success", False)

    except Exception as e:
        print(f"  ⚠️ 提交反馈失败: {e}")
        return False


def evaluate_result(expected: str, actual: str) -> tuple[bool, float]:
    """
    评估结果并计算满意度

    Args:
        expected: 预期能力
        actual: 实际能力

    Returns:
        (是否成功, 满意度)
    """
    if expected == actual:
        return True, 1.0
    else:
        # 根据能力相似度给出部分分数
        # 同类能力给予0.5分
        capability_groups = {
            "基础": ["daily_chat", "platform_controller", "coding_assistant", "life_assistant"],
            "专业": ["patent", "legal"],
            "高级": ["nlp", "knowledge_graph", "memory", "optimization"],
            "Phase3": ["multimodal", "agent_fusion", "autonomous"],
            "Phase4": ["enterprise", "quantization", "federated"],
            "智能体": ["xiaochen"],
        }

        # 检查是否在同一组
        for _group, capabilities in capability_groups.items():
            if expected in capabilities and actual in capabilities:
                return False, 0.5

        return False, 0.0


def run_test_batch(selector_type: str, test_queries: list[dict[str, str]) -> dict[str, Any]]:
    """
    运行一批测试

    Args:
        selector_type: 选择器类型("smart" 或 "simple")
        test_queries: 测试查询列表

    Returns:
        统计数据
    """
    print(f"\n{'=' * 60}")
    print(f"🧪 测试模式: {selector_type.upper()} SELECTOR")
    print(f"{'=' * 60}")

    stats = {"total": 0, "success": 0, "total_satisfaction": 0.0, "total_time": 0.0, "results": []}

    for i, query_data in enumerate(test_queries, 1):
        message = query_data["message"]
        expected = query_data["expected"]
        category = query_data["category"]

        # 生成唯一用户ID
        user_id = f"{selector_type}_test_user_{i}_{int(time.time())}"

        print(f"\n[{i}/{len(test_queries)}] {category}")
        print(f"  查询: {message}")
        print(f"  预期: {expected}")

        # 发送请求
        success, response_data = send_chat_request(message, user_id, selector_type)

        if success:
            response = response_data["response"]
            actual_capability = response.get("tool_used", "unknown")
            execution_time = response_data["elapsed_time"]

            print(f"  实际: {actual_capability}")
            print(f"  耗时: {execution_time:.3f}s")

            # 评估结果
            is_correct, satisfaction = evaluate_result(expected, actual_capability)
            print(f"  结果: {'✅ 正确' if is_correct else '❌ 错误'}")
            print(f"  满意度: {satisfaction:.1f}")

            # 更新统计
            stats["total"] += 1
            if is_correct:
                stats["success"] += 1
            stats["total_satisfaction"] += satisfaction
            stats["total_time"] += execution_time

            # 记录结果
            stats["results"].append(
                {
                    "query": message,
                    "expected": expected,
                    "actual": actual_capability,
                    "correct": is_correct,
                    "satisfaction": satisfaction,
                    "time": execution_time,
                }
            )

        else:
            print(f"  ❌ 请求失败: {response_data.get('error', 'Unknown error')}")
            stats["total"] += 1
            # 失败给0分
            stats["total_satisfaction"] += 0.0

    return stats


def print_statistics(stats: dict[str, Any], selector_type: str) -> Any:
    """打印统计数据"""
    print(f"\n{'=' * 60}")
    print(f"📊 {selector_type.upper()} SELECTOR 统计")
    print(f"{'=' * 60}")

    total = stats["total"]
    success = stats["success"]

    if total > 0:
        success_rate = (success / total) * 100
        avg_satisfaction = stats["total_satisfaction"] / total
        avg_time = stats["total_time"] / total

        print(f"总测试数: {total}")
        print(f"成功数: {success}")
        print(f"准确率: {success_rate:.1f}%")
        print(f"平均满意度: {avg_satisfaction:.3f}")
        print(f"平均耗时: {avg_time:.3f}s")
    else:
        print("无测试数据")


def compare_statistics(smart_stats: dict[str, Any], simple_stats: dict[str, Any]) -> None:
    """对比两种选择器的统计"""
    print(f"\n{'=' * 60}")
    print("📈 A/B测试对比分析")
    print(f"{'=' * 60}")

    if smart_stats["total"] == 0 or simple_stats["total"] == 0:
        print("⚠️ 缺少对比数据")
        return

    # 准确率对比
    smart_rate = (smart_stats["success"] / smart_stats["total"]) * 100
    simple_rate = (simple_stats["success"] / simple_stats["total"]) * 100
    rate_improvement = smart_rate - simple_rate

    print("\n准确率对比:")
    print(f"  智能选择器: {smart_rate:.1f}%")
    print(f"  简单映射: {simple_rate:.1f}%")
    print(f"  提升: {rate_improvement:+.1f}%")

    # 满意度对比
    smart_sat = smart_stats["total_satisfaction"] / smart_stats["total"]
    simple_sat = simple_stats["total_satisfaction"] / simple_stats["total"]
    sat_improvement = smart_sat - simple_sat

    print("\n满意度对比:")
    print(f"  智能选择器: {smart_sat:.3f}")
    print(f"  简单映射: {simple_sat:.3f}")
    print(f"  提升: {sat_improvement:+.3f}")

    # 耗时对比
    smart_time = smart_stats["total_time"] / smart_stats["total"]
    simple_time = simple_stats["total_time"] / simple_stats["total"]
    time_reduction = ((simple_time - smart_time) / simple_time) * 100 if simple_time > 0 else 0

    print("\n平均耗时对比:")
    print(f"  智能选择器: {smart_time:.3f}s")
    print(f"  简单映射: {simple_time:.3f}s")
    print(f"  减少: {time_reduction:+.1f}%")

    # 结论
    print(f"\n{'=' * 60}")
    if rate_improvement > 10:
        print("🏆 智能选择器表现显著优于简单映射!")
        print("   建议: 将智能选择器流量比例提升至100%")
    elif rate_improvement > 0:
        print("👍 智能选择器表现优于简单映射")
        print("   建议: 继续观察,保持当前流量比例")
    else:
        print("⚠️ 智能选择器未明显优于简单映射")
        print("   建议: 需要进一步优化模型或调整特征")


def main() -> None:
    """主函数"""
    print("🚀 开始反馈数据收集...")
    print(f"目标: {len(TEST_QUERIES)}条测试查询")

    # 1. 测试智能选择器
    print("\n" + "=" * 60)
    print("第一步: 测试智能选择器 (100% 流量)")
    print("=" * 60)

    set_ab_test_config(enabled=True, ratio=1.0)
    time.sleep(1)  # 等待配置生效

    smart_stats = run_test_batch("smart", TEST_QUERIES)
    print_statistics(smart_stats, "Smart")

    # 2. 测试简单映射
    print("\n" + "=" * 60)
    print("第二步: 测试简单映射 (0% 流量)")
    print("=" * 60)

    set_ab_test_config(enabled=True, ratio=0.0)
    time.sleep(1)  # 等待配置生效

    simple_stats = run_test_batch("simple", TEST_QUERIES)
    print_statistics(simple_stats, "Simple")

    # 3. 对比分析
    compare_statistics(smart_stats, simple_stats)

    # 4. 恢复默认配置(50%流量)
    print(f"\n{'=' * 60}")
    print("恢复默认A/B测试配置 (50% 流量)")
    print(f"{'=' * 60}")

    set_ab_test_config(enabled=True, ratio=0.5)

    print("\n✅ 反馈数据收集完成!")


if __name__ == "__main__":
    main()

