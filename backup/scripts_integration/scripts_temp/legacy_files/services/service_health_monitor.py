#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena工作平台服务健康监控器
Service Health Monitor for Athena Work Platform

用于实时监控所有核心服务的健康状态，提供自动化告警和恢复机制

使用方法:
python3 service_health_monitor.py --check
python3 service_health_monitor.py --monitor
python3 service_health_monitor.py --report

作者: Athena AI系统
创建时间: 2025-12-08
版本: 1.0.0
"""

import argparse
import asyncio
import json
import logging
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
import psutil

logger = logging.getLogger(__name__)

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

class ServiceHealthMonitor:
    """服务健康监控器"""

    def __init__(self):
        self.services = {
            'athena_main': {
                'name': 'Athena主服务',
                'port': 8000,
                'health_endpoint': '/health',
                'description': '平台核心API和路由服务'
            },
            'athena_memory': {
                'name': 'Athena记忆服务',
                'port': 8008,
                'health_endpoint': '/health',
                'description': '企业级知识管理和记忆系统'
            },
            'xiaonuo_memory': {
                'name': '小诺记忆服务',
                'port': 8083,
                'health_endpoint': '/health',
                'description': '个人记忆和情感交互系统'
            },
            'athena_identity': {
                'name': 'Athena身份认知服务',
                'port': 8010,
                'health_endpoint': '/health',
                'description': '身份识别和认知管理'
            },
            'memory_integration': {
                'name': '记忆集成服务',
                'port': 8011,
                'health_endpoint': '/health',
                'description': '跨系统记忆数据集成'
            }
        }

        self.monitoring_log = project_root / 'logs' / 'service_monitoring.log'
        self.monitoring_log.parent.mkdir(exist_ok=True)

        # 告警阈值
        self.thresholds = {
            'response_time_ms': 5000,  # 5秒响应时间阈值
            'cpu_percent': 80,         # CPU使用率阈值
            'memory_percent': 85,      # 内存使用率阈值
            'disk_percent': 90         # 磁盘使用率阈值
        }

    async def check_service_health(self, service_key: str) -> Dict[str, Any]:
        """检查单个服务的健康状态"""
        service = self.services[service_key]
        url = f"http://localhost:{service['port']}{service['health_endpoint']}"

        health_info = {
            'service_key': service_key,
            'name': service['name'],
            'port': service['port'],
            'status': 'unknown',
            'response_time_ms': 0,
            'last_check': datetime.now().isoformat(),
            'error': None,
            'details': {}
        }

        try:
            start_time = time.time()

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(url) as response:
                    response_time = (time.time() - start_time) * 1000
                    health_info['response_time_ms'] = round(response_time, 2)

                    if response.status == 200:
                        try:
                            data = await response.json()
                            health_info['status'] = data.get('status', 'healthy')
                            health_info['details'] = data
                        except json.JSONDecodeError:
                            health_info['status'] = 'warning'
                            health_info['error'] = 'Invalid JSON response'
                    else:
                        health_info['status'] = 'unhealthy'
                        health_info['error'] = f"HTTP {response.status}"

        except asyncio.TimeoutError:
            health_info['status'] = 'timeout'
            health_info['error'] = 'Request timeout'
        except aiohttp.ClientError as e:
            health_info['status'] = 'unreachable'
            health_info['error'] = str(e)
        except Exception as e:
            health_info['status'] = 'error'
            health_info['error'] = str(e)

        return health_info

    async def check_all_services(self) -> Dict[str, Any]:
        """检查所有服务的健康状态"""
        logger.info('🔍 正在检查所有服务健康状态...')

        tasks = []
        for service_key in self.services.keys():
            task = asyncio.create_task(self.check_service_health(service_key))
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # 整理结果
        health_report = {
            'check_time': datetime.now().isoformat(),
            'total_services': len(self.services),
            'healthy_services': 0,
            'unhealthy_services': 0,
            'services': {}
        }

        for result in results:
            service_key = result['service_key']
            health_report['services'][service_key] = result

            if result['status'] in ['healthy']:
                health_report['healthy_services'] += 1
            else:
                health_report['unhealthy_services'] += 1

        # 计算整体健康评分
        health_report['health_score'] = round(
            (health_report['healthy_services'] / health_report['total_services']) * 100, 1
        )

        return health_report

    def check_system_resources(self) -> Dict[str, Any]:
        """检查系统资源使用情况"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)

            # 内存使用情况
            memory = psutil.virtual_memory()

            # 磁盘使用情况
            disk = psutil.disk_usage('/')

            # 网络统计
            network = psutil.net_io_counters()

            # 进程信息
            process_count = len(psutil.pids())

            resources = {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count(),
                    'status': 'warning' if cpu_percent > self.thresholds['cpu_percent'] else 'normal'
                },
                'memory': {
                    'total_gb': round(memory.total / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'used_gb': round(memory.used / (1024**3), 2),
                    'percent': memory.percent,
                    'status': 'warning' if memory.percent > self.thresholds['memory_percent'] else 'normal'
                },
                'disk': {
                    'total_gb': round(disk.total / (1024**3), 2),
                    'used_gb': round(disk.used / (1024**3), 2),
                    'free_gb': round(disk.free / (1024**3), 2),
                    'percent': round((disk.used / disk.total) * 100, 2),
                    'status': 'warning' if (disk.used / disk.total) * 100 > self.thresholds['disk_percent'] else 'normal'
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                'processes': {
                    'count': process_count,
                    'active': len([p for p in psutil.process_iter() if p.status() == 'running'])
                }
            }

            return resources

        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'status': 'error'
            }

    def print_health_report(self, health_report: Dict[str, Any]):
        """打印健康检查报告"""
        logger.info(f"\n📊 Athena工作平台服务健康报告")
        logger.info(f"🕐 检查时间: {health_report['check_time']}")
        logger.info(f"📈 健康评分: {health_report['health_score']}%")
        logger.info(f"✅ 健康服务: {health_report['healthy_services']}/{health_report['total_services']}")

        logger.info(f"\n🏥 服务状态详情:")
        for service_key, service_info in health_report['services'].items():
            status_emoji = {
                'healthy': '✅',
                'warning': '⚠️',
                'unhealthy': '❌',
                'timeout': '⏰',
                'unreachable': '🔌',
                'error': '💥',
                'unknown': '❓'
            }.get(service_info['status'], '❓')

            logger.info(f"  {status_emoji} {service_info['name']} (端口{service_info['port']})")
            logger.info(f"    状态: {service_info['status']}")
            logger.info(f"    响应时间: {service_info['response_time_ms']}ms")

            if service_info['error']:
                logger.info(f"    错误: {service_info['error']}")

            # 检查响应时间
            if service_info['response_time_ms'] > self.thresholds['response_time_ms']:
                logger.info(f"    ⚠️ 响应时间超过阈值 ({self.thresholds['response_time_ms']}ms)")

    def print_system_resources(self, resources: Dict[str, Any]):
        """打印系统资源报告"""
        logger.info(f"\n💻 系统资源使用情况")
        logger.info(f"🕐 检查时间: {resources['timestamp']}")

        if 'error' in resources:
            logger.info(f"❌ 获取系统信息失败: {resources['error']}")
            return

        # CPU
        cpu_emoji = '⚠️' if resources['cpu']['status'] == 'warning' else '✅'
        logger.info(f"{cpu_emoji} CPU使用率: {resources['cpu']['percent']}% ({resources['cpu']['count']}核)")

        # 内存
        memory_emoji = '⚠️' if resources['memory']['status'] == 'warning' else '✅'
        logger.info(f"{memory_emoji} 内存使用: {resources['memory']['used_gb']}GB/{resources['memory']['total_gb']}GB ({resources['memory']['percent']}%)")

        # 磁盘
        disk_emoji = '⚠️' if resources['disk']['status'] == 'warning' else '✅'
        logger.info(f"{disk_emoji} 磁盘使用: {resources['disk']['used_gb']}GB/{resources['disk']['total_gb']}GB ({resources['disk']['percent']}%)")

        # 进程
        logger.info(f"🔄 运行进程: {resources['processes']['active']}/{resources['processes']['count']}")

    async def continuous_monitoring(self, interval: int = 60):
        """持续监控模式"""
        logger.info(f"🔄 启动持续监控模式，检查间隔: {interval}秒")
        logger.info("按 Ctrl+C 停止监控\n")

        try:
            while True:
                # 检查服务健康
                health_report = await self.check_all_services()

                # 检查系统资源
                resources = self.check_system_resources()

                # 打印报告
                self.print_health_report(health_report)
                self.print_system_resources(resources)

                # 记录日志
                self._log_monitoring_data(health_report, resources)

                # 检查是否需要告警
                await self._check_alerts(health_report, resources)

                logger.info(f"\n⏰ 下次检查: {interval}秒后...")
                logger.info(str('-' * 60))

                await asyncio.sleep(interval)

        except KeyboardInterrupt:
            logger.info("\n👋 监控已停止")

    def _log_monitoring_data(self, health_report: Dict[str, Any], resources: Dict[str, Any]):
        """记录监控数据到日志文件"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'health_report': health_report,
            'system_resources': resources
        }

        try:
            with open(self.monitoring_log, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.info(f"⚠️ 写入日志失败: {e}")

    async def _check_alerts(self, health_report: Dict[str, Any], resources: Dict[str, Any]):
        """检查告警条件"""
        alerts = []

        # 服务告警
        for service_key, service_info in health_report['services'].items():
            if service_info['status'] != 'healthy':
                alerts.append({
                    'type': 'service',
                    'severity': 'high' if service_info['status'] in ['unreachable', 'error'] else 'medium',
                    'message': f"{service_info['name']} 状态异常: {service_info['status']}",
                    'details': service_info
                })

            if service_info['response_time_ms'] > self.thresholds['response_time_ms']:
                alerts.append({
                    'type': 'performance',
                    'severity': 'medium',
                    'message': f"{service_info['name']} 响应时间过长: {service_info['response_time_ms']}ms",
                    'details': service_info
                })

        # 系统资源告警
        if resources.get('cpu', {}).get('percent', 0) > self.thresholds['cpu_percent']:
            alerts.append({
                'type': 'system',
                'severity': 'high',
                'message': f"CPU使用率过高: {resources['cpu']['percent']}%",
                'details': resources['cpu']
            })

        if resources.get('memory', {}).get('percent', 0) > self.thresholds['memory_percent']:
            alerts.append({
                'type': 'system',
                'severity': 'high',
                'message': f"内存使用率过高: {resources['memory']['percent']}%",
                'details': resources['memory']
            })

        # 输出告警
        if alerts:
            logger.info(f"\n🚨 告警通知 ({len(alerts)}个)")
            for alert in alerts:
                severity_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(alert['severity'], '⚪')
                logger.info(f"  {severity_emoji} [{alert['severity'].upper()}] {alert['message']}")

    def generate_report(self) -> str:
        """生成详细的监控报告"""
        logger.info('📋 生成服务监控报告...')

        report_file = project_root / 'reports' / 'service_monitoring_report.md'
        report_file.parent.mkdir(exist_ok=True)

        # 这里可以生成更详细的Markdown报告
        report_content = f"""# Athena工作平台服务监控报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 服务概览

