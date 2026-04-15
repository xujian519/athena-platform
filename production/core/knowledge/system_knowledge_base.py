#!/usr/bin/env python3
"""
系统知识库建设
System Knowledge Base Builder

建立Athena平台的知识库系统:
- 决策案例库
- 最佳实践库
- 问题解决模式库
- 经验教训库

作者: 小诺·双鱼公主
创建时间: 2025-12-27
版本: v1.0.0 "知识库建设"
"""

from __future__ import annotations
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class KnowledgeType(Enum):
    """知识类型"""

    DECISION_CASE = "decision_case"  # 决策案例
    BEST_PRACTICE = "best_practice"  # 最佳实践
    PROBLEM_PATTERN = "problem_pattern"  # 问题模式
    LESSON_LEARNED = "lesson_learned"  # 经验教训
    ARCHITECTURE_PATTERN = "architecture_pattern"  # 架构模式


class KnowledgeCategory(Enum):
    """知识分类"""

    SYSTEM_ARCHITECTURE = "system_architecture"
    DECISION_MAKING = "decision_making"
    AGENT_COORDINATION = "agent_coordination"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    ERROR_HANDLING = "error_handling"
    USER_INTERACTION = "user_interaction"


@dataclass
class KnowledgeItem:
    """知识条目"""

    id: str
    type: KnowledgeType
    category: KnowledgeCategory
    title: str
    description: str
    content: dict[str, Any]
    tags: list[str] = field(default_factory=list)
    confidence: float = 1.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = "system"
    usage_count: int = 0
    effectiveness_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type.value,
            "category": self.category.value,
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "tags": self.tags,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "source": self.source,
            "usage_count": self.usage_count,
            "effectiveness_score": self.effectiveness_score,
        }

    def generate_id(self) -> str:
        """生成唯一ID"""
        content_str = f"{self.type.value}_{self.category.value}_{self.title}_{self.created_at}"
        return hashlib.md5(content_str.encode(), usedforsecurity=False).hexdigest()


