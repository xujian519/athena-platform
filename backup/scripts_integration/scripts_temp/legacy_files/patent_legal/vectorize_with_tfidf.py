#!/usr/bin/env python3
"""
使用TF-IDF替代方案进行专利法律法规向量化
Use TF-IDF Alternative for Patent Legal Vectorization

作者: 小诺·双鱼公主
创建时间: 2024年12月15日
"""

import os
import json
import logging
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
import aiofiles
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
import jieba
import re

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PatentLegalTFIDFVectorizer:
    """专利法律法规TF-IDF向量化器"""

    def __init__(self):
        """初始化"""
        self.vector_size = 384  # 降低维度
        self.chunk_size = 1000
        self.overlap = 200

        # 初始化jieba分词器
        jieba.initialize()

        # 预处理专利法律术语
        self.legal_terms = {
            "发明专利", "实用新型", "外观设计", "国防专利",
            "新颖性", "创造性", "实用性", "优先权", "现有技术",
            "初步审查", "实质审查", "复审", "无效宣告",
            "权利要求书", "说明书", "附图", "摘要",
            "专利申请", "专利授权", "专利侵权", "专利实施",
            "专利代理", "专利许可", "专利转让", "专利质押"
        }

        # 添加法律术语到jieba词典
        for term in self.legal_terms:
            jieba.add_word(term)

    async def load_documents(self, folder_path: str) -> List[Dict[str, Any]]:
        """加载文档"""
        folder_path = Path(folder_path)
        documents = []

        # 处理MD文件
        for md_file in folder_path.glob("*.md"):
            content = await self._read_file(md_file)
            if content:
                documents.append({
                    "path": str(md_file),
                    "name": md_file.name,
                    "content": content,
                    "type": "markdown"
                })

        # 处理DOCX文件
        for docx_file in folder_path.glob("*.docx"):
            content = await self._read_docx(docx_file)
            if content:
                documents.append({
                    "path": str(docx_file),
                    "name": docx_file.name,
                    "content": content,
                    "type": "docx"
                })

        # 处理PDF文件
        for pdf_file in folder_path.glob("*.pdf"):
            content = await self._read_pdf(pdf_file)
            if content:
                documents.append({
                    "path": str(pdf_file),
                    "name": pdf_file.name,
                    "content": content,
                    "type": "pdf"
                })

        logger.info(f"加载了 {len(documents)} 个文档")
        return documents

    async def _read_file(self, file_path: Path) -> str:
        """读取文件"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {e}")
            return ""

    async def _read_docx(self, file_path: Path) -> str:
        """读取Word文档"""
        try:
            from docx import Document
            doc = Document(file_path)
            return '\n'.join([para.text for para in doc.paragraphs])
        except ImportError:
            logger.error(f"需要安装python-docx: pip install python-docx")
            return ""
        except Exception as e:
            logger.error(f"读取DOCX文件失败 {file_path}: {e}")
            return ""

    async def _read_pdf(self, file_path: Path) -> str:
        """读取PDF文件"""
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                content = []
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text.strip():
                        content.append(text)
                return '\n'.join(content)
        except ImportError:
            logger.error(f"需要安装PyPDF2: pip install PyPDF2")
            return ""
        except Exception as e:
            logger.error(f"读取PDF文件失败 {file_path}: {e}")
            return ""

    def preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 清理文本
        text = re.sub(r'\s+', ' ', text)  # 合并空白字符
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', text)  # 保留中文、英文、数字

        return text

    def chunk_document(self, content: str, doc_name: str) -> List[Dict[str, Any]]:
        """文档分块"""
        content = self.preprocess_text(content)
        chunks = []

        # 按段落分割
        paragraphs = content.split('\n\n')
        current_chunk = ""
        chunk_id = 0

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

    def vectorize_chunks(self, chunks: List[Dict[str, Any]]) -> np.ndarray:
        """向量化文档块"""
        logger.info(f"开始向量化 {len(chunks)} 个文档块...")

        # 提取文本
        texts = [chunk["content"] for chunk in chunks]

        # 使用TF-IDF向量化
        vectorizer = TfidfVectorizer(
            max_features=5000,  # 最大特征数
            min_df=1,          # 最小文档频率
            max_df=0.8,        # 最大文档频率
            ngram_range=(1, 2),  # 1-gram和2-gram
            stop_words=None   # 保留所有词，包括法律术语
        )

        # 训练TF-IDF模型
        tfidf_matrix = vectorizer.fit_transform(texts)

        # 使用PCA降维
        if tfidf_matrix.shape[1] > self.vector_size:
            pca = PCA(n_components=self.vector_size, random_state=42)
            vectors = pca.fit_transform(tfidf_matrix.toarray())
            logger.info(f"使用PCA降维从 {tfidf_matrix.shape[1]} 到 {self.vector_size} 维")
        else:
            vectors = tfidf_matrix.toarray()
            self.vector_size = vectors.shape[1]
            logger.info(f"向量维度: {self.vector_size}")

        logger.info(f"向量化完成！")
        return vectors

    def prepare_qdrant_data(self, chunks: List[Dict[str, Any]], vectors: np.ndarray) -> Dict[str, Any]:
        """准备Qdrant导入数据"""
        points = []

        for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
            # 生成唯一ID
            point_id = hash(f"{chunk['doc_name']}_{chunk['chunk_id']}") & 0xFFFFFFFF

            point = {
                "id": point_id,
                "vector": vector.tolist(),
                "payload": {
                    "doc_name": chunk["doc_name"],
                    "chunk_id": chunk["chunk_id"],
                    "content": chunk["content"][:1000],  # 截断前1000字符
                    "char_count": chunk["char_count"],
                    "vectorizer": "tfidf",
                    "created_at": datetime.now().isoformat()
                }
            }
            points.append(point)

        return {
            "collection_name": "patent_legal_vectors_tfidf",
            "points": points
        }

    async def save_vectors(self, vectors: np.ndarray, chunks: List[Dict[str, Any]], output_path: str):
        """保存向量到文件"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "vectorizer": "tfidf",
            "vector_size": self.vector_size,
            "chunk_count": len(chunks),
            "chunks": chunks,
            "vectors": vectors.tolist(),
            "created_at": datetime.now().isoformat()
        }

        async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))

        logger.info(f"向量数据已保存到: {output_path}")

