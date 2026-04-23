#!/usr/bin/env python3
from __future__ import annotations

"""
推理模式提取器 - Reasoning Pattern Extractor
从无效决定中提取三步法推理模式

功能:
1. 从无效决定文本中提取三步法推理链
2. 识别区别技术特征
3. 识别技术问题推导
4. 识别技术启示判断
5. 构建推理模式模板库

版本: 1.0.0
创建时间: 2026-01-23
"""

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# 导入规则引擎
from .legal_rule_engine import (
    CreativityLevel,
)

logger = logging.getLogger(__name__)


# ============ 数据模型 ============


class SectionType(Enum):
    """无效决定段落类型"""

    BACKGROUND = "背景技术"
    CLAIMS = "权利要求"
    PRIOR_ART = "对比文件"
    DISTINGUISHING = "区别特征"
    TECHNICAL_PROBLEM = "技术问题"
    TECHNICAL_HINT = "技术启示"
    CONCLUSION = "审查结论"


@dataclass
class ReasoningPattern:
    """推理模式"""

    pattern_id: str
    name: str
    technical_field: str
    step1_distinguishing: list[str]  # 区别技术特征模式
    step2_problem: str  # 技术问题模式
    step3_hint: str  # 技术启示模式
    conclusion: CreativityLevel
    source_document: str  # 来源无效决定
    confidence: float = 0.0
    extracted_patterns: list[str] = field(default_factory=list)


@dataclass
class InvalidDecision:
    """无效决定结构化数据"""

    decision_id: str
    title: str
    patent_number: str
    technical_field: str
    content: str
    sections: dict[SectionType, str] = field(default_factory=dict)
    extracted_patterns: list[ReasoningPattern] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


# ============ 提取器 ============


