#!/usr/bin/env python3
"""
使用本地缓存模型的专利向量化工具
Patent Vectorization Tool with Local Cached Models

使用本地已缓存的BGE模型，无需网络连接
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
from sentence_transformers import SentenceTransformer

# 设置环境变量
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['TRANSFORMERS_OFFLINE'] = '1'  # 强制离线模式

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

# 本地模型缓存路径
HF_CACHE_HOME = Path.home() / '.cache' / 'huggingface' / 'hub'

class LocalVectorizer:
    """使用本地缓存模型的向量化器"""

    def __init__(self):
        """初始化向量化器"""
        self.model = None
        self.device = 'cpu'
        self.embedding_dim = 768
        self.model_path = None

    def find_local_model(self, preferred_models: List[str]) -> str | None:
        """
        查找本地已缓存的模型

        Args:
            preferred_models: 优先选择的模型列表

        Returns:
            找到的模型路径
        """
        available_models = []

        # 扫描huggingface缓存目录
        if HF_CACHE_HOME.exists():
            for model_dir in HF_CACHE_HOME.iterdir():
                if model_dir.is_dir() and model_dir.name.startswith('models--'):
                    # 提取模型名称
                    model_name = model_dir.name.replace('models--', '').replace('--', '/')
                    available_models.append((model_name, str(model_dir)))

        logger.info(f"🔍 找到 {len(available_models)} 个本地模型:")
        for model_name, _ in available_models:
            logger.info(f"   - {model_name}")

        # 按优先级查找
        for preferred in preferred_models:
            for model_name, model_path in available_models:
                if preferred in model_name:
                    logger.info(f"✅ 选择模型: {model_name}")
                    return model_name

        # 如果没有找到优先模型，返回第一个可用的
        if available_models:
            model_name, model_path = available_models[0]
            logger.info(f"⚠️ 未找到优先模型，使用: {model_name}")
            return model_name

        return None

    def load_model(self) -> bool:
        """加载本地模型"""
        try:
            # 优先级模型列表
            preferred_models = [
                'BAAI/bge-base-zh-v1.5',      # 最佳选择，768维
                'shibing624/text2vec-base-chinese',  # 原计划模型，768维
                'bert-base-chinese',         # 基础BERT，768维
                'BAAI/bge-small-zh-v1.5',    # 轻量级BGE
                'sentence-transformers/all-MiniLM-L6-v2'  # 英文模型备选
            ]

            # 查找本地模型
            model_name = self.find_local_model(preferred_models)

            if not model_name:
                logger.error('❌ 未找到可用的本地模型')
                return False

            logger.info(f"📥 加载本地模型: {model_name}")

            # 设置离线模式
            os.environ['TRANSFORMERS_OFFLINE'] = '1'
            os.environ['HF_DATASETS_OFFLINE'] = '1'

            # 加载模型（使用本地缓存）
            self.model = SentenceTransformer(model_name, device=self.device)

            # 测试向量化并获取维度
            test_embedding = self.model.encode(['测试'], device=self.device)
            self.embedding_dim = len(test_embedding[0])

            logger.info(f"✅ 本地模型加载成功！")
            logger.info(f"   模型: {model_name}")
            logger.info(f"   向量维度: {self.embedding_dim}")
            logger.info(f"   设备: {self.device}")

            return True

        except Exception as e:
            logger.error(f"❌ 本地模型加载失败: {e}")
            return False

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

            # 使用本地模型进行向量化
            embeddings = self.model.encode(
                valid_texts,
                device=self.device,
                batch_size=16,
                normalize_embeddings=True
            )

            return embeddings

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

def test_local_vectorization():
    """测试本地模型向量化功能"""
    logger.info('🚀 开始本地模型向量化测试...')

    # 1. 初始化向量化器
    vectorizer = LocalVectorizer()

    # 2. 加载本地模型
    if not vectorizer.load_model():
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
    logger.info(f"✅ 向量化成功！")
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
                        logger.info('💾 本地模型向量已成功保存到数据库')

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

    logger.info('🎉 本地模型向量化测试完成！')
    return True

def main():
    """主函数"""
    logger.info('🧪 本地模型向量化测试')
    logger.info(str('=' * 50))
    logger.info('✅ 离线模式 - 无需网络连接')
    logger.info('✅ 使用本地缓存模型')
    logger.info('✅ 自动检测最佳可用模型')
    logger.info(str('=' * 50))

    success = test_local_vectorization()

    if success:
        logger.info("\n✅ 本地模型向量化测试成功！")
        logger.info("\n🚀 优势:")
        logger.info('   - 无需网络连接')
        logger.info('   - 使用本地缓存模型')
        logger.info('   - 自动选择最优模型')
        logger.info('   - 完全离线工作')
        logger.info("\n💡 下一步:")
        logger.info('   1. 批量向量化更多专利')
        logger.info('   2. 创建向量索引')
        logger.info('   3. 部署到生产环境')
    else:
        logger.info("\n❌ 本地模型向量化测试失败")

    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)