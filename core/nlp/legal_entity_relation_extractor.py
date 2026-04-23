#!/usr/bin/env python3
from __future__ import annotations
"""
法律文档专用实体关系提取器
Legal Document Entity and Relation Extractor

专门针对专利法律文档的实体和关系提取
"""

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """实体"""

    text: str
    type: str
    start: int
    end: int
    confidence: float
    metadata: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        d = {
            "text": self.text,
            "type": self.type,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
        }
        if self.metadata:
            d["metadata"] = self.metadata
        return d


@dataclass
class Relation:
    """关系"""

    subject: str
    predicate: str
    object: str
    confidence: float
    evidence: str = ""
    metadata: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        d = {
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "confidence": self.confidence,
            "evidence": self.evidence,
        }
        if self.metadata:
            d["metadata"] = self.metadata
        return d


class LegalEntityRelationExtractor:
    """法律文档实体关系提取器"""

    # 法律文档特有的实体类型
    LEGAL_ENTITY_TYPES = {
        "LAW_CONCEPT": "法律概念",
        "LEGAL_PRINCIPLE": "法律原则",
        "LAW_REQUIREMENT": "法律要求",
        "RIGHT": "权利",
        "OBLIGATION": "义务",
        "CONDITION": "条件",
        "PROCEDURE": "程序",
        "AUTHORITY": "机关",
        "TIME_LIMIT": "时限",
        "LEGAL_TERM": "法律术语",
        # 通用实体
        "PATENT_NUMBER": "专利号",
        "DATE": "日期",
        "ORGANIZATION": "机构",
        "ARTICLE_REFERENCE": "法条引用",
        "LAW_REFERENCE": "法律引用",
    }

    # 法律文档特有的关系类型
    LEGAL_RELATION_TYPES = {
        "DEFINES": "定义",
        "REQUIRES": "要求",
        "PROHIBITS": "禁止",
        "AUTHORIZES": "授权",
        "REFERS_TO": "引用",
        "BASED_ON": "基于",
        "EXCEPTION_TO": "例外",
        "CONDITION_FOR": "条件",
        "MODIFIES": "修改",
        "REPLACES": "替代",
        "SUPERSEDES": "废止",
        "INTERPRETS": "解释",
        "SPECIFIES": "规定",
        "ESTABLISHES": "建立",
        "EXEMPTS": "豁免",
    }

    def __init__(self):
        """初始化提取器"""
        self._compile_patterns()

    def _compile_patterns(self) -> Any:
        """编译正则表达式模式"""

        # 法律概念模式(常见的法律术语)
        self.concept_patterns = [
            r"新颖性",
            r"创造性",
            r"实用性",
            r"优先权",
            r"专利权",
            r"发明创造",
            r"发明",
            r"实用新型",
            r"外观设计",
            r"专利申请",
            r"专利代理人",
            r"专利复审委员会",
            r"无效宣告",
            r"强制许可",
            r"侵权",
            r"公开",
            r"驳回",
            r"授予",
            r"期限",
            r"费用",
            r"保护",
            r"审查",
            r"公布",
            r"异议",
        ]

        # 法律要求/条件模式
        self.requirement_patterns = [
            r"应当[^。,]{0,50}",
            r"必须[^。,]{0,50}",
            r"可以[^。,]{0,50}",
            r"不得[^。,]{0,50}",
            r"禁止[^。,]{0,50}",
            r"有权[^。,]{0,50}",
            r"义务[^。,]{0,50}",
            r"责任[^。,]{0,50}",
        ]

        # 法条引用模式
        self.article_ref_patterns = [
            r"本法第[一二三四五六七八九十\d]+条",
            r"专利法实施细则第[一二三四五六七八九十\d]+条",
            r"根据[专利法实施细则]{0,10}第[一二三四五六七八九十\d]+条",
            r"依照[专利法实施细则]{0,10}第[一二三四五六七八九十\d]+条",
            r"按照[专利法实施细则]{0,10}第[一二三四五六七八九十\d]+条",
        ]

        # 法律引用模式
        self.law_ref_patterns = [
            r"专利法",
            r"专利法实施细则",
            r"审查指南",
            r"民法典",
            r"行政诉讼法",
        ]

    def extract_entities(
        self, text: str, entity_types: list[str] = None
    ) -> list[dict[str, Any]]:
        """
        提取法律文档实体

        Args:
            text: 输入文本
            entity_types: 要提取的实体类型,None表示全部

        Returns:
            实体列表
        """
        entities = []

        if entity_types is None:
            entity_types = list(self.LEGAL_ENTITY_TYPES.keys())

        # 1. 提取法律概念
        if "LAW_CONCEPT" in entity_types:
            for concept in self.concept_patterns:
                pattern = re.compile(concept)
                for match in pattern.finditer(text):
                    # 避免重复
                    if not any(
                        e["start"] <= match.start() and e["end"] >= match.end() for e in entities
                    ):
                        entities.append(
                            {
                                "text": match.group(),
                                "type": "LAW_CONCEPT",
                                "start": match.start(),
                                "end": match.end(),
                                "confidence": 0.95,
                                "metadata": {"category": "法律概念"},
                            }
                        )

        # 2. 提取法条引用
        if "ARTICLE_REFERENCE" in entity_types:
            for pattern_str in self.article_ref_patterns:
                pattern = re.compile(pattern_str)
                for match in pattern.finditer(text):
                    if not any(
                        e["start"] <= match.start() and e["end"] >= match.end() for e in entities
                    ):
                        entities.append(
                            {
                                "text": match.group(),
                                "type": "ARTICLE_REFERENCE",
                                "start": match.start(),
                                "end": match.end(),
                                "confidence": 0.99,
                                "metadata": {"category": "法条引用"},
                            }
                        )

        # 3. 提取法律引用
        if "LAW_REFERENCE" in entity_types:
            for pattern_str in self.law_ref_patterns:
                pattern = re.compile(pattern_str)
                for match in pattern.finditer(text):
                    if not any(
                        e["start"] <= match.start() and e["end"] >= match.end() for e in entities
                    ):
                        entities.append(
                            {
                                "text": match.group(),
                                "type": "LAW_REFERENCE",
                                "start": match.start(),
                                "end": match.end(),
                                "confidence": 0.98,
                                "metadata": {"category": "法律引用"},
                            }
                        )

        # 4. 提取日期
        if "DATE" in entity_types:
            date_pattern = re.compile(
                r"\d{4}年\d{1,2}月\d{1,2}日|\d{4}-\d{1,2}-\d{1,2}|\d{4}\.\d{1,2}\.\d{1,2}"
            )
            for match in date_pattern.finditer(text):
                if not any(
                    e["start"] <= match.start() and e["end"] >= match.end() for e in entities
                ):
                    entities.append(
                        {
                            "text": match.group(),
                            "type": "DATE",
                            "start": match.start(),
                            "end": match.end(),
                            "confidence": 0.98,
                            "metadata": {"category": "日期"},
                        }
                    )

        # 5. 提取机构
        if "AUTHORITY" in entity_types or "ORGANIZATION" in entity_types:
            org_patterns = [
                r"国务院专利行政部门",
                r"专利复审委员会",
                r"国家知识产权局",
                r"专利局",
                r"人民法院",
                r"最高人民法院",
                r"专利代理机构",
            ]
            for pattern_str in org_patterns:
                pattern = re.compile(pattern_str)
                for match in pattern.finditer(text):
                    if not any(
                        e["start"] <= match.start() and e["end"] >= match.end() for e in entities
                    ):
                        entities.append(
                            {
                                "text": match.group(),
                                "type": "AUTHORITY",
                                "start": match.start(),
                                "end": match.end(),
                                "confidence": 0.97,
                                "metadata": {"category": "机关/机构"},
                            }
                        )

        # 6. 提取时限/期间
        if "TIME_LIMIT" in entity_types:
            time_patterns = [
                r"\d+[年个月天日]",
                r"[一二三四五六七八九十\d]+[个月年内日前]",
                r"申请日起[^\d]{0,20}\d+",
                r"优先权日起[^\d]{0,20}\d+",
            ]
            for pattern_str in time_patterns:
                pattern = re.compile(pattern_str)
                for match in pattern.finditer(text):
                    if not any(
                        e["start"] <= match.start() and e["end"] >= match.end() for e in entities
                    ):
                        entities.append(
                            {
                                "text": match.group(),
                                "type": "TIME_LIMIT",
                                "start": match.start(),
                                "end": match.end(),
                                "confidence": 0.90,
                                "metadata": {"category": "时限"},
                            }
                        )

        # 按起始位置排序
        entities.sort(key=lambda x: x["start"])

        return entities

    def extract_relations(self, text: str, entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        提取实体间的关系

        Args:
            text: 输入文本
            entities: 实体列表

        Returns:
            关系列表
        """
        relations = []

        # 按类型分组实体
        entities_by_type = {}
        for entity in entities:
            etype = entity["type"]
            if etype not in entities_by_type:
                entities_by_type[etype] = []
            entities_by_type[etype].append(entity)

        # 1. 法律引用 -> 法条引用 关系
        if "LAW_REFERENCE" in entities_by_type and "ARTICLE_REFERENCE" in entities_by_type:
            for law_ref in entities_by_type["LAW_REFERENCE"]:
                # 查找同一句子或邻近句子中的法条引用
                context_start = max(0, law_ref["start"] - 100)
                context_end = min(len(text), law_ref["end"] + 100)
                context = text[context_start:context_end]

                for art_ref in entities_by_type["ARTICLE_REFERENCE"]:
                    if law_ref["start"] <= art_ref["start"] <= law_ref["end"] + 200:
                        relations.append(
                            {
                                "subject": law_ref["text"],
                                "predicate": "REFERS_TO",
                                "object": art_ref["text"],
                                "confidence": 0.92,
                                "evidence": context.strip(),
                                "metadata": {"relation_type": "法律条文引用"},
                            }
                        )

        # 2. 法律概念 -> 定义 关系
        if "LAW_CONCEPT" in entities_by_type:
            concept_entities = entities_by_type["LAW_CONCEPT"]
            for concept in concept_entities:
                # 查找定义模式
                text_after = text[concept["end"] : concept["end"] + 100]
                if any(pattern in text_after for pattern in ["是指", "系指", "所谓", "即"]):
                    relations.append(
                        {
                            "subject": "当前条款",
                            "predicate": "DEFINES",
                            "object": concept["text"],
                            "confidence": 0.85,
                            "evidence": text[concept["start"] : concept["end"] + 50],
                            "metadata": {"relation_type": "概念定义"},
                        }
                    )

        # 3. 检测权利/义务关系
        for entity in entities:
            if entity["type"] in ["RIGHT", "OBLIGATION", "AUTHORITY"]:
                text_before = text[max(0, entity["start"] - 30) : entity["start"]]

                # 检测权利
                if any(word in text_before for word in ["享有", "拥有", "具有"]):
                    relations.append(
                        {
                            "subject": "申请人/专利权人",
                            "predicate": "HAS_RIGHT",
                            "object": entity["text"],
                            "confidence": 0.88,
                            "evidence": text[max(0, entity["start"] - 20) : entity["end"] + 20],
                            "metadata": {"relation_type": "权利关系"},
                        }
                    )

                # 检测义务
                elif any(word in text_before for word in ["应当", "必须", "有义务"]):
                    relations.append(
                        {
                            "subject": "申请人/专利权人",
                            "predicate": "HAS_OBLIGATION",
                            "object": entity["text"],
                            "confidence": 0.90,
                            "evidence": text[max(0, entity["start"] - 20) : entity["end"] + 20],
                            "metadata": {"relation_type": "义务关系"},
                        }
                    )

        # 4. 检测条件关系
        if "CONDITION" in entities_by_type or "TIME_LIMIT" in entities_by_type:
            all_conditions = entities_by_type.get("CONDITION", []) + entities_by_type.get(
                "TIME_LIMIT", []
            )
            for condition in all_conditions:
                text_before = text[max(0, condition["start"] - 50) : condition["start"]]
                if any(word in text_before for word in ["在", "当", "如果", "若", "符合"]):
                    # 查找附近的法律概念作为主体
                    for concept_entity in entities_by_type.get("LAW_CONCEPT", []):
                        if abs(concept_entity["start"] - condition["start"]) < 100:
                            relations.append(
                                {
                                    "subject": concept_entity["text"],
                                    "predicate": "CONDITION_FOR",
                                    "object": condition["text"],
                                    "confidence": 0.82,
                                    "evidence": text[
                                        max(0, condition["start"] - 30) : condition["end"] + 30
                                    ],
                                    "metadata": {"relation_type": "条件关系"},
                                }
                            )
                            break

        # 5. 检测基于关系
        for law_ref in entities_by_type.get("ARTICLE_REFERENCE", []):
            text_before = text[max(0, law_ref["start"] - 30) : law_ref["start"]]
            if any(word in text_before for word in ["根据", "依据", "按照", "依照", "基于"]):
                # 查找主语(通常是"本法"或法律概念)
                for concept in entities_by_type.get("LAW_CONCEPT", []):
                    if (
                        concept["start"] < law_ref["start"]
                        and law_ref["start"] - concept["start"] < 100
                    ):
                        relations.append(
                            {
                                "subject": concept["text"],
                                "predicate": "BASED_ON",
                                "object": law_ref["text"],
                                "confidence": 0.91,
                                "evidence": text[concept["start"] : law_ref["end"] + 10],
                                "metadata": {"relation_type": "法律依据"},
                            }
                        )
                        break

        return relations

    def extract_entities_and_relations(
        self, text: str, entity_types: list[str] = None
    ) -> dict[str, Any]:
        """
        同时提取实体和关系

        Args:
            text: 输入文本
            entity_types: 要提取的实体类型,None表示全部

        Returns:
            包含entities和relations的字典
        """
        entities = self.extract_entities(text, entity_types)
        relations = self.extract_relations(text, entities)

        # 统计信息
        entity_type_counts = {}
        for entity in entities:
            etype = entity["type"]
            entity_type_counts[etype] = entity_type_counts.get(etype, 0) + 1

        relation_type_counts = {}
        for relation in relations:
            rtype = relation["predicate"]
            relation_type_counts[rtype] = relation_type_counts.get(rtype, 0) + 1

        return {
            "entities": entities,
            "relations": relations,
            "statistics": {
                "total_entities": len(entities),
                "total_relations": len(relations),
                "entity_types": entity_type_counts,
                "relation_types": relation_type_counts,
            },
        }


# 便捷函数
def extract_legal_entities_and_relations(text: str) -> dict[str, Any]:
    """
    提取法律文档的实体和关系(便捷函数)

    Args:
        text: 输入文本

    Returns:
        包含entities和relations的字典
    """
    extractor = LegalEntityRelationExtractor()
    return extractor.extract_entities_and_relations(text)


if __name__ == "__main__":
    # 测试代码
    test_text = """
    根据专利法第二十二条,授予专利权的发明和实用新型,应当具备新颖性、创造性和实用性。
    新颖性,是指该发明或者实用新型不属于现有技术。
    专利权人有权禁止他人为生产经营目的制造、使用、许诺销售、销售其专利产品。
    """

    result = extract_legal_entities_and_relations(test_text)

    print("实体:")
    for entity in result["entities"]:
        print(f"  - {entity['text']} ({entity['type']})")

    print("\n关系:")
    for relation in result["relations"]:
        print(f"  - {relation['subject']} {relation['predicate']} {relation['object']}")

    print(f"\n统计: {result['statistics']}")
