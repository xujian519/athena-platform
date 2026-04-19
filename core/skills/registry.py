from __future__ import annotations
"""
技能注册中心

管理所有已注册的技能。
"""

import asyncio
import logging
from pathlib import Path

from .base import (
    Skill,
    SkillCategory,
    SkillMetadata,
)

logger = logging.getLogger(__name__)


class SkillRegistry:
    """技能注册中心

    管理技能的注册、发现和生命周期。
    """

    def __init__(self, skills_dir: Path | None = None):
        self._skills: dict[str, Skill] = {}
        self._metadata: dict[str, SkillMetadata] = {}
        self._skills_dir = skills_dir or Path(__file__).parent.parent.parent / "skills"
        self._lock = asyncio.Lock()

    async def register(self, skill: Skill) -> None:
        """注册技能

        Args:
            skill: 技能实例

        Raises:
            ValueError: 如果技能名称已存在
        """
        async with self._lock:
            name = skill.metadata.name

            if name in self._skills:
                raise ValueError(f"Skill '{name}' already registered")

            self._skills[name] = skill
            self._metadata[name] = skill.metadata

            # 初始化技能
            await skill.initialize()

            logger.info(f"Registered skill: {name} v{skill.metadata.version}")

    def unregister(self, name: str) -> bool:
        """注销技能

        Args:
            name: 技能名称

        Returns:
            bool: 是否成功注销
        """
        if name in self._skills:
            self._skills.pop(name)
            self._metadata.pop(name, None)
            logger.info(f"Unregistered skill: {name}")
            return True
        return False

    def get(self, name: str) -> Skill | None:
        """获取技能

        Args:
            name: 技能名称

        Returns:
            Optional[Skill]: 技能实例，不存在则返回 None
        """
        return self._skills.get(name)

    def get_metadata(self, name: str) -> SkillMetadata | None:
        """获取技能元数据

        Args:
            name: 技能名称

        Returns:
            Optional[SkillMetadata]: 技能元数据
        """
        return self._metadata.get(name)

    def list_all(self) -> list[str]:
        """列出所有技能名称"""
        return list(self._skills.keys())

    def list_by_category(self, category: SkillCategory) -> list[str]:
        """按分类列出技能

        Args:
            category: 技能分类

        Returns:
            List[str]: 该分类下的技能名称列表
        """
        return [
            name for name, meta in self._metadata.items()
            if meta.category == category and meta.enabled
        ]

    def list_enabled(self) -> list[str]:
        """列出已启用的技能"""
        return [
            name for name, meta in self._metadata.items()
            if meta.enabled
        ]

    def exists(self, name: str) -> bool:
        """检查技能是否存在"""
        return name in self._skills

    def enable(self, name: str) -> bool:
        """启用技能"""
        skill = self.get(name)
        if skill:
            skill.enable()
            self._metadata[name].enabled = True
            logger.info(f"Enabled skill: {name}")
            return True
        return False

    def disable(self, name: str) -> bool:
        """禁用技能"""
        skill = self.get(name)
        if skill:
            skill.disable()
            self._metadata[name].enabled = False
            logger.info(f"Disabled skill: {name}")
            return True
        return False

    async def discover(self, directory: Path | None = None) -> list[Path]:
        """发现技能目录

        扫描指定目录，查找所有包含 SKILL.md 的子目录。

        Args:
            directory: 要扫描的目录，默认使用初始化时指定的目录

        Returns:
            List[Path]: 所有技能目录的路径列表
        """
        scan_dir = directory or self._skills_dir
        skill_dirs = []

        if not scan_dir.exists():
            logger.warning(f"Skills directory does not exist: {scan_dir}")
            return skill_dirs

        # 扫描公共技能和自定义技能
        for category in ["public", "custom"]:
            category_path = scan_dir / category
            if not category_path.exists():
                continue

            for item in category_path.iterdir():
                if item.is_dir():
                    skill_md = item / "SKILL.md"
                    if skill_md.exists():
                        skill_dirs.append(item)

        logger.info(f"Discovered {len(skill_dirs)} skill directories")
        return skill_dirs

    async def load_from_directory(self, directory: Path | None = None) -> int:
        """从目录加载技能

        扫描目录并加载所有技能。

        Args:
            directory: 要扫描的目录

        Returns:
            int: 成功加载的技能数量
        """
        from .manager import SkillManager

        skill_dirs = await self.discover(directory)
        manager = SkillManager(registry=self)

        loaded_count = 0
        for skill_dir in skill_dirs:
            try:
                skill = await manager.load_skill(skill_dir)
                if skill:
                    loaded_count += 1
            except Exception as e:
                logger.error(f"Failed to load skill from {skill_dir}: {e}")

        return loaded_count

    def get_statistics(self) -> dict:
        """获取统计信息

        Returns:
            dict: 包含技能数量、分类分布等统计信息
        """
        total = len(self._skills)
        enabled = len(self.list_enabled())
        disabled = total - enabled

        # 按分类统计
        by_category = {}
        for meta in self._metadata.values():
            category = meta.category.value
            by_category[category] = by_category.get(category, 0) + 1

        return {
            "total": total,
            "enabled": enabled,
            "disabled": disabled,
            "by_category": by_category,
        }

    def __len__(self) -> int:
        return len(self._skills)

    def __contains__(self, name: str) -> bool:
        return name in self._skills

    def __repr__(self) -> str:
        stats = self.get_statistics()
        return (
            f"SkillRegistry("
            f"total={stats['total']}, "
            f"enabled={stats['enabled']}, "
            f"disabled={stats['disabled']})"
        )
