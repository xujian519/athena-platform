#!/usr/bin/env python3
"""
小娜专利命名系统 - 技术分析器
Xiaona Patent Naming System - Technical Analyzer

作者: 小娜·天秤女神
创建时间: 2025-12-17
重构时间: 2026-01-27
版本: v2.0.0

负责技术内容分析，包括技术领域识别、关键特征提取、应用场景分析等。
"""

import re
from typing import Any

from .types import PatentNamingRequest
from .rule_loader import RuleLoader


class TechnicalAnalyzer:
    """技术分析器 - 负责分析专利技术内容"""

    def __init__(self, technical_vocabulary: dict[str, list[str]]):
        """初始化技术分析器

        Args:
            technical_vocabulary: 技术词汇库
        """
        self.technical_vocabulary = technical_vocabulary

    async def analyze_technical_content(self, request: PatentNamingRequest) -> dict[str, Any]:
        """技术内容分析"""
        # 识别技术领域
        technical_field = self.identify_technical_field(request)

        # 提取关键技术特征
        key_features = self.extract_key_features(request)

        # 分析应用场景
        applications = self.analyze_applications(request)

        # 专业术语匹配
        professional_terms = self.match_professional_terms(request)

        return {
            "technical_field": technical_field,
            "key_features": key_features,
            "applications": applications,
            "professional_terms": professional_terms,
            "complexity_level": self.assess_complexity_level(request),
        }

    def identify_technical_field(self, request: PatentNamingRequest) -> str:
        """识别技术领域"""
        description = (
            request.invention_description.lower() + " " + " ".join(request.key_features).lower()
        )

        field_keywords = {
            "化学工程": ["反应", "催化剂", "合成", "工艺", "化工", "化学"],
            "机械工程": ["机械", "装置", "设备", "结构", "驱动", "传动"],
            "电子工程": ["电路", "电子", "芯片", "信号", "控制", "通信"],
            "生物技术": ["生物", "基因", "酶", "细胞", "培养", "菌株"],
            "材料科学": ["材料", "纳米", "复合材料", "合金", "涂层", "薄膜"],
            "信息技术": ["数据", "算法", "软件", "系统", "网络", "平台"],
            "能源技术": ["能源", "电池", "太阳能", "风能", "新能源", "节能"],
            "环境保护": ["环保", "处理", "净化", "回收", "废水", "废气"],
        }

        for field, keywords in field_keywords.items():
            if any(keyword in description for keyword in keywords):
                return field

        return "其他技术领域"

    def extract_key_features(self, request: PatentNamingRequest) -> list[str]:
        """提取关键技术特征"""
        features = []

        # 从用户提供的特征中提取
        for feature in request.key_features:
            cleaned_feature = re.sub(r"[^\w\u4e00-\u9fff]", "", feature)
            if len(cleaned_feature) > 1:
                features.append(cleaned_feature)

        # 从描述中提取技术术语
        description = request.invention_description
        technical_terms = re.findall(
            r"[A-Z][a-z]+(?:[A-Z][a-z]+)*|\w{2,}技术|\w{2,}装置|\w{2,}系统|\w{2,}方法", description
        )
        features.extend([term for term in technical_terms if len(term) > 1])

        return list(set(features))  # 去重

    def analyze_applications(self, request: PatentNamingRequest) -> list[str]:
        """分析应用场景"""
        applications = []

        # 用户提供的应用场景
        applications.extend(request.application_scenarios)

        # 根据技术领域推断应用场景
        field_applications = {
            "化学工程": ["化工生产", "石油化工", "精细化工", "制药化工"],
            "机械工程": ["制造业", "装备制造", "精密机械", "自动化设备"],
            "电子工程": ["电子设备", "通信设备", "控制系统", "消费电子"],
            "生物技术": ["生物医药", "农业生物", "工业生物", "环境生物"],
            "材料科学": ["新材料应用", "建筑工程", "汽车制造", "航空航天"],
            "信息技术": ["软件开发", "数据处理", "网络应用", "人工智能"],
        }

        request.invention_description.lower()
        technical_field = self.identify_technical_field(request)

        if technical_field in field_applications:
            for app in field_applications[technical_field]:
                if app not in applications:
                    applications.append(app)

        return applications

    def match_professional_terms(self, request: PatentNamingRequest) -> list[str]:
        """匹配专业术语"""
        terms = []

        # 从技术词汇库中匹配
        technical_field = self.identify_technical_field(request)
        if technical_field in self.technical_vocabulary:
            vocab = self.technical_vocabulary[technical_field]

            text = (
                request.invention_description
                + " "
                + " ".join(request.key_features)
                + " "
                + " ".join(request.innovation_points)
            ).lower()

            for term in vocab:
                if term in text:
                    terms.append(term)

        return terms

    def assess_complexity_level(self, request: PatentNamingRequest) -> str:
        """评估技术复杂度"""
        complexity_indicators = {
            "high": ["系统", "集成", "综合", "多级", "智能", "自动"],
            "medium": ["装置", "设备", "方法", "工艺", "结构"],
            "low": ["工具", "部件", "简单", "基础"],
        }

        text = (
            request.invention_description
            + " "
            + " ".join(request.key_features)
            + " "
            + " ".join(request.innovation_points)
        ).lower()

        for level, indicators in complexity_indicators.items():
            if any(indicator in text for indicator in indicators):
                return level

        return "medium"
