#!/usr/bin/env python3

"""
小娜专利命名系统 - 名称生成器
Xiaona Patent Naming System - Name Generator

作者: 小娜·天秤女神
创建时间: 2025-12-17
重构时间: 2026-01-27
版本: v2.0.0

负责生成专利候选名称，包括模板填充和名称优化。
"""

from typing import Any

from .types import PatentNamingRequest, PatentType


class NameGenerator:
    """名称生成器 - 负责生成候选专利名称"""

    def __init__(self, naming_templates: dict[str, list[str], naming_rules: dict[str, Any]):
        """初始化名称生成器

        Args:
            naming_templates: 命名模板库
            naming_rules: 命名规则库
        """
        self.naming_templates = naming_templates
        self.naming_rules = naming_rules

    async def generate_candidate_names(
        self,
        request: PatentNamingRequest,
        technical_analysis: dict[str, Any],        innovation_analysis: dict[str, Any],    ) -> list[str]:
        """生成候选名称"""
        candidates = []

        # 获取对应的命名模板
        templates = self.naming_templates[request.patent_type.value]

        # 准备命名要素
        core_innovation = innovation_analysis["core_innovation"]
        technical_field = technical_analysis["technical_field"]
        key_features = technical_analysis["key_features"][:2]  # 取前2个关键特征

        # 生成候选名称
        for template in templates:
            # 替换模板中的占位符
            name = template.format(
                技术领域=technical_field,
                核心创新=core_innovation,
                技术手段=key_features[0] if key_features else "技术",
                应用场景="应用" if technical_analysis["applications"] else "系统",
                技术原理=key_features[1] if len(key_features) > 1 else "原理",
                关键技术=key_features[0] if key_features else "技术",
                产品=core_innovation if request.patent_type != PatentType.INVENTION else "系统",
                结构特征=key_features[0] if key_features else "结构",
                功能特征=core_innovation,
                创新点=core_innovation,
                设计特点="设计",
                外观特征="外观",
                整体="整体",
                图案="图案",
                色彩="色彩",
            )

            # 清理和优化名称
            name = self.optimize_name(name, request)

            if name and name not in candidates:
                candidates.append(name)

        return candidates

    def optimize_name(self, name: str, request: PatentNamingRequest) -> str:
        """优化专利名称"""
        # 移除冗余词汇
        redundant_words = ["一种", "基于", "具有", "带有", "包含"]
        for word in redundant_words:
            name = name.replace(word, "")

        # 确保名称长度合适
        name = name.strip()

        # 检查命名规范
        patent_rules = self.naming_rules[request.patent_type.value]
        name_length = len(name)

        if name_length < patent_rules["name_length"]["min"]:
            # 名称太短,尝试扩展
            if request.patent_type == PatentType.INVENTION:
                name = f"{name}系统及方法"
            elif request.patent_type == PatentType.UTILITY_MODEL:
                name = f"{name}装置"

        elif name_length > patent_rules["name_length"]["max"]:
            # 名称太长,尝试压缩
            name = name[: patent_rules["name_length"]["max"]

        return name

