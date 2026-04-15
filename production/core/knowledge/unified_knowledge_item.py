#!/usr/bin/env python3
"""
统一知识条目数据模型
Unified Knowledge Item Data Model

基于乔布斯产品哲学的知识条目定义:
- 极简主义:清晰的数据结构
- 质量优先:严格的质量控制字段
- 用户体验:便于检索和展示

作者: 小诺·双鱼公主
创建时间: 2025-12-27
版本: v1.0.0 "质量控制"
"""

from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class QualityLevel(Enum):
    """知识质量等级

    基于乔布斯"只保留最高质量知识"的理念,
    将知识分为四个等级,严格控制入库标准。
    """

    DRAFT = 0  # 草稿 - 待审核,不对外展示
    REVIEWED = 1  # 已审核 - 质量合格,可检索
    APPROVED = 2  # 已批准 - 高质量,优先推荐
    EXCELLENT = 3  # 优秀 - 核心知识,置顶展示

    def __str__(self) -> str:
        return self.name

    def get_label(self) -> Any | None:
        """获取中文标签"""
        labels = {
            QualityLevel.DRAFT: "草稿",
            QualityLevel.REVIEWED: "已审核",
            QualityLevel.APPROVED: "已批准",
            QualityLevel.EXCELLENT: "优秀",
        }
        return labels[self]

    def get_color(self) -> Any | None:
        """获取展示颜色(用于Web UI)"""
        colors = {
            QualityLevel.DRAFT: "#999999",  # 灰色
            QualityLevel.REVIEWED: "#3498db",  # 蓝色
            QualityLevel.APPROVED: "#2ecc71",  # 绿色
            QualityLevel.EXCELLENT: "#f39c12",  # 金色
        }
        return colors[self]


class KnowledgeType(Enum):
    """知识类型"""

    DECISION_CASE = "decision_case"  # 决策案例
    BEST_PRACTICE = "best_practice"  # 最佳实践
    PROBLEM_PATTERN = "problem_pattern"  # 问题模式
    LESSON_LEARNED = "lesson_learned"  # 经验教训
    ARCHITECTURE_PATTERN = "architecture_pattern"  # 架构模式
    API_REFERENCE = "api_reference"  # API参考
    DEPLOYMENT_GUIDE = "deployment_guide"  # 部署指南
    TROUBLESHOOTING = "troubleshooting"  # 故障排查


class KnowledgeCategory(Enum):
    """知识分类"""

    SYSTEM_ARCHITECTURE = "system_architecture"
    DECISION_MAKING = "decision_making"
    AGENT_COORDINATION = "agent_coordination"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    ERROR_HANDLING = "error_handling"
    USER_INTERACTION = "user_interaction"
    DEPLOYMENT = "deployment"
    INTEGRATION = "integration"


@dataclass
class QualityMetrics:
    """质量指标

    用于AI辅助质量评分的详细指标
    """

    completeness: float = 0.0  # 完整性 (0-1) - 30%
    accuracy: float = 0.0  # 准确性 (0-1) - 30%
    usefulness: float = 0.0  # 实用性 (0-1) - 25%
    clarity: float = 0.0  # 清晰度 (0-1) - 15%

    def calculate_total_score(self) -> float:
        """计算总评分(加权平均)"""
        return (
            self.completeness * 0.30
            + self.accuracy * 0.30
            + self.usefulness * 0.25
            + self.clarity * 0.15
        )

    def to_dict(self) -> dict[str, float]:
        """转换为字典"""
        return {
            "completeness": self.completeness,
            "accuracy": self.accuracy,
            "usefulness": self.usefulness,
            "clarity": self.clarity,
            "total_score": self.calculate_total_score(),
        }


