#!/usr/bin/env python3
from __future__ import annotations
"""
统一报告服务API路由

提供RESTful API接口,支持:
- 单文档报告生成
- 批量报告生成
- 文档对比分析
- 工作流任务管理

Author: Athena工作平台
Date: 2026-01-16
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# 导入核心服务
from core.reporting.unified_report_service import (
    OutputFormat,
    ReportType,
    UnifiedReportService,
)
from core.reporting.workflow_processor import (
    HybridWorkflowProcessor,
    WorkflowStatus,
)

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/v2/reports", tags=["统一报告服务"])

# 全局工作流处理器实例
workflow_processor: HybridWorkflowProcessor | None = None

# 全局报告服务实例
report_service: UnifiedReportService | None = None


# ========== 请求/响应模型 ==========

class ReportGenerationRequest(BaseModel):
    """报告生成请求"""
    report_type: str = Field(..., description="报告类型")
    output_formats: list[str] = Field(default=["markdown", "docx"], description="输出格式列表")
    enable_dolphin: bool = Field(default=True, description="启用Dolphin解析")
    enable_networkx: bool = Field(default=True, description="启用NetworkX分析")
    enable_ai_generation: bool = Field(default=True, description="启用AI生成")
    custom_data: dict | None = Field(default=None, description="自定义数据")


class BatchReportRequest(BaseModel):
    """批量报告生成请求"""
    report_type: str = Field(..., description="报告类型")
    output_dir: str | None = Field(default=None, description="输出目录")
    max_concurrent: int = Field(default=3, description="最大并发数")


class DocumentComparisonRequest(BaseModel):
    """文档对比请求"""
    output_formats: list[str] = Field(default=["markdown", "docx"], description="输出格式列表")


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    error: str | None = None
    processing_time: float | None = None


class ReportResponse(BaseModel):
    """报告响应"""
    task_id: str
    report_type: str
    input_source: str
    output_files: dict[str, str]
    processing_time: float
    quality_score: float
    generation_time: str


# ========== 初始化函数 ==========

def init_services():
    """初始化服务"""
    global report_service, workflow_processor

    if report_service is None:
        logger.info("🔧 初始化统一报告服务...")
        report_service = UnifiedReportService()

    if workflow_processor is None:
        logger.info("🔧 初始化工作流处理器...")
        workflow_processor = HybridWorkflowProcessor(max_concurrent_tasks=3)


# ========== API端点 ==========

@router.post("/generate/upload", response_model=ReportResponse)
async def generate_report_from_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="上传的文档文件"),
    report_type: str = Form("patent_technical_analysis", description="报告类型"),
    output_formats: str = Form("markdown,docx", description="输出格式"),
):
    """
    从上传的文档生成报告

    工作流程: Dolphin解析 → NetworkX分析 → Athena生成 → 多格式输出
    """
    try:
        # 初始化服务
        init_services()

        # 保存上传文件
        upload_dir = Path("/tmp/athena_uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = upload_dir / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        logger.info(f"📄 文件已上传: {file_path}")

        # 解析报告类型
        try:
            report_type_enum = ReportType(report_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的报告类型: {report_type}"
            ) from None

        # 解析输出格式
        format_list = [f.strip() for f in output_formats.split(",")]
        output_format_enums = []
        for fmt in format_list:
            try:
                output_format_enums.append(OutputFormat(fmt))
            except ValueError:
                logger.warning(f"⚠️  不支持的输出格式: {fmt},已跳过")

        # 更新配置
        report_service.config.output_formats = output_format_enums

        # 生成报告
        result = await report_service.generate_from_document(
            document_path=str(file_path),
            report_type=report_type_enum,
        )

        # 删除上传文件
        file_path.unlink(missing_ok=True)

        # 返回结果
        return ReportResponse(
            task_id=str(uuid.uuid4()),
            report_type=report_type,
            input_source=file.filename,
            output_files=result.output_files,
            processing_time=result.processing_time_seconds,
            quality_score=result.quality_score,
            generation_time=result.generation_time.isoformat(),
        )

    except Exception as e:
        logger.error(f"❌ 报告生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/generate/document")
async def generate_report_from_path(
    document_path: str = Form(..., description="文档路径"),
    report_type: str = Form("patent_technical_analysis", description="报告类型"),
    output_dir: str | None = Form(None, description="输出目录"),
):
    """
    从文档路径生成报告
    """
    try:
        init_services()

        # 验证文件存在
        doc_path = Path(document_path)
        if not doc_path.exists():
            raise HTTPException(status_code=404, detail=f"文件不存在: {document_path}")

        # 解析报告类型
        try:
            report_type_enum = ReportType(report_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的报告类型: {report_type}"
            ) from None

        # 生成报告
        result = await report_service.generate_from_document(
            document_path=str(doc_path),
            report_type=report_type_enum,
            output_dir=output_dir,
        )

        return {
            "status": "success",
            "data": {
                "task_id": str(uuid.uuid4()),
                "report_type": report_type,
                "input_source": str(doc_path),
                "output_files": result.output_files,
                "processing_time": result.processing_time_seconds,
                "quality_score": result.quality_score,
                "generation_time": result.generation_time.isoformat(),
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 报告生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/generate/data")
async def generate_report_from_data(
    request: ReportGenerationRequest,
):
    """
    从数据直接生成报告(跳过Dolphin解析和NetworkX分析)
    """
    try:
        init_services()

        # 解析报告类型
        try:
            report_type_enum = ReportType(request.report_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的报告类型: {request.report_type}"
            ) from None

        # 更新配置
        report_service.config.enable_dolphin_parsing = request.enable_dolphin
        report_service.config.enable_networkx_analysis = request.enable_networkx
        report_service.config.enable_ai_generation = request.enable_ai_generation

        # 生成报告
        result = await report_service.generate_from_data(
            data=request.custom_data or {},
            report_type=report_type_enum,
        )

        return {
            "status": "success",
            "data": {
                "task_id": str(uuid.uuid4()),
                "report_type": request.report_type,
                "output_files": result.output_files,
                "processing_time": result.processing_time_seconds,
                "quality_score": result.quality_score,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 报告生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/compare")
async def compare_documents_api(
    doc1_path: str = Form(..., description="文档1路径"),
    doc2_path: str = Form(..., description="文档2路径"),
    output_dir: str | None = Form(None, description="输出目录"),
):
    """
    对比两个文档并生成对比报告
    """
    try:
        init_services()

        # 验证文件存在
        path1 = Path(doc1_path)
        path2 = Path(doc2_path)

        if not path1.exists():
            raise HTTPException(status_code=404, detail=f"文件不存在: {doc1_path}")
        if not path2.exists():
            raise HTTPException(status_code=404, detail=f"文件不存在: {doc2_path}")

        # 执行对比
        result = await report_service.compare_documents(
            doc1_path=str(path1),
            doc2_path=str(path2),
            output_dir=output_dir,
        )

        return {
            "status": "success",
            "data": {
                "task_id": str(uuid.uuid4()),
                "report_type": "patent_comparison",
                "input_source": f"{path1.name} vs {path2.name}",
                "output_files": result.output_files,
                "processing_time": result.processing_time_seconds,
                "quality_score": result.quality_score,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 对比报告生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/batch")
async def batch_generate_reports_api(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(..., description="上传的文档文件列表"),
    report_type: str = Form("patent_technical_analysis", description="报告类型"),
    max_concurrent: int = Form(3, description="最大并发数"),
):
    """
    批量生成报告
    """
    try:
        init_services()

        # 解析报告类型
        try:
            report_type_enum = ReportType(report_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的报告类型: {report_type}"
            ) from None

        # 保存上传文件
        upload_dir = Path("/tmp/athena_batch_uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)

        saved_paths = []
        for file in files:
            file_path = upload_dir / file.filename
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            saved_paths.append(str(file_path))

        # 创建批量任务
        batch_id = str(uuid.uuid4())

        # 添加后台任务
        background_tasks.add_task(
            _batch_generate_task,
            batch_id,
            saved_paths,
            report_type_enum,
            max_concurrent,
        )

        return {
            "status": "success",
            "data": {
                "batch_id": batch_id,
                "total_files": len(saved_paths),
                "report_type": report_type,
                "max_concurrent": max_concurrent,
                "message": "批量任务已提交,请使用 /tasks/{batch_id} 查询进度",
            }
        }

    except Exception as e:
        logger.error(f"❌ 批量任务创建失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


async def _batch_generate_task(
    batch_id: str,
    file_paths: list[str],
    report_type: ReportType,
    max_concurrent: int,
):
    """后台批量生成任务"""
    try:
        processor = HybridWorkflowProcessor(max_concurrent_tasks=max_concurrent)

        # 添加所有任务
        for i, file_path in enumerate(file_paths):
            await processor.add_task(
                task_id=f"{batch_id}_task_{i}",
                report_type=report_type,
                input_source=file_path,
            )

        # 处理所有任务
        await processor.process_all()

        logger.info(f"✅ 批量任务完成: {batch_id}")

    except Exception as e:
        logger.error(f"❌ 批量任务失败: {batch_id} - {e}")


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    获取任务状态
    """
    try:
        if workflow_processor is None:
            raise HTTPException(status_code=503, detail="服务未初始化")

        task = workflow_processor.get_task_status(task_id)

        if task is None:
            raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

        return TaskStatusResponse(
            task_id=task.task_id,
            status=task.status.value,
            created_at=task.created_at.isoformat(),
            started_at=task.started_at.isoformat() if task.started_at else None,
            completed_at=task.completed_at.isoformat() if task.completed_at else None,
            error=task.error,
            processing_time=task.result.processing_time_seconds if task.result else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/tasks")
async def list_all_tasks(
    status: str | None = None,
    limit: int = 100,
):
    """
    列出所有任务
    """
    try:
        if workflow_processor is None:
            raise HTTPException(status_code=503, detail="服务未初始化")

        # 获取任务列表
        if status:
            WorkflowStatus(status)
            tasks = {
                "pending": workflow_processor.get_pending_tasks,
                "running": workflow_processor.get_running_tasks,
                "completed": workflow_processor.get_completed_tasks,
                "failed": workflow_processor.get_failed_tasks,
            }.get(status, lambda: [])()
        else:
            tasks = workflow_processor.get_all_tasks()

        # 限制返回数量
        tasks = tasks[:limit]

        return {
            "status": "success",
            "data": {
                "total": len(tasks),
                "tasks": [
                    {
                        "task_id": t.task_id,
                        "status": t.status.value,
                        "report_type": t.report_type.value,
                        "created_at": t.created_at.isoformat(),
                    }
                    for t in tasks
                ],
            },
        }

    except Exception as e:
        logger.error(f"❌ 获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/download/{task_id}/{format}")
async def download_report(
    task_id: str,
    format: str,
):
    """
    下载生成的报告文件
    """
    try:
        if workflow_processor is None:
            raise HTTPException(status_code=503, detail="服务未初始化")

        task = workflow_processor.get_task_status(task_id)

        if task is None:
            raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

        if task.result is None:
            raise HTTPException(status_code=400, detail="任务尚未完成")

        # 获取文件路径
        file_path = task.result.output_files.get(format)

        if not file_path:
            raise HTTPException(status_code=404, detail=f"文件不存在: {format}")

        # 返回文件
        return FileResponse(
            path=file_path,
            filename=Path(file_path).name,
            media_type="application/octet-stream",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 文件下载失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/health")
async def health_check():
    """
    健康检查
    """
    return {
        "status": "healthy",
        "service": "Unified Report Service",
        "version": "2.0",
        "timestamp": datetime.now().isoformat(),
        "report_service": report_service is not None,
        "workflow_processor": workflow_processor is not None,
    }


# ========== 路由注册函数 ==========

def register_unified_report_routes(app):
    """
    注册统一报告服务路由到FastAPI应用

    Args:
        app: FastAPI应用实例
    """
    app.include_router(router)
    logger.info("✅ 统一报告服务API路由已注册: /api/v2/reports")
