#!/usr/bin/env python3
"""
智能体编排器
Agent Orchestrator - 负责专业智能体的生命周期管理和协调
"""

import asyncio
import logging
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import psutil

logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    """智能体状态枚举"""
    INACTIVE = "inactive"      # 未启动
    STARTING = "starting"      # 启动中
    ACTIVE = "active"          # 运行中
    BUSY = "busy"              # 忙碌中
    IDLE = "idle"              # 空闲中
    STOPPING = "stopping"      # 停止中
    ERROR = "error"            # 错误状态

@dataclass
class AgentConfig:
    """智能体配置"""
    name: str
    display_name: str
    role: str
    startup_script: str
    port: int
    health_check_url: str = ""
    startup_timeout: int = 30
    idle_timeout: int = 300  # 5分钟后自动停止
    dependencies: list[str] = field(default_factory=list)
    max_concurrent_tasks: int = 5
    environment: dict[str, str] = field(default_factory=dict)

@dataclass
class AgentTask:
    """智能体任务"""
    id: str
    agent_name: str
    task_type: str
    parameters: dict[str, Any]
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    timeout: int = 60

class ProcessManager:
    """进程管理器"""

    @staticmethod
    def is_port_in_use(port: int) -> bool:
        """检查端口是否被占用"""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port:
                    return True
            return False
        except Exception:
            return False

    @staticmethod
    def find_process_by_port(port: int) -> psutil.Process | None:
        """根据端口查找进程"""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.pid:
                    return psutil.Process(conn.pid)
        except Exception:
            pass
        return None

    @staticmethod
    def kill_process_by_port(port: int) -> bool:
        """根据端口杀死进程"""
        try:
            process = ProcessManager.find_process_by_port(port)
            if process:
                process.terminate()
                process.wait(timeout=5)
                return True
        except Exception as e:
            logger.error(f"无法杀死端口 {port} 的进程: {e}")
        return False

