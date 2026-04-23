#!/usr/bin/env python3
"""
Skills系统单元测试 - SkillLoader

测试SkillLoader的文件加载功能。

作者: Athena平台团队
创建时间: 2026-04-21
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from core.skills.loader import SkillLoader
from core.skills.registry import SkillRegistry
from core.skills.types import SkillCategory


def test_load_from_file():
    """测试从文件加载技能"""
    # Arrange - 创建临时YAML文件
    skill_data = {
        "id": "test_skill",
        "name": "Test Skill",
        "category": "analysis",
        "description": "A test skill",
        "tools": ["tool1", "tool2"],
        "metadata": {
            "author": "Athena Team",
            "version": "1.0.0",
            "tags": ["test"],
        },
    }

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".yaml",
        delete=False,
    ) as f:
        yaml.dump(skill_data, f)
        temp_path = Path(f.name)

    try:
        # Act
        loader = SkillLoader()
        skill = loader.load_from_file(temp_path)

        # Assert
        assert skill is not None
        assert skill.id == "test_skill"
        assert skill.name == "Test Skill"
        assert skill.category == SkillCategory.ANALYSIS
        assert skill.description == "A test skill"
        assert skill.tools == ["tool1", "tool2"]
        assert skill.metadata.author == "Athena Team"
        assert skill.metadata.version == "1.0.0"
        assert skill.metadata.tags == ["test"]
    finally:
        # Cleanup
        temp_path.unlink()


def test_load_from_file_not_found():
    """测试加载不存在的文件"""
    # Arrange
    loader = SkillLoader()

    # Act & Assert
    with pytest.raises(FileNotFoundError, match="技能文件不存在"):
        loader.load_from_file("/nonexistent/file.yaml")


def test_load_from_file_invalid_yaml():
    """测试加载无效的YAML文件"""
    # Arrange - 创建无效YAML文件
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".yaml",
        delete=False,
    ) as f:
        f.write("invalid: yaml: content: [")
        temp_path = Path(f.name)

    try:
        # Act
        loader = SkillLoader()

        # Assert
        with pytest.raises(ValueError, match="YAML解析错误"):
            loader.load_from_file(temp_path)
    finally:
        # Cleanup
        temp_path.unlink()


def test_load_from_file_missing_required_field():
    """测试缺少必需字段"""
    # Arrange - 创建缺少id的YAML
    skill_data = {
        "name": "Test Skill",
        "category": "analysis",
        "description": "A test skill",
    }

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".yaml",
        delete=False,
    ) as f:
        yaml.dump(skill_data, f)
        temp_path = Path(f.name)

    try:
        # Act
        loader = SkillLoader()

        # Assert
        with pytest.raises(ValueError, match="缺少必需字段"):
            loader.load_from_file(temp_path)
    finally:
        # Cleanup
        temp_path.unlink()


def test_load_from_file_invalid_category():
    """测试无效的类别"""
    # Arrange - 创建无效类别
    skill_data = {
        "id": "test_skill",
        "name": "Test Skill",
        "category": "invalid_category",
        "description": "A test skill",
    }

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".yaml",
        delete=False,
    ) as f:
        yaml.dump(skill_data, f)
        temp_path = Path(f.name)

    try:
        # Act
        loader = SkillLoader()

        # Assert
        with pytest.raises(ValueError, match="无效的类别"):
            loader.load_from_file(temp_path)
    finally:
        # Cleanup
        temp_path.unlink()


def test_load_from_directory():
    """测试从目录加载技能"""
    # Arrange - 创建临时目录和技能文件
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # 创建3个技能文件
        for i in range(3):
            skill_data = {
                "id": f"skill_{i}",
                "name": f"Skill {i}",
                "category": "analysis",
                "description": f"Test skill {i}",
                "tools": [f"tool{i}"],
            }

            skill_file = temp_path / f"skill_{i}.yaml"
            with open(skill_file, "w") as f:
                yaml.dump(skill_data, f)

        # Act
        loader = SkillLoader()
        skills = loader.load_from_directory(temp_path, register=True)

        # Assert
        assert len(skills) == 3
        assert loader.registry.get_skill("skill_0") is not None
        assert loader.registry.get_skill("skill_1") is not None
        assert loader.registry.get_skill("skill_2") is not None


def test_load_from_directory_recursive():
    """测试递归加载子目录"""
    # Arrange - 创建嵌套目录结构
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # 创建子目录
        subdir = temp_path / "subdir"
        subdir.mkdir()

        # 创建主目录的技能
        skill_data_1 = {
            "id": "main_skill",
            "name": "Main Skill",
            "category": "analysis",
            "description": "Main directory skill",
        }
        main_file = temp_path / "main.yaml"
        with open(main_file, "w") as f:
            yaml.dump(skill_data_1, f)

        # 创建子目录的技能
        skill_data_2 = {
            "id": "sub_skill",
            "name": "Sub Skill",
            "category": "search",
            "description": "Subdirectory skill",
        }
        sub_file = subdir / "sub.yaml"
        with open(sub_file, "w") as f:
            yaml.dump(skill_data_2, f)

        # Act
        loader = SkillLoader()

        # 非递归 - 只加载主目录
        skills_non_recursive = loader.load_from_directory(
            temp_path,
            recursive=False,
        )
        assert len(skills_non_recursive) == 1

        # 递归 - 加载所有目录
        skills_recursive = loader.load_from_directory(
            temp_path,
            recursive=True,
        )
        assert len(skills_recursive) == 2


def test_load_from_directory_nonexistent():
    """测试加载不存在的目录"""
    # Arrange
    loader = SkillLoader()

    # Act
    skills = loader.load_from_directory("/nonexistent/directory")

    # Assert
    assert skills == []


def test_load_from_custom_registry():
    """测试使用自定义注册表"""
    # Arrange
    custom_registry = SkillRegistry()

    skill_data = {
        "id": "custom_skill",
        "name": "Custom Skill",
        "category": "writing",
        "description": "Custom registry skill",
    }

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".yaml",
        delete=False,
    ) as f:
        yaml.dump(skill_data, f)
        temp_path = Path(f.name)

    try:
        # Act
        loader = SkillLoader(registry=custom_registry)
        loader.load_from_directory(temp_path.parent, register=True)

        # Assert - 应该在自定义注册表中
        assert custom_registry.get_skill("custom_skill") is not None
        # 不应该在默认注册表中
        default_loader = SkillLoader()
        assert default_loader.registry.get_skill("custom_skill") is None
    finally:
        # Cleanup
        temp_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

