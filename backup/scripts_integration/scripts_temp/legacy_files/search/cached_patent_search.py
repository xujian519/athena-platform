#!/usr/bin/env python3
"""
带Redis缓存的专利检索引擎
Cached Patent Search Engine with Redis

基于双表协同+Redis缓存的高性能专利检索系统
"""

import hashlib
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import psycopg2
import redis

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

# Redis配置
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'decode_responses': True
}

@dataclass
class SearchResult:
    """搜索结果"""
    id: int
    patent_name: str
    applicant: str
    abstract: str
    ipc_main_class: str
    patent_type: str
    source_year: int
    application_number: str
    score: float = 0.0
    search_type: str = 'hybrid'

class CachedPatentSearchEngine:
    """带Redis缓存的专利搜索引擎"""

    def __init__(self):
        """初始化搜索引擎"""
        self.conn = None
        self.redis_client = None
        self.cache_ttl = 3600  # 缓存1小时
        self.popular_cache_ttl = 86400  # 热门查询缓存24小时

        # 热门查询词列表
        self.popular_queries = {
            '人工智能', '机器学习', '深度学习', '神经网络',
            '通信技术', '半导体', '大数据', '云计算',
            '物联网', '区块链', '5G', '自动驾驶'
        }

    def connect(self) -> bool:
        """连接数据库和Redis"""
        # 连接PostgreSQL
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.conn.autocommit = True
            logger.info('✅ PostgreSQL连接成功')
        except Exception as e:
            logger.error(f"❌ PostgreSQL连接失败: {e}")
            return False

        # 连接Redis
        try:
            self.redis_client = redis.Redis(**REDIS_CONFIG)
            self.redis_client.ping()
            logger.info('✅ Redis连接成功')
        except Exception as e:
            logger.error(f"❌ Redis连接失败: {e}")
            return False

        return True

    def _generate_cache_key(self, query: str, limit: int = 10, search_type: str = 'fulltext') -> str:
        """生成缓存键"""
        content = f"patent_search:{search_type}:{query}:{limit}"
        return hashlib.md5(content.encode('utf-8'), usedforsecurity=False).hexdigest()

    def _is_popular_query(self, query: str) -> bool:
        """判断是否为热门查询"""
        return query.strip() in self.popular_queries

    def get_cached_results(self, query: str, limit: int = 10) -> List[SearchResult | None]:
        """从缓存获取搜索结果"""
        cache_key = self._generate_cache_key(query, limit, 'fulltext')

        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                logger.info(f"🎯 缓存命中: {query}")
                data = json.loads(cached_data)
                return [SearchResult(**item) for item in data]
        except Exception as e:
            logger.warning(f"⚠️ 缓存读取失败: {e}")

        return None

    def cache_search_results(self, query: str, results: List[SearchResult], limit: int = 10):
        """缓存搜索结果"""
        cache_key = self._generate_cache_key(query, limit, 'fulltext')

        # 确定TTL
        ttl = self.popular_cache_ttl if self._is_popular_query(query) else self.cache_ttl

        try:
            # 序列化结果
            serialized_results = json.dumps([asdict(result) for result in results], ensure_ascii=False)

            # 存储到Redis
            self.redis_client.setex(cache_key, ttl, serialized_results)

            # 记录缓存设置
            logger.info(f"💾 缓存已设置: {query} (TTL: {ttl}秒)")

            # 添加到热门查询计数
            self.redis_client.incr(f"search_count:{query}")
            self.redis_client.expire(f"search_count:{query}", 86400 * 7)  # 7天过期

        except Exception as e:
            logger.warning(f"⚠️ 缓存设置失败: {e}")

    def search_patents_simple_fulltext(self, query: str, limit: int = 1000) -> List[str]:
        """使用全文检索索引快速筛选patents_simple"""
        sql = """
        SELECT DISTINCT application_number
        FROM patents_simple
        WHERE to_tsvector('chinese', COALESCE(patent_name, '') || ' ' || COALESCE(abstract, '')) @@ plainto_tsquery('chinese', %s)
        LIMIT %s
        """

        start_time = time.time()

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, (query, limit))
                results = cursor.fetchall()

            end_time = time.time()
            search_time = (end_time - start_time) * 1000
            logger.info(f"✅ 全文检索筛选完成：{len(results)}条候选，耗时 {search_time:.2f}ms")

            return [row[0] for row in results]

        except Exception as e:
            logger.error(f"❌ 全文检索筛选失败: {e}")
            return []

    def search_patents_detailed_fulltext(self, query: str, candidate_numbers: List[str], limit: int = 100) -> List[SearchResult]:
        """基于候选集进行全文检索"""
        if not candidate_numbers:
            return []

        # 使用全文检索的详细搜索
        sql = """
        SELECT
            p.id,
            p.patent_name,
            p.applicant,
            p.abstract,
            p.ipc_main_class,
            p.patent_type,
            p.source_year,
            p.application_number,
            -- 基于全文检索的相关性评分
            ts_rank(
                to_tsvector('chinese', COALESCE(p.patent_name, '') || ' ' || COALESCE(p.abstract, '')),
                plainto_tsquery('chinese', %s)
            ) * 10 + -- 文本匹配得分(0-10)
            CASE
                WHEN p.citation_count > 0 THEN LEAST(p.citation_count / 50.0, 2.0)  -- 引用得分(0-2)
                ELSE 0
            END +
            CASE
                WHEN p.source_year >= 2020 THEN 1.0  -- 时效性得分
                ELSE 0.5
            END as score
        FROM patents p
        WHERE p.application_number = ANY(%s)
          AND to_tsvector('chinese', COALESCE(p.patent_name, '') || ' ' || COALESCE(p.abstract, '')) @@ plainto_tsquery('chinese', %s)
        ORDER BY score DESC, p.citation_count DESC
        LIMIT %s
        """

        start_time = time.time()

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, (query, candidate_numbers, query, limit))
                results = cursor.fetchall()

            end_time = time.time()
            search_time = (end_time - start_time) * 1000
            logger.info(f"✅ 全文详细检索完成：{len(results)}条结果，耗时 {search_time:.2f}ms")

            search_results = []
            for row in results:
                search_results.append(SearchResult(
                    id=row[0],
                    patent_name=row[1] or '',
                    applicant=row[2] or '',
                    abstract=row[3] or '',
                    ipc_main_class=row[4] or '',
                    patent_type=row[5] or '',
                    source_year=row[6] or 0,
                    application_number=row[7] or '',
                    score=float(row[8]),
                    search_type='fulltext_cached'
                ))

            return search_results

        except Exception as e:
            logger.error(f"❌ 全文详细检索失败: {e}")
            return []

    def cached_hybrid_search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """带缓存的混合搜索"""
        logger.info(f"🚀 开始缓存混合搜索: {query}")
        total_start = time.time()

        # 第一步：检查缓存
        cached_results = self.get_cached_results(query, limit)
        if cached_results:
            logger.info(f"✅ 缓存命中，直接返回 {len(cached_results)} 条结果")
            return cached_results

        # 第二步：执行搜索
        # 第一阶段：全文快速筛选
        logger.info('🔄 第一阶段：全文快速筛选...')
        candidate_numbers = self.search_patents_simple_fulltext(query, limit=1000)

        # 第二阶段：全文详细检索
        logger.info('🔄 第二阶段：全文详细检索...')
        results = self.search_patents_detailed_fulltext(query, candidate_numbers, limit)

        # 第三步：缓存结果
        if results:
            self.cache_search_results(query, results, limit)

        total_end = time.time()
        total_time = (total_end - total_start) * 1000
        logger.info(f"✅ 缓存混合搜索完成：{len(results)}条结果，总耗时 {total_time:.2f}ms")

        return results

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            # 获取搜索次数统计
            search_counts = {}
            for query in self.popular_queries:
                count = self.redis_client.get(f"search_count:{query}")
                if count:
                    search_counts[query] = int(count)

            # 获取Redis基本信息
            redis_info = self.redis_client.info()

            return {
                'popular_search_counts': search_counts,
                'redis_memory_used': redis_info.get('used_memory_human', 'N/A'),
                'redis_connected_clients': redis_info.get('connected_clients', 'N/A'),
                'redis_total_commands_processed': redis_info.get('total_commands_processed', 'N/A')
            }

        except Exception as e:
            logger.error(f"❌ 获取缓存统计失败: {e}")
            return {}

    def clear_cache(self, pattern: str = 'patent_search:*'):
        """清理缓存"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"🧹 已清理 {len(keys)} 个缓存项")
            else:
                logger.info('🧹 没有找到需要清理的缓存项')
        except Exception as e:
            logger.error(f"❌ 缓存清理失败: {e}")

def main():
    """主函数：测试带缓存的专利搜索"""
    logger.info('🎯 带Redis缓存的专利检索测试')
    logger.info(str('=' * 60))

    # 初始化搜索引擎
    engine = CachedPatentSearchEngine()
    if not engine.connect():
        logger.info('❌ 连接失败')
        return

    # 测试查询列表（包含热门查询）
    test_queries = [
        '人工智能',    # 热门查询
        '机器学习',    # 热门查询
        '深度学习',    # 热门查询
        '神经网络',    # 热门查询
        '通信技术',    # 热门查询
        '半导体',      # 热门查询
        '大数据',      # 热门查询
        '云计算'       # 热门查询
    ]

    logger.info('📝 测试查询列表:')
    for i, query in enumerate(test_queries, 1):
        popular = '🔥' if engine._is_popular_query(query) else '  '
        logger.info(f"   {popular} {i}. {query}")

    logger.info(str("\n" + '=' * 60))
    logger.info('🚀 开始测试（带缓存）...')

    # 第一次搜索（缓存未命中）
    logger.info("\n📊 第一轮搜索（缓存未命中）:")
    for i, query in enumerate(test_queries[:4], 1):  # 测试前4个
        logger.info(f"\n🔍 搜索 {i}: {query}")
        logger.info(str('-' * 30))

        start_time = time.time()
        results = engine.cached_hybrid_search(query, limit=5)
        end_time = time.time()

        if results:
            logger.info(f"✅ 找到 {len(results)} 条相关专利 (耗时 {(end_time-start_time)*1000:.2f}ms)")
            for j, result in enumerate(results, 1):
                logger.info(f"   {j}. {result.patent_name[:40]}... (得分: {result.score:.3f})")
        else:
            logger.info('❌ 未找到相关专利')

    # 第二次搜索（缓存命中）
    logger.info(str("\n" + '=' * 60))
    logger.info('📊 第二轮搜索（应该缓存命中）:')
    for i, query in enumerate(test_queries[:4], 1):  # 重复搜索前4个
        logger.info(f"\n🔍 搜索 {i}: {query}")
        logger.info(str('-' * 30))

        start_time = time.time()
        results = engine.cached_hybrid_search(query, limit=5)
        end_time = time.time()

        if results:
            logger.info(f"✅ 找到 {len(results)} 条相关专利 (耗时 {(end_time-start_time)*1000:.2f}ms)")
        else:
            logger.info('❌ 未找到相关专利')

    # 显示缓存统计
    logger.info(str("\n" + '=' * 60))
    logger.info('📈 缓存统计信息:')
    stats = engine.get_cache_stats()

    logger.info('🔥 热门查询搜索次数:')
    for query, count in stats.get('popular_search_counts', {}).items():
        logger.info(f"   {query}: {count}次")

    logger.info("\n📊 Redis状态:")
    logger.info(f"   内存使用: {stats.get('redis_memory_used', 'N/A')}")
    logger.info(f"   连接客户端: {stats.get('redis_connected_clients', 'N/A')}")

    logger.info("\n✅ 缓存测试完成!")

if __name__ == '__main__':
    main()