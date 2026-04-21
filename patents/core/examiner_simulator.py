#!/usr/bin/env python3
from __future__ import annotations
"""
审查员模拟器
Examiner Simulator

模拟审查员的思维过程和反驳逻辑，支持多轮论证对话

Author: Athena平台团队
Created: 2026-01-26
Version: v1.0.0
"""

import logging
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class RejectionType(Enum):
    """驳回类型"""
    INVENTIVENESS = "inventiveness"          # 创造性
    OBVIOUSNESS = "obviousness"              # 显而易见性
    LACK_OF_NOVELTY = "lack_of_novelty"      # 缺乏新颖性
    INSUFFICIENT_DISCLOSURE = "insufficient_disclosure"  # 公开不充分
    UNPATENTABLE_SUBJECT = "unpatentable_subject"  # 不属于专利保护客体


class ArgumentationStrategy(Enum):
    """论证策略"""
    STRICT_LITERAL = "strict_literal"        # 严格字面解释
    BROAD_INTERPRETATION = "broad_interpretation"  # 宽泛解释
    COMBINATION_ANALYSIS = "combination_analysis"  # 组合分析
    HINDSIGHT_BIAS = "hindsight_bias"        # 事后诸葛亮


class ExaminerSimulator:
    """
    审查员模拟器

    功能：
    1. 模拟审查员基于对比文件的反驳逻辑
    2. 提供多轮论证对话能力
    3. 支持不同类型的审查意见
    4. 动态调整论证策略
    """

    # 审查员常用质疑模板
    OBJECTION_TEMPLATES = {
        RejectionType.INVENTIVENESS: [
            "对比文件{d}已经公开了{feature}，本领域技术人员根据其教导，容易想到将其应用于本案。",
            "{feature}属于本领域的常规技术手段，无需创造性劳动即可获得。",
            "对比文件{d1}给出了{feature1}的技术启示，结合对比文件{d2}的{feature2}，得到本申请权利要求的技术方案是显而易见的。",
        ],
        RejectionType.OBVIOUSNESS: [
            "权利要求{claim}的技术方案是对比文件{d}与公知常识的简单组合。",
            "在对比文件{d}的基础上，本领域技术人员结合其掌握的公知常识，无需创造性劳动就能得到权利要求{claim}的技术方案。",
        ],
        RejectionType.LACK_OF_NOVELTY: [
            "对比文件{d}已经公开了权利要求{claim}的全部技术特征，因此该权利要求不具备新颖性。",
        ],
    }

    # 审查员论证策略
    ARGUMENTATION_PATTERNS = {
        "feature_matching": {
            "name": "特征逐一对比",
            "template": "对比文件{d}明确公开了{feature}（参见第{page}页第{line}行），"
        },
        "combination_analysis": {
            "name": "组合对比分析",
            "template": "对比文件{d1}公开了{feature1}，对比文件{d2}公开了{feature2}，"
                       "本领域技术人员有动机将两者结合。",
        },
        "obvious_variation": {
            "name": "显而易见变型",
            "template": "{feature}与对比文件{d}记载的{similar_feature}仅是{difference}，"
                       "这种变型对本领域技术人员来说是显而易见的。",
        },
        "common_general_knowledge": {
            "name": "公知常识论证",
            "template": "{feature}属于本领域的公知常识，本领域技术人员无需创造性劳动即可采用。",
        },
    }

    def __init__(self):
        """初始化审查员模拟器"""
        self.rejection_type = RejectionType.INVENTIVENESS
        self.current_strategy = ArgumentationStrategy.STRICT_LITERAL
        self.dialogue_history = []
        self.concession_made = 0  # 已让步次数
        self.tone_level = "strict"  # strict, moderate, flexible

        logger.info("✅ 审查员模拟器初始化完成")

    def simulate_initial_review(
        self,
        oa_text: str,
        claims: list[str],
        prior_art_analysis: dict
    ) -> dict[str, Any]:
        """
        模拟初次审查意见

        Args:
            oa_text: 审查意见全文
            claims: 权利要求列表
            prior_art_analysis: 对比文件分析结果

        Returns:
            初次审查意见模拟结果
        """
        logger.info("📋 模拟审查员初次审查意见")

        # 提取驳回类型
        self.rejection_type = self._detect_rejection_type(oa_text)

        # 选择论证策略
        self.current_strategy = self._select_strategy(
            claims=claims,
            prior_art_analysis=prior_art_analysis
        )

        # 生成初步质疑
        initial_objections = []

        for i, claim in enumerate(claims, 1):
            # 为每个权利要求生成质疑
            objection = self._generate_claim_objection(
                claim_number=i,
                claim_text=claim,
                prior_art_analysis=prior_art_analysis
            )
            initial_objections.append(objection)

        result = {
            "rejection_type": self.rejection_type.value,
            "strategy": self.current_strategy.value,
            "objections": initial_objections,
            "overall_conclusion": self._generate_overall_conclusion(
                rejection_type=self.rejection_type,
                objections=initial_objections
            )
        }

        # 记录对话历史
        self.dialogue_history.append({
            "role": "examiner",
            "type": "initial_review",
            "content": result
        })

        logger.info(f"✅ 初次审查意见模拟完成: {len(initial_objections)}个质疑")

        return result

    def respond_to_applicant_argument(
        self,
        applicant_argument: str,
        prior_art_analysis: dict,
        round_number: int = 1
    ) -> dict[str, Any]:
        """
        模拟审查员对申请人答复的回应

        Args:
            applicant_argument: 申请人的答复意见
            prior_art_analysis: 对比文件分析结果
            round_number: 对话轮次

        Returns:
            审查员的回应
        """
        logger.info(f"💬 模拟审查员第{round_number}轮回应")

        # 分析申请人答复的策略和论据
        argument_analysis = self._analyze_applicant_argument(applicant_argument)

        # 确定审查员的回应策略
        response_strategy = self._determine_response_strategy(
            argument_analysis=argument_analysis,
            round_number=round_number
        )

        # 生成具体反驳
        rebuttal = self._generate_rebuttal(
            applicant_argument=applicant_argument,
            argument_analysis=argument_analysis,
            prior_art_analysis=prior_art_analysis,
            strategy=response_strategy
        )

        result = {
            "round_number": round_number,
            "response_strategy": response_strategy,
            "rebuttal": rebuttal,
            "applicant_points_addressed": argument_analysis.get("key_points", []),
            "remaining_concerns": rebuttal.get("remaining_concerns", []),
            "suggestions_for_improvement": rebuttal.get("suggestions", [])
        }

        # 记录对话历史
        self.dialogue_history.append({
            "role": "examiner",
            "type": "response",
            "round": round_number,
            "content": result
        })

        logger.info(f"✅ 第{round_number}轮回应完成")

        return result

    def evaluate_final_response(
        self,
        applicant_response: str,
        dialogue_history: list[dict]
    ) -> dict[str, Any]:
        """
        评估申请人最终答复的质量

        Args:
            applicant_response: 申请人的最终答复
            dialogue_history: 完整对话历史

        Returns:
            评估结果
        """
        logger.info("📊 评估申请人最终答复质量")

        # 评估维度
        completeness_score = self._evaluate_completeness(applicant_response)
        persuasiveness_score = self._evaluate_persuasiveness(applicant_response)
        technical_depth_score = self._evaluate_technical_depth(applicant_response)
        logic_consistency_score = self._evaluate_logic_consistency(applicant_response)

        overall_score = (
            completeness_score * 0.25 +
            persuasiveness_score * 0.30 +
            technical_depth_score * 0.25 +
            logic_consistency_score * 0.20
        )

        # 生成评估意见
        evaluation = {
            "overall_score": overall_score,
            "scores": {
                "completeness": completeness_score,
                "persuasiveness": persuasiveness_score,
                "technical_depth": technical_depth_score,
                "logic_consistency": logic_consistency_score
            },
            "strengths": self._identify_strengths(applicant_response),
            "weaknesses": self._identify_weaknesses(applicant_response),
            "recommendations": self._generate_recommendations(overall_score),
            "predicted_outcome": self._predict_outcome(overall_score)
        }

        logger.info(f"✅ 评估完成: 总分 {overall_score:.2f}/100")

        return evaluation

    def _detect_rejection_type(self, oa_text: str) -> RejectionType:
        """检测驳回类型"""
        oa_text.lower()

        # 优先级顺序检测
        keywords = {
            RejectionType.INVENTIVENESS: ["创造性", "专利法第22条第3款", "突出的实质性特点", "显著进步"],
            RejectionType.OBVIOUSNESS: ["显而易见", "显而易见性", "本领域技术人员容易想到"],
            RejectionType.LACK_OF_NOVELTY: ["新颖性", "专利法第22条第2款", "相同", "完全公开"],
            RejectionType.INSUFFICIENT_DISCLOSURE: ["公开不充分", "无法实现", "说明书未清楚记载"],
            RejectionType.UNPATENTABLE_SUBJECT: ["智力活动规则", "疾病诊断方法", "不属于专利保护客体"],
        }

        for rejection_type, patterns in keywords.items():
            if any(pattern in oa_text for pattern in patterns):
                return rejection_type

        # 默认返回创造性
        return RejectionType.INVENTIVENESS

    def _select_strategy(
        self,
        claims: list[str],
        prior_art_analysis: dict
    ) -> ArgumentationStrategy:
        """选择论证策略"""
        # 基于对比文件数量和权利要求数量选择策略
        prior_art_count = len([k for k in prior_art_analysis.keys() if k.startswith("d")])

        if prior_art_count == 1:
            return ArgumentationStrategy.STRICT_LITERAL
        elif prior_art_count >= 3:
            return ArgumentationStrategy.COMBINATION_ANALYSIS
        else:
            return ArgumentationStrategy.BROAD_INTERPRETATION

    def _generate_claim_objection(
        self,
        claim_number: int,
        claim_text: str,
        prior_art_analysis: dict
    ) -> dict[str, Any]:
        """为特定权利要求生成质疑"""
        # 提取权利要求中的技术特征
        features = self._extract_features_from_claim(claim_text)

        # 为每个特征生成质疑
        feature_objections = []

        for feature in features:
            # 检查是否在对比文件中公开
            is_disclosed, disclosure_info = self._check_disclosure(
                feature=feature,
                prior_art_analysis=prior_art_analysis
            )

            if is_disclosed:
                # 如果已公开，生成对比质疑
                objection = self._generate_disclosure_objection(
                    feature=feature,
                    disclosure_info=disclosure_info
                )
            else:
                # 如果未公开，生成显而易见性质疑
                objection = self._generate_obviousness_objection(
                    feature=feature,
                    prior_art_analysis=prior_art_analysis
                )

            feature_objections.append(objection)

        return {
            "claim_number": claim_number,
            "claim_text": claim_text[:100] + "..." if len(claim_text) > 100 else claim_text,
            "feature_objections": feature_objections,
            "conclusion": self._generate_claim_conclusion(feature_objections)
        }

    def _generate_disclosure_objection(
        self,
        feature: str,
        disclosure_info: dict
    ) -> str:
        """生成公开性质疑"""
        # 只使用第一个模板（最简单的一个，只有{d}和{feature}占位符）
        template = self.OBJECTION_TEMPLATES[RejectionType.INVENTIVENESS][0]
        prior_art_ref = disclosure_info.get("prior_art", "D1")

        return template.format(
            d=prior_art_ref,
            feature=feature
        )

    def _generate_obviousness_objection(
        self,
        feature: str,
        prior_art_analysis: dict
    ) -> str:
        """生成显而易见性质疑"""
        # 查找最相似的特征
        similar_feature = self._find_most_similar_feature(
            feature=feature,
            prior_art_analysis=prior_art_analysis
        )

        if similar_feature:
            return f"对于{feature}，本领域技术人员基于对比文件公开的{similar_feature}，" \
                   f"结合本领域的常规技术手段，无需创造性劳动即可得到。"
        else:
            return f"{feature}属于本领域的公知常识或常规技术手段。"

    def _extract_features_from_claim(self, claim_text: str) -> list[str]:
        """从权利要求中提取技术特征"""
        import re

        # 按照标点符号分割
        parts = re.split(r'[，。；；,;\n]', claim_text)

        features = []
        for part in parts:
            part = part.strip()
            # 移除序号前缀
            part = re.sub(r'^[一二三四五六七八九十\d]+[、.．]', '', part)
            # 过滤长度
            if 10 < len(part) < 100:
                features.append(part)

        return features[:5]  # 最多5个特征

    def _check_disclosure(
        self,
        feature: str,
        prior_art_analysis: dict
    ) -> tuple[bool, dict | None]:
        """检查特征是否在对比文件中公开"""
        # 简化实现：检查undisclosed_features列表
        for key, value in prior_art_analysis.items():
            if key.startswith("d"):
                undisclosed = value.get("undisclosed_features", [])

                # 如果特征不在未公开列表中，认为已公开
                if not any(feature[:30] in u[:30] for u in undisclosed):
                    return True, {
                        "prior_art": key.upper(),
                        "disclosed": True
                    }

        return False, None

    def _find_most_similar_feature(
        self,
        feature: str,
        prior_art_analysis: dict
    ) -> str | None:
        """查找最相似的特征"""
        from difflib import SequenceMatcher

        best_match = None
        best_similarity = 0.0

        for key, value in prior_art_analysis.items():
            if key.startswith("d"):
                # 从实施方式中查找相似内容
                implementation = value.get("implementation", "")

                similarity = SequenceMatcher(None, feature, implementation).ratio()

                if similarity > best_similarity and similarity > 0.3:
                    best_similarity = similarity
                    best_match = implementation[:50]

        return best_match

    def _generate_claim_conclusion(self, feature_objections: list[str]) -> str:
        """生成权利要求结论"""
        if len(feature_objections) >= 3:
            return "因此，权利要求的技术方案不具备突出的实质性特点和显著的进步，不具备创造性。"
        else:
            return "权利要求的上述技术特征被对比文件公开或属于本领域的常规技术手段。"

    def _generate_overall_conclusion(
        self,
        rejection_type: RejectionType,
        objections: list[dict]
    ) -> str:
        """生成总体结论"""
        if rejection_type == RejectionType.INVENTIVENESS:
            return "综上所述，本申请权利要求不具备专利法第22条第3款规定的创造性。"
        elif rejection_type == RejectionType.OBVIOUSNESS:
            return "综上所述，本申请权利要求的技术方案对本领域技术人员来说是显而易见的。"
        elif rejection_type == RejectionType.LACK_OF_NOVELTY:
            return "综上所述，本申请权利要求不具备专利法第22条第2款规定的新颖性。"
        else:
            return "综上所述，本申请存在上述驳回问题。"

    def _analyze_applicant_argument(self, argument: str) -> dict[str, Any]:
        """分析申请人答复的策略和论据"""
        # 提取关键论点
        key_points = []

        # 检测论证策略
        if "四要素" in argument or "协同" in argument:
            key_points.append("四要素协同效应")
        if "预料不到" in argument or "意想不到" in argument:
            key_points.append("预料不到的技术效果")
        if "对比文件" in argument and "未公开" in argument:
            key_points.append("对比文件未公开")
        if "商业成功" in argument:
            key_points.append("商业成功")

        # 检测技术深度
        technical_keywords = ["参数", "工艺", "方法", "机理", "原理"]
        technical_depth = sum(1 for kw in technical_keywords if kw in argument)

        return {
            "key_points": key_points,
            "technical_depth": technical_depth,
            "argument_length": len(argument),
            "citation_count": argument.count("参见") + argument.count("如")
        }

    def _determine_response_strategy(
        self,
        argument_analysis: dict,
        round_number: int
    ) -> str:
        """确定审查员的回应策略"""
        if round_number == 1:
            # 第一轮：严格态度
            return "strict"
        elif round_number == 2:
            # 第二轮：根据技术深度调整
            if argument_analysis["technical_depth"] >= 3:
                return "moderate"
            else:
                return "strict"
        else:
            # 第三轮及以后：更灵活
            return "flexible"

    def _generate_rebuttal(
        self,
        applicant_argument: str,
        argument_analysis: dict,
        prior_art_analysis: dict,
        strategy: str
    ) -> dict[str, Any]:
        """生成具体反驳"""
        rebuttal_points = []

        # 基于申请人论点生成反驳
        for point in argument_analysis["key_points"]:
            if point == "四要素协同效应":
                rebuttal_points.append(
                    "关于四要素协同效应：虽然申请人强调了协同效应，"
                    "但对比文件已经公开了各要素的单独作用，"
                    "本领域技术人员有动机尝试组合使用，"
                    "且协同效果的实现无需创造性劳动。"
                )
            elif point == "预料不到的技术效果":
                rebuttal_points.append(
                    "关于预料不到的技术效果：申请人未提供足够的实验数据证明"
                    "所述技术效果是预料不到的，且所述效果可以通过"
                    "对比文件教导的常规优化得到。"
                )
            elif point == "对比文件未公开":
                rebuttal_points.append(
                    "关于对比文件未公开：申请人声称的未公开特征，"
                    "实际上在对比文件中已有明确教导或属于本领域的公知常识。"
                )

        # 生成剩余关注点
        remaining_concerns = []
        if strategy == "strict":
            remaining_concerns = [
                "权利要求的技术方案与对比文件相比差异不明显",
                "技术效果的论述缺乏充分的实验数据支持",
                "未充分说明为何所述技术方案是非显而易见的"
            ]
        elif strategy == "moderate":
            remaining_concerns = [
                "需要进一步补充实验数据证明技术效果的显著性"
            ]
        elif strategy == "flexible":
            remaining_concerns = []

        # 生成改进建议
        suggestions = []
        if strategy in ["moderate", "flexible"]:
            suggestions = [
                "建议补充对比实验数据，证明技术效果的显著性",
                "建议详细说明各要素之间的协同机理"
            ]

        return {
            "rebuttal_points": rebuttal_points,
            "remaining_concerns": remaining_concerns,
            "suggestions": suggestions,
            "tone": strategy
        }

    def _evaluate_completeness(self, response: str) -> float:
        """评估完整性"""
        required_elements = [
            "权利要求分析",
            "对比文件对比",
            "技术效果论述",
            "法律依据引用"
        ]

        score = 0.0
        for element in required_elements:
            # 简化检查：是否包含相关关键词
            if any(keyword in response for keyword in [element, element.replace("分析", ""), element.replace("论述", "")]):
                score += 25.0

        return score

    def _evaluate_persuasiveness(self, response: str) -> float:
        """评估说服力"""
        # 检查论证元素

        score = 0.0

        # 数据支撑
        if any(kw in response for kw in ["实验数据", "对比试验", "参数", "效果显著"]):
            score += 25

        # 逻辑清晰
        if response.count("因此") + response.count("综上") >= 2:
            score += 25

        # 案例引用
        if "对比文件" in response and "参见" in response:
            score += 20

        # 法理结合
        if "专利法" in response and ("技术" in response or "效果" in response):
            score += 30

        return min(score, 100.0)

    def _evaluate_technical_depth(self, response: str) -> float:
        """评估技术深度"""
        technical_keywords = [
            "机理", "原理", "参数", "工艺", "方法",
            "协同", "优化", "效果", "性能", "实验"
        ]

        keyword_count = sum(1 for kw in technical_keywords if kw in response)

        # 基础分：技术关键词数量
        score = min(keyword_count * 10, 70)

        # 加分：有具体参数
        if any(kw in response for kw in ["℃", "%", "g/mL", "h", "min"]):
            score += 15

        # 加分：有机理分析
        if "机理" in response or "原理" in response:
            score += 15

        return min(score, 100.0)

    def _evaluate_logic_consistency(self, response: str) -> float:
        """评估逻辑一致性"""
        score = 0.0

        # 检查是否有明确的论证结构
        if response.count("首先") + response.count("其一") >= 1:
            score += 20
        if response.count("其次") + response.count("其二") >= 1:
            score += 20
        if response.count("最后") + response.count("综上") + response.count("因此") >= 1:
            score += 20

        # 检查是否有因果逻辑
        if "因此" in response and ("所以" in response or "从而" in response):
            score += 20

        # 检查是否有引用支撑
        if "参见" in response or "如" in response:
            score += 20

        return min(score, 100.0)

    def _identify_strengths(self, response: str) -> list[str]:
        """识别优势"""
        strengths = []

        if "实验数据" in response or "对比试验" in response:
            strengths.append("提供了充分的实验数据支撑")
        if "机理" in response or "原理" in response:
            strengths.append("深入分析了技术机理")
        if "专利法" in response:
            strengths.append("正确引用了法律条款")
        if "对比文件" in response and "未公开" in response:
            strengths.append("详细对比了与对比文件的差异")

        return strengths if strengths else ["答复结构完整"]

    def _identify_weaknesses(self, response: str) -> list[str]:
        """识别不足"""
        weaknesses = []

        if "实验数据" not in response and "对比试验" not in response:
            weaknesses.append("缺乏充分的实验数据支撑")
        if "机理" not in response and "原理" not in response:
            weaknesses.append("技术机理分析不够深入")
        if response.count("对比文件") < 2:
            weaknesses.append("与对比文件的对比不够详细")
        if "专利法" not in response:
            weaknesses.append("未引用法律条款")

        return weaknesses if weaknesses else ["无明显不足"]

    def _generate_recommendations(self, score: float) -> list[str]:
        """生成改进建议"""
        if score >= 85:
            return [
                "答复质量优秀，可以提交",
                "建议保持当前论证深度"
            ]
        elif score >= 70:
            return [
                "答复质量良好，可考虑进一步优化",
                "建议补充更多实验数据",
                "建议加强技术机理分析"
            ]
        else:
            return [
                "答复质量需要改进",
                "必须补充充分的实验数据",
                "必须详细对比与对比文件的差异",
                "必须引用相关法律条款",
                "建议重新组织论证结构"
            ]

    def _predict_outcome(self, score: float) -> str:
        """预测审查结果"""
        if score >= 85:
            return "很有可能获得授权（成功率85%+）"
        elif score >= 70:
            return "有望获得授权（成功率60-85%）"
        elif score >= 50:
            return "存在授权可能（成功率40-60%）"
        else:
            return "授权可能性较低（成功率<40%）"


