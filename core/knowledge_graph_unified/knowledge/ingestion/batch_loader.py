#!/usr/bin/env python3

"""
批量数据加载器
Batch Data Loader

批量处理文档并导入知识图谱
作者: 小诺·双鱼座
创建时间: 2025-12-21
版本: v1.0.0 "批量导入"
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ..collection_config import get_collection_mapper
from .document_processor import DocumentProcessor, DocumentType, ProcessedDocument

logger = logging.getLogger(__name__)


@dataclass
class LoadingStats:
    """加载统计"""

    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    total_chunks: int = 0
    loaded_chunks: int = 0
    failed_chunks: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    errors: list[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_files == 0:
            return 0.0
        return (self.processed_files / self.total_files) * 100

    @property
    def chunk_success_rate(self) -> float:
        """块加载成功率"""
        if self.total_chunks == 0:
            return 0.0
        return (self.loaded_chunks / self.total_chunks) * 100


class BatchLoader:
    """批量数据加载器"""

    def __init__(self, knowledge_graph=None):
        self.document_processor = DocumentProcessor()
        self.knowledge_graph = knowledge_graph
        self.collection_mapper = get_collection_mapper()
        self.stats = LoadingStats()

    async def load_directory(
        self,
        directory_path: str | Path,
        pattern: str = "*",
        recursive: bool = True,
        max_concurrent: int = 5,
    ) -> LoadingStats:
        """
        加载目录中的文档

        Args:
            directory_path: 目录路径
            pattern: 文件匹配模式
            recursive: 是否递归搜索
            max_concurrent: 最大并发数

        Returns:
            LoadingStats: 加载统计
        """
        directory_path = Path(directory_path)
        if not directory_path.exists() or not directory_path.is_dir():
            raise ValueError(f"无效的目录路径: {directory_path}")

        self.stats = LoadingStats()
        self.stats.start_time = datetime.now()

        try:
            # 1. 收集所有待处理文件
            if recursive:
                files = list(directory_path.rglob(pattern))
            else:
                files = list(directory_path.glob(pattern))

            # 过滤支持的文件类型
            supported_extensions = {".txt", ".pdf", ".docx", ".doc"}
            files = [f for f in files if f.suffix.lower() in supported_extensions]

            self.stats.total_files = len(files)
            logger.info(f"📁 找到 {len(files)} 个文件待处理")

            if not files:
                logger.warning("⚠️ 没有找到支持的文件")
                return self.stats

            # 2. 分批处理文件
            semaphore = asyncio.Semaphore(max_concurrent)
            tasks = []

            for file_path in files:
                task = self._process_file_with_semaphore(semaphore, file_path)
                tasks.append(task)

            # 3. 等待所有任务完成
            await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"❌ 批量加载失败: {e}")
            self.stats.errors.append(str(e))

        finally:
            self.stats.end_time = datetime.now()
            self._log_final_stats()

        return self.stats

    async def load_single_file(self, file_path: str | Path) -> LoadingStats:
        """
        加载单个文件

        Args:
            file_path: 文件路径

        Returns:
            LoadingStats: 加载统计
        """
        self.stats = LoadingStats()
        self.stats.start_time = datetime.now()
        self.stats.total_files = 1

        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        try:
            await self._process_file(file_path)
        except Exception as e:
            logger.error(f"❌ 文件处理失败: {e}")
            self.stats.failed_files = 1
            self.stats.errors.append(str(e))

        finally:
            self.stats.end_time = datetime.now()
            self._log_final_stats()

        return self.stats

    async def _process_file_with_semaphore(self, semaphore: asyncio.Semaphore, file_path: Path):
        """带信号量的文件处理"""
        async with semaphore:
            await self._process_file(file_path)

    async def _process_file(self, file_path: Path):
        """处理单个文件"""
        try:
            logger.info(f"📄 处理文件: {file_path.name}")

            # 1. 处理文档
            processed_doc = await self.document_processor.process_document(file_path)
            if not processed_doc:
                self.stats.failed_files += 1
                error_msg = f"文档处理失败: {file_path.name}"
                logger.error(error_msg)
                self.stats.errors.append(error_msg)
                return

            self.stats.processed_files += 1
            self.stats.total_chunks += len(processed_doc.chunks)

            # 2. 如果没有知识图谱实例,只处理文档
            if self.knowledge_graph is None:
                logger.info(f"✅ 文档处理完成: {file_path.name} ({len(processed_doc.chunks)}个块)")
                self.stats.loaded_chunks += len(processed_doc.chunks)
                return

            # 3. 将块导入知识图谱
            for chunk in processed_doc.chunks:
                success = await self._import_chunk_to_kg(chunk, processed_doc)
                if success:
                    self.stats.loaded_chunks += 1
                else:
                    self.stats.failed_chunks += 1

            logger.info(
                f"✅ 文件导入完成: {file_path.name} ({self.stats.loaded_chunks}/{len(processed_doc.chunks)}个块)"
            )

        except Exception as e:
            self.stats.failed_files += 1
            error_msg = f"文件处理异常 {file_path.name}: {e}"
            logger.error(error_msg)
            self.stats.errors.append(error_msg)

    async def _import_chunk_to_kg(self, chunk, processed_doc: ProcessedDocument) -> bool:
        """
        将块导入知识图谱

        Args:
            chunk: 文档块
            processed_doc: 处理后的文档

        Returns:
            bool: 是否导入成功
        """
        try:
            # 构建节点数据
            node_data = {
                "node_id": f"{processed_doc.doc_id}_{chunk.chunk_id}",
                "node_type": self._map_chunk_to_node_type(chunk, processed_doc),
                "title": self._generate_chunk_title(chunk, processed_doc),
                "description": chunk.content,
                "properties": {
                    "doc_id": processed_doc.doc_id,
                    "doc_type": processed_doc.doc_type.value,
                    "chunk_type": chunk.chunk_type,
                    "hierarchy_level": chunk.hierarchy_level,
                    "source_file": processed_doc.metadata.get("source_file"),
                    "chunk_metadata": chunk.metadata,
                    "processed_at": processed_doc.metadata.get("processed_at"),
                },
            }

            # 添加到知识图谱
            success = await self.knowledge_graph.add_node(node_data)
            return success

        except Exception as e:
            logger.error(f"❌ 块导入失败 {chunk.chunk_id}: {e}")
            return False

    def _map_chunk_to_node_type(self, chunk, processed_doc: ProcessedDocument) -> str:
        """将块映射到节点类型"""
        doc_type = processed_doc.doc_type
        chunk_type = chunk.chunk_type

        # 基于文档类型和块类型映射
        if doc_type == DocumentType.PATENT_LAW:
            if chunk_type == "article":
                return "ARTICLE"
            elif chunk_type == "chapter" or chunk_type == "section":
                return "CONCEPT"
        elif doc_type == DocumentType.EXAMINATION_GUIDE:
            if chunk_type == "article":
                return "ARTICLE"
            else:
                return "CONCEPT"
        elif doc_type == DocumentType.LEGAL_CASE:
            return "LEGAL_CASE"
        elif doc_type == DocumentType.PATENT_APPLICATION:
            if chunk_type == "claims":
                return "PATENT"
            elif chunk_type == "technical_field":
                return "TECHNOLOGY"
            elif chunk_type == "summary":
                return "PATENT"
            else:
                return "PRIOR_ART"
        else:
            # 默认映射
            if chunk_type == "paragraph":
                return "CONCEPT"
            else:
                return "KEYWORD"

        return "CONCEPT"  # 默认值

    def _generate_chunk_title(self, chunk, processed_doc: ProcessedDocument) -> str:
        """生成块的标题"""
        doc_title = processed_doc.title
        chunk_type = chunk.chunk_type
        chunk_num = chunk.chunk_id.split("_")[-1]

        type_titles = {
            "article": "条款",
            "chapter": "章节",
            "section": "节",
            "claim": "权利要求",
            "technical_field": "技术领域",
            "background_art": "背景技术",
            "summary": "发明内容",
            "detailed_description": "具体实施方式",
            "paragraph": "段落",
        }

        chunk_title_cn = type_titles.get(chunk_type, "内容")
        return f"{doc_title} - {chunk_title_cn}{chunk_num}"

    def _log_final_stats(self) -> Any:
        """记录最终统计"""
        duration = (self.stats.end_time - self.stats.start_time).total_seconds()

        logger.info("=" * 60)
        logger.info("📊 批量加载统计报告")
        logger.info("=" * 60)
        logger.info(f"📁 总文件数: {self.stats.total_files}")
        logger.info(f"✅ 成功处理: {self.stats.processed_files}")
        logger.info(f"❌ 失败文件: {self.stats.failed_files}")
        logger.info(f"📈 成功率: {self.stats.success_rate:.2f}%")
        logger.info(f"📝 总块数: {self.stats.total_chunks}")
        logger.info(f"✅ 成功加载: {self.stats.loaded_chunks}")
        logger.info(f"❌ 失败块数: {self.stats.failed_chunks}")
        logger.info(f"📈 块成功率: {self.stats.chunk_success_rate:.2f}%")
        logger.info(f"⏱️ 处理时长: {duration:.2f}秒")
        logger.info(
            f"🚀 平均速度: {self.stats.total_chunks/duration:.2f}块/秒"
            if duration > 0
            else "🚀 平均速度: N/A"
        )

        if self.stats.errors:
            logger.info("❗ 错误信息:")
            for error in self.stats.errors[:5]:  # 只显示前5个错误
                logger.info(f"  - {error}")
            if len(self.stats.errors) > 5:
                logger.info(f"  ... 还有 {len(self.stats.errors) - 5} 个错误")

        logger.info("=" * 60)


# 便捷函数
async def load_documents_to_kg(
    directory_path: str, knowledge_graph, pattern: str = "*"
) -> LoadingStats:
    """
    便捷函数:加载文档到知识图谱

    Args:
        directory_path: 文档目录路径
        knowledge_graph: 知识图谱实例
        pattern: 文件匹配模式

    Returns:
        LoadingStats: 加载统计
    """
    loader = BatchLoader(knowledge_graph=knowledge_graph)
    return await loader.load_directory(directory_path, pattern)


async def process_documents_only(directory_path: str, pattern: str = "*") -> LoadingStats:
    """
    便捷函数:仅处理文档(不导入知识图谱)

    Args:
        directory_path: 文档目录路径
        pattern: 文件匹配模式

    Returns:
        LoadingStats: 处理统计
    """
    loader = BatchLoader(knowledge_graph=None)
    return await loader.load_directory(directory_path, pattern)

