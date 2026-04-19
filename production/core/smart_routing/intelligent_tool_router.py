#!/usr/bin/env python3
from __future__ import annotations
"""
智能工具路由系统
Intelligent Tool Router

基于用户意图自动选择最优工具组合,并提供实时路由建议

作者: Athena AI系统
创建时间: 2025-12-08
版本: 1.0.0
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """意图类型枚举"""

    PATENT_SEARCH = "patent_search"
    OPINION_RESPONSE = "opinion_response"
    PATENT_DRAFTING = "patent_drafting"
    INFRINGEMENT_ANALYSIS = "infringement_analysis"
    TECHNICAL_EVALUATION = "technical_evaluation"
    CREATIVE_WRITING = "creative_writing"
    GENERAL_CONVERSATION = "general_conversation"
    SYSTEM_MONITORING = "system_monitoring"
    DATA_ANALYSIS = "data_analysis"


class ToolPriority(Enum):
    """工具优先级"""

    CRITICAL = "critical"  # 核心工具,必须使用
    IMPORTANT = "important"  # 重要工具,推荐使用
    OPTIONAL = "optional"  # 可选工具,按需使用


@dataclass
class ToolRecommendation:
    """工具推荐"""

    tool_name: str
    priority: ToolPriority
    confidence: float
    reason: str
    estimated_time: float
    dependencies: list[str] | None = None
    file_path: str = None


@dataclass
class RoutingResult:
    """路由结果"""

    intent_type: IntentType
    confidence: float
    primary_tools: list[ToolRecommendation]
    supporting_tools: list[ToolRecommendation]
    workflow: str
    estimated_total_time: float
    optimization_suggestions: list[str]
    fallback_options: list[str] | None = None


class IntelligentToolRouter:
    """智能工具路由系统"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 初始化工具数据库
        self.tool_database = self._initialize_tool_database()

        # 意图识别关键词
        self.intent_keywords = self._initialize_intent_keywords()

        # 性能监控数据
        self.performance_data = {}

        # 路由统计
        self.routing_stats = {
            "total_requests": 0,
            "successful_routes": 0,
            "intent_distribution": {},
            "tool_usage_stats": {},
            "average_response_time": 0.0,
        }

        self.logger.info("🧠 智能工具路由系统初始化完成")

    def _initialize_tool_database(self) -> dict[str, dict[str, Any]]:
        """初始化工具数据库"""
        return {
            # 专利检索工具
            "patent_crawler": {
                "file_path": "domains/patent/crawlers/production_real_patent_crawler.py",
                "category": "patent_search",
                "priority": ToolPriority.CRITICAL,
                "estimated_time": 30,
                "dependencies": ["internet_connection"],
                "success_rate": 0.92,
            },
            "enhanced_patent_perception": {
                "file_path": "core/perception/enhanced_patent_perception.py",
                "category": "patent_analysis",
                "priority": ToolPriority.CRITICAL,
                "estimated_time": 20,
                "dependencies": [],
                "success_rate": 0.95,
            },
            "patent_retrieval_workflow": {
                "file_path": "workflows/patent_retrieval_workflow.py",
                "category": "workflow",
                "priority": ToolPriority.IMPORTANT,
                "estimated_time": 60,
                "dependencies": ["patent_crawler", "vector_search"],
                "success_rate": 0.88,
            },
            # 审查意见答复工具
            "patent_professional_workflow": {
                "file_path": "workflows/patent_professional_workflow.py",
                "category": "workflow",
                "priority": ToolPriority.CRITICAL,
                "estimated_time": 180,
                "dependencies": ["patent_perception", "legal_analyzer"],
                "success_rate": 0.94,
            },
            "comprehensive_patent_processor": {
                "file_path": "domains/patent/services/comprehensive_patent_processor.py",
                "category": "patent_processing",
                "priority": ToolPriority.IMPORTANT,
                "estimated_time": 90,
                "dependencies": [],
                "success_rate": 0.91,
            },
            "chemical_analyzer": {
                "category": "chemical_analysis",
                "priority": ToolPriority.OPTIONAL,
                "estimated_time": 15,
                "dependencies": [],
                "success_rate": 0.89,
            },
            # 创意写作工具
            "xiaonuo_enhanced": {
                "file_path": "core/agent/xiaonuo_enhanced.py",
                "category": "creative_agent",
                "priority": ToolPriority.IMPORTANT,
                "estimated_time": 30,
                "dependencies": ["glm4_model"],
                "success_rate": 0.96,
            },
            "creative_writing_tool": {
                "file_path": "domains/creative/services/creative_writer.py",
                "category": "creative_writing",
                "priority": ToolPriority.IMPORTANT,
                "estimated_time": 25,
                "dependencies": [],
                "success_rate": 0.93,
            },
            # 系统监控工具
            "platform_manager": {
                "file_path": "core/autonomous_control/platform_manager.py",
                "category": "system_management",
                "priority": ToolPriority.CRITICAL,
                "estimated_time": 10,
                "dependencies": [],
                "success_rate": 0.99,
            },
            "health_monitor": {
                "file_path": "infrastructure/monitoring/health_monitor.py",
                "category": "system_monitoring",
                "priority": ToolPriority.IMPORTANT,
                "estimated_time": 15,
                "dependencies": [],
                "success_rate": 0.98,
            },
        }

    def _initialize_intent_keywords(self) -> dict[IntentType, list[dict[str, Any]]]:
        """初始化意图识别关键词"""
        return {
            IntentType.PATENT_SEARCH: [
                {"keywords": ["检索", "搜索", "查新", "现有技术", "对比文件"], "weight": 1.0},
                {"keywords": ["专利数据库", "Google Patents", "USPTO", "EPO"], "weight": 0.9},
                {"keywords": ["新颖性", "创造性", "专利性分析"], "weight": 0.8},
            ],
            IntentType.OPINION_RESPONSE: [
                {"keywords": ["审查意见", "审查员", "通知书", "答复", "补正"], "weight": 1.0},
                {"keywords": ["专利法第26条", "专利法第33条", "不清楚", "不支持"], "weight": 0.9},
                {"keywords": ["驳回", "修改", "权利要求"], "weight": 0.8},
            ],
            IntentType.PATENT_DRAFTING: [
                {"keywords": ["撰写", "申请", "权利要求", "说明书", "技术交底"], "weight": 1.0},
                {"keywords": ["专利申请文档", "申请文件", "提交"], "weight": 0.9},
                {"keywords": ["发明点", "技术特征", "保护范围"], "weight": 0.8},
            ],
            IntentType.CREATIVE_WRITING: [
                {"keywords": ["写作", "创作", "故事", "文案", "创意"], "weight": 1.0},
                {"keywords": ["小说", "诗歌", "剧本", "营销文案"], "weight": 0.9},
                {"keywords": ["想象力", "灵感", "艺术"], "weight": 0.7},
            ],
            IntentType.TECHNICAL_EVALUATION: [
                {"keywords": ["评估", "评价", "技术方案", "可行性"], "weight": 1.0},
                {"keywords": ["技术优势", "创新性", "市场前景"], "weight": 0.8},
                {"keywords": ["技术难点", "解决方案"], "weight": 0.7},
            ],
            IntentType.SYSTEM_MONITORING: [
                {"keywords": ["监控", "健康检查", "系统状态", "性能"], "weight": 1.0},
                {"keywords": ["日志", "错误", "故障", "优化"], "weight": 0.8},
            ],
        }

    async def route_request(
        self, user_input: str, context: dict[str, Any] | None = None
    ) -> RoutingResult:
        """智能路由请求"""
        start_time = time.time()

        self.routing_stats["total_requests"] += 1

        try:
            # 1. 意图识别
            intent_type, intent_confidence = await self._recognize_intent(user_input)

            # 2. 工具推荐
            primary_tools, supporting_tools = await self._recommend_tools(intent_type, user_input)

            # 3. 工作流确定
            workflow = self._determine_workflow(intent_type)

            # 4. 时间估算
            total_time = self._estimate_time(primary_tools, supporting_tools)

            # 5. 优化建议
            suggestions = await self._generate_optimization_suggestions(intent_type, user_input)

            # 6. 备选方案
            fallback_options = self._generate_fallback_options(intent_type)

            result = RoutingResult(
                intent_type=intent_type,
                confidence=intent_confidence,
                primary_tools=primary_tools,
                supporting_tools=supporting_tools,
                workflow=workflow,
                estimated_total_time=total_time,
                optimization_suggestions=suggestions,
                fallback_options=fallback_options,
            )

            # 更新统计
            self._update_routing_stats(intent_type, result, time.time() - start_time)

            self.logger.info(f"✅ 路由成功: {intent_type.value} (置信度: {intent_confidence:.2f})")

            return result

        except Exception as e:
            self.logger.error(f"❌ 路由失败: {e!s}")
            return self._create_fallback_result(user_input)

    async def _recognize_intent(self, user_input: str) -> tuple[IntentType, float]:
        """识别用户意图"""
        intent_scores = {}

        for intent_type, keyword_groups in self.intent_keywords.items():
            score = 0.0

            for keyword_group in keyword_groups:
                keywords = keyword_group["keywords"]
                weight = keyword_group["weight"]

                for keyword in keywords:
                    if keyword.lower() in user_input.lower():
                        score += weight

            if score > 0:
                intent_scores[intent_type] = score

        # 标准化分数
        if intent_scores:
            max_score = max(intent_scores.values())
            normalized_scores = {k: v / max_score for k, v in intent_scores.items()}
            best_intent = max(normalized_scores.keys(), key=lambda x: normalized_scores[x])
            confidence = normalized_scores[best_intent]

            # 更新意图分布统计
            if best_intent not in self.routing_stats["intent_distribution"]:
                self.routing_stats["intent_distribution"][best_intent] = 0
            self.routing_stats["intent_distribution"][best_intent] += 1

            return best_intent, confidence
        else:
            # 默认意图
            return IntentType.GENERAL_CONVERSATION, 0.5

    async def _recommend_tools(
        self, intent_type: IntentType, user_input: str
    ) -> tuple[list[ToolRecommendation], list[ToolRecommendation]]:
        """推荐工具"""
        primary_tools = []
        supporting_tools = []

        # 基于意图类型推荐核心工具
        intent_tool_mapping = {
            IntentType.PATENT_SEARCH: [
                "patent_crawler",
                "enhanced_patent_perception",
                "patent_retrieval_workflow",
            ],
            IntentType.OPINION_RESPONSE: [
                "patent_professional_workflow",
                "comprehensive_patent_processor",
            ],
            IntentType.PATENT_DRAFTING: ["patent_professional_workflow", "patent_ai_agent"],
            IntentType.CREATIVE_WRITING: ["xiaonuo_enhanced", "creative_writing_tool"],
            IntentType.SYSTEM_MONITORING: ["platform_manager", "health_monitor"],
        }

        core_tools = intent_tool_mapping.get(intent_type, [])

        # 转换为推荐对象
        for tool_name in core_tools:
            if tool_name in self.tool_database:
                tool_info = self.tool_database[tool_name]
                recommendation = ToolRecommendation(
                    tool_name=tool_name,
                    priority=tool_info["priority"],
                    confidence=tool_info.get("success_rate", 0.8),
                    reason=f"适合{intent_type.value}场景",
                    estimated_time=tool_info["estimated_time"],
                    dependencies=tool_info.get("dependencies", []),
                    file_path=tool_info["file_path"],
                )

                if tool_info["priority"] == ToolPriority.CRITICAL:
                    primary_tools.append(recommendation)
                else:
                    supporting_tools.append(recommendation)

        # 检查是否有化学式分析需求
        if any(
            keyword in user_input.lower() for keyword in ["化学式", "分子式", "反应式", "有机物"]
        ) and "chemical_analyzer" in self.tool_database:
            tool_info = self.tool_database["chemical_analyzer"]
            chemical_rec = ToolRecommendation(
                tool_name="chemical_analyzer",
                priority=ToolPriority.IMPORTANT,
                confidence=0.9,
                reason="检测到化学式分析需求",
                estimated_time=tool_info["estimated_time"],
                file_path=tool_info["file_path"],
            )
            supporting_tools.append(chemical_rec)

        return primary_tools, supporting_tools

    def _determine_workflow(self, intent_type: IntentType) -> str:
        """确定工作流"""
        workflow_mapping = {
            IntentType.PATENT_SEARCH: "专利检索工作流",
            IntentType.OPINION_RESPONSE: "专利专业工作流",
            IntentType.PATENT_DRAFTING: "专利撰写工作流",
            IntentType.CREATIVE_WRITING: "创意写作流程",
            IntentType.SYSTEM_MONITORING: "系统监控流程",
        }

        return workflow_mapping.get(intent_type, "通用处理流程")

    def _estimate_time(
        self, primary_tools: list[ToolRecommendation], supporting_tools: list[ToolRecommendation]
    ) -> float:
        """估算总时间"""
        total_time = 0

        # 主要工具时间(并行度0.7)
        primary_time = sum(tool.estimated_time for tool in primary_tools)
        total_time += primary_time * 0.7

        # 辅助工具时间(并行度0.5)
        supporting_time = sum(tool.estimated_time for tool in supporting_tools)
        total_time += supporting_time * 0.5

        # 基础处理时间
        total_time += 10  # 意图识别和路由时间

        return round(total_time, 1)

    async def _generate_optimization_suggestions(
        self, intent_type: IntentType, user_input: str
    ) -> list[str]:
        """生成优化建议"""
        suggestions = []

        # 基于意图的建议
        if intent_type == IntentType.OPINION_RESPONSE:
            suggestions.append("建议先使用专业工作流,确保答复的专业性")
            suggestions.append("可以结合法律知识图谱,提高答复质量")

        elif intent_type == IntentType.PATENT_SEARCH:
            suggestions.append("使用多数据库并行检索,提高覆盖面")
            suggestions.append("建议使用语义搜索,发现隐含相关的专利")

        # 基于输入长度的建议
        if len(user_input) < 20:
            suggestions.append("建议提供更详细的描述,以便更准确地识别需求")

        # 基于历史的建议
        if intent_type in self.routing_stats["intent_distribution"]:
            usage_count = self.routing_stats["intent_distribution"][intent_type]
            if usage_count > 100:
                suggestions.append(f"这是您第{usage_count}次处理此类请求,可以考虑使用预设模板")

        return suggestions

    def _generate_fallback_options(self, intent_type: IntentType) -> list[str]:
        """生成备选方案"""
        fallback_mapping = {
            IntentType.PATENT_SEARCH: ["使用通用搜索引擎进行专利检索", "咨询专业专利检索机构"],
            IntentType.OPINION_RESPONSE: ["使用通用AI助手分析", "咨询专利代理机构"],
            IntentType.CREATIVE_WRITING: ["使用基础小诺代理", "使用其他创意写作工具"],
        }

        return fallback_mapping.get(intent_type, ["使用Athena通用代理"])

    def _update_routing_stats(
        self, intent_type: IntentType, result: RoutingResult, response_time: float
    ):
        """更新路由统计"""
        self.routing_stats["successful_routes"] += 1

        # 更新平均响应时间
        current_avg = self.routing_stats["average_response_time"]
        total_routes = self.routing_stats["successful_routes"]
        new_avg = (current_avg * (total_routes - 1) + response_time) / total_routes
        self.routing_stats["average_response_time"] = new_avg

        # 更新工具使用统计
        all_tools = result.primary_tools + result.supporting_tools
        for tool in all_tools:
            if tool.tool_name not in self.routing_stats["tool_usage_stats"]:
                self.routing_stats["tool_usage_stats"][tool.tool_name] = 0
            self.routing_stats["tool_usage_stats"][tool.tool_name] += 1

    def _create_fallback_result(self, user_input: str) -> RoutingResult:
        """创建回退结果"""
        fallback_tool = ToolRecommendation(
            tool_name="athena_agent.py",
            priority=ToolPriority.CRITICAL,
            confidence=0.6,
            reason="路由系统降级,使用默认代理",
            estimated_time=30.0,
        )

        return RoutingResult(
            intent_type=IntentType.GENERAL_CONVERSATION,
            confidence=0.5,
            primary_tools=[fallback_tool],
            supporting_tools=[],
            workflow="通用处理流程",
            estimated_total_time=30.0,
            optimization_suggestions=["建议提供更详细的需求描述"],
            fallback_options=["使用小诺代理", "手动选择工具"],
        )

    def get_routing_stats(self) -> dict[str, Any]:
        """获取路由统计信息"""
        return {
            "routing_stats": {
                "total_requests": self.routing_stats["total_requests"],
                "successful_routes": self.routing_stats["successful_routes"],
                "intent_distribution": {
                    k.value: v for k, v in self.routing_stats["intent_distribution"].items()
                },
                "tool_usage_stats": self.routing_stats["tool_usage_stats"],
                "average_response_time": self.routing_stats["average_response_time"],
            },
            "tool_database_size": len(self.tool_database),
            "supported_intents": len(self.intent_keywords),
            "last_updated": datetime.now().isoformat(),
        }


