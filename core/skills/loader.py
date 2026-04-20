#!/usr/bin/env python3
"""
技能加载器

从文件系统加载技能定义。

作者: Athena平台团队
创建时间: 2026-04-21
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

import yaml

from .registry import SkillRegistry
from .types import SkillDefinition, SkillCategory, SkillMetadata

logger = logging.getLogger(__name__)


class SkillLoader:
    """技能加载器

    从文件系统加载技能定义并注册到注册表。
    """

    def __init__(self, registry: Optional[SkillRegistry] = None):
        """初始化加载器

        Args:
            registry: 技能注册表，默认创建新的
        """
        self.registry = registry or SkillRegistry()
        logger.info("📚 技能加载器已初始化")

    def load_from_file(self, file_path: str | Path) -> Optional[SkillDefinition]:
        """从文件加载技能

        Args:
            file_path: 文件路径（.yaml或.yml）

        Returns:
            SkillDefinition | None: 技能定义，失败返回None

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式错误
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"技能文件不存在: {file_path}")

        # 读取YAML文件
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"YAML解析错误: {e}")

        # 解析技能定义
        skill = self._parse_skill_definition(data, file_path)

        logger.info(f"✅ 从文件加载技能: {skill.id} - {skill.name}")
        return skill

    def load_from_directory(
        self,
        directory: str | Path,
        recursive: bool = False,
        register: bool = True,
    ) -> List[SkillDefinition]:
        """从目录加载技能

        Args:
            directory: 目录路径
            recursive: 是否递归加载子目录
            register: 是否自动注册到注册表

        Returns:
            list[SkillDefinition]: 加载的技能列表
        """
        directory = Path(directory)
        skills = []

        if not directory.exists():
            logger.warning(f"⚠️ 技能目录不存在: {directory}")
            return skills

        # 查找所有YAML文件
        pattern = "**/*.yaml" if recursive else "*.yaml"
        yaml_files = list(directory.glob(pattern))
        yaml_files.extend(directory.glob(pattern.replace("yaml", "yml")))

        logger.info(f"📂 在目录中找到 {len(yaml_files)} 个技能文件: {directory}")

        # 加载每个文件
        for yaml_file in yaml_files:
            try:
                skill = self.load_from_file(yaml_file)
                skills.append(skill)

                # 自动注册
                if register:
                    self.registry.register(skill)
            except Exception as e:
                logger.error(f"❌ 加载技能失败 {yaml_file}: {e}")

        logger.info(f"✅ 成功加载 {len(skills)} 个技能")
        return skills

    def _parse_skill_definition(
        self,
        data: dict,
        file_path: Path,
    ) -> SkillDefinition:
        """解析技能定义

        Args:
            data: YAML数据
            file_path: 文件路径

        Returns:
            SkillDefinition: 技能定义

        Raises:
            ValueError: 数据格式错误
        """
        # 验证必需字段
        required_fields = ["id", "name", "category", "description"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"缺少必需字段: {field}")

        # 解析类别
        try:
            category = SkillCategory(data["category"])
        except ValueError:
            valid_categories = [c.value for c in SkillCategory]
            raise ValueError(
                f"无效的类别 '{data['category']}'，"
                f"有效值为: {valid_categories}"
            )

        # 解析元数据
        metadata_data = data.get("metadata", {})
        metadata = SkillMetadata(
            author=metadata_data.get("author"),
            version=metadata_data.get("version", "1.0.0"),
            tags=metadata_data.get("tags", []),
            enabled=metadata_data.get("enabled", True),
            priority=metadata_data.get("priority", 5),
            created_at=metadata_data.get("created_at"),
            updated_at=metadata_data.get("updated_at"),
        )

        # 创建技能定义
        skill = SkillDefinition(
            id=data["id"],
            name=data["name"],
            category=category,
            description=data["description"],
            tools=data.get("tools", []),
            metadata=metadata,
            content=data.get("content", ""),
            source=data.get("source", "file"),
            path=str(file_path),
        )

        return skill


__all__ = [
    "SkillLoader",
]
