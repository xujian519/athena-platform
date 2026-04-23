#!/usr/bin/env python3
from __future__ import annotations
"""
技术本体管理器 - Technical Ontology Manager
从专利文档构建技术概念知识图谱

功能:
1. 从专利文档提取技术概念
2. 构建技术概念层次结构
3. 识别技术领域分类
4. 建立概念间关系(父子、相关、替代)
5. 支持技术概念语义检索

版本: 1.0.0
创建时间: 2026-01-23
"""

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ============ 数据模型 ============


class ConceptType(Enum):
    """概念类型"""

    TECHNICAL_FIELD = "技术领域"  # 如:机械制造、电子通信
    COMPONENT = "部件"  # 如:传感器、处理器
    MATERIAL = "材料"  # 如:合金、聚合物
    METHOD = "方法"  # 如:焊接、编码
    PARAMETER = "参数"  # 如:温度、电压
    APPLICATION = "应用"  # 如:医疗、军事


class RelationType(Enum):
    """关系类型"""

    IS_A = "is_a"  # 父子关系(概念层级)
    PART_OF = "part_of"  # 组成关系
    RELATED_TO = "related_to"  # 相关关系
    ALTERNATIVE_TO = "alternative_to"  # 替代关系
    USED_FOR = "used_for"  # 用途关系
    SIMILAR_TO = "similar_to"  # 相似关系


@dataclass
class TechnicalConcept:
    """技术概念"""

    concept_id: str
    name: str
    concept_type: ConceptType
    aliases: list[str] = field(default_factory=list)
    definition: str = ""
    technical_field: str = ""
    parent_concepts: list[str] = field(default_factory=list)
    child_concepts: list[str] = field(default_factory=list)
    related_concepts: list[str] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    source_documents: list[str] = field(default_factory=list)


@dataclass
class ConceptRelation:
    """概念关系"""

    relation_id: str
    source_concept: str
    target_concept: str
    relation_type: RelationType
    weight: float = 1.0
    confidence: float = 1.0
    evidence: list[str] = field(default_factory=list)


@dataclass
class OntologyStatistics:
    """本体统计信息"""

    total_concepts: int = 0
    total_relations: int = 0
    by_type: dict[str, int] = field(default_factory=dict)
    by_field: dict[str, int] = field(default_factory=dict)
    avg_depth: float = 0.0
    connectivity: float = 0.0


# ============ 本体管理器 ============


