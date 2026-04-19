#!/usr/bin/env python3
from __future__ import annotations
"""
小诺记忆系统集成
Xiaonuo Memory Integration

将智能体身份记忆集成到小诺的响应系统中
"""

import sys
from pathlib import Path
from typing import Any

# 添加项目路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from core.memory.agent_identity_memory import (
    get_agent_identity,
    get_identity_memory,
)


class XiaonuoMemoryHelper:
    """小诺记忆助手"""

    def __init__(self):
        self.memory = get_identity_memory()
        self.recent_reminders = {}  # 记录最近的提醒,避免重复

    def process_message(self, message: str) -> dict[str, Any]:
        """处理消息,检查是否需要提醒"""
        result = {
            "original_message": message,
            "has_reminder": False,
            "reminders": [],
            "corrected_message": message,
            "agent_mentions": [],
        }

        # 检查消息中的智能体提及
        message_lower = message.lower()


        # 检查其他智能体
        agent_keywords = {
            "小宸": "xiaochen",
            "xiaochen": "xiaochen",
            "小辰": "xiaochen_memory",
            "xiaochen_memory": "xiaochen_memory",
        }

        for keyword, key in agent_keywords.items():
            if keyword in message_lower:
                identity = get_agent_identity(key)
                if "error" not in identity:
                    result["agent_mentions"].append(
                        {
                            "name": identity.get("name"),
                            "chinese_name": identity.get("chinese_name"),
                            "role": identity.get("role"),
                            "status": identity.get("status"),
                        }
                    )

        return result

    def _should_remind(self, key: str) -> bool:
        """判断是否应该提醒"""
        # 如果最近5分钟内提醒过,不再提醒
        import time

        last_reminder = self.recent_reminders.get(key, 0)
        return time.time() - last_reminder > 300

    def _record_reminder(self, key: str) -> Any:
        """记录提醒时间"""
        import time

        self.recent_reminders[key] = time.time()

    def get_agent_summary(self) -> str:
        """获取智能体摘要(供小诺使用)"""
        agents = self.memory.get_agent_list()

        summary = "🤖 Athena平台智能体列表:\n"
        summary += "=" * 40 + "\n"

        for agent in agents:
            if agent["important"]:
                star = "⭐"
                status_emoji = "✅" if agent["status"] == "active" else "🔧"
            else:
                star = "  "
                status_emoji = {"development": "🔨", "planned": "📋", "active": "✅"}.get(
                    agent["status"], "❓"
                )

            summary += f"{star} {status_emoji} {agent['name']} ({agent['chinese_name']})\n"
            summary += f"   角色: {agent['role']}\n"
            if agent["port"]:
                summary += f"   端口: {agent['port']}\n"
            summary += "\n"

        # 特别提醒

        return summary

    def suggest_correction(self, wrong_name: str) -> str | None:
        """建议名称纠正"""
        corrections = {
            "yun-pat": "YunPat",
            "yun pat": "YunPat",
        }

        return corrections.get(wrong_name.lower())


# 全局实例
_memory_helper = None


def get_memory_helper() -> XiaonuoMemoryHelper:
    """获取小诺记忆助手"""
    global _memory_helper
    if _memory_helper is None:
        _memory_helper = XiaonuoMemoryHelper()
    return _memory_helper


# 导入到小诺系统的函数
def xiaonuo_check_agent_names(message: str) -> dict[str, Any]:
    """小诺检查智能体名称(主入口函数)"""
    helper = get_memory_helper()
    return helper.process_message(message)


def xiaonuo_get_agent_info() -> str:
    """小诺获取智能体信息"""
    helper = get_memory_helper()
    return helper.get_agent_summary()


if __name__ == "__main__":
    # 测试集成
    print("🧪 小诺记忆集成测试")
    print("=" * 50)

    helper = get_memory_helper()

    # 测试消息处理
    test_messages = [
        "请调用YunPat进行专利分析",
        "云夕智能体状态如何?",
        "yun-pat能帮我处理专利吗?",
        "小宸和小辰有什么区别?",
    ]

    for msg in test_messages:
        print(f"\n📝 输入: {msg}")
        result = helper.process_message(msg)

        if result["has_reminder"]:
            print("⚠️ 提醒:")
            for reminder in result["reminders"]:
                print(f"   {reminder}")

        if result["agent_mentions"]:
            print("🤖 提及的智能体:")
            for mention in result["agent_mentions"]:
                print(f"   - {mention}")

    print("\n" + "=" * 50)
    print(helper.get_agent_summary())
