#!/usr/bin/env python3
"""
爬虫性能监控仪表板
Crawler Performance Monitor Dashboard

实时监控爬虫性能指标和优化效果

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.0.0
"""

import asyncio
import json
import logging
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import psutil

# 导入优化的爬虫
from crawler_performance_optimizer import CrawlerConfig, OptimizedAsyncCrawler
from matplotlib.animation import FuncAnimation

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"crawler_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """性能指标数据结构"""
    timestamp: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    cache_hits: int
    cache_misses: int
    avg_response_time: float
    requests_per_second: float
    success_rate: float
    cache_hit_rate: float
    cpu_usage: float
    memory_usage: float
    network_io: dict[str, int]

class CrawlerPerformanceDashboard:
    """爬虫性能监控仪表板"""

    def __init__(self, config: CrawlerConfig = None):
        self.config = config or CrawlerConfig()
        self.crawler = None
        self.metrics_history = []
        self.max_history_points = 100
        self.is_monitoring = False
        self.monitor_thread = None

        # 图表设置
        plt.style.use('seaborn-v0_8-darkgrid')
        self.fig = None
        self.axes = {}
        self.lines = {}
        self.animation = None

        logger.info('🎛️ 性能监控仪表板初始化完成')

    async def initialize(self):
        """初始化监控仪表板"""
        # 创建优化爬虫实例
        self.crawler = OptimizedAsyncCrawler(self.config)
        await self.crawler.initialize_session()

        logger.info('✅ 监控仪表板已连接到爬虫引擎')
        logger.info(f"   并发数: {self.config.max_concurrent}")
        logger.info(f"   Redis: {'启用' if self.config.redis_enabled else '禁用'}")
        logger.info(f"   智能延迟: {'启用' if self.config.adaptive_delay else '禁用'}")

    def collect_system_metrics(self) -> dict[str, Any]:
        """收集系统性能指标"""
        # CPU使用率
        cpu_usage = psutil.cpu_percent(interval=1)

        # 内存使用率
        memory = psutil.virtual_memory()
        memory_usage = memory.percent

        # 网络IO
        network = psutil.net_io_counters()
        network_io = {
            'bytes_sent': network.bytes_sent,
            'bytes_recv': network.bytes_recv,
            'packets_sent': network.packets_sent,
            'packets_recv': network.packets_recv
        }

        return {
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'network_io': network_io
        }

    def collect_crawler_metrics(self) -> PerformanceMetrics | None:
        """收集爬虫性能指标"""
        if not self.crawler:
            return None

        try:
            # 获取爬虫统计
            crawler_stats = self.crawler.get_stats()
            system_metrics = self.collect_system_metrics()

            # 构建性能指标
            metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                total_requests=crawler_stats.get('total_requests', 0),
                successful_requests=crawler_stats.get('successful_requests', 0),
                failed_requests=crawler_stats.get('failed_requests', 0),
                cache_hits=crawler_stats.get('cache_hits', 0),
                cache_misses=crawler_stats.get('cache_misses', 0),
                avg_response_time=crawler_stats.get('avg_response_time', 0),
                requests_per_second=crawler_stats.get('requests_per_second', 0),
                success_rate=crawler_stats.get('success_rate', 0),
                cache_hit_rate=crawler_stats.get('cache_hit_rate', 0),
                cpu_usage=system_metrics['cpu_usage'],
                memory_usage=system_metrics['memory_usage'],
                network_io=system_metrics['network_io']
            )

            # 更新历史记录
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history_points:
                self.metrics_history.pop(0)

            return metrics

        except Exception as e:
            logger.warning(f"收集爬虫指标时出错: {e}")
            return None

    def setup_charts(self):
        """设置监控图表"""
        # 创建图表布局
        self.fig, self.axes = plt.subplots(2, 3, figsize=(18, 10))
        self.fig.suptitle('爬虫性能监控仪表板', fontsize=16, fontweight='bold')

        # 定义子图
        chart_configs = {
            'requests_rate': {'ax': self.axes[0, 0], 'title': '请求速率 (req/s)', 'ylabel': '请求/秒'},
            'success_rate': {'ax': self.axes[0, 1], 'title': '成功率 (%)', 'ylabel': '百分比'},
            'cache_hit_rate': {'ax': self.axes[0, 2], 'title': '缓存命中率 (%)', 'ylabel': '百分比'},
            'response_time': {'ax': self.axes[1, 0], 'title': '平均响应时间 (s)', 'ylabel': '秒'},
            'system_resources': {'ax': self.axes[1, 1], 'title': '系统资源使用率', 'ylabel': '百分比'},
            'domain_performance': {'ax': self.axes[1, 2], 'title': '域名性能分布', 'ylabel': '响应时间 (s)'}
        }

        # 初始化每个图表
        for key, config in chart_configs.items():
            ax = config['ax']
            ax.set_title(config['title'])
            ax.set_xlabel('时间')
            ax.set_ylabel(config['ylabel'])
            ax.grid(True, alpha=0.3)

            # 初始化空线条
            self.lines[key], = ax.plot([], [], 'b-', linewidth=2)
            if key == 'system_resources':
                self.lines['cpu_line'], = ax.plot([], [], 'r-', linewidth=2, label='CPU')
                self.lines['memory_line'], = ax.plot([], [], 'g-', linewidth=2, label='内存')
                ax.legend()

        plt.tight_layout()

    def update_charts(self, frame):
        """更新图表数据"""
        if not self.metrics_history:
            return

        # 准备时间序列数据
        timestamps = [m.timestamp for m in self.metrics_history]
        request_rates = [m.requests_per_second for m in self.metrics_history]
        success_rates = [m.success_rate for m in self.metrics_history]
        cache_hit_rates = [m.cache_hit_rate for m in self.metrics_history]
        response_times = [m.avg_response_time for m in self.metrics_history]
        cpu_usages = [m.cpu_usage for m in self.metrics_history]
        memory_usages = [m.memory_usage for m in self.metrics_history]

        # 更新请求速率图表
        self.lines['requests_rate'].set_data(timestamps, request_rates)
        self.axes[0, 0].relim()
        self.axes[0, 0].autoscale_view()

        # 更新成功率图表
        self.lines['success_rate'].set_data(timestamps, success_rates)
        self.axes[0, 1].relim()
        self.axes[0, 1].autoscale_view()
        self.axes[0, 1].set_ylim(0, 100)

        # 更新缓存命中率图表
        self.lines['cache_hit_rate'].set_data(timestamps, cache_hit_rates)
        self.axes[0, 2].relim()
        self.axes[0, 2].autoscale_view()
        self.axes[0, 2].set_ylim(0, 100)

        # 更新响应时间图表
        self.lines['response_time'].set_data(timestamps, response_times)
        self.axes[1, 0].relim()
        self.axes[1, 0].autoscale_view()

        # 更新系统资源图表
        self.lines['cpu_line'].set_data(timestamps, cpu_usages)
        self.lines['memory_line'].set_data(timestamps, memory_usages)
        self.axes[1, 1].relim()
        self.axes[1, 1].autoscale_view()
        self.axes[1, 1].set_ylim(0, 100)

        # 格式化时间轴
        for ax in self.axes.flat:
            if len(timestamps) > 1:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
                ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=1))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

    def start_monitoring(self, interval=5):
        """启动实时监控"""
        if self.is_monitoring:
            logger.warning('监控已经在运行中')
            return

        self.is_monitoring = True

        # 设置图表
        self.setup_charts()

        # 启动数据收集线程
        def monitor_loop():
            while self.is_monitoring:
                try:
                    metrics = self.collect_crawler_metrics()
                    if metrics:
                        logger.debug(f"收集到指标: 请求速率={metrics.requests_per_second:.1f}/s, "
                                   f"成功率={metrics.success_rate:.1f}%")
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"监控循环出错: {e}")
                    time.sleep(interval)

        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()

        # 启动图表动画
        self.animation = FuncAnimation(
            self.fig, self.update_charts, interval=interval*1000, blit=False
        )

        logger.info(f"🚀 监控已启动，更新间隔: {interval}秒")

    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.animation:
            self.animation.event_source.stop()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info('⏹️ 监控已停止')

    def show_performance_report(self) -> str:
        """显示性能报告"""
        if not self.metrics_history:
            return '暂无性能数据'

        latest = self.metrics_history[-1]

        report = f"""
