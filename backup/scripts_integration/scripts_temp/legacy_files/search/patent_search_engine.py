#!/usr/bin/env python3
"""
三阶段专利混合检索引擎
Three-Stage Hybrid Patent Search Engine

基于向量检索+关键词检索+分类过滤的专利检索系统
避免漏检的核心策略：多路召回+智能重排
"""

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import jieba
import numpy as np
import psycopg2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('documentation/logs/patent_search.log'),
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

class SearchStage(Enum):
    """检索阶段枚举"""
    RECALL = 'recall'      # 第一阶段：召回
    RERANK = 'rerank'    # 第二阶段：重排
    FETCH = 'fetch'       # 第三阶段：获取全文

@dataclass
class SearchResult:
    """搜索结果"""
    id: int
    patent_id: str
    patent_name: str
    applicant: str
    abstract: str
    ipc_main_class: str
    patent_type: str
    source_year: int
    score: float = 0.0
    vector_score: float = 0.0
    keyword_score: float = 0.0
    llm_score: float = 0.0
    full_text: str | None = None

class PatentSearchEngine:
    """专利搜索引擎"""

    def __init__(self):
        """初始化搜索引擎"""
        self.conn = None
        self.redis_client = None  # 可选：用于缓存
        self.llm_client = None  # 可选：用于LLM重排

        # 搜索参数
        self.recall_limit = 200  # 第一阶段召回数量
        self.rerank_limit = 50   # 第二阶段重排数量
        self.final_limit = 10     # 最终返回数量

        # 权重配置
        self.vector_weight = 0.6    # 向量检索权重
        self.keyword_weight = 0.3   # 关键词检索权重
        self.category_weight = 0.1   # 分类过滤权重

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

    def preprocess_query(self, query: str) -> Dict[str, Any]:
        """
        查询预处理
        提取关键词、生成查询向量、预测分类

        Args:
            query: 用户查询

        Returns:
            预处理结果
        """
        # 1. 提取关键词
        keywords = self._extract_keywords(query)

        # 2. 生成查询向量（需要模型支持）
        query_vector = self._generate_query_vector(query)

        # 3. 预测IPC分类（简化版）
        ipc_predictions = self._predict_ipc_category(query)

        # 4. 同义词扩展
        synonyms = self._expand_synonyms(keywords)

        # 5. 生成查询条件
        query_conditions = self._build_query_conditions(keywords, ipc_predictions)

        return {
            'original_query': query,
            'keywords': keywords,
            'synonyms': synonyms,
            'query_vector': query_vector,
            'ipc_predictions': ipc_predictions,
            'query_conditions': query_conditions
        }

    def _extract_keywords(self, query: str) -> List[str]:
        """提取关键词"""
        # 使用jieba分词
        words = jieba.lcut(query)

        # 过滤停用词和短词
        stopwords = {'的', '是', '在', '有', '和', '与', '或', '但', '而', '及', '等'}
        keywords = [word for word in words if len(word) > 1 and word not in stopwords]

        # 去重
        keywords = list(set(keywords))

        return keywords

    def _generate_query_vector(self, query: str) -> List[float | None]:
        """生成查询向量"""
        # TODO: 集成实际的向量模型
        # 这里返回None，实际使用时需要加载模型
        logger.warning('⚠️ 向量模型未集成，将跳过向量检索')
        return None

    def _predict_ipc_category(self, query: str) -> List[str]:
        """预测IPC分类（简化版）"""
        ipc_mapping = {
            '人工智能': ['G06F', 'G06N'],
            '机器学习': ['G06F', 'G06N'],
            '深度学习': ['G06F', 'G06N'],
            '通信': ['H04L'],
            '网络': ['H04L'],
            '图像': ['G06T'],
            '显示': ['G09F'],
            '电池': ['H01M'],
            '医疗': ['A61'],
            '药物': ['A61K'],
            '汽车': ['B60'],
            '电子': ['H05'],
        }

        predicted_ipcs = []
        query_lower = query.lower()

        for keyword, ipcs in ipc_mapping.items():
            if keyword in query_lower:
                predicted_ipcs.extend(ipcs)

        return list(set(predicted_ipcs))

    def _expand_synonyms(self, keywords: List[str]) -> Dict[str, List[str]]:
        """同义词扩展"""
        synonym_map = {
            '人工智能': ['AI', '智能', '机器智能'],
            '机器学习': ['ML', '深度学习', '神经网络'],
            '通信': ['通讯', '传输', '信息传输'],
            '图像': ['图片', '视觉', '成像'],
            '电池': ['蓄电池', '电源', '储能'],
        }

        expanded = {}
        for keyword in keywords:
            synonyms = [keyword]
            if keyword in synonym_map:
                synonyms.extend(synonym_map[keyword])
            expanded[keyword] = list(set(synonyms))

        return expanded

    def _build_query_conditions(self, keywords: List[str], ipcs: List[str]) -> Dict[str, Any]:
        """构建查询条件"""
        conditions = {
            'keyword_conditions': [],
            'ipc_conditions': [],
            'date_range': None
        }

        # 关键词条件
        for keyword in keywords:
            conditions['keyword_conditions'].append(f"patent_name ILIKE '%{keyword}%'")
            conditions['keyword_conditions'].append(f"abstract ILIKE '%{keyword}%'")

        # IPC分类条件
        for ipc in ipcs:
            conditions['ipc_conditions'].append(f"ipc_main_class LIKE '{ipc}%'")

        return conditions

    def stage1_recall(self, query_info: Dict[str, Any]) -> List[SearchResult]:
        """
        第一阶段：多路召回
        向量检索 + 关键词检索 + 分类过滤

        Args:
            query_info: 预处理后的查询信息

        Returns:
            召回结果列表
        """
        logger.info(f"🔄 第一阶段：开始召回...")
        start_time = time.time()

        results = []

        # 1. 向量检索
        if query_info['query_vector']:
            vector_results = self._vector_search(query_info['query_vector'], limit=100)
            results.extend(vector_results)

        # 2. 关键词检索
        keyword_results = self._keyword_search(query_info['query_conditions'], limit=100)
        results.extend(keyword_results)

        # 3. 分类过滤
        if query_info['ipc_predictions']:
            category_results = self._category_search(query_info['ipc_predictions'], limit=100)
            results.extend(category_results)

        # 4. 去重和排序
        unique_results = self._deduplicate_and_sort(results, query_info)

        # 5. 限制数量
        final_results = unique_results[:self.recall_limit]

        elapsed = time.time() - start_time
        logger.info(f"✅ 第一阶段完成：召回 {len(final_results)} 条记录，耗时 {elapsed:.2f}s")

        return final_results

    def _vector_search(self, query_vector: List[float], limit: int = 100) -> List[SearchResult]:
        """向量检索"""
        cursor = self.conn.cursor()

        try:
            # 使用向量相似度搜索
            query = f"""
                SELECT
                    id,
                    application_number as patent_id,
                    patent_name,
                    applicant,
                    abstract,
                    ipc_main_class,
                    patent_type,
                    source_year,
                    1 - (embedding_combined <=> %s::vector) as similarity
                FROM patents_vectorized
                WHERE embedding_combined IS NOT NULL
                ORDER BY embedding_combined <=> %s::vector
                LIMIT %s
            """

            cursor.execute(query, (query_vector, query_vector, limit))
            rows = cursor.fetchall()

            results = []
            for row in rows:
                result = SearchResult(
                    id=row[0],
                    patent_id=row[1],
                    patent_name=row[2] or '',
                    applicant=row[3] or '',
                    abstract=row[4] or '',
                    ipc_main_class=row[5] or '',
                    patent_type=row[6] or '',
                    source_year=row[7] or 0,
                    vector_score=float(row[8])
                )
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"❌ 向量检索失败: {e}")
            return []
        finally:
            cursor.close()

    def _keyword_search(self, query_conditions: Dict[str, Any], limit: int = 100) -> List[SearchResult]:
        """关键词检索"""
        cursor = self.conn.cursor()

        try:
            # 构建SQL查询
            where_clauses = []
            params = []

            # 关键词条件
            if query_conditions['keyword_conditions']:
                keyword_where = ' OR '.join(query_conditions['keyword_conditions'])
                where_clauses.append(f"({keyword_where})")

            # IPC分类条件
            if query_conditions['ipc_conditions']:
                ipc_where = ' OR '.join(query_conditions['ipc_conditions'])
                where_clauses.append(f"({ipc_where})")

            if not where_clauses:
                return []

            query = f"""
                SELECT
                    id,
                    application_number as patent_id,
                    patent_name,
                    applicant,
                    abstract,
                    ipc_main_class,
                    patent_type,
                    source_year,
                    ts_rank(search_vector, plainto_tsquery('chinese', %s)) as rank_score
                FROM patents
                WHERE {' AND '.join(where_clauses)}
                ORDER BY rank_score DESC
                LIMIT %s
            """

            # 准备搜索查询
            search_query = ' & '.join(query_conditions['keyword_conditions'][:5])  # 限制关键词数量
            params.append(search_query)
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            results = []
            for row in rows:
                result = SearchResult(
                    id=row[0],
                    patent_id=row[1],
                    patent_name=row[2] or '',
                    applicant=row[3] or '',
                    abstract=row[4] or '',
                    ipc_main_class=row[5] or '',
                    patent_type=row[6] or '',
                    source_year=row[7] or 0,
                    keyword_score=float(row[8])
                )
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"❌ 关键词检索失败: {e}")
            return []
        finally:
            cursor.close()

    def _category_search(self, ipc_predictions: List[str], limit: int = 100) -> List[SearchResult]:
        """分类检索"""
        cursor = self.conn.cursor()

        try:
            # 构建IPC分类查询
            ipc_conditions = ' OR '.join([f"ipc_main_class LIKE '{ipc}%'" for ipc in ipc_predictions])

            query = f"""
                SELECT
                    id,
                    application_number as patent_id,
                    patent_name,
                    applicant,
                    abstract,
                    ipc_main_class,
                    patent_type,
                    source_year
                FROM patents
                WHERE {ipc_conditions}
                ORDER BY source_year DESC
                LIMIT %s
            """

            cursor.execute(query, (limit,))
            rows = cursor.fetchall()

            results = []
            for row in rows:
                result = SearchResult(
                    id=row[0],
                    patent_id=row[1],
                    patent_name=row[2] or '',
                    applicant=row[3] or '',
                    abstract=row[4] or '',
                    ipc_main_class=row[5] or '',
                    patent_type=row[6] or '',
                    source_year=row[7] or 0
                )
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"❌ 分类检索失败: {e}")
            return []
        finally:
            cursor.close()

    def _deduplicate_and_sort(self, results: List[SearchResult], query_info: Dict[str, Any]) -> List[SearchResult]:
        """去重和排序"""
        # 按ID去重
        seen_ids = set()
        unique_results = []

        for result in results:
            if result.id not in seen_ids:
                seen_ids.add(result.id)
                unique_results.append(result)

        # 计算综合评分
        for result in unique_results:
            # 归一化评分
            vector_score = min(result.vector_score, 1.0) if result.vector_score > 0 else 0
            keyword_score = min(result.keyword_score, 1.0) if result.keyword_score > 0 else 0

            # 综合评分（带权重）
            result.score = (
                vector_score * self.vector_weight +
                keyword_score * self.keyword_weight
            )

        # 按评分排序
        unique_results.sort(key=lambda x: x.score, reverse=True)

        return unique_results

    def stage2_rerank(self, recall_results: List[SearchResult], query_info: Dict[str, Any]) -> List[SearchResult]:
        """
        第二阶段：LLM重排
        使用大语言模型对召回结果进行精准评分

        Args:
            recall_results: 第一阶段召回的结果
            query_info: 查询信息

        Returns:
            重排后的结果
        """
        logger.info(f"🔄 第二阶段：开始重排...")
        start_time = time.time()

        # TODO: 集成LLM重排
        # 这里先使用简单的规则重排
        reranked_results = self._rule_based_rerank(recall_results, query_info)

        # 限制数量
        final_results = reranked_results[:self.rerank_limit]

        elapsed = time.time() - start_time
        logger.info(f"✅ 第二阶段完成：重排 {len(final_results)} 条记录，耗时 {elapsed:.2f}s")

        return final_results

    def _rule_based_rerank(self, results: List[SearchResult], query_info: Dict[str, Any]) -> List[SearchResult]:
        """基于规则的重排"""
        # 规则1：年份权重（越新越重要）
        current_year = datetime.now().year
        for result in results:
            year_weight = max(0.1, 1.0 - (current_year - result.source_year) * 0.02)
            result.score = result.score * 0.7 + year_weight * 0.3

        # 规则2：专利类型权重（发明 > 实用新型 > 外观设计）
        type_weights = {'发明': 1.0, '实用新型': 0.7, '外观设计': 0.5}
        for result in results:
            type_weight = type_weights.get(result.patent_type, 0.5)
            result.score = result.score * type_weight

        # 规则3：IPC分类匹配度
        query_keywords = set(query_info['keywords'])
        for result in results:
            if result.ipc_main_class:
                # 简单的IPC-关键词匹配
                match_score = 1.0 if any(kw in result.ipc_main_class for kw in query_keywords) else 0.5
                result.score = result.score * match_score

        # 重新排序
        results.sort(key=lambda x: x.score, reverse=True)

        return results

    def stage3_fetch_fulltext(self, reranked_results: List[SearchResult]) -> List[SearchResult]:
        """
        第三阶段：获取全文
        从外部数据源获取完整专利文本

        Args:
            reranked_results: 第二阶段重排的结果

        Returns:
            包含全文的最终结果
        """
        logger.info(f"🔄 第三阶段：获取全文...")
        start_time = time.time()

        # TODO: 集成Google Patents API或其他全文获取服务
        # 这里先使用数据库中的摘要
        final_results = reranked_results[:self.final_limit]

        elapsed = time.time() - start_time
        logger.info(f"✅ 第三阶段完成：获取 {len(final_results)} 条记录的全文，耗时 {elapsed:.2f}s")

        return final_results

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        执行完整的三阶段检索

        Args:
            query: 搜索查询
            limit: 返回结果数量限制

        Returns:
            搜索结果列表
        """
        start_time = time.time()

        try:
            # 查询预处理
            query_info = self.preprocess_query(query)

            # 第一阶段：召回
            recall_results = self.stage1_recall(query_info)

            # 第二阶段：重排
            reranked_results = self.stage2_rerank(recall_results, query_info)

            # 第三阶段：获取全文
            final_results = self.stage3_fetch_fulltext(reranked_results)

            # 限制最终结果数量
            if limit < len(final_results):
                final_results = final_results[:limit]

            # 构建返回结果
            search_results = []
            for i, result in enumerate(final_results, 1):
                search_results.append({
                    'rank': i,
                    'id': result.id,
                    'patent_id': result.patent_id,
                    'patent_name': result.patent_name,
                    'applicant': result.applicant,
                    'abstract': result.abstract,
                    'ipc_main_class': result.ipc_main_class,
                    'patent_type': result.patent_type,
                    'source_year': result.source_year,
                    'score': result.score,
                    'vector_score': result.vector_score,
                    'keyword_score': result.keyword_score,
                    'llm_score': result.llm_score
                })

            total_time = time.time() - start_time

            # 记录搜索日志
            self._log_search(query, len(search_results), total_time)

            return search_results

        except Exception as e:
            logger.error(f"❌ 搜索失败: {e}")
            return []

    def _log_search(self, query: str, result_count: int, execution_time: float):
        """记录搜索日志"""
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO patent_search_logs (query, search_type, results_count, execution_time_ms)
                VALUES (%s, %s, %s, %s)
            """, (query, 'three_stage_search', result_count, execution_time * 1000))
        except Exception as e:
            logger.error(f"❌ 记录搜索日志失败: {e}")
        finally:
            cursor.close()

def main():
    """测试搜索引擎"""
    logger.info('🔧 三阶段专利混合检索引擎测试')
    logger.info(str('=' * 50))

    # 创建搜索引擎
    engine = PatentSearchEngine()

    # 连接数据库
    if not engine.connect():
        logger.info('❌ 无法连接数据库')
        return

    # 测试查询
    test_queries = [
        '人工智能图像识别',
        '电动汽车电池技术',
        '5G通信系统',
        '医疗诊断设备'
    ]

    for query in test_queries:
        logger.info(f"\n🔍 搜索: {query}")
        logger.info(str('-' * 50))

        results = engine.search(query, limit=5)

        if results:
            for result in results:
                logger.info(f"\n排名 {result['rank']}: {result['patent_name']}")
                logger.info(f"   申请人: {result['applicant']}")
                logger.info(f"   年份: {result['source_year']}")
                logger.info(f"   评分: {result['score']:.3f}")
                logger.info(f"   摘要: {result['abstract'][:100]}...")
        else:
            logger.info('   未找到相关专利')

if __name__ == '__main__':
    main()