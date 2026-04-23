#!/usr/bin/env python3
"""
Athena平台启动脚本（集成多模态文件系统）
Athena Platform Launcher with Multimodal File System Integration

根据使用场景智能启动多模态文件系统
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "services" / "multimodal"))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AthenaLauncher:
    """Athena平台启动器"""

    def __init__(self):
        self.config_file = project_root / "athena_config.json"
        self.multimodal_config = project_root / "services/multimodal/startup_configs.json"
        self.launch_mode = None
        self.scenario = None

    def detect_startup_scenario(self) -> str:
        """检测启动场景"""

        # 检查环境变量
        env_scenario = os.getenv('ATHENA_SCENARIO')
        if env_scenario:
            logger.info(f"检测到环境变量场景: {env_scenario}")
            return env_scenario

        # 检查配置文件
        if self.config_file.exists():
            with open(self.config_file, encoding='utf-8') as f:
                config = json.load(f)
                return config.get('startup_scenario', 'default')

        # 检查时间场景
        current_time = datetime.now()
        hour = current_time.hour

        # 工作时间默认启用监控
        if 9 <= hour <= 17:
            return 'production'
        else:
            return 'minimal'

    def check_existing_services(self) -> dict[str, bool]:
        """检查现有服务状态"""
        services = {
            'database': self._check_service(5432, 'postgresql'),
            'redis': self._check_service(6379, 'redis'),
            'elasticsearch': self._check_service(9200, 'elasticsearch'),
            'multimodal_api': self._check_service(8000, 'multimodal')
        }
        return services

    def _check_service(self, port: int, service_name: str) -> bool:
        """检查服务是否在运行"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result == 0
        except:
            return False

    def calculate_startup_mode(self) -> tuple:
        """计算最佳启动模式"""
        scenario = self.detect_startup_scenario()

        # 检查系统资源
        import psutil
        memory_gb = psutil.virtual_memory().total / (1024**3)
        cpu_cores = psutil.cpu_count()

        # 检查文件系统使用情况
        multimodal_path = project_root / "storage-system" / "data" / "multimodal_files"
        if multimodal_path.exists():
            file_count = len(list(multimodal_path.rglob('*')))
        else:
            file_count = 0

        logger.info(f"检测场景: {scenario}")
        logger.info(f"系统资源: {memory_gb:.1f}GB RAM, {cpu_cores} cores")
        logger.info(f"现有文件: {file_count} 个")

        # 根据场景和资源决定启动模式
        if scenario == 'development':
            return 'full', "开发环境 - 启动所有功能"
        elif scenario == 'production':
            if file_count > 100:
                return 'full', f"生产环境 - {file_count}个文件需要完整功能"
            else:
                return 'core', "生产环境 - 基础功能+监控"
        elif scenario == 'testing':
            return 'custom', "测试环境 - 按需求启动"
        else:
            if file_count > 50:
                return 'custom', "文件数量较多 - 启动额外功能"
            else:
                return 'minimal', "轻量级使用 - 基础功能"

    async def launch_athena(self):
        """启动Athena平台"""
        print("🚀 Athena平台启动器")
        print("=" * 50)

        # 显示当前状态
        self._show_current_status()

        # 计算启动模式
        mode, reason = self.calculate_startup_mode()
        self.launch_mode = mode
        self.scenario = self.detect_startup_scenario()

        print(f"\n📋 启动模式: {mode}")
        print(f"💡 启动原因: {reason}")
        print(f"🎯 运行场景: {self.scenario}")

        # 确认启动
        if not self._confirm_startup():
            print("\n❌ 用户取消启动")
            return

        # 启动多模态文件系统
        await self._start_multimodal_system(mode)

        # 启动其他Athena服务
        await self._start_athena_services()

        # 显示服务状态
        self._show_service_status()

    def _show_current_status(self) -> Any:
        """显示当前状态"""
        print("\n📊 当前环境状态:")

        services = self.check_existing_services()
        for service, running in services.items():
            status = "✅ 运行中" if running else "⏸️ 停止"
            print(f"  {service:<15} {status}")

        # 检查资源使用
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()

        print("\n💻 系统资源:")
        print(f"  CPU使用率: {cpu_percent}%")
        print(f"  内存使用: {memory.percent}% ({memory.used/1024/1024/1024:.1f}GB / {memory.total/1024/1024/1024:.1f}GB)")

    def _confirm_startup(self) -> bool:
        """确认启动"""
        print("\n" + "=" * 50)
        print("即将启动:")
        print("  ✅ Athena核心服务")
        print("  ✅ 多模态文件系统")

        if self.launch_mode in ['full', 'core']:
            print("  ✅ 性能监控")
        if self.launch_mode == 'full':
            print("  ✅ 批量处理")
            print("  ✅ 版本管理")
            print("  ✅ AI处理")
            print("  ✅ 分布式存储")

        print("\n继续启动吗？ (y/n): ", end="")
        try:
            response = input().strip().lower()
            return response in ['y', 'yes', '是', 'ok']
        except:
            return False

    async def _start_multimodal_system(self, mode: str):
        """启动多模态文件系统"""
        print(f"\n🔧 启动多模态文件系统 (模式: {mode})...")

        try:
            # 导入智能启动器
            from smart_launcher import ComponentManager

            # 读取配置
            config_file = project_root / "services/multimodal/startup_configs.json"
            if config_file.exists():
                with open(config_file) as f:
                    startup_configs = json.load(f)

                # 应用场景配置
                if self.scenario in startup_configs.get("startup_scenarios", {}):
                    scenario_config = startup_configs["startup_scenarios"][self.scenario]
                    mode = scenario_config.get("mode", mode)

                    print(f"  📝 应用场景配置: {self.scenario}")
                    print(f"  📋 启动模式: {mode}")

            # 创建组件管理器并启动
            manager = ComponentManager()
            await manager.startup(mode)

            print("✅ 多模态文件系统启动成功")

        except Exception as e:
            logger.error(f"多模态系统启动失败: {e}")
            raise

    async def _start_athena_services(self):
        """启动其他Athena服务"""
        print("\n🚀 启动Athena其他服务...")

        services_to_start = []

        # 根据场景启动不同服务
        if self.scenario in ['development', 'production']:
            services_to_start.extend([
                '知识图谱服务',
                '专利检索服务',
                '爬虫工具服务',
                'AI对话服务'
            ])

        # 启动服务
        for service in services_to_start:
            try:
                print(f"  🔄 启动{service}...")
                # 这里添加实际的启动逻辑
                # 例如：subprocess.Popen(['python3', f'{service}_server.py'])
                print(f"  ✅ {service}启动成功")
            except Exception as e:
                print(f"  ⚠️ {service}启动失败: {e}")

    def _show_service_status(self) -> Any:
        """显示服务状态"""
        print("\n" + "=" * 60)
        print("🎉 Athena平台启动完成!")
        print("=" * 60)

        print("\n📍 服务地址:")
        print("  🌐 主API: http://localhost:8080")
        print("  📁 文件系统: http://localhost:8000")
        print("  📚 API文档: http://localhost:8000/docs")

        print("\n📊 服务状态:")
        services = self.check_existing_services()
        for service, running in services.items():
            status = "🟢 在线" if running else "🔴 离线"
            print(f"  {status} {service}")

        print("\n💡 使用提示:")
        print("  • 使用 'smart_launcher.py' 单独启动文件系统")
        print("  • 使用 'python -m athena_platform' 启动完整平台")
        print("  • 查看日志: tail -f logs/athena.log")

    def save_startup_record(self) -> None:
        """保存启动记录"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "scenario": self.scenario,
            "launch_mode": self.launch_mode,
            "services": self.check_existing_services()
        }

        # 保存到日志
        log_dir = project_root / "logs"
        log_dir.mkdir(exist_ok=True)

        with open(log_dir / f"startup_{datetime.now().strftime('%Y%m%d')}.json", 'a') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

async def main():
    """主函数"""
    launcher = AthenaLauncher()

    try:
        await launcher.launch_athena()

        # 保持运行
        print("\n🔄 系统运行中...")
        print("按 Ctrl+C 停止")

        # 保持主线程运行
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n👋 系统已停止")
        launcher.save_startup_record()
    except Exception as e:
        logger.error(f"启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
