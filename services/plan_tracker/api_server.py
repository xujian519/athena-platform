#!/usr/bin/env python3
"""
Plan Tracker Web API
双层规划系统的 Web API 服务

提供 RESTful API 和 WebSocket 支持，用于显示和管理任务计划。

Author: Athena Team
Version: 1.0.0
Date: 2026-02-25
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# 导入双层规划系统
try:
    from core.cognition.dual_layer_planner_v2 import (
        ExecutionMode,
        MarkdownPlanManager,
        PlanStep,
        TaskExecutionEngine,
    )
    from core.cognition.task_templates import TemplateManager
    from core.communication.websocket.progress_pusher import (
        ConnectionManager,
        ProgressPusher,
        ProgressUpdate,
    )
    DUAL_LAYER_AVAILABLE = True
except ImportError:
    DUAL_LAYER_AVAILABLE = False

logger = logging.getLogger(__name__)


# ========== Pydantic 模型 ==========


class CreateTaskRequest(BaseModel):
    """创建任务请求"""
    task_id: str
    title: str
    description: str
    template_id: str | None = None
    steps: list[dict[str, Any]] = []
    execution_mode: str = "sequential"


class ExecuteStepRequest(BaseModel):
    """执行步骤请求"""
    task_id: str
    step_id: str


class SubscribeRequest(BaseModel):
    """订阅请求"""
    task_id: str


# ========== FastAPI 应用 ==========


app = FastAPI(
    title="Athena Plan Tracker",
    description="双层规划系统 Web API",
    version="1.0.0",
)

# 静态文件目录
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 全局组件
if DUAL_LAYER_AVAILABLE:
    plan_manager = MarkdownPlanManager(storage_path=Path("plans"))
    execution_engine = TaskExecutionEngine(plan_manager)
    template_manager = TemplateManager()
    progress_pusher = ProgressPusher()
    connection_manager = progress_pusher.connection_manager

    # 注册智能体（如果有的话）
    try:
        from core.agents.patent_search_agent import PatentSearchAgent
        patent_agent = PatentSearchAgent()
        asyncio.create_task(patent_agent.initialize())
        execution_engine.register_agent("xiaona", patent_agent)
        logger.info("✅ 专利检索智能体已注册")
    except Exception as e:
        logger.warning(f"⚠️ 专利检索智能体注册失败: {e}")
else:
    plan_manager = None
    execution_engine = None
    template_manager = None
    progress_pusher = None
    connection_manager = None


# ========== HTML 页面 ==========


HTML_CONTENT = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Athena Plan Tracker - 任务进度追踪</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            background: white;
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }

        .header h1 {
            color: #333;
            font-size: 28px;
            margin-bottom: 8px;
        }

        .header p {
            color: #666;
            font-size: 14px;
        }

        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #ccc;
            margin-right: 8px;
        }

        .status-indicator.connected {
            background: #4CAF50;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .task-card {
            background: white;
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }

        .task-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }

        .task-title {
            font-size: 20px;
            font-weight: 600;
            color: #333;
        }

        .task-meta {
            font-size: 12px;
            color: #999;
        }

        .progress-container {
            margin-bottom: 24px;
        }

        .progress-bar {
            height: 8px;
            background: #f0f0f0;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 8px;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 4px;
            transition: width 0.5s ease;
        }

        .progress-text {
            font-size: 14px;
            color: #666;
        }

        .steps-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .step-item {
            display: flex;
            align-items: center;
            padding: 12px 16px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 3px solid #ddd;
            transition: all 0.3s ease;
        }

        .step-item.pending {
            border-left-color: #ccc;
        }

        .step-item.in_progress {
            border-left-color: #FFA726;
            background: #FFF3E0;
        }

        .step-item.completed {
            border-left-color: #66BB6A;
            background: #E8F5E9;
        }

        .step-item.failed {
            border-left-color: #EF5350;
            background: #FFEBEE;
        }

        .step-icon {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 12px;
            background: white;
            font-size: 16px;
        }

        .step-content {
            flex: 1;
        }

        .step-name {
            font-weight: 500;
            color: #333;
            margin-bottom: 4px;
        }

        .step-meta {
            font-size: 12px;
            color: #999;
        }

        .controls {
            display: flex;
            gap: 12px;
            margin-top: 20px;
        }

        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }

        .btn-secondary {
            background: #e0e0e0;
            color: #333;
        }

        .btn-secondary:hover {
            background: #d0d0d0;
        }

        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }

        .empty-state svg {
            width: 80px;
            height: 80px;
            margin-bottom: 16px;
            opacity: 0.5;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Athena Plan Tracker</h1>
            <p>双层规划系统 - 任务进度实时追踪</p>
            <div style="margin-top: 16px;">
                <span class="status-indicator" id="statusIndicator"></span>
                <span id="statusText">未连接</span>
            </div>
        </div>

        <div id="taskContainer">
            <div class="empty-state">
                <p>加载中...</p>
            </div>
        </div>
    </div>

    <script>
        const ws = new WebSocket('ws://localhost:8005/ws/progress');
        const statusIndicator = document.getElementById('statusIndicator');
        const statusText = document.getElementById('statusText');
        const taskContainer = document.getElementById('taskContainer');

        let currentTaskId = null;
        let taskData = null;

        ws.onopen = () => {
            statusIndicator.classList.add('connected');
            statusText.textContent = '已连接';

            // 加载任务列表
            loadTasks();
        };

        ws.onclose = () => {
            statusIndicator.classList.remove('connected');
            statusText.textContent = '连接断开';
        };

        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);

            switch (message.msg_type) {
                case 'task_list':
                    renderTaskList(message.data.tasks);
                    break;
                case 'task_detail':
                    taskData = message.data;
                    renderTaskDetail(taskData);
                    break;
                case 'progress_update':
                    handleProgressUpdate(message.data);
                    break;
                case 'subscription_confirmed':
                    console.log('已订阅:', message.data.task_id);
                    break;
            }
        };

        async function loadTasks() {
            const response = await fetch('/api/tasks');
            const data = await response.json();

            if (data.tasks && data.tasks.length > 0) {
                renderTaskList(data.tasks);
            } else {
                taskContainer.innerHTML = `
                    <div class="empty-state">
                        <p>暂无任务</p>
                        <p style="margin-top: 8px;">请先创建一个任务计划</p>
                    </div>
                `;
            }
        }

        function renderTaskList(tasks) {
            if (tasks.length === 0) {
                taskContainer.innerHTML = `
                    <div class="empty-state">
                        <p>暂无任务</p>
                    </div>
                `;
                return;
            }

            taskContainer.innerHTML = tasks.map(task => `
                <div class="task-card">
                    <div class="task-header">
                        <div>
                            <div class="task-title">${task.title}</div>
                            <div class="task-meta">ID: ${task.task_id}</div>
                        </div>
                        <button class="btn btn-primary" onclick="loadTask('${task.task_id}')">查看详情</button>
                    </div>
                    <div class="progress-container">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${task.progress.progress_percent}%"></div>
                        </div>
                        <div class="progress-text">${task.progress.progress_percent}% 完成 (${task.progress.completed}/${task.progress.total})</div>
                    </div>
                </div>
            `).join('');
        }

        function renderTaskDetail(task) {
            currentTaskId = task.task_id;

            taskContainer.innerHTML = `
                <div class="task-card">
                    <div class="task-header">
                        <div>
                            <div class="task-title">${task.title}</div>
                            <div class="task-meta">ID: ${task.task_id} | 状态: ${task.status}</div>
                        </div>
                        <div class="controls">
                            <button class="btn btn-secondary" onclick="loadTasks()">返回列表</button>
                            <button class="btn btn-primary" onclick="executeAll()">执行全部</button>
                        </div>
                    </div>

                    <div class="progress-container">
                        <div class="progress-bar">
                            <div class="progress-fill" id="mainProgress" style="width: ${task.progress.progress_percent}%"></div>
                        </div>
                        <div class="progress-text" id="progressText">${task.progress.progress_percent}% 完成</div>
                    </div>

                    <div class="steps-list">
                        ${task.steps.map((step, index) => `
                            <div class="step-item ${step.status}" id="step-${step.id}">
                                <div class="step-icon">${getStepIcon(step.status)}</div>
                                <div class="step-content">
                                    <div class="step-name">${step.name}</div>
                                    <div class="step-meta">${step.description || ''}</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;

            // 订阅任务更新
            ws.send(JSON.stringify({
                msg_type: 'subscribe',
                data: { task_id: task.task_id }
            }));
        }

        function getStepIcon(status) {
            const icons = {
                'pending': '⏸️',
                'in_progress': '🔄',
                'completed': '✅',
                'failed': '❌',
                'timeout': '⏱️',
            };
            return icons[status] || '⏸️';
        }

        function handleProgressUpdate(update) {
            if (!taskData) return;

            // 更新步骤状态
            const stepElement = document.getElementById(`step-${update.step_id}`);
            if (stepElement) {
                stepElement.className = `step-item ${update.status}`;
                const iconElement = stepElement.querySelector('.step-icon');
                if (iconElement) {
                    iconElement.textContent = getStepIcon(update.status);
                }
            }

            // 更新总进度
            const mainProgress = document.getElementById('mainProgress');
            const progressText = document.getElementById('progressText');
            if (mainProgress) {
                mainProgress.style.width = `${update.progress_percent}%`;
            }
            if (progressText) {
                progressText.textContent = `${update.progress_percent}% 完成`;
            }
        }

        async function loadTask(taskId) {
            ws.send(JSON.stringify({
                msg_type: 'get_task',
                data: { task_id: taskId }
            }));
        }

        async function executeAll() {
            if (!currentTaskId) return;

            const response = await fetch('/api/execute-all', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ task_id: currentTaskId })
            });

            const data = await response.json();

            if (data.success) {
                console.log('执行成功');
            }
        }

        // 初始加载
        loadTasks();
    </script>
</body>
</html>
"""


