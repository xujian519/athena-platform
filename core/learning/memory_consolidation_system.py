#!/usr/bin/env python3
"""
记忆整合系统 - Memory Consolidation System
实现短期记忆向长期知识的转化

核心功能:
1. 经验整合 - 将学习经验转化为知识
2. 模式识别 - 识别重复模式并提取规则
3. 知识固化 - 将重要经验存入永恒记忆
4. 遗忘管理 - 清理过时或低质量记忆

作者: Athena平台团队
创建时间: 2026-01-23
版本: v1.0.0
"""

import asyncio
import hashlib
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from core.logging_config import setup_logging

logger = setup_logging()


class ConsolidationPriority(Enum):
    """整合优先级"""

    CRITICAL = "critical"  # 关键(立即整合)
    HIGH = "high"  # 高优先级
    MEDIUM = "medium"  # 中等优先级
    LOW = "low"  # 低优先级


@dataclass
class ConsolidationCandidate:
    """整合候选"""

    memory_id: str
    content: str
    importance: float
    access_count: int
    last_accessed: datetime
    creation_time: datetime
    consolidation_score: float = 0.0
    priority: ConsolidationPriority = ConsolidationPriority.MEDIUM


@dataclass
class PatternInsight:
    """模式洞察"""

    pattern_id: str
    pattern_type: str  # 'temporal', 'semantic', 'causal'
    description: str
    confidence: float
    examples: list[str]
    extraction_time: datetime


@dataclass
class ConsolidationReport:
    """整合报告"""

    timestamp: datetime
    total_candidates: int
    consolidated_count: int
    patterns_discovered: list[PatternInsight]
    knowledge_items_created: list[dict[str, Any]]
    memories_forgotten: list[str]
    processing_time: float


