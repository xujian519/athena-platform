#!/usr/bin/env python3
"""
发明内容分块器
Content Chunker

支持发明内容的结构化分段（技术问题/技术方案/有益效果/具体实施方式）

作者: Athena平台团队
创建时间: 2025-12-25
"""

from __future__ import annotations
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ContentSection(Enum):
    """发明内容分段类型"""
    TECHNICAL_PROBLEM = "技术问题"        # 技术问题
    TECHNICAL_SOLUTION = "技术方案"      # 技术方案
    BENEFICIAL_EFFECT = "有益效果"        # 有益效果
    EMBODIMENT = "具体实施方式"          # 具体实施方式


@dataclass
class ContentChunk:
    """内容分块"""
    chunk_id: str               # 分块ID
    section_type: ContentSection  # 分段类型
    content: str                # 内容文本

    # 元数据
    patent_number: str
    chunk_index: int = 0        # 分块索引（同类型内的序号）
    total_chunks: int = 1       # 同类型总分块数

    # 统计信息
    char_count: int = 0
    word_count: int = 0
    sentence_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "chunk_id": self.chunk_id,
            "section_type": self.section_type.value,
            "content": self.content,
            "patent_number": self.patent_number,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "char_count": self.char_count,
            "word_count": self.word_count,
            "sentence_count": self.sentence_count
        }


@dataclass
class ChunkedContent:
    """分块结果"""
    patent_number: str
    success: bool

    # 各分段的分块
    technical_problems: list[ContentChunk] = field(default_factory=list)
    technical_solutions: list[ContentChunk] = field(default_factory=list)
    beneficial_effects: list[ContentChunk] = field(default_factory=list)
    embodiments: list[ContentChunk] = field(default_factory=list)

    # 统计信息
    total_chunk_count: int = 0
    processing_time: float = 0.0
    error_message: str | None = None

    @property
    def all_chunks(self) -> list[ContentChunk]:
        """获取所有分块"""
        return (
            self.technical_problems +
            self.technical_solutions +
            self.beneficial_effects +
            self.embodiments
        )

    def get_chunks_by_type(self, section_type: ContentSection) -> list[ContentChunk]:
        """按类型获取分块"""
        mapping = {
            ContentSection.TECHNICAL_PROBLEM: self.technical_problems,
            ContentSection.TECHNICAL_SOLUTION: self.technical_solutions,
            ContentSection.BENEFICIAL_EFFECT: self.beneficial_effects,
            ContentSection.EMBODIMENT: self.embodiments
        }
        return mapping.get(section_type, [])

    def get_summary(self) -> dict[str, Any]:
        """获取分块摘要"""
        return {
            "patent_number": self.patent_number,
            "success": self.success,
            "total_chunks": self.total_chunk_count,
            "technical_problem_count": len(self.technical_problems),
            "technical_solution_count": len(self.technical_solutions),
            "beneficial_effect_count": len(self.beneficial_effects),
            "embodiment_count": len(self.embodiments),
            "processing_time": self.processing_time
        }