class AgentOrchestrator:
    """智能体编排器"""

    def __init__(self):
        self.agents: dict[str, AgentConfig] = {}
        self.agent_status: dict[str, AgentStatus] = {}
        self.agent_processes: dict[str, subprocess.Popen] = {}
        self.agent_last_activity: dict[str, datetime] = {}
        self.task_queue: list[AgentTask] = []
        self.active_tasks: dict[str, AgentTask] = {}

        self._initialize_agents()

        # 后台监控任务将在系统启动时启动

    def _initialize_agents(self):
        """初始化智能体配置"""
        self.agents = {
            "xiaona": AgentConfig(
                name="xiaona",
                display_name="小娜·天秤女神",
                role="专利法律专家",
                startup_script="services/xiaonuo/start_xiaona_legal_support.py",
                port=8006,
                health_check_url="http://localhost:8006/health",
                dependencies=["python3"],
                environment={"PYTHONPATH": "/Users/xujian/Athena工作平台"}
            ),
            "yunxi": AgentConfig(
                name="yunxi",
                display_name="云熙·织女星",
                role="IP管理专家",
                startup_script="services/yunxi-ip/yunxi_simple_api.py",
                port=8007,
                health_check_url="http://localhost:8007/health",
                dependencies=["python3", "fastapi"],
                environment={"PYTHONPATH": "/Users/xujian/Athena工作平台"}
            ),
            "athena": AgentConfig(
                name="athena",
                display_name="Athena·智慧女神",
                role="平台核心智能体",
                startup_script="core/athena_core_system.py",
                port=8005,
                health_check_url="http://localhost:8005/health",
                dependencies=["python3"],
                environment={"PYTHONPATH": "/Users/xujian/Athena工作平台"}
            ),
            "xiaochen": AgentConfig(
                name="xiaochen",
                display_name="小宸",
                role="自媒体运营专家",
                startup_script="services/xiaochen/social_media_agent.py",
                port=8008,
                health_check_url="http://localhost:8008/health",
                dependencies=["python3"],
                environment={"PYTHONPATH": "/Users/xujian/Athena工作平台"}
            )
        }

        # 初始化状态
        for agent_name in self.agents:
            self.agent_status[agent_name] = AgentStatus.INACTIVE
            self.agent_last_activity[agent_name] = datetime.now()

    async def launch_agent(self, agent_name: str, force: bool = False) -> bool:
        """启动智能体"""
        if agent_name not in self.agents:
            logger.error(f"未知的智能体: {agent_name}")
            return False

        if self.agent_status[agent_name] in [AgentStatus.ACTIVE, AgentStatus.STARTING] and not force:
            logger.info(f"智能体 {agent_name} 已在运行或启动中")
            return True

        config = self.agents[agent_name]

        try:
            logger.info(f"🚀 启动智能体: {config.display_name}")
            self.agent_status[agent_name] = AgentStatus.STARTING

            # 检查端口是否被占用
            if ProcessManager.is_port_in_use(config.port):
                if not force:
                    logger.warning(f"端口 {config.port} 已被占用，跳过启动")
                    self.agent_status[agent_name] = AgentStatus.ERROR
                    return False
                else:
                    logger.info(f"强制释放端口 {config.port}")
                    ProcessManager.kill_process_by_port(config.port)

            # 准备启动命令
            cmd = ["python3", config.startup_script]
            env = dict(config.environment)

            # 启动进程
            process = subprocess.Popen(
                cmd,
                cwd="/Users/xujian/Athena工作平台/deploy",
                env={**dict(os.environ), **env},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            self.agent_processes[agent_name] = process

            # 等待启动完成
            start_time = time.time()
            while time.time() - start_time < config.startup_timeout:
                if process.poll() is not None:
                    # 进程已退出
                    stdout, stderr = process.communicate()
                    logger.error(f"智能体 {agent_name} 启动失败:")
                    logger.error(f"stdout: {stdout}")
                    logger.error(f"stderr: {stderr}")
                    self.agent_status[agent_name] = AgentStatus.ERROR
                    return False

                # 检查健康状态
                if await self._health_check(agent_name):
                    self.agent_status[agent_name] = AgentStatus.ACTIVE
                    self.agent_last_activity[agent_name] = datetime.now()
                    logger.info(f"✅ 智能体 {config.display_name} 启动成功")
                    return True

                await asyncio.sleep(1)

            # 启动超时
            logger.error(f"智能体 {agent_name} 启动超时")
            self.agent_status[agent_name] = AgentStatus.ERROR
            process.terminate()
            return False

        except Exception as e:
            logger.error(f"启动智能体 {agent_name} 时发生错误: {e}")
            self.agent_status[agent_name] = AgentStatus.ERROR
            return False

    async def stop_agent(self, agent_name: str) -> bool:
        """停止智能体"""
        if agent_name not in self.agents:
            logger.error(f"未知的智能体: {agent_name}")
            return False

        if self.agent_status[agent_name] == AgentStatus.INACTIVE:
            return True

        logger.info(f"⏹️ 停止智能体: {self.agents[agent_name].display_name}")
        self.agent_status[agent_name] = AgentStatus.STOPPING

        try:
            process = self.agent_processes.get(agent_name)
            if process:
                # 先尝试优雅终止
                process.terminate()

                # 等待进程结束
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # 强制杀死
                    process.kill()
                    process.wait()

                del self.agent_processes[agent_name]

            # 清理端口
            config = self.agents[agent_name]
            ProcessManager.kill_process_by_port(config.port)

            self.agent_status[agent_name] = AgentStatus.INACTIVE
            logger.info(f"✅ 智能体 {agent_name} 已停止")
            return True

        except Exception as e:
            logger.error(f"停止智能体 {agent_name} 时发生错误: {e}")
            self.agent_status[agent_name] = AgentStatus.ERROR
            return False

    async def restart_agent(self, agent_name: str) -> bool:
        """重启智能体"""
        await self.stop_agent(agent_name)
        await asyncio.sleep(2)
        return await self.launch_agent(agent_name)

    async def _health_check(self, agent_name: str) -> bool:
        """健康检查"""
        if agent_name not in self.agents:
            return False

        config = self.agents[agent_name]

        # 检查进程状态
        process = self.agent_processes.get(agent_name)
        if process and process.poll() is not None:
            return False

        # 检查端口是否开放
        if not ProcessManager.is_port_in_use(config.port):
            return False

        # 如果配置了健康检查URL，进行HTTP检查
        if config.health_check_url:
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(config.health_check_url, timeout=2) as response:
                        return response.status == 200
            except Exception:
                return False

        return True

    async def submit_task(self, task: AgentTask) -> bool:
        """提交任务给智能体"""
        if task.agent_name not in self.agents:
            logger.error(f"未知的智能体: {task.agent_name}")
            return False

        # 确保智能体已启动
        if self.agent_status[task.agent_name] == AgentStatus.INACTIVE:
            if not await self.launch_agent(task.agent_name):
                return False

        # 检查智能体是否可以接受新任务
        config = self.agents[task.agent_name]
        active_count = len([t for t in self.active_tasks.values() if t.agent_name == task.agent_name])

        if active_count >= config.max_concurrent_tasks:
            logger.warning(f"智能体 {task.agent_name} 已达到最大并发任务数")
            self.task_queue.append(task)
            return False

        # 执行任务
        self.active_tasks[task.id] = task
        self.agent_status[task.agent_name] = AgentStatus.BUSY
        self.agent_last_activity[task.agent_name] = datetime.now()

        # 异步执行任务
        asyncio.create_task(self._execute_task(task))

        return True

    async def _execute_task(self, task: AgentTask):
        """执行任务"""
        try:
            logger.info(f"🎯 执行任务 {task.id} 在智能体 {task.agent_name}")

            # 这里实现具体的任务执行逻辑
            # 可以是HTTP请求、进程间通信等

            # 模拟任务执行
            await asyncio.sleep(2)

            logger.info(f"✅ 任务 {task.id} 执行完成")

        except Exception as e:
            logger.error(f"❌ 任务 {task.id} 执行失败: {e}")
        finally:
            # 清理任务记录
            if task.id in self.active_tasks:
                del self.active_tasks[task.id]

            # 更新智能体状态
            active_count = len([t for t in self.active_tasks.values() if t.agent_name == task.agent_name])
            if active_count == 0:
                self.agent_status[task.agent_name] = AgentStatus.IDLE

            # 处理队列中的下一个任务
            await self._process_next_task(task.agent_name)

    async def _process_next_task(self, agent_name: str):
        """处理队列中的下一个任务"""
        # 找到该智能体的下一个任务
        next_task = None
        for i, task in enumerate(self.task_queue):
            if task.agent_name == agent_name:
                next_task = self.task_queue.pop(i)
                break

        if next_task:
            await self.submit_task(next_task)

    async def _monitor_agents(self):
        """监控智能体状态"""
        while True:
            try:
                for agent_name, _config in self.agents.items():
                    if self.agent_status[agent_name] in [AgentStatus.ACTIVE, AgentStatus.IDLE, AgentStatus.BUSY]:
                        # 进行健康检查
                        is_healthy = await self._health_check(agent_name)
                        if not is_healthy:
                            logger.warning(f"⚠️ 智能体 {agent_name} 健康检查失败")
                            self.agent_status[agent_name] = AgentStatus.ERROR
                            # 尝试重启
                            await self.launch_agent(agent_name, force=True)

                await asyncio.sleep(30)  # 每30秒检查一次

            except Exception as e:
                logger.error(f"监控智能体时发生错误: {e}")
                await asyncio.sleep(10)

    async def _cleanup_idle_agents(self):
        """清理空闲的智能体"""
        while True:
            try:
                current_time = datetime.now()

                for agent_name, config in self.agents.items():
                    if self.agent_status[agent_name] == AgentStatus.IDLE:
                        idle_time = current_time - self.agent_last_activity[agent_name]
                        if idle_time.total_seconds() > config.idle_timeout:
                            logger.info(f"🧹 智能体 {agent_name} 空闲超时，自动停止")
                            await self.stop_agent(agent_name)

                await asyncio.sleep(60)  # 每分钟检查一次

            except Exception as e:
                logger.error(f"清理空闲智能体时发生错误: {e}")
                await asyncio.sleep(30)

    def get_agent_status(self, agent_name: str | None = None) -> dict[str, Any]:
        """获取智能体状态"""
        if agent_name:
            return {
                "name": agent_name,
                "status": self.agent_status.get(agent_name, AgentStatus.INACTIVE).value,
                "last_activity": self.agent_last_activity.get(agent_name).isoformat() if agent_name in self.agent_last_activity else None,
                "config": self.agents.get(agent_name).__dict__ if agent_name in self.agents else None,
                "active_tasks": len([t for t in self.active_tasks.values() if t.agent_name == agent_name])
            }
        else:
            return {
                name: self.get_agent_status(name)
                for name in self.agents.keys()
            }

    def get_system_overview(self) -> dict[str, Any]:
        """获取系统概览"""
        total_agents = len(self.agents)
        active_agents = len([s for s in self.agent_status.values() if s == AgentStatus.ACTIVE])
        idle_agents = len([s for s in self.agent_status.values() if s == AgentStatus.IDLE])
        error_agents = len([s for s in self.agent_status.values() if s == AgentStatus.ERROR])

        return {
            "total_agents": total_agents,
            "active_agents": active_agents,
            "idle_agents": idle_agents,
            "inactive_agents": total_agents - active_agents - idle_agents - error_agents,
            "error_agents": error_agents,
            "pending_tasks": len(self.task_queue),
            "active_tasks": len(self.active_tasks),
            "timestamp": datetime.now().isoformat()
        }

# 全局实例（延迟初始化）
agent_orchestrator = None

def get_agent_orchestrator():
    """获取智能体编排器实例（延迟初始化）"""
    global agent_orchestrator
    if agent_orchestrator is None:
        agent_orchestrator = AgentOrchestrator()
    return agent_orchestrator

# 测试代码
async def main():
    """测试智能体编排器"""
    print("🎭 智能体编排器测试")
    print("=" * 50)

    # 获取系统概览
    overview = agent_orchestrator.get_system_overview()
    print(f"系统概览: {overview}")

    # 启动一个智能体
    print("\n🚀 启动云熙智能体...")
    success = await agent_orchestrator.launch_agent("yunxi")
    print(f"启动结果: {success}")

    # 获取状态
    status = agent_orchestrator.get_agent_status("yunxi")
    print(f"云熙状态: {status}")

    # 提交任务
    task = AgentTask(
        id="test_task_001",
        agent_name="yunxi",
        task_type="ip_management",
        parameters={"action": "query", "target": "patent_info"}
    )

    print("\n📋 提交测试任务...")
    task_success = await agent_orchestrator.submit_task(task)
    print(f"任务提交结果: {task_success}")

    # 等待任务完成
    await asyncio.sleep(5)

    # 停止智能体
    print("\n⏹️ 停止云熙智能体...")
    stop_success = await agent_orchestrator.stop_agent("yunxi")
    print(f"停止结果: {stop_success}")

    # 最终状态
    final_overview = agent_orchestrator.get_system_overview()
    print(f"\n最终系统概览: {final_overview}")

if __name__ == "__main__":
    import os
    asyncio.run(main())
