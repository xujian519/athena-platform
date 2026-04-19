#!/usr/bin/env python3
"""
PDF判决书文本提取模块
Patent Judgment PDF Text Extractor

功能:
- 从PDF中提取文本内容
- 识别案件基本信息
- 分段识别判决书结构
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pdfplumber

from core.logging_config import setup_logging

logger = setup_logging()


@dataclass
class CaseInfo:
    """案件基本信息"""

    case_id: str  # 案号
    court: str  # 法院
    level: str  # 审级
    case_type: str  # 案由
    date: str  # 判决日期
    plaintiff: str = ""  # 原告
    defendant: str = ""  # 被告
    third_party: str = ""  # 第三人
    judges: list[str] = field(default_factory=list)  # 审判长、审判员


@dataclass
class JudgmentSections:
    """判决书分段内容"""

    case_statement: str = ""  # 案情感述
    dispute_focus: list[str] = field(default_factory=list)  # 争议焦点
    court_opinion: str = ""  # 本院认为
    judgment_result: str = ""  # 判决结果


class PDFExtractor:
    """PDF判决书文本提取器"""

    # 案号正则模式
    CASE_NUMBER_PATTERNS = [
        r"\(?\d{4}\)?[^(]+法[^(]+?\d+号",  # (2020)最高法知行终197号
        r"\d{4}[^(]+?[一二三四五六七八九十]+[号字号]",  # 2020...第X号
        r"[(\(]?\d{4}[)\)]?[^(]+?[一二三四五六七八九十]+[号字号]",  # (2020)...X号
    ]

    # 法院名称模式
    COURT_PATTERNS = [
        r"最高人民法院",
        r"高级人民法院",
        r"中级人民法院",
        r"基层人民法院",
        r"知识产权法院",
        r"铁路运输法院",
    ]

    # 判决书段落关键词
    SECTION_KEYWORDS = {
        "case_statement": ["案情感述", "原审法院查明", "一审法院查明", "查明"],
        "dispute_focus": ["争议焦点", "诉辩意见", "当事人争议"],
        "court_opinion": ["本院认为", "本院审理认为", "经审理"],
        "judgment_result": ["判决如下", "裁定如下", "判决结果", "裁决结果"],
    }

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化PDF提取器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.stats = {
            "processed": 0,
            "failed": 0,
            "total_pages": 0,
        }

    def extract_from_pdf(self, pdf_path: str) -> dict[str, Any] | None:
        """
        从PDF文件提取完整判决书信息

        Args:
            pdf_path: PDF文件路径

        Returns:
            包含案件信息、分段内容的字典,失败返回None
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            logger.error(f"PDF文件不存在: {pdf_path}")
            self.stats["failed"] += 1
            return None

        try:
            logger.info(f"开始提取: {pdf_path.name}")

            # 使用pdfplumber提取文本
            with pdfplumber.open(pdf_path) as pdf:
                # 提取全部文本
                full_text = self._extract_full_text(pdf)
                if not full_text:
                    logger.warning(f"未能提取到文本: {pdf_path.name}")
                    return None

                # 提取案件信息
                case_info = self._extract_case_info(full_text, pdf_path.name)

                # 分段识别
                sections = self._extract_sections(full_text)

                self.stats["processed"] += 1
                self.stats["total_pages"] += len(pdf.pages)

                result = {
                    "case_info": case_info,
                    "sections": sections,
                    "full_text": full_text,
                    "metadata": {
                        "source_file": str(pdf_path),
                        "pages": len(pdf.pages),
                        "extracted_at": datetime.now().isoformat(),
                    },
                }

                logger.info(f"✅ 提取完成: {case_info.case_id if case_info else pdf_path.name}")
                return result

        except Exception as e:
            logger.error(f"❌ 提取失败 {pdf_path.name}: {e!s}")
            self.stats["failed"] += 1
            return None

    def _extract_full_text(self, pdf: pdfplumber.PDF) -> str:
        """
        提取PDF全部文本

        Args:
            pdf: pdfplumber.PDF对象

        Returns:
            完整文本内容
        """
        text_parts = []

        for page in pdf.pages:
            try:
                page_text = page.extract_text()
                if page_text:
                    # 清理文本
                    page_text = self._clean_text(page_text)
                    text_parts.append(page_text)
            except Exception as e:
                logger.warning(f"页面提取失败: {e!s}")
                continue

        return "\n".join(text_parts)

    def _clean_text(self, text: str) -> str:
        """
        清理文本

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        # 移除多余空白
        text = re.sub(r"\s+", " ", text)
        # 移除页码
        text = re.sub(r"第\s*\d+\s*页", "", text)
        # 移除页眉页脚
        text = re.sub(r"-\s*\d+\s*-", "", text)

        return text.strip()

    def _extract_case_info(self, text: str, filename: str) -> CaseInfo | None:
        """
        提取案件基本信息

        Args:
            text: 判决书文本
            filename: 文件名

        Returns:
            CaseInfo对象
        """
        # 尝试从文本中提取案号
        case_id = self._extract_case_number(text)
        if not case_id:
            # 尝试从文件名提取
            case_id = filename.replace(".pdf", "")

        # 提取法院
        court = self._extract_court(text)

        # 提取审级
        level = self._extract_case_level(text, case_id)

        # 提取案由
        case_type = self._extract_case_type(text)

        # 提取判决日期
        date = self._extract_judgment_date(text)

        # 提取当事人
        plaintiff, defendant, third_party = self._extract_parties(text)

        # 提取法官
        judges = self._extract_judges(text)

        return CaseInfo(
            case_id=case_id,
            court=court,
            level=level,
            case_type=case_type,
            date=date,
            plaintiff=plaintiff,
            defendant=defendant,
            third_party=third_party,
            judges=judges,
        )

    def _extract_case_number(self, text: str) -> str | None:
        """提取案号"""
        for pattern in self.CASE_NUMBER_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                # 返回第一个匹配的案号
                return matches[0].strip()
        return None

    def _extract_court(self, text: str) -> str:
        """提取法院名称"""
        for pattern in self.COURT_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        return "未知法院"

    def _extract_case_level(self, text: str, case_id: str) -> str:
        """提取审级"""
        # 从案号中判断
        if "最高法" in case_id or "最高" in text:
            return "最高法院"
        elif "高" in case_id or "高级" in text:
            return "高级法院"
        elif "中" in case_id or "中级" in text:
            return "中级法院"
        elif "终" in case_id or "终审" in text:
            return "二审"
        else:
            return "一审"

    def _extract_case_type(self, text: str) -> str:
        """提取案由"""
        # 常见专利案由
        patent_types = [
            "发明专利权无效行政纠纷",
            "实用新型专利权侵权纠纷",
            "外观设计专利权侵权纠纷",
            "侵害发明专利权纠纷",
            "侵害实用新型专利权纠纷",
            "侵害外观设计专利权纠纷",
            "专利申请权权属纠纷",
        ]

        for case_type in patent_types:
            if case_type in text:
                return case_type

        # 如果没有匹配,尝试通用模式
        match = re.search(r"专利.*?纠纷", text)
        if match:
            return match.group(0)

        return "专利纠纷"

    def _extract_judgment_date(self, text: str) -> str:
        """提取判决日期"""
        # 匹配日期格式: 2020年12月15日
        date_pattern = r"(\d{4})年(\d{1,2})月(\d{1,2})日"
        matches = re.findall(date_pattern, text)

        if matches:
            # 返回最后一个匹配(通常是判决日期)
            year, month, day = matches[-1]
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

        return ""

    def _extract_parties(self, text: str) -> tuple:
        """提取当事人"""
        plaintiff = ""
        defendant = ""
        third_party = ""

        # 提取原告
        plaintiff_match = re.search(r"原告[::]\s*([^\n]+)", text)
        if plaintiff_match:
            plaintiff = plaintiff_match.group(1).strip()

        # 提取被告
        defendant_match = re.search(r"被告[::]\s*([^\n]+)", text)
        if defendant_match:
            defendant = defendant_match.group(1).strip()

        # 提取第三人
        third_party_match = re.search(r"第三人[::]\s*([^\n]+)", text)
        if third_party_match:
            third_party = third_party_match.group(1).strip()

        return plaintiff, defendant, third_party

    def _extract_judges(self, text: str) -> list[str]:
        """提取法官"""
        judges = []

        # 提取审判长
        chief_judge_match = re.search(r"审判长[::]\s*([^\n]+)", text)
        if chief_judge_match:
            judges.append(chief_judge_match.group(1).strip())

        # 提取审判员
        judge_matches = re.findall(r"审判员[::]\s*([^\n]+)", text)
        for judge in judge_matches:
            judges.append(judge.strip())

        # 提取代理审判员
        acting_judge_matches = re.findall(r"代理审判员[::]\s*([^\n]+)", text)
        for judge in acting_judge_matches:
            judges.append(judge.strip())

        return judges

    def _extract_sections(self, text: str) -> JudgmentSections:
        """
        分段识别判决书

        Args:
            text: 判决书文本

        Returns:
            JudgmentSections对象
        """
        sections = JudgmentSections()

        # 尝试使用关键词分段
        for section_type, keywords in self.SECTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    # 提取该部分内容
                    content = self._extract_section_content(text, keyword)
                    if content:
                        if section_type == "case_statement":
                            sections.case_statement = content
                        elif section_type == "dispute_focus":
                            sections.dispute_focus = self._parse_dispute_focus(content)
                        elif section_type == "court_opinion":
                            sections.court_opinion = content
                        elif section_type == "judgment_result":
                            sections.judgment_result = content
                    break

        return sections

    def _extract_section_content(self, text: str, keyword: str) -> str:
        """
        提取特定部分内容

        Args:
            text: 全文
            keyword: 关键词

        Returns:
            该部分内容
        """
        # 找到关键词位置(使用第一个出现的)
        keyword_pos = text.find(keyword)
        if keyword_pos == -1:
            return ""

        # 从关键词开始,到下一个关键词或文档结尾
        start_pos = keyword_pos + len(keyword)

        # 查找下一个关键词位置(需要在一定距离之后)
        next_section_pos = len(text)
        min_distance = 200  # 最小间距,避免误判

        for section_keywords in self.SECTION_KEYWORDS.values():
            for kw in section_keywords:
                if kw == keyword:
                    continue
                pos = text.find(kw, start_pos + min_distance)
                if pos != -1 and pos < next_section_pos:
                    next_section_pos = pos

        # 提取内容
        content = text[start_pos:next_section_pos].strip()

        # 清理内容(移除多余的空白字符)
        content = re.sub(r"\s+", " ", content)

        # 对于"本院认为"部分,确保有足够的内容
        if keyword == "本院认为" and len(content) < 100:
            # 如果提取的内容太短,尝试提取更大的范围
            # 查找"判决如下"或"裁定如下"作为结束
            ending_pattern = r"[判决裁定].下如"
            ending_match = re.search(ending_pattern, text[start_pos:])
            if ending_match:
                content = text[start_pos : start_pos + ending_match.end()].strip()
                content = re.sub(r"\s+", " ", content)

        # 限制长度(避免过长)
        if len(content) > 10000:
            content = content[:10000] + "..."

        return content

    def _parse_dispute_focus(self, content: str) -> list[str]:
        """
        解析争议焦点

        Args:
            content: 争议焦点部分内容

        Returns:
            争议焦点列表
        """
        focus_list = []

        # 尝试按数字分割
        pattern = r"[一二三四五六七八九十1-9][、．.]"
        parts = re.split(pattern, content)

        for part in parts:
            part = part.strip()
            if part and len(part) > 5:
                focus_list.append(part)

        # 如果没有分割成功,尝试按句子分割
        if not focus_list:
            sentences = re.split(r"[。;;]", content)
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and "是否" in sentence:
                    focus_list.append(sentence)

        return focus_list

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "processed": self.stats["processed"],
            "failed": self.stats["failed"],
            "success_rate": (
                self.stats["processed"] / (self.stats["processed"] + self.stats["failed"])
                if (self.stats["processed"] + self.stats["failed"]) > 0
                else 0
            ),
            "total_pages": self.stats["total_pages"],
            "avg_pages_per_doc": (
                self.stats["total_pages"] / self.stats["processed"]
                if self.stats["processed"] > 0
                else 0
            ),
        }

    def print_stats(self) -> Any:
        """打印统计信息"""
        stats = self.get_stats()
        logger.info("\n" + "=" * 60)
        logger.info("📊 PDF提取统计信息")
        logger.info("=" * 60)
        logger.info(f"✅ 成功处理: {stats['processed']}份")
        logger.info(f"❌ 处理失败: {stats['failed']}份")
        logger.info(f"📈 成功率: {stats['success_rate']*100:.1f}%")
        logger.info(f"📄 总页数: {stats['total_pages']}页")
        logger.info(f"📊 平均页数: {stats['avg_pages_per_doc']:.1f}页/份")
        logger.info("=" * 60 + "\n")


# 便捷函数
def extract_pdf(pdf_path: str | None = None, config: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """
    提取PDF判决书

    Args:
        pdf_path: PDF文件路径
        config: 配置字典

    Returns:
        提取结果字典
    """
    extractor = PDFExtractor(config)
    return extractor.extract_from_pdf(pdf_path)


if __name__ == "__main__":
    # 测试代码
    # setup_logging()  # 日志配置已移至模块导入

    # 测试提取单个PDF
    test_pdf = "/Volumes/AthenaData/07_Corpus_Data/语料/专利判决案件/(2020)最高法知行终197号.pdf"

    if Path(test_pdf).exists():
        result = extract_pdf(test_pdf)

        if result:
            print("\n" + "=" * 60)
            print("📄 提取结果预览")
            print("=" * 60)
            print(f"案号: {result['case_info'].case_id}")
            print(f"法院: {result['case_info'].court}")
            print(f"审级: {result['case_info'].level}")
            print(f"案由: {result['case_info'].case_type}")
            print(f"日期: {result['case_info'].date}")
            print(f"页数: {result['metadata']['pages']}")
            print(f"争议焦点数量: {len(result['sections'].dispute_focus)}")
            print("=" * 60)
    else:
        print(f"测试文件不存在: {test_pdf}")
