#!/usr/bin/env python3
"""
知识系统性能测试
"""

from __future__ import annotations
import statistics
import time
from typing import Any

from nebula3.Config import Config
from nebula3.gclient.net import ConnectionPool
from qdrant_client import QdrantClient


def test_qdrant_perf() -> Any:
    """测试 Qdrant 性能"""
    client = QdrantClient(url='http://localhost:6333')

    times = []
    for _i in range(100):
        start = time.time()
        client.scroll(
            collection_name='legal_laws_enhanced',
            limit=10,
            with_payload=True,
            with_vectors=False
        )
        times.append((time.time() - start) * 1000)

    return {
        'avg': round(statistics.mean(times), 2),
        'p95': round(statistics.quantiles(times, n=20)[18], 2),
        'max': round(max(times), 2)
    }

def test_nebula_perf() -> Any:
    """测试 NebulaGraph 性能"""
    config = Config()
    connection_pool = ConnectionPool()
    connection_pool.init([('127.0.0.1', 9669)], config)
    session = connection_pool.get_session('root', 'nebula')
    session.execute('USE legal_kg;')

    times = []
    for _i in range(100):
        start = time.time()
        session.execute('MATCH (l:Law) RETURN count(l) AS count;')
        times.append((time.time() - start) * 1000)

    session.release()
    connection_pool.close()

    return {
        'avg': round(statistics.mean(times), 2),
        'p95': round(statistics.quantiles(times, n=20)[18], 2),
        'max': round(max(times), 2)
    }

if __name__ == '__main__':
    print('=' * 60)
    print('知识系统性能测试')
    print('=' * 60)

    print('\n_qdrant 向量搜索性能 (100次):')
    qdrant = test_qdrant_perf()
    for k, v in qdrant.items():
        print(f'  {k}: {v}ms')

    print('\n_nebula_graph 图查询性能 (100次):')
    nebula = test_nebula_perf()
    for k, v in nebula.items():
        print(f'  {k}: {v}ms')

    print('\n性能评估:')
    if qdrant['p95'] < 100 and nebula['p95'] < 100:
        print('  ✅ 性能优秀 (P95 < 100ms)')
    elif qdrant['p95'] < 500 and nebula['p95'] < 500:
        print('  ✅ 性能良好 (P95 < 500ms)')
    else:
        print('  ⚠️  需要优化')
