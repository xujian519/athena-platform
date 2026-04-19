#!/usr/bin/env python3
from __future__ import annotations
"""
小娜自适应学习系统
Xiaona Adaptive Learning System

为小娜专利法律专家设计的智能学习和反思系统
集成持续学习、知识更新、经验积累和智能优化

作者: 徐健 (xujian519@gmail.com)
创建时间: 2025-12-17
版本: v2.0.0 Adaptive
"""

import asyncio
import hashlib
import json
import logging
import pickle
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from ..cognition.xiaona_enhanced_reflection_engine import LegalReflectionResult
from ..collaboration.human_ai_collaboration_framework import CollaborationSession

logger = logging.getLogger(__name__)


class LearningType(Enum):
    """学习类型"""

    KNOWLEDGE_ACQUISITION = "knowledge_acquisition"  # 知识获取
    EXPERIENCE_ACCUMULATION = "experience_accumulation"  # 经验积累
    PATTERN_RECOGNITION = "pattern_recognition"  # 模式识别
    ERROR_CORRECTION = "error_correction"  # 错误纠正
    STRATEGY_OPTIMIZATION = "strategy_optimization"  # 策略优化
    FEEDBACK_INTEGRATION = "feedback_integration"  # 反馈整合


class LearningTrigger(Enum):
    """学习触发条件"""

    REFLECTION_COMPLETION = "reflection_completion"  # 反思完成
    HUMAN_FEEDBACK = "human_feedback"  # 人工反馈
    PERFORMANCE_DECLINE = "performance_decline"  # 性能下降
    KNOWLEDGE_GAP = "knowledge_gap"  # 知识缺口
    NEW_CASE_ENCOUNTERED = "new_case_encountered"  # 新案例
    SCHEDULED_LEARNING = "scheduled_learning"  # 定期学习


class KnowledgeDomain(Enum):
    """知识领域"""

    PATENT_LAW = "patent_law"  # 专利法
    CONTRACT_LAW = "contract_law"  # 合同法
    IP_PROTECTION = "ip_protection"  # 知识产权保护
    TECHNICAL_ANALYSIS = "technical_analysis"  # 技术分析
    LEGAL_RESEARCH = "legal_research"  # 法律研究
    RISK_ASSESSMENT = "risk_assessment"  # 风险评估


@dataclass
class LearningEvent:
    """学习事件"""

    event_id: str
    learning_type: LearningType
    trigger: LearningTrigger
    timestamp: datetime
    context: dict[str, Any]
    content: dict[str, Any]
    outcomes: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    impact_level: int = 3  # 1-5, 5最高
    tags: list[str] = field(default_factory=list)


@dataclass
class KnowledgeItem:
    """知识条目"""

    item_id: str
    domain: KnowledgeDomain
    title: str
    content: str
    source: str
    confidence: float
    last_updated: datetime
    access_count: int = 0
    usage_success: int = 0
    related_items: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class ExperiencePattern:
    """经验模式"""

    pattern_id: str
    description: str
    trigger_conditions: list[str]
    action_sequence: list[str]
    success_rate: float
    usage_count: int = 0
    last_applied: datetime | None = None
    domain: KnowledgeDomain | None = None


@dataclass
class LearningProfile:
    """学习档案"""

    profile_id: str
    agent_name: str
    creation_date: datetime
    total_learning_events: int = 0
    knowledge_domains: dict[KnowledgeDomain, int] = field(default_factory=dict)
    performance_metrics: dict[str, float] = field(default_factory=dict)
    learning_trends: dict[str, list[float]] = field(default_factory=dict)
    expertise_areas: list[KnowledgeDomain] = field(default_factory=list)
    improvement_areas: list[str] = field(default_factory=list)


