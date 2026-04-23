#!/usr/bin/env python3
"""
代理管理器 - 高级代理轮换和健康检查系统
Proxy Manager - Advanced Proxy Rotation and Health Check System

实现智能代理池管理、健康检查、故障恢复和自动轮换

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.0.0
"""

import asyncio
import json
import logging
import queue
import random
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import aiohttp

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [ProxyManager] %(message)s',
    handlers=[
        logging.FileHandler(f"proxy_manager_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ProxyConfig:
    """代理配置"""
    host: str
    port: int
    username: str | None = None
    password: str | None = None
    proxy_type: str = 'http'  # http, https, socks4, socks5
    location: str = 'unknown'  # 地理位置
    provider: str = 'unknown'  # 提供商
    max_connections: int = 100  # 最大连接数
    timeout: int = 30  # 超时时间

@dataclass
class ProxyStats:
    """代理统计信息"""
    proxy_config: ProxyConfig
    success_count: int = 0
    failure_count: int = 0
    total_response_time: float = 0.0
    last_used: datetime | None = None
    last_health_check: datetime | None = None
    is_healthy: bool = True
    consecutive_failures: int = 0
    ban_count: int = 0  # 被封禁次数
    current_connections: int = 0
    total_requests: int = 0

    @property
    def success_rate(self) -> float:
        """成功率"""
        total = self.success_count + self.failure_count
        return (self.success_count / total * 100) if total > 0 else 0.0

    @property
    def avg_response_time(self) -> float:
        """平均响应时间"""
        return (self.total_response_time / self.success_count) if self.success_count > 0 else 0.0

    @property
    def health_score(self) -> float:
        """健康评分 (0-100)"""
        # 综合成功率、响应时间、连续失败次数计算
        success_score = self.success_rate
        response_score = max(0, 100 - (self.avg_response_time * 10))  # 响应时间越短越好
        failure_penalty = self.consecutive_failures * 10

        return max(0, min(100, (success_score + response_score) / 2 - failure_penalty))

class ProxyHealthChecker:
    """代理健康检查器"""

    def __init__(self, check_interval: int = 300, test_urls: list[str] | None = None):
        self.check_interval = check_interval
        self.test_urls = test_urls or [
            'http://httpbin.org/ip',
            'http://icanhazip.com',
            'http://checkip.amazonaws.com'
        ]
        self.is_running = False
        self.check_thread = None

    async def check_proxy(self, proxy_config: ProxyConfig) -> tuple[bool, float, str]:
        """检查单个代理的健康状态"""
        start_time = time.time()

        try:
            # 构建代理URL
            if proxy_config.username and proxy_config.password:
                proxy_url = f"{proxy_config.proxy_type}://{proxy_config.username}:{proxy_config.password}@{proxy_config.host}:{proxy_config.port}"
            else:
                proxy_url = f"{proxy_config.proxy_type}://{proxy_config.host}:{proxy_config.port}"

            # 创建测试会话
            timeout = aiohttp.ClientTimeout(total=15, connect=10)
            connector = aiohttp.TCPConnector(ssl=False)

            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                # 测试多个URL以确保稳定性
                for test_url in self.test_urls[:2]:  # 只测试前2个URL
                    try:
                        async with session.get(
                            test_url,
                            proxy=proxy_url,
                            headers={'User-Agent': 'Mozilla/5.0 (compatible; ProxyChecker/1.0)'}
                        ) as response:
                            if response.status == 200:
                                response_time = time.time() - start_time
                                return True, response_time, 'OK'
                    except Exception:
                        continue

                return False, time.time() - start_time, 'All test URLs failed'

        except Exception as e:
            return False, time.time() - start_time, str(e)

    def start_health_check(self, proxy_stats: dict[str, ProxyStats]):
        """启动健康检查线程"""
        def health_check_loop():
            while self.is_running:
                try:
                    asyncio.run(self._check_all_proxies(proxy_stats))
                    time.sleep(self.check_interval)
                except Exception as e:
                    logger.error(f"健康检查循环出错: {e}")

        self.is_running = True
        self.check_thread = threading.Thread(target=health_check_loop, daemon=True)
        self.check_thread.start()
        logger.info(f"🔍 代理健康检查已启动，检查间隔: {self.check_interval}秒")

    def stop_health_check(self):
        """停止健康检查"""
        self.is_running = False
        if self.check_thread:
            self.check_thread.join(timeout=5)
        logger.info('⏹️ 代理健康检查已停止')

    async def _check_all_proxies(self, proxy_stats: dict[str, ProxyStats]):
        """检查所有代理的健康状态"""
        check_tasks = []
        proxy_keys = list(proxy_stats.keys())

        for proxy_key in proxy_keys:
            proxy_stat = proxy_stats[proxy_key]
            task = asyncio.create_task(self.check_proxy(proxy_stat.proxy_config))
            check_tasks.append((proxy_key, task))

        # 并发检查所有代理
        for proxy_key, task in check_tasks:
            try:
                is_healthy, response_time, error_msg = await task
                proxy_stat = proxy_stats[proxy_key]

                proxy_stat.last_health_check = datetime.now()
                proxy_stat.is_healthy = is_healthy

                if is_healthy:
                    proxy_stat.consecutive_failures = 0
                    logger.debug(f"✅ 代理 {proxy_key} 健康检查通过 (响应时间: {response_time:.2f}s)")
                else:
                    proxy_stat.consecutive_failures += 1
                    logger.warning(f"❌ 代理 {proxy_key} 健康检查失败: {error_msg}")

            except Exception as e:
                logger.error(f"检查代理 {proxy_key} 时出错: {e}")

class ProxyRotationManager:
    """代理轮换管理器"""

    def __init__(self, proxy_configs: list[ProxyConfig] | None = None):
        self.proxy_stats: dict[str, ProxyStats] = {}
        self.rotation_queue = queue.Queue()
        self.health_checker = ProxyHealthChecker()
        self.load_balancer = None
        self.lock = threading.Lock()

        # 初始化代理
        if proxy_configs:
            self.add_proxies(proxy_configs)

        logger.info(f"🔄 代理轮换管理器初始化完成，加载了 {len(self.proxy_stats)} 个代理")

    def add_proxies(self, proxy_configs: list[ProxyConfig]):
        """添加代理列表"""
        for config in proxy_configs:
            proxy_key = f"{config.host}:{config.port}"
            if proxy_key not in self.proxy_stats:
                self.proxy_stats[proxy_key] = ProxyStats(proxy_config=config)
                self.rotation_queue.put(proxy_key)
                logger.info(f"➕ 添加代理: {proxy_key} ({config.location})")

    def add_proxy_from_string(self, proxy_string: str, location: str = 'unknown'):
        """从字符串添加代理"""
        try:
            # 解析代理字符串格式: http://username:password@host:port
            parsed = urlparse(proxy_string)

            config = ProxyConfig(
                host=parsed.hostname,
                port=parsed.port,
                username=parsed.username,
                password=parsed.password,
                proxy_type=parsed.scheme,
                location=location
            )

            self.add_proxies([config])
            return True

        except Exception as e:
            logger.error(f"解析代理字符串失败 '{proxy_string}': {e}")
            return False

    def load_proxies_from_file(self, file_path: str):
        """从文件加载代理列表"""
        try:
            with open(file_path, encoding='utf-8') as f:
                lines = f.readlines()

            proxy_configs = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # 支持多种格式
                    if '://' in line:
                        # 完整URL格式
                        self.add_proxy_from_string(line)
                    else:
                        # 简单格式: host:port
                        parts = line.split(':')
                        if len(parts) == 2:
                            config = ProxyConfig(
                                host=parts[0],
                                port=int(parts[1])
                            )
                            proxy_configs.append(config)

            if proxy_configs:
                self.add_proxies(proxy_configs)

            logger.info(f"📂 从文件 {file_path} 加载了 {len(proxy_configs)} 个代理")

        except Exception as e:
            logger.error(f"加载代理文件失败 {file_path}: {e}")

    def get_best_proxy(self, exclude_banned: bool = True) -> ProxyConfig | None:
        """获取最佳代理"""
        with self.lock:
            # 过滤可用代理
            available_proxies = []
            for proxy_key, stat in self.proxy_stats.items():
                if stat.is_healthy and (not exclude_banned or stat.ban_count < 3):
                    if stat.current_connections < stat.proxy_config.max_connections:
                        available_proxies.append((proxy_key, stat))

            if not available_proxies:
                logger.warning('⚠️ 没有可用的代理')
                return None

            # 按健康评分排序
            available_proxies.sort(key=lambda x: x[1].health_score, reverse=True)

            # 选择top 3中的随机代理（避免总是用同一个）
            top_proxies = available_proxies[:min(3, len(available_proxies))]
            selected_key, selected_stat = random.choice(top_proxies)

            # 更新使用统计
            selected_stat.last_used = datetime.now()
            selected_stat.current_connections += 1
            selected_stat.total_requests += 1

            logger.debug(f"🎯 选择代理: {selected_key} (健康评分: {selected_stat.health_score:.1f})")
            return selected_stat.proxy_config

    def release_proxy(self, proxy_config: ProxyConfig, success: bool, response_time: float = 0):
        """释放代理并更新统计"""
        proxy_key = f"{proxy_config.host}:{proxy_config.port}"

        with self.lock:
            if proxy_key in self.proxy_stats:
                stat = self.proxy_stats[proxy_key]
                stat.current_connections = max(0, stat.current_connections - 1)

                if success:
                    stat.success_count += 1
                    stat.total_response_time += response_time
                else:
                    stat.failure_count += 1
                    stat.consecutive_failures += 1

                    # 连续失败过多，标记为不健康
                    if stat.consecutive_failures >= 5:
                        stat.is_healthy = False
                        logger.warning(f"🚫 代理 {proxy_key} 连续失败5次，标记为不健康")

    def ban_proxy(self, proxy_config: ProxyConfig, duration_minutes: int = 30):
        """临时封禁代理"""
        proxy_key = f"{proxy_config.host}:{proxy_config.port}"

        with self.lock:
            if proxy_key in self.proxy_stats:
                stat = self.proxy_stats[proxy_key]
                stat.ban_count += 1
                stat.is_healthy = False

                # 设置解封定时器
                def unban_proxy():
                    time.sleep(duration_minutes * 60)
                    with self.lock:
                        if proxy_key in self.proxy_stats:
                            self.proxy_stats[proxy_key].is_healthy = True
                            logger.info(f"🔓 代理 {proxy_key} 已解封")

                threading.Thread(target=unban_proxy, daemon=True).start()
                logger.warning(f"🚫 代理 {proxy_key} 已封禁 {duration_minutes} 分钟")

    def get_proxy_stats(self) -> dict[str, Any]:
        """获取代理统计信息"""
        with self.lock:
            total_proxies = len(self.proxy_stats)
            healthy_proxies = sum(1 for stat in self.proxy_stats.values() if stat.is_healthy)
            banned_proxies = sum(1 for stat in self.proxy_stats.values() if stat.ban_count > 0)
            active_connections = sum(stat.current_connections for stat in self.proxy_stats.values())
            total_requests = sum(stat.total_requests for stat in self.proxy_stats.values())

            # 计算平均健康评分
            health_scores = [stat.health_score for stat in self.proxy_stats.values() if stat.is_healthy]
            avg_health_score = sum(health_scores) / len(health_scores) if health_scores else 0

            # 按地区统计
            location_stats = {}
            for stat in self.proxy_stats.values():
                location = stat.proxy_config.location
                if location not in location_stats:
                    location_stats[location] = {'healthy': 0, 'unhealthy': 0}

                if stat.is_healthy:
                    location_stats[location]['healthy'] += 1
                else:
                    location_stats[location]['unhealthy'] += 1

            return {
                'total_proxies': total_proxies,
                'healthy_proxies': healthy_proxies,
                'unhealthy_proxies': total_proxies - healthy_proxies,
                'banned_proxies': banned_proxies,
                'active_connections': active_connections,
                'total_requests': total_requests,
                'health_rate': (healthy_proxies / total_proxies * 100) if total_proxies > 0 else 0,
                'avg_health_score': round(avg_health_score, 1),
                'location_distribution': location_stats,
                'top_proxies': [
                    {
                        'proxy': f"{stat.proxy_config.host}:{stat.proxy_config.port}",
                        'location': stat.proxy_config.location,
                        'health_score': round(stat.health_score, 1),
                        'success_rate': round(stat.success_rate, 1),
                        'avg_response_time': round(stat.avg_response_time, 2),
                        'current_connections': stat.current_connections
                    }
                    for stat in sorted(self.proxy_stats.values(), key=lambda x: x.health_score, reverse=True)[:5]
                ]
            }

    def export_stats(self, filename: str = None) -> str:
        """导出代理统计"""
        if not filename:
            filename = f"proxy_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        stats_data = {
            'export_time': datetime.now().isoformat(),
            'summary': self.get_proxy_stats(),
            'detailed_stats': {
                proxy_key: {
                    'config': asdict(stat.proxy_config),
                    'stats': {
                        'success_count': stat.success_count,
                        'failure_count': stat.failure_count,
                        'success_rate': round(stat.success_rate, 1),
                        'avg_response_time': round(stat.avg_response_time, 2),
                        'total_requests': stat.total_requests,
                        'health_score': round(stat.health_score, 1),
                        'is_healthy': stat.is_healthy,
                        'consecutive_failures': stat.consecutive_failures,
                        'ban_count': stat.ban_count,
                        'last_used': stat.last_used.isoformat() if stat.last_used else None,
                        'last_health_check': stat.last_health_check.isoformat() if stat.last_health_check else None
                    }
                }
                for proxy_key, stat in self.proxy_stats.items()
            }
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(stats_data, f, indent=2, ensure_ascii=False)

        logger.info(f"📊 代理统计已导出到: {filename}")
        return filename

    def start_health_monitoring(self):
        """启动健康监控"""
        self.health_checker.start_health_check(self.proxy_stats)

    def stop_health_monitoring(self):
        """停止健康监控"""
        self.health_checker.stop_health_check()

def main():
    """演示代理管理器"""
    logger.info('🔄 代理管理器演示')
    logger.info(str('=' * 50))

    # 创建一些测试代理配置
    test_proxies = [
        ProxyConfig(
            host='proxy1.example.com',
            port=8080,
            location='美国',
            provider='ExampleProxy'
        ),
        ProxyConfig(
            host='proxy2.example.com',
            port=3128,
            location='欧洲',
            provider='ExampleProxy'
        ),
        ProxyConfig(
            host='proxy3.example.com',
            port=8888,
            location='亚洲',
            provider='ExampleProxy'
        )
    ]

    # 创建代理管理器
    manager = ProxyRotationManager(test_proxies)

    # 从字符串添加代理
    proxy_strings = [
        'http://user1:pass1@proxy4.example.com:8080',
        'http://user2:pass2@proxy5.example.com:3128'
    ]

    for proxy_str in proxy_strings:
        manager.add_proxy_from_string(proxy_str, '未知地区')

    logger.info("\n📋 代理统计:")
    stats = manager.get_proxy_stats()
    for key, value in stats.items():
        logger.info(f"   {key}: {value}")

    # 启动健康监控
    logger.info("\n🔍 启动健康监控...")
    manager.start_health_monitoring()

    # 模拟获取最佳代理
    logger.info("\n🎯 获取最佳代理:")
    for i in range(3):
        best_proxy = manager.get_best_proxy()
        if best_proxy:
            logger.info(f"   第{i+1}次: {best_proxy.host}:{best_proxy.port} ({best_proxy.location})")

            # 模拟使用代理
            time.sleep(0.1)
            success = random.choice([True, True, False])  # 2/3 成功率
            response_time = random.uniform(0.5, 2.0)

            manager.release_proxy(best_proxy, success, response_time)
            logger.info(f"      结果: {'成功' if success else '失败'}, 响应时间: {response_time:.2f}s")

    # 导出统计
    export_file = manager.export_stats()
    logger.info(f"\n📊 统计已导出到: {export_file}")

    # 停止监控
    manager.stop_health_monitoring()
    logger.info("\n✅ 演示完成")

if __name__ == '__main__':
    main()
