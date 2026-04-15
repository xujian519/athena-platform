#!/usr/bin/env python3
"""
PDF文本提取模块
支持中英文专利PDF的文本提取，保留结构化信息

作者: Athena平台团队
创建时间: 2025-12-24
"""

from __future__ import annotations
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

# 尝试导入PDF处理库
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class PatentPDFContent:
    """专利PDF内容提取结果"""
    patent_number: str
    file_path: str
    file_size: int

    # 文本内容
    full_text: str
    title: str
    abstract: str
    claims: str
    description: str

    # 元数据
    extraction_method: str
    pages_count: int
    language: str  # zh, en, mixed

    # 统计信息
    char_count: int
    word_count: int


class PDFExtractor:
    """PDF文本提取器"""

    def __init__(self, preferred_method: str = "pdfplumber"):
        """
        初始化PDF提取器

        Args:
            preferred_method: 首选方法 (pdfplumber, pypdf2, auto)
        """
        self.preferred_method = preferred_method
        self._check_dependencies()

    def _check_dependencies(self) -> Any:
        """检查依赖库"""
        available_methods = []
        if PDFPLUMBER_AVAILABLE:
            available_methods.append("pdfplumber")
        if PYPDF2_AVAILABLE:
            available_methods.append("pypdf2")

        if not available_methods:
            raise ImportError(
                "需要安装PDF处理库: pip install pdfplumber PyPDF2"
            )

        self.available_methods = available_methods
        logger.info(f"✅ 可用的PDF提取方法: {', '.join(available_methods)}")

    def extract(self, pdf_path: str) -> PatentPDFContent:
        """
        提取PDF内容

        Args:
            pdf_path: PDF文件路径

        Returns:
            PatentPDFContent: 提取的内容
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        patent_number = pdf_path.stem
        file_size = pdf_path.stat().st_size

        logger.info(f"📄 开始提取PDF: {patent_number}")

        # 选择提取方法
        method = self._select_method()

        # 提取内容
        if method == "pdfplumber":
            content = self._extract_with_pdfplumber(pdf_path)
        else:
            content = self._extract_with_pypdf2(pdf_path)

        # 补充元数据
        content.patent_number = patent_number
        content.file_path = str(pdf_path)
        content.file_size = file_size
        content.char_count = len(content.full_text)
        content.word_count = len(content.full_text.split())

        # 检测语言
        content.language = self._detect_language(content.full_text)

        logger.info(f"✅ 提取完成: {content.pages_count}页, {content.char_count}字符")
        logger.info(f"   语言: {content.language}, 方法: {method}")

        return content

    def _select_method(self) -> str:
        """选择提取方法"""
        if self.preferred_method == "auto":
            return self.available_methods[0]
        if self.preferred_method in self.available_methods:
            return self.preferred_method
        return self.available_methods[0]

    def _extract_with_pdfplumber(self, pdf_path: Path) -> PatentPDFContent:
        """使用pdfplumber提取（推荐，更好的中文支持）"""
        import pdfplumber

        full_text_parts = []
        pages_count = 0

        try:
            with pdfplumber.open(pdf_path) as pdf:
                pages_count = len(pdf.pages)

                for _page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        full_text_parts.append(text)
        except Exception as e:
            logger.error(f"❌ 使用pdfplumber提取PDF失败: {e}")
            # 返回空内容
            return PatentPDFContent(
                patent_number="",
                file_path=str(pdf_path),
                file_size=pdf_path.stat().st_size if pdf_path.exists() else 0,
                full_text="",
                title="",
                abstract="",
                claims="",
                description="",
                extraction_method="pdfplumber",
                pages_count=0,
                language="",
                char_count=0,
                word_count=0
            )

        full_text = "\n".join(full_text_parts)

        # 解析结构化内容
        content = PatentPDFContent(
            patent_number="",
            file_path="",
            file_size=0,
            full_text=full_text,
            title=self._extract_title(full_text),
            abstract=self._extract_abstract(full_text),
            claims=self._extract_claims(full_text),
            description=self._extract_description(full_text),
            extraction_method="pdfplumber",
            pages_count=pages_count,
            language="",
            char_count=0,
            word_count=0
        )

        return content

    def _extract_with_pypdf2(self, pdf_path: Path) -> PatentPDFContent:
        """使用PyPDF2提取"""
        import PyPDF2

        full_text_parts = []
        pages_count = 0

        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            pages_count = len(pdf_reader.pages)

            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    full_text_parts.append(text)

        full_text = "\n".join(full_text_parts)

        content = PatentPDFContent(
            patent_number="",
            file_path="",
            file_size=0,
            full_text=full_text,
            title=self._extract_title(full_text),
            abstract=self._extract_abstract(full_text),
            claims=self._extract_claims(full_text),
            description=self._extract_description(full_text),
            extraction_method="pypdf2",
            pages_count=pages_count,
            language="",
            char_count=0,
            word_count=0
        )

        return content

    def _extract_title(self, full_text: str) -> str:
        """提取标题（专利名称）"""
        lines = full_text.split('\n')

        # 通常标题在前几行，取前3行中最长的非空行
        for i in range(min(3, len(lines))):
            line = lines[i].strip()
            if len(line) > 10 and len(line) < 200:
                return line

        return ""

    def _extract_abstract(self, full_text: str) -> str:
        """提取摘要"""
        # 中文摘要关键词
        zh_keywords = ['摘要', '【摘要】', '技术领域']
        # 英文摘要关键词
        en_keywords = ['Abstract', 'ABSTRACT', 'SUMMARY']

        # 查找摘要部分
        for keyword in zh_keywords + en_keywords:
            idx = full_text.find(keyword)
            if idx != -1:
                # 提取摘要部分（通常在关键词后500-1000字符）
                abstract_part = full_text[idx:idx+1500]
                # 移除关键词本身
                for kw in zh_keywords + en_keywords:
                    abstract_part = abstract_part.replace(kw, '')
                # 截取到段落结束或下一个章节
                lines = abstract_part.split('\n')
                abstract_lines = []
                for line in lines[:20]:  # 最多取20行
                    line = line.strip()
                    if not line:
                        continue
                    # 遇到新的章节标题就停止
                    if any(kw in line for kw in ['权利要求', 'Claims', '说明书', 'Description']):
                        break
                    abstract_lines.append(line)
                    if len('\n'.join(abstract_lines)) > 1000:
                        break

                return '\n'.join(abstract_lines).strip()

        return ""

    def _extract_claims(self, full_text: str) -> str:
        """提取权利要求书"""
        # 权利要求关键词
        start_keywords = ['权利要求书', '【权利要求书】', 'Claims', 'CLAIMS', 'What is claimed']
        end_keywords = ['说明书', '【说明书】', 'Description', 'Detailed Description']

        start_idx = -1
        for keyword in start_keywords:
            idx = full_text.find(keyword)
            if idx != -1:
                start_idx = idx
                break

        if start_idx == -1:
            return ""

        # 查找结束位置
        end_idx = len(full_text)
        for keyword in end_keywords:
            idx = full_text.find(keyword, start_idx)
            if idx != -1:
                end_idx = idx
                break

        claims_text = full_text[start_idx:end_idx]

        # 清理和格式化
        lines = claims_text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line:
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def _extract_description(self, full_text: str) -> str:
        """提取说明书"""
        # 说明书关键词
        keywords = ['说明书', '【说明书】', 'Description', 'DETAILED DESCRIPTION']

        for keyword in keywords:
            idx = full_text.find(keyword)
            if idx != -1:
                # 从说明书开始到文档结束
                return full_text[idx:].strip()

        # 如果没有找到说明书关键词，返回剩余文本
        return full_text

    def _detect_language(self, text: str) -> str:
        """检测文本语言"""
        # 统计中文字符
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        # 统计英文字符
        english_chars = len(re.findall(r'[a-z_a-Z]', text))

        total = chinese_chars + english_chars
        if total == 0:
            return "unknown"

        chinese_ratio = chinese_chars / total
        english_ratio = english_chars / total

        if chinese_ratio > 0.3:
            return "zh"  # 中文
        elif english_ratio > 0.7:
            return "en"  # 英文
        else:
            return "mixed"  # 中英混合


def batch_extract(pdf_dir: str, pattern: str = "*.pdf") -> list[PatentPDFContent]:
    """
    批量提取PDF

    Args:
        pdf_dir: PDF目录
        pattern: 文件匹配模式

    Returns:
        List[PatentPDFContent]: 提取结果列表
    """
    pdf_dir = Path(pdf_dir)
    pdf_files = list(pdf_dir.glob(pattern))

    logger.info(f"📦 批量提取PDF: {len(pdf_files)}个文件")

    extractor = PDFExtractor()
    results = []

    for i, pdf_file in enumerate(pdf_files, 1):
        try:
            logger.info(f"\n[{i}/{len(pdf_files)}] {pdf_file.name}")
            content = extractor.extract(str(pdf_file))
            results.append(content)
        except Exception as e:
            logger.error(f"❌ 提取失败: {pdf_file.name} - {e}")

    # 输出统计
    logger.info("\n" + "=" * 70)
    logger.info("批量提取统计")
    logger.info("=" * 70)
    logger.info(f"总计: {len(pdf_files)}")
    logger.info(f"成功: {len(results)}")
    logger.info(f"失败: {len(pdf_files) - len(results)}")
    logger.info(f"成功率: {len(results)/len(pdf_files)*100:.1f}%")

    # 语言统计
    lang_stats = {}
    for r in results:
        lang_stats[r.language] = lang_stats.get(r.language, 0) + 1
    logger.info("\n语言分布:")
    for lang, count in lang_stats.items():
        logger.info(f"  {lang}: {count}")

    return results


# ==================== 示例使用 ====================

def main() -> None:
    """示例使用"""
    # 示例1: 提取单个PDF
    extractor = PDFExtractor()

    # 查找测试PDF
    test_pdfs = list(Path("/Users/xujian/apps/apps/patents/PDF/CN").glob("*.pdf"))
    if test_pdfs:
        test_pdf = test_pdfs[0]
        print(f"\n{'=' * 70}")
        print(f"测试PDF提取: {test_pdf.name}")
        print('=' * 70)

        content = extractor.extract(str(test_pdf))

        print("\n📋 基本信息:")
        print(f"   专利号: {content.patent_number}")
        print(f"   文件大小: {content.file_size:,} bytes")
        print(f"   页数: {content.pages_count}")
        print(f"   语言: {content.language}")
        print(f"   提取方法: {content.extraction_method}")

        print("\n📝 内容长度:")
        print(f"   全文: {content.char_count} 字符")
        print(f"   标题: {len(content.title)} 字符")
        print(f"   摘要: {len(content.abstract)} 字符")
        print(f"   权利要求: {len(content.claims)} 字符")
        print(f"   说明书: {len(content.description)} 字符")

        if content.title:
            print(f"\n🏷️  标题: {content.title}")

        if content.abstract:
            abstract_preview = content.abstract[:200] + "..." if len(content.abstract) > 200 else content.abstract
            print(f"\n📄 摘要预览: {abstract_preview}")

    # 示例2: 批量提取（注释掉，避免长时间运行）
    # results = batch_extract("/Users/xujian/apps/apps/patents/PDF/CN")


if __name__ == "__main__":
    main()
