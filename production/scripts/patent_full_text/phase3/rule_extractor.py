#!/usr/bin/env python3
"""
规则提取器
Rule Extractor

基于规则和关键词的问题-特征-效果三元组提取

作者: Athena平台团队
创建时间: 2025-12-25
"""

from __future__ import annotations
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ProblemType(Enum):
    """问题类型"""
    TECHNICAL = "technical"      # 技术问题
    EFFICIENCY = "efficiency"    # 效率问题
    COST = "cost"               # 成本问题
    SAFETY = "safety"           # 安全问题


class FeatureCategory(Enum):
    """特征类别"""
    STRUCTURAL = "structural"    # 结构特征
    FUNCTIONAL = "functional"    # 功能特征
    PERFORMANCE = "performance"  # 性能特征


class RelationType(Enum):
    """特征关系类型"""
    COMBINATIONAL = "combinational"  # 组合关系
    DEPENDENT = "dependent"          # 依赖关系
    ALTERNATIVE = "alternative"      # 替代关系
    SEQUENTIAL = "sequential"        # 顺序关系
    HIERARCHICAL = "hierarchical"    # 层次关系
    CAUSAL = "causal"               # 因果关系


@dataclass
class TechnicalProblem:
    """技术问题"""
    id: str
    description: str
    problem_type: str = ProblemType.TECHNICAL.value
    source_section: str = "invention_content"  # background/invention_content
    severity: float = 0.5  # 0-1

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "problem_type": self.problem_type,
            "source_section": self.source_section,
            "severity": self.severity
        }


@dataclass
class TechnicalFeature:
    """技术特征"""
    id: str
    description: str
    feature_category: str = FeatureCategory.STRUCTURAL.value
    feature_type: str = "component"  # component/parameter/process/structure
    source_claim: int = 0
    importance: float = 0.5  # 0-1

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "feature_category": self.feature_category,
            "feature_type": self.feature_type,
            "source_claim": self.source_claim,
            "importance": self.importance
        }


@dataclass
class TechnicalEffect:
    """技术效果"""
    id: str
    description: str
    effect_type: str = "direct"  # direct/indirect
    quantifiable: bool = False
    metrics: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "effect_type": self.effect_type,
            "quantifiable": self.quantifiable,
            "metrics": self.metrics
        }


@dataclass
class FeatureRelation:
    """特征关系"""
    from_feature: str
    to_feature: str
    relation_type: str
    strength: float = 0.5  # 0-1
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_feature": self.from_feature,
            "to_feature": self.to_feature,
            "relation_type": self.relation_type,
            "strength": self.strength,
            "description": self.description
        }


@dataclass
class Triple:
    """三元组"""
    subject: str    # 通常是feature
    relation: str   # SOLVES/ACHIEVES
    object: str     # problem/effect
    confidence: float = 0.7

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "relation": self.relation,
            "object": self.object,
            "confidence": self.confidence
        }


@dataclass
class TripleExtractionResult:
    """三元组提取结果"""
    patent_number: str
    success: bool

    # 提取的实体和关系
    problems: list[TechnicalProblem] = field(default_factory=list)
    features: list[TechnicalFeature] = field(default_factory=list)
    effects: list[TechnicalEffect] = field(default_factory=list)
    triples: list[Triple] = field(default_factory=list)
    feature_relations: list[FeatureRelation] = field(default_factory=list)

    # 统计信息
    processing_time: float = 0.0
    error_message: str | None = None
    extraction_confidence: float = 0.0

    def get_summary(self) -> dict[str, Any]:
        """获取提取摘要"""
        return {
            "patent_number": self.patent_number,
            "success": self.success,
            "problem_count": len(self.problems),
            "feature_count": len(self.features),
            "effect_count": len(self.effects),
            "triple_count": len(self.triples),
            "relation_count": len(self.feature_relations),
            "confidence": self.extraction_confidence,
            "processing_time": self.processing_time
        }


