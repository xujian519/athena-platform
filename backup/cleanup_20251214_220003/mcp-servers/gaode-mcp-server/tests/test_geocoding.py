#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地理编码工具测试
Tests for Geocoding Tool
"""

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock

import pytest
from amap_mcp_server.api.gaode_client import AmapApiClient
from amap_mcp_server.tools.geocoding import GeocodingTool


class TestGeocodingTool:
    """地理编码工具测试"""

    @pytest.fixture
    def mock_api_client(self):
        """模拟API客户端"""
        client = MagicMock(spec=AmapApiClient)
        return client

    @pytest.fixture
    def geocoding_tool(self, mock_api_client):
        """地理编码工具实例"""
        return GeocodingTool(mock_api_client)

    @pytest.mark.asyncio
    async def test_geocoding_success(self, geocoding_tool, mock_api_client):
        """测试地理编码成功"""
        # 模拟API响应
        mock_response = {
            'status': '1',
            'info': 'OK',
            'infocode': '10000',
            'geocodes': [
                {
                    'formatted_address': '北京市海淀区中关村',
                    'location': '116.397428,39.90923',
                    'level': '兴趣点',
                    'adcode': '110108',
                    'city': '北京市',
                    'district': '海淀区',
                    'province': '北京',
                    'country': '中国',
                    'confidence': '100'
                }
            ]
        }
        mock_api_client.geocoding.return_value = mock_response

        # 测试地理编码
        result = await geocoding_tool.call({
            'operation': 'geocode',
            'address': '中关村',
            'city': '北京'
        })

        # 验证结果
        assert result['success'] is True
        assert result['count'] == 1
        assert len(result['results']) == 1

        first_result = result['results'][0]
        assert first_result['formatted_address'] == '北京市海淀区中关村'
        assert first_result['location']['longitude'] == 116.397428
        assert first_result['location']['latitude'] == 39.90923
        assert first_result['city'] == '北京市'
        assert first_result['district'] == '海淀区'

    @pytest.mark.asyncio
    async def test_geocoding_no_results(self, geocoding_tool, mock_api_client):
        """测试地理编码无结果"""
        # 模拟API响应
        mock_response = {
            'status': '1',
            'info': 'OK',
            'infocode': '10000',
            'geocodes': []
        }
        mock_api_client.geocoding.return_value = mock_response

        # 测试地理编码
        result = await geocoding_tool.call({
            'operation': 'geocode',
            'address': '不存在的地址'
        })

        # 验证结果
        assert result['success'] is False
        assert result['count'] == 0
        assert len(result['results']) == 0
        assert '未找到匹配的地址' in result['message']

    @pytest.mark.asyncio
    async def test_reverse_geocoding_success(self, geocoding_tool, mock_api_client):
        """测试逆地理编码成功"""
        # 模拟API响应
        mock_response = {
            'status': '1',
            'info': 'OK',
            'infocode': '10000',
            'regeocode': {
                'formatted_address': '北京市海淀区中关村大街1号',
                'addressComponent': {
                    'country': '中国',
                    'province': '北京',
                    'city': '北京市',
                    'citycode': '010',
                    'district': '海淀区',
                    'adcode': '110108',
                    'township': '海淀街道',
                    'townshipcode': '110108001000'
                },
                'pois': [
                    {
                        'id': 'B000A7BD6C',
                        'name': '中关村',
                        'type': '商务住宅;商业;商务写字楼',
                        'tel': '010-58888888',
                        'address': '中关村大街1号',
                        'location': '116.397428,39.90923',
                        'distance': '0.123',
                        'direction': '东北'
                    }
                ]
            }
        }
        mock_api_client.reverse_geocoding.return_value = mock_response

        # 测试逆地理编码
        result = await geocoding_tool.call({
            'operation': 'reverse_geocode',
            'location': '116.397428,39.90923',
            'radius': 1000
        })

        # 验证结果
        assert result['success'] is True
        assert result['location'] == '116.397428,39.90923'
        assert result['pois_count'] == 1
        assert len(result['pois']) == 1

        address = result['address']
        assert address['formatted_address'] == '北京市海淀区中关村大街1号'
        assert address['city'] == '北京市'
        assert address['district'] == '海淀区'

        poi = result['pois'][0]
        assert poi['name'] == '中关村'
        assert poi['type'] == '商务住宅;商业;商务写字楼'
        assert poi['address'] == '中关村大街1号'
        assert poi['distance'] == '0.123'

    @pytest.mark.asyncio
    async def test_reverse_geocoding_no_results(self, geocoding_tool, mock_api_client):
        """测试逆地理编码无结果"""
        # 模拟API响应
        mock_response = {
            'status': '1',
            'info': 'OK',
            'infocode': '10000',
            'regeocode': {}
        }
        mock_api_client.reverse_geocoding.return_value = mock_response

        # 测试逆地理编码
        result = await geocoding_tool.call({
            'operation': 'reverse_geocode',
            'location': '0.0,0.0'
        })

        # 验证结果
        assert result['success'] is False
        assert result['address'] is None
        assert len(result['pois']) == 0
        assert '未找到匹配的地址信息' in result['message']

    @pytest.mark.asyncio
    async def test_invalid_operation(self, geocoding_tool):
        """测试无效操作类型"""
        with pytest.raises(ValueError, match='不支持的操作类型'):
            await geocoding_tool.call({
                'operation': 'invalid_operation',
                'address': '测试地址'
            })

    @pytest.mark.asyncio
    async def test_missing_required_parameters(self, geocoding_tool):
        """测试缺少必需参数"""
        # 地理编码缺少地址
        with pytest.raises(ValueError, match='地址参数不能为空'):
            await geocoding_tool.call({
                'operation': 'geocode',
                'city': '北京'
            })

        # 逆地理编码缺少坐标
        with pytest.raises(ValueError, match='坐标参数不能为空'):
            await geocoding_tool.call({
                'operation': 'reverse_geocode',
                'radius': 1000
            })

    @pytest.mark.asyncio
    async def test_api_error_handling(self, geocoding_tool, mock_api_client):
        """测试API错误处理"""
        # 模拟API异常
        mock_api_client.geocoding.side_effect = Exception('网络连接失败')

        # 测试地理编码
        result = await geocoding_tool.call({
            'operation': 'geocode',
            'address': '测试地址'
        })

        # 验证错误处理
        assert result['success'] is False
        assert '地理编码失败' in result['message']
        assert '网络连接失败' in result['message']
        assert result['count'] == 0
        assert len(result['results']) == 0

    def test_input_schema(self, geocoding_tool):
        """测试输入参数模式"""
        schema = geocoding_tool.get_input_schema()

        assert schema['type'] == 'object'
        assert 'operation' in schema['properties']
        assert schema['properties']['operation']['enum'] == ['geocode', 'reverse_geocode']
        assert 'operation' in schema['required']

    def test_output_schema(self, geocoding_tool):
        """测试输出结果模式"""
        schema = geocoding_tool.get_output_schema()

        assert schema['type'] == 'object'
        assert 'success' in schema['properties']
        assert 'message' in schema['properties']
        assert 'count' in schema['properties']
        assert 'results' in schema['properties']


if __name__ == '__main__':
    pytest.main([__file__])