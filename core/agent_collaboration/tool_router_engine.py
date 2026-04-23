from __future__ import annotations
"""
智能工具路由引擎
负责智能体的工具选择和路由决策
"""

import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from loguru import logger

from .service_kg import ServiceCategory, ServiceKnowledgeGraph, get_service_kg


class RoutingStrategy(Enum):
    """路由策略"""

    SEMANTIC_MATCH = "semantic_match"  # 语义匹配
    KEYWORD_MATCH = "keyword_match"  # 关键词匹配
    HYBRID = "hybrid"  # 混合策略
    CONFIDENCE_BASED = "confidence_based"  # 基于置信度
    LEARNING_BASED = "learning_based"  # 基于学习


@dataclass
class RoutingDecision:
    """路由决策结果"""

    service_id: str
    service_name: str
    confidence: float  # 决策置信度
    reasoning: str  # 决策理由
    alternative_services: list[tuple[str, float]] = field(default_factory=list)  # 备选方案
    estimated_time: float = 0.0  # 预估响应时间
    cost: float = 0.0  # 预估成本

    def to_dict(self) -> dict[str, Any]:
        return {
            "service_id": self.service_id,
            "service_name": self.service_name,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "alternative_services": self.alternative_services,
            "estimated_time": self.estimated_time,
            "cost": self.cost,
        }


@dataclass
class UserIntent:
    """用户意图解析结果"""

    primary_intent: str  # 主要意图
    secondary_intents: list[str]  # 次要意图
    entities: dict[str, Any]  # 实体信息
    keywords: list[str]  # 关键词
    complexity: float  # 复杂度 (0-1)
    urgency: float  # 紧急程度 (0-1)


