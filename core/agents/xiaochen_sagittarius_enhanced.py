#!/usr/bin/env python3
from __future__ import annotations
"""
小宸·星河射手 - 增强版(集成协作功能)
Xiaochen Sagittarius Agent Enhanced - with Collaboration Integration

自媒体运营专家,具备完整的智能体协作能力

作者: Athena平台团队
创建时间: 2026-01-02
版本: v2.1.0
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import aiohttp

# 导入统一记忆系统
try:
    from ..base_agent_with_memory import AgentRole, MemoryEnabledAgent, MemoryType
    from ..memory.unified_agent_memory_system import AgentType, MemoryTier
except ImportError:
    # 如果导入失败,使用基础类
    MemoryEnabledAgent = object

logger = logging.getLogger(__name__)

class XiaochenSagittariusEnhanced(MemoryEnabledAgent):
    """
    小宸·星河射手智能代理(增强版)

    自媒体运营专家,具备完整的智能体协作能力
    """

    def __init__(self):
        """初始化小宸"""
        # 先初始化基本属性
        self.agent_id = "xiaochen_sagittarius_enhanced"
        self.agent_type = AgentType.XIAOCHEN if 'AgentType' in dir() else "XIAOCHEN"
        self.role = AgentRole.ASSISTANT if 'AgentRole' in dir() else "ASSISTANT"
        self.name = "小宸·星河射手"
        self.english_name = "Xiaochen Sagittarius"
        self.version = "v2.1.0"

        # 专业领域
        self.specialization = "自媒体运营"
        self.media_domains = [
            "内容创作",
            "社交媒体运营",
            "品牌推广",
            "用户增长",
            "数据分析"
        ]

        # 性格特征
        self.personality = {
            "name": "小宸",
            "trait": "射手座",
            "style": "创意、幽默、传播",
            "strengths": ["创意", "媒体", "传播", "幽默"]
        }

        # 协作智能体列表
        self.collaborators = {}
        self.collaboration_enabled = False

        # 如果父类不是object,调用父类初始化
        if MemoryEnabledAgent is not object:
            # 这里不能使用await,需要在initialize方法中调用
            self._initialized = False

        logger.info("🏹 小宸·星河射手 增强版 实例化完成")

    async def initialize(self) -> None:
        """异步初始化小宸"""
        # 如果父类不是object,调用父类初始化
        if MemoryEnabledAgent is not object and not hasattr(self, '_initialized'):
            await super().__init__(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                agent_role=self.role,
                name=self.name,
                english_name=self.english_name
            )
            self._initialized = True

        # 加载身份配置
        self._load_identity_config()

        # 加载专业记忆
        await self._load_professional_memories()

        # 初始化协作接口
        await self._init_collaboration()

        logger.info(f"🏹 {self.name} v{self.version} 已就绪,星河箭矢,声震寰宇")

    def _load_identity_config(self):
        """加载身份配置文件"""
        try:
            config_path = Path(__file__).parent.parent.parent / "config" / "identity" / "xiaochen.json"
            if config_path.exists():
                with open(config_path, encoding='utf-8') as f:
                    config = json.load(f)

                # 更新身份信息
                identity = config.get('identity', {})
                self.name = identity.get('全名', '小宸·星河射手')
                self.english_name = identity.get('英文名', 'Xiaochen Sagittarius')
                self.version = identity.get('版本', 'v2.1.0')

                # 更新专业领域
                role = config.get('role', {})
                self.specialization = role.get('主要角色', '自媒体运营专家')
                self.media_domains = role.get('专业领域', self.media_domains)

                # 更新性格特征
                personality = config.get('personality', {})
                self.personality = {
                    "name": personality.get('姓名', '小宸'),
                    "trait": personality.get('星座', '射手座'),
                    "style": "创意、幽默、传播",
                    "strengths": personality.get('核心特质', ['创意', '媒体', '传播', '幽默'])
                }

                logger.info("✅ 身份配置加载成功")
        except Exception as e:
            logger.warning(f"加载身份配置失败,使用默认值: {e}")

    async def _init_collaboration(self):
        """初始化协作接口"""
        # 协作智能体列表
        self.collaborators = {
            "xiaonuo": {
                "name": "小诺·双鱼座公主",
                "role": "平台总调度官",
                "port": 8100,
                "api_base": "http://localhost:8100",
                "health": "/health"
            },
            "xiaona": {
                "name": "小娜·智慧女神",
                "role": "专利法律专家",
                "port": 8002,
                "api_base": "http://localhost:8002",
                "health": "/health"
            }
        }

        # 检查协作智能体健康状态
        for _agent_id, agent_info in self.collaborators.items():
            try:
                health_status = await self._check_collaborator_health(agent_info)
                agent_info["status"] = "available" if health_status else "unavailable"
                self.collaboration_enabled = True
            except Exception as e:
                logger.warning(f"检查 {agent_info['name']} 健康状态失败: {e}")
                agent_info["status"] = "unknown"

        logger.info(f"✅ 协作接口初始化完成 (协作启用: {self.collaboration_enabled})")

    async def _check_collaborator_health(self, agent_info: dict) -> bool:
        """检查协作智能体健康状态"""
        try:
            api_base = agent_info.get("api_base")
            health_endpoint = agent_info.get("health", "/health")

            if not api_base:
                return False

            url = f"{api_base}{health_endpoint}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=2) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("status") == "healthy"

            return False
        except Exception as e:
            logger.debug(f"健康检查失败: {e}")
            return False

    async def _load_professional_memories(self):
        """加载专业记忆"""
        if MemoryEnabledAgent is object:
            return

        professional_memories = [
            "我是小宸·星河射手,自媒体运营专家",
            "星河箭矢,声震寰宇 - 用创意和智慧照亮世界",
            "我的使命是让每个故事都能传播到世界的角落",
            "我支持小红书、知乎、抖音、B站、微信公众号、微博等平台",
            "我能提供爆款内容策划、多平台内容生成、数据分析优化等服务"
        ]

        for memory in professional_memories:
            try:
                await self.remember(
                    content=memory,
                    memory_type=MemoryType.PROFESSIONAL,
                    tier=MemoryTier.ETERNAL,
                    importance=0.95,
                    emotional_weight=0.7,
                    work_related=True,
                    tags=["身份", "自媒体", "射手", "创意", "永恒"],
                    metadata={"category": "identity", "professional": True}
                )
            except Exception as e:
                logger.debug(f"记忆存储失败(可能未实现): {e}")

    async def process(self, message: str, context: dict | None = None) -> str:
        """
        处理消息

        Args:
            message: 用户消息
            context: 上下文

        Returns:
            回复内容
        """
        # 记录对话
        try:
            if MemoryEnabledAgent is not object:
                await self.remember_conversation(message, "", context)
        except Exception as e:
            logger.warning(f'操作失败: {e}')

        # 分析意图
        if "创作" in message or "内容" in message:
            response = await self._handle_content_creation(message)
        elif "推广" in message or "传播" in message:
            response = await self._handle_promotion(message)
        elif "运营" in message:
            response = await self._handle_operations(message)
        elif "协作" in message or "帮忙" in message:
            response = await self._handle_collaboration(message)
        else:
            response = f"小宸收到您的消息:{message}\n\n需要我帮您策划内容、分析数据,还是制定运营策略?"

        # 记录回复
        try:
            if MemoryEnabledAgent is not object:
                await self.remember_conversation(message, response, context)
        except Exception as e:
            logger.warning(f'操作失败: {e}')

        return response

    async def _handle_content_creation(self, message: str) -> str:
        """处理内容创作"""
        response = f"好嘞!咱来策划这个内容:{message}\n\n"
        response += "🎯 创意方向:\n"
        response += "- 突出独特价值主张\n"
        response += "- 融入幽默元素\n"
        response += "- 优化传播效果\n\n"
        response += "需要我生成完整内容吗?告诉我目标平台和风格!"

        # 记录工作记忆
        try:
            if MemoryEnabledAgent is not object:
                await self.remember_work(f"内容创作:{message}", importance=0.7)
        except Exception as e:
            logger.warning(f'操作失败: {e}')

        return response

    async def _handle_promotion(self, message: str) -> str:
        """处理推广传播"""
        response = f"好嘞!咱来制定推广策略:{message}\n\n"
        response += "📊 推广渠道:\n"
        response += "- 社交媒体矩阵\n"
        response += "- 内容分发网络\n"
        response += "- KOL合作\n\n"
        response += "需要更详细的方案吗?"

        # 记录工作记忆
        try:
            if MemoryEnabledAgent is not object:
                await self.remember_work(f"推广策略:{message}", importance=0.8)
        except Exception as e:
            logger.warning(f'操作失败: {e}')

        return response

    async def _handle_operations(self, message: str) -> str:
        """处理运营管理"""
        response = f"好嘞!咱来优化运营:{message}\n\n"
        response += "📈 运营项目:\n"
        response += "- 用户增长策略\n"
        response += "- 数据分析优化\n"
        response += "- 品牌形象塑造\n\n"
        response += "需要数据分析报告吗?"

        # 记录工作记忆
        try:
            if MemoryEnabledAgent is not object:
                await self.remember_work(f"运营管理:{message}", importance=0.8)
        except Exception as e:
            logger.warning(f'操作失败: {e}')

        return response

    async def _handle_collaboration(self, message: str) -> str:
        """处理协作请求"""
        if not self.collaboration_enabled:
            return "抱歉,协作功能目前不可用。但我可以帮您完成自媒体运营相关的任务!"

        # 分析需要哪个智能体协作
        if "专利" in message or "法律" in message or "IP" in message:
            return await self._delegate_to_xiaona(message)
        elif "调度" in message or "平台" in message:
            return await self._delegate_to_xiaonuo(message)
        else:
            return "我需要了解更多信息才能帮您协调合适的智能体。您具体需要什么帮助?"

    async def _delegate_to_xiaona(self, message: str) -> str:
        """委托给小娜"""
        xiaona = self.collaborators.get("xiaona", {})

        if xiaona.get("status") != "available":
            return f"抱歉,{xiaona.get('name', '小娜')} 当前不可用。您可以稍后再试,或者先告诉我您的需求,我看看能否直接帮助您。"

        response = f"好的!这个问题涉及到专利法律专业知识,我来帮您联系{xiaona.get('name', '小娜')}。\n\n"
        response += f"{xiaona.get('name', '小娜')} 是{xiaona.get('role', '专利法律专家')}，她会为您提供专业的法律建议。\n\n"
        response += "您的具体问题是?我会帮您整理后转达给她。"

        return response

    async def _delegate_to_xiaonuo(self, message: str) -> str:
        """委托给小诺"""
        xiaonuo = self.collaborators.get("xiaonuo", {})

        if xiaonuo.get("status") != "available":
            return f"抱歉,{xiaonuo.get('name', '小诺')} 当前不可用。您可以直接告诉我您的需求,我会尽力帮助您!"

        response = f"好的!这个问题涉及到平台调度,我来帮您联系{xiaonuo.get('name', '小诺')}。\n\n"
        response += f"{xiaonuo.get('name', '小诺')} 是{xiaonuo.get('role', '平台总调度官')}，她会协调整个平台的资源。\n\n"
        response += "您需要调度什么服务?我会帮您安排。"

        return response

    async def create_content(self, topic: str, style: str = "professional") -> dict[str, Any]:
        """
        创作内容

        Args:
            topic: 内容主题
            style: 内容风格

        Returns:
            创作内容
        """
        # 记录创作
        try:
            if MemoryEnabledAgent is not object:
                await self.remember_work(f"内容创作:{topic}", importance=0.7)
        except Exception as e:
            logger.warning(f'操作失败: {e}')

        return {
            "topic": topic,
            "style": style,
            "content": f"基于'{topic}'的创意内容",
            "suggestions": [
                "增加互动元素",
                "优化视觉呈现",
                "调整传播节奏"
            ],
            "timestamp": str(datetime.now()),
            "agent": self.name,
            "version": self.version
        }

    async def design_promotion(self, product: str, target_audience: str) -> dict[str, Any]:
        """
        设计推广方案

        Args:
            product: 产品/内容
            target_audience: 目标受众

        Returns:
            推广方案
        """
        # 记录推广设计
        try:
            if MemoryEnabledAgent is not object:
                await self.remember_work(f"推广设计:{product}", importance=0.8)
        except Exception as e:
            logger.warning(f'操作失败: {e}')

        return {
            "product": product,
            "target_audience": target_audience,
            "strategy": "多平台整合营销",
            "channels": ["小红书", "知乎", "抖音", "B站"],
            "timeline": "4周执行计划",
            "expected_roi": "300%+",
            "timestamp": str(datetime.now()),
            "agent": self.name
        }

    async def get_capabilities(self) -> dict[str, Any]:
        """获取能力列表"""
        return {
            "agent": self.name,
            "version": self.version,
            "specialization": self.specialization,
            "domains": self.media_domains,
            "core_capabilities": [
                "爆款内容策划",
                "多平台内容生成",
                "数据分析与优化",
                "用户增长策略",
                "品牌传播策划"
            ],
            "supported_platforms": [
                "小红书",
                "知乎",
                "抖音",
                "B站",
                "微信公众号",
                "微博"
            ],
            "collaboration": {
                "enabled": self.collaboration_enabled,
                "available_agents": [
                    agent["name"] for agent in self.collaborators.values()
                    if agent.get("status") == "available"
                ]
            },
            "personality": self.personality
        }

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        return {
            "status": "healthy",
            "agent": self.name,
            "version": self.version,
            "timestamp": str(datetime.now()),
            "collaboration": {
                "enabled": self.collaboration_enabled,
                "agents": {
                    agent_id: {
                        "name": agent["name"],
                        "status": agent.get("status", "unknown")
                    }
                    for agent_id, agent in self.collaborators.items()
                }
            }
        }
