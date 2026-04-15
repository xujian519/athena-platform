from __future__ import annotations
"""
技能管理器

负责技能的加载、解析和实例化。
"""

import importlib
import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any

from .base import Skill, SkillMetadata
from .registry import SkillRegistry

logger = logging.getLogger(__name__)


class SkillManager:
    """技能管理器

    负责从文件系统加载技能并实例化。
    """

    def __init__(
        self,
        registry: SkillRegistry | None = None,
        skills_dir: Path | None = None
    ):
        self._registry = registry or SkillRegistry(skills_dir)
        self._skills_dir = skills_dir or Path(__file__).parent.parent.parent / "skills"
        self._import_cache: dict[str, Any] = {}

    @property
    def registry(self) -> SkillRegistry:
        """获取技能注册中心"""
        return self._registry

    async def load_skill(self, skill_dir: Path) -> Skill | None:
        """从目录加载技能

        Args:
            skill_dir: 技能目录路径

        Returns:
            Optional[Skill]: 加载的技能实例，失败返回 None

        Raises:
            SkillException: 技能加载失败
        """
        # 查找 SKILL.md
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            logger.warning(f"SKILL.md not found in {skill_dir}")
            return None

        # 解析元数据
        metadata = self._parse_skill_metadata(skill_md)
        if not metadata:
            return None

        # 查找技能实现
        skill_impl = await self._load_skill_implementation(skill_dir, metadata)
        if not skill_impl:
            return None

        # 注册技能
        try:
            await self._registry.register(skill_impl)
            return skill_impl
        except Exception as e:
            logger.error(f"Failed to register skill {metadata.name}: {e}")
            return None

    def _parse_skill_metadata(self, skill_md: Path) -> SkillMetadata | None:
        """解析技能元数据

        Args:
            skill_md: SKILL.md 文件路径

        Returns:
            Optional[SkillMetadata]: 解析的元数据
        """
        try:
            content = skill_md.read_text(encoding="utf-8")

            # 提取 YAML 前置元数据
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    yaml_content = parts[1]
                    metadata = SkillMetadata.from_yaml(yaml_content)

                    # 验证必需字段
                    if not metadata.name or not metadata.display_name:
                        logger.error(f"Invalid metadata in {skill_md}: missing name or display_name")
                        return None

                    return metadata

            logger.warning(f"No valid YAML frontmatter in {skill_md}")
            return None

        except Exception as e:
            logger.error(f"Failed to parse metadata from {skill_md}: {e}")
            return None

    async def _load_skill_implementation(
        self,
        skill_dir: Path,
        metadata: SkillMetadata
    ) -> Skill | None:
        """加载技能实现

        Args:
            skill_dir: 技能目录
            metadata: 技能元数据

        Returns:
            Optional[Skill]: 技能实例
        """
        # 尝试加载 Python 实现
        py_file = skill_dir / f"{metadata.name}.py"
        main_py = skill_dir / "main.py"

        if py_file.exists():
            return await self._load_from_python_file(py_file, metadata)
        elif main_py.exists():
            return await self._load_from_python_file(main_py, metadata)
        else:
            # 创建简单的包装技能
            return self._create_wrapper_skill(skill_dir, metadata)

    async def _load_from_python_file(
        self,
        py_file: Path,
        metadata: SkillMetadata
    ) -> Skill | None:
        """从 Python 文件加载技能

        Args:
            py_file: Python 文件路径
            metadata: 技能元数据

        Returns:
            Optional[Skill]: 技能实例
        """
        try:
            # 动态导入模块
            module_name = f"skill_{metadata.name}"
            spec = importlib.util.spec_from_file_location(module_name, py_file)

            if spec is None or spec.loader is None:
                logger.error(f"Failed to load module spec from {py_file}")
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # 查找技能类
            skill_class = getattr(module, "Skill", None)
            if skill_class is None:
                # 尝试查找与技能名称同名的类
                class_name = "".join(
                    word.capitalize() for word in metadata.name.split("_")
                )
                skill_class = getattr(module, class_name, None)

            if skill_class is None:
                logger.error(f"No skill class found in {py_file}")
                return None

            # 实例化技能
            skill = skill_class(metadata)
            return skill

        except Exception as e:
            logger.error(f"Failed to load skill from {py_file}: {e}", exc_info=True)
            return None

    def _create_wrapper_skill(
        self,
        skill_dir: Path,
        metadata: SkillMetadata
    ) -> Skill | None:
        """创建包装技能

        为没有 Python 实现的技能创建简单的包装。

        Args:
            skill_dir: 技能目录
            metadata: 技能元数据

        Returns:
            Optional[Skill]: 包装技能实例
        """
        from .base import Skill, SkillResult

        class WrapperSkill(Skill):
            """包装技能基类"""

            def __init__(self, skill_dir: Path, metadata: SkillMetadata):
                super().__init__(metadata)
                self._skill_dir = skill_dir
                self._description = self._load_description()

            def _load_description(self) -> str:
                """加载技能描述"""
                readme = self._skill_dir / "SKILL.md"
                if readme.exists():
                    content = readme.read_text(encoding="utf-8")
                    # 移除 YAML 前置元数据
                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            return parts[2].strip()
                    return content
                return self._metadata.description

            async def execute(self, **kwargs) -> SkillResult:
                """执行技能（默认实现）"""
                return SkillResult(
                    success=True,
                    data={
                        "message": f"Skill '{self._metadata.name}' executed",
                        "description": self._description,
                        "parameters": kwargs,
                    },
                    metadata={"skill_type": "wrapper"},
                )

        return WrapperSkill(skill_dir, metadata)

    async def reload_skill(self, name: str) -> Skill | None:
        """重新加载技能

        Args:
            name: 技能名称

        Returns:
            Optional[Skill]: 重新加载的技能实例
        """
        # 先注销旧技能
        self._registry.unregister(name)

        # 查找技能目录
        skill_dirs = await self._registry.discover()
        for skill_dir in skill_dirs:
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                metadata = self._parse_skill_metadata(skill_md)
                if metadata and metadata.name == name:
                    return await self.load_skill(skill_dir)

        logger.warning(f"Skill '{name}' not found for reload")
        return None

    async def load_all(self) -> int:
        """加载所有技能

        Returns:
            int: 成功加载的技能数量
        """
        return await self._registry.load_from_directory(self._skills_dir)

    def create_skill(
        self,
        name: str,
        display_name: str,
        description: str,
        category: str = "custom",
        **metadata_kwargs
    ) -> SkillMetadata:
        """创建新技能元数据

        用于快速创建技能的元数据对象。

        Args:
            name: 技能名称
            display_name: 显示名称
            description: 技能描述
            category: 技能分类
            **metadata_kwargs: 其他元数据

        Returns:
            SkillMetadata: 技能元数据对象
        """
        from .base import SkillCategory

        return SkillMetadata(
            name=name,
            display_name=display_name,
            description=description,
            category=SkillCategory(category),
            **metadata_kwargs
        )

    def validate_skill_directory(self, skill_dir: Path) -> tuple[bool, list[str]]:
        """验证技能目录结构

        Args:
            skill_dir: 技能目录路径

        Returns:
            tuple[bool, list[str]]: (是否有效, 错误信息列表)
        """
        errors = []

        # 检查 SKILL.md
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            errors.append("SKILL.md not found")

        # 检查元数据
        if skill_md.exists():
            metadata = self._parse_skill_metadata(skill_md)
            if metadata is None:
                errors.append("Invalid metadata in SKILL.md")
            elif not metadata.name or not metadata.display_name:
                errors.append("Missing required metadata fields (name, display_name)")

        # 检查 Python 实现
        py_files = list(skill_dir.glob("*.py"))
        if not py_files:
            errors.append("No Python implementation found (optional for wrapper skills)")

        return len(errors) == 0, errors
