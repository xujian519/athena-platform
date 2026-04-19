from __future__ import annotations
"""
Athena智能体工厂

负责创建和管理智能体实例。支持动态加载和配置化创建。

Author: Athena Team
Version: 1.0.0
Date: 2025-02-21
"""

import importlib
import inspect
import logging
from pathlib import Path
from typing import Any

from core.agents.base import AgentRegistry, BaseAgent

logger = logging.getLogger("agent.factory")


class AgentFactory:
    """
    智能体工厂

    根据配置动态创建和管理智能体实例。

    Usage:
        ```python
        # 注册智能体类
        AgentFactory.register_agent_class(XiaonaLegalAgent)

        # 创建智能体
        agent = AgentFactory.create("xiaona-legal")

        # 带配置创建
        agent = AgentFactory.create(
            "xiaona-legal",
            config={"llm_model": "claude-3.5-sonnet"}
        )

        # 创建并初始化
        agent = await AgentFactory.create_async("xiaona-legal")
        ```
    """

    # 类级别的智能体类注册表
    _agent_classes: dict[str, type[BaseAgent]] = {}

    @classmethod
    def register_agent_class(cls, agent_class: type[BaseAgent]) -> str:
        """
        注册智能体类

        Args:
            agent_class: 继承自BaseAgent的智能体类

        Returns:
            智能体名称

        Raises:
            TypeError: 如果不是BaseAgent的子类
            ValueError: 如果智能体名称已存在

        Note:
            智能体类会自动注册，使用其name属性作为标识
        """
        # 验证类型
        if not issubclass(agent_class, BaseAgent):
            raise TypeError(f"{agent_class} 必须继承自 BaseAgent")

        # 创建临时实例获取名称
        temp_instance = agent_class()
        name = temp_instance.name
        del temp_instance

        # 检查重复
        if name in cls._agent_classes:
            raise ValueError(f"智能体类 {name} 已存在")

        # 注册
        cls._agent_classes[name] = agent_class
        logger.info(f"注册智能体类: {name} -> {agent_class.__name__}")

        return name

    @classmethod
    def unregister_agent_class(cls, name: str) -> None:
        """
        注销智能体类

        Args:
            name: 智能体名称
        """
        if name in cls._agent_classes:
            del cls._agent_classes[name]
            logger.info(f"注销智能体类: {name}")

    @classmethod
    def create(
        cls,
        name: str,
        config: dict[str, Any] | None = None,
        register: bool = True
    ) -> BaseAgent:
        """
        创建智能体实例

        Args:
            name: 智能体名称
            config: 配置字典
            register: 是否注册到AgentRegistry

        Returns:
            智能体实例

        Raises:
            ValueError: 如果智能体类型未注册

        Note:
            创建的智能体处于INITIALIZING状态，需要调用initialize()方法
        """
        if name not in cls._agent_classes:
            available = ", ".join(cls.list_available_agents())
            raise ValueError(
                f"未知的智能体类型: {name}. "
                f"可用类型: {available or '无'}"
            )

        agent_class = cls._agent_classes[name]
        agent = agent_class(config)

        logger.info(f"创建智能体实例: {name}")

        # 注册到注册中心
        if register:
            AgentRegistry.register(agent)

        return agent

    @classmethod
    async def create_async(
        cls,
        name: str,
        config: dict[str, Any] | None = None,
        register: bool = True
    ) -> BaseAgent:
        """
        创建并初始化智能体实例

        Args:
            name: 智能体名称
            config: 配置字典
            register: 是否注册到AgentRegistry

        Returns:
            已初始化的智能体实例
        """
        agent = cls.create(name, config, register)
        await agent.initialize()
        return agent

    @classmethod
    async def create_many(
        cls,
        configs: list[dict[str, Any]]
    ) -> list[BaseAgent]:
        """
        批量创建智能体

        Args:
            configs: 配置列表，每个配置包含 name 和可选的 config 字段
                例如: [{"name": "xiaona-legal", "config": {...}}]

        Returns:
            智能体实例列表

        Note:
            并发创建，提高效率
        """
        tasks = []
        for config_spec in configs:
            name = config_spec.get("name")
            agent_config = config_spec.get("config")
            if name:
                tasks.append(cls.create_async(name, agent_config))

        return await asyncio.gather(*tasks, return_exceptions=True)

    @classmethod
    def list_available_agents(cls) -> list[str]:
        """
        列出已注册的智能体类型

        Returns:
            智能体名称列表
        """
        return list(cls._agent_classes.keys())

    @classmethod
    def get_agent_class(cls, name: str) -> type[BaseAgent] | None:
        """
        获取智能体类

        Args:
            name: 智能体名称

        Returns:
            智能体类，如果不存在返回None
        """
        return cls._agent_classes.get(name)

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """
        检查智能体类是否已注册

        Args:
            name: 智能体名称

        Returns:
            是否已注册
        """
        return name in cls._agent_classes

    @classmethod
    def clear(cls) -> None:
        """
        清空所有注册的智能体类

        Note:
        主要用于测试环境
        """
        cls._agent_classes.clear()
        logger.info("清空智能体类注册表")

    @classmethod
    def load_declarative_agents(cls, project_root: str | None = None) -> list[str]:
        """
        加载声明式 Agent 定义并注册到工厂

        从 .md 文件加载 Agent 定义，创建 DeclarativeAgent 子类并注册。

        Args:
            project_root: 项目根目录

        Returns:
            成功注册的 Agent 名称列表
        """
        try:
            from core.agents.declarative import DeclarativeAgent, load_all_agents
        except ImportError:
            logger.warning("无法导入声明式 Agent 模块")
            return []

        try:
            definitions = load_all_agents(project_root)
        except Exception as e:
            logger.error(f"加载声明式 Agent 定义失败: {e}")
            return []

        registered = []

        for name, definition in definitions.items():
            if name in cls._agent_classes:
                logger.debug(f"声明式 Agent {name} 已存在，跳过")
                continue

            try:
                agent_cls = DeclarativeAgent.from_definition(definition)
                if not issubclass(agent_cls, BaseAgent):
                    logger.warning(f"声明式 Agent {name} 不是 BaseAgent 的子类，跳过")
                    continue
                cls._agent_classes[name] = agent_cls
                registered.append(name)
                logger.info(f"注册声明式 Agent: {name}")
            except Exception as e:
                logger.warning(f"注册声明式 Agent {name} 失败: {e}")

        return registered