@dataclass
class UnifiedKnowledgeItem:
    """统一知识条目

    基于现有KnowledgeItem扩展,增加质量控制字段
    """

    # ===== 基础标识 =====
    id: str
    type: KnowledgeType
    category: KnowledgeCategory
    title: str
    description: str
    content: dict[str, Any]
    # ===== 质量控制(核心!) =====
    quality_level: QualityLevel = QualityLevel.DRAFT
    quality_metrics: QualityMetrics = field(default_factory=QualityMetrics)
    ai_quality_score: float = 0.0  # AI辅助评分 (0-1)
    reviewed_by: str = ""  # 审核人("爸爸")
    reviewed_at: datetime | None = None
    review_notes: str = ""  # 审核意见

    # ===== 原有字段(保留兼容) =====
    confidence: float = 1.0
    tags: list[str] = field(default_factory=list)
    source: str = "manual"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # ===== 使用统计 =====
    usage_count: int = 0
    effectiveness_score: float = 0.0
    last_accessed_at: datetime | None = None

    # ===== 图谱关联 =====
    nebula_node_id: str | None = None
    qdrant_point_id: str | None = None

    def __post_init__(self):
        """初始化后处理"""
        if self.id == "":
            self.id = self.generate_id()

    def generate_id(self) -> str:
        """生成唯一ID"""
        content_str = (
            f"{self.type.value}_{self.category.value}_{self.title}_{self.created_at.isoformat()}"
        )
        return hashlib.md5(content_str.encode(), usedforsecurity=False).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            # 基础标识
            "id": self.id,
            "type": self.type.value,
            "category": self.category.value,
            "title": self.title,
            "description": self.description,
            "content": self.content,
            # 质量控制
            "quality_level": self.quality_level.value,
            "quality_metrics": self.quality_metrics.to_dict(),
            "ai_quality_score": self.ai_quality_score,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "review_notes": self.review_notes,
            # 原有字段
            "confidence": self.confidence,
            "tags": self.tags,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            # 使用统计
            "usage_count": self.usage_count,
            "effectiveness_score": self.effectiveness_score,
            "last_accessed_at": (
                self.last_accessed_at.isoformat() if self.last_accessed_at else None
            ),
            # 图谱关联
            "nebula_node_id": self.nebula_node_id,
            "qdrant_point_id": self.qdrant_point_id,
        }

    def to_summary_dict(self) -> dict[str, Any]:
        """转换为摘要字典(用于列表展示)"""
        return {
            "id": self.id,
            "title": self.title,
            "description": (
                self.description[:100] + "..." if len(self.description) > 100 else self.description
            ),
            "type": self.type.value,
            "category": self.category.value,
            "quality_level": self.quality_level.value,
            "quality_level_label": self.quality_level.get_label(),
            "quality_level_color": self.quality_level.get_color(),
            "ai_quality_score": self.ai_quality_score,
            "tags": self.tags,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat(),
            "reviewed_by": self.reviewed_by,
        }

    def approve(self, reviewer: str, quality_level: QualityLevel, notes: str = "") -> Any:
        """批准知识

        Args:
            reviewer: 审核人(如"爸爸")
            quality_level: 质量等级
            notes: 审核意见
        """
        self.quality_level = quality_level
        self.reviewed_by = reviewer
        self.reviewed_at = datetime.now()
        self.review_notes = notes
        self.updated_at = datetime.now()

    def reject(self, reviewer: str, notes: str = "") -> Any:
        """拒绝知识

        Args:
            reviewer: 审核人
            notes: 拒绝原因
        """
        self.quality_level = QualityLevel.DRAFT
        self.reviewed_by = reviewer
        self.reviewed_at = datetime.now()
        self.review_notes = f"拒绝: {notes}"
        self.updated_at = datetime.now()

    def is_approved(self) -> bool:
        """是否已批准(可对外展示)"""
        return self.quality_level in [
            QualityLevel.REVIEWED,
            QualityLevel.APPROVED,
            QualityLevel.EXCELLENT,
        ]

    def is_excellent(self) -> bool:
        """是否为优秀知识(置顶推荐)"""
        return self.quality_level == QualityLevel.EXCELLENT

    def record_usage(self, effectiveness: float | None = None) -> Any:
        """记录使用

        Args:
            effectiveness: 有效性评分 (0-1)
        """
        self.usage_count += 1
        self.last_accessed_at = datetime.now()

        if effectiveness is not None:
            # 更新效果分数(移动平均)
            if self.effectiveness_score == 0:
                self.effectiveness_score = effectiveness
            else:
                self.effectiveness_score = self.effectiveness_score * 0.8 + effectiveness * 0.2

        self.updated_at = datetime.now()


