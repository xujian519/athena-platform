#!/usr/bin/env python3
"""
纯对话交互接口
Pure Dialogue Interface for Patent Judgment Vector Database

功能:
- 纯对话式交互
- 智能意图识别
- 任务编排协调
- 主动建议系统
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class DialogueIntent(Enum):
    """对话意图枚举"""

    QUERY = "query"  # 查询
    ANALYZE = "analyze"  # 分析
    GENERATE = "generate"  # 生成文章
    COMPARE = "compare"  # 对比
    SUMMARIZE = "summarize"  # 汇总
    CLARIFY = "clarify"  # 澄清需求
    GREETING = "greeting"  # 问候


@dataclass
class DialogueContext:
    """对话上下文"""

    session_id: str  # 会话ID
    user_id: str  # 用户ID
    history: list[dict[str, str]]  # 历史对话
    current_topic: str | None = None  # 当前主题
    pending_tasks: list[str] | None = None  # 待处理任务
    preferences: dict[str, Any] | None = None  # 用户偏好


@dataclass
class DialogueResponse:
    """对话响应"""

    response_text: str  # 响应文本
    intent: DialogueIntent  # 识别的意图
    suggestions: list[str]  # 建议列表
    actions: list[dict[str, Any]]  # 执行的动作
    metadata: dict[str, Any]  # 元数据
    needs_clarification: bool  # 是否需要澄清


class PureDialogueInterface:
    """纯对话交互接口"""

    def __init__(
        self,
        query_classifier,
        hybrid_retriever,
        viewpoint_analyzer,
        article_generator,
        config: dict[str, Any] | None = None,
    ):
        """
        初始化对话接口

        Args:
            query_classifier: 查询分类器
            hybrid_retriever: 混合检索引擎
            viewpoint_analyzer: 观点分析器
            article_generator: 文章生成器
            config: 配置字典
        """
        self.classifier = query_classifier
        self.retriever = hybrid_retriever
        self.analyzer = viewpoint_analyzer
        self.generator = article_generator
        self.config = config or {}

        # 对话历史
        self.contexts = {}  # session_id -> DialogueContext

        # 主动建议配置
        self.enable_proactive_suggestions = self.config.get("enable_proactive_suggestions", True)

    def process_user_input(
        self, user_input: str, session_id: str = "default", user_id: str = "default_user"
    ) -> DialogueResponse:
        """
        处理用户输入

        Args:
            user_input: 用户输入文本
            session_id: 会话ID
            user_id: 用户ID

        Returns:
            DialogueResponse对象
        """
        logger.info(f"📝 用户输入: {user_input}")

        # 1. 获取或创建上下文
        context = self._get_or_create_context(session_id, user_id)

        # 2. 添加到历史
        context.history.append(
            {"role": "user", "content": user_input, "timestamp": self._get_timestamp()}
        )

        # 3. 识别意图
        intent = self._recognize_intent(user_input, context)

        # 4. 根据意图处理
        if intent == DialogueIntent.QUERY:
            response = self._handle_query(user_input, context)
        elif intent == DialogueIntent.ANALYZE:
            response = self._handle_analyze(user_input, context)
        elif intent == DialogueIntent.GENERATE:
            response = self._handle_generate(user_input, context)
        elif intent == DialogueIntent.COMPARE:
            response = self._handle_compare(user_input, context)
        elif intent == DialogueIntent.SUMMARIZE:
            response = self._handle_summarize(user_input, context)
        elif intent == DialogueIntent.GREETING:
            response = self._handle_greeting(user_input, context)
        else:
            response = self._handle_clarify(user_input, context)

        # 5. 添加响应到历史
        context.history.append(
            {
                "role": "assistant",
                "content": response.response_text,
                "timestamp": self._get_timestamp(),
            }
        )

        # 6. 生成主动建议
        if self.enable_proactive_suggestions:
            proactive_suggestions = self._generate_proactive_suggestions(
                user_input, context, response
            )
            response.suggestions.extend(proactive_suggestions)

        logger.info(f"✅ 响应生成: intent={intent.value}")
        return response

    def _get_or_create_context(self, session_id: str, user_id: str) -> DialogueContext:
        """获取或创建对话上下文"""
        if session_id not in self.contexts:
            self.contexts[session_id] = DialogueContext(
                session_id=session_id, user_id=user_id, history=[], pending_tasks=[], preferences={}
            )

        return self.contexts[session_id]

    def _recognize_intent(self, user_input: str, context: DialogueContext) -> DialogueIntent:
        """识别用户意图"""
        input_lower = user_input.lower()

        # 问候
        greeting_patterns = ["你好", "hello", "hi", "您好"]
        if any(p in input_lower for p in greeting_patterns):
            return DialogueIntent.GREETING

        # 分析意图
        analyze_patterns = ["分析", "研究", "探讨", "evaluate", "analyze"]
        if any(p in input_lower for p in analyze_patterns):
            return DialogueIntent.ANALYZE

        # 生成意图
        generate_patterns = ["生成", "撰写", "写", "generate", "write"]
        if any(p in input_lower for p in generate_patterns):
            return DialogueIntent.GENERATE

        # 对比意图
        compare_patterns = ["对比", "比较", "差异", "compare", "difference"]
        if any(p in input_lower for p in compare_patterns):
            return DialogueIntent.COMPARE

        # 汇总意图
        summarize_patterns = ["汇总", "总结", "整体", "summarize", "summary"]
        if any(p in input_lower for p in summarize_patterns):
            return DialogueIntent.SUMMARIZE

        # 默认为查询
        return DialogueIntent.QUERY

    def _handle_query(self, user_input: str, context: DialogueContext) -> DialogueResponse:
        """处理查询意图"""
        # 1. 查询分类
        analysis = self.classifier.classify(user_input)

        # 2. 执行检索
        from core.judgment_vector_db.retrieval.hybrid_retriever import RetrievalStrategy

        strategy = self._map_to_strategy(analysis.suggested_strategy)
        result = self.retriever.retrieve(
            query=user_input, strategy=strategy, layer=analysis.granularity.value, limit=10
        )

        # 3. 格式化响应
        response_text = self._format_query_results(user_input, result, analysis)

        # 4. 生成建议
        suggestions = self._generate_query_suggestions(user_input, result)

        return DialogueResponse(
            response_text=response_text,
            intent=DialogueIntent.QUERY,
            suggestions=suggestions,
            actions=[],
            metadata={"retrieval_result": result},
            needs_clarification=False,
        )

    def _handle_analyze(self, user_input: str, context: DialogueContext) -> DialogueResponse:
        """处理分析意图"""
        # 1. 生成分析报告
        report = self.analyzer.generate_analysis_report(
            query=user_input, analysis_types=["viewpoints", "rules", "trends"]
        )

        # 2. 格式化响应
        response_text = self._format_analysis_report(user_input, report)

        # 3. 生成建议
        suggestions = ["生成完整的分析文章", "查看具体案例详情", "对比不同时期观点", "导出分析数据"]

        return DialogueResponse(
            response_text=response_text,
            intent=DialogueIntent.ANALYZE,
            suggestions=suggestions,
            actions=[],
            metadata={"analysis_report": report},
            needs_clarification=False,
        )

    def _handle_generate(self, user_input: str, context: DialogueContext) -> DialogueResponse:
        """处理生成意图"""
        # 1. 识别文章类型
        article_type = self._infer_article_type(user_input)

        # 2. 提取主题
        topic = self._extract_topic_from_input(user_input)

        # 3. 生成文章
        article = self.generator.generate_article(topic=topic, article_type=article_type)

        # 4. 格式化响应
        response_text = self._format_generated_article(article)

        # 5. 生成建议
        suggestions = [
            "导出为Markdown格式",
            "导出为Word文档",
            "生成PPT演示文稿",
            "查看质量检查报告",
        ]

        return DialogueResponse(
            response_text=response_text,
            intent=DialogueIntent.GENERATE,
            suggestions=suggestions,
            actions=[],
            metadata={"article": article},
            needs_clarification=False,
        )

    def _handle_compare(self, user_input: str, context: DialogueContext) -> DialogueResponse:
        """处理对比意图"""
        response_text = f"""正在为您进行对比分析:{user_input}

