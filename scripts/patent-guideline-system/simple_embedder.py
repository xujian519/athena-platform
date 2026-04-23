#!/usr/bin/env python3
"""
简化的向量化服务
"""

import json
import logging
import os

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimplePatentGuidelineEmbedder:
    """简化的专利审查指南向量化器"""

    def __init__(self):
        """初始化向量化器"""
        model_path = '/Users/xujian/Athena工作平台/models/bge-large-zh-v1.5'
        self.model_name = model_path
        self.device = 'mps' if torch.backends.mps.is_available() else 'cpu'
        self.vector_size = 1024

        # 加载模型
        logger.info(f"加载模型: {model_path}")
        self.model = SentenceTransformer(
            model_path,
            device=self.device
        )
        logger.info(f"模型加载成功，设备: {self.device}")

    def encode_texts(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """批量编码文本"""
        logger.info(f"开始编码 {len(texts)} 个文本")
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        logger.info("编码完成")
        return embeddings

def main():
    """主函数"""
    # 创建向量化器
    embedder = SimplePatentGuidelineEmbedder()

    # 加载解析数据
    data_path = '/Users/xujian/Athena工作平台/patent-guideline-system/data/processed/test_parse_result.json'
    logger.info(f"加载数据: {data_path}")
    with open(data_path, encoding='utf-8') as f:
        data = json.load(f)

    # 提取文本内容
    texts = []
    metadata_list = []

    if 'structure' in data:
        for i, section in enumerate(data['structure']):
            if 'content' in section and section['content'].strip():
                # 只处理前500个章节
                if len(texts) >= 500:
                    break

                # 限制内容长度
                content = section['content'].strip()[:500]
                texts.append(content)

                metadata_list.append({
                    'id': section.get('id', f'section_{i}'),
                    'title': section.get('title', ''),
                    'level': section.get('level', 0),
                    'parent_id': section.get('parent_id', ''),
                    'page_number': section.get('page_number', 0)
                })

    logger.info(f"提取了 {len(texts)} 个文本段落")

    # 执行向量化
    embeddings = embedder.encode_texts(texts, batch_size=16)

    # 准备保存数据
    results = []
    for i, (text, embedding) in enumerate(zip(texts, embeddings, strict=False)):
        results.append({
            'id': metadata_list[i]['id'],
            'text': text,
            'embedding': embedding.tolist(),
            'metadata': metadata_list[i]
        })

    # 保存结果
    output_path = '/Users/xujian/Athena工作平台/patent-guideline-system/data/embeddings/guideline_embeddings_simple.json'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    save_data = {
        'model_name': embedder.model_name,
        'vector_size': embedder.vector_size,
        'device': embedder.device,
        'total_embeddings': len(results),
        'embeddings': results
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)

    logger.info(f"向量化完成！结果保存到: {output_path}")
    logger.info(f"共处理 {len(results)} 个段落")

    # 保存样本到Qdrant
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, PointStruct, VectorParams

        client = QdrantClient(host='localhost', port=6333)
        collection_name = 'patent_guidelines'

        # 创建集合
        if not client.collection_exists(collection_name):
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=embedder.vector_size,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"创建Qdrant集合: {collection_name}")

        # 准备数据点
        points = []
        for i, result in enumerate(results):
            points.append(PointStruct(
                id=i,
                vector=result['embedding'],
                payload={
                    'id': result['id'],
                    'text': result['text'][:200],  # 限制文本长度
                    'title': result['metadata']['title'],
                    'level': result['metadata']['level']
                }
            ))

        # 上传到Qdrant
        client.upsert(collection_name=collection_name, points=points)
        logger.info(f"成功上传 {len(points)} 个向量到Qdrant")

    except Exception as e:
        logger.error(f"上传到Qdrant失败: {e}")

if __name__ == '__main__':
    main()
