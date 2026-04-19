"""
地理围栏工具
Geofence Tool
"""

from typing import Any

import structlog

from ..api.extended_gaode_client import ExtendedAmapApiClient

logger = structlog.get_logger(__name__)

class GeofenceTool:
    """地理围栏工具"""

    name: str = 'gaode_geofence'
    description: str = '高德地图地理围栏服务，提供围栏的创建、查询、更新、删除功能'

    def __init__(self, api_client: ExtendedAmapApiClient):
        self.api_client = api_client

    async def call(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        地理围栏处理

        Args:
            arguments: 包含以下字段的字典
                - operation: 操作类型 ('create', 'search', 'update', 'delete')
                - name: 围栏名称 (创建、更新时必需)
                - center: 围栏中心点坐标 (创建时必需)
                - radius: 围栏半径，单位米 (创建时必需)
                - id: 围栏ID (查询、更新、删除时必需)
                - search_radius: 搜索半径 (查询时使用)
                - page: 页码 (查询时使用)
                - size: 每页数量 (查询时使用)

        Returns:
            包含地理围栏操作结果的字典
        """
        operation = arguments.get('operation')

        if operation == 'create':
            return await self._handle_create_geofence(arguments)
        elif operation == 'search':
            return await self._handle_search_geofence(arguments)
        elif operation == 'update':
            return await self._handle_update_geofence(arguments)
        elif operation == 'delete':
            return await self._handle_delete_geofence(arguments)
        else:
            raise ValueError(f"不支持的操作类型: {operation}")

    async def _handle_create_geofence(self, args: dict[str, Any]) -> dict[str, Any]:
        """处理创建地理围栏"""
        name = args.get('name')
        center = args.get('center')
        radius = args.get('radius')
        if not name or not center or not radius:
            raise ValueError('围栏名称、中心点和半径不能为空')

        enable = args.get('enable', 'true')

        logger.info(
            '创建地理围栏',
            name=name,
            center=center,
            radius=radius,
            enable=enable
        )

        try:
            result = await self.api_client.create_geofence(
                name=name,
                center=center,
                radius=radius,
                enable=enable
            )

            # 提取围栏信息
            geofence_info = result.get('data', {})
            if geofence_info:
                formatted_geofence = {
                    'id': geofence_info.get('id', ''),
                    'name': geofence_info.get('name', ''),
                    'center': geofence_info.get('center', ''),
                    'radius': geofence_info.get('radius', 0),
                    'enable': geofence_info.get('enable', ''),
                    'create_time': geofence_info.get('create_time', ''),
                    'modify_time': geofence_info.get('modify_time', '')
                }
            else:
                formatted_geofence = None

            return {
                'success': True,
                'message': '地理围栏创建成功',
                'operation': 'create',
                'geofence': formatted_geofence,
                'info': result.get('info'),
                'infocode': result.get('infocode')
            }

        except Exception as e:
            error_msg = str(e)
            # 检查是否是权限问题
            if 'Unknown error' in error_msg or '4' in error_msg:
                error_msg = '地理围栏API需要企业级权限，请在高德开放平台申请开通'

            logger.error(
                '地理围栏创建失败',
                name=name,
                center=center,
                error=error_msg
            )
            return {
                'success': False,
                'message': error_msg,
                'operation': 'create',
                'requires_enterprise_permission': True
            }

    async def _handle_search_geofence(self, args: dict[str, Any]) -> dict[str, Any]:
        """处理查询地理围栏"""
        center = args.get('center')
        if not center:
            raise ValueError('中心点坐标不能为空')

        radius = args.get('radius', 500)
        page = args.get('page', 1)
        size = args.get('size', 20)

        logger.info(
            '查询地理围栏',
            center=center,
            radius=radius,
            page=page,
            size=size
        )

        try:
            result = await self.api_client.search_geofence(
                center=center,
                radius=radius,
                page=page,
                size=size
            )

            # 提取围栏列表
            geofences = result.get('data', [])
            formatted_geofences = []

            for geofence in geofences:
                geofence_info = {
                    'id': geofence.get('id', ''),
                    'name': geofence.get('name', ''),
                    'center': geofence.get('center', ''),
                    'radius': geofence.get('radius', 0),
                    'enable': geofence.get('enable', ''),
                    'create_time': geofence.get('create_time', ''),
                    'modify_time': geofence.get('modify_time', ''),
                    'monitor_count': geofence.get('monitor_count', 0),
                    'bind_count': geofence.get('bind_count', 0)
                }
                formatted_geofences.append(geofence_info)

            return {
                'success': True,
                'message': '地理围栏查询成功',
                'operation': 'search',
                'center': center,
                'radius': radius,
                'page': page,
                'size': size,
                'total_count': result.get('count', 0),
                'geofences': formatted_geofences,
                'info': result.get('info'),
                'infocode': result.get('infocode')
            }

        except Exception as e:
            error_msg = str(e)
            # 检查是否是权限问题
            if 'Unknown error' in error_msg or '4' in error_msg:
                error_msg = '地理围栏API需要企业级权限，请在高德开放平台申请开通'

            logger.error(
                '地理围栏查询失败',
                center=center,
                radius=radius,
                error=error_msg
            )
            return {
                'success': False,
                'message': error_msg,
                'operation': 'search',
                'requires_enterprise_permission': True
            }

    async def _handle_update_geofence(self, args: dict[str, Any]) -> dict[str, Any]:
        """处理更新地理围栏"""
        id_ = args.get('id')
        if not id_:
            raise ValueError('围栏ID不能为空')

        name = args.get('name')
        center = args.get('center')
        radius = args.get('radius')

        logger.info(
            '更新地理围栏',
            id=id_,
            name=name,
            center=center,
            radius=radius
        )

        try:
            result = await self.api_client.update_geofence(
                id=id_,
                name=name,
                center=center,
                radius=radius
            )

            # 提取更新后的围栏信息
            geofence_info = result.get('data', {})
            if geofence_info:
                formatted_geofence = {
                    'id': geofence_info.get('id', ''),
                    'name': geofence_info.get('name', ''),
                    'center': geofence_info.get('center', ''),
                    'radius': geofence_info.get('radius', 0),
                    'enable': geofence_info.get('enable', ''),
                    'create_time': geofence_info.get('create_time', ''),
                    'modify_time': geofence_info.get('modify_time', '')
                }
            else:
                formatted_geofence = None

            return {
                'success': True,
                'message': '地理围栏更新成功',
                'operation': 'update',
                'geofence': formatted_geofence,
                'info': result.get('info'),
                'infocode': result.get('infocode')
            }

        except Exception as e:
            logger.error(
                '地理围栏更新失败',
                id=id_,
                error=str(e)
            )
            return {
                'success': False,
                'message': f"地理围栏更新失败: {str(e)}",
                'operation': 'update'
            }

    async def _handle_delete_geofence(self, args: dict[str, Any]) -> dict[str, Any]:
        """处理删除地理围栏"""
        id_ = args.get('id')
        if not id_:
            raise ValueError('围栏ID不能为空')

        logger.info(
            '删除地理围栏',
            id=id_
        )

        try:
            result = await self.api_client.delete_geofence(id=id_)

            return {
                'success': True,
                'message': '地理围栏删除成功',
                'operation': 'delete',
                'deleted_id': id_,
                'info': result.get('info'),
                'infocode': result.get('infocode')
            }

        except Exception as e:
            logger.error(
                '地理围栏删除失败',
                id=id_,
                error=str(e)
            )
            return {
                'success': False,
                'message': f"地理围栏删除失败: {str(e)}",
                'operation': 'delete'
            }

    def get_input_schema(self) -> dict[str, Any]:
        """获取输入参数模式"""
        return {
            'type': 'object',
            'properties': {
                'operation': {
                    'type': 'string',
                    'enum': ['create', 'search', 'update', 'delete'],
                    'description': '操作类型: create(创建), search(查询), update(更新), delete(删除)'
                },
                'id': {
                    'type': 'string',
                    'description': '围栏ID (查询、更新、删除时必需)'
                },
                'name': {
                    'type': 'string',
                    'description': '围栏名称 (创建、更新时必需)'
                },
                'center': {
                    'type': 'string',
                    'description': '围栏中心点坐标，格式: 经度,纬度 (创建时必需)'
                },
                'radius': {
                    'type': 'integer',
                    'minimum': 100,
                    'maximum': 100000,
                    'description': '围栏半径，单位米 (创建时必需)'
                },
                'search_radius': {
                    'type': 'integer',
                    'minimum': 100,
                    'maximum': 10000,
                    'description': '搜索半径，单位米 (查询时使用)'
                },
                'page': {
                    'type': 'integer',
                    'minimum': 1,
                    'description': '页码 (查询时使用)'
                },
                'size': {
                    'type': 'integer',
                    'minimum': 1,
                    'maximum': 100,
                    'description': '每页数量 (查询时使用)'
                },
                'enable': {
                    'type': 'string',
                    'enum': ['true', 'false'],
                    'description': '是否启用围栏 (创建时使用)'
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
                'operation': {
                    'type': 'string',
                    'description': '执行的操作类型'
                },
                'geofence': {
                    'type': 'object',
                    'description': '围栏信息详情'
                },
                'deleted_id': {
                    'type': 'string',
                    'description': '删除的围栏ID'
                },
                'center': {
                    'type': 'string',
                    'description': '查询中心点'
                },
                'radius': {
                    'type': 'integer',
                    'description': '查询半径'
                },
                'total_count': {
                    'type': 'integer',
                    'description': '围栏总数'
                },
                'geofences': {
                    'type': 'array',
                    'description': '围栏列表'
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
