#!/usr/bin/env python3
from __future__ import annotations
"""
改进的专利决定信息提取器
Improved Patent Decision Information Extractor

基于实际文档结构优化提取算法
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ImprovedPatentData:
    """改进的专利数据结构"""

    decision_number: str = ""
    patent_number: str = ""
    petitioner: str = ""
    patent_owner: str = ""
    patent_title: str = ""
    decision_result: str = ""
    dispute_foci: Optional[list[str]] = None
    legal_basis: Optional[list[str]] = None
    decision_reason: str = ""
    full_content: str = ""

    def __post_init__(self):
        if self.dispute_foci is None:
            self.dispute_foci = []
        if self.legal_basis is None:
            self.legal_basis = []


class ImprovedPatentExtractor:
    """改进的专利信息提取器"""

    def __init__(self):
        """初始化提取器"""
        # 改进的正则表达式模式

        # 决定号 - 匹配 (第XXXXXX号) 格式
        self.decision_number_pattern = re.compile(r"[((]第(\d+)号[))]")

        # 专利号 - 匹配 ZLxxxxxxxxxxx.x 格式
        self.patent_number_pattern = re.compile(r"ZL\s*(\d{12,}[\.X]?\d*)", re.IGNORECASE)

        # 请求人 - 多种格式
        self.petitioner_patterns = [
            re.compile(r"无效宣告请求人(.{2,20}?)(.{2,10}请求人)"),
            re.compile(r"无效宣告请求人(.{2,30}?)于"),
            re.compile(r"请求人[::](.{2,50}?)(?:,|。|\n)"),
            re.compile(r"请求人\s+(.{2,30}?)(?:\s|,|。)"),
        ]

        # 专利权人
        self.owner_patterns = [
            re.compile(r"专利权人为(.{2,50}?)(?:,|。|。本|\(|本)"),
            re.compile(r"专利权人[::](.{2,50}?)(?:,|。|\n)"),
        ]

        # 专利名称
        self.title_patterns = [
            re.compile(r'名称为["「」“”](.+?)["「」“”]的'),
            re.compile(r"名称为(.{2,100}?)(?:的发明|的实用)"),
        ]

        # 决定结果 - 改进的模式
        self.result_patterns = [
            re.compile(r"宣告(.{2,100}?)专利权(?:全部|部分)?无效", re.IGNORECASE),
            re.compile(r"维持(.{2,20}?)有效", re.IGNORECASE),
            re.compile(r"驳回(.{2,20}?)请求", re.IGNORECASE),
        ]

    def extract_from_docx(self, file_path: str) -> ImprovedPatentData:
        """从DOCX文件提取信息"""
        try:
            from docx import Document
        except ImportError:
            raise ImportError("需要安装 python-docx: pip install python-docx") from None

        doc = Document(file_path)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        full_content = "\n".join(paragraphs)

        data = ImprovedPatentData(full_content=full_content)

        # 提取各项信息
        self._extract_decision_number(data, paragraphs)
        self._extract_patent_number(data, paragraphs)
        self._extract_parties(data, paragraphs)
        self._extract_patent_title(data, paragraphs)
        self._extract_decision_result(data, paragraphs)
        self._extract_dispute_foci(data, paragraphs)
        self._extract_legal_basis(data, paragraphs)

        return data

    def _extract_decision_number(self, data: ImprovedPatentData, paragraphs: list[str]) -> Any:
        """提取决定号"""
        for para in paragraphs[:20]:  # 通常在前20段
            match = self.decision_number_pattern.search(para)
            if match:
                data.decision_number = match.group(1)
                return

        # 备用:从文件名提取
        filename = Path(data.file_path).stem if hasattr(data, "file_path") else ""
        if filename:
            data.decision_number = filename

    def _extract_patent_number(self, data: ImprovedPatentData, paragraphs: list[str]) -> Any:
        """提取专利号"""
        for para in paragraphs[:50]:  # 通常在前50段
            match = self.patent_number_pattern.search(para)
            if match:
                data.patent_number = match.group(1)
                return

    def _extract_parties(self, data: ImprovedPatentData, paragraphs: list[str]) -> Any:
        """提取当事人信息"""
        for para in paragraphs:
            # 提取请求人
            if not data.petitioner:
                for pattern in self.petitioner_patterns:
                    match = pattern.search(para)
                    if match:
                        data.petitioner = match.group(1).strip()
                        break

            # 提取专利权人
            if not data.patent_owner:
                for pattern in self.owner_patterns:
                    match = pattern.search(para)
                    if match:
                        data.patent_owner = match.group(1).strip()
                        break

            if data.petitioner and data.patent_owner:
                break

    def _extract_patent_title(self, data: ImprovedPatentData, paragraphs: list[str]) -> Any:
        """提取专利名称"""
        for para in paragraphs[:50]:
            for pattern in self.title_patterns:
                match = pattern.search(para)
                if match:
                    data.patent_title = match.group(1).strip()
                    return

    def _extract_decision_result(self, data: ImprovedPatentData, paragraphs: list[str]) -> Any:
        """提取决定结果"""
        # 通常在最后几段
        for para in paragraphs[-20:]:
            for pattern in self.result_patterns:
                match = pattern.search(para)
                if match:
                    result_text = match.group(0)

                    if "全部无效" in result_text:
                        data.decision_result = "宣告专利权全部无效"
                    elif "部分无效" in result_text:
                        data.decision_result = "宣告专利权部分无效"
                    elif "无效" in result_text:
                        data.decision_result = "宣告专利权无效"
                    elif "维持" in result_text:
                        data.decision_result = "维持专利权有效"
                    elif "驳回" in result_text:
                        data.decision_result = "驳回请求"

                    return

    def _extract_dispute_foci(self, data: ImprovedPatentData, paragraphs: list[str]) -> Any:
        """提取争议焦点"""
        # 查找明确表述争议范围的段落
        focus_keywords = ["明确其", "无效理由", "范围为", "争议的实质", "争议焦点", "本案争议"]

        foci = []
        for para in paragraphs:
            if any(keyword in para for keyword in focus_keywords):
                # 提取关键句子
                sentences = re.split(r"[,。;;]", para)
                for sentence in sentences:
                    if len(sentence) > 20 and any(
                        keyword in sentence for keyword in focus_keywords
                    ):
                        foci.append(sentence.strip())
                        if len(foci) >= 5:  # 最多5个争议焦点
                            break

            if len(foci) >= 5:
                break

        data.dispute_foci = foci

    def _extract_legal_basis(self, data: ImprovedPatentData, paragraphs: list[str]) -> Any:
        """提取法律依据"""
        legal_articles = []
        legal_pattern = re.compile(r"专利法(?:实施细则)?第?\d+条[第款]?")

        for para in paragraphs:
            matches = legal_pattern.findall(para)
            legal_articles.extend(matches)

        # 去重
        data.legal_basis = list(set(legal_articles))


# 测试
if __name__ == "__main__":
    extractor = ImprovedPatentExtractor()

    test_file = (
        "/Volumes/AthenaData/07_Corpus_Data/语料/专利/专利无效复审决定原文/2015106590755.docx"
    )

    print("🧪 测试改进的提取器")
    print("=" * 80)

    data = extractor.extract_from_docx(test_file)

    print("\n✅ 提取结果:")
    print(f"   决定号: {data.decision_number}")
    print(f"   专利号: {data.patent_number}")
    print(f"   请求人: {data.petitioner}")
    print(f"   专利权人: {data.patent_owner}")
    print(f"   专利名称: {data.patent_title[:50] if data.patent_title else ''}...")
    print(f"   决定结果: {data.decision_result}")
    print(f"   争议焦点数: {len(data.dispute_foci)}")
    print(f"   法律依据: {data.legal_basis}")
