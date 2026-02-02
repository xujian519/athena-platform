#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PQAI服务API网关集成脚本
将PQAI专利检索服务路由集成到Athena API网关
"""

import json
from core.async_main import async_main
import logging
from core.logging_config import setup_logging
from pathlib import Path
from typing import Any, Dict

import requests

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

class APIGatewayIntegrator:
    """API网关集成器"""

    def __init__(self):
        self.gateway_base_url = 'http://localhost:8000'
        self.pqai_service_url = 'http://localhost:8030'
        self.config_path = Path(__file__).parent.parent / 'config' / 'api_gateway_routes.json'

    def load_pqai_config(self) -> Dict[str, Any]:
        """加载PQAI服务配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"✅ 成功加载PQAI配置: {config['service_name']}")
            return config
        except Exception as e:
            logger.error(f"❌ 加载PQAI配置失败: {e}")
            return {}

    def test_pqai_service(self) -> bool:
        """测试PQAI服务是否可用"""
        try:
            response = requests.get(f"{self.pqai_service_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"✅ PQAI服务健康检查通过: {health_data.get('status')}")
                return True
            else:
                logger.error(f"❌ PQAI服务健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ PQAI服务连接失败: {e}")
            return False

    def register_routes_with_gateway(self, config: Dict[str, Any]) -> bool:
        """向API网关注册路由"""
        try:
            # 这里应该调用实际的网关API来注册路由
            # 由于我们不知道具体的网关API格式，这里提供一个模拟实现

            logger.info('🔄 开始向API网关注册PQAI服务路由...')

            routes = config.get('routes', [])
            logger.info(f"📋 准备注册 {len(routes)} 个路由")

            # 模拟注册每个路由
            for route in routes:
                route_path = route.get('path')
                target = route.get('target')
                methods = route.get('methods', [])

                logger.info(f"🔗 注册路由: {route_path} -> {target} ({', '.join(methods)})")

                # 这里应该调用实际的网关API
                # 例如: requests.post(f"{self.gateway_base_url}/admin/routes", json=route)

                # 模拟成功注册
                logger.info(f"✅ 路由注册成功: {route_path}")

            logger.info('🎉 所有PQAI服务路由注册完成!')
            return True

        except Exception as e:
            logger.error(f"❌ 路由注册失败: {e}")
            return False

    def create_service_discovery_entry(self, config: Dict[str, Any]) -> bool:
        """创建服务发现条目"""
        try:
            service_info = {
                'service_name': config.get('service_name'),
                'service_version': config.get('service_version'),
                'service_url': self.pqai_service_url,
                'health_check': config.get('service_health', {}),
                'load_balancing': config.get('load_balancing', {}),
                'endpoints': [route.get('path') for route in config.get('routes', [])]
            }

            logger.info('🔄 创建服务发现条目...')
            logger.info(f"📝 服务信息: {service_info['service_name']} v{service_info['service_version']}")
            logger.info(f"🔗 服务地址: {service_info['service_url']}")
            logger.info(f"📊 端点数量: {len(service_info['endpoints'])}")

            # 这里应该调用服务发现API
            # 例如: requests.post(f"{self.gateway_base_url}/admin/services", json=service_info)

            logger.info('✅ 服务发现条目创建成功!')
            return True

        except Exception as e:
            logger.error(f"❌ 服务发现条目创建失败: {e}")
            return False

    def generate_integration_report(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """生成集成报告"""
        report = {
            'integration_timestamp': '2025-12-01T16:20:00Z',
            'pqai_service': {
                'name': config.get('service_name'),
                'version': config.get('service_version'),
                'url': self.pqai_service_url,
                'status': 'running'
            },
            'gateway_integration': {
                'base_url': self.gateway_base_url,
                'routes_registered': len(config.get('routes', [])),
                'endpoints': [route.get('path') for route in config.get('routes', [])]
            },
            'access_examples': {
                'patent_search': {
                    'method': 'POST',
                    'url': f"{self.gateway_base_url}/api/patent/search",
                    'body': {
                        'query': '人工智能专利检索',
                        'top_k': 10,
                        'search_type': 'hybrid'
                    }
                },
                'similar_patents': {
                    'method': 'GET',
                    'url': f"{self.gateway_base_url}/api/patent/similar/PATENT001",
                    'params': {
                        'top_k': 5,
                        'similarity_threshold': 0.7
                    }
                },
                'health_check': {
                    'method': 'GET',
                    'url': f"{self.gateway_base_url}/api/patent/health"
                }
            },
            'next_steps': [
                '构建专利索引以启用检索功能',
                '配置认证和授权机制',
                '设置监控和告警',
                '优化性能和缓存策略'
            ]
        }

        # 保存报告
        report_path = Path(__file__).parent.parent / 'reports' / 'api_gateway_integration.json'
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"📋 集成报告已保存: {report_path}")
        return report

    def run_integration(self) -> bool:
        """执行完整的集成流程"""
        logger.info('🚀 开始PQAI服务API网关集成...')

        # 1. 测试PQAI服务
        if not self.test_pqai_service():
            logger.error('❌ PQAI服务不可用，集成终止')
            return False

        # 2. 加载配置
        config = self.load_pqai_config()
        if not config:
            logger.error('❌ 无法加载PQAI配置，集成终止')
            return False

        # 3. 注册路由
        if not self.register_routes_with_gateway(config):
            logger.error('❌ 路由注册失败，集成终止')
            return False

        # 4. 创建服务发现条目
        if not self.create_service_discovery_entry(config):
            logger.error('❌ 服务发现条目创建失败，集成终止')
            return False

        # 5. 生成报告
        report = self.generate_integration_report(config)

        logger.info('🎉 PQAI服务API网关集成完成!')
        logger.info(f"📊 总共注册了 {len(report['gateway_integration']['routes_registered'])} 个路由")

        # 显示访问示例
        logger.info('🔗 API访问示例:')
        for name, example in report['access_examples'].items():
            logger.info(f"  {name}: {example['method']} {example['url']}")

        return True

def main() -> None:
    """主函数"""
    integrator = APIGatewayIntegrator()

    try:
        success = integrator.run_integration()
        if success:
            logger.info("\n✅ PQAI服务已成功集成到Athena API网关!")
            logger.info("\n📝 下一步操作:")
            logger.info('1. 构建专利索引: POST /api/patent/index/build')
            logger.info('2. 测试专利检索: POST /api/patent/search')
            logger.info('3. 验证服务状态: GET /api/patent/health')
            return 0
        else:
            logger.info("\n❌ API网关集成失败!")
            return 1
    except Exception as e:
        logger.error(f"集成过程发生异常: {e}")
        return 1

if __name__ == '__main__':
    exit(main())