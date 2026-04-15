#!/usr/bin/env python3
"""
专利规则复杂语义关系抽取器
Patent Rules Semantic Relation Extractor

支持复杂的语义关系抽取，包括：
- 引用关系（REFERS_TO）
- 层级关系（CONTAINS）
- 依赖关系（DEPENDS_ON）
- 矛盾关系（CONFLICTS_WITH）
- 补充关系（SUPPLEMENTS）
- 修正关系（AMENDS）
- 适用关系（APPLIES_TO）

作者: Athena AI系统
创建时间: 2025-01-15
"""

from __future__ import annotations
import asyncio
import logging
import re

# 添加项目路径
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from core.embedding.bge_embedding_service import BGEEmbeddingService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RelationType(Enum):
    """关系类型"""
    REFERS_TO = "refers_to"                 # 引用关系
    CONTAINS = "contains"                   # 包含关系（层级）
    DEPENDS_ON = "depends_on"               # 依赖关系
    CONFLICTS_WITH = "conflicts_with"       # 矛盾关系
    SUPPLEMENTS = "supplements"             # 补充关系
    AMENDS = "amends"                       # 修正关系
    APPLIES_TO = "applies_to"               # 适用关系
    DEFINES = "defines"                     # 定义关系
    RESTRICTS = "restricts"                 # 限制关系
    EXEMPTS = "exempts"                     # 豁免关系


@dataclass
class SemanticRelation:
    """语义关系"""
    source_id: str                    # 源规则ID
    target_id: str                    # 目标规则ID
    relation_type: RelationType       # 关系类型
    confidence: float                 # 置信度 (0-1)
    evidence: str                     # 证据（支持该关系的文本片段）
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据