# ========== API 端点 ==========


@app.get("/", response_class=HTMLResponse)
async def root():
    """首页"""
    return HTMLResponse(content=HTML_CONTENT)


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "dual_layer_available": DUAL_LAYER_AVAILABLE,
        "connections": connection_manager.get_connection_count() if connection_manager else 0,
    }


@app.get("/api/tasks")
async def list_tasks():
    """列出所有任务"""
    if not DUAL_LAYER_AVAILABLE:
        raise HTTPException(status_code=503, detail="双层规划系统不可用")

    plans_dir = Path("plans")
    if not plans_dir.exists():
        return {"tasks": []}

    tasks = []
    for plan_file in plans_dir.glob("*.md"):
        if "_history" in plan_file.name:
            continue

        task_id = plan_file.stem
        plan = await plan_manager.load_plan(task_id)

        if plan:
            tasks.append({
                "task_id": plan.task_id,
                "title": plan.title,
                "status": plan.status.value,
                "progress": plan.get_progress(),
                "created_at": plan.created_at,
                "updated_at": plan.updated_at,
            })

    return {"tasks": tasks}


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    """获取任务详情"""
    if not DUAL_LAYER_AVAILABLE:
        raise HTTPException(status_code=503, detail="双层规划系统不可用")

    plan = await plan_manager.load_plan(task_id)

    if not plan:
        raise HTTPException(status_code=404, detail="任务不存在")

    return {
        "task_id": plan.task_id,
        "title": plan.title,
        "description": plan.description,
        "status": plan.status.value,
        "execution_mode": plan.execution_mode.value,
        "progress": plan.get_progress(),
        "steps": [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "status": s.status.value,
                "agent": s.agent,
                "dependencies": s.dependencies,
                "result": s.result,
                "error": s.error,
            }
            for s in plan.steps
        ],
    }


