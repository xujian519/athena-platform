#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena工作平台渐进式优化工具
在现有架构基础上逐步优化性能
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http.exceptions import UnexpectedResponse
    from qdrant_client.models import Distance, OptimizersConfigDiff, VectorParams
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProgressiveOptimizer:
    """渐进式优化器"""

    def __init__(self):
        self.project_root = Path(project_root)
        self.qdrant_client = QdrantClient('http://localhost:6333') if QDRANT_AVAILABLE else None
        self.optimization_log = []

    def analyze_current_state(self) -> Dict[str, Any]:
        """分析当前系统状态"""
        logger.info('🔍 分析当前系统状态...')

        state = {
            'timestamp': datetime.now().isoformat(),
            'qdrant_collections': {},
            'total_vectors': 0,
            'optimization_opportunities': []
        }

        if not self.qdrant_client:
            logger.error('❌ Qdrant客户端未初始化')
            return state

        # 分析每个集合
        collections = self.qdrant_client.get_collections().collections

        for collection in collections:
            try:
                # 获取基本信息
                count = self.qdrant_client.count(collection.name).count
                info = self.qdrant_client.get_collection(collection.name)

                collection_state = {
                    'vectors_count': count,
                    'vector_size': info.config.params.vectors.size,
                    'distance': info.config.params.vectors.distance.value,
                    'status': info.status
                }

                # 分析优化机会
                if count > 0:
                    # 大集合可能需要分片
                    if count > 100000:
                        state['optimization_opportunities'].append({
                            'type': 'sharding',
                            'collection': collection.name,
                            'reason': f"大集合({count:,} vectors)可考虑分片"
                        })

                    # 检查是否需要索引优化
                    if count > 10000:
                        state['optimization_opportunities'].append({
                            'type': 'indexing',
                            'collection': collection.name,
                            'reason': f"中型集合({count:,} vectors)可优化HNSW参数"
                        })

                    # 检查向量维度
                    if info.config.params.vectors.size > 1024:
                        state['optimization_opportunities'].append({
                            'type': 'dimension_reduction',
                            'collection': collection.name,
                            'reason': f"高维向量({info.config.params.vectors.size}维)可考虑降维"
                        })

                state['qdrant_collections'][collection.name] = collection_state
                state['total_vectors'] += count

                logger.info(f"  ✅ {collection.name}: {count:,} vectors")

            except Exception as e:
                logger.warning(f"  ⚠️ 分析集合失败 {collection.name}: {e}")
                state['qdrant_collections'][collection.name] = {'error': str(e)}

        return state

    def optimize_hnsw_parameters(self, collection_name: str, m: int = 16, ef_construct: int = 100) -> Dict[str, Any]:
        """优化HNSW参数"""
        logger.info(f"🔧 优化 {collection_name} 的HNSW参数...")

        try:
            # 更新HNSW参数
            self.qdrant_client.update_collection(
                collection_name=collection_name,
                optimizer_config=OptimizersConfigDiff(
                    hnsw={
                        'm': m,
                        'ef_construct': ef_construct,
                        'full_scan_threshold': 10000
                    }
                )
            )

            result = {
                'status': 'success',
                'collection': collection_name,
                'm': m,
                'ef_construct': ef_construct,
                'timestamp': datetime.now().isoformat()
            }

            logger.info(f"  ✅ HNSW参数已更新: m={m}, ef_construct={ef_construct}")
            return result

        except Exception as e:
            logger.error(f"  ❌ 优化失败: {e}")
            return {
                'status': 'error',
                'collection': collection_name,
                'error': str(e)
            }

    def create_search_performance_report(self) -> Dict[str, Any]:
        """创建搜索性能报告"""
        logger.info('📊 创建搜索性能报告...')

        if not self.qdrant_client:
            return {'error': 'Qdrant客户端未初始化'}

        # 选择几个代表性集合进行测试
        test_collections = []
        for name, info in self.analyze_current_state()['qdrant_collections'].items():
            if info.get('vectors_count', 0) > 1000:
                test_collections.append(name)

        performance_report = {
            'timestamp': datetime.now().isoformat(),
            'test_collections': test_collections,
            'results': {}
        }

        for collection in test_collections[:3]:  # 测试前3个
            try:
                # 获取一个查询向量
                points, _ = self.qdrant_client.scroll(
                    collection_name=collection,
                    limit=1,
                    with_vectors=True
                )

                if points:
                    query_vector = points[0].vector

                    # 测试不同搜索参数的性能
                    search_tests = [
                        {'limit': 10, 'search_params': {'hnsw_ef': 64}},
                        {'limit': 50, 'search_params': {'hnsw_ef': 128}},
                        {'limit': 100, 'search_params': {'hnsw_ef': 256}}
                    ]

                    collection_results = []

                    for test in search_tests:
                        start_time = time.time()

                        results = self.qdrant_client.search(
                            collection_name=collection,
                            query_vector=query_vector,
                            limit=test['limit'],
                            search_params=test['search_params']
                        )

                        elapsed = time.time() - start_time

                        collection_results.append({
                            'limit': test['limit'],
                            'hnsw_ef': test['search_params']['hnsw_ef'],
                            'time_ms': elapsed * 1000,
                            'results_count': len(results)
                        })

                    performance_report['results'][collection] = collection_results
                    logger.info(f"  ✅ {collection} 性能测试完成")

            except Exception as e:
                logger.error(f"  ❌ 测试 {collection} 失败: {e}")
                performance_report['results'][collection] = {'error': str(e)}

        return performance_report

    def suggest_optimization_plan(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """建议优化计划"""
        logger.info('💡 生成优化建议...')

        plan = []

        # 1. 基于集合大小的优化建议
        for name, info in state['qdrant_collections'].items():
            if 'error' in info:
                continue

            count = info.get('vectors_count', 0)

            if count > 100000:
                plan.append({
                    'priority': 'high',
                    'action': '分片优化',
                    'target': name,
                    'description': f"大集合({count:,} vectors)建议分片存储",
                    'implementation': '考虑按类型或时间分片'
                })

            elif count > 10000:
                plan.append({
                    'priority': 'medium',
                    'action': '索引优化',
                    'target': name,
                    'description': f"中等集合({count:,} vectors)优化HNSW参数",
                    'implementation': '调整m=16, ef_construct=128'
                })

            elif count > 0:
                plan.append({
                    'priority': 'low',
                    'action': '监控观察',
                    'target': name,
                    'description': f"小集合({count:,} vectors)保持现状",
                    'implementation': '定期检查性能指标'
                })

        # 2. 通用优化建议
        plan.extend([
            {
                'priority': 'high',
                'action': '缓存策略',
                'target': 'system',
                'description': '实现查询结果缓存',
                'implementation': '使用Redis缓存热门查询'
            },
            {
                'priority': 'medium',
                'action': '批量操作',
                'target': 'api',
                'description': '优化批量向量操作',
                'implementation': '使用批处理提高吞吐量'
            },
            {
                'priority': 'low',
                'action': '监控建设',
                'target': 'monitoring',
                'description': '建立性能监控体系',
                'implementation': 'Prometheus + Grafana仪表板'
            }
        ])

        return plan

    def run_optimization_phase_1(self) -> Dict[str, Any]:
        """执行第一阶段优化（立即执行）"""
        logger.info('🚀 执行第一阶段优化...')

        results = {
            'phase': 'phase_1_immediate',
            'start_time': datetime.now().isoformat(),
            'actions': []
        }

        # 1. 优化主要集合的HNSW参数
        main_collections = [
            'legal_clauses',
            'ai_technical_terms_vector_db',
            'legal_documents',
            'patent_rules_unified_1024'
        ]

        for collection in main_collections:
            try:
                # 检查集合是否存在且有数据
                count = self.qdrant_client.count(collection).count
                if count > 5000:
                    # 根据集合大小调整参数
                    m = 16 if count < 50000 else 32
                    ef_construct = 128 if count < 50000 else 200

                    result = self.optimize_hnsw_parameters(collection, m, ef_construct)
                    results['actions'].append(result)
                    self.optimization_log.append(result)

            except Exception as e:
                logger.warning(f"  ⚠️ 跳过集合 {collection}: {e}")

        results['end_time'] = datetime.now().isoformat()
        results['duration_seconds'] = (
            datetime.fromisoformat(results['end_time']) -
            datetime.fromisoformat(results['start_time'])
        ).total_seconds()

        return results

    def generate_optimization_report(self) -> Dict[str, Any]:
        """生成完整的优化报告"""
        logger.info('📋 生成优化报告...')

        # 1. 分析当前状态
        state = self.analyze_current_state()

        # 2. 性能测试
        performance = self.create_search_performance_report()

        # 3. 优化计划
        plan = self.suggest_optimization_plan(state)

        # 4. 执行第一阶段优化
        phase1_results = self.run_optimization_phase_1()

        # 5. 生成报告
        report = {
            'report_id': f"optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'generated_at': datetime.now().isoformat(),
            'current_state': state,
            'performance_tests': performance,
            'optimization_plan': plan,
            'phase_1_results': phase1_results,
            'optimization_log': self.optimization_log,
            'next_steps': [
                '1. 监控第一阶段优化的效果',
                '2. 根据性能测试结果调整参数',
                '3. 实施第二阶段优化计划',
                '4. 建立持续优化流程'
            ]
        }

        # 保存报告
        report_path = self.project_root / 'optimization_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)

        return report

def main():
    """主函数"""
    logger.info('🔄 Athena工作平台 - 渐进式优化工具')
    logger.info(str('='*60))

    if not QDRANT_AVAILABLE:
        logger.info('❌ 请安装qdrant-client')
        return

    optimizer = ProgressiveOptimizer()

    try:
        # 生成完整优化报告
        report = optimizer.generate_optimization_report()

        # 打印摘要
        logger.info(str("\n" + '='*60))
        logger.info('📊 优化报告摘要')
        logger.info(str('='*60))

        state = report['current_state']
        plan = report['optimization_plan']
        phase1 = report['phase_1_results']

        logger.info(f"总向量数: {state['total_vectors']:,}")
        logger.info(f"集合数量: {len(state['qdrant_collections'])}")
        logger.info(f"优化机会: {len(state['optimization_opportunities'])}")

        logger.info("\n优化计划:")
        for item in plan[:5]:
            priority_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(item['priority'], '⚪')
            logger.info(f"  {priority_icon} {item['action']}: {item['description']}")

        logger.info("\n第一阶段执行:")
        logger.info(f"  执行时间: {phase1['duration_seconds']:.2f}秒")
        logger.info(f"  优化操作: {len(phase1['actions'])}")

        logger.info("\n✅ 优化报告已生成: optimization_report.json")
        logger.info("\n建议下一步:")
        for step in report['next_steps'][:3]:
            logger.info(f"  • {step}")

    except Exception as e:
        logger.error(f"❌ 优化失败: {e}")
        logger.info(f"\n❌ 优化过程中出现错误: {e}")

if __name__ == '__main__':
    main()