#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将专利审查指南向量导入Qdrant
"""

import json
import pickle
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_to_qdrant():
    """导入向量到Qdrant"""
    client = QdrantClient(host="localhost", port=6333, check_compatibility=False)

    collection_name = "patent_guideline"

    # 创建集合
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE)
        )
        logger.info(f"✅ 创建集合: {collection_name}")

    # 加载向量数据
    with open("/Users/xujian/Athena工作平台/data/guideline_vectors/patent_guideline_vectors.json", "r") as f:
        data = json.load(f)

    # 批量导入
    points = []
    for item in data["vectors"]:
        point = PointStruct(
            id=item["id"],
            vector=item["vector"],
            payload=item["payload"]
        )
        points.append(point)

    # 分批上传
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i+batch_size]
        client.upsert(collection_name=collection_name, points=batch)
        logger.info(f"✅ 导入批次 {i//batch_size + 1}/{(len(points)-1)//batch_size + 1}")

    logger.info(f"✅ 总计导入 {len(points)} 个向量到 {collection_name}")

if __name__ == "__main__":
    import_to_qdrant()
