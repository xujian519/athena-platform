#!/usr/bin/env python3
"""
专利数据向量化工具
Patent Data Vectorization Tool

用于将专利数据的文本内容转换为向量表示，支持语义搜索
"""

import json
import logging
import multiprocessing as mp
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import psycopg2
from tqdm import tqdm

# 导入文本向量化库
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMER_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMER_AVAILABLE = False
    logger.info('⚠️ sentence-transformers未安装，请运行: pip install sentence-transformers')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('documentation/logs/patent_vectorizer.log'),
        logging.StreamHandler()
    ]
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

class PatentVectorizer:
    """专利数据向量化类"""

    def __init__(self, model_name: str = 'shibing624/text2vec-base-chinese'):
        """
        初始化向量化器

        Args:
            model_name: 使用的预训练模型名称
        """
        self.model_name = model_name
        self.model = None
        self.conn = None
        self.batch_size = 500  # 批处理大小
        self.chunk_size = 1000  # 每次从数据库读取的记录数

    def connect(self) -> bool:
        """连接数据库"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.conn.autocommit = True
            logger.info('✅ 数据库连接成功')
            return True
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            return False

    def load_model(self) -> bool:
        """加载向量化模型"""
        try:
            logger.info(f"📥 加载模型: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)

            # 测试模型
            test_text = '测试文本'
            test_vector = self.model.encode(test_text)
            logger.info(f"✅ 模型加载成功，向量维度: {len(test_vector)}")
            return True

        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            return False

    def prepare_text(self, patent_name: str, abstract: str, claims: str) -> Tuple[str, str, str, str]:
        """
        准备用于向量化的文本

        Args:
            patent_name: 专利名称
            abstract: 摘要
            claims: 权利要求

        Returns:
            四个元组：(标题文本, 摘要文本, 权利要求文本, 组合文本)
        """
        # 清理和预处理文本
        patent_name = self._clean_text(patent_name) if patent_name else ''
        abstract = self._clean_text(abstract) if abstract else ''

        # 权利要求可能很长，截取前1000字符
        claims = self._clean_text(claims) if claims else ''
        claims = claims[:1000] if len(claims) > 1000 else claims

        # 组合文本（权重：标题20%，摘要50%，权利要求30%）
        combined_parts = []
        if patent_name:
            combined_parts.extend([patent_name] * 2)  # 标题权重2
        if abstract:
            combined_parts.extend([abstract] * 5)  # 摘要权重5
        if claims:
            combined_parts.extend([claims] * 3)  # 权利要求权重3

        combined_text = ' '.join(combined_parts)

        return patent_name, abstract, claims, combined_text

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ''

        # 移除特殊字符和多余空格
        import re
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def get_batch_data(self, offset: int = 0) -> List[Tuple]:
        """
        获取一批未向量化的数据

        Args:
            offset: 偏移量

        Returns:
            专利数据列表
        """
        cursor = self.conn.cursor()

        try:
            query = """
                SELECT id, patent_name, abstract, claims_content
                FROM patents
                WHERE embedding_abstract IS NULL
                AND abstract IS NOT NULL
                ORDER BY id
                LIMIT %s OFFSET %s
            """

            cursor.execute(query, (self.chunk_size, offset))
            results = cursor.fetchall()

            logger.info(f"📊 获取到 {len(results)} 条未向量化的记录")
            return results

        except Exception as e:
            logger.error(f"❌ 获取数据失败: {e}")
            return []
        finally:
            cursor.close()

    def encode_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        批量编码文本

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        try:
            # 过滤空文本
            valid_texts = [t for t in texts if t.strip()]

            if not valid_texts:
                return [None] * len(texts)

            # 批量编码
            embeddings = self.model.encode(
                valid_texts,
                batch_size=32,
                show_progress_bar=False,
                convert_to_numpy=True
            )

            # 构建结果列表，保持与输入文本的对应关系
            result = []
            text_iter = iter(embeddings)

            for text in texts:
                if text.strip():
                    result.append(next(text_iter).tolist())
                else:
                    result.append(None)

            return result

        except Exception as e:
            logger.error(f"❌ 编码失败: {e}")
            return [None] * len(texts)

    def update_vectors(self, updates: List[Tuple[int, List[float], List[float], List[float], List[float]]]) -> int:
        """
        更新数据库中的向量

        Args:
            updates: 更新列表，每个元素为(id, title_vector, abstract_vector, claims_vector, combined_vector)

        Returns:
            成功更新的记录数
        """
        if not updates:
            return 0

        cursor = self.conn.cursor()

        try:
            # 准备批量插入SQL
            query = """
                UPDATE patents
                SET
                    embedding_title = %s,
                    embedding_abstract = %s,
                    embedding_claims = %s,
                    embedding_combined = %s,
                    vectorized_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """

            # 批量执行更新
            cursor.executemany(query, updates)
            updated_count = cursor.rowcount

            logger.info(f"✅ 成功更新 {updated_count} 条记录的向量")
            return updated_count

        except Exception as e:
            logger.error(f"❌ 更新向量失败: {e}")
            return 0
        finally:
            cursor.close()

    def process_chunk(self, offset: int) -> Tuple[int, int]:
        """
        处理一块数据

        Args:
            offset: 数据偏移量

        Returns:
            (处理的记录数, 成功向量化的记录数)
        """
        logger.info(f"🔄 处理数据块 (offset: {offset})")

        # 获取数据
        data = self.get_batch_data(offset)
        if not data:
            return 0, 0

        # 准备文本
        titles = []
        abstracts = []
        claims_list = []
        combined_texts = []

        for record in data:
            patent_id, patent_name, abstract, claims = record
            title, abstract_text, claims_text, combined_text = self.prepare_text(patent_name, abstract, claims)

            titles.append(title)
            abstracts.append(abstract_text)
            claims_list.append(claims_text)
            combined_texts.append(combined_text)

        # 批量编码
        logger.info('🔄 开始向量编码...')
        title_vectors = self.encode_batch(titles)
        abstract_vectors = self.encode_batch(abstracts)
        claims_vectors = self.encode_batch(claims_list)
        combined_vectors = self.encode_batch(combined_texts)

        # 准备更新数据
        updates = []
        for i, record in enumerate(data):
            patent_id = record[0]
            updates.append((
                patent_id,
                title_vectors[i],
                abstract_vectors[i],
                claims_vectors[i],
                combined_vectors[i]
            ))

        # 更新数据库
        success_count = self.update_vectors(updates)

        return len(data), success_count

    def get_progress(self) -> Tuple[int, int]:
        """
        获取向量化进度

        Returns:
            (总数, 已完成数)
        """
        cursor = self.conn.cursor()

        try:
            # 总数
            cursor.execute("""
                SELECT COUNT(*) FROM patents WHERE abstract IS NOT NULL
            """)
            total = cursor.fetchone()[0]

            # 已完成数
            cursor.execute("""
                SELECT COUNT(*) FROM patents WHERE embedding_abstract IS NOT NULL
            """)
            completed = cursor.fetchone()[0]

            return total, completed

        except Exception as e:
            logger.error(f"❌ 获取进度失败: {e}")
            return 0, 0
        finally:
            cursor.close()

    def run(self, max_workers: int = 4) -> bool:
        """
        运行向量化过程

        Args:
            max_workers: 最大工作进程数

        Returns:
            是否成功完成
        """
        if not self.connect():
            return False

        if not self.load_model():
            return False

        # 获取进度
        total, completed = self.get_progress()
        logger.info(f"📊 向量化进度: {completed:,}/{total:,} ({completed/total*100:.1f}%)")

        if completed >= total:
            logger.info('✅ 所有数据已经向量化完成')
            return True

        # 计算需要处理的数据
        remaining = total - completed
        logger.info(f"🔄 剩余需要处理: {remaining:,} 条记录")

        # 多进程处理
        start_time = time.time()
        total_processed = 0
        total_success = 0

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []

            # 提交任务
            for offset in range(0, remaining, self.chunk_size):
                future = executor.submit(self.process_chunk, offset + completed)
                futures.append(future)

            # 收集结果
            for future in tqdm(as_completed(futures), total=len(futures), desc='向量化进度'):
                processed, success = future.result()
                total_processed += processed
                total_success += success

                # 更新进度
                current_completed = completed + total_processed
                progress = current_completed / total * 100
                logger.info(f"📊 进度: {current_completed:,}/{total:,} ({progress:.1f}%)")

        # 最终统计
        elapsed_time = time.time() - start_time
        final_total, final_completed = self.get_progress()

        logger.info('=' * 50)
        logger.info('🎉 向量化完成!')
        logger.info(f"⏱️ 总耗时: {elapsed_time/3600:.2f} 小时")
        logger.info(f"📊 处理记录: {total_processed:,}")
        logger.info(f"✅ 成功向量: {total_success:,}")
        logger.info(f"📈 最终进度: {final_completed:,}/{final_total:,} ({final_completed/final_total*100:.1f}%)")
        logger.info(f"⚡ 处理速度: {total_processed/(elapsed_time/3600):,.0f} 条/小时")
        logger.info('=' * 50)

        return final_completed >= total

def main():
    """主函数"""
    logger.info('🔧 专利数据向量化工具')
    logger.info(str('=' * 50))

    # 创建日志目录
    os.makedirs('logs', exist_ok=True)

    # 检查依赖
    if not SENTENCE_TRANSFORMER_AVAILABLE:
        logger.info('❌ 缺少必要的依赖，请先安装:')
        logger.info('   pip install sentence-transformers')
        logger.info('   pip install psycopg2-binary')
        logger.info('   pip install tqdm')
        return False

    # 创建向量化器
    vectorizer = PatentVectorizer()

    # 运行向量化
    success = vectorizer.run(max_workers=4)

    if success:
        logger.info("\n✅ 向量化任务完成!")
        logger.info("\n下一步:")
        logger.info('1. 更新数据库统计信息: ANALYZE patents;')
        logger.info('2. 测试向量搜索功能')
        logger.info('3. 配置搜索API接口')
    else:
        logger.info("\n❌ 向量化任务失败!")
        logger.info('请检查日志文件: documentation/logs/patent_vectorizer.log')

    return success

if __name__ == '__main__':
    main()