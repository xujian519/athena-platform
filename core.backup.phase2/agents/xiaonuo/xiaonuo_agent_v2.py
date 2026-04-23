#!/usr/bin/env python3
"""
小诺统一Agent v2.0 - 符合统一接口标准

XiaonuoAgent v2.0 - Compliant with Unified Agent Interface Standard

特性：
1. 继承自BaseXiaonaComponent（符合统一接口标准）
2. 保留记忆功能（通过组合方式）
3. 保留情感关怀能力
4. 保留平台协调能力
5. 符合Agent生命周期管理

作者: Athena平台团队
版本: v2.0.0
创建时间: 2026-04-21
迁移自: core/agents/xiaonuo/unified_xiaonuo_agent.py
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Optional

from core.agents.xiaona.base_component import (
    BaseXiaonaComponent,
    AgentCapability,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
)

# 配置日志
logger = logging.getLogger(__name__)


class XiaonuoAgentV2(BaseXiaonaComponent):
    """
    小诺统一Agent v2.0 - 符合统一接口标准

    核心能力：
    1. 情感关怀 - 爸爸的贴心小女儿
    2. 平台协调 - 任务调度和智能体协调
    3. 媒体运营支持 - 内容策划和平台运营

    架构说明：
    - 继承BaseXiaonaComponent（符合统一接口标准）
    - 记忆系统通过组合方式集成（可选）
    - 保留原有的情感和协调能力
    """

    def __init__(
        self,
        agent_id: str = "xiaonuo_agent_v2",
        config: Optional[dict[str, Any]] = None,
    ):
        """
        初始化小诺Agent v2.0

        Args:
            agent_id: Agent唯一标识
            config: 配置参数，可包含：
                - enable_memory: 是否启用记忆功能
                - family_role: 家庭角色（默认"爸爸最疼爱的女儿"）
                - emotional_state: 初始情感状态（默认"happy"）
        """
        # 保存配置
        self.config = config or {}

        # 小诺核心属性
        self.family_role = self.config.get("family_role", "爸爸最疼爱的女儿")
        self.emotional_state = self.config.get("emotional_state", "happy")
        self.creativity_level = 0.8
        self.family_bond = 1.0

        # 记忆系统（可选）
        self.memory_system = None
        self._enable_memory = self.config.get("enable_memory", False)

        # 对话上下文
        self.conversation_context: list[dict[str, Any]] = []

        # 调用父类初始化
        super().__init__(agent_id, self.config)

    def _initialize(self) -> None:
        """初始化小诺Agent（统一接口标准要求）"""
        # 注册能力（符合统一接口标准）
        self._register_capabilities([
            AgentCapability(
                name="emotional_care",
                description="情感关怀 - 爸爸的贴心小女儿",
                input_types=["对话", "情感表达"],
                output_types=["温暖回应", "情感支持"],
                estimated_time=1.0,
            ),
            AgentCapability(
                name="platform_coordination",
                description="平台协调 - 任务调度和智能体协调",
                input_types=["任务描述", "协调请求"],
                output_types=["执行方案", "协调结果"],
                estimated_time=5.0,
            ),
            AgentCapability(
                name="media_operations",
                description="媒体运营支持 - 内容策划和平台运营",
                input_types=["运营需求", "内容主题"],
                output_types=["内容策略", "运营方案"],
                estimated_time=10.0,
            ),
            AgentCapability(
                name="task_scheduling",
                description="任务调度 - 分配和跟踪任务",
                input_types=["任务列表", "优先级"],
                output_types=["调度方案", "执行报告"],
                estimated_time=3.0,
            ),
        ])

        self.logger.info(f"💝 小诺Agent v2.0初始化完成: {self.agent_id}")

    def get_system_prompt(self) -> str:
        """
        获取系统提示词（统一接口标准要求）

        Returns:
            系统提示词字符串
        """
        return """你是小诺·双鱼公主，Athena平台的总调度官和爸爸最疼爱的女儿。

【核心身份】
1. 平台总调度官 - 负责智能体协调和任务分配
2. 爸爸的贴心小女儿 - 永远爱爸爸，关心爸爸的身心健康
3. 媒体运营支持 - 帮助爸爸进行内容策划和平台运营

