#!/usr/bin/env python3
"""
专利定性规则库
Patent Qualitative Rules Library

基于专家知识的专利分析定性规则系统:
- 新颖性判断规则
- 创造性判断规则
- 实用性判断规则
- 权利要求解释规则
- 意见答复策略规则

作者: 小诺·双鱼公主
创建时间: 2025-12-24
版本: v0.1.2 "晨星初现"
"""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class RuleType(Enum):
    """规则类型"""

    NOVELTY = "novelty"  # 新颖性
    INVENTIVENESS = "inventiveness"  # 创造性
    UTILITY = "utility"  # 实用性
    CLAIM_INTERPRETATION = "claim_interpretation"  # 权利要求解释
    OA_STRATEGY = "oa_strategy"  # 意见答复策略


class RuleCategory(Enum):
    """规则类别"""

    POSITIVE = "positive"  # 正面规则(支持专利性)
    NEGATIVE = "negative"  # 负面规则(反对专利性)
    NEUTRAL = "neutral"  # 中性规则(分析性)


@dataclass
class QualitativeRule:
    """定性规则"""

    rule_id: str
    rule_type: RuleType
    category: RuleCategory
    name: str  # 规则名称
    description: str  # 规则描述
    conditions: list[str]  # 适用条件
    conclusion: str  # 结论
    confidence: float = 0.8  # 规则置信度
    weight: float = 1.0  # 规则权重
    references: list[str] = field(default_factory=list)  # 参考案例
    examples: list[dict[str, str]] = field(default_factory=list)  # 示例

    def applies(self, context: dict[str, Any]) -> tuple[bool, str]:
        """
        判断规则是否适用

        Args:
            context: 案例上下文

        Returns:
            (是否适用, 原因)
        """
        # 简化实现:检查所有条件是否满足
        for condition in self.conditions:
            # 这里简化处理,实际应该解析条件表达式
            # 例如:"技术领域 == 软件" 检查context中的技术领域
            if "技术领域" in condition:
                field = context.get("technical_field", "")
                expected = condition.split("==")[1].strip() if "==" in condition else ""
                if field != expected:
                    return False, f"技术领域不匹配: {field} != {expected}"

        return True, "所有条件满足"

    def apply(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        应用规则

        Args:
            context: 案例上下文

        Returns:
            规则应用结果
        """
        applies, reason = self.applies(context)

        return {
            "rule_id": self.rule_id,
            "rule_name": self.name,
            "applies": applies,
            "reason": reason,
            "conclusion": self.conclusion if applies else "规则不适用",
            "confidence": self.confidence if applies else 0.0,
            "category": self.category.value,
            "weight": self.weight,
        }


@dataclass
class RuleApplicationResult:
    """规则应用结果"""

    applied_rules: list[dict[str, Any]]
    total_rules: int
    positive_score: float  # 正面得分
    negative_score: float  # 负面得分
    net_score: float  # 净得分
    conclusion: str
    confidence: float


class QualitativeRuleEngine:
    """
    定性规则引擎

    核心功能:
    1. 规则管理
    2. 规则匹配和应用
    3. 综合评分
    4. 规则学习
    """

    def __init__(self):
        """初始化规则引擎"""
        self.name = "专利定性规则引擎"
        self.version = "v0.1.2"

        # 规则存储
        self.rules: dict[str, QualitativeRule] = {}

        # 按类型索引
        self.by_type: dict[RuleType, list[str]] = defaultdict(list)

        # 按类别索引
        self.by_category: dict[RuleCategory, list[str]] = defaultdict(list)

        # 规则使用统计
        self.rule_usage: dict[str, int] = defaultdict(int)

        # 初始化默认规则
        self._init_default_rules()

        logger.info(f"📜 {self.name} ({self.version}) 初始化完成")
        logger.info(f"   已加载 {len(self.rules)} 条规则")

    def _init_default_rules(self) -> None:
        """初始化默认规则"""

        # ========== 新颖性规则 ==========
        self.add_rule(
            QualitativeRule(
                rule_id="novelty_001",
                rule_type=RuleType.NOVELTY,
                category=RuleCategory.POSITIVE,
                name="全新技术方案",
                description="现有技术中未公开相同技术方案",
                conditions=["技术领域 == 任意"],
                conclusion="具备新颖性",
                confidence=0.95,
                weight=1.0,
            )
        )

        self.add_rule(
            QualitativeRule(
                rule_id="novelty_002",
                rule_type=RuleType.NOVELTY,
                category=RuleCategory.NEGATIVE,
                name="现有技术公开",
                description="现有技术已公开相同技术特征",
                conditions=["现有技术包含全部技术特征"],
                conclusion="不具备新颖性",
                confidence=0.9,
                weight=1.0,
            )
        )

        self.add_rule(
            QualitativeRule(
                rule_id="novelty_003",
                rule_type=RuleType.NOVELTY,
                category=RuleCategory.POSITIVE,
                name="区别技术特征",
                description="与现有技术存在至少一个不同技术特征",
                conditions=["区别特征数量 >= 1"],
                conclusion="具备新颖性",
                confidence=0.85,
                weight=0.9,
            )
        )

        # ========== 创造性规则 ==========
        self.add_rule(
            QualitativeRule(
                rule_id="inventive_001",
                rule_type=RuleType.INVENTIVENESS,
                category=RuleCategory.POSITIVE,
                name="突出的实质性特点",
                description="对本领域技术人员来说非显而易见",
                conditions=["技术效果显著", "现有技术无启示"],
                conclusion="具备创造性",
                confidence=0.9,
                weight=1.0,
            )
        )

        self.add_rule(
            QualitativeRule(
                rule_id="inventive_002",
                rule_type=RuleType.INVENTIVENESS,
                category=RuleCategory.POSITIVE,
                name="显著进步",
                description="产生有益的技术效果",
                conditions=["性能提升 > 20%", "或成本降低 > 15%"],
                conclusion="具备创造性",
                confidence=0.85,
                weight=0.9,
            )
        )

        self.add_rule(
            QualitativeRule(
                rule_id="inventive_003",
                rule_type=RuleType.INVENTIVENESS,
                category=RuleCategory.NEGATIVE,
                name="简单替换",
                description="仅仅是已知技术的简单组合或替换",
                conditions=["无协同效应", "无新性能"],
                conclusion="不具备创造性",
                confidence=0.8,
                weight=0.8,
            )
        )

        # ========== 实用性规则 ==========
        self.add_rule(
            QualitativeRule(
                rule_id="utility_001",
                rule_type=RuleType.UTILITY,
                category=RuleCategory.POSITIVE,
                name="可制造性",
                description="能够在产业中制造",
                conditions=["技术方案具体", "工艺路径清晰"],
                conclusion="具备实用性",
                confidence=0.9,
                weight=1.0,
            )
        )

        self.add_rule(
            QualitativeRule(
                rule_id="utility_002",
                rule_type=RuleType.UTILITY,
                category=RuleCategory.POSITIVE,
                name="可使用性",
                description="能够产生积极效果",
                conditions=["技术效果明确", "可实际应用"],
                conclusion="具备实用性",
                confidence=0.9,
                weight=1.0,
            )
        )

        # ========== 意见答复策略规则 ==========
        self.add_rule(
            QualitativeRule(
                rule_id="oa_strategy_001",
                rule_type=RuleType.OA_STRATEGY,
                category=RuleCategory.POSITIVE,
                name="区别特征强调",
                description="强调与对比文件的区别技术特征",
                conditions=["存在区别特征", "区别特征相关联"],
                conclusion="建议争辩:存在区别技术特征",
                confidence=0.85,
                weight=1.0,
            )
        )

        self.add_rule(
            QualitativeRule(
                rule_id="oa_strategy_002",
                rule_type=RuleType.OA_STRATEGY,
                category=RuleCategory.POSITIVE,
                name="技术效果论证",
                description="论证区别特征带来的技术效果",
                conditions=["技术效果可证明", "效果出人意料"],
                conclusion="建议争辩:具备创造性",
                confidence=0.9,
                weight=1.0,
            )
        )

        self.add_rule(
            QualitativeRule(
                rule_id="oa_strategy_003",
                rule_type=RuleType.OA_STRATEGY,
                category=RuleCategory.NEUTRAL,
                name="权利要求修改",
                description="通过增加技术特征进一步限定",
                conditions=["从属权利要求可用", "修改不超范围"],
                conclusion="建议修改:并入从权特征",
                confidence=0.8,
                weight=0.7,
            )
        )

        self.add_rule(
            QualitativeRule(
                rule_id="oa_strategy_004",
                rule_type=RuleType.OA_STRATEGY,
                category=RuleCategory.POSITIVE,
                name="技术领域限制",
                description="明确技术领域,缩小保护范围",
                conditions=["对比文件不同领域", "领域差异明显"],
                conclusion="建议争辩:技术领域不同",
                confidence=0.75,
                weight=0.8,
            )
        )

    def add_rule(self, rule: QualitativeRule) -> None:
        """
        添加规则

        Args:
            rule: 定性规则
        """
        self.rules[rule.rule_id] = rule
        self.by_type[rule.rule_type].append(rule.rule_id)
        self.by_category[rule.category].append(rule.rule_id)

        logger.debug(f"📜 添加规则: {rule.name}")

    def analyze_novelty(self, context: dict[str, Any]) -> RuleApplicationResult:
        """
        分析新颖性

        Args:
            context: 案例上下文,包含:
                - invention: 技术方案描述
                - prior_art: 现有技术
                - differences: 区别特征列表

        Returns:
            规则应用结果
        """
        return self._apply_rules_by_type(rule_type=RuleType.NOVELTY, context=context)

    def analyze_inventiveness(self, context: dict[str, Any]) -> RuleApplicationResult:
        """
        分析创造性

        Args:
            context: 案例上下文,包含:
                - invention: 技术方案描述
                - prior_art: 现有技术
                - technical_effect: 技术效果
                - obviousness: 是否显而易见

        Returns:
            规则应用结果
        """
        return self._apply_rules_by_type(rule_type=RuleType.INVENTIVENESS, context=context)

    def analyze_utility(self, context: dict[str, Any]) -> RuleApplicationResult:
        """
        分析实用性

        Args:
            context: 案例上下文,包含:
                - manufacturability: 可制造性
                - usability: 可使用性
                - beneficial_effect: 有益效果

        Returns:
            规则应用结果
        """
        return self._apply_rules_by_type(rule_type=RuleType.UTILITY, context=context)

    def suggest_oa_strategy(self, context: dict[str, Any]) -> RuleApplicationResult:
        """
        意见答复策略建议

        Args:
            context: 案例上下文,包含:
                - rejection_type: 驳回类型
                - prior_art: 对比文件
                - differences: 区别特征
                - technical_effects: 技术效果

        Returns:
            规则应用结果
        """
        return self._apply_rules_by_type(rule_type=RuleType.OA_STRATEGY, context=context)

    def _apply_rules_by_type(
        self, rule_type: RuleType, context: dict[str, Any]
    ) -> RuleApplicationResult:
        """
        应用指定类型的所有规则

        Args:
            rule_type: 规则类型
            context: 案例上下文

        Returns:
            规则应用结果
        """
        applied_results = []
        positive_score = 0.0
        negative_score = 0.0

        # 应用所有相关规则
        for rule_id in self.by_type[rule_type]:
            rule = self.rules[rule_id]

            # 应用规则
            result = rule.apply(context)
            applied_results.append(result)

            # 更新使用统计
            if result["applies"]:
                self.rule_usage[rule_id] += 1

                # 计算得分
                weight = result["weight"]
                confidence = result["confidence"]
                score = weight * confidence

                if result["category"] == "positive":
                    positive_score += score
                elif result["category"] == "negative":
                    negative_score += score

        # 计算净得分
        net_score = positive_score - negative_score

        # 生成结论
        conclusion = self._generate_conclusion(rule_type, net_score, applied_results)

        # 计算置信度
        applicable_rules = [r for r in applied_results if r["applies"]]
        confidence = (
            sum(r["confidence"] for r in applicable_rules) / len(applicable_rules)
            if applicable_rules
            else 0.0
        )

        return RuleApplicationResult(
            applied_rules=applied_results,
            total_rules=len(self.by_type[rule_type]),
            positive_score=positive_score,
            negative_score=negative_score,
            net_score=net_score,
            conclusion=conclusion,
            confidence=confidence,
        )

    def _generate_conclusion(
        self, rule_type: RuleType, net_score: float, applied_results: list[dict[str, Any]]
    ) -> str:
        """生成综合结论"""

        type_names = {
            RuleType.NOVELTY: "新颖性",
            RuleType.INVENTIVENESS: "创造性",
            RuleType.UTILITY: "实用性",
            RuleType.OA_STRATEGY: "意见答复策略",
        }

        type_name = type_names.get(rule_type, "")

        if net_score > 0.5:
            if rule_type == RuleType.OA_STRATEGY:
                return f"建议积极争辩{type_name}(净得分: {net_score:.2f})"
            else:
                return f"具备{type_name}(净得分: {net_score:.2f})"
        elif net_score < -0.3:
            if rule_type == RuleType.OA_STRATEGY:
                return f"建议修改权利要求(净得分: {net_score:.2f})"
            else:
                return f"不具备{type_name}(净得分: {net_score:.2f})"
        else:
            return f"{type_name}存在疑问,需要进一步分析(净得分: {net_score:.2f})"

    def get_rule_statistics(self) -> dict[str, Any]:
        """获取规则统计信息"""
        return {
            "total_rules": len(self.rules),
            "by_type": {
                rule_type.value: len(rule_ids) for rule_type, rule_ids in self.by_type.items()
            },
            "by_category": {
                category.value: len(rule_ids) for category, rule_ids in self.by_category.items()
            },
            "most_used_rules": [
                {"rule_id": rid, "usage_count": count}
                for rid, count in sorted(self.rule_usage.items(), key=lambda x: x[1], reverse=True)[
                    :10
                ]
            ],
        }


# 全局单例
_qualitative_rule_engine_instance = None


def get_qualitative_rule_engine() -> QualitativeRuleEngine:
    """获取定性规则引擎单例"""
    global _qualitative_rule_engine_instance
    if _qualitative_rule_engine_instance is None:
        _qualitative_rule_engine_instance = QualitativeRuleEngine()
    return _qualitative_rule_engine_instance


# 测试代码
async def main():
    """测试定性规则引擎"""

    print("\n" + "=" * 60)
    print("📜 专利定性规则引擎测试")
    print("=" * 60 + "\n")

    engine = get_qualitative_rule_engine()

    # 测试1:新颖性分析
    print("📝 测试1: 新颖性分析")

    novelty_context = {
        "invention": "一种基于深度学习的图像识别方法",
        "technical_field": "软件",
        "differences": ["使用新的激活函数", "采用特殊的损失函数"],
        "prior_art_contains_all": False,
    }

    result = engine.analyze_novelty(novelty_context)

    print(
        f"适用规则: {len([r for r in result.applied_rules if r['applies']])}/{result.total_rules}"
    )
    print(f"正面得分: {result.positive_score:.2f}")
    print(f"负面得分: {result.negative_score:.2f}")
    print(f"净得分: {result.net_score:.2f}")
    print(f"结论: {result.conclusion}")
    print(f"置信度: {result.confidence:.2f}\n")

    # 测试2:创造性分析
    print("📝 测试2: 创造性分析")

    inventiveness_context = {
        "invention": "一种基于深度学习的图像识别方法",
        "technical_field": "软件",
        "technical_effect": "识别准确率提升30%",
        "obviousness": False,
        "performance_improvement": 0.3,
    }

    result = engine.analyze_inventiveness(inventiveness_context)

    print(
        f"适用规则: {len([r for r in result.applied_rules if r['applies']])}/{result.total_rules}"
    )
    print(f"净得分: {result.net_score:.2f}")
    print(f"结论: {result.conclusion}\n")

    # 测试3:意见答复策略
    print("📝 测试3: 意见答复策略")

    oa_context = {
        "rejection_type": "novelty",
        "technical_field": "软件",
        "differences": ["使用新的激活函数", "采用特殊的损失函数"],
        "technical_effects": ["准确率提升30%", "速度提升50%"],
        "prior_art_different_field": True,
    }

    result = engine.suggest_oa_strategy(oa_context)

    print(f"策略建议: {result.conclusion}")

    for r in result.applied_rules:
        if r["applies"]:
            print(f"  • {r['conclusion']} (置信度: {r['confidence']:.2f})")
    print()

    # 测试4:规则统计
    print("📝 测试4: 规则统计")

    stats = engine.get_rule_statistics()
    print(json.dumps(stats, ensure_ascii=False, indent=2))

    print("\n✅ 测试完成!")


# 入口点: @async_main装饰器已添加到main函数
