#!/usr/bin/env python3
"""
完全离线的专利向量化工具
Offline Patent Vectorization Tool

直接使用本地缓存的模型文件，无需网络连接
"""

import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import psycopg2
import torch
from transformers import AutoModel, AutoTokenizer

# 设置环境变量强制离线
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'
os.environ['HF_HUB_OFFLINE'] = '1'

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'patent_db'
}

class OfflineVectorizer:
    """完全离线的向量化器"""

    def __init__(self):
        """初始化离线向量化器"""
        self.tokenizer = None
        self.model = None
        self.device = 'cpu'
        self.embedding_dim = 768
        self.model_path = None

    def find_local_model(self) -> str | None:
        """查找本地模型"""
        # 检查huggingface缓存
        hf_cache = Path.home() / '.cache' / 'huggingface' / 'hub'

        # 优先级模型列表
        preferred_models = [
            'models--BAAI--bge-base-zh-v1.5',
            'models--shibing624--text2vec-base-chinese',
            'models--bert-base-chinese'
        ]

        for model_name in preferred_models:
            model_path = hf_cache / model_name
            if model_path.exists():
                logger.info(f"✅ 找到本地模型: {model_name}")
                logger.info(f"   路径: {model_path}")
                return str(model_path)

        return None

    def load_model_from_cache(self) -> bool:
        """从缓存加载模型"""
        try:
            model_path = self.find_local_model()

            if not model_path:
                logger.error('❌ 未找到本地模型缓存')
                return False

            logger.info(f"📥 从缓存加载模型: {model_path}")

            # 直接从缓存路径加载
            if 'bge-base-zh-v1.5' in model_path:
                # BGE模型
                from sentence_transformers import SentenceTransformer

                # 使用离线模式加载
                self.model = SentenceTransformer(
                    'BAAI/bge-base-zh-v1.5',
                    device=self.device,
                    cache_folder=str(Path(model_path).parent)
                )

                # 测试向量化
                test_embedding = self.model.encode(['测试'], device=self.device)
                self.embedding_dim = len(test_embedding[0])

            else:
                # 使用transformers直接加载
                self.tokenizer = AutoTokenizer.from_pretrained(
                    model_path,
                    local_files_only=True
                )
                self.model = AutoModel.from_pretrained(
                    model_path,
                    local_files_only=True
                ).to(self.device)

                # 测试向量化
                test_text = '测试文本'
                inputs = self.tokenizer(test_text, return_tensors='pt', truncation=True, padding=True)
                with torch.no_grad():
                    outputs = self.model(**inputs)
                test_embedding = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
                self.embedding_dim = test_embedding.shape[1]

            logger.info(f"✅ 离线模型加载成功！")
            logger.info(f"   模型类型: {'SentenceTransformer' if hasattr(self, 'model') else 'AutoModel'}")
            logger.info(f"   向量维度: {self.embedding_dim}")
            logger.info(f"   设备: {self.device}")

            return True

        except Exception as e:
            logger.error(f"❌ 离线模型加载失败: {e}")
            return False

    def encode_text(self, text: str) -> np.ndarray | None:
        """编码单个文本"""
        try:
            if hasattr(self.model, 'encode'):  # SentenceTransformer
                # BGE或其他sentence-transformers模型
                embedding = self.model.encode([text], device=self.device)[0]
                # 归一化向量
                embedding = embedding / np.linalg.norm(embedding)
                return embedding
            else:  # Transformers模型
                inputs = self.tokenizer(text, return_tensors='pt', truncation=True, padding=True)
                with torch.no_grad():
                    outputs = self.model(**inputs)
                # 平均池化
                embedding = outputs.last_hidden_state.mean(dim=1).cpu().numpy()[0]
                # 归一化向量
                embedding = embedding / np.linalg.norm(embedding)
                return embedding

        except Exception as e:
            logger.error(f"❌ 文本编码失败: {e}")
            return None

    def vectorize_batch(self, texts: List[str]) -> np.ndarray | None:
        """批量向量化文本"""
        if not self.model:
            logger.error('❌ 模型未加载')
            return None

        try:
            # 过滤空文本
            valid_texts = [text for text in texts if text and text.strip()]

            if not valid_texts:
                return None

            logger.info(f"🔄 批量向量化 {len(valid_texts)} 条文本...")

            embeddings = []
            for i, text in enumerate(valid_texts):
                if i > 0 and i % 10 == 0:
                    logger.info(f"   进度: {i}/{len(valid_texts)}")

                embedding = self.encode_text(text)
                if embedding is not None:
                    embeddings.append(embedding)

            if embeddings:
                return np.array(embeddings)
            else:
                return None

        except Exception as e:
            logger.error(f"❌ 批量向量化失败: {e}")
            return None

    def save_vectors_to_db(self, patent_data: List[Dict], embeddings: np.ndarray) -> bool:
        """保存向量到数据库"""
        if not patent_data or embeddings is None:
            return False

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # 准备批量更新数据
            update_data = []
            for i, patent in enumerate(patent_data):
                if i < len(embeddings):
                    embedding_list = embeddings[i].tolist()
                    update_data.append((
                        embedding_list,  # embedding_title
                        embedding_list,  # embedding_abstract
                        embedding_list,  # embedding_claims
                        embedding_list,  # embedding_combined
                        patent['id']
                    ))

            # 执行批量更新
            query = """
                UPDATE patents
                SET
                    embedding_title = %s::vector,
                    embedding_abstract = %s::vector,
                    embedding_claims = %s::vector,
                    embedding_combined = %s::vector,
                    vectorized_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """

            cursor.executemany(query, update_data)
            conn.commit()

            logger.info(f"✅ 成功更新 {len(update_data)} 条专利的向量数据")

            cursor.close()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"❌ 保存向量到数据库失败: {e}")
            return False

