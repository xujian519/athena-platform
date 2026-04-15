#!/usr/bin/env python3
"""
小娜NLP集成服务
将小诺NLP服务的能力集成到小娜系统中

作者: 小诺·双鱼公主
创建时间: 2025-12-26
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import httpx


class XiaonaIntent(Enum):
    """小娜专用意图分类"""
    # 法律咨询类
    LAW_QUERY = "law_query"              # 法条查询
    LAW_EXPLAIN = "law_explain"          # 法条解释
    LAW_RELATION = "law_relation"        # 法条关联

    # 案例分析类
    CASE_SEARCH = "case_search"          # 案例检索
    CASE_ANALYSIS = "case_analysis"      # 案例分析

    # 专利撰写类
    PATENT_WRITING = "patent_writing"    # 专利撰写
    TECH_ANALYSIS = "tech_analysis"      # 技术分析
    DISCLOSURE_UNDERSTAND = "disclosure_understand"  # 理解交底书

    # 审查意见类
    OFFICE_ACTION = "office_action"      # 审查意见答复
    NOVELTY_RESPONSE = "novelty_response"  # 新颖性答复
    CREATIVITY_RESPONSE = "creativity_response"  # 创造性答复

    # 通用类
    GENERAL_QUERY = "general_query"      # 一般咨询
    CLARIFICATION = "clarification"      # 参数澄清
    UNKNOWN = "unknown"                  # 未知意图


@dataclass
class NLPEnhancement:
    """NLP增强结果"""
    intent: str                         # 识别的意图
    confidence: float                   # 置信度
    entities: list[dict[str, Any]]      # 提取的实体
    extracted_params: dict[str, Any]    # 提取的参数
    missing_params: list[str]           # 缺失的参数
    suggested_scenario: str             # 建议的场景
    enhanced_query: str                 # 增强的查询
    complexity_level: str               # 复杂度等级 (simple/medium/complex)


class XiaonaNLPIntegration:
    """
    小娜NLP集成服务

    功能:
    1. 意图识别 - 自动识别用户查询意图
    2. 实体提取 - 提取专利号、法条编号等关键实体
    3. 场景推荐 - 基于意图推荐最佳业务场景
    4. 参数补全 - 识别缺失参数并生成追问
    5. 复杂度评估 - 评估查询复杂度，指导模型选择
    """

    # 复杂查询关键词
    COMPLEX_KEYWORDS = [
        "创造性分析", "三步法", "技术启示",
        "无效宣告", "无效策略", "无效分析",
        "权利要求修改", "答复策略",
        "多法条关联", "法条关系",
        "对比文件分析", "区别特征",
        "最接近现有技术", "实际解决技术问题"
    ]

    # 简单查询关键词
    SIMPLE_KEYWORDS = [
        "什么是", "是什么", "如何定义",
        "法条查询", "查询法条",
        "简单解释", "简述",
        "流程", "步骤"
    ]

    # 意图到场景的映射
    INTENT_TO_SCENARIO = {
        XiaonaIntent.PATENT_WRITING: "patent_writing",
        XiaonaIntent.TECH_ANALYSIS: "patent_writing",
        XiaonaIntent.DISCLOSURE_UNDERSTAND: "patent_writing",
        XiaonaIntent.OFFICE_ACTION: "office_action",
        XiaonaIntent.NOVELTY_RESPONSE: "office_action",
        XiaonaIntent.CREATIVITY_RESPONSE: "office_action",
        XiaonaIntent.LAW_QUERY: "general",
        XiaonaIntent.LAW_EXPLAIN: "general",
        XiaonaIntent.GENERAL_QUERY: "general"
    }

    def __init__(self,
                 nlp_service_url: str = "http://localhost:8001",
                 timeout: float = 5.0,
                 enable_cache: bool = True):
        """
        初始化NLP集成服务

        Args:
            nlp_service_url: NLP服务地址
            timeout: 请求超时时间
            enable_cache: 是否启用缓存
        """
        self.nlp_service_url = nlp_service_url.rstrip('/')
        self.timeout = timeout
        self.enable_cache = enable_cache

        # HTTP客户端
        self._client: httpx.AsyncClient | None = None

        # 缓存
        self._cache: dict[str, NLPEnhancement] = {}

        # 日志
        self.logger = logging.getLogger(__name__)

        # 专利领域实体模式
        self._init_entity_patterns()

    def _init_entity_patterns(self) -> Any:
        """初始化实体识别模式"""
        self.entity_patterns = {
            "patent_number": r"(?:CN|ZL)?\d{8,10}[A-Z]?\d?(?:\.\d)?",
            "law_article": r"(?:专利法|实施细则|审查指南)(?:第)?[\d一二三四五六七八九十]+(?:条|款|项|章|节)",
            "decision_number": r"\d+W\d{6}",
            "application_number": r"\d{12}\.\d",
            "date": r"\d{4}[-年]\d{1,2}[-月]\d{1,2}",
            "ipc_classification": r"[A-H]\d{2}[A-Z]\s*\d{1,2}/\d{2}"
        }

    async def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.nlp_service_url,
                timeout=self.timeout
            )
        return self._client

    async def close(self):
        """关闭连接"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def enhance_query(self,
                           query: str,
                           user_id: str = None,
                           session_id: str = None) -> NLPEnhancement:
        """
        增强查询

        Args:
            query: 用户查询
            user_id: 用户ID
            session_id: 会话ID

        Returns:
            NLP增强结果
        """
        # 检查缓存
        cache_key = f"{query}_{user_id}_{session_id}"
        if self.enable_cache and cache_key in self._cache:
            return self._cache[cache_key]

        try:
            # 调用NLP服务
            nlp_result = await self._call_nlp_service(query, user_id, session_id)

            # 转换为小娜专用格式
            enhancement = self._convert_to_xiaona_format(nlp_result, query)

            # 缓存结果
            if self.enable_cache:
                self._cache[cache_key] = enhancement

            return enhancement

        except Exception as e:
            self.logger.warning(f"NLP服务调用失败，使用本地规则: {e}")
            # 降级到本地规则
            return self._local_enhancement(query)

    async def _call_nlp_service(self,
                                query: str,
                                user_id: str = None,
                                session_id: str = None) -> dict[str, Any]:
        """调用NLP服务"""
        client = await self._get_client()

        payload = {"text": query}
        if user_id:
            payload["user_id"] = user_id
        if session_id:
            payload["session_id"] = session_id

        response = await client.post("/process", json=payload)
        response.raise_for_status()

        return response.json()

    def _convert_to_xiaona_format(self,
                                  nlp_result: dict[str, Any],
                                  original_query: str) -> NLPEnhancement:
        """将NLP服务结果转换为小娜格式"""
        # 提取意图
        raw_intent = nlp_result.get("intent", "UNKNOWN")
        intent = self._map_intent(raw_intent)

        # 提取实体
        entities = nlp_result.get("entities", [])

        # 提取参数
        extracted_params = nlp_result.get("extracted_parameters", {})

        # 识别缺失参数
        missing_params = self._identify_missing_params(intent, extracted_params)

        # 推荐场景
        suggested_scenario = self._recommend_scenario(intent, original_query)

        # 增强查询
        enhanced_query = self._enhance_query_text(original_query, entities, extracted_params)

        # 评估复杂度
        complexity_level = self._assess_complexity(original_query, intent)

        return NLPEnhancement(
            intent=intent.value,
            confidence=nlp_result.get("confidence", 0.0),
            entities=entities,
            extracted_params=extracted_params,
            missing_params=missing_params,
            suggested_scenario=suggested_scenario,
            enhanced_query=enhanced_query,
            complexity_level=complexity_level
        )

    def _map_intent(self, raw_intent: str) -> XiaonaIntent:
        """映射NLP服务意图到小娜意图"""
        intent_mapping = {
            "query": XiaonaIntent.GENERAL_QUERY,
            "patent_query": XiaonaIntent.CASE_SEARCH,
            "patent_analysis": XiaonaIntent.CASE_ANALYSIS,
            "law_query": XiaonaIntent.LAW_QUERY,
            "tech_writing": XiaonaIntent.PATENT_WRITING,
            "office_action": XiaonaIntent.OFFICE_ACTION
        }

        return intent_mapping.get(raw_intent, XiaonaIntent.UNKNOWN)

    def _identify_missing_params(self,
                                intent: XiaonaIntent,
                                extracted_params: dict[str, Any]) -> list[str]:
        """识别缺失参数"""
        required_params = {
            XiaonaIntent.LAW_QUERY: ["law_article"],
            XiaonaIntent.CASE_SEARCH: ["patent_number", "decision_number", "keywords"],
            XiaonaIntent.CREATIVITY_RESPONSE: ["patent_number", "d1_reference", "d2_reference"],
            XiaonaIntent.PATENT_WRITING: ["technical_field", "technical_problem", "technical_solution"]
        }

        required = required_params.get(intent, [])
        missing = [p for p in required if p not in extracted_params]

        return missing

    def _recommend_scenario(self, intent: XiaonaIntent, query: str) -> str:
        """推荐业务场景"""
        # 基于意图推荐
        if intent in self.INTENT_TO_SCENARIO:
            return self.INTENT_TO_SCENARIO[intent]

        # 基于关键词推荐
        query_lower = query.lower()

        scenario_keywords = {
            "patent_writing": ["撰写", "交底书", "申请", "技术方案", "权利要求书"],
            "office_action": ["审查意见", "答复", "驳回", "审查员", "oa", "通知书"],
            "general": ["查询", "是什么", "如何", "解释", "说明"]
        }

        for scenario, keywords in scenario_keywords.items():
            if any(kw in query for kw in keywords):
                return scenario

        return "general"

    def _enhance_query_text(self,
                           original_query: str,
                           entities: list[dict[str, Any]],
                           params: dict[str, Any]) -> str:
        """增强查询文本"""
        enhanced_parts = [original_query]

        # 添加实体信息
        if entities:
            enhanced_parts.append("\n【识别实体】")
            for entity in entities[:5]:  # 最多5个
                enhanced_parts.append(f"- {entity.get('type', '')}: {entity.get('text', '')}")

        # 添加参数信息
        if params:
            enhanced_parts.append("\n【提取参数】")
            for key, value in params.items():
                enhanced_parts.append(f"- {key}: {value}")

        return "\n".join(enhanced_parts)

    def _assess_complexity(self, query: str, intent: XiaonaIntent) -> str:
        """评估查询复杂度"""
        query_lower = query.lower()

        # 检查复杂查询关键词
        if any(kw in query for kw in self.COMPLEX_KEYWORDS):
            return "complex"

        # 检查简单查询关键词
        if any(kw in query for kw in self.SIMPLE_KEYWORDS):
            return "simple"

        # 检查特定意图
        complex_intents = [
            XiaonaIntent.CREATIVITY_RESPONSE,
            XiaonaIntent.CASE_ANALYSIS,
            XiaonaIntent.PATENT_WRITING
        ]

        if intent in complex_intents:
            return "complex"

        # 检查查询长度
        if len(query) > 200:
            return "complex"

        # 检查是否包含多个问题
        if query.count('?') > 1 or query.count('？') > 1:
            return "complex"

        # 默认中等复杂度
        return "medium"

    def _local_enhancement(self, query: str) -> NLPEnhancement:
        """本地规则增强（NLP服务不可用时）"""
        # 简单的本地规则
        intent = XiaonaIntent.GENERAL_QUERY
        confidence = 0.6
        entities = []
        extracted_params = {}

        # 本地关键词匹配
        query_lower = query.lower()

        if "法条" in query_lower or "专利法" in query_lower:
            intent = XiaonaIntent.LAW_QUERY
            confidence = 0.8

        elif "审查意见" in query_lower or "答复" in query_lower:
            intent = XiaonaIntent.OFFICE_ACTION
            confidence = 0.85

        elif "撰写" in query_lower or "交底书" in query_lower:
            intent = XiaonaIntent.PATENT_WRITING
            confidence = 0.8

        # 推荐场景
        suggested_scenario = self._recommend_scenario(intent, query)

        # 评估复杂度
        complexity_level = self._assess_complexity(query, intent)

        return NLPEnhancement(
            intent=intent.value,
            confidence=confidence,
            entities=entities,
            extracted_params=extracted_params,
            missing_params=[],
            suggested_scenario=suggested_scenario,
            enhanced_query=query,
            complexity_level=complexity_level
        )

    def get_model_recommendation(self, complexity_level: str) -> str:
        """
        基于复杂度推荐LLM模型

        Args:
            complexity_level: 复杂度等级

        Returns:
            推荐的模型名称
        """
        model_mapping = {
            "simple": "glm-4-flash",      # 简单查询用Flash，快速响应
            "medium": "glm-4-flash",      # 中等复杂度也用Flash，性价比高
            "complex": "glm-4"            # 复杂查询用完整模型，保证质量
        }

        return model_mapping.get(complexity_level, "glm-4-flash")

    def generate_clarification_questions(self,
                                        missing_params: list[str],
                                        intent: str) -> list[str]:
        """
        生成参数澄清问题

        Args:
            missing_params: 缺失的参数列表
            intent: 用户意图

        Returns:
            澄清问题列表
        """
        questions = []

        param_questions = {
            "law_article": "请问您想查询哪条法条？(例如：专利法第22条第3款)",
            "patent_number": "请问专利号是多少？",
            "decision_number": "请问决定书编号是多少？",
            "d1_reference": "请提供对比文件D1的信息",
            "d2_reference": "请提供对比文件D2的信息",
            "technical_field": "请问技术领域是什么？",
            "technical_problem": "请描述要解决的技术问题",
            "technical_solution": "请描述技术方案"
        }

        for param in missing_params:
            if param in param_questions:
                questions.append(param_questions[param])

        return questions


