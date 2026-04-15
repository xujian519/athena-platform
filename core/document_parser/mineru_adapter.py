#!/usr/bin/env python3
from __future__ import annotations
"""
MinerU文档解析适配器
MinerU Document Parser Adapter

通过HTTP调用本地MinerU服务（端口7860），支持同步和异步两种模式。
作者: Athena平台团队
"""

import asyncio
import json
import logging
import os
import re
import time
import uuid
from typing import Any

from core.document_parser.base import BaseDocumentParser, ParseRequest, ParseResult, ParserBackend

logger = logging.getLogger(__name__)

# 文件大小上限（200MB），超过直接拒绝
_MAX_FILE_SIZE = 200 * 1024 * 1024
# MinerU同步/异步模式阈值
_ASYNC_SIZE_THRESHOLD = 10 * 1024 * 1024
# Markdown内容最小有效长度
_MIN_MD_LENGTH = 50
# 页面分隔标记（MinerU 不使用此标记，保留仅用于兼容旧版本）
_PAGE_BREAK_MARKER = "--- PAGE BREAK ---"
# 默认置信度（MinerU pipeline质量较高）
_DEFAULT_CONFIDENCE = 0.95
# 安全的task_id正则（仅允许UUID和字母数字）
_SAFE_TASK_ID_RE = re.compile(r"^[a-zA-Z0-9\-_]+$")


