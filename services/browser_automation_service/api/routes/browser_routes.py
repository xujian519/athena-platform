#!/usr/bin/env python3
"""
浏览器操作路由
Browser Operation Routes for Browser Automation Service

提供浏览器操作的API端点

作者: 小诺·双鱼公主
版本: 1.0.0
"""


from config.settings import logger
from core.browser_manager import get_browser_manager
from core.task_executor import TaskExecutor
from fastapi import APIRouter, Depends, HTTPException

from api.middleware.auth_middleware import TokenData, verify_any_auth
from api.models.requests import (
    ClickRequest,
    EvaluateRequest,
    FillRequest,
    NavigateRequest,
    ScreenshotRequest,
    TaskRequest,
)
from api.models.responses import (
    ClickResponse,
    ContentResponse,
    EvaluateResponse,
    FillResponse,
    NavigateResponse,
    ScreenshotResponse,
    TaskResponse,
)
from core.concurrency import get_concurrency_manager
from core.exceptions import (
    generate_error_id,
)

browser_router = APIRouter(prefix="/api/v1", tags=["浏览器操作"])


# =============================================================================
# JavaScript沙箱配置
# =============================================================================

# 危险操作黑名单
JS_DANGEROUS_PATTERNS = [
    "window.location",
    "document.cookie",
    "localStorage.",
    "sessionStorage.",
    "XMLHttpRequest",
    "fetch(",
    "eval(",
    "Function(",
    "import(",
    "require(",
    # 可以访问外部网络的操作
    ".postMessage",
    "WebSocket",
    # 危险的DOM操作
    "document.write",
    "document.writeln",
]

# 允许的简单操作白名单
JS_SAFE_PATTERNS = [
    "document.",
    "window.",
    "navigator.",
    "screen.",
    "history.",
]


def validate_javascript_safety(script: str) -> tuple[bool, str | None]:
    """
    验证JavaScript代码安全性

    Args:
        script: JavaScript代码

    Returns:
        tuple[bool, str | None]: (是否安全, 错误消息)
    """
    # 检查危险模式
    for pattern in JS_DANGEROUS_PATTERNS:
        if pattern in script:
            return False, f"禁止使用危险操作: {pattern}"

    # 检查脚本长度
    if len(script) > 10000:
        return False, "JavaScript代码长度超过限制（10000字符）"

    # 检查是否有至少一个安全操作
    has_safe_operation = any(pattern in script for pattern in JS_SAFE_PATTERNS)
    if not has_safe_operation and script.strip() and not script.startswith("return "):
        return False, "JavaScript代码不包含任何允许的操作"

    return True, None


@browser_router.post(
    "/navigate",
    response_model=NavigateResponse,
    summary="导航到URL",
    description="在浏览器中导航到指定的URL",
)
async def navigate(
    request: NavigateRequest,
    auth: TokenData | bool = Depends(verify_any_auth),
) -> NavigateResponse:
    """
    导航到指定URL

    Args:
        request: 导航请求
        auth: 认证信息

    Returns:
        NavigateResponse: 导航结果
    """
    try:
        # 并发控制
        concurrency_manager = get_concurrency_manager()
        async with concurrency_manager.navigate_semaphore.acquire():
            manager = await get_browser_manager()
            result = await manager.navigate(
                url=request.url,
                wait_until=request.wait_until,
            )

            if not result.get("success"):
                raise HTTPException(status_code=400, detail=result.get("message"))

            return NavigateResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 导航API错误: {e}")
        raise HTTPException(status_code=500, detail=f"导航失败: {e}") from e


@browser_router.post(
    "/click",
    response_model=ClickResponse,
    summary="点击元素",
    description="点击页面上的指定元素",
)
async def click(
    request: ClickRequest,
    auth: TokenData | bool = Depends(verify_any_auth),
) -> ClickResponse:
    """
    点击元素

    Args:
        request: 点击请求
        auth: 认证信息

    Returns:
        ClickResponse: 点击结果
    """
    try:
        # 并发控制
        concurrency_manager = get_concurrency_manager()
        async with concurrency_manager.click_semaphore.acquire():
            manager = await get_browser_manager()
            result = await manager.click(
                selector=request.selector,
                timeout=request.timeout,
            )

            if not result.get("success"):
                raise HTTPException(status_code=400, detail=result.get("message"))

            return ClickResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 点击API错误: {e}")
        raise HTTPException(status_code=500, detail=f"点击失败: {e}") from e