def test_offline_vectorization():
    """测试离线向量化功能"""
    logger.info('🚀 开始离线向量化测试...')

    # 1. 初始化离线向量化器
    vectorizer = OfflineVectorizer()

    # 2. 加载本地模型
    if not vectorizer.load_model_from_cache():
        return False

    # 3. 测试向量化
    test_texts = [
        '人工智能图像识别技术',
        '电动汽车电池管理系统',
        '5G通信网络优化方法'
    ]

    logger.info(f"🔄 测试向量化 {len(test_texts)} 条文本...")

    # 4. 生成向量
    start_time = time.time()
    embeddings = vectorizer.vectorize_batch(test_texts)

    if embeddings is None:
        logger.error('❌ 向量化失败')
        return False

    elapsed = time.time() - start_time
    logger.info(f"✅ 离线向量化成功！")
    logger.info(f"   文本数量: {len(test_texts)}")
    logger.info(f"   向量形状: {embeddings.shape}")
    logger.info(f"   向量维度: {embeddings.shape[1]}")
    logger.info(f"   处理时间: {elapsed:.2f}秒")

    # 5. 测试相似度计算
    from sklearn.metrics.pairwise import cosine_similarity

    # 计算第一个和第二个文本的相似度
    similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    logger.info(f"📊 相似度测试: '{test_texts[0]}' vs '{test_texts[1]}' = {similarity:.4f}")

    # 6. 测试数据库保存
    logger.info('🔗 测试数据库连接...')

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 查询待向量化的专利
        cursor.execute("""
            SELECT id, patent_name, abstract
            FROM patents
            WHERE abstract IS NOT NULL
            AND length(abstract) > 50
            AND embedding_combined IS NULL
            LIMIT 3
        """)

        patents = cursor.fetchall()
        logger.info(f"✅ 查询到 {len(patents)} 条未向量化的专利")

        if patents:
            # 准备数据
            patent_data = []
            texts = []

            for patent_id, title, abstract in patents:
                combined_text = f"{title or ''} {abstract or ''}".strip()
                if combined_text:
                    patent_data.append({
                        'id': patent_id,
                        'title': title,
                        'abstract': abstract,
                        'combined': combined_text
                    })
                    texts.append(combined_text)

            # 向量化
            if texts:
                embeddings_batch = vectorizer.vectorize_batch(texts)

                if embeddings_batch is not None:
                    # 保存到数据库
                    success = vectorizer.save_vectors_to_db(patent_data, embeddings_batch)

                    if success:
                        logger.info('💾 离线模型向量已成功保存到数据库')

                        # 验证结果
                        cursor.execute("""
                            SELECT COUNT(*) as count
                            FROM patents
                            WHERE embedding_combined IS NOT NULL
                        """)
                        result = cursor.fetchone()
                        logger.info(f"✅ 数据库中已向量化专利数量: {result[0]}")
                    else:
                        logger.error('❌ 保存到数据库失败')
                        return False

        cursor.close()
        conn.close()

    except Exception as e:
        logger.error(f"❌ 数据库操作失败: {e}")
        return False

    logger.info('🎉 离线向量化测试完成！')
    return True

def main():
    """主函数"""
    logger.info('🧪 完全离线向量化测试')
    logger.info(str('=' * 50))
    logger.info('✅ 完全离线 - 无需网络连接')
    logger.info('✅ 使用本地缓存模型')
    logger.info('✅ 强制离线模式')
    logger.info('✅ BAAI/bge-base-zh-v1.5 模型')
    logger.info(str('=' * 50))

    success = test_offline_vectorization()

    if success:
        logger.info("\n✅ 离线向量化测试成功！")
        logger.info("\n🚀 离线方案优势:")
        logger.info('   - 无需网络连接')
        logger.info('   - 使用本地缓存')
        logger.info('   - 高性能BGE模型')
        logger.info('   - 768维向量完全兼容')
        logger.info("\n💡 使用方法:")
        logger.info('   1. 直接运行: python3 scripts/search/patent_vectorizer_offline.py')
        logger.info('   2. 集成到其他脚本中')
        logger.info('   3. 部署到生产环境')
    else:
        logger.info("\n❌ 离线向量化测试失败")

    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)