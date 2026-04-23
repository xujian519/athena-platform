"""
自主控制API服务
提供Athena和小诺自主控制平台的RESTful API接口
"""

import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import uvicorn

# 导入安全认证
from auth import Permissions, User, auth_manager, get_current_user, require_permission
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field

# 导入自主控制系统
from core.autonomous_control import (
    AutonomousController,
    ControlMode,
    TaskPriority,
)
from core.logging_config import setup_logging

# 导入统一认证模块

# Token验证函数（使用get_current_user）
async def verify_token(token: str = Depends(HTTPBearer())) -> str:
    """验证token并返回用户ID"""
    user = await get_current_user(token)
    return user.id if user else "anonymous"

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

# 安全认证
security = HTTPBearer()

# API请求/响应模型
class ControlModeRequest(BaseModel):
    """控制模式请求"""
    mode: ControlMode
    reason: str | None = None

class TaskRequest(BaseModel):
    """自主任务请求"""
    title: str = Field(..., description='任务标题')
    description: str = Field(..., description='任务描述')
    priority: TaskPriority = TaskPriority.MEDIUM
    goal_type: str = Field(..., description='目标类型')
    target_metrics: dict[str, Any] = Field(default_factory=dict, description='目标指标')
    deadline: datetime | None = None

class ServiceControlRequest(BaseModel):
    """服务控制请求"""
    service_name: str = Field(..., description='服务名称')
    action: str = Field(..., description='操作: start/stop/restart')
    reason: str | None = None

class AgentMessageRequest(BaseModel):
    """Agent消息请求"""
    sender: str = Field(..., description='发送者: athena/xiaonuo')
    receiver: str = Field(..., description='接收者: athena/xiaonuo')
    content: str = Field(..., description='消息内容')
    message_type: str = Field(..., description='消息类型')
    emotions: dict[str, float] = Field(default_factory=dict, description='情感值')

