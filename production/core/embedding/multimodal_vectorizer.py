#!/usr/bin/env python3
"""
多模态向量化模块
Multimodal Vectorization Module

使用平台NLP服务对多模态文件内容进行向量化
支持文档、图像、音频、视频等多种文件类型

作者: 小诺·双鱼公主
创建时间: 2025-12-24
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from core.embedding.nlp_service_adapter import NLPServiceAdapter, get_nlp_adapter

logger = logging.getLogger(__name__)


@dataclass
class VectorizationResult:
    """向量化结果"""

    file_id: str
    file_path: str
    file_type: str
    vector: np.ndarray
    dimension: int
    content_preview: str
    metadata: dict[str, Any]
    created_at: datetime
    processing_time: float

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "file_id": self.file_id,
            "file_path": str(self.file_path),
            "file_type": self.file_type,
            "vector": self.vector.tolist(),  # 转换为列表以便序列化
            "dimension": self.dimension,
            "content_preview": self.content_preview,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "processing_time": self.processing_time,
        }


class MultimodalVectorizer:
    """
    多模态文件向量化器

    使用平台NLP服务对文件内容进行向量化处理
    """

    def __init__(
        self,
        nlp_service_url: str = "http://localhost:8001",
        cache_enabled: bool = True,
        batch_size: int = 32,
    ):
        """
        初始化多模态向量化器

        Args:
            nlp_service_url: NLP服务地址
            cache_enabled: 是否启用缓存
            batch_size: 批处理大小
        """
        self.nlp_service_url = nlp_service_url
        self.cache_enabled = cache_enabled
        self.batch_size = batch_size

        # 获取NLP适配器
        self.nlp_adapter: NLPServiceAdapter = get_nlp_adapter(
            service_url=nlp_service_url, cache_enabled=cache_enabled
        )

        # 文件类型处理器
        self.processors = {
            ".txt": self._process_text_file,
            ".md": self._process_text_file,
            ".py": self._process_text_file,
            ".js": self._process_text_file,
            ".html": self._process_text_file,
            ".css": self._process_text_file,
            ".json": self._process_text_file,
            ".xml": self._process_text_file,
            ".pdf": self._process_pdf_file,
            ".docx": self._process_docx_file,
            ".xlsx": self._process_xlsx_file,
            ".jpg": self._process_image_file,
            ".jpeg": self._process_image_file,
            ".png": self._process_image_file,
            ".gif": self._process_image_file,
            ".bmp": self._process_image_file,
        }

        logger.info("🚀 多模态向量化器初始化完成")

    async def vectorize_file(
        self, file_path: str | Path | None = None, file_id: str | None = None
    ) -> VectorizationResult:
        """
        向量化单个文件

        Args:
            file_path: 文件路径
            file_id: 可选的文件ID

        Returns:
            向量化结果
        """
        start_time = datetime.now()
        file_path = Path(file_path)

        # 检查文件是否存在
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 生成文件ID
        if file_id is None:
            file_id = self._generate_file_id(file_path)

        # 获取文件扩展名
        ext = file_path.suffix.lower()

        # 提取文件内容
        content = await self._extract_content(file_path, ext)

        # 生成向量
        vector = await self.nlp_adapter.encode(content)

        # 计算处理时间
        processing_time = (datetime.now() - start_time).total_seconds()

        # 构建结果
        result = VectorizationResult(
            file_id=file_id,
            file_path=file_path,
            file_type=ext,
            vector=vector,
            dimension=len(vector),
            content_preview=content[:200] if len(content) > 200 else content,
            metadata={
                "file_size": file_path.stat().st_size,
                "nlp_service": self.nlp_service_url,
                "content_length": len(content),
            },
            created_at=datetime.now(),
            processing_time=processing_time,
        )

        logger.info(f"✅ 文件向量化完成: {file_path.name} ({processing_time:.3f}秒)")
        return result

    async def vectorize_batch(
        self, file_paths: list[str | Path], show_progress: bool = True
    ) -> list[VectorizationResult]:
        """
        批量向量化文件

        Args:
            file_paths: 文件路径列表
            show_progress: 是否显示进度

        Returns:
            向量化结果列表
        """
        results = []
        total = len(file_paths)

        for i, file_path in enumerate(file_paths):
            try:
                result = await self.vectorize_file(file_path)
                results.append(result)

                if show_progress:
                    progress = (i + 1) / total * 100
                    print(f"  进度: {i+1}/{total} ({progress:.1f}%) - {file_path}")

            except Exception as e:
                logger.error(f"❌ 文件向量化失败 {file_path}: {e}")
                # 继续处理下一个文件
                continue

        logger.info(f"✅ 批量向量化完成: {len(results)}/{total} 成功")
        return results

    async def _extract_content(self, file_path: Path, file_ext: str) -> str:
        """
        提取文件内容

        Args:
            file_path: 文件路径
            file_ext: 文件扩展名

        Returns:
            提取的文本内容
        """
        # 查找对应的处理器
        processor = self.processors.get(file_ext)

        if processor:
            return await processor(file_path)
        else:
            # 默认处理:读取为文本
            return await self._process_text_file(file_path)

    async def _process_text_file(self, file_path: Path) -> str:
        """处理文本文件"""
        try:
            # 尝试UTF-8编码
            with open(file_path, encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, encoding="gbk") as f:
                    return f.read()
            except Exception as e:
                logger.debug(f"空except块已触发: {e}")
                return f"无法解码文件: {file_path.name}"

    async def _process_pdf_file(self, file_path: Path) -> str:
        """处理PDF文件"""
        try:
            import PyPDF2

            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text[:5000]  # 限制长度
        except Exception as e:
            logger.error(f"PDF处理失败: {e}")
            return f"PDF处理失败: {file_path.name}"

    async def _process_docx_file(self, file_path: Path) -> str:
        """处理Word文档"""
        try:
            from docx import Document

            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text[:5000]
        except Exception as e:
            logger.error(f"DOCX处理失败: {e}")
            return f"DOCX处理失败: {file_path.name}"

    async def _process_xlsx_file(self, file_path: Path) -> str:
        """处理Excel文件"""
        try:
            import openpyxl

            wb = openpyxl.load_workbook(file_path)
            text = ""
            for sheet in wb.worksheets:
                for row in sheet.iter_rows(values_only=True):
                    row_text = " ".join([str(cell) if cell is not None else "" for cell in row])
                    text += row_text + "\n"
            return text[:5000]
        except Exception as e:
            logger.error(f"XLSX处理失败: {e}")
            return f"XLSX处理失败: {file_path.name}"

    async def _process_image_file(self, file_path: Path) -> str:
        """处理图像文件"""
        try:
            from PIL import Image

            img = Image.open(file_path)

            # 提取基本元数据
            metadata = f"图像文件: {file_path.name}\n"
            metadata += f"尺寸: {img.size}\n"
            metadata += f"模式: {img.mode}\n"

            # 提取EXIF信息
            try:
                from PIL.ExifTags import TAGS

                exif = img._getexif()
                if exif:
                    for tag, _value in exif.items():
                        TAGS.get(tag, tag)
            except Exception as e:
                logger.debug(f"空except块已触发: {e}")

            return metadata
        except Exception as e:
            logger.error(f"图像处理失败: {e}")
            return f"图像文件: {file_path.name}"

    def _generate_file_id(self, file_path: Path) -> str:
        """生成文件ID"""
        # 使用文件路径和修改时间生成唯一ID
        stat = file_path.stat()
        content = f"{file_path}_{stat.st_size}_{stat.st_mtime}"
        hash_obj = hashlib.md5(content.encode("utf-8", usedforsecurity=False), usedforsecurity=False)
        return f"file_{hash_obj.hexdigest()[:16]}"

    async def get_vector_statistics(self, results: list[VectorizationResult]) -> dict[str, Any]:
        """
        获取向量化统计信息

        Args:
            results: 向量化结果列表

        Returns:
            统计信息
        """
        if not results:
            return {}

        dimensions = [r.dimension for r in results]
        processing_times = [r.processing_time for r in results]
        file_sizes = [r.metadata.get("file_size", 0) for r in results]

        return {
            "total_files": len(results),
            "dimension": dimensions[0] if dimensions else 0,
            "avg_processing_time": np.mean(processing_times),
            "total_processing_time": np.sum(processing_times),
            "avg_file_size": np.mean(file_sizes),
            "total_file_size": np.sum(file_sizes),
            "files_by_type": self._count_by_type(results),
        }

    def _count_by_type(self, results: list[VectorizationResult]) -> dict[str, int]:
        """按文件类型统计"""
        type_counts = {}
        for result in results:
            file_type = result.file_type
            type_counts[file_type] = type_counts.get(file_type, 0) + 1
        return type_counts

    async def close(self):
        """关闭连接"""
        await self.nlp_adapter.close()


# 单例实例
_vectorizer_instance: MultimodalVectorizer | None = None


def get_multimodal_vectorizer(
    nlp_service_url: str = "http://localhost:8001", **kwargs
) -> MultimodalVectorizer:
    """
    获取多模态向量化器单例

    Args:
        nlp_service_url: NLP服务地址
        **kwargs: 其他配置参数

    Returns:
        多模态向量化器实例
    """
    global _vectorizer_instance

    if _vectorizer_instance is None:
        _vectorizer_instance = MultimodalVectorizer(nlp_service_url=nlp_service_url, **kwargs)
        logger.info("✅ 创建多模态向量化器单例")

    return _vectorizer_instance


if __name__ == "__main__":
    # 测试代码
    async def test():
        print("🧪 测试多模态向量化模块")
        print("=" * 60)

        vectorizer = MultimodalVectorizer()

        # 测试向量化
        test_files = ["config/multimodal_config.json", "README.md"]

        print("\n📁 测试文件向量化...")
        for file_path in test_files:
            try:
                result = await vectorizer.vectorize_file(file_path)
                print(f"\n✅ {file_path}")
                print(f"   维度: {result.dimension}")
                print(f"   处理时间: {result.processing_time:.3f}秒")
                print(f"   内容预览: {result.content_preview[:100]}...")
            except Exception as e:
                print(f"\n❌ {file_path}: {e}")

        await vectorizer.close()
        print("\n✅ 测试完成")

    asyncio.run(test())
