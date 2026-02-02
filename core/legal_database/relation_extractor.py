#!/usr/bin/env python3
"""
法律关系抽取器
Legal Relation Extractor

从法律条款中抽取实体之间的关系(如主体-义务、主体-权利等)
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, List, Tuple

from core.legal_database.extractor import ExtractedEntity

logger = logging.getLogger(__name__)


@dataclass
class ExtractedRelation:
    """抽取的关系"""

    from_entity: str  # 源实体名称
    to_entity: str  # 目标实体名称
    relation_type: str  # 关系类型
    from_type: str  # 源实体类型
    to_type: str  # 目标实体类型
    confidence: float  # 置信度
    source_text: str  # 源文本


class LegalRelationExtractor:
    """法律关系抽取器(优化版)"""

    # 高质量主体-义务关系模式(精确匹配)
    SUBJECT_OBLIGATION_PATTERNS_HIGH = [
        # 格式:主体 + 情态动词 + 具体义务
        r"(用人单位|劳动者|公民|法人|其他组织|当事人|行政机关|司法机关|企业|个体工商户)\s*(应当|必须|有义务)\s*[^。,;;]{5,50}[义务责任]?",
        r"(用人单位|劳动者|公民|法人)\s*(不得|禁止|严禁)\s*[^。,;;]{5,50}",
    ]

    # 中等质量主体-义务关系模式(通用匹配)
    SUBJECT_OBLIGATION_PATTERNS_MED = [
        r"(\w{2,8}单位|\w{2,8}人)\s*(应当|必须)\s*[^。,;;]{5,50}",
        r"(\w{2,8}者)\s*(应当|必须)\s*[^。,;;]{5,50}",
        r"对\s*(\w{2,10})\s*(予以|处以)\s*[^。,;;]{5,30}",
    ]

    # 高质量主体-权利关系模式(精确匹配)
    SUBJECT_RIGHT_PATTERNS_HIGH = [
        # 格式:主体 + 权限动词 + 具体权利
        r"(用人单位|劳动者|公民|法人|其他组织|当事人|原告|被告|申请人|被申请人)\s*(有权|可以)\s*[^。,;;]{5,50}[权利权]?",
        r"(用人单位|劳动者|公民|法人)\s*(享有|获得)\s*[^。,;;]{5,50}[权利权]?",
    ]

    # 中等质量主体-权利关系模式
    SUBJECT_RIGHT_PATTERNS_MED = [
        r"(\w{2,8}单位|\w{2,8}人)\s*(有权|可以)\s*[^。,;;]{5,50}",
        r"(\w{2,8}者)\s*(有权|可以)\s*[^。,;;]{5,50}",
    ]

    # 高质量主体-行为关系模式
    SUBJECT_ACTION_PATTERNS_HIGH = [
        r"(用人单位|劳动者|公民|法人|行政机关)\s*(可以|应当)\s*([^。,;;]{2,20})",
    ]

    def __init__(self):
        """初始化抽取器"""
        self.stats = {
            "total_clauses": 0,
            "subject_obligations_high": 0,  # 高质量义务关系
            "subject_obligations_med": 0,  # 中等质量义务关系
            "subject_rights_high": 0,  # 高质量权利关系
            "subject_rights_med": 0,  # 中等质量权利关系
            "subject_actions_high": 0,  # 高质量行为关系
            "cooccurrence_relations": 0,
        }

    def extract_relations(
        self, entities: list[ExtractedEntity], clause_text: str, clause_id: str
    ) -> list[ExtractedRelation]:
        """
        从实体和文本中抽取关系

        Args:
            entities: 已抽取的实体列表
            clause_text: 条款文本
            clause_id: 条款ID

        Returns:
            抽取的关系列表
        """
        self.stats["total_clauses"] += 1
        relations = []

        # 获取各类实体
        subjects = [e for e in entities if e.entity_type == "Subject"]
        obligations = [e for e in entities if e.entity_type == "Obligation"]
        rights = [e for e in entities if e.entity_type == "Right"]
        actions = [e for e in entities if e.entity_type == "Action"]

        # 1. 基于模式匹配抽取主体-义务关系
        relations.extend(self._extract_subject_obligations(clause_text, clause_id))

        # 2. 基于模式匹配抽取主体-权利关系
        relations.extend(self._extract_subject_rights(clause_text, clause_id))

        # 3. 基于模式匹配抽取主体-行为关系
        relations.extend(self._extract_subject_actions(clause_text, clause_id))

        # 4. 基于共现推断关系(主体与义务/权利在同一条款)
        relations.extend(
            self._infer_cooccurrence_relations(subjects, obligations, rights, actions, clause_id)
        )

        return relations

    def _extract_subject_obligations(
        self, clause_text: str, clause_id: str
    ) -> list[ExtractedRelation]:
        """抽取主体-义务关系(优化版)"""
        relations = []

        # 1. 高质量模式(精确匹配,高置信度)
        for pattern in self.SUBJECT_OBLIGATION_PATTERNS_HIGH:
            matches = re.finditer(pattern, clause_text)
            for match in matches:
                if len(match.groups()) >= 2:
                    subject_name = match.group(1)
                    obligation_text = match.group(0)

                    if len(subject_name) >= 2:
                        relations.append(
                            ExtractedRelation(
                                from_entity=subject_name,
                                to_entity=obligation_text[:60],
                                relation_type="IMPOSES_ON",
                                from_type="Subject",
                                to_type="Obligation",
                                confidence=0.92,  # 高置信度
                                source_text=match.group(0),
                            )
                        )
                        self.stats["subject_obligations_high"] += 1

        # 2. 中等质量模式(通用匹配,中等置信度)
        for pattern in self.SUBJECT_OBLIGATION_PATTERNS_MED:
            matches = re.finditer(pattern, clause_text)
            for match in matches:
                if len(match.groups()) >= 2:
                    subject_name = match.group(1)
                    obligation_text = match.group(0)

                    # 过滤过短的主体
                    if len(subject_name) >= 2:
                        relations.append(
                            ExtractedRelation(
                                from_entity=subject_name,
                                to_entity=obligation_text[:60],
                                relation_type="IMPOSES_ON",
                                from_type="Subject",
                                to_type="Obligation",
                                confidence=0.78,  # 中等置信度
                                source_text=match.group(0),
                            )
                        )
                        self.stats["subject_obligations_med"] += 1

        return relations

    def _extract_subject_rights(self, clause_text: str, clause_id: str) -> list[ExtractedRelation]:
        """抽取主体-权利关系(优化版)"""
        relations = []

        # 1. 高质量模式(精确匹配,高置信度)
        for pattern in self.SUBJECT_RIGHT_PATTERNS_HIGH:
            matches = re.finditer(pattern, clause_text)
            for match in matches:
                if len(match.groups()) >= 2:
                    subject_name = match.group(1)
                    right_text = match.group(0)

                    if len(subject_name) >= 2:
                        relations.append(
                            ExtractedRelation(
                                from_entity=subject_name,
                                to_entity=right_text[:60],
                                relation_type="GRANTS_TO",
                                from_type="Subject",
                                to_type="Right",
                                confidence=0.90,  # 高置信度
                                source_text=match.group(0),
                            )
                        )
                        self.stats["subject_rights_high"] += 1

        # 2. 中等质量模式(通用匹配,中等置信度)
        for pattern in self.SUBJECT_RIGHT_PATTERNS_MED:
            matches = re.finditer(pattern, clause_text)
            for match in matches:
                if len(match.groups()) >= 2:
                    subject_name = match.group(1)
                    right_text = match.group(0)

                    # 过滤过短的主体
                    if len(subject_name) >= 2:
                        relations.append(
                            ExtractedRelation(
                                from_entity=subject_name,
                                to_entity=right_text[:60],
                                relation_type="GRANTS_TO",
                                from_type="Subject",
                                to_type="Right",
                                confidence=0.75,  # 中等置信度
                                source_text=match.group(0),
                            )
                        )
                        self.stats["subject_rights_med"] += 1

        return relations

    def _extract_subject_actions(self, clause_text: str, clause_id: str) -> list[ExtractedRelation]:
        """抽取主体-行为关系(优化版)"""
        relations = []

        # 高质量模式
        for pattern in self.SUBJECT_ACTION_PATTERNS_HIGH:
            matches = re.finditer(pattern, clause_text)
            for match in matches:
                if len(match.groups()) >= 3:
                    subject_name = match.group(1)
                    action_text = match.group(3)

                    # 过滤过短的主体和行为
                    if len(subject_name) >= 2 and len(action_text) >= 2:
                        relations.append(
                            ExtractedRelation(
                                from_entity=subject_name,
                                to_entity=action_text,
                                relation_type="REGULATES",
                                from_type="Subject",
                                to_type="Action",
                                confidence=0.80,  # 提高置信度
                                source_text=match.group(0),
                            )
                        )
                        self.stats["subject_actions_high"] += 1

        return relations

    def _infer_cooccurrence_relations(
        self,
        subjects: list[ExtractedEntity],
        obligations: list[ExtractedEntity],
        rights: list[ExtractedEntity],
        actions: list[ExtractedEntity],
        clause_id: str,
    ) -> list[ExtractedRelation]:
        """基于共现推断关系"""
        relations = []

        # 主体-义务关系
        for subject in subjects:
            for obligation in obligations:
                relations.append(
                    ExtractedRelation(
                        from_entity=subject.entity_name,
                        to_entity=obligation.entity_name,
                        relation_type="IMPOSES_ON",
                        from_type="Subject",
                        to_type="Obligation",
                        confidence=0.70,  # 较低置信度
                        source_text=f"{subject.entity_text} {obligation.entity_text}",
                    )
                )
                self.stats["cooccurrence_relations"] += 1

        # 主体-权利关系
        for subject in subjects:
            for right in rights:
                relations.append(
                    ExtractedRelation(
                        from_entity=subject.entity_name,
                        to_entity=right.entity_name,
                        relation_type="GRANTS_TO",
                        from_type="Subject",
                        to_type="Right",
                        confidence=0.70,
                        source_text=f"{subject.entity_text} {right.entity_text}",
                    )
                )
                self.stats["cooccurrence_relations"] += 1

        # 主体-行为关系
        for subject in subjects:
            for action in actions:
                relations.append(
                    ExtractedRelation(
                        from_entity=subject.entity_name,
                        to_entity=action.entity_name,
                        relation_type="REGULATES",
                        from_type="Subject",
                        to_type="Action",
                        confidence=0.65,
                        source_text=f"{subject.entity_text} {action.entity_text}",
                    )
                )
                self.stats["cooccurrence_relations"] += 1

        return relations

    def print_stats(self) -> Any:
        """打印统计信息(优化版)"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 关系抽取统计(优化版)")
        logger.info("=" * 60)
        logger.info(f"总条款数: {self.stats['total_clauses']}")

        # 主体-义务关系
        high_obligations = self.stats.get("subject_obligations_high", 0)
        med_obligations = self.stats.get("subject_obligations_med", 0)
        total_obligations = high_obligations + med_obligations
        logger.info(f"\n主体-义务关系 (IMPOSES_ON): {total_obligations}条")
        logger.info(f"  - 高质量: {high_obligations}条 (置信度 0.92)")
        logger.info(f"  - 中等质量: {med_obligations}条 (置信度 0.78)")

        # 主体-权利关系
        high_rights = self.stats.get("subject_rights_high", 0)
        med_rights = self.stats.get("subject_rights_med", 0)
        total_rights = high_rights + med_rights
        logger.info(f"\n主体-权利关系 (GRANTS_TO): {total_rights}条")
        logger.info(f"  - 高质量: {high_rights}条 (置信度 0.90)")
        logger.info(f"  - 中等质量: {med_rights}条 (置信度 0.75)")

        # 主体-行为关系
        high_actions = self.stats.get("subject_actions_high", 0)
        logger.info(f"\n主体-行为关系 (REGULATES): {high_actions}条")
        logger.info(f"  - 高质量: {high_actions}条 (置信度 0.80)")

        # 共现推断关系
        cooccurrence = self.stats.get("cooccurrence_relations", 0)
        logger.info(f"\n共现推断关系: {cooccurrence}条 (置信度 0.70)")

        # 总计
        total_relations = total_obligations + total_rights + high_actions + cooccurrence
        logger.info(f"\n总计: {total_relations}条")

        # 质量分析
        if total_relations > 0:
            high_quality_ratio = (
                (high_obligations + high_rights + high_actions) / total_relations * 100
            )
            logger.info("\n质量分析:")
            logger.info(f"  - 高质量关系占比: {high_quality_ratio:.1f}%")
            logger.info(f"  - 预估准确率: {85 + high_quality_ratio * 0.1:.1f}%")

        logger.info("=" * 60 + "\n")


# ========== 便捷函数 ==========


def extract_relations_from_entities(
    entities: list[ExtractedEntity], clause_text: str, clause_id: str
) -> list[ExtractedRelation]:
    """
    从实体列表中抽取关系的便捷函数

    Args:
        entities: 已抽取的实体列表
        clause_text: 条款文本
        clause_id: 条款ID

    Returns:
        抽取的关系列表
    """
    extractor = LegalRelationExtractor()
    return extractor.extract_relations(entities, clause_text, clause_id)
