#!/usr/bin/env python3
from __future__ import annotations
"""
论点提取模块
Argument Extractor for Patent Judgments

功能:
- 从"本院认为"部分提取论点
- 识别法律条文引用
- 提取论证逻辑(前提→推理→结论)
- 构建三层粒度结构(L1法条→L2焦点→L3论点)
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

logger = setup_logging()


@dataclass
class LegalArticleReference:
    """法律条文引用"""

    article_name: str  # 如:专利法第26条第3款
    article_content: str = ""  # 条文内容
    is_direct_quote: bool = False  # 是否直接引用


@dataclass
class ArgumentLogic:
    """论证逻辑"""

    premise: str  # 前提(事实认定)
    reasoning: str  # 推理(法律适用)
    conclusion: str  # 结论(裁判结果)
    logic_type: str = "deductive"  # 推理类型:演绎/归纳/类比


@dataclass
class Argument:
    """论点(L3层)"""

    argument_id: str  # 论点ID
    case_id: str  # 所属案号
    legal_articles: list[LegalArticleReference]  # 引用的法条
    dispute_focus: str  # 争议焦点
    argument_logic: ArgumentLogic  # 论证逻辑
    confidence: float = 0.8  # 置信度
    evidence: list[str] = field(default_factory=list)  # 证据引用


class ArgumentExtractor:
    """论点提取器"""

    # 法律条文识别模式
    LEGAL_ARTICLE_PATTERNS = [
        r"专利法第?\d+[条款项号]*",
        r"专利法实施细则第?\d+[条款项号]*",
        r"审查指南第?\w*[部分章节条款]*",
        r"最高人民法院[关于]*[^,。]+",
        r"民事诉讼法第?\d+[条款项号]*",
    ]

    # 论证逻辑标识词
    LOGIC_INDICATORS = {
        "premise": ["鉴于", "根据", "依据", "查明", "认定", "事实是", "由于"],
        "reasoning": ["因此", "故", "所以", "据此", "综上", "可见", "显然"],
        "conclusion": ["判决", "裁定", "认定", "支持", "驳回", "确认", "不予支持"],
    }

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """
        初始化论点提取器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.stats = {
            "total_arguments": 0,
            "total_legal_articles": 0,
            "avg_arguments_per_case": 0,
        }

    def extract_arguments(
        self, case_id: str, court_opinion: str, dispute_focus_list: list[str]
    ) -> list[Argument]:
        """
        从"本院认为"部分提取论点

        Args:
            case_id: 案号
            court_opinion: 本院认为部分文本
            dispute_focus_list: 争议焦点列表

        Returns:
            论点列表
        """
        if not court_opinion:
            logger.warning(f"本院认为部分为空: {case_id}")
            return []

        arguments = []

        # 方法1: 按争议焦点划分论点
        if dispute_focus_list:
            for focus in dispute_focus_list:
                # 在本院认为中查找与该焦点相关的内容
                focus_content = self._find_focus_related_content(court_opinion, focus)

                if focus_content:
                    argument = self._extract_single_argument(case_id, focus, focus_content)
                    if argument:
                        arguments.append(argument)

        # 方法2: 如果没有争议焦点,尝试按段落划分
        if not arguments:
            paragraphs = self._split_paragraphs(court_opinion)
            for para in paragraphs:
                if len(para) > 50:  # 忽略太短的段落
                    argument = self._extract_single_argument(case_id, "", para)  # 无明确争议焦点
                    if argument:
                        arguments.append(argument)

        # 生成论点ID
        for i, arg in enumerate(arguments):
            arg.argument_id = f"{case_id}_{i+1:03d}"

        # 更新统计
        self.stats["total_arguments"] += len(arguments)

        logger.info(f"从 {case_id} 提取了 {len(arguments)} 个论点")
        return arguments

    def _find_focus_related_content(self, court_opinion: str, dispute_focus: str) -> str:
        """
        在本院认为中查找与争议焦点相关的内容

        Args:
            court_opinion: 本院认为全文
            dispute_focus: 争议焦点

        Returns:
            相关内容
        """
        # 提取争议焦点的关键词
        keywords = self._extract_keywords_from_focus(dispute_focus)

        # 在本院认为中查找包含这些关键词的句子
        sentences = re.split(r"[。;;]", court_opinion)

        relevant_sentences = []
        for sentence in sentences:
            if any(kw in sentence for kw in keywords):
                relevant_sentences.append(sentence)

        # 如果找到相关句子,返回它们的组合
        if relevant_sentences:
            # 按原文顺序组合
            combined = []
            last_pos = -1
            for sentence in sentences:
                if sentence in relevant_sentences:
                    current_pos = court_opinion.find(sentence)
                    if current_pos > last_pos:
                        combined.append(sentence)
                        last_pos = current_pos + len(sentence)

            return "。".join(combined)

        # 如果没有找到,返回空
        return ""

    def _extract_keywords_from_focus(self, dispute_focus: str) -> list[str]:
        """从争议焦点中提取关键词"""
        keywords = []

        # 提取专业术语
        # 如:创造性、新颖性、充分公开、等同侵权等
        term_patterns = [
            r"创造性|新颖性|实用性",
            r"充分公开|完整|清楚",
            r"等同侵权|全面覆盖",
            r"现有技术|区别技术特征|技术启示",
            r"显著性|实质性特点|进步",
        ]

        for pattern in term_patterns:
            matches = re.findall(pattern, dispute_focus)
            keywords.extend(matches)

        # 提取"是否"后的内容
        is_pattern = r"是否([^,。]+)"
        matches = re.findall(is_pattern, dispute_focus)
        keywords.extend(matches)

        return list(set(keywords))

    def _split_paragraphs(self, text: str) -> list[str]:
        """将文本分割成段落"""
        # 按换行符分割
        paragraphs = re.split(r"\n+", text)

        # 去除空白段落
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        return paragraphs

    def _extract_single_argument(
        self, case_id: str, dispute_focus: str, content: str
    ) -> Argument | None:
        """
        提取单个论点

        Args:
            case_id: 案号
            dispute_focus: 争议焦点
            content: 论点内容

        Returns:
            Argument对象
        """
        # 提取法律条文
        legal_articles = self._extract_legal_articles(content)

        # 提取论证逻辑
        argument_logic = self._extract_argument_logic(content)

        # 计算置信度
        confidence = self._calculate_confidence(legal_articles, argument_logic, content)

        argument = Argument(
            argument_id="",  # 将在外部生成
            case_id=case_id,
            legal_articles=legal_articles,
            dispute_focus=dispute_focus,
            argument_logic=argument_logic,
            confidence=confidence,
        )

        return argument

    def _extract_legal_articles(self, text: str) -> list[LegalArticleReference]:
        """
        提取法律条文引用

        Args:
            text: 文本

        Returns:
            法律条文列表
        """
        articles = []

        for pattern in self.LEGAL_ARTICLE_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                article = LegalArticleReference(
                    article_name=match.strip(), is_direct_quote=(match in text)
                )
                articles.append(article)

        # 去重
        unique_articles = {}
        for article in articles:
            if article.article_name not in unique_articles:
                unique_articles[article.article_name] = article

        self.stats["total_legal_articles"] += len(unique_articles)

        return list(unique_articles.values())

    def _extract_argument_logic(self, text: str) -> ArgumentLogic:
        """
        提取论证逻辑

        Args:
            text: 文本

        Returns:
            ArgumentLogic对象
        """
        # 尝试识别三段论结构

        # 1. 提取前提(事实认定)
        premise_parts = []
        for indicator in self.LOGIC_INDICATORS["premise"]:
            # 查找包含指示词的句子
            pattern = f"{indicator}([^。;;]+)"
            matches = re.findall(pattern, text)
            premise_parts.extend(matches)

        premise = ";".join(premise_parts) if premise_parts else text[:200]

        # 2. 提取推理(法律适用)
        reasoning_parts = []
        for indicator in self.LOGIC_INDICATORS["reasoning"]:
            pattern = f"{indicator}([^。;;]+)"
            matches = re.findall(pattern, text)
            reasoning_parts.extend(matches)

        reasoning = ";".join(reasoning_parts) if reasoning_parts else ""

        # 3. 提取结论(裁判结果)
        conclusion_parts = []
        for indicator in self.LOGIC_INDICATORS["conclusion"]:
            pattern = f"{indicator}([^。;;]+)"
            matches = re.findall(pattern, text)
            conclusion_parts.extend(matches)

        conclusion = ";".join(conclusion_parts) if conclusion_parts else text[-200:]

        return ArgumentLogic(
            premise=premise.strip(), reasoning=reasoning.strip(), conclusion=conclusion.strip()
        )

    def _calculate_confidence(
        self,
        legal_articles: list[LegalArticleReference],
        argument_logic: ArgumentLogic,
        content: str,
    ) -> float:
        """
        计算论点提取的置信度

        Args:
            legal_articles: 法律条文
            argument_logic: 论证逻辑
            content: 内容

        Returns:
            置信度分数(0-1)
        """
        score = 0.0

        # 有法律条文引用 +0.3
        if legal_articles:
            score += 0.3

        # 论证逻辑完整 +0.3
        if argument_logic.premise and argument_logic.reasoning and argument_logic.conclusion:
            score += 0.3

        # 内容长度合理 +0.2
        if 100 < len(content) < 1000:
            score += 0.2

        # 包含法律术语 +0.2
        legal_terms = ["创造性", "新颖性", "充分公开", "等同侵权", "现有技术", "区别技术特征"]
        if any(term in content for term in legal_terms):
            score += 0.2

        return min(score, 1.0)


