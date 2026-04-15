#!/usr/bin/env python3
"""
专利向量库构建器（集成本地NLP）
Patent Vector Builder with Local NLP Integration

利用本地NLP系统构建高质量的专利向量数据库

作者: Athena平台团队
创建时间: 2025-12-20
版本: v3.0.0
"""

from __future__ import annotations
import asyncio
import hashlib
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PatentChunk:
    """专利文档块"""
    chunk_id: str
    content: str
    doc_type: str
    metadata: dict
    embedding: list[float]
    embedding_model: str

class PatentVectorBuilderWithNLP:
    """专利向量库构建器（集成NLP）"""

    def __init__(self):
        # NLP服务配置
        self.nlp_url = "http://localhost:8001"
        self.embedding_model = "patent_bert"  # 使用专利BERT模型
        self.vector_dim = 1024

        # 分块配置
        self.chunk_size = 500  # 字符数
        self.overlap_size = 50
        self.batch_size = 10

        # 文档类型分类
        self.doc_types = {
            "patent_review": "专利复审决定",
            "invalid_decision": "无效宣告决定",
            "patent_grant": "专利授权决定",
            "patent_rejection": "专利驳回决定",
            "opposition": "专利异议决定",
            "prior_art": "现有技术",
            "technical_analysis": "技术分析报告",
            "infringement_analysis": "侵权分析",
            "licensing_agreement": "许可协议",
            "patent_litigation": "专利诉讼"
        }

        # 向量集合配置
        self.collections = {
            "patent_review_invalid": {
                "name": "专利复审无效向量库",
                "description": "专利复审和无效宣告决定的向量数据库"
            },
            "patent_analysis": {
                "name": "专利分析向量库",
                "description": "技术分析、侵权分析等专业报告的向量数据库"
            },
            "prior_art": {
                "name": "现有技术向量库",
                "description": "对比文件、现有技术的向量数据库"
            }
        }

    async def extract_vector_with_nlp(self, text: str) -> list[float]:
        """使用NLP服务提取向量"""
        try:
            # 使用专业NLP适配器
            from nlp_adapter_professional import ProfessionalNLPAdapter

            async with ProfessionalNLPAdapter(self.nlp_url) as adapter:
                vector = await adapter.encode_text(text, self.embedding_model)

                # 确保维度正确
                if len(vector) != self.vector_dim:
                    if len(vector) > self.vector_dim:
                        vector = vector[:self.vector_dim]
                    else:
                        vector.extend([0.0] * (self.vector_dim - len(vector)))

                logger.debug(f"成功生成向量，维度: {len(vector)}")
                return vector

        except Exception as e:
            logger.error(f"NLP调用失败: {e}")
            logger.info("使用后备哈希向量方法")

        # 使用哈希向量作为后备
        return self._generate_hash_vector(text)

    def _generate_hash_vector(self, text: str) -> list[float]:
        """生成哈希向量（后备方案）"""
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        vector = []
        for i in range(0, len(text_hash), 2):
            hex_pair = text_hash[i:i+2]
            val = int(hex_pair, 16) / 255.0
            vector.append(val)

        # 调整到指定维度
        while len(vector) < self.vector_dim:
            vector.extend(vector[:self.vector_dim - len(vector)])
        return vector[:self.vector_dim]

    async def process_document_with_nlp(self, doc: dict, collection_name: str) -> list[PatentChunk]:
        """使用NLP处理单个文档"""
        # 获取文档内容
        content = self._extract_content(doc)
        if not content:
            return []

        # 识别文档类型
        doc_type = self._identify_document_type(doc, content)

        # 使用NLP进行文档分析和分块
        chunks = await self._smart_chunk_with_nlp(content, doc_type)

        # 生成向量
        chunks_with_vectors = []
        for chunk in chunks:
            vector = await self.extract_vector_with_nlp(chunk['content'])

            patent_chunk = PatentChunk(
                chunk_id=chunk['chunk_id'],
                content=chunk['content'],
                doc_type=doc_type,
                metadata={
                    **chunk['metadata'],
                    "collection": collection_name,
                    "processed_at": datetime.now().isoformat(),
                    "doc_info": {
                        "title": doc.get("title", ""),
                        "source": doc.get("source", "")
                    }
                },
                embedding=vector,
                embedding_model=self.embedding_model
            )
            chunks_with_vectors.append(patent_chunk)

        return chunks_with_vectors

    async def _smart_chunk_with_nlp(self, content: str, doc_type: str) -> list[dict]:
        """使用NLP智能分块"""
        try:
            # 使用专业NLP适配器
            from nlp_adapter_professional import ProfessionalNLPAdapter

            async with ProfessionalNLPAdapter(self.nlp_url) as adapter:
                chunks = await adapter.smart_chunk(
                    content,
                    chunk_size=self.chunk_size,
                    overlap=self.overlap_size
                )
                logger.info(f"生成了 {len(chunks)} 个智能分块")
                return chunks

        except Exception as e:
            logger.error(f"NLP分块调用失败: {e}")
            logger.info("使用默认分块方法")

        # 使用默认分块作为后备
        return self._default_chunk(content, doc_type)

    def _default_chunk(self, content: str, doc_type: str) -> list[dict]:
        """默认分块方法"""
        chunks = []
        paragraphs = content.split('\n\n')
        current_chunk = ""
        current_size = 0
        chunk_index = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            if current_size + len(paragraph) > self.chunk_size and current_chunk:
                chunk = {
                    "chunk_id": str(uuid.uuid4()),
                    "content": current_chunk,
                    "metadata": {
                        "chunk_index": chunk_index,
                        "char_count": len(current_chunk),
                        "doc_type": doc_type
                    }
                }
                chunks.append(chunk)

                # 保留重叠
                words = current_chunk.split()
                overlap_words = words[-len(words)//3:]
                current_chunk = " ".join(overlap_words) + "\n\n" + paragraph
                current_size = len(current_chunk)
                chunk_index += 1
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                current_size += len(paragraph)

        if current_chunk:
            chunk = {
                "chunk_id": str(uuid.uuid4()),
                "content": current_chunk,
                "metadata": {
                    "chunk_index": chunk_index,
                    "char_count": len(current_chunk),
                    "doc_type": doc_type
                }
            }
            chunks.append(chunk)

        return chunks

    def _extract_content(self, doc: dict) -> str:
        """提取文档内容"""
        if isinstance(doc, str):
            return doc

        # 递归提取字典中的文本
        def extract_text(data):
            if isinstance(data, str):
                return data
            elif isinstance(data, dict):
                text_parts = []
                for key in ['content', 'text', 'body', 'decision', 'reasoning', 'abstract', 'claims']:
                    if key in data and data[key]:
                        text_parts.append(str(data[key]))
                # 递归处理嵌套结构
                for value in data.values():
                    nested_text = extract_text(value)
                    if nested_text:
                        text_parts.append(nested_text)
                return ' '.join(text_parts)
            elif isinstance(data, list):
                return ' '.join(extract_text(item) for item in data)
            else:
                return str(data)

        return extract_text(doc)

    def _identify_document_type(self, doc: dict, content: str) -> str:
        """识别文档类型"""
        # 检查文档标题
        title = doc.get("title", "").lower()
        content_lower = content.lower()

        if "复审" in title or "复审" in content_lower:
            return "patent_review"
        elif "无效" in title or "无效" in content_lower:
            return "invalid_decision"
        elif "授权" in title or "授权" in content_lower:
            return "patent_grant"
        elif "驳回" in title or "驳回" in content_lower:
            return "patent_rejection"
        elif "异议" in title or "异议" in content_lower:
            return "opposition"
        elif "现有技术" in title or "对比文件" in content_lower or "prior art" in content_lower:
            return "prior_art"
        elif "技术分析" in title or "技术" in content_lower and "分析" in content_lower:
            return "technical_analysis"
        elif "侵权" in title or "侵权" in content_lower:
            return "infringement_analysis"
        elif "许可" in title or "许可" in content_lower:
            return "licensing_agreement"
        elif "诉讼" in title or "诉讼" in content_lower:
            return "patent_litigation"
        else:
            return "unknown"

    async def process_document_collection(self, docs: list[dict], collection_name: str, collection_info: dict):
        """处理文档集合"""
        logger.info(f"\n🔄 处理文档集合: {collection_info['name']}")
        logger.info(f"   文档数: {len(docs)}")

        all_chunks = []
        for i, doc in enumerate(docs[:50]):  # 限制处理数量
            logger.info(f"  处理文档 {i+1}/{min(50, len(docs))}: {doc.get('title', 'Unknown')}")
            chunks = await self.process_document_with_nlp(doc, collection_name)
            all_chunks.extend(chunks)

        # 保存向量数据
        self._save_vectors(all_chunks, collection_name, collection_info)

        # 生成Qdrant导入文件
        self._generate_qdrant_import(all_chunks, collection_name)

        logger.info(f"✅ 集合 '{collection_info['name']}' 完成，生成 {len(all_chunks)} 个向量")

    def _save_vectors(self, chunks: list[PatentChunk], collection_name: str, collection_info: dict):
        """保存向量数据"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 创建输出目录
        output_dir = Path(f"/Users/xujian/Athena工作平台/production/data/vector_db/{collection_name}")
        output_dir.mkdir(parents=True, exist_ok=True)

        # 转换为可序列化格式
        vectors_data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "collection_name": collection_name,
                "description": collection_info["description"],
                "total_chunks": len(chunks),
                "vector_dim": self.vector_dim,
                "embedding_model": self.embedding_model,
                "nlp_integration": True
            },
            "chunks": []
        }

        for chunk in chunks:
            vectors_data["chunks"].append({
                "chunk_id": chunk.chunk_id,
                "content": chunk.content,
                "doc_type": chunk.doc_type,
                "metadata": chunk.metadata,
                "vector": chunk.embedding
            })

        # 保存向量数据
        vectors_file = output_dir / f"vectors_{timestamp}.json"
        with open(vectors_file, 'w', encoding='utf-8') as f:
            json.dump(vectors_data, f, ensure_ascii=False, indent=2)

        # 保存统计
        doc_type_stats = {}
        for chunk in chunks:
            doc_type = chunk.doc_type
            if doc_type not in doc_type_stats:
                doc_type_stats[doc_type] = 0
            doc_type_stats[doc_type] += 1

        stats = {
            "timestamp": datetime.now().isoformat(),
            "doc_type_distribution": doc_type_stats,
            "avg_chunk_size": sum(chunk.metadata.get("char_count", 0) for chunk in chunks) / len(chunks),
            "embedding_model": self.embedding_model
        }

        stats_file = output_dir / f"stats_{timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        logger.info(f"  📊 保存: {vectors_file}")

    def _generate_qdrant_import(self, chunks: list[PatentChunk], collection_name: str):
        """生成Qdrant导入文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 转换为Qdrant格式
        qdrant_points = []
        for chunk in chunks:
            # 提取关键信息作为payload
            keywords = self._extract_keywords(chunk.content)

            point = {
                "id": str(uuid.uuid5(uuid.NAMESPACE_URL, chunk.chunk_id)),
                "vector": chunk.embedding,
                "payload": {
                    "chunk_id": chunk.chunk_id,
                    "content": chunk.content[:500] + "..." if len(chunk.content) > 500 else chunk.content,
                    "doc_type": chunk.doc_type,
                    "keywords": keywords[:10],  # 限制关键词数量
                    "char_count": chunk.metadata.get("char_count", 0),
                    "collection": collection_name,
                    "processed_at": chunk.metadata.get("processed_at"),
                    "doc_title": chunk.metadata.get("doc_info", {}).get("title", ""),
                    "doc_source": chunk.metadata.get("doc_info", {}).get("source", ""),
                    "embedding_model": chunk.embedding_model
                }
            }
            qdrant_points.append(point)

        # 保存Qdrant导入文件
        output_dir = Path(f"/Users/xujian/Athena工作平台/production/data/vector_db/{collection_name}")
        qdrant_file = output_dir / f"qdrant_import_{timestamp}.json"

        with open(qdrant_file, 'w', encoding='utf-8') as f:
            json.dump(qdrant_points, f, ensure_ascii=False, indent=2)

        logger.info(f"  📦 Qdrant导入文件: {qdrant_file}")

    def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词"""
        # 专利相关关键词
        patent_keywords = [
            "新颖性", "创造性", "实用性", "现有技术", "对比文件",
            "权利要求", "独立权利要求", "从属权利要求", "技术方案",
            "技术特征", "技术效果", "技术领域", "背景技术",
            "发明内容", "具体实施方式", "附图说明",
            "专利法", "实施细则", "审查指南",
            "复审", "无效", "授权", "驳回", "异议",
            "侵权", "许可", "转让", "诉讼"
        ]

        keywords = []
        text_lower = text.lower()
        for keyword in patent_keywords:
            if keyword in text_lower:
                keywords.append(keyword)

        return keywords

async def main():
    """主函数"""
    print("="*100)
    print("🔢 专利向量库构建器（NLP集成） 🔢")
    print("="*100)

    builder = PatentVectorBuilderWithNLP()

    # 模拟数据集
    sample_datasets = {
        "patent_review_invalid": {
            "name": "专利复审无效向量库",
            "description": "专利复审决定和无效宣告决定的向量数据库",
            "docs": [
                {
                    "title": "CN202000000000.0 复审决定",
                    "content": """
                    复审请求审查决定书

                    专利号：CN202000000000.0
                    申请号：202000000000.0
                    发明名称：一种数据处理系统

                    复审请求人：甲公司
                    专利权人：甲公司

                    复审请求人于2023年01月01日向专利复审委员会提出复审请求。
                    经审查，本申请不符合专利法第22条第3款的规定。
                    """
                },
                {
                    "title": "CN202100000000.0 无效宣告请求审查决定",
                    "content": """
                    无效宣告请求审查决定

                    专利号：CN202100000000.0
                    申请号：202100000000.0
                    发明名称：一种新型装置

                    无效宣告请求人：乙公司
                    专利权人：丙公司

                    本决定针对专利号为CN202100000000.0的发明专利。
                    基于专利法第45条的规定，本专利权被宣告无效。
                    """
                }
            ]
        },
        "patent_analysis": {
            "name": "专利分析向量库",
            "description": "技术分析、侵权分析等专业报告的向量数据库",
            "docs": [
                {
                    "title": "技术分析报告",
                    "content": """
                    技术分析报告

                    分析对象：CN202000000000.0
                    分析时间：2023年06月01日

                    技术领域：数据处理
                    技术问题：提高数据处理效率
                    技术方案：采用优化算法

                    本报告详细分析了专利的技术方案，
                    并与现有技术进行了对比分析。
                    """
                }
            ]
        },
        "prior_art": {
            "name": "现有技术向量库",
            "description": "对比文件、现有技术的向量数据库",
            "docs": [
                {
                    "title": "对比文件1",
                    "content": """
                    对比文件1：CN1099999999A

                    公开日期：2020年01月01日

                    技术领域：数据处理
                    发明内容：一种数据处理方法

                    本对比文件公开了一种与本案相似的技术方案。
                    """
                }
            ]
        }
    }

    # 处理各个集合
    for collection_name, collection_data in sample_datasets.items():
        await builder.process_document_collection(
            collection_data["docs"],
            collection_name,
            collection_data
        )

    print("\n✅ 所有专利向量库构建完成！")

if __name__ == "__main__":
    asyncio.run(main())