class SystemKnowledgeBase:
    """
    系统知识库

    存储和管理平台的知识资产
    """

    def __init__(self, storage_path: Path | None = None):
        """初始化知识库"""
        self.storage_path = storage_path or Path("/Users/xujian/Athena工作平台/knowledge_base")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # 知识存储
        self.knowledge: dict[str, KnowledgeItem] = {}

        # 索引
        self.type_index: dict[KnowledgeType, list[str]] = {}
        self.category_index: dict[KnowledgeCategory, list[str]] = {}
        self.tag_index: dict[str, list[str]] = {}

        # 加载已有知识
        self._load_knowledge()

        logger.info("📚 系统知识库初始化完成")
        logger.info(f"   存储路径: {self.storage_path}")
        logger.info(f"   已加载知识: {len(self.knowledge)}条")

    def _load_knowledge(self) -> Any:
        """加载已有知识"""
        # 从JSON文件加载
        for kb_file in self.storage_path.glob("*.json"):
            try:
                with open(kb_file, encoding="utf-8") as f:
                    data = json.load(f)
                    item = KnowledgeItem(**data)
                    self._add_to_index(item)
                    self.knowledge[item.id] = item
            except Exception as e:
                logger.warning(f"加载知识失败 {kb_file}: {e}")

    def _add_to_index(self, item: KnowledgeItem) -> Any:
        """添加到索引"""
        # 类型索引
        if item.type not in self.type_index:
            self.type_index[item.type] = []
        self.type_index[item.type].append(item.id)

        # 分类索引
        if item.category not in self.category_index:
            self.category_index[item.category] = []
        self.category_index[item.category].append(item.id)

        # 标签索引
        for tag in item.tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = []
            self.tag_index[tag].append(item.id)

    def add_knowledge(
        self,
        knowledge_type: KnowledgeType,
        category: KnowledgeCategory,
        title: str,
        description: str,
        content: dict[str, Any],
        tags: list[str] | None = None,
        confidence: float = 1.0,
    ) -> KnowledgeItem:
        """
        添加知识

        Args:
            knowledge_type: 知识类型
            category: 知识分类
            title: 标题
            description: 描述
            content: 内容
            tags: 标签
            confidence: 置信度

        Returns:
            KnowledgeItem: 知识条目
        """
        item = KnowledgeItem(
            id="",
            type=knowledge_type,
            category=category,
            title=title,
            description=description,
            content=content,
            tags=tags or [],
            confidence=confidence,
        )

        # 生成ID
        item.id = item.generate_id()

        # 添加到索引
        self._add_to_index(item)

        # 存储知识
        self.knowledge[item.id] = item

        # 保存到文件
        self._save_knowledge(item)

        logger.info(f"✅ 添加知识: {item.id} - {title}")
        return item

    def _save_knowledge(self, item: KnowledgeItem) -> Any:
        """保存知识到文件"""
        file_path = self.storage_path / f"{item.id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(item.to_dict(), f, ensure_ascii=False, indent=2)

    def search(
        self,
        query: str,
        knowledge_type: KnowledgeType | None = None,
        category: KnowledgeCategory | None = None,
        tags: list[str] | None = None,
    ) -> list[KnowledgeItem]:
        """
        搜索知识

        Args:
            query: 搜索关键词
            knowledge_type: 知识类型过滤
            category: 分类过滤
            tags: 标签过滤

        Returns:
            匹配的知识列表
        """
        results = []

        for item in self.knowledge.values():
            # 类型过滤
            if knowledge_type and item.type != knowledge_type:
                continue

            # 分类过滤
            if category and item.category != category:
                continue

            # 标签过滤
            if tags and not any(tag in item.tags for tag in tags):
                continue

            # 关键词匹配
            query_lower = query.lower()
            if (
                query_lower in item.title.lower()
                or query_lower in item.description.lower()
                or any(query_lower in str(v).lower() for v in item.content.values())
            ):
                results.append(item)

        # 按使用次数和效果分数排序
        results.sort(key=lambda x: (x.usage_count, x.effectiveness_score), reverse=True)

        return results

    def get_best_practices(
        self, category: KnowledgeCategory | None = None, limit: int = 10
    ) -> list[KnowledgeItem]:
        """获取最佳实践"""
        items = [
            item
            for item in self.knowledge.values()
            if item.type == KnowledgeType.BEST_PRACTICE
            and (category is None or item.category == category)
        ]

        items.sort(key=lambda x: x.effectiveness_score, reverse=True)
        return items[:limit]

    def get_decision_cases(
        self, category: KnowledgeCategory | None = None, limit: int = 10
    ) -> list[KnowledgeItem]:
        """获取决策案例"""
        items = [
            item
            for item in self.knowledge.values()
            if item.type == KnowledgeType.DECISION_CASE
            and (category is None or item.category == category)
        ]

        items.sort(key=lambda x: x.usage_count, reverse=True)
        return items[:limit]

    def record_usage(self, item_id: str, effectiveness: float | None = None) -> Any:
        """记录知识使用"""
        if item_id in self.knowledge:
            item = self.knowledge[item_id]
            item.usage_count += 1

            if effectiveness is not None:
                # 更新效果分数(移动平均)
                current_score = item.effectiveness_score
                if current_score == 0:
                    item.effectiveness_score = effectiveness
                else:
                    item.effectiveness_score = current_score * 0.8 + effectiveness * 0.2

            item.updated_at = datetime.now().isoformat()

            # 保存更新
            self._save_knowledge(item)

            logger.info(f"📊 记录知识使用: {item_id}")

    def initialize_from_system_optimization(self) -> Any:
        """从系统优化中初始化知识库"""
        logger.info("🔧 从系统优化中初始化知识库...")

        # 添加系统架构知识
        self.add_knowledge(
            knowledge_type=KnowledgeType.ARCHITECTURE_PATTERN,
            category=KnowledgeCategory.SYSTEM_ARCHITECTURE,
            title="四层系统架构模式",
            description="Athena平台采用的四层架构:决策层、应用层、服务层、基础设施层",
            content={
                "layers": [
                    "第4层:决策协调层(总体设计部)",
                    "第3层:应用服务层(智能体)",
                    "第2层:业务服务层(服务)",
                    "第1层:基础设施层(数据库/缓存)",
                ],
                "benefits": ["清晰的职责分离", "灵活的扩展能力", "便于维护和优化"],
            },
            tags=["architecture", "layers", "design"],
            confidence=0.95,
        )

        # 添加决策方法知识
        self.add_knowledge(
            knowledge_type=KnowledgeType.BEST_PRACTICE,
            category=KnowledgeCategory.DECISION_MAKING,
            title="从定性到定量的综合集成法",
            description="基于钱学森系统工程思想的决策方法",
            content={
                "steps": [
                    "第1步:定性判断方向",
                    "第2步:组织专家会诊",
                    "第3步:综合集成迭代",
                    "第4步:给出明确决策",
                ],
                "applicable_scenarios": ["多智能体意见冲突", "复杂技术选型", "需要综合考量的问题"],
            },
            tags=["decision", "systems_engineering", "methodology"],
            confidence=0.98,
        )

        # 添加智能体协同知识
        self.add_knowledge(
            knowledge_type=KnowledgeType.BEST_PRACTICE,
            category=KnowledgeCategory.AGENT_COORDINATION,
            title="智能体协同模式选择指南",
            description="根据任务特点选择合适的协同模式",
            content={
                "modes": {
                    "PARALLEL": {
                        "description": "并行执行",
                        "best_for": "独立任务,可以同时执行",
                        "efficiency": "高",
                    },
                    "SEQUENTIAL": {
                        "description": "顺序执行",
                        "best_for": "有依赖关系的任务",
                        "efficiency": "中",
                    },
                    "PIPELINE": {
                        "description": "流水线执行",
                        "best_for": "输出作为下个输入",
                        "efficiency": "高",
                    },
                    "COLLABORATIVE": {
                        "description": "协作执行",
                        "best_for": "需要互相调整的任务",
                        "efficiency": "中高",
                    },
                }
            },
            tags=["collaboration", "agents", "optimization"],
            confidence=0.92,
        )

        logger.info("✅ 系统优化知识初始化完成")

    def get_statistics(self) -> dict[str, Any]:
        """获取知识库统计"""
        type_dist = {}
        for item in self.knowledge.values():
            t = item.type.value
            type_dist[t] = type_dist.get(t, 0) + 1

        category_dist = {}
        for item in self.knowledge.values():
            c = item.category.value
            category_dist[c] = category_dist.get(c, 0) + 1

        return {
            "total_knowledge": len(self.knowledge),
            "type_distribution": type_dist,
            "category_distribution": category_dist,
            "total_tags": len(self.tag_index),
            "average_usage": (
                sum(item.usage_count for item in self.knowledge.values()) / len(self.knowledge)
                if self.knowledge
                else 0
            ),
            "average_effectiveness": (
                sum(item.effectiveness_score for item in self.knowledge.values())
                / len(self.knowledge)
                if self.knowledge
                else 0
            ),
        }

    @classmethod
    async def initialize_global(cls):
        """初始化全局实例"""
        global _knowledge_base
        if _knowledge_base is None:
            _knowledge_base = cls()
        return _knowledge_base

    @classmethod
    async def shutdown_global(cls):
        """关闭全局实例"""
        global _knowledge_base
        _knowledge_base = None


