#!/usr/bin/env python3
"""
PDF深度分析器 - 完整提取专利文档信息
PDF Deep Analyzer - Complete Patent Document Extraction

Author: Athena平台团队
Created: 2026-01-26
Version: v1.0.0
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

try:
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logging.warning("PyMuPDF未安装，PDF分析功能受限")

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

logger = logging.getLogger(__name__)


class PDFDeepAnalyzer:
    """
    PDF深度分析器

    功能：
    1. 提取专利元数据（专利号、标题、摘要）
    2. 提取技术方案（技术领域、背景技术、发明内容）
    3. 提取具体实施方式（实施例、参数）
    4. 提取权利要求（独立/从属权利要求）
    5. 提取技术效果（有益效果、技术优势）
    """

    def __init__(self, parser_factory=None):
        """初始化分析器

        Args:
            parser_factory: 可选的DocumentParserFactory实例，
                           传入后对扫描型PDF自动使用MinerU解析。
                           不传时行为与原来完全一致。
        """
        if not PDF_AVAILABLE:
            raise RuntimeError("需要安装PyMuPDF: pip install PyMuPDF")
        self._parser_factory = parser_factory
        logger.info("✅ PDF深度分析器初始化完成")

    def analyze_patent_pdf(self, pdf_path: str) -> dict[str, Any]:
        """
        深度分析专利PDF文件

        Args:
            pdf_path: PDF文件路径

        Returns:
            分析结果字典，包含：
            {
                "file_name": "CN112616756A.pdf",
                "patent_number": "CN112616756A",
                "title": "商品成鱼瘦身加工养殖系统",
                "abstract": "摘要全文",
                "technical_field": "技术领域描述",
                "background_art": "背景技术",
                "summary": "发明内容",
                "embodiments": [...],
                "claims": [...],
                "technical_effects": [...],
                "key_parameters": {...}
            }
        """
        logger.info(f"🔍 开始分析PDF: {pdf_path}")

        # 1. 提取完整文本
        full_text = self._extract_full_text(pdf_path)

        # 2. 提取元数据
        patent_number = self._extract_patent_number(pdf_path, full_text)
        title = self._extract_title(full_text)

        # 3. 提取摘要
        abstract = self._extract_abstract(full_text)

        # 4. 提取技术方案
        technical_field = self._extract_section(full_text, "技术领域")
        background_art = self._extract_section(full_text, "背景技术")
        summary = self._extract_section(full_text, ["发明内容", "内容摘要"])

        # 5. 提取具体实施方式
        embodiments = self._extract_embodiments(full_text)

        # 6. 提取权利要求
        claims = self._extract_claims(full_text)

        # 7. 提取技术效果
        effects = self._extract_technical_effects(full_text)

        # 8. 提取关键参数
        parameters = self._extract_parameters(full_text)

        # 9. 提取结构化表格
        tables = self._extract_tables(pdf_path)

        result = {
            "file_name": Path(pdf_path).name,
            "patent_number": patent_number,
            "title": title,
            "abstract": abstract,
            "technical_field": technical_field,
            "background_art": background_art,
            "summary": summary,
            "embodiments": embodiments,
            "claims": claims,
            "technical_effects": effects,
            "key_parameters": parameters,
            "tables": tables,
        }

        logger.info(f"✅ PDF分析完成: {title}")
        logger.info(
            f"   权要求数: {len(claims)}, 实施例数: {len(embodiments)}, "
            f"表格数: {len(tables)}"
        )

        return result

    def _extract_full_text(self, pdf_path: str) -> str:
        """提取PDF完整文本

        优先使用PyMuPDF提取文本层。当文本层内容不足（扫描型PDF）
        且配置了parser_factory时，自动调用MinerU进行OCR解析。
        """
        with fitz.open(pdf_path) as doc:
            text_parts = []
            total_pages = len(doc)
            for page in doc:
                text = page.get_text()
                if text.strip():
                    text_parts.append(text)
        text = "\n".join(text_parts)

        # 文本层内容不足 + 有parser_factory → 尝试MinerU/Tesseract
        if len(text.strip()) < 100 and self._parser_factory and total_pages > 0:
            logger.info("PDF文本层不足(%d字符/%d页)，尝试文档解析服务", len(text.strip()), total_pages)
            try:
                from core.document_parser.base import ParseRequest
                from core.document_parser.parser_factory import run_async_safe

                factory = self._parser_factory
                request = ParseRequest(file_path=pdf_path)
                result = run_async_safe(factory.parse(request))
                if result.content and not result.error:
                    logger.info("文档解析服务成功: backend=%s, %d字符", result.backend_used, len(result.content))
                    return result.content
                else:
                    logger.warning("文档解析服务失败: %s", result.error)
            except Exception as e:
                logger.warning("文档解析服务异常: %s", e)

        return text

    def _extract_patent_number(self, pdf_path: str, text: str) -> str:
        """从文件名或文本中提取专利号"""
        # 优先从文件名提取
        filename = Path(pdf_path).stem
        if re.match(r'CN\d+[A-Z]', filename):
            return filename

        # 从文本开头提取（通常在第一页）
        patterns = [
            r'CN\d{7,9}[A-Z]',  # CN专利号
            r'US\d+[A-Z]?',     # US专利号
            r'EP\d+[A-Z]?',     # EP专利号
        ]

        for pattern in patterns:
            match = re.search(pattern, text[:500])
            if match:
                return match.group(0)

        return "未知专利号"

    def _extract_title(self, text: str) -> str:
        """提取发明名称"""
        patterns = [
            r'发明名称[：:]\s*(.+?)(?:\n|【)',
            r'标题[：:]\s*(.+?)(?:\n|【)',
            r'名称[：:]\s*(.+?)(?:\n|【)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text[:1000])
            if match:
                title = match.group(1).strip()
                # 清理标题
                title = re.sub(r'【.*?】', '', title)  # 移除【】标记
                return title[:100]  # 限制长度

        # 如果没有找到，尝试从摘要或开头提取
        lines = text.split('\n')[:10]
        for line in lines:
            if len(line) > 10 and len(line) < 80:
                # 可能是标题
                if not any(x in line for x in ['摘要', '权利要求', '发明内容']):
                    return line.strip()

        return "未知标题"

    def _extract_abstract(self, text: str) -> str:
        """提取摘要"""
        # 查找摘要部分
        section_match = re.search(
            r'摘要[：:：]?\s*(.+?)(?:【|权利要求书|技术领域|$)',
            text,
            re.DOTALL
        )

        if section_match:
            abstract = section_match.group(1).strip()
            # 清理摘要
            abstract = re.sub(r'\n+', ' ', abstract)  # 替换换行为空格
            abstract = re.sub(r'\s+', ' ', abstract)  # 合并多余空格
            return abstract[:500]  # 限制长度

        return ""

    def _extract_section(self, text: str, section_names) -> str:
        """
        提取指定章节内容

        Args:
            text: 完整文本
            section_names: 章节名称（字符串或列表）
        """
        if isinstance(section_names, str):
            section_names = [section_names]

        for section_name in section_names:
            pattern = rf'{section_name}[：:：]?\s*(.+?)(?=\n\n[【\[]|权利要求书|具体实施方式|$)'
            match = re.search(pattern, text, re.DOTALL)
            if match:
                content = match.group(1).strip()
                # 清理内容
                content = re.sub(r'\n+', ' ', content)
                content = re.sub(r'\s+', ' ', content)
                return content[:1000]  # 限制长度

        return ""

    def _extract_embodiments(self, text: str) -> list[dict[str, Any]:
        """提取具体实施方式"""
        embodiments = []

        # 查找实施例部分
        section_match = re.search(
            r'具体实施方式[：:：]?\s*(.+?)(?=\n\n[【\[]|$)',
            text,
            re.DOTALL
        )

        if not section_match:
            return embodiments

        embodiments_text = section_match.group(1)

        # 提取各个实施例
        # 匹配模式：实施例一、实施例1、图1等
        patterns = [
            r'(?:实施例|具体实施方式)[一二三四五六七八九十\d]+[：:：]?\s*(.+?)(?=(?:实施例|具体实施方式)[一二三四五六七八九十\d]+|$)',
            r'图\d+[：:：]?\s*(.+?)(?=\n图\d+|$)',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, embodiments_text, re.DOTALL)

            for i, match in enumerate(matches, 1):
                embodiment_text = match.group(1).strip()

                if len(embodiment_text) > 50:  # 过滤太短的匹配
                    # 提取参数
                    parameters = self._extract_parameters(embodiment_text)

                    embodiments.append({
                        "example_number": i,
                        "description": embodiment_text[:500],  # 限制长度
                        "technical_parameters": parameters
                    })

                    if len(embodiments) >= 10:  # 最多10个实施例
                        break

            if embodiments:
                break

        return embodiments

    def _extract_claims(self, text: str) -> list[dict[str, Any]:
        """提取权利要求"""
        claims = []

        # 查找权利要求书部分
        claims_section = re.search(
            r'权利要求书[：:：]?\s*(.+?)(?=\n\n[【\[]|说明书|附图说明|$)',
            text,
            re.DOTALL
        )

        if not claims_section:
            return claims

        claims_text = claims_section.group(1)

        # 提取各个权利要求
        # 匹配模式：1. xxxxxx 或 1、xxxxxx
        claim_pattern = r'(\d+)[.、　]\s*(.+?)(?=\n\d+[.、]|$)'
        matches = re.finditer(claim_pattern, claims_text, re.MULTILINE)

        for match in matches:
            claim_num = match.group(1)
            claim_content = match.group(2).strip()

            # 清理权利要求内容
            claim_content = re.sub(r'\s+', ' ', claim_content)  # 合并空格
            claim_content = claim_content[:300]  # 限制长度

            if len(claim_content) > 20:  # 过滤太短的
                # 提取技术特征
                features = self._extract_technical_features(claim_content)

                claims.append({
                    "claim_number": int(claim_num),
                    "claim_type": "dependent" if "根据权利要求" in claim_content else "independent",
                    "content": claim_content,
                    "technical_features": features
                })

                if len(claims) >= 20:  # 最多20个权利要求
                    break

        return claims

    def _extract_technical_features(self, claim_text: str) -> list[str]:
        """从权利要求中提取技术特征"""
        features = []

        # 按照分隔符分割
        separators = r'[，。；；,;\n]'
        parts = re.split(separators, claim_text)

        for part in parts:
            part = part.strip()
            # 过滤过短或过长的部分
            if 5 < len(part) < 100:
                # 移除序号前缀
                part = re.sub(r'^其中|^其特征在于|^所述', '', part)
                if part:
                    features.append(part)

        return features[:10]  # 最多10个特征

    def _extract_technical_effects(self, text: str) -> list[str]:
        """提取技术效果"""
        effects = []

        # 查找有益效果/技术效果部分
        effect_section = self._extract_section(text, ["有益效果", "技术效果", "优点"])

        if effect_section:
            # 从效果部分提取
            sentences = re.split(r'[。；；]', effect_section)
            for sentence in sentences:
                sentence = sentence.strip()
                if 10 < len(sentence) < 100:
                    effects.append(sentence)

        # 如果没有找到足够的效果，从全文搜索
        if len(effects) < 3:
            effect_patterns = [
                r'(?:能够|可以|实现|具有)[：:：]?\s*([^，。；;\n]{10,100})',
                r'(?:改善|提升|增强|促进)[：:：]?\s*([^，。；;\n]{10,100})',
            ]

            for pattern in effect_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    effect = match.group(1).strip()
                    if effect and effect not in effects:
                        effects.append(effect)
                        if len(effects) >= 10:
                            break

                if len(effects) >= 10:
                    break

        return effects[:10]  # 最多10个效果

    def _extract_parameters(self, text: str) -> dict[str, Any]:
        """提取关键参数"""
        parameters = {}

        # 1. 温度参数
        temp_patterns = [
            r'(\d+[\-～至—]\d+)[℃度]',  # 范围温度：15-25℃
            r'(\d+)℃',  # 单点温度
            r'(\d+)度',  # 中文温度
        ]

        for pattern in temp_patterns:
            matches = re.findall(pattern, text)
            if matches:
                parameters["temperature"] = matches[0]
                break

        # 2. 时间参数
        time_patterns = [
            r'(\d+[\-～至—]\d+)[天日月小时min分]',  # 范围时间
            r'(\d+)[天日月小时min分]',  # 单点时间
        ]

        for pattern in time_patterns:
            matches = re.findall(pattern, text)
            if matches:
                parameters["duration"] = matches[0]
                break

        # 3. 百分比参数
        percent_pattern = r'(\d+(?:\.\d+)?)[%％]'
        percents = re.findall(percent_pattern, text)
        if percents:
            parameters["percentages"] = percents[:5]  # 最多5个

        # 4. 浓度/比例参数
        concentration_patterns = [
            r'(\d+(?:\.\d+)?)[%％]\s*(?:以上|以下|左右)?',
            r'(\d+(?:\.\d+)?)\s*[g克kg毫升ml]',  # 重量/体积
        ]

        for pattern in concentration_patterns:
            matches = re.findall(pattern, text)
            if matches:
                parameters["concentrations"] = matches[:3]
                break

        # 5. 速度/速率参数
        speed_patterns = [
            r'(\d+(?:\.\d+)?)\s*[m米km千米]/[s秒h小时min分]',
            r'(\d+(?:\.\d+)?)\s*rpm',
        ]

        for pattern in speed_patterns:
            matches = re.findall(pattern, text)
            if matches:
                parameters["speed"] = matches[0]
                break

        return parameters

    def _extract_tables(self, pdf_path: str) -> list[dict[str, Any]:
        """使用pdfplumber提取PDF中的结构化表格"""
        if not HAS_PDFPLUMBER:
            logger.debug("pdfplumber未安装，跳过表格提取")
            return []

        tables: list[dict[str, Any] = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_tables = page.extract_tables()
                    for table_data in page_tables:
                        if not table_data:
                            continue
                        has_content = any(
                            any(cell and cell.strip() for cell in row)
                            for row in table_data
                        )
                        if not has_content:
                            continue
                        tables.append({
                            "table_index": len(tables) + 1,
                            "page_number": page_num,
                            "rows": [
                                [cell.strip() if cell else "" for cell in row]
                                for row in table_data
                            ],
                            "header": (
                                [cell.strip() if cell else "" for cell in table_data[0]
                                if table_data
                                else None
                            ),
                            "row_count": len(table_data),
                            "col_count": max(len(row) for row in table_data) if table_data else 0,
                            "source": "pdf",
                        })
        except Exception as e:
            logger.warning(f"表格提取失败: {e}")

        return tables

    def analyze_batch(self, pdf_paths: list[str]) -> dict[str, dict]:
        """
        批量分析PDF文件

        Args:
            pdf_paths: PDF文件路径列表

        Returns:
            分析结果字典 {pdf_path: analysis_result}
        """
        logger.info(f"📊 批量分析 {len(pdf_paths)} 个PDF文件")

        results = {}
        for i, pdf_path in enumerate(pdf_paths, 1):
            logger.info(f"进度: {i}/{len(pdf_paths)} - {Path(pdf_path).name}")
            try:
                results[pdf_path] = self.analyze_patent_pdf(pdf_path)
            except Exception as e:
                logger.error(f"分析失败: {pdf_path} - {e}")
                results[pdf_path] = {"error": str(e)}

        logger.info(f"✅ 批量分析完成: 成功 {len(results)} 个")
        return results


# 便捷函数
def get_pdf_deep_analyzer() -> PDFDeepAnalyzer:
    """获取PDF深度分析器单例"""
    return PDFDeepAnalyzer()


# 测试代码
if __name__ == "__main__":
    # 测试单个PDF分析
    analyzer = get_pdf_deep_analyzer()

    test_pdf = "data/temp_oa_analysis/对比文件1_CN112616756A.pdf"
    if Path(test_pdf).exists():
        result = analyzer.analyze_patent_pdf(test_pdf)

        print("\n=== PDF分析结果 ===")
        print(f"专利号: {result['patent_number']}")
        print(f"标题: {result['title']}")
        print(f"技术领域: {result['technical_field'][:100]}...")
        print(f"权利要求数: {len(result['claims'])}")
        print(f"实施例数: {len(result['embodiments'])}")
        print(f"技术效果数: {len(result['technical_effects'])}")
        print(f"关键参数: {result['key_parameters']}")