总服务数: {len(self.services)}
监控端口: {', '.join(str(s['port']) for s in self.services.values())}

## 🏥 服务状态

待完善...

---
*报告生成工具: ServiceHealthMonitor v1.0.0*
"""

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        logger.info(f"✅ 报告已生成: {report_file}")
        return str(report_file)

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Athena服务健康监控器')
    parser.add_argument('--check', action='store_true', help='执行一次性健康检查')
    parser.add_argument('--monitor', action='store_true', help='启动持续监控模式')
    parser.add_argument('--report', action='store_true', help='生成监控报告')
    parser.add_argument('--interval', type=int, default=60, help='监控间隔（秒）')

    args = parser.parse_args()

    monitor = ServiceHealthMonitor()

    if args.check or not any(vars(args).values()):
        # 默认执行一次检查
        health_report = await monitor.check_all_services()
        resources = monitor.check_system_resources()

        monitor.print_health_report(health_report)
        monitor.print_system_resources(resources)

        # 保存检查结果
        report_file = project_root / 'logs' / 'latest_health_check.json'
        report_file.parent.mkdir(exist_ok=True)

        check_data = {
            'timestamp': datetime.now().isoformat(),
            'health_report': health_report,
            'system_resources': resources
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(check_data, f, indent=2, ensure_ascii=False)

        logger.info(f"\n📄 检查结果已保存: {report_file}")

    elif args.monitor:
        await monitor.continuous_monitoring(args.interval)

    elif args.report:
        monitor.generate_report()

if __name__ == '__main__':
    asyncio.run(main())