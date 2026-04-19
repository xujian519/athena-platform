#!/usr/bin/env python3
from __future__ import annotations
"""
小娜专利命名系统 - 主系统
Xiaona Patent Naming System - Main System

作者: 小娜·天秤女神
创建时间: 2025-12-17
重构时间: 2026-01-27
版本: v2.0.0

专利命名系统的主类，协调各个组件完成专利命名任务。
"""

import logging

from core.logging_config import setup_logging

from .compliance_checker import ComplianceChecker
from .innovation_extractor import InnovationExtractor
from .name_generator import NameGenerator
from .rule_loader import RuleLoader
from .technical_analyzer import TechnicalAnalyzer
from .types import PatentNamingRequest, PatentNamingResult, PatentType

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class XiaonaPatentNamingSystem:
    """小娜专利命名系统"""

    def __init__(self):
        self.name = "小娜专利命名系统"
        self.version = "v2.0.0 Professional"

        # 加载规则和数据
        self.naming_rules = RuleLoader.load_naming_rules()
        self.technical_vocabulary = RuleLoader.load_technical_vocabulary()
        self.naming_templates = RuleLoader.load_naming_templates()
        self.success_cases = RuleLoader.load_success_cases()

        # 初始化组件
        self.technical_analyzer = TechnicalAnalyzer(self.technical_vocabulary)
        self.innovation_extractor = InnovationExtractor()
        self.name_generator = NameGenerator(self.naming_templates, self.naming_rules)
        self.compliance_checker = ComplianceChecker(self.naming_rules)

        # 专业能力评分
        self.professional_scores = {
            "patent_naming": 0.95,
            "technical_analysis": 0.92,
            "innovation_identification": 0.88,
            "compliance_check": 0.95,
        }

        logger.info(f"✅ 初始化{self.name} {self.version}")

    async def generate_patent_name(self, request: PatentNamingRequest) -> PatentNamingResult:
        """生成专利名称"""
        logger.info(f"开始生成专利名称: {request.patent_type.value}")

        try:
            # 1. 技术分析
            technical_analysis = await self.technical_analyzer.analyze_technical_content(request)

            # 2. 创新点提炼
            innovation_analysis = await self.innovation_extractor.extract_innovation_points(request)

            # 3. 生成候选名称
            candidate_names = await self.name_generator.generate_candidate_names(
                request, technical_analysis, innovation_analysis
            )

            # 4. 规范性检查
            compliant_names = await self.compliance_checker.check_compliance(candidate_names, request)

            # 5. 排序和优化
            ranked_names = await self.compliance_checker.rank_names(compliant_names, request)

            # 6. 生成最终结果
            result = await self._generate_naming_result(
                ranked_names, request, technical_analysis, innovation_analysis
            )

            logger.info(f"专利命名生成完成: {result.patent_name}")
            return result

        except Exception as e:
            logger.error(f"专利命名生成失败: {e}")
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    async def _generate_naming_result(
        self,
        ranked_names: list[str],
        request: PatentNamingRequest,
        technical_analysis: dict,
        innovation_analysis: dict,
    ) -> PatentNamingResult:
        """生成最终命名结果"""
        if not ranked_names:
            raise ValueError("无法生成符合规范的专利名称")

        # 选择最佳名称
        best_name = ranked_names[0]
        alternative_names = ranked_names[1:5]  # 取前4个作为备选

        # 生成命名依据
        naming_rationale = self._generate_naming_rationale(
            best_name, request, technical_analysis, innovation_analysis
        )

        # 提取技术亮点
        technical_highlights = technical_analysis["key_features"][:3]

        # 提取创新亮点
        innovation_highlights = list(
            set(
                innovation_analysis["user_innovations"]
                + innovation_analysis["implicit_innovations"]
            )
        )[:3]

        # 规范性检查结果
        compliance_check = {
            "patent_type": request.patent_type.value,
            "name_length": len(best_name),
            "compliant": True,
            "checked_items": ["长度规范", "禁用词汇", "专业术语", "结构要求"],
        }

        # 计算置信度
        naming_confidence = self._calculate_naming_confidence(best_name, request)

        # 生成专业见解
        professional_insights = self._generate_professional_insights(
            best_name, request, technical_analysis, innovation_analysis
        )

        # 生成建议
        recommendations = self._generate_recommendations(best_name, alternative_names, request)

        return PatentNamingResult(
            patent_name=best_name,
            alternative_names=alternative_names,
            naming_rationale=naming_rationale,
            technical_highlights=technical_highlights,
            innovation_highlights=innovation_highlights,
            compliance_check=compliance_check,
            naming_confidence=naming_confidence,
            professional_insights=professional_insights,
            recommendations=recommendations,
        )

    def _generate_naming_rationale(
        self,
        name: str,
        request: PatentNamingRequest,
        technical_analysis: dict,
        innovation_analysis: dict,
    ) -> str:
        """生成命名依据"""
        rationale_parts = []

        # 技术领域依据
        rationale_parts.append(f"基于技术领域'{technical_analysis['technical_field']}'的命名定位")

        # 创新点依据
        core_innovation = innovation_analysis["core_innovation"]
        rationale_parts.append(f"突出核心创新点'{core_innovation}'的技术价值")

        # 专利类型依据
        patent_type_mapping = {
            PatentType.INVENTION: "发明专利",
            PatentType.UTILITY_MODEL: "实用新型专利",
            PatentType.DESIGN: "外观设计专利",
        }
        rationale_parts.append(f"符合{patent_type_mapping[request.patent_type]}的命名规范")

        # 专业术语依据
        if technical_analysis["professional_terms"]:
            terms = technical_analysis["professional_terms"][:2]
            rationale_parts.append(f"融入专业术语'{', '.join(terms)}'提升专业性")

        return ";".join(rationale_parts) + "。"

    def _calculate_naming_confidence(self, name: str, request: PatentNamingRequest) -> float:
        """计算命名置信度"""
        confidence = 0.8  # 基础置信度

        # 根据名称长度调整
        name_length = len(name)
        if 10 <= name_length <= 20:
            confidence += 0.1
        elif name_length < 5 or name_length > 25:
            confidence -= 0.2

        # 根据技术特征数量调整
        if len(request.key_features) >= 3:
            confidence += 0.05

        # 根据创新点数量调整
        if len(request.innovation_points) >= 2:
            confidence += 0.05

        # 根据专业程度调整
        professional_terms = request.invention_description + " ".join(request.key_features)
        if len(professional_terms) > 50:
            confidence += 0.05

        return min(confidence, 1.0)

    def _generate_professional_insights(
        self,
        name: str,
        request: PatentNamingRequest,
        technical_analysis: dict,
        innovation_analysis: dict,
    ) -> list[str]:
        """生成专业见解"""
        insights = []

        # 技术见解
        complexity = technical_analysis["complexity_level"]
        if complexity == "high":
            insights.append("该专利涉及复杂技术系统,建议在说明书中详细描述技术方案")
        elif complexity == "medium":
            insights.append("该专利技术难度适中,建议突出核心技术创新点")

        # 创新见解
        innovation_level = innovation_analysis["innovation_level"]
        if innovation_level == "high":
            insights.append("该专利具有较高创新水平,建议强调突破性技术特征")
        elif innovation_level == "medium":
            insights.append("该专利具有改进性创新,建议重点说明技术优势")

        # 申请策略见解
        if request.patent_type == PatentType.INVENTION:
            insights.append("发明专利名称建议体现技术先进性和创新性")
        elif request.patent_type == PatentType.UTILITY_MODEL:
            insights.append("实用新型专利名称建议突出形状、构造或功能改进")

        # 保护范围见解
        if len(name) < 15:
            insights.append("名称较为简洁,保护范围相对较宽,有利但不建议过于宽泛")
        else:
            insights.append("名称较为具体,保护范围相对较窄,建议注意保护范围的适当性")

        return insights

    def _generate_recommendations(
        self, best_name: str, alternative_names: list[str], request: PatentNamingRequest
    ) -> list[str]:
        """生成建议"""
        recommendations = []

        # 备选方案建议
        if alternative_names:
            recommendations.append(f"可考虑备选名称: {'、'.join(alternative_names[:2])}")

        # 客户沟通建议
        if request.client_info:
            recommendations.append("建议与客户确认命名偏好,确保符合品牌定位")

        # 商业价值建议
        recommendations.append("建议考虑命名的商业价值和市场传播性")

        # 法律保护建议
        recommendations.append("建议进行商标查询,避免与现有商标冲突")

        # 后续维护建议
        recommendations.append("建议在后续申请过程中保持名称的一致性")

        return recommendations

    async def generate_batch_naming(
        self, requests: list[PatentNamingRequest]
    ) -> list[PatentNamingResult]:
        """批量生成专利名称"""
        results = []

        for request in requests:
            try:
                result = await self.generate_patent_name(request)
                results.append(result)
            except Exception as e:
                # 创建失败结果
                failed_result = PatentNamingResult(
                    patent_name="",
                    alternative_names=[],
                    naming_rationale="命名生成失败",
                    technical_highlights=[],
                    innovation_highlights=[],
                    compliance_check={"error": str(e)},
                    naming_confidence=0.0,
                    professional_insights=["需要重新评估技术内容"],
                    recommendations=["请提供更详细的技术描述"],
                )
                results.append(failed_result)

        return results

    async def analyze_naming_case(self, patent_name: str, patent_type: str) -> dict:
        """分析现有专利命名案例"""
        analysis = {
            "patent_name": patent_name,
            "patent_type": patent_type,
            "name_analysis": {},
            "strengths": [],
            "weaknesses": [],
            "suggestions": [],
            "similarity_score": 0.0,
        }

        # 名称长度分析
        name_length = len(patent_name)
        if patent_type in self.naming_rules:
            rules = self.naming_rules[patent_type]
            analysis["name_analysis"]["length"] = {  # type: ignore
                "current": name_length,
                "recommended_min": rules["name_length"]["min"],
                "recommended_max": rules["name_length"]["max"],
                "appropriate": rules["name_length"]["min"]
                <= name_length
                <= rules["name_length"]["max"],
            }

        # 结构分析
        structure_keywords = ["一种", "基于", "具有", "带有", "包含"]
        has_structure = any(keyword in patent_name for keyword in structure_keywords)
        analysis["name_analysis"]["structure"] = {  # type: ignore
            "has_structure": has_structure,
            "structure_type": self._identify_naming_structure(patent_name),
        }

        # 专业性分析
        professional_terms = []
        if patent_type == "invention":
            professional_terms = ["系统", "方法", "工艺", "装置", "设备"]
        elif patent_type == "utility_model":
            professional_terms = ["装置", "设备", "工具", "机构", "结构"]
        elif patent_type == "design":
            professional_terms = ["外观", "设计", "造型", "图案"]

        has_professional = any(term in patent_name for term in professional_terms)
        analysis["name_analysis"]["professionalism"] = {  # type: ignore
            "has_professional_terms": has_professional,
            "matched_terms": [term for term in professional_terms if term in patent_name],
        }

        # 优势和不足分析
        if analysis["name_analysis"]["length"]["appropriate"]:  # type: ignore
            analysis["strengths"].append("名称长度符合规范要求")
        else:
            analysis["weaknesses"].append("名称长度不符合规范要求")

        if has_structure:
            analysis["strengths"].append("命名结构完整")
        else:
            analysis["weaknesses"].append("缺乏完整的命名结构")

        if has_professional:
            analysis["strengths"].append("包含专业术语,提升专业性")
        else:
            analysis["weaknesses"].append("缺乏专业术语,影响专业性")

        # 改进建议
        if not analysis["name_analysis"]["length"]["appropriate"]:  # type: ignore
            rules = self.naming_rules[patent_type]
            if name_length < rules["name_length"]["min"]:
                analysis["suggestions"].append("建议增加描述性词汇,使名称更加完整")
            else:
                analysis["suggestions"].append("建议简化名称,去除冗余词汇")

        if not has_structure:
            analysis["suggestions"].append("建议添加结构词汇,如'一种'、'基于'等")

        if not has_professional:
            analysis["suggestions"].append(
                f"建议添加专业术语,如{', '.join(professional_terms[:3])}等"
            )

        # 与成功案例的相似度
        similarities = []
        for case in self.success_cases:
            if case["patent_type"] == patent_type:
                similarity = self._calculate_similarity(patent_name, case["name"])
                similarities.append((case, similarity))

        if similarities:
            best_match = max(similarities, key=lambda x: x[1])  # type: ignore
            analysis["similarity_score"] = best_match[1]
            analysis["similar_case"] = best_match[0]["name"]

        return analysis

    def _identify_naming_structure(self, name: str) -> str:
        """识别命名结构"""
        if "基于" in name:
            return "based_on_structure"
        elif "一种" in name:
            return "one_of_structure"
        elif "具有" in name:
            return "has_structure"
        else:
            return "simple_structure"

    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """计算名称相似度"""
        # 简单的相似度计算
        common_chars = set(name1) & set(name2)
        total_chars = set(name1) | set(name2)

        if not total_chars:
            return 0.0

        return len(common_chars) / len(total_chars)

    def get_naming_statistics(self) -> dict:
        """获取命名统计信息"""
        return {
            "system_version": self.version,
            "supported_types": [pt.value for pt in PatentType],
            "naming_rules_count": len(self.naming_rules),
            "technical_vocabulary_count": len(self.technical_vocabulary),
            "naming_templates_count": sum(
                len(templates) for templates in self.naming_templates.values()
            ),
            "success_cases_count": len(self.success_cases),
            "professional_scores": self.professional_scores,
        }
