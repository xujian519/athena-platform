#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能专利检索系统
Smart Patent Search System

策略：关键词检索 → 向量验证 → 优化输出
作者: 小诺
创建时间: 2025-12-10
"""

import argparse
import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List, Optional

from keyword_patent_search import KeywordPatentSearch, SearchQuery
from vector_verification_engine import VectorVerificationEngine, VerificationResult

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SmartSearchRequest:
    """智能搜索请求"""
    query_text: str
    boolean_logic: str = 'AND'  # AND, OR, NOT
    patent_types: List[str] = None
    year_range: Dict | None = None
    applicant: str | None = None
    ipc_code: str | None = None
    keyword_limit: int = 500
    final_limit: int = 20
    boost_recent: bool = True

@dataclass
class SmartSearchResult:
    """智能搜索结果"""
    query_info: Dict
    keyword_results: Dict
    verification_results: Dict
    final_results: List[Dict]
    metrics: Dict
    total_time: float
    recommendations: List[str]

class SmartPatentSearch:
    """智能专利检索系统"""

    def __init__(self):
        self.keyword_search = KeywordPatentSearch()
        self.vector_verification = VectorVerificationEngine()

    def connect(self):
        """连接所有组件"""
        return self.keyword_search.connect()

    def search(self, request: SmartSearchRequest) -> SmartSearchResult:
        """执行智能检索"""
        start_time = datetime.now()

        logger.info(f"🚀 开始智能检索: {request.query_text}")

        # 第一阶段：关键词检索
        keyword_query = SearchQuery(
            keywords=request.query_text,
            boolean_logic=request.boolean_logic,
            filters={
                'patent_type': request.patent_types,
                'year_range': request.year_range,
                'applicant': request.applicant,
                'ipc_code': request.ipc_code
            },
            limit=request.keyword_limit,
            boost_recent=request.boost_recent
        )

        keyword_result = self.keyword_search.search(keyword_query)
        keyword_time = (datetime.now() - start_time).total_seconds()

        logger.info(f"📊 关键词检索完成: {keyword_result.total_count}条，耗时{keyword_time:.3f}秒")

        # 第二阶段：向量验证
        verification_start = datetime.now()
        verified_patents = self.vector_verification.verify_batch(
            request.query_text,
            keyword_result.patents
        )
        verification_time = (datetime.now() - verification_start).total_seconds()

        logger.info(f"🔍 向量验证完成: {len(verified_patents)}条，耗时{verification_time:.3f}秒")

        # 第三阶段：分析和建议
        improvements = self.vector_verification.analyze_improvement(
            keyword_result.patents[:20],
            verified_patents
        )

        # 生成建议
        recommendations = self._generate_recommendations(
            request, keyword_result, verified_patents, improvements
        )

        total_time = (datetime.now() - start_time).total_seconds()

        return SmartSearchResult(
            query_info=asdict(request),
            keyword_results={
                'total_found': keyword_result.total_count,
                'returned': len(keyword_result.patents),
                'search_time': keyword_time,
                'query_used': keyword_result.query_used
            },
            verification_results={
                'verified_count': len(verified_patents),
                'verification_time': verification_time,
                'similarity_threshold': self.vector_verification.similarity_threshold
            },
            final_results=verified_patents[:request.final_limit],
            metrics=improvements,
            total_time=total_time,
            recommendations=recommendations
        )

    def _generate_recommendations(self, request: SmartSearchRequest,
                                 keyword_result, verified_patents, improvements) -> List[str]:
        """生成检索建议"""
        recommendations = []

        # 基于检索结果的建议
        if keyword_result.total_count == 0:
            recommendations.append('💡 尝试使用同义词或更宽泛的关键词')
            recommendations.append('💡 检查拼写错误或使用不同的布尔逻辑')

        elif keyword_result.total_count > 10000:
            recommendations.append('💡 结果过多，建议增加筛选条件（如年份、申请人）')

        elif len(verified_patents) < 5:
            recommendations.append('💡 验证结果较少，可尝试使用OR逻辑扩展搜索')

        # 基于改进效果的建议
        if improvements.get('score_improvement', 0) > 0.1:
            recommendations.append('✨ 向量验证显著提升了结果质量')
        elif improvements.get('score_improvement', 0) < -0.1:
            recommendations.append('⚠️ 向量验证显示相关性可能需要调整')

        # 基于查询复杂度的建议
        if len(request.query_text.split()) > 10:
            recommendations.append('💡 查询较长，建议分解为多个独立查询')
        elif not request.patent_types and not request.year_range:
            recommendations.append('💡 添加专利类型或年份筛选可提高精度')

        return recommendations

    def close(self):
        """关闭所有连接"""
        self.keyword_search.close()

# CLI接口
def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(description='智能专利检索系统')
    parser.add_argument('query', help='检索关键词')
    parser.add_argument('--logic', choices=['AND', 'OR', 'NOT'], default='AND', help='布尔逻辑')
    parser.add_argument('--type', nargs='+', choices=['发明', '实用新型', '外观设计'], help='专利类型')
    parser.add_argument('--year-start', type=int, help='开始年份')
    parser.add_argument('--year-end', type=int, help='结束年份')
    parser.add_argument('--applicant', help='申请人')
    parser.add_argument('--ipc', help='IPC分类')
    parser.add_argument('--limit', type=int, default=20, help='最终结果数量')
    parser.add_argument('--keyword-limit', type=int, default=500, help='关键词检索数量限制')
    parser.add_argument('--output', choices=['json', 'table'], default='table', help='输出格式')

    args = parser.parse_args()

    # 创建搜索请求
    request = SmartSearchRequest(
        query_text=args.query,
        boolean_logic=args.logic,
        patent_types=args.type,
        year_range={'start': args.year_start, 'end': args.year_end} if args.year_start or args.year_end else None,
        applicant=args.applicant,
        ipc_code=args.ipc,
        keyword_limit=args.keyword_limit,
        final_limit=args.limit
    )

    # 执行检索
    search_system = SmartPatentSearch()

    if not search_system.connect():
        logger.info('❌ 无法连接数据库')
        return

    try:
        result = search_system.search(request)

        # 输出结果
        if args.output == 'json':
            logger.info(str(json.dumps(asdict(result)), indent=2, ensure_ascii=False))
        else:
            # 表格格式输出
            logger.info(f"\n🎯 智能检索结果")
            logger.info(str(f"=" * 50))
            logger.info(f"查询: {request.query_text}")
            logger.info(f"关键词检索: {result.keyword_results['total_found']}条 → {result.keyword_results['returned']}条")
            logger.info(f"向量验证: {result.verification_results['verified_count']}条")
            logger.info(f"最终输出: {len(result.final_results)}条")
            logger.info(f"总耗时: {result.total_time:.3f}秒")
            print()

            logger.info(f"\n📊 检索指标")
            logger.info(str(f"=" * 30))
            if result.metrics:
                for metric, value in result.metrics.items():
                    logger.info(f"{metric}: {value:.3f}")

            logger.info(f"\n💡 智能建议")
            logger.info(str(f"=" * 30))
            for rec in result.recommendations:
                logger.info(str(rec))

            logger.info(f"\n🏆 最终结果 (Top {min(10, len(result.final_results))})")
            logger.info(str(f"=" * 50))
            for i, patent in enumerate(result.final_results[:10], 1):
                logger.info(f"{i:2d}. {patent.get('patent_name', '')[:60]}...")
                logger.info(f"    申请人: {patent.get('applicant', '')}")
                logger.info(f"    申请号: {patent.get('application_number', '')}")
                logger.info(f"    相关性: {patent.get('combined_score', 0):.3f}")
                print()

    except Exception as e:
        logger.info(f"❌ 检索失败: {e}")
        logger.error(f"检索失败: {e}: {exc_info=True}")

    finally:
        search_system.close()

if __name__ == '__main__':
    main()