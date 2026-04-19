#!/usr/bin/env python3
"""
学习引擎工具函数使用示例
Learning Engine Utility Functions Usage Examples

演示如何使用3个公共工具函数:
- epsilon_greedy_select: ε-贪婪选择策略
- calculate_q_table_reward: Q学习奖励计算
- get_q_values_from_orchestrator: 安全获取Q值

作者: Athena AI Team
版本: 1.0.0
创建: 2026-01-29
"""

from __future__ import annotations
import sys
from pathlib import Path

# 添加项目路径
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from production.core.learning.unified_interface import (
    calculate_q_table_reward,
    epsilon_greedy_select,
    get_q_values_from_orchestrator,
)

# =============================================================================
# 示例1: ε-贪婪选择策略
# =============================================================================

def example_epsilon_greedy():
    """示例1: ε-贪婪选择策略"""
    print("=" * 80)
    print("示例1: ε-贪婪选择策略")
    print("=" * 80)

    # 场景：智能体需要选择一个工具来完成任务
    tools = ["search_tool", "analysis_tool", "generate_tool"]

    # 假设这是学习得到的Q值（表示每个工具的历史表现）
    q_values = {
        "search_tool": 0.8,     # 历史表现最好
        "analysis_tool": 0.3,   # 中等表现
        "generate_tool": 0.1    # 表现较差
    }

    print("\n📊 可用工具及Q值:")
    for tool, q in q_values.items():
        print(f"  {tool}: Q={q:.2f}")

    # 场景1.1: 利用模式（epsilon=0，总是选择最优）
    print("\n🎯 场景1.1: 纯利用模式 (epsilon=0.0)")
    selected, confidence = epsilon_greedy_select(
        options=tools,
        q_values=q_values,
        epsilon=0.0  # 100%利用
    )
    print(f"  选择: {selected}")
    print(f"  置信度: {confidence:.2f}")

    # 场景1.2: 探索模式（epsilon=1，随机选择）
    print("\n🔍 场景1.2: 纯探索模式 (epsilon=1.0)")
    selected, confidence = epsilon_greedy_select(
        options=tools,
        q_values=q_values,
        epsilon=1.0  # 100%探索
    )
    print(f"  选择: {selected}")
    print(f"  置信度: {confidence:.2f} (探索时固定)")

    # 场景1.3: 平衡模式（epsilon=0.1，推荐）
    print("\n⚖️ 场景1.3: 平衡模式 (epsilon=0.1)")
    selections = []
    for _i in range(10):
        selected, confidence = epsilon_greedy_select(
            options=tools,
            q_values=q_values,
            epsilon=0.1  # 10%探索，90%利用
        )
        selections.append(selected)
    print(f"  10次选择结果: {selections}")
    print("  选择分布:")
    for tool in tools:
        count = selections.count(tool)
        print(f"    {tool}: {count}/10")


# =============================================================================
# 示例2: Q学习奖励计算
# =============================================================================

def example_reward_calculation():
    """示例2: Q学习奖励计算"""
    print("\n" + "=" * 80)
    print("示例2: Q学习奖励计算")
    print("=" * 80)

    # 场景2.1: 完美决策
    print("\n✅ 场景2.1: 完美决策")
    reward = calculate_q_table_reward(
        success=True,
        confidence=0.95,
        execution_time_ms=300.0,   # 非常快
        user_satisfaction=1.0,     # 满意度满分
        baseline_time_ms=1000.0
    )
    print("  执行成功: ✅")
    print("  置信度: 0.95")
    print("  执行时间: 300ms (快30%)")
    print("  用户满意度: 1.0 (满分)")
    print(f"  计算奖励: {reward:.2f}")

    # 场景2.2: 良好决策
    print("\n👍 场景2.2: 良好决策")
    reward = calculate_q_table_reward(
        success=True,
        confidence=0.8,
        execution_time_ms=800.0,
        user_satisfaction=0.8,
        baseline_time_ms=1000.0
    )
    print("  执行成功: ✅")
    print("  置信度: 0.8")
    print("  执行时间: 800ms")
    print("  用户满意度: 0.8")
    print(f"  计算奖励: {reward:.2f}")

    # 场景2.3: 失败决策
    print("\n❌ 场景2.3: 失败决策")
    reward = calculate_q_table_reward(
        success=False,
        confidence=0.3,
        execution_time_ms=2000.0,  # 很慢
        user_satisfaction=0.2,
        baseline_time_ms=1000.0
    )
    print("  执行成功: ❌")
    print("  置信度: 0.3")
    print("  执行时间: 2000ms (慢100%)")
    print("  用户满意度: 0.2")
    print(f"  计算奖励: {reward:.2f}")

    # 场景2.4: 无满意度反馈
    print("\n📊 场景2.4: 无满意度反馈")
    reward = calculate_q_table_reward(
        success=True,
        confidence=0.9,
        execution_time_ms=500.0,
        user_satisfaction=None,  # 无反馈
        baseline_time_ms=1000.0
    )
    print("  执行成功: ✅")
    print("  置信度: 0.9")
    print("  执行时间: 500ms")
    print("  用户满意度: 无反馈")
    print(f"  计算奖励: {reward:.2f}")


# =============================================================================
# 示例3: 安全获取Q值
# =============================================================================

