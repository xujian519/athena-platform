"""
iMessage 客户端 (使用 imsg 工具)
通过 steipete/imsg 工具与 iMessage 通信
支持发送和接收消息
"""

import asyncio
import subprocess
import json
import logging
from typing import Optional, Callable, Any, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class IMessageMessage:
    """iMessage 消息数据结构"""
    chat_id: str
    handle: str  # 发件人
    text: str
    timestamp: float
    is_from_me: bool
    group_id: Optional[str] = None


@dataclass
class RPCResponse:
    """RPC 响应数据结构"""
    success: bool
    data: Any = None
    error: Optional[str] = None


class IMessageClient:
    """
    iMessage 客户端

    通过 imsg 工具与 iMessage 通信
    支持发送和接收消息
    """

    def __init__(
        self,
        cli_path: str = None,
        db_path: str = None,
        max_message_length: int = 4000
    ):
        """
        初始化 iMessage 客户端

        Args:
            cli_path: imsg 命令路径（默认 ~/.local/bin/imsg）
            db_path: 可选的自定义数据库路径
            max_message_length: 最大消息长度
        """
        self.cli_path = cli_path or "~/.local/bin/imsg"
        self.db_path = db_path
        self.max_message_length = max_message_length
        self.message_callback: Optional[Callable[[IMessageMessage], None]] = None
        self._running = False
        self._watch_process: Optional[asyncio.subprocess.Process] = None
        self._rpc_process: Optional[asyncio.subprocess.Process] = None
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._request_id = 0

    async def start(self) -> None:
        """启动客户端（启动 watch 监听）"""
        if self._running:
            return

        self._running = True
        logger.info("iMessage client started (using imsg tool)")

        # 启动 watch 进程来监听新消息
        await self._start_watch()

    async def stop(self) -> None:
        """停止客户端"""
        if not self._running:
            return

        self._running = False

        # 停止 watch 进程
        if self._watch_process:
            self._watch_process.terminate()
            try:
                await asyncio.wait_for(self._watch_process.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                self._watch_process.kill()
            self._watch_process = None

        # 停止 RPC 进程
        if self._rpc_process:
            self._rpc_process.terminate()
            try:
                await asyncio.wait_for(self._rpc_process.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                self._rpc_process.kill()
            self._rpc_process = None

        logger.info("iMessage client stopped")

    async def _start_watch(self) -> None:
        """启动 watch 进程监听新消息"""
        args = ["watch", "--json"]
        if self.db_path:
            args.extend(["--db", self.db_path])

        cmd = f"{self.cli_path} " + " ".join(args)

        try:
            self._watch_process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # 启动读取输出的任务
            asyncio.create_task(self._read_watch_output())

            logger.info("Watch process started")

        except Exception as e:
            logger.error(f"Failed to start watch process: {e}")

    async def _read_watch_output(self) -> None:
        """读取 watch 进程的输出"""
        if not self._watch_process or not self._watch_process.stdout:
            return

        try:
            while self._running:
                line = await self._watch_process.stdout.readline()
                if not line:
                    break

                line_str = line.decode('utf-8').strip()
                if line_str:
                    await self._handle_watch_message(line_str)

        except Exception as e:
            logger.error(f"Error reading watch output: {e}")

    async def _handle_watch_message(self, line: str) -> None:
        """处理 watch 接收到的消息"""
        try:
            data = json.loads(line)

            # 解析消息
            message = IMessageMessage(
                chat_id=str(data.get("chat_id", "")),
                handle=data.get("sender", ""),
                text=data.get("text", ""),
                timestamp=data.get("date", 0) / 1000,  # 转换为秒
                is_from_me=data.get("is_from_me", False)
            )

            # 调用回调
            if self.message_callback and not message.is_from_me:
                self.message_callback(message)

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse watch message: {e}")
        except Exception as e:
            logger.error(f"Error handling watch message: {e}")

    async def send_message(
        self,
        chat_id: str,
        text: str,
        max_bytes: Optional[int] = None
    ) -> RPCResponse:
        """
        发送 iMessage

        Args:
            chat_id: 目标聊天ID（电话号码或邮箱）
            text: 消息文本
            max_bytes: 最大字节数（已弃用）

        Returns:
            RPCResponse 对象
        """
        try:
            # 截断过长的消息
            if len(text) > self.max_message_length:
                text = text[:self.max_message_length] + "..."

            # 使用 send 命令
            args = ["send", chat_id, text]
            cmd = f"{self.cli_path} " + " ".join([f'"{arg}"' if ' ' in arg else arg for arg in args])

            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode('utf-8').strip()
                return RPCResponse(success=False, error=error_msg)

            logger.info(f"Message sent to {chat_id}")
            return RPCResponse(success=True, data={"sent": True})

        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return RPCResponse(success=False, error=str(e))

    async def get_chat_id(self, handle: str) -> RPCResponse:
        """
        获取联系人对应的聊天ID

        Args:
            handle: 联系人标识（电话号码或邮箱）

        Returns:
            RPCResponse 对象，包含 chat_id
        """
        # 对于 iMessage，chat_id 通常就是 handle 本身
        # 但我们可以通过 chats 命令来验证
        try:
            cmd = f"{self.cli_path} chats --json"
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()
            output = stdout.decode('utf-8')

            # 查找匹配的聊天
            for line in output.strip().split('\n'):
                if line:
                    try:
                        chat = json.loads(line)
                        if chat.get("identifier") == handle:
                            return RPCResponse(success=True, data=str(chat.get("id")))
                    except json.JSONDecodeError:
                        continue

            # 如果没找到，返回 handle 本身
            return RPCResponse(success=True, data=handle)

        except Exception as e:
            logger.error(f"Failed to get chat ID: {e}")
            return RPCResponse(success=True, data=handle)

    async def list_chats(self) -> RPCResponse:
        """列出所有聊天"""
        try:
            cmd = f"{self.cli_path} chats --json"
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()
            output = stdout.decode('utf-8')

            # 解析 JSON 输出
            chats = []
            for line in output.strip().split('\n'):
                if line:
                    try:
                        chats.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

            return RPCResponse(success=True, data=chats)

        except Exception as e:
            logger.error(f"Failed to list chats: {e}")
            return RPCResponse(success=False, error=str(e))

    def on_message(self, callback: Callable[[IMessageMessage], None]) -> None:
        """
        注册消息回调

        Args:
            callback: 消息回调函数
        """
        self.message_callback = callback


async def test_imessage_client():
    """测试 iMessage 客户端"""
    client = IMessageClient()

    try:
        await client.start()

        # 测试列出聊天
        chats = await client.list_chats()
        print(f"Total chats: {len(chats.data) if chats.data else 0}")

        # 测试发送消息
        # result = await client.send_message("+8615662710999", "测试消息")
        # print(f"Send result: {result.success}")

        # 保持运行以监听新消息
        print("Listening for messages... (Ctrl+C to stop)")
        await asyncio.sleep(30)

    finally:
        await client.stop()


if __name__ == "__main__":
    asyncio.run(test_imessage_client())