class DecisionRequest(BaseModel):
    """决策请求"""
    context: dict[str, Any] = Field(..., description='决策上下文')
    decision_type: str = Field(..., description='决策类型')
    options: list[dict[str, Any] = Field(..., description='决策选项')

# 全局控制器实例
autonomous_controller = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global autonomous_controller

    # 启动时初始化
    logger.info('正在启动自主控制API服务...')
    autonomous_controller = AutonomousController()
    await autonomous_controller.initialize()

    # 启动自主控制
    await autonomous_controller.start_autonomous_control()
    logger.info('自主控制系统已启动')

    yield

    # 关闭时清理
    logger.info('正在关闭自主控制API服务...')
    if autonomous_controller:
        await autonomous_controller.shutdown()
    logger.info('自主控制API服务已关闭')

# 创建FastAPI应用
app = FastAPI(
    title='Athena自主控制API',
    description='Athena和小诺自主控制平台的API接口',
    version='1.0.0',
    lifespan=lifespan
)

# 添加CORS中间件

# ==================== 认证相关接口 ====================
@app.post('/api/v1/auth/login', summary='用户登录')
async def login(username: str, password: str):
    """用户登录获取访问令牌"""
    try:
        user = auth_manager.authenticate_user(username, password)
        if not user:
            raise HTTPException(status_code=401, detail='用户名或密码错误')

        access_token = auth_manager.create_access_token(username)
        return {
            'success': True,
            'data': {
                'access_token': access_token,
                'token_type': 'bearer',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'role': user.role,
                    'permissions': user.permissions
                }
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get('/api/v1/auth/me', summary='获取当前用户信息')
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前认证用户的信息"""
    return {
        'success': True,
        'data': {
            'id': current_user.id,
            'username': current_user.username,
            'role': current_user.role,
            'permissions': current_user.permissions
        }
    }

# ==================== 控制模式管理 ====================
@app.get('/api/v1/control/mode', summary='获取当前控制模式')
async def get_control_mode(current_user: User = Depends(require_permission(Permissions.READ_SYSTEM))):
    """获取当前控制模式"""
    try:
        status = await autonomous_controller.get_system_status()
        return {
            'success': True,
            'data': {
                'mode': status['control_mode'],
                'athena_active': status['athena_active'],
                'xiaonuo_active': status['xiaonuo_active'],
                'autonomous_level': status.get('autonomous_level', 'unknown')
            }
        }
    except Exception as e:
        logger.error(f"获取控制模式失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post('/api/v1/control/mode', summary='设置控制模式')
async def set_control_mode(
    request: ControlModeRequest,
    current_user: User = Depends(require_permission(Permissions.WRITE_SYSTEM))
):
    """设置控制模式"""
    try:
        result = await autonomous_controller.set_control_mode(request.mode)
        if result['success']:
            return {
                'success': True,
                'message': f"控制模式已设置为 {request.mode.value}",
                'data': {'previous_mode': result.get('previous_mode')}
            }
        else:
            raise HTTPException(status_code=400, detail=result.get('error'))
    except Exception as e:
        logger.error(f"设置控制模式失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

# ==================== 自主任务管理 ====================
@app.post('/api/v1/tasks', summary='创建自主任务')
async def create_autonomous_task(request: TaskRequest, background_tasks: BackgroundTasks, token: str = Depends(verify_token)):
    """创建新的自主任务"""
    try:
        task_id = await autonomous_controller.create_autonomous_task(
            title=request.title,
            description=request.description,
            priority=request.priority,
            goal_type=request.goal_type,
            target_metrics=request.target_metrics,
            deadline=request.deadline
        )

        # 在后台执行任务
        background_tasks.add_task(autonomous_controller.execute_autonomous_task, task_id)

        return {
            'success': True,
            'message': '自主任务创建成功',
            'data': {
                'task_id': task_id,
                'title': request.title,
                'priority': request.priority.value,
                'status': 'created'
            }
        }
    except Exception as e:
        logger.error(f"创建自主任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get('/api/v1/tasks', summary='获取自主任务列表')
async def get_autonomous_tasks(token: str = Depends(verify_token)):
    """获取所有自主任务"""
    try:
        tasks = await autonomous_controller.get_autonomous_tasks()
        return {
            'success': True,
            'data': {
                'tasks': tasks,
                'total': len(tasks),
                'active_count': len([t for t in tasks if t['status'] in ['pending', 'in_progress'])
            }
        }
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get('/api/v1/tasks/{task_id}', summary='获取任务详情')
async def get_task_detail(task_id: str, token: str = Depends(verify_token)):
    """获取指定任务的详细信息"""
    try:
        tasks = await autonomous_controller.get_autonomous_tasks()
        task = next((t for t in tasks if t['id'] == task_id), None)

        if not task:
            raise HTTPException(status_code=404, detail='任务不存在')

        return {
            'success': True,
            'data': task
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.delete('/api/v1/tasks/{task_id}', summary='取消任务')
async def cancel_task(task_id: str, token: str = Depends(verify_token)):
    """取消指定的自主任务"""
    try:
        # 这里需要在AutonomousController中实现cancel_task方法
        return {
            'success': True,
            'message': f"任务 {task_id} 已取消"
        }
    except Exception as e:
        logger.error(f"取消任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

# ==================== 平台服务控制 ====================
@app.get('/api/v1/platform/services', summary='获取平台服务状态')
async def get_platform_services(token: str = Depends(verify_token)):
    """获取所有平台服务的状态"""
    try:
        platform_status = await autonomous_controller.platform_manager.get_platform_status()
        return {
            'success': True,
            'data': platform_status
        }
    except Exception as e:
        logger.error(f"获取平台服务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post('/api/v1/platform/services/control', summary='控制平台服务')
async def control_service(request: ServiceControlRequest, background_tasks: BackgroundTasks, token: str = Depends(verify_token)):
    """控制指定的平台服务"""
    try:
        if request.action == 'start':
            result = await autonomous_controller.platform_manager.start_service(request.service_name)
        elif request.action == 'stop':
            result = await autonomous_controller.platform_manager.stop_service(request.service_name)
        elif request.action == 'restart':
            result = await autonomous_controller.platform_manager.restart_service(request.service_name)
        else:
            raise HTTPException(status_code=400, detail='无效的操作')

        if result['success']:
            return {
                'success': True,
                'message': result.get('message', f"服务 {request.service_name} {request.action} 成功"),
                'data': {
                    'service': request.service_name,
                    'action': request.action,
                    'reason': request.reason
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result.get('error'))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"控制服务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post('/api/v1/platform/restart', summary='重启整个平台')
async def restart_platform(background_tasks: BackgroundTasks, token: str = Depends(verify_token)):
    """重启整个平台"""
    try:
        # 在后台执行平台重启
        background_tasks.add_task(autonomous_controller.platform_manager.restart_platform)

        return {
            'success': True,
            'message': '平台重启已启动，请等待完成',
            'data': {
                'action': 'platform_restart',
                'initiated_at': datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"重启平台失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

# ==================== Agent协调管理 ====================
@app.get('/api/v1/agents/status', summary='获取Agent状态')
async def get_agents_status(token: str = Depends(verify_token)):
    """获取Athena和小诺的状态"""
    try:
        athena_status = await autonomous_controller.agent_coordinator.get_agent_status('athena')
        xiaonuo_status = await autonomous_controller.agent_coordinator.get_agent_status('xiaonuo')

        # 获取关系健康度
        relationship_health = await autonomous_controller.agent_coordinator.analyze_relationship_health()

        return {
            'success': True,
            'data': {
                'athena': athena_status,
                'xiaonuo': xiaonuo_status,
                'relationship_health': relationship_health,
                'collaboration_stats': autonomous_controller.agent_coordinator.get_collaboration_stats()
            }
        }
    except Exception as e:
        logger.error(f"获取Agent状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post('/api/v1/agents/message', summary='发送Agent消息')
async def send_agent_message(request: AgentMessageRequest, token: str = Depends(verify_token)):
    """在Athena和小诺之间发送消息"""
    try:
        from core.autonomous_control.agent_coordinator import (
            AgentMessage,
            AgentRole,
            InteractionType,
        )

        message = AgentMessage(
            id=str(uuid.uuid4()),
            sender=AgentRole(request.sender),
            receiver=AgentRole(request.receiver),
            content=request.content,
            message_type=InteractionType(request.message_type),
            emotions=request.emotions
        )

        response = await autonomous_controller.agent_coordinator.send_message(message)

        return {
            'success': True,
            'message': '消息发送成功',
            'data': {
                'message_id': message.id,
                'sender': message.sender.value,
                'receiver': message.receiver.value,
                'response': response.content if response else None
            }
        }
    except Exception as e:
        logger.error(f"发送Agent消息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get('/api/v1/agents/messages', summary='获取消息历史')
async def get_message_history(limit: int = 50, token: str = Depends(verify_token)):
    """获取Agent消息历史"""
    try:

        # 获取所有消息
        messages = await autonomous_controller.agent_coordinator.get_message_history(limit=limit)

        return {
            'success': True,
            'data': {
                'messages': messages,
                'total': len(messages)
            }
        }
    except Exception as e:
        logger.error(f"获取消息历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

# ==================== 决策引擎接口 ====================
@app.post('/api/v1/decisions/make', summary='执行自主决策')
async def make_decision(request: DecisionRequest, token: str = Depends(verify_token)):
    """使用决策引擎执行自主决策"""
    try:
        from core.autonomous_control.decision_engine import DecisionType

        decision_type = DecisionType(request.decision_type)

        decision_result = await autonomous_controller.decision_engine.make_decision(
            context=request.context,
            decision_type=decision_type,
            options=request.options
        )

        return {
            'success': True,
            'message': '决策执行成功',
            'data': {
                'decision': decision_result['decision'],
                'confidence': decision_result['confidence'],
                'reasoning': decision_result['reasoning'],
                'execution_plan': decision_result.get('execution_plan'),
                'estimated_outcome': decision_result.get('estimated_outcome')
            }
        }
    except Exception as e:
        logger.error(f"执行决策失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get('/api/v1/decisions/history', summary='获取决策历史')
async def get_decision_history(limit: int = 50, token: str = Depends(verify_token)):
    """获取决策历史记录"""
    try:
        # 这里需要在DecisionEngine中实现获取历史的方法
        return {
            'success': True,
            'data': {
                'decisions': [],  # 实际实现时从decision_engine获取
                'total': 0
            }
        }
    except Exception as e:
        logger.error(f"获取决策历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

# ==================== 系统监控 ====================
@app.get('/api/v1/system/status', summary='获取系统整体状态')
async def get_system_status(token: str = Depends(verify_token)):
    """获取自主控制系统的整体状态"""
    try:
        system_status = await autonomous_controller.get_system_status()

        return {
            'success': True,
            'data': system_status
        }
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get('/api/v1/system/health', summary='健康检查')
async def health_check():
    """API服务健康检查"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'autonomous_control_api',
        'version': '1.0.0'
    }

# ==================== 目标追踪 ====================
@app.get('/api/v1/goals', summary='获取系统目标')
async def get_system_goals(token: str = Depends(verify_token)):
    """获取系统当前的所有目标"""
    try:
        goals = await autonomous_controller.get_system_goals()

        return {
            'success': True,
            'data': {
                'goals': goals,
                'total': len(goals),
                'active_goals': len([g for g in goals if g['status'] == 'in_progress'])
            }
        }
    except Exception as e:
        logger.error(f"获取系统目标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get('/api/v1/goals/{goal_id}/progress', summary='获取目标进度')
async def get_goal_progress(goal_id: str, token: str = Depends(verify_token)):
    """获取指定目标的进度"""
    try:
        # 这里需要在GoalTracker中实现获取单个目标进度的方法
        return {
            'success': True,
            'data': {
                'goal_id': goal_id,
                'progress': 0,  # 实际实现时从goal_tracker获取
                'status': 'unknown'
            }
        }
    except Exception as e:
        logger.error(f"获取目标进度失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

if __name__ == '__main__':
    uvicorn.run(
        'autonomous_control_api:app',
        host='0.0.0.0',
        port=8090,
        reload=True,
        log_level='info'
    )
