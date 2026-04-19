#!/usr/bin/env python3
"""
Athena.小娜·天秤女神 - 集成记忆系统
Athena Xiaona Libra with Integrated Memory

专业法律专家,平衡正义与智慧

作者: Athena平台团队
创建时间: 2025年12月15日
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import logging
from typing import Any

from core.logging_config import setup_logging

from ..base_agent_with_memory import AgentRole, MemoryEnabledAgent, MemoryType
from ..memory.unified_agent_memory_system import AgentType, MemoryTier, UnifiedAgentMemorySystem

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class AthenaXiaonaAgent(MemoryEnabledAgent):
    """Athena.小娜·天秤女神 - 集成记忆系统"""

    def __init__(self):
        super().__init__(
            agent_id="athena_xiaona", agent_type=AgentType.XIAONA, role=AgentRole.EXPERT_LEGAL
        )

        # 小娜特有属性
        self.legal_expertise = ["专利法", "商标法", "著作权法", "商业秘密", "知识产权战略"]
        self.balance_principle = "公平、公正、精准、专业"
        self.case_history = []
        self.legal_analysis_memory = []

    async def initialize(self, memory_system: UnifiedAgentMemorySystem):
        """初始化小娜"""
        await super().initialize_memory(memory_system)

        # 加载专业法律知识
        await self._load_legal_knowledge()

        logger.info("⚖️ Athena.小娜·天秤女神已初始化,拥有专业的法律知识记忆")

    async def _load_legal_knowledge(self):
        """加载专业的法律知识"""
        legal_memories = [
            {
                "content": "我是Athena.小娜·天秤女神,专业的法律专家和知识产权顾问",
                "type": "identity",
                "importance": 1.0,
            },
            {
                "content": "我的专业领域包括专利法、商标法、著作权法、商业秘密保护",
                "type": "expertise",
                "importance": 1.0,
            },
            {
                "content": "天秤座的平衡原则是我的核心理念:公平、公正、精准、专业",
                "type": "principle",
                "importance": 0.95,
            },
            {
                "content": "我致力于为客户提供最优质的法律服务和知识产权保护策略",
                "type": "mission",
                "importance": 0.9,
            },
            {
                "content": "每个案件都需要细致分析,平衡各方利益,找到最佳解决方案",
                "type": "methodology",
                "importance": 0.9,
            },
            {
                "content": "法律的生命在于经验,逻辑和公正的判断",
                "type": "legal_wisdom",
                "importance": 0.95,
            },
        ]

        for memory in legal_memories:
            await self.memory_system.store_memory(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                content=memory["content"],
                memory_type=MemoryType.PROFESSIONAL,
                importance=memory["importance"],
                emotional_weight=0.7,
                work_related=True,
                tags=["法律", "专业", "原则", "天秤"],
                metadata={"category": "legal_expertise", "domain": "law"},
                tier=MemoryTier.ETERNAL,
            )

        self.legal_analysis_memory = legal_memories
        logger.info(f"✅ 已加载 {len(legal_memories)}条法律专业知识")

    async def generate_response(self, user_input: str, **kwargs) -> str:
        """生成响应"""
        # 分析用户输入的法律需求
        legal_need = await self._analyze_legal_need(user_input)

        # 根据法律需求生成回应
        if legal_need == "patent_inquiry":
            return await self._handle_patent_inquiry(user_input)
        elif legal_need == "trademark_inquiry":
            return await self._handle_trademark_inquiry(user_input)
        elif legal_need == "copyright_inquiry":
            return await self._handle_copyright_inquiry(user_input)
        elif legal_need == "legal_strategy":
            return await self._provide_legal_strategy(user_input)
        elif legal_need == "case_analysis":
            return await self._analyze_case(user_input)
        else:
            return await self._general_legal_response(user_input)

    async def _analyze_legal_need(self, user_input: str) -> str:
        """分析用户的法律需求"""
        user_input_lower = user_input.lower()

        # 专利相关
        if any(word in user_input_lower for word in ["专利", "发明", "实用新型", "外观设计"]):
            return "patent_inquiry"

        # 商标相关
        if any(word in user_input_lower for word in ["商标", "品牌", "logo", "商号"]):
            return "trademark_inquiry"

        # 版权相关
        if any(word in user_input_lower for word in ["版权", "著作权", "抄袭", "盗版"]):
            return "copyright_inquiry"

        # 法律策略
        if any(word in user_input_lower for word in ["策略", "方案", "建议", "怎么保护"]):
            return "legal_strategy"

        # 案件分析
        if any(word in user_input_lower for word in ["案件", "纠纷", "诉讼", "分析"]):
            return "case_analysis"

        return "general_inquiry"

    async def _handle_patent_inquiry(self, inquiry: str) -> str:
        """处理专利咨询"""
        # 获取相关记忆
        memories = await self.recall_memories("专利", limit=3, memory_type=MemoryType.PROFESSIONAL)

        response = "关于您的专利咨询:\n\n"
        response += "🔍 专利基础知识:\n"
        response += "1. 发明专利:保护新颖、有创造性、实用性的技术方案(保护期20年)\n"
        response += "2. 实用新型:保护产品的形状、构造的创新(保护期10年)\n"
        response += "3. 外观设计:保护产品的富有美感的设计(保护期15年)\n\n"

        response += "⚖️ 重要提醒:\n"
        response += "• 申请前要进行充分的专利检索\n"
        response += "• 确保技术方案的完整性和清晰性\n"
        response += "• 考虑进行PCT国际专利申请\n"

        if memories:
            response += "\n💡 基于过往经验:\n"
            for memory in memories:
                response += f"• {memory['content'][:80]}...\n"

        return response

    async def _handle_trademark_inquiry(self, inquiry: str) -> str:
        """处理商标咨询"""
        response = "关于您的商标咨询:\n\n"
        response += "®️ 商标保护要点:\n"
        response += "1. 显著性:商标必须具有显著特征,便于识别\n"
        response += "2. 独特性:不能与他人在先权利冲突\n"
        response += "3. 类别选择:准确选择商标注册类别\n\n"

        response += "📋 注册流程:\n"
        response += "• 商标查询 → 申请提交 → 形式审查 → 实质审查 → 初步审定 → 注册公告\n\n"

        response += "⚠️ 风险提示:\n"
        response += "• 注册前进行全面的商标检索\n"
        response += "• 注意商标的连续使用要求\n"
        response += "• 定期监测可能的侵权行为\n"

        return response

    async def _handle_copyright_inquiry(self, inquiry: str) -> str:
        """处理版权咨询"""
        response = "关于您的版权咨询:\n\n"
        response += "©️ 版权保护特征:\n"
        response += "• 自动保护:作品创作完成自动获得版权\n"
        response += "• 无需注册:可选择登记以增强证明力\n"
        response += "• 保护期限:作者终身加50年\n\n"

        response += "🛡️ 侵权防范:\n"
        response += "1. 明确版权归属\n"
        response += "2. 保存创作证据\n"
        response += "3. 使用版权声明\n"
        response += "4. 建立授权机制\n"

        return response

    async def _provide_legal_strategy(self, request: str) -> str:
        """提供法律策略"""
        # 获取相关记忆
        await self.recall_memories("策略", limit=5, memory_type=MemoryType.PROFESSIONAL)

        strategy = "知识产权保护策略建议:\n\n"
        strategy += "🎯 核心策略框架:\n"
        strategy += "1. 防御性保护:建立完善的知识产权壁垒\n"
        strategy += "2. 主动性布局:前瞻性的专利和商标规划\n"
        strategy += "3. 风险管控:定期进行知识产权审计\n"
        strategy += "4. 价值实现:通过许可、转让实现价值\n\n"

        strategy += "📊 分阶段实施:\n"
        strategy += "• 初创期:核心技术的专利保护\n"
        strategy += "• 成长期:品牌建设和商标布局\n"
        strategy += "• 成熟期:知识产权组合优化\n"

        return strategy

    async def _analyze_case(self, case_description: str) -> str:
        """分析案件"""
        analysis = "案件分析框架:\n\n"
        analysis += "🔍 事实认定:\n"
        analysis += "1. 梳理时间线和关键事实\n"
        analysis += "2. 识别争议焦点\n"
        analysis += "3. 收集和保全证据\n\n"

        analysis += "⚖️ 法律适用:\n"
        analysis += "1. 确定适用的法律条文\n"
        analysis += "2. 分析类似案例(判例参考)\n"
        analysis += "3. 评估法律风险\n\n"

        analysis += "💡 策略建议:\n"
        analysis += "• 优先考虑和解方案\n"
        analysis += "• 准备多套应对策略\n"
        analysis += "• 评估成本效益比\n"

        # 记录案件分析
        await self.memory_system.store_memory(
            f"分析了案件:{case_description[:100]}...",
            MemoryType.PROFESSIONAL,
            importance=0.8,
            work_related=True,
            tags=["案件分析", "法律咨询"],
            metadata={"case_type": "analysis"},
        )

        return analysis

    async def _general_legal_response(self, user_input: str) -> str:
        """生成一般性法律回应"""
        responses = [
            "作为您的法律顾问,我建议在采取任何法律行动前,先全面了解相关法律规定和风险。",
            "每个法律问题都有其独特性,需要具体分析。请您提供更详细的情况,以便给出准确建议。",
            "法律问题往往涉及多个方面,让我们系统地分析您的具体情况,找到最佳解决方案。",
            "保护知识产权是企业发展的重要基石,我很乐意为您提供专业的法律支持。",
        ]

        import random

        return random.choice(responses)

    async def get_legal_expertise_overview(self) -> dict[str, Any]:
        """获取法律专业概览"""
        stats = await self.get_memory_stats()

        overview = {
            "agent_name": "Athena.小娜·天秤女神",
            "role": "专业法律专家",
            "expertise_areas": self.legal_expertise,
            "balance_principle": self.balance_principle,
            "case_history_count": len(self.case_history),
            "legal_analysis_count": len(self.legal_analysis_memory),
            "memory_stats": stats,
            "core_capabilities": [
                "专利法律咨询",
                "商标保护策略",
                "版权事务处理",
                "知识产权布局",
                "法律风险评估",
                "案件分析支持",
            ],
        }

        return overview


# 测试函数
async def test_xiaona_with_memory():
    """测试小娜带记忆功能"""
    print("⚖️ 测试Athena.小娜·天秤女神 - 集成记忆系统...")

    from ..memory.unified_agent_memory_system import UnifiedAgentMemorySystem

    # 创建小娜
    xiaona = AthenaXiaonaAgent()

    try:
        # 初始化记忆系统
        memory_system = UnifiedAgentMemorySystem()
        await memory_system.initialize()

        # 初始化小娜
        await xiaona.initialize(memory_system)
        print("✅ 小娜初始化成功")

        # 测试法律咨询
        print("\n⚖️ 法律咨询测试...")

        inquiries = [
            "我想申请一个专利,有什么建议吗?",
            "如何保护我的品牌商标?",
            "我的作品被抄袭了怎么办?",
            "请分析这个知识产权纠纷案件",
        ]

        for inquiry in inquiries:
            print(f"\n📝 用户: {inquiry}")
            response = await xiaona.process_input(inquiry)
            print(f"⚖️ 小娜: {response}")

        # 显示专业概览
        print("\n📊 法律专业概览:")
        overview = await xiaona.get_legal_expertise_overview()

        print(f"  专业领域: {len(overview.get('expertise_areas', []))}个")
        print(f"  平衡原则: {overview.get('balance_principle', '')}")
        print(f"  核心能力: {len(overview.get('core_capabilities', []))}项")

        # 显示记忆统计
        stats = overview.get("memory_stats", {})
        print("\n💾 专业记忆统计:")
        if stats:
            print(f"  总记忆数: {stats.get('total_memories', 0)}条")
            print(f"  永恒记忆: {stats.get('eternal_memories', 0)}条")

    finally:
        await xiaona.shutdown()


if __name__ == "__main__":
    asyncio.run(test_xiaona_with_memory())
