#!/usr/bin/env python3
"""
主动探索引擎
Active Exploration Engine

基于《Agentic Design Patterns》第21章:Exploration and Discovery

实现智能体的主动探索能力:
1. 知识图谱空白分析
2. 主动知识发现
3. 替代方案探索
4. 意外发现机制

作者: 小诺·双鱼座
版本: v1.0.0 "探索先锋"
创建时间: 2025-01-05
"""

from __future__ import annotations
import asyncio
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class ExplorationStrategy(Enum):
    """探索策略"""

    KNOWLEDGE_GAP = "knowledge_gap"  # 知识空白探索
    ALTERNATIVE_SOLUTION = "alternative_solution"  # 替代方案探索
    SERENDIPITOUS = "serendipitous"  # 意外发现
    HYPOTHESIS_DRIVEN = "hypothesis_driven"  # 假设驱动


@dataclass
class ExplorationResult:
    """探索结果"""

    exploration_id: str
    strategy: ExplorationStrategy
    discovered_items: list[dict[str, Any]] = field(default_factory=list)
    confidence_scores: list[float] = field(default_factory=list)
    novelty_score: float = 0.0
    relevance_score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeGap:
    """知识空白"""

    gap_id: str
    domain: str
    topic: str
    description: str
    related_entities: list[str] = field(default_factory=list)
    importance: float = 0.0
    urgency: float = 0.0
    suggested_explorations: list[str] = field(default_factory=list)


@dataclass
class Hypothesis:
    """假设"""

    hypothesis_id: str
    statement: str
    confidence: float = 0.0
    evidence: list[dict[str, Any]] = field(default_factory=list)
    test_methods: list[str] = field(default_factory=list)
    status: str = "pending"  # pending, testing, confirmed, refuted