class MemoryConsolidationSystem:
    """
    记忆整合系统

    负责将短期记忆转化为长期知识,实现:
    - 经验 → 知识的转化
    - 模式识别与提取
    - 知识图谱更新
    - 遗忘曲线管理
    """

    def __init__(self, agent_id: str, memory_system=None):
        self.agent_id = agent_id
        self.memory_system = memory_system

        # 整合配置
        self.consolidation_threshold = 0.75  # 整合阈值
        self.consolidation_interval = timedelta(hours=6)  # 整合间隔
        self.last_consolidation = datetime.now()

        # 优先级阈值
        self.priority_thresholds = {
            ConsolidationPriority.CRITICAL: 0.95,
            ConsolidationPriority.HIGH: 0.85,
            ConsolidationPriority.MEDIUM: 0.75,
            ConsolidationPriority.LOW: 0.65,
        }

        # 遗忘曲线参数(艾宾浩斯遗忘曲线)
        self.forgetting_curve = {
            1: 0.84,  # 20分钟后
            2: 0.67,  # 1小时后
            3: 0.50,  # 1天后
            4: 0.30,  # 6天后
            5: 0.25,  # 31天后
        }

        # 统计信息
        self.stats = {
            "total_consolidations": 0,
            "patterns_discovered": 0,
            "knowledge_items_created": 0,
            "memories_forgotten": 0,
            "total_processing_time": 0.0,
        }

        # 模式检测器
        self.pattern_detector = PatternDetector()

        logger.info(f"🧠 记忆整合系统初始化: {agent_id}")

    async def consolidate_memories(self, force: bool = False) -> dict[str, Any]:
        """
        执行记忆整合

        Args:
            force: 是否强制执行(忽略时间间隔)

        Returns:
            整合报告
        """
        # 检查是否需要整合
        if not force and not self._should_consolidate():
            return {
                "status": "skipped",
                "reason": "距离上次整合时间不足",
                "next_consolidation": (
                    self.last_consolidation + self.consolidation_interval
                ).isoformat(),
            }

        logger.info("🔄 开始记忆整合...")
        start_time = datetime.now()

        # 1. 获取整合候选记忆
        candidates = await self._get_consolidation_candidates()

        if not candidates:
            logger.info("没有需要整合的记忆")
            return {"status": "completed", "consolidated_count": 0, "message": "没有需要整合的记忆"}

        # 2. 识别模式
        patterns = await self.pattern_detector.detect_patterns(candidates)

        # 3. 整合高重要性记忆
        knowledge_created = []
        consolidated_count = 0

        for candidate in candidates:
            if candidate.consolidation_score >= self.consolidation_threshold:
                # 转化为知识项
                knowledge_item = await self._create_knowledge_item(candidate)
                knowledge_created.append(knowledge_item)
                consolidated_count += 1

        # 4. 执行遗忘清理
        forgotten = await self._perform_forgetting()

        # 5. 更新统计
        processing_time = (datetime.now() - start_time).total_seconds()
        self.stats["total_consolidations"] += 1
        self.stats["patterns_discovered"] += len(patterns)
        self.stats["knowledge_items_created"] += len(knowledge_created)
        self.stats["memories_forgotten"] += len(forgotten)
        self.stats["total_processing_time"] += processing_time

        self.last_consolidation = datetime.now()

        # 构建报告
        report = {
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "total_candidates": len(candidates),
            "consolidated_count": consolidated_count,
            "patterns_discovered": len(patterns),
            "patterns": [
                {"type": p.pattern_type, "description": p.description, "confidence": p.confidence}
                for p in patterns
            ],
            "knowledge_created": len(knowledge_created),
            "memories_forgotten": len(forgotten),
            "processing_time": processing_time,
            "next_consolidation": (
                self.last_consolidation + self.consolidation_interval
            ).isoformat(),
        }

        logger.info(f"✅ 记忆整合完成: {consolidated_count}项, 耗时{processing_time:.2f}s")

        return report

    def _should_consolidate(self) -> bool:
        """检查是否应该执行整合"""
        return (datetime.now() - self.last_consolidation) >= self.consolidation_interval

    async def _get_consolidation_candidates(self) -> list[ConsolidationCandidate]:
        """获取整合候选记忆"""
        candidates = []

        # 如果有记忆系统,从系统获取
        if self.memory_system:
            try:
                # 获取最近的情景记忆
                recent_memories = await self._fetch_recent_memories(limit=100)

                for memory in recent_memories:
                    # 计算整合分数
                    consolidation_score = self._calculate_consolidation_score(memory)

                    # 确定优先级
                    priority = self._determine_priority(consolidation_score)

                    candidate = ConsolidationCandidate(
                        memory_id=memory.get("id", self._generate_id()),
                        content=memory.get("content", ""),
                        importance=memory.get("importance", 0.5),
                        access_count=memory.get("access_count", 0),
                        last_accessed=memory.get("last_accessed", datetime.now()),
                        creation_time=memory.get("created_at", datetime.now()),
                        consolidation_score=consolidation_score,
                        priority=priority,
                    )

                    candidates.append(candidate)
            except Exception as e:
                logger.warning(f"从记忆系统获取候选失败: {e}")

        # 按整合分数和优先级排序
        candidates.sort(
            key=lambda x: (
                -len(
                    [
                        p
                        for p in self.priority_thresholds
                        if x.consolidation_score >= self.priority_thresholds[p]
                    ]
                ),
                -x.consolidation_score,
            )
        )

        return candidates

    def _calculate_consolidation_score(self, memory: dict[str, Any]) -> float:
        """
        计算整合分数

        综合考虑:
        - 重要性权重 (40%)
        - 访问频率 (30%)
        - 时间衰减 (20%)
        - 情感权重 (10%)
        """
        importance = memory.get("importance", 0.5)
        access_count = memory.get("access_count", 0)
        created_at = memory.get("created_at", datetime.now())
        emotional_weight = memory.get("emotional_weight", 0.5)

        # 1. 重要性权重(40%)
        importance_score = importance * 0.4

        # 2. 访问频率(30%)
        access_score = min(access_count / 10.0, 1.0) * 0.3

        # 3. 时间衰减(20%)
        time_diff = (datetime.now() - created_at).total_seconds() / 3600  # 小时
        time_score = max(0, 1 - time_diff / 24) * 0.2  # 24小时内线性衰减

        # 4. 情感权重(10%)
        emotion_score = emotional_weight * 0.1

        total_score = importance_score + access_score + time_score + emotion_score

        return min(total_score, 1.0)

    def _determine_priority(self, score: float) -> ConsolidationPriority:
        """确定整合优先级"""
        if score >= self.priority_thresholds[ConsolidationPriority.CRITICAL]:
            return ConsolidationPriority.CRITICAL
        elif score >= self.priority_thresholds[ConsolidationPriority.HIGH]:
            return ConsolidationPriority.HIGH
        elif score >= self.priority_thresholds[ConsolidationPriority.MEDIUM]:
            return ConsolidationPriority.MEDIUM
        else:
            return ConsolidationPriority.LOW

    async def _create_knowledge_item(self, candidate: ConsolidationCandidate) -> dict[str, Any]:
        """从记忆创建知识项"""
        knowledge_item = {
            "id": f"knowledge_{candidate.memory_id}",
            "content": candidate.content,
            "type": "consolidated_knowledge",
            "importance": candidate.importance,
            "source_memory": candidate.memory_id,
            "priority": candidate.priority.value,
            "created_at": datetime.now().isoformat(),
            "access_count": candidate.access_count,
            "consolidation_score": candidate.consolidation_score,
        }

        # 存储到记忆系统(如果可用)
        if self.memory_system:
            try:
                # 导入必要的类型
                from core.memory.unified_agent_memory_system import MemoryType

                await self.memory_system.store_memory(
                    agent_id=self.agent_id,
                    agent_type="xiaonuo",
                    content=knowledge_item["content"],
                    memory_type=MemoryType.KNOWLEDGE,  # 知识记忆(语义记忆)
                    importance=knowledge_item["importance"],
                    emotional_weight=0.7,
                    work_related=True,
                    family_related=False,
                    tags=["consolidated", "knowledge", candidate.priority.value],
                    metadata={
                        "source": "consolidation",
                        "original_memory": candidate.memory_id,
                        "consolidation_score": candidate.consolidation_score,
                    },
                )
            except Exception as e:
                logger.warning(f"存储知识项失败: {e}")

        return knowledge_item

    async def _perform_forgetting(self) -> list[str]:
        """
        执行遗忘清理

        基于艾宾浩斯遗忘曲线,清理长期未访问的低重要性记忆
        """
        forgotten_ids = []

        if self.memory_system:
            try:
                # 获取需要评估的记忆
                memories_to_evaluate = await self._fetch_memories_for_forgetting()

                for memory in memories_to_evaluate:
                    # 计算遗忘概率
                    retention_probability = self._calculate_retention_probability(memory)

                    # 如果保留概率低于阈值,执行遗忘
                    if retention_probability < 0.3:  # 30%阈值
                        try:
                            # 从记忆系统中删除
                            await self.memory_system.delete_memory(
                                agent_id=self.agent_id, memory_id=memory["id"]
                            )
                            forgotten_ids.append(memory["id"])
                        except Exception as e:
                            logger.warning(f"删除记忆失败 {memory['id']}: {e}")

                self.stats["memories_forgotten"] += len(forgotten_ids)

            except Exception as e:
                logger.warning(f"执行遗忘失败: {e}")

        return forgotten_ids

    def _calculate_retention_probability(self, memory: dict[str, Any]) -> float:
        """
        计算记忆保留概率

        基于艾宾浩斯遗忘曲线 + 访问历史
        """
        created_at = memory.get("created_at", datetime.now())
        access_count = memory.get("access_count", 0)
        importance = memory.get("importance", 0.5)

        # 计算时间间隔(天)
        time_diff = (datetime.now() - created_at).total_seconds() / 86400

        # 查找遗忘曲线上的基准保留率
        base_retention = 0.25  # 默认31天后的保留率

        for day, retention in self.forgetting_curve.items():
            if time_diff <= day:
                base_retention = retention
                break

        # 访问增强:每次访问增强保留率
        access_bonus = min(access_count * 0.1, 0.5)

        # 重要性增强
        importance_bonus = importance * 0.3

        # 总保留率
        total_retention = min(base_retention + access_bonus + importance_bonus, 1.0)

        return total_retention

    async def _fetch_recent_memories(self, limit: int = 100) -> list[dict[str, Any]]:
        """获取最近的记忆"""
        if not self.memory_system:
            return []

        try:
            # 尝试从记忆系统获取
            # 这里需要根据实际的记忆系统API调整
            memories = []

            # 如果记忆系统有获取方法
            if hasattr(self.memory_system, "get_recent_memories"):
                memories = await self.memory_system.get_recent_memories(
                    agent_id=self.agent_id, limit=limit
                )

            return memories

        except Exception as e:
            logger.warning(f"获取最近记忆失败: {e}")
            return []

    async def _fetch_memories_for_forgetting(self) -> list[dict[str, Any]]:
        """获取需要遗忘评估的记忆"""
        if not self.memory_system:
            return []

        try:
            # 获取30天前的记忆
            cutoff_date = datetime.now() - timedelta(days=30)
            memories = []

            # 如果记忆系统有查询方法
            if hasattr(self.memory_system, "get_memories_before_date"):
                memories = await self.memory_system.get_memories_before_date(
                    agent_id=self.agent_id, date=cutoff_date
                )

            return memories

        except Exception as e:
            logger.warning(f"获取遗忘候选记忆失败: {e}")
            return []

    def _generate_id(self) -> str:
        """生成唯一ID"""
        return hashlib.md5(f"{datetime.now().isoformat()}_{id(self)}".encode()).hexdigest()[:16]

    async def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "agent_id": self.agent_id,
            "stats": self.stats,
            "config": {
                "consolidation_threshold": self.consolidation_threshold,
                "consolidation_interval_hours": self.consolidation_interval.total_seconds() / 3600,
                "last_consolidation": self.last_consolidation.isoformat(),
                "next_consolidation": (
                    self.last_consolidation + self.consolidation_interval
                ).isoformat(),
            },
        }


