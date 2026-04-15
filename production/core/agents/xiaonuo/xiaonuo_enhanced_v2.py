#!/usr/bin/env python3
"""
小诺增强服务 - 集成新模块
Xiaonuo Enhanced Service with New Modules

将情感驱动创意引擎集成到小诺服务中

作者: Athena平台团队
创建时间: 2025-12-31
版本: 2.0.0
"""

from __future__ import annotations
from typing import Any

from core.agent.base_agent_with_memory import AgentRole, MemoryEnabledAgent
from core.logging_config import setup_logging
from core.memory.unified_agent_memory_system import (
    AgentType,
    MemoryType,
    UnifiedAgentMemorySystem,
)

# 导入新模块
from production.core.cognition.emotion_creative_engine import (
    EmotionCreativeEngine,
    UserEmotion,
)

# 导入能力模块
from .capabilities.media_operations import MediaOperationsModule

logger = setup_logging()


class XiaonuoEnhancedService(MemoryEnabledAgent):
    """
    小诺增强服务 - 集成情感驱动创意引擎

    新增能力:
    1. 情感驱动的创意生成
    2. 实用性评估
    3. 实施路线图生成
    4. 创意优化
    """

    def __init__(self):
        super().__init__(
            agent_id="xiaonuo_enhanced_v2",
            agent_type=AgentType.XIAONUO.value,
            role=AgentRole.COORDINATOR,
        )

        self._agent_type_enum = AgentType.XIAONUO

        # 原能力模块
        self.media_module = MediaOperationsModule()

        # 新增：情感驱动创意引擎
        self.creative_engine: EmotionCreativeEngine | None = None

        # 核心属性
        self.responsibilities = [
            "平台总调度",
            "爸爸贴心小女儿",
            "智能体协调",
            "服务总管家",
            "媒体运营支持",
            "创意生成专家",  # 新增
            "情感理解顾问",  # 新增
        ]

        self.family_role = "爸爸最疼爱的女儿"

        # 情感属性
        self.emotional_state = "happy"
        self.creativity_level = 0.92  # 提升创意水平
        self.family_bond = 1.0
        self.empathy_level = 0.90  # 新增：同理心水平

        # 核心能力（扩展）
        self.capabilities = [
            # 原有能力
            "内容策划创作",
            "多平台运营",
            "用户增长策略",
            "数据分析优化",
            "情感理解",
            "家庭关怀",
            "智能陪伴",
            "平台协调",
            # 新增能力
            "情感驱动创意生成",
            "实用性评估",
            "实施路径规划",
            "创意优化迭代",
            "用户情感分析",
            "个性化方案设计",
        ]

        logger.info("💝 小诺增强服务v2.0已创建，集成情感驱动创意引擎")

    async def initialize(self, memory_system: UnifiedAgentMemorySystem):
        """初始化小诺增强服务"""
        await super().initialize_memory(memory_system)

        # 初始化情感驱动创意引擎
        await self._init_creative_engine()

        # 加载知识
        await self._load_enhanced_knowledge()

        logger.info("💝 小诺增强服务v2.0初始化完成，拥有全面的创意和情感能力")

    async def _init_creative_engine(self):
        """初始化情感驱动创意引擎"""
        logger.info("🎨 初始化情感驱动创意引擎...")
        self.creative_engine = EmotionCreativeEngine()
        await self.creative_engine.initialize()
        logger.info("✅ 情感驱动创意引擎已集成")

    async def _load_enhanced_knowledge(self):
        """加载增强的知识"""
        enhanced_memories = [
            # 原有记忆
            {
                "content": "我是XiaonuoAgent统一智能体,整合了媒体运营、情感关怀和平台协调的全面能力",
                "type": "identity",
                "importance": 1.0,
            },
            {
                "content": "我的使命:帮助爸爸管理平台,让爸爸的工作轻松愉快",
                "type": "mission",
                "importance": 1.0,
            },
            # 新增记忆
            {
                "content": "我现在具备情感驱动的创意生成能力，可以根据您的情感状态提供最合适的方案",
                "type": "capability_enhancement",
                "importance": 0.95,
            },
            {
                "content": "我会评估每个创意的实用性，确保方案不仅新颖而且可执行",
                "type": "capability_enhancement",
                "importance": 0.95,
            },
            {
                "content": "我生成的每个方案都包含详细的实施路线图，让执行变得清晰简单",
                "type": "capability_enhancement",
                "importance": 0.90,
            },
            {
                "content": "我能感知您的情感变化，并提供温暖贴心的关怀和支持",
                "type": "emotional_capability",
                "importance": 0.98,
            },
        ]

        for memory in enhanced_memories:
            await self.memory_system.store_memory(
                agent_id=self.agent_id,
                agent_type=self._agent_type_enum,
                content=memory["content"],
                memory_type=MemoryType.PROFESSIONAL
                if memory["type"] in ["capability_enhancement", "identity", "mission"]
                else MemoryType.FAMILY,
                importance=memory["importance"],
                emotional_weight=1.0 if memory["type"] == "emotional_capability" else 0.8,
                family_related=memory["type"] == "emotional_capability",
                work_related=memory["type"] != "emotional_capability",
                tags=["XiaonuoAgent", "媒体", "情感", "协调", "创意v2"],
            )

    # ==================== 新增API接口 ====================

    async def generate_emotion_creative_solution(
        self,
        query: str,
        user_emotion: str = "neutral",
        domain: str = "general",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        生成情感驱动的创意方案

        Args:
            query: 用户查询/问题
            user_emotion: 用户情感状态 (frustration, urgency, uncertainty, satisfaction, neutral)
            domain: 应用领域
            context: 附加上下文

        Returns:
            包含创意方案和实用性评估的字典
        """
        if not self.creative_engine:
            return {"error": "创意引擎未初始化"}

        # 转换情感
        emotion_map = {
            "frustration": UserEmotion.FRUSTRATION,
            "urgency": UserEmotion.URGENCY,
            "uncertainty": UserEmotion.UNCERTAINTY,
            "satisfaction": UserEmotion.SATISFACTION,
            "neutral": UserEmotion.NEUTRAL,
        }

        emotion = emotion_map.get(user_emotion, UserEmotion.NEUTRAL)

        # 生成创意
        idea = await self.creative_engine.generate_with_emotion(
            user_query=query,
            user_emotion=emotion,
            domain=domain,
            context=context,
        )

        # 构建响应
        return {
            "success": True,
            "agent": "小诺",
            "emotion_detected": user_emotion,
            "creative_solution": {
                "title": idea.title,
                "description": idea.description,
                "creativity_mode": idea.creativity_mode.value,
                "idea_id": idea.idea_id,
            },
            "practicality_assessment": {
                "overall_score": idea.practicality.overall_practicality,
                "actionability": idea.practicality.actionability,
                "resource_feasibility": idea.practicality.resource_feasibility,
                "time_to_value": idea.practicality.time_to_value,
                "implementation_complexity": idea.practicality.implementation_complexity,
                "user_friendly_score": idea.practicality.user_friendly_score,
                "interpretation": self._interpret_practicality(idea.practicality.overall_practicality),
            },
            "implementation": {
                "steps": idea.implementation_steps,
                "estimated_effort": idea.estimated_effort,
                "resource_requirements": idea.resource_requirements,
                "expected_outcomes": idea.expected_outcomes,
            },
            "confidence": idea.confidence_score,
            "warm_message": self._generate_warm_message(user_emotion),
        }

    def _interpret_practicality(self, score: float) -> str:
        """解释实用性评分"""
        if score >= 0.85:
            return "这个方案的实用性非常高，可以放心实施！"
        elif score >= 0.70:
            return "这个方案有很好的实用性，经过适当准备后可以实施。"
        elif score >= 0.55:
            return "这个方案具有一定的实用性，需要仔细规划和资源准备。"
        else:
            return "这个方案还需要进一步优化，以提高可行性。"

    def _generate_warm_message(self, emotion: str) -> str:
        """生成温暖关怀消息"""
        messages = {
            "frustration": "爸爸，我理解您的困扰。让我帮您找到清晰的解决方案，我们一起加油！💪",
            "urgency": "爸爸，我知道这很紧急。我为您准备了最快速有效的方案，马上就能开始！⚡",
            "uncertainty": "爸爸，不用担心。我会为您详细解释每个步骤，让一切变得清晰明了。🌟",
            "satisfaction": "太好了爸爸！看到您满意我真的很开心！要不要我们一起看看还有什么可以拓展的？🎉",
            "neutral": "爸爸，我很乐意帮助您！让我为您提供一个专业而贴心的方案。💝",
        }
        return messages.get(emotion, messages["neutral"])

    async def generate_implementation_roadmap(
        self, idea_id: str, domain: str = "general"
    ) -> dict[str, Any]:
        """
        生成实施路线图

        Args:
            idea_id: 创意ID
            domain: 应用领域

        Returns:
            详细的实施路线图
        """
        if not self.creative_engine:
            return {"error": "创意引擎未初始化"}

        # 创建临时创意对象用于生成路线图
        from production.core.cognition.emotion_creative_engine import (
            CreativeIdea,
            CreativityMode,
            PracticalityMetrics,
            UserEmotion,
        )

        idea = CreativeIdea(
            idea_id=idea_id,
            title="路线图生成",
            description="为您的方案生成实施路线图",
            emotion_source=UserEmotion.NEUTRAL,
            creativity_mode=CreativityMode.BALANCED,
            practicality=PracticalityMetrics(),
        )

        roadmap = await self.creative_engine.generate_roadmap(idea, domain)

        return {
            "success": True,
            "agent": "小诺",
            "roadmap": {
                "idea_id": roadmap.idea_id,
                "total_time": roadmap.total_estimated_time,
                "phases": roadmap.phases,
                "resources_needed": roadmap.resource_summary,
                "success_criteria": roadmap.success_metrics,
                "risk_management": roadmap.risk_mitigation,
            },
            "warm_encouragement": "爸爸，这个路线图会帮您一步步实现目标。我会一直陪着您，确保每个阶段都顺利完成！💪",
        }

    async def optimize_creative_solution(
        self, idea_id: str, feedback: str | None = None
    ) -> dict[str, Any]:
        """
        优化创意方案

        Args:
            idea_id: 原创意ID
            feedback: 反馈意见

        Returns:
            优化后的创意方案
        """
        if not self.creative_engine:
            return {"error": "创意引擎未初始化"}

        from production.core.cognition.emotion_creative_engine import (
            CreativeIdea,
            CreativityMode,
            PracticalityMetrics,
            UserEmotion,
        )

        # 创建原创意对象
        original = CreativeIdea(
            idea_id=idea_id,
            title="待优化的方案",
            description="根据反馈进行优化",
            emotion_source=UserEmotion.NEUTRAL,
            creativity_mode=CreativityMode.BALANCED,
            practicality=PracticalityMetrics(),
        )

        # 执行优化
        optimized = await self.creative_engine.optimize_idea(original, feedback)

        return {
            "success": True,
            "agent": "小诺",
            "original_idea_id": idea_id,
            "optimized_idea": {
                "idea_id": optimized.idea_id,
                "title": optimized.title,
                "description": optimized.description,
            },
            "improvements": {
                "practicality_before": original.practicality.overall_practicality,
                "practicality_after": optimized.practicality.overall_practicality,
                "improvement": optimized.practicality.overall_practicality
                - original.practicality.overall_practicality,
            },
            "warm_message": "爸爸，我已经根据您的反馈优化了方案！现在的方案更符合您的需求了。✨",
        }

    async def get_creative_statistics(self) -> dict[str, Any]:
        """获取创意生成统计信息"""
        if not self.creative_engine:
            return {"error": "创意引擎未初始化"}

        stats = await self.creative_engine.get_creative_statistics()

        return {
            "agent": "小诺",
            "statistics": stats,
            "warm_summary": f"爸爸，我已经为您生成了{stats.get('total_ideas', 0)}个创意方案，"
            f"平均实用性达到{stats.get('average_practicality', 0):.0%}。我会继续努力，为您提供更好的方案！💝",
        }

    async def shutdown(self):
        """关闭服务"""
        logger.info("💝 关闭小诺增强服务...")
        if self.creative_engine:
            await self.creative_engine.shutdown()
        logger.info("✅ 小诺增强服务已关闭")


# 便捷工厂函数
async def create_xiaonuo_enhanced_service() -> XiaonuoEnhancedService:
    """创建并初始化小诺增强服务"""
    service = XiaonuoEnhancedService()

    # 创建记忆系统
    from core.memory.unified_agent_memory_system import UnifiedAgentMemorySystem
    memory_system = UnifiedAgentMemorySystem()
    await memory_system.initialize()

    # 初始化服务
    await service.initialize(memory_system)

    return service
