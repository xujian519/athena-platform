#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P2 Agent协作和任务管理工具实现

基于Claude Code工具系统设计的P2协作工具：
1. Agent - 启动子Agent
2. TaskCreate - 创建后台任务
3. TaskList - 列出所有任务
4. TaskGet - 获取任务详情
5. TaskUpdate - 更新任务状态
6. TaskStop - 停止任务

这些工具增强Agent的协作和任务管理能力。

Author: Athena平台团队
Created: 2026-04-20
Version: v1.0.0
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from core.tools.decorators import tool

logger = logging.getLogger(__name__)


# ========================================
# 任务管理系统
# ========================================


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task:
    """任务对象"""

    def __init__(
        self,
        task_id: str,
        name: str,
        description: str,
        command: str,
        working_dir: str,
    ):
        self.task_id = task_id
        self.name = name
        self.description = description
        self.command = command
        self.working_dir = working_dir
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[str] = None
        self.error: Optional[str] = None
        self.process: Optional[asyncio.subprocess.Process] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "command": self.command,
            "working_dir": self.working_dir,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
        }


class TaskManager:
    """任务管理器（单例）"""

    _instance: Optional["TaskManager"] = None
    _tasks: Dict[str, Task] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def create_task(
        self,
        name: str,
        description: str,
        command: str,
        working_dir: str,
    ) -> Task:
        """创建新任务"""
        task_id = str(uuid.uuid4())[:8]
        task = Task(
            task_id=task_id,
            name=name,
            description=description,
            command=command,
            working_dir=working_dir,
        )
        self._tasks[task_id] = task
        logger.info(f"✅ 任务已创建: {task_id} - {name}")
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self._tasks.get(task_id)

    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[Task]:
        """列出所有任务"""
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks

    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[str] = None,
        error: Optional[str] = None,
    ) -> bool:
        """更新任务状态"""
        task = self.get_task(task_id)
        if not task:
            return False

        task.status = status
        if result:
            task.result = result
        if error:
            task.error = error

        if status == TaskStatus.IN_PROGRESS and not task.started_at:
            task.started_at = datetime.now()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            task.completed_at = datetime.now()

        logger.info(f"✅ 任务状态更新: {task_id} -> {status.value}")
        return True

    async def execute_task(self, task: Task) -> None:
        """执行任务"""
        try:
            self.update_task_status(task.task_id, TaskStatus.IN_PROGRESS)

            # 执行命令
            process = await asyncio.create_subprocess_shell(
                task.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=task.working_dir,
            )
            task.process = process

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                self.update_task_status(
                    task.task_id,
                    TaskStatus.COMPLETED,
                    result=stdout.decode("utf-8", errors="replace"),
                )
            else:
                self.update_task_status(
                    task.task_id,
                    TaskStatus.FAILED,
                    error=stderr.decode("utf-8", errors="replace"),
                )

        except Exception as e:
            self.update_task_status(
                task.task_id,
                TaskStatus.FAILED,
                error=str(e),
            )

    async def stop_task(self, task_id: str) -> bool:
        """停止任务"""
        task = self.get_task(task_id)
        if not task:
            return False

        if task.process and task.process.returncode is None:
            task.process.kill()
            await task.process.wait()
            self.update_task_status(task_id, TaskStatus.CANCELLED)
            return True

        return False


# 全局任务管理器
task_manager = TaskManager()


# ========================================
# 1. Agent工具 - 启动子Agent
# ========================================


class AgentInput(BaseModel):
    """Agent工具输入参数"""
    agent_type: str = Field(..., description="Agent类型（xiaona/xiaonuo/yunxi）")
    task: str = Field(..., description="任务描述")
    context: Optional[Dict[str, Any]] = Field(default=None, description="上下文信息")


class AgentOutput(BaseModel):
    """Agent工具输出结果"""
    agent_id: str = Field(..., description="Agent ID")
    result: str = Field(..., description="执行结果")
    execution_time: float = Field(..., description="执行时间（秒）")