# 单例实例
_nlp_integration_instance: XiaonaNLPIntegration | None = None


def get_xiaona_nlp_integration(
    nlp_service_url: str = "http://localhost:8001",
    **kwargs
) -> XiaonaNLPIntegration:
    """
    获取小娜NLP集成服务单例

    Args:
        nlp_service_url: NLP服务地址
        **kwargs: 其他配置参数

    Returns:
        NLP集成服务实例
    """
    global _nlp_integration_instance

    if _nlp_integration_instance is None:
        _nlp_integration_instance = XiaonaNLPIntegration(
            nlp_service_url=nlp_service_url,
            **kwargs
        )
        logging.info("✅ 创建小娜NLP集成服务单例")

    return _nlp_integration_instance


async def enhance_query_sync(query: str,
                            user_id: str = None,
                            session_id: str = None) -> NLPEnhancement:
    """
    便捷的查询增强函数

    Args:
        query: 用户查询
        user_id: 用户ID
        session_id: 会话ID

    Returns:
        NLP增强结果
    """
    integration = get_xiaona_nlp_integration()
    return await integration.enhance_query(query, user_id, session_id)


if __name__ == "__main__":
    # 测试代码
    import asyncio

    async def test():
        print("🧪 测试小娜NLP集成服务")
        print("=" * 60)

        integration = XiaonaNLPIntegration()

        test_queries = [
            "专利法第22条第3款是什么？",
            "审查员认为权利要求1不具备创造性，我该怎么答复？",
            "帮我分析这个技术交底书的核心创新点",
            "查询决定书5W123456",
            "什么是三步法？"
        ]

        for query in test_queries:
            print(f"\n📝 查询: {query}")

            enhancement = await integration.enhance_query(query)

            print(f"  意图: {enhancement.intent}")
            print(f"  置信度: {enhancement.confidence:.2f}")
            print(f"  推荐场景: {enhancement.suggested_scenario}")
            print(f"  复杂度: {enhancement.complexity_level}")
            print(f"  推荐模型: {integration.get_model_recommendation(enhancement.complexity_level)}")

            if enhancement.missing_params:
                print(f"  缺失参数: {enhancement.missing_params}")
                questions = integration.generate_clarification_questions(
                    enhancement.missing_params,
                    enhancement.intent
                )
                print("  追问问题:")
                for q in questions:
                    print(f"    - {q}")

        await integration.close()
        print("\n✅ 测试完成")

    asyncio.run(test())
