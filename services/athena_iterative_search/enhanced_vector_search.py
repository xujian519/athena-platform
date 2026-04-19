#!/usr/bin/env python3
"""
增强向量搜索模块
提供高性能的专利语义搜索和相似度匹配
"""

import hashlib
import json
import logging
import pickle
import time
from typing import Any

# 向量数据库和索引
import faiss
import jieba
import jieba.analyse
import numpy as np
import psycopg2
import redis

# 文本处理和嵌入
from sentence_transformers import SentenceTransformer

from .config_enhanced import VectorSearchConfig
from .types import PatentMetadata, PatentSearchResult, SearchEngineType

logger = logging.getLogger(__name__)

class PatentTextProcessor:
    """专利文本处理器"""

    def __init__(self, enable_jieba: bool = True):
        self.enable_jieba = enable_jieba
        self._init_jieba()

    def _init_jieba(self) -> Any:
        """初始化jieba分词"""
        if self.enable_jieba:
            # 添加专利领域专业词典
            patent_terms = [
                '发明专利', '实用新型', '外观设计', '专利申请', '专利权',
                '技术方案', '现有技术', '技术创新', '技术领域', '背景技术',
                '发明内容', '具体实施方式', '权利要求书', '说明书',
                'IPC分类', '国际专利分类', '专利检索', '专利分析',
                '人工智能', '机器学习', '深度学习', '神经网络', '算法',
                '大数据', '云计算', '物联网', '区块链', '量子计算'
            ]

            for term in patent_terms:
                jieba.add_word(term, freq=1000)

    def process_patent_text(self, title: str, abstract: str = '', claims: str = '') -> str:
        """处理专利文本，提取关键信息"""
        text_parts = []

        # 标题权重最高
        if title:
            text_parts.append(f"标题: {title}")

        # 摘要
        if abstract:
            text_parts.append(f"摘要: {abstract}")

        # 权利要求（部分）
        if claims:
            claims_preview = claims[:500] + '...' if len(claims) > 500 else claims
            text_parts.append(f"权利要求: {claims_preview}")

        combined_text = ' '.join(text_parts)

        # 使用jieba提取关键词
        if self.enable_jieba:
            keywords = jieba.analyse.extract_tags(combined_text, top_k=20, with_weight=False)
            if keywords:
                combined_text += ' 关键词: ' + ' '.join(keywords)

        return combined_text

    def extract_patent_features(self, patent: PatentSearchResult) -> dict[str, Any]:
        """提取专利特征"""
        features = {
            'text_length': 0,
            'ipc_sections': set(),
            'applicant_type': 'unknown',
            'technology_keywords': set()
        }

        if patent.patent_metadata:
            metadata = patent.patent_metadata

            # IPC分类分析
            if metadata.ipc_code:
                ipc_code = metadata.ipc_code
                if len(ipc_code) >= 1:
                    features['ipc_sections'].add(ipc_code[0])  # 部

            # 申请人类型分析
            if metadata.applicant:
                applicant = metadata.applicant.lower()
                if any(keyword in applicant for keyword in ['大学', '学院', '研究', 'institute', 'university']):
                    features['applicant_type'] = 'academic'
                elif any(keyword in applicant for keyword in ['公司', '集团', '企业', 'corp', 'ltd', 'co.']):
                    features['applicant_type'] = 'corporate'
                elif any(keyword in applicant for keyword in ['局', '部', '中心', 'government']):
                    features['applicant_type'] = 'government'

        # 文本长度
        content = patent.content or ''
        features['text_length'] = len(content)

        # 技术关键词
        tech_keywords = jieba.analyse.extract_tags(content, top_k=10, with_weight=False)
        features['technology_keywords'] = set(tech_keywords)

        return features