class TechnicalOntologyManager:
    """
    技术本体管理器

    构建和管理技术概念知识图谱
    """

    # 技术领域关键词
    TECHNICAL_FIELDS = {
        "机械制造": ["机械", "传动", "结构", "装配", "加工", "成型"],
        "电子通信": ["电子", "通信", "电路", "信号", "天线", "调制"],
        "计算机软件": ["计算机", "软件", "算法", "数据", "网络", "系统"],
        "化学材料": ["化学", "材料", "合成", "反应", "催化", "聚合物"],
        "生物医药": ["医疗", "药物", "治疗", "诊断", "生物", "基因"],
        "汽车工程": ["汽车", "车辆", "发动机", "制动", "转向", "悬挂"],
    }

    # 概念提取模式
    CONCEPT_PATTERNS = {
        ConceptType.COMPONENT: [
            r"([^。]{2,10})(?:装置|设备|部件|组件|单元|模块|器|件)",
            r"([^。]{2,10})(?:传感器|处理器|控制器|执行器)",
        ],
        ConceptType.MATERIAL: [
            r"([^。]{2,10})(?:材料|合金|聚合物|化合物|元素)",
        ],
        ConceptType.METHOD: [
            r"([^。]{2,10})(?:方法|工艺|技术|流程|步骤|处理)",
        ],
        ConceptType.PARAMETER: [
            r"([^。]{2,10})(?:温度|压力|速度|频率|电压|电流|浓度)",
        ],
        ConceptType.APPLICATION: [
            r"(?:用于|应用于|适用于)([^。]{2,15})",
        ],
    }

    def __init__(self):
        """初始化本体管理器"""
        # 概念存储:concept_id -> TechnicalConcept
        self.concepts: dict[str, TechnicalConcept] = {}

        # 关系存储:relation_id -> ConceptRelation
        self.relations: dict[str, ConceptRelation] = {}

        # 快速索引
        self.name_to_id: dict[str, str] = {}  # name -> concept_id
        self.field_to_concepts: dict[str, set[str]] = defaultdict(set)  # field -> concept_ids

        logger.info("✅ 技术本体管理器初始化成功")

    def extract_concepts_from_patent(
        self, patent_data: dict[str, Any], min_confidence: float = 0.5
    ) -> list[TechnicalConcept]:
        """
        从专利文档提取技术概念

        Args:
            patent_data: 专利数据
                {
                    'title': str,
                    'abstract': str,
                    'claims': list[str],
                    'description': str,
                    'technical_field': str
                }
            min_confidence: 最小置信度阈值

        Returns:
            提取的技术概念列表
        """
        logger.info("=" * 60)
        logger.info("🔍 开始从专利文档提取技术概念")
        logger.info("=" * 60)

        # 合并文本
        full_text = self._merge_patent_text(patent_data)

        # 提取概念
        extracted_concepts = []

        for concept_type, patterns in self.CONCEPT_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, full_text)
                for match in matches:
                    concept_name = match.group(1).strip()

                    # 过滤短概念
                    if len(concept_name) < 2:
                        continue

                    # 创建概念对象
                    concept = TechnicalConcept(
                        concept_id=f"concept_{len(self.concepts)}_{hash(concept_name)}",
                        name=concept_name,
                        concept_type=concept_type,
                        technical_field=patent_data.get("technical_field", ""),
                        source_documents=[patent_data.get("patent_number", "unknown")],
                        confidence=min_confidence,
                    )

                    extracted_concepts.append(concept)

        # 去重和合并
        merged_concepts = self._merge_duplicate_concepts(extracted_concepts)

        # 添加到本体
        for concept in merged_concepts:
            self._add_concept(concept)

        logger.info(f"✅ 提取到 {len(merged_concepts)} 个技术概念")
        logger.info("=" * 60)

        return merged_concepts

    def build_relations(
        self, patent_data: dict[str, Any], concepts: list[TechnicalConcept]
    ) -> list[ConceptRelation]:
        """
        构建概念间关系

        Args:
            patent_data: 专利数据
            concepts: 技术概念列表

        Returns:
            概念关系列表
        """
        logger.info("=" * 60)
        logger.info("🔗 开始构建概念关系")
        logger.info("=" * 60)

        relations = []
        concept_map = {c.name: c for c in concepts}

        # 识别层级关系(IS_A)
        relations.extend(self._identify_is_a_relations(concepts))

        # 识别组成关系(PART_OF)
        relations.extend(self._identify_part_of_relations(patent_data, concept_map))

        # 识别相关关系(RELATED_TO)
        relations.extend(self._identify_related_relations(concepts))

        # 添加到本体
        for relation in relations:
            self._add_relation(relation)

        logger.info(f"✅ 构建了 {len(relations)} 个概念关系")
        logger.info("=" * 60)

        return relations

    def classify_technical_field(self, text: str) -> str:
        """
        分类技术领域

        Args:
            text: 文本内容

        Returns:
            技术领域名称
        """
        scores = {}

        for field_name, keywords in self.TECHNICAL_FIELDS.items():
            score = sum(1 for keyword in keywords if keyword in text)
            scores[field_name] = score

        # 返回得分最高的领域
        if scores:
            max_field = max(scores.keys(), key=lambda k: scores[k])
            return max_field if scores[max_field] > 0 else "其他"

        return "未分类"

    def get_concept_by_name(self, name: str) -> TechnicalConcept | None:
        """根据名称获取概念"""
        concept_id = self.name_to_id.get(name)
        return self.concepts.get(concept_id) if concept_id else None

    def get_related_concepts(
        self,
        concept: TechnicalConcept,
        relation_type: RelationType | None = None,
        max_depth: int = 1,
    ) -> list[TechnicalConcept]:
        """
        获取相关概念

        Args:
            concept: 起始概念
            relation_type: 关系类型(None表示所有类型)
            max_depth: 最大深度

        Returns:
            相关概念列表
        """
        related = []
        visited = set()
        to_visit = [(concept, 0)]

        while to_visit:
            current_concept, depth = to_visit.pop(0)

            if depth >= max_depth:
                continue

            if current_concept.concept_id in visited:
                continue

            visited.add(current_concept.concept_id)

            # 获取相关概念ID
            related_ids = []
            if relation_type is None:
                related_ids.extend(current_concept.parent_concepts)
                related_ids.extend(current_concept.child_concepts)
                related_ids.extend(current_concept.related_concepts)
            else:
                # 根据关系类型获取
                for relation in self.relations.values():
                    if relation.source_concept == current_concept.concept_id:
                        if relation.relation_type == relation_type:
                            related_ids.append(relation.target_concept)

            # 添加到结果
            for concept_id in related_ids:
                if concept_id in self.concepts:
                    related_concept = self.concepts[concept_id]
                    if related_concept.concept_id not in visited:
                        related.append(related_concept)
                        to_visit.append((related_concept, depth + 1))

        return related

    def get_statistics(self) -> OntologyStatistics:
        """获取本体统计信息"""
        by_type = defaultdict(int)
        by_field = defaultdict(int)

        for concept in self.concepts.values():
            by_type[concept.concept_type.value] += 1
            if concept.technical_field:
                by_field[concept.technical_field] += 1

        # 计算平均深度
        total_depth = sum(
            self._calculate_concept_depth(concept) for concept in self.concepts.values()
        )
        avg_depth = total_depth / len(self.concepts) if self.concepts else 0.0

        # 计算连通性
        connectivity = len(self.relations) / len(self.concepts) if self.concepts else 0.0

        return OntologyStatistics(
            total_concepts=len(self.concepts),
            total_relations=len(self.relations),
            by_type=dict(by_type),
            by_field=dict(by_field),
            avg_depth=avg_depth,
            connectivity=connectivity,
        )

    def _merge_patent_text(self, patent_data: dict[str, Any]) -> str:
        """合并专利文本"""
        parts = [
            patent_data.get("title", ""),
            patent_data.get("abstract", ""),
            " ".join(patent_data.get("claims", [])),
            patent_data.get("description", ""),
        ]
        return " ".join(parts)

    def _merge_duplicate_concepts(self, concepts: list[TechnicalConcept]) -> list[TechnicalConcept]:
        """合并重复概念"""
        merged = {}
        for concept in concepts:
            name_key = concept.name.lower()

            if name_key in merged:
                # 合并到现有概念
                existing = merged[name_key]
                existing.source_documents.extend(concept.source_documents)
                existing.aliases.extend(concept.aliases)
                existing.confidence = max(existing.confidence, concept.confidence)
            else:
                merged[name_key] = concept

        return list(merged.values())

    def _add_concept(self, concept: TechnicalConcept):
        """添加概念到本体"""
        self.concepts[concept.concept_id] = concept
        self.name_to_id[concept.name.lower()] = concept.concept_id

        if concept.technical_field:
            self.field_to_concepts[concept.technical_field].add(concept.concept_id)

    def _add_relation(self, relation: ConceptRelation):
        """添加关系到本体"""
        self.relations[relation.relation_id] = relation

        # 更新概念的邻接列表
        if relation.source_concept in self.concepts:
            source_concept = self.concepts[relation.source_concept]
            if relation.relation_type == RelationType.IS_A:
                # 父子关系
                if relation.target_concept not in source_concept.parent_concepts:
                    source_concept.parent_concepts.append(relation.target_concept)
                if (
                    relation.source_concept
                    not in self.concepts[relation.target_concept].child_concepts
                ):
                    self.concepts[relation.target_concept].child_concepts.append(
                        relation.source_concept
                    )
            else:
                # 其他关系
                if relation.target_concept not in source_concept.related_concepts:
                    source_concept.related_concepts.append(relation.target_concept)

    def _identify_is_a_relations(self, concepts: list[TechnicalConcept]) -> list[ConceptRelation]:
        """识别IS_A关系"""
        relations = []

        # 简化实现:基于概念类型的层次关系

        for concept in concepts:
            # 查找可能的父概念
            for other in concepts:
                if concept.concept_id == other.concept_id:
                    continue

                # 检查名称包含关系
                if (
                    concept.name in other.name or other.name in concept.name
                ) and concept.name != other.name:
                    # 较短的概念是父概念
                    parent, child = (
                        (concept, other)
                        if len(concept.name) < len(other.name)
                        else (other, concept)
                    )

                    relation = ConceptRelation(
                        relation_id=f"rel_is_a_{parent.concept_id}_{child.concept_id}",
                        source_concept=child.concept_id,
                        target_concept=parent.concept_id,
                        relation_type=RelationType.IS_A,
                        confidence=0.7,
                    )
                    relations.append(relation)

        return relations

    def _identify_part_of_relations(
        self, patent_data: dict[str, Any], concept_map: dict[str, TechnicalConcept]
    ) -> list[ConceptRelation]:
        """识别PART_OF关系"""
        relations = []
        text = self._merge_patent_text(patent_data)

        # 查找"X包括Y"模式
        include_pattern = r"([^。]{2,10})包括([^。]{2,10})"
        matches = re.findall(include_pattern, text)

        for parent_name, child_name in matches:
            parent = concept_map.get(parent_name.strip())
            child = concept_map.get(child_name.strip())

            if parent and child:
                relation = ConceptRelation(
                    relation_id=f"rel_part_of_{child.concept_id}_{parent.concept_id}",
                    source_concept=child.concept_id,
                    target_concept=parent.concept_id,
                    relation_type=RelationType.PART_OF,
                    evidence=[f"{parent_name}包括{child_name}"],
                    confidence=0.8,
                )
                relations.append(relation)

        return relations

    def _identify_related_relations(
        self, concepts: list[TechnicalConcept]
    ) -> list[ConceptRelation]:
        """识别RELATED_TO关系"""
        relations = []

        # 简化实现:同类型的概念可能是相关的
        for i, concept1 in enumerate(concepts):
            for concept2 in concepts[i + 1 :]:
                if concept1.concept_type == concept2.concept_type:
                    # 检查是否在同一技术领域
                    if concept1.technical_field == concept2.technical_field:
                        relation = ConceptRelation(
                            relation_id=f"rel_related_{concept1.concept_id}_{concept2.concept_id}",
                            source_concept=concept1.concept_id,
                            target_concept=concept2.concept_id,
                            relation_type=RelationType.RELATED_TO,
                            confidence=0.5,
                        )
                        relations.append(relation)

        return relations

    def _calculate_concept_depth(self, concept: TechnicalConcept) -> int:
        """计算概念深度(层级深度)"""
        if not concept.parent_concepts:
            return 0

        max_parent_depth = 0
        for parent_id in concept.parent_concepts:
            if parent_id in self.concepts:
                parent_depth = self._calculate_concept_depth(self.concepts[parent_id])
                max_parent_depth = max(max_parent_depth, parent_depth)

        return max_parent_depth + 1


