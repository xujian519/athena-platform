#!/usr/bin/env python3
"""
执行引擎 - 生产环境启动脚本
Production Startup Script for Execution Engine

作者: Athena AI系统
创建时间: 2026-01-27
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import json
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.execution.config import ExecutionConfig
from core.execution.execution_engine.engine import ExecutionEngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('production/logs/execution_engine.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class ProductionExecutionEngine:
    """生产环境执行引擎"""

    def __init__(self):
        """初始化生产执行引擎"""
        self.engine = None
        self.shutdown_event = asyncio.Event()
        self.config = None

        # 加载配置
        self._load_config()

        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _load_config(self):
        """加载配置文件"""
        config_path = Path('production/config/execution_config.json')

        if not config_path.exists():
            logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
            self.config = ExecutionConfig()
        else:
            with open(config_path) as f:
                config_dict = json.load(f)
            self.config = ExecutionConfig.from_dict(config_dict['execution_engine'])
            logger.info(f"✅ 配置已加载: {config_path}")

    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"收到信号 {signum}，开始优雅关闭...")
        self.shutdown_event.set()

    async def start(self):
        """启动执行引擎"""
        try:
            logger.info("=" * 70)
            logger.info("Athena执行引擎 - 生产环境启动")
            logger.info("=" * 70)
            logger.info(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Python版本: {sys.version}")
            logger.info(f"工作目录: {Path.cwd()}")
            logger.info("")

            # 创建执行引擎
            agent_id = f"production_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.engine = ExecutionEngine(agent_id=agent_id, config=self.config.to_dict())

            logger.info("正在初始化执行引擎...")
            init_success = await self.engine.initialize()

            if not init_success:
                logger.error("❌ 执行引擎初始化失败")
                return False

            logger.info("✅ 执行引擎初始化成功")
            logger.info("")

            # 显示配置
            logger.info("执行引擎配置:")
            logger.info(f"  - 最大并发任务: {self.config.max_concurrent_tasks}")
            logger.info(f"  - 最大工作线程: {self.config.max_workers}")
            logger.info(f"  - 任务超时: {self.config.task_timeout}秒")
            logger.info(f"  - 最大重试次数: {self.config.max_retries}")
            logger.info(f"  - 死锁检测: {'启用' if self.config.enable_deadlock_detection else '禁用'}")
            logger.info(f"  - 监控: {'启用' if self.config.enable_monitoring else '禁用'}")
            logger.info("")

            # 健康检查
            logger.info("执行健康检查...")
            health = await self.engine.health_check()
            logger.info(f"健康状态: {health.value}")
            logger.info("")

            # 启动监控任务
            if self.config.enable_monitoring:
                asyncio.create_task(self._monitoring_loop())

            # 启动性能指标收集
            if self.config.enable_metrics:
                asyncio.create_task(self._metrics_loop())

            logger.info("✅ 执行引擎已启动，等待任务...")
            logger.info("")

            # 等待关闭信号
            await self.shutdown_event.wait()

            # 优雅关闭
            logger.info("开始关闭执行引擎...")
            await self.shutdown()

            return True

        except Exception as e:
            logger.error(f"❌ 启动失败: {e}", exc_info=True)
            return False

    async def shutdown(self):
        """关闭执行引擎"""
        if self.engine:
            try:
                await self.engine.shutdown()
                logger.info("✅ 执行引擎已关闭")
            except Exception as e:
                logger.error(f"关闭时出错: {e}", exc_info=True)

    async def _monitoring_loop(self):
        """监控循环"""
        while not self.shutdown_event.is_set():
            try:
                # 定期健康检查
                health = await self.engine.health_check()
                if health.value != "healthy":
                    logger.warning(f"健康状态异常: {health.value}")

                # 等待一段时间
                await asyncio.sleep(60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"监控循环出错: {e}", exc_info=True)
                await asyncio.sleep(60)

    async def _metrics_loop(self):
        """指标收集循环"""
        while not self.shutdown_event.is_set():
            try:
                # 收集性能指标
                stats = self.engine.get_statistics() if hasattr(self.engine, 'get_statistics') else {}

                if stats:
                    logger.info(f"性能统计: "
                              f"总计={stats.get('total_tasks', 0)}, "
                              f"完成={stats.get('completed_tasks', 0)}, "
                              f"失败={stats.get('failed_tasks', 0)}, "
                              f"活跃={stats.get('active_tasks', 0)}")

                # 等待一段时间
                await asyncio.sleep(self.config.metrics_collection_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"指标收集出错: {e}", exc_info=True)
                await asyncio.sleep(60)


def main():
    """主函数"""
    # 确保日志目录存在
    Path('production/logs').mkdir(parents=True, exist_ok=True)

    # 创建并启动引擎
    server = ProductionExecutionEngine()

    try:
        success = asyncio.run(server.start())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("收到键盘中断，退出...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"未处理的异常: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