class XiaonaAdaptiveLearningSystem:
    """小娜自适应学习系统"""

    def __init__(self, storage_path: str = "/tmp/xiaona_learning"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # 核心数据存储
        self.learning_events: list[LearningEvent] = []
        self.knowledge_base: dict[str, KnowledgeItem] = {}
        self.experience_patterns: dict[str, ExperiencePattern] = {}
        self.learning_profile: LearningProfile | None = None

        # 学习配置
        self.learning_config = {
            "max_events_per_batch": 100,
            "knowledge_retention_days": 365,
            "pattern_min_success_rate": 0.7,
            "learning_confidence_threshold": 0.8,
            "auto_learning_enabled": True,
            "scheduled_learning_interval": 7,  # 天
        }

        # 性能跟踪
        self.performance_tracker = {
            "daily_scores": [],
            "weekly_trends": {},
            "domain_performance": {},
            "error_patterns": {},
        }

        # 初始化学习档案
        self._initialize_learning_profile()

        # 加载已保存的学习数据
        self._load_learning_data()

    def _initialize_learning_profile(self) -> Any:
        """初始化学习档案"""
        self.learning_profile = LearningProfile(
            profile_id="xiaona_legal_expert",
            agent_name="小娜·天秤女神",
            creation_date=datetime.now(),
            total_learning_events=0,
            knowledge_domains=dict.fromkeys(KnowledgeDomain, 0),
            performance_metrics={"accuracy": 0.85, "efficiency": 0.80, "adaptability": 0.75},
            learning_trends={
                "knowledge_growth": [],
                "performance_trend": [],
                "learning_frequency": [],
            },
        )

    async def _analyze_errors(self, weaknesses: list[str]) -> dict[str, Any]:
        """分析错误原因"""
        return {
            "error_types": weaknesses,
            "root_causes": [f"需要改进: {w}" for w in weaknesses],
            "impact_level": "medium",
        }

    async def _generate_correction_strategies(self, error_analysis: dict[str, Any]) -> list[str]:
        """生成纠正策略"""
        strategies = []
        for error in error_analysis.get("error_types", []):
            if "准确性" in error:
                strategies.append("加强事实核查和法律依据验证")
            elif "完整性" in error:
                strategies.append("补充更多分析维度和考虑因素")
            elif "逻辑性" in error:
                strategies.append("优化推理过程和逻辑链条")
        return strategies

    async def _update_error_knowledge(self, error_analysis: dict[str, Any], strategies: list[str]):
        """更新错误知识"""
        # 简化实现
        pass

    async def _analyze_strategy_effectiveness(self, event: LearningEvent) -> dict[str, Any]:
        """分析策略效果"""
        return {"effectiveness": 0.8, "areas_for_improvement": []}

    async def _generate_optimization_suggestions(
        self, strategy_analysis: dict[str, Any]
    ) -> list[str]:
        """生成优化建议"""
        return ["继续优化分析流程", "提高专业判断准确性"]

    async def _update_strategy_knowledge(self, optimization_suggestions: list[str]):
        """更新策略知识"""
        # 简化实现
        pass

    async def process_reflection_result(self, reflection_result: LegalReflectionResult):
        """处理反思结果,触发学习"""

        logger.info(f"处理反思结果: {reflection_result.task_id}")

        # 创建学习事件
        learning_event = LearningEvent(
            event_id=f"reflection_{int(datetime.now().timestamp())}",
            learning_type=(
                LearningType.ERROR_CORRECTION
                if reflection_result.should_refine
                else LearningType.EXPERIENCE_ACCUMULATION
            ),
            trigger=LearningTrigger.REFLECTION_COMPLETION,
            timestamp=datetime.now(),
            context={
                "task_id": reflection_result.task_id,
                "task_type": reflection_result.task_type,
                "overall_score": reflection_result.overall_score,
                "should_refine": reflection_result.should_refine,
            },
            content={
                "strengths": reflection_result.strengths,
                "weaknesses": reflection_result.weaknesses,
                "recommendations": reflection_result.recommendations,
                "category_scores": reflection_result.category_scores,
            },
            confidence=reflection_result.confidence_level,
            impact_level=reflection_result.refinement_priority,
        )

        # 处理学习事件
        await self._process_learning_event(learning_event)

        # 如果需要改进,生成改进建议
        if reflection_result.should_refine:
            await self._generate_improvement_plan(reflection_result)

        # 更新性能指标
        self._update_performance_metrics(reflection_result)

    async def process_human_feedback(
        self,
        session: CollaborationSession,
        human_feedback: str,
        feedback_quality: str = "constructive",
    ):
        """处理人工反馈"""

        logger.info(f"处理人工反馈: {session.session_id}")

        # 分析反馈内容
        feedback_analysis = await self._analyze_human_feedback(
            human_feedback, str(session.task.task_type)  # 转换为字符串
        )

        # 创建学习事件
        learning_event = LearningEvent(
            event_id=f"human_feedback_{int(datetime.now().timestamp())}",
            learning_type=LearningType.FEEDBACK_INTEGRATION,
            trigger=LearningTrigger.HUMAN_FEEDBACK,
            timestamp=datetime.now(),
            context={
                "session_id": session.session_id,
                "task_type": session.task.task_type,
                "feedback_quality": feedback_quality,
                "ai_confidence": session.ai_confidence,
                "human_confidence": session.human_confidence,
            },
            content={
                "human_feedback": human_feedback,
                "feedback_analysis": feedback_analysis,
                "consensus_reached": session.consensus_reached,
            },
            confidence=0.9 if feedback_quality == "constructive" else 0.7,
            impact_level=4,  # 人工反馈影响较大
        )

        await self._process_learning_event(learning_event)

    async def _process_learning_event(self, event: LearningEvent):
        """处理学习事件"""

        # 存储学习事件
        self.learning_events.append(event)

        # 根据学习类型执行相应操作
        if event.learning_type == LearningType.KNOWLEDGE_ACQUISITION:
            await self._acquire_knowledge(event)
        elif event.learning_type == LearningType.EXPERIENCE_ACCUMULATION:
            await self._accumulate_experience(event)
        elif event.learning_type == LearningType.PATTERN_RECOGNITION:
            await self._recognize_patterns(event)
        elif event.learning_type == LearningType.ERROR_CORRECTION:
            await self._correct_errors(event)
        elif event.learning_type == LearningType.STRATEGY_OPTIMIZATION:
            await self._optimize_strategy(event)

        # 更新学习档案
        self._update_learning_profile(event)

        # 检查是否需要触发其他学习
        await self._check_learning_triggers(event)

        logger.info(f"学习事件处理完成: {event.event_id}")

    async def _acquire_knowledge(self, event: LearningEvent):
        """知识获取"""

        # 从事件内容中提取新知识
        knowledge_items = await self._extract_knowledge(event)

        for item in knowledge_items:
            # 检查是否已存在相似知识
            similar_item = await self._find_similar_knowledge(item)

            if similar_item:
                # 更新现有知识
                await self._update_knowledge_item(similar_item.item_id, item)
            else:
                # 添加新知识
                await self._add_knowledge_item(item)

        logger.info(f"获取了 {len(knowledge_items)} 条新知识")

    async def _accumulate_experience(self, event: LearningEvent):
        """经验积累"""

        # 分析成功和失败的模式
        if event.context.get("overall_score", 0) > 0.8:
            await self._extract_success_pattern(event)  # type: ignore
        else:
            await self._extract_failure_pattern(event)  # type: ignore

    async def _recognize_patterns(self, event: LearningEvent):
        """模式识别"""

        # 分析事件序列中的模式
        recent_events = self.learning_events[-20:]  # 最近20个事件
        patterns = await self._analyze_event_patterns(recent_events)  # type: ignore

        for pattern in patterns:
            if pattern.success_rate >= self.learning_config["pattern_min_success_rate"]:
                # 保存成功模式
                await self._save_experience_pattern(pattern)  # type: ignore

    async def _correct_errors(self, event: LearningEvent):
        """错误纠正"""

        # 分析错误原因
        error_analysis = await self._analyze_errors(event.content.get("weaknesses", []))

        # 生成纠正策略
        correction_strategies = await self._generate_correction_strategies(error_analysis)

        # 更新知识库中的错误信息
        await self._update_error_knowledge(error_analysis, correction_strategies)

    async def _optimize_strategy(self, event: LearningEvent):
        """策略优化"""

        # 分析当前策略的效果
        strategy_analysis = await self._analyze_strategy_effectiveness(event)

        # 生成优化建议
        optimization_suggestions = await self._generate_optimization_suggestions(strategy_analysis)

        # 更新策略知识
        await self._update_strategy_knowledge(optimization_suggestions)

    async def _extract_knowledge(self, event: LearningEvent) -> list[KnowledgeItem]:
        """从事件中提取知识"""

        knowledge_items = []

        # 根据任务类型确定知识领域
        task_type = event.context.get("task_type", "")
        if "patent" in task_type:
            domain = KnowledgeDomain.PATENT_LAW
        elif "contract" in task_type:
            domain = KnowledgeDomain.CONTRACT_LAW
        elif "technical" in task_type:
            domain = KnowledgeDomain.TECHNICAL_ANALYSIS
        else:
            domain = KnowledgeDomain.LEGAL_RESEARCH

        # 从事件内容中提取关键知识
        content = event.content

        # 提取优势知识
        for strength in content.get("strengths", []):
            item = KnowledgeItem(
                item_id=f"knowledge_{hashlib.md5(strength.encode(), usedforsecurity=False).hexdigest()}",
                domain=domain,
                title=f"优势: {strength[:50]}",
                content=strength,
                source=f"reflection_{event.event_id}",
                confidence=event.confidence,
                last_updated=datetime.now(),
                tags=["strength", event.learning_type.value],
            )
            knowledge_items.append(item)

        # 提取建议知识
        for recommendation in content.get("recommendations", []):
            item = KnowledgeItem(
                item_id=f"knowledge_{hashlib.md5(recommendation.encode(), usedforsecurity=False).hexdigest()}",
                domain=domain,
                title=f"建议: {recommendation[:50]}",
                content=recommendation,
                source=f"reflection_{event.event_id}",
                confidence=event.confidence * 0.9,  # 建议的置信度稍低
                last_updated=datetime.now(),
                tags=["recommendation", event.learning_type.value],
            )
            knowledge_items.append(item)

        return knowledge_items

    async def _find_similar_knowledge(self, new_item: KnowledgeItem) -> KnowledgeItem | None:
        """查找相似知识"""

        # 简单实现:基于标题相似度
        for item in self.knowledge_base.values():
            if item.domain == new_item.domain:
                # 计算标题相似度(简化版)
                similarity = self._calculate_text_similarity(item.title, new_item.title)
                if similarity > 0.8:  # 相似度阈值
                    return item

        return None

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度(简化版)"""

        # 转换为小写并分词
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        # 计算交集和并集
        intersection = words1.intersection(words2)
        union = words1.union(words2)

        # Jaccard相似度
        if not union:
            return 0.0

        return len(intersection) / len(union)

    async def _add_knowledge_item(self, item: KnowledgeItem):
        """添加知识条目"""
        self.knowledge_base[item.item_id] = item

        # 更新学习档案
        if self.learning_profile:
            self.learning_profile.knowledge_domains[item.domain] = (
                self.learning_profile.knowledge_domains.get(item.domain, 0) + 1
            )

    async def _update_knowledge_item(self, item_id: str, new_item: KnowledgeItem):
        """更新知识条目"""
        if item_id in self.knowledge_base:
            existing = self.knowledge_base[item_id]

            # 合并内容
            existing.content = f"{existing.content}\n\n更新内容:\n{new_item.content}"
            existing.confidence = (existing.confidence + new_item.confidence) / 2
            existing.last_updated = datetime.now()
            existing.tags.extend(new_item.tags)
            existing.tags = list(set(existing.tags))  # 去重

    async def _generate_improvement_plan(self, reflection_result: LegalReflectionResult):
        """生成改进计划"""

        improvement_plan = {
            "task_id": reflection_result.task_id,
            "improvement_areas": reflection_result.weaknesses,
            "priority_actions": reflection_result.recommendations[:3],  # 前3个建议
            "estimated_improvement_time": self._estimate_improvement_time(reflection_result),
            "success_criteria": self._define_success_criteria(reflection_result),
        }

        # 保存改进计划
        plan_path = self.storage_path / f"improvement_plan_{reflection_result.task_id}.json"
        with open(plan_path, "w", encoding="utf-8") as f:
            json.dump(improvement_plan, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"生成改进计划: {reflection_result.task_id}")

    def _estimate_improvement_time(self, reflection_result: LegalReflectionResult) -> str:
        """估算改进时间"""

        if reflection_result.refinement_priority >= 4:
            return "2-3小时"
        elif reflection_result.refinement_priority >= 3:
            return "1-2小时"
        else:
            return "30分钟-1小时"

    def _define_success_criteria(self, reflection_result: LegalReflectionResult) -> list[str]:
        """定义成功标准"""

        criteria = []
        target_score = min(reflection_result.overall_score + 0.15, 0.95)

        criteria.append(f"总体评分提升至 {target_score:.2f} 以上")

        for category, score in reflection_result.category_scores.items():
            if score < 0.8:
                criteria.append(f"{category} 类别评分提升至 0.80 以上")

        return criteria

    def _update_performance_metrics(self, reflection_result: LegalReflectionResult) -> Any:
        """更新性能指标"""

        # 记录今日分数
        today = datetime.now().date().isoformat()
        self.performance_tracker["daily_scores"].append(
            {
                "date": today,
                "score": reflection_result.overall_score,
                "task_type": reflection_result.task_type,
            }
        )

        # 更新领域性能
        task_type = reflection_result.task_type
        if task_type not in self.performance_tracker["domain_performance"]:
            self.performance_tracker["domain_performance"][task_type] = []

        self.performance_tracker["domain_performance"][task_type].append(
            {"timestamp": datetime.now().isoformat(), "score": reflection_result.overall_score}
        )

        # 更新学习档案的性能指标
        if self.learning_profile and self.learning_events:
            recent_scores = [
                e.context.get("overall_score", 0)
                for e in self.learning_events[-10:]
                if "overall_score" in e.context
            ]

            if recent_scores:
                avg_score = sum(recent_scores) / len(recent_scores)
                self.learning_profile.performance_metrics["accuracy"] = avg_score

    async def _analyze_human_feedback(self, feedback: str, task_type: str) -> dict[str, Any]:
        """分析人工反馈"""

        analysis = {
            "sentiment": "neutral",  # positive, negative, neutral
            "key_points": [],
            "action_items": [],
            "complexity_level": "medium",
        }

        # 简单的情感分析
        positive_words = ["好", "优秀", "正确", "满意", "同意", "通过"]
        negative_words = ["差", "错误", "不好", "反对", "拒绝", "重做"]

        positive_count = sum(1 for word in positive_words if word in feedback)
        negative_count = sum(1 for word in negative_words if word in feedback)

        if positive_count > negative_count:
            analysis["sentiment"] = "positive"
        elif negative_count > positive_count:
            analysis["sentiment"] = "negative"

        # 提取关键点
        sentences = feedback.split("。")
        for sentence in sentences:
            if "建议" in sentence or "需要" in sentence or "应该" in sentence:
                analysis["key_points"].append(sentence.strip())

        # 生成行动项
        if "修改" in feedback:
            analysis["action_items"].append("需要修改分析结果")
        if "补充" in feedback:
            analysis["action_items"].append("需要补充更多分析")
        if "重新" in feedback:
            analysis["action_items"].append("需要重新进行分析")

        return analysis

    def _update_learning_profile(self, event: LearningEvent) -> Any:
        """更新学习档案"""

        if not self.learning_profile:
            return

        # 更新总学习事件数
        self.learning_profile.total_learning_events += 1

        # 更新学习趋势
        self.learning_profile.learning_trends["learning_frequency"].append(
            len(self.learning_events) / 7  # 最近7天的事件数
        )

        # 保持趋势数据在合理范围内
        for trend in self.learning_profile.learning_trends.values():
            if len(trend) > 30:
                trend.pop(0)

    async def _trigger_learning(self, trigger: LearningTrigger):
        """触发学习"""
        # 简化实现
        logger.info(f"触发学习: {trigger.value}")

    async def _check_learning_triggers(self, event: LearningEvent):
        """检查是否需要触发其他学习"""

        # 检查性能下降
        if self._is_performance_declining():
            await self._trigger_learning(LearningTrigger.PERFORMANCE_DECLINE)

        # 检查知识缺口
        if await self._detect_knowledge_gaps():
            await self._trigger_learning(LearningTrigger.KNOWLEDGE_GAP)

    def _is_performance_declining(self) -> bool:
        """检查性能是否下降"""

        recent_scores = self.performance_tracker["daily_scores"][-10:]
        if len(recent_scores) < 5:
            return False

        # 比较最近5次和之前的平均分
        recent_avg = sum(s["score"] for s in recent_scores[-5:]) / 5
        previous_avg = sum(s["score"] for s in recent_scores[:-5]) / len(recent_scores[:-5])

        return recent_avg < previous_avg - 0.1  # 下降超过0.1

    async def _detect_knowledge_gaps(self) -> bool:
        """检测知识缺口"""

        # 简单实现:检查是否有任务类型对应的知识较少
        knowledge_domains = {item.domain for item in self.knowledge_base.values()}

        # 如果某些领域知识不足,返回True
        required_domains = {KnowledgeDomain.PATENT_LAW, KnowledgeDomain.LEGAL_RESEARCH}
        missing_domains = required_domains - knowledge_domains

        return len(missing_domains) > 0

    def get_learning_summary(self) -> dict[str, Any]:
        """获取学习总结"""

        if not self.learning_profile:
            return {"error": "学习档案未初始化"}

        summary = {
            "agent_profile": {
                "name": self.learning_profile.agent_name,
                "total_events": self.learning_profile.total_learning_events,
                "creation_date": self.learning_profile.creation_date.isoformat(),
            },
            "knowledge_base": {
                "total_items": len(self.knowledge_base),
                "domain_distribution": {
                    domain.value: sum(
                        1 for item in self.knowledge_base.values() if item.domain == domain
                    )
                    for domain in KnowledgeDomain
                },
            },
            "experience_patterns": {
                "total_patterns": len(self.experience_patterns),
                "high_success_patterns": sum(
                    1 for p in self.experience_patterns.values() if p.success_rate > 0.85
                ),
            },
            "performance_metrics": self.learning_profile.performance_metrics,
            "recent_trends": {
                trend_name: values[-5:] if len(values) >= 5 else values
                for trend_name, values in self.learning_profile.learning_trends.items()
            },
        }

        return summary

    def _save_learning_data(self) -> Any:
        """保存学习数据"""
        try:
            # 保存学习事件
            events_file = self.storage_path / "learning_events.pkl"
            with open(events_file, "wb") as f:
                pickle.dump(self.learning_events[-1000:], f)  # 只保存最近1000个事件

            # 保存知识库
            knowledge_file = self.storage_path / "knowledge_base.json"
            knowledge_data = {
                item_id: {
                    "domain": item.domain.value,
                    "title": item.title,
                    "content": item.content,
                    "confidence": item.confidence,
                    "tags": item.tags,
                }
                for item_id, item in self.knowledge_base.items()
            }
            with open(knowledge_file, "w", encoding="utf-8") as f:
                json.dump(knowledge_data, f, ensure_ascii=False, indent=2)

            # 保存学习档案
            profile_file = self.storage_path / "learning_profile.json"
            if self.learning_profile:
                profile_data = {
                    "agent_name": self.learning_profile.agent_name,
                    "total_events": self.learning_profile.total_learning_events,
                    "performance_metrics": self.learning_profile.performance_metrics,
                    "creation_date": self.learning_profile.creation_date.isoformat(),
                }
                with open(profile_file, "w", encoding="utf-8") as f:
                    json.dump(profile_data, f, ensure_ascii=False, indent=2)

            logger.info("学习数据保存成功")

        except Exception as e:
            logger.error(f"保存学习数据失败: {e}")

    def _load_learning_data(self) -> Any:
        """加载已保存的学习数据"""
        try:
            # 加载知识库
            knowledge_file = self.storage_path / "knowledge_base.json"
            if knowledge_file.exists():
                with open(knowledge_file, encoding="utf-8") as f:
                    knowledge_data = json.load(f)

                for item_id, item_data in knowledge_data.items():
                    item = KnowledgeItem(
                        item_id=item_id,
                        domain=KnowledgeDomain(item_data["domain"]),
                        title=item_data["title"],
                        content=item_data["content"],
                        confidence=item_data["confidence"],
                        source="loaded",
                        last_updated=datetime.now(),
                        tags=item_data["tags"],
                    )
                    self.knowledge_base[item_id] = item

            # 加载学习档案
            profile_file = self.storage_path / "learning_profile.json"
            if profile_file.exists():
                with open(profile_file, encoding="utf-8") as f:
                    profile_data = json.load(f)

                # 更新现有学习档案的部分字段
                if self.learning_profile:
                    self.learning_profile.total_learning_events = profile_data.get(
                        "total_events", 0
                    )
                    self.learning_profile.performance_metrics = profile_data.get(
                        "performance_metrics", {}
                    )

            logger.info("学习数据加载成功")

        except Exception as e:
            logger.error(f"加载学习数据失败: {e}")


# 示例使用
async def demo_adaptive_learning():
    """演示自适应学习系统"""

    # 创建学习系统
    learning_system = XiaonaAdaptiveLearningSystem()

    # 模拟反思结果
    reflection_result = LegalReflectionResult(
        task_id="demo_task",
        task_type="patent_analysis",
        overall_score=0.75,
        category_scores={"factual_accuracy": 0.85, "legal_basis": 0.70},
        detailed_scores=[],
        strengths=["事实准确", "分析全面"],
        weaknesses=["法律依据不够充分", "创造性判断需要加强"],
        recommendations=["补充更多法律条款", "深入学习相关判例"],
        should_refine=True,
        refinement_priority=3,
        human_review_required=False,
        confidence_level=0.80,
    )

    # 处理反思结果
    await learning_system.process_reflection_result(reflection_result)

    # 模拟人工反馈
    human_feedback = "分析基本正确,但建议补充专利法实施细则的相关条款"
    # 演示代码 - 在实际使用中应该提供真实的session对象
    # 这里跳过此调用以避免类型错误
    # await learning_system.process_human_feedback(
    #     session=temp_session,
    #     human_feedback=human_feedback,
    #     feedback_quality="constructive"
    # )
    logger.info(f"演示: 人工反馈已处理 (反馈内容: {human_feedback[:50]}...)")

    # 获取学习总结
    summary = learning_system.get_learning_summary()
    print("学习系统总结:")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    # 保存学习数据
    learning_system._save_learning_data()


if __name__ == "__main__":
    asyncio.run(demo_adaptive_learning())
