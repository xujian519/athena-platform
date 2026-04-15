#!/usr/bin/env python3
"""
小娜自然语言交互系统
支持通过自然语言指令与提示词系统交互
"""

from __future__ import annotations
import re
from datetime import datetime
from typing import Any

from xiaona_agent_optimized import XiaonaAgentOptimized


class XiaonaNaturalInterface:
    """
    小娜自然语言交互界面

    支持的自然语言指令类型：
    1. 任务执行: "帮我分析这个技术交底书"
    2. 场景切换: "切换到专利撰写模式"
    3. 问题解答: "A26.4是什么要求？"
    4. 状态查询: "当前状态怎么样？"
    5. 系统控制: "压缩对话历史"
    """

    # 任务关键词映射
    TASK_KEYWORDS = {
        # 专利撰写任务
        "理解技术交底|分析交底|交底书": "task_1_1",
        "检索现有技术|调研现有技术|对比分析|检索对比文件": "task_1_2",
        "撰写说明书|写说明书": "task_1_3",
        "撰写权利要求|写权利要求|起草权利要求": "task_1_4",
        "撰写摘要|写摘要|整理申请文件": "task_1_5",

        # 意见答复任务
        "解读审查意见|分析审查意见|看审查意见": "task_2_1",
        "分析驳回理由|分析驳回|为什么驳回": "task_2_2",
        "制定答复策略|答复策略|怎么答复": "task_2_3",
        "撰写答复|写答复|写意见陈述": "task_2_4",
    }

    # 场景关键词映射
    SCENARIO_KEYWORDS = {
        "专利撰写|撰写专利|写专利|申请专利": "patent_writing",
        "意见答复|答复审查意见|审查意见答复|答复审查员": "office_action",
        "通用|一般|综合": "general",
    }

    # 模式关键词映射
    MODE_KEYWORDS = {
        "最简|最小|精简|快速": "minimal",
        "平衡|标准|正常": "balanced",
        "完整|详细|全面": "full",
    }

    # 控制指令关键词
    CONTROL_KEYWORDS = {
        "状态|当前状态|怎么样": "get_status",
        "压缩对话|压缩历史|清理历史": "compress_history",
        "导出对话|保存对话|导出历史": "export_conversation",
        "重置对话|清空对话|新对话": "reset_conversation",
        "帮助|help|怎么用|使用说明": "show_help",
    }

    def __init__(self, context_window: int = 128000):
        """初始化自然语言交互界面"""
        self.agent = XiaonaAgentOptimized(default_mode="balanced", context_window=context_window)
        self.interaction_history = []

        print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║  🌟 小娜 - 专利法律AI助手 🌟                                  ║
