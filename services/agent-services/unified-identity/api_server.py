"""
统一身份服务API
提供身份管理和协作配置的RESTful接口
"""

import logging
from core.async_main import async_main

from fastapi import Depends, FastAPI, HTTPException

logger = logging.getLogger(__name__)

from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from unified_identity_manager import (
    AIIdentity,
    RoleType,
    TaskType,
    UnifiedIdentityManager,
    identity_manager,
)

# 导入统一认证模块
from shared.auth.auth_middleware import create_auth_middleware, setup_cors

# FastAPI应用
app = FastAPI(
    title='统一身份服务',
    description='Athena工作平台统一身份管理API',
    version='1.0.0'
)

# 配置CORS

# 请求/响应模型
class IdentityResponse(BaseModel):
    """身份响应模型"""
    name: str
    english_name: str
    role_type: str
    role_description: str
    expertise: List[str]
    capabilities: Dict[str, Any]
    personality: Dict[str, Any]
    collaboration_style: str

class CollaborationRequest(BaseModel):
    """协作请求模型"""
    task_type: str
    task_description: str
    complexity: float = 0.5
    preferred_mode: str | None = None

class CollaborationResponse(BaseModel):
    """协作响应模型"""
    participants: List[str]
    mode: str
    primary_role: str
    secondary_role: Optional[str]
    collaborative_identity: IdentityResponse
    estimated_efficiency: float

# 身份转换函数
def identity_to_response(identity: AIIdentity) -> IdentityResponse:
    """转换身份为响应模型"""
    return IdentityResponse(
        name=identity.name,
        english_name=identity.english_name,
        role_type=identity.role_type.value,
        role_description=identity.role_description,
        expertise=identity.expertise,
        capabilities=identity.capabilities,
        personality=identity.personality,
        collaboration_style=identity.collaboration_style
    )

# API端点
@app.get('/')
async def root():
    """根端点"""
    return {
        'service': '统一身份服务',
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    }

@app.get('/api/v1/identities', response_model=List[IdentityResponse])
async def get_all_identities():
    """获取所有身份"""
    identities = identity_manager.get_all_identities()
    return [identity_to_response(id) for id in identities]

@app.get('/api/v1/identities/{role_name}', response_model=IdentityResponse)
async def get_identity(role_name: str):
    """获取特定身份"""
    try:
        role_type = RoleType(role_name.lower())
        identity = identity_manager.get_identity(role_type)
        if not identity:
            raise HTTPException(status_code=404, detail='身份未找到')
        return identity_to_response(identity)
    except ValueError:
        raise HTTPException(status_code=400, detail='无效的角色名称')

@app.get('/api/v1/identities/athena', response_model=IdentityResponse)
async def get_athena_identity():
    """获取Athena身份"""
    identity = identity_manager.get_identity(RoleType.ATHENA)
    if not identity:
        raise HTTPException(status_code=404, detail='Athena身份未找到')
    return identity_to_response(identity)

@app.get('/api/v1/identities/xiaonuo', response_model=IdentityResponse)
async def get_xiaonuo_identity():
    """获取小诺身份"""
    identity = identity_manager.get_identity(RoleType.XIAONUO)
    if not identity:
        raise HTTPException(status_code=404, detail='小诺身份未找到')
    return identity_to_response(identity)

@app.post('/api/v1/collaboration', response_model=CollaborationResponse)
async def create_collaboration(request: CollaborationRequest):
    """创建协作配置"""
    try:
        # 解析任务类型
        task_type = TaskType(request.task_type.lower())

        # 选择参与者
        participants = identity_manager.select_optimal_participants(
            task_type,
            request.complexity
        )

        # 创建协作身份
        collaborative_identity = identity_manager.create_collaborative_identity(participants)

        # 获取协作配置
        config = identity_manager.get_collaboration_config(task_type)

        # 计算效率估算
        efficiency = 1.0
        if len(participants) > 1:
            efficiency = 1.5 + (request.complexity * 0.5)  # 协作效率提升

        return CollaborationResponse(
            participants=[p.value for p in participants],
            mode=config.get('mode', 'sequential'),
            primary_role=config.get('primary', participants[0].value).value,
            secondary_role=config.get('secondary', {}).value if config.get('secondary') else None,
            collaborative_identity=identity_to_response(collaborative_identity),
            estimated_efficiency=efficiency
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"无效的输入: {str(e)}")

@app.get('/api/v1/collaboration/configs')
async def get_collaboration_configs():
    """获取所有协作配置"""
    return {
        task_type.value: config
        for task_type, config in identity_manager.collaboration_configs.items()
    }

@app.post('/api/v1/identity/optimize')
async def optimize_task_routing(task_info: Dict[str, Any]):
    """优化任务路由"""
    task_type = task_info.get('task_type', 'technical').lower()
    complexity = task_info.get('complexity', 0.5)

    try:
        task_enum = TaskType(task_type)
        participants = identity_manager.select_optimal_participants(task_enum, complexity)

        # 路由建议
        if len(participants) == 1:
            routing_suggestion = {
                'action': 'single_agent',
                'agent': participants[0].value,
                'reason': '任务适合单个代理处理'
            }
        else:
            routing_suggestion = {
                'action': 'collaborative',
                'primary': participants[0].value,
                'secondary': participants[1].value if len(participants) > 1 else None,
                'mode': identity_manager.get_collaboration_config(task_enum).get('mode'),
                'reason': '复杂任务需要协作处理'
            }

        return {
            'task_analysis': {
                'type': task_type,
                'complexity': complexity,
                'recommended_participants': len(participants)
            },
            'routing_suggestion': routing_suggestion
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"路由优化失败: {str(e)}")

@app.post('/api/v1/identity/sync')
async def sync_identities():
    """同步身份配置"""
    try:
        identity_manager.save_unified_config()
        return {
            'status': 'success',
            'message': '身份配置同步成功',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")

@app.get('/api/v1/health')
async def health_check():
    """健康检查"""
    return {
        'status': 'healthy',
        'service': 'unified-identity',
        'identities_loaded': len(identity_manager.identities),
        'timestamp': datetime.now().isoformat()
    }

# 启动服务
if __name__ == '__main__':
    logger.info('🚀 启动统一身份服务...')
    logger.info('服务地址: http://localhost:8090')
    logger.info('API文档: http://localhost:8090/docs')

    uvicorn.run(
        'api_server:app',
        host='0.0.0.0',
        port=8090,
        reload=True,
        log_level='info'
    )