#!/usr/bin/env python3
"""
AI模型服务统一入口
AI Models Service Unified Gateway
提供所有AI模型的统一访问接口和智能路由
"""

import asyncio
from datetime import datetime
from enum import Enum
from typing import Any

import httpx
import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from core.logging_config import setup_logging
from core.security.auth import ALLOWED_ORIGINS

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

# 模型类型枚举
class ModelType(str, Enum):
    DEEPSEEK = "deepseek"
    GLM = "glm"
    GLM_CODE = "glm_code"
    GLM_VISION = "glm_vision"
    GLM_VIDEO = "glm_video"
    GLM_IMAGE = "glm_image"
    AUTO = "auto"  # 自动选择

# 任务类型枚举
class TaskType(str, Enum):
    CODE_GENERATION = "code_generation"
    TEXT_ANALYSIS = "text_analysis"
    PATENT_ANALYSIS = "patent_analysis"
    MULTIMODAL = "multimodal"
    GENERAL = "general"

# 请求模型
class ModelRequest(BaseModel):
    task_type: TaskType = Field(..., description="任务类型")
    model_type: ModelType | None = Field(None, description="指定模型类型，None表示自动选择")
    input: dict[str, Any] = Field(..., description="输入参数")
    priority: int = Field(1, description="优先级，1-5")
    timeout: int | None = Field(60, description="超时时间（秒）")

# 响应模型
class ModelResponse(BaseModel):
    task_id: str
    model_used: str
    result: Any
    metadata: dict[str, Any]
    timestamp: str

# 配置管理
class Settings(BaseSettings):
    """配置管理"""
    app_name: str = "AI Models Service Gateway"
    version: str = "1.0.0"
    debug: bool = False
    port: int = 8082

    # 模型服务配置
    deepseek_url: str = "http://localhost:8088"
    dual_orchestrator_url: str = "http://localhost:8089"
    glm_full_suite_url: str = "http://localhost:8090"
    glm_integration_url: str = "http://localhost:8091"

    # 智能路由配置
    enable_smart_routing: bool = True
    load_balance_strategy: str = "round_robin"  # round_robin, least_busy, priority

    class Config:
        env_file = ".env"

settings = Settings()

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    description="Athena平台AI模型统一网关服务",
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 模型服务管理器
class ModelServiceManager:
    """模型服务管理器"""

    def __init__(self):
        self.services = {
            ModelType.DEEPSEEK: {
                "url": settings.deepseek_url,
                "capabilities": ["code_generation", "patent_analysis"],
                "status": "unknown",
                "load": 0
            },
            ModelType.GLM: {
                "url": settings.dual_orchestrator_url,
                "capabilities": ["text_analysis", "patent_analysis", "general"],
                "status": "unknown",
                "load": 0
            },
            ModelType.GLM_CODE: {
                "url": settings.glm_integration_url,
                "capabilities": ["code_generation", "text_analysis"],
                "status": "unknown",
                "load": 0
            },
            ModelType.GLM_VISION: {
                "url": settings.glm_full_suite_url,
                "capabilities": ["multimodal", "image_analysis"],
                "status": "unknown",
                "load": 0
            },
            ModelType.GLM_VIDEO: {
                "url": settings.glm_full_suite_url,
                "capabilities": ["video_generation", "multimodal"],
                "status": "unknown",
                "load": 0
            },
            ModelType.GLM_IMAGE: {
                "url": settings.glm_full_suite_url,
                "capabilities": ["image_generation", "multimodal"],
                "status": "unknown",
                "load": 0
            }
        }
        self.task_queue = asyncio.Queue()
        self.http_client = httpx.AsyncClient(timeout=60.0)

    async def health_check(self):
        """检查所有服务的健康状态"""
        for model_type, service in self.services.items():
            try:
                response = await self.http_client.get(
                    f"{service['url']}/health",
                    timeout=5.0
                )
                service["status"] = "healthy" if response.status_code == 200 else "unhealthy"
            except Exception as e:
                logger.warning(f"服务 {model_type} 健康检查失败: {e}")
                service["status"] = "unhealthy"

    def select_model(self, task_type: TaskType, model_type: ModelType | None = None) -> ModelType:
        """智能选择最适合的模型"""
        if model_type and model_type != ModelType.AUTO:
            return model_type

        # 基于任务类型选择
        task_model_map = {
            TaskType.CODE_GENERATION: [ModelType.DEEPSEEK, ModelType.GLM_CODE],
            TaskType.PATENT_ANALYSIS: [ModelType.DEEPSEEK, ModelType.GLM],
            TaskType.MULTIMODAL: [ModelType.GLM_VISION, ModelType.GLM_IMAGE, ModelType.GLM_VIDEO],
            TaskType.TEXT_ANALYSIS: [ModelType.GLM, ModelType.GLM_CODE],
            TaskType.GENERAL: [ModelType.GLM]
        }

        candidates = task_model_map.get(task_type, [ModelType.GLM])

        # 过滤健康的服务
        healthy_candidates = [
            model for model in candidates
            if self.services[model]["status"] == "healthy"
        ]

        if not healthy_candidates:
            # 如果没有健康的服务，返回默认选择
            logger.warning(f"没有健康的{task_type}服务，使用默认模型")
            return candidates[0]

        # 根据负载策略选择
        if settings.load_balance_strategy == "least_busy":
            return min(healthy_candidates, key=lambda m: self.services[m]["load"])
        elif settings.load_balance_strategy == "priority":
            return healthy_candidates[0]  # 已按优先级排序
        else:  # round_robin
            import random
            return random.choice(healthy_candidates)

    async def call_model(self, model_type: ModelType, task_type: TaskType, input_data: dict[str, Any]) -> dict[str, Any]:
        """调用指定的模型服务"""
        service = self.services[model_type]

        # 增加负载
        self.services[model_type]["load"] += 1

        try:
            # 根据任务类型构建请求
            endpoint = self._get_endpoint(task_type, model_type)
            url = f"{service['url']}{endpoint}"

            # 发送请求
            response = await self.http_client.post(
                url,
                json=input_data,
                timeout=settings.timeout
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"模型 {model_type} 处理任务成功")
                return result
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"模型服务错误: {response.text}"
                )

        except Exception as e:
            logger.error(f"调用模型 {model_type} 失败: {e}")
            raise HTTPException(status_code=500, detail=f"模型调用失败: {str(e)}") from e

        finally:
            # 减少负载
            self.services[model_type]["load"] = max(0, self.services[model_type]["load"] - 1)

    def _get_endpoint(self, task_type: TaskType, model_type: ModelType) -> str:
        """获取任务对应的端点"""
        endpoint_map = {
            (TaskType.CODE_GENERATION, ModelType.DEEPSEEK): "/api/v1/code/generate",
            (TaskType.CODE_GENERATION, ModelType.GLM_CODE): "/api/v1/code/generate",
            (TaskType.PATENT_ANALYSIS, ModelType.DEEPSEEK): "/api/v1/patent/analyze",
            (TaskType.PATENT_ANALYSIS, ModelType.GLM): "/api/v1/patent/analyze",
            (TaskType.MULTIMODAL, ModelType.GLM_VISION): "/api/v1/vision/analyze",
            (TaskType.MULTIMODAL, ModelType.GLM_IMAGE): "/api/v1/image/generate",
            (TaskType.MULTIMODAL, ModelType.GLM_VIDEO): "/api/v1/video/generate",
            (TaskType.TEXT_ANALYSIS, ModelType.GLM): "/api/v1/text/analyze",
            (TaskType.GENERAL, ModelType.GLM): "/api/v1/chat"
        }
        return endpoint_map.get((task_type, model_type), "/api/v1/process")