class PatternExtractor:
    """
    推理模式提取器

    从无效决定中提取三步法推理模式
    """

    # 三步法关键词模式
    STEP1_PATTERNS = [
        r"区别[技术特征在于|在于]",
        r"权利要求\d+与对比文件\d+[的区别|区别在于]",
        r"不同[之处|点]在于",
        r"差异在于",
        r"相比于.*?的不同",
    ]

    STEP2_PATTERNS = [
        r"实际解决[的]?技术问题[是|为]",
        r"技术问题[是|为]",
        r"所要解决[的]?技术问题",
        r"发明目的[是|为]",
        r"改进了.*?的",
    ]

    STEP3_PATTERNS = [
        r"技术启示",
        r"给出了.*?启示",
        r"教导.*?结合",
        r"显而易见",
        r"公知常识",
        r"常规手段",
        r"容易想到",
    ]

    CONCLUSION_PATTERNS = [
        r"不具备创造性",
        r"具备创造性",
        r"维持无效",
        r"宣告无效",
        r"驳回请求",
        r"支持请求",
    ]

    def __init__(self):
        """初始化提取器"""
        self.pattern_library: list[ReasoningPattern] = []
        logger.info("✅ 推理模式提取器初始化成功")

    def parse_decision(
        self, decision_text: str, metadata: dict | None = None
    ) -> InvalidDecision:
        """
        解析无效决定文本

        Args:
            decision_text: 无效决定全文
            metadata: 元数据(专利号、决定号等)

        Returns:
            InvalidDecision: 结构化的无效决定对象
        """
        logger.info("=" * 60)
        logger.info("📄 开始解析无效决定")
        logger.info("=" * 60)

        # 提取元数据
        decision_id = metadata.get("decision_id", "UNKNOWN") if metadata else "UNKNOWN"
        title = metadata.get("title", "") if metadata else ""
        patent_number = metadata.get("patent_number", "") if metadata else ""
        technical_field = metadata.get("technical_field", "") if metadata else ""

        # 分段处理
        sections = self._split_into_sections(decision_text)

        logger.info("📊 分段结果:")
        for section_type, content in sections.items():
            if content:
                logger.info(f"  - {section_type.value}: {len(content)}字符")

        decision = InvalidDecision(
            decision_id=decision_id,
            title=title,
            patent_number=patent_number,
            technical_field=technical_field,
            content=decision_text,
            sections=sections,
            metadata=metadata or {},
        )

        logger.info("=" * 60)
        logger.info("✅ 无效决定解析完成")
        logger.info("=" * 60)

        return decision

    def extract_patterns(self, decision: InvalidDecision) -> list[ReasoningPattern]:
        """
        从无效决定中提取推理模式

        Args:
            decision: 结构化的无效决定

        Returns:
            推理模式列表
        """
        logger.info("=" * 60)
        logger.info("🔍 开始提取推理模式")
        logger.info("=" * 60)

        patterns = []

        # 提取三步法推理
        step1_features = self._extract_step1_features(decision)
        step2_problem = self._extract_step2_problem(decision)
        step3_hint = self._extract_step3_hint(decision)

        # 确定结论
        conclusion = self._extract_conclusion(decision)

        if step1_features or step2_problem or step3_hint:
            pattern = ReasoningPattern(
                pattern_id=f"{decision.decision_id}_pattern_{len(patterns)+1}",
                name=f"{decision.technical_field}创造性判断模式",
                technical_field=decision.technical_field,
                step1_distinguishing=step1_features,
                step2_problem=step2_problem,
                step3_hint=step3_hint,
                conclusion=conclusion,
                source_document=decision.decision_id,
                confidence=self._calculate_pattern_confidence(
                    step1_features, step2_problem, step3_hint
                ),
            )

            patterns.append(pattern)
            self.pattern_library.append(pattern)

            logger.info(f"✅ 提取推理模式: {pattern.pattern_id}")
            logger.info(f"  第一步: {len(step1_features)}个区别特征")
            logger.info(
                f"  第二步: {step2_problem[:50]}..." if step2_problem else "  第二步: 未提取"
            )
            logger.info(f"  第三步: {step3_hint[:50]}..." if step3_hint else "  第三步: 未提取")
            logger.info(f"  结论: {conclusion.value}")

        logger.info("=" * 60)
        logger.info(f"✅ 共提取 {len(patterns)} 个推理模式")
        logger.info("=" * 60)

        return patterns

    def _split_into_sections(self, text: str) -> dict[SectionType, str]:
        """将无效决定文本分段"""
        sections = {}

        # 定义段落标题模式
        section_patterns = {
            SectionType.BACKGROUND: r"(?:案情介绍|背景技术|事实认定)",
            SectionType.CLAIMS: r"(?:权利要求|本专利|涉案专利)",
            SectionType.PRIOR_ART: r"(?:对比文件|证据|现有技术)",
            SectionType.DISTINGUISHING: r"(?:区别特征|区别技术特征|不同之处|差异)",
            SectionType.TECHNICAL_PROBLEM: r"(?:技术问题|实际解决|发明目的)",
            SectionType.TECHNICAL_HINT: r"(?:技术启示|显而易见|结合启示)",
            SectionType.CONCLUSION: r"(?:审查结论|决定要点|认定结论)",
        }

        # 简化实现:按关键词提取
        for section_type, pattern in section_patterns.items():
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            if matches:
                # 获取匹配后的文本段落
                start = matches[0].end()
                # 查找下一个段落标题
                remaining_patterns = [p for p in section_patterns.values() if p != pattern]
                next_section_matches = []
                for other_pattern in remaining_patterns:
                    next_section_matches.extend(
                        re.finditer(other_pattern, text[start:])
                    )

                if next_section_matches:
                    end = start + min(m.start() for m in next_section_matches)
                else:
                    end = len(text)

                section_content = text[end]
                if section_content:
                    sections[section_type] = section_content

        return sections

    def _extract_step1_features(self, decision: InvalidDecision) -> list[str]:
        """提取第一步:区别技术特征"""
        features = []

        # 优先从专门段落提取
        if SectionType.DISTINGUISHING in decision.sections:
            section_text = decision.sections[SectionType.DISTINGUISHING]

            for pattern in self.STEP1_PATTERNS:
                matches = re.findall(pattern, section_text, re.IGNORECASE)
                features.extend(matches)

        # 从全文提取
        for pattern in self.STEP1_PATTERNS:
            matches = re.findall(pattern, decision.content, re.IGNORECASE)
            features.extend(matches)

        # 清理和去重
        features = self._clean_and_deduplicate(features)

        return features[:5]  # 返回最多5个特征

    def _extract_step2_problem(self, decision: InvalidDecision) -> str:
        """提取第二步:技术问题"""
        # 优先从专门段落提取
        if SectionType.TECHNICAL_PROBLEM in decision.sections:
            section_text = decision.sections[SectionType.TECHNICAL_PROBLEM]

            for pattern in self.STEP2_PATTERNS:
                match = re.search(pattern, section_text, re.IGNORECASE)
                if match:
                    # 提取完整句子
                    max(0, match.start() - 20)
                    end = min(len(section_text), match.end() + 100)
                    problem_sentence = section_text[end]
                    return problem_sentence

        # 从全文提取
        for pattern in self.STEP2_PATTERNS:
            match = re.search(pattern, decision.content, re.IGNORECASE)
            if match:
                max(0, match.start() - 20)
                end = min(len(decision.content), match.end() + 100)
                problem_sentence = decision.content[end]
                return problem_sentence

        return ""

    def _extract_step3_hint(self, decision: InvalidDecision) -> str:
        """提取第三步:技术启示"""
        # 优先从专门段落提取
        if SectionType.TECHNICAL_HINT in decision.sections:
            section_text = decision.sections[SectionType.TECHNICAL_HINT]

            for pattern in self.STEP3_PATTERNS:
                match = re.search(pattern, section_text, re.IGNORECASE)
                if match:
                    # 提取完整句子
                    max(0, match.start() - 20)
                    end = min(len(section_text), match.end() + 100)
                    hint_sentence = section_text[end]
                    return hint_sentence

        # 从全文提取
        for pattern in self.STEP3_PATTERNS:
            match = re.search(pattern, decision.content, re.IGNORECASE)
            if match:
                max(0, match.start() - 20)
                end = min(len(decision.content), match.end() + 100)
                hint_sentence = decision.content[end]
                return hint_sentence

        return ""

    def _extract_conclusion(self, decision: InvalidDecision) -> CreativityLevel:
        """提取审查结论"""
        # 优先从专门段落提取
        if SectionType.CONCLUSION in decision.sections:
            section_text = decision.sections[SectionType.CONCLUSION]

            for pattern in self.CONCLUSION_PATTERNS:
                if re.search(pattern, section_text, re.IGNORECASE):
                    if "不具备" in section_text or "无效" in section_text:
                        return CreativityLevel.CREATIVITY_NONE
                    else:
                        return CreativityLevel.CREATIVITY_HIGH

        # 从全文提取
        for pattern in self.CONCLUSION_PATTERNS:
            if re.search(pattern, decision.content, re.IGNORECASE):
                if "不具备" in decision.content or "无效" in decision.content:
                    return CreativityLevel.CREATIVITY_NONE
                else:
                    return CreativityLevel.CREATIVITY_HIGH

        return CreativityLevel.CREATIVITY_MEDIUM

    def _calculate_pattern_confidence(self, step1: list[str], step2: list[str] | None = None,
                                       step3: list[str] | None = None) -> float:
        """计算模式提取置信度"""
        confidence = 0.0

        if step1:
            confidence += 0.3
        if step2:
            confidence += 0.4
        if step3:
            confidence += 0.3

        return min(confidence, 1.0)

    def _clean_and_deduplicate(self, items: list[str]) -> list[str]:
        """清理和去重"""
        # 去除空白字符
        cleaned = [item.strip() for item in items if item.strip()]

        # 去重
        seen = set()
        result = []
        for item in cleaned:
            # 使用模糊去重
            item_lower = item.lower()
            is_duplicate = False
            for seen_item in seen:
                if item_lower in seen_item or seen_item in item_lower:
                    is_duplicate = True
                    break

            if not is_duplicate:
                seen.add(item_lower)
                result.append(item)

        return result

    def get_pattern_statistics(self) -> dict[str, Any]:
        """获取模式库统计信息"""
        if not self.pattern_library:
            return {"total_patterns": 0, "by_field": {}, "by_conclusion": {}, "avg_confidence": 0.0}

        by_field = defaultdict(int)
        by_conclusion = defaultdict(int)
        total_confidence = 0.0

        for pattern in self.pattern_library:
            by_field[pattern.technical_field] += 1
            by_conclusion[pattern.conclusion.value] += 1
            total_confidence += pattern.confidence

        return {
            "total_patterns": len(self.pattern_library),
            "by_field": dict(by_field),
            "by_conclusion": dict(by_conclusion),
            "avg_confidence": total_confidence / len(self.pattern_library),
        }