class AgentAutoLoader:
    """
    智能体自动加载器

    自动发现和加载core/agents目录下的所有智能体类。

    Usage:
        ```python
        # 扫描并加载所有智能体
        loader = AgentAutoLoader()
        loader.scan()

        # 获取扫描结果
        print(f"已加载 {len(loader.loaded_agents)} 个智能体")
        ```
    """

    def __init__(self, base_path: str | None = None):
        """
        初始化自动加载器

        Args:
            base_path: 智能体目录路径，默认为 core/agents
        """
        if base_path is None:
            # 获取core/agents目录的绝对路径
            current_file = Path(__file__).resolve()
            self.base_path = current_file.parent
        else:
            self.base_path = Path(base_path)

        self.loaded_agents: list[str] = []
        self.failed_loads: dict[str, str] = {}
        self.logger = logging.getLogger("agent.autoloader")

    def scan(
        self,
        pattern: str = "*_agent.py",
        recursive: bool = True,
        register: bool = True
    ) -> None:
        """
        扫描并加载智能体类

        Args:
            pattern: 文件匹配模式
            recursive: 是否递归扫描子目录
            register: 是否注册到AgentFactory

        Note:
            所有继承自BaseAgent的类都会被自动注册
        """
        self.logger.info(f"开始扫描智能体: {self.base_path}")

        # 查找所有匹配的文件
        if recursive:
            files = self.base_path.rglob(pattern)
        else:
            files = self.base_path.glob(pattern)

        for file_path in files:
            self._load_file(file_path)

        self.logger.info(
            f"扫描完成: 成功加载 {len(self.loaded_agents)} 个智能体, "
            f"失败 {len(self.failed_loads)} 个"
        )

    def _load_file(self, file_path: Path) -> None:
        """
        加载单个Python文件中的智能体类

        Args:
            file_path: Python文件路径
        """
        # 计算模块路径
        relative_path = file_path.relative_to(self.base_path.parent)
        module_path = str(relative_path.with_suffix("")).replace("/", ".")

        try:
            # 动态导入模块
            module = importlib.import_module(f"core.agents.{module_path}")

            # 查找所有BaseAgent子类
            for _name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and
                    issubclass(obj, BaseAgent) and
                    obj is not BaseAgent and
                    not obj.__name__.startswith("_")):

                    # 注册智能体类
                    agent_name = AgentFactory.register_agent_class(obj)
                    self.loaded_agents.append(agent_name)
                    self.logger.info(f"加载智能体: {agent_name} from {file_path.name}")

        except ImportError as e:
            error_msg = f"导入模块失败: {e}"
            self.failed_loads[str(file_path)] = error_msg
            self.logger.warning(f"加载 {file_path} 失败: {e}")

        except Exception as e:
            error_msg = f"加载失败: {e}"
            self.failed_loads[str(file_path)] = error_msg
            self.logger.error(f"加载 {file_path} 失败: {e}")

    def get_summary(self) -> dict[str, Any]:
        """
        获取扫描摘要

        Returns:
            包含扫描结果的字典
        """
        return {
            "loaded_agents": self.loaded_agents,
            "loaded_count": len(self.loaded_agents),
            "failed_loads": self.failed_loads,
            "failed_count": len(self.failed_loads)
        }


# ============ 辅助函数 ============


async def create_agent_from_config(config: dict[str, Any]) -> BaseAgent:
    """
    从配置字典创建智能体

    Args:
        config: 配置字典，必须包含 name 字段
            {
                "name": "xiaona-legal",
                "config": {...}  # 可选
            }

    Returns:
        智能体实例
    """
    name = config.get("name")
    if not name:
        raise ValueError("配置必须包含 name 字段")

    agent_config = config.get("config")
    return await AgentFactory.create_async(name, agent_config)


async def create_agents_from_yaml(yaml_path: str) -> list[BaseAgent]:
    """
    从YAML配置文件批量创建智能体

    Args:
        yaml_path: YAML配置文件路径

    Returns:
        智能体实例列表

    Note:
        YAML格式:
            agents:
              - name: xiaona-legal
                config:
                  llm_model: claude-3.5-sonnet
              - name: xiaonuo-orchestrator
                enabled: true
    """
    try:
        import yaml
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except ImportError:
        raise ImportError("需要安装PyYAML: pip install pyyaml") from None

    agents_config = data.get("agents", [])
    return await AgentFactory.create_many(agents_config)


# ============ 便捷导入 ============

# 导出
__all__ = [
    "AgentFactory",
    "AgentAutoLoader",
    "create_agent_from_config",
    "create_agents_from_yaml"
]


# asyncio导入（用于create_many方法）
import asyncio
