#!/usr/bin/env python3
from __future__ import annotations
"""
规划知识库
Planning Knowledge Base

功能:
1. 存储规划历史和经验
2. 管理最佳实践
3. 支持案例检索
4. 提供知识查询

Author: Athena Team
Version: 1.0.0
Date: 2026-02-24
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from .multi_plan_generator import PlanStrategy
from .plan_evaluator import PlanEvaluation
from .xiaonuo_planner_engine import ExecutionPlan, Intent, IntentType

logger = logging.getLogger(__name__)


class CaseType(Enum):
    """案例类型"""
    SUCCESS = "success"  # 成功案例
    FAILURE = "failure"  # 失败案例
    OPTIMIZED = "optimized"  # 优化案例


@dataclass
class PlanningCase:
    """规划案例"""
    case_id: str
    intent_type: IntentType
    user_input: str
    strategy_used: PlanStrategy
    plan: ExecutionPlan
    evaluation: PlanEvaluation | None = None
    case_type: CaseType = CaseType.SUCCESS
    lessons_learned: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class BestPractice:
    """最佳实践"""
    practice_id: str
    title: str
    description: str
    applicable_scenarios: list[str]
    implementation: str
    expected_benefit: str
    confidence: float  # 0-1
    source_case_ids: list[str] = field(default_factory=list)


@dataclass
class KnowledgeQuery:
    """知识查询"""
    query_id: str
    query_type: str  # similar_cases/best_practice/lessons_learned
    query_params: dict[str, Any]
    results: list[Any]
    timestamp: datetime = field(default_factory=datetime.now)


class PlanningKnowledgeBase:
    """
    规划知识库

    核心功能:
    1. 案例存储与检索
    2. 最佳实践管理
    3. 经验教训提取
    4. 智能知识查询
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.storage_path = storage_path or "data/planning_knowledge.json"

        # 知识存储
        self.cases: list[PlanningCase] = []
        self.best_practices: list[BestPractice] = []
        self.query_history: list[KnowledgeQuery] = []

        # 知识索引
        self.intent_type_index: dict[IntentType, list[str]] = {}  # intent -> case_ids
        self.strategy_index: dict[PlanStrategy, list[str]] = {}  # strategy -> case_ids
        self.tag_index: dict[str, list[str]] = {}  # tag -> case_ids

        self._load_knowledge()

        self.logger.info("📚 规划知识库初始化完成")

    def _load_knowledge(self) -> None:
        """加载知识库"""
        try:
            with open(self.storage_path, encoding="utf-8") as f:
                data = json.load(f)

                # 加载案例
                for case_data in data.get("cases", []):
                    case = self._deserialize_case(case_data)
                    self.cases.append(case)
                    self._index_case(case)

                # 加载最佳实践
                for practice_data in data.get("best_practices", []):
                    practice = BestPractice(
                        practice_id=practice_data["practice_id"],
                        title=practice_data["title"],
                        description=practice_data["description"],
                        applicable_scenarios=practice_data["applicable_scenarios"],
                        implementation=practice_data["implementation"],
                        expected_benefit=practice_data["expected_benefit"],
                        confidence=practice_data["confidence"],
                        source_case_ids=practice_data.get("source_case_ids", []),
                    )
                    self.best_practices.append(practice)

                # 加载查询历史
                for query_data in data.get("query_history", []):
                    query = KnowledgeQuery(
                        query_id=query_data["query_id"],
                        query_type=query_data["query_type"],
                        query_params=query_data["query_params"],
                        results=query_data["results"],
                        timestamp=datetime.fromisoformat(query_data["timestamp"]) if query_data.get("timestamp") else datetime.now(),
                    )
                    self.query_history.append(query)

                self.logger.info(f"   📂 加载 {len(self.cases)} 个案例, {len(self.best_practices)} 个最佳实践")
        except FileNotFoundError:
            self.logger.info("   📂 未找到知识库文件，创建新的")
        except Exception as e:
            self.logger.warning(f"   ⚠️ 加载知识库失败: {e}")

    def _save_knowledge(self) -> None:
        """保存知识库"""
        try:
            Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)

            data = {
                "cases": [self._serialize_case(c) for c in self.cases],
                "best_practices": [
                    {
                        "practice_id": p.practice_id,
                        "title": p.title,
                        "description": p.description,
                        "applicable_scenarios": p.applicable_scenarios,
                        "implementation": p.implementation,
                        "expected_benefit": p.expected_benefit,
                        "confidence": p.confidence,
                        "source_case_ids": p.source_case_ids,
                    }
                    for p in self.best_practices
                ],
                "query_history": [
                    {
                        "query_id": q.query_id,
                        "query_type": q.query_type,
                        "query_params": q.query_params,
                        "results": q.results,
                        "timestamp": q.timestamp.isoformat(),
                    }
                    for q in self.query_history[-100:]  # 只保存最近100条
                ],
                "last_updated": datetime.now().isoformat(),
            }

            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"   ❌ 保存知识库失败: {e}")

    def _serialize_case(self, case: PlanningCase) -> dict[str, Any]:
        """序列化案例"""
        return {
            "case_id": case.case_id,
            "intent_type": case.intent_type.value,
            "user_input": case.user_input,
            "strategy_used": case.strategy_used.value,
            "plan": {
                "plan_id": case.plan.plan_id,
                "mode": case.plan.mode.value,
                "steps_count": len(case.plan.steps),
                "estimated_time": case.plan.estimated_time,
                "confidence": case.plan.confidence.value,
            },
            "evaluation": {
                "evaluation_id": case.evaluation.evaluation_id,
                "overall_score": case.evaluation.overall_score,
                "grade": case.evaluation.grade,
            } if case.evaluation else None,
            "case_type": case.case_type.value,
            "lessons_learned": case.lessons_learned,
            "tags": case.tags,
            "created_at": case.created_at.isoformat(),
        }

    def _deserialize_case(self, data: dict[str, Any]) -> PlanningCase:
        """反序列化案例"""
        # 创建简化的 ExecutionPlan
        from .xiaonuo_planner_engine import ExecutionMode, PlanConfidence

        plan = ExecutionPlan(
            plan_id=data["plan"]["plan_id"],
            intent=Intent(
                intent_type=IntentType(data["intent_type"]),
                primary_goal=data["user_input"][:50],
            ),
            steps=[],  # 简化，不存储完整步骤
            mode=ExecutionMode(data["plan"]["mode"]),
            estimated_time=data["plan"]["estimated_time"],
            confidence=PlanConfidence(data["plan"]["confidence"]),
        )

        # 创建简化的评估
        evaluation = None
        if data.get("evaluation"):
            evaluation = PlanEvaluation(
                evaluation_id=data["evaluation"]["evaluation_id"],
                plan_id=data["plan"]["plan_id"],
                overall_score=data["evaluation"]["overall_score"],
                dimension_scores=[],
                grade=data["evaluation"]["grade"],
                strengths=[],
                weaknesses=[],
                optimization_opportunities=[],
            )

        return PlanningCase(
            case_id=data["case_id"],
            intent_type=IntentType(data["intent_type"]),
            user_input=data["user_input"],
            strategy_used=PlanStrategy(data["strategy_used"]),
            plan=plan,
            evaluation=evaluation,
            case_type=CaseType(data["case_type"]),
            lessons_learned=data.get("lessons_learned", []),
            tags=data.get("tags", []),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
        )

    def _index_case(self, case: PlanningCase) -> None:
        """为案例建立索引"""
        # 意图类型索引
        if case.intent_type not in self.intent_type_index:
            self.intent_type_index[case.intent_type] = []
        self.intent_type_index[case.intent_type].append(case.case_id)

        # 策略索引
        if case.strategy_used not in self.strategy_index:
            self.strategy_index[case.strategy_used] = []
        self.strategy_index[case.strategy_used].append(case.case_id)

        # 标签索引
        for tag in case.tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = []
            self.tag_index[tag].append(case.case_id)

    def add_case(
        self,
        intent: Intent,
        user_input: str,
        strategy: PlanStrategy,
        plan: ExecutionPlan,
        evaluation: PlanEvaluation | None = None,
        lessons_learned: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
    ) -> PlanningCase:
        """添加案例"""
        case_id = f"case_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 确定案例类型
        if evaluation:
            if evaluation.overall_score >= 0.8:
                case_type = CaseType.SUCCESS
            elif evaluation.overall_score < 0.6:
                case_type = CaseType.FAILURE
            else:
                case_type = CaseType.OPTIMIZED
        else:
            case_type = CaseType.SUCCESS

        case = PlanningCase(
            case_id=case_id,
            intent_type=intent.intent_type,
            user_input=user_input,
            strategy_used=strategy,
            plan=plan,
            evaluation=evaluation,
            case_type=case_type,
            lessons_learned=lessons_learned or [],
            tags=tags or [],
        )

        self.cases.append(case)
        self._index_case(case)
        self._save_knowledge()

        self.logger.info(f"📚 添加案例: {case_id} - {case_type.value}")

        return case

    def query_similar_cases(
        self,
        intent_type: IntentType,
        strategy: PlanStrategy | None = None,
        tags: Optional[list[str]] = None,
        limit: int = 5,
    ) -> list[PlanningCase]:
        """查询相似案例"""
        # 从意图类型索引开始
        candidate_ids = set(self.intent_type_index.get(intent_type, []))

        # 策略过滤
        if strategy:
            strategy_ids = set(self.strategy_index.get(strategy, []))
            candidate_ids = candidate_ids.intersection(strategy_ids)

        # 标签过滤
        if tags:
            tag_ids = set()
            for tag in tags:
                tag_ids.update(self.tag_index.get(tag, []))
            candidate_ids = candidate_ids.intersection(tag_ids) if tag_ids else candidate_ids

        # 获取案例
        cases = [c for c in self.cases if c.case_id in candidate_ids]

        # 按评分排序
        cases_with_score = [(c, c.evaluation.overall_score if c.evaluation else 0.5) for c in cases]
        cases_with_score.sort(key=lambda x: x[1], reverse=True)

        results = [c for c, _ in cases_with_score[:limit]]

        # 记录查询
        query = KnowledgeQuery(
            query_id=f"query_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            query_type="similar_cases",
            query_params={
                "intent_type": intent_type.value,
                "strategy": strategy.value if strategy else None,
                "tags": tags,
                "limit": limit,
            },
            results=[c.case_id for c in results],
        )
        self.query_history.append(query)

        return results

    def get_best_practices(
        self,
        scenario: Optional[str] = None,
        intent_type: IntentType | None = None,
        limit: int = 5,
    ) -> list[BestPractice]:
        """获取最佳实践"""
        practices = self.best_practices

        # 场景过滤
        if scenario:
            practices = [p for p in practices if scenario in p.applicable_scenarios]

        # 按置信度排序
        practices.sort(key=lambda p: p.confidence, reverse=True)

        return practices[:limit]

    def extract_lessons_from_evaluation(
        self,
        evaluation: PlanEvaluation,
        plan: ExecutionPlan
    ) -> list[str]:
        """从评估中提取经验教训"""
        lessons = []

        # 从优势中提取
        for strength in evaluation.strengths:
            if "优秀" in strength:
                lessons.append(f"保持优势: {strength}")

        # 从劣势中提取
        for weakness in evaluation.weaknesses:
            if "需改进" in weakness:
                lessons.append(f"需要改进: {weakness}")

        # 从优化机会中提取
        for opportunity in evaluation.optimization_opportunities:
            lessons.append(f"优化建议: {opportunity}")

        return lessons

    def add_best_practice(
        self,
        title: str,
        description: str,
        applicable_scenarios: list[str],
        implementation: str,
        expected_benefit: str,
        confidence: float,
        source_case_ids: Optional[list[str]] = None,
    ) -> BestPractice:
        """添加最佳实践"""
        practice = BestPractice(
            practice_id=f"practice_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title=title,
            description=description,
            applicable_scenarios=applicable_scenarios,
            implementation=implementation,
            expected_benefit=expected_benefit,
            confidence=confidence,
            source_case_ids=source_case_ids or [],
        )

        self.best_practices.append(practice)
        self._save_knowledge()

        self.logger.info(f"💡 添加最佳实践: {title}")

        return practice

    def get_statistics(self) -> dict[str, Any]:
        """获取知识库统计"""
        case_type_counts = {}
        for case in self.cases:
            case_type_counts[case.case_type.value] = case_type_counts.get(case.case_type.value, 0) + 1

        intent_type_counts = {}
        for case in self.cases:
            intent_type_counts[case.intent_type.value] = intent_type_counts.get(case.intent_type.value, 0) + 1

        return {
            "total_cases": len(self.cases),
            "total_best_practices": len(self.best_practices),
            "total_queries": len(self.query_history),
            "case_type_distribution": case_type_counts,
            "intent_type_distribution": intent_type_counts,
            "average_case_score": sum(
                c.evaluation.overall_score for c in self.cases if c.evaluation
            ) / len([c for c in self.cases if c.evaluation]) if self.cases else 0,
        }

    def search_lessons_learned(
        self,
        intent_type: IntentType | None = None,
        case_type: CaseType | None = None,
        limit: int = 10,
    ) -> list[str]:
        """搜索经验教训"""
        all_lessons = []

        for case in self.cases:
            # 过滤条件
            if intent_type and case.intent_type != intent_type:
                continue
            if case_type and case.case_type != case_type:
                continue

            all_lessons.extend(case.lessons_learned)

        # 去重并限制数量
        unique_lessons = list(dict.fromkeys(all_lessons))  # 保持顺序的去重

        return unique_lessons[:limit]
