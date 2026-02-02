#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志分析系统
Log Analysis System

提供强大的日志分析、查询和可视化功能

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import json
import logging
import re
import sqlite3
import threading
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# 配置matplotlib后端
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

matplotlib.use('Agg')  # 使用非GUI后端

logger = logging.getLogger(__name__)

class AnalysisType(Enum):
    """分析类型"""
    FREQUENCY = 'frequency'          # 频率分析
    TREND = 'trend'                 # 趋势分析
    PATTERN = 'pattern'             # 模式分析
    ANOMALY = 'anomaly'             # 异常分析
    CORRELATION = 'correlation'     # 相关性分析
    PERFORMANCE = 'performance'      # 性能分析
    ERROR = 'error'                 # 错误分析
    BUSINESS = 'business'           # 业务分析

@dataclass
class LogAnalysis:
    """日志分析结果"""
    analysis_id: str
    analysis_type: AnalysisType
    title: str
    description: str
    results: Dict[str, Any]
    visualizations: List[str]  # 可视化图表路径
    timestamp: datetime = field(default_factory=datetime.now)
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

class LogQuery:
    """日志查询"""
    def __init__(self):
        self.time_range: Optional[Tuple[datetime, datetime]] = None
        self.log_levels: List[str] = []
        self.categories: List[str] = []
        self.components: List[str] = []
        self.keywords: List[str] = []
        self.regex_pattern: str | None = None
        self.limit: int = 1000
        self.sort_by: str = 'timestamp'
        self.sort_order: str = 'desc'

