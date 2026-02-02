#!/usr/bin/env python3
"""
Athena平台通用工具 - 浏览器自动化
可由小诺智能控制的browser-use集成工具
"""

import asyncio
import json
import logging
from core.logging_config import setup_logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'services' / 'browser-automation'))

from athena_browser_glm import AthenaBrowserGLMAgent

# 导入安全配置
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "core"))
from security.env_config import get_env_var, get_database_url, get_jwt_secret

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class BrowserAutomationTool:
    """浏览器自动化通用工具类"""
    
    # 工具定义
    TOOL_DEFINITION = {
        'name': 'browser_automation',
        'display_name': '智能浏览器自动化',
        'description': '基于AI的智能浏览器自动化工具，可执行各种网页操作任务',
        'version': '1.0.0',
        'capabilities': [
            '网页导航和操作',
            '数据提取和抓取',
            '表单自动填写',
            '搜索和信息收集',
            '价格监控',
            '社交媒体管理',
            '专利检索',
            '学术研究辅助'
        ],
        'status': 'ready',
        'last_used': None,
        'usage_count': 0
    }
    
    # 预定义场景模板
    SCENARIOS = {
        'competitor_monitor': {
            'name': '竞品监控',
            'description': '监控竞争对手网站的最新动态',
            'task_template': '访问 {url}，查找产品更新、新闻动态、价格变化等信息',
            'suitable_sites': ['电商网站', '企业官网', '产品页面']
        },
        'price_monitor': {
            'name': '价格监控',
            'description': '监控指定商品的价格变化',
            'task_template': '访问 {url}，获取商品价格、折扣信息、库存状态',
            'suitable_sites': ['淘宝', '京东', '亚马逊', '拼多多']
        },
        'data_collection': {
            'name': '数据收集',
            'description': '从网站批量收集结构化数据',
            'task_template': '访问 {url}，提取{data_type}信息并整理成表格',
            'suitable_sites': ['数据网站', '信息门户', '报告页面']
        },
        'form_automation': {
            'name': '表单自动化',
            'description': '自动填写和提交在线表单',
            'task_template': '访问 {url}，使用{data}填写表单并提交',
            'suitable_sites': ['注册页面', '申报系统', '问卷调查']
        },
        'social_media': {
            'name': '社交媒体管理',
            'description': '自动管理社交媒体账号',
            'task_template': '访问 {platform}，执行{action}操作',
            'suitable_sites': ['微博', '微信公众号', '抖音', '小红书']
        },
        'patent_search': {
            'name': '专利检索',
            'description': '检索和分析专利信息',
            'task_template': '在{database}中检索{query}相关的专利，分析技术趋势',
            'suitable_sites': ['专利数据库', '学术网站', '研究门户']
        },
        'news_monitor': {
            'name': '新闻监控',
            'description': '监控特定主题的新闻动态',
            'task_template': '搜索关于{topic}的最新新闻，提取关键信息',
            'suitable_sites': ['新闻网站', '媒体门户', '搜索引擎']
        }
    }
    
    def __init__(self):
        """初始化工具"""
        self.tool_info = self.TOOL_DEFINITION.copy()
        self.agent: AthenaBrowserGLMAgent | None = None
        self.is_active = False
        self.current_task = None
        self.task_history = []
        
    async def initialize(self) -> Dict[str, Any]:
        """初始化工具"""
        try:
            logger.info('初始化浏览器自动化工具...')
            
            # 创建代理实例
            self.agent = AthenaBrowserGLMAgent(
                api_key='9efe5766a7cd4bb687e40082ee4032b6.0mYTotbC7aRmoNCe'
            )
            
            # 启动会话
            await self.agent.start_session()
            
            self.is_active = True
            self.tool_info['status'] = 'active'
            
            logger.info('浏览器自动化工具初始化成功')
            
            return {
                'success': True,
                'message': '浏览器自动化工具已启动',
                'tool_info': self.tool_info,
                'available_scenarios': list(self.SCENARIOS.keys())
            }
            
        except Exception as e:
            logger.error(f"工具初始化失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '工具启动失败'
            }
    
    async def shutdown(self) -> Dict[str, Any]:
        """关闭工具"""
        try:
            logger.info('关闭浏览器自动化工具...')
            
            if self.agent:
                await self.agent.stop_session()
                self.agent = None
            
            self.is_active = False
            self.tool_info['status'] = 'inactive'
            self.current_task = None
            
            logger.info('浏览器自动化工具已关闭')
            
            return {
                'success': True,
                'message': '工具已关闭',
                'usage_stats': {
                    'total_tasks': len(self.task_history),
                    'session_duration': self.tool_info.get('session_duration', 'unknown')
                }
            }
            
        except Exception as e:
            logger.error(f"工具关闭失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """获取工具状态"""
        return {
            'tool': self.tool_info['name'],
            'display_name': self.tool_info['display_name'],
            'status': self.tool_info['status'],
            'is_active': self.is_active,
            'current_task': self.current_task,
            'task_count': len(self.task_history),
            'last_used': self.tool_info['last_used']
        }
    
    def get_scenarios(self) -> List[Dict[str, Any]]:
        """获取可用场景"""
        scenarios = []
        for key, scenario in self.SCENARIOS.items():
            scenarios.append({
                'id': key,
                'name': scenario['name'],
                'description': scenario['description'],
                'suitable_sites': scenario.get('suitable_sites', [])
            })
        return scenarios
    
    async def execute_scenario(self, scenario_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行预定义场景"""
        if scenario_id not in self.SCENARIOS:
            return {
                'success': False,
                'error': f"未知场景: {scenario_id}",
                'available_scenarios': list(self.SCENARIOS.keys())
            }
        
        if not self.is_active:
            await self.initialize()
        
        scenario = self.SCENARIOS[scenario_id]
        
        # 构建任务
        task = scenario['task_template'].format(**params)
        
        # 记录任务开始
        self.current_task = {
            'scenario': scenario_id,
            'task': task,
            'params': params,
            'start_time': datetime.now().isoformat(),
            'status': 'executing'
        }
        
        logger.info(f"执行场景: {scenario['name']}")
        logger.info(f"任务: {task}")
        
        try:
            # 执行任务
            result = await self.agent.execute_task(task)
            
            # 更新任务状态
            self.current_task['status'] = 'completed'
            self.current_task['end_time'] = datetime.now().isoformat()
            self.current_task['result'] = result
            
            # 添加到历史记录
            self.task_history.append(self.current_task.copy())
            
            # 更新工具信息
            self.tool_info['last_used'] = datetime.now().isoformat()
            self.tool_info['usage_count'] += 1
            self.tool_info['session_duration'] = (
                datetime.now() - datetime.fromisoformat(self.current_task['start_time'])
            ).total_seconds()
            
            logger.info(f"场景执行成功: {scenario['name']}")
            
            return {
                'success': True,
                'scenario': scenario_id,
                'task': task,
                'result': result,
                'execution_time': self.current_task['end_time']
            }
            
        except Exception as e:
            # 更新任务状态为失败
            self.current_task['status'] = 'failed'
            self.current_task['error'] = str(e)
            self.current_task['end_time'] = datetime.now().isoformat()
            
            logger.error(f"场景执行失败: {e}")
            
            return {
                'success': False,
                'scenario': scenario_id,
                'error': str(e),
                'task': task
            }
    
    async def execute_custom_task(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行自定义任务"""
        if not self.is_active:
            await self.initialize()
        
        logger.info(f"执行自定义任务: {task}")
        
        # 记录任务
        self.current_task = {
            'type': 'custom',
            'task': task,
            'context': context,
            'start_time': datetime.now().isoformat(),
            'status': 'executing'
        }
        
        try:
            result = await self.agent.execute_task(task)
            
            self.current_task['status'] = 'completed'
            self.current_task['end_time'] = datetime.now().isoformat()
            self.current_task['result'] = result
            
            self.task_history.append(self.current_task.copy())
            
            self.tool_info['last_used'] = datetime.now().isoformat()
            self.tool_info['usage_count'] += 1
            
            logger.info('自定义任务执行成功')
            
            return {
                'success': True,
                'task': task,
                'result': result,
                'context': context
            }
            
        except Exception as e:
            self.current_task['status'] = 'failed'
            self.current_task['error'] = str(e)
            self.current_task['end_time'] = datetime.now().isoformat()
            
            logger.error(f"自定义任务执行失败: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'task': task
            }
    
    def get_task_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取任务历史"""
        return self.task_history[-limit:]
    
    def analyze_usage(self) -> Dict[str, Any]:
        """分析使用情况"""
        if not self.task_history:
            return {
                'total_tasks': 0,
                'scenarios_used': {},
                'average_execution_time': 0,
                'success_rate': 0
            }
        
        total_tasks = len(self.task_history)
        successful_tasks = len([t for t in self.task_history if t.get('status') == 'completed'])
        
        # 统计场景使用情况
        scenarios_used = {}
        for task in self.task_history:
            scenario = task.get('scenario', 'custom')
            scenarios_used[scenario] = scenarios_used.get(scenario, 0) + 1
        
        # 计算平均执行时间
        execution_times = []
        for task in self.task_history:
            if task.get('start_time') and task.get('end_time'):
                start = datetime.fromisoformat(task['start_time'])
                end = datetime.fromisoformat(task['end_time'])
                execution_times.append((end - start).total_seconds())
        
        avg_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        return {
            'total_tasks': total_tasks,
            'successful_tasks': successful_tasks,
            'success_rate': round((successful_tasks / total_tasks) * 100, 2),
            'scenarios_used': scenarios_used,
            'most_used_scenario': max(scenarios_used.items(), key=lambda x: x[1])[0] if scenarios_used else None,
            'average_execution_time': round(avg_time, 2),
            'total_usage_time': sum(execution_times)
        }


# 工具管理器
class BrowserToolManager:
    """浏览器自动化工具管理器"""
    
    def __init__(self):
        self.tools = {}
        self.default_tool = BrowserAutomationTool()
    
    def get_tool(self, tool_id: str = 'default') -> BrowserAutomationTool:
        """获取工具实例"""
        if tool_id not in self.tools:
            self.tools[tool_id] = BrowserAutomationTool()
        return self.tools[tool_id]
    
    async def initialize_all(self):
        """初始化所有工具"""
        for tool_id, tool in self.tools.items():
            await tool.initialize()


# 全局实例
browser_tool_manager = BrowserToolManager()


def get_browser_tool(tool_id: str = 'default') -> BrowserAutomationTool:
    """获取浏览器工具实例的便捷函数"""
    return browser_tool_manager.get_tool(tool_id)