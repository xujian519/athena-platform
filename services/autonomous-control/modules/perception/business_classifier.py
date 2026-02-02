#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
业务分类器
Business Classifier

智能识别用户业务类型：专利、商标、版权、合同

作者: 小娜·天秤女神
创建时间: 2024年12月15日
"""

import re
from core.async_main import async_main
import asyncio
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class BusinessType(Enum):
    """业务类型枚举"""
    PATENT = "patent"          # 专利业务
    TRADEMARK = "trademark"    # 商标业务
    COPYRIGHT = "copyright"    # 版权业务
    CONTRACT = "contract"      # 合同业务
    LEGAL_ADVICE = "legal_advice"  # 法律咨询
    UNKNOWN = "unknown"        # 未知类型

class BusinessClassifier:
    """智能业务分类器"""

    def __init__(self):
        """初始化分类器"""
        self._init_keywords()
        self._init_patterns()
        self._init_classifier()

    def _init_keywords(self) -> Any:
        """初始化关键词字典"""
        self.keywords = {
            BusinessType.PATENT: {
                'primary': [
                    '专利', '发明专利', '实用新型', '外观设计', '申请专利',
                    '专利申请', '专利权', '授权', '审查', '驳回', '权利要求',
                    '说明书', '技术方案', '新颖性', '创造性', '实用性'
                ],
                'secondary': [
                    '发明创造', '技术创新', '现有技术', '抵触申请',
                    '公开日', '申请日', '优先权', '同日申请',
                    'IPC分类', '技术领域', '背景技术'
                ],
                'weight': 1.0
            },

            BusinessType.TRADEMARK: {
                'primary': [
                    '商标', '注册商标', '商标申请', '商标权', '商标侵权',
                    '驰名商标', '商标使用', '商标注册', '商标查询'
                ],
                'secondary': [
                    '商标异议', '商标撤销', '商标续展', '商标转让',
                    '商标许可', '商标监测', '品牌', 'Logo', '标识'
                ],
                'weight': 1.0
            },

            BusinessType.COPYRIGHT: {
                'primary': [
                    '著作权', '版权', '作品', '版权登记', '版权保护',
                    '侵权', '合理使用', '法定许可', '署名权'
                ],
                'secondary': [
                    '复制权', '发行权', '出租权', '展览权',
                    '表演权', '放映权', '广播权', '信息网络传播权',
                    '改编权', '翻译权', '汇编权', '邻接权'
                ],
                'weight': 1.0
            },

            BusinessType.CONTRACT: {
                'primary': [
                    '合同', '协议', '合约', '条款', '违约',
                    '解除合同', '合同无效', '要约', '承诺'
                ],
                'secondary': [
                    '合同履行', '合同变更', '合同转让', '合同终止',
                    '违约责任', '定金', '违约金', '不可抗力',
                    '保密协议', '劳动合同', '买卖合同', '技术服务合同'
                ],
                'weight': 1.0
            },

            BusinessType.LEGAL_ADVICE: {
                'primary': [
                    '法律咨询', '法律意见', '法律建议', '法务',
                    '诉讼', '仲裁', '调解', '法律风险'
                ],
                'secondary': [
                    '法律程序', '法律救济', '法律适用', '法律责任',
                    '证据', '举证责任', '时效', '管辖权'
                ],
                'weight': 0.8
            }
        }

    def _init_patterns(self) -> Any:
        """初始化正则模式"""
        self.patterns = {
            # 专利号模式
            'patent_number': re.compile(r'CN\d{13}[A-Z\d]|ZL\d{12}[A-Z\d]'),
            # 商标申请号模式
            'trademark_number': re.compile(r'\d{8,10}'),
            # 合同编号模式
            'contract_number': re.compile(r'合同编号[：:]\s*[A-Z\d]+'),
            # 法律文书编号模式
            'legal_document': re.compile(r'[（(]\d{4}[）)][^\s]*号')
        }

    def _init_classifier(self) -> Any:
        """初始化分类器配置"""
        self.threshold = 0.6  # 分类阈值
        self.max_keywords = 20  # 最大关键词数

    async def classify(self, text: str, context: Dict | None = None) -> Dict[str, Any]:
        """
        分类业务类型

        Args:
            text: 输入文本
            context: 上下文信息

        Returns:
            分类结果
        """
        try:
            # 文本预处理
            cleaned_text = self._preprocess_text(text)

            # 基于关键词的初步分类
            keyword_scores = await self._classify_by_keywords(cleaned_text)

            # 基于模式的分类
            pattern_scores = await self._classify_by_patterns(cleaned_text)

            # 基于上下文的分类
            context_scores = await self._classify_by_context(cleaned_text, context) if context else {}

            # 综合评分
            final_scores = self._combine_scores(keyword_scores, pattern_scores, context_scores)

            # 确定最终分类
            best_type = max(final_scores, key=final_scores.get)
            confidence = final_scores[best_type]

            # 如果置信度过低，返回未知类型
            if confidence < self.threshold:
                best_type = BusinessType.UNKNOWN
                confidence = 1.0 - confidence

            return {
                'business_type': best_type.value,
                'confidence': round(confidence, 3),
                'all_scores': {k.value: round(v, 3) for k, v in final_scores.items()},
                'keywords_found': self._get_found_keywords(cleaned_text),
                'patterns_found': self._get_found_patterns(cleaned_text),
                'reasoning': self._generate_reasoning(best_type, final_scores)
            }

        except Exception as e:
            logger.error(f"业务分类失败: {str(e)}")
            return {
                'business_type': BusinessType.UNKNOWN.value,
                'confidence': 0.0,
                'error': str(e)
            }

    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 转换为小写
        text = text.lower()
        # 移除多余空白
        text = ' '.join(text.split())
        return text

    async def _classify_by_keywords(self, text: str) -> Dict[BusinessType, float]:
        """基于关键词分类"""
        scores = {}

        for business_type, keywords_data in self.keywords.items():
            score = 0.0
            found_keywords = []

            # 检查主要关键词
            for keyword in keywords_data['primary']:
                if keyword in text:
                    score += 1.0
                    found_keywords.append(keyword)

            # 检查次要关键词
            for keyword in keywords_data['secondary']:
                if keyword in text:
                    score += 0.5
                    found_keywords.append(keyword)

            # 应用权重
            score *= keywords_data['weight']

            # 归一化
            max_possible = len(keywords_data['primary']) + 0.5 * len(keywords_data['secondary'])
            if max_possible > 0:
                score = score / max_possible

            scores[business_type] = min(score, 1.0)

        return scores

    async def _classify_by_patterns(self, text: str) -> Dict[BusinessType, float]:
        """基于模式分类"""
        scores = {bt: 0.0 for bt in BusinessType}

        # 检查专利号
        if self.patterns['patent_number'].search(text):
            scores[BusinessType.PATENT] += 0.8

        # 检查商标申请号
        if self.patterns['trademark_number'].search(text):
            scores[BusinessType.TRADEMARK] += 0.8

        # 检查合同编号
        if self.patterns['contract_number'].search(text):
            scores[BusinessType.CONTRACT] += 0.7

        # 检查法律文书
        if self.patterns['legal_document'].search(text):
            scores[BusinessType.LEGAL_ADVICE] += 0.6

        return scores

    async def _classify_by_context(self, text: str, context: Dict) -> Dict[BusinessType, float]:
        """基于上下文分类"""
        scores = {bt: 0.0 for bt in BusinessType}

        # 检查上下文中的线索
        if 'previous_queries' in context:
            for query in context['previous_queries']:
                query_type = await self.classify(query)
                if query_type['confidence'] > 0.8:
                    bt = BusinessType(query_type['business_type'])
                    scores[bt] += 0.3

        if 'user_history' in context:
            history = context['user_history']
            if 'patent_queries' in history and history['patent_queries'] > 5:
                scores[BusinessType.PATENT] += 0.2

        return scores

    def _combine_scores(self, keyword_scores: Dict, pattern_scores: Dict, context_scores: Dict) -> Dict[BusinessType, float]:
        """综合评分"""
        combined = {}

        for bt in BusinessType:
            # 加权平均
            combined[bt] = (
                keyword_scores.get(bt, 0) * 0.6 +
                pattern_scores.get(bt, 0) * 0.3 +
                context_scores.get(bt, 0) * 0.1
            )

        return combined

    def _get_found_keywords(self, text: str) -> List[str]:
        """获取找到的关键词"""
        found = []
        for business_type, keywords_data in self.keywords.items():
            for keyword in keywords_data['primary'] + keywords_data['secondary']:
                if keyword in text:
                    found.append(keyword)
        return found[:self.max_keywords]

    def _get_found_patterns(self, text: str) -> List[str]:
        """获取找到的模式"""
        found = []
        for pattern_name, pattern in self.patterns.items():
            if pattern.search(text):
                found.append(pattern_name)
        return found

    def _generate_reasoning(self, best_type: BusinessType, scores: Dict[BusinessType, float]) -> str:
        """生成推理说明"""
        if best_type == BusinessType.UNKNOWN:
            return "未能明确识别业务类型，需要更多信息"

        type_names = {
            BusinessType.PATENT: "专利业务",
            BusinessType.TRADEMARK: "商标业务",
            BusinessType.COPYRIGHT: "版权业务",
            BusinessType.CONTRACT: "合同业务",
            BusinessType.LEGAL_ADVICE: "法律咨询"
        }

        confidence = scores[best_type]
        reason = f"基于关键词和模式匹配，识别为{type_names.get(best_type, '未知业务')}，置信度{confidence:.2%}"

        return reason

# 使用示例
async def main():
    """测试业务分类器"""
    classifier = BusinessClassifier()

    test_cases = [
        "我想申请发明专利，技术方案是关于人工智能的",
        "这个商标被侵权了，我该如何维权？",
        "请帮我审查这份技术服务合同",
        "我的小说被抄袭了，这是否构成侵权？"
    ]

    for text in test_cases:
        result = await classifier.classify(text)
        print(f"\n输入: {text}")
        print(f"分类结果: {result}")

# 入口点: @async_main装饰器已添加到main函数