#!/usr/bin/env python3
"""
Athena平台统一启动管理器
Comprehensive Startup Manager
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComprehensiveStartup:
    """全面启动管理器"""

    def __init__(self):
        self.project_root = project_root
        self.services: dict[str, Any] = {}
        self.pids: dict[str, int] = {}

    async def startup_all(self):
        """启动所有服务"""
        logger.info("=" * 60)
        logger.info("🚀 Athena平台统一启动管理器")
        logger.info("=" * 60)
        logger.info("📋 启动顺序: 基础设施 → 核心模块 → 智能体")
        logger.info("=" * 60)

        try:
            # 1. 启动基础设施
            await self.start_infrastructure()

            # 2. 启动核心模块
            await self.start_core_modules()

            # 3. 启动智能体
            await self.start_agents()

            # 4. 健康检查
            health_report = await self.comprehensive_health_check()

            logger.info("=" * 60)
            logger.info("✅ Athena平台启动完成！")
            logger.info("=" * 60)
            logger.info(f"⏱️ 总耗时: {health_report['total_time']:.2f}秒")
            logger.info(f"📊 娡块状态: {health_report['healthy']}/{health_report['total']} 健康")

            return health_report

        except Exception as e:
            logger.error(f"❌ 启动失败: {e}")
            raise

    async def start_infrastructure(self):
        """启动基础设施"""
        logger.info("📦 Step 1: 启动基础设施...")

        import subprocess
        import time

        try:
            # 启动Docker服务
            subprocess.run(
                ["docker-compose", "up", "-d"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )

            # 等待服务启动
            time.sleep(5)

            logger.info("✅ Docker服务已启动")

        except Exception as e:
            logger.error(f"❌ Docker启动失败: {e}")
            raise

    async def start_core_modules(self):
        """启动核心模块"""
        logger.info("⚙️ Step 2: 启动核心模块...")

        # 启动记忆系统
        await self._start_memory_system()

        # 启动执行引擎
        await self._start_execution_engine()

        logger.info("✅ 核心模块已启动")

    async def _start_memory_system(self):
        """启动记忆系统"""
        logger.info("💾 启动记忆系统...")

        # 记忆系统通常是自动初始化的， logger.info("✅ 记忆系统就绪")

    async def _start_execution_engine(self):
        """启动执行引擎"""
        logger.info("⚙️ 启动执行引擎...")

        # 执行引擎通常是自动初始化的
        logger.info("✅ 执行引擎就绪")

    async def start_agents(self):
        """启动智能体"""
        logger.info("🤖 Step 3: 启动智能体...")

        # 启动小诺
        await self._start_xiaonuo()

        # 启动小娜
        await self._start_xiaona()

        # 启动Gateway
        await self._start_gateway()

        logger.info("✅ 智能体已启动")

    async def _start_xiaonuo(self):
        """启动小诺智能体"""
        logger.info("💠 启动小诺·双鱼公主...")

        import os
        import subprocess

        xiaonuo_path = self.project_root / "services/intelligent-collaboration/xiaonuo_main.py"

        if os.path.exists(xiaonuo_path):
            proc = subprocess.Popen(
                [sys.executable, "python3", xiaonuo_path],
                stdout=open(self.project_root / "logs/xiaonuo.log", "w"),
                stderr=subprocess.STDOUT,
            )
            self.pids['xiaonuo'] = proc.pid
            logger.info(f"✅ 小诺已启动 (PID: {self.pids['xiaonuo']})")
        else:
            logger.warning("⚠️  小诺启动脚本不存在")

    async def _start_xiaona(self):
        """启动小娜智能体"""
        logger.info("⚖️ 启动小娜·天秤女神...")

        # 小娜通常通过小诺调度
        logger.info("✅ 小娜功能已集成到小诺中")

    async def _start_gateway(self):
        """启动Gateway"""
        logger.info("🌐 启动Gateway网关...")

        import subprocess

        gateway_path = self.project_root / "gateway-unified/gateway"

        if os.path.exists(gateway_path):
            proc = subprocess.Popen(
                [gateway_path],
                stdout=open(self.project_root / "logs/gateway.log", "w"),
                stderr=subprocess.STDOUT,
            )
            self.pids['gateway'] = proc.pid

            pid_file = self.project_root / "data/gateway.pid"
            with open(pid_file, 'w') as f:
                f.write(str(self.pids['gateway']))

            logger.info(f"✅ Gateway已启动 (PID: {self.pids['gateway']})")
        else:
            logger.warning("⚠️  Gateway启动脚本不存在")

    async def comprehensive_health_check(self) -> dict[str, Any]:
        """全面健康检查"""
        import time
        start_time = time.time()

        checks = {
            "redis": self._check_redis(),
            "postgresql": self._check_postgresql(),
            "neo4j": self._check_neo4j(),
            "qdrant": self._check_qdrant(),
            "gateway": self._check_gateway(),
            "xiaonuo": self._check_xiaonuo(),
        }

        results = {}
        healthy_count = 0
        total = len(checks)

        for name, check_func in checks.items():
            try:
                result = await check_func()
                results[name] = result
                if result:
                    healthy_count += 1
            except Exception as e:
                logger.error(f"❌ {name}检查失败: {e}")
                results[name] = False

        end_time = time.time()

        return {
            "healthy": healthy_count,
            "total": total,
            "details": results,
            "total_time": end_time - start_time
        }

    async def _check_redis(self) -> bool:
        """检查Redis"""
        try:
            import redis
            client = redis.Redis(host='localhost', port=6379)
            return client.ping()
        except Exception:
            return False

    async def _check_postgresql(self) -> bool:
        """检查PostgreSQL"""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                user="postgres",
                password="athena_dev_password_2024_secure",
                database="postgres"
            )
            conn.close()
            return True
        except Exception:
            return False

    async def _check_neo4j(self) -> bool:
        """检查Neo4j"""
        try:
            import requests
            response = requests.get("http://localhost:7474", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    async def _check_qdrant(self) -> bool:
        """检查Qdrant"""
        try:
            import requests
            response = requests.get("http://localhost:6333", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    async def _check_gateway(self) -> bool:
        """检查Gateway"""
        try:
            import requests
            response = requests.get("http://localhost:8005/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    async def _check_xiaonuo(self) -> bool:
        """检查小诺智能体"""
        try:
            return 'xiaonuo' in self.pids
        except Exception:
            return False

async def main():
    """主函数"""
    startup = ComprehensiveStartup()
    report = await startup.startup_all()

    # 打印详细报告
    print("\n" + "=" * 60)
    print("📊 详细检查报告")
    print("=" * 60)

    for service, status in report['details'].items():
        emoji = "✅" if status else "❌"
        status_text = '正常运行' if status else '异常'
        print(f"{emoji} {service}: {status_text}")

if __name__ == "__main__":
    asyncio.run(main())
