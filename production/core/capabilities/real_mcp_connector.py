#!/usr/bin/env python3
"""
真实MCP服务器连接器
Real MCP Server Connector

实现与实际MCP服务器的连接和通信
"""

from __future__ import annotations
import asyncio
import json
import logging
import os
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class RealMCPConnector:
    """真实MCP服务器连接器"""

    def __init__(self, config_path: str = "config/mcp_servers.yml"):
        """
        初始化MCP连接器

        Args:
            config_path: MCP配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.processes: dict[str, asyncio.subprocess.Process] = {}
        self.connections: dict[str, Any] = {}

        logger.info("✅ 真实MCP连接器初始化完成")

    def _load_config(self) -> dict[str, Any]:
        """加载MCP配置"""
        # 从项目根目录计算配置文件路径
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        config_file = os.path.join(project_root, self.config_path)

        try:
            with open(config_file, encoding="utf-8") as f:
                config = yaml.safe_load(f)
            logger.info(f"✅ MCP配置加载成功: {config_file}")
            return config
        except FileNotFoundError:
            logger.warning(f"⚠️  配置文件未找到: {config_file}")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"❌ 配置加载失败: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> dict[str, Any]:
        """获取默认配置"""
        return {
            "global": {"connection_timeout": 30, "request_timeout": 60, "max_retries": 3},
            "servers": {},
            "capability_mapping": {},
            "fallback": {"use_mock_data": True, "log_fallback_events": True},
        }

    async def start_server(self, server_name: str) -> bool:
        """
        启动MCP服务器

        Args:
            server_name: 服务器名称

        Returns:
            是否启动成功
        """
        if server_name not in self.config.get("servers", {}):
            logger.error(f"❌ 服务器配置不存在: {server_name}")
            return False

        server_config = self.config["servers"][server_name]

        if not server_config.get("enabled", False):
            logger.warning(f"⚠️  服务器未启用: {server_name}")
            return False

        try:
            # 根据服务器类型启动
            if server_config["type"] == "stdio":
                return await self._start_stdio_server(server_name, server_config)
            elif server_config["type"] == "node":
                return await self._start_node_server(server_name, server_config)
            else:
                logger.error(f"❌ 不支持的服务器类型: {server_config['type']}")
                return False

        except Exception as e:
            logger.error(f"❌ 启动服务器失败 [{server_name}]: {e}")
            return False

    async def _start_stdio_server(self, server_name: str, config: dict[str, Any]) -> bool:
        """启动stdio类型的MCP服务器"""
        try:
            # 构建命令
            cmd = [config["command"], *config.get("args", [])]
            cwd = config.get("cwd", os.getcwd())

            logger.info(f"🚀 启动stdio服务器 [{server_name}]: {' '.join(cmd)}")

            # 准备环境变量(合并配置的环境变量)
            env = os.environ.copy()
            if "env" in config:
                env.update(config["env"])

            # 启动子进程
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            self.processes[server_name] = process
            logger.info(f"✅ stdio服务器启动成功 [{server_name}] (PID: {process.pid})")
            return True

        except Exception as e:
            logger.error(f"❌ stdio服务器启动失败 [{server_name}]: {e}")
            return False

    async def _start_node_server(self, server_name: str, config: dict[str, Any]) -> bool:
        """启动Node.js类型的MCP服务器"""
        try:
            # 检查Node.js是否安装
            proc = await asyncio.create_subprocess_exec(
                "node", "--version", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()

            if proc.returncode != 0:
                logger.error("❌ Node.js未安装")
                return False

            logger.info(f"✅ Node.js版本: {stdout.decode().strip()}")

            # 构建命令
            cmd = [config["command"], *config.get("args", [])]
            cwd = config.get("cwd", os.getcwd())

            logger.info(f"🚀 启动Node服务器 [{server_name}]: {' '.join(cmd)}")

            # 准备环境变量(合并配置的环境变量)
            env = os.environ.copy()
            if "env" in config:
                env.update(config["env"])

            # 启动子进程
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            self.processes[server_name] = process
            logger.info(f"✅ Node服务器启动成功 [{server_name}] (PID: {process.pid})")
            return True

        except Exception as e:
            logger.error(f"❌ Node服务器启动失败 [{server_name}]: {e}")
            return False

    async def invoke_capability(
        self, capability_id: str, parameters: dict[str, Any], timeout: int = 30
    ) -> dict[str, Any]:
        """
        调用MCP能力

        Args:
            capability_id: 能力ID
            parameters: 调用参数
            timeout: 超时时间

        Returns:
            调用结果
        """
        # 获取能力映射
        capability_mapping = self.config.get("capability_mapping", {})
        if capability_id not in capability_mapping:
            logger.warning(f"⚠️  能力未配置映射: {capability_id}")
            return await self._fallback_to_mock(capability_id, parameters)

        mapping = capability_mapping[capability_id]
        server_name = mapping["server"]
        method = mapping["method"]

        # 检查服务器是否启动
        if server_name not in self.processes:
            logger.info(f"🔄 启动服务器: {server_name}")
            success = await self.start_server(server_name)
            if not success:
                return await self._fallback_to_mock(capability_id, parameters)

            # 等待服务器启动
            await asyncio.sleep(2)

        # 调用能力
        try:
            return await self._call_mcp_method(server_name, method, parameters, timeout)
        except Exception as e:
            logger.error(f"❌ MCP调用失败: {e}")
            return await self._fallback_to_mock(capability_id, parameters)

    async def _call_mcp_method(
        self, server_name: str, method: str, parameters: dict[str, Any], timeout: int
    ) -> dict[str, Any]:
        """调用MCP方法"""
        process = self.processes.get(server_name)
        if not process:
            raise Exception(f"服务器未启动: {server_name}")

        # 构建JSON-RPC请求
        request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": parameters}

        # 发送请求
        request_json = json.dumps(request) + "\n"
        process.stdin.write(request_json.encode())
        await process.stdin.drain()

        # 读取响应(带超时)
        try:
            response_line = await asyncio.wait_for(process.stdout.readline(), timeout=timeout)
            response = json.loads(response_line.decode())

            if "error" in response:
                raise Exception(response["error"])

            return response.get("result", {})

        except asyncio.TimeoutError:
            raise Exception(f"调用超时: {timeout}秒") from None

    async def _fallback_to_mock(
        self, capability_id: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """回退到模拟数据"""
        fallback_config = self.config.get("fallback", {})

        if fallback_config.get("log_fallback_events", True):
            logger.warning(f"⚠️  回退到模拟数据: {capability_id}")

        if not fallback_config.get("use_mock_data", True):
            return {"success": False, "error": "MCP服务器不可用且模拟数据已禁用"}

        # 返回模拟数据
        return await self._generate_mock_response(capability_id, parameters)

    async def _generate_mock_response(
        self, capability_id: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """生成模拟响应"""
        if "patent_search" in capability_id:
            return {
                "results": [
                    {
                        "title": f"专利示例-{parameters.get('query', '未知')}",
                        "application_number": "CN202310000000",
                        "abstract": "这是一项关于...的专利技术...",
                        "applicant": "某科技公司",
                    }
                ]
                * parameters.get("limit", 3),
                "total": 10,
                "query": parameters.get("query", ""),
            }
        elif "academic_search" in capability_id:
            return {
                "results": [
                    {
                        "title": f"论文示例-{parameters.get('query', '未知')}",
                        "authors": ["张三", "李四"],
                        "year": 2023,
                        "abstract": "本文研究了...的问题...",
                        "citation_count": 15,
                    }
                ]
                * parameters.get("limit", 3),
                "total": 5,
            }
        else:
            return {
                "success": True,
                "message": f"模拟调用成功: {capability_id}",
                "capability_id": capability_id,
                "parameters": parameters,
            }

    async def stop_server(self, server_name: str):
        """停止MCP服务器"""
        if server_name in self.processes:
            process = self.processes[server_name]
            process.terminate()
            await process.wait()
            del self.processes[server_name]
            logger.info(f"🛑 服务器已停止: {server_name}")

    async def stop_all_servers(self):
        """停止所有MCP服务器"""
        for server_name in list(self.processes.keys()):
            await self.stop_server(server_name)

    async def get_server_status(self) -> dict[str, Any]:
        """获取服务器状态"""
        status = {}
        for server_name, process in self.processes.items():
            status[server_name] = {"running": process.returncode is None, "pid": process.pid}
        return status

    def list_available_capabilities(self) -> list[str]:
        """列出可用能力列表"""
        mapping = self.config.get("capability_mapping", {})
        return list(mapping.keys())

    def list_enabled_servers(self) -> list[str]:
        """列出启用的服务器"""
        servers = self.config.get("servers", {})
        return [name for name, config in servers.items() if config.get("enabled", False)]


# 单例模式
_mcp_connector: RealMCPConnector | None = None


def get_mcp_connector() -> RealMCPConnector:
    """获取MCP连接器单例"""
    global _mcp_connector
    if _mcp_connector is None:
        _mcp_connector = RealMCPConnector()
    return _mcp_connector
