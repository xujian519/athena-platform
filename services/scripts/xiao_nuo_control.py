#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小诺智能控制中心
Xiao Nuo Intelligent Control Center for Athena Multimodal System
提供智能化的系统控制、监控和优化功能
"""

import asyncio
from core.async_main import async_main
import json
import logging
from core.logging_config import setup_logging
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import psutil
import requests
import uvicorn
import yaml

# FastAPI相关
from fastapi import (
    BackgroundTasks,
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 导入统一认证模块
from shared.auth.auth_middleware import create_auth_middleware, setup_cors

# AI决策相关
try:
    import numpy as np
    import pandas as pd
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = logging.getLogger('XiaoNuoControl')

class ControlAction(Enum):
    """控制动作"""
    START = 'start'
    STOP = 'stop'
    RESTART = 'restart'
    SCALE = 'scale'
    UPDATE_CONFIG = 'update_config'
    HEALTH_CHECK = 'health_check'

class ServiceStatus(Enum):
    """服务状态"""
    RUNNING = 'running'
    STOPPED = 'stopped'
    ERROR = 'error'
    STARTING = 'starting'
    STOPPING = 'stopping'

@dataclass
class ServiceInfo:
    """服务信息"""
    name: str
    port: int
    status: ServiceStatus
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    request_count: int = 0
    error_count: int = 0
    uptime: float = 0.0
    last_health_check: datetime | None = None
    config: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ControlDecision:
    """控制决策"""
    action: ControlAction
    target_service: str
    reason: str
    confidence: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

# Pydantic模型
class ServiceControlRequest(BaseModel):
    """服务控制请求"""
    service_name: str
    action: str
    parameters: Dict[str, Any] = {}

class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    service_name: str
    config_updates: Dict[str, Any]

class SystemMetrics(BaseModel):
    """系统指标"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    service_count: int
    active_services: List[str]
    timestamp: datetime

