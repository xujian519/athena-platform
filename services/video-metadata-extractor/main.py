"""
FastAPI 主应用程序
提供RESTful API接口
"""
import logging
from core.async_main import async_main
from core.logging_config import setup_logging
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from app.models import (
    APIResponse,
    ExtractionRequest,
    ExtractionResult,
    VideoPlatform,
    VideoQuality,
)
from app.service import video_service
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 导入统一认证模块
from shared.auth.auth_middleware import create_auth_middleware, setup_cors

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用程序生命周期管理"""
    # 启动时执行
    logger.info('视频元信息提取服务启动中...')
    
    try:
        # 检查服务状态
        health = video_service.get_service_health()
        if health.status != 'healthy':
            logger.warning('服务启动时健康检查异常')
        
        logger.info('视频元信息提取服务启动完成')
        
        yield
        
    except Exception as e:
        logger.error(f"服务启动失败: {str(e)}")
        raise
    
    finally:
        # 关闭时执行
        logger.info('视频元信息提取服务关闭中...')


# 创建FastAPI应用
app = FastAPI(
    title='Athena 视频元信息提取服务',
    description='基于BiliNote架构的视频元信息提取API，支持B站、YouTube、抖音等平台',
    version='1.0.0',
    lifespan=lifespan,
    docs_url='/docs',
    redoc_url='/redoc'
)

# 配置CORS


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error(f"未处理的异常: {str(exc)}: {exc_info=True}")
    
    return JSONResponse(
        status_code=500,
        content=APIResponse(
            success=False,
            message=f"服务器内部错误: {str(exc)}",
            data=None
        ).dict()
    )


# API路由
@app.get('/', response_model=APIResponse)
async def root():
    """根路径，返回服务信息"""
    return APIResponse(
        success=True,
        message='Athena 视频元信息提取服务运行中',
        data={
            'service': 'video-metadata-extractor',
            'version': '1.0.0',
            'docs_url': '/docs',
            'health_url': '/health'
        }
    )


@app.get('/health', response_model=APIResponse)
async def health_check():
    """健康检查"""
    try:
        health = video_service.get_service_health()
        
        return APIResponse(
            success=True,
            message='服务健康',
            data=health.dict()
        )
        
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        
        return JSONResponse(
            status_code=503,
            content=APIResponse(
                success=False,
                message=f"服务异常: {str(e)}",
                data=None
            ).dict()
        )


@app.post('/extract', response_model=APIResponse)
async def extract_metadata(request: ExtractionRequest, background_tasks: BackgroundTasks):
    """
    提取视频元信息
    
    Args:
        request: 提取请求
        background_tasks: 后台任务
        
    Returns:
        提取结果
    """
    try:
        logger.info(f"收到提取请求: {request.url}")
        
        # 异步执行提取
        result = await video_service.extract_video_metadata(request)
        
        if result.status.value == 'success':
            return APIResponse(
                success=True,
                message='提取成功',
                data=result.dict()
            )
        else:
            return APIResponse(
                success=False,
                message=result.error_message or '提取失败',
                data=result.dict()
            )
            
    except Exception as e:
        logger.error(f"提取元信息失败: {str(e)}")
        
        raise HTTPException(
            status_code=500,
            detail=f"提取失败: {str(e)}"
        )


@app.post('/extract/sync', response_model=APIResponse)
async def extract_metadata_sync(request: ExtractionRequest):
    """
    提取视频元信息（同步版本）
    
    Args:
        request: 提取请求
        
    Returns:
        提取结果
    """
    try:
        logger.info(f"收到同步提取请求: {request.url}")
        
        # 同步执行提取
        result = video_service.extract_video_metadata_sync(request)
        
        if result.status.value == 'success':
            return APIResponse(
                success=True,
                message='提取成功',
                data=result.dict()
            )
        else:
            return APIResponse(
                success=False,
                message=result.error_message or '提取失败',
                data=result.dict()
            )
            
    except Exception as e:
        logger.error(f"同步提取元信息失败: {str(e)}")
        
        raise HTTPException(
            status_code=500,
            detail=f"提取失败: {str(e)}"
        )


@app.get('/detect', response_model=APIResponse)
async def detect_platform(url: str = Query(..., description='视频URL')):
    """
    检测视频平台
    
    Args:
        url: 视频URL
        
    Returns:
        检测结果
    """
    try:
        result = video_service.detect_platform(url)
        
        return APIResponse(
            success=True,
            message='平台检测完成',
            data=result
        )
        
    except Exception as e:
        logger.error(f"平台检测失败: {str(e)}")
        
        raise HTTPException(
            status_code=500,
            detail=f"检测失败: {str(e)}"
        )


@app.get('/validate', response_model=APIResponse)
async def validate_url(
    url: str = Query(..., description='视频URL'),
    expected_platform: Optional[str] = Query(None, description='期望的平台')
):
    """
    验证URL格式
    
    Args:
        url: 视频URL
        expected_platform: 期望的平台
        
    Returns:
        验证结果
    """
    try:
        result = video_service.validate_url(url, expected_platform)
        
        return APIResponse(
            success=True,
            message='URL验证完成',
            data=result
        )
        
    except Exception as e:
        logger.error(f"URL验证失败: {str(e)}")
        
        raise HTTPException(
            status_code=500,
            detail=f"验证失败: {str(e)}"
        )


@app.get('/platforms', response_model=APIResponse)
async def get_supported_platforms():
    """获取支持的平台列表"""
    try:
        result = video_service.get_supported_platforms()
        
        return APIResponse(
            success=True,
            message='获取平台列表成功',
            data=result
        )
        
    except Exception as e:
        logger.error(f"获取平台列表失败: {str(e)}")
        
        raise HTTPException(
            status_code=500,
            detail=f"获取失败: {str(e)}"
        )


@app.get('/cookies/status', response_model=APIResponse)
async def get_cookie_status(
    platform: Optional[str] = Query(None, description='指定平台，不指定则返回所有平台')
):
    """获取Cookie状态"""
    try:
        result = video_service.get_cookie_status(platform)
        
        return APIResponse(
            success=True,
            message='获取Cookie状态成功',
            data=result
        )
        
    except Exception as e:
        logger.error(f"获取Cookie状态失败: {str(e)}")
        
        raise HTTPException(
            status_code=500,
            detail=f"获取失败: {str(e)}"
        )


@app.post('/cookies/refresh/{platform}', response_model=APIResponse)
async def refresh_cookies(platform: str):
    """刷新指定平台的Cookie"""
    try:
        result = video_service.refresh_cookies(platform)
        
        if result.get('success', False):
            return APIResponse(
                success=True,
                message=result.get('message', '刷新成功'),
                data=result
            )
        else:
            return APIResponse(
                success=False,
                message=result.get('error', '刷新失败'),
                data=result
            )
            
    except Exception as e:
        logger.error(f"刷新Cookie失败: {str(e)}")
        
        raise HTTPException(
            status_code=500,
            detail=f"刷新失败: {str(e)}"
        )


@app.get('/stats', response_model=APIResponse)
async def get_service_stats():
    """获取服务统计信息"""
    try:
        health = video_service.get_service_health()
        stats = health.cache_status.get('stats', {})
        
        return APIResponse(
            success=True,
            message='获取统计信息成功',
            data={
                'uptime': health.uptime,
                'stats': stats,
                'platform_status': health.platform_status
            }
        )
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        
        raise HTTPException(
            status_code=500,
            detail=f"获取失败: {str(e)}"
        )


# 测试接口
@app.get('/test', response_model=APIResponse)
async def test_service():
    """测试接口，用于验证服务功能"""
    try:
        # 测试平台检测
        test_urls = {
            'bilibili': 'https://www.bilibili.com/video/BV1234567890',
            'youtube': 'https://www.youtube.com/watch?v=d_qw4w9_wg_xc_q',
            'douyin': 'https://v.douyin.com/abcdef123456',
        }
        
        detection_results = {}
        for platform, url in test_urls.items():
            try:
                result = video_service.detect_platform(url)
                detection_results[platform] = {
                    'url': url,
                    'detected_platform': result.get('platform'),
                    'supported': result.get('supported', False),
                    'success': True
                }
            except Exception as e:
                detection_results[platform] = {
                    'url': url,
                    'success': False,
                    'error': str(e)
                }
        
        # 获取Cookie状态
        cookie_status = video_service.get_cookie_status()
        
        # 获取平台支持情况
        platforms_info = video_service.get_supported_platforms()
        
        return APIResponse(
            success=True,
            message='服务测试完成',
            data={
                'timestamp': video_service.get_service_health().timestamp.isoformat(),
                'platform_detection': detection_results,
                'cookie_status': cookie_status,
                'supported_platforms': platforms_info,
                'service_health': video_service.get_service_health().dict()
            }
        )
        
    except Exception as e:
        logger.error(f"服务测试失败: {str(e)}")
        
        raise HTTPException(
            status_code=500,
            detail=f"测试失败: {str(e)}"
        )


if __name__ == '__main__':
    import uvicorn

    # 直接运行时使用uvicorn
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=8080,
        reload=True,
        log_level='info'
    )