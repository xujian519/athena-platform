#!/usr/bin/env python3
from __future__ import annotations
"""
小诺高德地图MCP集成
Xiaonuo Gaode Maps MCP Integration

直接集成高德地图API,实现美食搜索、定位、天气等功能

作者: 小诺·双鱼座
创建时间: 2025-12-14
"""

import logging
import os
from dataclasses import dataclass
from typing import Any

import aiohttp


@dataclass
class Location:
    """位置信息"""

    name: str
    address: str
    lng: float  # 经度
    lat: float  # 纬度
    district: str = ""


@dataclass
class Restaurant:
    """餐厅信息"""

    name: str
    address: str
    phone: str = ""
    distance: str = ""
    rating: float = 0.0
    type: str = ""


@dataclass
class Route:
    """路线信息"""

    origin: str
    destination: str
    distance: str
    duration: str
    steps: list[str]


class XiaonuoGaodeMCP:
    """小诺高德地图MCP集成"""

    def __init__(self):
        self.name = "小诺·双鱼公主高德地图MCP"
        # 使用环境变量获取API密钥
        self.api_key = os.getenv("AMAP_API_KEY", "")
        if not self.api_key:
            logging.warning("AMAP_API_KEY环境变量未设置,高德地图功能将不可用")
        self.base_url = "https://restapi.amap.com/v3"
        self.session: aiohttp.ClientSession | None = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _make_request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        """发送API请求"""
        if not self.session:
            raise Exception("MCP未初始化,请使用 async with")

        params["key"] = self.api_key
        url = f"{self.base_url}/{endpoint}"

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "1":
                        return data
                    else:
                        return {"error": data.get("info", "请求失败")}
                else:
                    return {"error": f"HTTP错误: {response.status}"}
        except Exception as e:
            return {"error": str(e)}

    async def geocode(self, address: str) -> Location | None:
        """地址转坐标"""
        params = {"address": address, "city": "全国"}

        result = await self._make_request("geocode/geo", params)

        if "error" in result:
            print(f"❌ 地址解析失败: {result['error']}")
            return None

        geocodes = result.get("geocodes", [])
        if not geocodes:
            print(f"❌ 未找到地址: {address}")
            return None

        geo = geocodes[0]
        location_parts = geo.get("location", ",").split(",")

        return Location(
            name=geo.get("formatted_address", address),
            address=geo.get("formatted_address", address),
            lng=float(location_parts[0]) if len(location_parts) > 0 else 0,
            lat=float(location_parts[1]) if len(location_parts) > 1 else 0,
            district=geo.get("district", ""),
        )

    async def search_nearby(
        self, location: Location, keywords: str, radius: int = 3000
    ) -> list[Restaurant]:
        """搜索附近的POI"""
        params = {
            "keywords": keywords,
            "location": f"{location.lng},{location.lat}",
            "radius": radius,
            "sortrule": "distance",
            "offset": 20,
            "page": 1,
            "extensions": "all",
        }

        result = await self._make_request("place/around", params)

        if "error" in result:
            print(f"❌ 搜索失败: {result['error']}")
            return []

        pois = result.get("pois", [])
        restaurants = []

        for poi in pois:
            # 计算距离
            distance = poi.get("distance", "")
            if distance:
                distance = f"{int(distance)}米"

            # 获取评分
            rating = 0.0
            ext_info = poi.get("ext_info", {})
            if "rating" in ext_info:
                rating = float(ext_info["rating"])

            restaurant = Restaurant(
                name=poi.get("name", "未知餐厅"),
                address=poi.get("address", "地址未知"),
                phone=poi.get("tel", ""),
                distance=distance,
                rating=rating,
                type=poi.get("type", ""),
            )
            restaurants.append(restaurant)

        return restaurants

    async def search_food(self, location: str, food_type: str = "美食") -> list[Restaurant]:
        """搜索美食"""
        # 先获取位置坐标
        loc = await self.geocode(location)
        if not loc:
            return []

        print(f"\n📍 定位成功: {loc.name} ({loc.lng:.6f}, {loc.lat:.6f})")

        # 搜索美食
        restaurants = await self.search_nearby(loc, food_type)

        # 过滤出真正的餐厅
        food_keywords = ["餐厅", "饭店", "美食", "菜馆", "酒楼", "小吃", "快餐"]
        filtered_restaurants = []

        for r in restaurants:
            if any(keyword in r.name or keyword in r.type for keyword in food_keywords):
                filtered_restaurants.append(r)

        return filtered_restaurants[:10]  # 返回前10个

    async def get_weather(self, city: str) -> dict[str, Any]:
        """获取天气信息"""
        params = {"city": city, "extensions": "all"}

        result = await self._make_request("weather/weather_info", params)

        if "error" in result:
            return {"error": result["error"]}

        lives = result.get("lives", [])
        forecasts = result.get("forecasts", [])

        weather_info = {}

        if lives:
            live = lives[0]
            weather_info.update(
                {
                    "current": {
                        "temperature": f"{live.get('temperature', '')}°C",
                        "weather": live.get("weather", ""),
                        "winddirection": live.get("winddirection", ""),
                        "windpower": live.get("windpower", ""),
                        "humidity": live.get("humidity", ""),
                        "reporttime": live.get("reporttime", ""),
                    }
                }
            )

        if forecasts:
            forecast = forecasts[0]
            casts = forecast.get("casts", [])
            if casts:
                today = casts[0]
                weather_info.update(
                    {
                        "forecast": {
                            "dayweather": today.get("dayweather", ""),
                            "nightweather": today.get("nightweather", ""),
                            "daytemp": f"{today.get('daytemp', '')}°C",
                            "nighttemp": f"{today.get('nighttemp', '')}°C",
                            "daywind": today.get("daywind", ""),
                            "nightwind": today.get("nightwind", ""),
                        }
                    }
                )

        return weather_info

    async def plan_route(
        self, origin: str, destination: str, strategy: str = "LEAST_TIME"
    ) -> Route | None:
        """规划路线"""
        # 获取起点和终点坐标
        origin_loc = await self.geocode(origin)
        dest_loc = await self.geocode(destination)

        if not origin_loc or not dest_loc:
            return None

        params = {
            "origin": f"{origin_loc.lng},{origin_loc.lat}",
            "destination": f"{dest_loc.lng},{dest_loc.lat}",
            "strategy": strategy,
            "extensions": "all",
        }

        result = await self._make_request("direction/driving", params)

        if "error" in result:
            print(f"❌ 路线规划失败: {result['error']}")
            return None

        route = result.get("route", {})
        paths = route.get("paths", [])

        if not paths:
            print("❌ 未找到可行路线")
            return None

        path = paths[0]
        distance = f"{path.get('distance', 0)}米"
        duration = f"{path.get('duration', 0)}秒"

        # 转换为更友好的格式
        distance_km = float(distance.replace("米", "")) / 1000
        duration_min = float(duration.replace("秒", "")) / 60

        # 提取步骤
        steps = []
        for step in path.get("steps", [])[:5]:  # 只显示前5步
            instruction = step.get("instruction", "")
            if instruction:
                steps.append(instruction)

        return Route(
            origin=origin,
            destination=destination,
            distance=f"{distance_km:.1f}公里",
            duration=f"{duration_min:.0f}分钟",
            steps=steps,
        )

    async def smart_search(self, query: str) -> dict[str, Any]:
        """智能搜索,根据用户查询自动选择功能"""
        query_lower = query.lower()

        # 判断查询类型
        if any(
            keyword in query_lower for keyword in ["美食", "吃饭", "餐厅", "火锅", "烤鸭", "小吃"]
        ):
            # 美食搜索
            import re

            location_match = re.search(r"([^,,]+?)的?(美食|餐厅|火锅|烤鸭)", query)
            if location_match:
                location = location_match.group(1)
                food_type = location_match.group(2)
                restaurants = await self.search_food(location, food_type)
                return {"type": "美食搜索", "results": restaurants}

        elif any(keyword in query_lower for keyword in ["路线", "从", "到", "去", "导航"]):
            # 路线规划
            import re

            route_match = re.search(r"从(.+?)到(.+)", query)
            if route_match:
                origin = route_match.group(1)
                destination = route_match.group(2)
                route = await self.plan_route(origin, destination)
                return {"type": "路线规划", "result": route}

        elif any(keyword in query_lower for keyword in ["天气", "气温", "下雨"]):
            # 天气查询
            city = query.split("的")[0] if "的" in query else query
            weather = await self.get_weather(city)
            return {"type": "天气查询", "result": weather}

        else:
            # 默认为地址解析
            location = await self.geocode(query)
            return {"type": "地址定位", "result": location}

        return {"error": "无法理解您的查询"}


# 导出主类
__all__ = ["Location", "Restaurant", "Route", "XiaonuoGaodeMCP"]
