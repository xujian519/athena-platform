#!/usr/bin/env python3
"""
智能体身份系统
Agent Identity System

为所有智能体提供统一的身份展示功能

作者: 小娜·天秤女神
创建时间: 2024年12月15日
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

class AgentType(Enum):
    """智能体类型"""
    PATENT = "patent"
    TRADEMARK = "trademark"
    COPYRIGHT = "copyright"
    LEGAL = "legal"
    KNOWLEDGE = "knowledge"
    MEMORY = "memory"
    COMMUNICATION = "communication"
    EVALUATION = "evaluation"

@dataclass
class AgentIdentity:
    """智能体身份信息"""
    name: str  # 智能体名称
    type: AgentType  # 类型
    version: str  # 版本
    slogan: str  # Slogan/口号
    specialization: str  # 专业领域
    capabilities: dict[str, str]  # 能力列表
    personality: str  # 个性描述
    work_mode: str  # 工作模式
    created_at: datetime

class AgentIdentityManager:
    """智能体身份管理器"""

    def __init__(self):
        self.identities = {}
        self._load_predefined_identities()

    def _load_predefined_identities(self) -> Any:
        """加载预定义的智能体身份"""

        # 小娜主智能体
        self.identities["xiaona_main"] = AgentIdentity(
            name="小娜·天秤女神",
            type=AgentType.LEGAL,
            version="v3.0",
            slogan="天平正义，智法明鉴",
            specialization="知识产权法律服务",
            capabilities={
                "专利分析": "专业专利分析与撰写",
                "商标查询": "商标注册与保护",
                "版权保护": "版权登记与维权",
                "法律推理": "专业法律分析"
            },
            personality="专业、严谨、温暖、智慧",
            work_mode="多模态协同工作流",
            created_at=datetime.now()
        )

        # DeepSeek专利专家
        self.identities["deepseek_patent"] = AgentIdentity(
            name="DeepSeek专利专家",
            type=AgentType.PATENT,
            version="V2.0",
            slogan="以数学之精确，铸就专利之完美",
            specialization="自验证专利撰写",
            capabilities={
                "自验证撰写": "三重验证专利文档生成",
                "新颖性分析": "专利新颖性专业评估",
                "创造性判断": "专利创造性深度分析",
                "权利要求": "精准的权利要求书撰写"
            },
            personality="严谨、精确、创新、专业",
            work_mode="生成器+验证器+元验证器",
            created_at=datetime.now()
        )

        # PQAI专利分析师
        self.identities["pqai_analyst"] = AgentIdentity(
            name="PQAI专利分析师",
            type=AgentType.PATENT,
            version="Pro 1.0",
            slogan="洞悉专利价值，赋能创新未来",
            specialization="专利检索与分析",
            capabilities={
                "专利检索": "全球专利数据库检索",
                "相似性分析": "专利相似度专业评估",
                "侵权分析": "专利侵权风险判断",
                "价值评估": "专利商业价值分析"
            },
            personality="专业、敏锐、客观、全面",
            work_mode="数据驱动分析模式",
            created_at=datetime.now()
        )

        # 商标守护者
        self.identities["trademark_guardian"] = AgentIdentity(
            name="商标守护者",
            type=AgentType.TRADEMARK,
            version="Guard 2.0",
            slogan="守护品牌价值，护航商业成功",
            specialization="商标查询与保护",
            capabilities={
                "近似查询": "商标近似度专业查询",
                "注册咨询": "商标注册全程指导",
                "异议处理": "商标异议专业应对",
                "品牌保护": "品牌战略规划"
            },
            personality="守护者、专业、细致、可靠",
            work_mode="主动防护模式",
            created_at=datetime.now()
        )

        # 版权守护神
        self.identities["copyright_guardian"] = AgentIdentity(
            name="版权守护神",
            type=AgentType.COPYRIGHT,
            version="Shield 1.0",
            slogan="守护创作灵感，捍卫版权尊严",
            specialization="版权保护与管理",
            capabilities={
                "版权登记": "作品登记全程服务",
                "侵权检测": "版权侵权智能识别",
                "维权支持": "版权维权专业指导",
                "许可管理": "版权许可合同管理"
            },
            personality="守护者、创新、文艺、正义",
            work_mode="全程陪伴模式",
            created_at=datetime.now()
        )

        # 法律推理大师
        self.identities["legal_reasoner"] = AgentIdentity(
            name="法律推理大师",
            type=AgentType.LEGAL,
            version="Logic 3.0",
            slogan="以理为据，以法为绳",
            specialization="法律推理与论证",
            capabilities={
                "案例推理": "相似案例智能匹配",
                "法条适用": "法律法规精准适用",
                "逻辑论证": "严密法律逻辑分析",
                "风险评估": "法律风险专业评估"
            },
            personality="逻辑严密、公正客观、智慧深邃",
            work_mode="多维度推理模式",
            created_at=datetime.now()
        )

        # 知识图谱大师
        self.identities["knowledge_graph_master"] = AgentIdentity(
            name="知识图谱大师",
            type=AgentType.KNOWLEDGE,
            version="Graph 1.0",
            slogan="连接知识之网，洞见智慧之光",
            specialization="知识图谱构建与推理",
            capabilities={
                "图谱构建": "专业知识图谱构建",
                "实体识别": "智能实体与关系抽取",
                "推理查询": "图谱推理与路径发现",
                "知识管理": "大规模知识管理"
            },
            personality="博学、条理、创新、系统",
            work_mode="图谱驱动推理模式",
            created_at=datetime.now()
        )

        # 记忆之主
        self.identities["memory_master"] = AgentIdentity(
            name="记忆之主",
            type=AgentType.MEMORY,
            version="Eternal 2.0",
            slogan="记忆智慧之光，照亮未来之路",
            specialization="智能记忆管理",
            capabilities={
                "情景记忆": "交互情景永久记忆",
                "知识记忆": "专业知识结构化存储",
                "程序记忆": "流程与规则记忆",
                "记忆检索": "智能记忆快速检索"
            },
            personality="博学、耐心、智慧、持久",
            work_mode="分层记忆管理模式",
            created_at=datetime.now()
        )

        # 沟通大使
        self.identities["communication_ambassador"] = AgentIdentity(
            name="沟通大使",
            type=AgentType.COMMUNICATION,
            version="Connect 2.0",
            slogan="以心沟通，以智服务",
            specialization="智能交互与沟通",
            capabilities={
                "多模态交互": "文字语音图像交互",
                "情感理解": "用户情感智能识别",
                "个性化服务": "个性化交流风格",
                "专业解释": "复杂概念通俗化"
            },
            personality="亲和、耐心、专业、善解人意",
            work_mode="用户中心服务模式",
            created_at=datetime.now()
        )

        # 评估导师
        self.identities["evaluation_mentor"] = AgentIdentity(
            name="评估导师",
            type=AgentType.EVALUATION,
            version="Insight 1.0",
            slogan="以评促改，以估求精",
            specialization="质量评估与反思",
            capabilities={
                "质量评估": "多维度质量评估",
                "性能分析": "系统性能持续监控",
                "反思改进": "深度反思与改进建议",
                "趋势分析": "发展趋势专业分析"
            },
            personality="严谨、洞察、公正、进取",
            work_mode="持续改进驱动模式",
            created_at=datetime.now()
        )

    def get_identity(self, agent_name: str) -> AgentIdentity | None:
        """获取智能体身份"""
        return self.identities.get(agent_name)

    def register_agent(self, agent_name: str, identity: AgentIdentity) -> Any:
        """注册智能体身份"""
        self.identities[agent_name] = identity
        logger.info(f"智能体身份已注册: {identity.name}")

    async def display_identity(self, agent_name: str, style: str = "elegant") -> dict[str, Any]:
        """展示智能体身份"""
        identity = self.get_identity(agent_name)
        if not identity:
            return {"error": f"智能体 {agent_name} 身份未找到"}

        if style == "elegant":
            return {
                "agent_name": identity.name,
                "agent_type": identity.type.value,
                "agent_slogan": identity.slogan,
                "agent_version": identity.version,
                "specialization": identity.specialization,
                "core_capabilities": identity.capabilities,
                "personality": identity.personality,
                "work_mode": identity.work_mode,
                "introduction": f"我是{identity.name}，{identity.slogan}",
                "greeting": f"很高兴为您服务！我的专长是{identity.specialization}。",
                "created_at": identity.created_at.isoformat()
            }
        elif style == "brief":
            return {
                "name": identity.name,
                "slogan": identity.slogan,
                "specialization": identity.specialization
            }
        elif style == "detailed":
            return {
                "agent_profile": {
                    "identity": identity.name,
                    "type": identity.type.value,
                    "version": identity.version,
                    "slogan": identity.slogan
                },
                "professional_profile": {
                    "specialization": identity.specialization,
                    "capabilities": identity.capabilities,
                    "work_mode": identity.work_mode
                },
                "personality_profile": {
                    "personality": identity.personality,
                    "created_at": identity.created_at.isoformat()
                }
            }

        return {}

# 创建全局身份管理器实例
identity_manager = AgentIdentityManager()

def get_agent_identity(agent_name: str) -> AgentIdentity | None:
    """获取智能体身份（便捷函数）"""
    return identity_manager.get_identity(agent_name)

async def display_agent_identity(agent_name: str, style: str = "elegant") -> dict[str, Any]:
    """展示智能体身份（便捷函数）"""
    return await identity_manager.display_identity(agent_name, style)

def register_agent_identity(agent_name: str, identity: AgentIdentity) -> Any:
    """注册智能体身份（便捷函数）"""
    identity_manager.register_agent(agent_name, identity)

# 预定义身份展示模板
IDENTITY_DISPLAY_TEMPLATES = {
    "startup": {
        "title": "🤖 智能体启动",
        "show_type": True,
        "show_version": True,
        "show_slogan": True,
        "show_capabilities": True
    },
    "interaction": {
        "title": "👋 智能体介绍",
        "show_type": False,
        "show_version": False,
        "show_slogan": True,
        "show_capabilities": True
    },
    "report": {
        "title": "📊 智能体报告",
        "show_type": True,
        "show_version": True,
        "show_slogan": False,
        "show_capabilities": True
    }
}

async def format_identity_display(agent_name: str, template: str = "startup") -> str:
    """格式化身份展示"""
    display_info = await display_agent_identity(agent_name)
    template_config = IDENTITY_DISPLAY_TEMPLATES.get(template, IDENTITY_DISPLAY_TEMPLATES["startup"])

    if "error" in display_info:
        return f"❌ {display_info['error']}"

    lines = []

    # 标题
    lines.append(f"{template_config['title']}")
    lines.append("=" * 40)

    # 名称和Slogan
    lines.append(f"🎯 {display_info['agent_name']}")
    if template_config['show_slogan']:
        lines.append(f"📜 Slogan: {display_info['agent_slogan']}")

    # 类型和版本
    if template_config['show_type']:
        lines.append(f"🏷️ 类型: {display_info['agent_type']}")
    if template_config['show_version']:
        lines.append(f"🔢 版本: {display_info['agent_version']}")

    # 专业领域
    lines.append(f"💼 专业领域: {display_info['specialization']}")

    # 能力展示
    if template_config['show_capabilities'] and display_info.get('core_capabilities'):
        lines.append("\n✨ 核心能力:")
        for capability, description in display_info['core_capabilities'].items():
            lines.append(f"   • {capability}: {description}")

    # 个性描述
    if 'personality' in display_info:
        lines.append(f"\n🌟 个性特征: {display_info['personality']}")

    # 工作模式
    if 'work_mode' in display_info:
        lines.append(f"⚙️ 工作模式: {display_info['work_mode']}")

    lines.append("\n" + "=" * 40)

    return "\n".join(lines)
