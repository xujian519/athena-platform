#!/usr/bin/env python3
"""
Athena平台 - 多模态文件系统集成服务
Platform Integration Service for Multimodal File System
"""

from __future__ import annotations
import asyncio
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import requests

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class MultimodalIntegrationService:
    """多模态文件系统集成服务"""

    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.token = None
        self.token_expires = None
        self.username = "athena_platform"
        # 从环境变量读取密码
        self.password = os.getenv("MULTIMODAL_INTEGRATION_PASSWORD", "athena_integration_2024")
        self.session = requests.Session()

        # 集成配置
        self.config = {"auto_retry": True, "timeout": 30, "max_retries": 3, "cache_enabled": True}

        # 初始化认证
        self._authenticate()

    def _authenticate(self) -> Any:
        """认证获取token"""
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                data={"username": self.username, "password": self.password},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                self.token_expires = datetime.now() + timedelta(
                    seconds=data.get("expires_in", 86400)
                )

                # 设置认证头
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})

                logger.info("多模态文件系统认证成功")
                return True
            else:
                logger.error(f"认证失败: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"认证异常: {e}")
            return False

    def _check_token(self) -> Any:
        """检查token是否有效"""
        if not self.token or not self.token_expires:
            return self._authenticate()

        if datetime.now() >= self.token_expires - timedelta(minutes=5):
            return self._authenticate()

        return True

    async def upload_file(self, file_path: str, description: str | None = None) -> dict[str, Any]:
        """
        上传文件到多模态系统

        Args:
            file_path: 文件路径
            description: 文件描述

        Returns:
            上传结果
        """
        if not self._check_token():
            return {"success": False, "error": "认证失败"}

        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return {"success": False, "error": "文件不存在"}

            with open(file_path, "rb") as f:
                files = {"file": (file_path.name, f, "application/octet-stream")}
                data = {"token": self.token}

                if description:
                    data["description"] = description

                response = self.session.post(
                    f"{self.base_url}/upload",
                    files=files,
                    data=data,
                    timeout=self.config["timeout"],
                )

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"文件上传成功: {file_path.name}")
                    return result
                else:
                    logger.error(f"上传失败: {response.status_code} - {response.text}")
                    return {"success": False, "error": f"上传失败: {response.status_code}"}

        except Exception as e:
            logger.error(f"上传异常: {e}")
            return {"success": False, "error": str(e)}

    async def get_file_info(self, file_id: str) -> dict[str, Any]:
        """
        获取文件信息

        Args:
            file_id: 文件ID

        Returns:
            文件信息
        """
        if not self._check_token():
            return {"success": False, "error": "认证失败"}

        try:
            response = self.session.get(
                f"{self.base_url}/files/{file_id}", timeout=self.config["timeout"]
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return {"success": False, "error": "文件不存在"}
            else:
                return {"success": False, "error": f"查询失败: {response.status_code}"}

        except Exception as e:
            logger.error(f"查询文件信息异常: {e}")
            return {"success": False, "error": str(e)}

    async def list_files(self, file_type: str | None = None, limit: int = 100) -> dict[str, Any]:
        """
        列出文件

        Args:
            file_type: 文件类型过滤
            limit: 返回数量限制

        Returns:
            文件列表
        """
        if not self._check_token():
            return {"success": False, "error": "认证失败"}

        try:
            params = {}
            if file_type:
                params["type"] = file_type
            if limit:
                params["limit"] = limit

            response = self.session.get(
                f"{self.base_url}/files", params=params, timeout=self.config["timeout"]
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": f"获取列表失败: {response.status_code}"}

        except Exception as e:
            logger.error(f"获取文件列表异常: {e}")
            return {"success": False, "error": str(e)}

    async def download_file(self, file_id: str, save_path: str | None = None) -> dict[str, Any]:
        """
        下载文件

        Args:
            file_id: 文件ID
            save_path: 保存路径

        Returns:
            下载结果
        """
        if not self._check_token():
            return {"success": False, "error": "认证失败"}

        try:
            # 获取下载链接
            info_response = await self.get_file_info(file_id)
            if not info_response.get("success"):
                return info_response

            file_info = info_response.get("file_info", {})
            filename = file_info.get("filename", f"file_{file_id}")

            response = self.session.get(
                f"{self.base_url}/download/{file_id}", timeout=self.config["timeout"]
            )

            if response.status_code == 200:
                # 确定保存路径
                if not save_path:
                    save_path = f"/tmp/{filename}"
                else:
                    save_path = Path(save_path)
                    if save_path.is_dir():
                        save_path = save_path / filename

                # 保存文件
                with open(save_path, "wb") as f:
                    f.write(response.content)

                logger.info(f"文件下载成功: {save_path}")
                return {
                    "success": True,
                    "file_path": str(save_path),
                    "file_size": len(response.content),
                    "file_info": file_info,
                }
            else:
                return {"success": False, "error": f"下载失败: {response.status_code}"}

        except Exception as e:
            logger.error(f"下载异常: {e}")
            return {"success": False, "error": str(e)}

    async def get_statistics(self) -> dict[str, Any]:
        """获取系统统计信息"""
        if not self._check_token():
            return {"success": False, "error": "认证失败"}

        try:
            response = self.session.get(
                f"{self.base_url}/statistics", timeout=self.config["timeout"]
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": f"获取统计失败: {response.status_code}"}

        except Exception as e:
            logger.error(f"获取统计信息异常: {e}")
            return {"success": False, "error": str(e)}

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)

            if response.status_code == 200:
                return {"success": True, "status": "healthy", "data": response.json()}
            else:
                return {
                    "success": False,
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                }

        except Exception as e:
            return {"success": False, "status": "error", "error": str(e)}

    async def batch_upload(
        self, file_paths: list[str], descriptions: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """
        批量上传文件

        Args:
            file_paths: 文件路径列表
            descriptions: 描述列表(可选)

        Returns:
            批量上传结果
        """
        results = []

        for i, file_path in enumerate(file_paths):
            description = descriptions[i] if descriptions and i < len(descriptions) else None
            result = await self.upload_file(file_path, description)
            results.append(result)

            # 避免请求过快
            await asyncio.sleep(0.1)

        return results

    def get_service_info(self) -> dict[str, Any]:
        """获取服务信息"""
        return {
            "service_name": "Athena多模态文件系统集成服务",
            "version": "1.0.0",
            "base_url": self.base_url,
            "authenticated": bool(self.token),
            "token_expires": self.token_expires.isoformat() if self.token_expires else None,
            "config": self.config,
        }


# 创建全局实例
multimodal_service = MultimodalIntegrationService()

# 导出主要功能
__all__ = ["MultimodalIntegrationService", "multimodal_service"]
