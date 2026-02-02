#!/usr/bin/env python3
"""
替代方案探索器
Alternative Solution Explorer

为给定任务探索多个替代解决方案,提供多样化的选择

作者: 小诺·双鱼座
版本: v1.0.0
创建时间: 2025-01-05
"""

import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class ApproachType(Enum):
    """方法类型"""

    CONVENTIONAL = "conventional"  # 传统方法
    INNOVATIVE = "innovative"  # 创新方法
    HYBRID = "hybrid"  # 混合方法
    MINIMAL = "minimal"  # 最小化方法
    COMPREHENSIVE = "comprehensive"  # 全面方法


@dataclass
class AlternativeSolution:
    """替代方案"""

    solution_id: str
    name: str
    description: str
    approach_type: ApproachType
    steps: list[str] = field(default_factory=list)
    estimated_effort: float = 0.0  # 人日
    estimated_duration: float = 0.0  # 天
    required_resources: list[str] = field(default_factory=list)
    pros: list[str] = field(default_factory=list)
    cons: list[str] = field(default_factory=list)
    confidence: float = 0.0
    risk_score: float = 0.0
    innovation_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ComparisonResult:
    """对比结果"""

    task_id: str
    alternatives: list[AlternativeSolution] = field(default_factory=list)
    best_overall: str | None = None
    fastest: str | None = None
    most_reliable: str | None = None
    most_innovative: str | None = None
    comparison_matrix: dict[str, dict[str, float]] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)


