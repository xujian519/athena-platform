"""
POI搜索工具
POI Search Tool
"""

from typing import Any

import structlog

from ..api.gaode_client import AmapApiClient

logger = structlog.get_logger(__name__)

class POISearchTool:
    """POI搜索工具"""

    name: str = 'gaode_poi_search'
    description: str = '高德地图POI搜索服务，提供关键字搜索、周边搜索、多边形搜索等功能'

    def __init__(self, api_client: AmapApiClient):
        self.api_client = api_client

    async def call(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        POI搜索处理

        Args:
            arguments: 包含以下字段的字典
                - search_type: 搜索类型 ('text', 'around', 'polygon')
                - keywords: 搜索关键词
                - city: 城市名称
                - location: 中心点坐标 '经度,纬度' (周边和多边形搜索时必需)
                - radius: 搜索半径，单位米 (周边搜索时使用，默认1000)
                - types: POI类型代码
                - polygon: 多边形坐标点 (多边形搜索时使用)
                - citylimit: 是否限制在当前城市 (文本搜索时使用)
                - page: 页码，默认1
                - offset: 每页数量，默认20

        Returns:
            包含POI搜索结果的字典
        """
        search_type = arguments.get('search_type')

        if search_type == 'text':
            return await self._handle_text_search(arguments)
        elif search_type == 'around':
            return await self._handle_around_search(arguments)
        elif search_type == 'polygon':
            return await self._handle_polygon_search(arguments)
        else:
            raise ValueError(f"不支持的搜索类型: {search_type}")

    async def _handle_text_search(self, args: dict[str, Any]) -> dict[str, Any]:
        """处理文本搜索"""
        keywords = args.get('keywords')
        if not keywords:
            raise ValueError('搜索关键词不能为空')

        city = args.get('city')
        types = args.get('types')
        citylimit = args.get('citylimit', False)
        children = args.get('children', 1)
        offset = args.get('offset', 20)
        page = args.get('page', 1)

        logger.info(
            '执行POI文本搜索',
            keywords=keywords,
            city=city,
            types=types,
            page=page
        )

        try:
            result = await self.api_client.text_search(
                keywords=keywords,
                city=city,
                types=types,
                citylimit=citylimit,
                children=children,
                offset=offset,
                page=page
            )

            # 提取并格式化结果
            pois = result.get('pois', [])
            if not pois:
                return {
                    'success': True,
                    'message': '未找到匹配的POI',
                    'search_type': 'text',
                    'keywords': keywords,
                    'city': city,
                    'page': page,
                    'count': 0,
                    'total_count': int(result.get('count', 0)),
                    'suggestions': result.get('suggestion', {}).get('cities', []),
                    'results': []
                }

            formatted_results = []
            for poi in pois:
                formatted_result = {
                    'id': poi.get('id'),
                    'name': poi.get('name'),
                    'type': poi.get('type'),
                    'typecode': poi.get('typecode'),
                    'address': poi.get('address'),
                    'location': poi.get('location'),
                    'tel': poi.get('tel'),
                    'distance': poi.get('distance'),
                    'direction': poi.get('direction'),
                    'biz': {
                        'rating': poi.get('biz', {}).get('rating'),
                        'cost': poi.get('biz', {}).get('cost'),
                        'opentime': poi.get('biz', {}).get('opentime'),
                        'recommend': poi.get('biz', {}).get('recommend')
                    },
                    'photos': poi.get('photos', []),
                    'gridcode': poi.get('gridcode'),
                    'adname': poi.get('adname'),
                    'adcode': poi.get('adcode'),
                    'cityname': poi.get('cityname'),
                    'citycode': poi.get('citycode')
                }
                formatted_results.append(formatted_result)

            return {
                'success': True,
                'message': 'POI文本搜索成功',
                'search_type': 'text',
                'keywords': keywords,
                'city': city,
                'page': page,
                'offset': offset,
                'count': len(formatted_results),
                'total_count': int(result.get('count', 0)),
                'suggestions': result.get('suggestion', {}).get('cities', []),
                'results': formatted_results,
                'info': result.get('info'),
                'infocode': result.get('infocode')
            }

        except Exception as e:
            logger.error(
                'POI文本搜索失败',
                keywords=keywords,
                error=str(e)
            )
            return {
                'success': False,
                'message': f"POI文本搜索失败: {str(e)}",
                'search_type': 'text',
                'keywords': keywords,
                'count': 0,
                'total_count': 0,
                'results': []
            }

    async def _handle_around_search(self, args: dict[str, Any]) -> dict[str, Any]:
        """处理周边搜索"""
        keywords = args.get('keywords')
        location = args.get('location')
        if not location:
            raise ValueError('中心点坐标不能为空')

        radius = args.get('radius', 1000)
        types = args.get('types')
        offset = args.get('offset', 20)
        page = args.get('page', 1)

        logger.info(
            '执行POI周边搜索',
            keywords=keywords,
            location=location,
            radius=radius,
            page=page
        )

        try:
            result = await self.api_client.around_search(
                location=location,
                keywords=keywords,
                radius=radius,
                types=types,
                offset=offset,
                page=page
            )

            # 提取并格式化结果
            pois = result.get('pois', [])
            if not pois:
                return {
                    'success': True,
                    'message': '未找到周边的POI',
                    'search_type': 'around',
                    'keywords': keywords,
                    'location': location,
                    'radius': radius,
                    'page': page,
                    'count': 0,
                    'total_count': int(result.get('count', 0)),
                    'results': []
                }

            formatted_results = []
            for poi in pois:
                formatted_result = {
                    'id': poi.get('id'),
                    'name': poi.get('name'),
                    'type': poi.get('type'),
                    'typecode': poi.get('typecode'),
                    'address': poi.get('address'),
                    'location': poi.get('location'),
                    'tel': poi.get('tel'),
                    'distance': poi.get('distance'),
                    'direction': poi.get('direction'),
                    'biz': {
                        'rating': poi.get('biz', {}).get('rating'),
                        'cost': poi.get('biz', {}).get('cost'),
                        'opentime': poi.get('biz', {}).get('opentime'),
                        'recommend': poi.get('biz', {}).get('recommend')
                    },
                    'photos': poi.get('photos', []),
                    'gridcode': poi.get('gridcode'),
                    'adname': poi.get('adname'),
                    'adcode': poi.get('adcode'),
                    'cityname': poi.get('cityname'),
                    'citycode': poi.get('citycode')
                }
                formatted_results.append(formatted_result)

            return {
                'success': True,
                'message': 'POI周边搜索成功',
                'search_type': 'around',
                'keywords': keywords,
                'location': location,
                'radius': radius,
                'page': page,
                'offset': offset,
                'count': len(formatted_results),
                'total_count': int(result.get('count', 0)),
                'results': formatted_results,
                'info': result.get('info'),
                'infocode': result.get('infocode')
            }

        except Exception as e:
            logger.error(
                'POI周边搜索失败',
                keywords=keywords,
                location=location,
                error=str(e)
            )
            return {
                'success': False,
                'message': f"POI周边搜索失败: {str(e)}",
                'search_type': 'around',
                'keywords': keywords,
                'location': location,
                'count': 0,
                'total_count': 0,
                'results': []
            }

    async def _handle_polygon_search(self, args: dict[str, Any]) -> dict[str, Any]:
        """处理多边形搜索"""
        # 注意：当前高德地图API暂不直接支持多边形搜索，
        # 这里提供基于多个点的近似搜索逻辑
        keywords = args.get('keywords')
        polygon = args.get('polygon')
        if not polygon:
            raise ValueError('多边形坐标不能为空')

        # 解析多边形坐标点
        try:
            points = [point.strip() for point in polygon.split(';')]
            if len(points) < 3:
                raise ValueError('多边形至少需要3个点')
        except Exception as e:
            raise ValueError(f"多边形坐标格式错误: {str(e)}") from e

        logger.info(
            '执行POI多边形搜索',
            keywords=keywords,
            polygon=polygon,
            points_count=len(points)
        )

        # 计算多边形中心点
        coords = []
        for point in points:
            lon, lat = map(float, point.split(','))
            coords.append((lon, lat))

        center_lon = sum(c[0] for c in coords) / len(coords)
        center_lat = sum(c[1] for c in coords) / len(coords)
        center_location = f"{center_lon},{center_lat}"

        # 计算大致半径（多边形边界到中心的最大距离）
        import math
        max_distance = 0
        for lon, lat in coords:
            distance = math.sqrt((lon - center_lon)**2 + (lat - center_lat)**2) * 111000  # 度到米的粗略转换
            max_distance = max(max_distance, distance)

        # 使用周边搜索作为近似
        args_copy = args.copy()
        args_copy['search_type'] = 'around'
        args_copy['location'] = center_location
        args_copy['radius'] = int(max_distance * 1.2)  # 稍微扩大搜索范围

        result = await self._handle_around_search(args_copy)
        result['search_type'] = 'polygon'
        result['polygon'] = polygon
        result['center_location'] = center_location

        # 过滤结果，只返回真正在多边形内的POI
        if result['success'] and result['results']:
            filtered_results = []
            for poi in result['results']:
                poi_location = poi.get('location', '')
                if poi_location:
                    try:
                        poi_lon, poi_lat = map(float, poi_location.split(','))
                        if self._point_in_polygon(poi_lon, poi_lat, coords):
                            filtered_results.append(poi)
                    except Exception:
                        continue

            result['results'] = filtered_results
            result['count'] = len(filtered_results)

        return result

    def _point_in_polygon(self, x: float, y: float, polygon: list[tuple]) -> bool:
        """判断点是否在多边形内（射线法）"""
        n = len(polygon)
        inside = False

        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def get_input_schema(self) -> dict[str, Any]:
        """获取输入参数模式"""
        return {
            'type': 'object',
            'properties': {
                'search_type': {
                    'type': 'string',
                    'enum': ['text', 'around', 'polygon'],
                    'description': '搜索类型: text(文本搜索), around(周边搜索), polygon(多边形搜索)'
                },
                'keywords': {
                    'type': 'string',
                    'description': "搜索关键词，如'餐厅'、'加油站'、'医院'等"
                },
                'city': {
                    'type': 'string',
                    'description': '城市名称，用于提高搜索精度'
                },
                'location': {
                    'type': 'string',
                    'pattern': "^-?\\d+\\.\\d+,-?\\d+\\.\\d+$",
                    'description': '中心点坐标，格式: 经度,纬度'
                },
                'radius': {
                    'type': 'integer',
                    'minimum': 1,
                    'maximum': 50000,
                    'description': '搜索半径，单位米(1-50000)，默认1000'
                },
                'types': {
                    'type': 'string',
                    'description': 'POI类型代码，可从高德地图API文档获取'
                },
                'polygon': {
                    'type': 'string',
                    'pattern': "^-?\\d+\\.\\d+,-?\\d+\\.\\d+(;[-]?\\d+\\.\\d+,-?\\d+\\.\\d+)*$",
                    'description': '多边形坐标点，格式: 经度1,纬度1;经度2,纬度2;... 至少3个点'
                },
                'citylimit': {
                    'type': 'boolean',
                    'description': '是否限制在当前城市内搜索'
                },
                'page': {
                    'type': 'integer',
                    'minimum': 1,
                    'description': '页码，默认1'
                },
                'offset': {
                    'type': 'integer',
                    'minimum': 1,
                    'maximum': 50,
                    'description': '每页数量，默认20，最大50'
                }
            },
            'required': ['search_type', 'keywords']
        }

    def get_output_schema(self) -> dict[str, Any]:
        """获取输出结果模式"""
        return {
            'type': 'object',
            'properties': {
                'success': {
                    'type': 'boolean',
                    'description': '操作是否成功'
                },
                'message': {
                    'type': 'string',
                    'description': '操作结果消息'
                },
                'search_type': {
                    'type': 'string',
                    'description': '搜索类型'
                },
                'keywords': {
                    'type': 'string',
                    'description': '搜索关键词'
                },
                'city': {
                    'type': 'string',
                    'description': '搜索城市'
                },
                'location': {
                    'type': 'string',
                    'description': '搜索中心点'
                },
                'radius': {
                    'type': 'integer',
                    'description': '搜索半径'
                },
                'polygon': {
                    'type': 'string',
                    'description': '搜索多边形'
                },
                'page': {
                    'type': 'integer',
                    'description': '当前页码'
                },
                'offset': {
                    'type': 'integer',
                    'description': '每页数量'
                },
                'count': {
                    'type': 'integer',
                    'description': '当前页结果数量'
                },
                'total_count': {
                    'type': 'integer',
                    'description': '总结果数量'
                },
                'suggestions': {
                    'type': 'array',
                    'description': '搜索建议'
                },
                'results': {
                    'type': 'array',
                    'description': 'POI搜索结果列表'
                },
                'info': {
                    'type': 'string',
                    'description': 'API返回状态信息'
                },
                'infocode': {
                    'type': 'string',
                    'description': 'API返回状态码'
                }
            }
        }