class PatternDetector:
    """模式检测器 - 从记忆中识别模式"""

    def __init__(self):
        self.pattern_types = [
            "temporal",  # 时间模式(每天/每周/每月)
            "semantic",  # 语义模式(相似内容)
            "causal",  # 因果模式(A导致B)
        ]

        # 模式检测配置
        self.min_pattern_occurrences = 3  # 最少出现次数
        self.similarity_threshold = 0.8  # 相似度阈值

    async def detect_patterns(
        self, candidates: list[ConsolidationCandidate]
    ) -> list[PatternInsight]:
        """检测记忆中的模式"""
        patterns = []

        if len(candidates) < self.min_pattern_occurrences:
            return patterns

        # 1. 时间模式检测
        temporal_patterns = await self._detect_temporal_patterns(candidates)
        patterns.extend(temporal_patterns)

        # 2. 语义模式检测
        semantic_patterns = await self._detect_semantic_patterns(candidates)
        patterns.extend(semantic_patterns)

        # 3. 因果模式检测(简化版)
        # causal_patterns = await self._detect_causal_patterns(candidates)
        # patterns.extend(causal_patterns)

        return patterns

    async def _detect_temporal_patterns(
        self, candidates: list[ConsolidationCandidate]
    ) -> list[PatternInsight]:
        """检测时间模式"""
        patterns = []

        try:
            # 按小时分组
            hour_groups = defaultdict(list)
            for candidate in candidates:
                hour = candidate.creation_time.hour
                hour_groups[hour].append(candidate)

            # 识别高峰时段
            for hour, group in hour_groups.items():
                if len(group) >= self.min_pattern_occurrences:
                    pattern = PatternInsight(
                        pattern_id=f"temporal_hour_{hour}",
                        pattern_type="temporal",
                        description=f"每天{hour}时段有{len(group)}条记忆",
                        confidence=0.7,
                        examples=[c.content[:50] for c in group[:3]],
                        extraction_time=datetime.now(),
                    )
                    patterns.append(pattern)

        except Exception as e:
            logger.warning(f"时间模式检测失败: {e}")

        return patterns

    async def _detect_semantic_patterns(
        self, candidates: list[ConsolidationCandidate]
    ) -> list[PatternInsight]:
        """检测语义模式"""
        patterns = []

        try:
            # 简化的关键词检测
            keyword_groups = defaultdict(list)

            for candidate in candidates:
                # 提取关键词(简化版)
                words = candidate.content.split()
                for word in words:
                    if len(word) >= 2:  # 至少2个字符
                        keyword_groups[word].append(candidate)

            # 识别高频关键词
            for keyword, group in keyword_groups.items():
                if len(group) >= self.min_pattern_occurrences:
                    pattern = PatternInsight(
                        pattern_id=f"semantic_keyword_{keyword}",
                        pattern_type="semantic",
                        description=f"关键词'{keyword}'出现{len(group)}次",
                        confidence=0.6,
                        examples=[c.content[:50] for c in group[:3]],
                        extraction_time=datetime.now(),
                    )
                    patterns.append(pattern)

        except Exception as e:
            logger.warning(f"语义模式检测失败: {e}")

        return patterns


@dataclass
class ConsolidationStrategy:
    """整合策略配置"""

    name: str
    consolidation_threshold: float = 0.75
    priority_weight: float = 0.5
    temporal_weight: float = 0.3
    access_weight: float = 0.2
    enable_forgetting: bool = True
    forgetting_threshold: float = 0.3
    min_pattern_occurrences: int = 3


__all__ = [
    "ConsolidationCandidate",
    "ConsolidationPriority",
    "ConsolidationReport",
    "ConsolidationStrategy",
    "MemoryConsolidationSystem",
    "PatternDetector",
    "PatternInsight",
    "test_consolidation_system",
]


# 测试和实用函数
async def test_consolidation_system():
    """测试记忆整合系统"""
    logger.info("🧪 测试记忆整合系统...")

    # 创建整合系统
    consolidation_system = MemoryConsolidationSystem(agent_id="xiaonuo_test")

    # 执行整合
    report = await consolidation_system.consolidate_memories(force=True)

    print(f"整合报告: {report}")
    print(f"统计信息: {await consolidation_system.get_statistics()}")

    return consolidation_system


if __name__ == "__main__":
    # 配置日志
    # setup_logging()  # 日志配置已移至模块导入

    # 运行测试
    asyncio.run(test_consolidation_system())
