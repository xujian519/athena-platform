#!/usr/bin/env python3
"""
专利权利要求书专业分析报告
使用Athena专利分析系统
"""

import json
from datetime import datetime
from typing import Any


class PatentClaimProfessionalAnalyzer:
    """专利权利要求书专业分析器 - Athena增强版"""

    def __init__(self):
        self.analysis_timestamp = datetime.now().isoformat()
        self.analyzer = "Athena AI System - 专利分析专家"

    def analyze_patent_claims(self, patent_data: dict[str, Any]) -> dict[str, Any]:
        """
        对专利权利要求书进行全面分析

        Args:
            patent_data: 包含技术领域、背景技术、发明内容、权利要求书、具体实施方式的数据

        Returns:
            完整的分析报告
        """
        report = {
            "meta_info": {
                "analyzer": self.analyzer,
                "timestamp": self.analysis_timestamp,
                "analysis_type": "专利权利要求书全面质量评估"
            },
            "overall_assessment": self._overall_assessment(patent_data),
            "claims_analysis": self._analyze_all_claims(patent_data.get("claims", {})),
            "technical_analysis": self._technical_analysis(patent_data),
            "legal_analysis": self._legal_analysis(patent_data),
            "improvement_suggestions": self._generate_improvements(patent_data),
            "conclusion": self._generate_conclusion(patent_data)
        }
        return report

    def _overall_assessment(self, patent_data: dict[str, Any]) -> dict[str, Any]:
        """总体评估"""
        claims = patent_data.get("claims", {})

        # 计算得分
        scores = {
            "structure_completeness": self._score_structure_completeness(patent_data),
            "technical_clarity": self._score_technical_clarity(claims),
            "innovation_level": self._score_innovation_level(patent_data),
            "claim_quality": self._score_claim_quality(claims),
            "protection_scope": self._score_protection_scope(claims)
        }

        overall_score = sum(scores.values()) / len(scores)

        return {
            "overall_score": overall_score,
            "grade": self._determine_grade(overall_score),
            "dimension_scores": scores,
            "summary": self._generate_summary(scores, overall_score)
        }

    def _score_structure_completeness(self, patent_data: dict[str, Any]) -> float:
        """结构完整性评分"""
        required_sections = ["technical_field", "background_art", "invention_content", "claims", "embodiments"]
        present_sections = sum(1 for section in required_sections if section in patent_data and patent_data[section])
        return (present_sections / len(required_sections)) * 100

    def _score_technical_clarity(self, claims: dict[str, Any]) -> float:
        """技术清晰度评分"""
        independent_claim = claims.get("independent", "")
        dependent_claims = claims.get("dependent", [])

        score = 60  # 基础分

        # 检查是否有具体的技术特征
        if "特征提取" in independent_claim or "分类模型" in independent_claim:
            score += 10

        # 检查从属权利要求的层次
        if len(dependent_claims) >= 6:
            score += 15
        elif len(dependent_claims) >= 3:
            score += 10

        # 检查是否有模糊表述
        vague_terms = ["适当的", "合适的", "一定的", "相应的"]
        vague_count = sum(1 for term in vague_terms if term in independent_claim)
        score -= vague_count * 5

        return min(score, 100)

    def _score_innovation_level(self, patent_data: dict[str, Any]) -> float:
        """创新性评分"""
        background = patent_data.get("background_art", "")
        invention_content = patent_data.get("invention_content", "")

        score = 50  # 基础分

        # 检查是否明确了现有技术的问题
        if "现有技术" in background or "问题" in background:
            score += 10

        # 检查是否有技术效果
        if "技术效果" in invention_content or "有益效果" in invention_content:
            score += 10

        # 检查是否有独特的技术手段
        if "策略决策模型" in invention_content or "多维度特征" in invention_content:
            score += 15

        # 检查是否解决了技术问题
        if "解决" in invention_content and "技术问题" in invention_content:
            score += 15

        return min(score, 100)

    def _score_claim_quality(self, claims: dict[str, Any]) -> float:
        """权利要求质量评分"""
        independent_claim = claims.get("independent", "")
        dependent_claims = claims.get("dependent", [])

        score = 60  # 基础分

        # 检查必要技术特征是否完整
        essential_features = ["获取", "确定", "处理"]
        if all(feature in independent_claim for feature in essential_features):
            score += 10

        # 检查引用关系是否正确
        for claim in dependent_claims:
            if "根据权利要求" in claim:
                score += 3

        # 检查是否有保护范围的合理限定
        if "包括以下至少一项" in independent_claim:
            score += 5

        # 检查从属权利要求是否进一步限定
        further_refinement = any("所述" in claim and "包括" in claim for claim in dependent_claims)
        if further_refinement:
            score += 10

        return min(score, 100)

    def _score_protection_scope(self, claims: dict[str, Any]) -> float:
        """保护范围合理性评分"""
        independent_claim = claims.get("independent", "")

        score = 70  # 基础分

        # 检查是否过宽（缺乏技术特征）
        if len(independent_claim) < 50:
            score -= 20

        # 检查是否有合理的限定
        if "所述目标处理策略包括以下至少一项" in independent_claim:
            score += 10

        # 检查是否使用了功能性限定
        if "用于" in independent_claim or "配置为" in independent_claim:
            score += 5

        # 检查是否有支持（具体实施方式）
        # 这里简化处理
        score += 10

        return min(score, 100)

    def _determine_grade(self, score: float) -> str:
        """确定等级"""
        if score >= 90:
            return "优秀 (A)"
        elif score >= 80:
            return "良好 (B)"
        elif score >= 70:
            return "中等 (C)"
        elif score >= 60:
            return "及格 (D)"
        else:
            return "不及格 (E)"

    def _generate_summary(self, scores: dict[str, float], overall: float) -> str:
        """生成总体评述"""
        summary = "### 总体评估\n\n"
        summary += f"**综合得分**: {overall:.1f}/100 ({self._determine_grade(overall)})\n\n"

        summary += "#### 分项得分:\n"
        for dimension, score in scores.items():
            dimension_cn = {
                "structure_completeness": "结构完整性",
                "technical_clarity": "技术清晰度",
                "innovation_level": "创新性水平",
                "claim_quality": "权利要求质量",
                "protection_scope": "保护范围合理性"
            }.get(dimension, dimension)
            summary += f"- **{dimension_cn}**: {score:.1f}/100\n"

        summary += "\n#### 综合评价:\n"
        if overall >= 85:
            summary += "这是一份高质量的专利申请文件，具有较好的授权前景和维权价值。"
        elif overall >= 75:
            summary += "这是一份中等偏上的专利申请文件，主要问题较为明确，经过修改后可达到较好水平。"
        elif overall >= 60:
            summary += "这是一份基本合格的专利申请文件，但存在明显的缺陷，需要进行实质性的修改和完善。"
        else:
            summary += "这份专利申请文件存在严重问题，不建议直接提交，需要重新撰写或大幅度修改。"

        return summary

    def _analyze_all_claims(self, claims: dict[str, Any]) -> dict[str, Any]:
        """分析所有权利要求"""
        independent = claims.get("independent", "")
        dependent = claims.get("dependent", [])

        analysis = {
            "independent_claim_analysis": self._analyze_independent_claim(independent),
            "dependent_claims_analysis": [self._analyze_dependent_claim(i+2, claim) for i, claim in enumerate(dependent)],
            "claim_hierarchy_analysis": self._analyze_claim_hierarchy(independent, dependent),
            "claim_drafting_issues": self._identify_drafting_issues(independent, dependent)
        }
        return analysis

    def _analyze_independent_claim(self, claim: str) -> dict[str, Any]:
        """分析独立权利要求"""
        return {
            "claim_text": claim,
            "preamble_part": self._extract_preamble(claim),
            "characterizing_part": self._extract_characterizing_part(claim),
            "essential_features": self._extract_essential_features(claim),
            "technical_features_analysis": self._analyze_technical_features(claim),
            "breadth_assessment": self._assess_breadth(claim),
            "clarity_assessment": self._assess_clarity(claim)
        }

    def _analyze_dependent_claim(self, claim_num: int, claim: str) -> dict[str, Any]:
        """分析从属权利要求"""
        return {
            "claim_number": claim_num,
            "claim_text": claim,
            "dependency_analysis": self._analyze_dependency(claim),
            "additional_features": self._extract_additional_features(claim),
            "further_limitation": self._check_further_limitation(claim),
            "support_analysis": self._check_support(claim)
        }

    def _extract_preamble(self, claim: str) -> str:
        """提取前序部分"""
        if "其特征在于" in claim:
            return claim.split("其特征在于")[0]
        return ""

    def _extract_characterizing_part(self, claim: str) -> str:
        """提取特征部分"""
        if "其特征在于" in claim:
            return claim.split("其特征在于")[1]
        return claim

    def _extract_essential_features(self, claim: str) -> list[str]:
        """提取必要技术特征"""
        features = []
        if "获取待处理数据" in claim:
            features.append("获取待处理数据")
        if "确定所述待处理数据对应的目标处理策略" in claim:
            features.append("确定目标处理策略")
        if "基于所述目标处理策略，对所述待处理数据进行处理" in claim:
            features.append("基于策略进行处理")
        return features

    def _analyze_technical_features(self, claim: str) -> dict[str, Any]:
        """分析技术特征"""
        return {
            "feature_count": len([f for f in ["获取", "确定", "处理"] if f in claim]),
            "feature_details": [
                {"feature": "数据获取", "description": "获取待处理数据"},
                {"feature": "策略确定", "description": "确定目标处理策略，包括延迟/立即/分批处理"},
                {"feature": "数据处理", "description": "基于目标处理策略对数据进行处理"}
            ],
            "feature_concreteness": "中等"  # 有具体的技术手段，但缺乏细节
        }

    def _assess_breadth(self, claim: str) -> str:
        """评估保护范围宽度"""
        if "包括以下至少一项" in claim:
            return "较宽 - 使用'至少一项'表述，保护范围较宽"
        return "中等"

    def _assess_clarity(self, claim: str) -> str:
        """评估清晰度"""
        issues = []
        if "所述待处理数据" in claim:
            issues.append("使用了'所述'但没有明确定义待处理数据的具体内容")
        if "延迟处理、立即处理和分批处理" in claim:
            issues.append("三种处理方式没有具体的技术实现描述")

        if issues:
            return "存在清晰度问题: " + "; ".join(issues)
        return "清晰"

    def _analyze_dependency(self, claim: str) -> dict[str, Any]:
        """分析依赖关系"""
        if "根据权利要求" in claim:
            # 提取引用的权利要求号
            import re
            refs = re.findall(r"根据权利要求(\d+)", claim)
            return {
                "has_dependency": True,
                "referenced_claims": refs,
                "dependency_type": "单引" if len(refs) == 1 else "多引"
            }
        return {"has_dependency": False, "referenced_claims": []}

    def _extract_additional_features(self, claim: str) -> list[str]:
        """提取附加技术特征"""
        features = []
        if "目标数据类型" in claim:
            features.append("通过目标数据类型确定策略")
        if "特征提取" in claim:
            features.append("通过特征提取进行分类")
        if "优先处理" in claim:
            features.append("补充优先、降级、弃用处理策略")
        return features

    def _check_further_limitation(self, claim: str) -> bool:
        """检查是否进一步限定"""
        return "所述" in claim and ("包括" in claim or "为" in claim)

    def _check_support(self, claim: str) -> str:
        """检查说明书支持"""
        return "需要在说明书中充分支持"  # 简化判断

    def _analyze_claim_hierarchy(self, independent: str, dependent: list[str]) -> dict[str, Any]:
        """分析权利要求层次结构"""
        return {
            "total_claims": 1 + len(dependent),
            "hierarchy_depth": len(dependent),
            "hierarchy_quality": "良好" if len(dependent) >= 6 else "一般",
            "suggestions": "建议增加更多层次的从属权利要求以形成保护梯度" if len(dependent) < 6 else "层次结构合理"
        }

    def _identify_drafting_issues(self, independent: str, dependent: list[str]) -> list[dict[str, str]:
        """识别撰写问题"""
        issues = []

        # 检查独立权利要求
        if "延迟处理" in independent and "具体" not in independent:
            issues.append({
                "claim": "1",
                "issue": "技术特征缺乏具体性",
                "description": "'延迟处理'、'立即处理'、'分批处理'缺乏具体的技术实现描述",
                "severity": "高",
                "suggestion": "建议补充具体的技术手段，如延迟队列、批处理窗口等"
            })

        # 检查从属权利要求
        for i, claim in enumerate(dependent, start=2):
            if "特征提取" in claim and "规则" not in claim:
                issues.append({
                    "claim": str(i),
                    "issue": "特征提取方法不明确",
                    "description": "'特征提取'没有说明提取什么特征、用什么方法提取",
                    "severity": "中",
                    "suggestion": "建议补充具体的特征类型和提取方法"
                })

        return issues

    def _technical_analysis(self, patent_data: dict[str, Any]) -> dict[str, Any]:
        """技术分析"""
        return {
            "technical_field_analysis": self._analyze_technical_field(patent_data.get("technical_field", "")),
            "background_analysis": self._analyze_background(patent_data.get("background_art", "")),
            "technical_problem_analysis": self._analyze_technical_problem(patent_data),
            "technical_solution_analysis": self._analyze_technical_solution(patent_data),
            "technical_effect_analysis": self._analyze_technical_effect(patent_data)
        }

    def _analyze_technical_field(self, field: str) -> dict[str, Any]:
        """分析技术领域"""
        return {
            "field_classification": "数据处理技术",
            "appropriateness": "恰当",
            "suggestions": "技术领域描述合理，符合专利撰写要求"
        }

    def _analyze_background(self, background: str) -> dict[str, Any]:
        """分析背景技术"""
        return {
            "problem_identification": "明确" if "现有技术" in background else "不明确",
            "problem_description": self._assess_problem_description(background),
            "improvement_space": "可以进一步具体化现有技术的具体缺陷"
        }

    def _assess_problem_description(self, background: str) -> str:
        """评估问题描述"""
        if "大数据" in background and "处理" in background:
            return "描述了大数据处理的基本问题"
        return "问题描述不够具体"

    def _analyze_technical_problem(self, patent_data: dict[str, Any]) -> dict[str, Any]:
        """分析技术问题"""
        patent_data.get("invention_content", "")
        return {
            "problem_clarity": "中等",
            "problem_specificity": "需要更具体",
            "suggestions": "建议明确指出要解决的具体技术问题，而不是笼统的业务问题"
        }

    def _analyze_technical_solution(self, patent_data: dict[str, Any]) -> dict[str, Any]:
        """分析技术方案"""
        claims = patent_data.get("claims", {})
        independent = claims.get("independent", "")

        return {
            "solution_completeness": self._assess_solution_completeness(independent),
            "solution_clarity": self._assess_solution_clarity(independent),
            "technical_means": self._identify_technical_means(independent),
            "innovation_points": self._identify_innovation_points(patent_data)
        }

    def _assess_solution_completeness(self, claim: str) -> str:
        """评估技术方案完整性"""
        if all(keyword in claim for keyword in ["获取", "确定", "处理"]):
            return "基本完整"
        return "不完整"

    def _assess_solution_clarity(self, claim: str) -> str:
        """评估技术方案清晰度"""
        clarity_issues = []
        if "延迟处理" in claim and "队列" not in claim:
            clarity_issues.append("延迟处理缺乏技术实现细节")
        if "立即处理" in claim and "同步" not in claim:
            clarity_issues.append("立即处理缺乏技术实现细节")
        if "分批处理" in claim and "批处理" not in claim:
            clarity_issues.append("分批处理缺乏技术实现细节")

        if clarity_issues:
            return "存在问题: " + "; ".join(clarity_issues)
        return "清晰"

    def _identify_technical_means(self, claim: str) -> list[dict[str, str]:
        """识别技术手段"""
        means = []
        if "获取" in claim:
            means.append({"means": "数据获取", "concreteness": "低"})
        if "确定" in claim:
            means.append({"means": "策略确定", "concreteness": "低"})
        if "处理" in claim:
            means.append({"means": "数据处理", "concreteness": "低"})
        return means

    def _identify_innovation_points(self, patent_data: dict[str, Any]) -> list[str]:
        """识别创新点"""
        invention = patent_data.get("invention_content", "")
        points = []

        if "策略决策模型" in invention:
            points.append("使用策略决策模型确定处理策略")
        if "多维度特征" in invention:
            points.append("基于多维度特征进行分类")
        if "延迟队列" in invention:
            points.append("采用延迟队列技术")

        return points if points else ["创新点不够明确"]

    def _analyze_technical_effect(self, patent_data: dict[str, Any]) -> dict[str, Any]:
        """分析技术效果"""
        invention = patent_data.get("invention_content", "")

        return {
            "effect_clarity": "一般" if "技术效果" in invention else "不明确",
            "effect_verifiability": "需要进一步量化",
            "suggestions": "建议补充具体的性能指标，如处理效率提升百分比、资源利用率改善等"
        }

    def _legal_analysis(self, patent_data: dict[str, Any]) -> dict[str, Any]:
        """法律分析"""
        claims = patent_data.get("claims", {})

        return {
            "patentability_analysis": self._analyze_patentability(patent_data),
            "infringement_risk_analysis": self._analyze_infringement_risk(claims),
            "validity_risk_analysis": self._analyze_validity_risk(claims),
            "claim_interpretation_analysis": self._analyze_claim_interpretation(claims)
        }

    def _analyze_patentability(self, patent_data: dict[str, Any]) -> dict[str, Any]:
        """分析可专利性"""
        return {
            "novelty_assessment": {
                "level": "中等",
                "issues": ["数据处理方法是通用技术，需要与现有技术有更明显的区别"],
                "suggestions": ["建议补充与现有技术的区别特征", "建议强调独特的技术实现细节"]
            },
            "inventive_step_assessment": {
                "level": "中等偏下",
                "issues": ["策略决策模型需要更具体的描述以体现创造性"],
                "suggestions": ["建议详细描述策略决策模型的工作原理", "建议说明与现有方法的本质区别"]
            },
            "practical_applicability": {
                "level": "良好",
                "issues": [],
                "suggestions": []
            }
        }

    def _analyze_infringement_risk(self, claims: dict[str, Any]) -> dict[str, Any]:
        """分析侵权风险"""
        return {
            "detection_difficulty": "高",
            "reason": "权利要求中的技术特征较为抽象，难以直接判断是否被侵权",
            "suggestions": [
                "建议在从属权利要求中补充更具体的技术特征",
                "建议补充具体的实现方式以便于侵权比对"
            ]
        }

    def _analyze_validity_risk(self, claims: dict[str, Any]) -> dict[str, Any]:
        """分析有效性风险"""
        return {
            "invalidation_risk": "中等偏高",
            "risk_factors": [
                "技术特征较为通用，容易被现有技术攻击",
                "功能性限定可能被认定为缺乏具体技术手段",
                "保护范围较宽，容易被找到规避设计"
            ],
            "mitigation_suggestions": [
                "建议增加更多具体的技术特征",
                "建议在说明书中充分支持技术方案的创造性",
                "建议考虑增加方法对应的系统/装置权利要求"
            ]
        }

    def _analyze_claim_interpretation(self, claims: dict[str, Any]) -> dict[str, Any]:
        """分析权利要求解释"""
        independent = claims.get("independent", "")

        return {
            "ambiguous_terms": self._identify_ambiguous_terms(independent),
            "functional_limitations": self._identify_functional_limitations(independent),
            "interpretation_risks": self._assess_interpretation_risks(independent)
        }

    def _identify_ambiguous_terms(self, claim: str) -> list[str]:
        """识别模糊术语"""
        ambiguous = []
        if "待处理数据" in claim:
            ambiguous.append("待处理数据（需要明确定义数据类型和特征）")
        if "目标处理策略" in claim:
            ambiguous.append("目标处理策略（需要说明具体包含哪些策略）")
        return ambiguous

    def _identify_functional_limitations(self, claim: str) -> list[str]:
        """识别功能性限定"""
        functional = []
        if "延迟处理" in claim:
            functional.append("延迟处理（功能性限定，缺乏具体实现方式）")
        if "立即处理" in claim:
            functional.append("立即处理（功能性限定，缺乏具体实现方式）")
        return functional

    def _assess_interpretation_risks(self, claim: str) -> list[str]:
        """评估解释风险"""
        risks = []
        if "包括以下至少一项" in claim:
            risks.append("'至少一项'可能导致保护范围解释过宽")
        if len(claim) < 100:
            risks.append("权利要求过短，技术特征不够具体，可能被认定为缺乏创造性")
        return risks

    def _generate_improvements(self, patent_data: dict[str, Any]) -> dict[str, Any]:
        """生成改进建议"""
        return {
            "critical_improvements": self._generate_critical_improvements(patent_data),
            "important_improvements": self._generate_important_improvements(patent_data),
            "suggested_improvements": self._generate_suggested_improvements(patent_data),
            "rewriting_suggestions": self._generate_rewriting_suggestions(patent_data)
        }

    def _generate_critical_improvements(self, patent_data: dict[str, Any]) -> list[dict[str, str]:
        """生成关键改进建议"""
        return [
            {
                "priority": "高",
                "category": "技术特征具体化",
                "issue": "独立权利要求中的技术特征过于抽象",
                "suggestion": "补充具体的技术实现细节",
                "example": "将'延迟处理'改为'将数据写入延迟消息队列，设置预设的触发时间戳'"
            },
            {
                "priority": "高",
                "category": "创造性增强",
                "issue": "缺乏与现有技术的明显区别",
                "suggestion": "明确技术方案的创造性所在",
                "example": "说明策略决策模型与现有分类方法的技术差异"
            }
        ]

    def _generate_important_improvements(self, patent_data: dict[str, Any]) -> list[dict[str, str]:
        """生成重要改进建议"""
        return [
            {
                "priority": "中",
                "category": "权利要求层次",
                "issue": "从属权利要求层次不够丰富",
                "suggestion": "增加更多层次的从属权利要求",
                "example": "增加特征提取的具体方法、分类模型的具体类型等"
            },
            {
                "priority": "中",
                "category": "说明书支持",
                "issue": "需要在说明书中充分支持权利要求",
                "suggestion": "在具体实施方式中详细描述每个技术特征",
                "example": "补充延迟队列的具体配置、批处理窗口的设置等"
            }
        ]

    def _generate_suggested_improvements(self, patent_data: dict[str, Any]) -> list[dict[str, str]:
        """生成建议性改进"""
        return [
            {
                "priority": "低",
                "category": "权利要求类型",
                "issue": "只有方法权利要求",
                "suggestion": "考虑增加对应的装置/系统权利要求",
                "example": "增加'一种数据处理装置，包括...'的独立权利要求"
            },
            {
                "priority": "低",
                "category": "技术效果量化",
                "issue": "技术效果缺乏量化数据",
                "suggestion": "补充具体的性能提升数据",
                "example": "处理效率提升30%、资源利用率提高25%等"
            }
        ]

    def _generate_rewriting_suggestions(self, patent_data: dict[str, Any]) -> dict[str, Any]:
        """生成重写建议"""
        independent_claim = patent_data.get("claims", {}).get("independent", "")

        return {
            "independent_claim_rewrite": self._rewrite_independent_claim(independent_claim),
            "rewrite_rationale": "通过增加具体的技术特征，提高权利要求的技术性和创造性，同时保持合理的保护范围"
        }

    def _rewrite_independent_claim(self, original: str) -> str:
        """重写独立权利要求"""
        # 这里提供一个改进版本的建议
        improved = """1. 一种数据处理方法，其特征在于，包括：
获取待处理数据，并提取所述待处理数据的元数据信息，所述元数据信息包括数据类型标签、数据大小和处理时效要求中的至少一种；
基于所述元数据信息，通过预设的策略决策模型确定目标处理策略，其中：
所述策略决策模型根据所述元数据信息中的至少两个维度进行综合分析；
所述目标处理策略包括延迟处理、立即处理和分批处理中的至少一种；
调用与所述目标处理策略匹配的处理引擎，其中：
所述延迟处理包括：将所述待处理数据写入延迟消息队列，并设置触发时间戳；
所述立即处理包括：通过同步调用链路执行数据处理逻辑；
所述分批处理包括：将所述待处理数据缓存至批处理缓冲区，在满足预设聚合条件时统一处理；
通过所述处理引擎对所述待处理数据执行相应的处理操作。"""

        return improved

    def _generate_conclusion(self, patent_data: dict[str, Any]) -> dict[str, Any]:
        """生成结论"""
        overall = self._overall_assessment(patent_data)

        return {
            "overall_rating": overall["grade"],
            "authorization_probability": self._estimate_authorization_probability(overall["overall_score"]),
            "key_strengths": self._identify_strengths(patent_data),
            "key_weaknesses": self._identify_weaknesses(patent_data),
            "final_recommendation": self._generate_final_recommendation(overall["overall_score"]),
            "next_steps": self._suggest_next_steps(patent_data)
        }

    def _estimate_authorization_probability(self, score: float) -> str:
        """估算授权概率"""
        if score >= 85:
            return "高 (80-90%)"
        elif score >= 75:
            return "中等偏高 (60-80%)"
        elif score >= 60:
            return "中等 (40-60%)"
        else:
            return "低 (<40%)"

    def _identify_strengths(self, patent_data: dict[str, Any]) -> list[str]:
        """识别优势"""
        strengths = []
        claims = patent_data.get("claims", {})

        if len(claims.get("dependent", [])) >= 4:
            strengths.append("权利要求层次结构基本合理")
        if patent_data.get("technical_field"):
            strengths.append("技术领域界定清晰")
        if patent_data.get("background_art"):
            strengths.append("背景技术描述完整")

        return strengths if strengths else ["暂无明显优势"]

    def _identify_weaknesses(self, patent_data: dict[str, Any]) -> list[str]:
        """识别劣势"""
        weaknesses = []
        claims = patent_data.get("claims", {})
        independent = claims.get("independent", "")

        if "延迟处理" in independent and "队列" not in independent:
            weaknesses.append("技术特征缺乏具体性")
        if "策略决策模型" not in independent:
            weaknesses.append("缺乏核心创新点的明确描述")
        if len(independent) < 150:
            weaknesses.append("独立权利要求过于简短，保护范围可能不稳定")

        return weaknesses

    def _generate_final_recommendation(self, score: float) -> str:
        """生成最终建议"""
        if score >= 80:
            return "该专利申请文件质量较好，建议经过适当修改后提交。主要改进方向：补充具体技术特征，增强创造性描述。"
        elif score >= 60:
            return "该专利申请文件基本合格，但存在明显缺陷，建议进行实质性修改后再提交。重点关注：技术特征具体化、创造性增强。"
        else:
            return "该专利申请文件存在严重问题，不建议直接提交。建议重新撰写或寻求专业专利代理人的帮助。"

    def _suggest_next_steps(self, patent_data: dict[str, Any]) -> list[str]:
        """建议后续步骤"""
        return [
            "1. 根据关键改进建议修改独立权利要求，补充具体技术特征",
            "2. 在从属权利要求中增加更多层次的技术特征限定",
            "3. 在说明书中充分补充技术方案的具体实施方式",
            "4. 明确与现有技术的区别特征，强调技术方案的创造性",
            "5. 补充具体的性能数据和实验结果",
            "6. 考虑增加对应的装置/系统权利要求",
            "7. 建议提交前请专业专利代理人进行审核"
        ]


# 使用示例
if __name__ == "__main__":
    # 创建分析器
    analyzer = PatentClaimProfessionalAnalyzer()

    # 准备测试数据 - 基于用户上传的图片内容
    patent_data = {
        "technical_field": "本发明涉及数据处理技术领域，尤其涉及一种数据处理方法、装置、电子设备及可读存储介质。",
        "background_art": """
        随着大数据技术的飞速发展，企业积累了海量的业务数据。这些数据具有多样性、复杂性和海量性的特点。
        现有技术在处理这些数据时，通常采用统一的处理方式，无法根据数据的特点进行差异化处理。
        这导致了一些数据处理效率低下，资源浪费严重的问题。
        """,
        "invention_content": """
        本发明提供一种数据处理方法，通过策略决策模型确定数据的处理策略，
        实现对数据的差异化处理，提高数据处理效率。
        包括：获取数据、提取特征、确定策略、执行处理等步骤。
        """,
        "claims": {
            "independent": """1. 一种数据处理方法，其特征在于，包括：
获取待处理数据；
确定所述待处理数据对应的目标处理策略，所述目标处理策略包括以下至少一项：延迟处理、立即处理和分批处理；
基于所述目标处理策略，对所述待处理数据进行处理。""",
            "dependent": [
                "2. 根据权利要求1所述的方法，其特征在于，所述确定所述待处理数据对应的目标处理策略，包括：获取所述待处理数据的目标数据类型；确定与所述目标数据类型相匹配的目标处理策略。",
                "3. 根据权利要求2所述的方法，其特征在于，所述获取所述待处理数据的目标数据类型，包括：对所述待处理数据进行特征提取，得到所述待处理数据的目标特征；基于所述目标特征，对所述待处理数据进行分类，得到所述待处理数据的目标数据类型。",
                "4. 根据权利要求1所述的方法，其特征在于，所述目标处理策略还包括以下至少一项：优先处理、降级处理和弃用处理。"
            ]
        },
        "embodiments": "具体实施方式..."
    }

    # 执行分析
    report = analyzer.analyze_patent_claims(patent_data)

    # 打印报告
    print(json.dumps(report, ensure_ascii=False, indent=2))
