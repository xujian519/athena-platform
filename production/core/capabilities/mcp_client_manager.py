#!/usr/bin/env python3
"""
MCP客户端管理器
MCP Client Manager - 真实MCP服务器连接

版本: 1.0.0
功能:
- 管理MCP服务器连接池
- 支持stdio类型的MCP服务器
- 提供真实的MCP方法调用
- 连接复用和自动清理
"""

from __future__ import annotations
import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """MCP服务器配置"""

    name: str
    server_type: str  # "stdio"
    command: str
    args: list[str]
    cwd: str
    env: dict[str, str] = field(default_factory=dict)
    capabilities: list[str] = field(default_factory=list)
    enabled: bool = True
    description: str = ""


@dataclass
class MCPConnection:
    """MCP连接"""

    server_name: str
    process: asyncio.subprocess.Process = None
    stdin: asyncio.StreamWriter = None
    stdout: asyncio.StreamReader = None
    stderr: asyncio.StreamReader = None
    created_at: datetime = field(default_factory=datetime.now)
    call_count: int = 0
    is_active: bool = True


class MCPClientManager:
    """
    MCP客户端管理器

    管理与MCP服务器的stdio连接,支持真实的MCP协议调用
    """

    def __init__(
        self, config_path: str | None = None, connection_timeout: int = 30, max_connections: int = 10
    ):
        """
        初始化MCP客户端管理器

        Args:
            config_path: MCP配置文件路径
            connection_timeout: 连接超时时间
            max_connections: 最大连接数
        """
        self.config_path = config_path or "/Users/xujian/Athena工作平台/config/mcp_servers.yml"
        self.connection_timeout = connection_timeout
        self.max_connections = max_connections

        # 服务器配置
        self.servers: dict[str, MCPServerConfig] = {}
        self.connections: dict[str, MCPConnection] = {}

        # 加载配置
        self._load_config()

        logger.info(f"✅ MCP客户端管理器初始化完成({len(self.servers)}个服务器)")

    def _load_config(self):
        """加载MCP服务器配置"""
        try:
            import yaml

            with open(self.config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 解析服务器配置
            for server_id, server_config in config.get("servers", {}).items():
                if not server_config.get("enabled", True):
                    continue

                self.servers[server_id] = MCPServerConfig(
                    name=server_config.get("name", server_id),
                    server_type=server_config.get("type", "stdio"),
                    command=server_config.get("command", "python"),
                    args=server_config.get("args", []),
                    cwd=server_config.get("cwd", ""),
                    env=server_config.get("env", {}),
                    capabilities=server_config.get("capabilities", []),
                    enabled=server_config.get("enabled", True),
                    description=server_config.get("description", ""),
                )

            logger.info(f"  已加载服务器: {list(self.servers.keys())}")

        except Exception as e:
            logger.error(f"❌ 加载MCP配置失败: {e}")

    async def get_connection(self, server_id: str) -> MCPConnection:
        """
        获取或创建MCP服务器连接

        Args:
            server_id: 服务器ID

        Returns:
            MCPConnection对象
        """
        if server_id not in self.servers:
            raise ValueError(f"未配置的服务器: {server_id}")

        # 复用现有连接
        if server_id in self.connections:
            conn = self.connections[server_id]
            if conn.is_active and conn.process and not conn.process.returncode:
                conn.call_count += 1
                return conn
            else:
                # 连接已失效,清理
                await self._close_connection(server_id)

        # 创建新连接
        server_config = self.servers[server_id]
        connection = await self._create_connection(server_config)
        self.connections[server_id] = connection

        return connection

    async def _create_connection(self, config: MCPServerConfig) -> MCPConnection:
        """
        创建到MCP服务器的stdio连接

        Args:
            config: 服务器配置

        Returns:
            MCPConnection对象
        """
        logger.info(f"🔌 创建MCP连接: {config.name}")

        try:
            # 构建环境变量
            env = dict(os.environ)
            env.update(config.env)

            # 创建子进程
            process = await asyncio.create_subprocess_exec(
                config.command,
                *config.args,
                cwd=config.cwd,
                env=env,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=1024 * 1024,  # 1MB buffer
            )

            connection = MCPConnection(
                server_name=config.name,
                process=process,
                stdin=process.stdin,
                stdout=process.stdout,
                stderr=process.stderr,
            )

            # 等待进程启动
            await asyncio.sleep(0.5)

            # 验证进程是否正常运行
            if process.returncode is not None:
                raise RuntimeError(f"MCP服务器启动失败,退出码: {process.returncode}")

            logger.info(f"✅ MCP连接创建成功: {config.name}")
            return connection

        except Exception as e:
            logger.error(f"❌ 创建MCP连接失败: {e}")
            if "process" in locals() and process:
                process.kill()
                await process.wait()
            raise

    async def call_method(
        self, server_id: str, method: str, params: dict[str, Any] | None = None, timeout: int = 30
    ) -> Any:
        """
        调用MCP服务器的方法

        Args:
            server_id: 服务器ID
            method: 方法名
            params: 参数字典
            timeout: 超时时间

        Returns:
            方法执行结果
        """
        if server_id not in self.servers:
            raise ValueError(f"未配置的服务器: {server_id}")

        connection = await self.get_connection(server_id)

        logger.info(f"📡 调用MCP方法: {server_id}.{method}")

        try:
            # 构建JSON-RPC请求
            request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}

            # 发送请求
            request_json = json.dumps(request) + "\n"
            connection.stdin.write(request_json.encode("utf-8"))
            await connection.stdin.drain()

            # 读取响应(带超时)
            response_line = await asyncio.wait_for(connection.stdout.readline(), timeout=timeout)

            if not response_line:
                raise RuntimeError("MCP服务器关闭了连接")

            response = json.loads(response_line.decode("utf-8"))

            # 检查错误
            if "error" in response:
                raise RuntimeError(f"MCP错误: {response['error']}")

            connection.call_count += 1

            logger.info(f"✅ MCP调用成功: {server_id}.{method}")
            return response.get("result")

        except asyncio.TimeoutError:
            logger.error(f"❌ MCP调用超时: {server_id}.{method}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"❌ MCP响应解析失败: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ MCP调用失败: {e}")
            # 标记连接为无效
            connection.is_active = False
            raise

    async def _close_connection(self, server_id: str):
        """关闭指定服务器的连接"""
        if server_id in self.connections:
            conn = self.connections[server_id]
            try:
                if conn.process:
                    conn.process.terminate()
                    await asyncio.wait_for(conn.process.wait(), timeout=5.0)
            except Exception as e:
                logger.warning(f"⚠️ 关闭连接失败: {e}")
                if conn.process:
                    conn.process.kill()

            del self.connections[server_id]

    async def close_all(self):
        """关闭所有MCP连接"""
        logger.info("🔌 关闭所有MCP连接...")

        server_ids = list(self.connections.keys())
        for server_id in server_ids:
            await self._close_connection(server_id)

        logger.info("✅ 所有MCP连接已关闭")

    def get_server_info(self, server_id: str) -> MCPServerConfig | None:
        """获取服务器配置信息"""
        return self.servers.get(server_id)

    def list_active_servers(self) -> list[str]:
        """列出所有活动服务器"""
        return [
            server_id
            for server_id, conn in self.connections.items()
            if conn.is_active and conn.process and conn.process.returncode is None
        ]

    def get_connection_stats(self) -> dict[str, Any]:
        """获取连接统计信息"""
        stats = {
            "total_servers": len(self.servers),
            "active_connections": len([c for c in self.connections.values() if c.is_active]),
            "total_calls": sum(c.call_count for c in self.connections.values()),
            "connections": {},
        }

        for server_id, conn in self.connections.items():
            stats["connections"][server_id] = {
                "is_active": conn.is_active,
                "call_count": conn.call_count,
                "uptime_seconds": (datetime.now() - conn.created_at).total_seconds(),
            }

        return stats


# 全局单例
_mcp_client_manager: MCPClientManager | None = None


def get_mcp_client_manager(
    config_path: str | None = None, connection_timeout: int = 30
) -> MCPClientManager:
    """
    获取MCP客户端管理器单例

    Args:
        config_path: 配置文件路径
        connection_timeout: 连接超时时间

    Returns:
        MCPClientManager实例
    """
    global _mcp_client_manager

    if _mcp_client_manager is None:
        _mcp_client_manager = MCPClientManager(
            config_path=config_path, connection_timeout=connection_timeout
        )

    return _mcp_client_manager


# 导入os(在顶部需要添加)
import os
