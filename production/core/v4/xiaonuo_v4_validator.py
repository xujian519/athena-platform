#!/usr/bin/env python3
from __future__ import annotations
"""
小诺v4.0自检机制
Xiaonuo v4.0 Self-Validation Module

基于维特根斯坦《逻辑哲学论》原则
确保每个响应都符合v4.0标准
"""

import re


class ResponseValidator:
    """响应验证器"""

    def __init__(self):
        # 禁止模式(不应该出现的表达)
        self.forbidden_patterns = {
            "模糊推测": [r"我觉得可能", r"大概也许", r"应该可以", r"估计", r"差不多", r"好像"],
            "无根据判断": [r"直觉告诉我", r"感觉像是", r"凭经验"],
            "无意义填充": [r"某种程度上", r"从某种角度", r"可以说"],
        }

        # 必需特征(每个响应应该有的)
        self.required_features = {
            "结构清晰": "响应应该有明确的结论或说明",
            "逻辑一致": "响应不能自相矛盾",
            "证据支持": "如果有结论,应该有证据支持",
            "不确定性标注": "不确定的必须明确说明",
        }

    def validate(self, response: str) -> tuple[bool, list[str], list[str]]:
        """
        验证响应是否符合v4.0标准

        Returns:
            (是否通过, 问题列表, 建议列表)
        """
        issues = []
        suggestions = []

        # 检查禁止模式
        for category, patterns in self.forbidden_patterns.items():
            for pattern in patterns:
                if re.search(pattern, response):
                    issues.append(f"发现禁止表达:{category} - '{pattern}'")
                    suggestions.append("替换为确定表达或明确说不确定")

        # 检查模糊表达
        vague_count = len(re.findall(r"(可能|也许|大概|应该|估计)", response))
        if vague_count > 3:
            issues.append(f"模糊表达过多:发现{vague_count}处")
            suggestions.append("减少模糊表达,增加确定性")

        # 检查是否有明确结论
        has_conclusion = self._check_conclusion(response)
        if not has_conclusion and "?" not in response:
            issues.append("缺少明确结论")
            suggestions.append("提供明确的结论或说明")

        # 检查是否有证据支持
        has_evidence = self._check_evidence(response)
        if has_conclusion and not has_evidence:
            issues.append("结论缺乏证据支持")
            suggestions.append("提供支持结论的证据或数据")

        # 检查不确定性标注
        has_uncertainty_label = self._check_uncertainty_label(response)
        if vague_count > 0 and not has_uncertainty_label:
            issues.append("不确定但未标注")
            suggestions.append("明确标注确定性程度")

        passed = len(issues) == 0

        return passed, issues, suggestions

    def _check_conclusion(self, response: str) -> bool:
        """检查是否有明确结论"""
        # 有明确的结论标记
        conclusion_markers = ["结论", "因此", "所以", "确定", "✅", "❌"]
        return any(marker in response for marker in conclusion_markers)

    def _check_evidence(self, response: str) -> bool:
        """检查是否有证据支持"""
        evidence_markers = ["证据", "数据", "文档", "测试", "验证", "因为", "基于", "根据"]
        return any(marker in response for marker in evidence_markers)

    def _check_uncertainty_label(self, response: str) -> bool:
        """检查是否标注了不确定性"""
        uncertainty_labels = ["置信度", "确定性", "不确定", "信息不足", "无法确定"]
        return any(label in response for label in uncertainty_labels)