class IntentAnalyzer:
    """意图分析器"""

    # 意图关键词映射
    INTENT_KEYWORDS = {
        "patent_search": [
            "专利",
            "搜索",
            "检索",
            "查询",
            "查找",
            "专利搜索",
            "patent",
            "search",
            "检索专利",
            "找专利",
        ],
        "patent_analysis": [
            "专利",
            "分析",
            "评估",
            "价值分析",
            "技术分析",
            "专利分析",
            "分析专利",
            "评估专利",
            "专利价值",
            "技术趋势",
            "竞争对手",
            "技术含量",
        ],
        "patent_download": ["下载", "获取", "全文", "PDF", "专利下载", "下载专利", "获取全文"],
        "knowledge_graph": [
            "知识图谱",
            "关系",
            "关联",
            "图谱",
            "关联分析",
            "知识关系",
            "图谱查询",
            "实体识别",
            "关系推理",
        ],
        "browser_control": [
            "浏览器",
            "网页",
            "截图",
            "浏览器控制",
            "自动化",
            "网页操作",
            "打开网页",
            "访问网站",
            "Chrome",
            "浏览器自动化",
        ],
        "autonomous_control": [
            "自主控制",
            "自动执行",
            "任务自动化",
            "自主任务",
            "工作流",
            "智能决策",
            "自动化执行",
        ],
        "academic_search": [
            "论文",
            "学术",
            "文献",
            "学术搜索",
            "参考文献",
            "学术论文",
            "文献检索",
            "Semantic Scholar",
            "论文引用",
        ],
        "map_service": [
            "地图",
            "位置",
            "导航",
            "路径",
            "地址",
            "路线规划",
            "地理编码",
            "周边搜索",
            "高德",
            "地图服务",
        ],
        "ai_service": [
            "向量嵌入",
            "重排序",
            "Jina AI",
            "文本嵌入",
            "文档重排序",
            "内容提取",
            "AI服务",
        ],
        "storage_service": [
            "存储",
            "向量存储",
            "缓存",
            "数据库",
            "键值存储",
            "相似度检索",
            "向量数据库",
        ],
        "monitoring": [
            "监控",
            "指标",
            "可视化",
            "仪表盘",
            "Grafana",
            "Prometheus",
            "监控数据",
            "性能监控",
        ],
    }

    def analyze(self, user_input: str) -> UserIntent:
        """分析用户输入意图"""
        user_input_lower = user_input.lower()

        # 提取关键词
        keywords = self._extract_keywords(user_input)

        # 匹配意图
        primary_intent, secondary_intents = self._match_intents(user_input_lower)

        # 提取实体
        entities = self._extract_entities(user_input)

        # 计算复杂度和紧急程度
        complexity = self._calculate_complexity(user_input, entities)
        urgency = self._calculate_urgency(user_input)

        return UserIntent(
            primary_intent=primary_intent,
            secondary_intents=secondary_intents,
            entities=entities,
            keywords=keywords,
            complexity=complexity,
            urgency=urgency,
        )

    def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词 - 从服务关键词库中匹配"""
        keywords = []

        # 基础领域关键词(保持向后兼容)
        domain_keywords_map = {
            "patent": ["专利", "patent"],
            "browser": ["浏览器", "网页", "自动化", "Chrome", "浏览器控制"],
            "knowledge": ["知识图谱", "图谱", "关系"],
            "academic": ["论文", "学术", "文献", "学术搜索"],
            "map": ["地图", "导航", "路线", "位置"],
            "analysis": ["分析", "评估", "价值分析", "技术分析"],
            "ai": ["机器学习", "深度学习", "向量嵌入", "Jina AI"],  # 移除通用的"AI"和"人工智能"
            "control": ["自主控制", "任务自动化", "工作流"],
            "storage": ["存储", "向量存储", "缓存", "数据库"],
        }

        # 从文本中提取匹配的关键词
        for _domain, domain_keywords in domain_keywords_map.items():
            for kw in domain_keywords:
                if kw in text:
                    keywords.append(kw)

        # 使用知识图谱服务的关键词库进行动态匹配(如果可用)
        try:
            from core.agent_collaboration.service_kg import get_service_kg

            kg = get_service_kg()

            # 获取所有服务的关键词作为词汇表
            all_service_keywords = set()
            for service in kg.get_all_services():
                all_service_keywords.update(service.keywords)

            # 在文本中匹配服务关键词
            for service_keyword in all_service_keywords:
                if service_keyword in text and service_keyword not in keywords:
                    keywords.append(service_keyword)
        except Exception:
            pass  # 如果知识图谱不可用,使用基础关键词

        return keywords

    def _match_intents(self, text: str) -> tuple[str, list[str]]:
        """匹配意图 - 改进版,支持上下文感知优先级"""
        intent_scores = {}

        # 定义意图优先级(数字越小优先级越高)
        intent_priority = {
            "patent_download": 1,  # 最具体
            "knowledge_graph": 2,
            "browser_control": 3,
            "academic_search": 4,
            "map_service": 5,
            "ai_service": 6,
            "storage_service": 7,
            "monitoring": 8,
            "autonomous_control": 9,
            "patent_analysis": 10,
            "patent_search": 11,  # 最通用,优先级最低
        }

        # 同义词扩展
        synonym_map = {
            "路线": ["路径", "路线规划"],
            "论文": ["学术论文", "文献"],
            "浏览器": ["Chrome", "浏览器控制"],
            "专利": ["patent", "专利检索"],
        }

        # 扩展文本以包含同义词
        expanded_text = text
        for term, synonyms in synonym_map.items():
            if term in text:
                for synonym in synonyms:
                    if synonym not in expanded_text:
                        expanded_text += " " + synonym

        # 上下文感知的意图匹配
        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = 0
            for kw in keywords:
                if kw in expanded_text:
                    # 原始文本中的关键词得2分,扩展的得1分
                    score += 2 if kw in text else 1

            if score > 0:
                # 优先级加权:优先级高的得分加倍
                priority = intent_priority.get(intent, 10)
                weighted_score = score * (12 - priority) / 10  # 优先级1加权1.1倍,优先级11加权0.1倍

                # 特殊处理:当同时有"搜索"和"分析"时,根据主导词调整
                if "搜索" in text and intent == "patent_search":
                    weighted_score *= 1.2  # 搜索优先
                elif "分析" in text and intent == "patent_analysis":
                    weighted_score *= 1.2  # 分析优先

                intent_scores[intent] = weighted_score

        if not intent_scores:
            return "unknown", []

        # 按加权分数排序
        sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)  # type: ignore[arg-type]
        primary_intent = sorted_intents[0][0]
        secondary_intents = [intent for intent, _ in sorted_intents[1:4]]

        return primary_intent, secondary_intents

    def _extract_entities(self, text: str) -> dict[str, Any]:
        """提取实体信息"""
        entities = {}

        # 提取专利号
        patent_pattern = r"(CN|US|JP|EP)?\s*\d{7,}"
        patents = re.findall(patent_pattern, text)
        if patents:
            entities["patent_numbers"] = patents

        # 提取年份
        year_pattern = r"(19|20)\d{2}"
        years = re.findall(year_pattern, text)
        if years:
            entities["years"] = years

        # 提取技术领域关键词
        tech_fields = []
        if "人工智能" in text or "AI" in text.upper():
            tech_fields.append("AI")
        if "机器学习" in text:
            tech_fields.append("机器学习")
        if "区块链" in text:
            tech_fields.append("区块链")

        if tech_fields:
            entities["tech_fields"] = tech_fields

        return entities

    def _calculate_complexity(self, text: str, entities: dict[str, Any]) -> float:
        """计算任务复杂度 (0-1)"""
        complexity = 0.0

        # 文本长度因子
        text_length_factor = min(1.0, len(text) / 200)
        complexity += text_length_factor * 0.3

        # 实体数量因子
        entity_count = sum(len(v) if isinstance(v, list) else 1 for v in entities.values())
        entity_factor = min(1.0, entity_count / 5)
        complexity += entity_factor * 0.4

        # 关键词复杂度
        if "分析" in text and "搜索" in text:
            complexity += 0.3  # 多步骤任务

        return min(1.0, complexity)

    def _calculate_urgency(self, text: str) -> float:
        """计算紧急程度 (0-1)"""
        urgency = 0.0

        urgent_keywords = ["紧急", "立即", "马上", "尽快", "急需"]
        for kw in urgent_keywords:
            if kw in text:
                urgency += 0.2

        return min(1.0, urgency)


class ToolRouterEngine:
    """智能工具路由引擎"""

    def __init__(
        self,
        service_kg: ServiceKnowledgeGraph | None = None,
        strategy: RoutingStrategy = RoutingStrategy.HYBRID,
    ):
        self.service_kg = service_kg or get_service_kg()
        self.strategy = strategy
        self.intent_analyzer = IntentAnalyzer()

        # 路由历史记录(用于学习优化)
        self.routing_history: list[dict[str, Any]] = []

        logger.info(f"智能工具路由引擎初始化完成,策略: {strategy.value}")

    async def route(
        self, user_input: str, context: Optional[dict[str, Any]] = None, top_k: int = 3
    ) -> list[RoutingDecision]:
        """路由决策"""
        # 1. 分析用户意图
        intent = self.intent_analyzer.analyze(user_input)
        logger.info(f"意图分析结果: {intent.primary_intent}")

        # 2. 根据策略选择服务
        if self.strategy == RoutingStrategy.SEMANTIC_MATCH:
            decisions = await self._semantic_route(intent, top_k)
        elif self.strategy == RoutingStrategy.KEYWORD_MATCH:
            decisions = await self._keyword_route(intent, top_k)
        elif self.strategy == RoutingStrategy.CONFIDENCE_BASED:
            decisions = await self._confidence_route(intent, top_k)
        else:  # HYBRID
            decisions = await self._hybrid_route(intent, top_k, context)

        # 3. 记录路由历史
        self._record_routing(user_input, intent, decisions)

        return decisions

    async def _semantic_route(self, intent: UserIntent, top_k: int) -> list[RoutingDecision]:
        """语义路由"""
        decisions = []

        # 构造查询
        query = f"{intent.primary_intent} {' '.join(intent.keywords)}"

        # 语义搜索
        search_results = self.service_kg.semantic_search(query, embedding_model=None, top_k=top_k)

        for service_id, score in search_results:
            service = self.service_kg.get_service(service_id)
            if service:
                decisions.append(
                    RoutingDecision(
                        service_id=service_id,
                        service_name=service.service_name,
                        confidence=score / 10.0,  # 归一化
                        reasoning=f"语义匹配度: {score}, 意图: {intent.primary_intent}",
                        estimated_time=service.avg_response_time,
                        cost=0.0,
                    )
                )

        return decisions

    async def _keyword_route(self, intent: UserIntent, top_k: int) -> list[RoutingDecision]:
        """关键词路由"""
        decisions = []

        # 关键词搜索
        search_results = self.service_kg.search_by_keywords(intent.keywords, top_k=top_k)

        for service_id, score in search_results:
            service = self.service_kg.get_service(service_id)
            if service:
                decisions.append(
                    RoutingDecision(
                        service_id=service_id,
                        service_name=service.service_name,
                        confidence=min(1.0, score / len(intent.keywords)),
                        reasoning=f"关键词匹配: {score}/{len(intent.keywords)}",
                        estimated_time=service.avg_response_time,
                        cost=0.0,
                    )
                )

        return decisions

    async def _confidence_route(self, intent: UserIntent, top_k: int) -> list[RoutingDecision]:
        """基于置信度的路由"""
        decisions = []

        # 获取所有服务并按置信度排序
        all_services = self.service_kg.get_all_services()
        sorted_services = sorted(all_services, key=lambda s: s.confidence_score, reverse=True)

        # 根据意图过滤
        category_map = {
            "patent_search": ServiceCategory.PATENT,
            "patent_analysis": ServiceCategory.ANALYSIS,
            "patent_download": ServiceCategory.PATENT,
            "knowledge_graph": ServiceCategory.KNOWLEDGE,
            "browser_control": ServiceCategory.BROWSER,
            "autonomous_control": ServiceCategory.CONTROL,
        }

        target_category = category_map.get(intent.primary_intent)

        for service in sorted_services[: top_k * 2]:  # 多取一些候选
            if target_category is None or service.category == target_category:
                decisions.append(
                    RoutingDecision(
                        service_id=service.service_id,
                        service_name=service.service_name,
                        confidence=service.confidence_score,
                        reasoning=f"综合置信度评分: {service.confidence_score:.3f}",
                        estimated_time=service.avg_response_time,
                        cost=0.0,
                    )
                )

                if len(decisions) >= top_k:
                    break

        return decisions

    async def _hybrid_route(
        self, intent: UserIntent, top_k: int, context: dict[str, Any]
    ) -> list[RoutingDecision]:
        """混合路由策略(推荐)- 改进版,支持意图过滤"""
        decisions = []
        service_scores: dict[str, float] = {}
        matched_services = set()

        # 1. 关键词匹配评分 (40%)
        keyword_results = self.service_kg.search_by_keywords(intent.keywords, top_k=20)
        for service_id, score in keyword_results:
            service_scores[service_id] = service_scores.get(service_id, 0.0) + score * 0.4
            matched_services.add(service_id)

        # 2. 语义搜索评分 (40%)
        query = f"{intent.primary_intent} {' '.join(intent.keywords)}"
        semantic_results = self.service_kg.semantic_search(query, embedding_model=None, top_k=20)
        for service_id, score in semantic_results:
            service_scores[service_id] = service_scores.get(service_id, 0.0) + score * 0.4
            matched_services.add(service_id)

        # 3. 置信度评分 (20%) - 只对匹配的服务应用
        for service_id in matched_services:
            service = self.service_kg.get_service(service_id)
            if service:
                service_scores[service_id] = (
                    service_scores.get(service_id, 0.0) + service.confidence_score * 2.0
                )

        # 意图到分类的映射
        intent_to_category = {
            "patent_search": ServiceCategory.PATENT,
            "patent_analysis": ServiceCategory.ANALYSIS,
            "patent_download": ServiceCategory.PATENT,
            "knowledge_graph": ServiceCategory.KNOWLEDGE,
            "browser_control": ServiceCategory.BROWSER,
            "autonomous_control": ServiceCategory.CONTROL,
            "academic_search": ServiceCategory.SEARCH,
            "map_service": ServiceCategory.UTILITY,
            "ai_service": ServiceCategory.ANALYSIS,
            "storage_service": ServiceCategory.STORAGE,
            "monitoring": ServiceCategory.MONITORING,
        }

        # 特殊处理:当查询同时包含"搜索"和"分析"时,优先PATENT分类
        # 因为yunpat-agent可以处理搜索和分析两种操作
        if ("搜索" in " ".join(intent.keywords) or "检索" in " ".join(intent.keywords)) and (
            "分析" in " ".join(intent.keywords) or "评估" in " ".join(intent.keywords)
        ):
            # 如果是专利相关的混合查询,使用PATENT分类
            if any(kw in " ".join(intent.keywords) for kw in ["专利", "patent"]):
                target_category = ServiceCategory.PATENT
            else:
                target_category = intent_to_category.get(intent.primary_intent)
        else:
            target_category = intent_to_category.get(intent.primary_intent)

        # 排序并按意图过滤
        sorted_results = sorted(service_scores.items(), key=lambda x: x[1], reverse=True)

        # 优先选择目标分类的服务
        category_matches: list[tuple[str, float]] = []
        other_matches: list[tuple[str, float]] = []

        for service_id, total_score in sorted_results:
            service = self.service_kg.get_service(service_id)
            if not service:
                continue

            if target_category and service.category == target_category:
                category_matches.append((service_id, total_score))
            else:
                other_matches.append((service_id, total_score))

        # 合并结果:优先返回目标分类的服务
        combined_results = category_matches + other_matches

        # 生成决策(返回top_k个)
        for service_id, total_score in combined_results[:top_k]:
            service = self.service_kg.get_service(service_id)
            if service:
                # 查找备选方案
                alternatives: list[tuple[str, float]] = [
                    (sid, score)
                    for sid, score in combined_results[top_k : top_k + 3]
                    if sid != service_id
                ]

                decisions.append(
                    RoutingDecision(
                        service_id=service_id,
                        service_name=service.service_name,
                        confidence=min(1.0, total_score / 10.0),
                        reasoning=(
                            f"混合评分: {total_score:.2f} "
                            f"(关键词+语义+置信度), 意图: {intent.primary_intent}"
                        ),
                        alternative_services=alternatives,
                        estimated_time=service.avg_response_time,
                        cost=0.0,
                    )
                )

        return decisions

    def _record_routing(
        self, user_input: str, intent: UserIntent, decisions: list[RoutingDecision]
    ):
        """记录路由历史"""
        record = {
            "user_input": user_input,
            "intent": intent.primary_intent,
            "decisions": [d.to_dict() for d in decisions],
            "timestamp": time.time(),
        }
        self.routing_history.append(record)

        # 限制历史记录数量
        if len(self.routing_history) > 1000:
            self.routing_history = self.routing_history[-1000:]

    def record_feedback(self, decision: RoutingDecision, satisfaction: float):
        """记录用户反馈,用于优化"""
        # 更新服务知识图谱
        self.service_kg.record_feedback(decision.service_id, satisfaction)

        # 更新路由历史中的反馈
        for record in reversed(self.routing_history):
            if record["decisions"] and record["decisions"][0]["service_id"] == decision.service_id:
                record["user_satisfaction"] = satisfaction
                break

        logger.info(f"已记录反馈: {decision.service_id}, 满意度: {satisfaction}")

    def get_statistics(self) -> dict[str, Any]:
        """获取路由统计信息"""
        if not self.routing_history:
            return {"total_routes": 0}

        # 统计最常用的服务
        service_usage: dict[str, int] = {}
        intent_distribution: dict[str, int] = {}

        for record in self.routing_history:
            intent = record.get("intent", "")
            if isinstance(intent, str):
                intent_distribution[intent] = intent_distribution.get(intent, 0) + 1

            decisions = record.get("decisions", [])
            if decisions and isinstance(decisions, list):
                first_decision = decisions[0]
                if isinstance(first_decision, dict):
                    service_id = first_decision.get("service_id")
                    if isinstance(service_id, str):
                        service_usage[service_id] = service_usage.get(service_id, 0) + 1

        return {
            "total_routes": len(self.routing_history),
            "intent_distribution": intent_distribution,
            "most_used_services": sorted(
                service_usage.items(), key=lambda x: x[1], reverse=True  # type: ignore[arg-type]
            )[:10],
            "strategy": self.strategy.value,
        }


# 全局路由引擎实例
_router_engine: ToolRouterEngine | None = None


def get_tool_router() -> ToolRouterEngine:
    """获取全局工具路由引擎实例"""
    global _router_engine
    if _router_engine is None:
        _router_engine = ToolRouterEngine()
    return _router_engine
