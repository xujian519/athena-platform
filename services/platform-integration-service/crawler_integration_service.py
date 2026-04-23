#!/usr/bin/env python3
"""
Athena平台爬虫集成服务
统一管理平台中的爬虫功能
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

from common_tools.crawler_tool import CrawlerScenario, get_crawler_tool
from xiaonuo_crawler_control import get_xiaonuo_crawler_controller

logger = logging.getLogger(__name__)

class CrawlerIntegrationService:
    """爬虫集成服务"""

    def __init__(self, config: dict[str, Any]):
        """初始化集成服务

        Args:
            config: 配置参数
        """
        self.config = config
        self.crawler_tool = get_crawler_tool()
        self.xiaonuo_controller = get_xiaonuo_crawler_controller()
        self.service_status = 'initializing'
        self.integration_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'xiaonuo_decisions': 0,
            'direct_executions': 0,
            'scenarios_used': {},
            'data_collected_gb': 0.0,
            'active_tasks': 0
        }

        # 服务配置
        self.service_config = {
            'auto_start': True,
            'enable_xiaonuo': True,
            'enable_scheduling': True,
            'max_concurrent_tasks': 10,
            'default_timeout': 300,
            'enable_monitoring': True
        }

        # 任务调度器
        self.task_scheduler = None
        self.running_tasks = {}

        asyncio.create_task(self._initialize_service())

    async def _initialize_service(self):
        """初始化服务"""
        try:
            # 初始化爬虫工具
            if self.service_config['auto_start']:
                await self.crawler_tool.initialize()
                logger.info('爬虫工具已启动')

            # 初始化小诺控制器
            if self.service_config['enable_xiaonuo']:
                # 小诺控制器已在获取实例时初始化
                logger.info('小诺爬虫控制器已启动')

            # 启动任务调度器
            if self.service_config['enable_scheduling']:
                await self._start_task_scheduler()
                logger.info('任务调度器已启动')

            # 启动监控服务
            if self.service_config['enable_monitoring']:
                asyncio.create_task(self._monitoring_service())
                logger.info('监控服务已启动')

            self.service_status = 'running'
            logger.info('爬虫集成服务启动成功')

        except Exception as e:
            self.service_status = 'error'
            logger.error(f"服务初始化失败: {e}")

    async def _start_task_scheduler(self):
        """启动任务调度器"""
        self.task_scheduler = asyncio.Queue()

        # 启动调度器工作协程
        for i in range(self.service_config['max_concurrent_tasks']):
            asyncio.create_task(self._task_worker(f"worker_{i}"))

        logger.info(f"启动了 {self.service_config['max_concurrent_tasks']} 个任务工作进程")

    async def _task_worker(self, worker_id: str):
        """任务工作进程"""
        logger.info(f"任务工作进程 {worker_id} 启动")

        while True:
            try:
                # 获取任务
                task_data = await self.task_scheduler.get()

                # 执行任务
                await self._execute_scheduled_task(worker_id, task_data)

            except Exception as e:
                logger.error(f"任务工作进程 {worker_id} 执行异常: {e}")
                await asyncio.sleep(1)

    async def _execute_scheduled_task(self, worker_id: str, task_data: dict[str, Any]):
        """执行调度任务"""
        task_id = task_data.get('task_id')
        task_type = task_data.get('type', 'scenario')

        logger.info(f"工作进程 {worker_id} 开始执行任务: {task_id}")

        try:
            self.running_tasks[task_id] = {
                'worker_id': worker_id,
                'start_time': datetime.now(),
                'status': 'running'
            }

            if task_type == 'scenario':
                # 场景任务
                result = await self.crawler_tool.execute_scenario(
                    CrawlerScenario(task_data['scenario']),
                    task_data['params']
                )
            elif task_type == 'custom':
                # 自定义任务
                result = await self.crawler_tool.execute_custom_task(
                    task_data['urls'],
                    task_data['config']
                )
            else:
                raise ValueError(f"不支持的任务类型: {task_type}")

            # 更新任务状态
            self.running_tasks[task_id].update({
                'status': 'completed',
                'end_time': datetime.now(),
                'result': {
                    'success': result.success,
                    'data_count': len(result.data),
                    'execution_time': result.execution_time
                }
            })

            # 更新统计
            self.integration_metrics['active_tasks'] -= 1

            logger.info(f"任务 {task_id} 执行完成")

        except Exception as e:
            logger.error(f"任务 {task_id} 执行失败: {e}")

            if task_id in self.running_tasks:
                self.running_tasks[task_id].update({
                    'status': 'failed',
                    'error': str(e),
                    'end_time': datetime.now()
                })

            self.integration_metrics['active_tasks'] -= 1

    async def _monitoring_service(self):
        """监控服务"""
        logger.info('监控服务启动')

        while self.service_status == 'running':
            try:
                # 收集性能指标
                await self._collect_metrics()

                # 检查任务超时
                await self._check_task_timeouts()

                # 等待下次检查
                await asyncio.sleep(60)  # 每分钟检查一次

            except Exception as e:
                logger.error(f"监控服务异常: {e}")
                await asyncio.sleep(10)

    async def _collect_metrics(self):
        """收集性能指标"""
        try:
            # 获取爬虫工具状态
            crawler_status = self.crawler_tool.get_status()

            # 更新数据收集量
            total_data = crawler_status['metrics']['data_collected']
            self.integration_metrics['data_collected_gb'] = total_data * 0.000001  # 转换为GB

        except Exception as e:
            logger.error(f"收集指标失败: {e}")

    async def _check_task_timeouts(self):
        """检查任务超时"""
        current_time = datetime.now()
        default_timeout = self.service_config['default_timeout']

        for task_id, task_info in list(self.running_tasks.items()):
            if task_info['status'] == 'running':
                elapsed = (current_time - task_info['start_time']).total_seconds()
                if elapsed > default_timeout:
                    logger.warning(f"任务 {task_id} 超时 ({elapsed:.1f}s > {default_timeout}s)")

                    # 标记为超时
                    task_info['status'] = 'timeout'
                    task_info['error'] = '任务执行超时'
                    task_info['end_time'] = current_time

                    self.integration_metrics['active_tasks'] -= 1

    async def process_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """处理爬虫请求

        Args:
            request: 请求参数

        Returns:
            处理结果
        """
        self.integration_metrics['total_requests'] += 1

        request_id = request.get('request_id', f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        user_input = request.get('user_input', '')
        context = request.get('context', {})
        execution_mode = request.get('mode', 'auto')  # auto, xiaonuo, direct, scheduled
        scenario = request.get('scenario')
        urls = request.get('urls', [])
        config = request.get('config', {})

        logger.info(f"处理爬虫请求 {request_id}: {user_input}")

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
                xiaonuo_result = await self.xiaonuo_controller.smart_crawler_execution(
                    user_input, context
                )
                result.update({
                    'success': xiaonuo_result['success'],
                    'xiaonuo_analysis': xiaonuo_result['analysis'],
                    'execution_result': xiaonuo_result.get('execution_result')
                })

            elif execution_mode == 'direct' or scenario or urls:
                # 直接执行模式
                self.integration_metrics['direct_executions'] += 1
                if scenario:
                    # 预定义场景
                    execution_result = await self.crawler_tool.execute_scenario(
                        CrawlerScenario(scenario),
                        {
                            'urls': urls,
                            **config
                        }
                    )
                else:
                    # 自定义任务
                    execution_result = await self.crawler_tool.execute_custom_task(urls, config)

                result.update({
                    'success': execution_result.success,
                    'execution_result': {
                        'task_id': execution_result.task_id,
                        'data_count': len(execution_result.data),
                        'execution_time': execution_result.execution_time,
                        'stats': execution_result.stats
                    },
                    'data_preview': execution_result.data[:5] if execution_result.data else []
                })

                # 记录场景使用情况
                if scenario:
                    self.integration_metrics['scenarios_used'][scenario] = \
                        self.integration_metrics['scenarios_used'].get(scenario, 0) + 1

            elif execution_mode == 'scheduled':
                # 调度执行模式
                scheduled_result = await self._schedule_task(request)
                result.update({
                    'success': scheduled_result['success'],
                    'scheduled_task_id': scheduled_result.get('task_id'),
                    'scheduled_at': scheduled_result.get('scheduled_at')
                })

            else:
                result['error'] = '没有可用的执行模式'

            # 更新成功计数
            if result['success']:
                self.integration_metrics['successful_requests'] += 1

            return result

        except Exception as e:
            logger.error(f"处理爬虫请求失败: {e}")
            return {
                'request_id': request_id,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def _schedule_task(self, request: dict[str, Any]) -> dict[str, Any]:
        """调度任务执行"""
        if not self.task_scheduler:
            return {
                'success': False,
                'error': '任务调度器未启用'
            }

        # 检查并发限制
        if self.integration_metrics['active_tasks'] >= self.service_config['max_concurrent_tasks']:
            return {
                'success': False,
                'error': '达到最大并发任务数限制'
            }

        # 创建任务
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        task_data = {
            'task_id': task_id,
            'type': 'scenario' if request.get('scenario') else 'custom',
            'scenario': request.get('scenario'),
            'urls': request.get('urls', []),
            'config': request.get('config', {}),
            'params': request.get('params', {}),
            'scheduled_at': datetime.now().isoformat()
        }

        # 添加到调度队列
        await self.task_scheduler.put(task_data)
        self.integration_metrics['active_tasks'] += 1

        return {
            'success': True,
            'task_id': task_id,
            'scheduled_at': task_data['scheduled_at'],
            'queue_size': self.task_scheduler.qsize()
        }

    async def batch_process(self, requests: list[dict[str, Any]) -> list[dict[str, Any]:
        """批量处理请求

        Args:
            requests: 请求列表

        Returns:
            处理结果列表
        """
        logger.info(f"批量处理 {len(requests)} 个爬虫请求")

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
        return await self.crawler_tool.list_scenarios()

    async def get_service_status(self) -> dict[str, Any]:
        """获取服务状态"""
        return {
            'service': 'CrawlerIntegrationService',
            'status': self.service_status,
            'config': self.service_config,
            'metrics': self.integration_metrics,
            'components': {
                'crawler_tool': self.crawler_tool.get_status(),
                'xiaonuo_controller': self.xiaonuo_controller.get_status(),
                'task_scheduler': {
                    'enabled': self.task_scheduler is not None,
                    'queue_size': self.task_scheduler.qsize() if self.task_scheduler else 0,
                    'active_tasks': len(self.running_tasks)
                }
            },
            'running_tasks': {
                task_id: {
                    'worker_id': info['worker_id'],
                    'status': info['status'],
                    'start_time': info['start_time'].isoformat(),
                    'duration': (datetime.now() - info['start_time']).total_seconds()
                }
                for task_id, info in self.running_tasks.items()
            },
            'timestamp': datetime.now().isoformat()
        }

    async def get_task_status(self, task_id: str) -> dict[str, Any | None]:
        """获取任务状态"""
        # 检查运行中的任务
        if task_id in self.running_tasks:
            task_info = self.running_tasks[task_id]
            return {
                'task_id': task_id,
                'status': task_info['status'],
                'worker_id': task_info['worker_id'],
                'start_time': task_info['start_time'].isoformat(),
                'duration': (datetime.now() - task_info['start_time']).total_seconds(),
                'result': task_info.get('result'),
                'error': task_info.get('error')
            }

        # 检查爬虫工具中的任务
        crawler_task_status = await self.crawler_tool.get_task_status(task_id)
        if crawler_task_status:
            return crawler_task_status

        return None

    async def cancel_task(self, task_id: str) -> dict[str, Any]:
        """取消任务"""
        if task_id not in self.running_tasks:
            return {
                'success': False,
                'error': '任务不存在或已完成'
            }

        # 更新任务状态
        self.running_tasks[task_id]['status'] = 'cancelled'
        self.running_tasks[task_id]['end_time'] = datetime.now()

        self.integration_metrics['active_tasks'] -= 1

        return {
            'success': True,
            'message': f"任务 {task_id} 已取消"
        }

    async def update_config(self, new_config: dict[str, Any]):
        """更新服务配置"""
        self.service_config.update(new_config)
        logger.info(f"爬虫服务配置已更新: {new_config}")

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
            'scenarios_used': {},
            'data_collected_gb': 0.0,
            'active_tasks': 0
        }
        logger.info('爬虫服务指标已重置')

    async def shutdown(self):
        """关闭服务"""
        logger.info('正在关闭爬虫集成服务...')

        try:
            # 等待所有运行任务完成
            while self.running_tasks:
                logger.info(f"等待 {len(self.running_tasks)} 个任务完成...")
                await asyncio.sleep(5)

            # 关闭爬虫工具
            await self.crawler_tool.shutdown()

            self.service_status = 'shutdown'
            logger.info('爬虫集成服务已关闭')

        except Exception as e:
            logger.error(f"关闭服务时出错: {e}")

# 全局服务实例
crawler_integration_service: CrawlerIntegrationService | None = None

def get_crawler_integration_service(config: dict[str, Any] | None = None) -> CrawlerIntegrationService:
    """获取爬虫集成服务实例"""
    global crawler_integration_service
    if crawler_integration_service is None:
        default_config = {
            'max_concurrent_tasks': 10,
            'default_timeout': 300
        }
        if config:
            default_config.update(config)
        crawler_integration_service = CrawlerIntegrationService(default_config)
    return crawler_integration_service

# 测试函数
async def test_crawler_integration_service():
    """测试爬虫集成服务"""
    logger.info('🕷️ 测试爬虫集成服务')
    logger.info(str('=' * 50))

    service = get_crawler_integration_service()

    # 等待服务初始化
    await asyncio.sleep(3)

    # 测试请求
    test_requests = [
        {
            'user_input': '爬取AI相关的专利信息',
            'mode': 'xiaonuo',
            'context': {'user': 'test_user'}
        },
        {
            'user_input': '收集网站数据',
            'mode': 'direct',
            'scenario': 'website_scraping',
            'urls': ['https://example.com']
        },
        {
            'user_input': '执行数据收集任务',
            'mode': 'scheduled',
            'scenario': 'data_collection'
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
    logger.info(f"   数据收集量: {status['metrics']['data_collected_gb']:.2f} GB")

    # 获取可用场景
    scenarios = await service.get_available_scenarios()
    logger.info(f"\n🎯 可用场景数: {scenarios['total_count']}")

    logger.info("\n✅ 爬虫集成服务测试完成")

if __name__ == '__main__':
    asyncio.run(test_crawler_integration_service())