class EnhancedVectorSearch:
    """增强向量搜索引擎"""

    def __init__(self, config: VectorSearchConfig, db_config: dict[str, Any]):
        self.config = config
        self.db_config = db_config
        self.model = None
        self.index = None
        self.text_processor = PatentTextProcessor()
        self.redis_client = None
        self.db_connection = None
        self._init_components()

    def _init_components(self) -> Any:
        """初始化组件"""
        # 初始化嵌入模型
        try:
            self.model = SentenceTransformer(self.config.model_name)
            logger.info(f"加载向量模型: {self.config.model_name}")
        except Exception as e:
            logger.error(f"加载向量模型失败: {e}")
            # 使用轻量级模型作为后备
            self.model = SentenceTransformer('all-MiniLM-L6-v2')

        # 初始化Redis缓存
        try:
            self.redis_client = redis.Redis(
                host=self.db_config.get('redis_host', 'localhost'),
                port=self.db_config.get('redis_port', 6379),
                db=self.db_config.get('redis_db', 0),
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info('Redis连接成功')
        except Exception as e:
            logger.warning(f"Redis连接失败: {e}")

        # 初始化数据库连接
        try:
            self.db_connection = psycopg2.connect(
                host=self.db_config.get('host', 'localhost'),
                port=self.db_config.get('port', 5432),
                database=self.db_config.get('database', 'athena_patents'),
                user=self.db_config.get('user', 'postgres'),
                password=self.db_config.get('password', '')
            )
            logger.info('数据库连接成功')
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")

        # 加载或创建FAISS索引
        self._load_or_create_index()

    def _load_or_create_index(self) -> Any:
        """加载或创建FAISS索引"""
        try:
            # 尝试从Redis加载索引
            if self.redis_client:
                index_data = self.redis_client.get('vector_index')
                if index_data:
                    self.index = pickle.loads(index_data)
                    logger.info('从Redis加载向量索引成功')
                    return
        except Exception as e:
            logger.warning(f"从Redis加载索引失败: {e}")

        # 创建新索引
        embedding_dim = self.model.get_sentence_embedding_dimension()
        nlist = self.config.nlist

        if self.config.index_type == 'ivf_flat':
            quantizer = faiss.IndexFlatL2(embedding_dim)
            self.index = faiss.IndexIVFFlat(quantizer, embedding_dim, nlist)
        elif self.config.index_type == 'ivf_pq':
            quantizer = faiss.IndexFlatL2(embedding_dim)
            m = 16  # PQ编码的子向量数
            self.index = faiss.IndexIVFPQ(quantizer, embedding_dim, nlist, m, 8)
        else:
            self.index = faiss.IndexFlatL2(embedding_dim)

        logger.info(f"创建新的向量索引: {self.config.index_type}")

    async def build_index_from_database(self, batch_size: int = 1000):
        """从数据库构建向量索引"""
        if not self.db_connection:
            logger.error('数据库连接不可用')
            return

        try:
            cursor = self.db_connection.cursor()

            # 获取专利总数
            cursor.execute("SELECT COUNT(*) FROM patents WHERE abstract IS NOT NULL AND abstract != ''")
            total_count = cursor.fetchone()[0]
            logger.info(f"开始构建向量索引，总计{total_count}条专利")

            # 分批处理
            offset = 0
            processed = 0
            all_embeddings = []
            patent_ids = []

            while offset < total_count:
                # 获取一批专利
                query = """
                SELECT id, patent_name, abstract, applicant, ipc_code
                FROM patents
                WHERE abstract IS NOT NULL AND abstract != ''
                ORDER BY id
                LIMIT %s OFFSET %s
                """
                cursor.execute(query, (batch_size, offset))
                patents = cursor.fetchall()

                if not patents:
                    break

                # 处理这批专利
                batch_embeddings = []
                batch_patent_ids = []

                for patent_id, title, abstract, _applicant, _ipc_code in patents:
                    # 处理文本
                    text = self.text_processor.process_patent_text(title, abstract)

                    # 生成嵌入
                    embedding = self.model.encode(text, convert_to_numpy=True)
                    batch_embeddings.append(embedding)
                    batch_patent_ids.append(patent_id)

                if batch_embeddings:
                    # 添加到索引
                    batch_embeddings_np = np.array(batch_embeddings).astype('float32')
                    self.index.train(batch_embeddings_np) if not self.index.is_trained else None
                    self.index.add_with_ids(batch_embeddings_np, np.array(batch_patent_ids))

                    all_embeddings.extend(batch_embeddings)
                    patent_ids.extend(batch_patent_ids)

                processed += len(patents)
                offset += batch_size

                logger.info(f"已处理 {processed}/{total_count} 条专利")

                # 定期保存索引
                if processed % 5000 == 0:
                    await self._save_index()

            # 保存最终索引
            await self._save_index()

            logger.info(f"向量索引构建完成，共处理{processed}条专利")

        except Exception as e:
            logger.error(f"构建向量索引失败: {e}")
            raise
        finally:
            cursor.close()

    async def search_similar_patents(
        self,
        query_text: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None
    ) -> list[PatentSearchResult]:
        """搜索相似专利"""
        start_time = time.time()

        # 生成查询向量
        query_embedding = self.model.encode(query_text, convert_to_numpy=True)
        query_embedding = query_embedding.reshape(1, -1).astype('float32')

        # 执行向量搜索
        k = min(top_k, self.index.ntotal)
        distances, indices = self.index.search(query_embedding, k)

        # 获取候选专利ID
        candidate_ids = [int(idx) for idx in indices[0] if idx != -1]

        if not candidate_ids:
            return []

        # 从数据库获取专利详细信息
        patents = await self._get_patents_by_ids(candidate_ids, filters)

        # 计算相似度分数并排序
        results = []
        for i, patent in enumerate(patents):
            similarity = 1.0 / (1.0 + distances[0][i])  # 转换为相似度分数

            search_result = PatentSearchResult(
                title=patent['patent_name'],
                content=patent['abstract'] or '',
                score=similarity,
                similarity_score=similarity,
                engine_type=SearchEngineType.VECTOR_SEARCH,
                patent_metadata=PatentMetadata(
                    patent_id=str(patent['id']),
                    patent_name=patent['patent_name'],
                    applicant=patent['applicant'],
                    ipc_code=patent['ipc_code']
                )
            )
            results.append(search_result)

        # 记录搜索时间
        search_time = time.time() - start_time
        logger.info(f"向量搜索完成，返回{len(results)}条结果，耗时{search_time:.3f}秒")

        return results

    async def _get_patents_by_ids(
        self,
        patent_ids: list[int],
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """根据ID获取专利信息"""
        if not self.db_connection:
            return []

        try:
            cursor = self.db_connection.cursor()

            # 构建基础查询
            placeholders = ','.join(['%s'] * len(patent_ids))
            query = f"""
            SELECT id, patent_name, abstract, applicant, ipc_code,
                   application_date, publication_number, patent_type
            FROM patents
            WHERE id IN ({placeholders})
            """

            params = patent_ids

            # 添加过滤条件
            if filters:
                if filters.get('patent_type'):
                    query += ' AND patent_type = %s'
                    params.append(filters['patent_type'])

                if filters.get('applicant'):
                    query += ' AND applicant ILIKE %s'
                    params.append(f"%{filters['applicant']}%")

                if filters.get('ipc_code'):
                    query += ' AND ipc_code LIKE %s'
                    params.append(f"{filters['ipc_code']}%")

                if filters.get('start_date'):
                    query += ' AND application_date >= %s'
                    params.append(filters['start_date'])

                if filters.get('end_date'):
                    query += ' AND application_date <= %s'
                    params.append(filters['end_date'])

            query += ' ORDER BY id'

            cursor.execute(query, params)
            patents = [dict(zip([col[0] for col in cursor.description], row, strict=False))
                       for row in cursor.fetchall()]

            return patents

        except Exception as e:
            logger.error(f"获取专利信息失败: {e}")
            return []
        finally:
            cursor.close()

    async def _save_index(self):
        """保存索引到Redis"""
        if self.redis_client:
            try:
                index_data = pickle.dumps(self.index)
                self.redis_client.setex('vector_index', 86400, index_data)  # 保存24小时
                logger.info('向量索引已保存到Redis')
            except Exception as e:
                logger.error(f"保存索引失败: {e}")

    def get_cache_key(self, text: str) -> str:
        """生成缓存键"""
        return f"vector_embedding:{hashlib.md5(text.encode(), usedforsecurity=False).hexdigest()}"

    async def get_embedding(self, text: str) -> np.ndarray:
        """获取文本嵌入（带缓存）"""
        cache_key = self.get_cache_key(text)

        # 尝试从缓存获取
        if self.redis_client:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    return np.array(json.loads(cached_data))
            except Exception as e:
                logger.warning(f"从Redis获取嵌入缓存失败: {e}")

        # 生成新的嵌入
        embedding = self.model.encode(text, convert_to_numpy=True)

        # 保存到缓存
        if self.redis_client:
            try:
                self.redis_client.setex(
                    cache_key,
                    self.config.cache_ttl if hasattr(self.config, 'cache_ttl') else 604800,
                    json.dumps(embedding.tolist())
                )
            except Exception as e:
                logger.warning(f"保存嵌入缓存失败: {e}")

        return embedding

    async def hybrid_search(
        self,
        query_text: str,
        top_k: int = 10,
        text_weight: float = 0.3,
        vector_weight: float = 0.7,
        filters: dict[str, Any] | None = None
    ) -> list[PatentSearchResult]:
        """混合搜索（文本+向量）"""
        # 向量搜索
        vector_results = await self.search_similar_patents(query_text, top_k * 2, filters)

        # 简单的文本匹配（作为补充）
        text_results = await self._text_search(query_text, top_k, filters)

        # 合并结果
        all_results = {}

        # 添加向量搜索结果
        for result in vector_results:
            result_id = result.patent_metadata.patent_id if result.patent_metadata else result.title
            all_results[result_id] = {
                'result': result,
                'vector_score': result.similarity_score,
                'text_score': 0.0
            }

        # 添加文本搜索结果
        for result in text_results:
            result_id = result.patent_metadata.patent_id if result.patent_metadata else result.title
            if result_id in all_results:
                all_results[result_id]['text_score'] = result.score
            else:
                all_results[result_id] = {
                    'result': result,
                    'vector_score': 0.0,
                    'text_score': result.score
                }

        # 计算综合分数
        for item in all_results.values():
            combined_score = (
                item['text_score'] * text_weight +
                item['vector_score'] * vector_weight
            )
            item['result'].combined_score = combined_score

        # 排序并返回结果
        results = [item['result'] for item in all_results.values()]
        results.sort(key=lambda x: x.combined_score, reverse=True)

        return results[:top_k]

    async def _text_search(
        self,
        query_text: str,
        top_k: int,
        filters: dict[str, Any] | None = None
    ) -> list[PatentSearchResult]:
        """简单文本搜索"""
        if not self.db_connection:
            return []

        try:
            cursor = self.db_connection.cursor()

            # 构建查询
            query = """
            SELECT id, patent_name, abstract, applicant, ipc_code,
                   ts_rank_cd(to_tsvector('chinese', patent_name || ' ' || COALESCE(abstract, '')),
                             plainto_tsquery('chinese', %s)) as rank
            FROM patents
            WHERE patent_name || ' ' || COALESCE(abstract, '') ILIKE %s
            """

            params = [query_text, f"%{query_text}%"]

            # 添加过滤条件
            if filters:
                if filters.get('patent_type'):
                    query += ' AND patent_type = %s'
                    params.append(filters['patent_type'])

                if filters.get('applicant'):
                    query += ' AND applicant ILIKE %s'
                    params.append(f"%{filters['applicant']}%")

            query += ' ORDER BY rank DESC LIMIT %s'
            params.append(top_k)

            cursor.execute(query, params)
            patents = cursor.fetchall()

            results = []
            for patent in patents:
                result = PatentSearchResult(
                    title=patent[1],
                    content=patent[2] or '',
                    score=float(patent[5]),
                    engine_type=SearchEngineType.ELASTICSEARCH,
                    patent_metadata=PatentMetadata(
                        patent_id=str(patent[0]),
                        patent_name=patent[1],
                        applicant=patent[3],
                        ipc_code=patent[4]
                    )
                )
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"文本搜索失败: {e}")
            return []
        finally:
            cursor.close()

    def get_statistics(self) -> dict[str, Any]:
        """获取搜索统计信息"""
        stats = {
            'index_type': self.config.index_type,
            'index_size': self.index.ntotal if self.index else 0,
            'embedding_dimension': self.model.get_sentence_embedding_dimension(),
            'model_name': self.config.model_name,
            'cache_enabled': self.redis_client is not None,
            'database_connected': self.db_connection is not None
        }

        return stats

    async def close(self):
        """关闭连接"""
        if self.db_connection:
            self.db_connection.close()

        if self.redis_client:
            self.redis_client.close()

        logger.info('向量搜索引擎已关闭')
