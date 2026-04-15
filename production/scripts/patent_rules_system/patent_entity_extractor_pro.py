#!/usr/bin/env python3
"""
专利专业实体提取器 - 增强版
Patent Professional Entity Extractor - Enhanced Version

使用规则和统计方法结合提取专利相关实体

作者: Athena平台团队
创建时间: 2025-12-20
版本: v2.0.0
"""

from __future__ import annotations
import asyncio
import logging
import re
from collections import defaultdict
from typing import Any

import jieba
import jieba.posseg as pseg

logger = logging.getLogger(__name__)

class PatentEntityExtractorPro:
    """专利专业实体提取器"""

    def __init__(self):
        """初始化提取器"""
        self._load_patent_dict()
        self._setup_entity_patterns()

    def _load_patent_dict(self) -> dict[str, Any]:
        """加载专利词典"""
        # 专利类型词典
        self.patent_types = {
            '发明', '发明专利', '实用新型', '实用新型专利',
            '外观设计', '外观设计专利', '发明专利申请',
            '实用新型专利申请', '外观设计专利申请'
        }

        # 法律术语词典
        self.legal_terms = {
            '专利法', '专利法实施细则', '专利审查指南',
            '权利要求书', '说明书', '摘要', '附图',
            '优先权', '新颖性', '创造性', '实用性',
            '现有技术', '现有设计', '公开不充分',
            '单一性', '修改超范围', '保护范围',
            '侵权', '无效', '撤销', '复审',
            '授权', '驳回', '撤回', '终止',
            '专利权', '专利权人', '申请人', '发明人',
            '代理机构', '代理人'
        }

        # 时间相关术语
        self.time_terms = {
            '10年', '二十年', '10年', '十年',
            '申请日', '授权日', '公开日', '优先权日',
            '12个月', '12个月', '6个月', '3个月',
            '18个月', '3年', '5年'
        }

        # 技术领域通用术语
        self.tech_fields = {
            '人工智能', 'AI', '机器学习', '深度学习',
            '大数据', '云计算', '物联网', '5G',
            '新能源', '生物医药', '基因工程',
            '纳米技术', '量子计算', '区块链',
            '自动驾驶', '机器人', '无人机'
        }

        # 动作术语
        self.action_terms = {
            '申请', '提交', '审查', '授权', '驳回',
            '修改', '补正', '答复', '陈述',
            '提起', '上诉', '起诉', '应诉',
            '许可', '转让', '质押', '评估',
            '检索', '分析', '评价', '判断'
        }

        # 添加到jieba词典
        for term in self.patent_types | self.legal_terms | self.time_terms:
            jieba.add_word(term)

    def _setup_entity_patterns(self) -> Any:
        """设置实体识别模式"""
        # 专利号模式
        self.patent_number_patterns = [
            r'CN\d{8,9}[A-Z]',  # 中国专利号
            r'CN\d{13}',  # 13位申请号
            r'US\d{7,8}',  # 美国专利
            r'WO\d{8}',  # PCT专利
            r'EP\d{7,8}',  # 欧洲专利
        ]

        # 条款模式
        self.clause_patterns = [
            r'第[一二三四五六七八九十百千万\d]+条',
            r'实施细则第[一二三四五六七八九十百千万\d]+条',
            r'专利法第[一二三四五六七八九十百千万\d]+条',
            r'审查指南第[一二三四五六七八九十百千万\d]+部分',
        ]

        # 金额模式
        self.amount_patterns = [
            r'\d+元',
            r'\d+万元',
            r'\d+美元',
            r'\d+万欧元',
        ]

        # 百分比模式
        self.percentage_patterns = [
            r'\d+%',
            r'\d+\.\d+%',
        ]

    def extract_patent_entities(self, text: str, doc_id: str) -> list[dict[str, Any]]:
        """提取专利相关实体"""
        entities = []

        # 1. 提取专利类型
        entities.extend(self._extract_patent_types(text, doc_id))

        # 2. 提取法律术语
        entities.extend(self._extract_legal_terms(text, doc_id))

        # 3. 提取时间术语
        entities.extend(self._extract_time_terms(text, doc_id))

        # 4. 提取技术领域
        entities.extend(self._extract_tech_fields(text, doc_id))

        # 5. 提取动作术语
        entities.extend(self._extract_action_terms(text, doc_id))

        # 6. 提取专利号
        entities.extend(self._extract_patent_numbers(text, doc_id))

        # 7. 提取条款引用
        entities.extend(self._extract_clauses(text, doc_id))

        # 8. 提取金额
        entities.extend(self._extract_amounts(text, doc_id))

        # 9. 使用词性标注提取名词实体
        entities.extend(self._extract_noun_entities(text, doc_id))

        # 去重和过滤
        entities = self._deduplicate_entities(entities)

        return entities

    def _extract_patent_types(self, text: str, doc_id: str) -> list[dict[str, Any]]:
        """提取专利类型"""
        entities = []
        for patent_type in self.patent_types:
            if patent_type in text:
                for match in re.finditer(patent_type, text):
                    entities.append({
                        'text': patent_type,
                        'type': 'PATENT_TYPE',
                        'start': match.start(),
                        'end': match.end(),
                        'confidence': 0.95,
                        'source': doc_id
                    })
        return entities

    def _extract_legal_terms(self, text: str, doc_id: str) -> list[dict[str, Any]]:
        """提取法律术语"""
        entities = []
        for term in self.legal_terms:
            if term in text:
                for match in re.finditer(term, text):
                    entities.append({
                        'text': term,
                        'type': 'LEGAL_TERM',
                        'start': match.start(),
                        'end': match.end(),
                        'confidence': 0.9,
                        'source': doc_id
                    })
        return entities

    def _extract_time_terms(self, text: str, doc_id: str) -> list[dict[str, Any]]:
        """提取时间术语"""
        entities = []
        for term in self.time_terms:
            if term in text:
                for match in re.finditer(term, text):
                    entities.append({
                        'text': term,
                        'type': 'TIME_TERM',
                        'start': match.start(),
                        'end': match.end(),
                        'confidence': 0.85,
                        'source': doc_id
                    })
        return entities

    def _extract_tech_fields(self, text: str, doc_id: str) -> list[dict[str, Any]]:
        """提取技术领域"""
        entities = []
        for field in self.tech_fields:
            if field in text:
                for match in re.finditer(field, text):
                    entities.append({
                        'text': field,
                        'type': 'TECH_FIELD',
                        'start': match.start(),
                        'end': match.end(),
                        'confidence': 0.8,
                        'source': doc_id
                    })
        return entities

    def _extract_action_terms(self, text: str, doc_id: str) -> list[dict[str, Any]]:
        """提取动作术语"""
        entities = []
        for term in self.action_terms:
            if term in text:
                for match in re.finditer(term, text):
                    entities.append({
                        'text': term,
                        'type': 'ACTION_TERM',
                        'start': match.start(),
                        'end': match.end(),
                        'confidence': 0.75,
                        'source': doc_id
                    })
        return entities

    def _extract_patent_numbers(self, text: str, doc_id: str) -> list[dict[str, Any]]:
        """提取专利号"""
        entities = []
        for pattern in self.patent_number_patterns:
            for match in re.finditer(pattern, text):
                entities.append({
                    'text': match.group(),
                    'type': 'PATENT_NUMBER',
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.95,
                    'source': doc_id
                })
        return entities

    def _extract_clauses(self, text: str, doc_id: str) -> list[dict[str, Any]]:
        """提取条款引用"""
        entities = []
        for pattern in self.clause_patterns:
            for match in re.finditer(pattern, text):
                entities.append({
                    'text': match.group(),
                    'type': 'CLAUSE_REFERENCE',
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.9,
                    'source': doc_id
                })
        return entities

    def _extract_amounts(self, text: str, doc_id: str) -> list[dict[str, Any]]:
        """提取金额"""
        entities = []
        for pattern in self.amount_patterns:
            for match in re.finditer(pattern, text):
                entities.append({
                    'text': match.group(),
                    'type': 'AMOUNT',
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.85,
                    'source': doc_id
                })
        return entities

    def _extract_noun_entities(self, text: str, doc_id: str) -> list[dict[str, Any]]:
        """使用词性标注提取名词实体"""
        entities = []

        # 分词和词性标注
        words = pseg.cut(text)

        # 提取名词和术语
        for word, flag in words:
            # 过滤长度太短的词
            if len(word) < 2:
                continue

            # 提取名词
            if flag.startswith('n') or flag == 'nz':
                # 检查是否是重要的技术术语
                if self._is_important_term(word):
                    entities.append({
                        'text': word,
                        'type': 'TERM',
                        'start': text.find(word),
                        'end': text.find(word) + len(word),
                        'confidence': 0.7,
                        'source': doc_id,
                        'pos': flag
                    })

        return entities

    def _is_important_term(self, word: str) -> bool:
        """判断是否是重要术语"""
        # 长度大于等于3
        if len(word) >= 3:
            return True

        # 包含技术相关字
        tech_chars = ['技', '术', '方', '法', '系', '统', '设', '备', '装', '置']
        if any(char in word for char in tech_chars):
            return True

        # 已经在词典中的词
        return word in self.legal_terms or word in self.tech_fields

    def _deduplicate_entities(self, entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """去重和过滤实体"""
        # 按文本和类型去重
        seen = set()
        unique_entities = []

        for entity in entities:
            key = (entity['text'], entity['type'])
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)

        # 按置信度排序
        unique_entities.sort(key=lambda x: (-x['confidence'], x['start']))

        # 限制每种类型的数量
        type_counts = defaultdict(int)
        final_entities = []
        max_per_type = 20

        for entity in unique_entities:
            entity_type = entity['type']
            if type_counts[entity_type] < max_per_type:
                final_entities.append(entity)
                type_counts[entity_type] += 1

        return final_entities

    def extract_relations(self, text: str, entities: list[dict[str, Any]], doc_id: str) -> list[dict[str, Any]]:
        """提取实体间的关系"""
        relations = []

        # 基于共现提取关系
        for i, e1 in enumerate(entities):
            for j, e2 in enumerate(entities):
                if i < j:
                    # 计算距离
                    distance = abs(e1['start'] - e2['start'])

                    # 如果距离小于100个字符，认为可能有关系
                    if distance < 100:
                        # 根据实体类型推断关系
                        relation_type = self._infer_relation_type(e1['type'], e2['type'])

                        if relation_type:
                            relations.append({
                                'subject': e1['text'],
                                'object': e2['text'],
                                'relation': relation_type,
                                'confidence': max(0.5, 1 - distance/100),
                                'source': doc_id,
                                'distance': distance
                            })

        return relations

    def _infer_relation_type(self, type1: str, type2: str) -> str:
        """根据实体类型推断关系"""
        type_pairs = {
            ('PATENT_TYPE', 'TIME_TERM'): 'has_protection_period',
            ('ACTION_TERM', 'PATENT_TYPE'): 'action_on_patent',
            ('LEGAL_TERM', 'PATENT_TYPE'): 'regulates',
            ('TECH_FIELD', 'PATENT_TYPE'): 'applies_to',
            ('CLAUSE_REFERENCE', 'LEGAL_TERM'): 'refers_to',
        }

        if (type1, type2) in type_pairs:
            return type_pairs[(type1, type2)]
        elif (type2, type1) in type_pairs:
            return type_pairs[(type2, type1)][::-1]  # 反转关系

        return 'related_to'  # 默认关系


async def test_extractor():
    """测试提取器"""
    extractor = PatentEntityExtractorPro()

    test_text = """
    中华人民共和国专利法第四十二条规定：发明专利的保护期为二十年，
    实用新型专利的保护期为十年，外观设计专利的保护期为十五年，
    均自申请日起计算。专利权人应当自被授予专利权的当年开始缴纳年费。
    """

    # 提取实体
    entities = extractor.extract_patent_entities(test_text, "test_doc")

    # 提取关系
    relations = extractor.extract_relations(test_text, entities, "test_doc")

    print("提取的实体：")
    for entity in entities:
        print(f"  - {entity['text']} [{entity['type']}] (置信度: {entity['confidence']:.2f})")

    print("\n提取的关系：")
    for relation in relations:
        print(f"  - {relation['subject']} --{relation['relation']}--> {relation['object']} (置信度: {relation['confidence']:.2f})")


if __name__ == "__main__":
    asyncio.run(test_extractor())
