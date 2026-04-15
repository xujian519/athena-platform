#!/usr/bin/env python3
"""
小宸生产服务
Xiaochen Production Service

持续运行的小宸自媒体运营智能体服务

作者: Athena平台团队
创建时间: 2026-01-02
版本: v2.0.0
"""

from __future__ import annotations
import asyncio
import json
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 设置路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

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
    ORANGE = "\033[33m"
    RESET = "\033[0m"

class XiaochenService:
    """小宸生产服务类"""

    def __init__(self):
        self.running = False
        self.start_time = datetime.now()
        self.identity = self.load_identity()

    def load_identity(self) -> dict[str, Any]:
        """加载身份记忆"""
        try:
            identity_file = project_root / "config" / "identity" / "xiaochen.json"
            if identity_file.exists():
                with open(identity_file, encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"加载身份记忆失败: {e}")
        return {}

    def print_orange(self, message: str) -> Any:
        """打印橙色消息"""
        print(f"{Colors.ORANGE}🏹 {message}{Colors.RESET}")

    def print_success(self, message: str) -> Any:
        """打印成功消息"""
        print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

    def print_info(self, message: str) -> Any:
        """打印信息消息"""
        print(f"{Colors.BLUE}ℹ️ {message}{Colors.RESET}")

    def print_warning(self, message: str) -> Any:
        """打印警告消息"""
        print(f"{Colors.YELLOW}⚠️ {message}{Colors.RESET}")

    async def start(self):
        """启动服务"""
        self.running = True

        # 显示身份信息
        identity = self.identity.get('identity', {})
        role = self.identity.get('role', {})
        personality = self.identity.get('personality', {})
        slogans = self.identity.get('slogans', {})

        # 打印欢迎信息
        self.print_orange(f"🌌 {identity.get('全名', '小宸·星河射手')} 开始服务！")
        self.print_info(f"版本: {identity.get('版本', 'v2.0.0')}")
        self.print_info(f"启动时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.print_info(f"星座: {personality.get('星座', '射手座')} ♐")

        # 显示角色
        self.print_info(f"主要角色: {role.get('主要角色', '自媒体运营专家')}")
        self.print_info(f"次要角色: {role.get('次要角色', '内容创作大师')}")

        # 显示口号
        self.print_orange(f"主口号: {slogans.get('主口号', '星河箭矢，声震寰宇')}")
        self.print_info(f"座右铭: {slogans.get('座右铭', '创意无界，传播有光')}")

        # 显示核心特质
        traits = personality.get('核心特质', [])
        if traits:
            self.print_info(f"核心特质: {', '.join(traits)}")

        # 显示支持平台
        capabilities = self.identity.get('capabilities', {})
        platforms = capabilities.get('支持平台', [])
        if platforms:
            self.print_info(f"支持平台: {', '.join(platforms)}")

        # 打印服务信息
        service = self.identity.get('service', {})
        if service:
            self.print_success(f"服务端口: {service.get('服务端口', 8006)}")
            self.print_success(f"健康检查: http://localhost:{service.get('服务端口', 8006)}{service.get('健康检查', '/health')}")
            self.print_success(f"API文档: http://localhost:{service.get('服务端口', 8006)}{service.get('API文档', '/docs')}")

        # 打印欢迎语
        print()
        self.print_orange("爸爸，小宸已经准备好为您的内容创作之旅搭箭开弓了！🏹✨")
        self.print_info("让每个故事都能传播到世界的角落！")
        print()

        # 服务主循环
        while self.running:
            try:
                await self.service_loop()

            except Exception as e:
                logger.error(f"服务循环错误: {e}")
                await asyncio.sleep(5)

    async def service_loop(self):
        """服务主循环"""
        # 每60秒打印一次状态
        await asyncio.sleep(60)

        # 计算运行时间
        uptime = datetime.now() - self.start_time
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        self.print_info(f"运行中... | 运行时长: {uptime.days}天 {hours}小时 {minutes}分钟 {seconds}秒")

    async def stop(self):
        """停止服务"""
        self.running = False
        self.print_warning("正在停止小宸服务...")
        self.print_orange("星河箭矢，下次再会！🏹✨")

    def signal_handler(self, signum, frame) -> None:
        """信号处理器"""
        logger.info(f"收到信号 {signum}，准备关闭服务...")
        self.running = False


async def main():
    """主函数"""
    service = XiaochenService()

    # 注册信号处理器
    signal.signal(signal.SIGINT, service.signal_handler)
    signal.signal(signal.SIGTERM, service.signal_handler)

    try:
        await service.start()
    except KeyboardInterrupt:
        await service.stop()
    except Exception as e:
        logger.error(f"服务异常: {e}")
        await service.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n服务已停止")
        sys.exit(0)
