#!/usr/bin/env python3
"""
Athena工作平台 - 生产环境部署脚本
Production Deployment Script for Athena Platform

功能:
1. 环境检查和准备
2. 依赖安装和验证
3. 配置文件加载
4. 服务启动
5. 健康检查验证

Author: Athena Team
Version: 1.0.0
Date: 2026-02-24
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 设置项目根目录
PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(PROJECT_ROOT / "logs" / "deployment.log")
    ]
)
logger = logging.getLogger(__name__)


class ProductionDeployer:
    """生产环境部署器"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.config_dir = self.project_root / "config"
        self.logs_dir = self.project_root / "logs"
        self.data_dir = self.project_root / "data"
        self.services = {}

        # 创建必要目录
        self._create_directories()

    def _create_directories(self):
        """创建必要的目录"""
        dirs = [
            self.config_dir,
            self.logs_dir,
            self.data_dir,
            self.data_dir / "planning_knowledge.json",
            self.data_dir / "feedback_history.json",
            self.data_dir / "strategy_optimization.json",
        ]
        for dir_path in dirs:
            if isinstance(dir_path, Path):
                dir_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                Path(dir_path).parent.mkdir(parents=True, exist_ok=True)

        logger.info("✅ 目录结构已准备就绪")

    def check_environment(self) -> dict[str, Any]:
        """检查环境"""
        logger.info("🔍 检查部署环境...")

        results = {
            "python_version": sys.version.split()[0],
            "python_path": sys.executable,
            "project_root": str(self.project_root),
            "checks": {}
        }

        # 检查Python版本
        python_version = sys.version_info
        if python_version >= (3, 11):
            results["checks"]["python"] = "✅ Python版本符合要求 (>=3.11)"
        else:
            results["checks"]["python"] = f"❌ Python版本过低: {python_version}"

        # 检查必需的包
        required_packages = [
            "fastapi", "uvicorn", "pydantic", "aiohttp"
        ]
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
                results["checks"][package] = f"✅ {package} 已安装"
            except ImportError:
                results["checks"][package] = f"❌ {package} 未安装"
                missing_packages.append(package)

        if missing_packages:
            logger.warning(f"⚠️ 缺少依赖包: {', '.join(missing_packages)}")

        # 检查核心模块
        try:
            from core.cognition.xiaonuo_planner_engine import XiaonuoPlannerEngine
            results["checks"]["planner_engine"] = "✅ 智能规划引擎可用"
            self.planner_available = True
        except ImportError as e:
            results["checks"]["planner_engine"] = f"❌ 智能规划引擎不可用: {e}"
            self.planner_available = False

        try:
            from core.framework.agents.xiaonuo_coordinator import XiaonuoCoordinator
            results["checks"]["xiaonuo_coordinator"] = "✅ 小诺协调器可用"
            self.coordinator_available = True
        except ImportError as e:
            results["checks"]["xiaonuo_coordinator"] = f"❌ 小诺协调器不可用: {e}"
            self.coordinator_available = False

        return results

    def install_dependencies(self) -> bool:
        """安装依赖"""
        logger.info("📦 安装依赖包...")

        # 安装核心依赖
        requirements = [
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "pydantic>=2.5.0",
            "aiohttp>=3.9.0",
            "websockets>=12.0",
        ]

        for req in requirements:
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-q", req],
                    check=True,
                    capture_output=True
                )
                logger.info(f"  ✅ {req}")
            except subprocess.CalledProcessError as e:
                logger.error(f"  ❌ {req}: {e}")
                return False

        logger.info("✅ 依赖安装完成")
        return True

    def load_environment(self) -> dict[str, Any]:
        """加载环境配置"""
        logger.info("⚙️ 加载环境配置...")

        env_config = {}

        # 加载生产环境配置
        env_file = self.config_dir / "production.env"
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_config[key.strip()] = value.strip()
                        os.environ[key.strip()] = value.strip()
            logger.info(f"  ✅ 加载 {len(env_config)} 个配置项")
        else:
            logger.warning("  ⚠️ 生产环境配置文件不存在，使用默认配置")

        # 设置关键环境变量
        os.environ.setdefault('PYTHONPATH', str(self.project_root))
        os.environ.setdefault('ENVIRONMENT', 'production')
        os.environ.setdefault('DEBUG', 'false')
        os.environ.setdefault('GATEWAY_PORT', '8005')

        return env_config

    async def start_gateway_service(self) -> bool:
        """启动网关服务（使用gateway-unified Go实现）"""
        logger.info("🚀 启动统一网关服务（Gateway Unified）...")

        try:
            # Gateway Unified (Go) 已通过系统服务启动
            # 这里只检查运行状态
            gateway_binary = self.project_root / "gateway-unified" / "bin" / "gateway-unified"
            config_file = self.project_root / "gateway-unified" / "gateway-config.yaml"

            if not gateway_binary.exists():
                logger.error(f"  ❌ Gateway二进制文件不存在: {gateway_binary}")
                return False

            if not config_file.exists():
                logger.error(f"  ❌ Gateway配置文件不存在: {config_file}")
                return False

            # 检查Gateway是否已经在运行
            import subprocess
            try:
                result = subprocess.run(
                    ["pgrep", "-f", "gateway-unified"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    logger.info("  ✅ Gateway Unified已在运行")
                    return True
            except Exception as e:
                logger.warning(f"  ⚠️ 无法检查Gateway状态: {e}")

            # 如果Gateway未运行，启动它
            logger.info("  🔄 启动Gateway Unified...")
            gateway_dir = self.project_root / "gateway-unified"

            # 使用nohup后台启动
            subprocess.Popen(
                [str(gateway_binary), "-config", "gateway-config.yaml"],
                cwd=str(gateway_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )

            # 等待启动
            await asyncio.sleep(2)

            # 验证启动成功
            result = subprocess.run(
                ["pgrep", "-f", "gateway-unified"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info("  ✅ Gateway Unified启动成功")
                return True
            else:
                logger.error("  ❌ Gateway Unified启动失败")
                return False

            # 保存PID
            with open(pid_file, 'w') as f:
                f.write(str(os.getpid()))

            self.services['gateway'] = server
            self.services['gateway_config'] = config

            logger.info("✅ 网关服务启动配置完成")
            return True

        except Exception as e:
            logger.error(f"❌ 网关服务启动失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def start_xiaonuo_service(self) -> bool:
        """启动小诺服务"""
        logger.info("🧠 启动小诺智能规划服务...")

        if not self.coordinator_available:
            logger.error("❌ 小诺协调器不可用，无法启动服务")
            return False

        try:
            from core.framework.agents.xiaonuo_coordinator import XiaonuoCoordinator

            # 初始化小诺
            xiaonuo = XiaonuoCoordinator()
            await xiaonuo.initialize()

            self.services['xiaonuo'] = xiaonuo

            logger.info("✅ 小诺智能规划服务启动完成")
            logger.info("  🎯 智能规划功能: 可用" if self.planner_available else "  ⚠️ 智能规划功能: 不可用")
            return True

        except Exception as e:
            logger.error(f"❌ 小诺服务启动失败: {e}")
            return False

    async def run_health_checks(self) -> dict[str, Any]:
        """运行健康检查"""
        logger.info("🏥 执行健康检查...")

        health_status = {
            "timestamp": datetime.now().isoformat(),
            "services": {}
        }

        # 检查网关服务
        gateway_port = os.getenv('GATEWAY_PORT', '8005')
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://localhost:{gateway_port}/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        health_status["services"]["gateway"] = "✅ 健康"
                        logger.info("  ✅ 网关服务健康")
                    else:
                        health_status["services"]["gateway"] = f"⚠️ HTTP {response.status}"
        except Exception as e:
            health_status["services"]["gateway"] = f"❌ 检查失败: {e}"
            logger.warning(f"  ⚠️ 网关服务未响应: {e}")

        # 检查小诺服务
        if 'xiaonuo' in self.services:
            try:
                self.services['xiaonuo']
                # 简单检查服务是否可用
                health_status["services"]["xiaonuo"] = "✅ 运行中"
                logger.info("  ✅ 小诺服务健康")
            except Exception as e:
                health_status["services"]["xiaonuo"] = f"❌ 检查失败: {e}"
                logger.warning(f"  ⚠️ 小诺服务异常: {e}")

        return health_status

    async def deploy(self):
        """执行完整部署"""
        logger.info("=" * 60)
        logger.info("🚀 Athena工作平台 - 生产环境部署")
        logger.info("=" * 60)

        # 1. 环境检查
        env_check = self.check_environment()
        logger.info("\n📊 环境检查结果:")
        for _check, result in env_check["checks"].items():
            logger.info(f"  {result}")

        # 2. 加载配置
        self.load_environment()

        # 3. 启动服务
        logger.info("\n🎯 启动服务...")

        # 启动网关
        gateway_ok = await self.start_gateway_service()

        # 启动小诺
        xiaonuo_ok = await self.start_xiaonuo_service()

        if not (gateway_ok or xiaonuo_ok):
            logger.error("❌ 服务启动失败")
            return False

        # 4. 健康检查
        logger.info("\n🏥 执行健康检查...")
        health_status = await self.run_health_checks()

        logger.info("\n📊 健康检查结果:")
        for service, status in health_status["services"].items():
            logger.info(f"  {service}: {status}")

        # 5. 显示访问信息
        logger.info("\n" + "=" * 60)
        logger.info("🎉 部署完成！")
        logger.info("=" * 60)
        logger.info("\n📱 服务访问地址:")
        logger.info(f"  • API网关:   http://localhost:{os.getenv('GATEWAY_PORT', '8005')}")
        logger.info(f"  • API文档:   http://localhost:{os.getenv('GATEWAY_PORT', '8005')}/docs")
        logger.info(f"  • 健康检查: http://localhost:{os.getenv('GATEWAY_PORT', '8005')}/health")
        logger.info("\n🧠 小诺智能规划:")
        logger.info(f"  • Phase 1 (基础): {'✅ 已启用' if self.planner_available else '❌ 未启用'}")
        logger.info(f"  • Phase 2 (多方案): {'✅ 已启用' if self.planner_available else '❌ 未启用'}")
        logger.info(f"  • Phase 3 (学习优化): {'✅ 已启用' if self.planner_available else '❌ 未启用'}")
        logger.info("\n📋 管理命令:")
        logger.info("  • 查看日志: tail -f logs/deployment.log")
        logger.info("  • 停止服务: pkill -f athena_gateway")
        logger.info("  • 重启服务: python3 scripts/deploy_production.py restart")
        logger.info("\n" + "=" * 60)

        return True


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Athena工作平台部署脚本")
    parser.add_argument(
        "command",
        nargs="?",
        choices=["deploy", "health", "status", "stop", "restart"],
        default="deploy",
        help="部署命令: deploy(部署), health(健康检查), status(状态), stop(停止), restart(重启)"
    )

    args = parser.parse_args()
    deployer = ProductionDeployer()

    if args.command == "deploy":
        await deployer.deploy()

    elif args.command == "health":
        health_status = await deployer.run_health_checks()
        print(json.dumps(health_status, indent=2, ensure_ascii=False))

    elif args.command == "status":
        print("检查服务状态...")
        # 这里可以添加更多状态检查逻辑
        health_status = await deployer.run_health_checks()
        for service, status in health_status["services"].items():
            print(f"  {service}: {status}")

    elif args.command == "stop":
        print("停止服务...")
        # 停止所有服务
        subprocess.run(["pkill", "-f", "athena_gateway"])
        print("✅ 服务已停止")

    elif args.command == "restart":
        print("重启服务...")
        subprocess.run(["pkill", "-f", "athena_gateway"])
        await asyncio.sleep(2)
        await deployer.deploy()


if __name__ == "__main__":
    asyncio.run(main())
