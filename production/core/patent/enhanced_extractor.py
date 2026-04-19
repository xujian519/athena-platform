#!/usr/bin/env python3
"""
增强的专利决定信息提取器
Enhanced Patent Decision Information Extractor

基于实际文档结构分析优化的智能提取算法
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Any

from docx import Document

from core.logging_config import setup_logging

logger = setup_logging()


@dataclass
class EnhancedPatentData:
    """增强的专利数据结构"""

    file_path: str = ""
    file_format: str = ""

    # 核心信息
    decision_number: str = ""
    patent_number: str = ""
    petitioner: str = ""
    patent_owner: str = ""
    patent_title: str = ""

    # 决定结果
    decision_result: str = ""
    decision_date: str = ""

    # 内容
    dispute_foci: list[str] = field(default_factory=list)
    legal_basis: list[str] = field(default_factory=list)
    decision_reason: str = ""
    full_content: str = ""

    # 元数据
    application_date: str = ""
    priority_date: str = ""
    grant_date: str = ""


class EnhancedPatentExtractor:
    """增强的专利信息提取器 - 基于文档结构分析的智能提取"""

    def __init__(self):
        """初始化提取器"""
        # 精确的正则表达式模式(基于实际文档结构)

        # 决定号: (第XXXXXX号)
        self.decision_number_pattern = re.compile(r"[((]第(\d+)号[))]")

        # 专利号: ZLxxxxxxxxxxx.x 或 ZLxxxxxxxxxxx
        self.patent_number_pattern = re.compile(r"ZL\s*(\d{12,}[\.X]?\d*)", re.IGNORECASE)

        # 请求人: 无效宣告请求人XXX(下称请求人)
        self.petitioner_pattern = re.compile(r"无效宣告请求人(.{2,30}?)(.{2,10}?请求人)")

        # 专利权人: 专利权人为XXX 或 专利权人原为XXX,后变更为XXX
        self.owner_patterns = [
            re.compile(r"专利权人为(.{2,50}?),"),
            re.compile(r"专利权人原为(.{2,30}?),后变更为(.{2,30}?),"),
            re.compile(r"专利权人原为(.{2,30}?),后变更为(.{2,30}?)的"),
        ]

        # 专利名称: 名称为"XXX"的发明专利
        self.title_pattern = re.compile(r'名称为["「」""' r'](.+?)["「」""' r"]的")

        # 申请日、优先权日、授权公告日
        self.date_pattern = re.compile(r"(\d{4})年(\d{2})月(\d{2})日")

    def extract(self, file_path: str) -> EnhancedPatentData:
        """
        从DOCX文件提取信息

        Args:
            file_path: 文档路径

        Returns:
            EnhancedPatentData对象
        """
        logger.info(f"📄 处理文件: {file_path}")

        try:
            doc = Document(file_path)
        except Exception as e:
            logger.error(f"❌ 无法读取文件: {e}")
            raise

        # 提取所有段落
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        full_content = "\n".join(paragraphs)

        data = EnhancedPatentData(
            file_path=file_path, file_format="docx", full_content=full_content
        )

        # 按顺序提取信息
        self._extract_decision_number(data, paragraphs)
        self._extract_patent_info(data, paragraphs)  # 专利号、专利权人、专利名称
        self._extract_petitioner(data, paragraphs)
        self._extract_decision_result(data, paragraphs)
        self._extract_dates(data, paragraphs)
        self._extract_dispute_foci(data, paragraphs)
        self._extract_legal_basis(data, paragraphs)

        # 打印提取结果
        logger.info(f"   决定号: {data.decision_number}")
        logger.info(f"   专利号: {data.patent_number}")
        logger.info(f"   请求人: {data.petitioner}")
        logger.info(f"   专利权人: {data.patent_owner}")
        logger.info(f"   专利名称: {data.patent_title[:50] if data.patent_title else ''}...")
        logger.info(f"   决定结果: {data.decision_result}")
        logger.info(f"   争议焦点数: {len(data.dispute_foci)}")

        return data

    def _extract_decision_number(self, data: EnhancedPatentData, paragraphs: list[str]) -> Any:
        """提取决定号 - 在段落2"""
        if len(paragraphs) >= 2:
            match = self.decision_number_pattern.search(paragraphs[1])
            if match:
                data.decision_number = match.group(1)

    def _extract_patent_info(self, data: EnhancedPatentData, paragraphs: list[str]) -> Any:
        """提取专利信息(专利号、专利权人、专利名称)- 通常在段落14-15"""
        for para in paragraphs[10:30]:  # 搜索段落10-30
            # 提取专利号
            if not data.patent_number:
                match = self.patent_number_pattern.search(para)
                if match:
                    data.patent_number = match.group(1)

            # 提取专利名称
            if not data.patent_title:
                match = self.title_pattern.search(para)
                if match:
                    data.patent_title = match.group(1).strip()

            # 提取专利权人
            if not data.patent_owner:
                for pattern in self.owner_patterns:
                    match = pattern.search(para)
                    if match:
                        if "后变更为" in para:  # 有变更情况
                            data.patent_owner = (
                                match.group(2).strip()
                                if match.lastindex >= 2
                                else match.group(1).strip()
                            )
                        else:
                            data.patent_owner = match.group(1).strip()
                        break

            # 如果都找到了就退出
            if data.patent_number and data.patent_title and data.patent_owner:
                break

    def _extract_petitioner(self, data: EnhancedPatentData, paragraphs: list[str]) -> Any:
        """提取请求人 - 通常在段落30-60"""
        for para in paragraphs[25:80]:
            match = self.petitioner_pattern.search(para)
            if match:
                data.petitioner = match.group(1).strip()
                break

    def _extract_decision_result(self, data: EnhancedPatentData, paragraphs: list[str]) -> Any:
        """提取决定结果 - 在最后20段"""
        # 决定结果通常在文档末尾
        for para in paragraphs[-20:]:
            # 查找具体的结果陈述
            if "宣告" in para and "专利权" in para:
                if "全部无效" in para:
                    data.decision_result = "宣告专利权全部无效"
                    return
                elif "部分无效" in para:
                    data.decision_result = "宣告专利权部分无效"
                    return
                elif "无效" in para:
                    data.decision_result = "宣告专利权无效"
                    return
            elif "维持" in para and "有效" in para:
                data.decision_result = "维持专利权有效"
                return
            elif "驳回" in para and "请求" in para:
                data.decision_result = "驳回请求"
                return

    def _extract_dates(self, data: EnhancedPatentData, paragraphs: list[str]) -> Any:
        """提取日期信息"""
        for para in paragraphs[10:30]:
            # 申请日
            if "申请日为" in para:
                match = self.date_pattern.search(para)
                if match:
                    data.application_date = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

            # 优先权日
            if "优先权日为" in para:
                match = self.date_pattern.search(para[para.find("优先权日为") :])
                if match:
                    data.priority_date = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

            # 授权公告日
            if "授权公告日" in para or "授权公告的" in para:
                matches = self.date_pattern.findall(para)
                for match in matches:
                    if not data.grant_date:
                        data.grant_date = f"{match[0]}-{match[1]}-{match[2]}"

    def _extract_dispute_foci(self, data: EnhancedPatentData, paragraphs: list[str]) -> Any:
        """提取争议焦点"""
        # 查找包含明确争议表述的段落
        focus_keywords = ["明确其", "无效理由", "范围为", "争议的实质"]

        foci = []
        for para in paragraphs:
            # 检查是否包含争议关键词
            if any(keyword in para for keyword in focus_keywords):
                # 分割句子并提取
                sentences = re.split(r"[,。;;]", para)
                for sentence in sentences:
                    if len(sentence) > 30:  # 只取有实质内容的句子
                        foci.append(sentence.strip())
                        if len(foci) >= 5:
                            break

            if len(foci) >= 5:
                break

        data.dispute_foci = foci[:5]

    def _extract_legal_basis(self, data: EnhancedPatentData, paragraphs: list[str]) -> Any:
        """提取法律依据"""
        legal_pattern = re.compile(r"专利法(?:实施细则)?第?\d+条[第款项]?")

        legal_articles = set()
        for para in paragraphs:
            matches = legal_pattern.findall(para)
            legal_articles.update(matches)

        data.legal_basis = list(legal_articles)


# 测试代码
if __name__ == "__main__":

    # 配置日志
    # setup_logging()  # 日志配置已移至模块导入

    extractor = EnhancedPatentExtractor()

    # 测试文件
    test_file = (
        "/Volumes/AthenaData/07_Corpus_Data/语料/专利/专利无效复审决定原文/2015106590755.docx"
    )

    print("\n" + "=" * 80)
    print("🧪 测试增强的专利信息提取器")
    print("=" * 80 + "\n")

    try:
        data = extractor.extract(test_file)

        print("\n" + "=" * 80)
        print("✅ 提取结果汇总")
        print("=" * 80)
        print(f"决定号:        {data.decision_number}")
        print(f"专利号:        {data.patent_number}")
        print(f"请求人:        {data.petitioner}")
        print(f"专利权人:      {data.patent_owner}")
        print(f"专利名称:      {data.patent_title}")
        print(f"申请日:        {data.application_date}")
        print(f"优先权日:      {data.priority_date}")
        print(f"授权公告日:    {data.grant_date}")
        print(f"决定结果:      {data.decision_result}")
        print(f"争议焦点数:    {len(data.dispute_foci)}")
        print(f"法律依据:      {', '.join(data.legal_basis[:5])}")

        if data.dispute_foci:
            print("\n争议焦点:")
            for i, focus in enumerate(data.dispute_foci[:3], 1):
                print(f"  {i}. {focus[:100]}...")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