class JudgmentStructurer:
    """判决书结构化处理器"""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """
        初始化结构化处理器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.argument_extractor = ArgumentExtractor(config)

    def structure_judgment(self, extraction_result: dict[str, Any]) -> dict[str, Any]:
        """
        结构化判决书

        Args:
            extraction_result: PDF提取结果

        Returns:
            结构化数据
        """
        case_info = extraction_result["case_info"]
        sections = extraction_result["sections"]
        extraction_result["full_text"]

        # 提取论点
        arguments = self.argument_extractor.extract_arguments(
            case_info.case_id, sections.court_opinion, sections.dispute_focus
        )

        # 构建三层结构
        structured = {
            "case_info": {
                "case_id": case_info.case_id,
                "court": case_info.court,
                "level": case_info.level,
                "case_type": case_info.case_type,
                "date": case_info.date,
                "plaintiff": case_info.plaintiff,
                "defendant": case_info.defendant,
            },
            "layer1": self._build_layer1(arguments),  # 法条层
            "layer2": self._build_layer2(arguments),  # 焦点层
            "layer3": self._build_layer3(arguments),  # 论点层
            "metadata": extraction_result["metadata"],
        }

        return structured

    def _build_layer1(self, arguments: list[Argument]) -> dict[str, Any]:
        """
        构建L1层:法条层

        Args:
            arguments: 论点列表

        Returns:
            L1层数据
        """
        layer1 = {}

        for arg in arguments:
            for article_ref in arg.legal_articles:
                article_name = article_ref.article_name

                if article_name not in layer1:
                    layer1[article_name] = {
                        "article_name": article_name,
                        "related_cases": set(),
                        "related_arguments": [],
                    }

                layer1[article_name]["related_cases"].add(arg.case_id)
                layer1[article_name]["related_arguments"].append(arg.argument_id)

        # 转换set为list
        for article in layer1.values():
            article["related_cases"] = list(article["related_cases"])

        return layer1

    def _build_layer2(self, arguments: list[Argument]) -> dict[str, Any]:
        """
        构建L2层:争议焦点层

        Args:
            arguments: 论点列表

        Returns:
            L2层数据
        """
        layer2 = {}

        for arg in arguments:
            focus = arg.dispute_focus or "未分类"

            if focus not in layer2:
                layer2[focus] = {
                    "focus_description": focus,
                    "related_cases": set(),
                    "related_arguments": [],
                }

            layer2[focus]["related_cases"].add(arg.case_id)
            layer2[focus]["related_arguments"].append(arg.argument_id)

        # 转换set为list
        for focus in layer2.values():
            focus["related_cases"] = list(focus["related_cases"])

        return layer2

    def _build_layer3(self, arguments: list[Argument]) -> list[dict[str, Any]]:
        """
        构建L3层:论点层

        Args:
            arguments: 论点列表

        Returns:
            L3层数据
        """
        layer3 = []

        for arg in arguments:
            arg_dict = {
                "argument_id": arg.argument_id,
                "case_id": arg.case_id,
                "dispute_focus": arg.dispute_focus,
                "legal_articles": [
                    {"article_name": ref.article_name, "is_direct_quote": ref.is_direct_quote}
                    for ref in arg.legal_articles
                ],
                "argument_logic": {
                    "premise": arg.argument_logic.premise,
                    "reasoning": arg.argument_logic.reasoning,
                    "conclusion": arg.argument_logic.conclusion,
                },
                "confidence": arg.confidence,
            }
            layer3.append(arg_dict)

        return layer3


# 便捷函数
def structure_judgment(
    extraction_result: dict[str, Any], config: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """
    结构化判决书

    Args:
        extraction_result: PDF提取结果
        config: 配置字典

    Returns:
        结构化数据
    """
    structurer = JudgmentStructurer(config)
    return structurer.structure_judgment(extraction_result)


if __name__ == "__main__":
    # 测试代码
    # setup_logging()  # 日志配置已移至模块导入

    from .pdf_extractor import PDFExtractor

    # 测试完整流程
    test_pdf = "/Volumes/AthenaData/07_Corpus_Data/语料/专利判决案件/(2020)最高法知行终197号.pdf"

    if Path(test_pdf).exists():
        # Step 1: 提取PDF
        extractor = PDFExtractor()
        extraction_result = extractor.extract_from_pdf(test_pdf)

        if extraction_result:
            # Step 2: 结构化
            structurer = JudgmentStructurer()
            structured = structurer.structure_judgment(extraction_result)

            # 输出结果
            print("\n" + "=" * 60)
            print("📊 结构化结果")
            print("=" * 60)
            print(f"案号: {structured['case_info']['case_id']}")
            print(f"\nL1层(法条): {len(structured['layer1'])}个")
            for article, data in structured["layer1"].items():
                print(f"  - {article}: {len(data['related_cases'])}份案例")

            print(f"\nL2层(焦点): {len(structured['layer2'])}个")
            for focus, data in structured["layer2"].items():
                print(f"  - {focus}: {len(data['related_cases'])}份案例")

            print(f"\nL3层(论点): {len(structured['layer3'])}个")
            for arg in structured["layer3"][:3]:  # 只显示前3个
                print(f"  - {arg['argument_id']}: {arg['dispute_focus']}")

            print("=" * 60)
