"""
交通服务工具
Traffic Service Tool
"""

import logging
from typing import Any, Dict, List, Optional

import structlog
from mcp.types import Tool

from ..api.extended_gaode_client import ExtendedAmapApiClient

logger = structlog.get_logger(__name__)

class TrafficServiceTool:
    """交通服务工具"""

    name: str = 'gaode_traffic_service'
    description: str = '高德地图交通服务，提供实时交通态势查询功能'

    def __init__(self, api_client: ExtendedAmapApiClient):
        self.api_client = api_client

    async def call(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        交通服务处理

        Args:
            arguments: 包含以下字段的字典
                - service: 服务类型 ('rectangle', 'circle', 'road')
                - location: 位置坐标 (经度,纬度)
                - rectangle: 矩形区域坐标
                - road_name: 道路名称
                - radius: 搜索半径 (米)
                - level: 道路等级 (1-7)
                - extensions: 返回结果控制

        Returns:
            包含交通服务结果的字典
        """
        service = arguments.get('service')

        if service == 'rectangle':
            return await self._handle_rectangle_traffic(arguments)
        elif service == 'circle':
            return await self._handle_circle_traffic(arguments)
        elif service == 'road':
            return await self._handle_road_traffic(arguments)
        else:
            raise ValueError(f"不支持的服务类型: {service}")

    async def _handle_rectangle_traffic(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """处理矩形区域交通态势"""
        rectangle = args.get('rectangle')
        if not rectangle:
            raise ValueError('矩形区域坐标不能为空')

        level = args.get('level', 5)
        extensions = args.get('extensions', 'base')

        logger.info(
            '查询矩形区域交通态势',
            rectangle=rectangle,
            level=level,
            extensions=extensions
        )

        try:
            result = await self.api_client.rectangle_traffic(
                rectangle=rectangle,
                level=level,
                extensions=extensions
            )

            # 提取交通信息
            traffic_info = result.get('traffic', {})
            description = result.get('description', '')
            evaluation = result.get('evaluation', {})

            formatted_result = {
                'service': 'rectangle_traffic',
                'rectangle': rectangle,
                'level': level,
                'extensions': extensions,
                'description': description,
                'evaluation': {
                    'congestion': evaluation.get('congestion', ''),
                    'status': evaluation.get('status', ''),
                    'description': evaluation.get('description', ''),
                    'expedite': evaluation.get('expedite', ''),
                    'unsuggest': evaluation.get('unsuggest', '')
                },
                'roads': []
            }

            # 提取道路信息
            if 'roads' in traffic_info:
                for road in traffic_info.get('roads', [])[:50]:  # 显示前50条道路
                    road_info = {
                        'name': road.get('name', ''),
                        'status': road.get('status', ''),
                        'direction': road.get('direction', ''),
                        'speed': road.get('speed', ''),
                        'lci': road.get('lci', ''),
                        'polyline': road.get('polyline', '')
                    }
                    formatted_result['roads'].append(road_info)

            return {
                'success': True,
                'message': '矩形区域交通态势查询成功',
                'service': 'rectangle_traffic',
                'result': formatted_result,
                'total_roads': len(formatted_result['roads']),
                'info': result.get('info'),
                'infocode': result.get('infocode')
            }

        except Exception as e:
            logger.error(
                '矩形区域交通态势查询失败',
                rectangle=rectangle,
                error=str(e)
            )
            return {
                'success': False,
                'message': f"矩形区域交通态势查询失败: {str(e)}",
                'service': 'rectangle_traffic'
            }

    async def _handle_circle_traffic(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """处理圆形区域交通态势"""
        location = args.get('location')
        if not location:
            raise ValueError('位置坐标不能为空')

        radius = args.get('radius', 1000)
        level = args.get('level', 5)
        extensions = args.get('extensions', 'base')

        logger.info(
            '查询圆形区域交通态势',
            location=location,
            radius=radius,
            level=level,
            extensions=extensions
        )

        try:
            result = await self.api_client.circle_traffic(
                location=location,
                radius=radius,
                level=level,
                extensions=extensions
            )

            # 提取交通信息
            traffic_info = result.get('traffic', {})
            description = result.get('description', '')
            evaluation = result.get('evaluation', {})

            formatted_result = {
                'service': 'circle_traffic',
                'location': location,
                'radius': radius,
                'level': level,
                'extensions': extensions,
                'description': description,
                'evaluation': {
                    'congestion': evaluation.get('congestion', ''),
                    'status': evaluation.get('status', ''),
                    'description': evaluation.get('description', ''),
                    'expedite': evaluation.get('expedite', ''),
                    'unsuggest': evaluation.get('unsuggest', '')
                },
                'roads': []
            }

            # 提取道路信息
            if 'roads' in traffic_info:
                for road in traffic_info.get('roads', [])[:50]:  # 显示前50条道路
                    road_info = {
                        'name': road.get('name', ''),
                        'status': road.get('status', ''),
                        'direction': road.get('direction', ''),
                        'speed': road.get('speed', ''),
                        'lci': road.get('lci', ''),
                        'polyline': road.get('polyline', ''),
                        'distance': road.get('distance', 0)
                    }
                    formatted_result['roads'].append(road_info)

            return {
                'success': True,
                'message': '圆形区域交通态势查询成功',
                'service': 'circle_traffic',
                'result': formatted_result,
                'total_roads': len(formatted_result['roads']),
                'info': result.get('info'),
                'infocode': result.get('infocode')
            }

        except Exception as e:
            logger.error(
                '圆形区域交通态势查询失败',
                location=location,
                radius=radius,
                error=str(e)
            )
            return {
                'success': False,
                'message': f"圆形区域交通态势查询失败: {str(e)}",
                'service': 'circle_traffic'
            }

    async def _handle_road_traffic(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """处理指定线路交通态势"""
        road_name = args.get('road_name')
        if not road_name:
            raise ValueError('道路名称不能为空')

        level = args.get('level', 5)
        extensions = args.get('extensions', 'base')

        logger.info(
            '查询指定线路交通态势',
            road_name=road_name,
            level=level,
            extensions=extensions
        )

        try:
            result = await self.api_client.road_traffic(
                road_name=road_name,
                level=level,
                extensions=extensions
            )

            # 提取交通信息
            traffic_info = result.get('traffic', {})
            description = result.get('description', '')
            evaluation = result.get('evaluation', {})

            formatted_result = {
                'service': 'road_traffic',
                'road_name': road_name,
                'level': level,
                'extensions': extensions,
                'description': description,
                'evaluation': {
                    'congestion': evaluation.get('congestion', ''),
                    'status': evaluation.get('status', ''),
                    'description': evaluation.get('description', ''),
                    'expedite': evaluation.get('expedite', ''),
                    'unsuggest': evaluation.get('unsuggest', '')
                }
            }

            # 提取路段信息
            if 'roads' in traffic_info:
                road_segments = []
                for road in traffic_info.get('roads', []):
                    segment_info = {
                        'name': road.get('name', ''),
                        'status': road.get('status', ''),
                        'direction': road.get('direction', ''),
                        'speed': road.get('speed', ''),
                        'lci': road.get('lci', ''),
                        'polyline': road.get('polyline', ''),
                        'distance': road.get('distance', 0)
                    }
                    road_segments.append(segment_info)

                formatted_result['segments'] = road_segments
                formatted_result['total_segments'] = len(road_segments)

            return {
                'success': True,
                'message': '指定线路交通态势查询成功',
                'service': 'road_traffic',
                'result': formatted_result,
                'info': result.get('info'),
                'infocode': result.get('infocode')
            }

        except Exception as e:
            logger.error(
                '指定线路交通态势查询失败',
                road_name=road_name,
                error=str(e)
            )
            return {
                'success': False,
                'message': f"指定线路交通态势查询失败: {str(e)}",
                'service': 'road_traffic'
            }

    def get_input_schema(self) -> Dict[str, Any]:
        """获取输入参数模式"""
        return {
            'type': 'object',
            'properties': {
                'service': {
                    'type': 'string',
                    'enum': ['rectangle', 'circle', 'road'],
                    'description': '服务类型: rectangle(矩形区域), circle(圆形区域), road(指定道路)'
                },
                'rectangle': {
                    'type': 'string',
                    'description': '矩形区域坐标，格式: 左下经度,左下纬度;右上经度,右上纬度'
                },
                'location': {
                    'type': 'string',
                    'description': '中心位置坐标，格式: 经度,纬度'
                },
                'radius': {
                    'type': 'integer',
                    'minimum': 100,
                    'maximum': 50000,
                    'description': '搜索半径，单位米'
                },
                'road_name': {
                    'type': 'string',
                    'description': '道路名称'
                },
                'level': {
                    'type': 'integer',
                    'minimum': 1,
                    'maximum': 7,
                    'description': '道路等级 (1-7，默认5)'
                },
                'extensions': {
                    'type': 'string',
                    'enum': ['base', 'all'],
                    'description': '返回结果控制: base(基础信息) 或 all(全部信息)'
                }
            },
            'required': ['service']
        }

    def get_output_schema(self) -> Dict[str, Any]:
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
                'service': {
                    'type': 'string',
                    'description': '服务类型'
                },
                'result': {
                    'type': 'object',
                    'description': '交通态势详情'
                },
                'total_roads': {
                    'type': 'integer',
                    'description': '道路总数'
                },
                'total_segments': {
                    'type': 'integer',
                    'description': '路段总数'
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
