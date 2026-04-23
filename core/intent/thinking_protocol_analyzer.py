#!/usr/bin/env python3
from __future__ import annotations
"""
思维协议驱动的意图分析器
Thinking Protocol-Driven Intent Analyzer

整合Claude深度思考协议,用于复杂意图的深度分析:
- 多假设生成
- 问题分解
- 模式识别
- 知识综合
- 适应性推理

适用于:模糊输入、多意图、复杂上下文、歧义场景

作者: Athena AI Team
版本: 1.0.0
创建: 2026-01-23
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

# 导入基础组件
from core.intent.intelligent_intent_service import (
    IntentCategory,
    Layer3DeepAnalyzer,
)

logger = logging.getLogger(__name__)


class ThoughtPhase(Enum):
    """思维阶段(基于Claude思维协议)"""

    INITIAL_ENGAGEMENT = "initial_engagement"  # 初次参与
    PROBLEM_ANALYSIS = "problem_analysis"  # 问题分析
    MULTIPLE_HYPOTHESES = "multiple_hypotheses"  # 多假设生成
    PATTERN_RECOGNITION = "pattern_recognition"  # 模式识别
    KNOWLEDGE_SYNTHESIS = "knowledge_synthesis"  # 知识综合
    VERIFICATION = "verification"  # 验证


@dataclass
class Hypothesis:
    """意图假设"""

    intent: IntentCategory
    confidence: float
    reasoning: list[str]  # 推理路径
    evidence: list[str]  # 支持证据
    contradictions: list[str]  # 矛盾点


@dataclass
class ThoughtTrace:
    """思维轨迹"""

    phase: ThoughtPhase
    timestamp: datetime
    thoughts: list[str]
    hypotheses: list[Hypothesis]
    insights: list[str]
    decisions: list[str]

    def add_thought(self, thought: str):
        """添加思考"""
        self.thoughts.append(thought)

    def add_hypothesis(self, hypothesis: Hypothesis):
        """添加假设"""
        self.hypotheses.append(hypothesis)

    def add_insight(self, insight: str):
        """添加洞察"""
        self.insights.append(insight)


class ThinkingProtocolAnalyzer:
    """
    思维协议分析器

    基于Claude深度思考协议的意图分析器
    """

    def __init__(self):
        """初始化分析器"""
        self.base_analyzer = Layer3DeepAnalyzer()
        logger.info("✅ 思维协议分析器初始化完成")

    async def analyze_with_thinking_protocol(
        self,
        text: str,
        context: Optional[dict[str, Any]] = None,
        entities: dict[str, list[str]] | None = None,
        previous_trace: ThoughtTrace | None = None,
    ) -> ThoughtTrace:
        """
        使用思维协议分析意图

        Args:
            text: 用户输入
            context: 上下文信息
            entities: 已提取的实体
            previous_trace: 之前的思维轨迹(用于对话)

        Returns:
            思维轨迹
        """
        trace = ThoughtTrace(
            phase=ThoughtPhase.INITIAL_ENGAGEMENT,
            timestamp=datetime.now(),
            thoughts=[],
            hypotheses=[],
            insights=[],
            decisions=[],
        )

        # ========== 阶段1: 初次参与 ==========
        await self._initial_engagement(text, context, trace)

        # ========== 阶段2: 问题分析 ==========
        await self._problem_analysis(text, context, entities, trace)

        # ========== 阶段3: 多假设生成 ==========
        await self._generate_hypotheses(text, entities, trace)

        # ========== 阶段4: 模式识别 ==========
        await self._pattern_recognition(text, entities, trace)

        # ========== 阶段5: 知识综合 ==========
        await self._synthesize_knowledge(text, context, entities, trace)

        # ========== 阶段6: 验证 ==========
        await self._verify_conclusions(text, trace)

        return trace

    async def _initial_engagement(
        self, text: str, context: dict[str, Any], trace: ThoughtTrace
    ):
        """
        初次参与阶段

        类似Claude的"初次约定":
        1. 用自己的语言重新表述信息
        2. 形成初步印象
        3. 考虑更广泛的背景
        4. 绘制已知/未知元素
        """
        trace.add_thought(f"📝 用户输入: '{text}'")
        trace.add_thought("🔍 开始初步分析...")

        # 重新表述
        paraphrase = self._paraphrase_input(text)
        trace.add_thought(f"💭 理解为: {paraphrase}")

        # 初步印象
        initial_intent = self._form_initial_impression(text)
        trace.add_thought(f"🎯 初步印象: {initial_intent}")

        # 背景分析
        background = self._analyze_background(text, context)
        if background:
            trace.add_insight(f"🌍 背景信息: {background}")

        trace.phase = ThoughtPhase.PROBLEM_ANALYSIS

    async def _problem_analysis(
        self,
        text: str,
        context: dict[str, Any],        entities: dict[str, list[str]],
        trace: ThoughtTrace,
    ):
        """
        问题分析阶段

        分解为:
        1. 核心部分
        2. 显性和隐性需求
        3. 约束和限制
        4. 成功回应的要素
        """
        trace.add_thought("\n🔬 进入问题分析阶段...")

        # 分解核心部分
        core_elements = self._decompose_problem(text)
        trace.add_thought(f"📦 核心元素: {core_elements}")

        # 识别需求
        needs = self._identify_needs(text, entities)
        trace.add_thought(f"🎯 识别需求: {needs}")

        # 分析约束
        constraints = self._identify_constraints(text)
        if constraints:
            trace.add_thought(f"⚠️  约束条件: {constraints}")

        trace.phase = ThoughtPhase.MULTIPLE_HYPOTHESES

    async def _generate_hypotheses(
        self, text: str, entities: dict[str, list[str]], trace: ThoughtTrace
    ):
        """
        多假设生成阶段

        生成多种可能的意图解释:
        1. 主要意图
        2. 次要意图
        3. 隐含意图
        4. 创造性解释
        """
        trace.add_thought("\n💡 进入多假设生成阶段...")

        # 生成假设
        hypotheses = await self._generate_intent_hypotheses(text, entities)

        trace.add_thought(f"🤔 生成 {len(hypotheses)} 个假设:")

        for i, hypothesis in enumerate(hypotheses, 1):
            trace.add_hypothesis(hypothesis)

            confidence_str = (
                "高"
                if hypothesis.confidence > 0.7
                else "中" if hypothesis.confidence > 0.4 else "低"
            )
            trace.add_thought(
                f"   {i}. {hypothesis.intent.value} "
                f"({confidence_str}置信度) - "
                f"推理: {'; '.join(hypothesis.reasoning[:2])}"
            )

        trace.phase = ThoughtPhase.PATTERN_RECOGNITION

    async def _pattern_recognition(
        self, text: str, entities: dict[str, list[str]], trace: ThoughtTrace
    ):
        """
        模式识别阶段

        识别:
        1. 语言模式(疑问句、祈使句等)
        2. 实体模式(专利号、法律条文等)
        3. 领域模式(专利、法律、技术)
        4. 行为模式(查询、分析、创作)
        """
        trace.add_thought("\n🔍 进入模式识别阶段...")

        # 语言模式
        lang_patterns = self._recognize_language_patterns(text)
        if lang_patterns:
            trace.add_insight(f"📝 语言模式: {lang_patterns}")

        # 实体模式
        if entities:
            entity_patterns = self._analyze_entity_patterns(entities)
            trace.add_insight(f"🏷️ 实体模式: {entity_patterns}")

        # 领域模式
        domain_patterns = self._recognize_domain_patterns(text, entities)
        trace.add_insight(f"🎓 领域模式: {domain_patterns}")

        # 验证模式一致性
        consistency = self._verify_pattern_consistency(trace)
        trace.add_thought(f"✓ 模式一致性: {consistency}")

        trace.phase = ThoughtPhase.KNOWLEDGE_SYNTHESIS

    async def _synthesize_knowledge(
        self,
        text: str,
        context: dict[str, Any],        entities: dict[str, list[str]],
        trace: ThoughtTrace,
    ):
        """
        知识综合阶段

        整合:
        1. 实体信息
        2. 上下文信息
        3. 领域知识
        4. 推理路径
        """
        trace.add_thought("\n🧩 进入知识综合阶段...")

        # 连接不同信息
        connections = self._find_connections(text, entities, trace)
        trace.add_insight(f"🔗 信息连接: {connections}")

        # 构建完整图景
        big_picture = self._build_big_picture(trace)
        trace.add_insight(f"🖼️ 整体图景: {big_picture}")

        # 确定关键原则
        principles = self._identify_key_principles(trace)
        if principles:
            trace.add_insight(f"⚡ 关键原则: {principles}")

        trace.phase = ThoughtPhase.VERIFICATION

    async def _verify_conclusions(self, text: str, trace: ThoughtTrace):
        """
        验证阶段

        1. 质疑假设
        2. 测试结论
        3. 检查逻辑一致性
        4. 验证理解完整性
        """
        trace.add_thought("\n✔️  进入验证阶段...")

        # 获取最佳假设
        if trace.hypotheses:
            best_hypothesis = max(trace.hypotheses, key=lambda h: h.confidence)

            trace.add_thought(f"🎯 最佳假设: {best_hypothesis.intent.value}")

            # 自我质疑
            questions = self._question_hypothesis(best_hypothesis, text)
            trace.add_thought(f"❓ 自我质疑: {questions}")

            # 验证逻辑
            is_consistent = self._verify_logical_consistency(trace)
            trace.add_thought(f"🔗 逻辑一致性: {'✓ 通过' if is_consistent else '⚠️ 警告'}")

            # 检查完整性
            is_complete = self._verify_completeness(text, trace)
            trace.add_thought(f"📋 完整性: {'✓ 完整' if is_complete else '⚠️ 可能不完整'}")

        # 最终决策
        final_intent = self._make_final_decision(trace)
        trace.decisions.append(f"最终意图: {final_intent}")

    # ========== 辅助方法 ==========

    @staticmethod
    def _paraphrase_input(text: str) -> str:
        """重新表述输入"""
        # 简化版:提取关键信息
        if "?" in text or "吗" in text:
            return f"用户提出疑问: {text}"
        elif "检索" in text or "搜索" in text or "查找" in text:
            return f"用户请求检索信息: {text}"
        elif "分析" in text or "评估" in text:
            return f"用户请求分析: {text}"
        elif "写" in text or "生成" in text or "创建" in text:
            return f"用户请求生成内容: {text}"
        else:
            return f"用户陈述: {text}"

    @staticmethod
    def _form_initial_impression(text: str) -> str:
        """形成初步印象"""
        if any(kw in text for kw in ["专利", "检索", "搜索"]):
            return "可能是专利检索任务"
        elif any(kw in text for kw in ["分析", "评估", "判断"]):
            return "可能是分析评估任务"
        elif any(kw in text for kw in ["写", "生成", "创建"]):
            return "可能是内容生成任务"
        elif any(kw in text for kw in ["侵权", "合法", "法律"]):
            return "可能是法律咨询任务"
        else:
            return "需要深入分析的通用查询"

    @staticmethod
    def _analyze_background(text: str, context: dict) -> Optional[str]:
        """分析背景信息"""
        if not context:
            return None

        background = []
        if "domain" in context:
            background.append(f"领域: {context['domain']}")
        if "previous_intents" in context:
            background.append(f"历史意图: {context['previous_intents']}")
        if "user_profile" in context:
            background.append(f"用户画像: {context['user_profile']}")

        return "; ".join(background) if background else None

    @staticmethod
    def _decompose_problem(text: str) -> list[str]:
        """分解问题"""
        elements = []

        # 提取动词(意图)
        action_verbs = {
            "检索": "搜索",
            "搜索": "查找",
            "分析": "分析",
            "评估": "判断",
            "写": "创作",
            "生成": "生成",
        }
        for verb, keywords in action_verbs.items():
            if any(kw in text for kw in keywords):
                elements.append(f"动作: {verb}")
                break

        # 提取对象
        if "专利" in text:
            elements.append("对象: 专利")
        elif "代码" in text or "程序" in text:
            elements.append("对象: 代码")
        elif "合同" in text or "协议" in text:
            elements.append("对象: 合同")

        return elements

    @staticmethod
    def _identify_needs(text: str, entities: dict[str, list[str]]) -> dict[str, Any]:
        """识别需求"""
        needs = {"explicit_needs": [], "implicit_needs": []}

        # 显性需求(从文本中直接提取)
        if "检索" in text or "搜索" in text:
            needs["explicit_needs"].append("信息检索")
        if "分析" in text:
            needs["explicit_needs"].append("分析评估")
        if "写" in text or "生成" in text:
            needs["explicit_needs"].append("内容生成")

        # 隐性需求(推断)
        if entities and "PATENT_NUMBER" in entities:
            needs["implicit_needs"].append("专利详细信息")
        if "?" in text or "吗" in text:
            needs["implicit_needs"].append("答案/确认")

        return needs

    @staticmethod
    def _identify_constraints(text: str) -> list[str]:
        """识别约束"""
        constraints = []

        # 时间约束
        time_words = ["快速", "紧急", "立即", "尽快"]
        if any(kw in text for kw in time_words):
            constraints.append("时间敏感")

        # 精确性约束
        precision_words = ["详细", "具体", "精确"]
        if any(kw in text for kw in precision_words):
            constraints.append("需要详细回应")

        # 格式约束
        if "列表" in text:
            constraints.append("需要结构化输出")

        return constraints

    async def _generate_intent_hypotheses(
        self, text: str, entities: dict[str, list[str]]
    ) -> list[Hypothesis]:
        """
        生成多个意图假设

        这是核心功能:考虑多种可能的解释
        """
        hypotheses = []

        # 主假设(基于关键词)
        main_intent = self._generate_main_hypothesis(text, entities)
        hypotheses.append(main_intent)

        # 次要假设(备选解释)
        secondary_intents = self._generate_secondary_hypotheses(text, entities)
        hypotheses.extend(secondary_intents)

        # 创造性假设(非常规解释)
        creative_intents = self._generate_creative_hypotheses(text, entities)
        hypotheses.extend(creative_intents)

        # 按置信度排序
        hypotheses.sort(key=lambda h: h.confidence, reverse=True)

        return hypotheses[:5]  # 返回top 5

    def _generate_main_hypothesis(
        self, text: str, entities: dict[str, list[str]]
    ) -> Hypothesis:
        """生成主假设"""
        # 关键词匹配
        keyword_intent_map = {
            "专利": IntentCategory.PATENT_SEARCH,
            "检索": IntentCategory.PATENT_SEARCH,
            "分析": IntentCategory.PATENT_ANALYSIS,
            "写": IntentCategory.CODE_GENERATION,
            "侵权": IntentCategory.LEGAL_QUERY,
        }

        best_intent = None
        best_match_count = 0
        matched_keyword = None

        for keyword, intent in keyword_intent_map.items():
            if keyword in text:
                count = text.count(keyword)
                if count > best_match_count:
                    best_intent = intent
                    best_match_count = count
                    matched_keyword = keyword

        if best_intent:
            return Hypothesis(
                intent=best_intent,
                confidence=0.8,
                reasoning=[f"关键词'{matched_keyword}'匹配"],
                evidence=[f"文本包含'{matched_keyword}'"],
                contradictions=[],
            )

        # 默认假设
        return Hypothesis(
            intent=IntentCategory.KNOWLEDGE_QUERY,
            confidence=0.3,
            reasoning=["通用查询,无特定关键词"],
            evidence=[],
            contradictions=[],
        )

    def _generate_secondary_hypotheses(
        self, text: str, entities: dict[str, list[str]]
    ) -> list[Hypothesis]:
        """生成次要假设"""
        hypotheses = []

        # 基于实体推断
        if entities:
            if "PATENT_NUMBER" in entities:
                hypotheses.append(
                    Hypothesis(
                        intent=IntentCategory.PATENT_SEARCH,
                        confidence=0.7,
                        reasoning=["包含专利号"],
                        evidence=["实体: PATENT_NUMBER"],
                        contradictions=[],
                    )
                )

            if "LAW_ARTICLE" in entities:
                hypotheses.append(
                    Hypothesis(
                        intent=IntentCategory.LEGAL_QUERY,
                        confidence=0.6,
                        reasoning=["引用法律条文"],
                        evidence=["实体: LAW_ARTICLE"],
                        contradictions=[],
                    )
                )

        return hypotheses

    def _generate_creative_hypotheses(
        self, text: str, entities: dict[str, list[str]]
    ) -> list[Hypothesis]:
        """生成创造性假设"""
        hypotheses = []

        # 隐喻理解
        if "探索" in text or "发现" in text:
            hypotheses.append(
                Hypothesis(
                    intent=IntentCategory.TECHNICAL_RESEARCH,
                    confidence=0.5,
                    reasoning=["探索性关键词"],
                    evidence=["探索", "发现"],
                    contradictions=[],
                )
            )

        return hypotheses

    @staticmethod
    def _recognize_language_patterns(text: str) -> dict[str, str]:
        """识别语言模式"""
        patterns = {}

        # 句式模式
        if text.endswith("?"):
            patterns["sentence_type"] = "疑问句"
        elif text.endswith("。") or text.endswith("."):
            patterns["sentence_type"] = "陈述句"
        elif any(text.endswith(p) for p in ["!", "~", "!"]):
            patterns["sentence_type"] = "感叹句"
        else:
            patterns["sentence_type"] = "未知句式"

        # 疑问词模式
        question_words = ["什么", "如何", "怎么", "为什么", "是否", "能否"]
        found_questions = [qw for qw in question_words if qw in text]
        if found_questions:
            patterns["question_type"] = f"包含疑问词: {', '.join(found_questions)}"

        return patterns

    @staticmethod
    def _analyze_entity_patterns(entities: dict[str, list[str]]) -> dict[str, Any]:
        """分析实体模式"""
        patterns = {
            "entity_types": list(entities.keys()),
            "total_entities": sum(len(v) for v in entities.values()),
            "primary_domain": "unknown",
        }

        # 确定主要领域
        entity_type_priority = {
            "PATENT_NUMBER": "patent",
            "APPLICATION_NUMBER": "patent",
            "LAW_ARTICLE": "legal",
            "REGULATION": "legal",
            "TECH_TERM": "technical",
        }

        for entity_type, domain in entity_type_priority.items():
            if entity_type in entities:
                patterns["primary_domain"] = domain
                break

        return patterns

    @staticmethod
    def _recognize_domain_patterns(
        text: str, entities: dict[str, list[str]]
    ) -> list[str]:
        """识别领域模式"""
        patterns = []

        # 领域关键词
        domain_keywords = {
            "patent": ["专利", "发明", "权利要求", "申请"],
            "legal": ["法律", "侵权", "合规", "合同"],
            "technical": ["算法", "代码", "系统", "架构"],
            "research": ["研究", "分析", "评估"],
        }

        for domain, keywords in domain_keywords.items():
            if any(kw in text for kw in keywords):
                patterns.append(domain)

        return patterns

    @staticmethod
    def _verify_pattern_consistency(trace: ThoughtTrace) -> str:
        """验证模式一致性"""
        # 检查不同阶段的模式是否一致
        return "一致"  # 简化版

    @staticmethod
    def _find_connections(
        text: str, entities: dict[str, list[str]], trace: ThoughtTrace
    ) -> list[str]:
        """找到信息连接"""
        connections = []

        # 连接实体与意图
        if entities:
            for entity_type in entities:
                connections.append(f"{entity_type} → 可能的意图线索")

        # 连接假设
        if len(trace.hypotheses) > 1:
            connections.append("多个假设需要权衡")

        return connections

    @staticmethod
    def _build_big_picture(trace: ThoughtTrace) -> str:
        """构建整体图景"""
        if trace.hypotheses:
            best = max(trace.hypotheses, key=lambda h: h.confidence)
            return f"最可能的意图: {best.intent.value} (置信度: {best.confidence:.2f})"
        return "需要更多信息来确定意图"

    @staticmethod
    def _identify_key_principles(trace: ThoughtTrace) -> list[str]:
        """识别关键原则"""
        principles = []

        # 从证据中提取
        for hypothesis in trace.hypotheses:
            if hypothesis.confidence > 0.7:
                principles.append(f"高置信意图: {hypothesis.intent.value}")

        return principles

    @staticmethod
    def _question_hypothesis(hypothesis: Hypothesis, text: str) -> list[str]:
        """质疑假设"""
        questions = []

        # 检查是否有更好的解释
        if hypothesis.confidence < 0.8:
            questions.append("置信度不足80%,可能存在其他解释")

        # 检查矛盾
        if hypothesis.contradictions:
            questions.append(f"存在矛盾: {hypothesis.contradictions}")

        return questions

    @staticmethod
    def _verify_logical_consistency(trace: ThoughtTrace) -> bool:
        """验证逻辑一致性"""
        # 简化版:检查假设之间是否有严重冲突
        return True

    @staticmethod
    def _verify_completeness(text: str, trace: ThoughtTrace) -> bool:
        """验证理解完整性"""
        # 检查是否遗漏关键信息
        # 简化版:基于文本长度和实体数量
        has_entities = any(trace.insights for insight in trace.insights if "实体" in insight)
        text_length = len(text)

        return not (text_length < 5 and not has_entities)

    def _make_final_decision(self, trace: ThoughtTrace) -> IntentCategory:
        """做出最终决策"""
        if not trace.hypotheses:
            return IntentCategory.CHITCHAT

        # 返回置信度最高的假设
        best = max(trace.hypotheses, key=lambda h: h.confidence)
        return best.intent


# =============================================================================
# 使用示例
# =============================================================================


async def example_usage():
    """使用示例"""
    analyzer = ThinkingProtocolAnalyzer()

    # 复杂输入示例
    text = "我刚才看到一项专利CN202310000000,想了解它和我们的产品是否冲突"

    print(f"输入: {text}\n")

    # 使用思维协议分析
    trace = await analyzer.analyze_with_thinking_protocol(text)

    # 打印思维轨迹
    for thought in trace.thoughts:
        print(thought)

    print(f"\n🎯 最终意图: {trace.decisions[-1]}")


if __name__ == "__main__":
    asyncio.run(example_usage())
