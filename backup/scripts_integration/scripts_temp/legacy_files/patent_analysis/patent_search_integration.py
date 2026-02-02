#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利检索集成模块
Patent Search Integration Module

整合本地PostgreSQL数据库和外部专利检索功能
"""

import json
import logging
import re
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

sys.path.append('/Users/xujian/Athena工作平台')

class PatentSearchIntegration:
    """专利检索集成类"""
    
    def __init__(self):
        self.local_patents = []
        self.external_results = []
        
    def search_local_database(self, keywords: List[str], technical_field: str = '') -> List[Dict]:
        """在本地PostgreSQL数据库中检索相关专利"""
        try:
            import psycopg2

            # 连接本地数据库
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                user='postgres',
                database='patent_db'
            )
            cursor = conn.cursor()
            
            results = []
            
            # 构建检索查询
            search_terms = keywords + ([technical_field] if technical_field else [])
            
            for term in search_terms:
                # 在专利名称、摘要、权利要求中搜索
                query = """
                SELECT 
                    id,
                    patent_name,
                    abstract,
                    applicant,
                    application_date,
                    publication_number,
                    ipc_code
                FROM patents 
                WHERE 
                    patent_name ILIKE %s OR 
                    abstract ILIKE %s OR 
                    applicant ILIKE %s
                LIMIT 50;
                """
                
                cursor.execute(query, (f'%{term}%', f'%{term}%', f'%{term}%'))
                
                for row in cursor.fetchall():
                    patent = {
                        'source': 'local_pgsql',
                        'id': row[0],
                        'patent_name': row[1],
                        'abstract': row[2] or '',
                        'applicant': row[3] or '',
                        'application_date': str(row[4]) if row[4] else '',
                        'publication_number': row[5] or '',
                        'ipc_code': row[6] or '',
                        'relevance_score': self._calculate_relevance(term, row[1], row[2] or '')
                    }
                    results.append(patent)
            
            conn.close()
            
            # 去重并按相关性排序
            results = self._deduplicate_and_sort(results)
            self.local_patents = results[:20]  # 保留前20个最相关的
            
            return self.local_patents
            
        except Exception as e:
            logger.info(f"本地数据库检索失败: {e}")
            return []
    
    def search_external_patents(self, keywords: List[str], technical_field: str = '') -> List[Dict]:
        """外部专利检索（Google Patents等）"""
        try:
            # 这里可以调用之前的Google Patents搜索功能
            # 或者使用其他外部API
            results = []
            
            # 模拟外部检索结果
            for keyword in keywords[:3]:  # 限制搜索词数量
                external_results = self._search_google_patents(keyword)
                results.extend(external_results)
            
            self.external_results = results[:10]  # 保留前10个
            
            return self.external_results
            
        except Exception as e:
            logger.info(f"外部检索失败: {e}")
            return []
    
    def _search_google_patents(self, keyword: str) -> List[Dict]:
        """搜索Google Patents"""
        # 这里应该集成实际的Google Patents API
        # 暂时返回模拟数据
        return [
            {
                'source': 'google_patents',
                'patent_name': f'Related patent for {keyword}',
                'abstract': f'This patent relates to {keyword} technology...',
                'applicant': 'External Company',
                'publication_number': 'USXXXXXXXX',
                'relevance_score': 0.7
            }
        ]
    
    def _calculate_relevance(self, keyword: str, title: str, abstract: str) -> float:
        """计算专利与关键词的相关性得分"""
        score = 0.0
        
        # 标题匹配
        if keyword.lower() in title.lower():
            score += 0.5
        
        # 摘要匹配
        if keyword.lower() in abstract.lower():
            score += 0.3
        
        # 部分匹配
        title_words = title.lower().split()
        abstract_words = abstract.lower().split()
        
        for word in title_words:
            if keyword.lower() in word or word in keyword.lower():
                score += 0.1
                
        for word in abstract_words:
            if keyword.lower() in word or word in keyword.lower():
                score += 0.05
        
        return min(score, 1.0)
    
    def _deduplicate_and_sort(self, patents: List[Dict]) -> List[Dict]:
        """去重并按相关性排序"""
        # 按专利号去重
        seen_patents = set()
        unique_patents = []
        
        for patent in patents:
            patent_id = patent.get('publication_number', '') + patent.get('patent_name', '')
            if patent_id not in seen_patents:
                seen_patents.add(patent_id)
                unique_patents.append(patent)
        
        # 按相关性排序
        unique_patents.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return unique_patents
    
    def compare_with_prior_art(self, invention_features: List[str], search_results: List[Dict]) -> Dict:
        """与现有技术进行对比分析"""
        comparison = {
            'closest_prior_art': [],
            'novelty_analysis': {},
            'obviousness_assessment': '',
            'recommendations': []
        }
        
        if not search_results:
            comparison['novelty_analysis'] = {
                'status': 'highly_novel',
                'reason': '未发现高度相关的现有技术'
            }
            comparison['obviousness_assessment'] = '技术方案具有非显而易见性'
            return comparison
        
        # 找出最接近的现有技术
        closest_patents = sorted(search_results, key=lambda x: x.get('relevance_score', 0), reverse=True)[:3]
        comparison['closest_prior_art'] = closest_patents
        
        # 分析新颖性
        novelty_score = self._analyze_novelty(invention_features, closest_patents)
        comparison['novelty_analysis'] = novelty_score
        
        # 评估显而易见性
        comparison['obviousness_assessment'] = self._assess_obviousness(invention_features, closest_patents)
        
        # 生成建议
        comparison['recommendations'] = self._generate_recommendations(novelty_score, closest_patents)
        
        return comparison
    
    def _analyze_novelty(self, features: List[str], prior_art: List[Dict]) -> Dict:
        """分析新颖性"""
        if not prior_art:
            return {'status': 'highly_novel', 'score': 1.0, 'reason': '无相关现有技术'}
        
        # 将现有技术的内容合并
        prior_content = ''
        for patent in prior_art:
            prior_content += f" {patent.get('patent_name', '')} {patent.get('abstract', '')}"
        
        # 检查每个特征的新颖性
        novel_features = []
        known_features = []
        
        for feature in features:
            feature_words = set(feature.lower().split())
            prior_words = set(prior_content.lower().split())
            
            # 计算特征在现有技术中的出现程度
            overlap = len(feature_words & prior_words) / len(feature_words) if feature_words else 0
            
            if overlap < 0.3:  # 低于30%重叠认为是新颖的
                novel_features.append(feature)
            else:
                known_features.append(feature)
        
        novelty_ratio = len(novel_features) / len(features) if features else 0
        
        if novelty_ratio >= 0.7:
            status = 'highly_novel'
            reason = '大部分技术特征具有新颖性'
        elif novelty_ratio >= 0.4:
            status = 'moderately_novel'
            reason = '部分技术特征具有新颖性'
        else:
            status = 'low_novelty'
            reason = '大部分技术特征已被现有技术披露'
        
        return {
            'status': status,
            'score': novelty_ratio,
            'reason': reason,
            'novel_features': novel_features,
            'known_features': known_features
        }
    
    def _assess_obviousness(self, features: List[str], prior_art: List[Dict]) -> str:
        """评估显而易见性"""
        if not prior_art:
            return '由于缺少相关现有技术，技术方案具有非显而易见性'
        
        # 分析是否存在技术启示
        teaching_found = False
        combination_motive = False
        
        # 检查现有技术是否提供了组合的技术启示
        if len(prior_art) > 1:
            # 假设多篇专利的组合可能提供启示
            teaching_found = True
            combination_motive = True
        
        # 评估
        if teaching_found and combination_motive:
            return '多篇现有技术的组合可能提供了技术启示，需要证明组合产生了预料不到的技术效果'
        elif teaching_found:
            return '现有技术可能提供了一定的技术启示，需要证明技术方案的进步性'
        else:
            return '现有技术未提供明确的技术启示，技术方案具有非显而易见性'
    
    def _generate_recommendations(self, novelty_analysis: Dict, prior_art: List[Dict]) -> List[str]:
        """生成建议"""
        recommendations = []
        
        novelty_score = novelty_analysis.get('score', 0)
        
        if novelty_score < 0.4:
            recommendations.append('建议重新评估技术方案的创新点，或寻找其他发明构思')
            recommendations.append('考虑限制保护范围，突出核心技术特征')
        
        if prior_art:
            recommendations.append('在说明书中详细描述与现有技术的区别')
            recommendations.append('强调技术方案解决了现有技术未能解决的问题')
            recommendations.append('提供技术效果的对比数据')
        
        if novelty_analysis.get('novel_features'):
            recommendations.append('重点保护具有新颖性的技术特征')
        
        return recommendations

# 测试代码
if __name__ == '__main__':
    searcher = PatentSearchIntegration()
    
    # 测试检索
    keywords = ['机械装置', '传动机构', '自动控制']
    results = searcher.search_local_database(keywords, '机械工程')
    
    logger.info(f"找到 {len(results)} 个相关专利")
    for result in results[:5]:
        logger.info(f"- {result['patent_name']} (相关性: {result['relevance_score']:.2f})")