# 创建服务管理器实例
service_manager = ModelServiceManager()

# 启动时检查服务健康状态
@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    logger.info(f"启动 {settings.app_name} v{settings.version}")
    await service_manager.health_check()
    logger.info("AI模型服务网关启动完成")

# 移除阻塞的定期健康检查 - 改为在后台任务中运行

# API端点
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": settings.app_name,
        "version": settings.version,
        "status": "running",
        "models": list(service_manager.services.keys()),
        "message": "AI模型服务网关运行正常",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    """健康检查"""
    await service_manager.health_check()

    service_status = {}
    healthy_count = 0

    for model_type, service in service_manager.services.items():
        service_status[model_type.value] = {
            "status": service["status"],
            "load": service["load"],
            "url": service["url"]
        }
        if service["status"] == "healthy":
            healthy_count += 1

    return {
        "status": "healthy" if healthy_count > 0 else "degraded",
        "total_models": len(service_manager.services),
        "healthy_models": healthy_count,
        "services": service_status,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/models")
async def list_models():
    """列出所有可用模型及其状态"""
    await service_manager.health_check()

    models_info = []
    for model_type, service in service_manager.services.items():
        models_info.append({
            "name": model_type.value,
            "capabilities": service["capabilities"],
            "status": service["status"],
            "load": service["load"],
            "url": service["url"]
        })

    return {
        "models": models_info,
        "total": len(models_info),
        "routing_strategy": settings.load_balance_strategy
    }

@app.post("/api/v1/inference", response_model=ModelResponse)
async def inference(request: ModelRequest, background_tasks: BackgroundTasks):
    """统一推理接口"""
    import uuid
    task_id = str(uuid.uuid4())

    # 选择最适合的模型
    selected_model = service_manager.select_model(request.task_type, request.model_type)

    try:
        # 调用模型服务
        result = await service_manager.call_model(
            selected_model,
            request.task_type,
            request.input
        )

        # 构建响应
        response = ModelResponse(
            task_id=task_id,
            model_used=selected_model.value,
            result=result,
            metadata={
                "task_type": request.task_type.value,
                "selected_model": selected_model.value,
                "processing_time": 0,  # TODO: 计算实际处理时间
                "priority": request.priority
            },
            timestamp=datetime.now().isoformat()
        )

        logger.info(f"任务 {task_id} 完成，使用模型: {selected_model.value}")
        return response

    except Exception as e:
        logger.error(f"任务 {task_id} 失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post("/api/v1/batch")
async def batch_inference(requests: list[ModelRequest]):
    """批量推理接口"""
    tasks = []
    for req in requests:
        selected_model = service_manager.select_model(req.task_type, req.model_type)
        task = service_manager.call_model(selected_model, req.task_type, req.input)
        tasks.append(task)

    # 并发执行
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 处理结果
    responses = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            responses.append({
                "index": i,
                "status": "error",
                "error": str(result)
            })
        else:
            responses.append({
                "index": i,
                "status": "success",
                "result": result
            })

    return {
        "batch_id": str(__import__('uuid').uuid4()),
        "total": len(requests),
        "success": sum(1 for r in responses if r["status"] == "success"),
        "results": responses,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/stats")
async def get_statistics():
    """获取服务统计信息"""
    await service_manager.health_check()

    stats = {
        "gateway": {
            "uptime": "0h 0m 0s",  # TODO: 计算实际运行时间
            "total_requests": 0,   # TODO: 添加请求计数
            "active_tasks": 0
        },
        "models": {}
    }

    for model_type, service in service_manager.services.items():
        stats["models"][model_type.value] = {
            "status": service["status"],
            "load": service["load"],
            "capabilities": service["capabilities"]
        }

    return stats

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug
    )