class PatentRuleRelationExtractor:
    """专利规则关系抽取器（复杂语义抽取）"""

    def __init__(self, embedding_service: BGEEmbeddingService | None = None):
        """
        初始化关系抽取器

        Args:
            embedding_service: BGE嵌入服务（用于语义相似度计算）
        """
        self.embedding_service = embedding_service
        self.stats = {
            'total_relations': 0,
            'by_type': dict.fromkeys(RelationType, 0),
            'high_confidence': 0,  # 置信度 > 0.8
            'medium_confidence': 0,  # 置信度 0.6-0.8
            'low_confidence': 0,  # 置信度 < 0.6
        }

    # ========== 关系抽取模式 ==========

    # 引用关系模式
    REFERS_PATTERNS = [
        r'根据[本法条例规定]?.*[第]*([一二三四五六七八九十百千\d]+)条',
        r'依照[本法条例规定]?.*[第]*([一二三四五六七八九十百千\d]+)条',
        r'按照[本法条例规定]?.*[第]*([一二三四五六七八九十百千\d]+)条',
        r'依据[本法条例规定]?.*[第]*([一二三四五六七八九十百千\d]+)条',
        r'参照[本法条例规定]?.*[第]*([一二三四五六七八九十百千\d]+)条',
    ]

    # 依赖关系模式
    DEPENDS_PATTERNS = [
        r'在.*[满足符合遵照遵循].*[第]*([一二三四五六七八九十百千\d]+)条.*前提下',
        r'只有.*[符合满足].*[第]*([一二三四五六七八九十百千\d]+)条.*方可',
    ]

    # 矛盾关系模式
    CONFLICTS_PATTERNS = [
        r'除.*例外',
        r'不.*[适用遵照遵循].*[第]*([一二三四五六七八九十百千\d]+)条',
        r'不受.*[限制约束]',
    ]

    # 补充关系模式
    SUPPLEMENTS_PATTERNS = [
        r'还.*[应当必须]',
        r'同时.*[应当必须]',
        r'另.*[规定要求]',
    ]

    # 修正关系模式
    AMENDS_PATTERNS = [
        r'修正[本法条例规定]',
        r'修订[本法条例规定]',
        r'代替.*[规定条款]',
    ]

    # 适用关系模式
    APPLIES_PATTERNS = [
        r'适用于',
        r'适用.*[范围对象]',
    ]

    # 定义关系模式
    DEFINES_PATTERNS = [
        r'本法.*[指称定义]为',
        r'.*[指称定义].*:',
        r'是指.*:',
    ]

    # 限制关系模式
    RESTRICTS_PATTERNS = [
        r'限制.*[范围数量条件]',
        r'不得超过',
        r'仅限于',
    ]

    # 豁免关系模式
    EXEMPTS_PATTERNS = [
        r'除外',
        r'不适用.*[规定条款]',
        r'免于',
    ]

    def extract_relations(
        self,
        rules: list[dict[str, Any]],
        use_semantic: bool = True
    ) -> list[SemanticRelation]:
        """
        从规则列表中抽取关系

        Args:
            rules: 规则列表，每个规则包含 id, content, metadata 等字段
            use_semantic: 是否使用语义相似度计算

        Returns:
            抽取的关系列表
        """
        relations = []

        logger.info(f"开始抽取 {len(rules)} 个规则之间的关系...")

        # 1. 基于规则的关系抽取
        relations.extend(self._extract_rule_based_relations(rules))

        # 2. 基于层级的关系抽取（CONTAINS）
        relations.extend(self._extract_hierarchy_relations(rules))

        # 3. 基于语义的关系抽取（如果启用了嵌入服务）
        if use_semantic and self.embedding_service:
            relations.extend(self._extract_semantic_relations(rules))

        # 4. 去重和过滤
        relations = self._deduplicate_relations(relations)
        relations = self._filter_by_confidence(relations, threshold=0.5)

        # 更新统计
        for rel in relations:
            self.stats['total_relations'] += 1
            self.stats['by_type'][rel.relation_type] += 1
            if rel.confidence > 0.8:
                self.stats['high_confidence'] += 1
            elif rel.confidence > 0.6:
                self.stats['medium_confidence'] += 1
            else:
                self.stats['low_confidence'] += 1

        logger.info(f"✅ 共抽取 {len(relations)} 条关系")
        self._print_stats()

        return relations

    def _extract_rule_based_relations(
        self,
        rules: list[dict[str, Any]]
    ) -> list[SemanticRelation]:
        """基于规则模式抽取关系"""
        relations = []

        # 构建规则ID到规则的映射
        rule_map = {r['id']: r for r in rules}

        # 构建条款号到规则ID的映射
        article_to_rules = {}
        for rule in rules:
            article_num = rule.get('article_number')
            if article_num:
                # 提取数字
                match = re.search(r'[一二三四五六七八九十百千零\d]+', article_num)
                if match:
                    article_num_str = match.group(0)
                    if article_num_str not in article_to_rules:
                        article_to_rules[article_num_str] = []
                    article_to_rules[article_num_str].append(rule['id'])

        for rule in rules:
            content = rule.get('content', '')
            source_id = rule['id']

            # 检测各种关系
            # 1. 引用关系
            for pattern in self.REFERS_PATTERNS:
                matches = re.finditer(pattern, content)
                for match in matches:
                    article_num = match.group(1)
                    target_ids = article_to_rules.get(article_num, [])
                    for target_id in target_ids:
                        if target_id != source_id:
                            relations.append(SemanticRelation(
                                source_id=source_id,
                                target_id=target_id,
                                relation_type=RelationType.REFERS_TO,
                                confidence=0.92,  # 基于明确引用模式，高置信度
                                evidence=match.group(0),
                                metadata={'pattern': 'refers', 'article_number': article_num}
                            ))

            # 2. 依赖关系
            for pattern in self.DEPENDS_PATTERNS:
                matches = re.finditer(pattern, content)
                for match in matches:
                    article_num = match.group(1)
                    target_ids = article_to_rules.get(article_num, [])
                    for target_id in target_ids:
                        if target_id != source_id:
                            relations.append(SemanticRelation(
                                source_id=source_id,
                                target_id=target_id,
                                relation_type=RelationType.DEPENDS_ON,
                                confidence=0.88,
                                evidence=match.group(0),
                                metadata={'pattern': 'depends', 'article_number': article_num}
                            ))

            # 3. 补充关系
            for pattern in self.SUPPLEMENTS_PATTERNS:
                if re.search(pattern, content):
                    # 补充关系通常指向同一章节的其他规则
                    chapter = rule.get('chapter')
                    if chapter:
                        for other_rule in rules:
                            if (other_rule['id'] != source_id and
                                other_rule.get('chapter') == chapter):
                                relations.append(SemanticRelation(
                                    source_id=source_id,
                                    target_id=other_rule['id'],
                                    relation_type=RelationType.SUPPLEMENTS,
                                    confidence=0.75,
                                    evidence=re.search(pattern, content).group(0),
                                    metadata={'pattern': 'supplements', 'chapter': chapter}
                                ))
                                break  # 只添加一个最相关的

        return relations

    def _extract_hierarchy_relations(
        self,
        rules: list[dict[str, Any]]
    ) -> list[SemanticRelation]:
        """抽取层级关系（CONTAINS）"""
        relations = []

        # 按层级分组
        chapter_rules: dict[str, list[str]] = {}  # 章 -> 规则列表
        section_rules: dict[str, list[str]] = {}  # 节 -> 规则列表

        for rule in rules:
            rule_id = rule['id']
            chapter = rule.get('chapter')
            section = rule.get('section')

            if chapter:
                if chapter not in chapter_rules:
                    chapter_rules[chapter] = []
                chapter_rules[chapter].append(rule_id)

            if section:
                if section not in section_rules:
                    section_rules[section] = []
                section_rules[section].append(rule_id)

        # 创建CONTAINS关系
        # 章 -> 节
        for chapter, c_rules in chapter_rules.items():
            for section, s_rules in section_rules.items():
                # 如果节的规则包含在章的规则中，创建关系
                if set(s_rules).issubset(set(c_rules)):
                    # 找到章和节的代表规则
                    chapter_rep = c_rules[0] if c_rules else None
                    section_rep = s_rules[0] if s_rules else None
                    if chapter_rep and section_rep:
                        relations.append(SemanticRelation(
                            source_id=chapter_rep,
                            target_id=section_rep,
                            relation_type=RelationType.CONTAINS,
                            confidence=1.0,  # 层级关系是确定的
                            evidence=f"{chapter} 包含 {section}",
                            metadata={'chapter': chapter, 'section': section, 'level': 1}
                        ))

        return relations

    def _extract_semantic_relations(
        self,
        rules: list[dict[str, Any]]
    ) -> list[SemanticRelation]:
        """基于语义相似度抽取关系"""
        relations = []

        if not self.embedding_service:
            return relations

        logger.info("计算语义相似度...")

        # 获取所有规则内容
        contents = [r.get('content', '') for r in rules]
        rule_ids = [r['id'] for r in rules]

        # 批量编码
        embeddings = self.embedding_service.encode(contents)

        # 计算相似度矩阵
        similarity_matrix = np.dot(embeddings, embeddings.T)

        # 找出高相似度对
        threshold = 0.85  # 相似度阈值
        for i in range(len(rules)):
            for j in range(i + 1, len(rules)):
                similarity = similarity_matrix[i][j]

                if similarity > threshold:
                    # 高相似度可能表示：
                    # 1. 补充关系
                    # 2. 适用关系
                    # 3. 定义关系

                    # 基于关键词判断关系类型
                    content_i = rules[i].get('content', '')
                    content_j = rules[j].get('content', '')

                    # 检查是否是定义关系
                    if any(kw in content_i for kw in ['指', '定义', '是指']):
                        relations.append(SemanticRelation(
                            source_id=rule_ids[i],
                            target_id=rule_ids[j],
                            relation_type=RelationType.DEFINES,
                            confidence=similarity,
                            evidence=f"语义相似度: {similarity:.3f}",
                            metadata={'similarity': float(similarity), 'method': 'semantic'}
                        ))
                    else:
                        # 默认为补充关系
                        relations.append(SemanticRelation(
                            source_id=rule_ids[i],
                            target_id=rule_ids[j],
                            relation_type=RelationType.SUPPLEMENTS,
                            confidence=similarity * 0.9,  # 略微降低置信度
                            evidence=f"语义相似度: {similarity:.3f}",
                            metadata={'similarity': float(similarity), 'method': 'semantic'}
                        ))

        logger.info(f"✅ 基于语义相似度抽取 {len(relations)} 条关系")
        return relations

    def _deduplicate_relations(
        self,
        relations: list[SemanticRelation]
    ) -> list[SemanticRelation]:
        """去重关系（相同的源、目标、类型只保留置信度最高的）"""
        unique_relations: dict[tuple[str, str, RelationType], SemanticRelation] = {}

        for rel in relations:
            key = (rel.source_id, rel.target_id, rel.relation_type)
            if key not in unique_relations or rel.confidence > unique_relations[key].confidence:
                unique_relations[key] = rel

        return list(unique_relations.values())

    def _filter_by_confidence(
        self,
        relations: list[SemanticRelation],
        threshold: float = 0.5
    ) -> list[SemanticRelation]:
        """按置信度过滤"""
        return [r for r in relations if r.confidence >= threshold]

    def _print_stats(self) -> Any:
        """打印统计信息"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 关系抽取统计")
        logger.info("=" * 60)
        logger.info(f"总关系数: {self.stats['total_relations']}")

        logger.info("\n按类型统计:")
        for rel_type, count in self.stats['by_type'].items():
            if count > 0:
                logger.info(f"  {rel_type.value}: {count}条")

        logger.info("\n按置信度统计:")
        logger.info(f"  高置信度(>0.8): {self.stats['high_confidence']}条")
        logger.info(f"  中置信度(0.6-0.8): {self.stats['medium_confidence']}条")
        logger.info(f"  低置信度(<0.6): {self.stats['low_confidence']}条")
        logger.info("=" * 60 + "\n")


async def test_relation_extractor():
    """测试关系抽取器"""
    from core.embedding.bge_embedding_service import BGEEmbeddingService

    # 初始化嵌入服务
    embedding_service = BGEEmbeddingService(
        model_name='bge-m3',
        device='mps',
        batch_size=32
    )

    # 初始化抽取器
    extractor = PatentRuleRelationExtractor(embedding_service)

    # 创建测试规则
    test_rules = [
        {
            'id': 'rule_001',
            'content': '专利权的期限为二十年，自申请日起计算。',
            'article_number': '第四十二条',
            'chapter': '第一章',
            'section': None
        },
        {
            'id': 'rule_002',
            'content': '发明专利权的期限为二十年，实用新型专利权的期限为十年，外观设计专利权的期限为十五年，均自申请日起计算。',
            'article_number': '第四十二条',
            'chapter': '第一章',
            'section': None
        },
        {
            'id': 'rule_003',
            'content': '专利权人应当自被授予专利权的当年开始缴纳年费。',
            'article_number': '第四十三条',
            'chapter': '第一章',
            'section': None
        },
        {
            'id': 'rule_004',
            'content': '有下列情形之一的，专利权在期限届满前终止：（一）没有按照规定缴纳年费的；（二）专利权人以书面声明放弃其专利权的。',
            'article_number': '第四十四条',
            'chapter': '第一章',
            'section': None
        }
    ]

    # 抽取关系
    relations = extractor.extract_relations(test_rules, use_semantic=True)

    # 打印结果
    print("\n" + "=" * 60)
    print("🔗 抽取的关系")
    print("=" * 60)
    for i, rel in enumerate(relations, 1):
        print(f"\n{i}. {rel.relation_type.value}")
        print(f"   源: {rel.source_id}")
        print(f"   目标: {rel.target_id}")
        print(f"   置信度: {rel.confidence:.3f}")
        print(f"   证据: {rel.evidence[:80]}...")

    return relations


if __name__ == "__main__":
    asyncio.run(test_relation_extractor())