对比功能正在开发中,将支持:
- 不同法院的裁判观点对比
- 不同时期的观点演变对比
- 不同法条的适用对比
- 不同技术领域的处理方式对比

请稍候..."""

        return DialogueResponse(
            response_text=response_text,
            intent=DialogueIntent.COMPARE,
            suggestions=["查看对比结果", "导出对比表格"],
            actions=[],
            metadata={},
            needs_clarification=False,
        )

    def _handle_summarize(self, user_input: str, context: DialogueContext) -> DialogueResponse:
        """处理汇总意图"""
        # 1. 生成汇总报告
        report = self.analyzer.generate_analysis_report(
            query=user_input, analysis_types=["viewpoints"]
        )

        # 2. 格式化响应
        response_text = self._format_summary_report(user_input, report)

        # 3. 生成建议
        suggestions = ["生成详细分析文章", "查看具体观点分布", "导出汇总数据"]

        return DialogueResponse(
            response_text=response_text,
            intent=DialogueIntent.SUMMARIZE,
            suggestions=suggestions,
            actions=[],
            metadata={"summary_report": report},
            needs_clarification=False,
        )

    def _handle_greeting(self, user_input: str, context: DialogueContext) -> DialogueResponse:
        """处理问候意图"""
        response_text = """您好!我是专利判决智能分析助手,可以帮您:

