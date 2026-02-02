"""
Athena iMessage Remote Control - 主程序
通过 iMessage 远程控制 Athena 工作平台
"""

import asyncio
import signal
import sys
import logging
from pathlib import Path
from typing import Optional

import yaml

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.imessage_client import IMessageClient, IMessageMessage
from core.command_parser import CommandParser
from core.command_router import CommandRouter
from agents.xiaonuo_agent import XiaonuoAgent
from agents.athena_agent import AthenaAgent
from obsidian.writer import ObsidianWriter
from feedback.smart_feedback import SmartFeedbackGenerator, FeedbackConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/xujian/Athena工作平台/logs/imessage_remote.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class IMessageRemoteController:
    """
    iMessage 远程控制器

    整合所有组件，实现完整的远程控制功能
    """

    def __init__(self, config_path: str = None):
        """
        初始化控制器

        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        self.config = self._load_config(config_path)

        # 创建组件
        self.imessage_client = self._create_imessage_client()
        self.command_parser = CommandParser()
        self.obsidian_writer = self._create_obsidian_writer()
        self.feedback_generator = self._create_feedback_generator()

        # 创建智能体
        self.xiaonuo_agent = XiaonuoAgent(
            self.config["agents"]["xiaonuo"]
        )
        self.athena_agent = AthenaAgent(
            self.config["agents"]["athena"]
        )

        # 创建命令路由器
        self.command_router = CommandRouter(
            self.imessage_client,
            self.xiaonuo_agent,
            self.athena_agent
        )

        # 控制标志
        self._running = False
        self._shutdown_event = asyncio.Event()

        # 注册信号处理
        self._setup_signal_handlers()

    def _load_config(self, config_path: str = None) -> dict:
        """
        加载配置文件

        Args:
            config_path: 配置文件路径

        Returns:
            配置字典
        """
        if config_path is None:
            config_path = "/Users/xujian/Athena工作平台/imessage-remote/config/config.yaml"

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        return config

    def _create_imessage_client(self) -> IMessageClient:
        """创建 iMessage 客户端"""
        imsg_config = self.config["imessage"]["rpc"]
        return IMessageClient(
            cli_path=imsg_config.get("cli_path", "imsg"),
            db_path=imsg_config.get("db_path"),
            timeout_ms=imsg_config.get("timeout_ms", 10000)
        )

    def _create_obsidian_writer(self) -> ObsidianWriter:
        """创建 Obsidian 写入器"""
        obsidian_config = self.config["obsidian"]
        return ObsidianWriter(
            vault_path=obsidian_config["vault_path"],
            organize_by=obsidian_config.get("organize_by", "task_type")
        )

    def _create_feedback_generator(self) -> SmartFeedbackGenerator:
        """创建反馈生成器"""
        feedback_config = self.config.get("feedback", {})
        config = FeedbackConfig(
            mode=feedback_config.get("mode", "smart"),
            summary_max_length=feedback_config.get("summary_max_length", 500),
            include_file_links=feedback_config.get("include_file_links", True),
            include_suggestions=feedback_config.get("include_suggestions", True),
            smart_thresholds=feedback_config.get("smart_thresholds")
        )
        return SmartFeedbackGenerator(config)

    def _setup_signal_handlers(self):
        """设置信号处理器"""
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda s, f: self._signal_handler(s, f))

    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"Received signal {signum}, shutting down...")
        self._shutdown_event.set()

    async def start(self):
        """启动控制器"""
        if self._running:
            return

        logger.info("Starting Athena iMessage Remote Controller...")

        try:
            # 启动 iMessage 客户端
            await self.imessage_client.start()

            # 注册消息回调
            self.imessage_client.on_message(self._handle_message)

            self._running = True
            logger.info("Controller started successfully")

            # 等待关闭信号
            await self._shutdown_event.wait()

        except Exception as e:
            logger.error(f"Failed to start controller: {e}")
            raise

    async def stop(self):
        """停止控制器"""
        if not self._running:
            return

        logger.info("Stopping controller...")

        try:
            # 停止 iMessage 客户端
            await self.imessage_client.stop()

            self._running = False
            logger.info("Controller stopped")

        except Exception as e:
            logger.error(f"Error stopping controller: {e}")

    async def _handle_message(self, message: IMessageMessage):
        """
        处理接收到的消息

        Args:
            message: iMessage 消息对象
        """
        # 忽略自己发送的消息
        if message.is_from_me:
            return

        # 安全验证：检查发件人是否在白名单中
        if not self._is_allowed_sender(message.handle):
            logger.warning(f"Message from unauthorized sender: {message.handle}")
            return

        logger.info(f"Received message from {message.handle}: {message.text[:50]}...")

        try:
            # 1. 解析命令
            parsed_command = self.command_parser.parse(message.text)
            logger.info(f"Parsed command: agent={parsed_command.agent.value}, "
                       f"task_type={parsed_command.task_type.value}, "
                       f"confidence={parsed_command.confidence:.2f}")

            # 2. 路由命令到智能体并执行
            result = await self.command_router.route_command(
                parsed_command,
                message.handle
            )

            # 3. 写入详情到 Obsidian
            obsidian_file = None
            if result.status.value == "completed":
                obsidian_file = await self.obsidian_writer.write_result(
                    result,
                    message.text
                )
                logger.info(f"Written to Obsidian: {obsidian_file}")

            # 4. 生成反馈消息
            feedback = self.feedback_generator.generate(result, obsidian_file)

            # 5. 发送反馈到 iMessage
            await self._send_feedback(message.handle, feedback)

            logger.info(f"Task {result.task_id} completed and feedback sent")

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            # 发送错误提示
            await self._send_feedback(
                message.handle,
                f"❌ 处理失败：{str(e)}"
            )

    def _is_allowed_sender(self, handle: str) -> bool:
        """
        检查发件人是否在白名单中

        Args:
            handle: 发件人标识

        Returns:
            是否允许
        """
        allowed_senders = self.config["imessage"].get("allowed_senders", [])
        return handle in allowed_senders

    async def _send_feedback(self, sender_handle: str, feedback: str):
        """
        发送反馈消息

        Args:
            sender_handle: 收件人标识
            feedback: 反馈消息
        """
        try:
            # 获取聊天ID
            chat_id = await self.imessage_client.get_chat_id(sender_handle)

            if chat_id.data:
                await self.imessage_client.send_message(
                    chat_id.data,
                    feedback
                )
            else:
                # 如果 get_chat_id 失败，尝试直接使用 handle
                await self.imessage_client.send_message(
                    sender_handle,
                    feedback
                )

            logger.info(f"Feedback sent to {sender_handle}")

        except Exception as e:
            logger.error(f"Failed to send feedback: {e}")


async def main():
    """主函数"""
    controller = None

    try:
        # 创建并启动控制器
        controller = IMessageRemoteController()
        await controller.start()

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        if controller:
            await controller.stop()


if __name__ == "__main__":
    # 开发模式参数
    if "--dev" in sys.argv:
        logger.setLevel(logging.DEBUG)
        logger.info("Running in development mode")

    # 守护进程模式参数
    if "--daemon" in sys.argv:
        # TODO: 实现守护进程模式
        logger.info("Running in daemon mode")

    asyncio.run(main())