# ============ 主函数 ============


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="技术本体管理器测试")
    parser.add_argument("--test", action="store_true", help="运行测试")
    parser.add_argument("--input", type=str, help="输入专利文件(JSON)")
    parser.add_argument("--output", type=str, help="输出本体文件(JSON)")

    args = parser.parse_args()

    if args.test:
        test_ontology_manager()
    elif args.input:
        build_from_file(args.input, args.output)


def test_ontology_manager():
    """测试本体管理器"""
    print("🧪 测试技术本体管理器")

    manager = TechnicalOntologyManager()

    # 模拟专利数据
    mock_patent = {
        "title": "一种智能传感器装置",
        "abstract": "本发明涉及一种智能传感器装置,包括传感器单元、处理器和通信模块",
        "claims": [
            "一种智能传感器装置,其特征在于,包括传感器单元、处理器和通信模块",
            "根据权利要求1所述的装置,传感器单元为温度传感器",
        ],
        "description": "本发明提供了一种智能传感器装置,用于实时监测环境参数",
        "technical_field": "电子通信",
        "patent_number": "CN202010123456.7",
    }

    # 提取概念
    concepts = manager.extract_concepts_from_patent(mock_patent)

    print(f"\n✅ 提取到 {len(concepts)} 个技术概念")
    for concept in concepts[:5]:
        print(f"  - {concept.name} ({concept.concept_type.value})")

    # 构建关系
    relations = manager.build_relations(mock_patent, concepts)

    print(f"\n✅ 构建了 {len(relations)} 个概念关系")
    for relation in relations[:5]:
        source = manager.concepts.get(relation.source_concept)
        target = manager.concepts.get(relation.target_concept)
        if source and target:
            print(f"  - {source.name} --[{relation.relation_type.value}]--> {target.name}")

    # 统计信息
    stats = manager.get_statistics()
    print("\n📊 本体统计:")
    print(f"  总概念数: {stats.total_concepts}")
    print(f"  总关系数: {stats.total_relations}")
    print(f"  平均深度: {stats.avg_depth:.2f}")
    print(f"  连通性: {stats.connectivity:.2f}")
    print("  按类型分布:")
    for concept_type, count in stats.by_type.items():
        print(f"    {concept_type}: {count}")


def build_from_file(input_file: str, output_file: Optional[str] = None):
    """从文件构建本体"""
    print(f"📄 读取文件: {input_file}")

    import json

    with open(input_file, encoding="utf-8") as f:
        patent_data = json.load(f)

    manager = TechnicalOntologyManager()

    # 提取概念
    concepts = manager.extract_concepts_from_patent(patent_data)

    # 构建关系
    manager.build_relations(patent_data, concepts)

    print("✅ 本体构建完成")

    if output_file:
        # 导出为JSON
        output_data = {
            "statistics": {
                "total_concepts": len(manager.concepts),
                "total_relations": len(manager.relations),
            },
            "concepts": [
                {
                    "id": c.concept_id,
                    "name": c.name,
                    "type": c.concept_type.value,
                    "field": c.technical_field,
                }
                for c in manager.concepts.values()
            ],
            "relations": [
                {
                    "source": r.source_concept,
                    "target": r.target_concept,
                    "type": r.relation_type.value,
                }
                for r in manager.relations.values()
            ],
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 结果已保存到: {output_file}")


if __name__ == "__main__":
    main()
