#!/usr/bin/env python3
from __future__ import annotations
"""
演化式专利撰写系统
Evolutionary Patent Drafting System

基于王立铭《生命是什么》中演化思想的专利撰写系统:
- 从简单到复杂的渐进式撰写
- 类似生物演化的版本迭代
- 自然选择:保留优秀版本特征
- 赫布学习:从成功案例中学习模式

作者: 小诺·双鱼公主
创建时间: 2025-12-24
版本: v0.1.2 "晨星初现"
"""

import logging

# 导入生物学模块
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.biology.evolutionary_memory_system import (
    EvolutionaryPressure,
    MutationType,
    get_evolutionary_memory,
)
from core.biology.hebbian_optimizer import get_hebbian_optimizer
from core.patent.case_database import (
    CaseStatus,
    CaseType,
    PatentCase,
    TechnicalField,
    get_patent_case_db,
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class DraftVersion(Enum):
    """撰写版本(类似生物演化阶段)"""

    V1_BASIC = "v1_basic"  # 基础版(单细胞)
    V2_DETAILED = "v2_detailed"  # 详细版(多细胞)
    V3_OPTIMIZED = "v3_optimized"  # 优化版(复杂生物)
    V4_PERFECTED = "v4_perfected"  # 完善版(智慧生命)


class DraftSection(Enum):
    """撰写部分"""

    TITLE = "title"  # 标题
    ABSTRACT = "abstract"  # 摘要
    CLAIMS = "claims"  # 权利要求
    DESCRIPTION = "description"  # 说明书
    EMBODIMENTS = "embodiments"  # 具体实施方式


@dataclass
class DraftTrait:
    """撰写特征(类似基因)"""

    trait_id: str
    name: str  # 特征名称
    value: Any  # 特征值
    category: str  # 类别(结构/内容/表达)
    fitness: float = 0.5  # 适应度

    # 来源
    source_case: str | None = None  # 来源案例
    mutation_type: MutationType | None = None


@dataclass
class PatentDraft:
    """专利草稿"""

    draft_id: str
    version: DraftVersion
    invention_title: str

    # 各部分内容
    title: str = ""
    abstract: str = ""
    claims: list[str] = field(default_factory=list)
    description: str = ""
    embodiments: str = ""

    # 演化信息
    parent_draft: str | None = None  # 父草稿ID(遗传)
    traits: list[DraftTrait] = field(default_factory=list)  # 特征集合
    fitness: float = 0.5  # 适应度

    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class DraftGenerationResult:
    """撰写生成结果"""

    draft: PatentDraft
    generation_time: float
    used_traits: list[DraftTrait]
    fitness_score: float
    quality_metrics: dict[str, Any]
    improvement_suggestions: list[str]


class EvolutionaryDraftingSystem:
    """
    演化式专利撰写系统

    核心思想:
    1. V1基础版:核心发明点(单细胞生物)
    2. V2详细版:扩展描述(多细胞生物)
    3. V3优化版:语言优化(复杂生物)
    4. V4完善版:最终定稿(智慧生命)

    每个版本都是一次"演化",保留优秀特征,改进不足
    """

    def __init__(self):
        """初始化撰写系统"""
        self.name = "演化式专利撰写系统"
        self.version = "v0.1.2"

        # 生物学模块
        self.evolutionary_memory = get_evolutionary_memory()
        self.hebbian_optimizer = get_hebbian_optimizer()

        # 案例数据库
        self.case_db = get_patent_case_db()

        # 草稿存储
        self.drafts: dict[str, PatentDraft] = {}

        # 特征基因库(从成功案例中提取)
        self.trait_library: dict[str, list[DraftTrait]] = {
            "structure": [],  # 结构特征
            "content": [],  # 内容特征
            "expression": [],  # 表达特征
        }

        logger.info(f"✍️ {self.name} ({self.version}) 初始化完成")

    def draft_from_invention(
        self, invention: dict[str, Any], target_version: DraftVersion = DraftVersion.V4_PERFECTED
    ) -> DraftGenerationResult:
        """
        从发明构思撰写专利

        Args:
            invention: 发明信息,包含:
                - title: 发明名称
                - technical_field: 技术领域
                - background: 背景技术
                - problem: 技术问题
                - solution: 技术方案
                - advantages: 有益效果
                - embodiments: 实施方式
            target_version: 目标版本

        Returns:
            撰写结果
        """
        start_time = datetime.now()

        # 提取特征
        traits = self._extract_traits(invention)

        # 渐进式撰写
        current_draft = None

        for version in [
            DraftVersion.V1_BASIC,
            DraftVersion.V2_DETAILED,
            DraftVersion.V3_OPTIMIZED,
            DraftVersion.V4_PERFECTED,
        ]:
            current_draft = self._generate_version(
                invention=invention, version=version, parent_draft=current_draft, traits=traits
            )

            # 存储草稿
            self.drafts[current_draft.draft_id] = current_draft

            # 记录到演化记忆
            self.evolutionary_memory.record_mutation(
                agent_id="patent_drafter",
                mutation_type=MutationType.STRUCTURE_OPTIMIZATION,
                pressure=EvolutionaryPressure.USER_FEEDBACK,
                trait_name=version.value,
                trait_value=current_draft.draft_id,
                description=f"生成{version.value}草稿",
            )

            # 如果已达到目标版本,停止
            if version == target_version:
                break

        generation_time = (datetime.now() - start_time).total_seconds()

        # 计算质量指标
        quality_metrics = self._calculate_quality_metrics(current_draft)

        # 生成改进建议
        suggestions = self._generate_improvement_suggestions(current_draft, quality_metrics)

        # 记录赫布学习:协同激活的模式
        self.hebbian_optimizer.record_activation(
            nodes=[
                "专利撰写",
                invention.get("technical_field", "未知"),
                current_draft.version.value,
            ],
            context={"invention": invention.get("title", "")[:30]},
        )

        return DraftGenerationResult(
            draft=current_draft,
            generation_time=generation_time,
            used_traits=traits,
            fitness_score=current_draft.fitness,
            quality_metrics=quality_metrics,
            improvement_suggestions=suggestions,
        )

    def _extract_traits(self, invention: dict[str, Any]) -> list[DraftTrait]:
        """从发明信息中提取特征"""
        traits = []

        # 从案例库中检索相似案例
        similar_case = self._find_similar_case(invention)

        # 结构特征
        if similar_case:
            for trait in similar_case.input_data.get("traits", []):
                traits.append(
                    DraftTrait(
                        trait_id=f"trait_{len(traits)}",
                        name=trait.get("name", ""),
                        value=trait.get("value"),
                        category=trait.get("category", "content"),
                        fitness=trait.get("fitness", 0.7),
                        source_case=similar_case.case_id,
                    )
                )

        # 如果没有相似案例,使用默认特征
        if not traits:
            traits.extend(self._get_default_traits(invention))

        return traits

    def _find_similar_case(self, invention: dict[str, Any]) -> PatentCase | None:
        """查找相似案例"""
        # 简化实现:查找同技术领域的成功案例
        query_case = PatentCase(
            case_id="",
            case_type=CaseType.PATENT_DRAFTING,
            status=CaseStatus.SUCCESS,
            technical_field=TechnicalField.SOFTWARE,
            title=invention.get("title", ""),
            description=invention.get("solution", ""),
            input_data={},
            output_result={},
            solution="",
            tags=[invention.get("technical_field", "")],
        )

        result = self.case_db.retrieve_similar_cases(
            query_case, top_n=1, case_type=CaseType.PATENT_DRAFTING
        )

        if result.cases:
            return result.cases[0]
        return None

    def _get_default_traits(self, invention: dict[str, Any]) -> list[DraftTrait]:
        """获取默认特征"""
        return [
            DraftTrait(
                trait_id="trait_structure_001",
                name="三段式结构",
                value={"background", "solution", "embodiments"},
                category="structure",
                fitness=0.8,
            ),
            DraftTrait(
                trait_id="trait_content_001",
                name="技术问题导向",
                value=invention.get("problem", ""),
                category="content",
                fitness=0.7,
            ),
            DraftTrait(
                trait_id="trait_expression_001",
                name="专业术语",
                value="使用标准专利术语",
                category="expression",
                fitness=0.6,
            ),
        ]

    def _generate_version(
        self,
        invention: dict[str, Any],        version: DraftVersion,
        parent_draft: PatentDraft,
        traits: list[DraftTrait],
    ) -> PatentDraft:
        """生成指定版本的草稿"""
        draft_id = f"draft_{datetime.now().timestamp()}_{version.value}"

        if version == DraftVersion.V1_BASIC:
            # 基础版:核心内容
            draft = PatentDraft(
                draft_id=draft_id,
                version=version,
                invention_title=invention.get("title", ""),
                title=self._generate_title_v1(invention),
                abstract=self._generate_abstract_v1(invention),
                claims=self._generate_claims_v1(invention),
                description=self._generate_description_v1(invention),
                embodiments=self._generate_embodiments_v1(invention),
                parent_draft=None,
                traits=traits,
            )

        elif version == DraftVersion.V2_DETAILED:
            # 详细版:扩展内容
            draft = PatentDraft(
                draft_id=draft_id,
                version=version,
                invention_title=invention.get("title", ""),
                title=parent_draft.title,
                abstract=self._expand_abstract(parent_draft.abstract, invention),
                claims=self._expand_claims(parent_draft.claims, invention),
                description=self._expand_description(parent_draft.description, invention),
                embodiments=self._expand_embodiments(parent_draft.embodiments, invention),
                parent_draft=parent_draft.draft_id,
                traits=traits,
            )

        elif version == DraftVersion.V3_OPTIMIZED:
            # 优化版:语言优化
            draft = PatentDraft(
                draft_id=draft_id,
                version=version,
                invention_title=invention.get("title", ""),
                title=self._optimize_title(parent_draft.title),
                abstract=self._optimize_text(parent_draft.abstract),
                claims=[self._optimize_text(claim) for claim in parent_draft.claims],
                description=self._optimize_text(parent_draft.description),
                embodiments=self._optimize_text(parent_draft.embodiments),
                parent_draft=parent_draft.draft_id,
                traits=traits,
            )

        else:  # V4_PERFECTED
            # 完善版:最终定稿
            draft = PatentDraft(
                draft_id=draft_id,
                version=version,
                invention_title=invention.get("title", ""),
                title=parent_draft.title,
                abstract=self._perfect_abstract(parent_draft.abstract, invention),
                claims=self._perfect_claims(parent_draft.claims, invention),
                description=self._perfect_description(parent_draft.description),
                embodiments=self._perfect_embodiments(parent_draft.embodiments, invention),
                parent_draft=parent_draft.draft_id,
                traits=traits,
            )

        # 计算适应度
        draft.fitness = self._calculate_draft_fitness(draft)

        return draft

    # ============ V1 基础版生成方法 ============

    def _generate_title_v1(self, invention: dict[str, Any]) -> str:
        """生成V1标题"""
        return invention.get("title", "发明名称")

    def _generate_abstract_v1(self, invention: dict[str, Any]) -> str:
        """生成V1摘要"""
        return f"""
本发明公开了{invention.get('title', '一种技术方案')},属于{invention.get('technical_field', '技术领域')}。
本发明解决的技术问题是:{invention.get('problem', '现有技术的不足')}。
本发明的技术方案是:{invention.get('solution', '技术方案描述')}。
本发明的有益效果是:{invention.get('advantages', '有益效果')}。
        """.strip()

    def _generate_claims_v1(self, invention: dict[str, Any]) -> list[str]:
        """生成V1权利要求"""
        return [
            f"1. {invention.get('title', '一种技术方案')},其特征在于,包括{invention.get('solution', '技术特征')}。"
        ]

    def _generate_description_v1(self, invention: dict[str, Any]) -> str:
        """生成V1说明书"""
        return f"""
[技术领域]
本发明涉及{invention.get('technical_field', '技术领域')},具体涉及{invention.get('title', '一种技术方案')}。

[背景技术]
{invention.get('background', '现有技术描述')}

[发明内容]
本发明要解决的技术问题是{invention.get('problem', '技术问题')}。

为解决上述技术问题,本发明采用如下技术方案:
{invention.get('solution', '技术方案描述')}

本发明的有益效果是:{invention.get('advantages', '有益效果')}。
        """.strip()

    def _generate_embodiments_v1(self, invention: dict[str, Any]) -> str:
        """生成V1具体实施方式"""
        return f"""
[具体实施方式]
下面结合具体实施例对本发明作进一步详细说明。

实施例1:
{invention.get('embodiments', '具体实施方式描述')}
        """.strip()

    # ============ V2 详细版扩展方法 ============

    def _expand_abstract(self, abstract: str, invention: dict[str, Any]) -> str:
        """扩展摘要"""
        # 添加更多细节
        return abstract + f"\n优选地,{invention.get('preferable_features', '优选特征')}。"

    def _expand_claims(self, claims: list[str], invention: dict[str, Any]) -> list[str]:
        """扩展权利要求"""
        # 添加从属权利要求
        additional = invention.get("additional_claims", [])
        return claims + [f"{i+2}. {claim}" for i, claim in enumerate(additional)]

    def _expand_description(self, description: str, invention: dict[str, Any]) -> str:
        """扩展说明书"""
        # 添加附图说明
        return description + f"\n[附图说明]\n{invention.get('figures', '附图说明')}"

    def _expand_embodiments(self, embodiments: str, invention: dict[str, Any]) -> str:
        """扩展具体实施方式"""
        # 添加更多实施例
        return embodiments + f"\n\n实施例2:\n{invention.get('embodiment_2', '第二实施例')}"

    # ============ V3 优化版优化方法 ============

    def _optimize_title(self, title: str) -> str:
        """优化标题"""
        # 确保标题符合规范
        if not title.startswith("一种") and not title.startswith("基于"):
            return f"一种{title}"
        return title

    def _optimize_text(self, text: str) -> str:
        """优化文本表达"""
        # 简化实现:去除多余空格,统一标点
        text = text.replace("  ", " ").replace("  ", " ")
        text = text.replace(",。", "。").replace("。。", "。")
        return text

    # ============ V4 完善版完善方法 ============

    def _perfect_abstract(self, abstract: str, invention: dict[str, Any]) -> str:
        """完善摘要"""
        return self._optimize_text(abstract)

    def _perfect_claims(self, claims: list[str], invention: dict[str, Any]) -> list[str]:
        """完善权利要求"""
        # 确保权利要求引用关系正确
        perfected = []
        for i, claim in enumerate(claims):
            if i == 0:
                perfected.append(claim)
            elif "根据权利要求" not in claim:
                # 添加引用
                perfected.append(
                    claim.replace(
                        f"{i+1}.",
                        f"{i+1}. 根据权利要求{i}所述的{invention.get('title', '技术方案')}",
                    )
                )
            else:
                perfected.append(claim)
        return perfected

    def _perfect_description(self, description: str) -> str:
        """完善说明书"""
        return self._optimize_text(description)

    def _perfect_embodiments(self, embodiments: str, invention: dict[str, Any]) -> str:
        """完善具体实施方式"""
        return self._optimize_text(embodiments)

    # ============ 辅助方法 ============

    def _calculate_draft_fitness(self, draft: PatentDraft) -> float:
        """计算草稿适应度"""
        fitness = 0.5

        # 标题质量
        if draft.title and len(draft.title) >= 5:
            fitness += 0.1

        # 摘要质量
        if draft.abstract and len(draft.abstract) >= 100:
            fitness += 0.1

        # 权利要求质量
        if draft.claims and len(draft.claims) >= 1:
            fitness += 0.15

        # 说明书质量
        if draft.description and len(draft.description) >= 300:
            fitness += 0.15

        return min(1.0, fitness)

    def _calculate_quality_metrics(self, draft: PatentDraft) -> dict[str, Any]:
        """计算质量指标"""
        return {
            "title_length": len(draft.title),
            "abstract_length": len(draft.abstract),
            "claims_count": len(draft.claims),
            "description_length": len(draft.description),
            "completeness": (
                1.0
                if all(
                    [
                        draft.title,
                        draft.abstract,
                        draft.claims,
                        draft.description,
                        draft.embodiments,
                    ]
                )
                else 0.5
            ),
            "version": draft.version.value,
        }

    def _generate_improvement_suggestions(
        self, draft: PatentDraft, metrics: dict[str, Any]
    ) -> list[str]:
        """生成改进建议"""
        suggestions = []

        if len(draft.title) < 10:
            suggestions.append("建议标题更加具体,体现技术特征")

        if len(draft.abstract) < 150:
            suggestions.append("建议摘要更加详细,包含技术问题、方案和效果")

        if len(draft.claims) < 2:
            suggestions.append("建议增加从属权利要求,形成保护层级")

        if len(draft.description) < 500:
            suggestions.append("建议说明书更加详细,充分公开技术方案")

        if not suggestions:
            suggestions.append("草稿质量良好,建议进入审查阶段")

        return suggestions

    def get_draft(self, draft_id: str) -> PatentDraft | None:
        """获取草稿"""
        return self.drafts.get(draft_id)

    def get_all_drafts(self) -> list[PatentDraft]:
        """获取所有草稿"""
        return list(self.drafts.values())


# 全局单例
_evolutionary_drafting_instance = None


def get_evolutionary_drafting_system() -> EvolutionaryDraftingSystem:
    """获取演化撰写系统单例"""
    global _evolutionary_drafting_instance
    if _evolutionary_drafting_instance is None:
        _evolutionary_drafting_instance = EvolutionaryDraftingSystem()
    return _evolutionary_drafting_instance


# 测试代码
async def main():
    """测试演化式专利撰写系统"""

    print("\n" + "=" * 60)
    print("✍️ 演化式专利撰写系统测试")
    print("=" * 60 + "\n")

    system = get_evolutionary_drafting_system()

    # 测试数据
    invention = {
        "title": "基于深度学习的图像识别方法",
        "technical_field": "计算机视觉",
        "background": "图像识别是计算机视觉的重要应用领域,传统方法识别准确率较低。",
        "problem": "现有图像识别方法在复杂场景下准确率不高,计算效率低。",
        "solution": "采用改进的卷积神经网络结构,引入注意力机制和特征金字塔",
        "advantages": "识别准确率提升30%,速度提升50%,适应复杂场景",
        "embodiments": "使用PyTorch实现,包括数据预处理、模型训练、后处理等步骤",
        "preferable_features": "注意力模块采用SENet结构,特征金字塔使用FPN",
        "additional_claims": ["所述注意力机制为SENet注意力模块", "所述特征金字塔包括5个尺度"],
    }

    print("📝 测试1: 从发明构思生成专利草稿")

    result = system.draft_from_invention(invention)

    print(f"生成草稿: {result.draft.draft_id}")
    print(f"版本: {result.draft.version.value}")
    print(f"适应度: {result.fitness_score:.2f}")
    print(f"生成时间: {result.generation_time:.2f}秒\n")

    print("📝 专利标题:")
    print(result.draft.title)
    print()

    print("📝 专利摘要:")
    print(result.draft.abstract[:200] + "...")
    print()

    print("📝 权利要求:")
    for i, claim in enumerate(result.draft.claims[:3], 1):
        print(f"  {i}. {claim[:80]}...")
    print()

    print("📝 质量指标:")
    for key, value in result.quality_metrics.items():
        print(f"  {key}: {value}")
    print()

    print("📝 改进建议:")
    for suggestion in result.improvement_suggestions:
        print(f"  • {suggestion}")

    print("\n✅ 测试完成!")


# 入口点: @async_main装饰器已添加到main函数
