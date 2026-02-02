#!/usr/bin/env python3
"""
重构后的平台启动脚本
使用新的服务管理框架
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加核心库路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.config import config
from core.database import db_manager
from services.manager import ServiceManager
from services.health_checker import health_checker
from services.monitoring import monitoring_service
from utils.logger import ScriptLogger
from utils.progress_tracker import ProgressTracker


class PlatformLauncher:
    """平台启动器"""

    def __init__(self):
        self.logger = ScriptLogger("PlatformLauncher")
        self.service_manager = ServiceManager.instance()
        self.health_checker = health_checker
        self.monitoring = monitoring_service

    async def start(self, services: list = None, enable_monitoring: bool = True):
        """启动平台"""
        try:
            self.logger.info("🚀 启动 Athena 平台...")

            # 创建进度跟踪器
            tracker = ProgressTracker(100, "平台启动")

            # 1. 初始化数据库连接
            self.logger.info("初始化数据库连接池...")
            await self._init_database()
            tracker.update(10, "数据库连接池初始化完成")

            # 2. 注册健康检查
            self._register_health_checks()
            tracker.update(20, "健康检查注册完成")

            # 3. 启动监控服务
            if enable_monitoring:
                self.logger.info("启动系统监控...")
                asyncio.create_task(self.monitoring.start_monitoring())
                tracker.update(30, "系统监控已启动")

            # 4. 启动指定的服务
            if services:
                self.logger.info(f"启动指定服务: {', '.join(services)}")
                results = {}
                for service in services:
                    result = self.service_manager.start_service(service)
                    results[service] = result
                    if result:
                        tracker.update(50 / len(services), f"{service} 启动成功")
                    else:
                        tracker.update(50 / len(services), f"{service} 启动失败")
            else:
                # 启动所有服务
                self.logger.info("启动所有服务...")
                results = self.service_manager.start_all_services()
                tracker.update(50, "服务启动完成")

            # 5. 启动健康检查
            self.logger.info("启动健康检查...")
            asyncio.create_task(self.health_checker.start_monitoring())
            tracker.update(60, "健康检查已启动")

            # 6. 验证服务状态
            self.logger.info("验证服务状态...")
            await self._verify_services()
            tracker.update(80, "服务状态验证完成")

            # 7. 显示启动报告
            self._show_startup_report(results)
            tracker.complete()

            self.logger.info("✅ Athena 平台启动完成！")

            # 8. 保持运行
            await self._keep_running()

        except Exception as e:
            self.logger.error(f"平台启动失败: {e}")
            self._cleanup()
            raise

    async def stop(self, graceful: bool = True):
        """停止平台"""
        self.logger.info("🛑 停止 Athena 平台...")

        try:
            # 停止健康检查
            self.health_checker.stop_monitoring()

            # 停止监控
            self.monitoring.stop_monitoring()

            # 停止服务
            if graceful:
                self.service_manager.stop_all_services()
            else:
                # 强制停止
                self.service_manager.force_stop_all()

            self.logger.info("✅ 平台已停止")

        except Exception as e:
            self.logger.error(f"停止平台时出错: {e}")

    async def _init_database(self):
        """初始化数据库"""
        # 测试数据库连接
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()

    def _register_health_checks(self):
        """注册健康检查"""
        # 注册核心服务健康检查
        health_checks = config.get('health_checks', {})

        for service_name, check_config in health_checks.items():
            self.health_checker.register_check(service_name, check_config)

        # 如果配置中没有定义，使用默认配置
        if not health_checks:
            default_checks = {
                'core_server': {
                    'url': 'http://localhost:8000/health',
                    'interval': 30
                },
                'ai_service': {
                    'url': 'http://localhost:8001/health',
                    'interval': 30
                },
                'patent_api': {
                    'url': 'http://localhost:8002/health',
                    'interval': 30
                }
            }

            for service_name, check_config in default_checks.items():
                self.health_checker.register_check(service_name, check_config)

    async def _verify_services(self):
        """验证服务状态"""
        # 等待服务完全启动
        await asyncio.sleep(5)

        # 获取服务状态
        status = self.service_manager.get_all_status()

        # 检查是否有失败的服务
        failed_services = [
            name for name, info in status.items()
            if info['status'] == 'error'
        ]

        if failed_services:
            self.logger.warning(f"以下服务启动失败: {', '.join(failed_services)}")

        # 执行健康检查
        health_results = await self.health_checker.check_all_services()
        unhealthy = [
            name for name, result in health_results.items()
            if result.status == 'unhealthy'
        ]

        if unhealthy:
            self.logger.warning(f"以下服务健康检查失败: {', '.join(unhealthy)}")

    def _show_startup_report(self, results: dict):
        """显示启动报告"""
        print("\n" + "="*60)
        print("📊 启动报告")
        print("="*60)

        # 服务启动结果
        print("\n🔧 服务启动结果:")
        for service, success in results.items():
            icon = "✅" if success else "❌"
            print(f"  {icon} {service}")

        # 服务状态
        print("\n📈 当前服务状态:")
        status = self.service_manager.get_all_status()
        for name, info in status.items():
            status_icon = {
                'running': '🟢',
                'stopped': '⭕',
                'error': '🔴',
                'starting': '🔄'
            }.get(info['status'], '❓')

            print(f"  {status_icon} {name:20} 状态: {info['status']:10} PID: {info['pid'] or 'N/A':>8}")

        # 系统资源
        print("\n💻 系统资源:")
        metrics = self.monitoring.get_metrics_summary()
        if 'system_cpu_percent' in metrics:
            cpu = metrics['system_cpu_percent']
            print(f"  CPU使用率: {cpu['current']:.1f}%")
        if 'system_memory_percent' in metrics:
            memory = metrics['system_memory_percent']
            print(f"  内存使用率: {memory['current']:.1f}%")

        print("\n📍 访问地址:")
        print("  - 核心服务: http://localhost:8000")
        print("  - AI服务: http://localhost:8001")
        print("  - 专利API: http://localhost:8002")

        print("="*60)

    async def _keep_running(self):
        """保持运行"""
        self.logger.info("平台运行中... (按 Ctrl+C 停止)")

        try:
            while True:
                await asyncio.sleep(10)

                # 定期输出状态
                if self.health_checker.results:
                    unhealthy = self.health_checker.get_unhealthy_services()
                    if unhealthy:
                        self.logger.warning(f"检测到不健康的服务: {', '.join(unhealthy)}")

        except KeyboardInterrupt:
            self.logger.info("\n收到停止信号...")
            await self.stop()

    def _cleanup(self):
        """清理资源"""
        self.logger.info("清理资源...")
        db_manager.close_all_connections()


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Athena 平台启动器')
    parser.add_argument('--services', nargs='*', help='指定要启动的服务')
    parser.add_argument('--no-monitoring', action='store_true', help='禁用系统监控')
    parser.add_argument('--config', help='指定配置文件')

    args = parser.parse_args()

    # 加载配置
    if args.config:
        config.load_from_file(args.config)

    # 创建启动器
    launcher = PlatformLauncher()

    # 启动平台
    await launcher.start(
        services=args.services,
        enable_monitoring=not args.no_monitoring
    )


if __name__ == "__main__":
    # 运行启动器
    asyncio.run(main())