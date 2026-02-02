#!/usr/bin/env python3
"""
执行引擎 - 动作执行器
Execution Engine - Action Executor

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

import asyncio
import json
import logging
import multiprocessing
import shlex
import subprocess
import traceback
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any

from ..types import ActionType, Task, TaskStatus
from .task_types import TaskResult

logger = logging.getLogger(__name__)


class ActionExecutor:
    """动作执行器

    负责执行各种类型的任务动作。
    """

    def __init__(self):
        self.executors = {
            ActionType.COMMAND: self._execute_command,
            ActionType.FUNCTION: self._execute_function,
            ActionType.API_CALL: self._execute_api_call,
            ActionType.FILE_OPERATION: self._execute_file_operation,
            ActionType.DATABASE: self._execute_database,
            ActionType.HTTP_REQUEST: self._execute_http_request,
            ActionType.WORKFLOW: self._execute_workflow,
            ActionType.CUSTOM: self._execute_custom,
        }
        self.thread_pool = ThreadPoolExecutor(max_workers=multiprocessing.cpu_count())

    async def execute_action(self, task: Task) -> TaskResult:
        """执行动作"""
        # 将 action_type 字符串转换为 ActionType 枚举
        try:
            if isinstance(task.action_type, str):
                action_key = ActionType(task.action_type)
            else:
                action_key = task.action_type
        except (ValueError, KeyError):
            action_key = ActionType.CUSTOM

        executor = self.executors.get(action_key, self._execute_custom)

        result = TaskResult(task_id=task.id, status=TaskStatus.RUNNING, start_time=datetime.now())

        try:
            # 使用 action_key.value 来显示类型名称
            logger.info(f"🚀 执行任务: {task.name} ({action_key.value})")

            # 执行动作
            action_result = await executor(task)

            # 更新结果
            result.result = action_result
            result.status = TaskStatus.COMPLETED
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()

            logger.info(f"✅ 任务完成: {task.name} (耗时: {result.duration:.2f}秒)")

        except asyncio.TimeoutError:
            result.status = TaskStatus.TIMEOUT
            result.error = "任务执行超时"
            result.end_time = datetime.now()
            logger.error(f"⏰ 任务超时: {task.name}")

        except Exception as e:
            result.status = TaskStatus.FAILED
            result.error = str(e)
            result.end_time = datetime.now()
            logger.error(f"❌ 任务失败: {task.name} - {e!s}")

            # 添加错误追踪
            result.logs.append(f"错误详情: {traceback.format_exc()}")

        return result

    async def _execute_command(self, task: Task) -> Any:
        """执行命令"""
        command = task.action_data.get("command")
        if not command:
            raise ValueError("缺少命令")

        shell = task.action_data.get("shell", False)
        cwd = task.action_data.get("cwd")
        env = task.action_data.get("env")

        # 在线程池中执行(避免阻塞)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.thread_pool,
            lambda: subprocess.run(
                command if shell else shlex.split(command),
                shell=shell,
                capture_output=True,
                text=True,
                cwd=cwd,
                env=env,
            ),
        )

        if result.returncode != 0:
            raise RuntimeError(f"命令执行失败: {result.stderr}")

        return {"stdout": result.stdout, "stderr": result.stderr, "return_code": result.returncode}

    async def _execute_function(self, task: Task) -> Any:
        """执行函数"""
        function_name = task.action_data.get("function")
        if not function_name:
            raise ValueError("缺少函数名")

        # 获取函数
        func = self._get_function(function_name)
        if not func:
            raise ValueError(f"函数不存在: {function_name}")

        args = task.action_data.get("args", [])
        kwargs = task.action_data.get("kwargs", {})

        # 执行函数
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(self.thread_pool, lambda: func(*args, **kwargs))

    async def _execute_api_call(self, task: Task) -> Any:
        """执行API调用"""
        import aiohttp

        url = task.action_data.get("url")
        if not url or not isinstance(url, str):
            raise ValueError("url 参数缺失或无效")

        method = task.action_data.get("method", "GET").upper()
        headers = task.action_data.get("headers", {})
        data = task.action_data.get("data")
        params = task.action_data.get("params")
        timeout = aiohttp.ClientTimeout(total=task.timeout or 30)

        async with aiohttp.ClientSession(timeout=timeout) as session, session.request(
            method=method, url=url, headers=headers, json=data, params=params
        ) as response:
            response_data = await response.text()

            if response.status >= 400:
                raise RuntimeError(f"API调用失败: {response.status} - {response_data}")

            try:
                return json.loads(response_data)
            except json.JSONDecodeError:
                return response_data

    async def _execute_file_operation(self, task: Task) -> Any:
        """执行文件操作"""
        operation = task.action_data.get("operation")
        file_path = task.action_data.get("path")

        if not operation or not file_path:
            raise ValueError("缺少操作类型或文件路径")

        path = Path(file_path)

        if operation == "read":
            mode = task.action_data.get("mode", "r")
            encoding = task.action_data.get("encoding", "utf-8")

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.thread_pool,
                lambda: path.read_text(encoding=encoding) if "b" not in mode else path.read_bytes(),
            )

        elif operation == "write":
            content = task.action_data.get("content")
            if content is None:
                raise ValueError("content 参数缺失")

            mode = task.action_data.get("mode", "w")
            encoding = task.action_data.get("encoding", "utf-8")

            loop = asyncio.get_event_loop()

            def write_content():
                if "b" in mode:
                    if not isinstance(content, (bytes, bytearray)):
                        raise TypeError("content 必须是 bytes 类型用于二进制写入")
                    path.write_bytes(content)
                else:
                    if not isinstance(content, str):
                        raise TypeError("content 必须是 str 类型用于文本写入")
                    path.write_text(content, encoding=encoding)

            await loop.run_in_executor(self.thread_pool, write_content)
            return {"written": len(content) if isinstance(content, (str, bytes)) else 0}

        elif operation == "delete":
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self.thread_pool, path.unlink)
            return {"deleted": str(path)}

        elif operation == "exists":
            return {"exists": path.exists()}

        elif operation == "list":
            if path.is_dir():
                loop = asyncio.get_event_loop()
                files = await loop.run_in_executor(self.thread_pool, lambda: list(path.iterdir()))
                return {"files": [str(f) for f in files]}
            else:
                return {"files": []}

        else:
            raise ValueError(f"不支持的文件操作: {operation}")

    async def _execute_database(self, task: Task) -> Any:
        """执行数据库操作"""
        db_type = task.action_data.get("db_type", "sqlite")

        if db_type == "sqlite":
            return await self._execute_sqlite(task)
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")

    async def _execute_sqlite(self, task: Task) -> Any:
        """执行SQLite操作"""
        import sqlite3

        db_path = task.action_data.get("db_path")
        operation = task.action_data.get("operation")

        if not db_path or not operation:
            raise ValueError("缺少数据库路径或操作")

        def _sqlite_operation() -> Any:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row

            try:
                cursor = conn.cursor()

                if operation == "query":
                    sql = task.action_data.get("sql")
                    if sql is None:
                        raise ValueError("sql 参数缺失")
                    params = task.action_data.get("params", [])

                    cursor.execute(sql, params)
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]

                elif operation == "execute":
                    sql = task.action_data.get("sql")
                    if sql is None:
                        raise ValueError("sql 参数缺失")
                    params = task.action_data.get("params", [])

                    cursor.execute(sql, params)
                    conn.commit()
                    return {"affected_rows": cursor.rowcount}

                elif operation == "script":
                    script = task.action_data.get("script")
                    if script is None:
                        raise ValueError("script 参数缺失")

                    cursor.executescript(script)
                    conn.commit()
                    return {"executed": True}

                else:
                    raise ValueError(f"不支持的SQLite操作: {operation}")

            finally:
                conn.close()

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.thread_pool, _sqlite_operation)

    async def _execute_http_request(self, task: Task) -> Any:
        """执行HTTP请求"""
        # 与API调用类似,但更通用
        return await self._execute_api_call(task)

    async def _execute_workflow(self, task: Task) -> Any:
        """执行工作流"""
        workflow_id = task.action_data.get("workflow_id")
        if not workflow_id:
            raise ValueError("缺少工作流ID")

        # 这里需要与工作流管理器交互
        # 简化实现
        return {"workflow_id": workflow_id, "status": "executed"}

    async def _execute_custom(self, task: Task) -> Any:
        """执行自定义动作"""
        custom_handler = task.action_data.get("handler")
        if not custom_handler:
            raise ValueError("缺少自定义处理器")

        # 尝试获取处理器
        handler = self._get_function(custom_handler)
        if not handler:
            raise ValueError(f"自定义处理器不存在: {custom_handler}")

        return await handler(task)

    def _get_function(self, function_path: str) -> Callable | None:
        """获取函数"""
        try:
            # 简化实现,实际需要更复杂的函数查找机制
            if function_path in globals():
                return globals()[function_path]

            # 尝试动态导入
            parts = function_path.split(".")
            if len(parts) >= 2:
                module_path = ".".join(parts[:-1])
                function_name = parts[-1]

                module = __import__(module_path, fromlist=[function_name])
                return getattr(module, function_name)

            return None
        except ImportError:
            return None
        except AttributeError:
            return None
        except Exception:
            return None
