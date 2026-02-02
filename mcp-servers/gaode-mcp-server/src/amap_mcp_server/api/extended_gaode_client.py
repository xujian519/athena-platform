"""
扩展的高德地图API客户端
Extended Gaode Maps API Client

包含所有已开通的服务API
"""

import asyncio
import hashlib
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
import structlog

from ..config import config

logger = structlog.get_logger(__name__)

class ExtendedAmapApiClient:
    """扩展的高德地图API客户端"""

    def __init__(self):
        self.api_key = config.amap.api_key
        self.secret_key = config.amap.secret_key
        self.base_url = config.amap.base_url
        self.timeout = config.amap.timeout
        self.max_retries = config.amap.max_retries
        self.retry_delay = config.amap.retry_delay

        # 限流器
        self.rate_limiter = RateLimiter(
            requests_per_minute=config.amap.rate_limit_requests_per_minute,
            requests_per_second=config.amap.rate_limit_requests_per_second
        )

        # HTTP客户端
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            base_url=self.base_url,
            headers={
                'User-Agent': 'Athena-Amap-MCP-Server/1.0.0'
            }
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self.client, 'aclose'):
            await self.client.aclose()

    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """生成API签名"""
        # 如果没有secret key，不生成签名
        if not self.secret_key:
            return ''

        # 添加API密钥
        params['key'] = self.api_key

        # 排序参数
        sorted_params = sorted(params.items())
        query_string = '&'.join([f"{k}={v}" for k, v in sorted_params])

        # 生成签名
        signature = hashlib.md5(
            f"{query_string}{self.secret_key}".encode('utf-8', usedforsecurity=False)
        ).hexdigest()

        return signature

    async def _make_request(
        self,
        endpoint: str,
        params: Dict[str, Any],
        method: str = 'GET',
        return_url: bool = False
    ) -> Dict[str, Any]:
        """发起API请求"""
        # 限流
        await self.rate_limiter.acquire()

        # 构造请求参数
        request_params = params.copy()
        request_params['key'] = self.api_key

        # 生成签名
        if self.secret_key:
            signature = self._generate_signature(request_params)
            if signature:
                request_params['sig'] = signature

        # 重试机制
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    'Making API request',
                    endpoint=endpoint,
                    attempt=attempt + 1,
                    params=request_params
                )

                if method.upper() == 'GET':
                    response = await self.client.get(endpoint, params=request_params)
                else:
                    response = await self.client.post(endpoint, json=request_params)

                response.raise_for_status()

                if return_url:
                    # 对于静态地图等需要返回URL的情况
                    query_string = '&'.join([f"{k}={v}" for k, v in request_params.items()])
                    return f"{self.base_url}{endpoint}?{query_string}"

                data = response.json()

                # 检查API响应状态
                if data.get('status') != '1':
                    error_msg = data.get('info', 'Unknown error')
                    logger.error(
                        'API error response',
                        endpoint=endpoint,
                        error_code=data.get('infocode'),
                        error_msg=error_msg
                    )
                    raise AmapApiError(error_msg, data.get('infocode'))

                return data

            except httpx.HTTPError as e:
                last_exception = e
                logger.warning(
                    'HTTP request failed, retrying',
                    endpoint=endpoint,
                    attempt=attempt + 1,
                    error=str(e)
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))

            except Exception as e:
                last_exception = e
                logger.error(
                    'API request failed',
                    endpoint=endpoint,
                    attempt=attempt + 1,
                    error=str(e)
                )
                raise

        # 所有重试失败
        logger.error(
            'API request failed after all retries',
            endpoint=endpoint,
            error=str(last_exception)
        )
        raise last_exception or Exception('Unknown error')

    # ============ 地理编码相关接口 ============

    async def geocoding(
        self,
        address: str,
        city: str | None = None,
        district: str | None = None
    ) -> Dict[str, Any]:
        """地址转坐标"""
        params = {
            'address': address,
            'output': 'JSON'
        }
        if city:
            params['city'] = city
        if district:
            params['district'] = district

        return await self._make_request('/v3/geocode/geo', params)

    async def reverse_geocoding(
        self,
        location: str,  # 经纬度 'longitude,latitude'
        radius: int = 1000,
        extensions: str = 'all'
    ) -> Dict[str, Any]:
        """坐标转地址"""
        params = {
            'location': location,
            'radius': radius,
            'extensions': extensions,
            'output': 'JSON'
        }

        return await self._make_request('/v3/geocode/regeo', params)

    # ============ POI搜索相关接口 ============

    async def text_search(
        self,
        keywords: str,
        city: str | None = None,
        types: str | None = None,
        citylimit: bool = False,
        children: int = 1,
        offset: int = 20,
        page: int = 1
    ) -> Dict[str, Any]:
        """关键字搜索POI"""
        params = {
            'keywords': keywords,
            'output': 'JSON',
            'offset': offset,
            'page': page,
            'children': children,
            'citylimit': 'true' if citylimit else 'false'
        }

        if city:
            params['city'] = city
        if types:
            params['types'] = types

        return await self._make_request('/v5/place/text', params)

    async def around_search(
        self,
        location: str,
        keywords: str,
        radius: int = 1000,
        types: str | None = None,
        offset: int = 20,
        page: int = 1
    ) -> Dict[str, Any]:
        """周边搜索POI"""
        params = {
            'location': location,
            'keywords': keywords,
            'radius': radius,
            'output': 'JSON',
            'offset': offset,
            'page': page
        }

        if types:
            params['types'] = types

        return await self._make_request('/v5/place/around', params)

    async def polygon_search(
        self,
        polygon: str,
        keywords: str,
        types: str | None = None
    ) -> Dict[str, Any]:
        """多边形搜索POI"""
        params = {
            'polygon': polygon,
            'keywords': keywords,
            'output': 'JSON'
        }

        if types:
            params['types'] = types

        return await self._make_request('/v5/place/polygon', params)

    async def poi_detail(
        self,
        id: str,
        extensions: str = 'all'
    ) -> Dict[str, Any]:
        """POI详情查询"""
        params = {
            'id': id,
            'extensions': extensions,
            'output': 'JSON'
        }

        return await self._make_request('/v5/place/detail', params)

    async def input_tips(
        self,
        keywords: str,
        city: str | None = None,
        type_: str | None = None,
        datatype: str = 'all'
    ) -> Dict[str, Any]:
        """输入提示"""
        params = {
            'keywords': keywords,
            'datatype': datatype,
            'output': 'JSON'
        }

        if city:
            params['city'] = city
        if type_:
            params['type'] = type_

        return await self._make_request('/v3/assistant/inputtips', params)

    # ============ 静态地图API ============

    async def static_map(
        self,
        location: str,
        zoom: int = 10,
        size: str = '600*400',
        markers: str | None = None,
        paths: str | None = None,
        traffic: str | None = None
    ) -> str:
        """静态地图"""
        params = {
            'location': location,
            'zoom': zoom,
            'size': size
        }

        if markers:
            params['markers'] = markers
        if paths:
            params['paths'] = paths
        if traffic:
            params['traffic'] = traffic

        return await self._make_request('/v3/staticmap', params, return_url=True)

    # ============ 路径规划API ============

    async def driving_route(
        self,
        origin: str,
        destination: str,
        strategy: int = 0,
        avoidpolygons: str | None = None,
        avoidroad: str | None = None
    ) -> Dict[str, Any]:
        """驾车路径规划"""
        # 如果origin和destination是地址，先进行地理编码
        if ',' not in origin and not origin.replace('.', '').isdigit():
            # 如果是地址，转换为坐标（这里简化处理，实际应该先调用地理编码）
            logger.warning(f"驾车路径建议使用坐标格式，地址格式可能导致错误: {origin=origin}")

        if ',' not in destination and not destination.replace('.', '').isdigit():
            # 如果是地址，转换为坐标（这里简化处理，实际应该先调用地理编码）
            logger.warning(f"驾车路径建议使用坐标格式，地址格式可能导致错误: {destination=destination}")

        params = {
            'origin': origin,
            'destination': destination,
            'strategy': strategy,
            'output': 'JSON'
        }

        if avoidpolygons:
            params['avoidpolygons'] = avoidpolygons
        if avoidroad:
            params['avoidroad'] = avoidroad

        return await self._make_request('/v5/direction/driving', params)

    async def walking_route(
        self,
        origin: str,
        destination: str
    ) -> Dict[str, Any]:
        """步行路径规划"""
        params = {
            'origin': origin,
            'destination': destination,
            'output': 'JSON'
        }

        return await self._make_request('/v5/direction/walking', params)

    async def bicycling_route(
        self,
        origin: str,
        destination: str
    ) -> Dict[str, Any]:
        """骑行路径规划"""
        params = {
            'origin': origin,
            'destination': destination,
            'output': 'JSON'
        }

        return await self._make_request('/v4/direction/bicycling', params)

    async def transit_route(
        self,
        origin: str,
        destination: str,
        city: str,
        cityd: str | None = None
    ) -> Dict[str, Any]:
        """公交路径规划"""
        params = {
            'origin': origin,
            'destination': destination,
            'city': city,
            'output': 'JSON'
        }

        if cityd:
            params['cityd'] = cityd

        return await self._make_request('/v5/direction/transit/integrated', params)

    # ============ 坐标转换API ============

    async def coordinate_convert(
        self,
        locations: str,
        coordsys: str = 'gps'
    ) -> Dict[str, Any]:
        """坐标转换"""
        params = {
            'locations': locations,
            'coordsys': coordsys,
            'output': 'JSON'
        }

        return await self._make_request('/v3/assistant/coordinate/convert', params)

    # ============ 行政区划查询API ============

    async def district_info(
        self,
        keywords: str,
        subdistrict: int = 1,
        extensions: str = 'base'
    ) -> Dict[str, Any]:
        """行政区划查询"""
        params = {
            'keywords': keywords,
            'subdistrict': subdistrict,
            'extensions': extensions,
            'output': 'JSON'
        }

        return await self._make_request('/v3/config/district', params)

    # ============ IP定位API ============

    async def ip_location(
        self,
        ip: str | None = None
    ) -> Dict[str, Any]:
        """IP定位"""
        params = {
            'output': 'JSON'
        }

        if ip:
            params['ip'] = ip

        return await self._make_request('/v3/ip', params)

    # ============ 天气查询API ============

    async def weather_info(
        self,
        city: str,
        extensions: str = 'base'
    ) -> Dict[str, Any]:
        """天气信息"""
        params = {
            'city': city,
            'extensions': extensions,
            'output': 'JSON'
        }

        return await self._make_request('/v3/weather/weather_info', params)

    # ============ 交通态势API ============

    async def rectangle_traffic(
        self,
        rectangle: str,
        level: int = 5,
        extensions: str = 'base'
    ) -> Dict[str, Any]:
        """矩形区域交通态势"""
        params = {
            'rectangle': rectangle,
            'level': level,
            'extensions': extensions,
            'output': 'JSON'
        }

        return await self._make_request('/v3/traffic/status/rectangle', params)

    async def circle_traffic(
        self,
        location: str,
        radius: int = 1000,
        level: int = 5,
        extensions: str = 'base'
    ) -> Dict[str, Any]:
        """圆形区域交通态势"""
        params = {
            'location': location,
            'radius': radius,
            'level': level,
            'extensions': extensions,
            'output': 'JSON'
        }

        return await self._make_request('/v3/traffic/status/circle', params)

    async def road_traffic(
        self,
        road_name: str,
        level: int = 5,
        extensions: str = 'base'
    ) -> Dict[str, Any]:
        """指定线路交通态势"""
        params = {
            'name': road_name,
            'level': level,
            'extensions': extensions,
            'output': 'JSON'
        }

        return await self._make_request('/v3/traffic/status/road', params)

    # ============ 地理围栏API ============

    async def create_geofence(
        self,
        name: str,
        center: str,
        radius: int,
        enable: str = 'true'
    ) -> Dict[str, Any]:
        """创建地理围栏"""
        params = {
            'name': name,
            'center': center,
            'radius': radius,
            'enable': enable,
            'output': 'JSON'
        }

        return await self._make_request('/v4/geofence/meta/create', params)

    async def search_geofence(
        self,
        center: str,
        radius: int = 500,
        page: int = 1,
        size: int = 20
    ) -> Dict[str, Any]:
        """查询地理围栏"""
        params = {
            'center': center,
            'radius': radius,
            'page': page,
            'size': size,
            'output': 'JSON'
        }

        return await self._make_request('/v4/geofence/meta/search', params)

    async def update_geofence(
        self,
        id: str,
        name: str | None = None,
        center: str | None = None,
        radius: int | None = None
    ) -> Dict[str, Any]:
        """更新地理围栏"""
        params = {
            'id': id,
            'output': 'JSON'
        }

        if name:
            params['name'] = name
        if center:
            params['center'] = center
        if radius:
            params['radius'] = radius

        return await self._make_request('/v4/geofence/meta/update', params)

    async def delete_geofence(
        self,
        id: str
    ) -> Dict[str, Any]:
        """删除地理围栏"""
        params = {
            'id': id,
            'output': 'JSON'
        }

        return await self._make_request('/v4/geofence/meta/delete', params)

class RateLimiter:
    """API限流器"""

    def __init__(self, requests_per_minute: int, requests_per_second: int):
        self.requests_per_minute = requests_per_minute
        self.requests_per_second = requests_per_second
        self.requests = []

    async def acquire(self):
        """获取请求许可"""
        now = time.time()

        # 清理过期的请求记录
        self.requests = [req_time for req_time in self.requests
                        if now - req_time < 60]

        # 检查每分钟限制
        if len(self.requests) >= self.requests_per_minute:
            sleep_time = 60 - (now - self.requests[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        # 检查每秒限制
        recent_requests = [req_time for req_time in self.requests
                          if now - req_time < 1]
        if len(recent_requests) >= self.requests_per_second:
            await asyncio.sleep(1)

        self.requests.append(now)

class AmapApiError(Exception):
    """高德地图API错误"""

    def __init__(self, message: str, error_code: str | None = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code

    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message