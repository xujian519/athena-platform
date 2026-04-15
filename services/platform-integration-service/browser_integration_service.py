#!/usr/bin/env python3
"""
Athena平台浏览器自动化集成服务
统一管理平台中的浏览器自动化功能
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'services'))

# 导入安全配置
import sys
from pathlib import Path

from browser_automation.athena_browser_glm import AthenaBrowserGLMAgent
from common_tools.browser_automation_tool import get_browser_tool
from xiaonuo_browser_control import get_xiaonuo_controller

sys.path.append(str(Path(__file__).parent.parent / "core"))

logger = logging.getLogger(__name__)

class BrowserIntegrationService:
    """浏览器自动化集成服务"""

    def __init__(self, config: dict[str, Any]):
        """初始化集成服务

        Args:
            config: 配置参数
        """
        self.config = config
        self.browser_tool = get_browser_tool()
        self.xiaonuo_controller = get_xiaonuo_controller(config.get('glm_api_key'))
        self.athena_agent = None
        self.service_status = 'initializing'
        self.integration_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'xiaonuo_decisions': 0,
            'direct_executions': 0,
            'scenarios_used': {}
        }

        # 服务配置
        self.service_config = {
            'auto_start': True,
            'enable_xiaonuo': True,
            'enable_athena': True,
            'metrics_enabled': True,
            'log_level': 'INFO'
        }

        asyncio.create_task(self._initialize_service())

    async def _initialize_service(self):
        """初始化服务"""
        try:
            # 初始化Athena代理
            if self.service_config['enable_athena']:
                self.athena_agent = AthenaBrowserGLMAgent(
                    api_key=self.config.get('glm_api_key')
                )
                await self.athena_agent.start_session()
                logger.info('Athena浏览器代理已启动')

            # 初始化小诺控制器
            if self.service_config['enable_xiaonuo']:
                # 小诺控制器已在获取实例时初始化
                logger.info('小诺浏览器控制器已启动')

            # 启动浏览器工具
            if self.service_config['auto_start']:
                await self.browser_tool.initialize()
                logger.info('浏览器自动化工具已启动')

            self.service_status = 'running'
            logger.info('浏览器自动化集成服务启动成功')

        except Exception as e:
            self.service_status = 'error'
            logger.error(f"服务初始化失败: {e}")

    async def process_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """处理浏览器自动化请求

        Args:
            request: 请求参数

        Returns:
            处理结果
        """
        self.integration_metrics['total_requests'] += 1

        request_id = request.get('request_id', f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        user_input = request.get('user_input', '')
        context = request.get('context', {})
        execution_mode = request.get('mode', 'auto')  # auto, xiaonuo, athena, direct
        scenario = request.get('scenario')

        logger.info(f"处理请求 {request_id}: {user_input}")

        try:
            result = {
                'request_id': request_id,
                'success': False,
                'mode': execution_mode,
                'timestamp': datetime.now().isoformat()
            }

            # 根据执行模式选择处理方式
            if execution_mode == 'xiaonuo' or (execution_mode == 'auto' and self.service_config['enable_xiaonuo']):
                # 小诺智能模式
                self.integration_metrics['xiaonuo_decisions'] += 1
                xiaonuo_result = await self.xiaonuo_controller.smart_task_execution(
                    user_input, context
                )
                result.update({
                    'success': xiaonuo_result['success'],
                    'xiaonuo_analysis': xiaonuo_result['analysis'],
                    'execution_result': xiaonuo_result.get('execution_result')
                })

            elif execution_mode == 'athena' or (execution_mode == 'auto' and self.athena_agent):
                # Athena代理模式
                athena_result = await self.athena_agent.execute_task(user_input)
                result.update({
                    'success': athena_result['success'],
                    'athena_response': athena_result['response'],
                    'execution_result': athena_result
                })

            elif execution_mode == 'direct' or scenario:
                # 直接执行模式
                self.integration_metrics['direct_executions'] += 1
                if scenario:
                    # 预定义场景
                    execution_result = await self.browser_tool.execute_scenario(
                        scenario, {'query': user_input, 'context': context}
                    )
                else:
                    # 自定义任务
                    execution_result = await self.browser_tool.execute_custom_task(user_input)

                result.update({
                    'success': execution_result['success'],
                    'execution_result': execution_result
                })

                # 记录场景使用情况
                if scenario:
                    self.integration_metrics['scenarios_used'][scenario] = \
                        self.integration_metrics['scenarios_used'].get(scenario, 0) + 1

            else:
                result['error'] = '没有可用的执行模式'

            # 更新成功计数
            if result['success']:
                self.integration_metrics['successful_requests'] += 1

            return result

        except Exception as e:
            logger.error(f"处理请求失败: {e}")
            return {
                'request_id': request_id,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def batch_process(self, requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """批量处理请求

        Args:
            requests: 请求列表

        Returns:
            处理结果列表
        """
        logger.info(f"批量处理 {len(requests)} 个请求")

        # 并发处理所有请求
        tasks = [self.process_request(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'request_id': requests[i].get('request_id', f"batch_{i}"),
                    'success': False,
                    'error': str(result),
                    'timestamp': datetime.now().isoformat()
                })
            else:
                processed_results.append(result)

        return processed_results

    async def get_available_scenarios(self) -> dict[str, Any]:
        """获取可用场景列表"""
        return await self.browser_tool.list_scenarios()

    async def get_service_status(self) -> dict[str, Any]:
        """获取服务状态"""
        return {
            'service': 'BrowserIntegrationService',
            'status': self.service_status,
            'config': self.service_config,
            'metrics': self.integration_metrics,
            'components': {
                'browser_tool': self.browser_tool.get_status(),
                'xiaonuo_controller': self.xiaonuo_controller.get_status(),
                'athena_agent': self.athena_agent.get_status() if self.athena_agent else None
            },
            'timestamp': datetime.now().isoformat()
        }

    async def update_config(self, new_config: dict[str, Any]):
        """更新服务配置"""
        self.service_config.update(new_config)
        logger.info(f"服务配置已更新: {new_config}")

        # 如果更新了小诺配置
        if 'xiaonuo_config' in new_config:
            self.xiaonuo_controller.update_config(new_config['xiaonuo_config'])

    async def reset_metrics(self):
        """重置指标"""
        self.integration_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'xiaonuo_decisions': 0,
            'direct_executions': 0,
            'scenarios_used': {}
        }
        logger.info('指标已重置')

    async def shutdown(self):
        """关闭服务"""
        logger.info('正在关闭浏览器自动化集成服务...')

        try:
            # 关闭Athena代理
            if self.athena_agent:
                await self.athena_agent.stop_session()

            # 关闭浏览器工具
            await self.browser_tool.shutdown()

            self.service_status = 'shutdown'
            logger.info('服务已关闭')

        except Exception as e:
            logger.error(f"关闭服务时出错: {e}")

# 全局服务实例
integration_service: BrowserIntegrationService | None = None

def get_integration_service(config: dict[str, Any] | None = None) -> BrowserIntegrationService:
    """获取集成服务实例"""
    global integration_service
    if integration_service is None:
        default_config = {
            'glm_api_key': '9efe5766a7cd4bb687e40082ee4032b6.0mYTotbC7aRmoNCe'
        }
        if config:
            default_config.update(config)
        integration_service = BrowserIntegrationService(default_config)
    return integration_service

# 测试函数
async def test_integration_service():
    """测试集成服务"""
    logger.info('🧪 测试浏览器自动化集成服务')
    logger.info(str('=' * 50))

    service = get_integration_service()

    # 等待服务初始化
    await asyncio.sleep(2)

    # 测试请求
    test_requests = [
        {
            'user_input': '帮我监控iPhone 15的价格',
            'mode': 'xiaonuo',
            'context': {'user': 'test_user'}
        },
        {
            'user_input': '访问淘宝搜索手机',
            'mode': 'direct',
            'scenario': 'price_monitor'
        },
        {
            'user_input': '自动执行专利搜索',
            'mode': 'auto'
        }
    ]

    logger.info("\n📋 执行测试请求...")
    results = await service.batch_process(test_requests)

    for result in results:
        logger.info(f"\n请求 {result['request_id']}:")
        logger.info(f"   成功: {result['success']}")
        logger.info(f"   模式: {result.get('mode', 'unknown')}")
        if not result['success']:
            logger.info(f"   错误: {result.get('error', 'unknown')}")

    # 显示服务状态
    status = await service.get_service_status()
    logger.info("\n📊 服务状态:")
    logger.info(f"   总请求数: {status['metrics']['total_requests']}")
    logger.info(f"   成功请求数: {status['metrics']['successful_requests']}")
    logger.info(f"   小诺决策数: {status['metrics']['xiaonuo_decisions']}")
    logger.info(f"   直接执行数: {status['metrics']['direct_executions']}")

    # 获取可用场景
    scenarios = await service.get_available_scenarios()
    logger.info(f"\n🎯 可用场景数: {len(scenarios['scenarios'])}")

    logger.info("\n✅ 集成服务测试完成")

if __name__ == '__main__':
    asyncio.run(test_integration_service())