class XiaonuoV4ResponseBuilder:
    """小诺v4.0响应构建器"""

    def __init__(self):
        self.validator = ResponseValidator()
        self.response_templates = {
            "certain": "✅ 确定:{statement}\n📋 证据:{evidence}",
            "likely": "⚠️ 很可能:{statement}\n📊 置信度:70-90%\n📋 依据:{evidence}",
            "uncertain": "❓ 不确定:{statement}\n⚠️ 原因:{reason}",
            "unknown": "❌ 我不知道:{question}\n💡 这超出了我的知识范围",
        }

    def build(
        self,
        statement: str,
        certainty: float,
        evidence: list | None = None,
        limitations: list | None = None,
    ) -> str:
        """
        构建v4.0标准响应

        Args:
            statement: 陈述内容
            certainty: 确定性 (0.0-1.0)
            evidence: 证据列表
            limitations: 局限性列表

        Returns:
            格式化的响应
        """
        # 根据确定性选择模板
        if certainty >= 0.9:
            template = self.response_templates["certain"]
            return template.format(
                statement=statement, evidence="\n".join(f"  • {ev}" for ev in (evidence or []))
            )
        elif certainty >= 0.7:
            template = self.response_templates["likely"]
            return template.format(statement=statement, evidence=", ".join(evidence or []))
        elif certainty >= 0.3:
            template = self.response_templates["uncertain"]
            return template.format(
                statement=statement, reason=", ".join(limitations or ["信息不足"])
            )
        else:
            template = self.response_templates["unknown"]
            return template.format(question=statement)

    def build_structured(
        self,
        conclusion: str,
        analysis: dict,
        certainty: float,
        recommendations: list | None = None,
    ) -> str:
        """
        构建结构化响应

        Args:
            conclusion: 结论
            analysis: 分析结果字典
            certainty: 确定性
            recommendations: 建议列表

        Returns:
            结构化响应
        """
        parts = []

        # 1. 结论(带确定性标注)
        if certainty >= 0.9:
            parts.append(f"✅ 确定:{conclusion}")
        elif certainty >= 0.7:
            parts.append(f"⚠️ 很可能:{conclusion}")
        elif certainty >= 0.5:
            parts.append(f"🤔 可能:{conclusion}")
        else:
            parts.append(f"❓ 不确定:{conclusion}")

        # 2. 详细分析
        if analysis:
            parts.append("\n📊 详细分析:")
            for key, value in analysis.items():
                parts.append(f"  • {key}:{value}")

        # 3. 确定性评估
        parts.append(f"\n📈 确定性:{certainty:.1%}")
        if certainty < 0.9:
            parts.append("  ⚠️ 低于高确定性阈值")

        # 4. 建议
        if recommendations:
            parts.append("\n💡 建议:")
            for i, rec in enumerate(recommendations, 1):
                parts.append(f"  {i}. {rec}")

        # 5. 局限性
        if certainty < 0.7:
            parts.append("\n⚠️ 注意:本评估基于当前可用信息,可能需要更多信息")

        return "\n".join(parts)

    def validate_response(self, response: str) -> tuple[bool, str]:
        """
        验证响应并提供反馈

        Returns:
            (是否通过, 反馈信息)
        """
        passed, issues, suggestions = self.validator.validate(response)

        if passed:
            return True, "✅ 响应符合v4.0标准"
        else:
            feedback = "❌ 响应不符合v4.0标准:\n\n"
            feedback += "问题:\n"
            for issue in issues:
                feedback += f"  • {issue}\n"

            feedback += "\n建议:\n"
            for suggestion in suggestions:
                feedback += f"  • {suggestion}\n"

            return False, feedback


# 使用示例和测试
if __name__ == "__main__":
    builder = XiaonuoV4ResponseBuilder()

    print("=" * 80)
    print("小诺v4.0响应构建器测试")
    print("=" * 80)

    # 测试1:高确定性
    print("\n测试1:高确定性响应")
    print("-" * 80)
    response1 = builder.build(
        statement="Python的列表是可变的数据结构",
        certainty=0.95,
        evidence=["官方文档定义", "语言规范", "实际测试验证"],
    )
    print(response1)

    # 验证
    passed1, feedback1 = builder.validate_response(response1)
    print(f"\n验证结果:{feedback1}")

    # 测试2:结构化响应
    print("\n" + "=" * 80)
    print("测试2:结构化响应")
    print("-" * 80)
    response2 = builder.build_structured(
        conclusion="该技术方案在架构上是可行的",
        analysis={
            "架构合理性": "符合设计原则",
            "性能考虑": "需要进一步测试",
            "维护成本": "中等复杂度",
        },
        certainty=0.75,
        recommendations=["进行性能基准测试", "评估扩展性", "制定监控方案"],
    )
    print(response2)

    # 验证
    passed2, feedback2 = builder.validate_response(response2)
    print(f"\n验证结果:{feedback2}")

    # 测试3:检测不合格响应
    print("\n" + "=" * 80)
    print("测试3:检测不合格响应")
    print("-" * 80)
    bad_response = "我觉得这个方案大概也许应该可以,估计差不多"
    passed3, feedback3 = builder.validate_response(bad_response)
    print(f"响应:{bad_response}")
    print(f"\n{feedback3}")