class ContentChunker:
    """
    发明内容分块器

    支持功能:
    1. 按技术问题/方案/效果/实施方式分段
    2. 大文本自动分块（按句子/段落）
    3. 分块边界优化（避免句子截断）
    """

    # 分段标题模式
    SECTION_PATTERNS = {
        ContentSection.TECHNICAL_PROBLEM: [
            r'技术问题[：:]\s*',
            r'发明内容[：:]\s*[^技术]*技术问题[：:]\s*',
            r'要解决的技术问题[：:]\s*',
        ],
        ContentSection.TECHNICAL_SOLUTION: [
            r'技术方案[：:]\s*',
            r'解决方案[：:]\s*',
            r'发明内容[：:]\s*[^技术]*技术方案[：:]\s*',
        ],
        ContentSection.BENEFICIAL_EFFECT: [
            r'有益效果[：:]\s*',
            r'优点[：:]\s*',
            r'积极效果[：:]\s*',
            r'有益效果[：:]\s*',
        ],
        ContentSection.EMBODIMENT: [
            r'具体实施方式[：:]\s*',
            r'实施例[：:]\s*',
            r'实施方式[：:]\s*',
        ]
    }

    # 句子分割模式
    SENTENCE_PATTERN = re.compile(r'[^。！？.!?]+[。！？.!?]+\s*')

    # 段落分割模式
    PARAGRAPH_PATTERN = re.compile(r'\n\n+')

    def __init__(
        self,
        max_chunk_size: int = 500,
        min_chunk_size: int = 50,
        split_by: str = "sentence"  # sentence/paragraph
    ):
        """
        初始化分块器

        Args:
            max_chunk_size: 最大分块大小（字符数）
            min_chunk_size: 最小分块大小
            split_by: 分块方式（sentence=按句子, paragraph=按段落）
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.split_by = split_by

        # 编译所有分段模式
        self._compile_patterns()

    def _compile_patterns(self) -> Any:
        """编译正则表达式"""
        self.compiled_patterns = {}
        for section_type, patterns in self.SECTION_PATTERNS.items():
            self.compiled_patterns[section_type] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

    def chunk(self, patent_number: str, content_text: str) -> ChunkedContent:
        """
        对发明内容进行分块

        Args:
            patent_number: 专利号
            content_text: 发明内容全文

        Returns:
            ChunkedContent 分块结果
        """
        import time
        start_time = time.time()

        try:
            # 1. 分段
            sections = self._split_sections(content_text)

            # 2. 对每段进行分块
            result = ChunkedContent(
                patent_number=patent_number,
                success=True
            )

            for section_type, section_text in sections.items():
                chunks = self._chunk_section(
                    patent_number,
                    section_type,
                    section_text
                )

                if section_type == ContentSection.TECHNICAL_PROBLEM:
                    result.technical_problems = chunks
                elif section_type == ContentSection.TECHNICAL_SOLUTION:
                    result.technical_solutions = chunks
                elif section_type == ContentSection.BENEFICIAL_EFFECT:
                    result.beneficial_effects = chunks
                elif section_type == ContentSection.EMBODIMENT:
                    result.embodiments = chunks

            result.total_chunk_count = len(result.all_chunks)
            result.processing_time = time.time() - start_time

            logger.info(f"✅ 分块完成: {result.total_chunk_count}个分块")

            return result

        except Exception as e:
            logger.error(f"❌ 分块失败: {e}")
            return ChunkedContent(
                patent_number=patent_number,
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )

    def _split_sections(self, content_text: str) -> dict[ContentSection, str]:
        """
        分割发明内容为各个分段

        Returns:
            {section_type: section_text}
        """
        sections = {}
        content = content_text

        # 按顺序查找各个分段
        last_end = 0
        section_positions = []

        for section_type in [
            ContentSection.TECHNICAL_PROBLEM,
            ContentSection.TECHNICAL_SOLUTION,
            ContentSection.BENEFICIAL_EFFECT,
            ContentSection.EMBODIMENT
        ]:
            # 尝试所有模式
            for pattern in self.compiled_patterns[section_type]:
                match = pattern.search(content, last_end)
                if match:
                    section_positions.append((match.start(), section_type))
                    last_end = match.end()
                    break

        # 提取各分段内容
        for i, (start, section_type) in enumerate(section_positions):
            end = section_positions[i + 1][0] if i + 1 < len(section_positions) else len(content)
            section_text = content[start:end].strip()

            # 去除标题
            for pattern in self.compiled_patterns[section_type]:
                section_text = pattern.sub('', section_text, count=1).strip()

            if section_text:
                sections[section_type] = section_text

        return sections

    def _chunk_section(
        self,
        patent_number: str,
        section_type: ContentSection,
        section_text: str
    ) -> list[ContentChunk]:
        """
        对单个分段进行分块

        Args:
            patent_number: 专利号
            section_type: 分段类型
            section_text: 分段文本

        Returns:
            List[ContentChunk]
        """
        chunks = []

        # 如果文本小于最大块大小，不分块
        if len(section_text) <= self.max_chunk_size:
            chunk = self._create_chunk(
                patent_number,
                section_type,
                section_text,
                0,
                1
            )
            chunks.append(chunk)
            return chunks

        # 根据分块方式分割
        if self.split_by == "paragraph":
            pieces = self._split_by_paragraphs(section_text)
        else:  # sentence
            pieces = self._split_by_sentences(section_text)

        # 合并小块
        chunks_text = self._merge_chunks(pieces)

        # 创建分块对象
        for i, chunk_text in enumerate(chunks_text):
            chunk = self._create_chunk(
                patent_number,
                section_type,
                chunk_text,
                i,
                len(chunks_text)
            )
            chunks.append(chunk)

        return chunks

    def _split_by_sentences(self, text: str) -> list[str]:
        """按句子分割"""
        sentences = self.SENTENCE_PATTERN.findall(text)
        return [s.strip() for s in sentences if s.strip()]

    def _split_by_paragraphs(self, text: str) -> list[str]:
        """按段落分割"""
        paragraphs = self.PARAGRAPH_PATTERN.split(text)
        return [p.strip() for p in paragraphs if p.strip()]

    def _merge_chunks(self, pieces: list[str]) -> list[str]:
        """
        合并小块到合适的大小

        策略:
        1. 将小块合并直到接近max_chunk_size
        2. 避免在句子中间断开
        """
        chunks = []
        current_chunk = ""
        current_size = 0

        for piece in pieces:
            piece_size = len(piece)

            # 如果当前块+新块不超过最大大小，合并
            if current_size + piece_size <= self.max_chunk_size:
                current_chunk += piece
                current_size += piece_size
            else:
                # 当前块已满，保存
                if current_chunk:
                    chunks.append(current_chunk)

                # 开始新块
                current_chunk = piece
                current_size = piece_size

        # 保存最后一个块
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _create_chunk(
        self,
        patent_number: str,
        section_type: ContentSection,
        content: str,
        index: int,
        total: int
    ) -> ContentChunk:
        """创建分块对象"""
        # 统计信息
        char_count = len(content)
        word_count = len(content.replace(' ', ''))
        sentence_count = len(self.SENTENCE_PATTERN.findall(content))

        chunk_id = f"{patent_number}_{section_type.value}_{index}"

        return ContentChunk(
            chunk_id=chunk_id,
            section_type=section_type,
            content=content,
            patent_number=patent_number,
            chunk_index=index,
            total_chunks=total,
            char_count=char_count,
            word_count=word_count,
            sentence_count=sentence_count
        )


# ========== 便捷函数 ==========

def chunk_content(
    patent_number: str,
    content_text: str,
    **kwargs
) -> ChunkedContent:
    """
    对发明内容进行分块

    Args:
        patent_number: 专利号
        content_text: 发明内容全文
        **kwargs: 传递给ContentChunker的参数

    Returns:
        ChunkedContent 分块结果
    """
    chunker = ContentChunker(**kwargs)
    return chunker.chunk(patent_number, content_text)


# ========== 示例使用 ==========

def main() -> None:
    """示例使用"""
    print("=" * 70)
    print("发明内容分块器 示例")
    print("=" * 70)

    # 示例发明内容
    sample_content = """
    发明内容：

    技术问题：现有图像识别方法在处理复杂场景时精度较低，计算效率不高，
    难以满足实时性要求。

    技术方案：本发明提供一种基于深度学习的图像识别方法，包括：
    构建卷积神经网络模型，所述模型包括特征提取层、注意力机制模块和
    分类输出层；
    获取待识别图像，输入到所述卷积神经网络模型；
    通过所述特征提取层提取图像的多层特征；
    通过所述注意力机制模块对所述多层特征进行加权融合；
    通过所述分类输出层输出分类结果。

    有益效果：与现有技术相比，本发明具有以下优点：
    1. 通过注意力机制提高了特征提取的有效性，识别准确率提升15%；
    2. 模型参数量减少30%，计算速度提高50%；
    3. 对复杂场景的适应性更强。

    具体实施方式：下面结合附图和具体实施例对本发明进行详细说明。
    实施例1：如图1所示，一种基于深度学习的图像识别方法，
    包括以下步骤：
    步骤S1：获取待识别图像...
    步骤S2：构建卷积神经网络模型...
    （详细实施步骤省略）
    """

    # 分块
    result = chunk_content("CN112233445A", sample_content)

    print("\n📋 分块结果:")
    summary = result.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    print("\n📄 各分段的分块:")
    for section_type in ContentSection:
        chunks = result.get_chunks_by_type(section_type)
        if chunks:
            print(f"\n{section_type.value} ({len(chunks)}个分块):")
            for chunk in chunks:
                print(f"  [{chunk.chunk_index + 1}/{chunk.total_chunks}] "
                      f"{chunk.char_count}字, {chunk.sentence_count}句")
                print(f"    {chunk.content[:80]}...")


if __name__ == "__main__":
    main()
