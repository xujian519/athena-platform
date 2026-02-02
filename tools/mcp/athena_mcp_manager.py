#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena MCP管理器 - 统一管理所有MCP服务器
Athena MCP Manager - Unified Management for All MCP Servers

控制者: 小诺 & Athena
创建时间: 2025年12月11日
版本: 1.0.0
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

class MCPServerStatus(Enum):
    """MCP服务器状态枚举"""
    RUNNING = 'running'
    STOPPED = 'stopped'
    ERROR = 'error'
    UNKNOWN = 'unknown'

@dataclass
class MCPServerConfig:
    """MCP服务器配置"""
    name: str
    path: str
    command: str
    args: List[str]
    env: Dict[str, str]
    description: str
    capabilities: List[str]
    status: MCPServerStatus = MCPServerStatus.UNKNOWN
    process: subprocess.Popen | None = None

@dataclass
class MCPTool:
    """MCP工具定义"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    server: str

class AthenaMCPManager:
    """Athena MCP管理器 - 统一管理所有MCP服务器"""

    def __init__(self, config_path: str | None = None):
        """
        初始化MCP管理器

        Args:
            config_path: 配置文件路径
        """
        self.platform_root = Path('/Users/xujian/Athena工作平台')
        self.config_path = config_path or (self.platform_root / 'config' / 'mcp_config.json')
        self.controllers = ['小诺', 'Athena']
        self.version = '1.0.0'

        # MCP服务器配置
        self.servers: Dict[str, MCPServerConfig] = {}

        # 初始化服务器配置
        self._initialize_servers()

        # 加载配置
        self._load_config()

    def _initialize_servers(self):
        """初始化所有MCP服务器配置"""

        # Jina AI MCP服务器
        self.servers['jina-ai'] = MCPServerConfig(
            name='jina-ai',
            path=str(self.platform_root / 'mcp-servers' / 'jina-ai-mcp-server'),
            command='node',
            args=['index.js'],
            env={
                'JINA_API_KEY': 'jina_105bd89b0a3b4ac79e5879d7177ed5e7vKow46ADR-Kvz7GRheO8Sj8pGEL4',
                'NODE_PATH': str(self.platform_root / 'mcp-servers' / 'jina-ai-mcp-server' / 'node_modules')
            },
            description='Jina AI MCP工具服务器 - 提供Web读取、搜索、向量化和重排序等AI功能',
            capabilities=['read_web', 'web_search', 'vector_search', 'rerank', 'embedding', 'get_system_info']
        )

        # Bing中文搜索MCP服务器
        self.servers['bing-cn-search'] = MCPServerConfig(
            name='bing-cn-search',
            path=str(self.platform_root / 'mcp-servers' / 'bing-cn-mcp-server'),
            command='node',
            args=['index.js'],
            env={},
            description='Bing中文搜索MCP服务器 - 专门优化的中文搜索引擎，无需API密钥',
            capabilities=['search_chinese', 'fetch_web_content', 'search_images', 'search_news', 'get_system_info']
        )

        # 高德地图MCP服务器
        self.servers['amap-mcp'] = MCPServerConfig(
            name='amap-mcp',
            path=str(self.platform_root / 'amap-mcp-server'),
            command='python3',
            args=['run_server.py'],
            env={
                'AMAP_API_KEY': '4c98d375577d64cfce0d4d0dfee25fb9',
                'PYTHONPATH': str(self.platform_root / 'amap-mcp-server')
            },
            description='高德地图MCP服务器 - 提供地理位置、路径规划、POI搜索等功能',
            capabilities=['geocode', 'reverse_geocode', 'search_poi', 'search_text', 'search_around', 'direction_driving', 'direction_walking', 'direction_bicycling', 'direction_transit', 'distance', 'get_district', 'get_weather']
        )

        # 学术搜索MCP服务器 (待集成)
        self.servers['academic-search'] = MCPServerConfig(
            name='academic-search',
            path=str(self.platform_root / 'mcp-servers' / 'academic-search-mcp-server'),
            command='python',
            args=['-m', 'academic_search_mcp'],
            env={},
            description='学术搜索MCP服务器 - 提供学术论文和期刊搜索功能',
            capabilities=['search_papers', 'get_paper_metadata', 'search_by_author', 'get_citations']
        )

    def _load_config(self):
        """加载配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 更新服务器配置
                    for name, server_config in config.get('servers', {}).items():
                        if name in self.servers:
                            self.servers[name].env.update(server_config.get('env', {}))
                            self.servers[name].status = MCPServerStatus(server_config.get('status', 'unknown'))
        except Exception as e:
            logger.warning(f"加载MCP配置文件失败: {e}")

    def _save_config(self):
        """保存配置文件"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            config = {
                'version': self.version,
                'controllers': self.controllers,
                'servers': {
                    name: {
                        'env': server.env,
                        'status': server.status.value,
                        'description': server.description,
                        'capabilities': server.capabilities
                    }
                    for name, server in self.servers.items()
                },
                'last_updated': datetime.now().isoformat()
            }

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存MCP配置文件失败: {e}")

    async def start_server(self, server_name: str) -> bool:
        """
        启动指定的MCP服务器

        Args:
            server_name: 服务器名称

        Returns:
            是否启动成功
        """
        if server_name not in self.servers:
            logger.error(f"未找到MCP服务器: {server_name}")
            return False

        server = self.servers[server_name]

        if server.status == MCPServerStatus.RUNNING:
            logger.info(f"MCP服务器 {server_name} 已在运行")
            return True

        try:
            # 设置环境变量
            env = os.environ.copy()
            env.update(server.env)

            # 启动服务器进程
            server.process = subprocess.Popen(
                [server.command] + server.args,
                cwd=server.path,
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # 等待服务器启动
            await asyncio.sleep(2)

            # 检查进程状态
            if server.process.poll() is None:
                server.status = MCPServerStatus.RUNNING
                logger.info(f"MCP服务器 {server_name} 启动成功")
                self._save_config()
                return True
            else:
                server.status = MCPServerStatus.ERROR
                logger.error(f"MCP服务器 {server_name} 启动失败")
                return False

        except Exception as e:
            server.status = MCPServerStatus.ERROR
            logger.error(f"启动MCP服务器 {server_name} 时发生错误: {e}")
            return False

    async def stop_server(self, server_name: str) -> bool:
        """
        停止指定的MCP服务器

        Args:
            server_name: 服务器名称

        Returns:
            是否停止成功
        """
        if server_name not in self.servers:
            logger.error(f"未找到MCP服务器: {server_name}")
            return False

        server = self.servers[server_name]

        if server.process is None:
            logger.info(f"MCP服务器 {server_name} 未运行")
            server.status = MCPServerStatus.STOPPED
            return True

        try:
            server.process.terminate()
            await asyncio.sleep(2)

            if server.process.poll() is None:
                server.process.kill()
                await asyncio.sleep(1)

            server.process = None
            server.status = MCPServerStatus.STOPPED
            logger.info(f"MCP服务器 {server_name} 已停止")
            self._save_config()
            return True

        except Exception as e:
            logger.error(f"停止MCP服务器 {server_name} 时发生错误: {e}")
            return False

    async def restart_server(self, server_name: str) -> bool:
        """
        重启指定的MCP服务器

        Args:
            server_name: 服务器名称

        Returns:
            是否重启成功
        """
        logger.info(f"重启MCP服务器: {server_name}")
        await self.stop_server(server_name)
        return await self.start_server(server_name)

    async def get_server_status(self, server_name: str) -> Dict[str, Any]:
        """
        获取服务器状态信息

        Args:
            server_name: 服务器名称

        Returns:
            服务器状态信息
        """
        if server_name not in self.servers:
            return {'error': f"未找到MCP服务器: {server_name}"}

        server = self.servers[server_name]

        status_info = {
            'name': server.name,
            'description': server.description,
            'status': server.status.value,
            'capabilities': server.capabilities,
            'path': server.path,
            'process_id': server.process.pid if server.process else None
        }

        # 如果服务器正在运行，尝试获取工具列表
        if server.status == MCPServerStatus.RUNNING and server.process:
            try:
                tools = await self.list_tools(server_name)
                status_info['available_tools'] = tools
            except Exception as e:
                status_info['tools_error'] = str(e)

        return status_info

    async def list_tools(self, server_name: str) -> List[MCPTool]:
        """
        列出指定服务器的所有工具

        Args:
            server_name: 服务器名称

        Returns:
            工具列表
        """
        if server_name not in self.servers:
            raise ValueError(f"未找到MCP服务器: {server_name}")

        server = self.servers[server_name]

        if server.status != MCPServerStatus.RUNNING or not server.process:
            raise RuntimeError(f"MCP服务器 {server_name} 未运行")

        try:
            # 发送工具列表请求
            request = {
                'jsonrpc': '2.0',
                'method': 'tools/list',
                'params': {},
                'id': 1
            }

            server.process.stdin.write(json.dumps(request) + "\n")
            server.process.stdin.flush()

            # 读取响应
            response_line = server.process.stdout.readline()
            response = json.loads(response_line.strip())

            tools = []
            for tool_data in response.get('result', {}).get('tools', []):
                tool = MCPTool(
                    name=tool_data['name'],
                    description=tool_data['description'],
                    input_schema=tool_data['input_schema'],
                    server=server_name
                )
                tools.append(tool)

            return tools

        except Exception as e:
            logger.error(f"获取服务器 {server_name} 工具列表失败: {e}")
            raise

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用指定服务器的工具

        Args:
            server_name: 服务器名称
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        if server_name not in self.servers:
            raise ValueError(f"未找到MCP服务器: {server_name}")

        server = self.servers[server_name]

        if server.status != MCPServerStatus.RUNNING or not server.process:
            raise RuntimeError(f"MCP服务器 {server_name} 未运行")

        try:
            # 发送工具调用请求
            request = {
                'jsonrpc': '2.0',
                'method': 'tools/call',
                'params': {
                    'name': tool_name,
                    'arguments': arguments
                },
                'id': 2
            }

            server.process.stdin.write(json.dumps(request) + "\n")
            server.process.stdin.flush()

            # 读取响应
            response_line = server.process.stdout.readline()
            response = json.loads(response_line.strip())

            if 'error' in response:
                raise RuntimeError(f"工具调用失败: {response['error']}")

            return response.get('result', {})

        except Exception as e:
            logger.error(f"调用工具 {tool_name} 失败: {e}")
            raise

    async def get_all_status(self) -> Dict[str, Any]:
        """
        获取所有MCP服务器的状态

        Returns:
            所有服务器状态信息
        """
        status_report = {
            'manager_version': self.version,
            'controllers': self.controllers,
            'timestamp': datetime.now().isoformat(),
            'servers': {}
        }

        for server_name in self.servers:
            try:
                status_report['servers'][server_name] = await self.get_server_status(server_name)
            except Exception as e:
                status_report['servers'][server_name] = {
                    'error': str(e),
                    'status': 'unknown'
                }

        return status_report

    async def start_all_servers(self) -> Dict[str, bool]:
        """
        启动所有可用的MCP服务器

        Returns:
            启动结果字典
        """
        results = {}

        for server_name in self.servers:
            if server_name == 'jina-ai':  # 优先启动Jina AI
                results[server_name] = await self.start_server(server_name)
                await asyncio.sleep(1)  # 等待启动完成

        # 启动其他服务器
        for server_name in self.servers:
            if server_name != 'jina-ai':
                results[server_name] = await self.start_server(server_name)
                await asyncio.sleep(0.5)

        return results

    async def stop_all_servers(self) -> Dict[str, bool]:
        """
        停止所有MCP服务器

        Returns:
            停止结果字典
        """
        results = {}

        for server_name in self.servers:
            results[server_name] = await self.stop_server(server_name)

        return results

    def get_server_info(self, server_name: str) -> MCPServerConfig | None:
        """
        获取服务器配置信息

        Args:
            server_name: 服务器名称

        Returns:
            服务器配置信息
        """
        return self.servers.get(server_name)

    def list_all_servers(self) -> List[str]:
        """
        列出所有可用的服务器名称

        Returns:
            服务器名称列表
        """
        return list(self.servers.keys())


# 便捷函数
async def get_mcp_manager() -> AthenaMCPManager:
    """获取MCP管理器实例"""
    return AthenaMCPManager()

async def start_jina_ai_tools() -> AthenaMCPManager:
    """启动Jina AI工具服务器"""
    manager = await get_mcp_manager()
    success = await manager.start_server('jina-ai')
    if success:
        logger.info('Jina AI MCP服务器启动成功')
    else:
        logger.error('Jina AI MCP服务器启动失败')
    return manager