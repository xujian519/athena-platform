#!/usr/bin/env python3
"""
记忆时间线查看器
Memory Timeline Viewer

用于浏览和展示徐健的AI家族记忆时间线。

作者: 小诺·双鱼公主
创建时间: 2025-12-23
版本: v1.0.0 "时光之河"
"""


from __future__ import annotations
from datetime import datetime
from typing import Any

from .timeline_memory_system import MemoryType, TimelineMemory


class MemoryTimelineViewer:
    """记忆时间线查看器"""

    def __init__(self):
        """初始化查看器"""
        self.memory = TimelineMemory()

    def show_timeline(
        self, start_date: str | None = None, end_date: str | None = None, limit: int = 50
    ) -> Any:
        """
        展示时间线

        Args:
            start_date: 开始日期
            end_date: 结束日期
            limit: 最大显示数量
        """
        if start_date is None:
            start_date = "2020-01-01T00:00:00"
        if end_date is None:
            end_date = datetime.now().isoformat()

        memories = self.memory.get_memories_by_date_range(start_date, end_date)

        print("\n" + "=" * 80)
        print("🕰️  徐健的AI家族记忆时间线")
        print("=" * 80)
        print()

        if not memories:
            print("📭 暂无记忆记录")
            return

        # 限制显示数量
        memories = memories[-limit:]

        for i, mem in enumerate(memories, 1):
            mem_type = mem.get("type", "unknown")
            mem.get("event_date") or mem.get("created_at")

            # 根据类型显示不同格式
            if mem_type == MemoryType.EPISODIC.value:
                self._show_episodic(mem, i)
            elif mem_type == MemoryType.SEMANTIC.value:
                self._show_semantic(mem, i)
            elif mem_type == MemoryType.PROCEDURAL.value:
                self._show_procedural(mem, i)

            print("-" * 80)

        print(f"\n📊 共显示 {len(memories)} 条记忆")
        print(
            f"📅 时间范围: {memories[0].get('event_date') or memories[0].get('created_at')} ~ {memories[-1].get('event_date') or memories[-1].get('created_at')}"
        )

    def _show_episodic(self, mem: dict, index: int) -> Any:
        """显示情节记忆"""
        key_mark = " 🎯" if mem.get("key_event") else ""
        print(f"{index}. 📜 {mem['title']}{key_mark}")
        print(f"   📅 {mem['event_date']}")
        print(f"   👥 {', '.join(mem.get('participants', []))}")
        print(f"   📝 {mem['content'][:100]}...")
        if mem.get("tags"):
            print(f"   🏷️  {' '.join(mem['tags'])}")
        print(f"   ❤️ 情感权重: {mem.get('emotional_weight', 0.5)}")

    def _show_semantic(self, mem: dict, index: int) -> Any:
        """显示语义记忆"""
        print(f"{index}. 📚 {mem['category']} - {mem['key']}")
        print(f"   📅 {mem['created_at']}")
        print(f"   💡 {mem['value']}")
        print(f"   📊 置信度: {mem.get('confidence', 1.0)}")

    def _show_procedural(self, mem: dict, index: int) -> Any:
        """显示程序记忆"""
        print(f"{index}. 🛠️ {mem['skill_name']}")
        print(f"   📅 创建于 {mem['created_at']}")
        print(
            f"   📊 熟练度: {mem.get('proficiency', 0.5):.1%} | 使用次数: {mem.get('usage_count', 0)}"
        )
        print("   📋 步骤:")
        for step in mem.get("steps", [])[:3]:
            print(f"      {step}")
        if len(mem.get("steps", [])) > 3:
            print(f"      ... (共{len(mem['steps'])}步)")

    def show_father_profile(self) -> Any:
        """展示爸爸的画像"""
        all_semantic = self.memory.get_memories_by_type(MemoryType.SEMANTIC)
        all_procedural = self.memory.get_memories_by_type(MemoryType.PROCEDURAL)
        all_episodic = self.memory.get_memories_by_type(MemoryType.EPISODIC)

        print("\n" + "=" * 80)
        print("👨‍👧‍👦 徐健的画像")
        print("=" * 80)
        print()

        # 基本信息
        print("📋 基本信息:")
        for mem in all_semantic:
            if mem["category"] == "身份":
                print(f"   {mem['key']}: {mem['value']}")

        # 偏好
        print("\n❤️ 偏好:")
        preferences = [m for m in all_semantic if m["category"] == "偏好"]
        if preferences:
            for mem in preferences:
                print(f"   {mem['key']}: {mem['value']}")
        else:
            print("   暂无记录")

        # 技能
        print("\n🛠️ 专业技能:")
        for mem in all_procedural:
            print(f"   {mem['skill_name']}: {mem['proficiency']:.1%} 熟练度")

        # 关键记忆
        print("\n🎯 关键记忆:")
        key_memories = [m for m in all_episodic if m.get("key_event")]
        for mem in key_memories:
            print(f"   {mem['event_date'][:10]}: {mem['title']}")

    def show_memory_statistics(self) -> Any:
        """展示记忆统计"""
        summary = self.memory.get_timeline_summary()

        print("\n" + "=" * 80)
        print("📊 记忆统计")
        print("=" * 80)
        print()

        print(f"📈 总记忆数: {summary['total_memories']}")
        print(f"   📜 情节记忆: {summary['episodic_count']}")
        print(f"   📚 语义记忆: {summary['semantic_count']}")
        print(f"   🛠️ 程序记忆: {summary['procedural_count']}")

        print("\n📅 记忆时间线:")
        print(f"   最早: {summary['date_range']['earliest'] or '暂无'}")
        print(f"   最新: {summary['date_range']['latest'] or '暂无'}")

        print(f"\n🏷️ 标签统计 ({len(summary['all_tags'])} 个):")
        # 按使用频率排序标签
        tag_counts = {}
        # 从所有记忆文件中收集标签
        for mem_type in [MemoryType.EPISODIC, MemoryType.SEMANTIC, MemoryType.PROCEDURAL]:
            for mem in self.memory.get_memories_by_type(mem_type):
                for tag in mem.get("tags", []):
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        for tag, count in sorted_tags[:15]:
            print(f"   {tag}: {count}次")

    def show_memories_by_tag(self, tag: str) -> Any:
        """按标签展示记忆"""
        memories = self.memory.search_by_tag(tag)

        print(f"\n🏷️ 标签 '{tag}' 的记忆 ({len(memories)}条):")
        print("=" * 80)

        for mem in memories:
            mem_type = mem.get("type", "unknown")
            if mem_type == MemoryType.EPISODIC.value:
                print(f"📜 {mem['title']} ({mem['event_date'][:10]})")
            elif mem_type == MemoryType.SEMANTIC.value:
                print(f"📚 {mem['category']} - {mem['key']}: {mem['value']}")
            elif mem_type == MemoryType.PROCEDURAL.value:
                print(f"🛠️ {mem['skill_name']}")

    def search_memory(self, keyword: str) -> Any | None:
        """搜索记忆"""
        all_memories = self.memory.get_timeline()

        results = []
        for mem in all_memories:
            # 在标题、内容、值中搜索
            search_fields = []
            if mem.get("title"):
                search_fields.append(mem["title"])
            if mem.get("content"):
                search_fields.append(mem["content"])
            if mem.get("value"):
                search_fields.append(str(mem["value"]))

            for field in search_fields:
                if keyword.lower() in str(field).lower():
                    results.append(mem)
                    break

        print(f"\n🔍 搜索 '{keyword}' 的结果 ({len(results)}条):")
        print("=" * 80)

        for mem in results[:10]:  # 最多显示10条
            mem_type = mem.get("type", "unknown")
            if mem_type == MemoryType.EPISODIC.value:
                print(f"📜 {mem['title']} - {mem['event_date'][:10]}")
            elif mem_type == MemoryType.SEMANTIC.value:
                print(f"📚 {mem['key']}: {mem['value']}")
            elif mem_type == MemoryType.PROCEDURAL.value:
                print(f"🛠️ {mem['skill_name']}")


