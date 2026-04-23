#!/usr/bin/env python3

"""
提示词质量评估器
Prompt Quality Evaluator

评估维度：
1. 清晰度 (Clarity) - 结构清晰，易于理解
2. 完整性 (Completeness) - 包含所有必要信息
3. 一致性 (Consistency) - 内部逻辑一致
4. Token效率 (Token Efficiency) - 信息密度
5. 可执行性 (Actionability) - 指令可执行

作者: 小诺·双鱼公主
版本: v1.0
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class QualityMetric:
    """质量指标"""
    name: str
    score: float  # 0.0 - 1.0
    max_score: float = 1.0
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def percentage(self) -> float:
        return self.score / self.max_score * 100


@dataclass
class QualityReport:
    """质量报告"""
    clarity: QualityMetric
    completeness: QualityMetric
    consistency: QualityMetric
    token_efficiency: QualityMetric
    actionability: QualityMetric
    overall_score: float
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "overall_score": round(self.overall_score, 3),
            "metrics": {
                "clarity": round(self.clarity.score, 3),
                "completeness": round(self.completeness.score, 3),
                "consistency": round(self.consistency.score, 3),
                "token_efficiency": round(self.token_efficiency.score, 3),
                "actionability": round(self.actionability.score, 3),
            },
            "recommendations": self.recommendations,
        }

    def __str__(self) -> str:
        lines = [
            "=" * 60,
            "提示词质量评估报告",
            "=" * 60,
            f"\n总分: {self.overall_score:.1%}",
            "\n各维度得分:",
        ]

        for metric in [self.clarity, self.completeness, self.consistency,
                       self.token_efficiency, self.actionability]:
            bar = "█" * int(metric.percentage / 5) + "░" * (20 - int(metric.percentage / 5))
            lines.append(f"  {metric.name:15s} [{bar}] {metric.percentage:5.1f}%")

        if self.recommendations:
            lines.append("\n优化建议:")
            for i, rec in enumerate(self.recommendations, 1):
                lines.append(f"  {i}. {rec}")

        return '\n'.join(lines)


class PromptQualityEvaluator:
    """提示词质量评估器"""

    # 必须包含的元素
    REQUIRED_ELEMENTS = {
        "identity": ["身份", "你是", "我是", "AI助手"],
        "role": ["职责", "任务", "负责", "核心职责"],
        "instruction": ["必须", "禁止", "要求", "注意", "步骤"],
        "example": ["示例", "例如", "比如", "````"],
        "output": ["输出", "格式", "结果", "回复"],
    }

    # 可执行性关键词
    ACTION_KEYWORDS = [
        "必须", "禁止", "要求", "注意", "步骤", "规则",
        "确认", "检查", "验证", "执行", "完成",
        "MUST", "MUST NOT", "REQUIRED", "SHOULD",
    ]

    # 冗余模式
    REDUNDANT_PATTERNS = [
        r'\n{3,}',           # 连续3个以上空行
        r'---+\n---+',       # 连续分隔线
        r'#{2,}\s*#{2,}',    # 连续标题符号
        r'(\*\*[^*]+\*\*)\s*\1',  # 重复的加粗内容
    ]

    def evaluate(self, prompt: str) -> QualityReport:
        """
        评估提示词质量

        Args:
            prompt: 提示词内容

        Returns:
            QualityReport: 质量报告
        """
        clarity = self._evaluate_clarity(prompt)
        completeness = self._evaluate_completeness(prompt)
        consistency = self._evaluate_consistency(prompt)
        token_efficiency = self._evaluate_token_efficiency(prompt)
        actionability = self._evaluate_actionability(prompt)

        # 计算总分（加权平均）
        weights = {
            "clarity": 0.25,
            "completeness": 0.25,
            "consistency": 0.15,
            "token_efficiency": 0.15,
            "actionability": 0.20,
        }

        overall = (
            clarity.score * weights["clarity"] +
            completeness.score * weights["completeness"] +
            consistency.score * weights["consistency"] +
            token_efficiency.score * weights["token_efficiency"] +
            actionability.score * weights["actionability"]
        )

        # 生成优化建议
        recommendations = self._generate_recommendations(
            clarity, completeness, consistency, token_efficiency, actionability
        )

        return QualityReport(
            clarity=clarity,
            completeness=completeness,
            consistency=consistency,
            token_efficiency=token_efficiency,
            actionability=actionability,
            overall_score=overall,
            recommendations=recommendations,
        )

    def _evaluate_clarity(self, prompt: str) -> QualityMetric:
        """评估清晰度"""
        score = 0.0
        details = {}

        # 1. 结构化程度
        lines = prompt.split('\n')
        headers = sum(1 for l in lines if l.strip().startswith('#'))
        lists = sum(1 for l in lines if re.match(r'^[-\d]+\.\s+', l.strip()))
        structure_score = min(1.0, (headers + lists) / max(len(lines) * 0.1, 1))
        details["structure_score"] = structure_score
        score += structure_score * 0.3

        # 2. 句子长度
        sentences = re.split(r'[。！？\n]', prompt)
        sentences = [s for s in sentences if s.strip()]
        if sentences:
            avg_length = sum(len(s) for s in sentences) / len(sentences)
            # 理想长度 20-50 字符
            length_score = 1.0 - abs(avg_length - 35) / 100
            length_score = max(0, min(1, length_score))
            details["avg_sentence_length"] = avg_length
            details["length_score"] = length_score
            score += length_score * 0.3
        else:
            score += 0.15

        # 3. 代码块和示例
        code_blocks = prompt.count('```')
        code_score = min(1.0, code_blocks / 4)  # 4个代码块为满分
        details["code_blocks"] = code_blocks
        details["code_score"] = code_score
        score += code_score * 0.2

        # 4. 标注和强调
        bold_count = prompt.count('**')
        highlight_score = min(1.0, bold_count / 20)  # 20个强调为满分
        details["bold_count"] = bold_count
        details["highlight_score"] = highlight_score
        score += highlight_score * 0.2

        return QualityMetric(
            name="清晰度",
            score=score,
            details=details,
        )

    def _evaluate_completeness(self, prompt: str) -> QualityMetric:
        """评估完整性"""
        score = 0.0
        details = {}

        # 检查必须元素
        found_elements = {}
        for element, keywords in self.REQUIRED_ELEMENTS.items():
            found = any(kw in prompt for kw in keywords)
            found_elements[element] = found
            if found:
                score += 0.2

        details["found_elements"] = found_elements
        details["missing_elements"] = [k for k, v in found_elements.items() if not v]

        return QualityMetric(
            name="完整性",
            score=score,
            details=details,
        )

    def _evaluate_consistency(self, prompt: str) -> QualityMetric:
        """评估一致性"""
        score = 1.0
        details = {}

        # 1. 检查术语一致性
        # 查找可能不一致的术语对
        inconsistencies = []

        # 人称一致性
        first_person = len(re.findall(r'\b我\b', prompt))
        third_person = len(re.findall(r'\b它\b', prompt))
        if first_person > 0 and third_person > 0:
            ratio = abs(first_person - third_person) / max(first_person, third_person)
            if ratio > 0.5:
                inconsistencies.append("人称使用不一致")
                score -= 0.2

        # 2. 检查格式一致性
        # 标题层级
        headers = re.findall(r'^(#{1,6})\s+', prompt, re.MULTILINE)
        if headers:
            levels = [len(h) for h in headers]
            # 检查是否跳级（如 # 直接到 ###）
            for i in range(1, len(levels)):
                if levels[i] - levels[i-1] > 1:
                    inconsistencies.append(f"标题层级跳跃: {levels[i-1]} -> {levels[i]}")
                    score -= 0.1
                    break

        details["inconsistencies"] = inconsistencies
        score = max(0, score)

        return QualityMetric(
            name="一致性",
            score=score,
            details=details,
        )

    def _evaluate_token_efficiency(self, prompt: str) -> QualityMetric:
        """评估Token效率"""
        score = 1.0
        details = {}

        # 1. 检查冗余
        redundant_count = 0
        for pattern in self.REDUNDANT_PATTERNS:
            matches = re.findall(pattern, prompt)
            redundant_count += len(matches)

        redundancy_penalty = min(0.3, redundant_count * 0.05)
        score -= redundancy_penalty
        details["redundant_patterns"] = redundant_count

        # 2. 信息密度
        # 去除空白后的长度占比
        stripped_len = len(prompt.replace('\n', '').replace(' ', '').replace('\t', ''))
        original_len = len(prompt)
        density = stripped_len / original_len if original_len > 0 else 0

        # 理想密度 0.7-0.85
        if density < 0.6:
            score -= (0.6 - density) * 0.5
        elif density > 0.9:
            score -= (density - 0.9) * 0.3

        details["information_density"] = density

        # 3. 有效内容比例
        # 统计有效行（非空、非装饰）
        lines = prompt.split('\n')
        effective_lines = [
            l for l in lines
            if l.strip() and not re.match(r'^[-=]{3,}$', l.strip())
        ]
        effective_ratio = len(effective_lines) / len(lines) if lines else 0
        details["effective_line_ratio"] = effective_ratio

        if effective_ratio < 0.7:
            score -= (0.7 - effective_ratio) * 0.2

        score = max(0, min(1, score))

        return QualityMetric(
            name="Token效率",
            score=score,
            details=details,
        )

    def _evaluate_actionability(self, prompt: str) -> QualityMetric:
        """评估可执行性"""
        score = 0.0
        details = {}

        # 1. 可执行关键词
        keyword_count = sum(1 for kw in self.ACTION_KEYWORDS if kw in prompt)
        keyword_score = min(1.0, keyword_count / 10)  # 10个关键词为满分
        score += keyword_score * 0.4
        details["action_keyword_count"] = keyword_count

        # 2. 步骤指示
        step_patterns = [
            r'步骤\s*\d+',
            r'第\s*\d+\s*步',
            r'Step\s*\d+',
            r'\d+\.\s+',
        ]
        step_count = sum(len(re.findall(p, prompt)) for p in step_patterns)
        step_score = min(1.0, step_count / 5)  # 5个步骤为满分
        score += step_score * 0.3
        details["step_count"] = step_count

        # 3. 条件判断
        condition_patterns = [
            r'如果.*则',
            r'当.*时',
            r'若.*则',
            r'if.*then',
        ]
        condition_count = sum(len(re.findall(p, prompt, re.IGNORECASE)) for p in condition_patterns)
        condition_score = min(1.0, condition_count / 3)  # 3个条件为满分
        score += condition_score * 0.3
        details["condition_count"] = condition_count

        return QualityMetric(
            name="可执行性",
            score=score,
            details=details,
        )

    def _generate_recommendations(
        self,
        clarity: QualityMetric,
        completeness: QualityMetric,
        consistency: QualityMetric,
        token_efficiency: QualityMetric,
        actionability: QualityMetric,
    ) -> list[str]:
        """生成优化建议"""
        recommendations = []

        # 清晰度建议
        if clarity.score < 0.7:
            if clarity.details.get("structure_score", 1) < 0.5:
                recommendations.append("增加结构化元素（标题、列表）提高可读性")
            if clarity.details.get("length_score", 1) < 0.5:
                recommendations.append("优化句子长度，保持 20-50 字符为宜")

        # 完整性建议
        if completeness.score < 0.8:
            missing = completeness.details.get("missing_elements", [])
            if "identity" in missing:
                recommendations.append("添加明确的身份定义")
            if "instruction" in missing:
                recommendations.append("添加明确的指令和规则")
            if "example" in missing:
                recommendations.append("添加示例帮助理解")

        # 一致性建议
        if consistency.score < 0.8:
            inconsistencies = consistency.details.get("inconsistencies", [])
            for inc in inconsistencies[:3]:
                recommendations.append(f"修复一致性问题: {inc}")

        # Token效率建议
        if token_efficiency.score < 0.7:
            redundant = token_efficiency.details.get("redundant_patterns", 0)
            if redundant > 3:
                recommendations.append(f"删除 {redundant} 处冗余内容")
            density = token_efficiency.details.get("information_density", 0)
            if density < 0.6:
                recommendations.append("提高信息密度，减少空白和装饰")

        # 可执行性建议
        if actionability.score < 0.7:
            keywords = actionability.details.get("action_keyword_count", 0)
            if keywords < 5:
                recommendations.append("增加明确的指令关键词（必须、禁止、步骤等）")
            steps = actionability.details.get("step_count", 0)
            if steps < 3:
                recommendations.append("添加明确的步骤指示")

        return recommendations[:5]  # 最多5条建议


def evaluate_prompt_file(file_path: Path | str) -> QualityReport:
    """评估提示词文件"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    content = path.read_text()
    evaluator = PromptQualityEvaluator()
    return evaluator.evaluate(content)


