#!/usr/bin/env python3

"""
DSPy增强评估指标模块
Enhanced Metrics for DSPy Training

提供更宽容、多层次的评估方式,支持部分匹配和结构化奖励

作者: Athena平台团队
创建时间: 2025-12-30
版本: v1.0.0
"""

import re

import dspy
from typing import Optional


class EnhancedPatentMetrics:
    """
    增强的专利案例分析评估指标

    相比原始的evaluate_exact_match,本指标提供:
    - 部分匹配支持(相关类型给部分分)
    - 关键信息提取奖励(不管格式如何)
    - 推理质量评估(结构化、长度适中)
    - 容忍格式差异
    """

    # 类型分组(用于部分匹配)
    TYPE_GROUPS = {
        "novelty_related": ["novelty", "novel", "新颖性", "nov"],
        "creative_related": ["creative", "inventive", "创造性", "cre", "inv"],
        "disclosure_related": ["disclosure", "clarity", "公开", "清晰", "dis", "cla"],
        "evidence_related": ["evidence", "proof", "证据", "evi"],
        "procedure_related": ["procedure", "procedural", "程序", "pro"],
    }

    # 法律关键词(用于评估内容质量)
    LEGAL_KEYWORDS = [
        "专利法",
        "新颖性",
        "创造性",
        "实用性",
        "公开充分",
        "证据",
        "举证",
        "规定",
        "条款",
        "不符合",
        "认为",
        "因此",
        "综上",
        "根据",
        "按照",
    ]

    # 技术领域关键词
    TECH_KEYWORDS = ["技术领域", "所属领域", "涉及", "应用于", "领域"]

    # 结构化标记
    STRUCTURE_MARKERS = ["一、", "二、", "三、", "1.", "2.", "3.", "首先", "其次", "最后", "综上"]

    @staticmethod
    def evaluate_enhanced(example: dspy.Example, pred: dspy.Prediction, trace=None) -> float:
        """
        增强评估 - 多层次打分

        评分结构:
        - 层次1: Case Type匹配 (40分) - 完全匹配40分,相关类型20分
        - 层次2: 关键信息提取 (30分) - 专利号10分,技术领域10分,法律关键词10分
        - 层次3: 推理质量 (30分) - 长度适中15分,结构化15分

        Args:
            example: 标准答案示例
            pred: 模型预测结果
            trace: 训练轨迹(可选)

        Returns:
            评分 (0.0 - 1.0)
        """
        score = 0.0

        # ========== 层次1: Case Type匹配 (40分) ==========
        actual_type = EnhancedPatentMetrics._extract_case_type(example)
        pred_type = EnhancedPatentMetrics._extract_case_type(pred)

        if pred_type and actual_type:
            if pred_type.lower() == actual_type.lower():
                score += 0.40  # 完全匹配
            elif EnhancedPatentMetrics._is_related_type(pred_type, actual_type):
                score += 0.20  # 相关类型给部分分

        # ========== 层次2: 关键信息提取 (30分) ==========

        # 获取文本内容
        pred_text = EnhancedPatentMetrics._get_prediction_text(pred)
        example_text = EnhancedPatentMetrics._get_example_text(example)

        # 2.1 专利号匹配 (10分)
        pred_patent = EnhancedPatentMetrics._extract_patent_number(pred_text)
        example_patent = EnhancedPatentMetrics._extract_patent_number(example_text)
        if pred_patent and example_patent and pred_patent == example_patent:
            score += 0.10

        # 2.2 技术领域匹配 (10分)
        if EnhancedPatentMetrics._has_technical_field(pred_text):
            score += 0.10

        # 2.3 法律问题关键词 (10分)
        legal_keywords_found = sum(
            1 for kw in EnhancedPatentMetrics.LEGAL_KEYWORDS if kw in pred_text
        )
        if legal_keywords_found >= 3:
            score += 0.10
        elif legal_keywords_found >= 1:
            score += 0.05

        # ========== 层次3: 推理质量 (30分) ==========
        reasoning = EnhancedPatentMetrics._extract_reasoning(pred)

        if reasoning:
            # 3.1 长度适中 (100-1000字符) - 15分
            reasoning_len = len(reasoning)
            if 100 <= reasoning_len <= 1000:
                score += 0.15
            elif 50 <= reasoning_len < 100 or 1000 < reasoning_len <= 1500:
                score += 0.08  # 接近适中给部分分

            # 3.2 结构化 (有分段/标记) - 15分
            structure_count = sum(
                1 for marker in EnhancedPatentMetrics.STRUCTURE_MARKERS if marker in reasoning
            )
            if structure_count >= 3:
                score += 0.15
            elif structure_count >= 1:
                score += 0.08

        return min(score, 1.0)

    @staticmethod
    def _extract_case_type(obj) -> Optional[str]:
        """提取案例类型"""
        if hasattr(obj, "case_type"):
            return str(obj.case_type).strip()
        elif hasattr(obj, "output_analysis"):
            # 从output_analysis中提取类型
            text = str(obj.output_analysis)
            # 尝试从文本中提取类型标记
            for keyword in ["案例类型", "案件类型", "case_type", "类型:"]:
                if keyword in text:
                    match = re.search(rf"{keyword}\s*[::]\s*(\w+)", text)
                    if match:
                        return match.group(1).strip()
        return None

    @staticmethod
    def _is_related_type(pred_type: str, actual_type: str) -> bool:
        """
        检查类型是否相关

        Args:
            pred_type: 预测的类型
            actual_type: 实际的类型

        Returns:
            是否在同一类型分组中
        """
        pred_lower = pred_type.lower()
        actual_lower = actual_type.lower()

        for group in EnhancedPatentMetrics.TYPE_GROUPS.values():
            if pred_lower in group and actual_lower in group:
                return True

        return False

    @staticmethod
    def _extract_patent_number(text: str) -> Optional[str]:
        """
        提取专利号

        支持格式:CN1234567X, CN 1234567 X, 1234567X
        """
        # 匹配CN专利号
        match = re.search(r"CN\s*(\d+[A-Z])", text, re.IGNORECASE)
        if match:
            return f"CN{match.group(1).upper()}"

        # 匹配纯数字+字母格式
        match = re.search(r"\b(\d{7,}[A-Z])\b", text)
        if match:
            return match.group(0).upper()

        return None

    @staticmethod
    def _has_technical_field(text: str) -> bool:
        """
        检查是否包含技术领域信息

        Args:
            text: 待检查文本

        Returns:
            是否包含技术领域信息
        """
        return any(kw in text for kw in EnhancedPatentMetrics.TECH_KEYWORDS)

    @staticmethod
    def _get_prediction_text(pred: dspy.Prediction) -> str:
        """获取预测结果的完整文本"""
        text_parts = []

        if hasattr(pred, "output_analysis"):
            text_parts.append(str(pred.output_analysis))

        if hasattr(pred, "reasoning"):
            text_parts.append(str(pred.reasoning))

        if hasattr(pred, "case_type"):
            text_parts.append(str(pred.case_type))

        if hasattr(pred, "legal_issues"):
            text_parts.append(str(pred.legal_issues))

        if hasattr(pred, "conclusion"):
            text_parts.append(str(pred.conclusion))

        return " ".join(text_parts)

    @staticmethod
    def _get_example_text(example: dspy.Example) -> str:
        """获取示例的完整文本"""
        text_parts = []

        if hasattr(example, "context"):
            text_parts.append(str(example.context))

        if hasattr(example, "user_input"):
            text_parts.append(str(example.user_input))

        if hasattr(example, "analysis_result"):
            text_parts.append(str(example.analysis_result))

        return " ".join(text_parts)

    @staticmethod
    def _extract_reasoning(pred: dspy.Prediction) -> Optional[str]:
        """提取推理内容"""
        # 优先使用reasoning字段
        if hasattr(pred, "reasoning") and pred.reasoning:
            reasoning = str(pred.reasoning)
            if len(reasoning) > 20:  # 确保有实质内容
                return reasoning

        # 尝试从output_analysis中提取推理部分
        if hasattr(pred, "output_analysis"):
            text = str(pred.output_analysis)
            # 查找推理部分标记
            for keyword in ["分析", "理由", "reasoning", "推理", "说明"]:
                if keyword in text:
                    # 提取关键词后面的内容
                    idx = text.find(keyword)
                    if idx >= 0:
                        return text[idx:]

        return None

    @classmethod
    def get_evaluation_breakdown(
        cls, example: dspy.Example, pred: dspy.Prediction, trace=None
    ) -> dict:
        """
        获取详细评估分解

        用于调试和理解评分构成

        Args:
            example: 标准答案示例
            pred: 模型预测结果
            trace: 训练轨迹(可选)

        Returns:
            评分分解字典
        """
        breakdown = {
            "total_score": 0.0,
            "case_type_match": {"score": 0.0, "max": 0.40, "details": ""},
            "key_info_extraction": {"score": 0.0, "max": 0.30, "breakdown": {}},
            "reasoning_quality": {"score": 0.0, "max": 0.30, "breakdown": {}},
        }

        # Case Type匹配
        actual_type = cls._extract_case_type(example)
        pred_type = cls._extract_case_type(pred)

        if pred_type and actual_type:
            if pred_type.lower() == actual_type.lower():
                breakdown["case_type_match"]["score"] = 0.40
                breakdown["case_type_match"]["details"] = f"完全匹配: {pred_type}"
            elif cls._is_related_type(pred_type, actual_type):
                breakdown["case_type_match"]["score"] = 0.20
                breakdown["case_type_match"]["details"] = f"相关类型: {pred_type} ~ {actual_type}"
            else:
                breakdown["case_type_match"]["details"] = f"不匹配: {pred_type} != {actual_type}"

        # 关键信息提取
        pred_text = cls._get_prediction_text(pred)
        example_text = cls._get_example_text(example)

        # 专利号
        pred_patent = cls._extract_patent_number(pred_text)
        example_patent = cls._extract_patent_number(example_text)
        if pred_patent and example_patent and pred_patent == example_patent:
            breakdown["key_info_extraction"]["breakdown"]["patent_number"] = 0.10
        else:
            breakdown["key_info_extraction"]["breakdown"]["patent_number"] = 0.0

        # 技术领域
        breakdown["key_info_extraction"]["breakdown"]["technical_field"] = (
            0.10 if cls._has_technical_field(pred_text) else 0.0
        )

        # 法律关键词
        legal_count = sum(1 for kw in cls.LEGAL_KEYWORDS if kw in pred_text)
        if legal_count >= 3:
            breakdown["key_info_extraction"]["breakdown"]["legal_keywords"] = 0.10
        elif legal_count >= 1:
            breakdown["key_info_extraction"]["breakdown"]["legal_keywords"] = 0.05
        else:
            breakdown["key_info_extraction"]["breakdown"]["legal_keywords"] = 0.0

        breakdown["key_info_extraction"]["score"] = sum(
            breakdown["key_info_extraction"]["breakdown"].values()
        )

        # 推理质量
        reasoning = cls._extract_reasoning(pred)

        if reasoning:
            reasoning_len = len(reasoning)
            if 100 <= reasoning_len <= 1000:
                breakdown["reasoning_quality"]["breakdown"]["length"] = 0.15
            elif 50 <= reasoning_len < 100 or 1000 < reasoning_len <= 1500:
                breakdown["reasoning_quality"]["breakdown"]["length"] = 0.08
            else:
                breakdown["reasoning_quality"]["breakdown"]["length"] = 0.0

            structure_count = sum(1 for marker in cls.STRUCTURE_MARKERS if marker in reasoning)
            if structure_count >= 3:
                breakdown["reasoning_quality"]["breakdown"]["structure"] = 0.15
            elif structure_count >= 1:
                breakdown["reasoning_quality"]["breakdown"]["structure"] = 0.08
            else:
                breakdown["reasoning_quality"]["breakdown"]["structure"] = 0.0

            breakdown["reasoning_quality"]["score"] = sum(
                breakdown["reasoning_quality"]["breakdown"].values()
            )

        # 计算总分
        breakdown["total_score"] = (
            breakdown["case_type_match"]["score"]
            + breakdown["key_info_extraction"]["score"]
            + breakdown["reasoning_quality"]["score"]
        )

        return breakdown