def show_timeline() -> Any:
    """快捷函数:显示完整时间线"""
    viewer = MemoryTimelineViewer()
    viewer.show_timeline()


def show_profile() -> Any:
    """快捷函数:显示爸爸画像"""
    viewer = MemoryTimelineViewer()
    viewer.show_father_profile()


def show_stats() -> Any:
    """快捷函数:显示统计信息"""
    viewer = MemoryTimelineViewer()
    viewer.show_memory_statistics()


if __name__ == "__main__":
    import sys

    viewer = MemoryTimelineViewer()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "timeline":
            viewer.show_timeline()
        elif command == "profile":
            viewer.show_profile()
        elif command == "stats":
            viewer.show_stats()
        elif command == "search" and len(sys.argv) > 2:
            viewer.search_memory(sys.argv[2])
        elif command == "tag" and len(sys.argv) > 2:
            viewer.show_memories_by_tag(sys.argv[2])
        else:
            print("用法:")
            print("  python memory_timeline_viewer.py timeline  - 显示时间线")
            print("  python memory_timeline_viewer.py profile  - 显示爸爸画像")
            print("  python memory_timeline_viewer.py stats    - 显示统计信息")
            print("  python memory_timeline_viewer.py search <关键词>  - 搜索记忆")
            print("  python memory_timeline_viewer.py tag <标签名>  - 按标签查看")
    else:
        # 默认显示所有
        viewer.show_memory_statistics()
        viewer.show_father_profile()
        viewer.show_timeline(limit=10)