# 使用示例
async def test_intelligent_router():
    """测试智能路由系统"""
    logger.info("🧠 测试智能工具路由系统")

    router = IntelligentToolRouter()

    # 测试用例
    test_inputs = [
        "我需要回复专利202311334091.8的审查意见",
        "帮我检索机器学习相关的专利",
        "帮我写一个关于星空的短故事",
        "检查一下系统健康状态",
        "评估这个技术方案的可行性",
    ]

    for i, test_input in enumerate(test_inputs, 1):
        logger.info(f"\n📝 测试 {i}: {test_input}")
        logger.info(str("-" * 50))

        result = await router.route_request(test_input)

        logger.info(f"🎯 识别意图: {result.intent_type.value}")
        logger.info(f"📊 置信度: {result.confidence:.2f}")
        logger.info(f"⏱️  预估时间: {result.estimated_total_time:.1f}分钟")
        logger.info(f"🔄 工作流: {result.workflow}")

        logger.info("\n🔧 推荐工具:")
        for tool in result.primary_tools:
            logger.info(
                f"  ✅ {tool.tool_name} ({tool.priority.value}, 置信度: {tool.confidence:.2f})"
            )

        if result.supporting_tools:
            logger.info("\n🔧 辅助工具:")
            for tool in result.supporting_tools:
                logger.info(
                    f"  ⚙️  {tool.tool_name} ({tool.priority.value}, 置信度: {tool.confidence:.2f})"
                )

        if result.optimization_suggestions:
            logger.info("\n💡 优化建议:")
            for suggestion in result.optimization_suggestions:
                logger.info(f"  • {suggestion}")

    # 显示统计信息
    logger.info("\n📊 路由统计:")
    stats = router.get_routing_stats()
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(test_intelligent_router())
