"""
主服务模块
统一的服务入口和业务逻辑
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

from app.cookie_manager import cookie_manager
from app.extractors import BilibiliExtractor, DouyinExtractor, YouTubeExtractor
from app.models import (
    APIResponse,
    ExtractionRequest,
    ExtractionResult,
    ExtractionStats,
    HealthResponse,
    VideoMetadata,
    VideoPlatform,
)
from app.platform_detector import detect_video_platform, platform_router

logger = logging.getLogger(__name__)


class VideoMetadataService:
    """视频元信息提取服务"""
    
    def __init__(self):
        """初始化服务"""
        self.start_time = time.time()
        self.stats = ExtractionStats()
        
        # 注册提取器
        self._register_extractors()
        
        logger.info('视频元信息提取服务初始化完成')
    
    def _register_extractors(self) -> Any:
        """注册平台提取器"""
        try:
            platform_router.register_extractor(VideoPlatform.BILIBILI, BilibiliExtractor)
            platform_router.register_extractor(VideoPlatform.YOUTUBE, YouTubeExtractor)
            platform_router.register_extractor(VideoPlatform.DOUYIN, DouyinExtractor)
            
            logger.info('所有提取器注册完成')
            
        except Exception as e:
            logger.error(f"注册提取器失败: {str(e)}")
            raise
    
    async def extract_video_metadata(self, request: ExtractionRequest) -> ExtractionResult:
        """
        提取视频元信息（异步接口）
        
        Args:
            request: 提取请求
            
        Returns:
            提取结果
        """
        # 更新统计信息
        self.stats.total_requests += 1
        
        try:
            # 检测平台并验证URL
            platform, video_id = platform_router.detect_and_validate(request.url)
            
            logger.info(f"开始提取视频信息: 平台={platform.value}, 视频ID={video_id}")
            
            # 如果指定了平台，验证是否匹配
            if request.platform and request.platform != platform:
                raise ValueError(f"平台不匹配: 请求={request.platform.value}, 实际={platform.value}")
            
            # 获取对应的提取器
            extractor = platform_router.get_extractor(platform)
            
            # 执行提取
            result = await self._execute_extraction(extractor, request)
            
            # 更新统计信息
            self._update_stats(result)
            
            return result
            
        except Exception as e:
            logger.error(f"提取视频元信息失败: {str(e)}")
            
            # 更新失败统计
            self.stats.failed_extractions += 1
            
            # 返回错误结果
            return ExtractionResult(
                request_id=self._generate_request_id(),
                status=ExtractionStatus.FAILED,
                platform=platform if 'platform' in locals() else VideoPlatform.UNKNOWN,
                metadata=None,
                error_message=str(e),
                extraction_time=0.0,
                cached=False,
                created_at=datetime.now()
            )
    
    async def _execute_extraction(self, extractor, request: ExtractionRequest) -> ExtractionResult:
        """执行提取（异步包装）"""
        loop = asyncio.get_event_loop()
        
        # 在线程池中执行同步的提取操作
        result = await loop.run_in_executor(
            None, 
            extractor.extract, 
            request
        )
        
        return result
    
    def extract_video_metadata_sync(self, request: ExtractionRequest) -> ExtractionResult:
        """
        提取视频元信息（同步接口）
        
        Args:
            request: 提取请求
            
        Returns:
            提取结果
        """
        # 更新统计信息
        self.stats.total_requests += 1
        
        try:
            # 检测平台并验证URL
            platform, video_id = platform_router.detect_and_validate(request.url)
            
            logger.info(f"开始提取视频信息: 平台={platform.value}, 视频ID={video_id}")
            
            # 如果指定了平台，验证是否匹配
            if request.platform and request.platform != platform:
                raise ValueError(f"平台不匹配: 请求={request.platform.value}, 实际={platform.value}")
            
            # 获取对应的提取器
            extractor = platform_router.get_extractor(platform)
            
            # 执行提取
            result = extractor.extract(request)
            
            # 更新统计信息
            self._update_stats(result)
            
            return result
            
        except Exception as e:
            logger.error(f"提取视频元信息失败: {str(e)}")
            
            # 更新失败统计
            self.stats.failed_extractions += 1
            
            # 返回错误结果
            return ExtractionResult(
                request_id=self._generate_request_id(),
                status=ExtractionStatus.FAILED,
                platform=platform if 'platform' in locals() else VideoPlatform.UNKNOWN,
                metadata=None,
                error_message=str(e),
                extraction_time=0.0,
                cached=False,
                created_at=datetime.now()
            )
    
    def detect_platform(self, url: str) -> Dict[str, Any]:
        """
        检测视频平台
        
        Args:
            url: 视频URL
            
        Returns:
            检测结果
        """
        platform, video_id = detect_video_platform(url)
        
        return {
            'url': url,
            'platform': platform.value if platform != VideoPlatform.UNKNOWN else None,
            'video_id': video_id,
            'supported': platform != VideoPlatform.UNKNOWN,
        }
    
    def validate_url(self, url: str, expected_platform: str | None = None) -> Dict[str, Any]:
        """
        验证URL格式
        
        Args:
            url: 视频URL
            expected_platform: 期望的平台
            
        Returns:
            验证结果
        """
        try:
            platform = VideoPlatform(expected_platform) if expected_platform else None
            
            is_valid = platform_router.detector.validate_url_format(url, platform)
            
            return {
                'url': url,
                'valid': is_valid,
                'expected_platform': expected_platform,
                'detected_platform': None,  # 可以添加检测逻辑
            }
            
        except Exception as e:
            return {
                'url': url,
                'valid': False,
                'error': str(e),
                'expected_platform': expected_platform,
                'detected_platform': None,
            }
    
    def get_supported_platforms(self) -> Dict[str, Any]:
        """获取支持的平台列表"""
        return platform_router.get_detector_stats()
    
    def get_cookie_status(self, platform: str | None = None) -> Dict[str, Any]:
        """
        获取Cookie状态
        
        Args:
            platform: 指定平台，不指定则返回所有平台状态
            
        Returns:
            Cookie状态信息
        """
        if platform:
            try:
                platform_enum = VideoPlatform(platform)
                is_valid = cookie_manager.validate_cookies(platform_enum)
                cookies = cookie_manager.get_cookies_for_platform(platform_enum)
                
                return {
                    'platform': platform,
                    'valid': is_valid,
                    'cookie_count': len(cookies),
                    'last_update': cookie_manager.get_cache_info().get(platform, {}).get('last_update'),
                }
            except ValueError:
                return {
                    'platform': platform,
                    'error': f'不支持的平台: {platform}',
                }
        else:
            # 返回所有平台的状态
            status = {}
            
            for plat in VideoPlatform:
                if plat != VideoPlatform.UNKNOWN:
                    try:
                        is_valid = cookie_manager.validate_cookies(plat)
                        cookies = cookie_manager.get_cookies_for_platform(plat)
                        
                        status[plat.value] = {
                            'valid': is_valid,
                            'cookie_count': len(cookies),
                            'last_update': cookie_manager.get_cache_info().get(plat.value, {}).get('last_update'),
                        }
                    except Exception as e:
                        status[plat.value] = {
                            'error': str(e),
                        }
            
            return status
    
    def refresh_cookies(self, platform: str) -> Dict[str, Any]:
        """
        刷新指定平台的Cookie
        
        Args:
            platform: 平台名称
            
        Returns:
            刷新结果
        """
        try:
            platform_enum = VideoPlatform(platform)
            
            # 清除缓存
            cookie_manager.clear_cache(platform_enum)
            
            # 重新获取Cookie
            cookies = cookie_manager.get_cookies_for_platform(platform_enum, force_refresh=True)
            
            return {
                'platform': platform,
                'success': len(cookies) > 0,
                'cookie_count': len(cookies),
                'message': f'成功刷新 {platform} Cookie' if cookies else f'未能获取 {platform} Cookie',
            }
            
        except ValueError as e:
            return {
                'platform': platform,
                'success': False,
                'error': str(e),
            }
        except Exception as e:
            return {
                'platform': platform,
                'success': False,
                'error': f'刷新Cookie失败: {str(e)}',
            }
    
    def get_service_health(self) -> HealthResponse:
        """获取服务健康状态"""
        uptime = time.time() - self.start_time
        
        # 检查平台状态
        platform_status = {}
        
        for platform in VideoPlatform:
            if platform != VideoPlatform.UNKNOWN:
                try:
                    # 检查是否有对应的提取器
                    if platform in platform_router.extractors:
                        platform_status[platform.value] = True
                    else:
                        platform_status[platform.value] = False
                except Exception:
                    platform_status[platform.value] = False
        
        # 检查缓存状态
        cache_status = {
            'cookie_cache': cookie_manager.get_cache_info(),
            'stats': {
                'total_requests': self.stats.total_requests,
                'successful_extractions': self.stats.successful_extractions,
                'failed_extractions': self.stats.failed_extractions,
                'cache_hits': self.stats.cache_hits,
                'success_rate': (
                    self.stats.successful_extractions / max(self.stats.total_requests, 1) * 100
                ),
            }
        }
        
        return HealthResponse(
            status='healthy',
            version='1.0.0',
            uptime=uptime,
            platform_status=platform_status,
            cache_status=cache_status,
            timestamp=datetime.now()
        )
    
    def _update_stats(self, result: ExtractionResult) -> Any:
        """更新统计信息"""
        if result.status == ExtractionStatus.SUCCESS:
            self.stats.successful_extractions += 1
            
            # 更新平台统计
            if result.platform not in self.stats.platform_stats:
                self.stats.platform_stats[result.platform] = 0
            self.stats.platform_stats[result.platform] += 1
            
            # 更新平均提取时间
            if self.stats.successful_extractions > 0:
                total_time = self.stats.average_extraction_time * (self.stats.successful_extractions - 1) + result.extraction_time
                self.stats.average_extraction_time = total_time / self.stats.successful_extractions
            
        elif result.status == ExtractionStatus.FAILED:
            self.stats.failed_extractions += 1
        
        if result.cached:
            self.stats.cache_hits += 1
        
        self.stats.last_updated = datetime.now()
    
    def _generate_request_id(self) -> str:
        """生成请求ID"""
        import uuid
        return str(uuid.uuid4())


# 全局服务实例
video_service = VideoMetadataService()