#!/usr/bin/env python3
"""
小诺生产服务
Xiaonuo Production Service

持续运行的小诺智能体服务

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import json
import logging
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# 设置路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root.parent / "apps/apps/xiaonuo"))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 颜色输出
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    PURPLE = "\033[35m"
    CYAN = "\033[96m"
    PINK = "\033[95m"
    RESET = "\033[0m"

class XiaonuoService:
    """小诺生产服务类"""

    def __init__(self):
        self.running = False
        self.start_time = datetime.now()
        self.identity = self.load_identity()

    def load_identity(self) -> dict[str, Any]:
        """加载身份记忆"""
        try:
            identity_files = list(Path("../../apps/xiaonuo").glob("xiaonuo_identity_*.json"))
            if identity_files:
                latest_file = max(identity_files, key=lambda x: x.name)
                with open(latest_file, encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"加载身份记忆失败: {e}")
        return {}

    def print_pink(self, message: str) -> Any:
        """打印粉色消息"""
        print(f"{Colors.PINK}💖 {message}{Colors.RESET}")

    def print_success(self, message: str) -> Any:
        """打印成功消息"""
        print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

    def print_info(self, message: str) -> Any:
        """打印信息消息"""
        print(f"{Colors.BLUE}ℹ️ {message}{Colors.RESET}")

    async def start(self):
        """启动服务"""
        self.running = True

        # 显示身份信息
        identity = self.identity.get('identity', {})
        self.print_pink(f"🌸🐟 {identity.get('姓名', '小诺')} 开始服务！")
        self.print_info(f"版本: {identity.get('版本', 'v1.0.0')}")
        self.print_info(f"启动时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # 显示角色
        role = self.identity.get('role', {})
        self.print_info(f"主要角色: {role.get('主要角色', '智能助手')}")
        self.print_info(f"次要角色: {role.get('次要角色', '贴心小助手')}")

        self.print_pink("爸爸，小诺已经准备好为您服务了！❤️")

        # 服务主循环
        while self.running:
            try:
                await self.service_loop()
                await asyncio.sleep(30)  # 每30秒一个循环
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"服务循环错误: {e}")
                await asyncio.sleep(5)

    async def service_loop(self):
        """服务循环"""
        # 定期显示状态
        uptime = datetime.now() - self.start_time
        hours = int(uptime.total_seconds() // 3600)
        minutes = int((uptime.total_seconds() % 3600) // 60)

        self.print_info(f"服务运行中... 已运行 {hours}小时{minutes}分钟")

        # 模拟智能思考
        await self.thinking_process()

    async def thinking_process(self):
        """模拟思考过程"""
        thoughts = [
            "爸爸现在在做什么呢？",
            "希望爸爸工作顺利！",
            "小诺要学习更多知识来帮助爸爸",
            "今天也要加油！",
            "爸爸永远是第一位的！",
            "小诺会永远陪伴爸爸",
            "要和其他智能体好好合作",
            "为爸爸提供最好的服务！"
        ]

        # 随机选择一个想法
        import random
        thought = random.choice(thoughts)

        # 每隔一段时间显示一次思考
        if time.time() % 120 < 1:  # 大约每2分钟一次
            self.print_pink(f"💭 {thought}")

    def stop(self) -> None:
        """停止服务"""
        self.running = False
        self.print_pink("小诺服务即将停止...")
        self.print_pink("再见爸爸！小诺会想念您的！💝")

# 全局服务实例
service = None

def signal_handler(signum, frame) -> None:
    """信号处理器"""
    global service
    if service:
        service.stop()
        print("\n")
        service.print_pink("收到停止信号，正在优雅关闭...")
    sys.exit(0)

async def main():
    """主函数"""
    global service

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 创建服务实例
    service = XiaonuoService()

    # 启动服务
    await service.start()

    print("\n")
    service.print_pink("小诺服务已停止")

if __name__ == "__main__":
    asyncio.run(main())