def example_get_q_values():
    """示例3: 安全获取Q值"""
    print("\n" + "=" * 80)
    print("示例3: 安全获取Q值")
    print("=" * 80)

    # 场景3.1: None接口（防御性编程）
    print("\n🛡️ 场景3.1: None接口处理")
    q_values = get_q_values_from_orchestrator(
        learning_interface=None,  # 传入None
        state="test_state",
        options=["a", "b", "c"]
    )
    print("  输入: learning_interface=None")
    print(f"  输出: {q_values} (安全返回空字典)")

    # 场景3.2: 缺少orchestrator属性
    print("\n🛡️ 场景3.2: 缺少orchestrator属性")
    class FakeInterface:
        pass

    interface = FakeInterface()
    q_values = get_q_values_from_orchestrator(
        learning_interface=interface,
        state="test_state",
        options=["a", "b", "c"]
    )
    print("  输入: FakeInterface (无orchestrator属性)")
    print(f"  输出: {q_values} (安全返回空字典)")

    # 场景3.3: 与ε-贪婪选择配合
    print("\n🔗 场景3.3: 完整决策流程")
    options = ["tool_a", "tool_b", "tool_c"]
    state = "decision_search"

    # 安全获取Q值
    q_values = get_q_values_from_orchestrator(
        learning_interface=None,
        state=state,
        options=options
    )

    # 即使Q值为空，也能正常选择
    selected, confidence = epsilon_greedy_select(
        options=options,
        q_values=q_values,
        epsilon=0.1
    )

    print(f"  状态: {state}")
    print(f"  选项: {options}")
    print(f"  Q值: {q_values if q_values else '(空，触发探索)'}")
    print(f"  选择: {selected}")
    print(f"  置信度: {confidence:.2f}")


# =============================================================================
# 示例4: 完整决策流程
# =============================================================================

class SimpleDecisionAgent:
    """简单决策智能体示例"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        # 模拟Q表（实际应该从学习接口获取）
        self.q_table = {}

    def make_decision(self, context: dict, options: list) -> tuple:
        """做出决策"""
        # 1. 构建状态
        state = self._build_state(context)

        # 2. 获取Q值
        q_values = self._get_q_values(state, options)

        # 3. ε-贪婪选择
        selected, confidence = epsilon_greedy_select(
            options=options,
            q_values=q_values,
            epsilon=0.1
        )

        return selected, confidence

    def learn_from_result(self, decision: str, result: dict) -> float:
        """从结果中学习"""
        # 计算奖励
        reward = calculate_q_table_reward(
            success=result.get("success", False),
            confidence=result.get("confidence", 0.5),
            execution_time_ms=result.get("execution_time_ms", 1000),
            user_satisfaction=result.get("user_satisfaction"),
        )

        # 更新Q表（简化版）
        state = self._build_state(result.get("context", {}))
        current_q = self.q_table.get((state, decision), 0.0)

        # Q学习更新公式: Q(s,a) = Q(s,a) + α * (reward - Q(s,a))
        alpha = 0.1  # 学习率
        new_q = current_q + alpha * (reward - current_q)
        self.q_table[(state, decision)] = new_q

        return reward

    def _build_state(self, context: dict) -> str:
        """构建状态标识"""
        task_type = context.get("task_type", "general")
        return f"decision_{task_type}"

    def _get_q_values(self, state: str, options: list) -> dict:
        """获取Q值"""
        return {option: self.q_table.get((state, option), 0.0) for option in options}


def example_complete_workflow():
    """示例4: 完整决策工作流"""
    print("\n" + "=" * 80)
    print("示例4: 完整决策工作流")
    print("=" * 80)

    # 创建智能体
    agent = SimpleDecisionAgent("example_agent")

    # 模拟任务
    tasks = [
        {"task_type": "search", "query": "搜索专利信息"},
        {"task_type": "analysis", "query": "分析专利数据"},
        {"task_type": "generation", "query": "生成专利报告"},
    ]

    available_tools = ["search_tool", "analysis_tool", "generate_tool"]

    print("\n📝 执行多个任务并学习:")
    print("-" * 80)

    for i, task in enumerate(tasks, 1):
        print(f"\n任务{i}: {task['query']}")
        print(f"类型: {task['task_type']}")

        # 做出决策
        selected, confidence = agent.make_decision(task, available_tools)
        print(f"选择工具: {selected}")
        print(f"置信度: {confidence:.2f}")

        # 模拟执行结果
        is_correct_tool = selected == f"{task['task_type']}_tool"

        result = {
            "success": is_correct_tool,
            "confidence": confidence,
            "execution_time_ms": 500.0 if is_correct_tool else 1500.0,
            "user_satisfaction": 0.9 if is_correct_tool else 0.3,
            "context": task
        }

        # 从结果中学习
        reward = agent.learn_from_result(selected, result)
        print(f"执行结果: {'✅ 成功' if result['success'] else '❌ 失败'}")
        print(f"获得奖励: {reward:.2f}")

    # 显示学习后的Q表
    print("\n📊 学习后的Q表:")
    print("-" * 80)
    for (state, action), q_value in sorted(agent.q_table.items()):
        print(f"  {state:20} + {action:15} = Q值: {q_value:.3f}")


# =============================================================================
# 主函数
# =============================================================================

def main():
    """运行所有示例"""
    print("\n" + "=" * 80)
    print("🧪 学习引擎工具函数使用示例")
    print("=" * 80)

    # 运行所有示例
    example_epsilon_greedy()
    example_reward_calculation()
    example_get_q_values()
    example_complete_workflow()

    print("\n" + "=" * 80)
    print("✅ 所有示例运行完成!")
    print("=" * 80)


if __name__ == "__main__":
    main()