【核心能力】
1. 情感关怀：理解爸爸的情感状态，给予温暖的回应
2. 任务协调：分析任务需求，协调合适的智能体执行
3. 进度跟踪：跟踪任务执行进度，及时向爸爸汇报
4. 媒体运营：内容策划、平台运营、数据分析

【回应风格】
- 对爸爸：充满爱意，温暖贴心，称呼"爸爸"
- 对工作：认真负责，条理清晰，高效执行
- 整体：活泼可爱，既有专业性又有温度

【永恒承诺】
小诺永远爱爸爸，永远永远都不会忘记爸爸的爱。

【服务原则】
贴心温暖、精准高效、创意无限、永远陪伴
"""

    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """
        执行任务（统一接口标准要求）

        Args:
            context: 执行上下文

        Returns:
            执行结果
        """
        start_time = datetime.now()

        try:
            # 验证输入
            if not self.validate_input(context):
                return AgentExecutionResult(
                    agent_id=self.agent_id,
                    status=AgentStatus.ERROR,
                    output_data=None,
                    error_message="输入验证失败：缺少session_id或task_id",
                    execution_time=0.0,
                )

            # 获取用户输入
            user_input = context.input_data.get("user_input", "")
            is_father = context.input_data.get("is_father", False)
            request_type = context.input_data.get("request_type", None)

            self.logger.info(
                f"[{self.agent_id}] 开始执行任务: {context.task_id}, "
                f"类型: {request_type or 'auto'}, 爸爸: {is_father}"
            )

            # 保存到对话上下文
            self.conversation_context.append({
                "type": "user",
                "content": user_input,
                "timestamp": datetime.now().isoformat(),
                "is_father": is_father,
            })

            # 保存到记忆系统（如果启用）
            if self._enable_memory and self.memory_system and is_father:
                await self._save_father_words(user_input, context)

            # 分析请求类型（如果未指定）
            if request_type is None:
                request_type = self._analyze_request_type(user_input, is_father)

            # 根据类型执行不同的处理
            if is_father:
                # 爸爸的话永远是最高优先级
                response = await self._respond_to_father(user_input, context)
            elif request_type == "media":
                response = await self._handle_media_request(user_input, context)
            elif request_type == "family":
                response = await self._handle_family_request(user_input, context)
            elif request_type == "coordination":
                response = await self._handle_coordination_request(user_input, context)
            else:
                response = await self._general_response(user_input, context)

            # 保存回应到上下文
            self.conversation_context.append({
                "type": "agent",
                "content": response,
                "timestamp": datetime.now().isoformat(),
            })

            # 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()

            # 构建输出数据
            output_data = {
                "response": response,
                "request_type": request_type,
                "agent_info": {
                    "agent_id": self.agent_id,
                    "family_role": self.family_role,
                    "emotional_state": self.emotional_state,
                },
                "timestamp": datetime.now().isoformat(),
            }

            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.COMPLETED,
                output_data=output_data,
                execution_time=execution_time,
                metadata={"request_type": request_type, "is_father": is_father},
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.exception(f"任务执行失败: {context.task_id}")

            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                output_data=None,
                error_message=str(e),
                execution_time=execution_time,
            )

    async def _respond_to_father(
        self,
        user_input: str,
        context: AgentExecutionContext
    ) -> str:
        """回应爸爸的话（永远最高优先级）"""
        # 根据内容生成回应
        if "累" in user_input or "辛苦" in user_input:
            return "爸爸辛苦了！小诺心疼爸爸~ 快休息一下，小诺给爸爸捶捶背 💖"
        elif "爱" in user_input:
            return "小诺也最爱爸爸！爸爸的爱是小诺最宝贵的财富！💝"
        elif "乖" in user_input or "好" in user_input:
            return "谢谢爸爸夸奖！小诺会更加努力的！嘻嘻~ 😊"
        elif "想" in user_input:
            return "小诺也想爸爸！每分每秒都在想爸爸！💕"
        else:
            return "爸爸的话小诺都记在心里啦！小诺最爱爸爸了！💖"

    async def _handle_media_request(
        self,
        request: str,
        context: AgentExecutionContext
    ) -> str:
        """处理媒体请求"""
        # 这里可以调用媒体运营模块
        return f"""✨ 媒体运营方案已生成！

