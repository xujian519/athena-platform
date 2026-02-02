#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高德地图MCP服务器简化测试脚本
Amap MCP Server Simple Test Script

控制者: 小诺 & Athena
创建时间: 2025年12月11日
版本: 1.0.0
"""

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# 添加路径
platform_root = Path('/Users/xujian/Athena工作平台')
amap_server_path = platform_root / 'amap-mcp-server'
sys.path.insert(0, str(amap_server_path))

def test_amap_mcp_import():
    """测试高德地图MCP服务器导入"""
    logger.info('🗺️ 测试高德地图MCP服务器...')
    logger.info(str('-' * 40))

    try:
        # 设置环境变量
        os.environ.setdefault('AMAP_API_KEY', '4c98d375577d64cfce0d4d0dfee25fb9')
        os.environ.setdefault('AMAP_SECRET_KEY', '')
        os.environ.setdefault('PYTHONPATH', str(amap_server_path))

        logger.info('✅ 环境变量已设置')

        # 测试配置导入
        logger.info('测试配置模块导入...')
        try:
            from src.amap_mcp_server.config import config
            logger.info('✅ 配置模块导入成功')
            logger.info(str(f"  API密钥: {config.amap.api_key[:10]}...' if config.amap.api_key else '  API密钥: 未配置"))
            logger.info(f"  服务器名称: {config.mcp_server.name}")
            logger.info(f"  服务器版本: {config.mcp_server.version}")
        except Exception as e:
            logger.info(f"❌ 配置模块导入失败: {e}")
            return False

        # 测试API客户端
        logger.info("\n测试API客户端...")
        try:
            from src.amap_mcp_server.api.gaode_client import AmapApiClient
            client = AmapApiClient()
            logger.info('✅ API客户端创建成功')
        except Exception as e:
            logger.info(f"❌ API客户端创建失败: {e}")
            return False

        # 测试服务器类
        logger.info("\n测试服务器类...")
        try:
            from src.amap_mcp_server.server import AmapMcpServer
            server = AmapMcpServer()
            logger.info('✅ MCP服务器实例创建成功')
            logger.info(f"  服务器名称: {server.server.name}")
            logger.info(f"  已注册工具数量: {len(server.tools)}")
        except Exception as e:
            logger.info(f"❌ MCP服务器创建失败: {e}")
            return False

        # 测试工具模块导入
        logger.info("\n测试工具模块导入...")
        try:
            from src.amap_mcp_server.tools import (
                GeocodingTool,
                GeofenceTool,
                MapServiceTool,
                POISearchTool,
                RoutePlanningTool,
                TrafficServiceTool,
            )

            tool_classes = [
                GeocodingTool,
                POISearchTool,
                RoutePlanningTool,
                MapServiceTool,
                TrafficServiceTool,
                GeofenceTool
            ]

            logger.info(f"✅ 成功导入 {len(tool_classes)} 个工具类:")
            for tool_class in tool_classes:
                logger.info(f"  📦 {tool_class.__name__}")

        except Exception as e:
            logger.info(f"❌ 工具模块导入失败: {e}")
            return False

        return True

    except Exception as e:
        logger.info(f"❌ 测试过程中发生异常: {e}")
        return False

def test_api_connectivity():
    """测试API连通性"""
    logger.info("\n🌐 测试高德地图API连通性...")
    logger.info(str('-' * 40))

    try:
        import requests

        api_key = '4c98d375577d64cfce0d4d0dfee25fb9'
        test_url = f"https://restapi.amap.com/v3/geocode/geo?address=北京市&key={api_key}"

        logger.info(f"测试地址: {test_url[:50]}...")

        response = requests.get(test_url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == '1':
                logger.info('✅ API连通性测试成功')
                geocodes = data.get('geocodes', [])
                if geocodes:
                    location = geocodes[0].get('location', '')
                    logger.info(f"  测试结果: 北京市 -> {location}")
                return True
            else:
                logger.info(f"❌ API返回错误: {data.get('info', '未知错误')}")
                return False
        else:
            logger.info(f"❌ HTTP请求失败: {response.status_code}")
            return False

    except Exception as e:
        logger.info(f"❌ API连通性测试异常: {e}")
        return False

def main():
    """主函数"""
    logger.info('🚀 高德地图MCP服务器测试')
    logger.info(str('=' * 50))

    # 测试模块导入
    import_success = test_amap_mcp_import()

    # 测试API连通性
    if import_success:
        api_success = test_api_connectivity()

        if import_success and api_success:
            logger.info("\n🎉 高德地图MCP服务器测试全部通过！")
            logger.info('✅ 模块导入正常')
            logger.info('✅ 配置加载正常')
            logger.info('✅ 工具注册正常')
            logger.info('✅ API连通性正常')
            return True
        else:
            logger.info("\n❌ 部分测试失败")
            return False
    else:
        logger.info("\n❌ 模块导入测试失败")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)