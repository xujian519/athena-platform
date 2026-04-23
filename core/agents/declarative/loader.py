from __future__ import annotations
"""
声明式 Agent 加载器

从文件系统加载 .md 格式的 Agent 定义文件。
支持三层搜索路径（内置 → 用户级 → 项目级），后者覆盖前者。

Author: Athena Team
"""

import logging
import threading
from pathlib import Path

from .models import AgentDefinition, AgentSource
from .utils import parse_frontmatter

logger = logging.getLogger("agent.declarative.loader")


class AgentLoader:
    """
    Agent 定义加载器

    从多个搜索路径加载 .md 文件，解析 YAML frontmatter，
    返回 AgentDefinition 实例。

    搜索路径优先级（高优先级覆盖低优先级）：
    1. core/agents/declarative/builtin/ (内置)
    2. ~/.athena/agents/ (用户级)
    3. .athena/agents/ (项目级)
    """

    def __init__(self, project_root: str | Path | None = None):
        """
        初始化加载器

        Args:
            project_root: 项目根目录，默认为当前工作目录
        """
        self._project_root = Path(project_root) if project_root else Path.cwd()
        self._agents: dict[str, AgentDefinition] = {}
        self._loaded = False

    def _get_search_paths(self) -> list[tuple[Path, AgentSource]]:
        """获取搜索路径列表（按优先级从低到高）"""
        paths = []

        # 1. 内置路径
        builtin_path = Path(__file__).parent / "builtin"
        if builtin_path.is_dir():
            paths.append((builtin_path, AgentSource.BUILTIN))

        # 2. 用户级路径
        user_path = Path.home() / ".athena" / "agents"
        if user_path.is_dir():
            paths.append((user_path, AgentSource.USER))

        # 3. 项目级路径
        project_path = self._project_root / ".athena" / "agents"
        if project_path.is_dir():
            paths.append((project_path, AgentSource.PROJECT))

        return paths

    def _parse_frontmatter(self, content: str) -> tuple[dict, str]:
        """
        解析 YAML frontmatter

        委托给公共工具函数 parse_frontmatter()。

        Args:
            content: 文件完整内容

        Returns:
            (metadata_dict, body_content) 元组
        """
        return parse_frontmatter(content)

    def _load_file(self, file_path: Path, source: AgentSource) -> AgentDefinition | None:
        """
        加载单个 .md 文件

        Args:
            file_path: 文件路径
            source: 来源类型

        Returns:
            AgentDefinition 或 None（解析失败时）
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"读取文件失败 {file_path}: {e}")
            return None

        metadata, body = self._parse_frontmatter(content)
        if not metadata.get("name"):
            # 如果没有指定 name，使用文件名（去掉 .md 后缀）
            metadata["name"] = file_path.stem

        definition = AgentDefinition.from_frontmatter(
            metadata=metadata,
            content=body,
            source=source,
            filename=file_path.name,
        )

        logger.debug(f"加载 Agent 定义: {definition.name} from {file_path} ({source.value})")
        return definition

    def load_all(self, force_reload: bool = False) -> dict[str, AgentDefinition]:
        """
        加载所有搜索路径中的 Agent 定义

        Args:
            force_reload: 是否强制重新加载

        Returns:
            {name: AgentDefinition} 字典
        """
        if self._loaded and not force_reload:
            return self._agents.copy()

        self._agents.clear()
        search_paths = self._get_search_paths()

        for search_path, source in search_paths:
            for md_file in search_path.glob("*.md"):
                definition = self._load_file(md_file, source)
                if definition:
                    # 同名 Agent 后者覆盖前者（项目级 > 用户级 > 内置）
                    self._agents[definition.name] = definition

        self._loaded = True
        logger.info(f"加载完成: {len(self._agents)} 个声明式 Agent")
        return self._agents.copy()

    def get(self, name: str) -> AgentDefinition | None:
        """
        获取指定名称的 Agent 定义

        Args:
            name: Agent 名称

        Returns:
            AgentDefinition 或 None
        """
        if not self._loaded:
            self.load_all()
        return self._agents.get(name)

    def list_names(self) -> list[str]:
        """列出所有已加载的 Agent 名称"""
        if not self._loaded:
            self.load_all()
        return list(self._agents.keys())

    def get_all(self) -> dict[str, AgentDefinition]:
        """获取所有已加载的 Agent 定义"""
        if not self._loaded:
            self.load_all()
        return self._agents.copy()


# 模块级便捷函数
_loader_instance: AgentLoader | None = None
_loader_lock = threading.Lock()


def get_loader(project_root: Optional[str] = None) -> AgentLoader:
    """获取 AgentLoader 单例（线程安全）"""
    global _loader_instance
    if _loader_instance is None:
        with _loader_lock:
            if _loader_instance is None:
                _loader_instance = AgentLoader(project_root)
    elif project_root is not None:
        # 需要自定义 project_root 时返回新实例，不覆盖全局单例
        return AgentLoader(project_root)
    return _loader_instance


def load_all_agents(project_root: Optional[str] = None) -> dict[str, AgentDefinition]:
    """加载所有声明式 Agent 定义"""
    return get_loader(project_root).load_all()


def get_agent(name: str, project_root: Optional[str] = None) -> AgentDefinition | None:
    """获取指定名称的 Agent 定义"""
    return get_loader(project_root).get(name)
