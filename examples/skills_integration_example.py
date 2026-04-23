#!/usr/bin/env python3
"""
Skills系统集成示例

展示如何在Agent中使用Skills系统。

作者: Athena平台团队
创建时间: 2026-04-21
"""
from __future__ import annotations

import logging

from core.framework.agents.base_agent import BaseAgent
from core.skills.loader import SkillLoader
from core.skills.registry import SkillRegistry
from core.skills.tool_mapper import SkillToolMapper
from core.skills.types import SkillCategory

logger = logging.getLogger(__name__)


class SkillEnabledAgent(BaseAgent):
    """启用技能的Agent基类

    提供技能管理、选择和执行能力。
    """

    def __init__(self, name: str):
        """初始化Agent

        Args:
            name: Agent名称
        """
        super().__init__(name, role="SkillEnabledAgent")

        # 初始化技能系统
        self.skill_registry = SkillRegistry()
        self.skill_loader = SkillLoader(self.skill_registry)
        self.tool_mapper = SkillToolMapper(self.skill_registry)

        # 加载内置技能
        self._load_builtin_skills()

        logger.info(f"✅ {self.name} 技能系统已初始化")

    def _load_builtin_skills(self) -> None:
        """加载内置技能"""
        try:
            skills = self.skill_loader.load_from_directory(
                "core/skills/bundled",
                recursive=False,
                register=True,
            )
            logger.info(f"📚 {self.name} 加载了 {len(skills)} 个技能")
        except Exception as e:
            logger.error(f"❌ 加载技能失败: {e}")

    def select_skill_by_task(
        self,
        task_description: str,
        task_type: str | None = None,
    ) -> str | None:
        """根据任务描述选择技能

        Args:
            task_description: 任务描述
            task_type: 任务类型（可选）

        Returns:
            str | None: 技能ID
        """
        # 基于关键词的简单匹配
        if "专利" in task_description:
            if "分析" in task_description:
                return "patent_analysis"
        elif "案例" in task_description:
            if "检索" in task_description or "搜索" in task_description:
                return "case_retrieval"
        elif "文书" in task_description or "文档" in task_description:
            return "document_writing"
        elif "协调" in task_description or "多任务" in task_description:
            return "task_coordination"

        # 默认返回协调技能
        return "task_coordination"

    def execute_skill(
        self,
        skill_id: str,
        **_kwargs  # noqa: ARG001,
    ) -> dict[str, any]:
        """执行技能

        Args:
            skill_id: 技能ID
            **_kwargs  # noqa: ARG001: 传递给工具的参数

        Returns:
            dict: 执行结果
        """
        # 获取技能
        skill = self.skill_registry.get_skill(skill_id)
        if not skill:
            logger.error(f"❌ 技能不存在: {skill_id}")
            return {}

        logger.info(f"🎯 {self.name} 执行技能: {skill.name}")

        # 执行技能的工具
        results = {}
        for tool_id in skill.tools:
            try:
                # 这里需要与实际的工具系统集成
                # 示例：模拟工具执行
                results[tool_id] = {
                    "status": "success",
                    "data": f"Tool {tool_id} executed",
                }
                logger.debug(f"  ✅ 工具 {tool_id} 执行成功")
            except Exception as e:
                logger.error(f"  ❌ 工具 {tool_id} 执行失败: {e}")
                results[tool_id] = {
                    "status": "error",
                    "error": str(e),
                }

        return {
            "skill_id": skill_id,
            "skill_name": skill.name,
            "results": results,
        }

    def analyze_skills_usage(self) -> dict[str, any]:
        """分析技能使用情况

        Returns:
            dict: 分析报告
        """
        stats = self.skill_registry.get_stats()
        tool_usage = self.tool_mapper.get_tool_usage_stats()
        conflicts = self.tool_mapper.detect_tool_conflicts()
        dependencies = self.tool_mapper.detect_tool_dependencies()

        return {
            "total_skills": stats["total_skills"],
            "by_category": stats["by_category"],
            "tool_usage": tool_usage,
            "conflicts": conflicts,
            "dependencies": dependencies,
        }


class XiaonaAgentWithSkills(SkillEnabledAgent):
    """小娜Agent - 集成Skills系统"""

    def __init__(self):
        """初始化小娜"""
        super().__init__("小娜")
        self.role = "法律专家"

    def process(self, input_text: str) -> str:
        """处理用户输入（实现抽象方法）

        Args:
            input_text: 用户输入

        Returns:
            str: 处理结果
        """
        # 选择技能
        skill_id = self.select_skill_by_task(
            task_description=input_text,
        )

        # 执行技能
        result = self.execute_skill(
            skill_id=skill_id,
            input_text=input_text,
        )

        # 返回结果
        return f"已使用 {result['skill_name']} 处理您的请求"

    def process_patent_task(self, patent_id: str, task_type: str) -> dict[str, any]:
        """处理专利相关任务

        Args:
            patent_id: 专利ID
            task_type: 任务类型（analysis/retrieval/writing）

        Returns:
            dict: 处理结果
        """
        task_description = f"专利{task_type}任务"

        # 选择技能
        skill_id = self.select_skill_by_task(
            task_description=task_description,
            task_type=task_type,
        )

        # 执行技能
        result = self.execute_skill(
            skill_id=skill_id,
            patent_id=patent_id,
        )

        return result

    def get_patent_analysis_skills(self) -> list[str]:
        """获取所有专利分析相关技能"""
        skills = self.skill_registry.list_skills(
            category=SkillCategory.ANALYSIS,
        )
        return [s.id for s in skills]


