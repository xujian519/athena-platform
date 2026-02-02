#!/usr/bin/env python3
"""
📊 向量数据库性能监控守护进程
小诺的智能监控系统

功能:
1. 定期监控向量数据库性能
2. 异常检测和告警
3. 性能数据记录和分析
4. 自动化报告生成

作者: 小诺 (AI助手)
创建时间: 2025-12-11
"""

import asyncio
import json
import logging
import signal
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import httpx
import psutil
from loguru import logger

logger = logging.getLogger(__name__)

# 配置日志
logger.add('vector_monitor.log', rotation='50 MB', level='INFO')

class VectorMonitorDaemon:
    """向量数据库监控守护进程"""

    def __init__(self, qdrant_url: str = 'http://localhost:6333',
                 check_interval: int = 60):
        self.qdrant_url = qdrant_url
        self.check_interval = check_interval
        self.client = httpx.AsyncClient(timeout=30.0)
        self.running = False
        self.performance_history = []
        self.alerts = []

        # 性能阈值配置
        self.thresholds = {
            'search_time_ms': 50,      # 搜索时间阈值 (ms)
            'memory_usage_percent': 80,  # 内存使用阈值 (%)
            'cpu_usage_percent': 85,     # CPU使用阈值 (%)
            'error_rate': 5,            # 错误率阈值 (%)
            'indexing_ratio': 0.9       # 索引覆盖率阈值
        }

    async def get_system_metrics(self) -> Dict:
        """获取系统性能指标"""
        try:
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'memory_available_gb': psutil.virtual_memory().available / (1024**3),
                'disk_usage_percent': psutil.disk_usage('/').percent,
                'load_average': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
            }
        except Exception as e:
            logger.error(f"获取系统指标失败: {e}")
            return {}

    async def get_collections_info(self) -> List[Dict]:
        """获取所有集合信息"""
        try:
            response = await self.client.get(f"{self.qdrant_url}/collections")
            response.raise_for_status()
            data = response.json()
            collections = data['result']['collections']

            detailed_info = []
            for col in collections:
                name = col['name']
                try:
                    response = await self.client.get(f"{self.qdrant_url}/collections/{name}")
                    response.raise_for_status()
                    info = response.json()['result']
                    detailed_info.append(info)
                except Exception as e:
                    logger.warning(f"获取集合 {name} 详细信息失败: {e}")
                    continue

            return detailed_info

        except Exception as e:
            logger.error(f"获取集合信息失败: {e}")
            return []

    async def test_collection_search_performance(self, collection_name: str,
                                                vector_size: int) -> Dict:
        """测试集合搜索性能"""
        try:
            # 创建测试向量
            test_vector = [0.1] * vector_size

            search_data = {
                'vector': test_vector,
                'limit': 10,
                'with_payload': False
            }

            # 执行多次测试
            times = []
            errors = 0
            test_count = 5

            for i in range(test_count):
                try:
                    start_time = time.time()
                    response = await self.client.post(
                        f"{self.qdrant_url}/collections/{collection_name}/points/search",
                        json=search_data,
                        timeout=10.0
                    )
                    search_time = (time.time() - start_time) * 1000
                    times.append(search_time)

                    if response.status_code != 200:
                        errors += 1

                except Exception:
                    errors += 1
                    continue

            if times:
                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)
                p95_time = sorted(times)[int(len(times) * 0.95)] if len(times) > 1 else times[-1]
            else:
                avg_time = min_time = max_time = p95_time = 0

            return {
                'collection': collection_name,
                'avg_search_time_ms': round(avg_time, 2),
                'min_search_time_ms': round(min_time, 2),
                'max_search_time_ms': round(max_time, 2),
                'p95_search_time_ms': round(p95_time, 2),
                'test_count': test_count,
                'error_count': errors,
                'error_rate': round((errors / test_count) * 100, 1),
                'test_success': len(times) > 0
            }

        except Exception as e:
            logger.error(f"测试集合 {collection_name} 性能失败: {e}")
            return {
                'collection': collection_name,
                'error': str(e),
                'test_success': False
            }

    async def perform_health_check(self) -> Dict:
        """执行健康检查"""
        try:
            start_time = time.time()
            response = await self.client.get(f"{self.qdrant_url}/health")
            response.raise_for_status()
            response_time = (time.time() - start_time) * 1000

            return {
                'healthy': True,
                'response_time_ms': round(response_time, 2),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def check_alerts(self, metrics: Dict) -> List[Dict]:
        """检查告警条件"""
        alerts = []

        # 检查搜索时间
        for perf in metrics.get('collection_performance', []):
            if perf.get('avg_search_time_ms', 0) > self.thresholds['search_time_ms']:
                alerts.append({
                    'type': 'performance',
                    'severity': 'warning',
                    'message': f"集合 {perf['collection']} 搜索时间过慢: {perf['avg_search_time_ms']}ms",
                    'timestamp': datetime.now().isoformat()
                })

            if perf.get('error_rate', 0) > self.thresholds['error_rate']:
                alerts.append({
                    'type': 'error_rate',
                    'severity': 'critical',
                    'message': f"集合 {perf['collection']} 错误率过高: {perf['error_rate']}%",
                    'timestamp': datetime.now().isoformat()
                })

        # 检查系统资源
        system_metrics = metrics.get('system_metrics', {})
        if system_metrics.get('memory_percent', 0) > self.thresholds['memory_usage_percent']:
            alerts.append({
                'type': 'memory',
                'severity': 'warning',
                'message': f"内存使用率过高: {system_metrics['memory_percent']}%",
                'timestamp': datetime.now().isoformat()
            })

        if system_metrics.get('cpu_percent', 0) > self.thresholds['cpu_usage_percent']:
            alerts.append({
                'type': 'cpu',
                'severity': 'warning',
                'message': f"CPU使用率过高: {system_metrics['cpu_percent']}%",
                'timestamp': datetime.now().isoformat()
            })

        # 检查索引覆盖率
        for info in metrics.get('collections_info', []):
            name = info.get('name', '')
            total = info.get('points_count', 0)
            indexed = info.get('indexed_vectors_count', 0)

            if total > 0:
                coverage = indexed / total
                if coverage < self.thresholds['indexing_ratio']:
                    alerts.append({
                        'type': 'indexing',
                        'severity': 'info',
                        'message': f"集合 {name} 索引覆盖率较低: {coverage:.1%}",
                        'timestamp': datetime.now().isoformat()
                    })

        return alerts

    async def collect_metrics(self) -> Dict:
        """收集所有性能指标"""
        logger.info('开始收集性能指标...')

        metrics = {
            'timestamp': datetime.now().isoformat(),
            'check_interval_seconds': self.check_interval
        }

        # 1. 系统指标
        system_metrics = await self.get_system_metrics()
        metrics['system_metrics'] = system_metrics

        # 2. 集合信息
        collections_info = await self.get_collections_info()
        metrics['collections_info'] = collections_info

        # 3. 集合性能测试
        collection_performance = []
        for info in collections_info:
            name = info.get('name', '')
            if name and info.get('config', {}).get('params', {}).get('vectors'):
                vector_size = info['config']['params']['vectors']['size']
                perf = await self.test_collection_search_performance(name, vector_size)
                collection_performance.append(perf)

        metrics['collection_performance'] = collection_performance

        # 4. 健康检查
        health = await self.perform_health_check()
        metrics['health_check'] = health

        # 5. 告警检查
        alerts = await self.check_alerts(metrics)
        metrics['alerts'] = alerts
        self.alerts.extend(alerts)

        # 6. 统计摘要
        total_vectors = sum(info.get('points_count', 0) for info in collections_info)
        total_indexed = sum(info.get('indexed_vectors_count', 0) for info in collections_info)

        metrics['summary'] = {
            'total_collections': len(collections_info),
            'total_vectors': total_vectors,
            'total_indexed_vectors': total_indexed,
            'indexing_ratio': total_indexed / total_vectors if total_vectors > 0 else 1,
            'avg_search_time_ms': sum(p.get('avg_search_time_ms', 0) for p in collection_performance) / len(collection_performance) if collection_performance else 0,
            'active_alerts': len(alerts),
            'system_healthy': health.get('healthy', False)
        }

        logger.info(f"指标收集完成: {len(collections_info)}个集合, {total_vectors}个向量")
        return metrics

    async def save_metrics(self, metrics: Dict):
        """保存性能指标"""
        try:
            # 保存到历史记录
            self.performance_history.append(metrics)

            # 保持最近24小时的数据 (每分钟一次，最多1440条)
            if len(self.performance_history) > 1440:
                self.performance_history = self.performance_history[-1440:]

            # 保存到文件
            history_file = '.runtime/performance_history.json'
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.performance_history, f, ensure_ascii=False, indent=2)

            # 保存最新指标
            latest_file = '.runtime/latest_metrics.json'
            with open(latest_file, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, ensure_ascii=False, indent=2)

            logger.debug(f"性能指标已保存到: {latest_file}")

        except Exception as e:
            logger.error(f"保存性能指标失败: {e}")

    async def generate_daily_report(self) -> Dict:
        """生成每日报告"""
        try:
            if len(self.performance_history) < 10:
                return {'error': '数据不足，无法生成报告'}

            # 获取过去24小时的数据
            now = datetime.now()
            yesterday = now - timedelta(hours=24)

            daily_data = [
                m for m in self.performance_history
                if datetime.fromisoformat(m['timestamp']) >= yesterday
            ]

            if not daily_data:
                return {'error': '没有过去24小时的数据'}

            # 计算统计指标
            summary_stats = {
                'avg_cpu_usage': sum(d.get('system_metrics', {}).get('cpu_percent', 0) for d in daily_data) / len(daily_data),
                'avg_memory_usage': sum(d.get('system_metrics', {}).get('memory_percent', 0) for d in daily_data) / len(daily_data),
                'avg_search_time': sum(d.get('summary', {}).get('avg_search_time_ms', 0) for d in daily_data) / len(daily_data),
                'total_alerts': len(self.alerts[-100:]) if self.alerts else 0,  # 最近100个告警
                'health_check_success_rate': sum(1 for d in daily_data if d.get('health_check', {}).get('healthy', False)) / len(daily_data) * 100
            }

            # 找出性能最差的集合
            collection_performance = {}
            for d in daily_data:
                for perf in d.get('collection_performance', []):
                    name = perf.get('collection', '')
                    if name:
                        if name not in collection_performance:
                            collection_performance[name] = []
                        collection_performance[name].append(perf.get('avg_search_time_ms', 0))

            worst_collections = []
            for name, times in collection_performance.items():
                if times:
                    avg_time = sum(times) / len(times)
                    worst_collections.append({'collection': name, 'avg_time_ms': round(avg_time, 2)})

            worst_collections.sort(key=lambda x: x['avg_time_ms'], reverse=True)

            report = {
                'report_type': 'daily_performance',
                'generated_at': datetime.now().isoformat(),
                'period': f"{yesterday.isoformat()} to {now.isoformat()}",
                'data_points': len(daily_data),
                'summary_stats': {
                    'avg_cpu_usage_percent': round(summary_stats['avg_cpu_usage'], 1),
                    'avg_memory_usage_percent': round(summary_stats['avg_memory_usage'], 1),
                    'avg_search_time_ms': round(summary_stats['avg_search_time'], 2),
                    'health_check_success_rate_percent': round(summary_stats['health_check_success_rate'], 1),
                    'total_alerts': summary_stats['total_alerts']
                },
                'worst_performing_collections': worst_collections[:5],
                'recent_alerts': self.alerts[-10:] if self.alerts else []
            }

            # 保存报告
            report_file = f".runtime/daily_report_{now.strftime('%Y%m%d')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            logger.info(f"每日报告已生成: {report_file}")
            return report

        except Exception as e:
            logger.error(f"生成每日报告失败: {e}")
            return {'error': str(e)}

    async def monitor_loop(self):
        """监控主循环"""
        logger.info(f"🚀 向量数据库监控守护进程启动 (检查间隔: {self.check_interval}秒)")

        last_daily_report = datetime.now().date()

        try:
            while self.running:
                logger.info('📊 开始性能监控检查...')

                # 收集指标
                metrics = await self.collect_metrics()

                # 保存指标
                await self.save_metrics(metrics)

                # 显示当前状态
                summary = metrics.get('summary', {})
                health = metrics.get('health_check', {})

                logger.info(f"✅ 监控检查完成 - 集合: {summary.get('total_collections', 0)}, "
                          f"向量: {summary.get('total_vectors', 0)}, "
                          f"健康: {'✅' if health.get('healthy', False) else '❌'}, "
                          f"告警: {summary.get('active_alerts', 0)}")

                # 检查是否需要生成每日报告
                current_date = datetime.now().date()
                if current_date > last_daily_report:
                    logger.info('📋 生成每日性能报告...')
                    await self.generate_daily_report()
                    last_daily_report = current_date

                # 等待下次检查
                await asyncio.sleep(self.check_interval)

        except Exception as e:
            logger.error(f"监控循环出错: {e}")
        finally:
            logger.info('监控守护进程停止')

    async def start(self):
        """启动监控守护进程"""
        self.running = True

        # 设置信号处理
        def signal_handler(signum, frame):
            logger.info(f"收到信号 {signum}，正在停止监控...")
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        await self.monitor_loop()

    async def stop(self):
        """停止监控守护进程"""
        logger.info('正在停止向量数据库监控守护进程...')
        self.running = False
        await self.close()

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='向量数据库性能监控守护进程')
    parser.add_argument('--interval', type=int, default=60,
                       help='监控检查间隔 (秒)')
    parser.add_argument('--url', type=str, default='http://localhost:6333',
                       help='Qdrant服务地址')

    args = parser.parse_args()

    # 创建并启动监控守护进程
    monitor = VectorMonitorDaemon(
        qdrant_url=args.url,
        check_interval=args.interval
    )

    try:
        await monitor.start()
    except KeyboardInterrupt:
        logger.info("\n⚠️ 用户中断了监控进程")
    except Exception as e:
        logger.error(f"监控进程运行出错: {e}")
    finally:
        await monitor.stop()

if __name__ == '__main__':
    asyncio.run(main())