@app.post("/api/tasks")
async def create_task(request: CreateTaskRequest):
    """创建新任务"""
    if not DUAL_LAYER_AVAILABLE:
        raise HTTPException(status_code=503, detail="双层规划系统不可用")

    # 如果指定了模板，使用模板创建
    if request.template_id:
        task_data = template_manager.create_task_from_template(
            request.template_id,
            request.task_id,
            request.title,
            request.description,
            {},
        )
        steps_data = task_data.pop("steps", [])
        execution_mode = task_data.pop("execution_mode", "sequential")
    else:
        steps_data = request.steps
        execution_mode = request.execution_mode

    # 转换步骤
    from core.cognition.dual_layer_planner_v2 import PlanStep

    steps = []
    for i, step_data in enumerate(steps_data):
        step = PlanStep(
            id=step_data.get("id", f"step_{i+1}"),
            name=step_data.get("name", f"步骤 {i+1}"),
            description=step_data.get("description", ""),
            agent=step_data.get("agent", "xiaonuo"),
            action=step_data.get("action", "process"),
            parameters=step_data.get("parameters", {}),
            dependencies=step_data.get("dependencies", []),
            estimated_time=step_data.get("estimated_time", 60),
            timeout=step_data.get("timeout", 300),
            can_parallel=step_data.get("can_parallel", False),
        )
        steps.append(step)

    # 创建任务
    try:
        from core.cognition.dual_layer_planner_v2 import ExecutionMode
        plan_file = await execution_engine.start_task(
            request.task_id,
            request.title,
            request.description,
            steps,
            ExecutionMode(execution_mode),
        )

        return {
            "success": True,
            "task_id": request.task_id,
            "plan_file": plan_file,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/execute-step")
async def execute_step(request: ExecuteStepRequest):
    """执行单个步骤"""
    if not DUAL_LAYER_AVAILABLE:
        raise HTTPException(status_code=503, detail="双层规划系统不可用")

    result = await execution_engine.execute_step(request.task_id, request.step_id)
    return result


@app.post("/api/execute-all")
async def execute_all(request: ExecuteStepRequest):
    """执行所有步骤"""
    if not DUAL_LAYER_AVAILABLE:
        raise HTTPException(status_code=503, detail="双层规划系统不可用")

    result = await execution_engine.execute_all_pending(request.task_id)
    return result


@app.get("/api/templates")
async def list_templates():
    """列出所有模板"""
    if not DUAL_LAYER_AVAILABLE:
        raise HTTPException(status_code=503, detail="双层规划系统不可用")

    templates = template_manager.list_templates()

    return {
        "templates": [
            {
                "template_id": t.template_id,
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "tags": t.tags,
            }
            for t in templates
        ]
    }


@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 端点"""
    if not DUAL_LAYER_AVAILABLE:
        await websocket.close()

    connection_id = await connection_manager.connect(websocket)

    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message = json.loads(data)

            msg_type = message.get("msg_type")

            if msg_type == "subscribe":
                task_id = message.get("data", {}).get("task_id")
                if task_id:
                    await connection_manager.subscribe(connection_id, task_id)

                    # 发送任务详情
                    plan = await plan_manager.load_plan(task_id)
                    if plan:
                        await websocket.send_text(json.dumps({
                            "msg_type": "task_detail",
                            "data": {
                                "task_id": plan.task_id,
                                "title": plan.title,
                                "status": plan.status.value,
                                "progress": plan.get_progress(),
                                "steps": [
                                    {
                                        "id": s.id,
                                        "name": s.name,
                                        "description": s.description,
                                        "status": s.status.value,
                                    }
                                    for s in plan.steps
                                ],
                            },
                        }))

            elif msg_type == "unsubscribe":
                task_id = message.get("data", {}).get("task_id")
                if task_id:
                    await connection_manager.unsubscribe(connection_id, task_id)

            elif msg_type == "ping":
                await websocket.send_text(json.dumps({
                    "msg_type": "pong",
                    "data": {"timestamp": datetime.now().isoformat()},
                }))

    except WebSocketDisconnect:
        await connection_manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
        await connection_manager.disconnect(connection_id)


# ========== 启动命令 ==========


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8005,
        log_level="info",
    )
