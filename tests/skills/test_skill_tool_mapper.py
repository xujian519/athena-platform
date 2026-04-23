#!/usr/bin/env python3
"""
Skills系统单元测试 - SkillToolMapper

测试技能与工具的映射关系。

作者: Athena平台团队
创建时间: 2026-04-21
"""

import pytest

from core.skills.registry import SkillRegistry
from core.skills.tool_mapper import SkillToolMapper
from core.skills.types import SkillCategory, SkillDefinition


def test_map_tools_to_skills():
    """测试工具到技能的映射"""
    # Arrange - 创建注册表和技能
    registry = SkillRegistry()

    skill1 = SkillDefinition(
        id="skill1",
        name="Skill 1",
        category=SkillCategory.SEARCH,
        description="Uses tool1",
        tools=["tool1", "tool2"],
    )

    skill2 = SkillDefinition(
        id="skill2",
        name="Skill 2",
        category=SkillCategory.ANALYSIS,
        description="Uses tool2 and tool3",
        tools=["tool2", "tool3"],
    )

    registry.register(skill1)
    registry.register(skill2)

    # Act - 创建映射器
    mapper = SkillToolMapper(registry)
    tool_to_skills = mapper.map_tools_to_skills()

    # Assert
    assert "tool1" in tool_to_skills
    assert "tool2" in tool_to_skills
    assert "tool3" in tool_to_skills

    # tool1 只被 skill1 使用
    assert len(tool_to_skills["tool1"]) == 1
    assert skill1.id in tool_to_skills["tool1"]

    # tool2 被 skill1 和 skill2 使用
    assert len(tool_to_skills["tool2"]) == 2
    assert skill1.id in tool_to_skills["tool2"]
    assert skill2.id in tool_to_skills["tool2"]

    # tool3 只被 skill2 使用
    assert len(tool_to_skills["tool3"]) == 1
    assert skill2.id in tool_to_skills["tool3"]


def test_get_tools_for_skill():
    """测试获取技能所需的工具"""
    # Arrange
    registry = SkillRegistry()
    skill = SkillDefinition(
        id="test_skill",
        name="Test Skill",
        category=SkillCategory.SEARCH,
        description="Test",
        tools=["tool1", "tool2", "tool3"],
    )
    registry.register(skill)

    mapper = SkillToolMapper(registry)

    # Act
    tools = mapper.get_tools_for_skill("test_skill")

    # Assert
    assert tools == ["tool1", "tool2", "tool3"]


def test_get_tools_for_nonexistent_skill():
    """测试获取不存在技能的工具"""
    # Arrange
    registry = SkillRegistry()
    mapper = SkillToolMapper(registry)

    # Act
    tools = mapper.get_tools_for_skill("nonexistent")

    # Assert
    assert tools == []


def test_get_skills_for_tool():
    """测试获取使用某工具的所有技能"""
    # Arrange
    registry = SkillRegistry()

    skill1 = SkillDefinition(
        id="skill1",
        name="Skill 1",
        category=SkillCategory.SEARCH,
        description="Test",
        tools=["tool1", "tool2"],
    )

    skill2 = SkillDefinition(
        id="skill2",
        name="Skill 2",
        category=SkillCategory.ANALYSIS,
        description="Test",
        tools=["tool2", "tool3"],
    )

    skill3 = SkillDefinition(
        id="skill3",
        name="Skill 3",
        category=SkillCategory.WRITING,
        description="Test",
        tools=["tool3"],
    )

    registry.register(skill1)
    registry.register(skill2)
    registry.register(skill3)

    mapper = SkillToolMapper(registry)

    # Act - 获取使用 tool2 的技能
    skills = mapper.get_skills_for_tool("tool2")

    # Assert
    assert len(skills) == 2
    assert skill1 in skills
    assert skill2 in skills
    assert skill3 not in skills


def test_get_skills_for_nonexistent_tool():
    """测试获取不存在工具的技能"""
    # Arrange
    registry = SkillRegistry()
    mapper = SkillToolMapper(registry)

    # Act
    skills = mapper.get_skills_for_tool("nonexistent_tool")

    # Assert
    assert skills == []


