#!/usr/bin/env python3
from __future__ import annotations
"""
Dolphin文档解析API路由
Dolphin Document Parsing API Routes for Athena
"""

import logging
import os
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from core.perception.dolphin_client import get_dolphin_client

logger = logging.getLogger(__name__)

# Dolphin服务地址
DOLPHIN_SERVICE_URL = os.getenv("DOLPHIN_SERVICE_URL", "http://localhost:8090")
DOLPHIN_API_KEY = os.getenv("DOLPHIN_API_KEY", "")


def register_dolphin_routes(app):
    """注册Dolphin文档解析API路由"""

    router = APIRouter(prefix="/api/v2/dolphin", tags=["Dolphin文档解析"])

    @router.get("/health")
    async def dolphin_health_check():
        """Dolphin服务健康检查"""
        try:
            client = await get_dolphin_client(
                service_url=DOLPHIN_SERVICE_URL,
                api_key=DOLPHIN_API_KEY if DOLPHIN_API_KEY else None,
            )
            health = await client.health_check()
            return JSONResponse(health)
        except Exception as e:
            logger.error(f"❌ Dolphin健康检查失败: {e}")
            return JSONResponse({"status": "unhealthy", "error": str(e)}, status_code=503)

    @router.get("/model/info")
    async def dolphin_model_info():
        """获取Dolphin模型信息"""
        try:
            client = await get_dolphin_client(
                service_url=DOLPHIN_SERVICE_URL,
                api_key=DOLPHIN_API_KEY if DOLPHIN_API_KEY else None,
            )
            info = await client.get_model_info()
            return JSONResponse(info)
        except Exception as e:
            logger.error(f"❌ 获取模型信息失败: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e

    @router.post("/parse")
    async def parse_document(
        file: UploadFile = File(..., description="文档文件(图片或PDF)"),
        output_format: Literal["json", "markdown", "both"] = Form("both"),
        max_batch_size: int = Form(8),
        enable_cache: bool = Form(True),
    ):
        """
        解析文档

        支持的格式:
        - 图片:PNG, JPG, JPEG, BMP, GIF
        - 文档:PDF

        返回格式:
        - JSON:结构化数据,包含元素类型、坐标、内容
        - Markdown:保留格式的文档内容
        """
        try:
            # 保存临时文件
            temp_dir = Path("/tmp/athena_dolphin")
            temp_dir.mkdir(exist_ok=True)
            temp_file = temp_dir / (file.filename or "temp_file")

            with open(temp_file, "wb") as f:
                content = await file.read()
                f.write(content)

            # 获取客户端并解析
            client = await get_dolphin_client(
                service_url=DOLPHIN_SERVICE_URL,
                api_key=DOLPHIN_API_KEY if DOLPHIN_API_KEY else None,
            )

            result = await client.parse_document(
                file_path=str(temp_file),
                output_format=output_format,
                max_batch_size=max_batch_size,
                enable_cache=enable_cache,
            )

            # 清理临时文件
            temp_file.unlink(missing_ok=True)

            return JSONResponse(
                {
                    "success": True,
                    "file_name": file.filename,
                    "result": result,
                }
            )

        except Exception as e:
            logger.error(f"❌ 文档解析失败: {e}")
            # 清理临时文件
            if "temp_file" in locals():
                temp_file.unlink(missing_ok=True)
            raise HTTPException(status_code=500, detail=str(e)) from e

    @router.post("/parse/patent")
    async def parse_patent_document(
        file: UploadFile = File(..., description="专利文档文件"),
        extract_claims: bool = Form(True),
        extract_tables: bool = Form(True),
        extract_formulas: bool = Form(True),
    ):
        """
        解析专利文档(专用接口)

        自动提取专利的关键信息:
        - 标题
        - 摘要
        - 权利要求
        - 表格
        - 公式
        """
        try:
            # 保存临时文件
            temp_dir = Path("/tmp/athena_dolphin")
            temp_dir.mkdir(exist_ok=True)
            temp_file = temp_dir / (file.filename or "temp_file")

            with open(temp_file, "wb") as f:
                content = await file.read()
                f.write(content)

            # 获取客户端并解析
            client = await get_dolphin_client(
                service_url=DOLPHIN_SERVICE_URL,
                api_key=DOLPHIN_API_KEY if DOLPHIN_API_KEY else None,
            )

            result = await client.parse_patent_document(
                file_path=str(temp_file),
                extract_claims=extract_claims,
                extract_tables=extract_tables,
                extract_formulas=extract_formulas,
            )

            # 清理临时文件
            temp_file.unlink(missing_ok=True)

            return JSONResponse(
                {
                    "success": True,
                    "file_name": file.filename,
                    "patent_data": result,
                }
            )

        except Exception as e:
            logger.error(f"❌ 专利文档解析失败: {e}")
            # 清理临时文件
            if "temp_file" in locals():
                temp_file.unlink(missing_ok=True)
            raise HTTPException(status_code=500, detail=str(e)) from e

    @router.post("/chat")
    async def chat_with_document(
        file: UploadFile = File(..., description="文档图片"),
        prompt: str = Form(..., description="提示词"),
        use_cache: bool = Form(True),
    ):
        """
        聊天式文档解析

        使用自然语言提示词与文档交互
        """
        try:
            # 保存临时文件
            temp_dir = Path("/tmp/athena_dolphin")
            temp_dir.mkdir(exist_ok=True)
            temp_file = temp_dir / (file.filename or "temp_file")

            with open(temp_file, "wb") as f:
                content = await file.read()
                f.write(content)

            # 获取客户端并解析
            client = await get_dolphin_client(
                service_url=DOLPHIN_SERVICE_URL,
                api_key=DOLPHIN_API_KEY if DOLPHIN_API_KEY else None,
            )

            response = await client.chat_with_document(
                file_path=str(temp_file),
                prompt=prompt,
                use_cache=use_cache,
            )

            # 清理临时文件
            temp_file.unlink(missing_ok=True)

            return JSONResponse(
                {
                    "success": True,
                    "response": response,
                }
            )

        except Exception as e:
            logger.error(f"❌ 聊天解析失败: {e}")
            # 清理临时文件
            if "temp_file" in locals():
                temp_file.unlink(missing_ok=True)
            raise HTTPException(status_code=500, detail=str(e)) from e

    # 注册路由
    app.include_router(router)
    logger.info("✅ Dolphin文档解析路由已注册到 /api/v2/dolphin")
