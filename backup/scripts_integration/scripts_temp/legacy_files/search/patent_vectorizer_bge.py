#!/usr/bin/env python3
"""
使用BGE模型的专利向量化工具
Patent Vectorization Tool with BGE Model

替代shibing624/text2vec-base-chinese，使用性能更优的BAAI/bge-base-zh-v1.5
"""

import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import psycopg2
from sentence_transformers import SentenceTransformer

# 设置环境变量
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

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

class BGEVectorizer:
    """使用BGE模型的专利向量化器"""

    def __init__(self, model_name: str = 'BAAI/bge-base-zh-v1.5'):
        """
        初始化BGE向量化器

        Args:
            model_name: 模型名称，默认使用bge-base-zh-v1.5
        """
        self.model_name = model_name
        self.model = None
        self.device = 'cpu'
        self.embedding_dim = 768

    def load_model(self) -> bool:
        """加载BGE模型"""
        try:
            logger.info(f"📥 加载BGE模型: {self.model_name}")

            # 使用sentence-transformers加载BGE模型
            self.model = SentenceTransformer(self.model_name, device=self.device)

            # 获取向量维度
            test_embedding = self.model.encode(['测试'], device=self.device)
            self.embedding_dim = len(test_embedding[0])

            logger.info(f"✅ BGE模型加载成功！")
            logger.info(f"   模型: {self.model_name}")
            logger.info(f"   向量维度: {self.embedding_dim}")
            logger.info(f"   设备: {self.device}")

            return True

        except Exception as e:
            logger.error(f"❌ BGE模型加载失败: {e}")
            return False

    def vectorize_batch(self, texts: List[str]) -> np.ndarray | None:
        """
        批量向量化文本

        Args:
            texts: 待向量化的文本列表

        Returns:
            向量数组
        """
        if not self.model:
            logger.error('❌ 模型未加载')
            return None

        try:
            # 过滤空文本
            valid_texts = [text for text in texts if text and text.strip()]

            if not valid_texts:
                return None

            # 使用BGE模型进行向量化
            embeddings = self.model.encode(
                valid_texts,
                device=self.device,
                batch_size=32,
                normalize_embeddings=True  # BGE模型推荐进行归一化
            )

            return embeddings

        except Exception as e:
            logger.error(f"❌ 批量向量化失败: {e}")
            return None

    def save_vectors_to_db(self, patent_data: List[Dict], embeddings: np.ndarray) -> bool:
        """
        保存向量到数据库

        Args:
            patent_data: 专利数据列表
            embeddings: 对应的向量数组

        Returns:
            是否保存成功
        """
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

def test_bge_vectorization():
    """测试BGE向量化功能"""
    logger.info('🚀 开始BGE向量化测试...')

    # 1. 初始化BGE向量化器
    vectorizer = BGEVectorizer()

    # 2. 加载模型
    if not vectorizer.load_model():
        return False

    # 3. 测试向量化
    test_texts = [
        '人工智能图像识别技术',
        '电动汽车电池管理系统',
        '5G通信网络优化方法',
        '一种洗碗机用装饰边框安装装置及安装方法',
        '一种复卷机'
    ]

    logger.info(f"🔄 测试向量化 {len(test_texts)} 条文本...")

    # 4. 生成向量
    embeddings = vectorizer.vectorize_batch(test_texts)

    if embeddings is None:
        logger.error('❌ 向量化失败')
        return False

    logger.info(f"✅ 向量化成功！")
    logger.info(f"   文本数量: {len(test_texts)}")
    logger.info(f"   向量形状: {embeddings.shape}")
    logger.info(f"   向量维度: {embeddings.shape[1]}")

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
                        logger.info('💾 BGE向量已成功保存到数据库')

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

    logger.info('🎉 BGE向量化测试完成！')
    return True

def main():
    """主函数"""
    logger.info('🧪 BGE模型向量化测试')
    logger.info(str('=' * 50))
    logger.info('模型: BAAI/bge-base-zh-v1.5')
    logger.info('维度: 768')
    logger.info('性能: C-MTEB 63.13 (vs text2vec 47.63)')
    logger.info(str('=' * 50))

    success = test_bge_vectorization()

    if success:
        logger.info("\n✅ BGE向量化测试成功！")
        logger.info("\n🚀 BGE模型优势:")
        logger.info('   - 性能提升32.5% (63.13 vs 47.63)')
        logger.info('   - 专门针对中文检索优化')
        logger.info('   - 本地已缓存，无需下载')
        logger.info('   - 768维完全兼容现有系统')
        logger.info("\n💡 建议替换方案:")
        logger.info("   将 'shibing624/text2vec-base-chinese'")
        logger.info("   替换为 'BAAI/bge-base-zh-v1.5'")
    else:
        logger.info("\n❌ BGE向量化测试失败")

    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)