def test_detect_tool_conflicts():
    """测试检测工具冲突"""
    # Arrange - 创建两个技能声明使用相同工具的不同版本
    registry = SkillRegistry()

    skill1 = SkillDefinition(
        id="skill1",
        name="Skill 1",
        category=SkillCategory.SEARCH,
        description="Test",
        tools=["tool1@v1", "tool2"],
    )

    skill2 = SkillDefinition(
        id="skill2",
        name="Skill 2",
        category=SkillCategory.ANALYSIS,
        description="Test",
        tools=["tool1@v2", "tool3"],
    )

    registry.register(skill1)
    registry.register(skill2)

    mapper = SkillToolMapper(registry)

    # Act
    conflicts = mapper.detect_tool_conflicts()

    # Assert
    assert len(conflicts) > 0
    # tool1 存在版本冲突
    conflict_tools = [c["tool"] for c in conflicts]
    assert "tool1" in conflict_tools


def test_detect_tool_dependencies():
    """测试检测工具依赖"""
    # Arrange - skill3 依赖 skill1 和 skill2 的工具
    registry = SkillRegistry()

    skill1 = SkillDefinition(
        id="skill1",
        name="Skill 1",
        category=SkillCategory.SEARCH,
        description="Test",
        tools=["tool1"],
    )

    skill2 = SkillDefinition(
        id="skill2",
        name="Skill 2",
        category=SkillCategory.ANALYSIS,
        description="Test",
        tools=["tool2"],
    )

    skill3 = SkillDefinition(
        id="skill3",
        name="Skill 3",
        category=SkillCategory.COORDINATION,
        description="Test",
        tools=["tool1", "tool2", "tool3"],  # 依赖 skill1 和 skill2
    )

    registry.register(skill1)
    registry.register(skill2)
    registry.register(skill3)

    mapper = SkillToolMapper(registry)

    # Act
    dependencies = mapper.detect_tool_dependencies()

    # Assert
    assert "skill3" in dependencies
    # skill3 依赖 skill1 和 skill2
    deps_for_skill3 = dependencies["skill3"]
    assert "skill1" in deps_for_skill3 or "tool1" in str(deps_for_skill3)


def test_get_tool_usage_stats():
    """测试获取工具使用统计"""
    # Arrange
    registry = SkillRegistry()

    # tool1 被3个技能使用
    for i in range(3):
        skill = SkillDefinition(
            id=f"skill_{i}",
            name=f"Skill {i}",
            category=SkillCategory.SEARCH,
            description="Test",
            tools=["tool1"],
        )
        registry.register(skill)

    # tool2 被1个技能使用
    skill = SkillDefinition(
        id="skill_3",
        name="Skill 3",
        category=SkillCategory.ANALYSIS,
        description="Test",
        tools=["tool2"],
    )
    registry.register(skill)

    mapper = SkillToolMapper(registry)

    # Act
    stats = mapper.get_tool_usage_stats()

    # Assert
    assert stats["tool1"]["count"] == 3
    assert stats["tool2"]["count"] == 1
    assert stats["tool1"]["skill_ids"] == ["skill_0", "skill_1", "skill_2"]
    assert stats["tool2"]["skill_ids"] == ["skill_3"]


def test_find_unused_tools():
    """测试查找未使用的工具"""
    # Arrange
    registry = SkillRegistry()

    skill = SkillDefinition(
        id="skill1",
        name="Skill 1",
        category=SkillCategory.SEARCH,
        description="Test",
        tools=["tool1", "tool2"],
    )

    registry.register(skill)

    mapper = SkillToolMapper(registry)

    # Act - 声明有 tool1, tool2, tool3, tool4
    all_tools = ["tool1", "tool2", "tool3", "tool4"]
    unused = mapper.find_unused_tools(all_tools)

    # Assert
    assert "tool1" not in unused
    assert "tool2" not in unused
    assert "tool3" in unused
    assert "tool4" in unused


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

