#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP服务器监控和自动重启系统
MCP Server Monitoring and Auto-Restart System

控制者: 小诺 & Athena
创建时间: 2025年12月11日
版本: 1.0.0
"""

import asyncio
import json
import logging
import signal
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil

# 添加平台路径
platform_root = Path('/Users/xujian/Athena工作平台')
sys.path.insert(0, str(platform_root))

from tools.mcp.athena_mcp_manager import AthenaMCPManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(platform_root / 'logs' / 'mcp_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ServerStatus(Enum):
    """服务器状态枚举"""
    RUNNING = 'running'
    STOPPED = 'stopped'
    ERROR = 'error'
    UNKNOWN = 'unknown'

@dataclass
class ServerHealth:
    """服务器健康状态"""
    name: str
    status: ServerStatus
    last_check: datetime
    process_id: int | None = None
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    restart_count: int = 0
    last_restart: datetime | None = None
    error_message: str | None = None

@dataclass
class MonitorConfig:
    """监控配置"""
    check_interval: int = 30  # 检查间隔（秒）
    max_restarts: int = 3     # 最大重启次数
    restart_window: int = 300  # 重启时间窗口（秒）
    health_check_timeout: int = 15  # 健康检查超时（秒）
    enable_auto_restart: bool = True  # 启用自动重启
    cpu_threshold: float = 80.0  # CPU使用率阈值（%）
    memory_threshold: float = 80.0  # 内存使用率阈值（%）

class MCPMonitor:
    """MCP服务器监控器"""

    def __init__(self, config: MonitorConfig | None = None):
        self.config = config or MonitorConfig()
        self.platform_root = platform_root
        self.manager = AthenaMCPManager()
        self.servers: Dict[str, ServerHealth] = {}
        self.running = False
        self.monitor_task: asyncio.Task | None = None

        # 确保日志目录存在
        (self.platform_root / 'logs').mkdir(exist_ok=True)

    async def start_monitoring(self):
        """启动监控"""
        logger.info('启动MCP服务器监控...')
        self.running = True

        # 初始化服务器状态
        await self.initialize_server_status()

        # 启动监控任务
        self.monitor_task = asyncio.create_task(self.monitor_loop())

        logger.info(f"MCP监控已启动，检查间隔: {self.config.check_interval}秒")

    async def stop_monitoring(self):
        """停止监控"""
        logger.info('停止MCP服务器监控...')
        self.running = False

        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

        logger.info('MCP监控已停止')

    async def initialize_server_status(self):
        """初始化服务器状态"""
        servers = self.manager.list_all_servers()

        for server_name in servers:
            self.servers[server_name] = ServerHealth(
                name=server_name,
                status=ServerStatus.UNKNOWN,
                last_check=datetime.now()
            )

        logger.info(f"已初始化 {len(self.servers)} 个服务器的监控状态")

    async def monitor_loop(self):
        """监控主循环"""
        while self.running:
            try:
                await self.check_all_servers()
                await asyncio.sleep(self.config.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"监控循环异常: {e}")
                await asyncio.sleep(5)  # 出错时短暂等待

    async def check_all_servers(self):
        """检查所有服务器状态"""
        current_time = datetime.now()

        for server_name, health in self.servers.items():
            try:
                # 更新最后检查时间
                health.last_check = current_time

                # 获取服务器状态
                status_info = await self.manager.get_server_status(server_name)

                # 更新状态
                if status_info.get('error'):
                    health.status = ServerStatus.ERROR
                    health.error_message = status_info['error']
                    await self.handle_server_error(server_name, health)
                else:
                    process_id = status_info.get('process_id')
                    if process_id:
                        health.status = ServerStatus.RUNNING
                        health.process_id = process_id
                        health.error_message = None

                        # 获取资源使用情况
                        await self.update_resource_usage(health, process_id)
                    else:
                        health.status = ServerStatus.STOPPED
                        health.process_id = None
                        await self.handle_server_stopped(server_name, health)

                # 记录状态
                logger.debug(f"服务器 {server_name} 状态: {health.status.value}")

            except Exception as e:
                logger.error(f"检查服务器 {server_name} 时发生异常: {e}")
                health.status = ServerStatus.ERROR
                health.error_message = str(e)

    async def update_resource_usage(self, health: ServerHealth, process_id: int):
        """更新资源使用情况"""
        try:
            process = psutil.Process(process_id)
            health.cpu_usage = process.cpu_percent()
            health.memory_usage = process.memory_percent()

            # 检查资源使用是否超过阈值
            if health.cpu_usage > self.config.cpu_threshold:
                logger.warning(f"服务器 {health.name} CPU使用率过高: {health.cpu_usage:.1f}%")

            if health.memory_usage > self.config.memory_threshold:
                logger.warning(f"服务器 {health.name} 内存使用率过高: {health.memory_usage:.1f}%")

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            logger.warning(f"无法获取进程 {process_id} 的资源信息")

    async def handle_server_error(self, server_name: str, health: ServerHealth):
        """处理服务器错误"""
        logger.error(f"服务器 {server_name} 发生错误: {health.error_message}")

        if self.config.enable_auto_restart:
            # 检查是否在重启窗口内
            if self.should_restart(health):
                await self.restart_server(server_name, health)
            else:
                logger.warning(f"服务器 {server_name} 重启次数过多，暂时跳过")

    async def handle_server_stopped(self, server_name: str, health: ServerHealth):
        """处理服务器停止"""
        logger.warning(f"服务器 {server_name} 已停止")

        if self.config.enable_auto_restart:
            if self.should_restart(health):
                await self.restart_server(server_name, health)
            else:
                logger.warning(f"服务器 {server_name} 重启次数过多，暂时跳过")

    def should_restart(self, health: ServerHealth) -> bool:
        """判断是否应该重启"""
        # 检查重启次数
        if health.restart_count >= self.config.max_restarts:
            # 检查是否在时间窗口内
            if health.last_restart:
                time_since_last_restart = datetime.now() - health.last_restart
                if time_since_last_restart.total_seconds() < self.config.restart_window:
                    return False

        return True

    async def restart_server(self, server_name: str, health: ServerHealth):
        """重启服务器"""
        logger.info(f"重启服务器: {server_name}")

        try:
            # 停止服务器
            await self.manager.stop_server(server_name)
            await asyncio.sleep(2)

            # 启动服务器
            success = await self.manager.start_server(server_name)

            if success:
                health.restart_count += 1
                health.last_restart = datetime.now()
                health.status = ServerStatus.RUNNING
                health.error_message = None

                logger.info(f"服务器 {server_name} 重启成功 (第 {health.restart_count} 次)")
            else:
                logger.error(f"服务器 {server_name} 重启失败")

        except Exception as e:
            logger.error(f"重启服务器 {server_name} 时发生异常: {e}")
            health.status = ServerStatus.ERROR
            health.error_message = str(e)

    async def manual_restart(self, server_name: str) -> bool:
        """手动重启服务器"""
        if server_name not in self.servers:
            logger.error(f"未知服务器: {server_name}")
            return False

        health = self.servers[server_name]
        logger.info(f"手动重启服务器: {server_name}")

        try:
            # 停止服务器
            await self.manager.stop_server(server_name)
            await asyncio.sleep(3)

            # 启动服务器
            success = await self.manager.start_server(server_name)

            if success:
                health.restart_count = 0  # 手动重启重置计数器
                health.last_restart = datetime.now()
                health.status = ServerStatus.RUNNING
                health.error_message = None

                logger.info(f"服务器 {server_name} 手动重启成功")
            else:
                logger.error(f"服务器 {server_name} 手动重启失败")

            return success

        except Exception as e:
            logger.error(f"手动重启服务器 {server_name} 时发生异常: {e}")
            return False

    async def get_health_report(self) -> Dict[str, Any]:
        """获取健康状态报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'monitor_config': {
                'check_interval': self.config.check_interval,
                'max_restarts': self.config.max_restarts,
                'enable_auto_restart': self.config.enable_auto_restart
            },
            'servers': {}
        }

        for name, health in self.servers.items():
            report['servers'][name] = {
                'status': health.status.value,
                'last_check': health.last_check.isoformat(),
                'process_id': health.process_id,
                'cpu_usage': health.cpu_usage,
                'memory_usage': health.memory_usage,
                'restart_count': health.restart_count,
                'last_restart': health.last_restart.isoformat() if health.last_restart else None,
                'error_message': health.error_message
            }

        return report

    async def start_all_servers(self) -> Dict[str, bool]:
        """启动所有服务器"""
        logger.info('启动所有MCP服务器...')
        return await self.manager.start_all_servers()

    async def stop_all_servers(self) -> Dict[str, bool]:
        """停止所有服务器"""
        logger.info('停止所有MCP服务器...')
        return await self.manager.stop_all_servers()