class XiaoNuoControlCenter:
    """小诺智能控制中心"""

    def __init__(self, config_path: str = None):
        self.config_path = config_path or '/Users/xujian/Athena工作平台/deploy/multimodal_platform_config.yaml'
        self.config = self._load_config()

        # 服务管理
        self.services: Dict[str, ServiceInfo] = {}
        self.control_history: List[ControlDecision] = []

        # AI决策
        self.ai_enabled = AI_AVAILABLE and self.config.get('xiao_nuo', {}).get('ai_decision', {}).get('enabled', False)

        # WebSocket连接
        self.websocket_connections: List[WebSocket] = []

        # 初始化服务监控
        self._initialize_services()

        logger.info(f"小诺智能控制中心初始化完成")
        logger.info(f"AI决策: {'启用' if self.ai_enabled else '禁用'}")

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"配置文件加载失败: {e}")
            return {}

    def _initialize_services(self) -> Any:
        """初始化服务监控"""
        services_config = self.config.get('services', {})

        for service_name, service_config in services_config.items():
            service_info = ServiceInfo(
                name=service_config.get('name', service_name),
                port=service_config.get('port'),
                status=ServiceStatus.STOPPED,
                config=service_config
            )
            self.services[service_name] = service_info

    async def start_service(self, service_name: str) -> Dict[str, Any]:
        """启动服务"""
        if service_name not in self.services:
            return {'success': False, 'error': f"服务不存在: {service_name}"}

        service_info = self.services[service_name]

        try:
            if service_info.status == ServiceStatus.RUNNING:
                return {'success': True, 'message': f"服务已在运行: {service_name}"}

            # 更新状态
            service_info.status = ServiceStatus.STARTING

            # 根据服务类型执行启动命令
            if service_name == 'dolphin_parser':
                result = await self._start_dolphin_service()
            elif service_name == 'glm_vision':
                result = await self._start_glm_vision_service()
            elif service_name == 'multimodal_processor':
                result = await self._start_multimodal_processor()
            elif service_name == 'api_gateway':
                result = await self._start_api_gateway()
            else:
                result = await self._start_custom_service(service_name, service_info.config)

            if result['success']:
                service_info.status = ServiceStatus.RUNNING
                service_info.uptime = 0.0
                await self._record_control_decision(
                    ControlAction.START, service_name, '用户请求启动', 1.0
                )
            else:
                service_info.status = ServiceStatus.ERROR

            return result

        except Exception as e:
            logger.error(f"启动服务失败 {service_name}: {e}")
            service_info.status = ServiceStatus.ERROR
            return {'success': False, 'error': str(e)}

    async def stop_service(self, service_name: str) -> Dict[str, Any]:
        """停止服务"""
        if service_name not in self.services:
            return {'success': False, 'error': f"服务不存在: {service_name}"}

        service_info = self.services[service_name]

        try:
            if service_info.status == ServiceStatus.STOPPED:
                return {'success': True, 'message': f"服务已停止: {service_name}"}

            # 更新状态
            service_info.status = ServiceStatus.STOPPING

            # 执行停止命令
            if service_name == 'dolphin_parser':
                result = await self._stop_dolphin_service()
            elif service_name == 'glm_vision':
                result = await self._stop_glm_vision_service()
            elif service_name == 'multimodal_processor':
                result = await self._stop_multimodal_processor()
            elif service_name == 'api_gateway':
                result = await self._stop_api_gateway()
            else:
                result = await self._stop_custom_service(service_name)

            if result['success']:
                service_info.status = ServiceStatus.STOPPED
                await self._record_control_decision(
                    ControlAction.STOP, service_name, '用户请求停止', 1.0
                )
            else:
                service_info.status = ServiceStatus.ERROR

            return result

        except Exception as e:
            logger.error(f"停止服务失败 {service_name}: {e}")
            service_info.status = ServiceStatus.ERROR
            return {'success': False, 'error': str(e)}

    async def restart_service(self, service_name: str) -> Dict[str, Any]:
        """重启服务"""
        # 先停止
        stop_result = await self.stop_service(service_name)
        if not stop_result['success']:
            return stop_result

        # 等待一段时间
        await asyncio.sleep(2)

        # 再启动
        start_result = await self.start_service(service_name)

        return start_result

    async def scale_service(self, service_name: str, replicas: int) -> Dict[str, Any]:
        """扩展服务实例"""
        if service_name not in self.services:
            return {'success': False, 'error': f"服务不存在: {service_name}"}

        try:
            service_info = self.services[service_name]
            current_replicas = service_info.config.get('instances', 1)

            if replicas == current_replicas:
                return {'success': True, 'message': f"实例数已为: {replicas}"}

            # 更新配置
            service_info.config['instances'] = replicas

            # 重启服务以应用新配置
            restart_result = await self.restart_service(service_name)

            if restart_result['success']:
                await self._record_control_decision(
                    ControlAction.SCALE, service_name, f"扩展到{replicas}个实例", 0.9,
                    {'replicas': replicas}
                )
                return {'success': True, 'message': f"服务已扩展到 {replicas} 个实例"}
            else:
                return restart_result

        except Exception as e:
            logger.error(f"扩展服务失败 {service_name}: {e}")
            return {'success': False, 'error': str(e)}

    async def update_service_config(self, service_name: str, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新服务配置"""
        if service_name not in self.services:
            return {'success': False, 'error': f"服务不存在: {service_name}"}

        try:
            service_info = self.services[service_name]

            # 更新配置
            service_info.config.update(config_updates)

            # 重启服务以应用新配置
            restart_result = await self.restart_service(service_name)

            if restart_result['success']:
                await self._record_control_decision(
                    ControlAction.UPDATE_CONFIG, service_name, '配置更新', 0.8,
                    {'config_updates': config_updates}
                )
                return {'success': True, 'message': f"服务配置已更新"}
            else:
                return restart_result

        except Exception as e:
            logger.error(f"更新配置失败 {service_name}: {e}")
            return {'success': False, 'error': str(e)}

    async def health_check_all_services(self) -> Dict[str, Any]:
        """检查所有服务健康状态"""
        health_results = {}

        for service_name, service_info in self.services.items():
            if service_info.status == ServiceStatus.RUNNING:
                health_result = await self._health_check_service(service_name)
                health_results[service_name] = health_result
            else:
                health_results[service_name] = {
                    'healthy': False,
                    'reason': f"服务状态: {service_info.status.value}"
                }

        return {
            'overall_healthy': all(result.get('healthy', False) for result in health_results.values()),
            'service_health': health_results,
            'timestamp': datetime.now().isoformat()
        }

    async def _health_check_service(self, service_name: str) -> Dict[str, Any]:
        """检查单个服务健康状态"""
        service_info = self.services[service_name]

        try:
            # 调用服务健康检查接口
            health_url = f"http://localhost:{service_info.port}/health"
            response = requests.get(health_url, timeout=5)

            if response.status_code == 200:
                service_info.last_health_check = datetime.now()
                return {'healthy': True, 'response': response.json()}
            else:
                return {'healthy': False, 'reason': f"HTTP {response.status_code}"}

        except Exception as e:
            return {'healthy': False, 'reason': str(e)}

    async def get_system_metrics(self) -> SystemMetrics:
        """获取系统指标"""
        # 系统资源使用
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')

        # 网络IO
        net_io = psutil.net_io_counters()

        # 服务统计
        active_services = [
            name for name, info in self.services.items()
            if info.status == ServiceStatus.RUNNING
        ]

        return SystemMetrics(
            cpu_usage=cpu_usage,
            memory_usage=memory_info.percent,
            disk_usage=disk_info.percent,
            network_io={
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv
            },
            service_count=len(self.services),
            active_services=active_services,
            timestamp=datetime.now()
        )

    async def ai_optimize_system(self) -> Dict[str, Any]:
        """AI优化系统"""
        if not self.ai_enabled:
            return {'success': False, 'error': 'AI决策未启用'}

        try:
            # 获取当前系统状态
            metrics = await self.get_system_metrics()
            health_results = await self.health_check_all_services()

            # AI决策逻辑
            decisions = []

            # 1. 负载均衡优化
            if metrics.cpu_usage > 80:
                # 找出负载最高的服务
                high_load_service = self._find_high_load_service()
                if high_load_service:
                    decision = ControlDecision(
                        action=ControlAction.SCALE,
                        target_service=high_load_service,
                        reason='CPU使用率过高，扩展服务实例',
                        confidence=0.85,
                        parameters={'replicas': 2}
                    )
                    decisions.append(decision)

            # 2. 内存优化
            if metrics.memory_usage > 85:
                decision = ControlDecision(
                    action=ControlAction.RESTART,
                    target_service='api_gateway',
                    reason='内存使用率过高，重启服务释放内存',
                    confidence=0.7
                )
                decisions.append(decision)

            # 3. 健康检查优化
            if not health_results['overall_healthy']:
                unhealthy_services = [
                    name for name, health in health_results['service_health'].items()
                    if not health['healthy']
                ]
                for service in unhealthy_services:
                    decision = ControlDecision(
                        action=ControlAction.RESTART,
                        target_service=service,
                        reason=f"服务不健康，自动重启",
                        confidence=0.9
                    )
                    decisions.append(decision)

            # 执行决策
            execution_results = []
            for decision in decisions:
                result = await self._execute_control_decision(decision)
                execution_results.append(result)

            return {
                'success': True,
                'decisions_made': len(decisions),
                'decisions': [
                    {
                        'action': d.action.value,
                        'target': d.target_service,
                        'reason': d.reason,
                        'confidence': d.confidence
                    }
                    for d in decisions
                ],
                'execution_results': execution_results,
                'system_metrics': metrics.dict()
            }

        except Exception as e:
            logger.error(f"AI优化失败: {e}")
            return {'success': False, 'error': str(e)}

    def _find_high_load_service(self) -> str | None:
        """找出负载最高的服务"""
        max_cpu = 0
        high_load_service = None

        for service_name, service_info in self.services.items():
            if service_info.status == ServiceStatus.RUNNING and service_info.cpu_usage > max_cpu:
                max_cpu = service_info.cpu_usage
                high_load_service = service_name

        return high_load_service

    async def _execute_control_decision(self, decision: ControlDecision) -> Dict[str, Any]:
        """执行控制决策"""
        await self._record_control_decision(
            decision.action, decision.target_service,
            decision.reason, decision.confidence, decision.parameters
        )

        if decision.action == ControlAction.START:
            return await self.start_service(decision.target_service)
        elif decision.action == ControlAction.STOP:
            return await self.stop_service(decision.target_service)
        elif decision.action == ControlAction.RESTART:
            return await self.restart_service(decision.target_service)
        elif decision.action == ControlAction.SCALE:
            replicas = decision.parameters.get('replicas', 1)
            return await self.scale_service(decision.target_service, replicas)
        elif decision.action == ControlAction.UPDATE_CONFIG:
            return await self.update_service_config(
                decision.target_service, decision.parameters
            )
        else:
            return {'success': False, 'error': f"未知控制动作: {decision.action}"}

    async def _record_control_decision(self, action: ControlAction, target: str,
                                     reason: str, confidence: float, parameters: Dict = None):
        """记录控制决策"""
        decision = ControlDecision(
            action=action,
            target_service=target,
            reason=reason,
            confidence=confidence,
            parameters=parameters or {}
        )

        self.control_history.append(decision)

        # 限制历史记录数量
        if len(self.control_history) > 1000:
            self.control_history = self.control_history[-500:]

        # 通知WebSocket客户端
        await self._notify_websocket_clients({
            'type': 'control_decision',
            'decision': {
                'action': action.value,
                'target': target,
                'reason': reason,
                'confidence': confidence,
                'timestamp': decision.timestamp.isoformat()
            }
        })

    # 具体服务启动/停止方法
    async def _start_dolphin_service(self) -> Dict[str, Any]:
        """启动Dolphin服务"""
        try:
            cmd = ['bash', '/Users/xujian/Athena工作平台/scripts/startup/start_dolphin_service.sh']
            result = await self._execute_command(cmd)
            return {'success': result['success'], 'message': 'Dolphin服务启动命令执行完成'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _stop_dolphin_service(self) -> Dict[str, Any]:
        """停止Dolphin服务"""
        try:
            cmd = ['bash', '/Users/xujian/Athena工作平台/scripts/shutdown_dolphin_service.sh']
            result = await self._execute_command(cmd)
            return {'success': result['success'], 'message': 'Dolphin服务停止命令执行完成'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _start_glm_vision_service(self) -> Dict[str, Any]:
        """启动GLM视觉服务"""
        try:
            cmd = ['cd', '/Users/xujian/Athena工作平台/services/ai-models/glm-full-suite', '&&',
                   'nohup', 'python3', 'athena_glm_full_suite_server.py', '>',
                   '/Users/xujian/Athena工作平台/logs/glm_vision.log', '2>&1', '&']
            result = await self._execute_command(cmd)
            return {'success': result['success'], 'message': 'GLM视觉服务启动命令执行完成'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _stop_glm_vision_service(self) -> Dict[str, Any]:
        """停止GLM视觉服务"""
        try:
            # 查找并杀掉进程
            cmd = ['pkill', '-f', 'athena_glm_full_suite_server.py']
            result = await self._execute_command(cmd)
            return {'success': result['success'], 'message': 'GLM视觉服务停止命令执行完成'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _start_multimodal_processor(self) -> Dict[str, Any]:
        """启动多模态处理器"""
        try:
            cmd = ['cd', '/Users/xujian/Athena工作平台/services', '&&',
                   'nohup', 'python3', 'multimodal_processing_service.py', '>',
                   '/Users/xujian/Athena工作平台/logs/multimodal_processor.log', '2>&1', '&']
            result = await self._execute_command(cmd)
            return {'success': result['success'], 'message': '多模态处理器启动命令执行完成'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _stop_multimodal_processor(self) -> Dict[str, Any]:
        """停止多模态处理器"""
        try:
            cmd = ['pkill', '-f', 'multimodal_processing_service.py']
            result = await self._execute_command(cmd)
            return {'success': result['success'], 'message': '多模态处理器停止命令执行完成'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _start_api_gateway(self) -> Dict[str, Any]:
        """启动API网关"""
        try:
            cmd = ['cd', '/Users/xujian/Athena工作平台/services', '&&',
                   'nohup', 'python3', 'unified_multimodal_api.py', '>',
                   '/Users/xujian/Athena工作平台/logs/unified_multimodal_api.log', '2>&1', '&']
            result = await self._execute_command(cmd)
            return {'success': result['success'], 'message': 'API网关启动命令执行完成'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _stop_api_gateway(self) -> Dict[str, Any]:
        """停止API网关"""
        try:
            cmd = ['pkill', '-f', 'unified_multimodal_api.py']
            result = await self._execute_command(cmd)
            return {'success': result['success'], 'message': 'API网关停止命令执行完成'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _start_custom_service(self, service_name: str, config: Dict) -> Dict[str, Any]:
        """启动自定义服务"""
        try:
            # 这里可以根据配置启动自定义服务
            return {'success': True, 'message': f"自定义服务 {service_name} 启动完成"}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _stop_custom_service(self, service_name: str) -> Dict[str, Any]:
        """停止自定义服务"""
        try:
            # 这里可以根据配置停止自定义服务
            return {'success': True, 'message': f"自定义服务 {service_name} 停止完成"}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _execute_command(self, cmd: List[str]) -> Dict[str, Any]:
        """执行系统命令"""
        try:
            import subprocess
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _notify_websocket_clients(self, message: Dict):
        """通知所有WebSocket客户端"""
        if not self.websocket_connections:
            return

        message_str = json.dumps(message, ensure_ascii=False)
        disconnected_clients = []

        for websocket in self.websocket_connections:
            try:
                await websocket.send_text(message_str)
            except Exception:
                disconnected_clients.append(websocket)

        # 移除断开的连接
        for client in disconnected_clients:
            self.websocket_connections.remove(client)

    # WebSocket处理
    async def handle_websocket(self, websocket: WebSocket):
        """处理WebSocket连接"""
        await websocket.accept()
        self.websocket_connections.append(websocket)

        try:
            while True:
                # 接收客户端消息
                data = await websocket.receive_text()
                message = json.loads(data)

                # 处理消息
                if message.get('type') == 'subscribe':
                    # 客户端订阅特定事件
                    await self._handle_subscription(websocket, message.get('event'))
                elif message.get('type') == 'command':
                    # 执行控制命令
                    result = await self._handle_control_command(message)
                    await websocket.send_text(json.dumps(result, ensure_ascii=False))

        except WebSocketDisconnect:
            self.websocket_connections.remove(websocket)
        except Exception as e:
            logger.error(f"WebSocket处理错误: {e}")
            if websocket in self.websocket_connections:
                self.websocket_connections.remove(websocket)

    async def _handle_subscription(self, websocket: WebSocket, event: str):
        """处理客户端订阅"""
        # 这里可以实现特定事件的订阅逻辑
        await websocket.send_text(json.dumps({
            'type': 'subscription_confirmed',
            'event': event
        }, ensure_ascii=False))

    async def _handle_control_command(self, message: Dict) -> Dict:
        """处理控制命令"""
        command_type = message.get('command')

        if command_type == 'start':
            return await self.start_service(message.get('service'))
        elif command_type == 'stop':
            return await self.stop_service(message.get('service'))
        elif command_type == 'restart':
            return await self.restart_service(message.get('service'))
        elif command_type == 'scale':
            return await self.scale_service(
                message.get('service'),
                message.get('replicas', 1)
            )
        elif command_type == 'health_check':
            return await self.health_check_all_services()
        elif command_type == 'metrics':
            metrics = await self.get_system_metrics()
            return {'success': True, 'metrics': metrics.dict()}
        elif command_type == 'ai_optimize':
            return await self.ai_optimize_system()
        else:
            return {'success': False, 'error': f"未知命令: {command_type}"}

# 创建FastAPI应用
control_center = None

def create_control_center() -> Any:
    """创建控制中心实例"""
    global control_center
    if control_center is None:
        control_center = XiaoNuoControlCenter()
    return control_center

app = FastAPI(
    title='小诺智能控制中心',
    description='Athena多模态文件系统智能控制中心',
    version='1.0.0'
)


# API端点
@app.get('/')
async def root():
    """根端点"""
    return {
        'service': '小诺智能控制中心',
        'status': 'running',
        'version': '1.0.0',
        'ai_enabled': create_control_center().ai_enabled,
        'controlled_services': len(create_control_center().services)
    }

@app.post('/control/service')
async def control_service(request: ServiceControlRequest):
    """控制服务"""
    cc = create_control_center()

    if request.action == 'start':
        return await cc.start_service(request.service_name)
    elif request.action == 'stop':
        return await cc.stop_service(request.service_name)
    elif request.action == 'restart':
        return await cc.restart_service(request.service_name)
    else:
        raise HTTPException(status_code=400, detail=f"不支持的动作: {request.action}")

@app.post('/control/scale')
async def scale_service(service_name: str, replicas: int):
    """扩展服务"""
    cc = create_control_center()
    return await cc.scale_service(service_name, replicas)

@app.post('/config/update')
async def update_config(request: ConfigUpdateRequest):
    """更新配置"""
    cc = create_control_center()
    return await cc.update_service_config(
        request.service_name,
        request.config_updates
    )

@app.get('/health')
async def health_check():
    """健康检查"""
    cc = create_control_center()
    health_result = await cc.health_check_all_services()

    return {
        'status': 'healthy',
        'service_health': health_result,
        'timestamp': datetime.now().isoformat()
    }

@app.get('/metrics', response_model=SystemMetrics)
async def get_metrics():
    """获取系统指标"""
    cc = create_control_center()
    return await cc.get_system_metrics()

@app.post('/ai/optimize')
async def ai_optimize():
    """AI优化系统"""
    cc = create_control_center()
    return await cc.ai_optimize_system()

@app.get('/services')
async def get_services():
    """获取所有服务状态"""
    cc = create_control_center()

    services_status = {}
    for name, info in cc.services.items():
        services_status[name] = {
            'name': info.name,
            'port': info.port,
            'status': info.status.value,
            'cpu_usage': info.cpu_usage,
            'memory_usage': info.memory_usage,
            'uptime': info.uptime,
            'config': info.config
        }

    return {
        'services': services_status,
        'total_services': len(services_status),
        'active_services': len([s for s in services_status.values() if s['status'] == 'running'])
    }

@app.get('/control/history')
async def get_control_history(limit: int = 50):
    """获取控制历史"""
    cc = create_control_center()

    history = cc.control_history[-limit:]
    return {
        'history': [
            {
                'action': d.action.value,
                'target': d.target_service,
                'reason': d.reason,
                'confidence': d.confidence,
                'parameters': d.parameters,
                'timestamp': d.timestamp.isoformat()
            }
            for d in history
        ],
        'total_decisions': len(cc.control_history)
    }

@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点"""
    cc = create_control_center()
    await cc.handle_websocket(websocket)

# 启动服务
if __name__ == '__main__':
    control_config = {
        'host': '0.0.0.0',
        'port': 9001,
        'reload': False,
        'log_level': 'info'
    }

    uvicorn.run(
        'xiao_nuo_control:app',
        **control_config
    )