#!/usr/bin/env python3
from __future__ import annotations
"""
记忆记录器 - 自动记录每次对话
Memory Recorder - Auto-record Every Conversation

这是小诺使用的记忆记录工具,每次对话时自动记录记忆。

作者: 小诺·双鱼公主
创建时间: 2025-12-23
版本: v1.0.0 "永恒记录"
"""


from datetime import datetime
from typing import Any

from .timeline_memory_system import MemoryType, TimelineMemory


class MemoryRecorder:
    """记忆记录器 - 小诺的记忆工具"""

    def __init__(self):
        """初始化记忆记录器"""
        self.memory = TimelineMemory()
        self.current_session_start = datetime.now().isoformat()
        self.current_session_messages = []

    def record_conversation(
        self,
        user_input: str,
        xiaonuo_response: str,
        xiana_response: Optional[str] = None,
        emotional_tone: str = "neutral",
    ):
        """
        记录对话

        Args:
            user_input: 爸爸的输入
            xiaonuo_response: 小诺的回应
            xiana_response: 小娜的回应(可选)
            emotional_tone: 情感基调
        """
        timestamp = datetime.now().isoformat()

        # 记录到当前会话
        self.current_session_messages.append(
            {
                "timestamp": timestamp,
                "user": user_input,
                "apps/apps/xiaonuo": xiaonuo_response,
                "xiana": xiana_response,
                "tone": emotional_tone,
            }
        )

        # 提取语义记忆(偏好、事实)
        self._extract_semantic_memories(user_input)

    def _extract_semantic_memories(self, text: str) -> Any:
        """从对话中提取语义记忆"""
        # 提取偏好表达
        preference_keywords = ["我喜欢", "我想要", "我希望", "我觉得", "我倾向"]
        for keyword in preference_keywords:
            if keyword in text:
                # 提取偏好内容
                start = text.find(keyword)
                content = text[start + len(keyword) :].strip()
                if content and len(content) < 100:
                    self.memory.add_semantic_memory(
                        category="偏好",
                        key=f"偏好_{keyword}",
                        value=content,
                        confidence=0.8,
                        source="对话提取",
                        tags=["偏好", "自动提取"],
                    )

        # 提取事实信息
        fact_keywords = ["我是", "我的", "我有", "我在"]
        for keyword in fact_keywords:
            if keyword in text:
                start = text.find(keyword)
                content = text[start + len(keyword) :].strip()
                if content and len(content) < 100:
                    self.memory.add_semantic_memory(
                        category="事实",
                        key=f"事实_{keyword}",
                        value=content,
                        confidence=0.8,
                        source="对话提取",
                        tags=["事实", "自动提取"],
                    )

    def record_key_event(
        self,
        title: str,
        description: str,
        participants: Optional[list[str]] = None,
        emotional_weight: float = 0.7,
    ):
        """
        记录关键事件

        Args:
            title: 事件标题
            description: 事件描述
            participants: 参与者
            emotional_weight: 情感权重
        """
        if participants is None:
            participants = ["徐健", "小诺"]

        return self.memory.add_episodic_memory(
            title=title,
            content=description,
            event_date=datetime.now().isoformat(),
            participants=participants,
            tags=["关键事件", "当前会话"],
            emotional_weight=emotional_weight,
            key_event=True,
        )

    def record_preference(self, key: str, value: str, category: str = "偏好") -> Any:
        """记录偏好"""
        return self.memory.add_semantic_memory(
            category=category,
            key=key,
            value=value,
            confidence=1.0,
            source="用户明确表达",
            tags=["偏好", "重要"],
        )

    def record_skill_practice(
        self, skill_name: str, steps: list[str], context: Optional[str] = None
    ) -> Any:
        """记录技能实践"""
        skill = self.memory.get_procedural_skill(skill_name)
        if skill:
            # 更新现有技能
            skill["last_practiced"] = datetime.now().isoformat()
            skill["usage_count"] += 1
            skill["frequency"] += 1
            # 提高熟练度
            if skill["proficiency"] < 1.0:
                skill["proficiency"] = min(1.0, skill["proficiency"] + 0.01)
        else:
            # 创建新技能
            self.memory.add_procedural_memory(
                skill_name=skill_name,
                steps=steps,
                context=context,
                frequency=1,
                proficiency=0.5,
                tags=["新技能", "实践中"],
            )

    def end_session(self, session_summary: Optional[str] = None) -> Any:
        """
        结束当前会话

        Args:
            session_summary: 会话摘要
        """
        datetime.now().isoformat()

        # 记录会话本身作为一个情节记忆
        if self.current_session_messages:
            title = f"对话会话 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            content = f"会话包含{len(self.current_session_messages)}条对话"
            if session_summary:
                content += f"\n\n摘要: {session_summary}"

            self.memory.add_episodic_memory(
                title=title,
                content=content,
                event_date=self.current_session_start,
                participants=["徐健", "小诺"],
                tags=["对话会话", "日常"],
                emotional_weight=0.5,
            )

        # 清空当前会话
        self.current_session_messages = []
        self.current_session_start = None

    def query_memory(self, query: str, memory_type: Optional[str] = None) -> list[dict]:
        """
        查询记忆

        Args:
            query: 查询内容
            memory_type: 记忆类型过滤

        Returns:
            匹配的记忆列表
        """
        # 按标签搜索
        results = self.memory.search_by_tag(query)

        # 如果指定了类型,过滤
        if memory_type:
            results = [r for r in results if r["type"] == memory_type]

        return results

    def get_father_preferences(self) -> dict:
        """获取爸爸的所有偏好"""
        all_semantic = self.memory.get_memories_by_type(MemoryType.SEMANTIC)
        preferences = {}
        for mem in all_semantic:
            if mem["category"] == "偏好":
                preferences[mem["key"]] = mem["value"]
        return preferences

    def get_father_profile(self) -> dict:
        """获取爸爸的完整画像"""
        profile = {"基本信息": {}, "偏好": {}, "技能": [], "关键记忆": []}

        # 获取语义记忆
        semantic_memories = self.memory.get_memories_by_type(MemoryType.SEMANTIC)
        for mem in semantic_memories:
            if mem["category"] == "身份":
                profile["基本信息"][mem["key"]] = mem["value"]
            elif mem["category"] == "偏好":
                profile["偏好"][mem["key"]] = mem["value"]

        # 获取程序记忆
        procedural_memories = self.memory.get_memories_by_type(MemoryType.PROCEDURAL)
        for mem in procedural_memories:
            profile["技能"].append(
                {
                    "名称": mem["skill_name"],
                    "熟练度": mem["proficiency"],
                    "使用次数": mem["usage_count"],
                }
            )

        # 获取关键事件
        all_episodic = self.memory.get_memories_by_type(MemoryType.EPISODIC)
        for mem in all_episodic:
            if mem.get("key_event"):
                profile["关键记忆"].append({"日期": mem["event_date"], "标题": mem["title"]})

        return profile

    def export_memory_report(self) -> str:
        """导出记忆报告"""
        return self.memory.export_memory_report()

    def get_timeline(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> list[dict]:
        """
        获取时间线

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            按时间排序的记忆列表
        """
        if start_date is None:
            start_date = "2020-01-01T00:00:00"
        if end_date is None:
            end_date = datetime.now().isoformat()

        return self.memory.get_memories_by_date_range(start_date, end_date)


# 全局单例
_recorder = None


def get_memory_recorder() -> MemoryRecorder:
    """获取全局记忆记录器实例"""
    global _recorder
    if _recorder is None:
        _recorder = MemoryRecorder()
    return _recorder


if __name__ == "__main__":
    # 测试代码
    recorder = get_memory_recorder()

    print("🧠 记忆记录器测试")
    print("=" * 60)

    # 模拟对话记录
    recorder.record_conversation(
        user_input="我想要一份详细的记忆报告",
        xiaonuo_response="好的爸爸,我这就为您生成记忆报告",
        emotional_tone="friendly",
    )

    # 记录偏好
    recorder.record_preference("报告格式", "详细版")

    # 结束会话
    recorder.end_session("爸爸想要了解记忆系统")

    # 获取爸爸画像
    profile = recorder.get_father_profile()

    print("\n📊 爸爸画像:")
    print(f"   基本信息: {len(profile['基本信息'])} 条")
    print(f"   偏好: {len(profile['偏好'])} 条")
    print(f"   技能: {len(profile['技能'])} 项")
    print(f"   关键记忆: {len(profile['关键记忆'])} 个")

    print("\n✅ 记忆记录器测试完成")