class MinerUAdapter(BaseDocumentParser):
    """
    MinerU文档解析适配器

    通过HTTP调用本地MinerU服务（端口7860），
    支持同步（/file_parse）和异步（/tasks）两种模式。
    """

    def __init__(self, base_url: str = "http://127.0.0.1:7860",
                 parse_backend: str = "pipeline",
                 parse_method: str = "auto",
                 request_timeout: int = 300,
                 async_poll_interval: float = 2.0,
                 async_max_wait: float = 600.0):
        super().__init__(ParserBackend.MINERU)
        self.base_url = base_url.rstrip("/")
        self.parse_backend = parse_backend  # MinerU解析后端（pipeline/hybrid-auto-engine）
        self.parse_method = parse_method
        self.request_timeout = request_timeout
        self.async_poll_interval = async_poll_interval
        self.async_max_wait = async_max_wait

        # HTTP客户端（延迟初始化）
        self._client: Any = None  # httpx.AsyncClient | None

        # 可用性状态缓存
        self._is_available: bool = False
        self._last_health_check: float = -float('inf')
        self._consecutive_failures: int = 0
        self._health_cache_ttl: float = 30.0  # 健康检查缓存30秒

        # 统计信息
        self._total_requests: int = 0
        self._total_failures: int = 0

    async def initialize(self) -> bool:
        """初始化适配器，检查MinerU服务可用性"""
        # 幂等：如果已有client，先关闭
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception:
                pass

        try:
            import httpx
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(10.0, connect=5.0),
            )
        except ImportError:
            self._client = None

        # 首次检查强制跳过缓存
        self._last_health_check = 0.0
        self.force_recheck()
        self._is_available = await self.health_check()
        self._initialized = True
        logger.info("MinerU适配器初始化: base_url=%s, available=%s", self.base_url, self._is_available)
        return self._is_available

    async def close(self) -> None:
        """关闭HTTP客户端，释放连接池资源"""
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception:
                pass
            self._client = None

    async def health_check(self) -> bool:
        """
        检查MinerU服务可用性
        使用 /health 端点（返回 JSON 状态信息），使用缓存避免频繁探测
        """
        now = time.monotonic()
        if (now - self._last_health_check) < self._health_cache_ttl:
            return self._is_available

        try:
            if self._client:
                resp = await self._client.get(f"{self.base_url}/health", timeout=5.0)
                if resp.status_code == 200:
                    data = resp.json()
                    healthy = data.get("status") == "healthy"
                else:
                    healthy = False
            else:
                healthy = await self._urllib_health_check()

            if healthy:
                self._consecutive_failures = 0
                self._is_available = True
            else:
                self._consecutive_failures += 1
                if self._consecutive_failures >= 3:
                    self._is_available = False

        except Exception:
            self._consecutive_failures += 1
            if self._consecutive_failures >= 3:
                self._is_available = False

        self._last_health_check = now
        return self._is_available

    async def _urllib_health_check(self) -> bool:
        """使用urllib进行健康检查（异步非阻塞）"""
        import urllib.request

        def _check() -> bool:
            req = urllib.request.Request(f"{self.base_url}/health", method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status != 200:
                    return False
                data = json.loads(resp.read().decode())
                return data.get("status") == "healthy"

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _check)

    def _validate_file(self, file_path: str) -> ParseResult | None:
        """
        校验文件路径，返回错误ParseResult或None（通过校验）

        安全检查：文件必须存在、可读、不超过大小上限。
        """
        if not file_path:
            return ParseResult(error="文件路径为空", backend_used="mineru")

        # 路径规范化，防止路径遍历
        normalized = os.path.normpath(os.path.abspath(file_path))

        if not os.path.exists(normalized):
            return ParseResult(error=f"文件不存在: {file_path}", backend_used="mineru")

        if not os.path.isfile(normalized):
            return ParseResult(error=f"路径不是文件: {file_path}", backend_used="mineru")

        file_size = os.path.getsize(normalized)
        if file_size > _MAX_FILE_SIZE:
            return ParseResult(
                error=f"文件过大({file_size / 1024 / 1024:.1f}MB)，上限{_MAX_FILE_SIZE / 1024 / 1024:.0f}MB",
                backend_used="mineru",
            )

        return None  # 校验通过

    async def parse(self, request: ParseRequest) -> ParseResult:
        """
        解析文档，自动选择同步或异步模式
        小文件（<10MB）用同步，大文件用异步
        """
        start_time = time.time()
        self._total_requests += 1

        # 文件校验
        validation_error = self._validate_file(request.file_path)
        if validation_error:
            validation_error.processing_time = time.time() - start_time
            return validation_error

        file_size = os.path.getsize(os.path.normpath(os.path.abspath(request.file_path)))
        use_async = file_size > _ASYNC_SIZE_THRESHOLD

        try:
            if use_async:
                result = await self._parse_async(request)
            else:
                result = await self._parse_sync(request)

            result.processing_time = time.time() - start_time
            result.backend_used = "mineru"
            return result

        except Exception as e:
            self._total_failures += 1
            logger.warning("MinerU解析失败: %s", e)
            return ParseResult(
                error=str(e),
                backend_used="mineru",
                processing_time=time.time() - start_time,
            )

    async def _parse_sync(self, request: ParseRequest) -> ParseResult:
        """调用 POST /file_parse 同步端点"""
        if self._client:
            return await self._parse_sync_httpx(request)
        return await self._parse_sync_urllib(request)

    async def _parse_sync_httpx(self, request: ParseRequest) -> ParseResult:
        """使用httpx调用同步端点"""
        with open(request.file_path, "rb") as f:
            file_content = f.read()

        filename = os.path.basename(request.file_path)
        resp = await self._client.post(
            f"{self.base_url}/file_parse",
            files={"files": (filename, file_content, "application/octet-stream")},
            data=self._build_form_data(request),
            timeout=self.request_timeout,
        )

        return await self._handle_response(resp.status_code, resp.text)

    def _build_form_data(self, request: ParseRequest) -> dict[str, str | list[str]]:
        """构建统一的表单数据（httpx和urllib共用）"""
        return {
            "backend": self.parse_backend,
            "lang_list": [request.language or "ch"],  # MinerU 期望列表类型
            "parse_method": self.parse_method,
            "return_md": "true" if request.return_markdown else "false",
            "return_middle_json": "true",  # 用于准确统计页数
            "table_enable": "true" if request.extract_tables else "false",
            "formula_enable": "true" if request.extract_formulas else "false",
        }

    async def _parse_sync_urllib(self, request: ParseRequest) -> ParseResult:
        """使用urllib调用同步端点（httpx不可用时的备选）"""
        filename = os.path.basename(request.file_path)
        boundary = uuid.uuid4().hex
        body = b""

        with open(request.file_path, "rb") as f:
            file_content = f.read()

        body += f"--{boundary}\r\n".encode()
        body += 'Content-Disposition: form-data; name="files"; filename="{name}"\r\n'.format(
            name=filename.replace('"', '\\"')
        ).encode()
        body += b"Content-Type: application/octet-stream\r\n\r\n"
        body += file_content
        body += b"\r\n"

        form_data = self._build_form_data(request)
        for key, val in form_data.items():
            body += f"--{boundary}\r\n".encode()
            body += f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
            body += f"{val}\r\n".encode()

        body += f"--{boundary}--\r\n".encode()

        import urllib.request
        loop = asyncio.get_running_loop()

        def _do_request():
            req = urllib.request.Request(
                f"{self.base_url}/file_parse",
                data=body,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.request_timeout) as resp:
                return resp.status, resp.read().decode()

        status_code, text = await loop.run_in_executor(None, _do_request)
        return await self._handle_response(status_code, text)

    async def _handle_response(self, status_code: int, text: str) -> ParseResult:
        """处理MinerU响应（含同步端点返回任务URL的自动跟踪）"""
        if status_code == 200:
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                # 可能是同步端点返回了任务URL（纯文本）
                text_stripped = text.strip()
                if text_stripped.startswith(f"{self.base_url}/tasks/"):
                    logger.info("同步端点返回任务URL，自动跟踪异步结果")
                    return await self._follow_task_url(text_stripped)
                return ParseResult(
                    error=f"MinerU返回非JSON响应(status={status_code}): {text[:200]}",
                    backend_used="mineru",
                )

            # 检查是否返回了JSON格式的任务信息
            if isinstance(data, dict) and "task_id" in data and "status" in data:
                task_id = data["task_id"]
                task_url = data.get("status_url", f"{self.base_url}/tasks/{task_id}")
                result_url = data.get("result_url", f"{task_url}/result")
                logger.info("同步端点返回任务信息(task_id=%s)，自动跟踪", task_id)
                return await self._fetch_task_result(task_url, result_url)

            md_content = self._extract_md(data)
            # 保留完整 Markdown（含图片引用），仅纯文本字段去除图片
            plain_text = re.sub(r"!\[.*?\]\(.*?\)", "", md_content)

            # 从 middle_json 准确统计页数，而非依赖不存在的 PAGE_BREAK 标记
            page_count = self._count_pages(data)

            return ParseResult(
                content=plain_text.strip(),
                markdown_content=md_content,
                backend_used="mineru",
                confidence=_DEFAULT_CONFIDENCE,
                page_count=page_count,
            )

        if status_code == 409:
            try:
                data = json.loads(text)
                task_id = data.get("task_id", "")
                if task_id and data.get("status") == "completed":
                    return ParseResult(error=f"async_task:{task_id}", backend_used="mineru")
                error_msg = data.get("error", text[:200])
            except json.JSONDecodeError:
                error_msg = text[:200]
            return ParseResult(error=error_msg, backend_used="mineru")

        return ParseResult(error=f"HTTP {status_code}: {text[:200]}", backend_used="mineru")

    async def _follow_task_url(self, task_url: str) -> ParseResult:
        """跟踪同步端点返回的任务URL，轮询直到完成"""
        # 从URL提取task_id
        task_id = task_url.rstrip("/").split("/")[-1]
        if not _SAFE_TASK_ID_RE.match(task_id):
            return ParseResult(error=f"无效的task_id从URL: {task_id}", backend_used="mineru")

        deadline = time.monotonic() + self.async_max_wait
        while time.monotonic() < deadline:
            await asyncio.sleep(self.async_poll_interval)

            if self._client:
                poll_resp = await self._client.get(task_url, timeout=10.0)
                poll_data = poll_resp.json()
            else:
                poll_data = await self._poll_task_urllib(task_url)

            status = poll_data.get("status", "unknown")
            if status == "completed":
                result_url = poll_data.get("result_url", f"{task_url}/result")
                return await self._fetch_task_result(task_url, result_url)
            elif status == "failed":
                return ParseResult(error=poll_data.get("error", "异步任务失败"), backend_used="mineru")

        return ParseResult(error="跟踪任务URL超时", backend_used="mineru")

    async def _fetch_task_result(self, task_url: str, result_url: str) -> ParseResult:
        """获取异步任务的最终结果"""
        if self._client:
            result_resp = await self._client.get(result_url, timeout=30.0)
            content_type = result_resp.headers.get("content-type", "")

            if "application/zip" in content_type:
                return await self._extract_from_zip(result_resp.content)

            result_data = result_resp.json()
        else:
            result_data = await self._poll_task_urllib(result_url)

        md = self._extract_md(result_data)
        plain = re.sub(r"!\[.*?\]\(.*?\)", "", md)
        page_count = self._count_pages(result_data)

        return ParseResult(
            content=plain.strip(),
            markdown_content=md,
            backend_used="mineru",
            confidence=_DEFAULT_CONFIDENCE,
            page_count=page_count,
        )

    async def _extract_from_zip(self, zip_bytes: bytes) -> ParseResult:
        """从 ZIP 结果中提取 Markdown 内容"""
        import zipfile
        import io

        md_content = ""
        page_count = 0

        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            for name in zf.namelist():
                if name.endswith(".md"):
                    md_content = zf.read(name).decode("utf-8")
                elif name.endswith("_middle.json"):
                    try:
                        middle = json.loads(zf.read(name).decode("utf-8"))
                        pdf_info = middle.get("pdf_info", [])
                        if isinstance(pdf_info, list):
                            page_count = len(pdf_info)
                    except (json.JSONDecodeError, TypeError):
                        pass

        plain = re.sub(r"!\[.*?\]\(.*?\)", "", md_content)
        return ParseResult(
            content=plain.strip(),
            markdown_content=md_content,
            backend_used="mineru",
            confidence=_DEFAULT_CONFIDENCE,
            page_count=page_count,
        )

    async def _parse_async(self, request: ParseRequest) -> ParseResult:
        """
        调用异步端点:
        1. POST /tasks 提交任务
        2. 轮询 GET /tasks/{id} 等待完成
        3. GET /tasks/{id}/result 获取结果
        """
        # Step 1: 提交任务
        with open(request.file_path, "rb") as f:
            file_content = f.read()

        filename = os.path.basename(request.file_path)

        if self._client:
            resp = await self._client.post(
                f"{self.base_url}/tasks",
                files={"files": (filename, file_content, "application/octet-stream")},
                data=self._build_form_data(request),
                timeout=30.0,
            )
            submit_data = resp.json()
        else:
            submit_data = await self._submit_async_urllib(filename, file_content, request)

        task_id = submit_data.get("task_id", "")
        if not task_id:
            return ParseResult(error=f"提交任务失败: {submit_data}", backend_used="mineru")

        # 安全校验task_id
        if not _SAFE_TASK_ID_RE.match(task_id):
            return ParseResult(error=f"无效的task_id: {task_id}", backend_used="mineru")

        # Step 2: 轮询等待完成（使用绝对时间判断超时）
        status_url = f"{self.base_url}/tasks/{task_id}"
        deadline = time.monotonic() + self.async_max_wait

        while time.monotonic() < deadline:
            await asyncio.sleep(self.async_poll_interval)

            if self._client:
                poll_resp = await self._client.get(status_url, timeout=10.0)
                poll_data = poll_resp.json()
            else:
                poll_data = await self._poll_task_urllib(status_url)

            task_status = poll_data.get("status", "unknown")
            if task_status == "completed":
                # Step 3: 获取结果
                result_url = poll_data.get("result_url", f"{status_url}/result")
                # 安全校验result_url
                if result_url.startswith("/") or result_url.startswith(self.base_url):
                    if result_url.startswith("/"):
                        result_url = self.base_url + result_url
                else:
                    logger.warning("可疑的result_url被拒绝: %s", result_url)
                    return ParseResult(error=f"不安全的result_url: {result_url}", backend_used="mineru")

                if self._client:
                    result_resp = await self._client.get(result_url, timeout=30.0)
                    content_type = result_resp.headers.get("content-type", "")

                    if "application/zip" in content_type:
                        return await self._extract_from_zip(result_resp.content)

                    result_data = result_resp.json()
                else:
                    result_data = await self._poll_task_urllib(result_url)

                md = self._extract_md(result_data)
                plain = re.sub(r"!\[.*?\]\(.*?\)", "", md)
                page_count = self._count_pages(result_data)

                return ParseResult(
                    content=plain.strip(),
                    markdown_content=md,
                    backend_used="mineru",
                    confidence=_DEFAULT_CONFIDENCE,
                    page_count=page_count,
                )
            elif task_status == "failed":
                error_msg = poll_data.get("error", "未知错误")
                return ParseResult(error=error_msg, backend_used="mineru")

        return ParseResult(error="异步解析超时", backend_used="mineru")

    async def _poll_task_urllib(self, url: str) -> dict:
        """使用urllib轮询任务状态"""
        import urllib.request
        loop = asyncio.get_running_loop()

        def _poll():
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as r:
                return json.loads(r.read().decode())

        return await loop.run_in_executor(None, _poll)

    async def _submit_async_urllib(self, filename: str, file_content: bytes,
                                   request: ParseRequest) -> dict:
        """使用urllib提交异步任务"""
        import urllib.request

        boundary = uuid.uuid4().hex
        body = b""
        body += f"--{boundary}\r\n".encode()
        body += 'Content-Disposition: form-data; name="files"; filename="{name}"\r\n'.format(
            name=filename.replace('"', '\\"')
        ).encode()
        body += b"Content-Type: application/octet-stream\r\n\r\n"
        body += file_content + b"\r\n"

        form_data = self._build_form_data(request)
        for key, val in form_data.items():
            body += f"--{boundary}\r\n".encode()
            body += f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
            body += f"{val}\r\n".encode()
        body += f"--{boundary}--\r\n".encode()

        loop = asyncio.get_running_loop()

        def _submit():
            req = urllib.request.Request(
                f"{self.base_url}/tasks",
                data=body,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())

        return await loop.run_in_executor(None, _submit)

    @staticmethod
    def _count_pages(data: Any) -> int:
        """从 MinerU 响应中准确统计页数，优先从 middle_json 的 pdf_info 获取"""
        if isinstance(data, dict):
            results = data.get("results", {})
            if isinstance(results, dict):
                for file_data in results.values():
                    if not isinstance(file_data, dict):
                        continue
                    # 优先从 middle_json 获取页数
                    middle_json_str = file_data.get("middle_json")
                    if middle_json_str:
                        try:
                            middle = json.loads(middle_json_str) if isinstance(middle_json_str, str) else middle_json_str
                            pdf_info = middle.get("pdf_info", [])
                            if isinstance(pdf_info, list):
                                return len(pdf_info)
                        except (json.JSONDecodeError, TypeError):
                            pass
            # 兜底：直接在 data 中搜索 pdf_info
            pdf_info = data.get("pdf_info")
            if isinstance(pdf_info, list):
                return len(pdf_info)
        return 0

    @staticmethod
    def _extract_md(data: Any, depth: int = 0) -> str:
        """递归提取MinerU响应中的Markdown内容"""
        if depth > 6:
            return ""
        if isinstance(data, str) and len(data) > _MIN_MD_LENGTH:
            return data
        if isinstance(data, dict):
            for key in ["md_content", "markdown", "md", "content"]:
                if key in data and data[key] and len(str(data[key])) > _MIN_MD_LENGTH:
                    return str(data[key])
            for v in data.values():
                r = MinerUAdapter._extract_md(v, depth + 1)
                if r:
                    return r
        if isinstance(data, list):
            parts = []
            for item in data:
                r = MinerUAdapter._extract_md(item, depth + 1)
                if r:
                    parts.append(r)
            return "\n".join(parts) if parts else ""
        return ""

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "backend": "mineru",
            "base_url": self.base_url,
            "available": self._is_available,
            "initialized": self._initialized,
            "total_requests": self._total_requests,
            "total_failures": self._total_failures,
            "consecutive_failures": self._consecutive_failures,
        }

    @property
    def is_available(self) -> bool:
        return self._is_available

    def force_recheck(self):
        """强制下次调用时重新检查健康状态"""
        self._last_health_check = -float('inf')
