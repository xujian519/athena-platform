#!/usr/bin/env python3
"""
小娜智能代理 - 生产环境
基于四层提示词架构的专利法律AI助手
"""

from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from xiaona_prompt_loader import XiaonaPromptLoader


class XiaonaAgent:
    """
    小娜智能代理

    集成四层提示词架构：
    - L1: 基础层 (Foundation) - 身份与核心原则
    - L2: 数据层 (Data Layer) - 数据源配置
    - L3: 能力层 (Capability) - 10大核心能力
    - L4: 业务层 (Business) - 9个业务场景
    + HITL: 人机协作协议
    """

    def __init__(self, prompt_base_path: str = None, use_cache: bool = True):
        """
        初始化小娜代理

        Args:
            prompt_base_path: 提示词根目录
            use_cache: 是否使用缓存
        """
        self.prompt_loader = XiaonaPromptLoader(prompt_base_path)
        self.use_cache = use_cache

        # 尝试从缓存加载
        if use_cache and not self.prompt_loader.load_cache():
            # 缓存不存在，加载所有提示词
            self.prompt_loader.load_all_prompts()
            self.prompt_loader.save_cache()
        else:
            # 直接加载
            self.prompt_loader.load_all_prompts()

        # 工作状态
        self.current_task = None
        self.current_scenario = None
        self.conversation_history = []

        # 性能统计
        self.stats = {
            "total_queries": 0,
            "patent_writing_count": 0,
            "office_action_count": 0,
            "other_count": 0
        }

    def get_system_prompt(self, scenario: str = "general") -> str:
        """
        获取指定场景的系统提示词

        Args:
            scenario: 业务场景
                - general: 通用模式
                - patent_writing: 专利撰写模式
                - office_action: 意见答复模式

        Returns:
            完整的系统提示词
        """
        return self.prompt_loader.get_full_prompt(scenario)

    def query(self,
              user_message: str,
              scenario: str = "general",
              context: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        处理用户查询

        Args:
            user_message: 用户输入
            scenario: 业务场景
            context: 上下文信息（可选）

        Returns:
            {
                "response": "小娜的回复",
                "scenario": "使用的场景",
                "need_human_input": false,
                "prompt_tokens": 1234,
                "metadata": {}
            }
        """
        # 更新统计
        self.stats["total_queries"] += 1
        if scenario == "patent_writing":
            self.stats["patent_writing_count"] += 1
        elif scenario == "office_action":
            self.stats["office_action_count"] += 1
        else:
            self.stats["other_count"] += 1

        # 获取系统提示词
        system_prompt = self.get_system_prompt(scenario)

        # 记录对话历史
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
            "scenario": scenario,
            "timestamp": datetime.now().isoformat()
        })

        # 这里应该调用实际的LLM API
        # 返回结构化响应
        response = {
            "response": f"【小娜】{user_message}",  # 实际应该调用LLM
            "scenario": scenario,
            "need_human_input": self._check_hitl_required(user_message, scenario),
            "prompt_tokens": len(system_prompt) + len(user_message),
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "scenario_type": scenario,
                "context": context or {}
            }
        }

        return response

    def _check_hitl_required(self, message: str, scenario: str) -> bool:
        """
        检查是否需要人机交互

        Args:
            message: 用户消息
            scenario: 场景

        Returns:
            是否需要人工输入
        """
        # 关键决策点需要人机交互
        hitl_keywords = [
            "确认", "修改", "选择", "决定", "审核",
            "是否", "是否接受", "是否同意", "希望如何"
        ]

        return any(keyword in message for keyword in hitl_keywords)

    def switch_scenario(self, new_scenario: str) -> str:
        """
        切换业务场景

        Args:
            new_scenario: 新场景 (general/patent_writing/office_action)

        Returns:
            切换确认消息
        """
        old_scenario = self.current_scenario
        self.current_scenario = new_scenario

        return f"""【小娜】爸爸，我已切换到 {self._get_scenario_name(new_scenario)} 模式。

📋 当前场景配置：
├── 场景类型: {self._get_scenario_name(new_scenario)}
├── 可用能力: {self._get_available_capabilities(new_scenario)}
└── 预期任务: {self._get_expected_tasks(new_scenario)}

已为您加载相应的提示词和能力配置。"""

    def _get_scenario_name(self, scenario: str) -> str:
        """获取场景中文名称"""
        names = {
            "general": "通用协作",
            "patent_writing": "专利撰写",
            "office_action": "意见答复"
        }
        return names.get(scenario, scenario)

    def _get_available_capabilities(self, scenario: str) -> str:
        """获取场景可用能力"""
        if scenario == "patent_writing":
            return "技术交底理解、现有技术调研、说明书撰写、权利要求书撰写、摘要撰写"
        elif scenario == "office_action":
            return "审查意见解读、驳回理由分析、答复策略制定、答复文件撰写"
        else:
            return "全部10大核心能力"

    def _get_expected_tasks(self, scenario: str) -> str:
        """获取场景预期任务"""
        if scenario == "patent_writing":
            return "专利申请文件撰写全流程"
        elif scenario == "office_action":
            return "审查意见答复全流程"
        else:
            return "综合专利法律服务"

    def get_status(self) -> dict[str, Any]:
        """
        获取代理状态

        Returns:
            状态信息字典
        """
        return {
            "agent_info": {
                "name": "小娜",
                "version": "v2.0",
                "architecture": "四层提示词架构 + HITL"
            },
            "current_state": {
                "scenario": self.current_scenario,
                "task": self.current_task
            },
            "prompt_system": {
                "version": self.prompt_loader.metadata["version"],
                "last_updated": self.prompt_loader.metadata["last_updated"],
                "total_modules": self.prompt_loader.metadata["total_prompts"]
            },
            "statistics": self.stats,
            "conversation_history_length": len(self.conversation_history)
        }

    def reset_conversation(self) -> Any:
        """重置对话历史"""
        self.conversation_history = []
        self.current_task = None
        print("【小娜】爸爸，对话历史已重置。我们可以开始新的任务了。")

    def export_conversation(self, output_path: str = None) -> Any:
        """
        导出对话历史

        Args:
            output_path: 输出文件路径
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"conversation_{timestamp}.json"

        output_path = Path(output_path)

        export_data = {
            "metadata": {
                "export_time": datetime.now().isoformat(),
                "agent_version": "v2.0",
                "total_messages": len(self.conversation_history)
            },
            "statistics": self.stats,
            "conversation": self.conversation_history
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        print(f"💾 对话历史已导出: {output_path}")


def main() -> None:
    """测试小娜代理"""
    print("=" * 60)
    print("小娜智能代理 - 生产环境测试")
    print("=" * 60)

    # 初始化代理
    agent = XiaonaAgent()

    # 显示状态
    status = agent.get_status()
    print("\n📊 代理状态:")
    print(json.dumps(status, ensure_ascii=False, indent=2))

    # 场景切换测试
    print("\n" + "=" * 60)
    print(agent.switch_scenario("patent_writing"))

    print("\n" + "=" * 60)
    print(agent.switch_scenario("office_action"))

    # 查询测试
    print("\n" + "=" * 60)
    print("🧪 查询测试:")

    test_queries = [
        ("帮我分析这个技术交底书的核心创新点", "patent_writing"),
        ("审查员认为权利要求1不具备创造性，我该怎么答复？", "office_action"),
        ("我需要修改权利要求2，请提供建议", "patent_writing")
    ]

    for query, scenario in test_queries:
        print(f"\n用户: {query}")
        response = agent.query(query, scenario)
        print(f"小娜: {response['response']}")
        print(f"需要人机交互: {response['need_human_input']}")


if __name__ == "__main__":
    main()
