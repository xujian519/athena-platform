#!/usr/bin/env python3
"""
简单法律向量导入脚本
Simple Legal Vector Importer
"""

import json
import os
import uuid
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, Distance, VectorParams
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Qdrant客户端
client = QdrantClient(host="localhost", port=6333)

def import_patent_legal_vectors():
    """导入专利法律向量"""
    logger.info("开始导入专利法律向量...")

    # 查找所有法律向量文件
    vector_dir = "/Users/xujian/Athena工作平台/data/legal_patent_vectors"
    vector_files = [f for f in os.listdir(vector_dir) if f.endswith('.json')]

    logger.info(f"找到 {len(vector_files)} 个向量文件")

    # 创建集合
    collection_name = "patent_legal_vectors"

    try:
        # 检查集合是否存在
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]

        if collection_name not in collection_names:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
            )
            logger.info(f"✅ 创建集合 {collection_name}")

        # 导入向量数据
        total_points = 0
        for vector_file in vector_files:
            file_path = os.path.join(vector_dir, vector_file)
            logger.info(f"导入文件: {vector_file}")

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            points = []
            for idx, item in enumerate(data):
                if isinstance(item, dict) and 'vector' in item and 'chunk_info' in item:
                    point_id = str(uuid.uuid4())
                    vector = item['vector']
                    chunk_info = item['chunk_info']

                    payload = {
                        'doc_name': chunk_info.get('doc_name', ''),
                        'doc_type': chunk_info.get('doc_type', ''),
                        'content': chunk_info.get('content', '')[:500],  # 前500字符
                        'file_path': chunk_info.get('file_path', ''),
                        'source': 'legal_patent_vectors'
                    }

                    points.append(PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload
                    ))

            # 分批上传
            if points:
                # 每100个一批
                batch_size = 100
                for i in range(0, len(points), batch_size):
                    batch = points[i:i+batch_size]
                    client.upsert(collection_name=collection_name, points=batch)
                    total_points += len(batch)
                    logger.info(f"已上传 {total_points} 个向量")

        logger.info(f"✅ 成功导入 {total_points} 个专利法律向量")

    except Exception as e:
        logger.error(f"导入失败: {e}")

if __name__ == "__main__":
    import_patent_legal_vectors()