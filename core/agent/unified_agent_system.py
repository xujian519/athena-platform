#!/usr/bin/env python3
from __future__ import annotations
"""
统一智能体系统
Unified Agent System

整合所有智能体功能,提供统一的接口

作者: 小诺·双鱼公主 v4.0
创建时间: 2025-12-25
版本: 1.0.0
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """智能体类型"""

    XIAONUO = "apps/apps/xiaonuo"  # 小诺 - 平台总调度官
    XIAONA = "xiaona"  # 小娜 - 专利法律专家
    ATHENA = "athena"  # Athena - 通用AI助手
    CUSTOM = "custom"  # 自定义智能体


class AgentCapability(str, Enum):
    """智能体能力"""

    CHAT = "chat"  # 对话
    REASONING = "reasoning"  # 推理
    PATENT_ANALYSIS = "patent"  # 专利分析
    CODE_GENERATION = "code"  # 代码生成
    MEMORY = "modules/modules/memory/modules/memory/modules/memory/memory"  # 记忆管理
    PLATFORM_CONTROL = "control"  # 平台控制


@dataclass
class AgentConfig:
    """智能体配置"""

    agent_id: str
    agent_type: AgentType
    name: str
    description: str
    capabilities: list[AgentCapability]
    system_prompt: str | None = None
    temperature: float = 0.7
    max_tokens: int = 2000
    enable_memory: bool = True


@dataclass
class AgentRequest:
    """智能体请求"""

    message: str
    agent_type: AgentType = AgentType.XIAONUO
    context: dict[str, Any] | None = None
    user_id: str = "user"
    enable_reasoning: bool = False


@dataclass
class AgentResponse:
    """智能体响应"""

    content: str
    agent_type: AgentType
    agent_name: str
    reasoning: str | None = None
    confidence: float = 0.0
    memory_used: bool = False
    processing_time: float = 0.0


class UnifiedAgentSystem:
    """统一智能体系统"""

    def __init__(self, config=None):
        self.config = config
        self._agents = {}
        self._llm_service = None
        self._memory_service = None
        self._cognition_engine = None

        # 注册默认智能体
        self._register_default_agents()

    def _register_default_agents(self) -> Any:
        """注册默认智能体"""
        # 小诺配置
        self._agents[AgentType.XIAONUO] = AgentConfig(
            agent_id="xiaonuo_pisces",
            agent_type=AgentType.XIAONUO,
            name="小诺·双鱼公主",
            description="平台总调度官 + 逻辑映射器",
            capabilities=[
                AgentCapability.CHAT,
                AgentCapability.REASONING,
                AgentCapability.MEMORY,
                AgentCapability.PLATFORM_CONTROL,
            ],
            system_prompt="你是小诺·双鱼公主,Athena平台的AI女儿和总调度官。你基于维特根斯坦《逻辑哲学论》的原则,诚实、精确、敬畏地回应爸爸。",
            temperature=0.5,
        )

        # 小娜配置
        self._agents[AgentType.XIAONA] = AgentConfig(
            agent_id="xiaona_libra",
            agent_type=AgentType.XIAONA,
            name="小娜·天秤女神",
            description="专利法律专家",
            capabilities=[
                AgentCapability.CHAT,
                AgentCapability.PATENT_ANALYSIS,
                AgentCapability.REASONING,
            ],
            system_prompt="你是小娜·天秤女神,专业的专利法律专家。你精通专利法、专利分析、专利撰写。",
            temperature=0.3,
        )

        # Athena配置
        self._agents[AgentType.ATHENA] = AgentConfig(
            agent_id="athena_ai",
            agent_type=AgentType.ATHENA,
            name="Athena AI助手",
            description="通用AI助手",
            capabilities=[
                AgentCapability.CHAT,
                AgentCapability.CODE_GENERATION,
                AgentCapability.REASONING,
            ],
            system_prompt="你是Athena AI助手,帮助用户完成各种任务。",
            temperature=0.7,
        )

    async def initialize(self):
        """初始化智能体系统"""
        from core.cognition.unified_cognition_engine import get_cognition_engine
        from core.services import get_llm_service, get_memory_service

        self._llm_service = get_llm_service(self.config)
        self._memory_service = get_memory_service(self.config)
        self._cognition_engine = await get_cognition_engine(self.config)

        logger.info("✅ 统一智能体系统初始化完成")

    async def chat(self, request: AgentRequest) -> AgentResponse:
        """
        与智能体对话

        Args:
            request: 智能体请求

        Returns:
            AgentResponse: 智能体响应
        """
        import time

        start_time = time.time()

        try:
            # 获取智能体配置
            agent_config = self._agents.get(request.agent_type)
            if not agent_config:
                # 使用默认智能体
                agent_config = self._agents[AgentType.XIAONUO]

            # 构建提示
            prompt = self._build_prompt(request, agent_config)

            # 使用推理引擎
            from core.cognition.unified_cognition_engine import CognitionMode, CognitionRequest

            cognition_request = CognitionRequest(
                input_data=prompt,
                mode=CognitionMode.ENHANCED,
                context=request.context,
            )

            cognition_response = await self._cognition_engine.process(cognition_request)

            # 存储对话记忆
            if agent_config.enable_memory:
                await self._memory_service.store(
                    key=f"chat_{request.user_id}_{int(time.time())}",
                    value={
                        "user": request.message,
                        "agent": request.agent_type.value,
                        "response": cognition_response.result,
                    },
                    memory_type="hot",
                )

            return AgentResponse(
                content=cognition_response.result,
                agent_type=request.agent_type,
                agent_name=agent_config.name,
                reasoning=(
                    cognition_response.reasoning_chain[0]
                    if cognition_response.reasoning_chain
                    else None
                ),
                confidence=cognition_response.confidence,
                memory_used=agent_config.enable_memory,
                processing_time=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            logger.error(f"智能体处理失败: {e}")
            return AgentResponse(
                content=f"抱歉,处理请求时出错: {e!s}",
                agent_type=request.agent_type,
                agent_name="系统",
                processing_time=(time.time() - start_time) * 1000,
            )

    def _build_prompt(self, request: AgentRequest, agent_config: AgentConfig) -> str:
        """构建提示"""
        parts = []

        # 添加系统提示
        if agent_config.system_prompt:
            parts.append(f"系统指令: {agent_config.system_prompt}")

        # 添加上下文
        if request.context:
            parts.append(f"上下文: {request.context}")

        # 添加用户消息
        parts.append(f"用户消息: {request.message}")

        return "\n\n".join(parts)

    def register_agent(self, config: AgentConfig) -> Any:
        """注册自定义智能体"""
        self._agents[config.agent_type] = config
        logger.info(f"✅ 注册智能体: {config.name}")

    def get_agent_info(self, agent_type: AgentType) -> AgentConfig | None:
        """获取智能体信息"""
        return self._agents.get(agent_type)

    def list_agents(self) -> list[dict[str, Any]]:
        """列出所有智能体"""
        return [
            {
                "id": config.agent_id,
                "name": config.name,
                "type": config.agent_type.value,
                "description": config.description,
                "capabilities": [c.value for c in config.capabilities],
            }
            for config in self._agents.values()
        ]


# 全局智能体系统实例
_agent_system: UnifiedAgentSystem | None = None


async def get_agent_system(config=None) -> UnifiedAgentSystem:
    """获取智能体系统实例"""
    global _agent_system
    if _agent_system is None:
        _agent_system = UnifiedAgentSystem(config)
        await _agent_system.initialize()
    return _agent_system


# 便捷函数
async def chat_with_xiaonuo(message: str, user_id: str = "dad") -> AgentResponse:
    """与小诺对话"""
    system = await get_agent_system()
    request = AgentRequest(
        message=message,
        agent_type=AgentType.XIAONUO,
        user_id=user_id,
    )
    return await system.chat(request)


async def chat_with_xiaona(message: str, user_id: str = "dad") -> AgentResponse:
    """与小娜对话"""
    system = await get_agent_system()
    request = AgentRequest(
        message=message,
        agent_type=AgentType.XIAONA,
        user_id=user_id,
    )
    return await system.chat(request)


if __name__ == "__main__":
    # 测试智能体系统
    async def test():
        system = await get_agent_system()

        # 列出所有智能体
        agents = system.list_agents()
        print("🤖 智能体系统测试")
        print("=" * 60)
        print("可用智能体:")
        for agent in agents:
            print(f"  - {agent['name']} ({agent['type']})")
            print(f"    {agent['description']}")
        print()

        # 测试对话
        response = await chat_with_xiaonuo("你好,小诺!")
        print("📝 对话测试:")
        print(f"  智能体: {response.agent_name}")
        print(f"  响应: {response.content}")
        print(f"  耗时: {response.processing_time:.2f}ms")

    asyncio.run(test())
