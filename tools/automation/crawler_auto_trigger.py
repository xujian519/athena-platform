#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena爬虫自动触发器
当外部搜索引擎或MCP无法获取重要论文或网页时，自动启动爬虫尝试爬取
作者: 小娜 & 小诺
创建时间: 2025-12-04
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TriggerCondition(Enum):
    """触发条件"""
    SEARCH_FAILED = 'search_failed'
    MCP_FAILED = 'mcp_failed'
    TIMEOUT = 'timeout'
    NO_RESULTS = 'no_results'
    ERROR_RATE_HIGH = 'error_rate_high'

class CrawlerAutoTrigger:
    """爬虫自动触发器"""

    def __init__(self, crawler_path: str = None):
        """
        初始化自动触发器

        Args:
            crawler_path: 爬虫系统路径
        """
        self.crawler_path = crawler_path or '/Users/xujian/Athena工作平台/services/crawler-service'
        self.trigger_rules = self._load_trigger_rules()
        self.crawler_tasks = {}
        self.execution_history = []

        logger.info('🚀 爬虫自动触发器初始化完成')

    def _load_trigger_rules(self) -> Dict[str, Any]:
        """加载触发规则"""
        return {
            'patent_search': {
                'triggers': [TriggerCondition.SEARCH_FAILED, TriggerCondition.NO_RESULTS],
                'spider': 'patent_google',
                'priority': 'high',
                'max_retries': 2,
                'timeout': 300
            },
            'academic_paper': {
                'triggers': [TriggerCondition.MCP_FAILED, TriggerCondition.TIMEOUT],
                'spider': 'literature_arxiv',
                'priority': 'medium',
                'max_retries': 1,
                'timeout': 180
            },
            'company_info': {
                'triggers': [TriggerCondition.SEARCH_FAILED],
                'spider': 'company_tianyancha',
                'priority': 'low',
                'max_retries': 1,
                'timeout': 120
            },
            'legal_document': {
                'triggers': [TriggerCondition.SEARCH_FAILED, TriggerCondition.MCP_FAILED],
                'spider': 'legal_govcn',
                'priority': 'high',
                'max_retries': 2,
                'timeout': 240
            }
        }

    async def check_and_trigger(self, search_result: Dict[str, Any]) -> Dict[str, Any | None]:
        """
        检查搜索结果并决定是否触发爬虫

        Args:
            search_result: 搜索结果信息

        Returns:
            爬虫任务信息或None
        """
        content_type = search_result.get('content_type', '')
        search_status = search_result.get('status', '')
        error_type = search_result.get('error_type', '')
        query = search_result.get('query', '')

        logger.info(f"🔍 检查搜索结果: {content_type} - {search_status}")

        # 确定触发条件
        trigger_condition = self._determine_trigger_condition(search_result)
        if not trigger_condition:
            logger.info('✅ 搜索结果正常，无需触发爬虫')
            return None

        # 查找匹配的爬虫规则
        crawler_rule = self._find_crawler_rule(content_type, trigger_condition)
        if not crawler_rule:
            logger.warning(f"⚠️ 没有找到匹配的爬虫规则: {content_type} - {trigger_condition}")
            return None

        # 创建爬虫任务
        task = await self._create_crawler_task(query, crawler_rule, search_result)
        if task:
            logger.info(f"🕷️ 创建爬虫任务: {task['task_id']}")
            return task

        return None

    def _determine_trigger_condition(self, search_result: Dict[str, Any]) -> TriggerCondition | None:
        """确定触发条件"""
        status = search_result.get('status', '')
        error_type = search_result.get('error_type', '')
        result_count = search_result.get('result_count', 0)
        response_time = search_result.get('response_time', 0)

        if status == 'failed' or status == 'error':
            if error_type == 'mcp_error':
                return TriggerCondition.MCP_FAILED
            elif error_type == 'search_error':
                return TriggerCondition.SEARCH_FAILED
            elif error_type == 'timeout':
                return TriggerCondition.TIMEOUT

        if result_count == 0:
            return TriggerCondition.NO_RESULTS

        if response_time > 30:  # 30秒超时
            return TriggerCondition.TIMEOUT

        return None

    def _find_crawler_rule(self, content_type: str, condition: TriggerCondition) -> Dict[str, Any | None]:
        """查找匹配的爬虫规则"""
        # 映射内容类型到爬虫类型
        type_mapping = {
            'patent': 'patent_search',
            'paper': 'academic_paper',
            'literature': 'academic_paper',
            'company': 'company_info',
            'enterprise': 'company_info',
            'legal': 'legal_document',
            'law': 'legal_document'
        }

        crawler_type = type_mapping.get(content_type.lower())
        if not crawler_type:
            return None

        rule = self.trigger_rules.get(crawler_type)
        if rule and condition in rule['triggers']:
            return rule

        return None

    async def _create_crawler_task(self, query: str, rule: Dict[str, Any],
                                 search_result: Dict[str, Any]) -> Dict[str, Any | None]:
        """创建爬虫任务"""
        task_id = f"crawler_{int(time.time())}_{hash(query) % 10000}"

        task = {
            'task_id': task_id,
            'query': query,
            'spider': rule['spider'],
            'priority': rule['priority'],
            'max_retries': rule['max_retries'],
            'timeout': rule['timeout'],
            'created_at': datetime.now().isoformat(),
            'status': 'pending',
            'original_search': search_result,
            'config': {
                'max_pages': 3,
                'download_delay': 2.0,
                'concurrent_requests': 2
            }
        }

        # 记录任务
        self.crawler_tasks[task_id] = task

        return task

    async def execute_crawler_task(self, task_id: str) -> Dict[str, Any]:
        """
        执行爬虫任务

        Args:
            task_id: 任务ID

        Returns:
            执行结果
        """
        task = self.crawler_tasks.get(task_id)
        if not task:
            return {
                'success': False,
                'error': f"任务不存在: {task_id}"
            }

        logger.info(f"🕷️ 执行爬虫任务: {task_id}")

        try:
            task['status'] = 'running'
            task['started_at'] = datetime.now().isoformat()

            # 执行爬虫
            result = await self._run_crawler(task)

            task['status'] = 'completed'
            task['completed_at'] = datetime.now().isoformat()
            task['result'] = result

            # 记录执行历史
            self.execution_history.append({
                'task_id': task_id,
                'spider': task['spider'],
                'query': task['query'],
                'status': 'success',
                'items_found': len(result.get('items', [])),
                'execution_time': result.get('execution_time', 0),
                'timestamp': datetime.now().isoformat()
            })

            logger.info(f"✅ 爬虫任务完成: {task_id}, 找到 {len(result.get('items', []))} 个结果")

            return {
                'success': True,
                'task_id': task_id,
                'result': result
            }

        except Exception as e:
            task['status'] = 'failed'
            task['error'] = str(e)
            task['failed_at'] = datetime.now().isoformat()

            logger.error(f"❌ 爬虫任务失败: {task_id} - {e}")

            return {
                'success': False,
                'task_id': task_id,
                'error': str(e)
            }

    async def _run_crawler(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """运行爬虫（模拟实现）"""
        start_time = time.time()

        # 模拟爬虫运行
        spider_name = task['spider']
        query = task['query']

        logger.info(f"🔍 启动爬虫: {spider_name}, 查询: {query}")

        # 这里应该集成真实的爬虫系统
        # 目前返回模拟结果
        await asyncio.sleep(2)  # 模拟爬虫运行时间

        execution_time = time.time() - start_time

        # 模拟爬取结果
        mock_items = [
            {
                'title': f"模拟爬取结果 1 - {query}",
                'url': f"https://example.com/result1?q={query}",
                'source': spider_name,
                'timestamp': datetime.now().isoformat()
            },
            {
                'title': f"模拟爬取结果 2 - {query}",
                'url': f"https://example.com/result2?q={query}",
                'source': spider_name,
                'timestamp': datetime.now().isoformat()
            }
        ]

        return {
            'spider': spider_name,
            'query': query,
            'items': mock_items,
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat()
        }

    def get_task_status(self, task_id: str) -> Dict[str, Any | None]:
        """获取任务状态"""
        return self.crawler_tasks.get(task_id)

    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取执行历史"""
        return self.execution_history[-limit:]

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_tasks = len(self.crawler_tasks)
        completed_tasks = sum(1 for task in self.crawler_tasks.values() if task['status'] == 'completed')
        failed_tasks = sum(1 for task in self.crawler_tasks.values() if task['status'] == 'failed')

        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks,
            'success_rate': completed_tasks / total_tasks if total_tasks > 0 else 0,
            'trigger_rules_count': len(self.trigger_rules),
            'last_updated': datetime.now().isoformat()
        }


# 全局实例
_crawler_trigger = None

def get_crawler_trigger() -> CrawlerAutoTrigger:
    """获取全局爬虫触发器实例"""
    global _crawler_trigger
    if _crawler_trigger is None:
        _crawler_trigger = CrawlerAutoTrigger()
    return _crawler_trigger


async def auto_trigger_crawler(search_result: Dict[str, Any]) -> Dict[str, Any | None]:
    """
    自动触发爬虫的便捷函数

    Args:
        search_result: 搜索结果信息

    Returns:
        爬虫任务信息或None
    """
    trigger = get_crawler_trigger()
    return await trigger.check_and_trigger(search_result)


# 测试函数
async def test_auto_trigger():
    """测试自动触发功能"""
    logger.info('🧪 测试爬虫自动触发功能...')

    # 模拟搜索失败结果
    failed_search = {
        'content_type': 'patent',
        'status': 'failed',
        'error_type': 'search_error',
        'query': 'machine learning patent',
        'result_count': 0
    }

    # 触发爬虫
    trigger = get_crawler_trigger()
    task = await trigger.check_and_trigger(failed_search)

    if task:
        logger.info(f"✅ 成功触发爬虫任务: {task['task_id']}")
        logger.info(f"   爬虫: {task['spider']}")
        logger.info(f"   查询: {task['query']}")

        # 执行任务
        result = await trigger.execute_crawler_task(task['task_id'])
        if result['success']:
            logger.info(f"✅ 爬虫任务执行成功")
            items = result['result']['items']
            logger.info(f"   找到 {len(items)} 个结果")
        else:
            logger.info(f"❌ 爬虫任务执行失败: {result['error']}")
    else:
        logger.info('❌ 未能触发爬虫任务')


if __name__ == '__main__':
    asyncio.run(test_auto_trigger())