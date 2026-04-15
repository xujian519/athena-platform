"""
地理编码工具
Geocoding Tool
"""

from typing import Any

import structlog

from ..api.gaode_client import AmapApiClient

logger = structlog.get_logger(__name__)

class GeocodingTool:
    """地理编码工具"""

    name: str = 'gaode_geocode'
    description: str = '高德地图地理编码服务，提供地址与坐标的相互转换'

    def __init__(self, api_client: AmapApiClient):
        self.api_client = api_client

    async def call(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        地理编码处理

        Args:
            arguments: 包含以下字段的字典
                - operation: 操作类型 ('geocode' 或 'reverse_geocode')
                - address: 地址文本 (地理编码时必需)
                - location: 坐标点 '经度,纬度' (逆地理编码时必需)
                - city: 城市名称 (可选)
                - radius: 搜索半径，单位米 (逆地理编码时使用，默认1000)

        Returns:
            包含地理编码结果的字典
        """
        operation = arguments.get('operation')

        if operation == 'geocode':
            return await self._handle_geocoding(arguments)
        elif operation == 'reverse_geocode':
            return await self._handle_reverse_geocoding(arguments)
        else:
            raise ValueError(f"不支持的操作类型: {operation}")

    async def _handle_geocoding(self, args: dict[str, Any]) -> dict[str, Any]:
        """处理地址转坐标"""
        address = args.get('address')
        if not address:
            raise ValueError('地址参数不能为空')

        city = args.get('city')
        district = args.get('district')

        logger.info(
            '执行地理编码',
            address=address,
            city=city,
            district=district
        )

        try:
            result = await self.api_client.geocoding(address, city, district)

            # 提取并格式化结果
            geocodes = result.get('geocodes', [])
            if not geocodes:
                return {
                    'success': False,
                    'message': '未找到匹配的地址',
                    'count': 0,
                    'results': []
                }

            formatted_results = []
            for geocode in geocodes:
                formatted_result = {
                    'formatted_address': geocode.get('formatted_address'),
                    'location': {
                        'longitude': float(geocode.get('location', '').split(',')[0]),
                        'latitude': float(geocode.get('location', '').split(',')[1])
                    },
                    'level': geocode.get('level'),
                    'adcode': geocode.get('adcode'),
                    'city': geocode.get('city'),
                    'district': geocode.get('district'),
                    'province': geocode.get('province'),
                    'country': geocode.get('country'),
                    'confidence': geocode.get('confidence')
                }
                formatted_results.append(formatted_result)

            return {
                'success': True,
                'message': '地理编码成功',
                'count': len(formatted_results),
                'results': formatted_results,
                'info': result.get('info'),
                'infocode': result.get('infocode')
            }

        except Exception as e:
            logger.error(
                '地理编码失败',
                address=address,
                error=str(e)
            )
            return {
                'success': False,
                'message': f"地理编码失败: {str(e)}",
                'count': 0,
                'results': []
            }

    async def _handle_reverse_geocoding(self, args: dict[str, Any]) -> dict[str, Any]:
        """处理坐标转地址"""
        location = args.get('location')
        if not location:
            raise ValueError('坐标参数不能为空')

        radius = args.get('radius', 1000)
        extensions = args.get('extensions', 'all')

        logger.info(
            '执行逆地理编码',
            location=location,
            radius=radius,
            extensions=extensions
        )

        try:
            result = await self.api_client.reverse_geocoding(
                location, radius, extensions
            )

            # 提取并格式化结果
            regeocode = result.get('regeocode')
            if not regeocode:
                return {
                    'success': False,
                    'message': '未找到匹配的地址信息',
                    'location': location,
                    'address': None,
                    'pois': []
                }

            # 格式化地址信息
            address_component = regeocode.get('address_component', {})
            formatted_address = regeocode.get('formatted_address')

            address_info = {
                'formatted_address': formatted_address,
                'country': address_component.get('country'),
                'province': address_component.get('province'),
                'city': address_component.get('city'),
                'citycode': address_component.get('citycode'),
                'district': address_component.get('district'),
                'adcode': address_component.get('adcode'),
                'township': address_component.get('township'),
                'townshipcode': address_component.get('townshipcode'),
                'street_number': {
                    'number': address_component.get('street_number', {}).get('number'),
                    'location': address_component.get('street_number', {}).get('location'),
                    'direction': address_component.get('street_number', {}).get('direction'),
                    'distance': address_component.get('street_number', {}).get('distance')
                }
            }

            # 提取POI信息
            pois = regeocode.get('pois', [])
            formatted_pois = []
            for poi in pois:
                formatted_poi = {
                    'id': poi.get('id'),
                    'name': poi.get('name'),
                    'type': poi.get('type'),
                    'tel': poi.get('tel'),
                    'address': poi.get('address'),
                    'location': poi.get('location'),
                    'distance': poi.get('distance'),
                    'direction': poi.get('direction')
                }
                formatted_pois.append(formatted_poi)

            return {
                'success': True,
                'message': '逆地理编码成功',
                'location': location,
                'address': address_info,
                'pois': formatted_pois,
                'pois_count': len(formatted_pois),
                'info': result.get('info'),
                'infocode': result.get('infocode')
            }

        except Exception as e:
            logger.error(
                '逆地理编码失败',
                location=location,
                error=str(e)
            )
            return {
                'success': False,
                'message': f"逆地理编码失败: {str(e)}",
                'location': location,
                'address': None,
                'pois': []
            }

    def get_input_schema(self) -> dict[str, Any]:
        """获取输入参数模式"""
        return {
            'type': 'object',
            'properties': {
                'operation': {
                    'type': 'string',
                    'enum': ['geocode', 'reverse_geocode'],
                    'description': '操作类型: geocode(地址转坐标) 或 reverse_geocode(坐标转地址)'
                },
                'address': {
                    'type': 'string',
                    'description': '需要转换的地址文本'
                },
                'location': {
                    'type': 'string',
                    'pattern': "^-?\\d+\\.\\d+,-?\\d+\\.\\d+$",
                    'description': '经纬度坐标，格式: 经度,纬度'
                },
                'city': {
                    'type': 'string',
                    'description': '城市名称，用于提高搜索精度'
                },
                'district': {
                    'type': 'string',
                    'description': '区县名称，用于提高搜索精度'
                },
                'radius': {
                    'type': 'integer',
                    'minimum': 1,
                    'maximum': 50000,
                    'description': '搜索半径，单位米(1-50000)，默认1000'
                },
                'extensions': {
                    'type': 'string',
                    'enum': ['base', 'all'],
                    'description': '返回结果控制，base(基础信息) 或 all(全部信息)'
                }
            },
            'required': ['operation']
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
                'count': {
                    'type': 'integer',
                    'description': '返回结果数量'
                },
                'results': {
                    'type': 'array',
                    'description': '地理编码结果列表'
                },
                'location': {
                    'type': 'string',
                    'description': '查询的坐标点'
                },
                'address': {
                    'type': 'object',
                    'description': '地址详细信息'
                },
                'pois': {
                    'type': 'array',
                    'description': '周边POI信息列表'
                },
                'pois_count': {
                    'type': 'integer',
                    'description': 'POI数量'
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