📊 爬虫性能报告 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
{'='*60}

🎯 核心指标:
   • 总请求数: {latest.total_requests:,}
   • 成功请求数: {latest.successful_requests:,}
   • 失败请求数: {latest.failed_requests:,}
   • 成功率: {latest.success_rate:.1f}%
   • 请求速率: {latest.requests_per_second:.1f} req/s

💾 缓存效果:
   • 缓存命中: {latest.cache_hits:,}
   • 缓存未命中: {latest.cache_misses:,}
   • 命中率: {latest.cache_hit_rate:.1f}%

⏱️ 响应时间:
   • 平均响应时间: {latest.avg_response_time:.3f}s

🖥️ 系统资源:
   • CPU使用率: {latest.cpu_usage:.1f}%
   • 内存使用率: {latest.memory_usage:.1f}%

🚀 优化效果:
   • 预估性能提升: {self.crawler.get_stats().get('performance_metrics', {}).get('estimated_speedup', 0)}x
   • 缓存有效性: {self.crawler.get_stats().get('performance_metrics', {}).get('cache_effectiveness', 0)}%
   • 并发倍数: {self.crawler.get_stats().get('performance_metrics', {}).get('concurrency_factor', 0)}x

📈 Redis缓存状态: {self.crawler.get_stats().get('redis_cache', {}).get('status', 'disabled')}
"""
        return report

    def export_metrics(self, filename: str = None) -> str:
        """导出性能指标数据"""
        if not filename:
            filename = f"crawler_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        data = {
            'export_time': datetime.now().isoformat(),
            'config': asdict(self.config),
            'metrics_history': [asdict(m) for m in self.metrics_history]
        }

        # 转换datetime对象为字符串
        for metric in data['metrics_history']:
            metric['timestamp'] = metric['timestamp'].isoformat()

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"📊 性能指标已导出到: {filename}")
        return filename

    async def run_demo_crawl(self):
        """运行演示爬取"""
        if not self.crawler:
            logger.error('爬虫未初始化')
            return

        # 演示URLs
        demo_urls = [
            'https://patents.google.com',
            'https://www.uspto.gov',
            'https://worldwide.espacenet.com',
            'https://patentscope.justia.com',
            'https://www.freepatentsonline.com'
        ]

        # 重复URLs以测试缓存
        demo_urls.extend(demo_urls[:3])

        logger.info(f"🚀 开始演示爬取 {len(demo_urls)} 个URL")

        # 执行批量爬取
        results = await self.crawler.batch_fetch(demo_urls)

        # 统计结果
        successful = sum(1 for r in results if r.get('success', False))
        logger.info(f"✅ 演示完成: 成功 {successful}/{len(demo_urls)}")

    async def cleanup(self):
        """清理资源"""
        self.stop_monitoring()
        if self.crawler:
            await self.crawler.close()
        if self.fig:
            plt.close(self.fig)

async def main():
    """主函数"""
    logger.info('🎛️ 爬虫性能监控仪表板')
    logger.info(str('='*50))

    # 创建监控配置
    config = CrawlerConfig(
        max_concurrent=20,  # 较低的并发数用于演示
        batch_size=10,
        min_delay=0.1,
        max_delay=0.5,
        cache_enabled=True,
        redis_enabled=True,  # 尝试启用Redis
        adaptive_delay=True
    )

    # 创建仪表板
    dashboard = CrawlerPerformanceDashboard(config)

    try:
        # 初始化
        await dashboard.initialize()

        # 运行演示爬取
        await dashboard.run_demo_crawl()

        # 显示性能报告
        logger.info(str(dashboard.show_performance_report()))

        # 启动实时监控
        logger.info("\n🚀 启动实时监控 (按Ctrl+C停止)")
        dashboard.start_monitoring(interval=2)

        # 显示图表
        plt.show()

        # 导出数据
        dashboard.export_metrics()

    except KeyboardInterrupt:
        logger.info("\n👋 用户中断监控")
    except Exception as e:
        logger.error(f"监控过程中出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await dashboard.cleanup()

if __name__ == '__main__':
    # 检查依赖
    try:
        import matplotlib.pyplot as plt
        import pandas as pd
        import psutil
    except ImportError as e:
        logger.info(f"❌ 缺少依赖库: {e}")
        logger.info('请安装: pip install matplotlib pandas psutil')
        exit(1)

    # 运行仪表板
    asyncio.run(main())
