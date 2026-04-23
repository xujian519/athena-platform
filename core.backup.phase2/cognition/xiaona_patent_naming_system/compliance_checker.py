#!/usr/bin/env python3
from __future__ import annotations
"""
小娜专利命名系统 - 规范性检查器
Xiaona Patent Naming System - Compliance Checker

作者: 小娜·天秤女神
创建时间: 2025-12-17
重构时间: 2026-01-27
版本: v2.0.0

负责专利命名的规范性检查和排序。
"""

from typing import Any

from .types import PatentNamingRequest


class ComplianceChecker:
    """规范性检查器 - 负责检查命名规范性和排序"""

    def __init__(self, naming_rules: dict[str, Any]):
        """初始化规范性检查器

        Args:
            naming_rules: 命名规则库
        """
        self.naming_rules = naming_rules

    async def check_compliance(
        self, candidate_names: list[str], request: PatentNamingRequest
    ) -> list[dict[str, Any]]:
        """检查命名规范性"""
        compliant_names = []

        for name in candidate_names:
            compliance_result = {"name": name, "compliant": True, "issues": [], "score": 1.0}

            # 检查命名规则
            rules = self.naming_rules[request.patent_type.value]

            # 检查长度
            name_length = len(name)
            if (
                name_length < rules["name_length"]["min"]
                or name_length > rules["name_length"]["max"]
            ):
                compliance_result["compliant"] = False
                compliance_result["issues"].append(f"名称长度不符合要求: {name_length}")
                compliance_result["score"] -= 0.3

            # 检查禁用词汇
            for forbidden_word in rules["forbidden_words"]:
                if forbidden_word in name:
                    compliance_result["compliant"] = False
                    compliance_result["issues"].append(f"包含禁用词汇: {forbidden_word}")
                    compliance_result["score"] -= 0.2

            # 检查必需元素
            required_found = False
            for element in rules["required_elements"]:
                if element in name:
                    required_found = True
                    break

            if not required_found:
                compliance_result["compliant"] = False
                compliance_result["issues"].append("缺少必需元素")
                compliance_result["score"] -= 0.2

            # 检查是否包含关键词
            keyword_found = False
            for keyword in rules["keywords"]:
                if keyword in name:
                    keyword_found = True
                    break

            if not keyword_found:
                compliance_result["issues"].append("建议包含专业关键词")
                compliance_result["score"] -= 0.1

            compliant_names.append(compliance_result)

        return compliant_names

    async def rank_names(
        self, compliant_names: list[dict[str, Any]], request: PatentNamingRequest
    ) -> list[str]:
        """排序候选名称"""
        # 按规范性和质量评分排序
        sorted_names = sorted(
            compliant_names, key=lambda x: (x["compliant"], x["score"]), reverse=True
        )

        # 返回排序后的名称列表
        return [name_data.get("name") for name_data in sorted_names]  # type: ignore
