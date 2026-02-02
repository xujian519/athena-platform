#!/usr/bin/env python3
"""
使用项目本地向量模型进行专利法律法规向量化
Patent Legal Vectorization with Local Model

作者: 小诺·双鱼公主
创建时间: 2024年12月15日
"""

import os
import sys
import json
import logging
import asyncio
import aiofiles
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.append('/Users/xujian/Athena工作平台/storage-system/services')
from local_embedding import LocalEmbeddingService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PatentLegalLocalVectorizer:
    """使用项目本地模型的专利法律法规向量化器"""

    def __init__(self, model_type: str = "tfidf", vector_size: int = 1024):
        """
        初始化向量化器

        Args:
            model_type: 模型类型 (tfidf, word2vec, simple)
            vector_size: 向量维度 (1024)
        """
        self.model_type = model_type
        self.vector_size = vector_size
        self.chunk_size = 1000
        self.overlap = 200

        # 初始化本地嵌入服务
        self.embedding_service = None
        self._init_embedding_service()

        logger.info(f"本地向量化器初始化完成，模型类型: {model_type}, 向量维度: {vector_size}")

    def _init_embedding_service(self):
        """初始化嵌入服务"""
        try:
            # 创建自定义的本地嵌入服务，指定1024维度
            self.embedding_service = LocalEmbeddingService(model_type=self.model_type)

            # 修改向量维度为1024
            if hasattr(self.embedding_service, 'vector_size'):
                self.embedding_service.vector_size = self.vector_size

            logger.info(f"✅ 本地嵌入服务初始化成功")
            logger.info(f"   模型类型: {self.model_type}")
            logger.info(f"   向量维度: {self.vector_size}")

        except Exception as e:
            logger.error(f"初始化嵌入服务失败: {e}")
            # 创建简单的备用服务
            self.embedding_service = SimpleEmbeddingFallback(self.vector_size)

    async def load_documents(self, folder_path: str) -> List[Dict[str, Any]]:
        """加载文档"""
        folder_path = Path(folder_path)
        documents = []

        # 遍历所有文件
        for file_path in folder_path.glob("*"):
            if file_path.is_file():
                content = await self._extract_content(file_path)
                if content and len(content.strip()) > 100:
                    documents.append({
                        "file_name": file_path.name,
                        "file_path": str(file_path),
                        "content": content,
                        "type": self._classify_document(file_path.name, content)
                    })

        logger.info(f"加载了 {len(documents)} 个文档")
        return documents

    async def _extract_content(self, file_path: Path) -> str:
        """提取文件内容"""
        try:
            if file_path.suffix.lower() == '.md':
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    return await f.read()
            elif file_path.suffix.lower() == '.docx':
                from docx import Document
                doc = Document(file_path)
                return '\n'.join([para.text for para in doc.paragraphs if para.text.strip()])
            elif file_path.suffix.lower() == '.pdf':
                import PyPDF2
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    content = []
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        if text and text.strip():
                            content.append(text)
                    return '\n'.join(content)
            else:
                return ""
        except Exception as e:
            logger.error(f"读取文件 {file_path} 失败: {e}")
            return ""

    def _classify_document(self, file_name: str, content: str) -> str:
        """分类文档类型"""
        if "法" in file_name or "法律" in content:
            return "law"
        elif "条例" in file_name or "规定" in file_name:
            return "regulation"
        elif "指南" in file_name or "审查" in content:
            return "procedure"
        elif "解释" in file_name or "案例" in content:
            return "case"
        else:
            return "concept"

    def chunk_document(self, content: str, doc_name: str) -> List[Dict[str, Any]]:
        """文档分块"""
        chunks = []
        current_chunk = ""
        chunk_id = 0

        # 按段落分割
        paragraphs = content.split('\n\n')

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append({
                        "chunk_id": chunk_id,
                        "content": current_chunk.strip(),
                        "doc_name": doc_name,
                        "char_count": len(current_chunk)
                    })
                    chunk_id += 1

                if self.overlap > 0 and len(current_chunk) > self.overlap:
                    current_chunk = current_chunk[-self.overlap:] + para + "\n\n"
                else:
                    current_chunk = para + "\n\n"

        # 保存最后一块
        if current_chunk:
            chunks.append({
                "chunk_id": chunk_id,
                "content": current_chunk.strip(),
                "doc_name": doc_name,
                "char_count": len(current_chunk)
            })

        return chunks

    def vectorize_text(self, text: str) -> List[float | None]:
        """向量化单个文本"""
        if not text or not self.embedding_service:
            return None

        try:
            # 使用本地嵌入服务
            vector = self.embedding_service.encode(text)

            # 确保维度正确
            if len(vector) != self.vector_size:
                # 调整向量维度
                if len(vector) > self.vector_size:
                    vector = vector[:self.vector_size]
                else:
                    # 填充到指定维度
                    padded_vector = list(vector)
                    padded_vector.extend([0.0] * (self.vector_size - len(vector)))
                    vector = padded_vector

            return list(vector)

        except Exception as e:
            logger.error(f"向量化失败: {e}")
            return None

    def process_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理文档并生成向量"""
        all_chunks = []

        # 分块处理
        for doc in documents:
            chunks = self.chunk_document(doc["content"], doc["file_name"])
            all_chunks.extend(chunks)

        logger.info(f"总共生成 {len(all_chunks)} 个文档块")

        # 向量化
        vectors_data = []
        for i, chunk in enumerate(all_chunks):
            logger.info(f"正在处理第 {i+1}/{len(all_chunks)} 个文档块: {chunk['doc_name'][:50]}...")

            # 生成向量
            vector = self.vectorize_text(chunk["content"])

            if vector is not None:
                vector_data = {
                    "id": hash(f"{chunk['doc_name']}_{chunk['chunk_id']}") & 0xFFFFFFFF,
                    "vector": vector,
                    "metadata": {
                        "doc_name": chunk["doc_name"],
                        "chunk_id": chunk["chunk_id"],
                        "char_count": chunk["char_count"],
                        "content_preview": chunk["content"][:500],
                        "model_type": self.model_type,
                        "vector_size": self.vector_size
                    },
                    "created_at": datetime.now().isoformat()
                }
                vectors_data.append(vector_data)

        logger.info(f"成功向量化 {len(vectors_data)} 个文档块")
        return vectors_data

    def prepare_qdrant_data(self, vectors_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """准备Qdrant导入数据"""
        points = []

        for data in vectors_data:
            point = {
                "id": data["id"],
                "vector": data["vector"],
                "payload": {
                    "doc_name": data["metadata"]["doc_name"],
                    "chunk_id": data["metadata"]["chunk_id"],
                    "content": data["metadata"]["content_preview"],
                    "char_count": data["metadata"]["char_count"],
                    "model_type": data["metadata"]["model_type"],
                    "vector_size": data["metadata"]["vector_size"],
                    "created_at": data["created_at"]
                }
            }
            points.append(point)

        return {
            "collection_name": "patent_legal_vectors_1024",
            "points": points
        }

    async def save_results(self, vectors_data: List[Dict[str, Any]], qdrant_data: Dict[str, Any]):
        """保存结果"""
        output_dir = Path("/Users/xujian/Athena工作平台/data/patent_legal_vectors_1024")
        output_dir.mkdir(parents=True, exist_ok=True)

        # 保存向量数据
        vectors_path = output_dir / "vectors.json"
        with open(vectors_path, 'w', encoding='utf-8') as f:
            json.dump(vectors_data, f, ensure_ascii=False, indent=2)

        # 保存Qdrant导入数据
        qdrant_path = output_dir / "qdrant_import.json"
        async with aiofiles.open(qdrant_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(qdrant_data, ensure_ascii=False, indent=2))

        # 创建统计信息
        stats = {
            "total_documents": len(set(v["metadata"]["doc_name"] for v in vectors_data)),
            "total_vectors": len(vectors_data),
            "vector_dimension": self.vector_size,
            "model_type": self.model_type,
            "created_at": datetime.now().isoformat()
        }

        stats_path = output_dir / "stats.json"
        async with aiofiles.open(stats_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(stats, ensure_ascii=False, indent=2))

        logger.info(f"数据已保存:")
        logger.info(f"  向量数据: {vectors_path}")
        logger.info(f"  Qdrant数据: {qdrant_path}")
        logger.info(f"  统计信息: {stats_path}")


class SimpleEmbeddingFallback:
    """简单的嵌入服务备用方案"""

    def __init__(self, vector_size: int = 1024):
        self.vector_size = vector_size

    def encode(self, text: str) -> List[float]:
        """生成简单的哈希向量"""
        import hashlib

        if not text:
            return [0.0] * self.vector_size

        # 使用文本哈希生成向量
        hash_obj = hashlib.sha256(text.encode('utf-8'))
        hash_bytes = hash_obj.digest()

        vector = []
        for i in range(self.vector_size):
            # 组合多个哈希字节
            byte_idx = i % len(hash_bytes)
            next_idx = (i + 1) % len(hash_bytes)
            val = (hash_bytes[byte_idx] + hash_bytes[next_idx]) / 510.0
            vector.append(val)

        # 归一化
        import numpy as np
        vector = np.array(vector)
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector.tolist()


async def main():
    """主函数"""
    logger.info("开始使用本地向量模型进行专利法律法规向量化...")

    # 创建向量化器
    vectorizer = PatentLegalLocalVectorizer(
        model_type="tfidf",  # 使用TF-IDF模型
        vector_size=1024      # 1024维度
    )

    # 加载文档
    documents = await vectorizer.load_documents("/Users/xujian/学习资料/专利/专利法律法规")

    if not documents:
        logger.error("没有找到有效的文档")
        return

    # 处理文档
    vectors_data = vectorizer.process_documents(documents)

    # 准备Qdrant数据
    qdrant_data = vectorizer.prepare_qdrant_data(vectors_data)

    # 保存结果
    await vectorizer.save_results(vectors_data, qdrant_data)

    logger.info("\n✅ 本地向量模型向量化处理完成！")
    logger.info(f"\n处理统计:")
    logger.info(f"  处理文档数: {len(documents)}")
    logger.info(f"  生成向量数: {len(vectors_data)}")
    logger.info(f"  向量维度: {vectorizer.vector_size}")
    logger.info(f"  模型类型: {vectorizer.model_type}")


if __name__ == "__main__":
    asyncio.run(main())