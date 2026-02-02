#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全增强的多模态文件系统API
Secure Enhanced Multimodal File System API

集成安全验证、权限控制、性能监控等功能
"""

import sys
from core.async_main import async_main
import os
from pathlib import Path
from datetime import datetime
import asyncio
import json
import hashlib
import uuid
import time
from typing import Dict, List, Any, Optional
import logging
from core.logging_config import setup_logging

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Query, Header, Depends, status
from fastapi.middleware.cors import CORSMiddleware

from core.security.auth import ALLOWED_ORIGINS
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, Field
import uvicorn
import aiofiles
from PIL import Image
import io

# 导入安全模块
from security.auth_manager import auth_manager, file_validator, permission_manager
from cache_manager import cache_manager, FileCacheManager
from base_settings_manager import get_settings_manager
from monitoring.performance_monitor import performance_monitor, monitor_performance
from monitoring.metrics_collector import metrics_collector
from batch.batch_operations import batch_operation_manager, BatchOperationStatus
from storage.distributed_storage import distributed_storage, StorageType, StorageTier
from storage.storage_policy import storage_policy_manager
from version.file_version_manager import file_version_manager, ChangeType
from ai.ai_processor import ai_processor, ProcessingType, ProcessingStatus

# 日志配置
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title="Athena安全增强多模态文件系统API",
    description="集成安全验证、权限控制、性能监控的多模态文件处理平台",
    version="2.2.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 安全依赖
security = HTTPBearer()

# 配置管理器
settings_manager = get_settings_manager()

# API响应模型
class UploadResponse(BaseModel):
    success: bool
    message: str
    file_id: str | None = None
    filename: str | None = None
    file_type: str | None = None
    file_size: int | None = None
    security_score: Optional[float] = Field(None, description="安全评分 0-100")
    security_warnings: List[str] = Field(default_factory=list)
    upload_time: str | None = None

class UserInfo(BaseModel):
    user_id: str
    role: str
    name: str | None = None
    permissions: List[str] = Field(default_factory=list)

class FileResponseModel(BaseModel):
    success: bool
    message: str
    file_info: Optional[Dict[str, Any]] = None
    permissions: List[str] = Field(default_factory=list)

class SearchResponse(BaseModel):
    success: bool
    message: str
    total_count: int
    files: List[Dict[str, Any]]
    permissions: List[str] = Field(default_factory=list)
    took_seconds: float | None = None

class StatsResponse(BaseModel):
    success: bool
    stats: Dict[str, Any]
    security_stats: Dict[str, Any]
    performance_stats: Dict[str, Any]

# 性能监控
class PerformanceMonitor:
    def __init__(self):
        self.request_count = 0
        self.total_response_time = 0
        self.error_count = 0
        self.start_time = time.time()

    def log_request(self, endpoint: str, response_time: float, error: bool = False) -> Any:
        """记录请求"""
        self.request_count += 1
        self.total_response_time += response_time
        if error:
            self.error_count += 1

        # 记录到缓存
        cache_key = f"perf:{endpoint}:{int(time.time())}"
        cache_manager.set(cache_key, {
            "request_count": self.request_count,
            "total_response_time": self.total_response_time,
            "error_count": self.error_count,
            "avg_response_time": self.total_response_time / self.request_count if self.request_count > 0 else 0
        }, timeout=300)  # 5分钟缓存

    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        uptime = time.time() - self.start_time
        return {
            "uptime_seconds": uptime,
            "request_count": self.request_count,
            "total_response_time": self.total_response_time,
            "avg_response_time": self.total_response_time / self.request_count if self.request_count > 0 else 0,
            "error_count": self.error_count,
            "error_rate": self.error_count / self.request_count if self.request_count > 0 else 0,
            "requests_per_second": self.request_count / uptime if uptime > 0 else 0
        }

# 全局性能监控器
perf_monitor = PerformanceMonitor()

# 认证依赖
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = auth_manager.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌"
        )

    user_info = UserInfo(
        user_id=payload["user_id"],
        role=payload["user_data"].get("role", "guest"),
        name=payload["user_data"].get("name"),
        permissions=payload["user_data"].get("permissions", permission_manager.role_permissions.get(payload["user_data"].get("role", "guest"), []))
    )

    return user_info

def require_permission(permission: str) -> Any:
    """权限装饰器"""
    def decorator(func) -> None:
        async def wrapper(*args, **kwargs):
            user_info = kwargs.get("user_info")
            if not user_info or not permission_manager.has_permission(user_info.role, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足，需要权限: {permission}"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 增强的存储管理器
class SecureStorageManager:
    def __init__(self):
        self.storage_root = Path(settings_manager.get_setting("storage.base_path"))
        self.metadata_root = Path("/Users/xujian/Athena工作平台/storage-system/data/multimodal_metadata")
        self.thumbnail_root = Path("/Users/xujian/Athena工作平台/storage-system/data/thumbnails")

        # 确保目录存在
        for path in [self.storage_root, self.metadata_root, self.thumbnail_root]:
            path.mkdir(parents=True, exist_ok=True)

    async def save_file_secure(self, file_content: bytes, filename: str,
                           user_info: UserInfo, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """安全保存文件"""
        try:
            start_time = time.time()

            # 1. 文件类型验证
            content_type = mimetypes.guess_type(filename)
            type_result = file_validator.validate_file_type(filename, content_type)
            if not type_result["valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"文件类型验证失败: {'; '.join(type_result['warnings'])}"
                )

            # 2. 文件大小验证
            size_result = file_validator.validate_file_size(len(file_content))
            if not size_result["valid"]:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"文件大小验证失败: {'; '.join(size_result['warnings'])}"
                )

            # 3. 内容安全扫描
            file_hash = hashlib.sha256(file_content).hexdigest()
            scan_result = file_validator.scan_file_content(file_content, filename)

            # 缓存扫描结果
            if not file_validator.is_file_scanned(file_hash):
                file_validator.mark_file_scanned(file_hash, scan_result)

            # 计算安全评分
            security_score = 100
            security_warnings = []

            if not scan_result["safe"]:
                security_score -= 50
                security_warnings.extend(scan_result["warnings"])
                security_warnings.extend(type_result["warnings"])

            if not type_result["valid"]:
                security_score -= 30
                security_warnings.extend(type_result["warnings"])

            # 4. 保存文件（复用之前的逻辑）
            file_type = settings_manager.is_file_allowed(filename)
            if not file_type:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"不支持的文件类型"
                )

            # 生成唯一文件名
            file_ext = Path(filename).suffix
            stored_name = f"{uuid.uuid4()}{file_ext}"

            # 创建用户目录
            user_dir = self.storage_root / user_info.user_id
            user_dir.mkdir(parents=True, exist_ok=True)

            # 创建类型目录
            date_dir = datetime.now().strftime('%Y/%m')
            type_dir = user_dir / file_type / date_dir
            type_dir.mkdir(parents=True, exist_ok=True)

            # 保存文件
            file_path = type_dir / stored_name
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)

            # 生成缩略图
            thumbnail_url = None
            if file_type == 'image' and scan_result["safe"]:
                thumbnail_name = f"{stored_name}_thumb.jpg"
                thumbnail_path = self.thumbnail_root / thumbnail_name
                try:
                    with Image.open(io.BytesIO(file_content)) as img:
                        img.thumbnail((200, 200))
                        img.save(thumbnail_path)
                    thumbnail_url = f"/thumbnails/{thumbnail_name}"
                except Exception as e:
                    logger.warning(f"生成缩略图失败: {e}")

            # 保存元数据
            file_id = str(uuid.uuid4())
            file_metadata = {
                "file_id": file_id,
                "original_name": filename,
                "stored_name": stored_name,
                "file_path": str(file_path),
                "file_type": file_type,
                "file_size": len(file_content),
                "file_hash": file_hash,
                "upload_time": datetime.now().isoformat(),
                "user_id": user_info.user_id,
                "user_role": user_info.role,
                "thumbnail_url": thumbnail_url,
                "security_score": security_score,
                "security_warnings": security_warnings,
                "scan_result": scan_result,
                "metadata": metadata or {}
            }

            metadata_file = self.metadata_root / f"{file_id}.json"
            async with aiofiles.open(metadata_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(file_metadata, ensure_ascii=False, indent=2))

            # 更新文件缓存
            FileCacheManager.cache_file_info(file_id, file_metadata)
            FileCacheManager.cache_search_results("", "", [])

            processing_time = time.time() - start_time
            logger.info(f"文件 {filename} 上传成功，处理时间: {processing_time:.3f}s")

            # 记录性能指标
            performance_monitor.record_file_operation(
                operation_type="upload",
                file_type=file_type,
                file_size=len(file_content),
                processing_time=processing_time,
                success=True,
                user_id=user_info.user_id
            )

            # 记录自定义指标
            metrics_collector.collect_metric(
                "file.upload.count",
                1,
                {"user_id": user_info.user_id, "file_type": file_type},
                "counter"
            )
            metrics_collector.collect_metric(
                "file.upload.size",
                len(file_content),
                {"user_id": user_info.user_id, "file_type": file_type},
                "gauge"
            )

            return {
                "success": True,
                "file_id": file_id,
                "filename": filename,
                "file_type": file_type,
                "file_size": len(file_content),
                "security_score": security_score,
                "security_warnings": security_warnings,
                "upload_time": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"安全保存文件失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"文件上传失败: {str(e)}"
            )

# 全局存储管理器
secure_storage = SecureStorageManager()

@app.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    metadata: str = Form("{}"),
    user_info: UserInfo = Depends(get_current_user)
):
    """安全上传文件"""
    try:
        start_time = time.time()

        # 读取文件内容
        file_content = await file.read()
        processing_start = time.time()

        # 解析元数据
        try:
            file_metadata = json.loads(metadata)
        except (json.JSONDecodeError, TypeError, ValueError):
            file_metadata = {}

        # 检查上传权限
        if not permission_manager.has_permission(user_info.role, "upload"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有上传权限"
            )

        # 安全保存文件
        result = await secure_storage.save_file_secure(
            file_content,
            file.filename,
            user_info,
            file_metadata
        )

        processing_time = time.time() - processing_start
        total_time = time.time() - start_time

        perf_monitor.log_request("upload", total_time, error=False)

        return UploadResponse(
            success=True,
            message="文件上传成功",
            file_id=result.get("file_id"),
            filename=result.get("filename"),
            file_type=result.get("file_type"),
            file_size=result.get("file_size"),
            security_score=result.get("security_score"),
            security_warnings=result.get("security_warnings"),
            upload_time=result.get("upload_time")
        )

    except HTTPException:
        perf_monitor.log_request("upload", time.time() - start_time, error=True)
        raise
    except Exception as e:
        logger.error(f"上传文件异常: {e}")
        perf_monitor.log_request("upload", time.time() - start_time, error=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传失败: {str(e)}"
        )

@app.get("/download/{file_id}")
async def download_file(
    file_id: str,
    user_info: UserInfo = Depends(get_current_user)
):
    """安全下载文件"""
    try:
        start_time = time.time()

        # 获取文件信息
        file_info = await secure_storage.get_file_info(file_id)
        if not file_info:
            raise HTTPException(status_code=404, detail="文件不存在")

        # 检查下载权限
        access_check = permission_manager.check_file_access(
            user_info.user_id, file_id, "download", file_info
        )
        if not access_check["allowed"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"无权限下载此文件: {access_check.get('reason', '权限不足')}"
            )

        # 检查安全状态
        if file_info.get("security_score", 100) < 50:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="文件安全评分过低，禁止下载"
            )

        file_path = file_info.get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")

        original_name = file_info.get("original_name", "download")

        perf_monitor.log_request("download", time.time() - start_time, error=False)

        return FileResponse(
            path=file_path,
            filename=original_name,
            media_type='application/octet-stream'
        )

    except HTTPException:
        perf_monitor.log_request("download", time.time() - start_time, error=True)
        raise
    except Exception as e:
        logger.error(f"下载文件异常: {e}")
        perf_monitor.log_request("download", time.time() - start_time, error=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载失败: {str(e)}"
        )

@app.get("/search", response_model=SearchResponse)
async def search_files(
    query: str = Query(None, description="搜索关键词"),
    file_type: str = Query(None, description="文件类型"),
    limit: int = Query(20, ge=1, le=100, description="结果数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    user_info: UserInfo = Depends(get_current_user)
):
    """搜索文件"""
    try:
        start_time = time.time()

        # 检查搜索权限
        if not permission_manager.has_permission(user_info.role, "read"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有搜索权限"
            )

        # 执行搜索
        results = await secure_storage.search_files(
            query=query,
            file_type=file_type,
            limit=limit,
            offset=offset
        )

        # 过滤用户可访问的文件
        filtered_results = []
        for result in results:
            access_check = permission_manager.check_file_access(
                user_info.user_id, result.get("file_id"), "read", result
            )
            if access_check["allowed"]:
                filtered_results.append(result)

        file_infos = []
        for result in filtered_results:
            file_infos.append({
                "file_id": result.get("file_id"),
                "filename": result.get("original_name"),
                "file_type": result.get("file_type"),
                "file_size": result.get("file_size"),
                "upload_time": result.get("upload_time"),
                "file_hash": result.get("file_hash"),
                "thumbnail_url": result.get("thumbnail_url"),
                "metadata": result.get("metadata", {}),
                "security_score": result.get("security_score", 100),
                "user_id": result.get("user_id", "unknown"),
                "permissions": permission_manager.role_permissions.get(user_info.role, [])
            })

        total_time = time.time() - start_time

        perf_monitor.log_request("search", total_time, error=False)

        return SearchResponse(
            success=True,
            message="搜索完成",
            total_count=len(file_infos),
            files=file_infos,
            permissions=user_info.permissions,
            took_seconds=total_time
        )

    except HTTPException:
        perf_monitor.log_request("search", time.time() - start_time, error=True)
        raise
    except Exception as e:
        logger.error(f"搜索文件异常: {e}")
        perf_monitor.log_request("search", time.time() - start_time, error=True)
        return SearchResponse(
            success=False,
            message=f"搜索失败: {str(e)}",
            total_count=0,
            files=[],
            permissions=user_info.permissions,
            took_seconds=time.time() - start_time
        )

@app.get("/stats", response_model=StatsResponse)
async def get_stats(user_info: UserInfo = Depends(get_current_user)):
    """获取系统统计信息"""
    try:
        # 检查管理员权限
        if not permission_manager.has_permission(user_info.role, "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要管理员权限"
            )

        # 基础存储统计
        stats = {}

        # 按文件类型统计
        for file_type in settings_manager.get_setting("storage.allowed_types", {}).keys():
            type_results = await secure_storage.search_files(file_type=file_type, limit=1000)
            user_filtered_results = [
                r for r in type_results
                if permission_manager.check_file_access(
                    user_info.user_id, r.get("file_id"), "read", r
                ).get("allowed")
            ]
            stats[file_type] = {
                "count": len(user_filtered_results),
                "total_size": sum(r.get("file_size", 0) for r in user_filtered_results),
                "avg_security_score": sum(r.get("security_score", 100) for r in user_filtered_results) / len(user_filtered_results) if user_filtered_results else 100
            }

        # 总体统计
        all_results = await secure_storage.search_files(limit=10000)
        user_filtered_results = [
            r for r in all_results
            if permission_manager.check_file_access(
                user_info.user_id, r.get("file_id"), "read", r
            ).get("allowed")
        ]
        stats["total"] = {
            "count": len(user_filtered_results),
            "total_size": sum(r.get("file_size", 0) for r in user_filtered_results),
            "avg_security_score": sum(r.get("security_score", 100) for r in user_filtered_results) / len(user_filtered_results) if user_filtered_results else 100
        }

        # 性能统计
        performance_stats = perf_monitor.get_stats()

        # 安全统计
        security_stats = {
            "total_files_scanned": len(file_validator.scanned_files_cache),
            "safe_files": sum(1 for r in file_validator.scanned_files_cache.values() if r.get("result", {}).get("safe", False) == True),
            "dangerous_files": sum(1 for r in file_validator.scanned_files_cache.values() if r.get("result", {}).get("safe", False) == False),
            "blocked_uploads": 0  # 可以从错误日志统计
        }

        return StatsResponse(
            success=True,
            stats=stats,
            security_stats=security_stats,
            performance_stats=performance_stats
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取统计信息异常: {e}")
        return StatsResponse(
            success=False,
            stats={},
            security_stats={},
            performance_stats={}
        )

@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 系统状态
        stats = settings_manager.get_service_status()

        # 缓存状态
        cache_stats = cache_manager.get_stats()

        # 性能监控
        perf_stats = perf_monitor.get_stats()

        # 安全状态
        security_stats = {
            "auth_enabled": True,
            "file_validation_enabled": True,
            "scan_enabled": True
        }

        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": settings_manager.get_setting("version"),
            "uptime": perf_stats.get("uptime_seconds", 0),
            "system_stats": stats,
            "cache_stats": cache_stats,
            "performance_stats": perf_stats,
            "security_stats": security_stats
        }

        return JSONResponse(content=health_data)

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

# ========== 性能监控API端点 ==========

@app.get("/monitoring/dashboard")
@monitor_performance("/monitoring/dashboard", "GET")
async def get_monitoring_dashboard(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取监控仪表板数据"""
    try:
        # 验证令牌
        payload = auth_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="无效的访问令牌")

        dashboard_data = performance_monitor.get_dashboard_data()

        return JSONResponse(content={
            "success": True,
            "dashboard": dashboard_data
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取监控仪表板失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/monitoring/metrics")
@monitor_performance("/monitoring/metrics", "GET")
async def get_metrics_summary(
    metric_name: Optional[str] = Query(None, description="指标名称"),
    hours: int = Query(1, description="时间范围(小时)", ge=1, le=168),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """获取指标摘要"""
    try:
        # 验证令牌
        payload = auth_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="无效的访问令牌")

        if metric_name:
            # 获取特定指标摘要
            summary = metrics_collector.get_metric_summary(metric_name, hours)
            return JSONResponse(content={
                "success": True,
                "metric_summary": summary
            })
        else:
            # 获取系统概览
            overview = metrics_collector.get_system_overview()
            return JSONResponse(content={
                "success": True,
                "system_overview": overview
            })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取指标摘要失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/monitoring/metrics/export")
@monitor_performance("/monitoring/metrics/export", "GET")
async def export_metrics(
    metric_names: Optional[str] = Query(None, description="指标名称列表(逗号分隔)"),
    hours: int = Query(24, description="时间范围(小时)", ge=1, le=168),
    format: str = Query("json", description="导出格式", regex="^(json|csv)$"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """导出指标数据"""
    try:
        # 验证令牌
        payload = auth_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="无效的访问令牌")

        # 解析指标名称
        names = metric_names.split(',') if metric_names else None

        # 计算时间范围
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        # 导出数据
        export_data = metrics_collector.export_metrics(names, start_time, end_time, format)

        # 设置响应头
        if format == 'json':
            return JSONResponse(
                content=json.loads(export_data),
                headers={
                    "Content-Disposition": f"attachment; filename=metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                }
            )
        else:
            return JSONResponse(
                content={"data": export_data},
                headers={
                    "Content-Type": "text/csv",
                    "Content-Disposition": f"attachment; filename=metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出指标数据失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/monitoring/alerts")
@monitor_performance("/monitoring/alerts", "GET")
async def get_monitoring_alerts(
    level: Optional[str] = Query(None, description="告警级别", regex="^(warning|critical)$"),
    hours: int = Query(24, description="时间范围(小时)", ge=1, le=168),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """获取监控告警"""
    try:
        # 验证令牌
        payload = auth_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="无效的访问令牌")

        alerts = performance_monitor.system_monitor.get_alerts(level, hours)

        return JSONResponse(content={
            "success": True,
            "alerts": [
                {
                    "level": alert["level"],
                    "type": alert["type"],
                    "message": alert["message"],
                    "timestamp": alert["timestamp"].isoformat()
                }
                for alert in alerts
            ],
            "count": len(alerts)
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取监控告警失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/monitoring/metrics/custom")
@monitor_performance("/monitoring/metrics/custom", "POST")
async def add_custom_metric(
    metric_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """添加自定义指标"""
    try:
        # 验证令牌
        payload = auth_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="无效的访问令牌")

        # 提取指标数据
        metric_name = metric_data.get("name")
        value = metric_data.get("value")
        tags = metric_data.get("tags", {})
        metric_type = metric_data.get("type", "gauge")

        if not metric_name or value is None:
            raise HTTPException(status_code=400, detail="缺少必要参数: name, value")

        # 记录指标
        metrics_collector.collect_metric(metric_name, float(value), tags, metric_type)
        performance_monitor.add_custom_metric(metric_name, float(value), tags)

        logger.info(f"用户 {payload['user_id']} 添加自定义指标: {metric_name}={value}")

        return JSONResponse(content={
            "success": True,
            "message": "自定义指标已添加",
            "metric": {
                "name": metric_name,
                "value": value,
                "tags": tags,
                "type": metric_type,
                "timestamp": datetime.now().isoformat()
            }
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加自定义指标失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/monitoring/performance/api")
@monitor_performance("/monitoring/performance/api", "GET")
async def get_api_performance_stats(
    endpoint: Optional[str] = Query(None, description="API端点"),
    minutes: int = Query(60, description="时间范围(分钟)", ge=5, le=1440),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """获取API性能统计"""
    try:
        # 验证令牌
        payload = auth_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="无效的访问令牌")

        # 获取API调用统计
        stats = performance_monitor.api_tracker.get_stats(minutes * 60)

        # 如果指定了端点，获取特定端点的详细统计
        if endpoint:
            endpoint_calls = performance_monitor.api_tracker.endpoints.get(endpoint, [])
            if endpoint_calls:
                recent_calls = [
                    call for call in endpoint_calls
                    if call['timestamp'] > datetime.now() - timedelta(minutes=minutes)
                ]

                response_times = [call['response_time'] for call in recent_calls]
                status_codes = defaultdict(int)
                for call in recent_calls:
                    status_codes[call['status_code']] += 1

                endpoint_stats = {
                    "endpoint": endpoint,
                    "total_calls": len(recent_calls),
                    "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
                    "min_response_time": min(response_times) if response_times else 0,
                    "max_response_time": max(response_times) if response_times else 0,
                    "success_rate": sum(1 for code in status_codes if 200 <= code < 300) / len(recent_calls) * 100 if recent_calls else 0,
                    "status_distribution": dict(status_codes),
                    "recent_calls": [
                        {
                            "timestamp": call['timestamp'].isoformat(),
                            "response_time": call['response_time'],
                            "status_code": call['status_code'],
                            "user_id": call.get('user_id')
                        }
                        for call in recent_calls[-20:]  # 最近20次调用
                    ]
                }

                return JSONResponse(content={
                    "success": True,
                    "endpoint_stats": endpoint_stats
                })

        return JSONResponse(content={
            "success": True,
            "api_stats": stats
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取API性能统计失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/monitoring/performance/files")
@monitor_performance("/monitoring/performance/files", "GET")
async def get_file_processing_stats(
    file_type: Optional[str] = Query(None, description="文件类型"),
    operation: Optional[str] = Query(None, description="操作类型"),
    hours: int = Query(24, description="时间范围(小时)", ge=1, le=168),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """获取文件处理统计"""
    try:
        # 验证令牌
        payload = auth_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="无效的访问令牌")

        # 获取文件处理统计
        stats = performance_monitor.file_tracker.get_stats(hours * 3600)

        # 如果指定了文件类型或操作类型，进行过滤
        if file_type or operation:
            filtered_operations = [
                op for op in performance_monitor.file_tracker.operations
                if (not file_type or op['file_type'] == file_type) and
                   (not operation or op['operation_type'] == operation) and
                   op['timestamp'] > datetime.now() - timedelta(hours=hours)
            ]

            if filtered_operations:
                processing_times = [op['processing_time'] for op in filtered_operations]
                success_count = sum(1 for op in filtered_operations if op['success'])
                total_size = sum(op['file_size'] for op in filtered_operations)

                detailed_stats = {
                    "filters": {
                        "file_type": file_type,
                        "operation": operation,
                        "hours": hours
                    },
                    "total_operations": len(filtered_operations),
                    "success_rate": success_count / len(filtered_operations) * 100,
                    "avg_processing_time": sum(processing_times) / len(processing_times),
                    "total_bytes_processed": total_size,
                    "processing_speed": total_size / sum(processing_times) if sum(processing_times) > 0 else 0,
                    "recent_operations": [
                        {
                            "timestamp": op['timestamp'].isoformat(),
                            "operation_type": op['operation_type'],
                            "file_type": op['file_type'],
                            "file_size": op['file_size'],
                            "processing_time": op['processing_time'],
                            "success": op['success'],
                            "user_id": op.get('user_id')
                        }
                        for op in filtered_operations[-20:]  # 最近20次操作
                    ]
                }

                return JSONResponse(content={
                    "success": True,
                    "detailed_stats": detailed_stats
                })

        return JSONResponse(content={
            "success": True,
            "file_stats": stats
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件处理统计失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# ========== 批量操作API端点 ==========

class BatchOperationRequest(BaseModel):
    """批量操作请求"""
    operation_type: str = Field(..., description="操作类型: upload, download, process, analyze, delete")
    files: List[Dict[str, Any]] = Field(..., description="文件列表")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="配置参数")

class BatchOperationResponse(BaseModel):
    """批量操作响应"""
    success: bool
    operation_id: str | None = None
    message: str
    total_files: int = 0
    estimated_duration: float | None = None

@app.post("/batch/operations", response_model=BatchOperationResponse)
@monitor_performance("/batch/operations", "POST")
async def create_batch_operation(
    request: BatchOperationRequest,
    user_info: UserInfo = Depends(get_current_user)
):
    """创建批量操作"""
    try:
        # 验证操作类型
        valid_types = ["upload", "download", "process", "analyze", "delete"]
        if request.operation_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的操作类型: {request.operation_type}"
            )

        # 验证文件数量
        max_batch_size = settings_manager.get_setting("api.max_batch_size", 100)
        if len(request.files) > max_batch_size:
            raise HTTPException(
                status_code=400,
                detail=f"批量操作文件数量超出限制: {len(request.files)} > {max_batch_size}"
            )

        # 创建批量操作
        operation_id = await batch_operation_manager.create_batch_operation(
            operation_type=request.operation_type,
            user_id=user_info.user_id,
            files=request.files,
            config=request.config
        )

        # 估算执行时间
        estimated_duration = len(request.files) * 2.0  # 每个文件估算2秒

        logger.info(f"用户 {user_info.user_id} 创建批量操作: {operation_id} - {request.operation_type} ({len(request.files)} 个文件)")

        return JSONResponse(content={
            "success": True,
            "operation_id": operation_id,
            "message": "批量操作已创建",
            "total_files": len(request.files),
            "estimated_duration": estimated_duration
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建批量操作失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/batch/operations/{operation_id}")
@monitor_performance("/batch/operations/{operation_id}", "GET")
async def get_batch_operation_status(
    operation_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """获取批量操作状态"""
    try:
        # 验证令牌
        payload = auth_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="无效的访问令牌")

        operation = batch_operation_manager.get_operation_status(operation_id)
        if not operation:
            raise HTTPException(status_code=404, detail="操作不存在")

        return JSONResponse(content={
            "success": True,
            "operation": {
                "operation_id": operation.operation_id,
                "operation_type": operation.operation_type,
                "status": operation.status.value,
                "progress": operation.progress,
                "total_files": operation.total_files,
                "processed_files": operation.processed_files,
                "successful_files": operation.successful_files,
                "failed_files": operation.failed_files,
                "created_at": operation.created_at.isoformat(),
                "started_at": operation.started_at.isoformat() if operation.started_at else None,
                "completed_at": operation.completed_at.isoformat() if operation.completed_at else None,
                "error_message": operation.error_message,
                "config": operation.config
            }
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取批量操作状态失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/batch/operations")
@monitor_performance("/batch/operations", "GET")
async def get_user_batch_operations(
    status: Optional[str] = Query(None, description="状态过滤"),
    limit: int = Query(50, description="返回数量限制", ge=1, le=1000),
    user_info: UserInfo = Depends(get_current_user)
):
    """获取用户的批量操作列表"""
    try:
        # 状态过滤
        status_filter = None
        if status:
            try:
                status_filter = BatchOperationStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的状态: {status}")

        # 获取操作列表
        operations = batch_operation_manager.get_user_operations(
            user_id=user_info.user_id,
            status=status_filter
        )

        # 限制返回数量
        operations = operations[:limit]

        return JSONResponse(content={
            "success": True,
            "total_count": len(operations),
            "operations": [
                {
                    "operation_id": op.operation_id,
                    "operation_type": op.operation_type,
                    "status": op.status.value,
                    "progress": op.progress,
                    "total_files": op.total_files,
                    "processed_files": op.processed_files,
                    "successful_files": op.successful_files,
                    "failed_files": op.failed_files,
                    "created_at": op.created_at.isoformat(),
                    "completed_at": op.completed_at.isoformat() if op.completed_at else None
                }
                for op in operations
            ]
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取批量操作列表失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/batch/operations/{operation_id}/cancel")
@monitor_performance("/batch/operations/{operation_id}/cancel", "POST")
async def cancel_batch_operation(
    operation_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """取消批量操作"""
    try:
        # 验证令牌
        payload = auth_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="无效的访问令牌")

        # 检查操作是否存在
        operation = batch_operation_manager.get_operation_status(operation_id)
        if not operation:
            raise HTTPException(status_code=404, detail="操作不存在")

        # 检查权限
        if operation.user_id != payload["user_id"] and payload["user_data"].get("role") != "admin":
            raise HTTPException(status_code=403, detail="无权限取消此操作")

        # 取消操作
        success = await batch_operation_manager.cancel_operation(operation_id)

        if success:
            logger.info(f"用户 {payload['user_id']} 取消批量操作: {operation_id}")
            return JSONResponse(content={
                "success": True,
                "message": "操作已取消"
            })
        else:
            return JSONResponse(content={
                "success": False,
                "message": "无法取消操作（可能已完成或正在执行）"
            })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消批量操作失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/batch/operations/{operation_id}/results")
@monitor_performance("/batch/operations/{operation_id}/results", "GET")
async def get_batch_operation_results(
    operation_id: str,
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(20, description="每页大小", ge=1, le=100),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """获取批量操作结果"""
    try:
        # 验证令牌
        payload = auth_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="无效的访问令牌")

        # 检查操作是否存在
        operation = batch_operation_manager.get_operation_status(operation_id)
        if not operation:
            raise HTTPException(status_code=404, detail="操作不存在")

        # 检查权限
        if operation.user_id != payload["user_id"] and payload["user_data"].get("role") != "admin":
            raise HTTPException(status_code=403, detail="无权限查看此操作结果")

        # 分页获取结果
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        page_results = operation.results[start_index:end_index]

        return JSONResponse(content={
            "success": True,
            "operation_id": operation_id,
            "total_results": len(operation.results),
            "page": page,
            "page_size": page_size,
            "total_pages": (len(operation.results) + page_size - 1) // page_size,
            "results": page_results,
            "summary": {
                "successful_files": operation.successful_files,
                "failed_files": operation.failed_files,
                "success_rate": operation.successful_files / operation.total_files * 100 if operation.total_files > 0 else 0
            }
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取批量操作结果失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/batch/upload")
@monitor_performance("/batch/upload", "POST")
async def batch_upload_files(
    files: List[UploadFile] = File(...),
    metadata: str = Form("{}"),
    user_info: UserInfo = Depends(get_current_user)
):
    """批量上传文件"""
    try:
        start_time = time.time()

        # 限制批量上传数量
        max_batch_size = settings_manager.get_setting("api.max_batch_upload", 20)
        if len(files) > max_batch_size:
            raise HTTPException(
                status_code=400,
                detail=f"批量上传文件数量超出限制: {len(files)} > {max_batch_size}"
            )

        # 解析元数据
        try:
            metadata_dict = json.loads(metadata)
        except (json.JSONDecodeError, TypeError, ValueError):
            metadata_dict = {}

        # 准备文件数据
        file_data = []
        for file in files:
            content = await file.read()
            file_data.append({
                "filename": file.filename,
                "content": content,
                "content_type": file.content_type,
                "metadata": metadata_dict.get(file.filename, {})
            })

        # 创建批量上传操作
        operation_id = await batch_operation_manager.create_batch_operation(
            operation_type="upload",
            user_id=user_info.user_id,
            files=file_data,
            config={"batch_upload": True}
        )

        processing_time = time.time() - start_time

        logger.info(f"用户 {user_info.user_id} 批量上传 {len(files)} 个文件，操作ID: {operation_id}")

        return JSONResponse(content={
            "success": True,
            "operation_id": operation_id,
            "message": "批量上传已开始",
            "total_files": len(files),
            "processing_time": processing_time
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量上传失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/batch/statistics")
@monitor_performance("/batch/statistics", "GET")
async def get_batch_statistics(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """获取批量操作统计"""
    try:
        # 验证令牌
        payload = auth_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="无效的访问令牌")

        # 获取系统统计
        system_stats = batch_operation_manager.get_statistics()

        # 获取用户统计
        user_operations = batch_operation_manager.get_user_operations(payload["user_id"])
        user_stats = {
            "total_operations": len(user_operations),
            "active_operations": len([op for op in user_operations if op.status == BatchOperationStatus.RUNNING]),
            "completed_operations": len([op for op in user_operations if op.status == BatchOperationStatus.COMPLETED]),
            "failed_operations": len([op for op in user_operations if op.status == BatchOperationStatus.FAILED]),
            "total_files_processed": sum(op.total_files for op in user_operations)
        }

        return JSONResponse(content={
            "success": True,
            "system_statistics": system_stats,
            "user_statistics": user_stats
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取批量操作统计失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# ========== 分布式存储API端点 ==========

@app.post("/storage/configure")
@monitor_performance("/storage/configure", "POST")
async def configure_distributed_storage(
    config: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """配置分布式存储"""
    try:
        # 验证令牌
        payload = auth_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="无效的访问令牌")

        # 检查权限
        if payload["user_data"].get("role") != "admin":
            raise HTTPException(status_code=403, detail="需要管理员权限")

        from storage.distributed_storage import StorageConfig

        storage_type = StorageType(config.get("storage_type"))
        storage_config = StorageConfig(
            storage_type=storage_type,
            tier=StorageTier(config.get("tier", "hot")),
            access_key=config.get("access_key"),
            secret_key=config.get("secret_key"),
            region=config.get("region"),
            bucket_name=config.get("bucket_name"),
            endpoint=config.get("endpoint"),
            base_path=config.get("base_path"),
            max_file_size=config.get("max_file_size", 100 * 1024 * 1024),
            retention_days=config.get("retention_days", 30)
        )

        distributed_storage.add_storage_config(storage_config)

        logger.info(f"管理员 {payload['user_id']} 配置分布式存储: {storage_type.value}")

        return JSONResponse(content={
            "success": True,
            "message": f"分布式存储配置成功: {storage_type.value}"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"配置分布式存储失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/storage/stats")
@monitor_performance("/storage/stats", "GET")
async def get_storage_statistics(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """获取存储统计信息"""
    try:
        # 验证令牌
        payload = auth_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="无效的访问令牌")

        # 获取分布式存储统计
        storage_stats = distributed_storage.get_storage_stats()

        # 获取存储策略统计
        policies = {
            policy_id: storage_policy_manager.get_policy_summary(policy_id)
            for policy_id in storage_policy_manager.policies.keys()
        }

        return JSONResponse(content={
            "success": True,
            "distributed_storage": storage_stats,
            "storage_policies": policies,
            "total_policies": len(policies)
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取存储统计失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/storage/optimize")
@monitor_performance("/storage/optimize", "POST")
async def optimize_storage_layout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """优化存储布局"""
    try:
        # 验证令牌
        payload = auth_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="无效的访问令牌")

        # 检查权限
        if payload["user_data"].get("role") != "admin":
            raise HTTPException(status_code=403, detail="需要管理员权限")

        # 执行存储优化
        optimization_result = await distributed_storage.optimize_storage()

        logger.info(f"管理员 {payload['user_id']} 执行存储优化")

        return JSONResponse(content={
            "success": True,
            "optimization_result": optimization_result,
            "message": "存储优化完成"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"存储优化失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/storage/cleanup")
@monitor_performance("/storage/cleanup", "POST")
async def cleanup_expired_files(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """清理过期文件"""
    try:
        # 验证令牌
        payload = auth_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="无效的访问令牌")

        # 检查权限
        if payload["user_data"].get("role") != "admin":
            raise HTTPException(status_code=403, detail="需要管理员权限")

        # 执行清理
        deleted_count = await distributed_storage.cleanup_expired_files()

        logger.info(f"管理员 {payload['user_id']} 清理过期文件: {deleted_count} 个")

        return JSONResponse(content={
            "success": True,
            "deleted_files": deleted_count,
            "message": f"已清理 {deleted_count} 个过期文件"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清理过期文件失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/storage/policies")
@monitor_performance("/storage/policies", "POST")
async def create_storage_policy(
    policy_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """创建存储策略"""
    try:
        # 验证令牌
        payload = auth_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="无效的访问令牌")

        # 检查权限
        if payload["user_data"].get("role") != "admin":
            raise HTTPException(status_code=403, detail="需要管理员权限")

        from storage.storage_policy import StoragePolicy

        policy = StoragePolicy(
            policy_id=policy_data.get("policy_id"),
            name=policy_data.get("name"),
            description=policy_data.get("description"),
            default_tier=StorageTier(policy_data.get("default_tier", "hot")),
            replication_enabled=policy_data.get("replication_enabled", True),
            compression_enabled=policy_data.get("compression_enabled", False),
            encryption_enabled=policy_data.get("encryption_enabled", False),
            backup_enabled=policy_data.get("backup_enabled", True)
        )

        policy_id = storage_policy_manager.create_policy(policy)

        logger.info(f"管理员 {payload['user_id']} 创建存储策略: {policy.name}")

        return JSONResponse(content={
            "success": True,
            "policy_id": policy_id,
            "message": "存储策略创建成功"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建存储策略失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/storage/policies/{policy_id}")
@monitor_performance("/storage/policies/{policy_id}", "GET")
async def get_storage_policy(
    policy_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """获取存储策略详情"""
    try:
        # 验证令牌
        payload = auth_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="无效的访问令牌")

        policy = storage_policy_manager.get_policy(policy_id)
        if not policy:
            raise HTTPException(status_code=404, detail="存储策略不存在")

        # 序列化策略数据
        policy_data = {
            "policy_id": policy.policy_id,
            "name": policy.name,
            "description": policy.description,
            "default_tier": policy.default_tier.value,
            "replication_enabled": policy.replication_enabled,
            "compression_enabled": policy.compression_enabled,
            "encryption_enabled": policy.encryption_enabled,
            "backup_enabled": policy.backup_enabled,
            "lifecycle_rules": [
                {
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "description": rule.description,
                    "enabled": rule.enabled,
                    "priority": rule.priority,
                    "trigger_type": rule.trigger_type.value,
                    "trigger_value": rule.trigger_value,
                    "action": rule.action.value,
                    "target_tier": rule.target_tier.value if rule.target_tier else None
                }
                for rule in policy.lifecycle_rules
            ]
        }

        return JSONResponse(content={
            "success": True,
            "policy": policy_data
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取存储策略失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/storage/policies/{policy_id}/assign")
@monitor_performance("/storage/policies/{policy_id}/assign", "POST")
async def assign_storage_policy(
    policy_id: str,
    assignment_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """为文件分配存储策略"""
    try:
        # 验证令牌
        payload = auth_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="无效的访问令牌")

        file_id = assignment_data.get("file_id")
        if not file_id:
            raise HTTPException(status_code=400, detail="缺少文件ID")

        # 分配策略
        success = storage_policy_manager.assign_file_policy(
            file_id, policy_id,
            assignment_data.get("file_type"),
            assignment_data.get("file_size", 0)
        )

        if success:
            logger.info(f"用户 {payload['user_id']} 为文件 {file_id} 分配策略 {policy_id}")
            return JSONResponse(content={
                "success": True,
                "message": "存储策略分配成功"
            })
        else:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "存储策略分配失败"}
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分配存储策略失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/storage/policies/export")
@monitor_performance("/storage/policies/export", "GET")
async def export_storage_policies(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """导出存储策略配置"""
    try:
        # 验证令牌
        payload = auth_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="无效的访问令牌")

        # 导出策略
        policies_json = storage_policy_manager.export_policies()

        return JSONResponse(
            content=json.loads(policies_json),
            headers={
                "Content-Disposition": f"attachment; filename=storage_policies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出存储策略失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/storage/policies/import")
@monitor_performance("/storage/policies/import", "POST")
async def import_storage_policies(
    import_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """导入存储策略配置"""
    try:
        # 验证令牌
        payload = auth_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="无效的访问令牌")

        # 检查权限
        if payload["user_data"].get("role") != "admin":
            raise HTTPException(status_code=403, detail="需要管理员权限")

        policies_json = json.dumps(import_data.get("policies", {}))
        merge = import_data.get("merge", False)

        success = storage_policy_manager.import_policies(policies_json, merge)

        if success:
            logger.info(f"管理员 {payload['user_id']} 导入存储策略配置")
            return JSONResponse(content={
                "success": True,
                "message": "存储策略导入成功"
            })
        else:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "存储策略导入失败"}
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导入存储策略失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# ========== 文件版本管理API端点 ==========

@app.post("/files/{file_id}/versions")
@monitor_performance("/files/{file_id}/versions", "POST")
async def create_file_version(
    file_id: str,
    file: UploadFile = File(...),
    change_type: str = Form("update"),
    parent_version_id: Optional[str] = Form(None),
    branch_name: Optional[str] = Form(None),
    comment: Optional[str] = Form(None),
    user_info: UserInfo = Depends(get_current_user)
):
    """创建文件版本"""
    try:
        # 验证变更类型
        try:
            change_enum = ChangeType(change_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的变更类型: {change_type}")

        # 读取文件内容
        file_content = await file.read()

        # 创建版本
        version = await file_version_manager.create_version(
            file_id=file_id,
            file_content=file_content,
            file_name=file.filename,
            user_id=user_info.user_id,
            change_type=change_enum,
            parent_version_id=parent_version_id,
            branch_name=branch_name,
            comment=comment
        )

        logger.info(f"用户 {user_info.user_id} 创建文件版本: {file_id} v{version.version_number}")

        return JSONResponse(content={
            "success": True,
            "version": {
                "version_id": version.version_id,
                "version_number": version.version_number,
                "change_type": version.change_type.value,
                "created_at": version.created_at.isoformat(),
                "file_size": version.file_size,
                "file_hash": version.file_hash,
                "comment": version.comment
            }
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建文件版本失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/files/{file_id}/versions")
@monitor_performance("/files/{file_id}/versions", "GET")
async def get_file_versions(
    file_id: str,
    limit: int = Query(20, description="返回版本数量限制", ge=1, le=100),
    user_info: UserInfo = Depends(get_current_user)
):
    """获取文件的所有版本"""
    try:
        versions = await file_version_manager.get_file_versions(file_id, limit)

        return JSONResponse(content={
            "success": True,
            "file_id": file_id,
            "total_versions": len(versions),
            "versions": [
                {
                    "version_id": v.version_id,
                    "version_number": v.version_number,
                    "change_type": v.change_type.value,
                    "created_at": v.created_at.isoformat(),
                    "created_by": v.created_by,
                    "file_name": v.file_name,
                    "file_size": v.file_size,
                    "file_hash": v.file_hash,
                    "comment": v.comment,
                    "branch": v.branch_name
                }
                for v in versions
            ]
        })

    except Exception as e:
        logger.error(f"获取文件版本失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/files/{file_id}/versions/{version_id}")
@monitor_performance("/files/{file_id}/versions/{version_id}", "GET")
async def get_file_version(
    file_id: str,
    version_id: str,
    user_info: UserInfo = Depends(get_current_user)
):
    """获取特定版本信息"""
    try:
        version = await file_version_manager.get_version(version_id)
        if not version:
            raise HTTPException(status_code=404, detail="版本不存在")

        # 验证文件ID匹配
        if version.file_id != file_id:
            raise HTTPException(status_code=400, detail="版本与文件不匹配")

        return JSONResponse(content={
            "success": True,
            "version": {
                "version_id": version.version_id,
                "version_number": version.version_number,
                "change_type": version.change_type.value,
                "created_at": version.created_at.isoformat(),
                "created_by": version.created_by,
                "file_name": version.file_name,
                "file_path": version.file_path,
                "file_size": version.file_size,
                "file_hash": version.file_hash,
                "mime_type": version.mime_type,
                "metadata": version.metadata,
                "parent_version_id": version.parent_version_id,
                "branch_name": version.branch_name,
                "comment": version.comment,
                "tags": version.tags
            }
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件版本信息失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/files/{file_id}/versions/{version_id}/content")
@monitor_performance("/files/{file_id}/versions/{version_id}/content", "GET")
async def get_version_content(
    file_id: str,
    version_id: str,
    user_info: UserInfo = Depends(get_current_user)
):
    """获取版本文件内容"""
    try:
        # 验证版本存在
        version = await file_version_manager.get_version(version_id)
        if not version:
            raise HTTPException(status_code=404, detail="版本不存在")

        # 验证文件ID匹配
        if version.file_id != file_id:
            raise HTTPException(status_code=400, detail="版本与文件不匹配")

        # 获取文件内容
        content = await file_version_manager.get_version_content(version_id)

        # 返回文件
        return Response(
            content=content,
            media_type=version.mime_type or "application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={version.file_name}",
                "X-Version-ID": version_id,
                "X-Version-Number": str(version.version_number),
                "X-Created-At": version.created_at.isoformat()
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取版本文件内容失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/files/{file_id}/versions/{version_id1}/compare/{version_id2}")
@monitor_performance("/files/{file_id}/versions/{version_id1}/compare/{version_id2}", "GET")
async def compare_versions(
    file_id: str,
    version_id1: str,
    version_id2: str,
    user_info: UserInfo = Depends(get_current_user)
):
    """比较两个版本"""
    try:
        # 验证版本存在
        version1 = await file_version_manager.get_version(version_id1)
        version2 = await file_version_manager.get_version(version_id2)

        if not version1 or not version2:
            raise HTTPException(status_code=404, detail="版本不存在")

        # 验证文件ID匹配
        if version1.file_id != file_id or version2.file_id != file_id:
            raise HTTPException(status_code=400, detail="版本与文件不匹配")

        # 比较版本
        diff = await file_version_manager.compare_versions(version_id1, version_id2)

        return JSONResponse(content={
            "success": True,
            "comparison": {
                "old_version": {
                    "version_id": version1.version_id,
                    "version_number": version1.version_number,
                    "created_at": version1.created_at.isoformat()
                },
                "new_version": {
                    "version_id": version2.version_id,
                    "version_number": version2.version_number,
                    "created_at": version2.created_at.isoformat()
                },
                "diff_type": diff.diff_type,
                "summary": diff.summary,
                "changes": diff.changes
            }
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"比较版本失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/files/{file_id}/versions/{version_id}/revert")
@monitor_performance("/files/{file_id}/versions/{version_id}/revert", "POST")
async def revert_to_version(
    file_id: str,
    version_id: str,
    revert_data: Dict[str, Any] = None,
    user_info: UserInfo = Depends(get_current_user)
):
    """回滚到指定版本"""
    try:
        # 验证版本存在
        version = await file_version_manager.get_version(version_id)
        if not version:
            raise HTTPException(status_code=404, detail="版本不存在")

        # 验证文件ID匹配
        if version.file_id != file_id:
            raise HTTPException(status_code=400, detail="版本与文件不匹配")

        # 回滚版本
        revert_version = await file_version_manager.revert_to_version(
            file_id=file_id,
            target_version_id=version_id,
            user_id=user_info.user_id,
            comment=revert_data.get("comment") if revert_data else None
        )

        logger.info(f"用户 {user_info.user_id} 回滚文件 {file_id} 到版本 {version.version_number}")

        return JSONResponse(content={
            "success": True,
            "message": f"已回滚到版本 {version.version_number}",
            "revert_version": {
                "version_id": revert_version.version_id,
                "version_number": revert_version.version_number,
                "created_at": revert_version.created_at.isoformat(),
                "comment": revert_version.comment
            }
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"回滚版本失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/files/{file_id}/versions/branch")
@monitor_performance("/files/{file_id}/versions/branch", "POST")
async def create_version_branch(
    file_id: str,
    branch_data: Dict[str, Any],
    user_info: UserInfo = Depends(get_current_user)
):
    """创建版本分支"""
    try:
        branch_name = branch_data.get("branch_name")
        from_version_id = branch_data.get("from_version_id")

        if not branch_name or not from_version_id:
            raise HTTPException(status_code=400, detail="缺少必要参数: branch_name, from_version_id")

        # 创建分支
        branch_version = await file_version_manager.create_branch(
            file_id=file_id,
            branch_name=branch_name,
            from_version_id=from_version_id,
            user_id=user_info.user_id
        )

        logger.info(f"用户 {user_info.user_id} 创建版本分支: {branch_name}")

        return JSONResponse(content={
            "success": True,
            "message": f"已创建分支: {branch_name}",
            "branch_version": {
                "version_id": branch_version.version_id,
                "version_number": branch_version.version_number,
                "branch_name": branch_version.branch_name,
                "created_at": branch_version.created_at.isoformat()
            }
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建版本分支失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/files/{file_id}/history")
@monitor_performance("/files/{file_id}/history", "GET")
async def get_file_history(
    file_id: str,
    user_info: UserInfo = Depends(get_current_user)
):
    """获取文件完整历史"""
    try:
        history = await file_version_manager.get_file_history(file_id)

        return JSONResponse(content={
            "success": True,
            "history": history
        })

    except Exception as e:
        logger.error(f"获取文件历史失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.delete("/files/{file_id}/versions/{version_id}")
@monitor_performance("/files/{file_id}/versions/{version_id}", "DELETE")
async def delete_version(
    file_id: str,
    version_id: str,
    user_info: UserInfo = Depends(get_current_user)
):
    """删除文件版本"""
    try:
        # 验证版本存在
        version = await file_version_manager.get_version(version_id)
        if not version:
            raise HTTPException(status_code=404, detail="版本不存在")

        # 验证文件ID匹配
        if version.file_id != file_id:
            raise HTTPException(status_code=400, detail="版本与文件不匹配")

        # 检查权限（只有创建者或管理员可以删除）
        if version.created_by != user_info.user_id and user_info.role != "admin":
            raise HTTPException(status_code=403, detail="无权限删除此版本")

        # 删除版本
        success = await file_version_manager.delete_version(
            version_id=version_id,
            user_id=user_info.user_id
        )

        if success:
            logger.info(f"用户 {user_info.user_id} 删除版本: {version_id}")
            return JSONResponse(content={
                "success": True,
                "message": "版本已删除"
            })
        else:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "无法删除版本（可能存在依赖）"}
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除版本失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/version/statistics")
@monitor_performance("/version/statistics", "GET")
async def get_version_statistics(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """获取版本管理统计信息"""
    try:
        # 验证令牌
        payload = auth_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="无效的访问令牌")

        # 获取统计信息
        stats = file_version_manager.get_statistics()

        return JSONResponse(content={
            "success": True,
            "statistics": stats
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取版本统计失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/version/cleanup")
@monitor_performance("/version/cleanup", "POST")
async def cleanup_old_versions(
    cleanup_data: Dict[str, Any] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """清理旧版本"""
    try:
        # 验证令牌
        payload = auth_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="无效的访问令牌")

        # 检查权限
        if payload["user_data"].get("role") != "admin":
            raise HTTPException(status_code=403, detail="需要管理员权限")

        days = cleanup_data.get("days") if cleanup_data else None
        deleted_count = await file_version_manager.cleanup_old_versions(days)

        logger.info(f"管理员 {payload['user_id']} 清理旧版本: {deleted_count} 个")

        return JSONResponse(content={
            "success": True,
            "deleted_versions": deleted_count,
            "message": f"已清理 {deleted_count} 个旧版本"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清理旧版本失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# ========== AI处理API端点 ==========

@app.post("/ai/process")
@monitor_performance("/ai/process", "POST")
async def submit_ai_processing(
    file_id: str,
    processing_type: str,
    options: Dict[str, Any] = None,
    user_info: UserInfo = Depends(get_current_user)
):
    """提交AI处理任务"""
    try:
        # 验证处理类型
        try:
            proc_type = ProcessingType(processing_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的处理类型: {processing_type}"
            )

        # 获取文件路径（这里需要根据实际的存储实现来获取）
        file_path = f"/tmp/uploads/{file_id}"  # 简化实现

        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")

        # 提交处理任务
        task_id = await ai_processor.submit_processing_task(
            file_id=file_id,
            file_path=file_path,
            processing_type=proc_type,
            options=options
        )

        logger.info(f"用户 {user_info.user_id} 提交AI处理任务: {task_id}")

        return JSONResponse(content={
            "success": True,
            "task_id": task_id,
            "processing_type": processing_type,
            "status": "submitted"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提交AI处理任务失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/ai/process/{task_id}")
@monitor_performance("/ai/process/{task_id}", "GET")
async def get_processing_result(
    task_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """获取AI处理结果"""
    try:
        # 验证令牌
        payload = auth_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="无效的访问令牌")

        result = await ai_processor.get_processing_result(task_id)
        if not result:
            raise HTTPException(status_code=404, detail="处理任务不存在")

        # 序列化结果
        result_data = {
            "task_id": result.task_id,
            "file_id": result.file_id,
            "processing_type": result.processing_type.value,
            "status": result.status.value,
            "created_at": result.created_at.isoformat(),
            "started_at": result.started_at.isoformat() if result.started_at else None,
            "completed_at": result.completed_at.isoformat() if result.completed_at else None,
            "confidence": result.confidence,
            "processing_time": result.processing_time,
            "metadata": result.metadata
        }

        # 包含处理结果或错误信息
        if result.status == ProcessingStatus.COMPLETED:
            result_data["result"] = result.result
        elif result.status == ProcessingStatus.FAILED:
            result_data["error"] = result.error_message

        return JSONResponse(content={
            "success": True,
            "result": result_data
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取AI处理结果失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/ai/process/{task_id}/cancel")
@monitor_performance("/ai/process/{task_id}/cancel", "POST")
async def cancel_processing_task(
    task_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """取消AI处理任务"""
    try:
        # 验证令牌
        payload = auth_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="无效的访问令牌")

        # 取消任务
        success = await ai_processor.cancel_processing_task(task_id)

        if success:
            logger.info(f"用户 {payload['user_id']} 取消AI处理任务: {task_id}")
            return JSONResponse(content={
                "success": True,
                "message": "处理任务已取消"
            })
        else:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "无法取消任务（可能已完成）"}
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消AI处理任务失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/ai/process/types")
@monitor_performance("/ai/process/types", "GET")
async def get_supported_processing_types(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """获取支持的处理类型"""
    try:
        # 验证令牌
        payload = auth_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="无效的访问令牌")

        # 获取支持的处理类型
        types_info = {
            "image_analysis": {
                "name": "图像分析",
                "description": "分析图像的基本信息、颜色、质量等",
                "supported_formats": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
            },
            "document_parsing": {
                "name": "文档解析",
                "description": "解析PDF、Word、文本文档的内容",
                "supported_formats": [".pdf", ".doc", ".docx", ".txt", ".md"]
            },
            "text_analysis": {
                "name": "文本分析",
                "description": "中文分词、关键词提取、情感分析等",
                "supported_formats": [".txt", ".md"]
            },
            "content_extraction": {
                "name": "内容提取",
                "description": "从图像或文档中提取文本和元数据",
                "supported_formats": [".jpg", ".jpeg", ".png", ".pdf", ".docx", ".txt"]
            }
        }

        # 获取AI处理器统计
        stats = ai_processor.get_statistics()

        return JSONResponse(content={
            "success": True,
            "processing_types": types_info,
            "processor_stats": stats
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取处理类型失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/ai/batch/process")
@monitor_performance("/ai/batch/process", "POST")
async def batch_ai_processing(
    batch_data: Dict[str, Any],
    user_info: UserInfo = Depends(get_current_user)
):
    """批量AI处理"""
    try:
        file_ids = batch_data.get("file_ids", [])
        processing_type = batch_data.get("processing_type")
        options = batch_data.get("options", {})

        if not file_ids or not processing_type:
            raise HTTPException(
                status_code=400,
                detail="缺少必要参数: file_ids, processing_type"
            )

        # 验证处理类型
        try:
            proc_type = ProcessingType(processing_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的处理类型: {processing_type}"
            )

        # 限制批量处理数量
        max_batch_size = 10
        if len(file_ids) > max_batch_size:
            raise HTTPException(
                status_code=400,
                detail=f"批量处理数量超出限制: {len(file_ids)} > {max_batch_size}"
            )

        # 提交批量任务
        task_ids = []
        for file_id in file_ids:
            try:
                file_path = f"/tmp/uploads/{file_id}"  # 简化实现
                if os.path.exists(file_path):
                    task_id = await ai_processor.submit_processing_task(
                        file_id=file_id,
                        file_path=file_path,
                        processing_type=proc_type,
                        options=options
                    )
                    task_ids.append({
                        "file_id": file_id,
                        "task_id": task_id,
                        "status": "submitted"
                    })
                else:
                    task_ids.append({
                        "file_id": file_id,
                        "task_id": None,
                        "status": "file_not_found"
                    })
            except Exception as e:
                task_ids.append({
                    "file_id": file_id,
                    "task_id": None,
                    "status": "error",
                    "error": str(e)
                })

        logger.info(f"用户 {user_info.user_id} 批量提交 {len(task_ids)} 个AI处理任务")

        return JSONResponse(content={
            "success": True,
            "batch_id": str(uuid.uuid4()),
            "processing_type": processing_type,
            "total_files": len(file_ids),
            "submitted_tasks": len([t for t in task_ids if t["status"] == "submitted"]),
            "tasks": task_ids
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量AI处理失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/ai/statistics")
@monitor_performance("/ai/statistics", "GET")
async def get_ai_statistics(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """获取AI处理统计信息"""
    try:
        # 验证令牌
        payload = auth_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="无效的访问令牌")

        # 获取统计信息
        stats = ai_processor.get_statistics()

        return JSONResponse(content={
            "success": True,
            "statistics": stats
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取AI统计失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# 启动服务
if __name__ == "__main__":
    import asyncio

    async def start_services():
        """启动所有服务"""
        try:
            # 启动性能监控
            await performance_monitor.start()

            # 启动指标收集器
            metrics_collector.start()

            # 启动批量操作管理器
            await batch_operation_manager.start()

            # 启动AI处理器
            await ai_processor.start()

            logger.info("所有监控服务已启动")

            # 启动FastAPI应用
            config = uvicorn.Config(
                app=app,
                host=settings_manager.get_setting("api.host", "0.0.0.0"),
                port=settings_manager.get_setting("api.port", 8000),
                reload=settings_manager.get_setting("api.reload", False),
                workers=1,  # 监控模式下使用单进程
                log_level=settings_manager.get_setting("api.log_level", "info")
            )
            server = uvicorn.Server(config)

            logger.info(f"启动安全增强多模态文件系统API - http://localhost:{config.port}")
            await server.serve()

        except Exception as e:
            logger.error(f"服务启动失败: {e}")
            await performance_monitor.stop()
            metrics_collector.stop()
            await batch_operation_manager.stop()
            await ai_processor.stop()

    # 运行服务
    asyncio.run(start_services())