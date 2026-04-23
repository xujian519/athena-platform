
import psutil

#!/usr/bin/env python3
"""
按需启动智能体编排器
On-Demand Agent Orchestrator

智能按需启动系统,小诺作为常驻调度中心,其他智能体按专业需求启动

架构设计:
┌─────────────┐    调度请求    ┌─────────────┐
│   用户请求   │ ──────────────→ │   小诺(常驻) │
│             │                │  总调度官   │
└─────────────┘                └─────────────┘
                                      │ 专业需求
                                      ▼
                               ┌─────────────┐
                               │ 按需启动    │
                               │ 专业智能体   │
                               └─────────────┘
                                      │
                          ┌───────────┼───────────┐
                          ▼           ▼
                    ┌─────────┐ ┌─────────┐
                    │ 小娜    │ │ 小宸    │
                    │ 专利专家│ │ 自媒体  │
                    └─────────┘ └─────────┘

作者: Athena AI团队
创建时间: 2025-12-17 06:30:00
版本: v1.0.0 "智能编排"
"""

import asyncio
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

class AgentType(Enum):
    """智能体类型"""
    XIAONUO = "xiaonuo"      # 小诺 - 常驻调度中心
    XIAONA = "xiaona"        # 小娜 - 专利法律专家
    XIAOCHEN = "xiaochen"    # 小宸 - 自媒体专家

class AgentStatus(Enum):
    """智能体状态"""
    STOPPED = "stopped"      # 已停止
    STARTING = "starting"    # 启动中
    RUNNING = "running"      # 运行中
    STOPPING = "stopping"    # 停止中
    ERROR = "error"          # 错误

@dataclass
class AgentConfig:
    """智能体配置"""
    name: str
    agent_type: AgentType
    port: int
    script_path: str
    startup_timeout: int = 30  # 启动超时时间(秒)
    idle_timeout: int = 300   # 空闲超时时间(秒)
    auto_stop: bool = True    # 是否自动停止
    dependencies: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    priority: int = 1  # 启动优先级

@dataclass
class TaskRequest:
    """任务请求"""
    task_id: str
    user_id: str
    task_type: str
    content: str
    context: dict[str, Any] = field(default_factory=dict)
    priority: int = 1
    required_capabilities: list[str] = field(default_factory=list)
    preferred_agent: Optional[str] = None

@dataclass
class AgentInstance:
    """智能体实例"""
    config: AgentConfig
    status: AgentStatus = AgentStatus.STOPPED
    process: subprocess.Optional[Popen] = None
    pid: Optional[int] = None
    start_time: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    task_count: int = 0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0

