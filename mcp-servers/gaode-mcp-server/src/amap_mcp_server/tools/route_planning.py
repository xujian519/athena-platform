"""
路径规划工具
Route Planning Tool
"""

from typing import Any

import structlog

from ..api.extended_gaode_client import ExtendedAmapApiClient

logger = structlog.get_logger(__name__)

class RoutePlanningTool:
    """路径规划工具"""

    name: str = 'gaode_route_planning'
    description: str = '高德地图路径规划服务，支持驾车、步行、骑行、公交等多种出行方式'

    def __init__(self, api_client: ExtendedAmapApiClient):
        self.api_client = api_client

    async def call(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        路径规划处理

        Args:
            arguments: 包含以下字段的字典
                - mode: 出行方式 ('driving', 'walking', 'bicycling', 'transit')
                - origin: 起点坐标或地址
                - destination: 终点坐标或地址
                - city: 城市名称 (公交路径规划时必需)
                - cityd: 目标城市 (公交路径规划时可选)
                - strategy: 路径策略 (驾车时使用，0-9)
                - avoidpolygons: 避让区域 (可选)
                - avoidroad: 避让道路 (可选)

        Returns:
            包含路径规划结果的字典
        """
        mode = arguments.get('mode')

        if mode == 'driving':
            return await self._handle_driving_route(arguments)
        elif mode == 'walking':
            return await self._handle_walking_route(arguments)
        elif mode == 'bicycling':
            return await self._handle_bicycling_route(arguments)
        elif mode == 'transit':
            return await self._handle_transit_route(arguments)
        else:
            raise ValueError(f"不支持的出行方式: {mode}")

    async def _handle_driving_route(self, args: dict[str, Any]) -> dict[str, Any]:
        """处理驾车路径规划"""
        origin = args.get('origin')
        destination = args.get('destination')
        if not origin or not destination:
            raise ValueError('起点和终点不能为空')

        strategy = args.get('strategy', 0)
        avoidpolygons = args.get('avoidpolygons')
        avoidroad = args.get('avoidroad')

        logger.info(
            '执行驾车路径规划',
            origin=origin,
            destination=destination,
            strategy=strategy
        )

        try:
            result = await self.api_client.driving_route(
                origin=origin,
                destination=destination,
                strategy=strategy,
                avoidpolygons=avoidpolygons,
                avoidroad=avoidroad
            )

            # 提取并格式化结果
            route = result.get('route', {})
            paths = route.get('paths', [])
            if not paths:
                return {
                    'success': False,
                    'message': '未找到可行的驾车路径',
                    'mode': 'driving',
                    'routes': []
                }

            formatted_routes = []
            for path in paths:
                distance = path.get('distance', 0)
                duration = path.get('duration', 0)
                steps = path.get('steps', [])

                route_info = {
                    'distance': int(distance) if isinstance(distance, (str, int, float)) else 0,
                    'distance_text': f"{int(distance) / 1000:.1f}公里' if isinstance(distance, (str, int, float)) else '0公里",
                    'duration': int(duration) if isinstance(duration, (str, int, float)) else 0,
                    'duration_text': f"{int(duration) // 60}分钟{int(duration) % 60}秒' if isinstance(duration, (str, int, float)) else '0分钟",
                    'strategy': path.get('strategy', '未知'),
                    'traffic_lights': int(path.get('traffic_lights', 0)) if path.get('traffic_lights') else 0,
                    'steps_count': len(steps),
                    'steps': []
                }

                # 处理步骤
                for step in steps[:10]:  # 只显示前10步
                    step_info = {
                        'instruction': step.get('instruction', ''),
                        'distance': step.get('distance', 0),
                        'duration': step.get('duration', 0),
                        'road': step.get('road', ''),
                        'action': step.get('action', ''),
                        'polyline': step.get('polyline', '')
                    }
                    route_info['steps'].append(step_info)

                formatted_routes.append(route_info)

            return {
                'success': True,
                'message': '驾车路径规划成功',
                'mode': 'driving',
                'origin': origin,
                'destination': destination,
                'total_routes': len(formatted_routes),
                'routes': formatted_routes,
                'info': result.get('info'),
                'infocode': result.get('infocode')
            }

        except Exception as e:
            logger.error(
                '驾车路径规划失败',
                origin=origin,
                destination=destination,
                error=str(e)
            )
            return {
                'success': False,
                'message': f"驾车路径规划失败: {str(e)}",
                'mode': 'driving',
                'routes': []
            }

    async def _handle_walking_route(self, args: dict[str, Any]) -> dict[str, Any]:
        """处理步行路径规划"""
        origin = args.get('origin')
        destination = args.get('destination')
        if not origin or not destination:
            raise ValueError('起点和终点不能为空')

        logger.info(
            '执行步行路径规划',
            origin=origin,
            destination=destination
        )

        try:
            result = await self.api_client.walking_route(
                origin=origin,
                destination=destination
            )

            # 提取并格式化结果
            route = result.get('route', {})
            paths = route.get('paths', [])
            if not paths:
                return {
                    'success': False,
                    'message': '未找到可行的步行路径',
                    'mode': 'walking',
                    'routes': []
                }

            path = paths[0]  # 步行路径通常只有一种选择
            distance = path.get('distance', 0)
            duration = path.get('duration', 0)
            steps = path.get('steps', [])

            route_info = {
                'distance': distance,
                'distance_text': f"{distance}米",
                'duration': duration,
                'duration_text': f"{duration // 60}分钟{duration % 60}秒",
                'steps_count': len(steps),
                'steps': []
            }

            # 处理步骤
            for step in steps[:20]:  # 显示前20步
                step_info = {
                    'instruction': step.get('instruction', ''),
                    'distance': step.get('distance', 0),
                    'duration': step.get('duration', 0),
                    'road': step.get('road', ''),
                    'action': step.get('action', '')
                }
                route_info['steps'].append(step_info)

            return {
                'success': True,
                'message': '步行路径规划成功',
                'mode': 'walking',
                'origin': origin,
                'destination': destination,
                'route': route_info,
                'info': result.get('info'),
                'infocode': result.get('infocode')
            }

        except Exception as e:
            logger.error(
                '步行路径规划失败',
                origin=origin,
                destination=destination,
                error=str(e)
            )
            return {
                'success': False,
                'message': f"步行路径规划失败: {str(e)}",
                'mode': 'walking',
                'routes': []
            }

    async def _handle_bicycling_route(self, args: dict[str, Any]) -> dict[str, Any]:
        """处理骑行路径规划"""
        origin = args.get('origin')
        destination = args.get('destination')
        if not origin or not destination:
            raise ValueError('起点和终点不能为空')

        logger.info(
            '执行骑行路径规划',
            origin=origin,
            destination=destination
        )

        try:
            result = await self.api_client.bicycling_route(
                origin=origin,
                destination=destination
            )

            # 提取并格式化结果
            route = result.get('route', {})
            paths = route.get('paths', [])
            if not paths:
                return {
                    'success': False,
                    'message': '未找到可行的骑行路径',
                    'mode': 'bicycling',
                    'routes': []
                }

            path = paths[0]  # 骑行路径通常只有一种选择
            distance = path.get('distance', 0)
            duration = path.get('duration', 0)
            steps = path.get('steps', [])

            route_info = {
                'distance': distance,
                'distance_text': f"{distance / 1000:.1f}公里",
                'duration': duration,
                'duration_text': f"{duration // 60}分钟{duration % 60}秒",
                'steps_count': len(steps),
                'steps': []
            }

            # 处理步骤
            for step in steps[:20]:
                step_info = {
                    'instruction': step.get('instruction', ''),
                    'distance': step.get('distance', 0),
                    'duration': step.get('duration', 0),
                    'road': step.get('road', '')
                }
                route_info['steps'].append(step_info)

            return {
                'success': True,
                'message': '骑行路径规划成功',
                'mode': 'bicycling',
                'origin': origin,
                'destination': destination,
                'route': route_info,
                'info': result.get('info'),
                'infocode': result.get('infocode')
            }

        except Exception as e:
            logger.error(
                '骑行路径规划失败',
                origin=origin,
                destination=destination,
                error=str(e)
            )
            return {
                'success': False,
                'message': f"骑行路径规划失败: {str(e)}",
                'mode': 'bicycling',
                'routes': []
            }

    async def _handle_transit_route(self, args: dict[str, Any]) -> dict[str, Any]:
        """处理公交路径规划"""
        origin = args.get('origin')
        destination = args.get('destination')
        city = args.get('city')
        if not origin or not destination or not city:
            raise ValueError('起点、终点和城市不能为空')

        cityd = args.get('cityd')

        logger.info(
            '执行公交路径规划',
            origin=origin,
            destination=destination,
            city=city,
            cityd=cityd
        )

        try:
            result = await self.api_client.transit_route(
                origin=origin,
                destination=destination,
                city=city,
                cityd=cityd
            )

            # 提取并格式化结果
            route = result.get('route', [])
            if not route:
                return {
                    'success': False,
                    'message': '未找到可行的公交路径',
                    'mode': 'transit',
                    'routes': []
                }

            formatted_routes = []
            for transit_route in route[:5]:  # 显示前5种方案
                distance = transit_route.get('distance', 0)
                duration = transit_route.get('duration', 0)
                cost = transit_route.get('price', '0')
                walking_distance = transit_route.get('walking_distance', 0)

                # 提取公交信息
                transits = transit_route.get('transits', [])
                segments = []
                for transit in transits:
                    for segment in transit.get('segments', []):
                        seg_info = {
                            'walking': segment.get('walking', {}),
                            'bus': segment.get('bus', {}),
                            'railway': segment.get('railway', {}),
                            'enter_name': segment.get('enter_name', ''),
                            'exit_name': segment.get('exit_name', '')
                        }
                        segments.append(seg_info)

                route_info = {
                    'distance': distance,
                    'distance_text': f"{distance / 1000:.1f}公里",
                    'duration': duration,
                    'duration_text': f"{duration // 60}分钟{duration % 60}秒",
                    'cost': cost,
                    'cost_text': f"{cost}元",
                    'walking_distance': walking_distance,
                    'walking_text': f"{walking_distance}米步行",
                    'segments_count': len(segments),
                    'segments': segments[:5]  # 只显示前5段
                }

                formatted_routes.append(route_info)

            return {
                'success': True,
                'message': '公交路径规划成功',
                'mode': 'transit',
                'origin': origin,
                'destination': destination,
                'city': city,
                'total_routes': len(formatted_routes),
                'routes': formatted_routes,
                'info': result.get('info'),
                'infocode': result.get('infocode')
            }

        except Exception as e:
            logger.error(
                '公交路径规划失败',
                origin=origin,
                destination=destination,
                city=city,
                error=str(e)
            )
            return {
                'success': False,
                'message': f"公交路径规划失败: {str(e)}",
                'mode': 'transit',
                'routes': []
            }

    def get_input_schema(self) -> dict[str, Any]:
        """获取输入参数模式"""
        return {
            'type': 'object',
            'properties': {
                'mode': {
                    'type': 'string',
                    'enum': ['driving', 'walking', 'bicycling', 'transit'],
                    'description': '出行方式: driving(驾车), walking(步行), bicycling(骑行), transit(公交)'
                },
                'origin': {
                    'type': 'string',
                    'description': '起点坐标或地址'
                },
                'destination': {
                    'type': 'string',
                    'description': '终点坐标或地址'
                },
                'city': {
                    'type': 'string',
                    'description': '城市名称 (公交路径规划时必需)'
                },
                'cityd': {
                    'type': 'string',
                    'description': '目标城市 (公交路径规划时可选)'
                },
                'strategy': {
                    'type': 'integer',
                    'minimum': 0,
                    'maximum': 9,
                    'description': '路径策略 (0-9，仅驾车时使用)'
                },
                'avoidpolygons': {
                    'type': 'string',
                    'description': '避让区域坐标 (可选)'
                },
                'avoidroad': {
                    'type': 'string',
                    'description': '避让道路名称 (可选)'
                }
            },
            'required': ['mode', 'origin', 'destination']
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
                'mode': {
                    'type': 'string',
                    'description': '出行方式'
                },
                'origin': {
                    'type': 'string',
                    'description': '起点'
                },
                'destination': {
                    'type': 'string',
                    'description': '终点'
                },
                'city': {
                    'type': 'string',
                    'description': '城市名称'
                },
                'total_routes': {
                    'type': 'integer',
                    'description': '路径方案总数'
                },
                'routes': {
                    'type': 'array',
                    'description': '路径方案列表'
                },
                'route': {
                    'type': 'object',
                    'description': '单一路径信息 (步行和骑行)'
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