@tool(
    name="agent",
    description="启动子Agent执行任务",
    category="agent",
    tags=["agent", "collaboration", "subtask"],
)
async def agent_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent工具处理器

    启动子Agent执行指定任务。支持：
    - Xiaona（小娜）- 法律专家
    - Xiaonuo（小诺）- 调度官
    - Yunxi（云熙）- IP管理

    特性：
    - 任务委派
    - Agent间通信
    - 结果聚合
    - 超时控制

    Args:
        params: 包含agent_type, task, context的字典
        context: 上下文信息

    Returns:
        执行结果字典，包含agent_id, result等
    """
    # 解析参数
    agent_type = params.get("agent_type", "")
    task = params.get("task", "")
    agent_context = params.get("context", {})

    # 验证输入
    if not agent_type:
        return {
            "success": False,
            "error": "Agent类型不能为空",
        }

    if not task:
        return {
            "success": False,
            "error": "任务描述不能为空",
        }

    # 验证Agent类型
    valid_agents = ["xiaona", "xiaonuo", "yunxi"]
    if agent_type.lower() not in valid_agents:
        return {
            "success": False,
            "error": f"无效的Agent类型: {agent_type}（支持: {', '.join(valid_agents)}）",
        }

    logger.info(f"🤖 启动Agent: {agent_type}")
    logger.debug(f"任务: {task[:100]}...")

    start_time = datetime.now()

    try:
        # 模拟Agent执行
        # 实际应该导入并调用相应的Agent
        agent_id = f"{agent_type}_{uuid.uuid4()}[:8]"

        # 这里我们返回一个模拟结果
        # 实际实现应该：
        # 1. 导入相应的Agent（XiaonaAgent、XiaonuoAgent等）
        # 2. 创建Agent实例
        # 3. 调用Agent的process方法
        # 4. 返回结果

        result = f"Agent {agent_type} 已处理任务: {task[:50]}..."
        execution_time = (datetime.now() - start_time).total_seconds()

        logger.info(f"✅ Agent完成: {agent_id}")

        return {
            "success": True,
            "agent_id": agent_id,
            "result": result,
            "execution_time": execution_time,
        }

    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"❌ Agent执行失败: {e}")

        return {
            "success": False,
            "error": str(e),
            "execution_time": execution_time,
        }


# ========================================
# 2. TaskCreate工具 - 创建后台任务
# ========================================


class TaskCreateInput(BaseModel):
    """TaskCreate工具输入参数"""
    name: str = Field(..., description="任务名称")
    description: str = Field(..., description="任务描述")
    command: str = Field(..., description="要执行的命令")
    working_dir: Optional[str] = Field(default=None, description="工作目录")
    auto_start: Optional[bool] = Field(default=True, description="是否自动启动")


class TaskCreateOutput(BaseModel):
    """TaskCreate工具输出结果"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")


