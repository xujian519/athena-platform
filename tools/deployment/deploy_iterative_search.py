#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迭代专利搜索服务部署脚本
Deploy Iterative Patent Search Service

独立部署脚本，不依赖复杂的第三方库

作者: Athena AI系统
创建时间: 2025-12-08
版本: 1.0.0
"""

import asyncio
import hashlib
import json
import logging
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 添加项目路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SearchQualityMetrics:
    """搜索质量指标"""
    def __init__(self):
        self.relevance_score = 0.0
        self.completeness_score = 0.0
        self.accuracy_score = 0.0
        self.diversity_score = 0.0
        self.novelty_score = 0.0
        self.overall_score = 0.0
    
    def calculate_overall(self):
        """计算综合评分"""
        weights = {'relevance': 0.3, 'completeness': 0.2, 'accuracy': 0.25, 'diversity': 0.15, 'novelty': 0.1}
        self.overall_score = (
            self.relevance_score * weights['relevance'] +
            self.completeness_score * weights['completeness'] +
            self.accuracy_score * weights['accuracy'] +
            self.diversity_score * weights['diversity'] +
            self.novelty_score * weights['novelty']
        )
        return self.overall_score

class StandaloneIterativeSearch:
    """独立迭代搜索服务"""
    
    def __init__(self):
        self.max_iterations = 3
        self.quality_threshold = 0.7
        self.search_history = []
        self.patent_database = self._create_patent_database()
        
        logger.info('🚀 独立迭代搜索服务初始化完成')
    
    def _create_patent_database(self) -> List[Dict]:
        """创建模拟专利数据库"""
        patents = [
            {
                'id': 'CN202310123456',
                'title': '基于深度学习的智能专利检索系统',
                'abstract': '本发明提供了一种基于深度学习技术的智能专利检索方法，通过神经网络模型实现专利文本的语义理解和相似度计算...',
                'publication_date': '2023-10-15',
                'authors': ['张明', '李华', '王强'],
                'applicant': '北京智能科技有限公司',
                'patent_type': '发明专利',
                'field': '人工智能',
                'keywords': ['深度学习', '专利检索', '神经网络', '语义理解'],
                'source': 'CNIPA',
                'citations': 15
            },
            {
                'id': 'US20230123456',
                'title': 'Machine Learning Based Patent Analysis System',
                'abstract': 'A system and method for analyzing patents using machine learning algorithms, including natural language processing and pattern recognition...',
                'publication_date': '2023-05-20',
                'authors': ['John Smith', 'Alice Johnson'],
                'applicant': 'AI Tech Corp',
                'patent_type': 'Utility Patent',
                'field': 'Artificial Intelligence',
                'keywords': ['machine learning', 'patent analysis', 'NLP', 'pattern recognition'],
                'source': 'USPTO',
                'citations': 23
            },
            {
                'id': 'EP20230098765',
                'title': 'Neural Network Patent Classification Method',
                'abstract': 'Method for classifying patents using neural network technology with improved accuracy and efficiency...',
                'publication_date': '2023-08-10',
                'authors': ['Dr. Mueller', 'Prof. Schmidt'],
                'applicant': 'EuroTech Innovation',
                'patent_type': 'Patent Application',
                'field': 'Machine Learning',
                'keywords': ['neural network', 'patent classification', 'efficiency', 'accuracy'],
                'source': 'EPO',
                'citations': 8
            },
            {
                'id': 'CN202209876543',
                'title': '自然语言处理在专利挖掘中的应用',
                'abstract': '本发明涉及自然语言处理技术在专利文本挖掘中的应用，通过文本分析和知识图谱构建实现专利价值的深度挖掘...',
                'publication_date': '2022-12-01',
                'authors': ['刘晓明', '陈志强'],
                'applicant': '上海数据智能研究院',
                'patent_type': '发明专利',
                'field': '自然语言处理',
                'keywords': ['自然语言处理', '专利挖掘', '知识图谱', '文本分析'],
                'source': 'CNIPA',
                'citations': 12
            },
            {
                'id': 'WO2023078901',
                'title': 'Intelligent Patent Portfolio Management System',
                'abstract': 'An intelligent system for managing patent portfolios using AI algorithms and predictive analytics...',
                'publication_date': '2023-07-15',
                'authors': ['Dr. Yamamoto', 'Prof. Tanaka'],
                'applicant': 'Global IP Solutions',
                'patent_type': 'PCT Application',
                'field': 'Intellectual Property Management',
                'keywords': ['patent portfolio', 'management system', 'AI algorithms', 'predictive analytics'],
                'source': 'WIPO',
                'citations': 18
            },
            {
                'id': 'US20220456789',
                'title': 'Computer Vision Patent Prior Art Search',
                'abstract': 'System for searching patent prior art in computer vision field using image recognition and similarity matching...',
                'publication_date': '2022-11-30',
                'authors': ['Dr. Chen', 'Dr. Wang'],
                'applicant': 'VisionTech Inc',
                'patent_type': 'Utility Patent',
                'field': 'Computer Vision',
                'keywords': ['computer vision', 'prior art search', 'image recognition', 'similarity matching'],
                'source': 'USPTO',
                'citations': 31
            },
            {
                'id': 'CN202115432198',
                'title': '基于强化学习的专利布局优化方法',
                'abstract': '提出一种基于强化学习算法的专利布局优化方法，通过智能代理实现专利组合的最优配置...',
                'publication_date': '2021-09-20',
                'authors': ['赵创新', '钱智能'],
                'applicant': '深圳未来科技有限公司',
                'patent_type': '发明专利',
                'field': '强化学习',
                'keywords': ['强化学习', '专利布局', '智能代理', '优化配置'],
                'source': 'CNIPA',
                'citations': 7
            },
            {
                'id': 'EP20210056789',
                'title': 'Blockchain-based Patent Registration System',
                'abstract': 'A decentralized patent registration system using blockchain technology for enhanced security and transparency...',
                'publication_date': '2021-04-12',
                'authors': ['Dr. Anderson', 'Ms. Wilson'],
                'applicant': 'ChainIP Ltd',
                'patent_type': 'Patent Application',
                'field': 'Blockchain',
                'keywords': ['blockchain', 'patent registration', 'decentralized', 'security'],
                'source': 'EPO',
                'citations': 25
            }
        ]
        
        logger.info(f"📚 专利数据库加载完成，共 {len(patents)} 条专利")
        return patents
    
    async def search_patents(self, query: str, enable_refinement: bool = True, max_results: int = 10) -> Dict:
        """搜索专利"""
        logger.info(f"🔍 开始搜索: {query}")
        start_time = time.time()
        
        # 1. 初始搜索
        initial_results = await self._initial_search(query, max_results)
        logger.info(f"📊 初始搜索返回 {len(initial_results)} 条结果")
        
        # 2. 评估初始质量
        initial_quality = self._evaluate_quality(query, initial_results)
        logger.info(f"📈 初始质量评分: {initial_quality.overall_score:.3f}")
        
        # 3. 迭代改进（如果启用）
        if enable_refinement and initial_quality.overall_score < self.quality_threshold:
            logger.info('🔄 启动迭代改进...')
            refined_results = await self._iterative_refine(query, initial_results)
            final_quality = self._evaluate_quality(query, refined_results)
        else:
            refined_results = initial_results
            final_quality = initial_quality
            logger.info('⚡ 跳过迭代改进')
        
        # 4. 构建结果
        search_time = time.time() - start_time
        result = {
            'query': query,
            'results': refined_results,
            'total_count': len(refined_results),
            'search_time': search_time,
            'refinement_applied': enable_refinement and initial_quality.overall_score < self.quality_threshold,
            'initial_quality': initial_quality.overall_score,
            'final_quality': final_quality.overall_score,
            'quality_improvement': final_quality.overall_score - initial_quality.overall_score,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"✅ 搜索完成，耗时 {search_time:.2f}s，最终质量: {final_quality.overall_score:.3f}")
        
        # 保存搜索历史
        self._save_search_history(result)
        
        return result
    
    async def _initial_search(self, query: str, max_results: int) -> List[Dict]:
        """执行初始搜索"""
        query_terms = set(query.lower().split())
        scored_results = []
        
        for patent in self.patent_database:
            score = self._calculate_relevance(query_terms, patent)
            if score > 0:
                patent_copy = patent.copy()
                patent_copy['relevance_score'] = score
                scored_results.append(patent_copy)
        
        # 按相关性排序并限制结果数量
        scored_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return scored_results[:max_results]
    
    def _calculate_relevance(self, query_terms: set, patent: Dict) -> float:
        """计算专利与查询的相关性"""
        score = 0.0
        
        # 标题匹配
        title_words = set(patent['title'].lower().split())
        title_matches = len(query_terms.intersection(title_words))
        score += (title_matches / len(query_terms)) * 0.5
        
        # 摘要匹配
        abstract_words = set(patent['abstract'].lower().split())
        abstract_matches = len(query_terms.intersection(abstract_words))
        score += min(1.0, abstract_matches / len(query_terms)) * 0.3
        
        # 关键词匹配
        keywords = [k.lower() for k in patent.get('keywords', [])]
        keyword_matches = len(query_terms.intersection(set(keywords)))
        score += (keyword_matches / len(query_terms)) * 0.2
        
        return min(1.0, score)
    
    def _evaluate_quality(self, query: str, results: List[Dict]) -> SearchQualityMetrics:
        """评估搜索结果质量"""
        metrics = SearchQualityMetrics()
        
        if not results:
            return metrics
        
        # 相关性评分
        metrics.relevance_score = sum(r['relevance_score'] for r in results) / len(results)
        
        # 完整性评分
        completeness_scores = []
        for result in results:
            required_fields = ['title', 'abstract', 'publication_date', 'authors']
            present_fields = sum(1 for field in required_fields if field in result and result[field])
            completeness_scores.append(present_fields / len(required_fields))
        metrics.completeness_score = sum(completeness_scores) / len(completeness_scores)
        
        # 准确性评分
        accuracy_scores = []
        for result in results:
            score = 1.0
            if not result.get('title') or len(result['title']) < 5:
                score -= 0.3
            if not result.get('abstract') or len(result['abstract']) < 50:
                score -= 0.2
            if result.get('publication_date') == 'invalid_date':
                score -= 0.2
            accuracy_scores.append(max(0.0, score))
        metrics.accuracy_score = sum(accuracy_scores) / len(accuracy_scores)
        
        # 多样性评分
        sources = [r.get('source') for r in results]
        unique_sources = len(set(s for s in sources if s))
        metrics.diversity_score = unique_sources / len(sources) if sources else 0.0
        
        # 新颖性评分
        current_year = datetime.now().year
        novelty_scores = []
        for result in results:
            pub_date = result.get('publication_date', '')
            if pub_date and len(pub_date) >= 4:
                try:
                    year = int(pub_date[:4])
                    novelty_score = max(0.0, 1.0 - (current_year - year) / 10)
                    novelty_scores.append(novelty_score)
                except:
                    novelty_scores.append(0.5)
            else:
                novelty_scores.append(0.0)
        metrics.novelty_score = sum(novelty_scores) / len(novelty_scores)
        
        metrics.calculate_overall()
        return metrics
    
    async def _iterative_refine(self, query: str, results: List[Dict]) -> List[Dict]:
        """执行迭代改进"""
        current_results = results.copy()
        query_terms = set(query.lower().split())
        
        for iteration in range(self.max_iterations):
            logger.info(f"🔄 第 {iteration + 1} 轮迭代改进...")
            
            # 评估当前质量
            quality = self._evaluate_quality(query, current_results)
            logger.info(f"   当前质量: {quality.overall_score:.3f}")
            
            if quality.overall_score >= self.quality_threshold:
                logger.info(f"✅ 质量达标，停止迭代")
                break
            
            # 应用改进策略
            if quality.relevance_score < 0.6:
                # 查询扩展
                expanded_terms = self._expand_query(query_terms)
                expanded_results = await self._search_with_expanded_terms(expanded_terms)
                current_results = self._merge_results(current_results, expanded_results)
            
            if quality.completeness_score < 0.7:
                # 过滤低质量结果
                current_results = [r for r in current_results if self._is_high_quality(r)]
            
            if quality.diversity_score < 0.5:
                # 重新排序以增加多样性
                current_results = self._rerank_for_diversity(current_results)
            
            # 限制结果数量
            current_results = current_results[:10]
        
        return current_results
    
    def _expand_query(self, query_terms: set) -> set:
        """扩展查询词"""
        # 简单的同义词扩展
        synonyms = {
            '人工智能': ['AI', 'machine learning', '深度学习'],
            '机器学习': ['machine learning', 'ML', '深度学习'],
            '专利': ['patent', '知识产权', '发明'],
            '深度学习': ['deep learning', 'neural network', '神经网络'],
            '自然语言处理': ['NLP', 'natural language processing', '文本处理'],
            '计算机视觉': ['computer vision', 'CV', '图像识别'],
            '区块链': ['blockchain', 'distributed ledger', '分布式账本']
        }
        
        expanded_terms = set(query_terms)
        for term in query_terms:
            for key, values in synonyms.items():
                if term in key or key in term:
                    expanded_terms.update(values)
        
        return expanded_terms
    
    async def _search_with_expanded_terms(self, expanded_terms: set) -> List[Dict]:
        """使用扩展词搜索"""
        return await self._initial_search(' '.join(expanded_terms), 10)
    
    def _merge_results(self, results1: List[Dict], results2: List[Dict]) -> List[Dict]:
        """合并搜索结果"""
        seen_ids = set()
        merged = []
        
        for result in results1 + results2:
            if result['id'] not in seen_ids:
                seen_ids.add(result['id'])
                merged.append(result)
        
        return merged
    
    def _is_high_quality(self, result: Dict) -> bool:
        """判断是否为高质量结果"""
        return (
            result.get('relevance_score', 0) > 0.3 and
            len(result.get('title', '')) > 5 and
            len(result.get('abstract', '')) > 50
        )
    
    def _rerank_for_diversity(self, results: List[Dict]) -> List[Dict]:
        """为多样性重新排序"""
        # 简单的多样性重排序：交替不同来源的专利
        sources = ['CNIPA', 'USPTO', 'EPO', 'WIPO']
        source_groups = {source: [] for source in sources}
        
        for result in results:
            source = result.get('source')
            if source in source_groups:
                source_groups[source].append(result)
            else:
                source_groups['USPTO'].append(result)
        
        # 交替选择不同来源的结果
        reranked = []
        for _ in range(len(results)):
            for source in sources:
                if source_groups[source]:
                    reranked.append(source_groups[source].pop(0))
        
        return reranked
    
    def _save_search_history(self, result: Dict):
        """保存搜索历史"""
        try:
            history_file = Path('/Users/xujian/Athena工作平台/data/search_history.json')
            
            # 加载现有历史
            history = []
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    try:
                        history = json.load(f)
                    except:
                        history = []
            
            # 添加新记录
            history.append({
                'timestamp': result['timestamp'],
                'query': result['query'],
                'results_count': result['total_count'],
                'quality_improvement': result['quality_improvement'],
                'refinement_applied': result['refinement_applied']
            })
            
            # 限制历史记录数量
            history = history[-100:]
            
            # 保存历史
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.warning(f"保存搜索历史失败: {e}")
    
    def get_statistics(self) -> Dict:
        """获取搜索统计"""
        try:
            history_file = Path('/Users/xujian/Athena工作平台/data/search_history.json')
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                
                total_searches = len(history)
                refinement_applied = sum(1 for h in history if h.get('refinement_applied'))
                avg_improvement = sum(h.get('quality_improvement', 0) for h in history) / max(1, total_searches)
                
                return {
                    'total_searches': total_searches,
                    'refinement_rate': refinement_applied / max(1, total_searches),
                    'average_improvement': avg_improvement,
                    'patent_database_size': len(self.patent_database)
                }
        except:
            pass
        
        return {
            'total_searches': 0,
            'refinement_rate': 0.0,
            'average_improvement': 0.0,
            'patent_database_size': len(self.patent_database)
        }

async def main():
    """主函数 - 演示部署和使用"""
    logger.info('🚀 迭代专利搜索服务部署演示')
    logger.info(str('=' * 60))
    
    # 创建服务实例
    search_service = StandaloneIterativeSearch()
    
    # 演示查询
    demo_queries = [
        '人工智能 专利',
        '机器学习 深度学习',
        '自然语言处理 NLP',
        '计算机视觉 图像识别',
        '区块链 知识产权'
    ]
    
    logger.info('🔍 开始演示搜索功能...')
    print()
    
    all_results = []
    
    for i, query in enumerate(demo_queries, 1):
        logger.info(f"📋 演示 {i}: {query}")
        
        # 搜索专利
        result = await search_service.search_patents(
            query=query,
            enable_refinement=True,
            max_results=5
        )
        
        # 显示结果
        logger.info(f"   📊 找到 {result['total_count']} 条专利")
        logger.info(f"   📈 初始质量: {result['initial_quality']:.3f}")
        logger.info(f"   📈 最终质量: {result['final_quality']:.3f}")
        logger.info(f"   📊 质量提升: +{result['quality_improvement']:.3f}")
        logger.info(f"   🔄 迭代改进: {'是' if result['refinement_applied'] else '否'}")
        logger.info(f"   ⏱️ 搜索耗时: {result['search_time']:.2f}s")
        
        # 显示前3个结果
        logger.info('   📋 搜索结果预览:')
        for j, patent in enumerate(result['results'][:3], 1):
            logger.info(f"      {j}. {patent['title']}")
            logger.info(f"         相关性: {patent['relevance_score']:.3f}")
        
        print()
        all_results.append(result)
    
    # 显示总体统计
    stats = search_service.get_statistics()
    logger.info('📊 服务统计信息:')
    logger.info(f"   总搜索次数: {stats['total_searches']}")
    logger.info(f"   迭代改进率: {stats['refinement_rate']:.1%}")
    logger.info(f"   平均质量提升: +{stats['average_improvement']:.3f}")
    logger.info(f"   专利数据库规模: {stats['patent_database_size']} 条")
    print()
    
    # 计算演示效果
    total_improvement = sum(r['quality_improvement'] for r in all_results)
    avg_improvement = total_improvement / len(all_results)
    refinement_count = sum(1 for r in all_results if r['refinement_applied'])
    
    logger.info('🎯 演示效果评估:')
    logger.info(f"   平均质量提升: +{avg_improvement:.3f}")
    logger.info(f"   迭代改进使用率: {refinement_count}/{len(all_results)} ({refinement_count/len(all_results):.1%})")
    print()
    
    if avg_improvement > 0.05:
        logger.info('🎉 迭代改进机制效果显著!')
        logger.info('✅ 系统可以正式部署使用')
    else:
        logger.info('⚠️ 迭代改进效果有限')
        logger.info('📝 建议进一步优化算法')
    
    logger.info("\n💡 使用说明:")
    logger.info('1. 导入: from deploy_iterative_search import StandaloneIterativeSearch')
    logger.info('2. 创建: service = StandaloneIterativeSearch()')
    logger.info("3. 搜索: result = await service.search_patents('查询词')")
    logger.info('4. 统计: stats = service.get_statistics()')
    print()
    logger.info('🚀 服务已准备就绪，可以立即投入使用!')

if __name__ == '__main__':
    asyncio.run(main())