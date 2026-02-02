#!/usr/bin/env python3
"""
导入所有法律向量（1244个）
Import All Legal Vectors (1244 documents)
"""

import sqlite3
import json
import uuid
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, Distance, VectorParams
import numpy as np
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Qdrant客户端
client = QdrantClient(host="localhost", port=6333)

def import_all_legal_vectors():
    """导入所有法律向量"""
    logger.info("开始导入所有法律向量...")

    # 连接数据库
    db_path = "/Users/xujian/Athena工作平台/data/support_data/databases/legal_laws_database.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 获取法律文档信息
    cursor.execute("""
        SELECT ld.id, ld.title, ld.content, ld.doc_type, ld.category, le.embedding
        FROM law_documents ld
        JOIN law_embeddings le ON ld.id = le.law_id
    """)

    documents = cursor.fetchall()
    logger.info(f"找到 {len(documents)} 个法律文档（带向量）")

    # 创建或获取集合
    collection_name = "all_legal_vectors_1244"

    try:
        # 尝试获取集合
        client.get_collection(collection_name)
        logger.info(f"集合 {collection_name} 已存在，清空后重新导入")
        # 清空集合
        client.delete_collection(collection_name)
    except Exception:
        logger.info(f"创建新集合 {collection_name}")

    # 创建集合（假设向量是768维，使用sentence-transformers）
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=768, distance=Distance.COSINE)
    )

    # 导入向量数据
    points = []
    batch_size = 100
    imported_count = 0

    for i, (doc_id, title, content, doc_type, category, embedding_blob) in enumerate(documents):
        try:
            # 解码向量数据
            if isinstance(embedding_blob, bytes):
                embedding = np.frombuffer(embedding_blob, dtype=np.float32)
            else:
                embedding = np.array(json.loads(embedding_blob), dtype=np.float32)

            # 创建payload
            payload = {
                'doc_id': doc_id,
                'title': title,
                'content': content[:500] if content else '',  # 前500字符
                'doc_type': doc_type,
                'category': category,
                'source': 'legal_laws_database',
                'vector_dim': len(embedding)
            }

            # 创建点
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding.tolist(),
                payload=payload
            )

            points.append(point)
            imported_count += 1

            # 批量上传
            if len(points) >= batch_size:
                client.upsert(collection_name=collection_name, points=points)
                logger.info(f"已上传 {imported_count}/{len(documents)} 个向量")
                points = []

        except Exception as e:
            logger.error(f"处理文档 {doc_id} 失败: {e}")
            continue

    # 上传剩余的点
    if points:
        client.upsert(collection_name=collection_name, points=points)
        logger.info(f"最后上传 {len(points)} 个向量")
        imported_count += len(points)

    conn.close()

    # 验证导入
    collection_info = client.get_collection(collection_name)
    total_vectors = collection_info.points_count

    logger.info("=" * 50)
    logger.info(f"✅ 法律向量导入完成！")
    logger.info(f"   - 数据库文档数: {len(documents)}")
    logger.info(f"   - 成功导入向量: {imported_count}")
    logger.info(f"   - Qdrant集合: {collection_name}")
    logger.info(f"   - 向量总数: {total_vectors}")
    logger.info("=" * 50)

    return total_vectors

if __name__ == "__main__":
    import_all_legal_vectors()