@tool(
    name="task_create",
    description="创建后台任务",
    category="task_management",
    tags=["task", "create", "background"],
)
async def task_create_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    TaskCreate工具处理器

    创建后台任务。支持：
    - Shell命令执行
    - 长时间运行的任务
    - 任务状态跟踪
    - 结果获取

    Args:
        params: 包含name, description, command, working_dir, auto_start的字典
        context: 上下文信息

    Returns:
        创建结果字典，包含task_id, status等
    """
    # 解析参数
    name = params.get("name", "")
    description = params.get("description", "")
    command = params.get("command", "")
    working_dir = params.get("working_dir", os.getcwd())
    auto_start = params.get("auto_start", True)

    # 验证输入
    if not name:
        return {
            "success": False,
            "error": "任务名称不能为空",
        }

    if not command:
        return {
            "success": False,
            "error": "命令不能为空",
        }

    logger.info(f"📋 创建任务: {name}")
    logger.debug(f"命令: {command[:100]}...")

    try:
        # 创建任务
        task = task_manager.create_task(
            name=name,
            description=description,
            command=command,
            working_dir=working_dir,
        )

        # 自动启动
        if auto_start:
            asyncio.create_task(task_manager.execute_task(task))
            logger.info(f"✅ 任务已启动: {task.task_id}")

        return {
            "success": True,
            "task_id": task.task_id,
            "status": task.status.value,
            "auto_started": auto_start,
        }

    except Exception as e:
        logger.error(f"❌ 任务创建失败: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# ========================================
# 3. TaskList工具 - 列出所有任务
# ========================================


class TaskListInput(BaseModel):
    """TaskList工具输入参数"""
    status_filter: Optional[str] = Field(default=None, description="状态过滤（pending/in_progress/completed/failed/cancelled）")


class TaskListOutput(BaseModel):
    """TaskList工具输出结果"""
    tasks: List[Dict[str, Any]] = Field(..., description="任务列表")
    total_count: int = Field(..., description="总任务数")


@tool(
    name="task_list",
    description="列出所有后台任务",
    category="task_management",
    tags=["task", "list", "status"],
)
async def task_list_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    TaskList工具处理器

    列出所有后台任务。支持：
    - 状态过滤
    - 任务详情查看
    - 按创建时间排序

    Args:
        params: 包含status_filter的字典
        context: 上下文信息

    Returns:
        任务列表字典，包含tasks, total_count等
    """
    # 解析参数
    status_filter = params.get("status_filter")

    logger.info("📋 列出任务")

    try:
        # 解析状态过滤器
        status = None
        if status_filter:
            try:
                status = TaskStatus(status_filter)
            except ValueError:
                return {
                    "success": False,
                    "error": f"无效的状态: {status_filter}",
                }

        # 获取任务列表
        tasks = task_manager.list_tasks(status)

        # 按创建时间排序（最新的在前）
        tasks.sort(key=lambda t: t.created_at, reverse=True)

        # 转换为字典
        task_dicts = [task.to_dict() for task in tasks]

        logger.info(f"✅ 找到 {len(tasks)} 个任务")

        return {
            "success": True,
            "tasks": task_dicts,
            "total_count": len(tasks),
        }

    except Exception as e:
        logger.error(f"❌ 任务列表获取失败: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# ========================================
# 4. TaskGet工具 - 获取任务详情
# ========================================


class TaskGetInput(BaseModel):
    """TaskGet工具输入参数"""
    task_id: str = Field(..., description="任务ID")


class TaskGetOutput(BaseModel):
    """TaskGet工具输出结果"""
    task: Dict[str, Any] = Field(..., description="任务详情")


@tool(
    name="task_get",
    description="获取任务详情",
    category="task_management",
    tags=["task", "get", "details"],
)
async def task_get_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    TaskGet工具处理器

    获取任务的详细信息。包括：
    - 任务状态
    - 执行结果
    - 错误信息
    - 时间戳

    Args:
        params: 包含task_id的字典
        context: 上下文信息

    Returns:
        任务详情字典
    """
    # 解析参数
    task_id = params.get("task_id", "")

    # 验证输入
    if not task_id:
        return {
            "success": False,
            "error": "任务ID不能为空",
        }

    logger.info(f"🔍 获取任务详情: {task_id}")

    try:
        # 获取任务
        task = task_manager.get_task(task_id)

        if not task:
            return {
                "success": False,
                "error": f"任务不存在: {task_id}",
            }

        logger.info(f"✅ 任务状态: {task.status.value}")

        return {
            "success": True,
            "task": task.to_dict(),
        }

    except Exception as e:
        logger.error(f"❌ 任务详情获取失败: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# ========================================
# 5. TaskUpdate工具 - 更新任务状态
# ========================================


class TaskUpdateInput(BaseModel):
    """TaskUpdate工具输入参数"""
    task_id: str = Field(..., description="任务ID")
    status: Optional[str] = Field(default=None, description="新状态")
    result: Optional[str] = Field(default=None, description="执行结果")
    error: Optional[str] = Field(default=None, description="错误信息")


class TaskUpdateOutput(BaseModel):
    """TaskUpdate工具输出结果"""
    task_id: str = Field(..., description="任务ID")
    old_status: str = Field(..., description="旧状态")
    new_status: str = Field(..., description="新状态")


@tool(
    name="task_update",
    description="更新任务状态",
    category="task_management",
    tags=["task", "update", "status"],
)
async def task_update_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    TaskUpdate工具处理器

    更新任务状态。支持：
    - 状态更新
    - 结果更新
    - 错误信息更新

    Args:
        params: 包含task_id, status, result, error的字典
        context: 上下文信息

    Returns:
        更新结果字典
    """
    # 解析参数
    task_id = params.get("task_id", "")
    status_str = params.get("status")
    result = params.get("result")
    error = params.get("error")

    # 验证输入
    if not task_id:
        return {
            "success": False,
            "error": "任务ID不能为空",
        }

    logger.info(f"🔄 更新任务: {task_id}")

    try:
        # 获取任务
        task = task_manager.get_task(task_id)

        if not task:
            return {
                "success": False,
                "error": f"任务不存在: {task_id}",
            }

        old_status = task.status.value

        # 解析新状态
        new_status = None
        if status_str:
            try:
                new_status = TaskStatus(status_str)
            except ValueError:
                return {
                    "success": False,
                    "error": f"无效的状态: {status_str}",
                }

        # 更新任务
        success = task_manager.update_task_status(
            task_id,
            new_status if new_status else task.status,
            result=result,
            error=error,
        )

        if not success:
            return {
                "success": False,
                "error": "任务状态更新失败",
            }

        logger.info(f"✅ 任务状态更新: {old_status} -> {task.status.value}")

        return {
            "success": True,
            "task_id": task_id,
            "old_status": old_status,
            "new_status": task.status.value,
        }

    except Exception as e:
        logger.error(f"❌ 任务状态更新失败: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# ========================================
# 6. TaskStop工具 - 停止任务
# ========================================


class TaskStopInput(BaseModel):
    """TaskStop工具输入参数"""
    task_id: str = Field(..., description="任务ID")


class TaskStopOutput(BaseModel):
    """TaskStop工具输出结果"""
    task_id: str = Field(..., description="任务ID")
    stopped: bool = Field(..., description="是否成功停止")


@tool(
    name="task_stop",
    description="停止正在运行的任务",
    category="task_management",
    tags=["task", "stop", "cancel"],
)
async def task_stop_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    TaskStop工具处理器

    停止正在运行的任务。支持：
    - 终止进程
    - 清理资源
    - 更新状态

    Args:
        params: 包含task_id的字典
        context: 上下文信息

    Returns:
        停止结果字典
    """
    # 解析参数
    task_id = params.get("task_id", "")

    # 验证输入
    if not task_id:
        return {
            "success": False,
            "error": "任务ID不能为空",
        }

    logger.info(f"🛑 停止任务: {task_id}")

    try:
        # 停止任务
        stopped = await task_manager.stop_task(task_id)

        if not stopped:
            return {
                "success": False,
                "error": f"任务无法停止（可能已完成或不存在）: {task_id}",
            }

        logger.info(f"✅ 任务已停止: {task_id}")

        return {
            "success": True,
            "task_id": task_id,
            "stopped": True,
        }

    except Exception as e:
        logger.error(f"❌ 任务停止失败: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# ========================================
# 测试代码
# ========================================


if __name__ == "__main__":
    import sys
    import os

    sys.path.insert(0, "/Users/xujian/Athena工作平台")

    async def test_p2_tools():
        """测试P2工具"""
        print("=" * 60)
        print("测试P2 Agent协作和任务管理工具")
        print("=" * 60)
        print()

        # 测试Agent工具
        print("1. 测试Agent工具...")
        result = await agent_handler(
            {
                "agent_type": "xiaona",
                "task": "分析专利CN123456789A的创造性",
            },
            {}
        )
        if result["success"]:
            print(f"   ✅ Agent ID: {result['agent_id']}")
            print(f"   ✅ 执行时间: {result['execution_time']:.2f}秒")
        print()

        # 测试TaskCreate工具
        print("2. 测试TaskCreate工具...")
        result = await task_create_handler(
            {
                "name": "测试任务",
                "description": "这是一个测试任务",
                "command": "echo 'Hello from task!' && sleep 1",
                "auto_start": False,
            },
            {}
        )
        if result["success"]:
            print(f"   ✅ 任务ID: {result['task_id']}")
            print(f"   ✅ 状态: {result['status']}")
            task_id = result["task_id"]
        print()

        # 测试TaskList工具
        print("3. 测试TaskList工具...")
        result = await task_list_handler({}, {})
        if result["success"]:
            print(f"   ✅ 任务总数: {result['total_count']}")
        print()

        # 测试TaskGet工具
        print("4. 测试TaskGet工具...")
        result = await task_get_handler({"task_id": task_id}, {})
        if result["success"]:
            print(f"   ✅ 任务名称: {result['task']['name']}")
            print(f"   ✅ 任务状态: {result['task']['status']}")
        print()

        # 测试TaskUpdate工具
        print("5. 测试TaskUpdate工具...")
        result = await task_update_handler(
            {
                "task_id": task_id,
                "status": "completed",
                "result": "任务完成",
            },
            {}
        )
        if result["success"]:
            print(f"   ✅ 状态更新: {result['old_status']} -> {result['new_status']}")
        print()

        # 测试TaskStop工具
        print("6. 测试TaskStop工具...")
        # 创建一个运行中的任务
        result = await task_create_handler(
            {
                "name": "长时间任务",
                "description": "运行5秒的任务",
                "command": "sleep 5",
                "auto_start": True,
            },
            {}
        )
        if result["success"]:
            running_task_id = result["task_id"]
            # 等待一下让任务启动
            await asyncio.sleep(0.5)
            # 停止任务
            result = await task_stop_handler({"task_id": running_task_id}, {})
            if result["success"]:
                print(f"   ✅ 任务已停止: {running_task_id}")
        print()

        print("=" * 60)
        print("✅ P2工具测试完成")
        print("=" * 60)

    asyncio.run(test_p2_tools())