# ============ 主函数 ============


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="推理模式提取器测试")
    parser.add_argument("--test", action="store_true", help="运行测试")
    parser.add_argument("--input", type=str, help="输入无效决定文件")
    parser.add_argument("--output", type=str, help="输出模式文件")

    args = parser.parse_args()

    if args.test:
        test_pattern_extractor()
    elif args.input:
        extract_from_file(args.input, args.output)


def test_pattern_extractor():
    """测试模式提取器"""
    print("🧪 测试推理模式提取器")

    extractor = PatternExtractor()

    # 模拟无效决定文本
    mock_decision = """
    案情介绍:
    本专利涉及一种机械结构,专利号为CN202010123456.7。

    对比文件1(CN201812345678.9)公开了一种类似结构。

    区别特征:
    权利要求1与对比文件1的区别在于:本专利在连接处设置了加强筋,而对比文件1未设置。

    技术问题:
    根据区别特征,本专利实际解决的技术问题是:如何提高机械结构的强度和稳定性。

    技术启示:
    对比文件1未给出在连接处设置加强筋的技术启示,本领域技术人员没有动机将两者结合。

    审查结论:
    权利要求1具备创造性。
    """

    # 解析无效决定
    decision = extractor.parse_decision(
        mock_decision,
        metadata={
            "decision_id": "TEST_001",
            "patent_number": "CN202010123456.7",
            "technical_field": "机械结构",
        },
    )

    # 提取推理模式
    patterns = extractor.extract_patterns(decision)

    print(f"\n✅ 提取到 {len(patterns)} 个推理模式")
    for pattern in patterns:
        print(f"\n模式ID: {pattern.pattern_id}")
        print(f"技术领域: {pattern.technical_field}")
        print(f"结论: {pattern.conclusion.value}")
        print(f"置信度: {pattern.confidence:.2%}")
        print("第一步特征:")
        for feature in pattern.step1_distinguishing:
            print(f"  - {feature}")
        print(f"第二步问题: {pattern.step2_problem}")
        print(f"第三步启示: {pattern.step3_hint}")

    # 统计信息
    stats = extractor.get_pattern_statistics()
    print("\n📊 模式库统计:")
    print(f"  总模式数: {stats['total_patterns']}")
    print(f"  平均置信度: {stats['avg_confidence']:.2%}")


def extract_from_file(input_file: str, output_file: str | None = None):
    """从文件提取推理模式"""
    print(f"📄 读取文件: {input_file}")

    with open(input_file, encoding="utf-8") as f:
        content = f.read()

    extractor = PatternExtractor()
    decision = extractor.parse_decision(content)
    patterns = extractor.extract_patterns(decision)

    print(f"✅ 提取到 {len(patterns)} 个推理模式")

    if output_file:
        # 导出为JSON
        import json
        from dataclasses import asdict

        output_data = {
            "decision": {
                "decision_id": decision.decision_id,
                "title": decision.title,
                "patent_number": decision.patent_number,
                "technical_field": decision.technical_field,
            },
            "patterns": [asdict(p) for p in patterns],
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 结果已保存到: {output_file}")


if __name__ == "__main__":
    main()
