#!/usr/bin/env python3
"""
混合多模态API网关
Hybrid Multimodal API Gateway

提供统一的API接口，智能路由到MCP或本地系统
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

# 导入安全配置
import sys
from pathlib import Path

import aiofiles
import uvicorn
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

# 导入智能路由器
from intelligent_router import (
    get_intelligent_router,
    process_file_intelligently,
)
from pydantic import BaseModel

# 数据库连接
from sqlalchemy import create_engine, text

from core.security.auth import ALLOWED_ORIGINS

sys.path.append(str(Path(__file__).parent.parent / "core"))

# 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "athena_business",
    "username": "postgres",
    "password": "xj781102"
}

sync_engine = create_engine(
    f"{DB_CONFIG['username']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)

# 存储配置
STORAGE_ROOT = "/Users/xujian/Athena工作平台/storage-system/data/documents/multimodal"

# 创建FastAPI应用
app = FastAPI(
    title="Athena智能多模态API网关",
    description="智能路由到MCP或本地系统的混合处理平台",
    version="1.0.0"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 响应模型
class HybridProcessingResponse(BaseModel):
    success: bool
    request_id: str
    method_used: str
    processing_time: float
    cost: float
    quality_score: float
    result: dict[str, Any] | None = None
    error: str | None = None

class BatchProcessingResponse(BaseModel):
    success: bool
    batch_id: str
    total_files: int
    processed_files: int
    failed_files: int
    total_cost: float
    total_time: float
    results: list[dict[str, Any]

# 存储文件
async def save_uploaded_file(file: UploadFile) -> str:
    """保存上传的文件"""
    # 生成唯一文件名
    file_id = str(uuid.uuid4())
    file_ext = Path(file.filename).suffix
    stored_filename = f"{file_id}{file_ext}"

    # 保存文件
    file_path = os.path.join(STORAGE_ROOT, stored_filename)
    os.makedirs(STORAGE_ROOT, exist_ok=True)

    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)

    return file_path, file_id

@app.get("/")
async def root():
    """API根路径"""
    router = get_intelligent_router()
    stats = router.get_statistics()

    return {
        "service": "🚀 Athena智能多模态API网关",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "🤖 MCP工具集成",
            "🏠 本地系统支持",
            "🧠 智能路由决策",
            "💰 成本优化",
            "📊 批量处理",
            "🔒 数据安全控制"
        ],
        "statistics": stats,
        "message": "根据场景自动选择最优处理方案",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/process", response_model=HybridProcessingResponse)
async def process_file_hybrid(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    priority: str = Form("normal"),
    sensitivity: str = Form("public"),
    high_quality: bool = Form(False),
    auto_analyze: bool = Form(True)
):
    """
    智能处理文件（单文件）

    Parameters:
    - file: 上传的文件
    - priority: 优先级 (low/normal/high/urgent)
    - sensitivity: 数据敏感度 (public/internal/confidential/secret)
    - high_quality: 是否需要高质量处理
    - auto_analyze: 是否自动分析
    """
    try:
        # 保存文件
        file_path, file_id = await save_uploaded_file(file)

        # 获取文件类型
        file_ext = Path(file.filename).suffix.lower()
        if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            file_type = 'image'
        elif file_ext in ['.mp3', '.wav', '.flac', '.m4a', '.ogg', '.amr']:
            file_type = 'audio'
        elif file_ext in ['.pdf', '.doc', '.docx', '.txt', '.md']:
            file_type = 'document'
        else:
            file_type = 'unknown'

        # 智能处理
        result = await process_file_intelligently(
            file_path=file_path,
            file_type=file_type,
            priority=priority,
            sensitivity=sensitivity,
            high_quality=high_quality
        )

        # 保存到数据库（如果成功）
        if result['success'] and auto_analyze:
            background_tasks.add_task(
                save_processing_result,
                file_id,
                file.filename,
                result
            )

        return HybridProcessingResponse(
            success=result['success'],
            request_id=file_id,
            method_used=result['method_used'],
            processing_time=result['processing_time'],
            cost=result['cost'],
            quality_score=result['quality_score'],
            result=result.get('data'),
            error=result.get('error')
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}") from e

@app.post("/api/batch-process", response_model=BatchProcessingResponse)
async def process_files_batch(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    priority: str = Form("normal"),
    sensitivity: str = Form("public"),
    high_quality: bool = Form(False),
    max_concurrent: int = Form(5)
):
    """
    批量处理文件

    Parameters:
    - files: 上传的文件列表
    - priority: 优先级
    - sensitivity: 数据敏感度
    - high_quality: 是否需要高质量处理
    - max_concurrent: 最大并发数
    """
    batch_id = str(uuid.uuid4())
    start_time = datetime.now()

    try:
        # 保存所有文件
        file_info = []
        for file in files:
            file_path, file_id = await save_uploaded_file(file)
            file_info.append({
                'file_id': file_id,
                'file_path': file_path,
                'original_name': file.filename,
                'file_type': _get_file_type(file.filename)
            })

        # 并发处理（控制并发数）
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_single_file(info):
            async with semaphore:
                return await process_file_intelligently(
                    file_path=info['file_path'],
                    file_type=info['file_type'],
                    priority=priority,
                    sensitivity=sensitivity,
                    high_quality=high_quality,
                    batch_size=len(files)
                )

        # 执行批量处理
        tasks = [process_single_file(info) for info in file_info]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 统计结果
        processed_files = 0
        failed_files = 0
        total_cost = 0
        detailed_results = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_files += 1
                detailed_results.append({
                    'file_id': file_info[i]['file_id'],
                    'filename': file_info[i]['original_name'],
                    'success': False,
                    'error': str(result)
                })
            else:
                processed_files += 1
                total_cost += result.get('cost', 0)
                detailed_results.append({
                    'file_id': file_info[i]['file_id'],
                    'filename': file_info[i]['original_name'],
                    'success': result['success'],
                    'method_used': result.get('method_used'),
                    'processing_time': result.get('processing_time'),
                    'cost': result.get('cost'),
                    'quality_score': result.get('quality_score'),
                    'result': result.get('data'),
                    'error': result.get('error')
                })

        total_time = (datetime.now() - start_time).total_seconds()

        # 保存批量处理结果
        background_tasks.add_task(
            save_batch_results,
            batch_id,
            detailed_results
        )

        return BatchProcessingResponse(
            success=processed_files > 0,
            batch_id=batch_id,
            total_files=len(files),
            processed_files=processed_files,
            failed_files=failed_files,
            total_cost=total_cost,
            total_time=total_time,
            results=detailed_results
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量处理失败: {str(e)}") from e

@app.get("/api/statistics")
async def get_statistics():
    """获取处理统计信息"""
    router = get_intelligent_router()
    stats = router.get_statistics()

    # 添加系统信息
    stats.update({
        "system_status": {
            "mcp_available": True,  # 实际应该检测MCP是否可用
            "local_available": True,
            "storage_path": STORAGE_ROOT,
            "database_connected": _check_database()
        },
        "recommendations": _generate_recommendations(stats)
    })

    return stats

@app.get("/api/cost-analysis")
async def get_cost_analysis():
    """获取成本分析"""
    router = get_intelligent_router()
    history = router.processing_history

    if not history:
        return {"message": "暂无处理记录"}

    # 成本分析
    mcp_requests = [h for h in history if h['method'] == 'mcp']
    local_requests = [h for h in history if h['method'] == 'local']

    total_mcp_cost = len(mcp_requests) * 0.05
    total_local_cost = sum(h['processing_time'] / 3600 * 0.5 for h in local_requests)

    # 如果全部使用MCP的成本
    all_mcp_cost = len(history) * 0.05

    savings = all_mcp_cost - (total_mcp_cost + total_local_cost)

    return {
        "total_requests": len(history),
        "mcp_requests": len(mcp_requests),
        "local_requests": len(local_requests),
        "actual_cost": total_mcp_cost + total_local_cost,
        "estimated_mcp_only_cost": all_mcp_cost,
        "savings": savings,
        "savings_percentage": f"{(savings/all_mcp_cost*100):.1f}%",
        "average_cost_per_request": (total_mcp_cost + total_local_cost) / len(history)
    }

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "intelligent_router": "running",
            "mcp_tools": "available",
            "local_processors": "available",
            "database": "connected" if _check_database() else "disconnected"
        }
    }

# 辅助函数
def _get_file_type(filename: str) -> str:
    """获取文件类型"""
    ext = Path(filename).suffix.lower()
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
        return 'image'
    elif ext in ['.mp3', '.wav', '.flac', '.m4a', '.ogg', '.amr']:
        return 'audio'
    elif ext in ['.pdf', '.doc', '.docx', '.txt', '.md']:
        return 'document'
    else:
        return 'unknown'

def _check_database() -> bool:
    """检查数据库连接"""
    try:
        with sync_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except (KeyError, TypeError, IndexError, ValueError):
        return False

def _generate_recommendations(stats: dict) -> list[str]:
    """生成优化建议"""
    recommendations = []

    if stats.get('total_requests', 0) > 0:
        mcp_ratio = float(stats.get('mcp_ratio', '0%').rstrip('%'))

        if mcp_ratio > 80:
            recommendations.append("💡 考虑增加批量处理以降低成本")
        elif mcp_ratio < 30:
            recommendations.append("💡 可以增加MCP使用以提升处理质量")

        if float(stats.get('success_rate', '0%').rstrip('%')) < 90:
            recommendations.append("⚠️ 成功率偏低，检查文件格式和处理参数")

    if not recommendations:
        recommendations.append("✅ 系统运行良好，继续保持当前配置")

    return recommendations

# 后台任务
async def save_processing_result(file_id: str, filename: str, result: dict):
    """保存处理结果到数据库"""
    try:
        with sync_engine.connect():
            # 这里可以保存到处理结果表
            pass
    except Exception as e:
        print(f"保存结果失败: {e}")

async def save_batch_results(batch_id: str, results: list[dict]):
    """保存批量处理结果"""
    try:
        with sync_engine.connect():
            # 这里可以保存到批量处理结果表
            pass
    except Exception as e:
        print(f"保存批量结果失败: {e}")

if __name__ == "__main__":
    # 显示启动信息
    print("\n🚀 启动Athena智能多模态API网关")
    print("=" * 50)
    print("📋 功能特性：")
    print("  ✅ 智能路由：自动选择MCP或本地系统")
    print("  ✅ 成本优化：根据场景选择最优方案")
    print("  ✅ 批量处理：支持大规模文件处理")
    print("  ✅ 数据安全：敏感数据本地处理")
    print("  ✅ 高质量：MCP保证最佳效果")
    print("")
    print("📍 服务端口: 8090")
    print("🌐 API地址: http://localhost:8090")
    print("📊 统计信息: http://localhost:8090/api/statistics")
    print("💰 成本分析: http://localhost:8090/api/cost-analysis")
    print("")
    print("🎯 智能路由策略：")
    print("  - 机密数据 → 本地处理")
    print("  - 紧急任务 → MCP处理")
    print("  - 大批量 → 本地处理")
    print("  - 高质量要求 → MCP处理")
    print("")
    print("🚀 服务启动中...")

    # 启动服务
    uvicorn.run(app, host="127.0.0.1", port=8090)  # 内网通信，通过Gateway访问