# 便捷函数
def evaluate_enhanced(example: dspy.Example, pred: dspy.Prediction, trace=None) -> float:
    """增强评估的便捷函数"""
    return EnhancedPatentMetrics.evaluate_enhanced(example, pred, trace)


def get_evaluation_breakdown(example: dspy.Example, pred: dspy.Prediction, trace=None) -> dict:
    """获取评估分解的便捷函数"""
    return EnhancedPatentMetrics.get_evaluation_breakdown(example, pred, trace)


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("DSPy增强评估指标测试")
    print("=" * 60)

    # 创建测试示例
    example = dspy.Example(
        case_type="novelty",
        context="专利号: CN1234567X\n技术领域: 电子通信",
        analysis_result="这是一个新颖性案例",
    )

    # 测试1: 完全匹配
    print("\n[测试1]完全匹配")
    pred1 = dspy.Prediction(
        case_type="novelty",
        reasoning="一、案例分析\n首先,根据专利法规定,该专利不具备新颖性。\n因此,该专利无效。",
        output_analysis="专利号: CN1234567X\n技术领域: 电子通信\n根据专利法规定",
    )

    score1 = evaluate_enhanced(example, pred1)
    breakdown1 = get_evaluation_breakdown(example, pred1)
    print(f"总分: {score1:.2f}")
    print(
        f"Case Type: {breakdown1['case_type_match']['score']:.2f}/{breakdown1['case_type_match']['max']:.2f}"
    )
    print(
        f"关键信息: {breakdown1['key_info_extraction']['score']:.2f}/{breakdown1['key_info_extraction']['max']:.2f}"
    )
    print(
        f"推理质量: {breakdown1['reasoning_quality']['score']:.2f}/{breakdown1['reasoning_quality']['max']:.2f}"
    )

    # 测试2: 部分匹配
    print("\n[测试2]部分匹配(相关类型)")
    pred2 = dspy.Prediction(
        case_type="novel", reasoning="案例分析\n该专利不符合新颖性要求。"  # 相关类型
    )
    score2 = evaluate_enhanced(example, pred2)
    print(f"总分: {score2:.2f}")

    # 测试3: 无匹配
    print("\n[测试3]完全不匹配")
    pred3 = dspy.Prediction(case_type="creative", reasoning="简单分析")  # 不同类型
    score3 = evaluate_enhanced(example, pred3)
    print(f"总分: {score3:.2f}")

    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)