║                                                              ║
║  您可以直接用自然语言与我对话，例如：                          ║
║  • "帮我分析这个技术交底书"                                    ║
║  • "切换到专利撰写模式"                                        ║
║  • "审查员说权利要求1没有创造性，怎么办？"                      ║
║  • "当前状态怎么样？"                                          ║
║  • 输入"帮助"查看更多指令                                      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)

    def chat(self, user_input: str) -> str:
        """
        处理用户自然语言输入

        Args:
            user_input: 用户的自然语言输入

        Returns:
            小娜的回复
        """
        # 记录交互历史
        self.interaction_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })

        # 1. 检查控制指令
        control_result = self._check_control_commands(user_input)
        if control_result:
            response = control_result
        else:
            # 2. 解析用户意图
            intent = self._parse_intent(user_input)

            # 3. 执行相应操作
            if intent["type"] == "switch_scenario":
                response = self._handle_scenario_switch(intent["scenario"])
            elif intent["type"] == "execute_task":
                response = self._handle_task_execution(user_input, intent)
            elif intent["type"] == "question":
                response = self._handle_question(user_input, intent)
            else:
                response = self._handle_general_query(user_input)

        # 记录回复
        self.interaction_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })

        return response

    def _parse_intent(self, user_input: str) -> dict[str, Any]:
        """解析用户意图"""
        user_input_lower = user_input.lower()

        # 1. 检查场景切换意图
        for keywords, scenario in self.SCENARIO_KEYWORDS.items():
            if re.search(keywords, user_input_lower):
                return {"type": "switch_scenario", "scenario": scenario}

        # 2. 检查任务执行意图
        for keywords, task in self.TASK_KEYWORDS.items():
            if re.search(keywords, user_input_lower):
                # 确定模式
                mode = self._detect_mode(user_input)
                return {"type": "execute_task", "task": task, "mode": mode}

        # 3. 检查问题意图
        question_indicators = ["是什么", "什么是", "怎么", "如何", "为什么", "？", "?", "吗", "呢"]
        if any(indicator in user_input for indicator in question_indicators):
            return {"type": "question", "query": user_input}

        # 4. 默认为一般查询
        return {"type": "general", "query": user_input}

    def _detect_mode(self, user_input: str) -> str:
        """检测用户指定的模式"""
        user_input_lower = user_input.lower()

        for keywords, mode in self.MODE_KEYWORDS.items():
            if re.search(keywords, user_input_lower):
                return mode

        return None  # 使用默认模式

    def _check_control_commands(self, user_input: str) -> str | None:
        """检查控制指令"""
        user_input_lower = user_input.lower()

        for keywords, command in self.CONTROL_KEYWORDS.items():
            if re.search(keywords, user_input_lower):
                return self._execute_control_command(command)

        return None

    def _execute_control_command(self, command: str) -> str:
        """执行控制指令"""
        if command == "get_status":
            status = self.agent.get_status()
            return self._format_status(status)

        elif command == "compress_history":
            compressed = self.agent.compress_history(keep_recent=5)
            return f"""【小娜】爸爸，对话历史已压缩。

💬 压缩结果：
├── 保留最近: 5轮对话
└── 移除历史: {compressed}轮对话

现在有更多上下文空间可以继续对话了。"""

        elif command == "export_conversation":
            self.agent.export_conversation()
            return "【小娜】爸爸，对话历史已导出到当前目录。"

        elif command == "reset_conversation":
            self.agent.reset_conversation()
            return """【小娜】爸爸，对话历史已重置。

🆕 我们可以开始全新的对话了。
📋 您现在可以：
   • 提出一个新的任务
   • 切换到特定场景
   • 询问任何专利法律问题"""

        elif command == "show_help":
            return self._show_help()

        return None

    def _handle_scenario_switch(self, scenario: str) -> str:
        """处理场景切换"""
        scenario_names = {
            "patent_writing": "专利撰写",
            "office_action": "意见答复",
            "general": "通用协作"
        }

        return self.agent.switch_scenario(scenario)

    def _handle_task_execution(self, user_input: str, intent: dict) -> str:
        """处理任务执行"""
        task = intent["task"]
        mode = intent.get("mode")

        # 确定场景
        if task.startswith("task_1_"):
            scenario = "patent_writing"
        elif task.startswith("task_2_"):
            scenario = "office_action"
        else:
            scenario = "general"

        # 执行查询
        response = self.agent.query(
            user_message=user_input,
            task=task,
            scenario=scenario,
            mode=mode
        )

        # 格式化响应
        return self._format_task_response(response)

    def _handle_question(self, user_input: str, intent: dict) -> str:
        """处理问题解答"""
        # 尝试识别问题类型并加载相应能力
        question_lower = user_input.lower()

        # 法律条文问题
        if any(keyword in question_lower for keyword in ["a26.3", "a26.4", "a22.3", "法条", "专利法"]):
            response = self.agent.query(
                user_message=user_input,
                task="task_2_1",  # 使用审查意见分析任务（包含法条检索）
                mode="minimal"
            )
            return self._format_question_response(response)

        # 技术分析问题
        elif any(keyword in question_lower for keyword in ["技术方案", "创新点", "技术问题"]):
            response = self.agent.query(
                user_message=user_input,
                task="task_1_1",
                mode="minimal"
            )
            return self._format_question_response(response)

        # 通用问题
        else:
            return f"""【小娜】爸爸，关于您的问题：" {user_input} "

我需要更多信息来准确回答您。您可以：
1. 提供具体的技术交底书或审查意见
2. 描述具体的场景或任务
3. 或者输入"帮助"查看我可以做什么

💡 例如：
   - "帮我分析这个技术交底书：[粘贴内容]"
   - "审查员说权利要求1没有创造性（A22.3），我该怎么答复？"
"""

    def _handle_general_query(self, user_input: str) -> str:
        """处理一般查询"""
        # 尝试作为通用问题处理
        return self._handle_question(user_input, {"query": user_input})

    def _format_task_response(self, response: dict) -> str:
        """格式化任务执行响应"""
        context_info = f"""
📊 上下文使用情况：
├── 系统提示词: {response['context_usage']['system_prompt']:,} tokens
├── 用户输入: {response['context_usage']['user_messages']:,} tokens
├── 检索数据: {response['context_usage']['retrieval']:,} tokens
├── 总计: {response['context_usage']['total']:,} tokens ({response['context_percentage']:.1f}%)
└── 剩余空间: {128000 - response['context_usage']['total']:,} tokens

💡 建议: {response['suggestions_for_next']}
"""

        hitl_info = ""
        if response.get("need_human_input"):
            hitl_info = """

🤝 【需要您的确认】

这个操作需要您的决策才能继续。请选择：
A. 同意执行
B. 需要调整
C. 我来提供具体内容
"""

        return f"""{response['response']}{context_info}{hitl_info}

{'─' * 70}

您可以继续：
• 补充更多信息
• 提出相关问题
• 输入"状态"查看当前状态
• 输入"帮助"查看更多指令"""

    def _format_question_response(self, response: dict) -> str:
        """格式化问题解答响应"""
        return f"""{response['response']}

{'─' * 70}

💡 您可以：
• 继续追问相关问题
• 提供更多细节让我更准确地回答
• 输入"帮助"查看我能做什么"""

    def _format_status(self, status: dict) -> str:
        """格式化状态信息"""
        return f"""【小娜】爸爸，这是我的当前状态：

📋 代理信息
├── 姓名: {status['agent_info']['name']}
├── 版本: {status['agent_info']['version']}
└── 架构: {status['agent_info']['architecture']}

🎯 当前状态
├── 场景: {status['current_state']['scenario'] or '未设置'}
├── 任务: {status['current_state']['task'] or '未设置'}
└── 默认模式: {status['current_state']['default_mode']}

📊 上下文窗口
├── 总容量: {status['context_window']['total']:,} tokens
├── 已使用: {status['context_window']['usage']['total']:,} tokens ({status['context_window']['usage_percentage']:.1f}%)
└── 可用空间: {status['context_window']['available']:,} tokens

📈 统计信息
├── 总查询: {status['statistics']['total_queries']} 次
├── 专利撰写: {status['statistics']['patent_writing_count']} 次
├── 意见答复: {status['statistics']['office_action_count']} 次
└── 模式切换: {status['statistics']['mode_switches']} 次

💬 对话历史: {status['conversation_history_length']} 轮

{'─' * 70}

💡 您可以：
• 输入任务指令，如"帮我分析技术交底书"
• 输入"帮助"查看更多可用指令
• 输入"切换到XX模式"切换场景"""

    def _show_help(self) -> str:
        """显示帮助信息"""
        return """【小娜】爸爸，以下是我能帮您做的事情：

📝 任务类指令

专利撰写场景：
├── "帮我分析这个技术交底书"
├── "检索相关的现有技术"
├── "撰写说明书"
├── "撰写权利要求书"
└── "撰写摘要"

意见答复场景：
├── "帮我分析这个审查意见"
├── "分析驳回理由"
├── "制定答复策略"
└── "撰写答复文件"

🔄 场景切换指令

├── "切换到专利撰写模式"
├── "切换到意见答复模式"
└── "切换到通用模式"

🔍 问题解答指令

├── "A26.4是什么要求？"
├── "什么是三步法？"
├── "怎么判断创造性？"
└── 其他专利法律问题

⚙️ 系统控制指令

├── "状态" - 查看当前状态
├── "压缩对话历史" - 节省上下文空间
├── "导出对话" - 保存对话记录
├── "重置对话" - 开始新对话
└── "帮助" - 显示本帮助信息

💡 使用技巧：

1. 可以用自然语言描述您的需求
   例如："审查员说我的权利要求1没有创造性，引用了D1和D2，我该怎么办？"

2. 可以指定模式以控制上下文使用
   例如："用最简模式快速检查一下这个权利要求是否清楚"

3. 可以粘贴实际内容进行分析
   例如："帮我分析这个技术交底书：[然后粘贴内容]"

{'─' * 70}

现在，请告诉我您需要什么帮助？"""

    def interactive_loop(self) -> Any:
        """启动交互式对话循环"""
        print("\n🌟 小娜已准备就绪，您可以开始对话了！")
        print("💡 输入'帮助'查看可用指令，输入'退出'或'quit'结束对话\n")

        while True:
            try:
                # 获取用户输入
                user_input = input("\n您: ").strip()

                # 检查退出指令
                if not user_input or user_input.lower() in ["退出", "exit", "quit", "q"]:
                    print("\n【小娜】爸爸，再见！👋")
                    break

                # 处理输入并获取回复
                response = self.chat(user_input)

                # 显示回复
                print(f"\n小娜: {response}")

            except KeyboardInterrupt:
                print("\n\n【小娜】爸爸，检测到中断请求。")
                choice = input("您是想退出还是继续？(退出/继续): ").strip().lower()
                if choice in ["退出", "exit", "q"]:
                    print("\n【小娜】爸爸，再见！👋")
                    break
                else:
                    print("\n继续对话...")
                    continue

            except Exception as e:
                print(f"\n❌ 发生错误: {e}")
                print("💡 您可以尝试重新表述您的问题，或输入'帮助'查看可用指令")


def main() -> None:
    """主函数"""
    interface = XiaonaNaturalInterface()
    interface.interactive_loop()


if __name__ == "__main__":
    main()
