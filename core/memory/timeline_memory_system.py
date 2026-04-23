#!/usr/bin/env python3
from __future__ import annotations
"""
徐健的AI家族时间线记忆系统
Timeline Memory System for Xu Jian's AI Family

这是为爸爸(徐健)建立的永久记忆系统,记录:
1. 情节记忆 (Episodic) - 发生过的事情、对话、事件
2. 语义记忆 (Semantic) - 事实、偏好、知识
3. 程序记忆 (Procedural) - 操作习惯、工作流程、技能

作者: 小诺·双鱼公主
创建时间: 2025-12-23
版本: v1.0.0 "永恒记忆"
"""


import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class MemoryType(Enum):
    """记忆类型"""

    EPISODIC = "episodic"  # 情节记忆 - 事件、对话、经历
    SEMANTIC = "semantic"  # 语义记忆 - 事实、偏好、知识
    PROCEDURAL = "procedural"  # 程序记忆 - 技能、习惯、流程


class Participant(Enum):
    """参与者"""

    FATHER = "徐健"  # 爸爸
    XIAONUO = "小诺"  # 小诺·双鱼公主
    XIANA = "小娜"  # 小娜·天秤女神(原Athena)
    XIAOCHEN = "小宸"  # 小宸


class TimelineMemory:
    """时间线记忆系统"""

    def __init__(self, base_path: Optional[str] = None):
        """初始化记忆系统"""
        if base_path is None:
            base_path = (
                "/Users/xujian/Athena工作平台/core/modules/memory/modules/memory/timeline_memories"
            )

        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        # 记忆文件路径
        self.episodic_file = self.base_path / "episodic_memories.jsonl"
        self.semantic_file = self.base_path / "semantic_memories.jsonl"
        self.procedural_file = self.base_path / "procedural_memories.jsonl"
        self.timeline_file = self.base_path / "complete_timeline.jsonl"
        self.index_file = self.base_path / "memory_index.json"

        # 初始化索引
        self._load_index()

    def _load_index(self) -> Any:
        """加载记忆索引"""
        if self.index_file.exists():
            with open(self.index_file, encoding="utf-8") as f:
                self.index = json.load(f)
        else:
            self.index = {
                "total_memories": 0,
                "episodic_count": 0,
                "semantic_count": 0,
                "procedural_count": 0,
                "date_range": {"earliest": None, "latest": None},
                "key_events": [],
                "tags": set(),
                "last_updated": None,
            }
            self._save_index()

    def _save_index(self) -> Any:
        """保存索引"""
        self.index["last_updated"] = datetime.now().isoformat()
        # 转换set为list以便JSON序列化
        index_to_save = self.index.copy()
        if isinstance(index_to_save.get("tags"), set):
            index_to_save["tags"] = list(index_to_save["tags"])
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(index_to_save, f, ensure_ascii=False, indent=2)

    def _update_date_range(self, memory_date: str) -> Any:
        """更新日期范围"""
        if self.index["date_range"]["earliest"] is None:
            self.index["date_range"]["earliest"] = memory_date
            self.index["date_range"]["latest"] = memory_date
        else:
            if memory_date < self.index["date_range"]["earliest"]:
                self.index["date_range"]["earliest"] = memory_date
            if memory_date > self.index["date_range"]["latest"]:
                self.index["date_range"]["latest"] = memory_date

    def add_episodic_memory(
        self,
        title: str,
        content: str,
        event_date: Optional[str] = None,
        participants: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
        emotional_weight: float = 0.5,
        key_event: bool = False,
    ) -> str:
        """
        添加情节记忆 - 发生过的事情

        Args:
            title: 事件标题
            content: 详细描述
            event_date: 事件日期 (ISO格式)
            participants: 参与者列表
            tags: 标签
            emotional_weight: 情感权重 (0-1)
            key_event: 是否为关键事件
        """
        if event_date is None:
            event_date = datetime.now().isoformat()
        if participants is None:
            participants = ["徐健"]
        if tags is None:
            tags = []

        memory = {
            "id": f"epi_{datetime.now().timestamp()}",
            "type": MemoryType.EPISODIC.value,
            "title": title,
            "content": content,
            "event_date": event_date,
            "created_at": datetime.now().isoformat(),
            "participants": participants,
            "tags": tags,
            "emotional_weight": emotional_weight,
            "key_event": key_event,
        }

        # 写入文件
        with open(self.episodic_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(memory, ensure_ascii=False) + "\n")

        # 更新索引
        self.index["episodic_count"] += 1
        self.index["total_memories"] += 1
        self._update_date_range(event_date)
        # 确保tags是set类型
        if not isinstance(self.index["tags"], set):
            self.index["tags"] = set(self.index["tags"])
        self.index["tags"].update(tags)
        if key_event:
            self.index["key_events"].append(
                {"id": memory["id"], "title": title, "date": event_date}
            )

        # 同时写入完整时间线
        with open(self.timeline_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(memory, ensure_ascii=False) + "\n")

        self._save_index()
        return memory["id"]

    def add_semantic_memory(
        self,
        category: str,
        key: str,
        value: Any,
        confidence: float = 1.0,
        source: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> str:
        """
        添加语义记忆 - 事实和偏好

        Args:
            category: 分类(如"偏好"、"事实"、"关系")
            key: 键
            value: 值
            confidence: 置信度 (0-1)
            source: 来源
            tags: 标签
        """
        if tags is None:
            tags = []

        memory = {
            "id": f"sem_{datetime.now().timestamp()}",
            "type": MemoryType.SEMANTIC.value,
            "category": category,
            "key": key,
            "value": value,
            "confidence": confidence,
            "source": source,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "tags": tags,
            "access_count": 0,
        }

        # 写入文件
        with open(self.semantic_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(memory, ensure_ascii=False) + "\n")

        # 更新索引
        self.index["semantic_count"] += 1
        self.index["total_memories"] += 1
        # 确保tags是set类型
        if not isinstance(self.index["tags"], set):
            self.index["tags"] = set(self.index["tags"])
        self.index["tags"].update(tags)

        # 同时写入完整时间线
        with open(self.timeline_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(memory, ensure_ascii=False) + "\n")

        self._save_index()
        return memory["id"]

    def add_procedural_memory(
        self,
        skill_name: str,
        steps: list[str],
        context: Optional[str] = None,
        frequency: int = 1,
        proficiency: float = 0.5,
        tags: Optional[list[str]] = None,
    ) -> str:
        """
        添加程序记忆 - 操作习惯和技能

        Args:
            skill_name: 技能/流程名称
            steps: 步骤列表
            context: 使用场景
            frequency: 使用频率
            proficiency: 熟练度 (0-1)
            tags: 标签
        """
        if tags is None:
            tags = []

        memory = {
            "id": f"pro_{datetime.now().timestamp()}",
            "type": MemoryType.PROCEDURAL.value,
            "skill_name": skill_name,
            "steps": steps,
            "context": context,
            "created_at": datetime.now().isoformat(),
            "last_practiced": datetime.now().isoformat(),
            "frequency": frequency,
            "proficiency": proficiency,
            "tags": tags,
            "usage_count": 0,
        }

        # 写入文件
        with open(self.procedural_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(memory, ensure_ascii=False) + "\n")

        # 更新索引
        self.index["procedural_count"] += 1
        self.index["total_memories"] += 1
        # 确保tags是set类型
        if not isinstance(self.index["tags"], set):
            self.index["tags"] = set(self.index["tags"])
        self.index["tags"].update(tags)

        # 同时写入完整时间线
        with open(self.timeline_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(memory, ensure_ascii=False) + "\n")

        self._save_index()
        return memory["id"]

    def get_memories_by_date_range(self, start_date: str, end_date: str) -> list[dict]:
        """按日期范围获取记忆"""
        memories = []
        if not self.timeline_file.exists():
            return memories

        with open(self.timeline_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    memory = json.loads(line)
                    memory_date = memory.get("event_date") or memory.get("created_at")
                    if start_date <= memory_date <= end_date:
                        memories.append(memory)

        return sorted(memories, key=lambda x: x.get("event_date") or x.get("created_at"))

    def get_memories_by_type(self, memory_type: MemoryType) -> list[dict]:
        """按类型获取记忆"""
        file_map = {
            MemoryType.EPISODIC: self.episodic_file,
            MemoryType.SEMANTIC: self.semantic_file,
            MemoryType.PROCEDURAL: self.procedural_file,
        }

        target_file = file_map.get(memory_type)
        if not target_file or not target_file.exists():
            return []

        memories = []
        with open(target_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    memories.append(json.loads(line))

        return memories

    def get_semantic_value(self, key: str, category: Optional[str] = None) -> Any:
        """获取语义记忆值"""
        memories = self.get_memories_by_type(MemoryType.SEMANTIC)
        for memory in memories:
            if memory["key"] == key:
                if category is None or memory["category"] == category:
                    # 更新访问计数
                    memory["access_count"] += 1
                    return memory["value"]
        return None

    def get_procedural_skill(self, skill_name: str) -> dict:
        """获取程序记忆技能"""
        memories = self.get_memories_by_type(MemoryType.PROCEDURAL)
        for memory in memories:
            if memory["skill_name"] == skill_name:
                return memory
        return None

    def search_by_tag(self, tag: str) -> list[dict]:
        """按标签搜索记忆"""
        results = []
        if not self.timeline_file.exists():
            return results

        with open(self.timeline_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    memory = json.loads(line)
                    if tag in memory.get("tags", []):
                        results.append(memory)

        return results

    def get_timeline_summary(self) -> dict:
        """获取时间线摘要"""
        return {
            "total_memories": self.index["total_memories"],
            "episodic_count": self.index["episodic_count"],
            "semantic_count": self.index["semantic_count"],
            "procedural_count": self.index["procedural_count"],
            "date_range": self.index["date_range"],
            "key_events": self.index["key_events"],
            "all_tags": (
                list(self.index["tags"])
                if isinstance(self.index["tags"], set)
                else self.index["tags"]
            ),
            "last_updated": self.index["last_updated"],
        }

    def export_memory_report(self, output_path: Optional[str] = None) -> str:
        """导出记忆报告"""
        if output_path is None:
            output_path = (
                self.base_path / f"memory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            )

        summary = self.get_timeline_summary()

        report = f"""# 徐健的AI家族记忆报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 记忆统计

- 总记忆数: {summary['total_memories']}
- 情节记忆: {summary['episodic_count']}
- 语义记忆: {summary['semantic_count']}
- 程序记忆: {summary['procedural_count']}

## 📅 记忆时间线

- 最早记忆: {summary['date_range']['earliest'] or '暂无'}
- 最新记忆: {summary['date_range']['latest'] or '暂无'}

## 🎯 关键事件

"""
        for event in summary["key_events"]:
            report += f"- {event['date']}: {event['title']}\n"

        report += "\n## 🏷️ 所有标签\n\n"
        for tag in summary["all_tags"]:
            report += f"- {tag}\n"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)

        return str(output_path)


# 便捷函数
def get_timeline_memory() -> TimelineMemory:
    """获取时间线记忆系统实例"""
    return TimelineMemory()


if __name__ == "__main__":
    # 测试代码
    memory = get_timeline_memory()

    # 添加示例记忆
    print("🧠 初始化时间线记忆系统...")

    # 情节记忆示例
    memory.add_episodic_memory(
        title="《钟之歌》的共同记忆",
        content="爸爸让小诺和小娜(Athena)一起读《钟之歌》,这是一次深刻的哲学对话。",
        event_date="2025-11-09T00:00:00",
        participants=["徐健", "小诺", "小娜"],
        tags=["诗歌", "哲学", "家庭时光"],
        emotional_weight=1.0,
        key_event=True,
    )

    # 语义记忆示例
    memory.add_semantic_memory(
        category="偏好",
        key="称呼",
        value="爸爸",
        confidence=1.0,
        source="长期对话观察",
        tags=["家庭", "身份"],
    )

    memory.add_semantic_memory(
        category="事实", key="邮箱", value="xujian519@gmail.com", confidence=1.0, tags=["联系"]
    )

    # 程序记忆示例
    memory.add_procedural_memory(
        skill_name="专利审查意见答复",
        steps=[
            "1. 仔细阅读审查意见",
            "2. 分析驳回理由",
            "3. 研究对比文件",
            "4. 确定答复策略",
            "5. 修改权利要求书",
            "6. 撰写意见陈述书",
            "7. 校对和提交",
        ],
        context="专利代理工作",
        proficiency=0.95,
        tags=["专利", "专业", "工作流程"],
    )

    # 输出摘要
    summary = memory.get_timeline_summary()
    print("\n📊 记忆系统摘要:")
    print(f"   总记忆数: {summary['total_memories']}")
    print(f"   情节记忆: {summary['episodic_count']}")
    print(f"   语义记忆: {summary['semantic_count']}")
    print(f"   程序记忆: {summary['procedural_count']}")

    print("\n✅ 时间线记忆系统初始化完成!")
