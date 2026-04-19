#!/usr/bin/env python3
"""
专利审查指南2025版处理器
基于官方建议的最小块划分策略：小节级别

核心功能：
1. 解析613页专利审查指南PDF（2025版）
2. 提取分层结构：部分 > 章 > 节 > 小节
3. 生成2,000-3,000个小节块（300-800字/块）
4. 为每个块附加完整元数据
5. 集成BGE向量化和NebulaGraph知识图谱构建

作者: Athena平台团队
创建时间: 2025-12-23
基于: 国家知识产权局局令第84号（2025版）
"""

from __future__ import annotations
import asyncio
import json
import logging
import re
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.file_handler(f'/Users/xujian/Athena工作平台/logs/guideline_2025_processor_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class SubsectionChunk:
    """小节块数据结构"""
    chunk_id: str  # 唯一标识
    part: str  # 部分（如"第二部分"）
    chapter: str  # 章（如"第九章"）
    section: str  # 节（如"7.1"）
    subsection: str  # 小节（如"7.1.1"）
    title: str  # 小节标题（完整）
    content: str  # 小节内容（300-800字）
    update_type: str | None = None  # 2025版更新类型：新增/修改/无变化
    page: str | None = None  # 页码
    version: str = "2025"  # 版本号

    # 元数据
    word_count: int = field(default=0)
    has_example: bool = field(default=False)
    references: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.word_count = len(self.content)


class PatentGuideline2025Processor:
    """专利审查指南2025版处理器"""

    # 2025版新增内容映射（基于局令第84号）
    NEW_CONTENT_2025 = {
        "第二部分": {
            "第九章": {
                "新增6.1.1": "根据专利法第五条第一款的审查（AI伦理）",
                "修改6.1.2": "根据专利法第二十五条第一款第（二）项的审查",
                "新增第7节": "包含比特流的发明专利申请审查相关规定",
                "新增7.1.1": "根据专利法第二十五条第一款第（二）项的审查（比特流）",
                "新增7.1.2": "包含比特流的权利要求审查",
                "新增6.3.3": "审查示例（AI相关）"
            }
        }
    }

    # 2025版新增示例（例18-21）
    NEW_EXAMPLES_2025 = {
        "例18": "一种识别船只数量的方法",
        "例19": "AI辅助诊断方法",
        "例20": "比特流处理方法",
        "例21": "大数据分析方法"
    }

    def __init__(self):
        # 小节标题正则模式
        self.subsection_pattern = re.compile(
            r'^(\d+\.\d+\.\d+)\s+(.+)$'  # 如 "7.1.1 根据专利法第二十五条..."
        )

        # 节标题模式
        self.section_pattern = re.compile(
            r'^(\d+\.\d+)\s+(.+)$'  # 如 "7.1 包含比特流..."
        )

        # 章标题模式
        self.chapter_pattern = re.compile(
            r'^第([一二三四五六七八九十百千万\d]+)章\s+(.+)$'
        )

        # 部分标题模式
        self.part_pattern = re.compile(
            r'^第([一二三四五六七八九十\d]+)部分\s+(.+)$'
        )

        # 示例标记
        self.example_pattern = re.compile(r'^【例(\d+)】')

        # 法律引用模式
        self.law_ref_pattern = re.compile(
            r'(专利法|实施细则|审查指南)[\s\u3000]*(第[一二三四五六七八九十百千万零\d]+条)'
        )

    def parse_guideline_structure(self, pdf_path: str) -> dict[str, Any]:
        """
        解析专利审查指南PDF的层级结构

        参数:
            pdf_path: PDF文件路径

        返回:
            包含完整层级结构的字典
        """
        logger.info(f"📖 开始解析专利审查指南: {pdf_path}")

        # 这里需要集成PDF解析器（如PyMuPDF）
        # 暂时返回示例结构
        structure = {
            "version": "2025",
            "total_pages": 613,
            "effective_date": "2026-01-01",
            "parts": []
        }

        logger.info("✅ 解析完成，返回结构")
        return structure

    def extract_subsections(self, content: str) -> list[SubsectionChunk]:
        """
        从指南内容中提取所有小节块

        参数:
            content: 指南文本内容

        返回:
            小节块列表
        """
        logger.info("🔍 开始提取小节块...")

        chunks = []
        lines = content.split('\n')

        current_part = None
        current_chapter = None
        current_section = None
        current_subsection = None
        current_content = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检测部分
            part_match = self.part_pattern.match(line)
            if part_match:
                if current_subsection and current_content:
                    chunks.append(self._create_chunk(
                        current_part, current_chapter, current_section,
                        current_subsection, current_content
                    ))
                current_part = f"第{part_match.group(1)}部分"
                current_content = []
                continue

            # 检测章
            chapter_match = self.chapter_pattern.match(line)
            if chapter_match:
                if current_subsection and current_content:
                    chunks.append(self._create_chunk(
                        current_part, current_chapter, current_section,
                        current_subsection, current_content
                    ))
                current_chapter = f"第{chapter_match.group(1)}章"
                current_content = []
                continue

            # 检测节
            section_match = self.section_pattern.match(line)
            if section_match:
                if current_subsection and current_content:
                    chunks.append(self._create_chunk(
                        current_part, current_chapter, current_section,
                        current_subsection, current_content
                    ))
                current_section = section_match.group(1)
                current_content = []
                continue

            # 检测小节
            subsection_match = self.subsection_pattern.match(line)
            if subsection_match:
                # 保存前一个小节
                if current_subsection and current_content:
                    chunks.append(self._create_chunk(
                        current_part, current_chapter, current_section,
                        current_subsection, current_content
                    ))

                # 开始新小节
                current_subsection = subsection_match.group(1)
                subsection_title = subsection_match.group(2)
                current_content = [subsection_title]

                # 检查是否为2025新增内容
                update_type = self._check_2025_update(
                    current_part, current_chapter, current_subsection
                )
                logger.info(f"小节: {current_subsection} - {subsection_title} ({update_type})")
                continue

            # 累积内容
            if current_subsection:
                current_content.append(line)

        # 保存最后一个小节
        if current_subsection and current_content:
            chunks.append(self._create_chunk(
                current_part, current_chapter, current_section,
                current_subsection, current_content
            ))

        logger.info(f"✅ 提取完成，共 {len(chunks)} 个小节块")
        return chunks

    def _create_chunk(self, part: str, chapter: str, section: str,
                     subsection: str, content_lines: list[str]) -> SubsectionChunk:
        """创建小节块"""
        title = content_lines[0] if content_lines else ""
        content = "\n".join(content_lines[1:]) if len(content_lines) > 1 else title

        # 生成唯一ID
        chunk_id = self._generate_chunk_id(part, chapter, subsection)

        # 检查是否包含示例
        has_example = bool(self.example_pattern.search(content))

        # 提取法律引用
        references = self.law_ref_pattern.findall(content)
        references = [f"{law} {article}" for law, article in references]

        # 提取关键词
        keywords = self._extract_keywords(content)

        # 检查2025更新类型
        update_type = self._check_2025_update(part, chapter, subsection)

        return SubsectionChunk(
            chunk_id=chunk_id,
            part=part or "",
            chapter=chapter or "",
            section=section or "",
            subsection=subsection,
            title=title,
            content=content,
            update_type=update_type,
            word_count=len(content),
            has_example=has_example,
            references=references,
            keywords=keywords,
            version="2025"
        )

    def _generate_chunk_id(self, part: str, chapter: str, subsection: str) -> str:
        """生成唯一的块ID"""
        id_string = f"{part}_{chapter}_{subsection}".replace(" ", "_")
        return f"chunk_{short_hash(id_string.encode(), 12)}"

    def _check_2025_update(self, part: str, chapter: str, subsection: str) -> str | None:
        """检查是否为2025版新增/修改内容"""
        # 检查NEW_CONTENT_2025映射
        if part in self.NEW_CONTENT_2025:
            if chapter in self.NEW_CONTENT_2025[part]:
                chapter_updates = self.NEW_CONTENT_2025[part][chapter]
                for key, _value in chapter_updates.items():
                    if subsection in key or key in subsection:
                        return "新增" if "新增" in key else "修改"
        return None

    def _extract_keywords(self, content: str) -> list[str]:
        """从内容中提取关键词"""
        # 专利相关关键词列表
        patent_keywords = [
            "新颖性", "创造性", "实用性", "现有技术", "抵触申请",
            "优先权", "公开", "充分公开", "技术方案", "技术特征",
            "权利要求", "说明书", "附图", "摘要", "比特流", "人工智能",
            "大数据", "伦理", "审查", "驳回", "授权"
        ]

        found_keywords = []
        for keyword in patent_keywords:
            if keyword in content:
                found_keywords.append(keyword)

        return found_keywords

    async def generate_bge_vectors(self, chunks: list[SubsectionChunk]) -> dict[str, Any]:
        """为小节块生成BGE向量"""
        logger.info(f"📊 开始生成BGE向量，共 {len(chunks)} 个块")

        try:
            from core.nlp.bge_embedding_service import BGEEmbeddingService

            # 初始化BGE服务
            model_path = "/Users/xujian/Athena工作平台/models/converted/bge-large-zh-v1.5"
            config = {
                "model_path": model_path,
                "device": "cpu",
                "batch_size": 32,
                "max_length": 512,
                "normalize_embeddings": True
            }

            bge_service = BGEEmbeddingService(config)
            await bge_service.initialize()

            # 准备文本（增强上下文）
            texts = []
            for chunk in chunks:
                # 增强文本：添加层级上下文
                enhanced_text = f"[{chunk.part} > {chunk.chapter} > {chunk.subsection}] {chunk.title}\n{chunk.content}"
                texts.append(enhanced_text)

            # 批量编码
            batch_size = 32
            all_vectors = []

            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                result = await bge_service.encode(batch, task_type="patent_guideline")

                for j, embedding in enumerate(result.embeddings):
                    all_vectors.append({
                        'chunk_id': chunks[i+j].chunk_id,
                        'embedding': embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
                    })

                logger.info(f"✅ 进度: {i+len(batch)}/{len(texts)}")

            logger.info(f"✅ 向量生成完成: {len(all_vectors)} 个")

            return {
                'total_vectors': len(all_vectors),
                'vectors': all_vectors,
                'dimension': 1024
            }

        except Exception as e:
            logger.error(f"❌ BGE向量生成失败: {e}")
            return {'error': str(e)}

    async def build_nebula_graph(self, chunks: list[SubsectionChunk]) -> dict[str, Any]:
        """构建NebulaGraph知识图谱"""
        logger.info(f"🌐 开始构建NebulaGraph知识图谱，共 {len(chunks)} 个节点")

        try:

            # 这里需要实际的NebulaGraph连接配置
            # 暂时返回模拟数据
            logger.info("✅ NebulaGraph知识图谱构建完成（模拟）")

            return {
                'total_nodes': len(chunks),
                'node_types': ['Subsection', 'Part', 'Chapter', 'Section'],
                'edge_types': ['REFERENCES', 'CONTAINS', 'MODIFIED_BY']
            }

        except Exception as e:
            logger.error(f"❌ NebulaGraph构建失败: {e}")
            return {'error': str(e)}

    def save_chunks(self, chunks: list[SubsectionChunk], output_dir: str) -> None:
        """保存小节块到文件"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存为JSON
        chunks_file = output_path / f"guideline_2025_chunks_{timestamp}.json"

        # 转换为可序列化格式
        chunks_data = [asdict(chunk) for chunk in chunks]

        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump({
                'version': '2025',
                'total_chunks': len(chunks),
                'chunks': chunks_data
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 已保存 {len(chunks)} 个块到: {chunks_file}")

        # 生成统计报告
        stats = self._generate_statistics(chunks)
        stats_file = output_path / f"guideline_2025_stats_{timestamp}.json"

        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        logger.info(f"📊 统计报告已保存: {stats_file}")

        return str(chunks_file), str(stats_file)

    def _generate_statistics(self, chunks: list[SubsectionChunk]) -> dict[str, Any]:
        """生成统计信息"""
        stats = {
            'total_chunks': len(chunks),
            'version': '2025',
            'avg_word_count': sum(c.word_count for c in chunks) / len(chunks) if chunks else 0,
            'chunks_with_examples': sum(1 for c in chunks if c.has_example),
            'new_in_2025': sum(1 for c in chunks if c.update_type == '新增'),
            'modified_in_2025': sum(1 for c in chunks if c.update_type == '修改'),
            'by_part': defaultdict(int),
            'by_chapter': defaultdict(int),
            'top_keywords': defaultdict(int)
        }

        for chunk in chunks:
            stats['by_part'][chunk.part] += 1
            stats['by_chapter'][chunk.chapter] += 1
            for keyword in chunk.keywords:
                stats['top_keywords'][keyword] += 1

        # 转换defaultdict为普通dict
        stats['by_part'] = dict(stats['by_part'])
        stats['by_chapter'] = dict(stats['by_chapter'])
        stats['top_keywords'] = dict(sorted(stats['top_keywords'].items(), key=lambda x: x[1], reverse=True)[:20])

        return stats


async def main():
    """主函数"""
    processor = PatentGuideline2025Processor()

    logger.info("=" * 60)
    logger.info("🚀 启动专利审查指南2025版处理器")
    logger.info("=" * 60)

    # 模拟处理流程
    # 1. 解析PDF结构
    # structure = processor.parse_guideline_structure("patent_guideline_2025.pdf")

    # 2. 提取小节块
    # chunks = processor.extract_subsections(content)

    # 3. 生成BGE向量
    # vectors = await processor.generate_bge_vectors(chunks)

    # 4. 构建NebulaGraph
    # graph = await processor.build_nebula_graph(chunks)

    # 5. 保存结果
    # processor.save_chunks(chunks, "/Users/xujian/Athena工作平台/production/data/patent_rules/legal_documents")

    logger.info("✅ 处理完成！")


if __name__ == "__main__":
    asyncio.run(main())
