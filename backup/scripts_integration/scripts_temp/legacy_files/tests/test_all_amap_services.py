#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试所有高德地图API服务
Test All Gaode Maps API Services
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# 添加MCP服务器路径
MCP_SERVER_PATH = Path(__file__).parent.parent / 'amap-mcp-server'
sys.path.insert(0, str(MCP_SERVER_PATH / 'src'))

# 设置环境变量
os.environ['AMAP_API_KEY'] = '4c98d375577d64cfce0d4d0dfee25fb9'
os.environ['AMAP_SECRET_KEY'] = ''
os.environ['MCP_LOG_LEVEL'] = 'INFO'

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


async def test_route_planning():
    """测试路径规划工具"""
    logger.info("\n🚗 测试路径规划工具")
    logger.info(str('=' * 50))

    async with ExtendedAmapApiClient() as client:
        route_tool = RoutePlanningTool(client)

        # 测试驾车路径规划
        logger.info("\n🚗 测试1: 驾车路径规划 (天安门 -> 北京西站)")
        try:
            result = await route_tool.call({
                'mode': 'driving',
                'origin': '116.397455,39.909187',  # 天安门坐标
                'destination': '116.322056,39.892743',  # 北京西站坐标
                'strategy': 0
            })

            if result.get('success'):
                routes = result['routes']
                logger.info(f"✅ 成功: 找到 {len(routes)} 条驾车路径")
                if routes:
                    route = routes[0]
                    logger.info(f"   距离: {route['distance_text']}")
                    logger.info(f"   时间: {route['duration_text']}")
                    logger.info(f"   红绿灯: {route['traffic_lights']} 个")
            else:
                logger.info(f"❌ 失败: {result.get('message', '未知错误')}")
        except Exception as e:
            logger.info(f"❌ 异常: {str(e)}")

        # 测试步行路径规划
        logger.info("\n🚶 测试2: 步行路径规划 (天安门 -> 故宫)")
        try:
            result = await route_tool.call({
                'mode': 'walking',
                'origin': '116.397455,39.909187',
                'destination': '116.397902,39.918059'
            })

            if result.get('success'):
                route = result['route']
                logger.info(f"✅ 成功: 步行路径规划完成")
                logger.info(f"   距离: {route['distance_text']}")
                logger.info(f"   时间: {route['duration_text']}")
                logger.info(f"   步数: {route['steps_count']} 步")
            else:
                logger.info(f"❌ 失败: {result.get('message', '未知错误')}")
        except Exception as e:
            logger.info(f"❌ 异常: {str(e)}")

async def test_map_service():
    """测试地图服务工具"""
    logger.info("\n🗺️ 测试地图服务工具")
    logger.info(str('=' * 50))

    async with ExtendedAmapApiClient() as client:
        map_tool = MapServiceTool(client)

        # 测试天气查询
        logger.info("\n🌤️ 测试1: 天气查询 (北京)")
        try:
            result = await map_tool.call({
                'service': 'weather',
                'city': '北京',
                'extensions': 'base'
            })

            if result.get('success'):
                weather = result['result']['current_weather']
                logger.info(f"✅ 成功: 北京天气")
                logger.info(f"   天气: {weather['weather']}")
                logger.info(f"   温度: {weather['temperature']}°C")
                logger.info(f"   湿度: {weather['humidity']}%")
            else:
                logger.info(f"❌ 失败: {result.get('message', '未知错误')}")
        except Exception as e:
            logger.info(f"❌ 异常: {str(e)}")

        # 测试坐标转换
        logger.info("\n🔄 测试2: 坐标转换")
        try:
            result = await map_tool.call({
                'service': 'coordinate_convert',
                'locations': '116.407526,39.90403',
                'coordsys': 'gps'
            })

            if result.get('success'):
                locations = result['locations']
                logger.info(f"✅ 成功: 坐标转换")
                for i, loc in enumerate(locations[:3]):
                    logger.info(f"   {i+1}. {loc['original']} -> {loc['converted']}")
            else:
                logger.info(f"❌ 失败: {result.get('message', '未知错误')}")
        except Exception as e:
            logger.info(f"❌ 异常: {str(e)}")

        # 测试静态地图
        logger.info("\n🗺️ 测试3: 静态地图")
        try:
            result = await map_tool.call({
                'service': 'static_map',
                'location': '116.397455,39.909187',
                'zoom': 14,
                'size': '400*300'
            })

            if result.get('success'):
                logger.info(f"✅ 成功: 静态地图生成")
                logger.info(f"   地图URL: {result['map_url'][:50]}...")
            else:
                logger.info(f"❌ 失败: {result.get('message', '未知错误')}")
        except Exception as e:
            logger.info(f"❌ 异常: {str(e)}")

