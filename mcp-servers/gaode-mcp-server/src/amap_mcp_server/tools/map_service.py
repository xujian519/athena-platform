"""
地图服务工具
Map Service Tool
"""

from typing import Any

import structlog

from ..api.extended_gaode_client import ExtendedAmapApiClient

logger = structlog.get_logger(__name__)

class MapServiceTool:
    """地图服务工具"""

    name: str = 'gaode_map_service'
    description: str = '高德地图服务，提供静态地图、天气查询、坐标转换、行政区划等功能'

    def __init__(self, api_client: ExtendedAmapApiClient):
        self.api_client = api_client

    async def call(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        地图服务处理

        Args:
            arguments: 包含以下字段的字典
                - service: 服务类型 ('static_map', 'weather', 'coordinate_convert', 'district', 'ip_location')
                - location: 位置坐标 (经度,纬度)
                - zoom: 缩放级别
                - size: 地图尺寸 '宽*高'
                - markers: 标记点信息
                - city: 城市名称
                - coordsys: 坐标系统
                - ip: IP地址

        Returns:
            包含地图服务结果的字典
        """
        service = arguments.get('service')

        if service == 'static_map':
            return await self._handle_static_map(arguments)
        elif service == 'weather':
            return await self._handle_weather(arguments)
        elif service == 'coordinate_convert':
            return await self._handle_coordinate_convert(arguments)
        elif service == 'district':
            return await self._handle_district(arguments)
        elif service == 'ip_location':
            return await self._handle_ip_location(arguments)
        else:
            raise ValueError(f"不支持的服务类型: {service}")

    async def _handle_static_map(self, args: dict[str, Any]) -> dict[str, Any]:
        """处理静态地图"""
        location = args.get('location')
        if not location:
            raise ValueError('位置坐标不能为空')

        zoom = args.get('zoom', 10)
        size = args.get('size', '600*400')
        markers = args.get('markers')

        logger.info(
            '生成静态地图',
            location=location,
            zoom=zoom,
            size=size
        )

        try:
            map_url = await self.api_client.static_map(
                location=location,
                zoom=zoom,
                size=size,
                markers=markers
            )

            return {
                'success': True,
                'message': '静态地图生成成功',
                'service': 'static_map',
                'location': location,
                'zoom': zoom,
                'size': size,
                'map_url': map_url,
                'usage': f"您可以在浏览器中打开此URL查看地图: {map_url}"
            }

        except Exception as e:
            logger.error(
                '静态地图生成失败',
                location=location,
                error=str(e)
            )
            return {
                'success': False,
                'message': f"静态地图生成失败: {str(e)}",
                'service': 'static_map'
            }

    async def _handle_weather(self, args: dict[str, Any]) -> dict[str, Any]:
        """处理天气查询"""
        city = args.get('city')
        if not city:
            raise ValueError('城市名称不能为空')

        extensions = args.get('extensions', 'base')

        logger.info(
            '查询天气信息',
            city=city,
            extensions=extensions
        )

        try:
            result = await self.api_client.weather_info(
                city=city,
                extensions=extensions
            )

            # 提取天气信息
            weather_info = result.get('lives', [])
            forecasts = result.get('forecasts', [])

            formatted_result = {
                'city': city,
                'extensions': extensions,
                'current_weather': None,
                'forecast': None
            }

            # 当前天气
            if weather_info:
                current = weather_info[0]
                formatted_result['current_weather'] = {
                    'weather': current.get('weather', ''),
                    'temperature': current.get('temperature', ''),
                    'winddirection': current.get('winddirection', ''),
                    'windpower': current.get('windpower', ''),
                    'humidity': current.get('humidity', ''),
                    'reporttime': current.get('reporttime', '')
                }

            # 天气预报
            if forecasts:
                forecast_list = []
                for forecast in forecasts[:7]:  # 显示未来7天
                    forecast_info = {
                        'date': forecast.get('date', ''),
                        'week': forecast.get('week', ''),
                        'dayweather': forecast.get('dayweather', ''),
                        'nightweather': forecast.get('nightweather', ''),
                        'daytemp': forecast.get('daytemp', ''),
                        'nighttemp': forecast.get('nighttemp', ''),
                        'daywind': forecast.get('daywind', ''),
                        'nightwind': forecast.get('nightwind', ''),
                        'daypower': forecast.get('daypower', ''),
                        'nightpower': forecast.get('nightpower', '')
                    }
                    forecast_list.append(forecast_info)

                formatted_result['forecast'] = forecast_list

            return {
                'success': True,
                'message': '天气查询成功',
                'service': 'weather',
                'result': formatted_result,
                'info': result.get('info'),
                'infocode': result.get('infocode')
            }

        except Exception as e:
            logger.error(
                '天气查询失败',
                city=city,
                error=str(e)
            )
            return {
                'success': False,
                'message': f"天气查询失败: {str(e)}",
                'service': 'weather'
            }

    async def _handle_coordinate_convert(self, args: dict[str, Any]) -> dict[str, Any]:
        """处理坐标转换"""
        locations = args.get('locations')
        if not locations:
            raise ValueError('坐标位置不能为空')

        coordsys = args.get('coordsys', 'gps')

        logger.info(
            '坐标转换',
            locations=locations,
            coordsys=coordsys
        )

        try:
            result = await self.api_client.coordinate_convert(
                locations=locations,
                coordsys=coordsys
            )

            # 提取转换结果
            converted_locations = []

            # 检查API返回状态
            if result.get('status') == '1' and 'locations' in result:
                locations_data = result['locations']
                # 如果返回的是字符串，需要解析
                if isinstance(locations_data, str):
                    # 处理返回格式如 "116.651694,39.975359;116.651694,39.975359"
                    locations_list = locations_data.split(';')
                    for loc_str in locations_list:
                        if loc_str:
                            coord_parts = loc_str.split(',')
                            if len(coord_parts) >= 2:
                                converted_info = {
                                    'original': locations,
                                    'converted': loc_str,
                                    'lon': coord_parts[0],
                                    'lat': coord_parts[1]
                                }
                                converted_locations.append(converted_info)
                elif isinstance(locations_data, list):
                    for loc in locations_data:
                        converted_info = {
                            'original': f"{loc.get('x', '')},{loc.get('y', '')}",
                            'converted': f"{loc.get('lon', '')},{loc.get('lat', '')}",
                            'offset_x': loc.get('offset_x', 0),
                            'offset_y': loc.get('offset_y', 0),
                            'level': loc.get('level', '0')
                        }
                        converted_locations.append(converted_info)

            return {
                'success': True,
                'message': '坐标转换成功',
                'service': 'coordinate_convert',
                'coordsys_from': coordsys,
                'coordsys_to': 'gcj02',
                'locations': converted_locations,
                'total_count': len(converted_locations)
            }

        except Exception as e:
            logger.error(
                '坐标转换失败',
                locations=locations,
                error=str(e)
            )
            return {
                'success': False,
                'message': f"坐标转换失败: {str(e)}",
                'service': 'coordinate_convert'
            }

    async def _handle_district(self, args: dict[str, Any]) -> dict[str, Any]:
        """处理行政区划查询"""
        keywords = args.get('keywords')
        if not keywords:
            raise ValueError('查询关键词不能为空')

        subdistrict = args.get('subdistrict', 1)
        extensions = args.get('extensions', 'base')

        logger.info(
            '查询行政区划',
            keywords=keywords,
            subdistrict=subdistrict,
            extensions=extensions
        )

        try:
            result = await self.api_client.district_info(
                keywords=keywords,
                subdistrict=subdistrict,
                extensions=extensions
            )

            # 提取行政区划信息
            districts = result.get('districts', [])
            formatted_districts = []

            for district in districts[:20]:  # 显示前20个
                district_info = {
                    'adcode': district.get('adcode', ''),
                    'name': district.get('name', ''),
                    'center': district.get('center', ''),
                    'level': district.get('level', ''),
                    'citycode': district.get('citycode', ''),
                    'polyline': district.get('polyline', '')
                }
                formatted_districts.append(district_info)

            # 提取子区域
            sub_districts = []
            if extensions == 'all' and formatted_districts:
                # 简单处理子区域，实际可能需要递归查询
                pass

            return {
                'success': True,
                'message': '行政区划查询成功',
                'service': 'district',
                'keywords': keywords,
                'total_count': len(formatted_districts),
                'districts': formatted_districts,
                'subdistricts': sub_districts
            }

        except Exception as e:
            logger.error(
                '行政区划查询失败',
                keywords=keywords,
                error=str(e)
            )
            return {
                'success': False,
                'message': f"行政区划查询失败: {str(e)}",
                'service': 'district'
            }

    async def _handle_ip_location(self, args: dict[str, Any]) -> dict[str, Any]:
        """处理IP定位"""
        ip = args.get('ip')

        logger.info(
            'IP定位查询',
            ip=ip or '本机IP'
        )

        try:
            result = await self.api_client.ip_location(ip=ip)

            # 提取IP定位信息
            location_info = {
                'ip': result.get('ip', ''),
                'province': result.get('province', ''),
                'city': result.get('city', ''),
                'adcode': result.get('adcode', ''),
                'rectangle': result.get('rectangle', ''),
                'location': result.get('location', '')
            }

            # 解析矩形区域
            if 'rectangle' in result and result['rectangle']:
                rect = result['rectangle'].split(';')
                if len(rect) >= 2:
                    min_coords = rect[0].split(',')
                    max_coords = rect[1].split(',')
                    location_info['bounds'] = {
                        'min_lon': min_coords[0] if len(min_coords) > 0 else '',
                        'min_lat': min_coords[1] if len(min_coords) > 1 else '',
                        'max_lon': max_coords[0] if len(max_coords) > 0 else '',
                        'max_lat': max_coords[1] if len(max_coords) > 1 else ''
                    }

            return {
                'success': True,
                'message': 'IP定位成功',
                'service': 'ip_location',
                'result': location_info
            }

        except Exception as e:
            logger.error(
                'IP定位失败',
                ip=ip,
                error=str(e)
            )
            return {
                'success': False,
                'message': f"IP定位失败: {str(e)}",
                'service': 'ip_location'
            }

    def get_input_schema(self) -> dict[str, Any]:
        """获取输入参数模式"""
        return {
            'type': 'object',
            'properties': {
                'service': {
                    'type': 'string',
                    'enum': ['static_map', 'weather', 'coordinate_convert', 'district', 'ip_location'],
                    'description': '服务类型: static_map(静态地图), weather(天气), coordinate_convert(坐标转换), district(行政区划), ip_location(IP定位)'
                },
                'location': {
                    'type': 'string',
                    'description': '位置坐标，格式: 经度,纬度'
                },
                'zoom': {
                    'type': 'integer',
                    'minimum': 1,
                    'maximum': 20,
                    'description': '地图缩放级别'
                },
                'size': {
                    'type': 'string',
                    'pattern': "^\\d+\\*\\d+$",
                    'description': '地图尺寸，格式: 宽*高'
                },
                'markers': {
                    'type': 'string',
                    'description': '标记点信息'
                },
                'city': {
                    'type': 'string',
                    'description': '城市名称'
                },
                'extensions': {
                    'type': 'string',
                    'enum': ['base', 'all'],
                    'description': '返回结果控制: base(基础信息) 或 all(全部信息)'
                },
                'coordsys': {
                    'type': 'string',
                    'enum': ['gps', 'baidu', 'mapbar', 'sogou'],
                    'description': '原始坐标系统'
                },
                'keywords': {
                    'type': 'string',
                    'description': '查询关键词'
                },
                'subdistrict': {
                    'type': 'integer',
                    'minimum': 0,
                    'maximum': 3,
                    'description': '显示下级行政区划级别'
                },
                'ip': {
                    'type': 'string',
                    'description': 'IP地址，不填则定位本机IP'
                }
            },
            'required': ['service']
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
                'service': {
                    'type': 'string',
                    'description': '服务类型'
                },
                'result': {
                    'type': 'object',
                    'description': '服务结果详情'
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