def demo_basic_usage():
    """演示基本使用"""
    print("=" * 60)
    print("演示1: 基本使用")
    print("=" * 60)

    # 创建Agent
    agent = XiaonaAgentWithSkills()

    # 列出所有技能
    all_skills = agent.skill_registry.list_skills()
    print(f"\n📚 可用技能 ({len(all_skills)}个):")
    for skill in all_skills:
        print(f"  - {skill.id}: {skill.name} ({skill.category.value})")

    # 按类别列出
    analysis_skills = agent.skill_registry.list_skills(
        category=SkillCategory.ANALYSIS,
    )
    print(f"\n🔍 分析类技能 ({len(analysis_skills)}个):")
    for skill in analysis_skills:
        print(f"  - {skill.name}")

    # 获取技能详情
    patent_skill = agent.skill_registry.get_skill("patent_analysis")
    if patent_skill:
        print("\n📋 专利分析技能详情:")
        print(f"  ID: {patent_skill.id}")
        print(f"  名称: {patent_skill.name}")
        print(f"  描述: {patent_skill.description}")
        print(f"  工具: {', '.join(patent_skill.tools)}")
        print(f"  优先级: {patent_skill.metadata.priority}")


def demo_skill_execution():
    """演示技能执行"""
    print("\n" + "=" * 60)
    print("演示2: 技能执行")
    print("=" * 60)

    # 创建Agent
    agent = XiaonaAgentWithSkills()

    # 执行专利分析技能
    print("\n🎯 执行专利分析技能...")
    result = agent.execute_skill(
        skill_id="patent_analysis",
        patent_id="CN123456789A",
    )

    print("\n结果:")
    print(f"  技能: {result['skill_name']}")
    print("  执行的工具:")
    for tool_id, tool_result in result["results"].items():
        print(f"    - {tool_id}: {tool_result['status']}")


def demo_tool_mapping():
    """演示工具映射"""
    print("\n" + "=" * 60)
    print("演示3: 工具映射")
    print("=" * 60)

    # 创建Agent
    agent = XiaonaAgentWithSkills()

    # 获取技能的工具
    tools = agent.tool_mapper.get_tools_for_skill("patent_analysis")
    print("\n🔧 专利分析技能使用的工具:")
    print(f"  {', '.join(tools)}")

    # 获取工具的技能
    skills = agent.tool_mapper.get_skills_for_tool("patent_search")
    print("\n🔍 使用patent_search的技能:")
    for skill in skills:
        print(f"  - {skill.name}")

    # 工具使用统计
    stats = agent.tool_mapper.get_tool_usage_stats()
    print("\n📊 工具使用统计:")
    for tool_id, stat in stats.items():
        print(f"  {tool_id}: 被 {stat['count']} 个技能使用")


def demo_analysis():
    """演示分析功能"""
    print("\n" + "=" * 60)
    print("演示4: 分析报告")
    print("=" * 60)

    # 创建Agent
    agent = XiaonaAgentWithSkills()

    # 生成分析报告
    report = agent.analyze_skills_usage()

    print("\n📈 技能系统分析报告:")
    print(f"  总技能数: {report['total_skills']}")
    print("  按类别分布:")
    for category, count in report["by_category"].items():
        print(f"    - {category}: {count}个")

    print(f"\n  工具冲突: {len(report['conflicts'])}个")
    for conflict in report["conflicts"]:
        print(f"    - {conflict['tool']}: {conflict['versions']}")

    print(f"\n  技能依赖: {len(report['dependencies'])}个")
    for skill_id, deps in report["dependencies"].items():
        print(f"    - {skill_id} 依赖于: {', '.join(deps)}")


def demo_workflow():
    """演示工作流"""
    print("\n" + "=" * 60)
    print("演示5: 完整工作流")
    print("=" * 60)

    # 创建Agent
    agent = XiaonaAgentWithSkills()

    # 模拟用户任务
    task = "分析专利CN123456789A的创造性"

    print(f"\n📝 用户任务: {task}")

    # 选择技能
    skill_id = agent.select_skill_by_task(task_description=task)
    print(f"🎯 选择技能: {skill_id}")

    # 执行技能
    result = agent.execute_skill(
        skill_id=skill_id,
        patent_id="CN123456789A",
    )

    print("\n✅ 任务完成:")
    print(f"  使用技能: {result['skill_name']}")
    print(f"  执行工具数: {len(result['results'])}")


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # 运行演示
    demo_basic_usage()
    demo_skill_execution()
    demo_tool_mapping()
    demo_analysis()
    demo_workflow()

    print("\n" + "=" * 60)
    print("✅ 所有演示完成！")
    print("=" * 60)