# 全局实例
_knowledge_base: SystemKnowledgeBase | None = None


def get_knowledge_base() -> SystemKnowledgeBase:
    """获取知识库单例"""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = SystemKnowledgeBase()
        # 初始化系统优化知识
        _knowledge_base.initialize_from_system_optimization()
    return _knowledge_base


# 便捷函数
def add_best_practice(
    title: str,
    description: str,
    content: dict[str, Any],    category: KnowledgeCategory = KnowledgeCategory.SYSTEM_ARCHITECTURE,
) -> str:
    """便捷函数:添加最佳实践"""
    kb = get_knowledge_base()
    item = kb.add_knowledge(
        knowledge_type=KnowledgeType.BEST_PRACTICE,
        category=category,
        title=title,
        description=description,
        content=content,
    )
    return item.id


def search_knowledge(query: str, **filters) -> list[KnowledgeItem]:
    """便捷函数:搜索知识"""
    kb = get_knowledge_base()
    return kb.search(query, **filters)


if __name__ == "__main__":
    # 测试知识库
    print("🧪 测试系统知识库")
    print("=" * 70)

    kb = get_knowledge_base()

    # 查看统计
    stats = kb.get_statistics()
    print("\n📊 知识库统计:")
    print(f"   总知识数: {stats['total_knowledge']}")
    print(f"   类型分布: {stats['type_distribution']}")
    print(f"   分类分布: {stats['category_distribution']}")
    print(f"   平均使用: {stats['average_usage']:.2f}次")
    print(f"   平均效果: {stats['average_effectiveness']:.2f}")

    # 搜索知识
    print("\n🔍 搜索'决策':")
    results = kb.search("决策")
    for item in results[:3]:
        print(f"   - {item.title}: {item.description[:60]}...")

    # 获取最佳实践
    print("\n⭐ 最佳实践:")
    practices = kb.get_best_practices(limit=3)
    for item in practices:
        print(f"   - {item.title}")
        print(f"     {item.description[:60]}...")
