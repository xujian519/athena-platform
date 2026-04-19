from __future__ import annotations
"""
输出风格系统

借鉴 kode-agent 的 outputStyles 设计，支持通过 Markdown + YAML frontmatter
定义输出风格，影响 Agent 的回复格式和详细程度。

三层搜索路径（高优先级覆盖低优先级）：
1. 内置风格 (core/agents/declarative/builtin/output-styles/)
2. 用户级风格 (~/.athena/output-styles/)
3. 项目级风格 (.athena/output-styles/)

Author: Athena Team
"""

import logging
import threading
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .utils import parse_frontmatter

logger = logging.getLogger("agent.declarative.output_styles")


class StyleSource(Enum):
    """风格定义来源"""
    BUILTIN = "builtin"
    USER = "user"
    PROJECT = "project"


@dataclass
class OutputStyleDefinition:
    """
    输出风格定义

    从 Markdown + YAML frontmatter 加载。
    frontmatter 定义元数据，正文定义风格提示词。

    Example .md file:
        ---
        name: concise
        description: "简洁模式 - 只输出关键信息"
        keep_base_instructions: true
        ---
        你正在使用简洁输出模式...
    """
    name: str
    description: str = ""
    prompt: str = ""
    source: StyleSource = StyleSource.BUILTIN
    keep_base_instructions: bool = True
    filename: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "source": self.source.value,
            "keep_base_instructions": self.keep_base_instructions,
            "prompt_length": len(self.prompt),
        }

    @classmethod
    def from_frontmatter(
        cls,
        metadata: dict[str, Any],
        content: str,
        source: StyleSource = StyleSource.BUILTIN,
        filename: str = "",
    ) -> OutputStyleDefinition:
        """从 frontmatter 构建 OutputStyleDefinition"""
        name = metadata.get("name", filename.replace(".md", ""))
        description = metadata.get("description", "")

        # 如果没有描述，取正文第一行标题或文本
        if not description and content.strip():
            for line in content.strip().splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                # 取 Markdown 标题
                heading = stripped.lstrip("#").strip()
                if heading:
                    description = heading[:100]
                else:
                    description = stripped[:100]
                break

        keep_base = metadata.get("keep_base_instructions", True)
        if isinstance(keep_base, str):
            keep_base = keep_base.lower() in ("true", "yes", "1")

        return cls(
            name=name,
            description=description,
            prompt=content.strip(),
            source=source,
            keep_base_instructions=bool(keep_base),
            filename=filename,
        )


# 内置风格名称
DEFAULT_STYLE = "default"


class OutputStyleLoader:
    """
    输出风格加载器

    轻量级设计，无全局缓存膨胀风险：
    - _styles 字典仅保存风格元数据，prompt 按需读取
    - 提供 force_reload 支持热更新
    - 线程安全的单例获取
    """

    def __init__(self, project_root: str | Path | None = None):
        self._project_root = Path(project_root) if project_root else Path.cwd()
        self._styles: dict[str, OutputStyleDefinition] = {}
        self._loaded = False

    def _get_search_paths(self) -> list[tuple[Path, StyleSource]]:
        """获取搜索路径列表"""
        paths = []

        # 1. 内置路径
        builtin_path = Path(__file__).parent / "builtin" / "output-styles"
        if builtin_path.is_dir():
            paths.append((builtin_path, StyleSource.BUILTIN))

        # 2. 用户级路径
        user_path = Path.home() / ".athena" / "output-styles"
        if user_path.is_dir():
            paths.append((user_path, StyleSource.USER))

        # 3. 项目级路径
        project_path = self._project_root / ".athena" / "output-styles"
        if project_path.is_dir():
            paths.append((project_path, StyleSource.PROJECT))

        return paths

    def _load_file(self, file_path: Path, source: StyleSource) -> OutputStyleDefinition | None:
        """加载单个风格文件"""
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"读取风格文件失败 {file_path}: {e}")
            return None

        metadata, body = parse_frontmatter(content)
        if not metadata.get("name"):
            metadata["name"] = file_path.stem

        style = OutputStyleDefinition.from_frontmatter(
            metadata=metadata,
            content=body,
            source=source,
            filename=file_path.name,
        )

        logger.debug(f"加载输出风格: {style.name} from {file_path} ({source.value})")
        return style

    def load_all(self, force_reload: bool = False) -> dict[str, OutputStyleDefinition]:
        """加载所有输出风格"""
        if self._loaded and not force_reload:
            return self._styles.copy()

        self._styles.clear()
        for search_path, source in self._get_search_paths():
            for md_file in search_path.glob("*.md"):
                style = self._load_file(md_file, source)
                if style:
                    self._styles[style.name] = style

        self._loaded = True
        logger.info(f"加载完成: {len(self._styles)} 个输出风格")
        return self._styles.copy()

    def get(self, name: str) -> OutputStyleDefinition | None:
        """获取指定风格"""
        if not self._loaded:
            self.load_all()
        return self._styles.get(name)

    def list_names(self) -> list[str]:
        """列出所有风格名称"""
        if not self._loaded:
            self.load_all()
        return list(self._styles.keys())

    def get_all(self) -> dict[str, OutputStyleDefinition]:
        """获取所有风格"""
        if not self._loaded:
            self.load_all()
        return self._styles.copy()

    def resolve_name(self, raw: str) -> str | None:
        """
        解析风格名称（支持大小写不敏感匹配）

        Args:
            raw: 用户输入的风格名称

        Returns:
            匹配到的真实风格名，或 None
        """
        if not raw or not raw.strip():
            return None
        if not self._loaded:
            self.load_all()

        raw = raw.strip()
        if raw in self._styles:
            return raw

        # 大小写不敏感匹配
        lower = raw.lower()
        for name in self._styles:
            if name.lower() == lower:
                return name
        return None

    def get_style_prompt(self, name: str) -> str:
        """
        获取风格的提示词追加内容

        Args:
            name: 风格名称

        Returns:
            风格提示词，如果风格不存在则返回空字符串
        """
        style = self.get(name)
        if not style or not style.prompt:
            return ""
        return f"\n# 输出风格: {style.name}\n{style.prompt}\n"


# 模块级便捷函数（线程安全单例）
_loader_instance: OutputStyleLoader | None = None
_loader_lock = threading.Lock()


def get_loader(project_root: str | None = None) -> OutputStyleLoader:
    """获取 OutputStyleLoader 单例"""
    global _loader_instance
    if _loader_instance is None:
        with _loader_lock:
            if _loader_instance is None:
                _loader_instance = OutputStyleLoader(project_root)
    elif project_root is not None:
        return OutputStyleLoader(project_root)
    return _loader_instance


def get_available_styles(project_root: str | None = None) -> dict[str, OutputStyleDefinition]:
    """获取所有可用的输出风格"""
    return get_loader(project_root).load_all()


def get_style(name: str, project_root: str | None = None) -> OutputStyleDefinition | None:
    """获取指定名称的输出风格"""
    return get_loader(project_root).get(name)


def get_style_prompt(name: str, project_root: str | None = None) -> str:
    """获取风格的提示词追加内容"""
    return get_loader(project_root).get_style_prompt(name)
