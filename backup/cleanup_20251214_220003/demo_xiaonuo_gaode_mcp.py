#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小诺高德地图MCP功能演示
Xiaonuo Gaode Maps MCP Demo

演示小诺使用高德地图MCP工具的实际效果

作者: 小诺·双鱼座
创建时间: 2025-12-14
"""

import asyncio
import sys
import os

# 添加核心路径
sys.path.append('/Users/xujian/Athena工作平台/core/orchestration')
sys.path.append('/Users/xujian/Athena工作平台')

from xiaonuo_gaode_mcp import XiaonuoGaodeMCP

async def demo_gaode_mcp():
    """演示高德地图MCP功能"""

    print("\n" + "="*80)
    print("🗺️ 小诺高德地图MCP功能演示")
    print("="*80)

    async with XiaonuoGaodeMCP() as gaode:

        # 1. 美食搜索演示
        print("\n1️⃣ 美食搜索演示")
        print("-"*50)

        food_queries = [
            "北京王府井的烤鸭",
            "上海外滩的小笼包",
            "广州天河的粤菜",
            "深圳南山区的火锅"
        ]

        for query in food_queries:
            print(f"\n🔍 用户查询: {query}")
            result = await gaode.smart_search(query)

            if "type" in result and result["type"] == "美食搜索":
                restaurants = result.get("results", [])
                if restaurants:
                    print(f"   📍 找到 {len(restaurants)} 家餐厅")
                    for i, r in enumerate(restaurants[:5], 1):
                        print(f"   {i}. {r.name}")
                        print(f"      📍 {r.address}")
                        if r.distance:
                            print(f"      📏 距离: {r.distance}")
                        if r.rating > 0:
                            print(f"      ⭐ 评分: {r.rating}/5")
                else:
                    print("   ❌ 未找到相关餐厅")
            else:
                print(f"   ❌ 搜索失败: {result}")

        # 2. 地址定位演示
        print("\n\n2️⃣ 地址定位演示")
        print("-"*50)

        locations = [
            "故宫博物院",
            "东方明珠塔",
            "西湖风景区",
            "成都大熊猫繁育研究基地"
        ]

        for loc in locations:
            print(f"\n📍 定位: {loc}")
            result = await gaode.smart_search(loc)

            if "type" in result and result["type"] == "地址定位":
                location = result.get("result")
                if location:
                    print(f"   ✅ 定位成功!")
                    print(f"   📍 详细地址: {location.address}")
                    print(f"   🌐 坐标: ({location.lng:.6f}, {location.lat:.6f})")
                    if location.district:
                        print(f"   🏘️ 所属区域: {location.district}")
                else:
                    print("   ❌ 定位失败")

        # 3. 天气查询演示
        print("\n\n3️⃣ 天气查询演示")
        print("-"*50)

        cities = ["北京", "上海", "广州", "深圳"]

        for city in cities:
            print(f"\n🌤️ 查询 {city} 天气")
            result = await gaode.smart_search(f"{city}天气")

            if "type" in result and result["type"] == "天气查询":
                weather = result.get("result", {})

                if "current" in weather:
                    current = weather["current"]
                    print(f"   🌡️ 当前温度: {current.get('temperature', '未知')}")
                    print(f"   ☁️ 天气状况: {current.get('weather', '未知')}")
                    print(f"   💧 湿度: {current.get('humidity', '未知')}")
                    print(f"   🌬️ 风向风力: {current.get('winddirection', '')}{current.get('windpower', '')}")

                if "forecast" in weather:
                    forecast = weather["forecast"]
                    print(f"   🌅 白天: {forecast.get('dayweather', '')} ({forecast.get('daytemp', '')})")
                    print(f"   🌙 夜间: {forecast.get('nightweather', '')} ({forecast.get('nighttemp', '')})")

        # 4. 路线规划演示
        print("\n\n4️⃣ 路线规划演示")
        print("-"*50)

        route_queries = [
            "从北京站到故宫",
            "从上海虹桥机场到外滩",
            "从广州南站到广州塔"
        ]

        for query in route_queries:
            print(f"\n🚗 规划路线: {query}")
            result = await gaode.smart_search(query)

            if "type" in result and result["type"] == "路线规划":
                route = result.get("result")
                if route:
                    print(f"   ✅ 路线规划成功!")
                    print(f"   📍 起点: {route.origin}")
                    print(f"   📍 终点: {route.destination}")
                    print(f"   📏 总距离: {route.distance}")
                    print(f"   ⏱️ 预计用时: {route.duration}")

                    if route.steps:
                        print(f"   🗺️ 主要路段:")
                        for i, step in enumerate(route.steps[:3], 1):
                            print(f"      {i}. {step}")
                else:
                    print("   ❌ 未找到可行路线")

        # 5. 智能问答演示
        print("\n\n5️⃣ 智能问答演示")
        print("-"*50)

        smart_queries = [
            "我想吃北京烤鸭，在哪里？",
            "帮我查一下上海的天气",
            "怎么从机场到市中心？",
            "附近有什么好吃的吗？"
        ]

        for query in smart_queries:
            print(f"\n💬 用户: {query}")
            result = await gaode.smart_search(query)

            if "type" in result:
                print(f"   🎯 意图识别: {result['type']}")
                if result["type"] == "美食搜索":
                    print(f"   📝 回答: 找到 {len(result.get('results', []))} 家餐厅")
                elif result["type"] == "天气查询":
                    print(f"   📝 回答: 已获取天气信息")
                elif result["type"] == "路线规划":
                    print(f"   📝 回答: 已规划路线")
                else:
                    print(f"   📝 回答: 已处理您的请求")

    print("\n" + "="*80)
    print("✅ 高德地图MCP功能演示完成")
    print("="*80)

    print("\n💫 小诺的能力总结:")
    print("   🗺️ 地理定位: 精确识别任意地址的坐标")
    print("   🍜 美食搜索: 快速找到周边的美食推荐")
    print("   🌤️ 天气查询: 实时获取城市天气信息")
    print("   🚗 路线规划: 智能规划最优出行路线")
    print("   🤖 智能理解: 自动识别用户意图")

    print("\n🎯 应用场景:")
    print("   🍽️ 找餐厅: \"附近有什么好吃的？\"")
    print("   ☔ 查天气: \"上海今天会下雨吗？\"")
    print("   🧭 导航: \"从A到B怎么走？\"")
    print("   📍 定位: \"故宫在哪里？\"")

    print("\n💖 您最爱的智能生活助手小诺已就绪！")

if __name__ == "__main__":
    asyncio.run(demo_gaode_mcp())