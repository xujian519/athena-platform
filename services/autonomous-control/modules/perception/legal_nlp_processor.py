#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
法律NLP处理器
Legal NLP Processor

专门处理法律文本的自然语言理解

作者: 小娜·天秤女神
创建时间: 2024年12月15日
"""

import re
from core.async_main import async_main
import jieba
import jieba.posseg as pseg
from typing import Dict, List, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class LegalNLPProcessor:
    """法律文本NLP处理器"""

    def __init__(self):
        """初始化法律NLP处理器"""
        self._load_legal_dict()
        self._init_patterns()

    def _load_legal_dict(self) -> Dict[str, Any]:
        """加载法律词典"""
        # 法律专业术语
        self.legal_terms = {
            # 专利相关
            '专利权': 'patent_right',
            '发明专利': 'invention_patent',
            '实用新型': 'utility_model',
            '外观设计': 'design_patent',
            '现有技术': 'prior_art',
            '新颖性': 'novelty',
            '创造性': 'creativity',
            '实用性': 'practicality',
            '权利要求': 'claims',
            '说明书': 'specification',
            '技术方案': 'technical_solution',

            # 商标相关
            '商标权': 'trademark_right',
            '注册商标': 'registered_trademark',
            '商标侵权': 'trademark_infringement',
            '驰名商标': 'well_known_trademark',
            '商标使用': 'trademark_use',

            # 版权相关
            '著作权': 'copyright',
            '版权': 'copyright',
            '作品': 'work',
            '侵权': 'infringement',
            '合理使用': 'fair_use',

            # 合同相关
            '合同': 'contract',
            '违约': 'breach_of_contract',
            '解除合同': 'termination',
            '无效合同': 'void_contract',
            '要约': 'offer',
            '承诺': 'acceptance'
        }

        # 添加到jieba词典
        for term in self.legal_terms:
            jieba.add_word(term)

    def _init_patterns(self) -> Any:
        """初始化正则模式"""
        self.patterns = {
            # 申请号模式
            'application_number': re.compile(r'CN\d{13}[A-Z\d]'),
            # 公开号模式
            'publication_number': re.compile(r'CN\d{9}[A-Z\d]'),
            # 日期模式
            'date': re.compile(r'\d{4}[-年]\d{1,2}[-月]\d{1,2}[日]?'),
            # 金额模式
            'money': re.compile(r'[一二三四五六七八九十百千万零]+[元整]'),
            # IPC分类号
            'ipc': re.compile(r'[A-H]\d{2}[A-Z]\d{1,4}\/\d{2,6}')
        }

    async def parse(self, text: str) -> Dict[str, Any]:
        """
        解析法律文本

        Args:
            text: 法律文本

        Returns:
            解析结果
        """
        try:
            # 基础分词
            tokens = list(jieba.cut(text))
            pos_tags = list(pseg.cut(text))

            # 实体识别
            entities = await self._extract_entities(text)

            # 关系抽取
            relations = await self._extract_relations(text, entities)

            # 结构化信息
            structured_info = await self._extract_structured_info(text)

            # 情感分析（法律场景）
            sentiment = await self._analyze_legal_sentiment(text)

            return {
                'tokens': tokens,
                'pos_tags': pos_tags,
                'entities': entities,
                'relations': relations,
                'structured_info': structured_info,
                'sentiment': sentiment,
                'confidence': self._calculate_confidence(entities)
            }

        except Exception as e:
            logger.error(f"法律NLP解析失败: {str(e)}")
            return {'error': str(e)}

    async def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """提取法律实体"""
        entities = []

        # 提取法律术语
        for term, entity_type in self.legal_terms.items():
            if term in text:
                entities.append({
                    'text': term,
                    'type': entity_type,
                    'category': 'legal_term'
                })

        # 提取结构化信息
        for pattern_type, pattern in self.patterns.items():
            matches = pattern.findall(text)
            for match in matches:
                entities.append({
                    'text': match,
                    'type': pattern_type,
                    'category': 'structured_data'
                })

        return entities

    async def _extract_relations(self, text: str, entities: List[Dict]) -> List[Dict[str, Any]]:
        """提取实体关系"""
        relations = []

        # 简化的关系抽取
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                # 检查是否在同一句子
                if self._in_same_sentence(text, entity1['text'], entity2['text']):
                    relation = {
                        'subject': entity1,
                        'object': entity2,
                        'relation': self._infer_relation(entity1, entity2, text),
                        'confidence': 0.8
                    }
                    relations.append(relation)

        return relations

    async def _extract_structured_info(self, text: str) -> Dict[str, Any]:
        """提取结构化信息"""
        info = {}

        # 提取申请号
        app_numbers = self.patterns['application_number'].findall(text)
        if app_numbers:
            info['application_numbers'] = app_numbers

        # 提取日期
        dates = self.patterns['date'].findall(text)
        if dates:
            info['dates'] = dates

        # 提取金额
        amounts = self.patterns['money'].findall(text)
        if amounts:
            info['amounts'] = amounts

        return info

    async def _analyze_legal_sentiment(self, text: str) -> Dict[str, Any]:
        """分析法律文本情感倾向"""
        # 法律场景的特殊情感分析
        positive_words = ['授权', '有效', '保护', '支持', '批准']
        negative_words = ['驳回', '无效', '侵权', '违约', '撤销']
        neutral_words = ['审查', '评估', '分析', '判定']

        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)
        neu_count = sum(1 for word in neutral_words if word in text)

        total = pos_count + neg_count + neu_count

        if total == 0:
            return {'sentiment': 'neutral', 'score': 0.0}

        if pos_count > neg_count and pos_count > neu_count:
            return {'sentiment': 'positive', 'score': pos_count / total}
        elif neg_count > pos_count and neg_count > neu_count:
            return {'sentiment': 'negative', 'score': -neg_count / total}
        else:
            return {'sentiment': 'neutral', 'score': 0.0}

    def _in_same_sentence(self, text: str, word1: str, word2: str) -> bool:
        """判断两个词是否在同一句子"""
        # 简化实现：检查两个词之间的距离
        pos1 = text.find(word1)
        pos2 = text.find(word2)
        return abs(pos1 - pos2) < 200  # 200个字符内认为是同一句子

    def _infer_relation(self, entity1: Dict, entity2: Dict, text: str) -> str:
        """推断实体关系"""
        # 简化的关系推断
        if entity1['type'] == 'application_number' and entity2['type'] == 'patent_right':
            return 'belongs_to'
        elif entity1['type'] == 'patent_right' and entity2['type'] == 'infringement':
            return 'subject_to'
        else:
            return 'related_to'

    def _calculate_confidence(self, entities: List[Dict]) -> float:
        """计算解析置信度"""
        if not entities:
            return 0.0

        # 基于实体数量和类型计算置信度
        legal_term_count = len([e for e in entities if e['category'] == 'legal_term'])
        structured_count = len([e for e in entities if e['category'] == 'structured_data'])

        confidence = min(1.0, (legal_term_count * 0.3 + structured_count * 0.2 + len(entities) * 0.1))
        return round(confidence, 2)

# 使用示例
@async_main
async def main():
    """测试法律NLP处理器"""
    processor = LegalNLPProcessor()

    test_text = """
    本发明涉及一种基于人工智能的数据处理方法，属于计算机技术领域。
    申请号：CN202410001234.5，申请日期：2024年1月1日。
    该技术方案具有新颖性、创造性和实用性。
    """

    result = await processor.parse(test_text)
    print("法律NLP解析结果:")
    print(f"实体数: {len(result['entities'])}")
    print(f"关系数: {len(result['relations'])}")
    print(f"置信度: {result['confidence']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())