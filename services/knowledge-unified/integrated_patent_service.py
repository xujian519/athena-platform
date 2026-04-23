#!/usr/bin/env python3
"""
集成专利服务
Integrated Patent Service

为项目所有专利应用提供统一的智能服务接口

作者: 小诺·双鱼公主
创建时间: 2024年12月15日
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

from core.logging_config import setup_logging

from .dynamic_prompt_manager import DynamicPromptManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

class IntegratedPatentService:
    """集成专利服务"""

    def __init__(self):
        """初始化"""
        self.prompt_manager = None
        self.service_stats = {
            'total_queries': 0,
            'prompt_generated': 0,
            'knowledge_hits': 0,
            'response_cache': {}
        }

    async def initialize(self):
        """初始化服务"""
        self.prompt_manager = DynamicPromptManager()
        await self.prompt_manager.initialize()
        logger.info("集成专利服务初始化完成")

    async def process_patent_query(
        self,
        query: str,
        patent_text: str = "",
        context: dict[str, Any] = None,
        user_id: str = None
    ) -> dict[str, Any]:
        """处理专利查询"""

        self.service_stats['total_queries'] += 1
        query_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(query) % 10000:04d}"

        # 1. 识别查询意图
        intent = self._classify_query_intent(query)
        logger.info(f"查询意图: {intent}")

        # 2. 生成动态提示词
        prompts = await self.prompt_manager.generate_context_aware_prompts(
            user_query=query,
            patent_text=patent_text,
            context_type=intent,
            additional_context=context
        )
        self.service_stats['prompt_generated'] += 1

        # 3. 保存会话
        await self.prompt_manager.save_prompt_session(query_id, prompts)

        # 4. 构建响应
        response = {
            'query_id': query_id,
            'intent': intent,
            'prompts': prompts,
            'suggested_actions': self._generate_suggested_actions(intent),
            'knowledge_sources': self._get_knowledge_sources(),
            'metadata': {
                'query_length': len(query),
                'patent_text_length': len(patent_text),
                'timestamp': datetime.now().isoformat()
            }
        }

        # 5. 更新统计
        if 'knowledge_guidance' in prompts:
            self.service_stats['knowledge_hits'] += 1

        return response

    def _classify_query_intent(self, query: str) -> str:
        """分类查询意图"""
        query_lower = query.lower()

        # 意图分类
        intents = {
            "patent_review": ["审查", "授权", "驳回", "意见", "通知", "审查意见", "答复"],
            "legal_advice": ["法律", "侵权", "诉讼", "纠纷", "维权", "风险", "建议"],
            "technical_analysis": ["技术方案", "创新点", "技术效果", "实施方式", "技术问题"],
            "patent_search": ["检索", "搜索", "查找", "相似", "现有技术", "对比"],
            "patent_filing": ["申请", "提交", "文件", "流程", "程序", "费用"],
            "patent_value": ["价值", "评估", "市场", "商业化", "许可", "转让"],
            "general_inquiry": ["什么是", "如何", "为什么", "解释", "说明"]
        }

        # 匹配意图
        for intent, keywords in intents.items():
            if any(kw in query_lower for kw in keywords):
                return intent

        # 默认返回通用查询
        return "general_inquiry"

    def _generate_suggested_actions(self, intent: str) -> list[dict[str, str]:
        """生成建议的操作"""
        action_map = {
            "patent_review": [
                {"action": "generate_review_opinion", "label": "生成审查意见"},
                {"action": "check_formalities", "label": "检查形式要件"},
                {"action": "search_prior_art", "label": "检索现有技术"}
            ],
            "legal_advice": [
                {"action": "assess_infringement_risk", "label": "评估侵权风险"},
                {"action": "provide_legal_basis", "label": "提供法律依据"},
                {"action": "suggest_strategy", "label": "建议应对策略"}
            ],
            "technical_analysis": [
                {"action": "identify_innovation", "label": "识别创新点"},
                {"action": "analyze_feasibility", "label": "分析技术可行性"},
                {"action": "compare_with_state_of_art", "label": "与现有技术对比"}
            ],
            "patent_search": [
                {"action": "similarity_search", "label": "相似性检索"},
                {"action": "keyword_search", "label": "关键词检索"},
                {"action": "classification_search", "label": "分类号检索"}
            ]
        }

        return action_map.get(intent, [
            {"action": "general_analysis", "label": "综合分析"}
        ])

    def _get_knowledge_sources(self) -> list[dict[str, str]:
        """获取知识来源信息"""
        return [
            {
                "name": "专利法律法规知识图谱",
                "type": "Knowledge Graph",
                "entity_count": "45个实体",
                "relation_count": "202个关系"
            },
            {
                "name": "SQLite专利知识图谱",
                "type": "Knowledge Graph",
                "entity_count": "125万+实体",
                "relation_count": "329万+关系"
            },
            {
                "name": "审查指南向量数据库",
                "type": "Vector Database",
                "vector_count": "53个向量",
                "dimensions": "768维"
            },
            {
                "name": "专利法律法规向量库",
                "type": "Vector Database",
                "vector_count": "191个向量",
                "dimensions": "1024维"
            }
        ]

    async def batch_process_queries(
        self,
        queries: list[dict[str, Any]
    ) -> list[dict[str, Any]:
        """批量处理查询"""
        results = []

        for query_data in queries:
            result = await self.process_patent_query(
                query=query_data.get('query', ''),
                patent_text=query_data.get('patent_text', ''),
                context=query_data.get('context', {}),
                user_id=query_data.get('user_id')
            )
            results.append(result)

        return results

    async def get_service_statistics(self) -> dict[str, Any]:
        """获取服务统计信息"""
        return {
            'statistics': self.service_stats,
            'uptime': datetime.now().isoformat(),
            'capabilities': {
                'intents_supported': [
                    "patent_review",
                    "legal_advice",
                    "technical_analysis",
                    "patent_search",
                    "patent_filing",
                    "patent_value",
                    "general_inquiry"
                ],
                'knowledge_sources_count': 4,
                'prompt_templates_count': len(self.prompt_manager.prompt_templates)
            }
        }

    async def export_knowledge_insights(self) -> dict[str, Any]:
        """导出知识洞察"""
        insights = {
            "knowledge_graph_summary": {
                "legal_entities": 45,
                "legal_relations": 202,
                "sqlite_entities": 1259138,
                "sqlite_relations": 3290630,
                "guideline_vectors": 53,
                "legal_vectors": 191
            },
            "rule_distribution": {
                "novelty_rules": "extracted from SQLite KG",
                "creativity_rules": "extracted from SQLite KG",
                "procedure_rules": "extracted from Legal KG",
                "guidance_rules": "from Vector DB"
            },
            "integration_benefits": [
                "统一的规则提取",
                "上下文感知的提示词生成",
                "多源知识融合",
                "智能意图识别",
                "动态响应生成"
            ]
        }

        return insights

# 服务实例
_integrated_service = None

async def get_integrated_patent_service():
    """获取集成专利服务实例"""
    global _integrated_service
    if _integrated_service is None:
        _integrated_service = IntegratedPatentService()
        await _integrated_service.initialize()
    return _integrated_service

# API接口示例
async def api_example():
    """API使用示例"""
    service = await get_integrated_patent_service()

    # 示例1: 专利审查咨询
    review_query = await service.process_patent_query(
        query="这个专利的新颖性如何判断？",
        patent_text="本发明涉及一种基于AI的智能控制系统...",
        context={"application_number": "CN202410001234.5"}
    )

    # 示例2: 法律风险咨询
    legal_query = await service.process_patent_query(
        query="这个方案是否可能侵犯现有专利？",
        patent_text="技术方案描述...",
        context={"user_type": "企业", "industry": "AI"}
    )

    # 输出结果
    print("\n=== 专利审查响应 ===")
    print(f"查询ID: {review_query['query_id']}")
    print(f"意图: {review_query['intent']}")
    print(f"建议操作: {review_query['suggested_actions']}")

    print("\n=== 法律咨询响应 ===")
    print(f"查询ID: {legal_query['query_id']}")
    print(f"意图: {legal_query['intent']}")

if __name__ == "__main__":
    asyncio.run(api_example())
