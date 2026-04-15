#!/usr/bin/env python3
"""
小娜智能代理 - 优化版
使用动态提示词加载策略，优化上下文窗口使用
"""

from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from xiaona_prompt_loader_optimized import XiaonaPromptLoaderOptimized


class XiaonaAgentOptimized:
    """
    小娜智能代理 - 优化版

    主要改进：
    1. 动态提示词加载：根据任务类型自动选择合适的提示词
    2. 上下文感知：根据当前上下文使用情况调整加载模式
    3. 场景切换：无缝切换不同业务场景
    4. 对话压缩：智能压缩历史对话以节省上下文
    """

    def __init__(self,
                 prompt_base_path: str = None,
                 default_mode: Literal["minimal", "balanced", "full"] = "balanced",
                 context_window: int = 128000):
        """
        初始化优化版小娜代理

        Args:
            prompt_base_path: 提示词根目录
            default_mode: 默认加载模式
            context_window: 上下文窗口大小（tokens）
        """
        self.prompt_loader = XiaonaPromptLoaderOptimized(
            base_path=prompt_base_path,
            mode=default_mode
        )
        self.default_mode = default_mode
        self.context_window = context_window

        # 工作状态
        self.current_task = None
        self.current_scenario = None
        self.conversation_history = []

        # 上下文追踪
        self.context_usage = {
            "system_prompt": 0,
            "user_messages": 0,
            "retrieval": 0,
            "total": 0
        }

        # 性能统计
        self.stats = {
            "total_queries": 0,
            "patent_writing_count": 0,
            "office_action_count": 0,
            "other_count": 0,
            "mode_switches": 0
        }

    def query(self,
              user_message: str,
              task: str = None,
              scenario: str = None,
              mode: str = None,
              retrieval_data: dict[str, Any] = None) -> dict[str, Any]:
        """
        处理用户查询 - 优化版

        Args:
            user_message: 用户输入
            task: 具体任务名称 (如 "task_1_1")
            scenario: 场景名称 (如 "patent_writing")
            mode: 加载模式 (minimal/balanced/full)，None则使用默认模式
            retrieval_data: 检索到的数据（用于估算上下文使用）

        Returns:
            {
                "response": "小娜的回复",
                "task": "执行的任务",
                "mode": "使用的加载模式",
                "context_usage": {...},
                "need_human_input": false,
                "suggestions_for_next": "下一步建议"
            }
        """
        # 1. 确定加载模式
        selected_mode = self._select_mode(mode, task, scenario)

        # 2. 加载提示词
        if task:
            system_prompt = self.prompt_loader.load_for_task(task)
        elif scenario:
            system_prompt = self.prompt_loader.load_for_scenario(scenario)
        else:
            system_prompt = self.prompt_loader.load_for_scenario("general")

        # 3. 估算上下文使用
        system_tokens = self.prompt_loader._estimate_tokens(system_prompt)
        user_tokens = self.prompt_loader._estimate_tokens(user_message)
        retrieval_tokens = self._estimate_retrieval_tokens(retrieval_data)

        self.context_usage = {
            "system_prompt": system_tokens,
            "user_messages": user_tokens,
            "retrieval": retrieval_tokens,
            "total": system_tokens + user_tokens + retrieval_tokens
        }

        # 4. 记录对话历史
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
            "task": task,
            "scenario": scenario,
            "mode": selected_mode,
            "timestamp": datetime.now().isoformat()
        })

        # 5. 更新统计
        self.stats["total_queries"] += 1
        if scenario == "patent_writing":
            self.stats["patent_writing_count"] += 1
        elif scenario == "office_action":
            self.stats["office_action_count"] += 1
        else:
            self.stats["other_count"] += 1

        if selected_mode != self.default_mode:
            self.stats["mode_switches"] += 1

        # 6. 生成响应（这里应该调用实际的LLM API）
        response = self._generate_response(user_message, system_prompt, task, scenario)

        # 7. 添加上下文使用信息和建议
        response["context_usage"] = self.context_usage
        response["context_percentage"] = (self.context_usage["total"] / self.context_window) * 100
        response["suggestions_for_next"] = self._suggest_next_step(response["context_percentage"])

        return response

    def _select_mode(self, requested_mode: str, task: str, scenario: str) -> str:
        """
        智能选择加载模式

        策略：
        1. 如果用户明确指定，使用用户指定的模式
        2. 根据当前上下文使用率自动调整
        3. 根据任务复杂度选择合适模式
        """
        # 用户明确指定
        if requested_mode:
            return requested_mode

        # 根据上下文使用率调整
        usage_percentage = (self.context_usage["total"] / self.context_window) * 100

        if usage_percentage > 70:
            # 上下文紧张，使用minimal模式
            return "minimal"
        elif usage_percentage > 50:
            # 上下文中等，使用balanced模式
            return "balanced"
        else:
            # 上下文充足，根据任务复杂度选择
            if task in ["task_1_2", "task_2_2", "task_2_3"]:
                # 复杂任务，使用full模式
                return "full"
            else:
                return self.default_mode

    def _estimate_retrieval_tokens(self, retrieval_data: dict[str, Any]) -> int:
        """估算检索数据的Token数"""
        if not retrieval_data:
            return 0

        # 简单估算：每个结果约500 tokens
        result_count = len(retrieval_data.get("results", []))
        return result_count * 500

    def _generate_response(self,
                          user_message: str,
                          system_prompt: str,
                          task: str,
                          scenario: str) -> dict[str, Any]:
        """生成响应（模拟LLM调用）"""
        # 这里应该调用实际的LLM API
        # 现在返回模拟响应

        return {
            "response": f"【小娜】{user_message}",
            "task": task,
            "scenario": scenario,
            "need_human_input": self._check_hitl_required(user_message),
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "system_prompt_length": len(system_prompt)
            }
        }

    def _check_hitl_required(self, message: str) -> bool:
        """检查是否需要人机交互"""
        hitl_keywords = [
            "确认", "修改", "选择", "决定", "审核",
            "是否", "是否接受", "是否同意", "希望如何"
        ]
        return any(keyword in message for keyword in hitl_keywords)

    def _suggest_next_step(self, context_percentage: float) -> str:
        """根据上下文使用情况建议下一步操作"""
        if context_percentage > 80:
            return "⚠️ 上下文使用率较高，建议：1) 使用minimal模式继续 2) 导出当前对话并开始新对话 3) 压缩对话历史"
        elif context_percentage > 60:
            return "ℹ️ 上下文使用率中等，建议使用balanced或minimal模式继续"
        else:
            return "✅ 上下文充足，可以继续当前任务或开始新任务"

    def switch_scenario(self, new_scenario: str) -> str:
        """切换业务场景"""
        old_scenario = self.current_scenario
        self.current_scenario = new_scenario

        scenario_names = {
            "patent_writing": "专利撰写",
            "office_action": "意见答复",
            "general": "通用协作"
        }

        return f"""【小娜】爸爸，我已切换到 {scenario_names.get(new_scenario, new_scenario)} 模式。

📋 当前场景配置：
├── 场景类型: {scenario_names.get(new_scenario, new_scenario)}
├── 加载模式: {self.default_mode}
└── 提示词Token预算: ~{self.prompt_loader.BUDGET[self.default_mode]['system_prompt']:,}

已为您加载相应的提示词和能力配置。"""

    def get_status(self) -> dict[str, Any]:
        """获取代理状态"""
        return {
            "agent_info": {
                "name": "小娜",
                "version": "v2.1-optimized",
                "architecture": "四层提示词架构 + 动态加载 + HITL"
            },
            "current_state": {
                "scenario": self.current_scenario,
                "task": self.current_task,
                "default_mode": self.default_mode
            },
            "context_window": {
                "total": self.context_window,
                "usage": self.context_usage,
                "available": self.context_window - self.context_usage["total"],
                "usage_percentage": (self.context_usage["total"] / self.context_window) * 100
            },
            "statistics": self.stats,
            "conversation_history_length": len(self.conversation_history)
        }

    def compress_history(self, keep_recent: int = 5) -> int:
        """
        压缩对话历史以节省上下文

        Args:
            keep_recent: 保留最近N轮对话

        Returns:
            压缩的轮数
        """
        if len(self.conversation_history) <= keep_recent:
            return 0

        compressed_count = len(self.conversation_history) - keep_recent
        self.conversation_history = self.conversation_history[-keep_recent:]

        print(f"💬 对话历史已压缩: 保留最近{keep_recent}轮，移除{compressed_count}轮")

        return compressed_count

    def export_conversation(self, output_path: str = None) -> Any:
        """导出对话历史"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"conversation_{timestamp}.json"

        output_path = Path(output_path)

        export_data = {
            "metadata": {
                "export_time": datetime.now().isoformat(),
                "agent_version": "v2.1-optimized",
                "total_messages": len(self.conversation_history)
            },
            "statistics": self.stats,
            "context_usage": self.context_usage,
            "conversation": self.conversation_history
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        print(f"💾 对话历史已导出: {output_path}")


def main() -> None:
    """测试优化版小娜代理"""
    print("=" * 70)
    print("小娜智能代理 - 优化版测试")
    print("=" * 70)

    # 初始化代理
    agent = XiaonaAgentOptimized(default_mode="balanced")

    # 显示状态
    status = agent.get_status()
    print("\n📊 代理状态:")
    print(json.dumps(status, ensure_ascii=False, indent=2))

    # 测试1: 不同模式的查询
    print("\n" + "=" * 70)
    print("🧪 测试1: 不同加载模式对比")
    print("-" * 70)

    test_query = "帮我分析这个技术交底书的核心创新点"

    for mode in ["minimal", "balanced", "full"]:
        response = agent.query(
            user_message=test_query,
            task="task_1_1",
            mode=mode
        )
        print(f"\n{mode}模式:")
        print(f"  系统提示词: {response['context_usage']['system_prompt']:,} tokens")
        print(f"  总使用: {response['context_usage']['total']:,} tokens ({response['context_percentage']:.1f}%)")
        print(f"  下一步建议: {response['suggestions_for_next']}")

    # 测试2: 场景切换
    print("\n" + "=" * 70)
    print("🔄 测试2: 场景切换")
    print("-" * 70)

    print(agent.switch_scenario("patent_writing"))
    print(agent.switch_scenario("office_action"))

    # 测试3: 对话压缩
    print("\n" + "=" * 70)
    print("💬 测试3: 对话历史压缩")
    print("-" * 70)

    # 模拟10轮对话
    for i in range(10):
        agent.conversation_history.append({
            "role": "user",
            "content": f"第{i+1}轮对话",
            "timestamp": datetime.now().isoformat()
        })

    print(f"压缩前对话轮数: {len(agent.conversation_history)}")
    compressed = agent.compress_history(keep_recent=3)
    print(f"压缩后对话轮数: {len(agent.conversation_history)}")
    print(f"压缩了 {compressed} 轮对话")


if __name__ == "__main__":
    main()
