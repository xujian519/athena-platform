#!/usr/bin/env python3
"""
专利复审无效向量库构建器
Patent Review and Invalidity Vector Builder

构建专业的专利复审和无效决策向量数据库

作者: Athena平台团队
创建时间: 2025-12-20
版本: v2.0.0
"""

from __future__ import annotations
import hashlib
import json
import logging
import re
import uuid
from collections import Counter
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
    vector: list[float]
    embedding_model: str

class PatentVectorBuilder:
    """专利向量库构建器"""

    def __init__(self):
        # 向量配置
        self.vector_dim = 1024  # BGE-M3向量维度（已更新）  # 默认维度
        self.chunk_size = 500  # 分块大小（字符数）
        self.overlap_size = 50  # 重叠大小

        # 文档类型
        self.doc_types = {
            "patent_review": "专利复审决定",
            "invalid_decision": "无效宣告决定",
            "evidence": "证据材料",
            "prior_art": "对比文件",
            "legal_basis": "法律依据",
            "technical_analysis": "技术分析报告"
        }

        # 分块策略
        self.chunk_patterns = [
            (r"请求人：", "申请人信息"),
            (r"专利号：", "专利号"),
            (r"申请号：", "申请号"),
            (r"发明名称：", "发明名称"),
            (r"决定要点", "决定要点"),
            (r"合议组认为", "合议组意见"),
            (r"基于.*证据", "证据引用"),
            (r"根据.*法第", "法律引用")
        ]

    def process_patent_documents(self, data_dir: Path, output_dir: Path):
        """处理专利文档"""
        logger.info(f"开始处理专利文档: {data_dir}")

        # 查找文档
        doc_files = []
        for pattern in ["**/*.json", "**/*.txt", "**/*.md", "**/*.docx"]:
            doc_files.extend(data_dir.glob(pattern))

        logger.info(f"找到 {len(doc_files)} 个文档")

        all_chunks = []

        for doc_path in doc_files:
            try:
                # 识别文档类型
                doc_type = self._identify_document_type(doc_path)

                # 读取文档
                content = self._read_document(doc_path)

                if not content:
                    continue

                # 预处理
                content = self._preprocess_content(content)

                # 分块
                chunks = self._chunk_document(content, doc_type, str(doc_path))

                all_chunks.extend(chunks)
                logger.info(f"  处理完成: {doc_path.name} ({len(chunks)}个块)")

            except Exception as e:
                logger.error(f"处理文档失败 {doc_path}: {e}")

        # 生成向量
        logger.info("\n🔄 生成向量嵌入...")
        chunks_with_vectors = self._generate_vectors(all_chunks)

        # 保存结果
        self._save_vectors(chunks_with_vectors, output_dir)

        logger.info(f"✅ 向量库构建完成，总计 {len(chunks_with_vectors)} 个向量")

    def _identify_document_type(self, doc_path: Path) -> str:
        """识别文档类型"""
        filename = doc_path.name.lower()
        filepath = str(doc_path).lower()

        if "复审" in filename or "review" in filename:
            return "patent_review"
        elif "无效" in filename or "invalid" in filename:
            return "invalid_decision"
        elif "证据" in filename or "evidence" in filename:
            return "evidence"
        elif "对比" in filename or "prior" in filename:
            return "prior_art"
        elif "技术分析" in filename or "analysis" in filename:
            return "technical_analysis"
        else:
            return "unknown"

    def _read_document(self, doc_path: Path) -> str | None:
        """读取文档"""
        try:
            if doc_path.suffix == '.json':
                with open(doc_path, encoding='utf-8') as f:
                    data = json.load(f)
                    # 提取文本内容
                    if isinstance(data, dict):
                        # 尝试常见的文本字段
                        for field in ['content', 'text', 'decision', 'reasoning', 'body']:
                            if field in data and data[field]:
                                return str(data[field])
                        # 递归查找
                        return self._extract_text_from_dict(data)
                    elif isinstance(data, list):
                        return ' '.join(str(item) for item in data)
                    else:
                        return str(data)
            else:
                with open(doc_path, encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            logger.error(f"读取文件失败 {doc_path}: {e}")
            return None

    def _extract_text_from_dict(self, data: dict) -> str:
        """从字典中递归提取文本"""
        text_parts = []
        for _key, value in data.items():
            if isinstance(value, str):
                text_parts.append(value)
            elif isinstance(value, dict):
                text_parts.append(self._extract_text_from_dict(value))
            elif isinstance(value, list):
                text_parts.extend(str(item) for item in value)
        return ' '.join(text_parts)

    def _preprocess_content(self, content: str) -> str:
        """预处理内容"""
        # 清理空白
        content = re.sub(r'\s+', ' ', content)

        # 移除页眉页脚
        content = re.sub(r'^\s*第\s*\d+\s*页\s*$', '', content, flags=re.MULTILINE)

        # 标准化引用格式
        content = re.sub(r'CN\s*(\d+)', r'CN\1', content)

        return content.strip()

    def _chunk_document(self, content: str, doc_type: str, doc_path: str) -> list[dict]:
        """分块处理文档"""
        chunks = []

        # 按段落分块
        paragraphs = content.split('\n\n')
        current_chunk = ""
        current_size = 0
        chunk_index = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # 检查是否需要新分块
            if current_size + len(paragraph) > self.chunk_size and current_chunk:
                # 保存当前块
                chunk = self._create_chunk(
                    current_chunk,
                    chunk_index,
                    doc_type,
                    doc_path
                )
                chunks.append(chunk)

                # 开始新块（带重叠）
                overlap_text = current_chunk[-self.overlap_size:] if len(current_chunk) > self.overlap_size else ""
                current_chunk = overlap_text + "\n\n" + paragraph
                current_size = len(current_chunk)
                chunk_index += 1
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                current_size += len(paragraph)

        # 保存最后一个块
        if current_chunk:
            chunk = self._create_chunk(
                current_chunk,
                chunk_index,
                doc_type,
                doc_path
            )
            chunks.append(chunk)

        return chunks

    def _create_chunk(self, content: str, index: int, doc_type: str, doc_path: str) -> dict:
        """创建文档块"""
        # 提取专利号
        patent_numbers = re.findall(r'CN\s*\d+[A-Z]', content)

        # 提取IPC分类
        ipc_classes = re.findall(r'[A-H]\d{2}[A-Z]', content)

        # 提取法律引用
        legal_refs = re.findall(r'专利法第\d+条', content)

        return {
            "chunk_id": str(uuid.uuid4()),
            "content": content,
            "doc_type": doc_type,
            "metadata": {
                "source_file": str(doc_path),
                "chunk_index": index,
                "char_count": len(content),
                "patent_numbers": patent_numbers,
                "ipc_classes": ipc_classes,
                "legal_references": legal_refs,
                "created_at": datetime.now().isoformat()
            }
        }

    def _generate_vectors(self, chunks: list[dict]) -> list[PatentChunk]:
        """生成向量"""
        chunks_with_vectors = []

        for chunk in chunks:
            # 简单的哈希向量生成（实际应使用专业模型）
            content_hash = hashlib.sha256(chunk["content"].encode('utf-8')).hexdigest()

            # 转换为向量
            vector = []
            for i in range(0, len(content_hash), 2):
                hex_pair = content_hash[i:i+2]
                val = int(hex_pair, 16) / 255.0
                vector.append(val)

            # 调整维度
            while len(vector) < self.vector_dim:
                vector.extend(vector[:self.vector_dim - len(vector)])
            vector = vector[:self.vector_dim]

            patent_chunk = PatentChunk(
                chunk_id=chunk["chunk_id"],
                content=chunk["content"],
                doc_type=chunk["doc_type"],
                metadata=chunk["metadata"],
                vector=vector,
                embedding_model="hash_based"
            )
            chunks_with_vectors.append(patent_chunk)

        return chunks_with_vectors

    def _save_vectors(self, chunks: list[PatentChunk], output_dir: Path):
        """保存向量"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 创建输出目录
        vector_dir = output_dir / "patent_review_invalid_vectors"
        vector_dir.mkdir(parents=True, exist_ok=True)

        # 转换为可序列化格式
        vectors_data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "description": "专利复审无效向量数据库",
                "total_chunks": len(chunks),
                "vector_dim": self.vector_dim,
                "embedding_model": "hash_based"
            },
            "chunks": []
        }

        for chunk in chunks:
            vectors_data["chunks"].append({
                "chunk_id": chunk.chunk_id,
                "content": chunk.content,
                "doc_type": chunk.doc_type,
                "metadata": chunk.metadata,
                "vector": chunk.vector
            })

        # 保存向量数据
        vectors_file = vector_dir / f"patent_vectors_{timestamp}.json"
        with open(vectors_file, 'w', encoding='utf-8') as f:
            json.dump(vectors_data, f, ensure_ascii=False, indent=2)

        # 生成Qdrant导入格式
        qdrant_points = []
        for chunk in chunks:
            point = {
                "id": str(uuid.uuid5(uuid.NAMESPACE_URL, chunk.chunk_id)),
                "vector": chunk.vector,
                "payload": {
                    "chunk_id": chunk.chunk_id,
                    "content": chunk.content[:500] + "..." if len(chunk.content) > 500 else chunk.content,
                    "doc_type": chunk.doc_type,
                    "patent_numbers": chunk.metadata.get("patent_numbers", []),
                    "ipc_classes": chunk.metadata.get("ipc_classes", []),
                    "source_file": chunk.metadata.get("source_file", ""),
                    "created_at": chunk.metadata.get("created_at", "")
                }
            }
            qdrant_points.append(point)

        qdrant_file = vector_dir / f"qdrant_patent_vectors_{timestamp}.json"
        with open(qdrant_file, 'w', encoding='utf-8') as f:
            json.dump(qdrant_points, f, ensure_ascii=False, indent=2)

        # 保存统计信息
        stats = {
            "timestamp": datetime.now().isoformat(),
            "doc_type_stats": dict(Counter(c.doc_type for c in chunks)),
            "avg_chunk_size": sum(c.metadata.get("char_count", 0) for c in chunks) / len(chunks) if chunks else 0,
            "total_patents": len({patent for chunk in chunks for patent in chunk.metadata.get("patent_numbers", [])}),
            "total_ipc_classes": len({ipc for chunk in chunks for ipc in chunk.metadata.get("ipc_classes", [])})
        }

        stats_file = vector_dir / f"patent_vector_stats_{timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        logger.info("\n💾 向量数据已保存:")
        logger.info(f"  向量文件: {vectors_file}")
        logger.info(f"  Qdrant文件: {qdrant_file}")
        logger.info(f"  统计文件: {stats_file}")

def main():
    """主函数"""
    print("="*100)
    print("🔢 专利复审无效向量库构建器 🔢")
    print("="*100)

    builder = PatentVectorBuilder()

    # 数据目录
    data_dir = Path("/Users/xujian/Athena工作平台/dev/tools/patent_data")
    output_dir = Path("/Users/xujian/Athena工作平台/production/data/vector_db")

    if not data_dir.exists():
        logger.error(f"数据目录不存在: {data_dir}")
        logger.info("请将专利数据放入该目录，或修改数据路径")
        return

    # 处理文档
    builder.process_patent_documents(data_dir, output_dir)

if __name__ == "__main__":
    main()