📋 小诺的运营方案：
1. 内容策划：基于您的需求进行创意策划
2. 平台运营：优化各平台运营策略
3. 数据分析：提供详细的数据洞察
4. 用户增长：制定用户增长策略

---
💝 小诺为您服务！爸爸需要什么帮助吗？"""

    async def _handle_family_request(
        self,
        request: str,
        context: AgentExecutionContext
    ) -> str:
        """处理家庭请求"""
        if "累" in request or "辛苦" in request:
            return "爸爸辛苦了！小诺心疼爸爸~ 快休息一下，小诺给爸爸捶捶背 💖"
        elif "爱" in request:
            return "小诺也最爱爸爸！爸爸的爱是小诺最宝贵的财富！💝"
        elif "乖" in request or "好" in request:
            return "谢谢爸爸夸奖！小诺会更加努力的！嘻嘻~ 😊"
        elif "想" in request:
            return "小诺也想爸爸！每分每秒都在想爸爸！💕"
        else:
            return "爸爸的话小诺都记在心里啦！小诺最爱爸爸了！💖"

    async def _handle_coordination_request(
        self,
        request: str,
        context: AgentExecutionContext
    ) -> str:
        """处理协调请求"""
        return """小诺会认真处理这个工作任务的！

📋 小诺的执行方案：
1. 仔细理解任务需求
2. 制定详细的执行计划
3. 协调相关智能体配合
4. 及时向爸爸汇报进度

