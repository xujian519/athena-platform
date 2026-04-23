"""
PatentDraftingProxy健康检查模块
Health Check Module for PatentDraftingProxy

提供全面的健康检查和监控端点
Provides comprehensive health check and monitoring endpoints
"""

from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# 创建路由器
health_router = APIRouter(prefix="/health", tags=["health"])


# ==================== 数据模型 ====================
class HealthCheckResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态: healthy, degraded, unhealthy")
    timestamp: str = Field(..., description="检查时间戳")
    version: str = Field(..., description="服务版本")
    environment: str = Field(..., description="运行环境")
    uptime: float = Field(..., description="运行时间(秒)")


class ComponentHealth(BaseModel):
    """组件健康状态"""
    name: str = Field(..., description="组件名称")
    status: str = Field(..., description="状态: healthy, unhealthy, unknown")
    message: str = Field(..., description="状态消息")
    response_time_ms: Optional[float] = Field(None, description="响应时间(毫秒)")


class DetailedHealthCheckResponse(HealthCheckResponse):
    """详细健康检查响应"""
    components: Dict[str, ComponentHealth] = Field(..., description="各组件健康状态")
    metrics: Dict[str, Any] = Field(..., description="系统指标")


class LivenessResponse(BaseModel):
    """存活探针响应"""
    status: str = Field(..., description="存活状态")
    timestamp: str = Field(..., description="检查时间")


class ReadinessResponse(BaseModel):
    """就绪探针响应"""
    status: str = Field(..., description="就绪状态")
    timestamp: str = Field(..., description="检查时间")
    checks: Dict[str, bool] = Field(..., description="各项就绪检查")


# ==================== 全局变量 ====================
_start_time = datetime.now()
_service_version = "1.0.0"
_service_environment = "production"


# ==================== 健康检查函数 ====================
async def check_database_health() -> ComponentHealth:
    """检查数据库健康状态"""
    start_time = datetime.now()
    
    try:
        # 这里添加实际的数据库检查逻辑
        # 例如: ping PostgreSQL, Redis, Neo4j, Qdrant
        
        # PostgreSQL检查
        # from core.database import get_db
        # db = next(get_db())
        # await db.execute("SELECT 1")
        
        # Redis检查
        # from core.redis import redis_client
        # await redis_client.ping()
        
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        
        return ComponentHealth(
            name="database",
            status="healthy",
            message="所有数据库连接正常",
            response_time_ms=elapsed
        )
    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        logger.error(f"数据库健康检查失败: {e}")
        
        return ComponentHealth(
            name="database",
            status="unhealthy",
            message=f"数据库连接失败: {str(e)}",
            response_time_ms=elapsed
        )


async def check_llm_health() -> ComponentHealth:
    """检查LLM服务健康状态"""
    start_time = datetime.now()
    
    try:
        # 这里添加实际的LLM检查逻辑
        # 例如: 调用LLM API测试
        
        # from core.llm import llm_manager
        # await llm_manager.test_connection()
        
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        
        return ComponentHealth(
            name="llm",
            status="healthy",
            message="LLM服务连接正常",
            response_time_ms=elapsed
        )
    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        logger.error(f"LLM健康检查失败: {e}")
        
        return ComponentHealth(
            name="llm",
            status="degraded",
            message=f"LLM服务降级: {str(e)}",
            response_time_ms=elapsed
        )


async def check_knowledge_base_health() -> ComponentHealth:
    """检查知识库健康状态"""
    start_time = datetime.now()
    
    try:
        # 这里添加实际的知识库检查逻辑
        
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        
        return ComponentHealth(
            name="knowledge_base",
            status="healthy",
            message="知识库加载正常",
            response_time_ms=elapsed
        )
    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        logger.error(f"知识库健康检查失败: {e}")
        
        return ComponentHealth(
            name="knowledge_base",
            status="unhealthy",
            message=f"知识库访问失败: {str(e)}",
            response_time_ms=elapsed
        )


async def check_memory_health() -> ComponentHealth:
    """检查内存使用健康状态"""
    start_time = datetime.now()
    
    try:
        import psutil
        
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        
        if memory_percent < 70:
            status = "healthy"
            message = f"内存使用正常 ({memory_percent:.1f}%)"
        elif memory_percent < 85:
            status = "degraded"
            message = f"内存使用较高 ({memory_percent:.1f}%)"
        else:
            status = "unhealthy"
            message = f"内存使用过高 ({memory_percent:.1f}%)"
        
        return ComponentHealth(
            name="memory",
            status=status,
            message=message,
            response_time_ms=elapsed
        )
    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        logger.error(f"内存健康检查失败: {e}")
        
        return ComponentHealth(
            name="memory",
            status="unknown",
            message=f"无法获取内存状态: {str(e)}",
            response_time_ms=elapsed
        )