class MCPMonitorDaemon:
    """MCP监控守护进程"""

    def __init__(self):
        self.monitor = MCPMonitor()
        self.running = False

    async def start(self):
        """启动守护进程"""
        self.running = True

        # 注册信号处理
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

        # 启动监控
        await self.monitor.start_monitoring()

        # 保持运行
        while self.running:
            await asyncio.sleep(1)

    def handle_signal(self, signum, frame):
        """处理信号"""
        logger.info(f"收到信号 {signum}，正在停止...")
        self.running = False

    async def stop(self):
        """停止守护进程"""
        await self.monitor.stop_monitoring()

async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='MCP服务器监控守护进程')
    parser.add_argument('--daemon', action='store_true', help='以守护进程模式运行')
    parser.add_argument('--start', action='store_true', help='启动所有服务器')
    parser.add_argument('--stop', action='store_true', help='停止所有服务器')
    parser.add_argument('--status', action='store_true', help='显示服务器状态')
    parser.add_argument('--restart', metavar='SERVER', help='重启指定服务器')
    parser.add_argument('--report', action='store_true', help='生成健康报告')

    args = parser.parse_args()

    monitor = MCPMonitor()

    try:
        if args.daemon:
            daemon = MCPMonitorDaemon()
            await daemon.start()
        elif args.start:
            results = await monitor.start_all_servers()
            for server, success in results.items():
                logger.info(f"{server}: {'✅ 成功' if success else '❌ 失败'}")
        elif args.stop:
            results = await monitor.stop_all_servers()
            for server, success in results.items():
                logger.info(f"{server}: {'✅ 成功' if success else '❌ 失败'}")
        elif args.status:
            await monitor.initialize_server_status()
            await monitor.check_all_servers()
            report = await monitor.get_health_report()

            logger.info('MCP服务器状态:')
            logger.info(str('=' * 50))
            for name, info in report['servers'].items():
                status_icon = '🟢' if info['status'] == 'running' else '🔴' if info['status'] == 'stopped' else '🟡'
                logger.info(f"{status_icon} {name}: {info['status']}")
                if info['process_id']:
                    logger.info(f"  PID: {info['process_id']}, CPU: {info['cpu_usage']:.1f}%, MEM: {info['memory_usage']:.1f}%")
                if info['error_message']:
                    logger.info(f"  错误: {info['error_message']}")
        elif args.restart:
            success = await monitor.manual_restart(args.restart)
            logger.info(f"重启 {args.restart}: {'✅ 成功' if success else '❌ 失败'}")
        elif args.report:
            await monitor.initialize_server_status()
            await monitor.check_all_servers()
            report = await monitor.get_health_report()

            report_file = platform_root / 'logs' / f"mcp_health_report_{int(time.time())}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            logger.info(f"健康报告已保存到: {report_file}")
        else:
            parser.print_help()

    except KeyboardInterrupt:
        logger.info('用户中断，正在停止...')
    except Exception as e:
        logger.error(f"运行异常: {e}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())