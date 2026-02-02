#!/usr/bin/env python3
"""
小娜专利命名系统 - 创新点提取器
Xiaona Patent Naming System - Innovation Extractor

作者: 小娜·天秤女神
创建时间: 2025-12-17
重构时间: 2026-01-27
版本: v2.0.0

负责创新点提炼和分类，识别核心创新点。
"""

import re
from typing import Any

from .types import PatentNamingRequest, PatentType


class InnovationExtractor:
    """创新点提取器 - 负责提炼和分类创新点"""

    async def extract_innovation_points(self, request: PatentNamingRequest) -> dict[str, Any]:
        """提炼创新点"""
        # 分析用户提供的创新点
        user_innovations = request.innovation_points

        # 从描述中识别隐含创新点
        description = request.invention_description

        implicit_innovations = self.identify_implicit_innovations(description)

        # 创新点分类
        innovation_categories = {
            "technical_innovation": [],
            "functional_innovation": [],
            "structural_innovation": [],
            "application_innovation": [],
        }

        all_innovations = user_innovations + implicit_innovations

        for innovation in all_innovations:
            category = self.classify_innovation(innovation, request)
            innovation_categories[category].append(innovation)

        # 核心创新点
        core_innovation = self.identify_core_innovation(innovation_categories, request)

        return {
            "user_innovations": user_innovations,
            "implicit_innovations": implicit_innovations,
            "innovation_categories": innovation_categories,
            "core_innovation": core_innovation,
            "innovation_level": self.assess_innovation_level(all_innovations),
        }

    def identify_implicit_innovations(self, description: str) -> list[str]:
        """识别隐含创新点"""
        innovations = []

        # 创新模式识别
        innovation_patterns = [
            r".*?(\w+).*?智能.*?(\w+).*?",
            r".*?(\w+).*?自动.*?(\w+).*?",
            r".*?(\w+).*?高效.*?(\w+).*?",
            r".*?(\w+).*?新型.*?(\w+).*?",
            r".*?(\w+).*?集成.*?(\w+).*?",
        ]

        for pattern in innovation_patterns:
            matches = re.findall(pattern, description)
            for match in matches:
                if isinstance(match, tuple):
                    innovation = f"智能{match[0]}{match[1]}"
                else:
                    innovation = f"智能{match}"
                if innovation not in innovations:
                    innovations.append(innovation)

        return innovations

    def classify_innovation(self, innovation: str, request: PatentNamingRequest) -> str:
        """创新点分类"""
        innovation_lower = innovation.lower()

        # 技术创新
        if any(word in innovation_lower for word in ["技术", "方法", "工艺", "算法", "方案"]):
            return "technical_innovation"

        # 功能创新
        if any(word in innovation_lower for word in ["功能", "性能", "效果", "作用", "能力"]):
            return "functional_innovation"

        # 结构创新
        if any(word in innovation_lower for word in ["结构", "构造", "形状", "形式", "组成"]):
            return "structural_innovation"

        # 应用创新
        if any(word in innovation_lower for word in ["应用", "用途", "场景", "领域", "场合"]):
            return "application_innovation"

        return "technical_innovation"  # 默认分类

    def identify_core_innovation(
        self, categories: dict[str, list[str]], request: PatentNamingRequest
    ) -> str:
        """识别核心创新点"""
        # 根据专利类型确定核心创新点
        if request.patent_type == PatentType.INVENTION:
            # 发明专利优先技术创新和功能创新
            for category in ["technical_innovation", "functional_innovation"]:
                if categories[category]:
                    return categories[category][0]

        elif request.patent_type == PatentType.UTILITY_MODEL:
            # 实用新型优先结构创新
            if categories["structural_innovation"]:
                return categories["structural_innovation"][0]
            if categories["functional_innovation"]:
                return categories["functional_innovation"][0]

        elif request.patent_type == PatentType.DESIGN:
            # 外观设计优先结构创新
            if categories["structural_innovation"]:
                return categories["structural_innovation"][0]

        # 默认返回第一个创新点
        for innovations in categories.values():
            if innovations:
                return innovations[0]

        return "技术创新"

    def assess_innovation_level(self, innovations: list[str]) -> str:
        """评估创新水平"""
        high_level_keywords = ["突破性", "革命性", "颠覆性", "开创性", "原创性"]
        medium_level_keywords = ["创新", "改进", "优化", "提升", "增强"]

        text = " ".join(innovations).lower()

        if any(keyword in text for keyword in high_level_keywords):
            return "high"
        elif any(keyword in text for keyword in medium_level_keywords):
            return "medium"
        else:
            return "low"