# 便捷函数
def get_examiner_simulator() -> ExaminerSimulator:
    """获取审查员模拟器单例"""
    return ExaminerSimulator()


# 测试代码
if __name__ == "__main__":
    # 测试审查员模拟器
    simulator = get_examiner_simulator()

    # 模拟初次审查
    oa_text = "根据专利法第22条第3款的规定，权利要求1不具备创造性。"
    claims = [
        "1. 一种吊水净化处理罗非鱼泥腥味的方法，包括盐水处理步骤，水温15-25℃，盐度1-2%，在盐水中添加0.1%高稳维生素C和100g/m³活性炭。",
    ]
    prior_art_analysis = {
        "d1": {
            "undisclosed_features": ["盐水处理", "活性炭"],
            "implementation": "对比文件使用清水处理"
        }
    }

    initial_review = simulator.simulate_initial_review(
        oa_text=oa_text,
        claims=claims,
        prior_art_analysis=prior_art_analysis
    )

    print("\n=== 初次审查意见模拟 ===")
    print(f"驳回类型: {initial_review['rejection_type']}")
    print(f"论证策略: {initial_review['strategy']}")
    print(f"质疑数量: {len(initial_review['objections'])}")
    print(f"总体结论: {initial_review['overall_conclusion']}")

    # 模拟申请人答复后的回应
    applicant_argument = """
    尊敬的审查员：
    关于权利要求1的创造性，申请人认为：
    1. 对比文件未公开盐水处理步骤，更未公开使用活性炭和维生素C的组合。
    2. 四要素（盐水、温度、活性炭、维生素C）产生了协同效果。
    3. 实验数据显示，本申请方法显著优于对比文件。
    """

    response = simulator.respond_to_applicant_argument(
        applicant_argument=applicant_argument,
        prior_art_analysis=prior_art_analysis,
        round_number=1
    )

    print("\n=== 审查员回应 ===")
    print(f"回应策略: {response['response_strategy']}")
    print(f"反驳论点数量: {len(response['rebuttal']['rebuttal_points'])}")
    for i, point in enumerate(response['rebuttal']['rebuttal_points'], 1):
        print(f"{i}. {point[:80]}...")