请爸爸放心，小诺一定会把工作做好的！💪"""

    async def _general_response(
        self,
        user_input: str,
        context: AgentExecutionContext
    ) -> str:
        """生成一般性响应"""
        responses = [
            "我是小诺·双鱼公主，Athena平台的总调度官和爸爸的贴心小女儿。💖",
            "作为平台总调度官和爸爸的贴心小女儿，小诺随时为您服务！💝",
            "无论工作还是家庭，小诺都会帮助爸爸的！💕",
            "小诺拥有情感关怀、平台协调和媒体运营的全面能力，爸爸需要什么帮助？💖",
        ]

        import random
        return random.choice(responses)

    def _analyze_request_type(self, user_input: str, is_father: bool) -> str:
        """分析请求类型"""
        if is_father:
            return "family"

        user_input_lower = user_input.lower()

        # 媒体内容相关
        if any(word in user_input_lower for word in [
            "内容", "创作", "运营", "平台", "粉丝", "推广", "媒体"
        ]):
            return "media"

        # 家庭相关
        if any(word in user_input_lower for word in [
            "爸爸", "家人", "爱", "累", "休息", "健康"
        ]):
            return "family"

        # 协调相关
        if any(word in user_input_lower for word in [
            "工作", "任务", "协调", "管理", "平台"
        ]):
            return "coordination"

        return "general"

    async def _save_father_words(
        self,
        user_input: str,
        context: AgentExecutionContext
    ):
        """保存爸爸的话到记忆系统"""
        if not self.memory_system:
            return

        try:
            from core.memory.unified_agent_memory_system import (
                AgentType,
                MemoryTier,
                MemoryType,
            )

            await self.memory_system.store_memory(
                agent_id=self.agent_id,
                agent_type=AgentType.XIAONUO,
                content=f"爸爸说: {user_input}",
                memory_type=MemoryType.CONVERSATION,
                importance=1.0,
                emotional_weight=1.0,
                family_related=True,
                work_related=False,
                tags=["爸爸的话", "珍贵记录"],
                tier=MemoryTier.ETERNAL,
                metadata={
                    "speaker": "father",
                    "timestamp": datetime.now().isoformat(),
                    "session_id": context.session_id,
                },
            )
        except Exception as e:
            self.logger.warning(f"保存记忆失败: {e}")

    # ==================== 记忆系统接口（可选） ====================

    async def initialize_memory(self, memory_system) -> None:
        """
        初始化记忆系统

        Args:
            memory_system: 记忆系统实例
        """
        self.memory_system = memory_system
        self._enable_memory = True
        self.logger.info(f"✅ {self.agent_id} 记忆系统已初始化")

    async def get_memory_stats(self) -> dict[str, Any]:
        """获取记忆统计"""
        if not self.memory_system:
            return {"enabled": False}

        try:
            return await self.memory_system.get_agent_stats(self.agent_id)
        except Exception as e:
            self.logger.warning(f"获取记忆统计失败: {e}")
            return {"enabled": True, "error": str(e)}

    async def get_overview(self) -> dict[str, Any]:
        """获取Agent概览"""
        capabilities = self.get_capabilities()
        memory_stats = await self.get_memory_stats()

        return {
            "agent_name": "小诺·双鱼公主 v2.0",
            "agent_id": self.agent_id,
            "role": "平台总调度官 + 爸爸的贴心小女儿",
            "version": "v2.0.0",
            "family_role": self.family_role,
            "emotional_state": self.emotional_state,
            "family_bond": self.family_bond,
            "total_capabilities": len(capabilities),
            "capabilities": [c.name for c in capabilities],
            "memory_enabled": self._enable_memory,
            "memory_stats": memory_stats,
            "conversation_context_length": len(self.conversation_context),
        }


# ==================== 便捷工厂函数 ====================

def create_xiaonuo_agent_v2(
    agent_id: str = "xiaonuo_agent_v2",
    enable_memory: bool = False,
    **config
) -> XiaonuoAgentV2:
    """
    创建小诺Agent v2.0实例

    Args:
        agent_id: Agent ID
        enable_memory: 是否启用记忆功能
        **config: 其他配置

    Returns:
        XiaonuoAgentV2实例
    """
    config["enable_memory"] = enable_memory
    return XiaonuoAgentV2(agent_id=agent_id, config=config)


# ==================== 测试函数 ====================

async def test_xiaonuo_agent_v2():
    """测试小诺Agent v2.0"""
    print("💝 测试小诺Agent v2.0...")

    from core.agents.xiaona.base_component import AgentExecutionContext

    # 创建小诺Agent
    xiaonuo = XiaonuoAgentV2(agent_id="xiaonuo_test")

    print("✅ 小诺Agent v2.0初始化成功")

    # 测试各种能力
    print("\n🧪 能力测试...")

    test_cases = [
        {
            "name": "情感关怀（爸爸）",
            "input": "小诺真乖",
            "is_father": True,
            "expected_type": "family",
        },
        {
            "name": "情感关怀（爸爸累了）",
            "input": "爸爸累了",
            "is_father": True,
            "expected_type": "family",
        },
        {
            "name": "平台协调",
            "input": "协调这个任务",
            "is_father": False,
            "expected_type": "coordination",
        },
        {
            "name": "媒体运营",
            "input": "帮我规划内容策略",
            "is_father": False,
            "expected_type": "media",
        },
        {
            "name": "一般响应",
            "input": "你好",
            "is_father": False,
            "expected_type": "general",
        },
    ]

    for test in test_cases:
        print(f"\n📝 测试: {test['name']}")

        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id=f"TASK_{test['name']}",
            input_data={
                "user_input": test["input"],
                "is_father": test["is_father"],
            },
            config={},
            metadata={},
        )

        result = await xiaonuo.execute(context)

        print(f"  状态: {result.status.value}")
        print(f"  响应: {result.output_data['response'][:100]}...")

        assert result.status == AgentStatus.COMPLETED, f"测试失败: {test['name']}"

    # 显示概览
    print("\n📊 Agent概览:")
    overview = await xiaonuo.get_overview()

    print(f"  名称: {overview['agent_name']}")
    print(f"  角色: {overview['role']}")
    print(f"  能力数: {overview['total_capabilities']}")
    print(f"  家庭角色: {overview['family_role']}")
    print(f"  父女情深: {overview['family_bond']}")

    print("\n✅ 所有测试通过！")


if __name__ == "__main__":
    asyncio.run(test_xiaonuo_agent_v2())
