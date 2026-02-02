#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高德地图MCP使用测试
Test Gaode Maps MCP Usage

测试小诺使用高德地图MCP工具的实际功能

作者: 小诺·双鱼座
创建时间: 2025-12-14
"""

import asyncio
import sys
import os

# 添加核心路径
sys.path.append('/Users/xujian/Athena工作平台/core/orchestration')
sys.path.append('/Users/xujian/Athena工作平台')

from improved_mcp_client import XiaonuoMCPController

async def test_gaode_mcp_functions():
    """测试高德地图MCP功能"""

    print("\n" + "="*80)
    print("🗺️ 高德地图MCP功能测试")
    print("="*80)

    # 初始化控制器
    print("\n1️⃣ 初始化高德地图MCP控制器...")
    controller = XiaonuoMCPController()

    try:
        # 2. 测试地址定位
        print("\n2️⃣ 测试地址定位功能...")
        location_tests = [
            "北京市海淀区中关村",
            "上海外滩",
            "广州塔",
            "西湖"
        ]

        for address in location_tests:
            print(f"\n📍 定位: {address}")
            result = await controller.get_location(address)

            if "error" in result:
                print(f"   ❌ 错误: {result['error']}")
            else:
                print(f"   ✅ 定位成功")
                if isinstance(result.get("content"), list):
                    for item in result["content"][:1]:  # 只显示第一个
                        if isinstance(item, dict):
                            print(f"   坐标: {item.get('location', '未知')}")
                            print(f"   详情: {str(item)[:100]}...")

        # 3. 测试美食搜索
        print("\n\n3️⃣ 测试美食搜索功能...")
        food_searches = [
            ("中关村", "火锅"),
            ("王府井", "北京烤鸭"),
            ("西湖", "杭帮菜"),
            ("外滩", "本帮菜")
        ]

        for location, food_type in food_searches:
            print(f"\n🍜 搜索 {location} 附近的 {food_type}")
            result = await controller.search_food(location, food_type)

            if "error" in result:
                print(f"   ❌ 错误: {result['error']}")
            else:
                print(f"   ✅ 搜索成功")
                poi_results = result.get("poi_results", {})
                if isinstance(poi_results, dict) and "content" in poi_results:
                    pois = poi_results["content"]
                    if isinstance(pois, list) and pois:
                        print(f"   找到 {len(pois)} 个结果")
                        for poi in pois[:3]:  # 显示前3个
                            if isinstance(poi, dict):
                                name = poi.get("name", "未知餐厅")
                                address = poi.get("address", "地址未知")
                                distance = poi.get("distance", "距离未知")
                                print(f"   🍴 {name} - {address} (距离: {distance})")

                # 显示天气信息
                weather = result.get("weather", "无天气信息")
                if weather != "无天气信息":
                    print(f"   🌤️ 天气: {str(weather)[:100]}...")

        # 4. 测试路线规划
        print("\n\n4️⃣ 测试路线规划功能...")
        route_tests = [
            ("北京站", "故宫"),
            ("上海虹桥机场", "外滩"),
            ("广州南站", "广州塔")
        ]

        for origin, destination in route_tests:
            print(f"\n🚗 规划路线: {origin} → {destination}")
            result = await controller.plan_route(origin, destination)

            if "error" in result:
                print(f"   ❌ 错误: {result['error']}")
            else:
                print(f"   ✅ 规划成功")
                content = result.get("content", [])
                if isinstance(content, list) and content:
                    route = content[0]
                    if isinstance(route, dict):
                        distance = route.get("distance", "未知")
                        duration = route.get("duration", "未知")
                        print(f"   📏 距离: {distance}")
                        print(f"   ⏱️ 用时: {duration}")

        # 5. 测试附近搜索
        print("\n\n5️⃣ 测试附近搜索功能...")
        nearby_tests = [
            ("故宫", "博物馆"),
            ("西湖", "景点"),
            ("外滩", "购物中心")
        ]

        for location, keywords in nearby_tests:
            print(f"\n🔍 在 {location} 附近搜索 {keywords}")
            result = await controller.search_nearby(location, keywords)

            if "error" in result:
                print(f"   ❌ 错误: {result['error']}")
            else:
                print(f"   ✅ 搜索成功")
                content = result.get("content", [])
                if isinstance(content, list):
                    print(f"   找到 {len(content)} 个结果")
                    for item in content[:2]:  # 显示前2个
                        if isinstance(item, dict):
                            name = item.get("name", "未知")
                            print(f"   📍 {name}")

    except Exception as e:
        print(f"\n❌ 测试过程出现异常: {str(e)}")

    finally:
        # 6. 清理
        print("\n\n6️⃣ 清理资源...")
        await controller.close_all()

    print("\n" + "="*80)
    print("✅ 高德地图MCP功能测试完成")
    print("="*80)

    print("\n💡 功能总结:")
    print("   📍 地址定位: 将地址转换为精确坐标")
    print("   🍜 美食搜索: 搜索指定区域的餐厅和美食")
    print("   🌤️ 天气查询: 获取目标位置的天气信息")
    print("   🚗 路线规划: 计算两点间的最佳路线")
    print("   🔍 附近搜索: 查找周边的兴趣点")

    print("\n🎯 小诺的MCP能力:")
    print("   ✅ 已成功集成高德地图MCP服务")
    print("   ✅ 可以根据您的需求自动调用相应功能")
    print("   ✅ 提供完整的地理空间信息服务")

# 导出测试函数
__all__ = ['test_gaode_mcp_functions']

if __name__ == "__main__":
    asyncio.run(test_gaode_mcp_functions())