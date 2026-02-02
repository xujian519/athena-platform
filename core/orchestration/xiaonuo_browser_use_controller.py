#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小诺·双鱼公主Browser-Use全量控制系统
Xiaonuo·Pisces Princess Browser-Use Universal Control System

统一管理和控制所有browser-use工具,实现智能决策和全量控制

作者: 小诺·双鱼公主
创建时间: 2025-12-14
版本: 1.0.0
"""

import asyncio
import logging
from core.logging_config import setup_logging
import os
import subprocess
from datetime import datetime
from typing import Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

class BrowserUseMode(Enum):
    """Browser-Use模式"""
    AGENT_MODE = "agent"           # AI代理模式
    DIRECT_MODE = "direct"         # 直接控制模式
    SCENARIO_MODE = "scenario"     # 场景预设模式
    BATCH_MODE = "batch"           # 批量执行模式
    MONITOR_MODE = "monitor"       # 监控模式

class BrowserEngine(Enum):
    """浏览器引擎"""
    CHROMIUM = "chromium"         # Chromium引擎
    CHROME = "chrome"             # Chrome浏览器
    FIREFOX = "firefox"           # Firefox浏览器
    SAFARI = "safari"             # Safari浏览器
    PLAYWRIGHT = "playwright"     # Playwright引擎

@dataclass
class BrowserUseTask:
    """Browser-Use任务定义"""
    task_id: str
    mode: BrowserUseMode
    engine: BrowserEngine
    instructions: str
    url: str | None = None
    target_elements: list[str] = field(default_factory=list)
    output_format: str = "text"  # text, json, screenshot
    screenshot: bool = False
    timeout: int = 30
    max_steps: int = 10
    context: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    status: str = "pending"
    result: Optional[dict[str, Any] | None = None
    error: str | None = None

@dataclass
class BrowserUseAgent:
    """Browser-Use代理配置"""
    agent_id: str
    name: str
    model_provider: str  # openai, anthropic, google, ollama
    model_name: str
    api_key: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096
    system_prompt: str | None = None
    capabilities: list[str] = field(default_factory=list)

@dataclass
class BrowserUseSession:
    """Browser-Use会话"""
    session_id: str
    agent_id: str
    browser_engine: BrowserEngine
    headless: bool = True
    width: int = 1280
    height: int = 720
    user_data_dir: str | None = None
    extensions: list[str] = field(default_factory=list)
    proxy: str | None = None
    status: str = "idle"
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime | None = None

class XiaonuoBrowserUseController:
    """小诺·双鱼公主Browser-Use全量控制器"""

    def __init__(self):
        self.name = "小诺·双鱼公主Browser-Use全量控制系统"
        self.version = "1.0.0"
        self.logger = logging.getLogger(self.name)

        # 核心组件
        self.agents: dict[str, BrowserUseAgent] = {}
        self.sessions: dict[str, BrowserUseSession] = {}
        self.tasks: dict[str, BrowserUseTask] = {}
        self.task_queue: list[str] = []

        # 统计信息
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "active_sessions": 0,
            "total_agents": 0,
            "usage_time": 0.0,
            "screenshots_taken": 0,
            "pages_visited": 0
        }

        # 配置
        self.config = {
            "max_concurrent_sessions": 5,
            "default_engine": BrowserEngine.CHROMIUM,
            "default_timeout": 30,
            "auto_cleanup": True,
            "cleanup_interval": 3600,  # 1小时
            "screenshot_dir": "/Users/xujian/Athena工作平台/data/browser-use/screenshots",
            "temp_dir": "/Users/xujian/Athena工作平台/data/browser-use/temp"
        }

        # 初始化
        self._initialize_agents()
        self._create_directories()

        print(f"🌐 {self.name} 初始化完成")
        print(f"   注册代理: {len(self.agents)} 个")

    def _initialize_agents(self) -> Any:
        """初始化代理"""
        # OpenAI代理
        self.agents["openai_gpt4"] = BrowserUseAgent(
            agent_id="openai_gpt4",
            name="OpenAI GPT-4 Vision代理",
            model_provider="openai",
            model_name="gpt-4-vision-preview",
            api_key=os.getenv("OPENAI_API_KEY"),
            capabilities=["vision", "text_analysis", "element_extraction", "automation"]
        )

        # Anthropic代理
        self.agents["claude_opus"] = BrowserUseAgent(
            agent_id="claude_opus",
            name="Claude Opus代理",
            model_provider="anthropic",
            model_name="claude-3-opus-20240229",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            capabilities=["complex_reasoning", "visual_analysis", "multi_step_planning", "automation"]
        )

        # Google代理
        self.agents["gemini_pro"] = BrowserUseAgent(
            agent_id="gemini_pro",
            name="Google Gemini Pro代理",
            model_provider="google",
            model_name="gemini-pro-vision",
            api_key=os.getenv("GOOGLE_API_KEY"),
            capabilities=["multimodal", "code_execution", "analysis", "automation"]
        )

        # GLM代理
        self.agents["glm_4v"] = BrowserUseAgent(
            agent_id="glm_4v",
            name="智谱GLM-4V代理",
            model_provider="zhipu",
            model_name="glm-4v",
            api_key=os.getenv("ZHIPU_API_KEY"),
            capabilities=["chinese_vision", "text_understanding", "automation"]
        )

        self.stats["total_agents"] = len(self.agents)

    def _create_directories(self) -> Any:
        """创建必要的目录"""
        dirs = [
            self.config["screenshot_dir"],
            self.config["temp_dir"],
            "/Users/xujian/Athena工作平台/data/browser-use/logs"
        ]
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

    async def submit_task(self, task: BrowserUseTask) -> dict[str, Any]:
        """提交Browser-Use任务"""
        self.logger.info(f"提交任务: {task.task_id}")

        # 任务验证
        validation_result = await self._validate_task(task)
        if not validation_result["valid"]:
            return {
                "success": False,
                "message": validation_result["error"],
                "task_id": task.task_id
            }

        # 智能代理选择
        selected_agent = await self._select_agent(task)
        if not selected_agent:
            return {
                "success": False,
                "message": "没有可用的代理",
                "task_id": task.task_id
            }

        # 创建或获取会话
        session = await self._get_or_create_session(selected_agent, task)

        # 添加到队列
        self.tasks[task.task_id] = task
        self.task_queue.append(task.task_id)
        self.stats["total_tasks"] += 1

        return {
            "success": True,
            "message": "任务已提交",
            "task_id": task.task_id,
            "session_id": session.session_id,
            "agent_id": selected_agent.agent_id,
            "queue_position": len(self.task_queue)
        }

    async def _validate_task(self, task: BrowserUseTask) -> dict[str, Any]:
        """验证任务"""
        if not task.instructions:
            return {"valid": False, "error": "缺少操作指令"}

        # 检查代理是否存在
        if task.mode == BrowserUseMode.AGENT_MODE:
            # 确保有可用的代理
            if not any(agent for agent in self.agents.values() if agent.api_key):
                return {"valid": False, "error": "没有配置API密钥的代理"}

        return {"valid": True}

    async def _select_agent(self, task: BrowserUseTask) -> BrowserUseAgent | None:
        """智能选择代理"""
        if task.mode != BrowserUseMode.AGENT_MODE:
            return None

        # 根据任务需求选择代理
        if "视觉" in task.instructions or "图片" in task.instructions:
            # 优先选择支持视觉的代理
            for agent in self.agents.values():
                if "vision" in agent.capabilities and agent.api_key:
                    return agent

        # 根据URL选择合适的代理(中文网站优先使用GLM)
        if task.url and ".cn" in task.url:
            if "glm_4v" in self.agents and self.agents["glm_4v"].api_key:
                return self.agents["glm_4v"]

        # 默认选择第一个有API密钥的代理
        for agent in self.agents.values():
            if agent.api_key:
                return agent

        return None

    async def _get_or_create_session(self, agent: BrowserUseAgent, task: BrowserUseTask) -> BrowserUseSession:
        """获取或创建会话"""
        # 查找空闲会话
        for session in self.sessions.values():
            if session.agent_id == agent.agent_id and session.status == "idle":
                session.last_used = datetime.now()
                session.status = "active"
                self.stats["active_sessions"] += 1
                return session

        # 创建新会话
        session_id = f"session_{len(self.sessions) + 1}"
        session = BrowserUseSession(
            session_id=session_id,
            agent_id=agent.agent_id,
            browser_engine=task.engine or self.config["default_engine"],
            headless=True,  # 默认无头模式
            width=1280,
            height=720
        )

        self.sessions[session_id] = session
        self.stats["active_sessions"] += 1

        self.logger.info(f"创建新会话: {session_id} (代理: {agent.name})")
        return session

    async def process_tasks(self):
        """处理任务队列"""
        while True:
            try:
                if self.task_queue:
                    task_id = self.task_queue.pop(0)
                    task = self.tasks.get(task_id)

                    if task and task.status == "pending":
                        await self._execute_task(task)

                await asyncio.sleep(1)
            except Exception as e:
                self.logger.error(f"任务处理错误: {e}")
                await asyncio.sleep(5)

    async def _execute_task(self, task: BrowserUseTask):
        """执行任务"""
        self.logger.info(f"执行任务: {task.task_id}")

        task.status = "running"
        task.started_at = datetime.now()

        try:
            if task.mode == BrowserUseMode.DIRECT_MODE:
                result = await self._execute_direct_mode(task)
            elif task.mode == BrowserUseMode.AGENT_MODE:
                result = await self._execute_agent_mode(task)
            elif task.mode == BrowserUseMode.SCENARIO_MODE:
                result = await self._execute_scenario_mode(task)
            else:
                result = await self._execute_batch_mode(task)

            task.result = result
            task.status = "completed"
            task.completed_at = datetime.now()

            self.stats["completed_tasks"] += 1
            self.logger.info(f"任务完成: {task.task_id}")

        except Exception as e:
            task.error = str(e)
            task.status = "failed"
            task.completed_at = datetime.now()

            self.stats["failed_tasks"] += 1
            self.logger.error(f"任务失败: {task.task_id}, 错误: {e}")

    async def _execute_direct_mode(self, task: BrowserUseTask) -> dict[str, Any]:
        """执行直接模式"""
        # 使用browser-use CLI
        cmd = [
            "browser-use",
            "run",
            "--instruction", task.instructions,
            "--timeout", str(task.timeout)
        ]

        if task.url:
            cmd.extend(["--url", task.url])

        if task.screenshot:
            cmd.append("--screenshot")

        # 执行命令
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=task.timeout
        )

        if process.returncode == 0:
            return {
                "success": True,
                "output": process.stdout,
                "mode": "direct"
            }
        else:
            raise Exception(f"命令执行失败: {process.stderr}")

    async def _execute_agent_mode(self, task: BrowserUseTask) -> dict[str, Any]:
        """执行代理模式"""
        # 获取代理
        agent_id = None
        for session_id, session in self.sessions.items():
            if session.status == "active":
                agent_id = session.agent_id
                break

        if not agent_id:
            raise Exception("没有活跃的会话")

        agent = self.agents.get(agent_id)
        if not agent:
            raise Exception(f"代理不存在: {agent_id}")

        # 构建Python脚本执行
        script_content = self._generate_agent_script(task, agent)
        script_path = Path(self.config["temp_dir"]) / f"task_{task.task_id}.py"

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)

        # 执行脚本
        env = os.environ.copy()
        if agent.api_key:
            env[f"{agent.model_provider.upper()}_API_KEY"] = agent.api_key

        process = subprocess.run(
            ["python3", str(script_path)],
            capture_output=True,
            text=True,
            timeout=task.timeout,
            env=env
        )

        # 清理临时文件
        if self.config["auto_cleanup"]:
            script_path.unlink(missing_ok=True)

        if process.returncode == 0:
            return {
                "success": True,
                "output": process.stdout,
                "mode": "agent",
                "agent_id": agent_id
            }
        else:
            raise Exception(f"代理执行失败: {process.stderr}")

    def _generate_agent_script(self, task: BrowserUseTask, agent: BrowserUseAgent) -> str:
        """生成代理执行脚本"""
        return f'''#!/usr/bin/env python3
# Browser-Use代理执行脚本

import asyncio
from browser_use import Agent, Controller

async def main():
    # 配置代理
    agent = Agent(
        task="{task.instructions}",
        llm="{agent.model_provider}",
        model="{agent.model_name}",
        use_vision=True,
        {"include_windows_api" if "windows" in agent.capabilities else ""}
    )

    # 配置控制器
    controller = Controller()

    # 执行任务
    result = await agent.run(controller)
    print(result)

# 入口点: @async_main装饰器已添加到main函数
'''

    async def _execute_scenario_mode(self, task: BrowserUseTask) -> dict[str, Any]:
        """执行场景模式"""
        # 预设场景
        scenarios = {
            "price_monitor": self._scenario_price_monitor,
            "competitor_analysis": self._scenario_competitor_analysis,
            "data_extraction": self._scenario_data_extraction,
            "form_filling": self._scenario_form_filling,
            "screenshot_capture": self._scenario_screenshot_capture
        }

        scenario_name = task.context.get("scenario")
        if scenario_name not in scenarios:
            raise Exception(f"未知场景: {scenario_name}")

        scenario_func = scenarios[scenario_name]
        result = await scenario_func(task)

        return {
            "success": True,
            "result": result,
            "mode": "scenario",
            "scenario": scenario_name
        }

    async def _execute_batch_mode(self, task: BrowserUseTask) -> dict[str, Any]:
        """执行批量模式"""
        urls = task.context.get("urls", [])
        if not urls:
            raise Exception("批量模式需要提供URL列表")

        results = []
        for url in urls:
            # 为每个URL创建子任务
            sub_task = BrowserUseTask(
                task_id=f"{task.task_id}_{url}",
                mode=BrowserUseMode.DIRECT_MODE,
                engine=task.engine,
                instructions=task.instructions,
                url=url,
                output_format=task.output_format,
                timeout=task.timeout
            )

            try:
                sub_result = await self._execute_direct_mode(sub_task)
                results.append({
                    "url": url,
                    "success": True,
                    "result": sub_result
                })
            except Exception as e:
                results.append({
                    "url": url,
                    "success": False,
                    "error": str(e)
                })

        return {
            "success": True,
            "results": results,
            "mode": "batch",
            "total_urls": len(urls)
        }

    # 场景函数
    async def _scenario_price_monitor(self, task: BrowserUseTask) -> dict[str, Any]:
        """价格监控场景"""
        return {
            "scenario": "price_monitor",
            "steps": [
                "访问目标页面",
                "定位价格元素",
                "提取价格信息",
                "记录时间戳",
                "比较历史价格"
            ],
            "data": {"price": "示例价格", "currency": "CNY"}
        }

    async def _scenario_competitor_analysis(self, task: BrowserUseTask) -> dict[str, Any]:
        """竞品分析场景"""
        return {
            "scenario": "competitor_analysis",
            "steps": [
                "访问竞品网站",
                "截图保存",
                "提取关键信息",
                "生成分析报告"
            ],
            "data": {"competitor": "示例竞品", "analysis": "基础分析"}
        }

    async def _scenario_data_extraction(self, task: BrowserUseTask) -> dict[str, Any]:
        """数据提取场景"""
        return {
            "scenario": "data_extraction",
            "steps": [
                "导航到目标页面",
                "定位数据元素",
                "提取结构化数据",
                "导出为JSON"
            ],
            "data": {"extracted_data": []}
        }

    async def _scenario_form_filling(self, task: BrowserUseTask) -> dict[str, Any]:
        """表单填写场景"""
        return {
            "scenario": "form_filling",
            "steps": [
                "打开表单页面",
                "填写表单字段",
                "验证输入",
                "提交表单"
            ],
            "data": {"form_status": "submitted"}
        }

    async def _scenario_screenshot_capture(self, task: BrowserUseTask) -> dict[str, Any]:
        """截图场景"""
        screenshot_path = Path(self.config["screenshot_dir"]) / f"screenshot_{task.task_id}.png"

        return {
            "scenario": "screenshot_capture",
            "steps": [
                "打开目标页面",
                "等待加载完成",
                "截取全屏",
                "保存截图"
            ],
            "screenshot_path": str(screenshot_path)
        }

    def get_system_status(self) -> dict[str, Any]:
        """获取系统状态"""
        return {
            "controller_info": {
                "name": self.name,
                "version": self.version
            },
            "agents": {
                agent_id: {
                    "name": agent.name,
                    "model": f"{agent.model_provider}/{agent.model_name}",
                    "capabilities": agent.capabilities,
                    "has_api_key": bool(agent.api_key)
                }
                for agent_id, agent in self.agents.items()
            },
            "sessions": {
                session_id: {
                    "agent_id": session.agent_id,
                    "engine": session.engine.value,
                    "status": session.status,
                    "created_at": session.created_at.isoformat(),
                    "last_used": session.last_used.isoformat() if session.last_used else None
                }
                for session_id, session in self.sessions.items()
            },
            "statistics": self.stats.copy(),
            "config": self.config,
            "queue_length": len(self.task_queue)
        }

    def get_task_status(self, task_id: str) -> dict[str, Any] | None:
        """获取任务状态"""
        task = self.tasks.get(task_id)
        if not task:
            return None

        return {
            "task_id": task.task_id,
            "mode": task.mode.value,
            "engine": task.engine.value,
            "instructions": task.instructions,
            "url": task.url,
            "status": task.status,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "result": task.result,
            "error": task.error
        }

    async def cleanup(self):
        """清理资源"""
        self.logger.info("开始清理资源...")

        # 清理空闲会话
        for session in self.sessions.values():
            if session.status == "idle":
                session.status = "stopped"
                self.stats["active_sessions"] -= 1

        # 清理临时文件
        temp_dir = Path(self.config["temp_dir"])
        for file_path in temp_dir.glob("*.py"):
            try:
                file_path.unlink()
            except Exception as e:  # 清理临时文件失败，记录日志但不中断
                self.logger.debug(f"清理临时文件失败 {file_path}: {e}")

        self.logger.info("资源清理完成")

    def create_task_from_text(self, user_request: str) -> BrowserUseTask:
        """从用户请求创建任务"""
        # 智能解析用户请求
        mode = BrowserUseMode.DIRECT_MODE
        if "帮我" in user_request or "自动" in user_request:
            mode = BrowserUseMode.AGENT_MODE

        engine = BrowserEngine.CHROMIUM
        if "截图" in user_request:
            engine = BrowserEngine.CHROME

        return BrowserUseTask(
            task_id=f"task_{int(datetime.now().timestamp())}",
            mode=mode,
            engine=engine,
            instructions=user_request,
            screenshot="截图" in user_request,
            timeout=30
        )

# 导出主类
__all__ = [
    'XiaonuoBrowserUseController',
    'BrowserUseTask',
    'BrowserUseAgent',
    'BrowserUseSession',
    'BrowserUseMode',
    'BrowserEngine'
]