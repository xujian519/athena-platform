#!/usr/bin/env python3
"""
专利数据分析和可视化服务
Patent Data Analytics and Visualization Service

提供专利数据的统计分析、趋势分析、可视化图表等功能

作者: Athena (智慧女神)
创建时间: 2025-12-07
版本: 1.0.0
"""

import asyncio
import json
import logging
import re
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

import numpy as np

# 数据处理
from google_patents_retriever import PatentData

# 导入专利数据模型

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PatentAnalytics:
    """专利数据分析器"""

    def __init__(self):
        self.patent_data: list[PatentData] = []
        self.analytics_cache = {}

    async def analyze_patents(self, patents: list[PatentData]) -> dict[str, Any]:
        """
        分析专利数据

        Args:
            patents: 专利数据列表

        Returns:
            分析结果
        """
        self.patent_data = patents

        if not patents:
            return {
                'error': '没有专利数据可供分析',
                'total_patents': 0
            }

        try:
            analysis_result = {
                'summary': self._get_summary_statistics(),
                'temporal_analysis': self._analyze_temporal_trends(),
                'assignee_analysis': self._analyze_assignees(),
                'classification_analysis': self._analyze_classifications(),
                'inventor_analysis': self._analyze_inventors(),
                'keyword_analysis': self._analyze_keywords(),
                'geographic_analysis': self._analyze_geographic_distribution(),
                'technology_trends': self._analyze_technology_trends(),
                'quality_metrics': self._calculate_quality_metrics(),
                'recommendations': self._generate_recommendations(),
                'analysis_timestamp': datetime.now().isoformat()
            }

            return analysis_result

        except Exception as e:
            logger.error(f"专利分析失败: {e}")
            return {
                'error': str(e),
                'total_patents': len(patents)
            }

    def _get_summary_statistics(self) -> dict[str, Any]:
        """获取基础统计信息"""
        total_patents = len(self.patent_data)

        # 计算基础指标
        has_abstract = sum(1 for p in self.patent_data if p.abstract and p.abstract.strip())
        has_assignee = sum(1 for p in self.patent_data if p.assignee and p.assignee.strip())
        has_inventors = sum(1 for p in self.patent_data if p.inventors)
        has_classification = sum(1 for p in self.patent_data if p.classification and p.classification.strip())

        # 计算年份分布
        years = []
        for patent in self.patent_data:
            if patent.filing_date:
                year_match = re.search(r'(\d{4})', patent.filing_date)
                if year_match:
                    years.append(int(year_match.group(1)))

        year_range = (min(years), max(years)) if years else (None, None)

        return {
            'total_patents': total_patents,
            'patents_with_abstract': has_abstract,
            'patents_with_assignee': has_assignee,
            'patents_with_inventors': has_inventors,
            'patents_with_classification': has_classification,
            'data_completeness': {
                'abstract_rate': (has_abstract / total_patents * 100) if total_patents > 0 else 0,
                'assignee_rate': (has_assignee / total_patents * 100) if total_patents > 0 else 0,
                'inventor_rate': (has_inventors / total_patents * 100) if total_patents > 0 else 0,
                'classification_rate': (has_classification / total_patents * 100) if total_patents > 0 else 0
            },
            'year_range': {
                'earliest': year_range[0],
                'latest': year_range[1],
                'span': year_range[1] - year_range[0] if year_range[0] else 0
            }
        }

    def _analyze_temporal_trends(self) -> dict[str, Any]:
        """分析时间趋势"""
        yearly_counts = defaultdict(int)
        monthly_counts = defaultdict(int)

        for patent in self.patent_data:
            if patent.filing_date:
                # 提取年份
                year_match = re.search(r'(\d{4})', patent.filing_date)
                if year_match:
                    year = int(year_match.group(1))
                    yearly_counts[year] += 1

                # 提取月份（简化处理）
                month_match = re.search(r'(\d{4})-(\d{2})', patent.filing_date)
                if month_match:
                    year_month = f"{month_match.group(1)}-{month_match.group(2)}"
                    monthly_counts[year_month] += 1

        # 计算趋势
        years = sorted(yearly_counts.keys())
        if len(years) > 1:
            recent_years = years[-5:]  # 最近5年
            earlier_years = years[:-5] if len(years) > 5 else years[:-1]

            recent_avg = sum(yearly_counts[y] for y in recent_years) / len(recent_years)
            earlier_avg = sum(yearly_counts[y] for y in earlier_years) / len(earlier_years) if earlier_years else 0

            growth_rate = ((recent_avg - earlier_avg) / earlier_avg * 100) if earlier_avg > 0 else 0
        else:
            growth_rate = 0

        return {
            'yearly_distribution': dict(sorted(yearly_counts.items())),
            'monthly_distribution': dict(sorted(monthly_counts.items())[-24:]),  # 最近24个月
            'peak_year': max(yearly_counts.items(), key=lambda x: x[1]) if yearly_counts else None,
            'growth_rate': round(growth_rate, 2),
            'trend': 'increasing' if growth_rate > 10 else 'decreasing' if growth_rate < -10 else 'stable'
        }

    def _analyze_assignees(self) -> dict[str, Any]:
        """分析申请人分布"""
        assignee_counter = Counter()

        for patent in self.patent_data:
            if patent.assignee and patent.assignee.strip():
                # 清理申请人名称
                assignee = self._clean_assignee_name(patent.assignee)
                assignee_counter[assignee] += 1

        # 获取顶级申请人
        top_assignees = assignee_counter.most_common(20)

        # 计算集中度
        total_patents = len(self.patent_data)
        top_5_patents = sum(count for _, count in top_assignees[:5])
        concentration = (top_5_patents / total_patents * 100) if total_patents > 0 else 0

        # 分析申请人类型
        assignee_types = defaultdict(int)
        for assignee, _ in top_assignees:
            if any(keyword in assignee.lower() for keyword in ['university', 'college', 'institute', 'academic']):
                assignee_types['academic'] += 1
            elif any(keyword in assignee.lower() for keyword in ['corp', 'inc', 'ltd', 'company', 'co']):
                assignee_types['corporate'] += 1
            elif any(keyword in assignee.lower() for keyword in ['government', 'dept', 'ministry']):
                assignee_types['government'] += 1
            else:
                assignee_types['individual'] += 1

        return {
            'total_unique_assignees': len(assignee_counter),
            'top_assignees': [{'name': name, 'patents': count, 'percentage': round(count/total_patents*100, 2)}
                              for name, count in top_assignees],
            'concentration_metrics': {
                'top_5_concentration': round(concentration, 2),
                'herfindahl_index': self._calculate_herfindahl_index(assignee_counter)
            },
            'assignee_types': dict(assignee_types)
        }

    def _analyze_classifications(self) -> dict[str, Any]:
        """分析专利分类号"""
        classification_counter = Counter()
        section_counter = Counter()

        for patent in self.patent_data:
            if patent.classification and patent.classification.strip():
                # 处理多个分类号
                classifications = re.split(r'[,;]\s*', patent.classification)
                for classification in classifications:
                    classification = classification.strip()
                    if classification:
                        classification_counter[classification] += 1

                        # 提取主分类（第一个字母）
                        if classification and classification[0].isalpha():
                            section_counter[classification[0] += 1

        # 获取顶级分类
        top_classifications = classification_counter.most_common(20)

        # 分类号层级分析
        level_analysis = defaultdict(int)
        for classification, _ in top_classifications:
            # 简化分类号分析
            if len(classification) >= 1:
                level_analysis['section'] += 1
            if len(classification) >= 3:
                level_analysis['class'] += 1
            if len(classification) >= 4:
                level_analysis['subclass'] += 1

        return {
            'total_unique_classifications': len(classification_counter),
            'top_classifications': [{'code': code, 'patents': count, 'percentage': round(count/len(self.patent_data)*100, 2)}
                                   for code, count in top_classifications],
            'section_distribution': dict(section_counter),
            'level_analysis': dict(level_analysis)
        }

    def _analyze_inventors(self) -> dict[str, Any]:
        """分析发明人分布"""
        inventor_counter = Counter()
        patent_inventor_count = []

        for patent in self.patent_data:
            if patent.inventors:
                inventors = patent.inventors
                patent_inventor_count.append(len(inventors))

                for inventor in inventors:
                    inventor_counter[inventor] += 1

        # 发明人合作分析
        collaboration_stats = {
            'solo_inventions': patent_inventor_count.count(1),
            'team_inventions': len(patent_inventor_count) - patent_inventor_count.count(1),
            'average_inventors_per_patent': sum(patent_inventor_count) / len(patent_inventor_count) if patent_inventor_count else 0,
            'max_inventors': max(patent_inventor_count) if patent_inventor_count else 0
        }

        # 顶级发明人
        top_inventors = inventor_counter.most_common(20)

        return {
            'total_unique_inventors': len(inventor_counter),
            'top_inventors': [{'name': name, 'patents': count, 'percentage': round(count/len(self.patent_data)*100, 2)}
                             for name, count in top_inventors],
            'collaboration_stats': collaboration_stats
        }

    def _analyze_keywords(self) -> dict[str, Any]:
        """分析关键词"""
        # 合并标题和摘要
        all_text = []
        for patent in self.patent_data:
            text_parts = []
            if patent.title:
                text_parts.append(patent.title)
            if patent.abstract:
                text_parts.append(patent.abstract)
            all_text.append(' '.join(text_parts))

        combined_text = ' '.join(all_text).lower()

        # 清理文本
        cleaned_text = re.sub(r'[^\w\s]', ' ', combined_text)
        words = cleaned_text.split()

        # 过滤停用词（简化版）
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their'}

        # 统计关键词
        word_counter = Counter(word for word in words if word not in stopwords and len(word) > 2)

        # 技术术语识别（简化）
        tech_keywords = []
        for word, count in word_counter.most_common(50):
            if self._is_tech_keyword(word):
                tech_keywords.append({'keyword': word, 'frequency': count})

        return {
            'top_keywords': [{'word': word, 'frequency': count} for word, count in word_counter.most_common(30)],
            'tech_keywords': tech_keywords[:20],
            'total_words': len(words),
            'unique_words': len(word_counter)
        }

    def _analyze_geographic_distribution(self) -> dict[str, Any]:
        """分析地理分布（基于专利号前缀）"""
        geo_counter = Counter()

        for patent in self.patent_data:
            if patent.patent_id:
                prefix = patent.patent_id.split()[0] if ' ' in patent.patent_id else patent.patent_id[:2]

                # 简化的地理映射
                if prefix.startswith('US'):
                    geo_counter['United States'] += 1
                elif prefix.startswith('CN'):
                    geo_counter['China'] += 1
                elif prefix.startswith('EP'):
                    geo_counter['Europe'] += 1
                elif prefix.startswith('JP'):
                    geo_counter['Japan'] += 1
                elif prefix.startswith('KR'):
                    geo_counter['South Korea'] += 1
                elif prefix.startswith('WO'):
                    geo_counter['International (PCT)'] += 1
                else:
                    geo_counter['Other'] += 1

        return {
            'geographic_distribution': dict(geo_counter),
            'diversity_index': self._calculate_diversity_index(geo_counter)
        }

    def _analyze_technology_trends(self) -> dict[str, Any]:
        """分析技术趋势"""
        # 简化的技术趋势分析
        tech_keywords = ['ai', 'machine learning', 'artificial intelligence', 'blockchain', 'iot', 'internet of things', 'cloud', 'big data', '5g', 'quantum', 'biotech', 'nanotechnology']

        keyword_trends = {}
        combined_text = ' '.join([p.title + ' ' + (p.abstract or '') for p in self.patent_data]).lower()

        for keyword in tech_keywords:
            count = combined_text.count(keyword)
            if count > 0:
                keyword_trends[keyword] = count

        # 计算技术集中度
        total_tech_mentions = sum(keyword_trends.values())
        tech_concentration = {k: v/total_tech_mentions*100 for k, v in keyword_trends.items()} if total_tech_mentions > 0 else {}

        return {
            'emerging_technologies': sorted(keyword_trends.items(), key=lambda x: x[1], reverse=True)[:10],
            'technology_concentration': tech_concentration,
            'dominant_technology': max(keyword_trends.items(), key=lambda x: x[1]) if keyword_trends else None
        }

    def _calculate_quality_metrics(self) -> dict[str, Any]:
        """计算质量指标"""
        # 基于可用的数据计算质量指标
        completeness_scores = []

        for patent in self.patent_data:
            score = 0
            max_score = 6

            if patent.title and patent.title.strip():
                score += 1
            if patent.abstract and patent.abstract.strip() and len(patent.abstract) > 50:
                score += 1
            if patent.assignee and patent.assignee.strip():
                score += 1
            if patent.inventors and len(patent.inventors) > 0:
                score += 1
            if patent.classification and patent.classification.strip():
                score += 1
            if patent.filing_date and patent.filing_date.strip():
                score += 1

            completeness_scores.append(score / max_score * 100)

        avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0

        # 相关性分析
        relevance_scores = [getattr(p, 'relevance_score', 0) * 100 for p in self.patent_data]
        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0

        return {
            'data_quality': {
                'average_completeness': round(avg_completeness, 2),
                'high_quality_percentage': len([s for s in completeness_scores if s > 80]) / len(completeness_scores) * 100 if completeness_scores else 0,
                'low_quality_percentage': len([s for s in completeness_scores if s < 50]) / len(completeness_scores) * 100 if completeness_scores else 0
            },
            'relevance_metrics': {
                'average_relevance': round(avg_relevance, 2),
                'high_relevance_percentage': len([s for s in relevance_scores if s > 70]) / len(relevance_scores) * 100 if relevance_scores else 0
            }
        }

    def _generate_recommendations(self) -> list[str]:
        """生成分析建议"""
        recommendations = []

        summary = self._get_summary_statistics()
        assignee_analysis = self._analyze_assignees()
        temporal_analysis = self._analyze_temporal_trends()

        # 数据质量建议
        if summary['data_completeness']['abstract_rate'] < 80:
            recommendations.append('建议完善专利摘要信息，提高数据完整性')

        if summary['data_completeness']['classification_rate'] < 70:
            recommendations.append('建议补充专利分类号，便于技术领域分析')

        # 申请人建议
        if assignee_analysis['concentration_metrics']['top_5_concentration'] > 50:
            recommendations.append('申请人集中度较高，建议关注更多中小企业的创新活动')

        # 时间趋势建议
        if temporal_analysis['trend'] == 'decreasing':
            recommendations.append('专利数量呈下降趋势，建议关注该技术领域的发展前景')

        if temporal_analysis['growth_rate'] > 50:
            recommendations.append('该技术领域增长迅速，建议加大研发投入')

        return recommendations

    def _clean_assignee_name(self, assignee: str) -> str:
        """清理申请人名称"""
        # 移除常见的后缀和标准化格式
        assignee = assignee.strip()

        # 移除法律实体后缀
        suffixes_to_remove = [' ltd', ' ltd.', 'limited', ' inc', ' inc.', 'corporation', ' corp', ' corp.', 'co', 'co.']
        for suffix in suffixes_to_remove:
            pattern = r'\b' + re.escape(suffix) + r'\b\.?$'
            assignee = re.sub(pattern, '', assignee, flags=re.IGNORECASE)

        return assignee.strip()

    def _calculate_herfindahl_index(self, counter: Counter) -> float:
        """计算赫芬达尔指数（市场集中度）"""
        total = sum(counter.values())
        if total == 0:
            return 0

        hhi = sum((count / total) ** 2 for count in counter.values())
        return round(hhi * 10000, 2)  # 通常乘以10000

    def _calculate_diversity_index(self, counter: Counter) -> float:
        """计算多样性指数（香农指数）"""
        total = sum(counter.values())
        if total == 0:
            return 0

        diversity = -sum((count / total) * np.log(count / total) for count in counter.values())
        return round(diversity, 2)

    def _is_tech_keyword(self, word: str) -> bool:
        """判断是否为技术关键词"""
        tech_indicators = ['algorithm', 'system', 'method', 'device', 'apparatus', 'process', 'technology', 'technique', 'protocol', 'framework', 'architecture', 'platform', 'solution']
        return any(indicator in word.lower() for indicator in tech_indicators) or len(word) > 8

    def generate_visualization_data(self, analysis_result: dict[str, Any]) -> dict[str, Any]:
        """生成可视化数据"""
        viz_data = {}

        # 时间趋势图数据
        if 'temporal_analysis' in analysis_result:
            temporal = analysis_result['temporal_analysis']
            viz_data['temporal_chart'] = {
                'type': 'line',
                'data': [
                    {'year': year, 'patents': count}
                    for year, count in temporal['yearly_distribution'].items()
                ],
                'title': '专利数量年度趋势'
            }

        # 申请人分布图数据
        if 'assignee_analysis' in analysis_result:
            assignee = analysis_result['assignee_analysis']
            top_assignees = assignee['top_assignees'][:10]
            viz_data['assignee_chart'] = {
                'type': 'bar',
                'data': [
                    {'name': item['name'], 'patents': item['patents'], 'percentage': item['percentage']}
                    for item in top_assignees
                ],
                'title': '顶级申请人分布'
            }

        # 技术分类饼图数据
        if 'classification_analysis' in analysis_result:
            classification = analysis_result['classification_analysis']
            sections = classification['section_distribution']
            viz_data['classification_chart'] = {
                'type': 'pie',
                'data': [
                    {'section': section, 'patents': count}
                    for section, count in sections.items()
                ],
                'title': '专利分类分布'
            }

        # 关键词词云数据
        if 'keyword_analysis' in analysis_result:
            keywords = analysis_result['keyword_analysis']['top_keywords'][:30]
            viz_data['keyword_cloud'] = {
                'type': 'wordcloud',
                'data': [
                    {'text': word, 'size': frequency}
                    for word, frequency in keywords
                ],
                'title': '关键词分布'
            }

        return viz_data

# 全局分析器实例
patent_analytics = PatentAnalytics()

async def analyze_patent_data(patents: list[PatentData], include_visualization: bool = True) -> dict[str, Any]:
    """
    分析专利数据

    Args:
        patents: 专利数据列表
        include_visualization: 是否包含可视化数据

    Returns:
        分析结果
    """
    result = await patent_analytics.analyze_patents(patents)

    if include_visualization and 'error' not in result:
        result['visualizations'] = patent_analytics.generate_visualization_data(result)

    return result

if __name__ == '__main__':
    # 测试代码
    async def main():
        from google_patents_retriever import PatentData

        # 创建示例数据
        sample_patents = [
            PatentData(
                patent_id='US20210123456',
                title='Machine Learning System for Data Analysis',
                abstract='A novel machine learning system...',
                inventors=['Smith, John', 'Johnson, Mary'],
                assignee='Tech Innovations Inc.',
                filing_date='2021-01-15',
                classification='G06N 3/00',
                relevance_score=0.85
            ),
            PatentData(
                patent_id='CN112345678',
                title='深度学习图像识别方法',
                abstract='基于深度学习的图像识别技术...',
                inventors=['张三', '李四'],
                assignee='北京智能科技有限公司',
                filing_date='2021-03-10',
                classification='G06K 9/62',
                relevance_score=0.92
            )
        ]

        # 执行分析
        result = await analyze_patent_data(sample_patents)

        logger.info('专利分析结果:')
        print(json.dumps(result, indent=2, ensure_ascii=False))

    asyncio.run(main())
