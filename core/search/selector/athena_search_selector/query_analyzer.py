#!/usr/bin/env python3
from __future__ import annotations
"""
Athena智能搜索选择器 - 查询分析器
Athena Search Selector - Query Analyzer

作者: Athena AI系统
创建时间: 2025-12-05
重构时间: 2026-01-27
版本: 2.0.0

负责深度查询分析，理解用户意图和需求。
"""

import logging
import re
from typing import Any

from ...standards.base_search_tool import QueryComplexity
from .types import (
    DomainType,
    QueryAnalysis,
    QueryIntent,
)

logger = logging.getLogger(__name__)


class QueryAnalyzer:
    """查询分析器 - 负责分析查询文本"""

    def __init__(self):
        """初始化查询分析器"""
        self._intent_patterns = self._load_intent_patterns()
        self._domain_keywords = self._load_domain_keywords()

    def _load_intent_patterns(self) -> dict[QueryIntent, list[dict[str, Any]]]:
        """加载意图模式"""
        return {
            QueryIntent.INFORMATIONAL: [
                {'patterns': [r'what\s+is', r'define', r'解释', r'什么是'], 'weight': 0.9},
                {'patterns': [r'how\s+to', r'如何', r'怎么'], 'weight': 0.8},
                {'patterns': [r'tell\s+me\s+about', r'介绍', r'信息'], 'weight': 0.7}
            ],
            QueryIntent.RESEARCH: [
                {'patterns': [r'research', r'study', r'研究', r'学术'], 'weight': 0.9},
                {'patterns': [r'paper', r'article', r'论文', r'文献'], 'weight': 0.8},
                {'patterns': [r'experiment', r'实验', r'调查'], 'weight': 0.7}
            ],
            QueryIntent.COMPARISON: [
                {'patterns': [r'compare', r'vs', r'对比', r'比较'], 'weight': 0.9},
                {'patterns': [r'difference', r'区别', r'差异'], 'weight': 0.8},
                {'patterns': [r'better', r'best', r'更好', r'最佳'], 'weight': 0.7}
            ],
            QueryIntent.ANALYSIS: [
                {'patterns': [r'analyze', r'analysis', r'分析'], 'weight': 0.9},
                {'patterns': [r'trend', r'趋势', r'发展'], 'weight': 0.8},
                {'patterns': [r'pattern', r'模式', r'规律'], 'weight': 0.7}
            ],
            QueryIntent.VERIFICATION: [
                {'patterns': [r'verify', r'check', r'验证', r'检查'], 'weight': 0.9},
                {'patterns': [r'confirm', r'确认', r'证明'], 'weight': 0.8},
                {'patterns': [r'is\s+.*\s+true', r'是否', r'对吗'], 'weight': 0.7}
            ],
            QueryIntent.PATENT: [
                {'patterns': [r'patent', r'专利', r'US\d+', r'CN\d+'], 'weight': 0.95},
                {'patterns': [r'invention', r'发明', r'创新'], 'weight': 0.7},
                {'patterns': [r'IP', r'intellectual\s+property', r'知识产权'], 'weight': 0.8}
            ]
        }

    def _load_domain_keywords(self) -> dict[DomainType, dict[str, float]]:
        """加载领域关键词"""
        return {
            DomainType.PATENT: {
                'patent': 0.95, '专利': 0.95, 'US': 0.8, 'CN': 0.8,
                'invention': 0.8, '发明': 0.8, 'innovation': 0.7, '创新': 0.7,
                'IP': 0.7, 'intellectual property': 0.7, '知识产权': 0.7
            },
            DomainType.ACADEMIC: {
                'research': 0.9, '研究': 0.9, 'paper': 0.9, '论文': 0.9,
                'journal': 0.8, '期刊': 0.8, 'article': 0.8, '文章': 0.8,
                'study': 0.7, '学习': 0.7, 'experiment': 0.7, '实验': 0.7
            },
            DomainType.BUSINESS: {
                'business': 0.9, '商业': 0.9, 'company': 0.8, '公司': 0.8,
                'market': 0.8, '市场': 0.8, 'industry': 0.7, '行业': 0.7,
                'finance': 0.7, '金融': 0.7, 'economy': 0.7, '经济': 0.7
            },
            DomainType.TECHNOLOGY: {
                'technology': 0.9, '技术': 0.9, 'software': 0.8, '软件': 0.8,
                'AI': 0.8, '人工智能': 0.8, 'programming': 0.7, '编程': 0.7,
                'algorithm': 0.7, '算法': 0.7, 'data': 0.6, '数据': 0.6
            },
            DomainType.LEGAL: {
                'legal': 0.95, '法律': 0.95, 'law': 0.9, '法': 0.9,
                'court': 0.8, '法院': 0.8, 'case': 0.8, '案例': 0.8,
                'regulation': 0.7, '法规': 0.7, 'compliance': 0.7, '合规': 0.7
            }
        }

    async def analyze(self, query_text: str) -> QueryAnalysis:
        """
        分析查询

        Args:
            query_text: 查询文本

        Returns:
            QueryAnalysis: 查询分析结果
        """
        try:
            # 基本文本处理
            normalized_text = self._normalize_text(query_text)
            language = self._detect_language(normalized_text)
            complexity = self._analyze_complexity(normalized_text)

            # 意图分析
            primary_intent, secondary_intents, intent_confidence = await self._analyze_intent(normalized_text)

            # 领域识别
            primary_domain, secondary_domains, domain_confidence = self._analyze_domain(normalized_text)

            # 关键词提取
            keywords = self._extract_keywords(normalized_text)
            entities = self._extract_entities(normalized_text)
            technical_terms = self._extract_technical_terms(normalized_text)

            # 时间信息
            temporal_indicators = self._extract_temporal_indicators(normalized_text)
            time_sensitivity = len(temporal_indicators) > 0

            # 地理信息
            geographic_indicators = self._extract_geographic_indicators(normalized_text)
            geographic_scope = self._determine_geographic_scope(geographic_indicators)

            # 质量要求评估
            precision_requirement = self._assess_precision_requirement(normalized_text, complexity)
            freshness_requirement = self._assess_freshness_requirement(temporal_indicators)
            completeness_requirement = self._assess_completeness_requirement(primary_intent, complexity)

            return QueryAnalysis(
                original_text=query_text,
                normalized_text=normalized_text,
                language=language,
                complexity=complexity,
                primary_intent=primary_intent,
                secondary_intents=secondary_intents,
                confidence=intent_confidence,
                primary_domain=primary_domain,
                secondary_domains=secondary_domains,
                domain_confidence=domain_confidence,
                keywords=keywords,
                entities=entities,
                technical_terms=technical_terms,
                temporal_indicators=temporal_indicators,
                time_sensitivity=time_sensitivity,
                geographic_indicators=geographic_indicators,
                geographic_scope=geographic_scope,
                precision_requirement=precision_requirement,
                freshness_requirement=freshness_requirement,
                completeness_requirement=completeness_requirement
            )

        except Exception as e:
            logger.error(f"❌ 查询分析失败: {e}")
            # 返回默认分析结果
            return QueryAnalysis(
                original_text=query_text,
                normalized_text=query_text.lower(),
                language='unknown',
                complexity=QueryComplexity.SIMPLE,
                primary_intent=QueryIntent.INFORMATIONAL,
                secondary_intents=[],
                confidence=0.5,
                primary_domain=DomainType.GENERAL,
                secondary_domains=[],
                domain_confidence=0.5,
                keywords=[],
                entities=[],
                technical_terms=[],
                temporal_indicators=[],
                time_sensitivity=False,
                geographic_indicators=[],
                geographic_scope='global',
                precision_requirement=0.5,
                freshness_requirement=0.5,
                completeness_requirement=0.5
            )

    # 文本处理方法
    def _normalize_text(self, text: str) -> str:
        """标准化文本"""
        # 转小写,移除多余空格
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text)
        return text

    def _detect_language(self, text: str) -> str:
        """检测语言"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-z_A-Z]', text))

        if chinese_chars > english_chars:
            return 'zh'
        elif english_chars > 0:
            return 'en'
        else:
            return 'unknown'

    def _analyze_complexity(self, text: str) -> QueryComplexity:
        """分析查询复杂度"""
        word_count = len(text.split())

        # 检查逻辑运算符
        has_logic = any(op in text for op in ['and', 'or', 'not', '&&', '||', '!', '且', '或', '非'])

        # 检查分析型关键词
        analytic_keywords = ['analyze', 'analysis', 'compare', 'comparison', 'trend', '分析', '对比', '趋势']
        has_analytic = any(kw in text for kw in analytic_keywords)

        if has_analytic or word_count > 8:
            return QueryComplexity.ANALYTICAL
        elif has_logic or word_count > 5:
            return QueryComplexity.COMPLEX
        elif word_count >= 3:
            return QueryComplexity.MEDIUM
        else:
            return QueryComplexity.SIMPLE

    # 意图和领域分析
    async def _analyze_intent(self, text: str) -> tuple[QueryIntent, list[QueryIntent], float]:
        """分析查询意图"""
        intent_scores = {}

        # 基于模式匹配
        for intent, patterns in self._intent_patterns.items():
            score = 0.0
            for pattern_info in patterns:
                for pattern in pattern_info['patterns']:
                    if re.search(pattern, text, re.IGNORECASE):
                        score += pattern_info['weight']

            intent_scores[intent] = min(score, 1.0)

        # 找到主要意图
        if not intent_scores:
            return QueryIntent.INFORMATIONAL, [], 0.5

        primary_intent = max(intent_scores.keys(), key=lambda k: intent_scores[k])
        primary_score = intent_scores[primary_intent]

        # 找到次要意图
        secondary_intents = [
            intent for intent, score in intent_scores.items()
            if intent != primary_intent and score > 0.3
        ]

        return primary_intent, secondary_intents, primary_score

    def _analyze_domain(self, text: str) -> tuple[DomainType, list[DomainType], float]:
        """分析领域"""
        domain_scores = {}

        # 基于关键词匹配
        for domain, keywords in self._domain_keywords.items():
            score = 0.0
            for keyword, weight in keywords.items():
                if keyword in text:
                    score += weight

            domain_scores[domain] = min(score, 1.0)

        # 找到主要领域
        if not domain_scores:
            return DomainType.GENERAL, [], 0.5

        primary_domain = max(domain_scores.keys(), key=lambda k: domain_scores[k])
        primary_score = domain_scores[primary_domain]

        # 找到次要领域
        secondary_domains = [
            domain for domain, score in domain_scores.items()
            if domain != primary_domain and score > 0.3
        ]

        return primary_domain, secondary_domains, primary_score

    # 提取方法
    def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词"""
        # 简化的关键词提取
        words = re.findall(r'\b\w+\b', text)
        # 过滤停用词和短词
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', '的', '了', '是', '在', '有', '和', '就', '不', '人', '都', '一'}
        keywords = [word for word in words if len(word) > 2 and word.lower() not in stop_words]
        return keywords[:10]  # 限制数量

    def _extract_entities(self, text: str) -> list[str]:
        """提取实体"""
        entities = []

        # 简单的实体模式匹配
        # 专利号
        patent_pattern = r'\b[A-Z]{2}\d+\b'
        entities.extend(re.findall(patent_pattern, text))

        # 公司名 (简化版)
        company_pattern = r'\b[A-Z][a-z]+\s+(?:Inc|Corp|Ltd|Company|公司)\b'
        entities.extend(re.findall(company_pattern, text, re.IGNORECASE))

        return list(set(entities))  # 去重

    def _extract_technical_terms(self, text: str) -> list[str]:
        """提取技术术语"""
        # 简化的技术术语识别
        technical_patterns = [
            r'\b[A-Z]{2,}\b',  # 缩写
            r'\b\w+[-_]\w+\b',  # 连字符术语
            r'\b\w+(?:tion|ment|ness|ity|ism)\b'  # 常见技术后缀
        ]

        terms = []
        for pattern in technical_patterns:
            terms.extend(re.findall(pattern, text))

        return list(set(terms))

    def _extract_temporal_indicators(self, text: str) -> list[str]:
        """提取时间指示词"""
        temporal_patterns = [
            r'\b(?:recently|latest|current|today|now|recent)\b',
            r'\b(?:最近|最新|当前|今天|现在)\b',
            r'\b\d{4}\b',  # 年份
            r'\b(?:last|past|previous)\s+\d+\s*(?:years?|months?|days?)\b',
            r'\b(?:过去|最近|前)\s*\d+\s*(?:年|月|日)\b'
        ]

        indicators = []
        for pattern in temporal_patterns:
            indicators.extend(re.findall(pattern, text, re.IGNORECASE))

        return indicators

    def _extract_geographic_indicators(self, text: str) -> list[str]:
        """提取地理指示词"""
        geo_patterns = [
            r'\b(?:US|USA|United\s+States)\b',
            r'\b(?:China|CN|Chinese)\b',
            r'\b(?:Europe|EU|European)\b',
            r'\b(?:美国|中国|欧洲)\b',
            r'\b[A-Z]{2}\s*\d{5}\b'  # 美国邮编
        ]

        indicators = []
        for pattern in geo_patterns:
            indicators.extend(re.findall(pattern, text, re.IGNORECASE))

        return indicators

    def _determine_geographic_scope(self, indicators: list[str]) -> str:
        """确定地理范围"""
        if not indicators:
            return 'global'

        # 简化的地理范围判断
        if any(ind in ['US', 'USA', '美国'] for ind in indicators):
            return 'us'
        elif any(ind in ['China', 'CN', '中国'] for ind in indicators):
            return 'china'
        elif any(ind in ['Europe', 'EU', '欧洲'] for ind in indicators):
            return 'europe'
        else:
            return 'regional'

    # 质量评估方法
    def _assess_precision_requirement(self, text: str, complexity: QueryComplexity) -> float:
        """评估精度要求"""
        precision_indicators = [
            r'\b(?:exact|precise|specific|accurate)\b',
            r'\b(?:精确|准确|具体)\b',
            r'\b(?:must\s+be|require|need)\b'
        ]

        base_score = 0.5

        # 复杂度加分
        if complexity == QueryComplexity.ANALYTICAL:
            base_score += 0.2
        elif complexity == QueryComplexity.COMPLEX:
            base_score += 0.1

        # 关键词加分
        for pattern in precision_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                base_score += 0.2
                break

        return min(base_score, 1.0)

    def _assess_freshness_requirement(self, temporal_indicators: list[str]) -> float:
        """评估新鲜度要求"""
        if not temporal_indicators:
            return 0.5

        # 基于时间指示词判断
        recent_indicators = ['recent', 'latest', 'current', '最近', '最新', '当前']
        if any(ind in temporal_indicators for ind in recent_indicators):
            return 0.9

        # 有具体年份
        year_pattern = r'\b20(1|2)\d\b'
        if re.search(year_pattern, ' '.join(temporal_indicators)):
            return 0.7

        return 0.6

    def _assess_completeness_requirement(self, intent: QueryIntent, complexity: QueryComplexity) -> float:
        """评估完整性要求"""
        base_score = 0.5

        # 意图相关要求
        if intent in [QueryIntent.RESEARCH, QueryIntent.COMPARISON, QueryIntent.ANALYSIS]:
            base_score += 0.3
        elif intent == QueryIntent.VERIFICATION:
            base_score += 0.2

        # 复杂度相关要求
        if complexity == QueryComplexity.ANALYTICAL:
            base_score += 0.2

        return min(base_score, 1.0)
