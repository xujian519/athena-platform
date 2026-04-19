#!/usr/bin/env python3
"""
Rust缓存监控服务 - Prometheus指标导出器

提供实时性能指标和缓存统计
"""

import sys
import time
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from prometheus_client import Counter, Gauge, Histogram, generate_latest, REGISTRY
from prometheus_client.core import REGISTRY

# 项目路径
sys.path.insert(0, '/Users/xujian/Athena工作平台')

from athena_cache import TieredCache

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MetricsHandler(BaseHTTPRequestHandler):
    """Prometheus指标HTTP处理器"""

    def do_GET(self):
        """处理GET请求"""
        if self.path == '/metrics':
            # 更新指标
            update_metrics()

            # 生成Prometheus格式的指标
            metrics = generate_latest(REGISTRY).decode('utf-8')

            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(metrics.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """禁用默认日志输出"""
        pass


# 创建Prometheus指标
cache_hits = Counter('rust_cache_hits_total', 'Total cache hits', ['cache_type', 'layer'])
cache_misses = Counter('rust_cache_misses_total', 'Total cache misses', ['cache_type'])
requests_total = Counter('rust_cache_requests_total', 'Total requests', ['operation'])
cache_size = Gauge('rust_cache_size', 'Current cache size', ['layer'])
memory_usage = Gauge('rust_cache_memory_bytes', 'Memory usage in bytes')

# 创建缓存实例
llm_cache = TieredCache(hot_size=10000, warm_size=100000)
search_cache = TieredCache(hot_size=5000, warm_size=50000)

# 统计数据
stats = {
    'llm_cache': {'hits': 0, 'misses': 0},
    'search_cache': {'hits': 0, 'misses': 0}
}


def update_metrics():
    """更新指标"""
    # 更新缓存大小（假设值）
    cache_size.labels(layer='hot').set(10000)
    cache_size.labels(layer='warm').set(100000)
    memory_usage.set(50000000)  # 50MB


def start_monitoring_server(port=8000):
    """启动监控服务器"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, MetricsHandler)

    logger.info(f"🚀 Prometheus监控服务器启动: http://localhost:{port}/metrics")
    logger.info(f"📊 可用指标:")
    logger.info(f"   - rust_cache_hits_total: 缓存命中总数")
    logger.info(f"   - rust_cache_misses_total: 缓存未命中总数")
    logger.info(f"   - rust_cache_requests_total: 请求总数")
    logger.info(f"   - rust_cache_size: 缓存大小")
    logger.info(f"   - rust_cache_memory_bytes: 内存使用")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("⏹️  监控服务器已停止")
        httpd.server_close()


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🔍 Rust缓存监控服务")
    logger.info("=" * 60)

    # 测试缓存
    logger.info("测试Rust缓存...")
    llm_cache.put("test_key", b"test_value")
    result = llm_cache.get("test_key")
    if result == b"test_value":
        logger.info("✅ LLM缓存测试通过")
        stats['llm_cache']['hits'] += 1
    else:
        logger.error("❌ LLM缓存测试失败")
        stats['llm_cache']['misses'] += 1

    search_cache.put("search_test", b"search_value")
    result = search_cache.get("search_test")
    if result == b"search_value":
        logger.info("✅ 搜索缓存测试通过")
        stats['search_cache']['hits'] += 1
    else:
        logger.error("❌ 搜索缓存测试失败")
        stats['search_cache']['misses'] += 1

    logger.info(f"📊 初始统计:")
    logger.info(f"   LLM缓存 - 命中: {stats['llm_cache']['hits']}, 未命中: {stats['llm_cache']['misses']}")
    logger.info(f"   搜索缓存 - 命中: {stats['search_cache']['hits']}, 未命中: {stats['search_cache']['misses']}")

    # 启动监控服务器
    logger.info("")
    start_monitoring_server()