class LogAnalyzer:
    """日志分析器"""

    def __init__(self, db_path: str = 'log_analysis.db'):
        self.db_path = db_path
        self.conn = None
        self.analysis_cache = {}
        self.analysis_lock = threading.Lock()

        # 初始化数据库
        self._init_database()

        # 预定义的分析模板
        self.analysis_templates = self._create_analysis_templates()

    def _init_database(self):
        """初始化分析数据库"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        # 创建分析结果表
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS log_analysis (
                id TEXT PRIMARY KEY,
                analysis_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                results TEXT NOT NULL,
                visualizations TEXT,
                timestamp TEXT NOT NULL,
                insights TEXT,
                recommendations TEXT
            )
        """)

        # 创建索引
        self.conn.execute('CREATE INDEX IF NOT EXISTS idx_analysis_type ON log_analysis(analysis_type)')
        self.conn.execute('CREATE INDEX IF NOT EXISTS idx_analysis_timestamp ON log_analysis(timestamp)')

        logger.info('✅ 日志分析数据库初始化完成')

    def _create_analysis_templates(self) -> Dict[str, Dict]:
        """创建分析模板"""
        return {
            'error_frequency': {
                'type': AnalysisType.FREQUENCY,
                'title': '错误频率分析',
                'description': '分析各种错误类型的出现频率',
                'query': {'log_levels': ['ERROR', 'CRITICAL']},
                'analysis_function': 'analyze_error_frequency'
            },
            'performance_trend': {
                'type': AnalysisType.TREND,
                'title': '性能趋势分析',
                'description': '分析系统性能指标的变化趋势',
                'query': {'categories': ['PERFORMANCE']},
                'analysis_function': 'analyze_performance_trend'
            },
            'business_metrics': {
                'type': AnalysisType.BUSINESS,
                'title': '业务指标分析',
                'description': '分析业务相关的事件和指标',
                'query': {'categories': ['BUSINESS']},
                'analysis_function': 'analyze_business_metrics'
            },
            'component_health': {
                'type': AnalysisType.PERFORMANCE,
                'title': '组件健康度分析',
                'description': '评估各个系统组件的健康状态',
                'query': {},
                'analysis_function': 'analyze_component_health'
            },
            'error_patterns': {
                'type': AnalysisType.PATTERN,
                'title': '错误模式分析',
                'description': '识别错误发生的模式和规律',
                'query': {'log_levels': ['ERROR', 'CRITICAL']},
                'analysis_function': 'analyze_error_patterns'
            }
        }

    async def analyze_logs(self,
                          logs: List[Dict[str, Any]],
                          analysis_type: AnalysisType,
                          params: Optional[Dict[str, Any]] = None) -> LogAnalysis:
        """分析日志"""
        analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(analysis_cache)}"
        params = params or {}

        # 检查缓存
        cache_key = f"{analysis_type.value}_{hash(json.dumps(params, sort_keys=True))}"
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]

        logger.info(f"🔍 开始日志分析: {analysis_type.value}")

        try:
            # 转换为DataFrame
            df = pd.DataFrame(logs)
            if df.empty:
                return self._create_empty_analysis(analysis_id, analysis_type)

            # 执行具体分析
            if analysis_type == AnalysisType.FREQUENCY:
                results = await self._analyze_frequency(df, params)
            elif analysis_type == AnalysisType.TREND:
                results = await self._analyze_trend(df, params)
            elif analysis_type == AnalysisType.PATTERN:
                results = await self._analyze_pattern(df, params)
            elif analysis_type == AnalysisType.ANOMALY:
                results = await self._analyze_anomaly(df, params)
            elif analysis_type == AnalysisType.CORRELATION:
                results = await self._analyze_correlation(df, params)
            elif analysis_type == AnalysisType.PERFORMANCE:
                results = await self._analyze_performance(df, params)
            elif analysis_type == AnalysisType.ERROR:
                results = await self._analyze_error(df, params)
            elif analysis_type == AnalysisType.BUSINESS:
                results = await self._analyze_business(df, params)
            else:
                results = {'message': '不支持的分析类型'}

            # 生成可视化
            visualizations = await self._create_visualizations(df, analysis_type, results)

            # 生成洞察和建议
            insights = self._generate_insights(analysis_type, results)
            recommendations = self._generate_recommendations(analysis_type, results)

            # 创建分析对象
            analysis = LogAnalysis(
                analysis_id=analysis_id,
                analysis_type=analysis_type,
                title=f"{analysis_type.value}分析",
                description=f"基于{len(logs)}条日志的{analysis_type.value}分析",
                results=results,
                visualizations=visualizations,
                insights=insights,
                recommendations=recommendations
            )

            # 保存分析结果
            self._save_analysis(analysis)

            # 缓存结果
            self.analysis_cache[cache_key] = analysis

            logger.info(f"✅ 日志分析完成: {analysis_id}")
            return analysis

        except Exception as e:
            logger.error(f"❌ 日志分析失败: {e}")
            raise

    def _create_empty_analysis(self, analysis_id: str, analysis_type: AnalysisType) -> LogAnalysis:
        """创建空的分析结果"""
        return LogAnalysis(
            analysis_id=analysis_id,
            analysis_type=analysis_type,
            title=f"{analysis_type.value}分析",
            description='无可用数据进行',
            results={'message': '没有日志数据可供分析'},
            visualizations=[],
            insights=['需要提供日志数据才能进行分析'],
            recommendations=['请检查日志收集是否正常']
        )

    async def _analyze_frequency(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """频率分析"""
        results = {}

        # 按级别统计
        if 'level' in df.columns:
            level_counts = df['level'].value_counts().to_dict()
            results['level_distribution'] = level_counts

        # 按类别统计
        if 'category' in df.columns:
            category_counts = df['category'].value_counts().to_dict()
            results['category_distribution'] = category_counts

        # 按组件统计
        if 'component' in df.columns:
            component_counts = df['component'].value_counts().to_dict()
            results['component_distribution'] = component_counts

        # 按小时统计
        if 'timestamp' in df.columns:
            df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
            hourly_counts = df['hour'].value_counts().sort_index().to_dict()
            results['hourly_distribution'] = hourly_counts

        # 关键词频率
        if 'message' in df.columns:
            all_messages = ' '.join(df['message'].astype(str))
            words = re.findall(r'\w+', all_messages.lower())
            word_counts = Counter(words).most_common(20)
            results['top_keywords'] = word_counts

        return results

    async def _analyze_trend(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """趋势分析"""
        results = {}

        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date

            # 每日趋势
            daily_counts = df.groupby('date').size().to_dict()
            results['daily_trend'] = {str(k): v for k, v in daily_counts.items()}

            # 计算趋势方向
            dates = list(daily_counts.keys())
            counts = list(daily_counts.values())
            if len(counts) > 1:
                slope = np.polyfit(range(len(counts)), counts, 1)[0]
                results['trend_direction'] = 'increasing' if slope > 0 else 'decreasing'
                results['trend_slope'] = slope

        # 错误趋势
        if 'level' in df.columns:
            error_df = df[df['level'].isin(['ERROR', 'CRITICAL'])]
            if not error_df.empty and 'timestamp' in error_df.columns:
                error_df['timestamp'] = pd.to_datetime(error_df['timestamp'])
                error_df['date'] = error_df['timestamp'].dt.date
                daily_errors = error_df.groupby('date').size().to_dict()
                results['error_trend'] = {str(k): v for k, v in daily_errors.items()}

        return results

    async def _analyze_pattern(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """模式分析"""
        results = {}

        # 时间模式
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['hour'] = df['timestamp'].dt.hour
            df['weekday'] = df['timestamp'].dt.weekday

            hourly_pattern = df['hour'].value_counts().to_dict()
            weekday_pattern = df['weekday'].value_counts().to_dict()
            results['time_patterns'] = {
                'hourly': hourly_pattern,
                'weekday': weekday_pattern
            }

        # 错误模式
        if 'level' in df.columns and 'message' in df.columns:
            error_df = df[df['level'].isin(['ERROR', 'CRITICAL'])]
            if not error_df.empty:
                # 提取常见错误模式
                error_messages = error_df['message'].astype(str)
                error_patterns = []

                # 查找常见的错误模式
                common_patterns = [
                    r'Connection.*failed',
                    r'Timeout.*error',
                    r'File.*not.*found',
                    r'Permission.*denied',
                    r'Invalid.*parameter',
                    r'Memory.*error',
                    r'SQL.*error'
                ]

                for pattern in common_patterns:
                    matches = error_messages.str.contains(pattern, regex=True, na=False).sum()
                    if matches > 0:
                        error_patterns.append({
                            'pattern': pattern,
                            'count': int(matches)
                        })

                results['error_patterns'] = error_patterns

        # 序列模式
        if len(df) > 10:
            # 简单的序列模式检测
            consecutive_patterns = []
            for i in range(len(df) - 2):
                pattern = tuple(df.iloc[i:i+3]['level'].tolist())
                consecutive_patterns.append(pattern)

            pattern_counts = Counter(consecutive_patterns).most_common(5)
            results['sequence_patterns'] = [{'pattern': p[0], 'count': p[1]} for p in pattern_counts]

        return results

    async def _analyze_anomaly(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """异常检测"""
        results = {}

        # 基于统计的异常检测
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        anomalies = {}

        for col in numeric_columns:
            if df[col].std() > 0:
                # 使用Z-score检测异常
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                anomaly_indices = z_scores[z_scores > 3].index.tolist()

                if anomaly_indices:
                    anomalies[col] = {
                        'count': len(anomaly_indices),
                        'indices': anomaly_indices[:10],  # 只显示前10个
                        'percentage': len(anomaly_indices) / len(df) * 100
                    }

        results['statistical_anomalies'] = anomalies

        # 错误激增检测
        if 'timestamp' in df.columns and 'level' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['hour'] = df['timestamp'].dt.floor('H')

            error_df = df[df['level'].isin(['ERROR', 'CRITICAL'])]
            if not error_df.empty:
                hourly_errors = error_df.groupby('hour').size()

                # 检测错误激增
                mean_errors = hourly_errors.mean()
                std_errors = hourly_errors.std()
                threshold = mean_errors + 2 * std_errors

                error_spikes = hourly_errors[hourly_errors > threshold]
                results['error_spikes'] = {
                    'spike_hours': {str(k): v for k, v in error_spikes.items()},
                    'threshold': threshold,
                    'mean_errors': mean_errors
                }

        return results

    async def _analyze_correlation(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """相关性分析"""
        results = {}

        # 数值列相关性
        numeric_df = df.select_dtypes(include=[np.number])
        if len(numeric_df.columns) > 1:
            correlation_matrix = numeric_df.corr()
            results['numeric_correlations'] = correlation_matrix.to_dict()

            # 找出强相关性
            strong_correlations = []
            for i in range(len(correlation_matrix.columns)):
                for j in range(i+1, len(correlation_matrix.columns)):
                    col1 = correlation_matrix.columns[i]
                    col2 = correlation_matrix.columns[j]
                    corr_value = correlation_matrix.iloc[i, j]
                    if abs(corr_value) > 0.7:  # 强相关阈值
                        strong_correlations.append({
                            'field1': col1,
                            'field2': col2,
                            'correlation': corr_value
                        })

            results['strong_correlations'] = strong_correlations

        # 类别变量关联性
        categorical_columns = df.select_dtypes(include=['object', 'category']).columns
        if len(categorical_columns) > 1:
            # 使用卡方检验检测关联性
            from scipy.stats import chi2_contingency

            categorical_correlations = []
            for i in range(len(categorical_columns)):
                for j in range(i+1, len(categorical_columns)):
                    col1 = categorical_columns[i]
                    col2 = categorical_columns[j]

                    try:
                        contingency_table = pd.crosstab(df[col1], df[col2])
                        chi2, p_value, _, _ = chi2_contingency(contingency_table)

                        if p_value < 0.05:  # 显著关联
                            categorical_correlations.append({
                                'field1': col1,
                                'field2': col2,
                                'chi2_statistic': chi2,
                                'p_value': p_value
                            })
                    except:
                        continue

            results['categorical_correlations'] = categorical_correlations

        return results

    async def _analyze_performance(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """性能分析"""
        results = {}

        # 从日志中提取性能指标
        if 'message' in df.columns:
            # 查找响应时间
            response_times = []
            processing_times = []

            for message in df['message'].astype(str):
                # 使用正则表达式提取时间信息
                time_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:ms|秒|second)', message.lower())
                if time_match:
                    time_value = float(time_match.group(1))
                    if 'ms' in message.lower():
                        time_value /= 1000  # 转换为秒
                    response_times.append(time_value)

            if response_times:
                results['response_time_stats'] = {
                    'mean': np.mean(response_times),
                    'median': np.median(response_times),
                    'std': np.std(response_times),
                    'min': np.min(response_times),
                    'max': np.max(response_times),
                    'p95': np.percentile(response_times, 95),
                    'p99': np.percentile(response_times, 99)
                }

                # 性能趋势
                if len(response_times) > 10:
                    # 简单的性能趋势分析
                    recent_avg = np.mean(response_times[-10:])
                    overall_avg = np.mean(response_times)
                    results['performance_trend'] = {
                        'direction': 'improving' if recent_avg < overall_avg else 'degrading',
                        'recent_average': recent_avg,
                        'overall_average': overall_avg
                    }

        # 错误率分析
        if 'level' in df.columns:
            total_logs = len(df)
            error_logs = df[df['level'].isin(['ERROR', 'CRITICAL'])]
            error_rate = len(error_logs) / total_logs if total_logs > 0 else 0

            results['error_rate'] = {
                'current': error_rate,
                'total_errors': len(error_logs),
                'total_logs': total_logs
            }

        return results

    async def _analyze_error(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """错误分析"""
        results = {}

        if 'level' not in df.columns:
            return results

        error_df = df[df['level'].isin(['ERROR', 'CRITICAL'])]
        if error_df.empty:
            results['message'] = '没有错误日志可分析'
            return results

        # 错误类型统计
        if 'message' in df.columns:
            error_messages = error_df['message'].astype(str)

            # 提取错误类型
            error_types = defaultdict(int)
            for msg in error_messages:
                # 简单的错误类型提取
                if 'connection' in msg.lower():
                    error_types['connection_error'] += 1
                elif 'timeout' in msg.lower():
                    error_types['timeout_error'] += 1
                elif 'permission' in msg.lower():
                    error_types['permission_error'] += 1
                elif 'not found' in msg.lower():
                    error_types['not_found_error'] += 1
                elif 'invalid' in msg.lower():
                    error_types['invalid_error'] += 1
                else:
                    error_types['other_error'] += 1

            results['error_types'] = dict(error_types)

        # 错误组件分析
        if 'component' in df.columns:
            component_errors = error_df['component'].value_counts().to_dict()
            results['error_by_component'] = component_errors

        # 错误时间分析
        if 'timestamp' in df.columns:
            error_df['timestamp'] = pd.to_datetime(error_df['timestamp'])
            error_df['hour'] = error_df['timestamp'].dt.hour

            hourly_errors = error_df['hour'].value_counts().to_dict()
            results['error_by_hour'] = hourly_errors

            # 错误间隔分析
            sorted_timestamps = error_df['timestamp'].sort_values()
            if len(sorted_timestamps) > 1:
                intervals = sorted_timestamps.diff().dt.total_seconds().dropna()
                results['error_intervals'] = {
                    'mean': intervals.mean(),
                    'median': intervals.median(),
                    'std': intervals.std()
                }

        return results

    async def _analyze_business(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """业务分析"""
        results = {}

        if 'category' not in df.columns:
            # 尝试从消息中识别业务事件
            if 'message' in df.columns:
                business_events = 0
                user_actions = 0

                for message in df['message'].astype(str):
                    if any(keyword in message.lower() for keyword in ['登录', '注册', '购买', '下单']):
                        business_events += 1
                    if any(keyword in message.lower() for keyword in ['用户', 'user', '客户']):
                        user_actions += 1

                results['business_events'] = {
                    'total_events': business_events,
                    'user_actions': user_actions
                }

        # 业务指标统计
        if 'details' in df.columns:
            try:
                details_list = df['details'].apply(lambda x: json.loads(x) if isinstance(x, str) else x)

                # 提取业务指标
                business_metrics = defaultdict(list)
                for details in details_list:
                    if isinstance(details, dict):
                        for key, value in details.items():
                            if isinstance(value, (int, float)):
                                business_metrics[key].append(value)

                # 计算统计信息
                for metric, values in business_metrics.items():
                    if values:
                        results[f'business_metric_{metric}'] = {
                            'count': len(values),
                            'mean': np.mean(values),
                            'sum': np.sum(values),
                            'min': np.min(values),
                            'max': np.max(values)
                        }

            except Exception as e:
                logger.warning(f"业务指标提取失败: {e}")

        return results

    async def _create_visualizations(self,
                                     df: pd.DataFrame,
                                     analysis_type: AnalysisType,
                                     results: Dict[str, Any]) -> List[str]:
        """创建可视化图表"""
        visualizations = []
        viz_dir = Path('visualizations')
        viz_dir.mkdir(exist_ok=True)

        try:
            # 根据分析类型创建不同的图表
            if analysis_type == AnalysisType.FREQUENCY:
                # 饼图 - 日志级别分布
                if 'level_distribution' in results:
                    plt.figure(figsize=(8, 6))
                    levels = list(results['level_distribution'].keys())
                    counts = list(results['level_distribution'].values())
                    plt.pie(counts, labels=levels, autopct='%1.1f%%')
                    plt.title('日志级别分布')
                    plt.savefig(viz_dir / f"log_levels_pie_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                    plt.close()
                    visualizations.append(str(viz_dir / f"log_levels_pie_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"))

                # 柱状图 - 组件分布
                if 'component_distribution' in results:
                    plt.figure(figsize=(10, 6))
                    components = list(results['component_distribution'].keys())
                    counts = list(results['component_distribution'].values())
                    plt.bar(components, counts)
                    plt.title('日志组件分布')
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    plt.savefig(viz_dir / f"components_bar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                    plt.close()
                    visualizations.append(str(viz_dir / f"components_bar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"))

            elif analysis_type == AnalysisType.TREND:
                # 折线图 - 趋势分析
                if 'daily_trend' in results:
                    plt.figure(figsize=(12, 6))
                    dates = list(results['daily_trend'].keys())
                    counts = list(results['daily_trend'].values())
                    plt.plot(dates, counts, marker='o')
                    plt.title('日志数量趋势')
                    plt.xlabel('日期')
                    plt.ylabel('日志数量')
                    plt.xticks(rotation=45)
                    plt.grid(True)
                    plt.tight_layout()
                    plt.savefig(viz_dir / f"daily_trend_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                    plt.close()
                    visualizations.append(str(viz_dir / f"daily_trend_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"))

            elif analysis_type == AnalysisType.PERFORMANCE:
                # 箱线图 - 性能指标
                if 'response_time_stats' in results:
                    plt.figure(figsize=(8, 6))
                    stats = results['response_time_stats']
                    metrics = ['mean', 'median', 'p95', 'p99']
                    values = [stats[m] for m in metrics]
                    plt.bar(metrics, values)
                    plt.title('响应时间统计')
                    plt.ylabel('时间 (秒)')
                    plt.tight_layout()
                    plt.savefig(viz_dir / f"performance_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                    plt.close()
                    visualizations.append(str(viz_dir / f"performance_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"))

        except Exception as e:
            logger.error(f"创建可视化失败: {e}")

        return visualizations

    def _generate_insights(self, analysis_type: AnalysisType, results: Dict[str, Any]) -> List[str]:
        """生成洞察"""
        insights = []

        if analysis_type == AnalysisType.FREQUENCY:
            if 'level_distribution' in results:
                total_errors = results['level_distribution'].get('ERROR', 0) + \
                             results['level_distribution'].get('CRITICAL', 0)
                total_logs = sum(results['level_distribution'].values())
                if total_logs > 0:
                    error_rate = total_errors / total_logs
                    if error_rate > 0.1:
                        insights.append(f"错误率较高 ({error_rate:.1%})，需要重点关注")
                    elif error_rate < 0.01:
                        insights.append(f"系统运行稳定，错误率较低 ({error_rate:.1%})")

        elif analysis_type == AnalysisType.TREND:
            if 'trend_direction' in results:
                if results['trend_direction'] == 'increasing':
                    insights.append('日志数量呈上升趋势，可能需要扩容')
                else:
                    insights.append('日志数量呈下降趋势，系统运行良好')

        elif analysis_type == AnalysisType.ERROR:
            if 'error_types' in results:
                most_common_error = max(results['error_types'].items(), key=lambda x: x[1])
                insights.append(f"最常见的错误类型: {most_common_error[0]} (出现{most_common_error[1]}次)")

        elif analysis_type == AnalysisType.PERFORMANCE:
            if 'response_time_stats' in results:
                p95 = results['response_time_stats']['p95']
                if p95 > 1.0:  # 超过1秒
                    insights.append(f"95%响应时间较高 ({p95:.2f}秒)，建议优化性能")

        return insights

    def _generate_recommendations(self, analysis_type: AnalysisType, results: Dict[str, Any]) -> List[str]:
        """生成建议"""
        recommendations = []

        if analysis_type == AnalysisType.ERROR:
            if 'error_by_component' in results:
                top_error_component = max(results['error_by_component'].items(), key=lambda x: x[1])
                recommendations.append(f"重点关注组件 {top_error_component[0]}，错误次数最多")

        if analysis_type == AnalysisType.FREQUENCY:
            if 'level_distribution' in results:
                critical_count = results['level_distribution'].get('CRITICAL', 0)
                if critical_count > 0:
                    recommendations.append(f"发现 {critical_count} 个严重错误，需要立即处理")

        if analysis_type == AnalysisType.PERFORMANCE:
            if 'error_rate' in results:
                if results['error_rate']['current'] > 0.05:
                    recommendations.append('错误率超过5%，建议进行系统检查')

        return recommendations

    def _save_analysis(self, analysis: LogAnalysis):
        """保存分析结果"""
        with self.analysis_lock:
            self.conn.execute("""
                INSERT OR REPLACE INTO log_analysis
                (id, analysis_type, title, description, results,
                 visualizations, timestamp, insights, recommendations)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis.analysis_id,
                analysis.analysis_type.value,
                analysis.title,
                analysis.description,
                json.dumps(analysis.results),
                json.dumps(analysis.visualizations),
                analysis.timestamp.isoformat(),
                json.dumps(analysis.insights),
                json.dumps(analysis.recommendations)
            ))
            self.conn.commit()

    def query_analysis(self,
                       analysis_type: AnalysisType | None = None,
                       start_date: datetime | None = None,
                       end_date: datetime | None = None) -> List[Dict[str, Any]]:
        """查询分析结果"""
        query = 'SELECT * FROM log_analysis WHERE 1=1'
        params = []

        if analysis_type:
            query += ' AND analysis_type = ?'
            params.append(analysis_type.value)

        if start_date:
            query += ' AND timestamp >= ?'
            params.append(start_date.isoformat())

        if end_date:
            query += ' AND timestamp <= ?'
            params.append(end_date.isoformat())

        query += ' ORDER BY timestamp DESC'

        cursor = self.conn.execute(query, params)
        results = []

        for row in cursor.fetchall():
            results.append({
                'id': row['id'],
                'analysis_type': row['analysis_type'],
                'title': row['title'],
                'description': row['description'],
                'results': json.loads(row['results']),
                'visualizations': json.loads(row['visualizations']),
                'timestamp': row['timestamp'],
                'insights': json.loads(row['insights']),
                'recommendations': json.loads(row['recommendations'])
            })

        return results

    def get_analysis_summary(self) -> Dict[str, Any]:
        """获取分析摘要"""
        cursor = self.conn.execute("""
            SELECT
                analysis_type,
                COUNT(*) as count,
                MAX(timestamp) as latest
            FROM log_analysis
            GROUP BY analysis_type
        """)

        summary = {}
        for row in cursor.fetchall():
            summary[row['analysis_type']] = {
                'count': row['count'],
                'latest': row['latest']
            }

        return summary

# 测试用例
async def main():
    """主函数"""
    logger.info('🧠 日志分析系统测试')
    logger.info(str('='*50))

    # 创建模拟日志数据
    import random

    levels = ['INFO', 'WARNING', 'ERROR', 'CRITICAL']
    categories = ['SYSTEM', 'PERFORMANCE', 'BUSINESS', 'SECURITY', 'ERROR']
    components = ['auth', 'database', 'api', 'cache', 'queue']

    logs = []
    for i in range(1000):
        log = {
            'id': f"log_{i}",
            'timestamp': datetime.now() - timedelta(hours=random.randint(0, 168)),
            'level': random.choice(levels),
            'category': random.choice(categories),
            'component': random.choice(components),
            'message': f"Test log message {i} with content",
            'details': {
                'response_time': random.uniform(0.1, 2.0),
                'user_id': random.randint(1000, 9999)
            }
        }
        logs.append(log)

    # 创建分析器
    analyzer = LogAnalyzer(':memory:')

    # 执行各种分析
    logger.info("\n📊 执行日志分析...")

    # 频率分析
    logger.info("\n1. 频率分析:")
    freq_analysis = await analyzer.analyze_logs(logs, AnalysisType.FREQUENCY)
    logger.info(f"分析ID: {freq_analysis.analysis_id}")
    logger.info(f"洞察: {len(freq_analysis.insights)} 个")
    logger.info(f"建议: {len(freq_analysis.recommendations)} 个")

    # 趋势分析
    logger.info("\n2. 趋势分析:")
    trend_analysis = await analyzer.analyze_logs(logs, AnalysisType.TREND)
    logger.info(f"分析ID: {trend_analysis.analysis_id}")
    logger.info(f"洞察: {len(trend_analysis.insights)} 个")

    # 错误分析
    logger.info("\n3. 错误分析:")
    error_analysis = await analyzer.analyze_logs(logs, AnalysisType.ERROR)
    logger.info(f"分析ID: {error_analysis.analysis_id}")
    logger.info(f"洞察: {len(error_analysis.insights)} 个")

    # 性能分析
    logger.info("\n4. 性能分析:")
    perf_analysis = await analyzer.analyze_logs(logs, AnalysisType.PERFORMANCE)
    logger.info(f"分析ID: {perf_analysis.analysis_id}")
    logger.info(f"洞察: {len(perf_analysis.insights)} 个")

    # 获取分析摘要
    logger.info("\n📋 分析摘要:")
    summary = analyzer.get_analysis_summary()
    for analysis_type, info in summary.items():
        logger.info(f"  {analysis_type}: {info['count']} 次分析，最新: {info['latest']}")

    # 查询历史分析
    logger.info("\n🔍 查询历史分析:")
    history = analyzer.query_analysis(analysis_type=AnalysisType.ERROR)
    logger.info(f"找到 {len(history)} 个错误分析记录")

    logger.info("\n✅ 日志分析系统测试完成！")

if __name__ == '__main__':
    asyncio.run(main())