class OnDemandAgentOrchestrator:
    """按需启动智能体编排器"""

    def __init__(self):
        """初始化编排器"""
        self.project_root = Path(__file__).parent.parent.parent
        self.running_agents: dict[AgentType, AgentInstance] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.active_tasks: dict[str, TaskRequest] = {}
        self.agent_configs = self._load_agent_configs()
        self.xiaonuo_instance = None  # 小诺常驻实例

        # 性能统计
        self.stats = {
            'total_tasks': 0,
            'agent_starts': 0,
            'agent_stops': 0,
            'idle_time_saved': 0,
            'memory_saved': 0
        }

        # 启动小诺(常驻调度中心)
        asyncio.create_task(self._start_xiaonuo())

        # 启动调度器
        asyncio.create_task(self._task_scheduler())
        asyncio.create_task(self._idle_monitor())

        logger.info("🎭 按需启动智能体编排器已初始化")
        logger.info("👑 小诺已作为常驻调度中心启动")

    def _load_agent_configs(self) -> dict[AgentType, AgentConfig]:
        """加载智能体配置"""
        configs = {
            AgentType.XIAONUO: AgentConfig(
                name="小诺",
                agent_type=AgentType.XIAONUO,
                port=8005,
                script_path="services/intelligent-collaboration/xiaonuo_platform_controller.py",
                startup_timeout=20,
                idle_timeout=0,  # 小诺永不超时
                auto_stop=False,  # 小诺永不自动停止
                capabilities=["调度", "对话", "任务分配", "协调", "基础问答"]
            ),

            AgentType.XIAONA: AgentConfig(
                name="小娜",
                agent_type=AgentType.XIAONA,
                port=8001,
                script_path="services/autonomous-control/athena_control_server.py",
                startup_timeout=30,
                idle_timeout=600,  # 10分钟空闲后停止
                auto_stop=True,
                capabilities=["专利分析", "法律咨询", "权利要求撰写", "审查意见答复", "侵权分析"]
            ),


            AgentType.XIAOCHEN: AgentConfig(
                name="小宸",
                agent_type=AgentType.XIAOCHEN,
                port=8030,
                script_path="services/self-media-agent/app/main.py",
                startup_timeout=30,
                idle_timeout=240,  # 4分钟空闲后停止
                auto_stop=True,
                capabilities=["内容创作", "文章写作", "视频脚本", "社交媒体", "品牌推广"]
            )
        }

        return configs

    async def submit_task(self, task_request: TaskRequest) -> dict[str, Any]:
        """
        提交任务请求

        Args:
            task_request: 任务请求

        Returns:
            任务处理结果
        """
        # 生成任务ID
        if not task_request.task_id:
            task_request.task_id = f"task_{int(time.time())}_{len(self.active_tasks)}"

        # 添加到活动任务
        self.active_tasks[task_request.task_id] = task_request
        self.stats['total_tasks'] += 1

        logger.info(f"📝 收到任务: {task_request.task_type} ({task_request.task_id})")

        # 判断任务类型和所需智能体
        target_agent = await self._determine_target_agent(task_request)

        # 确保目标智能体运行
        if target_agent and target_agent != AgentType.XIAONUO:
            await self._ensure_agent_running(target_agent)
        else:
            # 小诺直接处理
            target_agent = AgentType.XIAONUO

        # 将任务加入队列
        await self.task_queue.put((task_request, target_agent))

        return {
            "task_id": task_request.task_id,
            "status": "queued",
            "target_agent": target_agent.value,
            "estimated_time": self._estimate_processing_time(task_request)
        }

    async def _determine_target_agent(self, task_request: TaskRequest) -> Optional[AgentType]:
        """确定目标智能体"""
        task_type = task_request.task_type.lower()
        content = task_request.content.lower()

        # 优先使用用户指定的智能体
        if task_request.preferred_agent:
            try:
                preferred = AgentType(task_request.preferred_agent)
                return preferred
            except ValueError:
                logger.warning(f"无效的智能体类型: {task_request.preferred_agent}, 将使用默认类型")

        # 根据任务类型判断
        if any(keyword in task_type or keyword in content for keyword in [
            "专利", "权利要求", "审查", "侵权", "法律", "撰写", "答复"
        ]):
            return AgentType.XIAONA


        elif any(keyword in task_type or keyword in content for keyword in [
            "自媒体", "文章", "写作", "视频", "脚本", "推广", "内容创作"
        ]):
            return AgentType.XIAOCHEN

        # 默认由小诺处理
        return AgentType.XIAONUO

    async def _start_xiaonuo(self):
        """启动小诺(常驻调度中心)"""
        config = self.agent_configs[AgentType.XIAONUO]

        logger.info("👑 启动小诺作为常驻调度中心...")

        try:
            instance = await self._start_agent_instance(config)
            self.xiaonuo_instance = instance
            self.running_agents[AgentType.XIAONUO] = instance

            logger.info(f"✅ 小诺已启动 (PID: {instance.pid}, 端口: {config.port})")

        except Exception as e:
            logger.error(f"❌ 启动小诺失败: {e}")
            raise

    async def _ensure_agent_running(self, agent_type: AgentType):
        """确保智能体运行"""
        if agent_type == AgentType.XIAONUO:
            return  # 小诺永远运行

        if agent_type in self.running_agents:
            instance = self.running_agents[agent_type]
            if instance.status == AgentStatus.RUNNING:
                instance.last_activity = datetime.now()
                return
            elif instance.status == AgentStatus.STOPPED:
                await self._start_agent(agent_type)
        else:
            await self._start_agent(agent_type)

    async def _start_agent(self, agent_type: AgentType):
        """启动智能体"""
        if agent_type == AgentType.XIAONUO:
            return  # 小诺已启动

        config = self.agent_configs[agent_type]

        logger.info(f"🚀 启动智能体: {config.name}...")

        try:
            instance = await self._start_agent_instance(config)
            self.running_agents[agent_type] = instance
            self.stats['agent_starts'] += 1

            logger.info(f"✅ {config.name}已启动 (PID: {instance.pid}, 端口: {config.port})")

        except Exception as e:
            logger.error(f"❌ 启动{config.name}失败: {e}")
            raise

    async def _start_agent_instance(self, config: AgentConfig) -> AgentInstance:
        """启动智能体实例"""
        script_path = self.project_root / config.script_path

        if not script_path.exists():
            raise FileNotFoundError(f"智能体脚本不存在: {script_path}")

        # 构建启动命令
        cmd = [sys.executable, str(script_path)]

        # 设置环境变量
        env = os.environ.copy()
        env['AGENT_PORT'] = str(config.port)
        env['AGENT_NAME'] = config.name
        env['AGENT_TYPE'] = config.agent_type.value

        # 启动进程
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(script_path.parent),
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # 创建实例
        instance = AgentInstance(
            config=config,
            status=AgentStatus.STARTING,
            process=process,
            pid=process.pid,
            start_time=datetime.now(),
            last_activity=datetime.now()
        )

        # 等待启动完成
        await self._wait_for_agent_ready(instance, config.startup_timeout)

        instance.status = AgentStatus.RUNNING
        return instance

    async def _wait_for_agent_ready(self, instance: AgentInstance, timeout: int):
        """等待智能体就绪"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            # 检查进程是否还在运行
            if instance.process and instance.process.returncode is not None:
                raise RuntimeError(f"智能体进程异常退出,返回码: {instance.process.returncode}")

            # 简单的端口检查
            if await self._check_port_ready(instance.config.port):
                return

            await asyncio.sleep(1)

        raise TimeoutError(f"智能体启动超时 ({timeout}秒)")

    async def _check_port_ready(self, port: int) -> bool:
        """检查端口是否就绪"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result == 0
        except (TimeoutError, OSError, ConnectionRefusedError) as e:
            logger.debug(f"端口检查失败 {port}: {e}")
            return False

    async def _task_scheduler(self):
        """任务调度器"""
        logger.info("📋 任务调度器已启动")

        while True:
            try:
                # 获取任务
                task_request, target_agent = await self.task_queue.get()

                # 更新活动时间
                if target_agent in self.running_agents:
                    self.running_agents[target_agent].last_activity = datetime.now()
                    self.running_agents[target_agent].task_count += 1

                # 处理任务
                await self._process_task(task_request, target_agent)

            except Exception as e:
                logger.error(f"任务调度错误: {e}")
                await asyncio.sleep(1)

    async def _process_task(self, task_request: TaskRequest, target_agent: AgentType):
        """处理任务"""
        logger.info(f"🔄 处理任务 {task_request.task_id} -> {target_agent.value}")

        try:
            # 这里应该调用相应智能体的API
            result = await self._call_agent_api(target_agent, task_request)

            # 保存结果
            self.active_tasks[task_request.task_id] = {
                **task_request.__dict__,
                "result": result,
                "completed_at": datetime.now().isoformat()
            }

            logger.info(f"✅ 任务 {task_request.task_id} 处理完成")

        except Exception as e:
            logger.error(f"❌ 任务 {task_request.task_id} 处理失败: {e}")
            self.active_tasks[task_request.task_id] = {
                **task_request.__dict__,
                "error": str(e),
                "completed_at": datetime.now().isoformat()
            }

    async def _call_agent_api(self, agent_type: AgentType, task_request: TaskRequest) -> dict[str, Any]:
        """调用智能体API"""
        # 模拟API调用
        instance = self.running_agents.get(agent_type)
        if not instance or instance.status != AgentStatus.RUNNING:
            raise RuntimeError(f"智能体 {agent_type.value} 未运行")

        # 模拟处理时间
        await asyncio.sleep(1)

        # 返回模拟结果
        return {
            "agent": agent_type.value,
            "response": f"来自{instance.config.name}的处理结果",
            "processing_time": 1.0,
            "quality_score": 0.95
        }

    async def _idle_monitor(self):
        """空闲监控器"""
        logger.info("👁️ 空闲监控器已启动")

        while True:
            try:
                current_time = datetime.now()

                for agent_type, instance in list(self.running_agents.items()):
                    # 跳过小诺(常驻)
                    if agent_type == AgentType.XIAONUO:
                        continue

                    # 检查是否超时
                    if (instance.status == AgentStatus.RUNNING and
                        instance.config.auto_stop and
                        instance.last_activity):

                        idle_time = (current_time - instance.last_activity).total_seconds()

                        if idle_time > instance.config.idle_timeout:
                            logger.info(f"🛑 {instance.config.name} 空闲超时,正在停止...")
                            await self._stop_agent(agent_type)

                await asyncio.sleep(60)  # 每分钟检查一次

            except Exception as e:
                logger.error(f"空闲监控错误: {e}")
                await asyncio.sleep(60)

    async def _stop_agent(self, agent_type: AgentType):
        """停止智能体"""
        if agent_type == AgentType.XIAONUO:
            return  # 不停止小诺

        if agent_type not in self.running_agents:
            return

        instance = self.running_agents[agent_type]
        config = instance.config

        logger.info(f"🛑 停止智能体: {config.name}...")

        try:
            instance.status = AgentStatus.STOPPING

            if instance.process:
                instance.process.terminate()
                await instance.process.wait()

            instance.status = AgentStatus.STOPPED
            self.stats['agent_stops'] += 1

            # 计算节省的资源
            running_time = (datetime.now() - instance.start_time).total_seconds()
            saved_memory = instance.memory_usage * running_time / 3600  # MB*小时
            self.stats['memory_saved'] += saved_memory

            logger.info(f"✅ {config.name}已停止,节省内存: {saved_memory:.1f} MB*小时")

        except Exception as e:
            logger.error(f"❌ 停止{config.name}失败: {e}")
            instance.status = AgentStatus.ERROR

    def _estimate_processing_time(self, task_request: TaskRequest) -> float:
        """估算处理时间"""
        # 基于任务类型的简单估算
        base_time = 1.0

        if task_request.task_type in ["专利分析", "法律咨询"]:
            base_time = 3.0
        elif task_request.task_type in ["IP管理", "案卷处理"]:
            base_time = 2.0
        elif task_request.task_type in ["内容创作", "文章写作"]:
            base_time = 5.0

        # 考虑优先级
        if task_request.priority > 1:
            base_time *= 0.8

        return base_time

    def get_system_status(self) -> dict[str, Any]:
        """获取系统状态"""
        current_time = datetime.now()

        # 计算资源使用情况
        total_memory = sum(
            psutil.Process(inst.pid).memory_info().rss / 1024 / 1024
            for inst in self.running_agents.values()
            if inst.pid and psutil.pid_exists(inst.pid)
        )

        # 计算运行智能体数量
        running_agents = sum(
            1 for inst in self.running_agents.values()
            if inst.status == AgentStatus.RUNNING
        )

        return {
            "orchestrator_status": "running",
            "running_agents": running_agents,
            "total_agents": len(self.agent_configs),
            "memory_usage_mb": round(total_memory, 2),
            "active_tasks": len(self.active_tasks),
            "queued_tasks": self.task_queue.qsize(),
            "stats": {
                **self.stats,
                "average_task_time": (
                    sum(task.get('processing_time', 0) for task in self.active_tasks.values()) /
                    max(1, len(self.active_tasks))
                )
            },
            "agent_details": {
                agent_type.value: {
                    "name": inst.config.name,
                    "status": inst.status.value,
                    "running_time": (
                        (current_time - inst.start_time).total_seconds()
                        if inst.start_time else 0
                    ),
                    "task_count": inst.task_count,
                    "last_activity": inst.last_activity.isoformat() if inst.last_activity else None
                }
                for agent_type, inst in self.running_agents.items()
            }
        }

    async def shutdown(self):
        """关闭编排器"""
        logger.info("🛑 正在关闭按需启动编排器...")

        # 停止所有智能体(除了小诺)
        for agent_type in list(self.running_agents.keys()):
            if agent_type != AgentType.XIAONUO:
                await self._stop_agent(agent_type)

        logger.info("✅ 按需启动编排器已关闭")