def evaluate_all_prompts(prompts_dir: Path | str) -> dict[str, QualityReport]:
    """评估所有提示词"""
    prompts_path = Path(prompts_dir)
    evaluator = PromptQualityEvaluator()
    results = {}

    for md_file in prompts_path.rglob("*.md"):
        try:
            content = md_file.read_text()
            report = evaluator.evaluate(content)
            results[str(md_file.relative_to(prompts_path))] = report
        except Exception as e:
            results[str(md_file.relative_to(prompts_path))] = f"Error: {e}"

    return results


# 命令行入口
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # 评估指定文件
        file_path = sys.argv[1]
        report = evaluate_prompt_file(file_path)
        print(report)
    else:
        # 评估所有提示词
        prompts_dir = "/Users/xujian/Athena工作平台/prompts"
        results = evaluate_all_prompts(prompts_dir)

        print("=" * 60)
        print("提示词质量评估汇总")
        print("=" * 60)

        total_score = 0
        count = 0

        for file_name, report in sorted(results.items()):
            if isinstance(report, QualityReport):
                total_score += report.overall_score
                count += 1
                if report.overall_score < 0.7:
                    print(f"\n⚠️ {file_name}: {report.overall_score:.1%}")
                    for rec in report.recommendations[:2]:
                        print(f"   - {rec}")

        if count > 0:
            print(f"\n平均得分: {total_score/count:.1%}")
            print(f"评估文件数: {count}")