async def main():
    """主函数"""
    logger.info("开始使用TF-IDF替代方案进行专利法律法规向量化...")

    # 创建向量化器
    vectorizer = PatentLegalTFIDFVectorizer()

    # 加载文档
    documents = await vectorizer.load_documents("/Users/xujian/学习资料/专利/专利法律法规")

    # 处理所有文档
    all_chunks = []
    for doc in documents:
        chunks = vectorizer.chunk_document(doc["content"], doc["name"])
        all_chunks.extend(chunks)

    logger.info(f"总共生成 {len(all_chunks)} 个文档块")

    # 向量化
    vectors = vectorizer.vectorize_chunks(all_chunks)

    # 准备Qdrant数据
    qdrant_data = vectorizer.prepare_qdrant_data(all_chunks, vectors)

    # 保存数据
    output_path = "/Users/xujian/Athena工作平台/data/patent_legal_vectors_tfidf/patent_legal_vectors.json"
    await vectorizer.save_vectors(vectors, all_chunks, output_path)

    # 保存Qdrant导入数据
    qdrant_path = "/Users/xujian/Athena工作平台/data/patent_legal_vectors_tfidf/qdrant_import.json"
    qdrant_path_obj = Path(qdrant_path)
    qdrant_path_obj.parent.mkdir(parents=True, exist_ok=True)

    async with aiofiles.open(qdrant_path, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(qdrant_data, ensure_ascii=False, indent=2))

    logger.info("TF-IDF向量化处理完成！")
    logger.info(f"生成了 {len(vectors)} 个向量（{vectorizer.vector_size}维）")
    logger.info(f"数据已保存到: {output_path}")
    logger.info(f"Qdrant导入数据已保存到: {qdrant_path}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())