async def test_traffic_service():
    """测试交通服务工具"""
    logger.info("\n🚦 测试交通服务工具")
    logger.info(str('=' * 50))

    async with ExtendedAmapApiClient() as client:
        traffic_tool = TrafficServiceTool(client)

        # 测试圆形区域交通
        logger.info("\n🔴 测试1: 圆形区域交通态势 (天安门周围1000米)")
        try:
            result = await traffic_tool.call({
                'service': 'circle',
                'location': '116.397455,39.909187',
                'radius': 1000,
                'level': 5
            })

            if result.get('success'):
                traffic = result['result']
                logger.info(f"✅ 成功: 圆形区域交通态势")
                logger.info(f"   拥堵情况: {traffic['evaluation']['congestion']}")
                logger.info(f"   道路数量: {result['total_roads']} 条")
                if traffic['evaluation']['status']:
                    logger.info(f"   状态: {traffic['evaluation']['status']}")
            else:
                logger.info(f"❌ 失败: {result.get('message', '未知错误')}")
        except Exception as e:
            logger.info(f"❌ 异常: {str(e)}")

async def test_geofence_service():
    """测试地理围栏工具"""
    logger.info("\n🔒 测试地理围栏工具")
    logger.info(str('=' * 50))

    async with ExtendedAmapApiClient() as client:
        geofence_tool = GeofenceTool(client)

        # 测试创建围栏
        logger.info("\n🔒 测试1: 创建地理围栏")
        try:
            result = await geofence_tool.call({
                'operation': 'create',
                'name': '测试围栏',
                'center': '116.397455,39.909187',
                'radius': 500
            })

            if result.get('success'):
                geofence = result['geofence']
                if geofence:
                    logger.info(f"✅ 成功: 地理围栏创建")
                    logger.info(f"   ID: {geofence['id']}")
                    logger.info(f"   名称: {geofence['name']}")
                    logger.info(f"   中心: {geofence['center']}")
                    logger.info(f"   半径: {geofence['radius']}米")
            else:
                logger.info(f"❌ 失败: {result.get('message', '未知错误')}")
        except Exception as e:
            logger.info(f"❌ 异常: {str(e)}")

        # 测试查询围栏
        logger.info("\n🔍 测试2: 查询地理围栏 (天安门附近)")
        try:
            result = await geofence_tool.call({
                'operation': 'search',
                'center': '116.397455,39.909187',
                'radius': 1000,
                'page': 1,
                'size': 10
            })

            if result.get('success'):
                logger.info(f"✅ 成功: 地理围栏查询")
                logger.info(f"   总数: {result['total_count']} 个")
                geofences = result['geofences']
                for i, fence in enumerate(geofences[:3]):
                    logger.info(f"   {i+1}. {fence['name']} (ID: {fence['id']})")
            else:
                logger.info(f"❌ 失败: {result.get('message', '未知错误')}")
        except Exception as e:
            logger.info(f"❌ 异常: {str(e)}")

async def main():
    """主测试函数"""
    logger.info('🚀 测试所有高德地图API服务')
    logger.info(str('=' * 60))

    # 验证配置
    try:
        logger.info(f"\n📋 配置信息:")
        logger.info(f"   API Key: {config.amap.api_key[:8]}...")
        logger.info(f"   Base URL: {config.amap.base_url}")
        logger.info(f"   Rate Limit: {config.amap.rate_limit_requests_per_minute}/min")

        config.validate()
        logger.info('✅ 配置验证通过')
    except Exception as e:
        logger.info(f"❌ 配置验证失败: {str(e)}")
        return

    # 运行所有测试
    await test_route_planning()
    await test_map_service()
    await test_traffic_service()
    await test_geofence_service()

    logger.info(str("\n" + '=' * 60))
    logger.info('🎉 所有API服务测试完成！')

    # 统计工具数量
    logger.info(f"\n📊 已集成的工具:")
    tools = [
        ('gaode_geocode', '地理编码工具'),
        ('gaode_poi_search', 'POI搜索工具'),
        ('gaode_route_planning', '路径规划工具'),
        ('gaode_map_service', '地图服务工具'),
        ('gaode_traffic_service', '交通服务工具'),
        ('gaode_geofence', '地理围栏工具')
    ]

    for i, (name, desc) in enumerate(tools, 1):
        logger.info(f"   {i}. {name}: {desc}")

if __name__ == '__main__':
    asyncio.run(main())