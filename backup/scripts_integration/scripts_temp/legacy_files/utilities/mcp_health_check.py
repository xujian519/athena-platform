#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena工作平台 - MCP服务健康检查器
MCP Service Health Checker for Athena Platform
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'amap-mcp-server' / 'src'))

# 设置环境变量
os.environ['AMAP_API_KEY'] = '4c98d375577d64cfce0d4d0dfee25fb9'
os.environ['AMAP_SECRET_KEY'] = ''
os.environ['MCP_LOG_LEVEL'] = 'ERROR'  # 健康检查时减少日志输出

from amap_mcp_server.api.extended_gaode_client import ExtendedAmapApiClient
from amap_mcp_server.config import config
from amap_mcp_server.tools import (
    GeocodingTool,
    GeofenceTool,
    MapServiceTool,
    POISearchTool,
    RoutePlanningTool,
    TrafficServiceTool,
)


class MCPHealthChecker:
    """MCP服务健康检查器"""

    def __init__(self):
        self.client = ExtendedAmapApiClient()
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'service': 'gaode-maps-mcp',
            'version': '1.0.0',
            'overall_status': 'unknown',
            'tools': {},
            'api_status': {},
            'performance': {},
            'errors': []
        }

    async def check_api_connectivity(self) -> bool:
        """检查API连接性"""
        try:
            # 使用简单的地理编码测试连接
            result = await self.client.geocoding(address='天安门', city='北京')

            if result.get('status') == '1':
                self.results['api_status']['connectivity'] = 'healthy'
                return True
            else:
                self.results['api_status']['connectivity'] = 'unhealthy'
                self.results['errors'].append('API连接测试失败')
                return False
        except Exception as e:
            self.results['api_status']['connectivity'] = 'error'
            self.results['errors'].append(f"API连接异常: {str(e)}")
            return False

    async def check_tool_health(self, tool_name: str, tool_instance) -> Dict[str, Any]:
        """检查单个工具的健康状态"""
        tool_result = {
            'name': tool_name,
            'status': 'unknown',
            'response_time': 0,
            'error': None
        }

        try:
            start_time = asyncio.get_event_loop().time()

            # 根据不同工具选择合适的测试参数
            test_params = self._get_tool_test_params(tool_name)

            if test_params:
                result = await tool_instance.call(test_params)

                # 计算响应时间
                tool_result['response_time'] = asyncio.get_event_loop().time() - start_time

                # 检查结果
                if result.get('success'):
                    tool_result['status'] = 'healthy'
                else:
                    # 对于地理围栏等需要企业权限的API，检查是否有权限提示
                    if result.get('requires_enterprise_permission'):
                        tool_result['status'] = 'permission_required'
                        tool_result['error'] = '需要企业级API权限'
                    else:
                        tool_result['status'] = 'unhealthy'
                        tool_result['error'] = result.get('message', '未知错误')
            else:
                tool_result['status'] = 'skipped'
                tool_result['error'] = '无可用测试参数'

        except Exception as e:
            tool_result['status'] = 'error'
            tool_result['error'] = str(e)

        return tool_result

    def _get_tool_test_params(self, tool_name: str) -> Dict[str, Any | None]:
        """获取工具测试参数"""
        test_cases = {
            'gaode_geocode': {
                'type': 'geocode',
                'address': '天安门',
                'city': '北京'
            },
            'gaode_poi_search': {
                'type': 'search',
                'keywords': '餐厅',
                'city': '北京'
            },
            'gaode_route_planning': {
                'mode': 'walking',
                'origin': '116.397455,39.909187',
                'destination': '116.397902,39.918059'
            },
            'gaode_map_service': {
                'service': 'weather',
                'city': '北京',
                'extensions': 'base'
            },
            'gaode_traffic_service': {
                'service': 'circle',
                'location': '116.397455,39.909187',
                'radius': 1000,
                'level': 5
            },
            'gaode_geofence': {
                'operation': 'search',
                'center': '116.397455,39.909187',
                'radius': 1000
            }
        }
        return test_cases.get(tool_name)

    async def run_health_check(self) -> Dict[str, Any]:
        """运行完整的健康检查"""
        logger.info('🚀 开始MCP服务健康检查...')
        logger.info(str('=' * 50))

        # 检查API连接性
        logger.info("\n📡 检查API连接性...")
        api_healthy = await self.check_api_connectivity()

        if not api_healthy:
            self.results['overall_status'] = 'critical'
            logger.info('❌ API连接失败，服务不可用')
            return self.results

        logger.info('✅ API连接正常')

        # 初始化工具实例
        tools = {
            'gaode_geocode': GeocodingTool(self.client),
            'gaode_poi_search': POISearchTool(self.client),
            'gaode_route_planning': RoutePlanningTool(self.client),
            'gaode_map_service': MapServiceTool(self.client),
            'gaode_traffic_service': TrafficServiceTool(self.client),
            'gaode_geofence': GeofenceTool(self.client)
        }

        # 检查每个工具
        logger.info("\n🔧 检查MCP工具...")
        healthy_count = 0
        total_count = len(tools)

        for tool_name, tool_instance in tools.items():
            logger.info(f"  检查 {tool_name}...")
            tool_result = await self.check_tool_health(tool_name, tool_instance)
            self.results['tools'][tool_name] = tool_result

            # 显示结果
            status_icon = {
                'healthy': '✅',
                'unhealthy': '❌',
                'error': '💥',
                'permission_required': '🔒',
                'skipped': '⏭️'
            }.get(tool_result['status'], '❓')

            logger.info(f"    {status_icon} {tool_name}: {tool_result['status']}")
            if tool_result.get('response_time'):
                logger.info(f"      响应时间: {tool_result['response_time']:.3f}s")
            if tool_result.get('error'):
                logger.info(f"      错误: {tool_result['error']}")

            if tool_result['status'] == 'healthy':
                healthy_count += 1

        # 计算整体状态
        logger.info("\n📊 计算整体健康状态...")
        self.results['performance']['tools_healthy'] = f"{healthy_count}/{total_count}"
        self.results['performance']['health_percentage'] = (healthy_count / total_count) * 100

        if healthy_count == total_count:
            self.results['overall_status'] = 'healthy'
            logger.info('✅ 所有工具运行正常')
        elif healthy_count >= total_count * 0.8:
            self.results['overall_status'] = 'degraded'
            logger.info('⚠️  部分工具异常，服务降级运行')
        else:
            self.results['overall_status'] = 'unhealthy'
            logger.info('❌ 多数工具异常，服务不健康')

        # 添加配置信息
        self.results['configuration'] = {
            'api_key_prefix': config.amap.api_key[:8] + '...',
            'base_url': config.amap.base_url,
            'rate_limit': config.amap.rate_limit_requests_per_minute
        }

        return self.results

    async def run_continuous_check(self, interval: int = 60, count: int = 5):
        """运行连续健康检查"""
        logger.info(f"🔄 开始连续健康检查 ({count}次，间隔{interval}秒)...")
        logger.info(str('=' * 60))

        check_results = []

        for i in range(count):
            logger.info(f"\n--- 第 {i+1} 次检查 ---")
            result = await self.run_health_check()
            check_results.append(result)

            if i < count - 1:  # 不是最后一次检查
                logger.info(f"\n⏱️  等待 {interval} 秒后进行下次检查...")
                await asyncio.sleep(interval)

        # 生成连续检查报告
        logger.info(str("\n" + '=' * 60))
        logger.info('📈 连续检查报告')
        logger.info(str('=' * 60))

        status_counts = {}
        for result in check_results:
            status = result['overall_status']
            status_counts[status] = status_counts.get(status, 0) + 1

        for status, count in status_counts.items():
            percentage = (count / len(check_results)) * 100
            status_icon = {
                'healthy': '✅',
                'degraded': '⚠️',
                'unhealthy': '❌',
                'critical': '💥'
            }.get(status, '❓')
            logger.info(f"{status_icon} {status}: {count}/{len(check_results)} ({percentage:.1f}%)")

        return check_results

    def save_results(self, filename: str = None):
        """保存检查结果"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"mcp_health_check_{timestamp}.json"

        output_path = PROJECT_ROOT / 'logs' / filename
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        logger.info(f"\n📄 检查结果已保存到: {output_path}")
        return output_path

def print_help():
    """打印帮助信息"""
    logger.info('Athena工作平台 - MCP服务健康检查器')
    logger.info(str('=' * 40))
    print()
    logger.info('用法:')
    logger.info('  python3 mcp_health_check.py [选项]')
    print()
    logger.info('选项:')
    logger.info('  --single              单次检查（默认）')
    logger.info('  --continuous [次数]   连续检查，默认5次')
    logger.info('  --interval [秒]       连续检查间隔，默认60秒')
    logger.info('  --save                保存检查结果到文件')
    logger.info('  --help                显示帮助信息')
    print()
    logger.info('示例:')
    logger.info('  python3 mcp_health_check.py --single')
    logger.info('  python3 mcp_health_check.py --continuous 3 --interval 30')
    logger.info('  python3 mcp_health_check.py --save')

async def main():
    """主函数"""
    args = sys.argv[1:]

    # 解析参数
    mode = 'single'
    continuous_count = 5
    interval = 60
    save_results = False

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '--single':
            mode = 'single'
        elif arg == '--continuous':
            mode = 'continuous'
            if i + 1 < len(args) and not args[i + 1].startswith('--'):
                continuous_count = int(args[i + 1])
                i += 1
        elif arg == '--interval':
            if i + 1 < len(args):
                interval = int(args[i + 1])
                i += 1
        elif arg == '--save':
            save_results = True
        elif arg == '--help' or arg == '-h':
            print_help()
            return
        i += 1

    # 运行健康检查
    checker = MCPHealthChecker()

    try:
        if mode == 'single':
            results = await checker.run_health_check()

            # 打印总结
            logger.info(str("\n" + '=' * 50))
            logger.info('📋 健康检查总结')
            logger.info(str('=' * 50))
            logger.info(f"整体状态: {results['overall_status']}")
            logger.info(f"健康工具: {results['performance']['tools_healthy']}")
            logger.info(f"健康百分比: {results['performance']['health_percentage']:.1f}%")

            if save_results:
                checker.save_results()

        elif mode == 'continuous':
            results = await checker.run_continuous_check(interval, continuous_count)
            if save_results:
                # 保存最后一次结果
                checker.save_results()

    except KeyboardInterrupt:
        logger.info("\n\n⚠️  健康检查被用户中断")
    except Exception as e:
        logger.info(f"\n💥 健康检查过程中发生错误: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())