@browser_router.post(
    "/fill",
    response_model=FillResponse,
    summary="填写表单",
    description="在指定的输入框中填写值",
)
async def fill(
    request: FillRequest,
    auth: TokenData | bool = Depends(verify_any_auth),
) -> FillResponse:
    """
    填写表单

    Args:
        request: 填写请求
        auth: 认证信息

    Returns:
        FillResponse: 填写结果
    """
    try:
        # 并发控制
        concurrency_manager = get_concurrency_manager()
        async with concurrency_manager.fill_semaphore.acquire():
            manager = await get_browser_manager()
            result = await manager.fill(
                selector=request.selector,
                value=request.value,
                timeout=request.timeout,
            )

            if not result.get("success"):
                raise HTTPException(status_code=400, detail=result.get("message"))

            return FillResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 填写API错误: {e}")
        raise HTTPException(status_code=500, detail=f"填写失败: {e}") from e


@browser_router.post(
    "/screenshot",
    response_model=ScreenshotResponse,
    summary="截取页面",
    description="截取当前页面的屏幕截图",
)
async def screenshot(
    request: ScreenshotRequest,
    auth: TokenData | bool = Depends(verify_any_auth),
) -> ScreenshotResponse:
    """
    截取页面

    Args:
        request: 截图请求
        auth: 认证信息

    Returns:
        ScreenshotResponse: 截图结果
    """
    try:
        # 并发控制（截图内存占用较大，限制并发）
        concurrency_manager = get_concurrency_manager()
        async with concurrency_manager.screenshot_semaphore.acquire(timeout=30):
            manager = await get_browser_manager()
            result = await manager.screenshot(full_page=request.full_page)

            if not result.get("success"):
                raise HTTPException(status_code=400, detail=result.get("message"))

            return ScreenshotResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 截图API错误: {e}")
        raise HTTPException(status_code=500, detail=f"截图失败: {e}") from e


@browser_router.get(
    "/content",
    response_model=ContentResponse,
    summary="获取页面内容",
    description="获取当前页面的内容（标题、文本、链接等）",
)
async def get_content(
    auth: TokenData | bool = Depends(verify_any_auth),
) -> ContentResponse:
    """
    获取页面内容

    Args:
        auth: 认证信息

    Returns:
        ContentResponse: 页面内容
    """
    try:
        manager = await get_browser_manager()
        result = await manager.get_content()

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))

        return ContentResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取内容API错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取内容失败: {e}") from e


@browser_router.post(
    "/evaluate",
    response_model=EvaluateResponse,
    summary="执行JavaScript",
    description="在页面上下文中执行JavaScript代码（受沙箱限制）",
)
async def evaluate(
    request: EvaluateRequest,
    auth: TokenData | bool = Depends(verify_any_auth),
) -> EvaluateResponse:
    """
    执行JavaScript

    Args:
        request: 执行请求
        auth: 认证信息

    Returns:
        EvaluateResponse: 执行结果
    """
    try:
        # JavaScript沙箱验证
        is_safe, error_msg = validate_javascript_safety(request.script)
        if not is_safe:
            error_id = generate_error_id()
            logger.warning(f"⚠️ JavaScript沙箱违规: {error_msg} [{error_id}]")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "JavaScript沙箱违规",
                    "message": error_msg,
                    "error_id": error_id,
                },
            )

        # 并发控制
        concurrency_manager = get_concurrency_manager()
        async with concurrency_manager.js_semaphore.acquire(timeout=10):
            manager = await get_browser_manager()
            result = await manager.evaluate(script=request.script)

            if not result.get("success"):
                raise HTTPException(status_code=400, detail=result.get("message"))

            return EvaluateResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 执行JavaScript API错误: {e}")
        raise HTTPException(status_code=500, detail=f"执行失败: {e}") from e


@browser_router.post(
    "/task",
    response_model=TaskResponse,
    summary="执行智能任务",
    description="使用自然语言描述执行浏览器自动化任务",
)
async def execute_task(
    request: TaskRequest,
    auth: TokenData | bool = Depends(verify_any_auth),
) -> TaskResponse:
    """
    执行智能任务

    Args:
        request: 任务请求
        auth: 认证信息

    Returns:
        TaskResponse: 任务执行结果
    """
    try:
        # 并发控制
        concurrency_manager = get_concurrency_manager()
        async with concurrency_manager.task_semaphore.acquire(timeout=60):
            manager = await get_browser_manager()
            executor = TaskExecutor(browser_manager=manager)

            result = await executor.execute(
                task=request.task,
                url=request.url,
                max_steps=request.max_steps,
            )

            return TaskResponse(**result)

    except Exception as e:
        logger.error(f"❌ 任务执行API错误: {e}")
        return TaskResponse(
            success=False,
            task_id="unknown",
            task=request.task,
            status="failed",
            steps_taken=0,
            message=f"任务执行异常: {e}",
            error=str(e),
        )


# 导出
__all__ = ["browser_router"]
