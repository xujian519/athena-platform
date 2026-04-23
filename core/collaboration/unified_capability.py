#!/usr/bin/env python3
from __future__ import annotations
"""
统一智能体能力接口
Unified Agent Capability Interface

为了解决不同模块中AgentCapability定义不一致的问题,
提供统一的接口和适配器
"""

from dataclasses import dataclass, field
from datetime import timedelta
from enum import Enum
from typing import Any

from core.protocols.advanced_coordination import AgentCapability


class CapabilityType(Enum):
    """能力类型枚举"""

    ANALYSIS = "analysis"  # 分析能力
    PROCESSING = "processing"  # 处理能力
    COORDINATION = "coordination"  # 协调能力
    DECISION = "decision"  # 决策能力
    COMMUNICATION = "communication"  # 通信能力
    CREATIVE = "creative"  # 创造能力
    TECHNICAL = "technical"  # 技术能力
    MANAGEMENT = "management"  # 管理能力


@dataclass
class UnifiedAgentCapability:
    """统一的智能体能力描述"""

    # 基本信息
    name: str  # 能力名称
    description: str  # 能力描述
    type: CapabilityType  # 能力类型

    # 性能指标
    proficiency: float = 0.8  # 熟练度 (0.0-1.0)
    availability: float = 1.0  # 可用性 (0.0-1.0)
    reliability: float = 0.9  # 可靠性 (0.0-1.0)

    # 资源相关
    max_concurrent_tasks: int = 3  # 最大并发任务数
    estimated_duration: timedelta = timedelta(minutes=30)  # 预估执行时间
    cost_per_hour: float = 100.0  # 每小时成本
    resource_requirements: dict[str, Any] = field(default_factory=dict)  # 资源需求

    # 质量指标
    quality_metrics: dict[str, float] = field(default_factory=dict)  # 质量指标
    success_rate: float = 0.95  # 成功率
    average_rating: float = 4.5  # 平均评分 (1.0-5.0)

    # 专业知识
    specializations: list[str] = field(default_factory=list)  # 专业领域
    dependencies: set[str] = field(default_factory=set)  # 依赖的其他能力

    # 元数据
    metadata: dict[str, Any] = field(default_factory=dict)  # 其他元数据
    tags: set[str] = field(default_factory=set)  # 标签
    created_at: Optional[str] = None  # 创建时间
    updated_at: Optional[str] = None  # 更新时间

    def __post_init__(self):
        """初始化后处理"""
        if not self.created_at:
            from datetime import datetime

            self.created_at = datetime.now().isoformat()
            self.updated_at = self.created_at

        # 验证数值范围
        self.proficiency = max(0.0, min(1.0, self.proficiency))
        self.availability = max(0.0, min(1.0, self.availability))
        self.reliability = max(0.0, min(1.0, self.reliability))
        self.success_rate = max(0.0, min(1.0, self.success_rate))
        self.average_rating = max(1.0, min(5.0, self.average_rating))

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "type": self.type.value,
            "proficiency": self.proficiency,
            "availability": self.availability,
            "reliability": self.reliability,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "estimated_duration": str(self.estimated_duration),
            "cost_per_hour": self.cost_per_hour,
            "resource_requirements": self.resource_requirements,
            "quality_metrics": self.quality_metrics,
            "success_rate": self.success_rate,
            "average_rating": self.average_rating,
            "specializations": self.specializations,
            "dependencies": list(self.dependencies),
            "metadata": self.metadata,
            "tags": list(self.tags),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UnifiedAgentCapability:
        """从字典创建"""
        # 处理estimated_duration
        if isinstance(data.get("estimated_duration"), str):
            from datetime import timedelta

            # 简单解析,实际应用中可能需要更复杂的解析
            duration_str = data["estimated_duration"]
            if "day" in duration_str:
                days = int(duration_str.split(" ")[0])
                estimated_duration = timedelta(days=days)
            elif "hour" in duration_str:
                hours = int(duration_str.split(" ")[0])
                estimated_duration = timedelta(hours=hours)
            elif "minute" in duration_str:
                minutes = int(duration_str.split(" ")[0])
                estimated_duration = timedelta(minutes=minutes)
            else:
                estimated_duration = timedelta(minutes=30)
        else:
            estimated_duration = data.get("estimated_duration", timedelta(minutes=30))

        return cls(
            name=data["name"],
            description=data["description"],
            type=CapabilityType(data["type"]),
            proficiency=data.get("proficiency", 0.8),
            availability=data.get("availability", 1.0),
            reliability=data.get("reliability", 0.9),
            max_concurrent_tasks=data.get("max_concurrent_tasks", 3),
            estimated_duration=estimated_duration,
            cost_per_hour=data.get("cost_per_hour", 100.0),
            resource_requirements=data.get("resource_requirements", {}),
            quality_metrics=data.get("quality_metrics", {}),
            success_rate=data.get("success_rate", 0.95),
            average_rating=data.get("average_rating", 4.5),
            specializations=data.get("specializations", []),
            dependencies=set(data.get("dependencies", [])),
            metadata=data.get("metadata", {}),
            tags=set(data.get("tags", [])),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def calculate_score(self, requirements: dict[str, Any]) -> float:
        """计算能力匹配分数"""
        score = 0.0

        # 熟练度权重
        proficiency_weight = requirements.get("proficiency_weight", 0.4)
        score += self.proficiency * proficiency_weight

        # 可用性权重
        availability_weight = requirements.get("availability_weight", 0.2)
        score += self.availability * availability_weight

        # 成功率权重
        success_rate_weight = requirements.get("success_rate_weight", 0.3)
        score += self.success_rate * success_rate_weight

        # 成本权重(成本越低分数越高)
        cost_weight = requirements.get("cost_weight", 0.1)
        max_cost = requirements.get("max_cost", 1000.0)
        cost_score = max(0.0, 1.0 - (self.cost_per_hour / max_cost))
        score += cost_score * cost_weight

        return min(1.0, score)

    def is_available(self) -> bool:
        """检查能力是否可用"""
        return self.availability > 0.0 and self.proficiency > 0.3

    def can_handle(self, task_requirements: dict[str, Any]) -> bool:
        """检查是否能处理特定任务"""
        # 检查基本可用性
        if not self.is_available():
            return False

        # 检查技能匹配
        required_skills = task_requirements.get("required_skills", [])
        if required_skills:
            has_skills = any(skill in self.specializations for skill in required_skills)
            if not has_skills:
                return False

        # 检查熟练度要求
        min_proficiency = task_requirements.get("min_proficiency", 0.0)
        if self.proficiency < min_proficiency:
            return False

        # 检查并发任务限制
        max_concurrent = task_requirements.get("max_concurrent_tasks", self.max_concurrent_tasks)
        return not max_concurrent > self.max_concurrent_tasks

    def update(self, **kwargs) -> Any:
        """更新能力信息"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        # 更新时间戳
        from datetime import datetime

        self.updated_at = datetime.now().isoformat()


class CapabilityAdapter:
    """能力适配器,用于在不同模块间转换AgentCapability"""

    @staticmethod
    def from_collaboration_framework(cap) -> UnifiedAgentCapability:
        """从协作框架的AgentCapability转换"""
        # 确定能力类型
        type_mapping = {
            "task_planning": CapabilityType.TECHNICAL,
            "strategic_thinking": CapabilityType.DECISION,
            "patent_analysis": CapabilityType.ANALYSIS,
            "data_processing": CapabilityType.PROCESSING,
            "goal_management": CapabilityType.MANAGEMENT,
            "progress_tracking": CapabilityType.MANAGEMENT,
            "coordination": CapabilityType.COORDINATION,
            "collaboration": CapabilityType.COORDINATION,
        }

        cap_type = type_mapping.get(cap.name, CapabilityType.TECHNICAL)

        return UnifiedAgentCapability(
            name=cap.name,
            description=cap.description,
            type=cap_type,
            max_concurrent_tasks=cap.max_concurrent_tasks,
            estimated_duration=cap.estimated_duration,
            resource_requirements=cap.resource_requirements,
            dependencies=cap.dependencies,
        )

    @staticmethod
    def from_advanced_coordination(cap) -> UnifiedAgentCapability:
        """从高级协调引擎的AgentCapability转换"""
        # 根据能力名称推断类型
        if "analysis" in cap.capability_name:
            cap_type = CapabilityType.ANALYSIS
        elif "coordination" in cap.capability_name:
            cap_type = CapabilityType.COORDINATION
        elif "decision" in cap.capability_name:
            cap_type = CapabilityType.DECISION
        else:
            cap_type = CapabilityType.TECHNICAL

        return UnifiedAgentCapability(
            name=cap.capability_name,
            description=f"Advanced coordination capability: {cap.capability_name}",
            type=cap_type,
            proficiency=cap.proficiency,
            availability=cap.availability,
            cost_per_hour=cap.cost_per_hour,
            quality_metrics=cap.quality_metrics,
            specializations=cap.specializations,
        )

    @staticmethod
    def from_integration_module(cap) -> UnifiedAgentCapability:
        """从集成模块的AgentCapability转换"""
        # 简单的类型推断
        if "analysis" in cap.name or "planning" in cap.name:
            cap_type = CapabilityType.ANALYSIS
        elif "coordination" in cap.name or "management" in cap.name:
            cap_type = CapabilityType.MANAGEMENT
        else:
            cap_type = CapabilityType.TECHNICAL

        return UnifiedAgentCapability(
            name=cap.name,
            description=cap.description,
            type=cap_type,
            proficiency=cap.proficiency_level,
            availability=1.0 if cap.availability else 0.0,
        )

    @staticmethod
    def to_collaboration_framework(cap: UnifiedAgentCapability) -> Any:
        """转换为协作框架的AgentCapability格式"""
        # 需要先导入协作框架的AgentCapability
        try:
            from core.collaboration.multi_agent_collaboration import (
                AgentCapability as CollabCapability,
            )

            return CollabCapability(
                name=cap.name,
                description=cap.description,
                max_concurrent_tasks=cap.max_concurrent_tasks,
                estimated_duration=cap.estimated_duration,
                resource_requirements=cap.resource_requirements,
                dependencies=cap.dependencies,
            )
        except ImportError:
            # 如果导入失败,返回字典格式的数据
            return {
                "name": cap.name,
                "description": cap.description,
                "max_concurrent_tasks": cap.max_concurrent_tasks,
                "estimated_duration": cap.estimated_duration,
                "resource_requirements": cap.resource_requirements,
                "dependencies": cap.dependencies,
            }

    @staticmethod
    def to_advanced_coordination(cap: UnifiedAgentCapability) -> Any:
        """转换为高级协调引擎的AgentCapability格式"""
        try:

            return AgentCapability(
                capability_name=cap.name,
                proficiency=cap.proficiency,
                availability=cap.availability,
                cost_per_hour=cap.cost_per_hour,
                quality_metrics=cap.quality_metrics,
                specializations=cap.specializations,
            )
        except ImportError:
            # 如果导入失败,返回字典格式的数据
            return {
                "capability_name": cap.name,
                "proficiency": cap.proficiency,
                "availability": cap.availability,
                "cost_per_hour": cap.cost_per_hour,
                "quality_metrics": cap.quality_metrics,
                "specializations": cap.specializations,
            }


class CapabilityRegistry:
    """能力注册表,统一管理所有能力定义"""

    def __init__(self):
        self.capabilities: dict[str, UnifiedAgentCapability] = {}

    def register(self, capability: UnifiedAgentCapability) -> bool:
        """注册能力"""
        try:
            if capability.name in self.capabilities:
                # 更新现有能力
                existing = self.capabilities[capability.name]
                existing.update(**capability.to_dict())
            else:
                # 注册新能力
                self.capabilities[capability.name] = capability

            return True
        except Exception as e:
            print(f"注册能力失败: {e}")
            return False

    def get(self, name: str) -> UnifiedAgentCapability | None:
        """获取能力"""
        return self.capabilities.get(name)

    def find_by_type(self, cap_type: CapabilityType) -> list[UnifiedAgentCapability]:
        """按类型查找能力"""
        return [cap for cap in self.capabilities.values() if cap.type == cap_type]

    def find_available(
        self, requirements: Optional[dict[str, Any]] = None
    ) -> list[UnifiedAgentCapability]:
        """查找可用能力"""
        available = [cap for cap in self.capabilities.values() if cap.is_available()]

        if requirements:
            # 进一步筛选满足要求的能力
            available = [cap for cap in available if cap.can_handle(requirements)]

        return available

    def get_best_match(self, requirements: dict[str, Any]) -> UnifiedAgentCapability | None:
        """获取最佳匹配能力"""
        candidates = self.find_available(requirements)

        if not candidates:
            return None

        # 计算每个候选者的匹配分数
        best_candidate = None
        best_score = -1.0

        for candidate in candidates:
            score = candidate.calculate_score(requirements)
            if score > best_score:
                best_score = score
                best_candidate = candidate

        return best_candidate

    def list_all(self) -> list[str]:
        """列出所有能力名称"""
        return list(self.capabilities.keys())

    def remove(self, name: str) -> bool:
        """移除能力"""
        if name in self.capabilities:
            del self.capabilities[name]
            return True
        return False

    def clear(self) -> Any:
        """清空注册表"""
        self.capabilities.clear()

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        type_counts = {}
        for cap_type in CapabilityType:
            type_counts[cap_type.value] = len(self.find_by_type(cap_type))

        total_caps = len(self.capabilities)
        available_caps = len(self.find_available())

        return {
            "total_capabilities": total_caps,
            "available_capabilities": available_caps,
            "availability_rate": available_caps / total_caps if total_caps > 0 else 0.0,
            "type_distribution": type_counts,
            "average_proficiency": (
                sum(cap.proficiency for cap in self.capabilities.values()) / total_caps
                if total_caps > 0
                else 0.0
            ),
        }


# 全局能力注册表实例
capability_registry = CapabilityRegistry()


def create_standard_capabilities() -> list[UnifiedAgentCapability]:
    """创建标准能力集合"""
    standard_caps = [
        # 分析能力
        UnifiedAgentCapability(
            name="patent_analysis",
            description="专利分析能力,包括技术评估、法律分析、市场前景分析",
            type=CapabilityType.ANALYSIS,
            proficiency=0.95,
            specializations=["技术分析", "法律分析", "市场分析"],
            cost_per_hour=180.0,
        ),
        # 处理能力
        UnifiedAgentCapability(
            name="data_processing",
            description="数据处理能力,包括清洗、转换、分析和可视化",
            type=CapabilityType.PROCESSING,
            proficiency=0.85,
            specializations=["数据清洗", "数据转换", "数据可视化"],
            cost_per_hour=120.0,
        ),
        # 协调能力
        UnifiedAgentCapability(
            name="coordination",
            description="协调能力,包括任务分配、资源调度、冲突解决",
            type=CapabilityType.COORDINATION,
            proficiency=0.85,
            specializations=["任务分配", "资源调度", "冲突解决"],
            cost_per_hour=160.0,
        ),
        # 决策能力
        UnifiedAgentCapability(
            name="strategic_thinking",
            description="战略思维能力,包括规划、决策、风险评估",
            type=CapabilityType.DECISION,
            proficiency=0.8,
            specializations=["战略规划", "风险评估", "决策支持"],
            cost_per_hour=200.0,
        ),
        # 管理能力
        UnifiedAgentCapability(
            name="goal_management",
            description="目标管理能力,包括目标设定、分解、跟踪、调整",
            type=CapabilityType.MANAGEMENT,
            proficiency=0.9,
            specializations=["目标设定", "进度跟踪", "绩效评估"],
            cost_per_hour=100.0,
        ),
        # 技术能力
        UnifiedAgentCapability(
            name="task_planning",
            description="任务规划能力,包括任务分解、排程、优化",
            type=CapabilityType.TECHNICAL,
            proficiency=0.9,
            specializations=["任务分解", "排程优化", "路径规划"],
            cost_per_hour=150.0,
        ),
    ]

    return standard_caps


# 初始化标准能力
def initialize_standard_capabilities() -> Any:
    """初始化标准能力到注册表"""
    standard_caps = create_standard_capabilities()
    for cap in standard_caps:
        capability_registry.register(cap)

    print(f"已初始化 {len(standard_caps)} 个标准能力")


# 自动初始化
if __name__ == "__main__":
    initialize_standard_capabilities()

    # 测试代码
    print("\n能力注册表统计:")
    stats = capability_registry.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # 测试查找最佳匹配
    print("\n测试最佳匹配:")
    requirements = {"required_skills": ["数据清洗"], "min_proficiency": 0.8, "max_cost": 150.0}

    best_match = capability_registry.get_best_match(requirements)
    if best_match:
        print(f"最佳匹配: {best_match.name} (分数: {best_match.calculate_score(requirements):.2f})")
    else:
        print("未找到匹配的能力")
