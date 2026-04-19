"""
MCP服务器主入口
MCP Server Main Entry
"""

import asyncio
import logging
import signal
import sys
from typing import Any

import structlog
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .api.extended_gaode_client import ExtendedAmapApiClient
from .api.gaode_client import AmapApiClient
from .config import config
from .tools import (
    GeocodingTool,
    GeofenceTool,
    MapServiceTool,
    POISearchTool,
    RoutePlanningTool,
    TrafficServiceTool,
)

# 配置结构化日志
logging.basicConfig(
    format='%(message)s',
    stream=sys.stderr,
    level=getattr(logging, config.mcp_server.log_level.upper())
)

logger = structlog.get_logger(__name__)

class AmapMcpServer:
    """高德地图MCP服务器"""

    def __init__(self):
        self.server = Server(config.mcp_server.name)
        self.api_client: AmapApiClient | None = None
        self.tools: dict[str, Tool] = {}
        self._setup_handlers()

    def _setup_handlers(self) -> Any:
        """设置MCP处理器"""

        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """列出所有可用工具"""
            if not self.api_client:
                await self._initialize_client()

            tools = []
            for tool_name, tool_instance in self.tools.items():
                tools.append(Tool(
                    name=tool_name,
                    description=tool_instance.description,
                    input_schema=tool_instance.get_input_schema()
                ))
            return tools

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """调用工具"""
            if not self.api_client:
                await self._initialize_client()

            if name not in self.tools:
                raise ValueError(f"未知工具: {name}")

            try:
                logger.info(
                    '调用MCP工具',
                    tool_name=name,
                    arguments=arguments
                )

                result = await self.tools[name].call(arguments)

                # 格式化返回结果
                if isinstance(result, dict):
                    formatted_result = self._format_result(result)
                    return [TextContent(type='text', text=formatted_result)]
                else:
                    return [TextContent(type='text', text=str(result))]

            except Exception as e:
                logger.error(
                    'MCP工具调用失败',
                    tool_name=name,
                    error=str(e)
                )
                error_result = {
                    'success': False,
                    'message': f"工具调用失败: {str(e)}",
                    'error': str(e)
                }
                return [TextContent(type='text', text=self._format_result(error_result))]

        @self.server.list_resources()
        async def handle_list_resources() -> list:
            """列出可用资源"""
            return []  # 暂不提供资源

        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """读取资源"""
            raise ValueError('暂不支持资源读取')

        @self.server.list_prompts()
        async def handle_list_prompts() -> list:
            """列出可用提示"""
            return []  # 暂不提供提示

    async def _initialize_client(self):
        """初始化API客户端和工具"""
        if not self.api_client:
            self.api_client = ExtendedAmapApiClient()

            # 初始化所有工具
            self.tools = {
                'gaode_geocode': GeocodingTool(self.api_client),
                'gaode_poi_search': POISearchTool(self.api_client),
                'gaode_route_planning': RoutePlanningTool(self.api_client),
                'gaode_map_service': MapServiceTool(self.api_client),
                'gaode_traffic_service': TrafficServiceTool(self.api_client),
                'gaode_geofence': GeofenceTool(self.api_client),
            }

            logger.info(
                '高德地图MCP服务器初始化完成',
                tools_count=len(self.tools),
                api_key_prefix=config.amap.api_key[:8] + '...'
            )

    def _format_result(self, result: dict[str, Any]) -> str:
        """格式化结果为易读的文本"""

        # 提取关键信息用于快速概览
        if result.get('success'):
            status_icon = '✅'
            status_text = '成功'
        else:
            status_icon = '❌'
            status_text = '失败'

        # 构建概览信息
        overview = f"{status_icon} 操作状态: {status_text}\n"
        overview += f"📝 消息: {result.get('message', '无')}\n"

        if result.get('count') is not None:
            overview += f"📊 结果数量: {result['count']}\n"

        # 构建详细信息
        if result.get('results'):
            overview += "\n🔍 搜索结果:\n"
            results = result['results']

            # 限制显示数量
            display_count = min(5, len(results))
            for i, item in enumerate(results[:display_count]):
                overview += f"\n{i+1}. {item.get('name', item.get('formatted_address', 'N/A'))}\n"
                if item.get('address'):
                    overview += f"   📍 地址: {item['address']}\n"
                if item.get('location'):
                    overview += f"   🌐 坐标: {item['location']}\n"
                if item.get('distance'):
                    overview += f"   📏 距离: {item['distance']}米\n"
                if item.get('tel'):
                    overview += f"   📞 电话: {item['tel']}\n"
                if item.get('type'):
                    overview += f"   🏷️ 类型: {item['type']}\n"

            if len(results) > display_count:
                overview += f"\n... 还有 {len(results) - display_count} 个结果\n"

        if result.get('address'):
            overview += "\n🏠 地址信息:\n"
            address = result['address']
            if isinstance(address, dict):
                for key, value in address.items():
                    if value:
                        overview += f"   {key}: {value}\n"
            else:
                overview += f"   {address}\n"

        if result.get('pois'):
            overview += f"\n🏢 周边POI ({result.get('pois_count', 0)}个):\n"
            pois = result['pois'][:3]  # 只显示前3个
            for poi in pois:
                overview += f"   • {poi.get('name', 'N/A')} - {poi.get('type', '')}\n"
                if poi.get('distance'):
                    overview += f"     📏 {poi.get('distance')}米\n"

        # 添加技术详情（可选）
        technical_details = []
        if result.get('search_type'):
            technical_details.append(f"搜索类型: {result['search_type']}")
        if result.get('keywords'):
            technical_details.append(f"关键词: {result['keywords']}")
        if result.get('location'):
            technical_details.append(f"位置: {result['location']}")
        if result.get('info'):
            technical_details.append(f"API状态: {result['info']}")
        if result.get('infocode'):
            technical_details.append(f"状态码: {result['infocode']}")

        if technical_details:
            overview += "\n🔧 技术详情:\n"
            for detail in technical_details:
                overview += f"   • {detail}\n"

        return overview

    async def run(self):
        """运行服务器"""
        logger.info(
            '启动高德地图MCP服务器',
            version=config.mcp_server.version,
            description=config.mcp_server.description
        )

        # 验证配置
        config.validate()

        # 使用stdio运行服务器
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name=config.mcp_server.name,
                    server_version=config.mcp_server.version,
                    capabilities={
                        'tools': {},
                    },
                ),
            )

async def main():
    """主函数"""
    server = AmapMcpServer()

    # 设置信号处理
    def signal_handler(signum, frame) -> None:
        logger.info(f"接收到信号 {signum}，正在关闭服务器...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await server.run()
    except KeyboardInterrupt:
        logger.info('用户中断，正在关闭服务器...')
    except Exception as e:
        logger.error(
            '服务器运行失败',
            error=str(e),
            exc_info=True
        )
        sys.exit(1)
    finally:
        logger.info('高德地图MCP服务器已关闭')

if __name__ == '__main__':
    asyncio.run(main())
