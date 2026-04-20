#!/usr/bin/env python3
"""
Skills系统单元测试

测试SkillRegistry的核心功能。

作者: Athena平台团队
创建时间: 2026-04-21
"""
from __future__ import annotations

import pytest

from core.skills.types import SkillDefinition, SkillCategory, SkillMetadata


def test_register_skill():
    """测试技能注册"""
    # Arrange
    from core.skills.registry import SkillRegistry

    registry = SkillRegistry()
    skill = SkillDefinition(
        id="test_skill",
        name="Test Skill",
        category=SkillCategory.ANALYSIS,
        description="A test skill for unit testing",
        tools=["tool1", "tool2"],
        metadata=SkillMetadata(
            author="Athena Team",
            version="1.0.0",
            tags=["test", "example"],
        ),
    )

    # Act
    registry.register(skill)

    # Assert
    retrieved = registry.get_skill("test_skill")
    assert retrieved is not None
    assert retrieved.id == "test_skill"
    assert retrieved.name == "Test Skill"
    assert retrieved.category == SkillCategory.ANALYSIS
    assert retrieved.description == "A test skill for unit testing"
    assert retrieved.tools == ["tool1", "tool2"]
    assert retrieved.metadata.author == "Athena Team"


def test_register_duplicate_skill_raises_error():
    """测试注册重复技能应抛出错误"""
    from core.skills.registry import SkillRegistry

    registry = SkillRegistry()

    skill1 = SkillDefinition(
        id="dup_skill",
        name="Duplicate Skill",
        category=SkillCategory.ANALYSIS,
        description="First skill",
        tools=[],
    )

    skill2 = SkillDefinition(
        id="dup_skill",
        name="Duplicate Skill 2",
        category=SkillCategory.ANALYSIS,
        description="Second skill",
        tools=[],
    )

    registry.register(skill1)

    # Act & Assert
    with pytest.raises(ValueError, match="already registered"):
        registry.register(skill2)


def test_get_nonexistent_skill():
    """测试获取不存在的技能"""
    from core.skills.registry import SkillRegistry

    registry = SkillRegistry()

    # Act
    result = registry.get_skill("nonexistent_skill")

    # Assert
    assert result is None


def test_list_skills_by_category():
    """测试按类别列出技能"""
    from core.skills.registry import SkillRegistry

    # Arrange
    registry = SkillRegistry()

    skill1 = SkillDefinition(
        id="analysis_skill_1",
        name="Analysis Skill 1",
        category=SkillCategory.ANALYSIS,
        description="Analysis skill 1",
        tools=[],
    )

    skill2 = SkillDefinition(
        id="writing_skill_1",
        name="Writing Skill 1",
        category=SkillCategory.WRITING,
        description="Writing skill 1",
        tools=[],
    )

    skill3 = SkillDefinition(
        id="analysis_skill_2",
        name="Analysis Skill 2",
        category=SkillCategory.ANALYSIS,
        description="Analysis skill 2",
        tools=[],
    )

    # Act
    registry.register(skill1)
    registry.register(skill2)
    registry.register(skill3)

    analysis_skills = registry.list_skills(category=SkillCategory.ANALYSIS)
    all_skills = registry.list_skills()

    # Assert
    assert len(analysis_skills) == 2
    assert analysis_skills[0].id == "analysis_skill_1"
    assert analysis_skills[1].id == "analysis_skill_2"
    assert len(all_skills) == 3


def test_list_all_skills():
    """测试列出所有技能"""
    from core.skills.registry import SkillRegistry

    # Arrange
    registry = SkillRegistry()

    skill1 = SkillDefinition(
        id="skill_a",
        name="Skill A",
        category=SkillCategory.SEARCH,
        description="Skill A",
        tools=[],
    )

    skill2 = SkillDefinition(
        id="skill_b",
        name="Skill B",
        category=SkillCategory.ANALYSIS,
        description="Skill B",
        tools=[],
    )

    # Act
    registry.register(skill1)
    registry.register(skill2)

    skills = registry.list_skills()

    # Assert
    assert len(skills) == 2
    skill_ids = {s.id for s in skills}
    assert skill_ids == {"skill_a", "skill_b"}


def test_unregister_skill():
    """测试注销技能"""
    from core.skills.registry import SkillRegistry

    # Arrange
    registry = SkillRegistry()
    skill = SkillDefinition(
        id="temp_skill",
        name="Temporary Skill",
        category=SkillCategory.SEARCH,
        description="Temporary skill",
        tools=[],
    )
    registry.register(skill)

    # Act
    result = registry.unregister("temp_skill")

    # Assert
    assert result is True
    assert registry.get_skill("temp_skill") is None


def test_find_skills_by_name_pattern():
    """测试按名称模式查找技能"""
    from core.skills.registry import SkillRegistry

    # Arrange
    registry = SkillRegistry()

    skill1 = SkillDefinition(
        id="patent_analysis",
        name="Patent Analysis Skill",
        category=SkillCategory.ANALYSIS,
        description="For patent analysis",
        tools=[],
    )

    skill2 = SkillDefinition(
        id="case_analysis",
        name="Case Analysis Skill",
        category=SkillCategory.ANALYSIS,
        description="For case analysis",
        tools=[],
    )

    registry.register(skill1)
    registry.register(skill2)

    # Act
    results = registry.find_skills(name_pattern="*analysis")

    # Assert
    assert len(results) == 2
    assert all("analysis" in s.name.lower() for s in results)


def test_get_skills_by_tools():
    """测试获取使用指定工具的技能"""
    from core.skills.registry import SkillRegistry

    # Arrange
    registry = SkillRegistry()

    skill1 = SkillDefinition(
        id="skill_with_search",
        name="Search Skill",
        category=SkillCategory.SEARCH,
        description="Search skill",
        tools=["patent_search", "case_search"],
    )

    skill2 = SkillDefinition(
        id="skill_without_search",
        name="Analysis Skill",
        category=SkillCategory.ANALYSIS,
        description="Analysis skill",
        tools=["patent_analyze"],
    )

    registry.register(skill1)
    registry.register(skill2)

    # Act
    skills_with_search = registry.get_skills_by_tool("patent_search")

    # Assert
    assert len(skills_with_search) == 1
    assert skills_with_search[0].id == "skill_with_search"


def test_skill_stats():
    """测试技能统计信息"""
    from core.skills.registry import SkillRegistry

    # Arrange
    registry = SkillRegistry()

    for i in range(3):
        skill = SkillDefinition(
            id=f"skill_{i}",
            name=f"Skill {i}",
            category=SkillCategory.ANALYSIS,
            description=f"Skill {i}",
            tools=[f"tool{i}"],
        )
        registry.register(skill)

    # Act
    stats = registry.get_stats()

    # Assert
    assert stats["total_skills"] == 3
    assert stats["by_category"][SkillCategory.ANALYSIS.value] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