📚 **智能检索**
- 基于法条、争议焦点、论证逻辑的多粒度检索
- 向量搜索+知识图谱+全文检索的混合模式

📊 **深度分析**
- 观点聚合分析
- 裁判规则提取
- 时间演变趋势

📝 **文章生成**
- 研究综述
- 案例分析
- 规则解读

💡 **纯对话交互**
- 自然语言提问
- 智能意图识别
- 主动建议

请问您想了解什么?"""

        suggestions = [
            "检索专利法第22条第3款的相关案例",
            "分析关于等同侵权的裁判观点",
            "生成创造性的研究综述",
            "查看近几年的裁判趋势",
        ]

        return DialogueResponse(
            response_text=response_text,
            intent=DialogueIntent.GREETING,
            suggestions=suggestions,
            actions=[],
            metadata={},
            needs_clarification=False,
        )

    def _handle_clarify(self, user_input: str, context: DialogueContext) -> DialogueResponse:
        """处理需要澄清的情况"""
        response_text = f"""我理解您想了解:{user_input}

为了更好地帮助您,请告诉我:
1. 您是要检索案例、分析观点,还是生成文章?
2. 您关注的具体法律问题是什么?
3. 您需要的结果形式是什么?"""

        suggestions = ["我要检索相关案例", "我要分析裁判观点", "我要生成分析文章"]

        return DialogueResponse(
            response_text=response_text,
            intent=DialogueIntent.CLARIFY,
            suggestions=suggestions,
            actions=[],
            metadata={},
            needs_clarification=True,
        )

    def _map_to_strategy(self, suggested_strategy: str) -> "RetrievalStrategy":
        """映射建议策略到实际策略"""
        from core.judgment_vector_db.retrieval.hybrid_retriever import RetrievalStrategy

        strategy_map = {
            "hybrid_standard": RetrievalStrategy.HYBRID_STANDARD,
            "hybrid_deep": RetrievalStrategy.HYBRID_DEEP,
            "vector_primary": RetrievalStrategy.VECTOR_ONLY,
            "fulltext_primary": RetrievalStrategy.FULLTEXT_PRIMARY,
            "knowledge_graph_first": RetrievalStrategy.GRAPH_FIRST,
        }

        return strategy_map.get(suggested_strategy, RetrievalStrategy.HYBRID_STANDARD)

    def _format_query_results(self, query: str, result, analysis) -> str:
        """格式化查询结果"""
        lines = [
            f"## 查询结果:{query}\n",
            f"**查询类型**: {analysis.query_type.value}",
            f"**查询粒度**: {analysis.granularity.value}",
            f"**检索策略**: {result.strategy_used}",
            f"**找到结果**: {len(result.results)}条\n",
            "---\n",
        ]

        # 显示前5个结果
        for i, r in enumerate(result.results[:5], 1):
            lines.append(f"### {i}. {r.id}")
            lines.append(f"**来源**: {r.source}")
            lines.append(f"**相关度**: {r.score:.2f}")
            lines.append(f"**内容**: {r.content[:200]}...")
            lines.append("")

        if len(result.results) > 5:
            lines.append(f"\n还有 {len(result.results) - 5} 条结果...")

        return "\n".join(lines)

    def _format_analysis_report(self, query: str, report: dict[str, Any]) -> str:
        """格式化分析报告"""
        lines = [
            f"## 分析报告:{query}\n",
            f"**生成时间**: {report['generated_at']}",
            f"**摘要**: {report.get('summary', '')}\n",
            "---\n",
        ]

        sections = report.get("sections", {})

        # 观点聚合
        if "viewpoint_aggregation" in sections:
            vp = sections["viewpoint_aggregation"]
            lines.append(f"### 观点聚类 ({vp['total_clusters']}个)")
            for cluster in vp["clusters"][:3]:
                lines.append(f"- **{cluster['topic']}** ({cluster['case_count']}个案例)")
                lines.append(f"  {cluster['summary']}")
            lines.append("")

        # 裁判规则
        if "judgment_rules" in sections:
            jr = sections["judgment_rules"]
            lines.append(f"### 裁判规则 ({jr['total_rules']}条)")
            for rule in jr["rules"][:3]:
                lines.append(f"- **{rule['name']}** (适用率: {rule['applicability']:.2f})")
                lines.append(f"  {rule['description']}")
            lines.append("")

        # 时间趋势
        if "temporal_evolution" in sections:
            te = sections["temporal_evolution"]
            lines.append(f"### 时间趋势 ({te['total_trends']}个)")
            for trend in te["trends"][:3]:
                lines.append(f"- **{trend['topic']}** ({trend['direction']})")

        return "\n".join(lines)

    def _format_generated_article(self, article) -> str:
        """格式化生成的文章"""
        lines = [
            f"# {article.title}\n",
            f"**质量等级**: {article.quality_level.value}",
            f"**质量分数**: {article.quality_score:.2f}\n",
            "---\n",
        ]

        for section in article.sections:
            lines.append(f"## {section.title}\n")
            lines.append(f"{section.content}\n")

        return "\n".join(lines)

    def _format_summary_report(self, query: str, report: dict[str, Any]) -> str:
        """格式化汇总报告"""
        lines = [f"## 汇总报告:{query}\n", "---\n"]

        sections = report.get("sections", {})

        if "viewpoint_aggregation" in sections:
            vp = sections["viewpoint_aggregation"]
            lines.append(f"### 识别出 {vp['total_clusters']} 个主要观点聚类:\n")

            for cluster in vp["clusters"]:
                lines.append(f"**{cluster['topic']}**")
                lines.append(f"- 涉及案例: {cluster['case_count']}份")
                lines.append(f"- 观点摘要: {cluster['summary']}")
                lines.append("")

        return "\n".join(lines)

    def _generate_query_suggestions(self, query: str, result) -> list[str]:
        """生成查询建议"""
        suggestions = ["查看更多相关案例", "分析这些案例的裁判观点", "生成分析文章"]

        return suggestions

    def _generate_proactive_suggestions(
        self, user_input: str, context: DialogueContext, response: DialogueResponse
    ) -> list[str]:
        """生成主动建议"""
        suggestions = []

        # 基于历史对话的建议
        if len(context.history) > 3:
            suggestions.append("查看完整对话历史")

        # 基于响应内容的建议
        if response.intent == DialogueIntent.QUERY:
            suggestions.append("深度分析检索结果")
            suggestions.append("生成分析文章")

        # 基于用户偏好的建议
        if context.preferences.get("prefer_detail"):
            suggestions.append("查看详细分析")

        return suggestions

    def _infer_article_type(self, user_input: str) -> "ArticleType":
        """推断文章类型"""
        from core.judgment_vector_db.generation.article_generator import ArticleType

        input_lower = user_input.lower()

        if "综述" in user_input or "overview" in input_lower:
            return ArticleType.REVIEW
        elif "案例" in user_input or "case" in input_lower:
            return ArticleType.CASE_ANALYSIS
        elif "规则" in user_input or "rule" in input_lower:
            return ArticleType.RULE_INTERPRETATION
        elif "对比" in user_input or "compare" in input_lower:
            return ArticleType.COMPARATIVE_STUDY
        elif "趋势" in user_input or "trend" in input_lower:
            return ArticleType.TREND_REPORT
        else:
            return ArticleType.REVIEW

    def _extract_topic_from_input(self, user_input: str) -> str:
        """从输入中提取主题"""
        # 简化:移除常见动词
        patterns = [
            r"生成.*关于(.+)",
            r"撰写.*(.+)",
            r"写.*(.+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, user_input)
            if match:
                return match.group(1).strip()

        return user_input

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime

        return datetime.now().isoformat()

    def export_conversation(self, session_id: str, format: str = "markdown") -> str:
        """导出对话历史"""
        if session_id not in self.contexts:
            return ""

        context = self.contexts[session_id]

        if format == "markdown":
            lines = ["# 对话历史\n"]
            lines.append(f"**会话ID**: {session_id}\n")
            lines.append(f"**用户ID**: {context.user_id}\n")
            lines.append(f"**对话轮数**: {len(context.history) // 2}\n")
            lines.append("---\n")

            for msg in context.history:
                role = "用户" if msg["role"] == "user" else "助手"
                lines.append(f"### {role} ({msg['timestamp']})")
                lines.append(msg["content"])
                lines.append("")

            return "\n".join(lines)

        return ""


# 便捷函数
def create_dialogue_interface(
    query_classifier,
    hybrid_retriever,
    viewpoint_analyzer,
    article_generator,
    config: dict[str, Any] | None = None,
) -> PureDialogueInterface:
    """
    创建对话接口

    Args:
        query_classifier: 查询分类器
        hybrid_retriever: 混合检索引擎
        viewpoint_analyzer: 观点分析器
        article_generator: 文章生成器
        config: 配置字典

    Returns:
        PureDialogueInterface实例
    """
    return PureDialogueInterface(
        query_classifier=query_classifier,
        hybrid_retriever=hybrid_retriever,
        viewpoint_analyzer=viewpoint_analyzer,
        article_generator=article_generator,
        config=config,
    )
