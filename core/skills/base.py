from __future__ import annotations
"""
技能基类和核心数据模型
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import yaml


class SkillCategory(Enum):
    """技能分类"""
    PATENT_ANALYSIS = "patent_analysis"      # 专利分析
    LEGAL_RESEARCH = "legal_research"        # 法律检索
    DOCUMENT_GENERATION = "document_generation"  # 文档生成
    DATA_VISUALIZATION = "data_visualization"    # 数据可视化
    WEB_SEARCH = "web_search"                # 网络搜索
    CUSTOM = "custom"                        # 自定义


class SkillStatus(Enum):
    """技能状态"""
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class SkillMetadata:
    """技能元数据

    从 SKILL.md 文件的 YAML 前置元数据解析而来。
    """
    name: str                              # 技能名称（唯一标识）
    display_name: str                       # 显示名称
    description: str                        # 技能描述
    version: str = "1.0.0"                 # 版本号
    author: str = "Athena Team"            # 作者
    license: str = "MIT"                   # 许可证
    category: SkillCategory = SkillCategory.CUSTOM  # 分类
    tags: list[str] = field(default_factory=list)  # 标签
    dependencies: list[str] = field(default_factory=list)  # 依赖的其他技能
    parameters: dict[str, Any] = field(default_factory=dict)  # 参数定义
    examples: list[dict] = field(default_factory=list)  # 使用示例
    enabled: bool = True                   # 是否启用

    # 性能指标
    avg_execution_time: Optional[float] = None  # 平均执行时间（秒）
    success_rate: float = 1.0               # 成功率

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "license": self.license,
            "category": self.category.value,
            "tags": self.tags,
            "dependencies": self.dependencies,
            "parameters": self.parameters,
            "examples": self.examples,
            "enabled": self.enabled,
            "avg_execution_time": self.avg_execution_time,
            "success_rate": self.success_rate,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SkillMetadata":
        """从字典创建"""
        # 处理 category 枚举
        if "category" in data and isinstance(data["category"], str):
            data["category"] = SkillCategory(data["category"])

        return cls(**data)

    @classmethod
    def from_yaml(cls, yaml_content: str) -> "SkillMetadata":
        """从 YAML 内容创建"""
        data = yaml.safe_load(yaml_content)
        return cls.from_dict(data)


@dataclass
class SkillResult:
    """技能执行结果"""
    success: bool                          # 是否成功
    data: Any                              # 返回数据
    error: Optional[str] = None            # 错误信息
    execution_time: float = 0.0            # 执行时间（秒）
    metadata: dict[str, Any] = field(default_factory=dict)  # 额外元数据

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time": self.execution_time,
            "metadata": self.metadata,
        }


class SkillException(Exception):
    """技能异常基类"""
    pass


class SkillNotFoundException(SkillException):
    """技能未找到异常"""
    pass


class SkillExecutionException(SkillException):
    """技能执行异常"""
    pass


class Skill(ABC):
    """技能抽象基类

    所有技能必须继承此类并实现 execute 方法。
    """

    def __init__(self, metadata: SkillMetadata):
        self._metadata = metadata
        self._status = SkillStatus.LOADED

    @property
    def metadata(self) -> SkillMetadata:
        """获取技能元数据"""
        return self._metadata

    @property
    def status(self) -> SkillStatus:
        """获取技能状态"""
        return self._status

    @abstractmethod
    async def execute(self, **kwargs) -> SkillResult:
        """执行技能

        Args:
            **kwargs: 技能参数

        Returns:
            SkillResult: 执行结果

        Raises:
            SkillExecutionException: 执行失败时抛出
        """
        pass

    async def validate(self, **kwargs) -> bool:
        """验证参数

        Args:
            **kwargs: 技能参数

        Returns:
            bool: 参数是否有效

        Raises:
            ValueError: 参数无效时抛出
        """
        # 检查必需参数
        required_params = self._metadata.parameters.get("required", [])
        for param in required_params:
            if param not in kwargs:
                raise ValueError(f"Missing required parameter: {param}")

        # 检查参数类型
        param_types = self._metadata.parameters.get("types", {})
        for param, expected_type in param_types.items():
            if param in kwargs and not isinstance(kwargs[param], expected_type):
                raise ValueError(
                    f"Parameter '{param}' must be {expected_type.__name__}, "
                    f"got {type(kwargs[param]).__name__}"
                )

        return True

    async def initialize(self) -> None:
        """初始化技能（可选重写）"""
        self._status = SkillStatus.ENABLED

    async def cleanup(self) -> None:
        """清理资源（可选重写）"""
        pass

    def enable(self) -> None:
        """启用技能"""
        self._metadata.enabled = True
        self._status = SkillStatus.ENABLED

    def disable(self) -> None:
        """禁用技能"""
        self._metadata.enabled = False
        self._status = SkillStatus.DISABLED

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name={self._metadata.name}, "
            f"version={self._metadata.version}, "
            f"status={self._status.value})"
        )


class FunctionSkill(Skill):
    """函数技能

    将普通函数包装为技能的便捷类。
    """

    def __init__(
        self,
        metadata: SkillMetadata,
        func: callable,
        is_async: bool = True
    ):
        super().__init__(metadata)
        self._func = func
        self._is_async = is_async

    async def execute(self, **kwargs) -> SkillResult:
        """执行包装的函数"""
        import time
        start_time = time.time()

        try:
            await self.validate(**kwargs)

            if self._is_async:
                result = await self._func(**kwargs)
            else:
                result = self._func(**kwargs)

            execution_time = time.time() - start_time

            return SkillResult(
                success=True,
                data=result,
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return SkillResult(
                success=False,
                error=str(e),
                execution_time=execution_time,
            )


def skill_function(
    name: str,
    display_name: str,
    description: str,
    category: SkillCategory = SkillCategory.CUSTOM,
    **metadata_kwargs
):
    """技能函数装饰器

    将普通函数装饰为技能。

    Example:
        @skill_function(
            name="my_skill",
            display_name="我的技能",
            description="这是一个示例技能"
        )
        async def my_function(param1: str, param2: int) -> dict:
            return {"result": "success"}
    """
    def decorator(func):
        metadata = SkillMetadata(
            name=name,
            display_name=display_name,
            description=description,
            category=category,
            **metadata_kwargs
        )
        return FunctionSkill(metadata, func, is_async=asyncio.iscoroutinefunction(func))
    return decorator