class RuleExtractor:
    """
    规则提取器

    基于规则和关键词提取:
    1. 技术问题
    2. 技术特征
    3. 技术效果
    4. 问题-特征-效果三元组
    5. 特征间关系
    """

    # ========== 问题关键词模式 ==========
    PROBLEM_PATTERNS = [
        r'(?:现有|传统|当前)(?:技术|方法|系统|装置)(?:存在|具有)?(?:的)?(?:以下)?(?:问题|缺陷|不足|缺点|局限性)',
        r'(?:难以|无法|不能|不便)(?:满足|实现|达到|解决)',
        r'(?:效率|精度|准确率|稳定性)(?:低|差|不高|不足)',
        r'(?:成本|费用|消耗)(?:高|大|过多)',
        r'(?:需要|需要解决|亟待解决)(?:的)?问题',
    ]

    # ========== 特征关键词模式 ==========
    FEATURE_PATTERNS = [
        r'(?:所述|其|该)(?:特征在于|包括|包含|设有|配置有|具有)',
        r'(?:通过|采用|使用|利用)(?:\w+)(?:模块|单元|部件|装置|组件|系统)',
        r'(?:设置|安装|连接|布置)(?:的)?(?:\w+)(?:结构|装置|组件)',
    ]

    # ========== 效果关键词模式 ==========
    EFFECT_PATTERNS = [
        r'(?:能够|可以|有助于)(?:实现|达到|提高|降低|减少|增强|改善)',
        r'(?:具有|具备|拥有)(?:以下)?(?:优点|优势|有益效果|积极效果)',
        r'(?:提高|降低|减少|增强|改善|优化)(?:了)?(?:效率|精度|性能|质量)',
        r'(?:相比|相对于|较之)(?:现有技术|传统方法)',
    ]

    # ========== 关系模式 ==========
    RELATION_PATTERNS = {
        RelationType.COMBINATIONAL: [
            r'(?:结合|组合|配合|协同)',
            r'(?:同时|分别)(?:设置|配置|采用)',
        ],
        RelationType.DEPENDENT: [
            r'(?:依赖于|基于|根据)',
            r'(?:通过|利用)(?:\w+)(?:实现|完成)',
        ],
        RelationType.ALTERNATIVE: [
            r'(?:或者|或是|可选择地)',
            r'(?:也可?以替换?为?)',
        ],
        RelationType.SEQUENTIAL: [
            r'(?:先|后|然后|接着|随后)',
            r'(?:首先|其次|最后)',
        ],
        RelationType.HIERARCHICAL: [
            r'(?:包括|包含)(?:以下)?(?:的)?',
            r'(?:其中|其特征在于)',
        ],
        RelationType.CAUSAL: [
            r'(?:从而|因此|因而|所以)',
            r'(?:导致|引起|使得)',
        ]
    }

    def __init__(self):
        """初始化提取器"""
        # 编译所有正则表达式
        self.compiled_problem_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.PROBLEM_PATTERNS
        ]
        self.compiled_feature_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.FEATURE_PATTERNS
        ]
        self.compiled_effect_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.EFFECT_PATTERNS
        ]

        self.compiled_relation_patterns = {}
        for rel_type, patterns in self.RELATION_PATTERNS.items():
            self.compiled_relation_patterns[rel_type] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

    def extract(
        self,
        patent_number: str,
        patent_text: str,
        claims: str | None = None,
        invention_content: str | None = None
    ) -> TripleExtractionResult:
        """
        提取三元组

        Args:
            patent_number: 专利号
            patent_text: 专利全文（可选，如果不提供则需要claims和invention_content）
            claims: 权利要求书
            invention_content: 发明内容

        Returns:
            TripleExtractionResult
        """
        import time
        start_time = time.time()

        try:
            result = TripleExtractionResult(
                patent_number=patent_number,
                success=True
            )

            # 合并文本
            full_text = patent_text or ""
            if claims:
                full_text += "\n" + claims
            if invention_content:
                full_text += "\n" + invention_content

            # 1. 提取技术问题
            result.problems = self._extract_problems(patent_number, full_text)

            # 2. 提取技术特征
            result.features = self._extract_features(
                patent_number,
                full_text,
                claims or ""
            )

            # 3. 提取技术效果
            result.effects = self._extract_effects(patent_number, full_text)

            # 4. 构建三元组
            result.triples = self._build_triples(
                result.problems,
                result.features,
                result.effects
            )

            # 5. 提取特征关系
            result.feature_relations = self._extract_feature_relations(
                result.features,
                full_text
            )

            # 6. 计算置信度
            result.extraction_confidence = self._calculate_confidence(result)

            result.processing_time = time.time() - start_time

            logger.info(f"✅ 规则提取完成: {len(result.problems)}问题, "
                       f"{len(result.features)}特征, {len(result.effects)}效果, "
                       f"{len(result.triples)}三元组")

            return result

        except Exception as e:
            logger.error(f"❌ 提取失败: {e}")
            return TripleExtractionResult(
                patent_number=patent_number,
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )

    def _extract_problems(
        self,
        patent_number: str,
        text: str
    ) -> list[TechnicalProblem]:
        """提取技术问题"""
        problems = []
        seen_descriptions: set[str] = set()

        # 按句子分割
        sentences = re.split(r'[。！？.!?]', text)

        for _i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence or len(sentence) < 10:
                continue

            # 匹配问题模式
            for pattern in self.compiled_problem_patterns:
                if pattern.search(sentence):
                    # 去重
                    if sentence not in seen_descriptions:
                        problem_type = self._classify_problem_type(sentence)

                        problem = TechnicalProblem(
                            id=f"{patent_number}_p_{len(problems)}",
                            description=sentence,
                            problem_type=problem_type,
                            severity=self._calculate_severity(sentence)
                        )
                        problems.append(problem)
                        seen_descriptions.add(sentence)
                    break

        return problems

    def _extract_features(
        self,
        patent_number: str,
        text: str,
        claims: str
    ) -> list[TechnicalFeature]:
        """提取技术特征"""
        features = []
        seen_descriptions: set[str] = set()

        # 优先从权利要求提取
        if claims:
            # 按条款分割
            claim_texts = re.split(r'\n\s*\d+\.', claims)
            for claim_text in claim_texts:
                if not claim_text.strip():
                    continue

                # 提取特征关键词后的内容
                for pattern in self.compiled_feature_patterns:
                    matches = pattern.finditer(claim_text)
                    for match in matches:
                        # 提取特征描述（匹配位置后一定长度）
                        start = match.start()
                        end = min(start + 100, len(claim_text))
                        feature_desc = claim_text[start:end].strip()

                        if feature_desc and len(feature_desc) > 5:
                            if feature_desc[:50] not in seen_descriptions:
                                feature = TechnicalFeature(
                                    id=f"{patent_number}_f_{len(features)}",
                                    description=feature_desc[:100],
                                    feature_category=self._classify_feature_category(feature_desc),
                                    feature_type=self._classify_feature_type(feature_desc),
                                    importance=0.7
                                )
                                features.append(feature)
                                seen_descriptions.add(feature_desc[:50])

        # 如果权利要求中特征太少，从全文补充
        if len(features) < 5:
            sentences = re.split(r'[。！？.!?]', text)
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence or len(sentence) < 15:
                    continue

                for pattern in self.compiled_feature_patterns:
                    if pattern.search(sentence):
                        if sentence[:50] not in seen_descriptions:
                            feature = TechnicalFeature(
                                id=f"{patent_number}_f_{len(features)}",
                                description=sentence[:100],
                                feature_category=self._classify_feature_category(sentence),
                                feature_type=self._classify_feature_type(sentence),
                                importance=0.5
                            )
                            features.append(feature)
                            seen_descriptions.add(sentence[:50])
                        break

        return features

    def _extract_effects(
        self,
        patent_number: str,
        text: str
    ) -> list[TechnicalEffect]:
        """提取技术效果"""
        effects = []
        seen_descriptions: set[str] = set()

        # 按句子分割
        sentences = re.split(r'[。！？.!?]', text)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 10:
                continue

            # 匹配效果模式
            for pattern in self.compiled_effect_patterns:
                if pattern.search(sentence):
                    if sentence not in seen_descriptions:
                        # 检测是否可量化
                        quantifiable = bool(re.search(r'\d+[%％]', sentence))
                        metrics = ""
                        if quantifiable:
                            metric_match = re.search(r'\d+[%％]', sentence)
                            if metric_match:
                                metrics = metric_match.group()

                        effect = TechnicalEffect(
                            id=f"{patent_number}_e_{len(effects)}",
                            description=sentence,
                            effect_type="direct" if "直接" in sentence else "indirect",
                            quantifiable=quantifiable,
                            metrics=metrics
                        )
                        effects.append(effect)
                        seen_descriptions.add(sentence)
                    break

        return effects

    def _build_triples(
        self,
        problems: list[TechnicalProblem],
        features: list[TechnicalFeature],
        effects: list[TechnicalEffect]
    ) -> list[Triple]:
        """
        构建三元组

        策略:
        1. 特征SOLVES问题
        2. 特征ACHIEVES效果
        """
        triples = []

        # 简单策略: 所有特征都关联所有问题和效果
        # (实际应用中应该更智能地匹配)

        # Feature SOLVES Problem
        for feature in features:
            for problem in problems:
                triple = Triple(
                    subject=feature.id,
                    relation="SOLVES",
                    object=problem.id,
                    confidence=0.6  # 规则提取置信度较低
                )
                triples.append(triple)

        # Feature ACHIEVES Effect
        for feature in features:
            for effect in effects:
                triple = Triple(
                    subject=feature.id,
                    relation="ACHIEVES",
                    object=effect.id,
                    confidence=0.6
                )
                triples.append(triple)

        return triples

    def _extract_feature_relations(
        self,
        features: list[TechnicalFeature],
        text: str
    ) -> list[FeatureRelation]:
        """提取特征间关系"""
        relations = []

        # 简化实现: 在文本中查找特征共现并推断关系
        feature_ids = [f.id for f in features]
        feature_descs = {f.id: f.description for f in features}

        for i, feature1 in enumerate(features):
            for feature2 in features[i + 1:]:
                # 检查两个特征是否在同一段落中出现
                # 简单实现: 在文本中查找它们之间的距离

                # 尝试各种关系类型
                for rel_type, patterns in self.compiled_relation_patterns.items():
                    for pattern in patterns:
                        # 在两个特征描述之间搜索关系词
                        # 这里简化处理，实际需要更复杂的文本分析
                        if pattern.search(text):
                            relation = FeatureRelation(
                                from_feature=feature1.id,
                                to_feature=feature2.id,
                                relation_type=rel_type.value,
                                strength=0.5,
                                description=""
                            )
                            relations.append(relation)
                            break

        return relations

    def _classify_problem_type(self, text: str) -> str:
        """分类问题类型"""
        if any(word in text for word in ['效率', '速度', '慢', '快']):
            return ProblemType.EFFICIENCY.value
        elif any(word in text for word in ['成本', '费用', '价格']):
            return ProblemType.COST.value
        elif any(word in text for word in ['安全', '危险', '风险']):
            return ProblemType.SAFETY.value
        else:
            return ProblemType.TECHNICAL.value

    def _classify_feature_category(self, text: str) -> str:
        """分类特征类别"""
        if any(word in text for word in ['结构', '构造', '组成', '部件']):
            return FeatureCategory.STRUCTURAL.value
        elif any(word in text for word in ['性能', '效果', '精度']):
            return FeatureCategory.PERFORMANCE.value
        else:
            return FeatureCategory.FUNCTIONAL.value

    def _classify_feature_type(self, text: str) -> str:
        """分类特征类型"""
        if any(word in text for word in ['模块', '单元', '组件', '部件']):
            return "component"
        elif any(word in text for word in ['参数', '数值', '范围']):
            return "parameter"
        elif any(word in text for word in ['步骤', '方法', '流程']):
            return "process"
        else:
            return "structure"

    def _calculate_severity(self, text: str) -> float:
        """计算问题严重程度"""
        severity = 0.5

        if any(word in text for word in ['严重', '重大', '关键']):
            severity = 0.8
        elif any(word in text for word in ['一定', '存在']):
            severity = 0.6
        elif any(word in text for word in ['轻微', '较小']):
            severity = 0.3

        return severity

    def _calculate_confidence(self, result: TripleExtractionResult) -> float:
        """计算整体提取置信度"""
        # 规则提取的置信度通常较低
        base_confidence = 0.6

        # 根据提取结果数量调整
        if len(result.problems) > 0 and len(result.features) > 0 and len(result.effects) > 0:
            base_confidence += 0.1

        if len(result.triples) > 0:
            base_confidence += 0.1

        return min(base_confidence, 1.0)