class AlternativeExplorer:
    """替代方案探索器"""

    def __init__(self):
        """初始化探索器"""
        self.name = "替代方案探索器"
        self.version = "1.0.0"

        # 日志配置
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.name)

        # 探索历史
        self.exploration_history: list[ComparisonResult] = []

        # 方法模板
        self.approach_templates = self._load_approach_templates()

        print(f"💡 {self.name} v{self.version} 初始化完成")

    async def explore_alternatives(
        self, task: dict[str, Any], num_alternatives: int = 5, diversity_factor: float = 0.8
    ) -> ComparisonResult:
        """
        探索替代方案

        Args:
            task: 任务描述
            num_alternatives: 生成的方案数量
            diversity_factor: 多样性因子 (0-1)

        Returns:
            ComparisonResult: 对比结果
        """
        self.logger.info(f"💡 为任务探索替代方案: {task.get('title', '未知任务')}")

        task_id = task.get("id", f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

        try:
            # 1. 分析任务特征
            task_features = await self._analyze_task(task)

            # 2. 生成多样化的替代方案
            alternatives = await self._generate_diverse_alternatives(
                task, task_features, num_alternatives, diversity_factor
            )

            # 3. 评估每个方案
            for alt in alternatives:
                await self._evaluate_solution(alt, task)

            # 4. 构建对比矩阵
            comparison_matrix = await self._build_comparison_matrix(alternatives)

            # 5. 确定最优方案
            best_overall = await self._determine_best_overall(alternatives)
            fastest = await self._determine_fastest(alternatives)
            most_reliable = await self._determine_most_reliable(alternatives)
            most_innovative = await self._determine_most_innovative(alternatives)

            # 6. 生成推荐
            recommendations = await self._generate_recommendations(alternatives, comparison_matrix)

            # 7. 构建结果
            result = ComparisonResult(
                task_id=task_id,
                alternatives=alternatives,
                best_overall=best_overall,
                fastest=fastest,
                most_reliable=most_reliable,
                most_innovative=most_innovative,
                comparison_matrix=comparison_matrix,
                recommendations=recommendations,
            )

            self.exploration_history.append(result)

            self.logger.info(
                f"✅ 探索完成: 生成 {len(alternatives)} 个替代方案, " f"最优方案: {best_overall}"
            )

            return result

        except Exception as e:
            self.logger.error(f"❌ 替代方案探索失败: {e}")
            return ComparisonResult(task_id=task_id)

    async def _analyze_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """分析任务特征"""
        return {
            "complexity": task.get("complexity", 0.5),
            "domain": task.get("domain", "通用"),
            "urgency": task.get("urgency", 0.5),
            "quality_requirement": task.get("quality_requirement", 0.8),
            "resource_constraints": task.get("resource_constraints", {}),
            "time_constraints": task.get("time_constraints", {}),
            "requirements": task.get("requirements", []),
        }

    async def _generate_diverse_alternatives(
        self,
        task: dict[str, Any],        features: dict[str, Any],        num_alternatives: int,
        diversity_factor: float,
    ) -> list[AlternativeSolution]:
        """生成多样化的替代方案"""
        alternatives = []

        # 确定方案类型分布
        approach_distribution = self._calculate_approach_distribution(
            num_alternatives, diversity_factor
        )

        # 为每种类型生成方案
        for approach_type, count in approach_distribution.items():
            for i in range(count):
                alt = await self._generate_single_alternative(task, features, approach_type, i)
                if alt:
                    alternatives.append(alt)

        return alternatives

    def _calculate_approach_distribution(
        self, num_alternatives: int, diversity_factor: float
    ) -> dict[ApproachType, int]:
        """计算方法类型分布"""
        if diversity_factor > 0.7:
            # 高多样性:尽可能使用不同类型
            types = list(ApproachType)
            distribution = {}
            for i, atype in enumerate(types):
                distribution[atype] = 1 if i < num_alternatives else 0

            # 填充剩余数量
            remaining = num_alternatives - len(types)
            if remaining > 0:
                for i in range(remaining):
                    atype = types[i % len(types)]
                    distribution[atype] += 1

        else:
            # 低多样性:主要使用1-2种类型
            primary_type = ApproachType.CONVENTIONAL
            secondary_type = ApproachType.INNOVATIVE if num_alternatives > 1 else None

            distribution = {primary_type: max(1, num_alternatives // 2)}
            if secondary_type:
                distribution[secondary_type] = num_alternatives - distribution[primary_type]

        return distribution

    async def _generate_single_alternative(
        self,
        task: dict[str, Any],        features: dict[str, Any],        approach_type: ApproachType,
        index: int,
    ) -> AlternativeSolution | None:
        """生成单个替代方案"""
        try:
            # 获取方法模板
            template = self.approach_templates.get(approach_type, {})

            # 生成方案ID
            solution_id = (
                f"{approach_type.value}_{index}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            # 生成名称
            name = await self._generate_solution_name(task, approach_type, index)

            # 生成描述
            description = await self._generate_solution_description(task, approach_type, template)

            # 生成步骤
            steps = await self._generate_solution_steps(task, approach_type, template)

            # 估算工作量
            effort = await self._estimate_effort(task, approach_type, steps)
            duration = await self._estimate_duration(task, approach_type, steps)

            # 识别所需资源
            resources = await self._identify_required_resources(task, approach_type)

            # 生成优缺点
            pros, cons = await self._generate_pros_cons(task, approach_type, features)

            # 计算评分
            confidence = await self._calculate_confidence(task, approach_type, features)
            risk_score = await self._calculate_risk_score(task, approach_type, features)
            innovation_score = await self._calculate_innovation_score(approach_type)

            return AlternativeSolution(
                solution_id=solution_id,
                name=name,
                description=description,
                approach_type=approach_type,
                steps=steps,
                estimated_effort=effort,
                estimated_duration=duration,
                required_resources=resources,
                pros=pros,
                cons=cons,
                confidence=confidence,
                risk_score=risk_score,
                innovation_score=innovation_score,
                metadata={
                    "task_features": features,
                    "template_used": template.get("name", "custom"),
                },
            )

        except Exception as e:
            self.logger.error(f"❌ 生成方案失败: {e}")
            return None

    async def _generate_solution_name(
        self, task: dict[str, Any], approach_type: ApproachType, index: int
    ) -> str:
        """生成方案名称"""
        type_names = {
            ApproachType.CONVENTIONAL: "传统方案",
            ApproachType.INNOVATIVE: "创新方案",
            ApproachType.HYBRID: "混合方案",
            ApproachType.MINIMAL: "最小化方案",
            ApproachType.COMPREHENSIVE: "全面方案",
        }

        base_name = type_names.get(approach_type, "替代方案")
        task_title = task.get("title", "任务")

        return f"{task_title} - {base_name} #{index + 1}"

    async def _generate_solution_description(
        self, task: dict[str, Any], approach_type: ApproachType, template: dict[str, Any]
    ) -> str:
        """生成方案描述"""
        descriptions = {
            ApproachType.CONVENTIONAL: "采用成熟的技术方案,稳定可靠,风险较低",
            ApproachType.INNOVATIVE: "采用创新技术方案,可能带来更好的效果,但风险较高",
            ApproachType.HYBRID: "结合传统与创新技术,平衡效果与风险",
            ApproachType.MINIMAL: "快速实现核心功能,适合快速验证和迭代",
            ApproachType.COMPREHENSIVE: "全面考虑所有需求,提供完整的解决方案",
        }

        base_desc = descriptions.get(approach_type, "一个可行的替代方案")

        return f"{base_desc}。{template.get('description', '')}"

    async def _generate_solution_steps(
        self, task: dict[str, Any], approach_type: ApproachType, template: dict[str, Any]
    ) -> list[str]:
        """生成解决方案步骤"""
        # 基础步骤模板
        base_steps = ["需求分析和确认", "方案设计", "实现开发", "测试验证", "部署上线"]

        # 根据方法类型调整
        if approach_type == ApproachType.MINIMAL:
            return ["核心功能识别", "快速原型开发", "基础测试", "用户反馈收集", "迭代优化"]
        elif approach_type == ApproachType.COMPREHENSIVE:
            return [
                "全面需求分析",
                "详细架构设计",
                "分阶段实现",
                "完整测试覆盖",
                "灰度发布",
                "持续优化",
            ]
        elif approach_type == ApproachType.INNOVATIVE:
            return [
                "创新方案研究",
                "技术可行性验证",
                "原型开发",
                "效果评估",
                "风险缓解",
                "正式实施",
            ]
        else:
            return base_steps

    async def _estimate_effort(
        self, task: dict[str, Any], approach_type: ApproachType, steps: list[str]
    ) -> float:
        """估算工作量(人日)"""
        base_effort = len(steps) * 2  # 每步2人日

        multipliers = {
            ApproachType.MINIMAL: 0.5,
            ApproachType.CONVENTIONAL: 1.0,
            ApproachType.HYBRID: 1.2,
            ApproachType.INNOVATIVE: 1.5,
            ApproachType.COMPREHENSIVE: 2.0,
        }

        return base_effort * multipliers.get(approach_type, 1.0)

    async def _estimate_duration(
        self, task: dict[str, Any], approach_type: ApproachType, steps: list[str]
    ) -> float:
        """估算持续时间(天)"""
        effort = await self._estimate_effort(task, approach_type, steps)
        return effort / 8  # 假设每天8小时

    async def _identify_required_resources(
        self, task: dict[str, Any], approach_type: ApproachType
    ) -> list[str]:
        """识别所需资源"""
        base_resources = ["开发人员", "测试环境"]

        if approach_type == ApproachType.INNOVATIVE:
            base_resources.extend(["研究专家", "实验环境"])
        elif approach_type == ApproachType.COMPREHENSIVE:
            base_resources.extend(["项目经理", "多领域专家"])
        elif approach_type == ApproachType.HYBRID:
            base_resources.extend(["技术顾问"])

        return base_resources

    async def _generate_pros_cons(
        self, task: dict[str, Any], approach_type: ApproachType, features: dict[str, Any]
    ) -> tuple[list[str], list[str]]:
        """生成优缺点"""
        pros_cons = {
            ApproachType.CONVENTIONAL: (
                ["技术成熟", "风险可控", "易于维护", "成本可预测"],
                ["创新性不足", "可能不是最优方案"],
            ),
            ApproachType.INNOVATIVE: (
                ["技术先进", "性能可能更优", "竞争优势"],
                ["风险较高", "技术不成熟", "维护成本不确定"],
            ),
            ApproachType.HYBRID: (["平衡风险与收益", "灵活性高"], ["复杂度较高", "需要更多协调"]),
            ApproachType.MINIMAL: (
                ["快速交付", "成本低", "易于迭代"],
                ["功能不完整", "可能需要重构"],
            ),
            ApproachType.COMPREHENSIVE: (["功能完整", "长期价值高"], ["开发周期长", "成本高"]),
        }

        return pros_cons.get(approach_type, (["可行的方案"], ["需要权衡"]))

    async def _calculate_confidence(
        self, task: dict[str, Any], approach_type: ApproachType, features: dict[str, Any]
    ) -> float:
        """计算置信度"""
        base_confidence = {
            ApproachType.CONVENTIONAL: 0.9,
            ApproachType.HYBRID: 0.8,
            ApproachType.MINIMAL: 0.7,
            ApproachType.COMPREHENSIVE: 0.85,
            ApproachType.INNOVATIVE: 0.6,
        }

        return base_confidence.get(approach_type, 0.7)

    async def _calculate_risk_score(
        self, task: dict[str, Any], approach_type: ApproachType, features: dict[str, Any]
    ) -> float:
        """计算风险分数(0-1,越高风险越大)"""
        risk_scores = {
            ApproachType.CONVENTIONAL: 0.2,
            ApproachType.HYBRID: 0.4,
            ApproachType.MINIMAL: 0.5,
            ApproachType.COMPREHENSIVE: 0.3,
            ApproachType.INNOVATIVE: 0.7,
        }

        return risk_scores.get(approach_type, 0.4)

    async def _calculate_innovation_score(self, approach_type: ApproachType) -> float:
        """计算创新分数"""
        innovation_scores = {
            ApproachType.CONVENTIONAL: 0.2,
            ApproachType.HYBRID: 0.6,
            ApproachType.MINIMAL: 0.4,
            ApproachType.COMPREHENSIVE: 0.3,
            ApproachType.INNOVATIVE: 0.9,
        }

        return innovation_scores.get(approach_type, 0.5)

    async def _evaluate_solution(self, solution: AlternativeSolution, task: dict[str, Any]) -> None:
        """评估解决方案"""
        # 这里可以添加更复杂的评估逻辑
        # 目前在生成时已经完成了基本评估
        pass

    async def _build_comparison_matrix(
        self, alternatives: list[AlternativeSolution]
    ) -> dict[str, dict[str, float]]:
        """构建对比矩阵"""
        matrix = {}


        for alt in alternatives:
            matrix[alt.solution_id] = {
                "effort": alt.estimated_effort,
                "duration": alt.estimated_duration,
                "confidence": alt.confidence,
                "risk": alt.risk_score,
                "innovation": alt.innovation_score,
                "overall": (
                    alt.confidence * 0.4 + (1 - alt.risk_score) * 0.3 + alt.innovation_score * 0.3
                ),
            }

        return matrix

    async def _determine_best_overall(
        self, alternatives: list[AlternativeSolution]
    ) -> str | None:
        """确定总体最优方案"""
        if not alternatives:
            return None

        # 综合评分
        def overall_score(alt) -> None:
            return alt.confidence * 0.4 + (1 - alt.risk_score) * 0.3 + alt.innovation_score * 0.3

        return max(alternatives, key=overall_score).solution_id

    async def _determine_fastest(self, alternatives: list[AlternativeSolution]) -> str | None:
        """确定最快方案"""
        if not alternatives:
            return None

        return min(alternatives, key=lambda a: a.estimated_duration).solution_id

    async def _determine_most_reliable(
        self, alternatives: list[AlternativeSolution]
    ) -> str | None:
        """确定最可靠方案"""
        if not alternatives:
            return None

        # 可靠性 = 高置信度 + 低风险
        def reliability(alt) -> None:
            return alt.confidence * 0.7 + (1 - alt.risk_score) * 0.3

        return max(alternatives, key=reliability).solution_id

    async def _determine_most_innovative(
        self, alternatives: list[AlternativeSolution]
    ) -> str | None:
        """确定最创新方案"""
        if not alternatives:
            return None

        return max(alternatives, key=lambda a: a.innovation_score).solution_id

    async def _generate_recommendations(
        self,
        alternatives: list[AlternativeSolution],
        comparison_matrix: dict[str, dict[str, float]],
    ) -> list[str]:
        """生成推荐"""
        recommendations = []

        if len(alternatives) == 0:
            return ["无法生成推荐:没有可用方案"]

        # 1. 总体推荐
        best = max(alternatives, key=lambda a: comparison_matrix[a.solution_id]["overall"])
        recommendations.append(f"推荐采用: {best.name}(综合评分最高)")

        # 2. 针对不同场景的推荐
        fastest = min(alternatives, key=lambda a: a.estimated_duration)
        recommendations.append(f"如果时间紧迫: {fastest.name}(最快可完成)")

        most_reliable = max(alternatives, key=lambda a: a.confidence)
        recommendations.append(f"如果追求稳定: {most_reliable.name}(最可靠)")

        most_innovative = max(alternatives, key=lambda a: a.innovation_score)
        recommendations.append(f"如果追求创新: {most_innovative.name}(最创新)")

        return recommendations

    def _load_approach_templates(self) -> dict[ApproachType, dict[str, Any]]:
        """加载方法模板"""
        return {
            ApproachType.CONVENTIONAL: {
                "name": "传统方法",
                "description": "使用成熟、经过验证的方法",
                "characteristics": ["稳定", "可预测", "低风险"],
            },
            ApproachType.INNOVATIVE: {
                "name": "创新方法",
                "description": "采用前沿、实验性的方法",
                "characteristics": ["先进", "高风险", "高回报"],
            },
            ApproachType.HYBRID: {
                "name": "混合方法",
                "description": "结合多种方法的优点",
                "characteristics": ["平衡", "灵活", "适应性强"],
            },
            ApproachType.MINIMAL: {
                "name": "最小化方法",
                "description": "快速实现核心功能",
                "characteristics": ["快速", "低成本", "可迭代"],
            },
            ApproachType.COMPREHENSIVE: {
                "name": "全面方法",
                "description": "完整实现所有需求",
                "characteristics": ["完整", "长期价值", "高质量"],
            },
        }

    def get_exploration_summary(self) -> dict[str, Any]:
        """获取探索摘要"""
        return {
            "total_explorations": len(self.exploration_history),
            "avg_alternatives_per_task": (
                sum(len(r.alternatives) for r in self.exploration_history)
                / len(self.exploration_history)
                if self.exploration_history
                else 0
            ),
        }


# ==================== 全局实例 ====================

_alternative_explorer: AlternativeExplorer | None = None


def get_alternative_explorer() -> AlternativeExplorer:
    """获取探索器单例"""
    global _alternative_explorer
    if _alternative_explorer is None:
        _alternative_explorer = AlternativeExplorer()
    return _alternative_explorer


# ==================== 导出 ====================

__all__ = [
    "AlternativeExplorer",
    "AlternativeSolution",
    "ApproachType",
    "ComparisonResult",
    "get_alternative_explorer",
]