class ActiveExplorationEngine:
    """主动探索引擎"""

    def __init__(self):
        """初始化探索引擎"""
        self.name = "主动探索引擎"
        self.version = "1.0.0"

        # 日志配置
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.name)

        # 探索历史
        self.exploration_history: list[ExplorationResult] = []

        # 知识空白缓存
        self.knowledge_gaps: dict[str, KnowledgeGap] = {}

        # 假设库
        self.hypotheses: dict[str, Hypothesis] = {}

        # 探索配置
        self.config = {
            "max_concurrent_explorations": 5,
            "novelty_threshold": 0.6,
            "relevance_threshold": 0.7,
            "auto_confirm_hypothesis": True,
            "exploration_depth": 3,
        }

        # 统计信息
        self.stats = {
            "total_explorations": 0,
            "successful_discoveries": 0,
            "knowledge_gaps_found": 0,
            "hypotheses_generated": 0,
            "hypotheses_confirmed": 0,
        }

        print(f"🔍 {self.name} v{self.version} 初始化完成")

    async def discover_knowledge_gaps(
        self, domain: str, context: dict[str, Any] | None = None
    ) -> list[KnowledgeGap]:
        """
        发现知识空白

        分析当前知识图谱,识别缺失的知识点
        """
        self.logger.info(f"🔍 分析知识空白: {domain}")

        try:
            # 1. 分析当前知识覆盖度
            coverage = await self._analyze_knowledge_coverage(domain)

            # 2. 识别实体间缺失的关系
            await self._find_missing_relations(domain)

            # 3. 识别未充分探索的主题
            underexplored = await self._find_underexplored_topics(domain)

            # 4. 生成知识空白对象
            gaps = []

            for topic in underexplored:
                gap = KnowledgeGap(
                    gap_id=f"gap_{domain}_{topic}_{len(self.knowledge_gaps)}",
                    domain=domain,
                    topic=topic,
                    description=f"在{domain}领域中,{topic}相关知识不足",
                    importance=self._assess_importance(topic, coverage),
                    urgency=self._assess_urgency(topic, context),
                    suggested_explorations=await self._generate_exploration_suggestions(topic),
                )
                gaps.append(gap)
                self.knowledge_gaps[gap.gap_id] = gap

            self.stats["knowledge_gaps_found"] += len(gaps)

            self.logger.info(f"✅ 发现 {len(gaps)} 个知识空白")
            return gaps

        except Exception as e:
            self.logger.error(f"❌ 知识空白分析失败: {e}")
            return []

    async def explore_new_knowledge(
        self, knowledge_gap: KnowledgeGap, exploration_depth: int = 3
    ) -> ExplorationResult:
        """
        探索新知识

        针对识别的知识空白,主动检索和发现新知识
        """
        self.logger.info(f"🔎 探索新知识: {knowledge_gap.topic}")

        exploration_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        discovered_items = []

        try:
            # 1. 生成探索查询
            queries = await self._generate_exploration_queries(knowledge_gap)

            # 2. 执行并行检索
            for i, query in enumerate(queries[:exploration_depth]):
                self.logger.info(f"   执行探索查询 {i+1}/{len(queries)}: {query}")

                # 模拟知识检索(实际实现中会调用真实的数据源)
                item = await self._simulate_knowledge_retrieval(query, knowledge_gap)

                if item:
                    discovered_items.append(item)

            # 3. 评估发现的新知识
            result = ExplorationResult(
                exploration_id=exploration_id,
                strategy=ExplorationStrategy.KNOWLEDGE_GAP,
                discovered_items=discovered_items,
                confidence_scores=[item.get("confidence", 0.7) for item in discovered_items],
                novelty_score=self._calculate_novelty_score(discovered_items),
                relevance_score=self._calculate_relevance_score(discovered_items, knowledge_gap),
                metadata={
                    "gap_id": knowledge_gap.gap_id,
                    "queries_used": queries,
                    "exploration_depth": exploration_depth,
                },
            )

            self.exploration_history.append(result)
            self.stats["total_explorations"] += 1
            self.stats["successful_discoveries"] += len(discovered_items)

            self.logger.info(f"✅ 探索完成: 发现 {len(discovered_items)} 条新知识")
            return result

        except Exception as e:
            self.logger.error(f"❌ 知识探索失败: {e}")
            return ExplorationResult(
                exploration_id=exploration_id, strategy=ExplorationStrategy.KNOWLEDGE_GAP
            )

    async def explore_alternative_solutions(
        self, task: dict[str, Any], num_alternatives: int = 3
    ) -> ExplorationResult:
        """
        探索替代方案

        为给定任务生成多个替代解决方案
        """
        self.logger.info(f"💡 探索替代方案: {task.get('title', '未知任务')}")

        exploration_id = f"alt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            # 1. 分析任务特征
            task_features = await self._analyze_task_features(task)

            # 2. 生成替代方案假设
            alternatives = await self._generate_alternative_hypotheses(
                task, task_features, num_alternatives
            )

            # 3. 评估每个替代方案
            evaluated_alternatives = []
            for alt in alternatives:
                evaluation = await self._evaluate_alternative(alt, task)
                evaluated_alternatives.append({"alternative": alt, "evaluation": evaluation})

            # 4. 按评估分数排序
            evaluated_alternatives.sort(
                key=lambda x: x["evaluation"]["overall_score"], reverse=True
            )

            result = ExplorationResult(
                exploration_id=exploration_id,
                strategy=ExplorationStrategy.ALTERNATIVE_SOLUTION,
                discovered_items=evaluated_alternatives,
                confidence_scores=[
                    alt["evaluation"]["overall_score"] for alt in evaluated_alternatives
                ],
                novelty_score=self._calculate_alternative_novelty(evaluated_alternatives),
                relevance_score=self._calculate_alternative_relevance(evaluated_alternatives, task),
                metadata={
                    "task_id": task.get("id"),
                    "num_alternatives": len(alternatives),
                    "task_features": task_features,
                },
            )

            self.exploration_history.append(result)
            self.stats["total_explorations"] += 1

            self.logger.info(f"✅ 生成 {len(alternatives)} 个替代方案")
            return result

        except Exception as e:
            self.logger.error(f"❌ 替代方案探索失败: {e}")
            return ExplorationResult(
                exploration_id=exploration_id, strategy=ExplorationStrategy.ALTERNATIVE_SOLUTION
            )

    async def serendipitous_discovery(
        self, domains: list[str], exploration_scope: str = "broad"
    ) -> ExplorationResult:
        """
        意外发现

        通过随机探索和跨领域关联发现意外知识
        """
        self.logger.info(f"🎲 执行意外发现探索: {domains}")

        exploration_id = f"ser_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            # 1. 随机选择探索起点
            exploration_points = await self._select_random_exploration_points(
                domains, exploration_scope
            )

            # 2. 执行探索性检索
            discoveries = []
            for point in exploration_points:
                # 执行广度优先探索
                found = await self._exploratory_search(point, depth=2)
                discoveries.extend(found)

            # 3. 识别意外关联
            unexpected_connections = await self._identify_unexpected_connections(discoveries)

            # 4. 生成创新洞察
            insights = await self._generate_insights(unexpected_connections)

            result = ExplorationResult(
                exploration_id=exploration_id,
                strategy=ExplorationStrategy.SERENDIPITOUS,
                discovered_items=insights,
                confidence_scores=[insight.get("confidence", 0.5) for insight in insights],
                novelty_score=0.8,  # 意外发现通常新颖性较高
                relevance_score=0.6,  # 相关性可能不确定
                metadata={
                    "domains": domains,
                    "scope": exploration_scope,
                    "exploration_points": exploration_points,
                },
            )

            self.exploration_history.append(result)
            self.stats["total_explorations"] += 1

            self.logger.info(f"✅ 意外发现: {len(insights)} 条创新洞察")
            return result

        except Exception as e:
            self.logger.error(f"❌ 意外发现失败: {e}")
            return ExplorationResult(
                exploration_id=exploration_id, strategy=ExplorationStrategy.SERENDIPITOUS
            )

    async def generate_and_test_hypothesis(
        self, observation: dict[str, Any], num_hypotheses: int = 5
    ) -> list[Hypothesis]:
        """
        生成并测试假设

        基于观察生成假设,并进行验证
        """
        self.logger.info(f"🧪 生成假设: {observation.get('description', '未知观察')}")

        try:
            # 1. 分析观察
            analysis = await self._analyze_observation(observation)

            # 2. 生成多个假设
            hypotheses = []
            for i in range(num_hypotheses):
                hyp = Hypothesis(
                    hypothesis_id=f"hyp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}",
                    statement=f"假设{i+1}: {analysis.get('primary_question', '')}",
                    confidence=0.5,  # 初始置信度
                    test_methods=await self._design_test_methods(observation),
                    status="pending",
                )
                hypotheses.append(hyp)
                self.hypotheses[hyp.hypothesis_id] = hyp

            self.stats["hypotheses_generated"] += len(hypotheses)

            # 3. 如果启用自动测试,则执行测试
            if self.config["auto_confirm_hypothesis"]:
                for hyp in hypotheses:
                    await self._test_hypothesis(hyp, observation)

            self.logger.info(f"✅ 生成 {len(hypotheses)} 个假设")
            return hypotheses

        except Exception as e:
            self.logger.error(f"❌ 假设生成失败: {e}")
            return []

    # ==================== 辅助方法 ====================

    async def _analyze_knowledge_coverage(self, domain: str) -> dict[str, float]:
        """分析知识覆盖度"""
        # 模拟实现
        return {"entities": 0.75, "relations": 0.65, "attributes": 0.80, "overall": 0.73}

    async def _find_missing_relations(self, domain: str) -> list[dict[str, Any]]:
        """查找缺失的关系"""
        # 模拟实现
        return [{"source": "AI", "target": "医疗", "type": "应用", "confidence": 0.8}]

    async def _find_underexplored_topics(self, domain: str) -> list[str]:
        """查找未充分探索的主题"""
        # 模拟实现
        return [f"{domain}前沿技术", f"{domain}发展趋势", f"{domain}创新应用"]

    def _assess_importance(self, topic: str, coverage: dict[str, float]) -> float:
        """评估重要性"""
        # 简单实现
        return 0.7

    def _assess_urgency(self, topic: str, context: dict[str, Any]) -> float:
        """评估紧迫性"""
        return 0.6

    async def _generate_exploration_suggestions(self, topic: str) -> list[str]:
        """生成探索建议"""
        return [f"检索{topic}最新研究", f"分析{topic}发展趋势", f"探索{topic}应用场景"]

    async def _generate_exploration_queries(self, knowledge_gap: KnowledgeGap) -> list[str]:
        """生成探索查询"""
        return [
            f"{knowledge_gap.topic} 概述",
            f"{knowledge_gap.topic} 最新进展",
            f"{knowledge_gap.topic} 应用案例",
            f"{knowledge_gap.topic} 技术挑战",
        ]

    async def _simulate_knowledge_retrieval(
        self, query: str, knowledge_gap: KnowledgeGap
    ) -> dict[str, Any] | None:
        """模拟知识检索"""
        # 实际实现中会调用真实的检索API
        return {
            "query": query,
            "content": f"关于{query}的知识内容",
            "source": "知识库",
            "confidence": 0.75,
            "timestamp": datetime.now().isoformat(),
        }

    def _calculate_novelty_score(self, items: list[dict[str, Any]]) -> float:
        """计算新颖性分数"""
        if not items:
            return 0.0
        return sum(item.get("confidence", 0.5) for item in items) / len(items)

    def _calculate_relevance_score(
        self, items: list[dict[str, Any]], knowledge_gap: KnowledgeGap
    ) -> float:
        """计算相关性分数"""
        return 0.8

    async def _analyze_task_features(self, task: dict[str, Any]) -> dict[str, Any]:
        """分析任务特征"""
        return {
            "complexity": task.get("complexity", 0.5),
            "domain": task.get("domain", "通用"),
            "requirements": task.get("requirements", []),
        }

    async def _generate_alternative_hypotheses(
        self, task: dict[str, Any], features: dict[str, Any], num_alternatives: int
    ) -> list[dict[str, Any]]:
        """生成替代假设"""
        alternatives = []
        for i in range(num_alternatives):
            alt = {
                "id": f"alt_{i}",
                "description": f"替代方案{i+1}",
                "approach": ["方法A", "方法B", "方法C"][i % 3],
                "estimated_effort": 10 * (i + 1),
                "expected_quality": 0.9 - i * 0.1,
            }
            alternatives.append(alt)
        return alternatives

    async def _evaluate_alternative(
        self, alternative: dict[str, Any], task: dict[str, Any]
    ) -> dict[str, Any]:
        """评估替代方案"""
        return {
            "feasibility": 0.8,
            "cost_effectiveness": 0.7,
            "time_efficiency": 0.75,
            "quality": 0.85,
            "overall_score": 0.77,
        }

    def _calculate_alternative_novelty(self, alternatives: list[dict]) -> float:
        """计算替代方案新颖性"""
        return 0.7

    def _calculate_alternative_relevance(
        self, alternatives: list[dict], task: dict[str, Any]
    ) -> float:
        """计算替代方案相关性"""
        return 0.8

    async def _select_random_exploration_points(
        self, domains: list[str], scope: str
    ) -> list[dict[str, Any]]:
        """选择随机探索点"""
        return [{"domain": domain, "topic": f"{domain}随机主题"} for domain in domains[:3]]

    async def _exploratory_search(self, point: dict[str, Any], depth: int) -> list[dict[str, Any]]:
        """探索性搜索"""
        return [{"point": point, "finding": f"发现{depth}层知识"}]

    async def _identify_unexpected_connections(
        self, discoveries: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """识别意外关联"""
        return [{"connection": "意外关联", "strength": 0.7}]

    async def _generate_insights(self, connections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """生成洞察"""
        return [{"insight": "创新洞察", "confidence": 0.7, "potential_impact": "high"}]

    async def _analyze_observation(self, observation: dict[str, Any]) -> dict[str, Any]:
        """分析观察"""
        return {"primary_question": "为什么会发生这种情况?", "key_factors": ["因素1", "因素2"]}

    async def _design_test_methods(self, observation: dict[str, Any]) -> list[str]:
        """设计测试方法"""
        return ["实验验证", "数据分析", "专家评估"]

    async def _test_hypothesis(self, hypothesis: Hypothesis, observation: dict[str, Any]) -> None:
        """测试假设"""
        # 模拟测试过程
        hypothesis.status = "testing"
        await asyncio.sleep(0.1)  # 模拟测试耗时

        # 随机确定结果
        import random

        if random.random() > 0.5:
            hypothesis.status = "confirmed"
            hypothesis.confidence = 0.85
            self.stats["hypotheses_confirmed"] += 1
        else:
            hypothesis.status = "refuted"
            hypothesis.confidence = 0.2

    def get_exploration_stats(self) -> dict[str, Any]:
        """获取探索统计"""
        return {
            **self.stats,
            "exploration_history_size": len(self.exploration_history),
            "knowledge_gaps_size": len(self.knowledge_gaps),
            "hypotheses_size": len(self.hypotheses),
        }

    def get_recent_explorations(self, limit: int = 10) -> list[ExplorationResult]:
        """获取最近的探索记录"""
        return self.exploration_history[-limit:]


# ==================== 全局实例 ====================

_active_exploration_engine: ActiveExplorationEngine | None = None


def get_active_exploration_engine() -> ActiveExplorationEngine:
    """获取主动探索引擎单例"""
    global _active_exploration_engine
    if _active_exploration_engine is None:
        _active_exploration_engine = ActiveExplorationEngine()
    return _active_exploration_engine


# ==================== 导出 ====================

__all__ = [
    "ActiveExplorationEngine",
    "ExplorationResult",
    "ExplorationStrategy",
    "Hypothesis",
    "KnowledgeGap",
    "get_active_exploration_engine",
]