# 使用示例
async def test_on_demand_orchestrator():
    """测试按需启动编排器"""
    print("🎭 测试按需启动智能体编排器")
    print("=" * 50)

    orchestrator = OnDemandAgentOrchestrator()

    # 等待小诺启动
    await asyncio.sleep(3)

    # 提交不同类型的任务
    tasks = [
        TaskRequest(
            task_id="task_001",
            user_id="user_001",
            task_type="专利分析",
            content="请分析这个专利的权利要求撰写质量",
            priority=1
        ),
        TaskRequest(
            task_id="task_002",
            user_id="user_001",
            task_type="IP管理",
            content="查询案卷CASE_001的状态",
            priority=2
        ),
        TaskRequest(
            task_id="task_003",
            user_id="user_001",
            task_type="普通对话",
            content="你好,今天天气怎么样?",
            priority=1
        ),
        TaskRequest(
            task_id="task_004",
            user_id="user_001",
            task_type="内容创作",
            content="写一篇关于AI专利技术的推广文章",
            priority=1
        )
    ]

    # 提交任务
    for task in tasks:
        result = await orchestrator.submit_task(task)
        print(f"📝 任务已提交: {result['task_id']} -> {result['target_agent']}")

    # 等待处理
    await asyncio.sleep(5)

    # 查看状态
    status = orchestrator.get_system_status()
    print("\n📊 系统状态:")
    print(f"   运行智能体: {status['running_agents']}/{status['total_agents']}")
    print(f"   内存使用: {status['memory_usage_mb']:.1f} MB")
    print(f"   处理任务数: {status['stats']['total_tasks']}")
    print(f"   智能体启动次数: {status['stats']['agent_starts']}")

    # 详细智能体状态
    print("\n🤖 智能体详情:")
    for _agent_type, details in status['agent_details'].items():
        print(f"   {details['name']}: {details['status']} "
              f"(任务数: {details['task_count']}, "
              f"运行时间: {details['running_time']:.0f}秒)")

    # 关闭编排器
    await orchestrator.shutdown()
    print("\n✅ 测试完成")


if __name__ == "__main__":
    import os
    asyncio.run(test_on_demand_orchestrator())