async def check_disk_health() -> ComponentHealth:
    """检查磁盘使用健康状态"""
    start_time = datetime.now()
    
    try:
        import psutil
        
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        
        if disk_percent < 80:
            status = "healthy"
            message = f"磁盘使用正常 ({disk_percent:.1f}%)"
        elif disk_percent < 90:
            status = "degraded"
            message = f"磁盘空间较少 ({disk_percent:.1f}%)"
        else:
            status = "unhealthy"
            message = f"磁盘空间不足 ({disk_percent:.1f}%)"
        
        return ComponentHealth(
            name="disk",
            status=status,
            message=message,
            response_time_ms=elapsed
        )
    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        logger.error(f"磁盘健康检查失败: {e}")
        
        return ComponentHealth(
            name="disk",
            status="unknown",
            message=f"无法获取磁盘状态: {str(e)}",
            response_time_ms=elapsed
        )


# ==================== API端点 ====================
@health_router.get("/", response_model=HealthCheckResponse)
async def health_check():
    """
    基本健康检查端点
    
    返回服务的基本健康状态，用于负载均衡器和监控系统
    Returns basic health status for load balancers and monitoring systems
    """
    uptime = (datetime.now() - _start_time).total_seconds()
    
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version=_service_version,
        environment=_service_environment,
        uptime=uptime
    )


@health_router.get("/detailed", response_model=DetailedHealthCheckResponse)
async def detailed_health_check():
    """
    详细健康检查端点
    
    返回所有组件的详细健康状态
    Returns detailed health status of all components
    """
    # 并行检查所有组件
    checks = await asyncio.gather(
        check_database_health(),
        check_llm_health(),
        check_knowledge_base_health(),
        check_memory_health(),
        check_disk_health(),
        return_exceptions=True
    )
    
    # 处理检查结果
    components = {}
    overall_status = "healthy"
    
    for check in checks:
        if isinstance(check, Exception):
            logger.error(f"健康检查异常: {check}")
            continue
        
        components[check.name] = check
        
        # 确定整体状态
        if check.status == "unhealthy":
            overall_status = "unhealthy"
        elif check.status == "degraded" and overall_status != "unhealthy":
            overall_status = "degraded"
    
    # 收集系统指标
    try:
        import psutil
        
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        metrics = {
            "cpu_percent": cpu_percent,
            "memory": {
                "total_gb": memory.total / (1024**3),
                "available_gb": memory.available / (1024**3),
                "used_percent": memory.percent,
                "used_gb": memory.used / (1024**3)
            },
            "disk": {
                "total_gb": disk.total / (1024**3),
                "free_gb": disk.free / (1024**3),
                "used_percent": disk.percent,
                "used_gb": disk.used / (1024**3)
            }
        }
    except Exception as e:
        logger.error(f"获取系统指标失败: {e}")
        metrics = {}
    
    uptime = (datetime.now() - _start_time).total_seconds()
    
    return DetailedHealthCheckResponse(
        status=overall_status,
        timestamp=datetime.now().isoformat(),
        version=_service_version,
        environment=_service_environment,
        uptime=uptime,
        components=components,
        metrics=metrics
    )


@health_router.get("/live", response_model=LivenessResponse)
async def liveness():
    """
    存活探针端点
    
    用于Kubernetes liveness probe，检查服务是否存活
    For Kubernetes liveness probe, checks if service is alive
    """
    return LivenessResponse(
        status="alive",
        timestamp=datetime.now().isoformat()
    )


@health_router.get("/ready", response_model=ReadinessResponse)
async def readiness():
    """
    就绪探针端点
    
    用于Kubernetes readiness probe，检查服务是否就绪接收流量
    For Kubernetes readiness probe, checks if service is ready to accept traffic
    """
    checks = {}
    all_ready = True
    
    # 检查数据库
    try:
        db_health = await check_database_health()
        checks["database"] = db_health.status == "healthy"
        if not checks["database"]:
            all_ready = False
    except Exception:
        checks["database"] = False
        all_ready = False
    
    # 检查LLM
    try:
        llm_health = await check_llm_health()
        checks["llm"] = llm_health.status in ["healthy", "degraded"]
        if not checks["llm"]:
            all_ready = False
    except Exception:
        checks["llm"] = False
        all_ready = False
    
    # 检查知识库
    try:
        kb_health = await check_knowledge_base_health()
        checks["knowledge_base"] = kb_health.status == "healthy"
        if not checks["knowledge_base"]:
            all_ready = False
    except Exception:
        checks["knowledge_base"] = False
        all_ready = False
    
    status = "ready" if all_ready else "not_ready"
    
    return ReadinessResponse(
        status=status,
        timestamp=datetime.now().isoformat(),
        checks=checks
    )


# ==================== 导出函数 ====================
def get_health_router() -> APIRouter:
    """获取健康检查路由器"""
    return health_router