def create_knowledge_item(
    title: str,
    description: str,
    content: dict[str, Any],    knowledge_type: KnowledgeType,
    category: KnowledgeCategory,
    tags: list[str] | None = None,
    source: str = "manual",
) -> UnifiedKnowledgeItem:
    """便捷函数:创建知识条目

    Args:
        title: 标题
        description: 描述
        content: 内容
        knowledge_type: 知识类型
        category: 知识分类
        tags: 标签
        source: 来源

    Returns:
        UnifiedKnowledgeItem: 知识条目
    """
    return UnifiedKnowledgeItem(
        id="",
        type=knowledge_type,
        category=category,
        title=title,
        description=description,
        content=content,
        tags=tags or [],
        source=source,
    )


if __name__ == "__main__":
    # 测试数据模型
    print("🧪 测试统一知识条目数据模型")
    print("=" * 80)

    # 创建一个知识条目
    item = create_knowledge_item(
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
        knowledge_type=KnowledgeType.ARCHITECTURE_PATTERN,
        category=KnowledgeCategory.SYSTEM_ARCHITECTURE,
        tags=["architecture", "layers", "design"],
        source="system",
    )

    print("\n📝 知识条目创建成功:")
    print(f"   ID: {item.id}")
    print(f"   标题: {item.title}")
    print(f"   类型: {item.type.value}")
    print(f"   分类: {item.category.value}")
    print(f"   质量等级: {item.quality_level.get_label()}")
    print(f"   标签: {', '.join(item.tags)}")

    # 模拟AI质量评分
    print("\n🤖 AI质量评分:")
    item.quality_metrics.completeness = 0.9
    item.quality_metrics.accuracy = 0.95
    item.quality_metrics.usefulness = 0.88
    item.quality_metrics.clarity = 0.92
    item.ai_quality_score = item.quality_metrics.calculate_total_score()

    metrics = item.quality_metrics.to_dict()
    print(f"   完整性 (30%): {metrics['completeness']:.2f}")
    print(f"   准确性 (30%): {metrics['accuracy']:.2f}")
    print(f"   实用性 (25%): {metrics['usefulness']:.2f}")
    print(f"   清晰度 (15%): {metrics['clarity']:.2f}")
    print(f"   总评分: {metrics['total_score']:.2f}")

    # 模拟人工审核
    print("\n✅ 人工审核:")
    item.approve(
        reviewer="爸爸",
        quality_level=QualityLevel.EXCELLENT,
        notes="核心架构知识,质量优秀,必须保留!",
    )

    print(f"   审核人: {item.reviewed_by}")
    print(f"   审核时间: {item.reviewed_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   质量等级: {item.quality_level.get_label()}")
    print(f"   审核意见: {item.review_notes}")

    # 模拟使用记录
    print("\n📊 使用记录:")
    item.record_usage(effectiveness=0.95)
    print(f"   使用次数: {item.usage_count}")
    print(f"   有效性评分: {item.effectiveness_score:.2f}")
    print(f"   最后访问: {item.last_accessed_at.strftime('%Y-%m-%d %H:%M:%S')}")

    # 输出完整字典
    print("\n📄 完整数据:")
    print(json.dumps(item.to_dict(), ensure_ascii=False, indent=2))

    print("\n✅ 测试完成!")
