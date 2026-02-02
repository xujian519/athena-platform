#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指标收集器
Metrics Collector

收集和聚合各种性能指标，提供指标查询和导出功能
"""

import time
from core.async_main import async_main
import json
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
from dataclasses import dataclass, asdict
import statistics

logger = logging.getLogger(__name__)

@dataclass
class MetricPoint:
    """指标数据点"""
    timestamp: datetime
    value: float
    tags: Dict[str, str]
    metric_type: str = 'gauge'  # gauge, counter, histogram

@dataclass
class AggregatedMetric:
    """聚合指标"""
    metric_name: str
    time_bucket: str
    count: int
    sum_value: float
    min_value: float
    max_value: float
    avg_value: float
    p50: float
    p95: float
    p99: float

class MetricsStorage:
    """指标存储器"""

    def __init__(self, db_path: str = "/tmp/metrics.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self) -> Any:
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建指标表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                value REAL NOT NULL,
                tags TEXT,
                metric_type TEXT DEFAULT 'gauge'
            )
        ''')

        # 创建聚合指标表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS aggregated_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                time_bucket TEXT NOT NULL,
                count INTEGER NOT NULL,
                sum_value REAL NOT NULL,
                min_value REAL NOT NULL,
                max_value REAL NOT NULL,
                avg_value REAL NOT NULL,
                p50 REAL NOT NULL,
                p95 REAL NOT NULL,
                p99 REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_name_time ON metrics (metric_name, timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_aggregated_name_bucket ON aggregated_metrics (metric_name, time_bucket)')

        conn.commit()
        conn.close()

    def store_metric(self, metric_name: str, value: float,
                    tags: Dict[str, str] = None, metric_type: str = 'gauge'):
        """存储指标"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        tags_json = json.dumps(tags) if tags else None

        cursor.execute('''
            INSERT INTO metrics (metric_name, timestamp, value, tags, metric_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (metric_name, datetime.now(), value, tags_json, metric_type))

        conn.commit()
        conn.close()

    def get_metrics(self, metric_name: str, start_time: datetime,
                   end_time: datetime, tags: Dict[str, str] = None) -> List[MetricPoint]:
        """查询指标"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = '''
            SELECT metric_name, timestamp, value, tags, metric_type
            FROM metrics
            WHERE metric_name = ? AND timestamp BETWEEN ? AND ?
        '''
        params = [metric_name, start_time, end_time]

        if tags:
            for key, value in tags.items():
                query += f' AND tags LIKE ?'
                params.append(f'%"{key}": "{value}"%')

        query += ' ORDER BY timestamp'

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        metrics = []
        for row in rows:
            metric_name, timestamp, value, tags_json, metric_type = row
            tags_dict = json.loads(tags_json) if tags_json else {}

            metrics.append(MetricPoint(
                timestamp=datetime.fromisoformat(timestamp),
                value=value,
                tags=tags_dict,
                metric_type=metric_type
            ))

        return metrics

    def aggregate_metrics(self, metric_name: str, start_time: datetime,
                         end_time: datetime, bucket_size: str = '5m') -> List[AggregatedMetric]:
        """聚合指标"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 将bucket_size转换为秒数
        bucket_seconds = self._parse_bucket_size(bucket_size)

        # SQL时间桶分组
        query = '''
            SELECT
                metric_name,
                datetime((strftime('%s', timestamp) / ?) * ?, 'unixepoch') as time_bucket,
                COUNT(*) as count,
                SUM(value) as sum_value,
                MIN(value) as min_value,
                MAX(value) as max_value,
                AVG(value) as avg_value
            FROM metrics
            WHERE metric_name = ? AND timestamp BETWEEN ? AND ?
            GROUP BY time_bucket
            ORDER BY time_bucket
        '''

        cursor.execute(query, (bucket_seconds, bucket_seconds, metric_name, start_time, end_time))
        rows = cursor.fetchall()
        conn.close()

        aggregated = []
        for row in rows:
            metric_name, time_bucket, count, sum_value, min_value, max_value, avg_value = row

            # 计算百分位数需要获取原始数据
            bucket_start = datetime.fromisoformat(time_bucket)
            bucket_end = bucket_start + timedelta(seconds=bucket_seconds)

            raw_metrics = self.get_metrics(metric_name, bucket_start, bucket_end)
            values = [m.value for m in raw_metrics]

            p50 = statistics.median(values) if values else 0
            p95 = statistics.quantiles(values, n=20)[18] if len(values) > 20 else max(values) if values else 0
            p99 = statistics.quantiles(values, n=100)[98] if len(values) > 100 else max(values) if values else 0

            aggregated.append(AggregatedMetric(
                metric_name=metric_name,
                time_bucket=time_bucket,
                count=count,
                sum_value=sum_value,
                min_value=min_value,
                max_value=max_value,
                avg_value=avg_value,
                p50=p50,
                p95=p95,
                p99=p99
            ))

        return aggregated

    def _parse_bucket_size(self, bucket_size: str) -> int:
        """解析时间桶大小"""
        if bucket_size.endswith('s'):
            return int(bucket_size[:-1])
        elif bucket_size.endswith('m'):
            return int(bucket_size[:-1]) * 60
        elif bucket_size.endswith('h'):
            return int(bucket_size[:-1]) * 3600
        elif bucket_size.endswith('d'):
            return int(bucket_size[:-1]) * 86400
        else:
            return 300  # 默认5分钟

    def cleanup_old_metrics(self, days: int = 30) -> Any:
        """清理旧指标"""
        cutoff_time = datetime.now() - timedelta(days=days)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 删除原始指标
        cursor.execute('DELETE FROM metrics WHERE timestamp < ?', (cutoff_time,))

        # 删除聚合指标（保留更长时间）
        agg_cutoff_time = datetime.now() - timedelta(days=days*7)
        cursor.execute('DELETE FROM aggregated_metrics WHERE created_at < ?', (agg_cutoff_time,))

        conn.commit()
        conn.close()

        logger.info(f"已清理 {days} 天前的指标数据")

class MetricsCollector:
    """指标收集器主类"""

    def __init__(self):
        self.storage = MetricsStorage()
        self.collectors = {}
        self.collection_interval = 30  # 30秒
        self.running = False
        self.collection_thread = None

        # 预定义指标
        self.predefined_metrics = {
            'system.cpu.usage': {'unit': 'percent', 'type': 'gauge'},
            'system.memory.usage': {'unit': 'percent', 'type': 'gauge'},
            'system.disk.usage': {'unit': 'percent', 'type': 'gauge'},
            'system.network.bytes_sent': {'unit': 'bytes', 'type': 'counter'},
            'system.network.bytes_recv': {'unit': 'bytes', 'type': 'counter'},
            'api.request.count': {'unit': 'count', 'type': 'counter'},
            'api.request.duration': {'unit': 'seconds', 'type': 'histogram'},
            'api.response.size': {'unit': 'bytes', 'type': 'histogram'},
            'file.upload.count': {'unit': 'count', 'type': 'counter'},
            'file.download.count': {'unit': 'count', 'type': 'counter'},
            'file.processing.duration': {'unit': 'seconds', 'type': 'histogram'},
            'cache.hit.rate': {'unit': 'percent', 'type': 'gauge'},
            'cache.miss.rate': {'unit': 'percent', 'type': 'gauge'},
            'error.rate': {'unit': 'percent', 'type': 'gauge'}
        }

    def register_collector(self, name: str, collector_func) -> None:
        """注册指标收集器"""
        self.collectors[name] = collector_func
        logger.info(f"已注册指标收集器: {name}")

    def start(self) -> None:
        """启动指标收集"""
        if self.running:
            return

        self.running = True
        self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.collection_thread.start()
        logger.info("指标收集器已启动")

    def stop(self) -> None:
        """停止指标收集"""
        self.running = False
        if self.collection_thread:
            self.collection_thread.join()
        logger.info("指标收集器已停止")

    def _collection_loop(self) -> Any:
        """收集循环"""
        while self.running:
            try:
                # 执行所有注册的收集器
                for name, collector_func in self.collectors.items():
                    try:
                        metrics = collector_func()
                        if metrics:
                            for metric_name, value in metrics.items():
                                self.storage.store_metric(
                                    metric_name=f"{name}.{metric_name}",
                                    value=value,
                                    metric_type=self.predefined_metrics.get(metric_name, {}).get('type', 'gauge')
                                )
                    except Exception as e:
                        logger.error(f"收集器 {name} 执行失败: {e}")

                time.sleep(self.collection_interval)

            except Exception as e:
                logger.error(f"指标收集循环异常: {e}")
                time.sleep(self.collection_interval)

    def collect_metric(self, metric_name: str, value: float,
                      tags: Dict[str, str] = None, metric_type: str = 'gauge'):
        """手动收集指标"""
        self.storage.store_metric(metric_name, value, tags, metric_type)

    def get_metric_summary(self, metric_name: str, hours: int = 1) -> Dict[str, Any]:
        """获取指标摘要"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        # 获取原始数据
        metrics = self.storage.get_metrics(metric_name, start_time, end_time)

        if not metrics:
            return {
                'metric_name': metric_name,
                'time_range': f"过去{hours}小时",
                'data_points': 0,
                'summary': "无数据"
            }

        values = [m.value for m in metrics]

        summary = {
            'metric_name': metric_name,
            'time_range': f"过去{hours}小时",
            'data_points': len(metrics),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'sum': sum(values),
            'latest': values[-1],
            'trend': self._calculate_trend(values)
        }

        # 计算百分位数
        if len(values) > 1:
            summary.update({
                'p50': statistics.median(values),
                'p90': statistics.quantiles(values, n=10)[8] if len(values) > 10 else max(values),
                'p95': statistics.quantiles(values, n=20)[18] if len(values) > 20 else max(values),
                'p99': statistics.quantiles(values, n=100)[98] if len(values) > 100 else max(values)
            })

        return summary

    def _calculate_trend(self, values: List[float]) -> str:
        """计算趋势"""
        if len(values) < 2:
            return "stable"

        # 简单的线性回归计算趋势
        n = len(values)
        x = list(range(n))
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)

        if slope > 0.01:
            return "increasing"
        elif slope < -0.01:
            return "decreasing"
        else:
            return "stable"

    def export_metrics(self, metric_names: List[str] = None,
                      start_time: datetime = None,
                      end_time: datetime = None,
                      format: str = 'json') -> str:
        """导出指标数据"""
        if start_time is None:
            start_time = datetime.now() - timedelta(hours=24)
        if end_time is None:
            end_time = datetime.now()

        if metric_names is None:
            # 导出所有预定义指标
            metric_names = list(self.predefined_metrics.keys())

        export_data = {
            'export_time': datetime.now().isoformat(),
            'time_range': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            },
            'metrics': {}
        }

        for metric_name in metric_names:
            metrics = self.storage.get_metrics(metric_name, start_time, end_time)
            export_data['metrics'][metric_name] = [
                {
                    'timestamp': m.timestamp.isoformat(),
                    'value': m.value,
                    'tags': m.tags,
                    'type': m.metric_type
                }
                for m in metrics
            ]

        if format == 'json':
            return json.dumps(export_data, ensure_ascii=False, indent=2)
        elif format == 'csv':
            # CSV格式导出
            csv_lines = ['metric_name,timestamp,value,tags']
            for metric_name, data in export_data['metrics'].items():
                for point in data:
                    tags_str = json.dumps(point['tags']) if point['tags'] else '{}'
                    csv_lines.append(f"{metric_name},{point['timestamp']},{point['value']},{tags_str}")
            return '\n'.join(csv_lines)
        else:
            raise ValueError(f"不支持的导出格式: {format}")

    def get_system_overview(self) -> Dict[str, Any]:
        """获取系统概览"""
        overview = {
            'timestamp': datetime.now().isoformat(),
            'collection_status': 'running' if self.running else 'stopped',
            'registered_collectors': list(self.collectors.keys()),
            'metrics_count': len(self.predefined_metrics),
            'recent_metrics': {}
        }

        # 获取最近1小时的指标概览
        key_metrics = [
            'system.cpu.usage',
            'system.memory.usage',
            'api.request.count',
            'file.upload.count',
            'cache.hit.rate'
        ]

        for metric in key_metrics:
            try:
                summary = self.get_metric_summary(metric, hours=1)
                overview['recent_metrics'][metric] = {
                    'current': summary.get('latest', 0),
                    'trend': summary.get('trend', 'stable'),
                    'data_points': summary.get('data_points', 0)
                }
            except Exception as e:
                overview['recent_metrics'][metric] = {
                    'error': str(e)
                }

        return overview

# 全局指标收集器实例
metrics_collector = MetricsCollector()

# 内置收集器
def system_metrics_collector() -> Dict[str, float]:
    """系统指标收集器"""
    import psutil

    return {
        'cpu.usage': psutil.cpu_percent(interval=1),
        'memory.usage': psutil.virtual_memory().percent,
        'disk.usage': psutil.disk_usage('/').percent,
        'network.bytes_sent': psutil.net_io_counters().bytes_sent,
        'network.bytes_recv': psutil.net_io_counters().bytes_recv,
        'process.count': len(psutil.pids())
    }

def cache_metrics_collector() -> Dict[str, float]:
    """缓存指标收集器"""
    try:
        from .cache_manager import cache_manager
        stats = cache_manager.get_stats()

        return {
            'hit.rate': stats.get('hit_rate', 0),
            'miss.rate': 100 - stats.get('hit_rate', 0),
            'size': stats.get('size', 0)
        }
    except Exception:
        return {}

# 注册内置收集器
metrics_collector.register_collector('system', system_metrics_collector)
metrics_collector.register_collector('cache', cache_metrics_collector)

# 使用示例
if __name__ == "__main__":
    collector = MetricsCollector()
    collector.start()

    # 手动收集一些指标
    collector.collect_metric('test.metric', 42.5, {'env': 'test'})

    # 获取指标摘要
    summary = collector.get_metric_summary('test.metric')
    print("指标摘要:", json.dumps(summary, ensure_ascii=False, indent=2, default=str))

    # 导出数据
    export_data = collector.export_metrics(['test.metric'], format='json')
    print("导出数据:", export_data[:200] + "...")

    collector.stop()