# ========== 便捷函数 ==========

def extract_triples(
    patent_number: str,
    patent_text: str,
    claims: str | None = None,
    invention_content: str | None = None
) -> TripleExtractionResult:
    """
    提取三元组

    Args:
        patent_number: 专利号
        patent_text: 专利全文
        claims: 权利要求书
        invention_content: 发明内容

    Returns:
        TripleExtractionResult
    """
    extractor = RuleExtractor()
    return extractor.extract(patent_number, patent_text, claims, invention_content)


# ========== 示例使用 ==========

def main() -> None:
    """示例使用"""
    print("=" * 70)
    print("规则提取器 示例")
    print("=" * 70)

    # 示例专利文本
    sample_claims = """
    1. 一种基于深度学习的图像识别方法，其特征在于，包括：
       获取待识别图像；
       使用卷积神经网络提取图像特征；
       通过注意力机制加权融合特征；
       输出分类结果。
    """

    sample_content = """
    技术问题：现有图像识别方法在复杂场景下精度较低，
    计算效率不高，难以满足实时性要求。

    技术方案：本发明提供一种基于深度学习的图像识别方法，
    包括卷积神经网络模型和注意力机制模块。

    有益效果：与现有技术相比，本发明识别准确率提高15%，
    计算速度提升50%。
    """

    # 提取
    result = extract_triples(
        "CN112233445A",
        "",
        sample_claims,
        sample_content
    )

    print("\n📊 提取结果:")
    summary = result.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    print(f"\n📄 技术问题 ({len(result.problems)}个):")
    for problem in result.problems:
        print(f"  [{problem.problem_type}] {problem.description[:60]}...")

    print(f"\n📄 技术特征 ({len(result.features)}个):")
    for feature in result.features[:5]:
        print(f"  [{feature.feature_category}] {feature.description[:60]}...")

    print(f"\n📄 技术效果 ({len(result.effects)}个):")
    for effect in result.effects:
        print(f"  [{effect.effect_type}] {effect.description[:60]}...")

    print(f"\n🔗 三元组 ({len(result.triples)}个):")
    for triple in result.triples[:3]:
        print(f"  {triple.subject} --[{triple.relation}]--> {triple.object}")


if __name__ == "__main__":
    main()
