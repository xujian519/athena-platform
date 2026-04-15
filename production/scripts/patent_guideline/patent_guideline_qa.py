#!/usr/bin/env python3
"""
专利指南问答与推荐系统
Patent Guideline Q&A and Recommendation System

基于知识图谱的智能问答和规则推荐系统

作者: Athena平台团队
创建时间: 2025-12-20
"""

from __future__ import annotations
import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class QAContext:
    """问答上下文"""
    user_id: str
    session_id: str
    conversation_history: list[dict]
    user_profile: dict
    current_patent: dict = None

@dataclass
class AnswerResult:
    """回答结果"""
    answer: str
    confidence: float
    sources: list[dict]
    related_rules: list[dict]
    recommendations: list[dict]
    follow_up_questions: list[str]

@dataclass
class RuleRecommendation:
    """规则推荐"""
    rule_id: str
    rule_title: str
    rule_content: str
    relevance_score: float
    application_scenario: str
    related_cases: list[str]

class PatentGuidelineQA:
    """专利指南问答系统"""

    def __init__(self):
        # 导入检索器
        from .patent_guideline_retriever import PatentGuidelineRetriever
        self.retriever = PatentGuidelineRetriever()

        # 初始化上下文
        self.contexts = {}  # 会话上下文缓存
        self.user_profiles = {}  # 用户画像

        # 问答模板
        self.qa_templates = {
            "definition": {
                "pattern": r"(什么是|什么叫|如何理解|定义)",
                "template": "根据专利审查指南，{term}是指：\n{definition}\n\n相关要点：\n{key_points}"
            },
            "procedure": {
                "pattern": r"(如何|怎么|步骤|流程)",
                "template": "根据专利审查指南，{topic}的流程如下：\n{procedure}\n\n注意事项：\n{notes}"
            },
            "criterion": {
                "pattern": r"(标准|条件|要求|判断)",
                "template": "根据专利审查指南，{topic}的判断标准包括：\n{criteria}\n\n具体要求：\n{requirements}"
            },
            "example": {
                "pattern": r"(案例|例子|实例)",
                "template": "相关案例：\n{example}\n\n案例分析：\n{analysis}"
            }
        }

        # 推荐规则
        self.recommendation_rules = {
            "novelty": {
                "keywords": ["新颖性", "现有技术", "公开", "抵触申请"],
                "priority": 1,
                "related_sections": ["2.1", "3.1", "3.2.1"]
            },
            "inventive": {
                "keywords": ["创造性", "技术方案", "显著进步", "实质性特点"],
                "priority": 2,
                "related_sections": ["2.3", "4.2", "4.3"]
            },
            "utility": {
                "keywords": ["实用性", "工业应用", "可实施性", "积极效果"],
                "priority": 3,
                "related_sections": ["2.4", "5.2"]
            }
        }

    async def initialize(self):
        """初始化系统"""
        await self.retriever.initialize()
        logger.info("✅ 专利指南问答系统初始化完成")

    async def ask(self, question: str, user_id: str = "anonymous",
                   session_id: str = None, patent_info: dict = None) -> AnswerResult:
        """处理用户提问"""
        logger.info(f"用户提问: {question[:100]}...")

        # 获取或创建会话上下文
        if not session_id:
            session_id = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        context = self._get_or_create_context(user_id, session_id)

        # 更新当前专利信息
        if patent_info:
            context.current_patent = patent_info

        # 分析问题类型
        question_type = self._classify_question(question)

        # 根据类型选择处理策略
        if question_type == "definition":
            answer = await self._handle_definition_question(question, context)
        elif question_type == "procedure":
            answer = await self._handle_procedure_question(question, context)
        elif question_type == "criterion":
            answer = await self._handle_criterion_question(question, context)
        elif question_type == "example":
            answer = await self._handle_example_question(question, context)
        elif question_type == "comparison":
            answer = await self._handle_comparison_question(question, context)
        else:
            answer = await self._handle_general_question(question, context)

        # 更新对话历史
        context.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "answer": answer.answer,
            "type": question_type
        })

        # 生成推荐
        if context.current_patent:
            answer.recommendations = await self._generate_rule_recommendations(
                answer, context.current_patent
            )

        # 生成追问
        answer.follow_up_questions = self._generate_follow_up_questions(
            question, answer, context
        )

        # 更新用户画像
        self._update_user_profile(user_id, question, answer)

        return answer

    async def _handle_definition_question(self, question: str, context: QAContext) -> AnswerResult:
        """处理定义类问题"""
        # 提取要定义的术语
        term = self._extract_term_from_question(question)

        # 检索相关内容
        search_results = await self.retriever.search(
            f"{term} 是什么 定义", top_k=5
        )

        if not search_results:
            return AnswerResult(
                answer=f"抱歉，未找到关于'{term}'的定义。",
                confidence=0.0,
                sources=[],
                related_rules=[],
                recommendations=[],
                follow_up_questions=[]
            )

        # 提取定义内容
        definitions = []
        key_points = []
        sources = []

        for result in search_results:
            content = result.content
            # 查找定义句式
            def_patterns = [
                f"{term}是指",
                f"{term}定义为",
                f"{term}指的是",
                f"{term}即",
                f"{term}也就是"
            ]

            for pattern in def_patterns:
                if pattern in content:
                    start = content.find(pattern)
                    end = self._find_sentence_end(content, start + len(pattern))
                    definition = content[start:end]
                    if definition not in definitions:
                        definitions.append(definition)
                        break

            # 提取要点
            if "要点" in content or "注意" in content:
                key_points.append(content[:200])

            sources.append({
                "title": result.title,
                "section_id": result.section_id,
                "full_path": result.full_path
            })

        # 构建答案
        if definitions:
            main_def = definitions[0]
            other_defs = definitions[1:] if len(definitions) > 1 else []
        else:
            main_def = search_results[0].content[:200]
            other_defs = []

        answer_text = f"根据专利审查指南，{term}是指：\n{main_def}"

        if other_defs:
            answer_text += "\n\n其他相关说明："
            for i, other_def in enumerate(other_defs, 1):
                answer_text += f"\n{i}. {other_def}"

        if key_points:
            answer_text += "\n\n相关要点：\n" + "\n".join(
                f"• {point}" for point in key_points[:3]
            )

        return AnswerResult(
            answer=answer_text,
            confidence=0.9 if definitions else 0.7,
            sources=sources,
            related_rules=self._extract_related_rules(search_results),
            recommendations=[],
            follow_up_questions=[]
        )

    async def _handle_procedure_question(self, question: str, context: QAContext) -> AnswerResult:
        """处理流程类问题"""
        # 提取流程关键词
        keywords = self._extract_procedure_keywords(question)

        # 检索流程相关内容
        search_results = await self.retriever.search(
            f"{keywords} 流程 步骤 程序", top_k=5
        )

        if not search_results:
            return AnswerResult(
                answer=f"抱歉，未找到关于'{keywords}'的流程说明。",
                confidence=0.0,
                sources=[],
                related_rules=[],
                recommendations=[],
                follow_up_questions=[]
            )

        # 提取步骤
        procedure_steps = []
        notes = []
        sources = []

        for result in search_results:
            content = result.content

            # 查找步骤关键词
            step_patterns = [
                "第一步", "第二步", "第三步", "首先", "其次", "然后", "最后",
                "1.", "2.", "3.", "4.", "5.",
                "（1）", "（2）", "（3）"
            ]

            lines = content.split('\n')
            for _i, line in enumerate(lines):
                for pattern in step_patterns:
                    if pattern in line:
                        step_text = line.strip()
                        if step_text not in procedure_steps:
                            procedure_steps.append(step_text)

            # 提取注意事项
            if "注意" in content or "应当" in content or "不得" in content:
                notes.append(content[:300])

            sources.append({
                "title": result.title,
                "section_id": result.section_id
            })

        # 构建答案
        answer_text = f"根据专利审查指南，{keywords}的流程如下：\n\n"

        if procedure_steps:
            answer_text += "\n".join(
                f"• {step}" for step in procedure_steps[:5]
            )
        else:
            answer_text += search_results[0].content[:500]

        if notes:
            answer_text += "\n\n注意事项：\n" + "\n".join(
                f"• {note}" for note in notes[:3]
            )

        return AnswerResult(
            answer=answer_text,
            confidence=0.8,
            sources=sources,
            related_rules=self._extract_related_rules(search_results),
            recommendations=[],
            follow_up_questions=[]
        )

    async def _handle_criterion_question(self, question: str, context: QAContext) -> AnswerResult:
        """处理标准类问题"""
        # 提取标准关键词
        criteria = self._extract_criteria_keywords(question)

        # 检索标准相关内容
        search_results = await self.retriever.search(
            f"{criteria} 标准 条件 要求", top_k=5
        )

        if not search_results:
            return AnswerResult(
                answer=f"抱歉，未找到关于'{criteria}'的标准说明。",
                confidence=0.0,
                sources=[],
                related_rules=[],
                recommendations=[],
                follow_up_questions=[]
            )

        # 提取标准和要求
        standards = []
        requirements = []
        sources = []

        for result in search_results:
            content = result.content

            # 查找标准句式
            standard_patterns = [
                "应当符合",
                "必须满足",
                "标准包括",
                "判断标准",
                "审查标准"
            ]

            lines = content.split('\n')
            for line in lines:
                for pattern in standard_patterns:
                    if pattern in line:
                        standard_text = line.strip()
                        if standard_text not in standards:
                            standards.append(standard_text)

            # 提取要求
            if "要求" in content or "条件" in content:
                requirements.append(content[:300])

            sources.append({
                "title": result.title,
                "section_id": result.section_id
            })

        # 构建答案
        answer_text = f"根据专利审查指南，{criteria}的判断标准包括：\n\n"

        if standards:
            answer_text += "\n".join(
                f"• {standard}" for standard in standards[:5]
            )
        else:
            answer_text += search_results[0].content[:500]

        if requirements:
            answer_text += "\n\n具体要求：\n" + "\n".join(
                f"• {req}" for req in requirements[:3]
            )

        return AnswerResult(
            answer=answer_text,
            confidence=0.8,
            sources=sources,
            related_rules=self._extract_related_rules(search_results),
            recommendations=[],
            follow_up_questions=[]
        )

    async def _handle_example_question(self, question: str, context: QAContext) -> AnswerResult:
        """处理案例类问题"""
        # 检索案例
        search_results = await self.retriever.search(
            f"{question} 案例 示例 实例", top_k=5
        )

        if not search_results:
            return AnswerResult(
                answer="抱歉，未找到相关的案例。",
                confidence=0.0,
                sources=[],
                related_rules=[],
                recommendations=[],
                follow_up_questions=[]
            )

        # 提取案例
        examples = []
        analyses = []
        sources = []

        for result in search_results:
            content = result.content

            # 查找案例标记
            if "【例" in content or "案例" in content:
                examples.append(content)
                # 查找分析
                if "分析" in content or "结论" in content:
                    analyses.append(content)

            sources.append({
                "title": result.title,
                "section_id": result.section_id
            })

        # 构建答案
        if examples:
            example = examples[0]
            answer_text = f"相关案例：\n\n{example[:800]}"

            if analyses:
                answer_text += f"\n\n案例分析：\n{analyses[0][:400]}"
        else:
            answer_text = search_results[0].content[:800]

        return AnswerResult(
            answer=answer_text,
            confidence=0.8,
            sources=sources,
            related_rules=self._extract_related_rules(search_results),
            recommendations=[],
            follow_up_questions=[]
        )

    async def _handle_comparison_question(self, question: str, context: QAContext) -> AnswerResult:
        """处理比较类问题"""
        # 提取比较对象
        comparison_items = self._extract_comparison_items(question)

        # 检索比较相关内容
        search_results = await self.retriever.search(
            f"{question} 区别 对比 不同", top_k=5
        )

        if not search_results:
            return AnswerResult(
                answer="抱歉，未找到相关的比较说明。",
                confidence=0.0,
                sources=[],
                related_rules=[],
                recommendations=[],
                follow_up_questions=[]
            )

        # 简化处理：返回检索内容
        return AnswerResult(
            answer=search_results[0].content[:800],
            confidence=0.7,
            sources=[{
                "title": search_results[0].title,
                "section_id": search_results[0].section_id
            }],
            related_rules=self._extract_related_rules(search_results),
            recommendations=[],
            follow_up_questions=[]
        )

    async def _handle_general_question(self, question: str, context: QAContext) -> AnswerResult:
        """处理一般性问题"""
        # 直接检索
        search_results = await self.retriever.search(question, top_k=5)

        if not search_results:
            return AnswerResult(
                answer="抱歉，未找到相关内容。请尝试使用更具体的关键词。",
                confidence=0.0,
                sources=[],
                related_rules=[],
                recommendations=[],
                follow_up_questions=["您可以询问关于专利审查的具体问题。"]
            )

        # 结合检索结果生成答案
        retriever_answer = await self.retriever.answer_question(question)
        if retriever_answer and retriever_answer.get('confidence', 0) > 0.5:
            return AnswerResult(
                answer=retriever_answer['answer'],
                confidence=retriever_answer['confidence'],
                sources=retriever_answer['sources'],
                related_rules=self._extract_related_rules(search_results),
                recommendations=[],
                follow_up_questions=[]
            )
        else:
            # 简单返回检索结果
            return AnswerResult(
                answer=f"以下是相关内容：\n\n{search_results[0].content}",
                confidence=0.6,
                sources=[{
                    "title": search_results[0].title,
                    "section_id": search_results[0].section_id
                }],
                related_rules=self._extract_related_rules(search_results),
                recommendations=[],
                follow_up_questions=[]
            )

    async def _generate_rule_recommendations(self, answer: AnswerResult,
                                              patent_info: dict) -> list[RuleRecommendation]:
        """生成规则推荐"""
        recommendations = []

        # 分析专利信息中的关键词
        patent_keywords = []
        if patent_info:
            patent_text = f"{patent_info.get('title', '')} {patent_info.get('abstract', '')} {patent_info.get('claims', '')}"
            patent_keywords = self._extract_patent_keywords(patent_text)

        # 匹配推荐规则
        for rule_name, rule_config in self.recommendation_rules.items():
            # 检查关键词匹配
            match_count = sum(1 for kw in rule_config['keywords'] if kw in patent_keywords)
            if match_count > 0:
                # 检索相关规则
                search_results = await self.retriever.search(
                    " ".join(rule_config['keywords']), top_k=3
                )

                for result in search_results:
                    recommendation = RuleRecommendation(
                        rule_id=f"{rule_name}_{result.section_id}",
                        rule_title=result.title,
                        rule_content=result.content[:500],
                        relevance_score=match_count / len(rule_config['keywords']),
                        application_scenario=f"适用于{rule_name}相关审查",
                        related_cases=[]
                    )
                    recommendations.append(recommendation)

        # 按相关性排序
        recommendations.sort(key=lambda x: x.relevance_score, reverse=True)

        return recommendations[:5]

    def _generate_follow_up_questions(self, question: str, answer: AnswerResult,
                                      context: QAContext) -> list[str]:
        """生成追问"""
        follow_ups = []

        # 基于问题类型生成追问
        if "定义" in question or "是什么" in question:
            follow_ups.extend([
                "这个概念在实际审查中如何应用？",
                "有没有相关的案例可以参考？",
                "与其他相关概念有什么区别？"
            ])

        elif "如何" in question or "怎么" in question:
            follow_ups.extend([
                "这个流程中需要注意哪些事项？",
                "相关的法律依据是什么？",
                "有没有例外情况？"
            ])

        elif "标准" in question or "条件" in question:
            follow_ups.extend([
                "这个标准的依据是什么？",
                "具体如何执行判断？",
                "有哪些常见的误区？"
            ])

        # 基于用户画像生成个性化追问
        user_history = context.conversation_history
        if len(user_history) > 0:
            last_topic = user_history[-1].get("question", "")
            if last_topic:
                follow_ups.append(f"关于'{last_topic[:20]}...'，您还想了解什么？")

        # 限制追问数量
        return follow_ups[:3]

    def _classify_question(self, question: str) -> str:
        """分类问题类型"""
        for question_type, config in self.qa_templates.items():
            if re.search(config['pattern'], question):
                return question_type

        # 特殊判断比较类问题
        if any(word in question for word in ["区别", "对比", "不同", "相同", "差异"]):
            return "comparison"

        return "general"

    def _extract_term_from_question(self, question: str) -> str:
        """从问题中提取术语"""
        # 简化处理
        patterns = [
            r"什么是(.+)",
            r"什么叫(.+)",
            r"如何理解(.+)",
            r"(.+)是指什么",
            r"(.+)的定义"
        ]

        for pattern in patterns:
            match = re.search(pattern, question)
            if match:
                term = match.group(1).strip("？。的")
                return term

        return question

    def _extract_procedure_keywords(self, question: str) -> str:
        """提取流程关键词"""
        keywords = ["流程", "程序", "步骤", "方法", "申请", "审查", "决定"]
        found = [kw for kw in keywords if kw in question]
        return found[0] if found else question

    def _extract_criteria_keywords(self, question: str) -> str:
        """提取标准关键词"""
        keywords = ["标准", "条件", "要求", "判断", "评估", "审查"]
        found = [kw for kw in keywords if kw in question]
        return found[0] if found else question

    def _extract_comparison_items(self, question: str) -> list[str]:
        """提取比较对象"""
        # 简化处理
        items = []
        if "和" in question:
            parts = question.split("和")
            if len(parts) >= 2:
                items.append(parts[0].strip())
                items.append(parts[1].split("的")[0].strip())
        return items

    def _extract_patent_keywords(self, text: str) -> list[str]:
        """提取专利关键词"""
        keywords = []
        # 技术领域关键词
        tech_fields = ["电子信息", "计算机", "通信", "机械", "化学", "生物", "医药"]
        keywords.extend([f for f in tech_fields if f in text])

        # 专利类型关键词
        patent_types = ["发明", "实用新型", "外观设计"]
        keywords.extend([t for t in patent_types if t in text])

        # 审查标准关键词
        review_standards = ["新颖性", "创造性", "实用性"]
        keywords.extend([s for s in review_standards if s in text])

        return keywords

    def _extract_related_rules(self, search_results: list) -> list[dict]:
        """提取相关规则"""
        rules = []
        for result in search_results[:3]:
            rules.append({
                "title": result.title,
                "section_id": result.section_id,
                "relevance": result.score
            })
        return rules

    def _find_sentence_end(self, text: str, start: int) -> int:
        """查找句子结束位置"""
        end_chars = ['。', '！', '？', '\n']
        min_end = len(text)

        for char in end_chars:
            pos = text.find(char, start)
            if pos > start:
                min_end = min(min_end, pos)

        return min_end

    def _get_or_create_context(self, user_id: str, session_id: str) -> QAContext:
        """获取或创建上下文"""
        key = f"{user_id}_{session_id}"
        if key not in self.contexts:
            self.contexts[key] = QAContext(
                user_id=user_id,
                session_id=session_id,
                conversation_history=[],
                user_profile=self.user_profiles.get(user_id, {})
            )
        return self.contexts[key]

    def _update_user_profile(self, user_id: str, question: str, answer: AnswerResult) -> Any:
        """更新用户画像"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                "question_count": 0,
                "topics": {},
                "last_active": datetime.now().isoformat()
            }

        profile = self.user_profiles[user_id]
        profile["question_count"] += 1
        profile["last_active"] = datetime.now().isoformat()

        # 统计话题
        topic = self._extract_topic_from_question(question)
        if topic:
            profile["topics"][topic] = profile["topics"].get(topic, 0) + 1

    def _extract_topic_from_question(self, question: str) -> str:
        """从问题中提取话题"""
        topics = ["新颖性", "创造性", "实用性", "审查", "申请", "授权", "驳回"]
        for topic in topics:
            if topic in question:
                return topic
        return "其他"

    async def close(self):
        """关闭系统"""
        await self.retriever.close()

# 使用示例
async def main():
    """主函数示例"""
    qa_system = PatentGuidelineQA()
    await qa_system.initialize()

    try:
        # 示例问答
        questions = [
            "什么是专利的创造性？",
            "如何判断新颖性？",
            "实用性的标准是什么？",
            "发明和实用新型有什么区别？"
        ]

        for question in questions:
            print(f"\n问: {question}")
            answer = await qa_system.ask(question, user_id="test_user")
            print(f"\n答: {answer.answer[:300]}...")
            print(f"置信度: {answer.confidence:.2f}")
            if answer.recommendations:
                print(f"推荐规则数: {len(answer.recommendations)}")
            if answer.follow_up_questions:
                print(f"推荐追问: {answer.follow_up_questions[0]}")

    finally:
        await qa_system.close()

if __name__ == "__main__":
    asyncio.run(main())
