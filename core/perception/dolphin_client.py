#!/usr/bin/env python3
from __future__ import annotations
"""
Dolphin文档解析客户端
Dolphin Document Parser Client for Athena
"""

import logging
from pathlib import Path
from typing import Literal

import httpx

logger = logging.getLogger(__name__)


class DolphinDocumentParser:
    """
    Dolphin文档解析客户端

    用于连接Dolphin微服务,提供文档解析能力
    """

    def __init__(
        self,
        service_url: str = "http://localhost:8090",
        api_key: Optional[str] = None,
        timeout: float = 300.0,  # 5分钟超时
    ):
        """
        初始化Dolphin客户端

        Args:
            service_url: Dolphin服务地址
            api_key: API密钥(如果服务启用了认证)
            timeout: 请求超时时间(秒)
        """
        self.service_url = service_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

        # 创建HTTP客户端
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers=self._get_headers(),
        )

        logger.info(f"🐬 Dolphin客户端初始化: {self.service_url}")

    def _get_headers(self) -> dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if self.api_key:
            headers["X-API-Key"] = self.api_key

        return headers

    async def health_check(self) -> dict:
        """
        健康检查

        Returns:
            服务健康状态
        """
        try:
            response = await self.client.get(f"{self.service_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ 健康检查失败: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def get_model_info(self) -> dict:
        """
        获取模型信息

        Returns:
            模型信息字典
        """
        try:
            response = await self.client.get(f"{self.service_url}/api/v1/model/info")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ 获取模型信息失败: {e}")
            raise

    async def parse_document(
        self,
        file_path: str | Path,
        output_format: Literal["json", "markdown", "both"] = "both",
        max_batch_size: int = 8,
        enable_cache: bool = True,
    ) -> dict:
        """
        解析文档

        Args:
            file_path: 文档路径(图片或PDF)
            output_format: 输出格式
            max_batch_size: 批处理大小
            enable_cache: 是否启用缓存

        Returns:
            解析结果字典
        """
        file_path = Path(file_path) if isinstance(file_path, str) else file_path

        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        logger.info(f"📄 解析文档: {file_path.name}")

        try:
            # 准备文件和数据
            with open(file_path, "rb") as f:
                files = {"file": (file_path.name, f, "application/octet-stream")}
                data = {
                    "output_format": output_format,
                    "max_batch_size": str(max_batch_size),
                    "enable_cache": str(enable_cache).lower(),
                }

                # 发送请求
                response = await self.client.post(
                    f"{self.service_url}/api/v1/parse/upload",
                    files=files,
                    data=data,
                )
                response.raise_for_status()

            result = response.json()

            if result.get("success"):
                logger.info(f"✅ 文档解析成功: {file_path.name}")
                return result.get("result", {})
            else:
                error = result.get("error", "未知错误")
                logger.error(f"❌ 文档解析失败: {error}")
                raise Exception(f"文档解析失败: {error}")

        except Exception as e:
            logger.error(f"❌ 解析文档异常 {file_path.name}: {e}")
            raise

    async def parse_patent_document(
        self,
        file_path: str,
        extract_claims: bool = True,
        extract_tables: bool = True,
        extract_formulas: bool = True,
    ) -> dict:
        """
        解析专利文档(专用接口)

        Args:
            file_path: 专利文档路径
            extract_claims: 是否提取权利要求
            extract_tables: 是否提取表格
            extract_formulas: 是否提取公式

        Returns:
            专利结构化数据
        """
        # 使用Dolphin解析文档
        result = await self.parse_document(
            file_path=file_path,
            output_format="both",
            max_batch_size=8,
        )

        # 提取专利特定信息
        patent_data = {
            "file_name": result.get("file_name", ""),
            "file_type": result.get("file_type", ""),
            "raw_result": result,
        }

        # 如果有页面数据
        if "pages" in result:
            for page in result.get("pages", []):
                # 提取权利要求
                if extract_claims:
                    patent_data["claims"] = self._extract_claims_from_result(page)

                # 提取表格
                if extract_tables:
                    patent_data["tables"] = self._extract_tables_from_result(page)

                # 提取公式
                if extract_formulas:
                    patent_data["formulas"] = self._extract_formulas_from_result(page)

        # 提取标题和摘要
        patent_data["title"] = self._extract_title_from_result(result)
        patent_data["abstract"] = self._extract_abstract_from_result(result)

        return patent_data

    def _extract_claims_from_result(self, page_result: dict) -> list[dict]:
        """从解析结果中提取权利要求"""
        claims = []

        # 根据Dolphin的输出格式提取
        if "elements" in page_result:
            for element in page_result.get("elements", []):
                if element.get("type") in ["para", "sec_0", "sec_1"]:
                    content = element.get("content", "")
                    if "权利要求" in content or "claim" in content.lower():
                        claims.append(element)

        return claims

    def _extract_tables_from_result(self, page_result: dict) -> list[dict]:
        """从解析结果中提取表格"""
        tables = []

        if "elements" in page_result:
            for element in page_result.get("elements", []):
                if element.get("type") == "tab":
                    tables.append(element)

        return tables

    def _extract_formulas_from_result(self, page_result: dict) -> list[dict]:
        """从解析结果中提取公式"""
        formulas = []

        if "elements" in page_result:
            for element in page_result.get("elements", []):
                if element.get("type") == "equ":
                    formulas.append(element)

        return formulas

    def _extract_title_from_result(self, result: dict) -> str:
        """提取标题"""
        # 简单实现:取第一个标题
        if "pages" in result and len(result.get("pages", [])) > 0:
            first_page = result["pages"][0]
            if "elements" in first_page:
                for element in first_page.get("elements", []):
                    if element.get("type") == "sec_0":
                        return element.get("content", "")
        return ""

    def _extract_abstract_from_result(self, result: dict) -> str:
        """提取摘要"""
        # 简单实现:查找包含"摘要"的段落
        if "pages" in result:
            for page in result.get("pages", []):
                if "elements" in page:
                    for element in page.get("elements", []):
                        content = element.get("content", "")
                        if "摘要" in content or "abstract" in content.lower():
                            return content
        return ""

    async def chat_with_document(
        self,
        file_path: str | Path,
        prompt: str,
        use_cache: bool = True,
    ) -> str:
        """
        聊天式文档解析

        Args:
            file_path: 文档路径
            prompt: 提示词
            use_cache: 是否使用缓存

        Returns:
            解析结果文本
        """
        file_path = Path(file_path) if isinstance(file_path, str) else file_path

        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        logger.info(f"💬 聊天解析: {file_path.name}")
        logger.info(f"   提示词: {prompt}")

        try:
            # 准备文件和数据
            with open(file_path, "rb") as f:
                files = {"file": (file_path.name, f, "application/octet-stream")}
                data = {
                    "prompt": prompt,
                    "use_cache": str(use_cache).lower(),
                }

                # 发送请求
                response = await self.client.post(
                    f"{self.service_url}/api/v1/chat",
                    files=files,
                    data=data,
                )
                response.raise_for_status()

            result = response.json()

            if result.get("success"):
                logger.info("✅ 聊天解析成功")
                return result.get("response", "")
            else:
                error = result.get("error", "未知错误")
                logger.error(f"❌ 聊天解析失败: {error}")
                raise Exception(f"聊天解析失败: {error}")

        except Exception as e:
            logger.error(f"❌ 聊天解析异常: {e}")
            raise

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
        logger.info("🔌 Dolphin客户端已关闭")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()


# 全局客户端实例
_client: DolphinDocumentParser | None = None


async def get_dolphin_client(
    service_url: str = "http://localhost:8090",
    api_key: Optional[str] = None,
) -> DolphinDocumentParser:
    """
    获取全局Dolphin客户端实例

    Args:
        service_url: Dolphin服务地址
        api_key: API密钥

    Returns:
        Dolphin客户端实例
    """
    global _client

    if _client is None:
        _client = DolphinDocumentParser(
            service_url=service_url,
            api_key=api_key,
        )

    return _client


async def close_dolphin_client():
    """关闭全局Dolphin客户端"""
    global _client

    if _client is not None:
        await _client.close()
        _client = None
