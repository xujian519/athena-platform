#!/usr/bin/env python3
"""
简化版专利法律法规向量化方案
Simplified Patent Legal Vectorization Solution

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
import jieba
import re

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimplePatentLegalVectorizer:
    """简化版专利法律法规向量化器"""

    def __init__(self):
        """初始化"""
        # 初始化jieba分词器
        jieba.initialize()
        logger.info("简化版向量化器初始化完成")

    async def load_documents(self, folder_path: str) -> List[Dict[str, Any]]:
        """加载并处理文档"""
        folder_path = Path(folder_path)
        processed_docs = []

        # 遍历所有文件
        for file_path in folder_path.glob("*"):
            if file_path.is_file():
                content = await self._extract_content(file_path)
                if content and len(content.strip()) > 100:  # 只处理有实质内容的文件
                    processed_docs.append({
                        "file_name": file_path.name,
                        "file_path": str(file_path),
                        "content": content,
                        "type": file_path.suffix[1:].upper() if file_path.suffix else "UNKNOWN"
                    })

        logger.info(f"处理了 {len(processed_docs)} 个文件")
        return processed_docs

    async def _extract_content(self, file_path: Path) -> str:
        """提取文件内容"""
        try:
            if file_path.suffix.lower() == '.md':
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    return await f.read()
            elif file_path.suffix.lower() == '.docx':
                # 使用python-docx读取Word文档
                from docx import Document
                doc = Document(file_path)
                return '\n'.join([para.text for para in doc.paragraphs if para.text.strip()])
            elif file_path.suffix.lower() == '.pdf':
                # 使用PyPDF2读取PDF
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

    def create_simple_vectors(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """创建简单的向量表示"""
        vectors = []

        for doc in documents:
            # 清理文本
            content = self._clean_text(doc["content"])

            # 提取关键信息
            key_info = {
                "file_name": doc["file_name"],
                "file_type": doc["type"],
                "word_count": len(content),
                "char_count": len(content),
                "has_patent_terms": any(term in content for term in ["专利", "发明", "实用新型", "外观设计"]),
                "has_legal_terms": any(term in content for term in ["法条", "规定", "办法", "实施细则"])
            }

            # 使用词频作为简单的向量特征
            words = list(jieba.cut(content))
            word_freq = {}
            for word in words:
                if len(word) > 1:  # 过滤单字符
                    word_freq[word] = word_freq.get(word, 0) + 1

            # 创建特征向量
            features = []

            # 1. 文档类型one-hot
            doc_types = ["MD", "DOCX", "PDF", "UNKNOWN"]
            for dt in doc_types:
                features.append(1.0 if doc["type"] == dt else 0.0)

            # 2. 长度特征
            features.append(len(content) / 10000.0)  # 标准化文档长度

            # 3. 关键词特征
            legal_keywords = ["专利", "发明", "实用新型", "外观设计", "新颖性", "创造性", "实用性",
                            "权利要求", "说明书", "申请", "授权", "侵权", "代理", "许可", "转让"]
            for keyword in legal_keywords:
                features.append(content.count(keyword) / 100.0)  # 标准化关键词频率

            # 4. 中文文本比例
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
            features.append(chinese_chars / len(content))

            # 5. 数字密度
            digits = len(re.findall(r'\d', content))
            features.append(digits / len(content))

            # 创建向量对象
            vector_obj = {
                "doc_id": hash(doc["file_name"]) & 0xFFFFFFFF,
                "source": doc["file_path"],
                "content": content[:500],  # 前500字符作为内容预览
                "vector": features,
                "metadata": key_info,
                "created_at": datetime.now().isoformat()
            }

            vectors.append(vector_obj)

        logger.info(f"创建了 {len(vectors)} 个向量")
        return vectors

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除多余的空白
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊字符
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', text)
        return text.strip()

    def prepare_qdrant_data(self, vectors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """准备Qdrant导入数据"""
        points = []

        for vector_obj in vectors:
            point = {
                "id": vector_obj["doc_id"],
                "vector": vector_obj["vector"],
                "payload": {
                    "file_name": vector_obj["source"].split("/")[-1],
                    "content": vector_obj["content"],
                    "vector_type": "simple_features",
                    "word_count": vector_obj["metadata"]["word_count"],
                    "char_count": vector_obj["metadata"]["char_count"],
                    "has_patent_terms": vector_obj["metadata"]["has_patent_terms"],
                    "has_legal_terms": vector_obj["metadata"]["has_legal_terms"],
                    "created_at": vector_obj["created_at"]
                }
            }
            points.append(point)

        return {
            "collection_name": "patent_legal_vectors_simple",
            "points": points
        }

    async def save_results(self, vectors: List[Dict[str, Any]], qdrant_data: Dict[str, Any]):
        """保存结果"""
        # 保存向量数据
        vectors_path = "/Users/xujian/Athena工作平台/data/patent_legal_vectors_simple/vectors.json"
        vectors_path_obj = Path(vectors_path)
        vectors_path_obj.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(vectors_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(vectors, ensure_ascii=False, indent=2))

        # 保存Qdrant导入数据
        qdrant_path = "/Users/xujian/Athena工作平台/data/patent_legal_vectors_simple/qdrant_import.json"
        qdrant_path_obj = Path(qdrant_path)
        qdrant_path_obj.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(qdrant_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(qdrant_data, ensure_ascii=False, indent=2))

        # 创建统计信息
        stats = {
            "total_documents": len(set(v["source"] for v in vectors)),
            "total_vectors": len(vectors),
            "vector_dimension": len(vectors[0]["vector"]) if vectors else 0,
            "created_at": datetime.now().isoformat()
        }

        stats_path = "/Users/xujian/Athena工作平台/data/patent_legal_vectors_simple/stats.json"
        async with aiofiles.open(stats_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(stats, ensure_ascii=False, indent=2))

        logger.info(f"数据已保存:")
        logger.info(f"  向量数据: {vectors_path}")
        logger.info(f"  Qdrant数据: {qdrant_path}")
        logger.info(f"  统计信息: {stats_path}")

async def main():
    """主函数"""
    logger.info("开始简化版专利法律法规向量化...")

    # 创建向量化器
    vectorizer = SimplePatentLegalVectorizer()

    # 加载文档
    documents = await vectorizer.load_documents("/Users/xujian/学习资料/专利/专利法律法规")

    if not documents:
        logger.error("没有找到有效的文档")
        return

    # 创建向量
    vectors = vectorizer.create_simple_vectors(documents)

    # 准备Qdrant数据
    qdrant_data = vectorizer.prepare_qdrant_data(vectors)

    # 保存结果
    await vectorizer.save_results(vectors, qdrant_data)

    logger.info("✅ 简化版向量化处理完成！")

    # 打印统计信息
    logger.info(f"\n处理统计:")
    logger.info(f"  处理文档数: {len(documents)}")
    logger.info(f"  生成向量数: {len(vectors)}")
    logger.info(f"  向量维度: {len(vectors[0]['vector']) if vectors else 0}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())