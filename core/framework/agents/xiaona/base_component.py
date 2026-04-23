"""
小娜基础组件类

所有小娜专业智能体的基类，定义统一的接口和生命周期。
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# LLM管理器导入
try:
    from core.ai.llm.base import LLMRequest, LLMResponse
    from core.ai.llm.unified_llm_manager import UnifiedLLMManager, get_unified_llm_manager
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    UnifiedLLMManager = None  # type: ignore
    get_unified_llm_manager = None  # type: ignore
    LLMRequest = None  # type: ignore
    LLMResponse = None  # type: ignore


class AgentStatus(Enum):
    """智能体状态枚举"""
    IDLE = "idle"           # 空闲
    BUSY = "busy"           # 忙碌
    ERROR = "error"         # 错误
    COMPLETED = "completed" # 完成


@dataclass
class AgentCapability:
    """智能体能力描述"""
    name: str  # 能力名称
    description: str  # 能力描述
    input_types: List[str]  # 支持的输入类型
    output_types: List[str]  # 输出类型
    estimated_time: float  # 预估执行时间（秒）


@dataclass
class AgentExecutionContext:
    """智能体执行上下文"""
    session_id: str                      # 会话ID
    input_data: Optional[Dict[str, Any]]  # 输入数据
    config: Optional[Dict[str, Any]]  # 配置参数
    metadata: Optional[Dict[str, Any]]  # 元数据

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@dataclass
class AgentExecutionResult:
    """智能体执行结果"""
    agent_id: str                        # 智能体ID
    status: AgentStatus                  # 执行状态
    output_data: Optional[Dict[str, Any]] = None  # 输出数据
    metadata: Optional[Dict[str, Any]] = None  # 元数据

    error_message: Optional[str] = None  # 错误信息
    execution_time: float = 0.0          # 执行时间（秒）


    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseXiaonaComponent(ABC):
    """
    小娜专业智能体基类

    所有专业智能体都必须继承此类并实现抽象方法。
    提供统一的生命周期管理、能力描述和执行接口。
    """

    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):

        """
        初始化智能体

        Args:
            agent_id: 智能体唯一标识
            config: 配置参数
        """
        self.agent_id = agent_id
        self.config = config or {}
        self.status = AgentStatus.IDLE
        self._capabilities: list = []

        # 初始化日志
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # LLM管理器（延迟初始化）
        self._llm_manager: Optional[UnifiedLLMManager ] = None
        self._llm_config: Optional[Dict[str, Any]] = {}

        self._llm_initialized = False

        # 子类初始化
        self._initialize()

    @abstractmethod
    def _initialize(self) -> str:
        """
        智能体初始化钩子

        子类应该在此方法中：
        1. 注册能力（self._register_capabilities）
        2. 初始化LLM客户端
        3. 加载提示词
        4. 初始化工具
        """
        pass

    @abstractmethod
    async def execute(self, context: AgentExecutionContext) -> str:
        """
        执行智能体任务

        Args:
            context: 执行上下文

        Returns:
            执行结果
        """
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        获取系统提示词

        Returns:
            系统提示词字符串
        """
        pass

    def _register_capabilities(self, capabilities: list) -> str:
        """
        注册智能体能力

        Args:
            capabilities: 能力列表（支持AgentCapability对象或字典）
        """
        # 转换字典为AgentCapability对象
        converted_capabilities = []
        for cap in capabilities:
            if isinstance(cap, dict):
                converted_capabilities.append(AgentCapability(
                    name=cap["name"],
                    description=cap["description"],
                    input_types=cap["input_types"],
                    output_types=cap["output_types"],
                    estimated_time=cap.get("estimated_time", 30.0)
                ))
            else:
                converted_capabilities.append(cap)

        self._capabilities = converted_capabilities
        self.logger.info(f"注册 {len(converted_capabilities)} 个能力: {[c.name for c in converted_capabilities]}")

    def get_capabilities(self) -> list[AgentCapability]:
        """
        获取智能体能力列表

        Returns:
            能力列表
        """
        return self._capabilities.copy()

    def has_capability(self, capability_name: str) -> str:
        """
        检查是否具备某项能力

        Args:
            capability_name: 能力名称

        Returns:
            是否具备该能力
        """
        return any(c.name == capability_name for c in self._capabilities)

    def get_info(self) -> Dict[str, Any]:
        """
        获取智能体信息

        Returns:
            智能体信息字典
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": self.__class__.__name__,
            "status": self.status.value,
            "capabilities": [
                {
                    "name": c.name,
                    "description": c.description,
                    "input_types": c.input_types,
                    "output_types": c.output_types,
                    "estimated_time": c.estimated_time,
                }
                for c in self._capabilities
            ],
        }

    def validate_input(self, context: AgentExecutionContext) -> str:
        """
        验证输入数据

        Args:
            context: 执行上下文

        Returns:
            验证是否通过
        """
        # 基础验证
        if not context.session_id:
            self.logger.error("缺少session_id")
            return False

        if not context.task_id:
            self.logger.error("缺少task_id")
            return False

        return True

    async def _execute_with_monitoring(
        self,
        context: AgentExecutionContext
    ) -> str:
        """
        带监控的执行方法

        Args:
            context: 执行上下文

        Returns:
            执行结果
        """
        # 更新状态
        self.status = AgentStatus.BUSY
        context.start_time = datetime.now()

        self.logger.info(f"开始执行任务: {context.task_id}")

        try:
            # 执行任务
            result = await self.execute(context)

            # 记录执行时间
            context.end_time = datetime.now()
            execution_time = (context.end_time - context.start_time).total_seconds()
            result.execution_time = execution_time

            # 更新状态
            if result.status == AgentStatus.COMPLETED:
                self.status = AgentStatus.IDLE
                self.logger.info(f"任务完成: {context.task_id}, 耗时: {execution_time:.2f}秒")
            else:
                self.status = AgentStatus.ERROR
                self.logger.error(f"任务失败: {context.task_id}, 错误: {result.error_message}")

            return result

        except Exception as e:
            # 异常处理
            context.end_time = datetime.now()
            execution_time = (context.end_time - context.start_time).total_seconds()

            self.status = AgentStatus.ERROR
            self.logger.exception(f"执行异常: {context.task_id}")

            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                output_data=None,
                error_message=str(e),
                execution_time=execution_time,
            )

    # ========== LLM集成方法 ==========

    def _ensure_llm_initialized(self) -> str:
        """
        确保LLM管理器已初始化

        如果LLM管理器未初始化，则进行初始化。
        注意：这是一个同步方法，如果需要异步初始化，应该在外部处理。
        """
        if self._llm_initialized:
            return

        try:
            if LLM_AVAILABLE and get_unified_llm_manager is not None:
                # 注意：这里使用同步方式获取管理器
                # 如果get_unified_llm_manager()是异步的，需要在外部先初始化
                import inspect
                if inspect.iscoroutinefunction(get_unified_llm_manager):
                    # 异步函数，暂时跳过，等待外部初始化
                    self.logger.warning(f"get_unified_llm_manager是异步函数，需要外部初始化: {self.agent_id}")
                    self._llm_manager = None
                else:
                    self._llm_manager = get_unified_llm_manager()

                self._llm_config = self._load_llm_config()
                self._llm_initialized = True
                if self._llm_manager is not None:
                    self.logger.info(f"LLM管理器初始化成功: {self.agent_id}")
            else:
                self.logger.warning(f"LLM模块不可用: {self.agent_id}")
                self._llm_initialized = True  # 标记为已尝试初始化
        except Exception as e:
            self.logger.error(f"LLM管理器初始化失败: {e}")
            self._llm_initialized = True  # 标记为已尝试初始化，避免重复尝试

    async def _call_llm(
        self,
        prompt: str,
        task_type: str = "general",
        **kwargs
    ) -> str:
        """
        调用LLM生成响应

        Args:
            prompt: 提示词
            task_type: 任务类型（用于选择模型）
            **kwargs: 额外的LLM参数

        Returns:
            LLM响应文本

        Raises:
            RuntimeError: 如果LLM未初始化或调用失败
        """
        self._ensure_llm_initialized()

        if self._llm_manager is None:
            raise RuntimeError(f"LLM管理器未初始化: {self.agent_id}")

        try:
            # 构建LLM请求
            context = self._build_llm_context(task_type)
            params = self._merge_llm_params(task_type, kwargs)

            # 创建请求对象（使用正确的字段名）
            if LLMRequest is not None:
                request = LLMRequest(
                    message=prompt,  # 注意：使用message而不是prompt
                    task_type=task_type,
                    context=context,
                    temperature=params.get("temperature", 0.7),
                    max_tokens=params.get("max_tokens", 4096),
                    stream=params.get("enable_streaming", False),
                )
            else:
                # 降级处理：直接传递参数
                request = None

            # 调用LLM
            if request is not None:
                response: LLMResponse = await self._llm_manager.generate_async(request)
                return response.content
            else:
                # 降级处理：使用简化接口
                result = await self._llm_manager.generate_async(
                    message=prompt,
                    task_type=task_type,
                    **params
                )
                if isinstance(result, str):
                    return result
                elif hasattr(result, 'content'):
                    return result.content
                else:
                    return str(result)

        except Exception as e:
            self.logger.error(f"LLM调用失败: {e}")
            raise

    async def _call_deepseek(
        self,
        prompt: str,
        task_type: str = "general",
        **kwargs
    ) -> str:
        """
        调用DeepSeek云端模型

        Args:
            prompt: 提示词
            task_type: 任务类型
            **kwargs: 额外的LLM参数

        Returns:
            LLM响应文本

        Raises:
            RuntimeError: DeepSeek调用失败
        """
        try:
            from core.ai.llm.deepseek_client import get_deepseek_client

            # 获取DeepSeek客户端
            client = get_deepseek_client()

            # 构建系统提示
            self.get_system_prompt()

            # 调用DeepSeek
            response = await client.reason(
                problem=prompt,
                task_type=task_type,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 4096),
            )

            return response.answer

        except ImportError as e:
            raise RuntimeError(f"DeepSeek客户端不可用: {e}")
        except Exception as e:
            raise RuntimeError(f"DeepSeek调用失败: {e}")

    async def _call_local_8009(
        self,
        prompt: str,
        task_type: str = "general",
        **kwargs
    ) -> str:
        """
        调用本地8009端口模型

        Args:
            prompt: 提示词
            task_type: 任务类型
            **kwargs: 额外的LLM参数

        Returns:
            LLM响应文本

        Raises:
            RuntimeError: 本地8009调用失败
        """
        try:
            from core.ai.llm.adapters.local_8009_adapter import get_local_8009_adapter

            # 获取本地8009适配器
            adapter = await get_local_8009_adapter()

            # 构建系统提示
            system_prompt = self.get_system_prompt()

            # 调用本地模型
            response = await adapter.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 4096),
            )

            return response

        except ImportError as e:
            raise RuntimeError(f"本地8009适配器不可用: {e}")
        except Exception as e:
            raise RuntimeError(f"本地8009调用失败: {e}")

    async def _call_llm_with_fallback(
        self,
        prompt: str,
        task_type: str = "general",
        fallback_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        带智能降级机制的LLM调用

        降级策略：
        1. 优先调用云端DeepSeek模型
        2. 失败时降级到本地8009端口模型
        3. 复杂任务禁止使用规则执行

        Args:
            prompt: 主要提示词
            task_type: 任务类型
            fallback_prompt: 降级提示词（保留兼容性，未使用）
            **kwargs: 额外的LLM参数

        Returns:
            LLM响应文本

        Raises:
            RuntimeError: 所有LLM调用均失败
        """
        # 策略1: 优先调用DeepSeek云端模型
        try:
            self.logger.info(f"📡 尝试DeepSeek云端模型: {task_type}")
            response = await self._call_deepseek(prompt, task_type, **kwargs)
            self.logger.info("✅ DeepSeek云端模型调用成功")
            return response
        except Exception as e:
            self.logger.warning(f"⚠️ DeepSeek云端模型调用失败: {e}")

        # 策略2: 降级到本地8009端口模型
        try:
            self.logger.info(f"📡 降级到本地8009端口模型: {task_type}")
            response = await self._call_local_8009(prompt, task_type, **kwargs)
            self.logger.info("✅ 本地8009端口模型调用成功")
            return response
        except Exception as e:
            self.logger.error(f"❌ 本地8009端口模型调用失败: {e}")

        # 策略3: 所有LLM均失败，抛出异常（禁止使用规则执行复杂任务）
        complex_tasks = {
            "invalidation_analysis",
            "grounds_analysis",
            "evidence_strategy",
            "creativity_analysis",
            "novelty_analysis",
        }

        if task_type in complex_tasks:
            raise RuntimeError(
                f"复杂任务'{task_type}'的LLM调用全部失败，禁止使用规则执行。"
                f"原始错误: DeepSeek失败 -> 本地8009失败"
            )
        else:
            # 简单任务可以抛出异常，由调用方决定是否使用规则
            raise RuntimeError(
                f"所有LLM调用均失败: DeepSeek -> 本地8009。"
                f"最后错误: {e}"
            )

    def _build_llm_context(self, task_type: str) -> Dict[str, Any]:
        """
        构建LLM上下文

        Args:
            task_type: 任务类型

        Returns:
            上下文字典
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": self.__class__.__name__,
            "task_type": task_type,
            "capabilities": [c.name for c in self._capabilities],

            "system_prompt": self.get_system_prompt(),
        }

    def _load_llm_config(self) -> Dict[str, Any]:
        """
        加载LLM配置

        Returns:
            LLM配置字典
        """
        # 1. 从实例配置中获取
        if "llm_config" in self.config:
            return self.config["llm_config"]

        # 2. 从全局配置中获取
        try:
            from core.config.xiaona_config import config_manager
            if hasattr(config_manager, 'export_config'):
                global_config = config_manager.export_config()
                if "llm" in global_config:
                    return global_config["llm"]
        except ImportError:
            pass

        # 3. 使用默认配置
        return {
            "model": "claude-3-5-sonnet-20241022",
            "temperature": 0.7,
            "max_tokens": 4096,
            "timeout": 30.0,
        }

    def _merge_llm_params(
        self,
        task_type: str,
        user_params: Optional[Dict[str, Any]]

    ) -> Dict[str, Any]:
        """
        合并LLM参数

        Args:
            task_type: 任务类型
            user_params: 用户提供的参数

        Returns:
            合并后的参数字典
        """
        # 基础配置
        base_params = self._llm_config.copy()

        # 任务类型特定配置
        try:
            from core.config.xiaona_config import LLM_TASK_TYPE_MAPPING
            if task_type in LLM_TASK_TYPE_MAPPING:
                task_config = LLM_TASK_TYPE_MAPPING[task_type]
                base_params.update(task_config)
        except (ImportError, AttributeError):
            pass

        # 用户参数优先级最高
        base_params.update(user_params)

        return base_params

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(agent_id='{self.agent_id}', status='{self.status.value}')>"
