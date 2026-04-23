import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# 添加路径
sys.path.append(str(Path(__file__).parent))

from ready_on_demand_system import ai_system

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('AISystem')

class SystemMonitor:
    """系统监控器"""

    def __init__(self):
        self.start_time = datetime.now()
        self.task_count = 0

    async def monitor(self):
        """监控系统状态"""
        print("👁️ 监控系统已启动")

        while True:
            try:
                status = ai_system.get_status()

                # 记录关键指标
                logger.info(f"运行智能体: {status['running_agents']}/{status['total_agents']}")
                logger.info(f"内存使用: {status['memory_usage_mb']} MB")
                logger.info(f"处理任务: {status['total_tasks']}")

                # 保存详细状态到文件
                with open('system_status.json', 'w') as f:
                    status['timestamp'] = datetime.now().isoformat()
                    json.dump(status, f, indent=2)

                # 告警检查
                if status['memory_usage_mb'] > 400:
                    logger.warning(f"内存使用过高: {status['memory_usage_mb']} MB")

                await asyncio.sleep(60)  # 每分钟监控一次

            except Exception as e:
                logger.error(f"监控错误: {e}")
                await asyncio.sleep(60)

async def main():
    """启动监控"""
    print("🚀 启动AI系统监控")
    print("📊 监控数据将保存到:")
    print("   - 控制台输出")
    print("   - ai_system.log")
    print("   - system_status.json")
    print()
    print("按 Ctrl+C 停止监控")

    monitor = SystemMonitor()
    await monitor.monitor()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 监控已停止")
