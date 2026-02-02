"""
平台检测和路由模块
自动识别视频URL所属平台，并路由到相应的提取器
"""
import logging
from core.async_main import async_main
from core.logging_config import setup_logging
import re
from typing import Optional, Tuple
from urllib.parse import parse_qs, urlparse

from app.models import VideoPlatform

logger = setup_logging()


class PlatformDetector:
    """平台检测器"""
    
    def __init__(self):
        # 平台URL模式映射
        self.platform_patterns = {
            VideoPlatform.BILIBILI: [
                r'bilibili\.com/video/([a-z_a-Z0-9]+)',
                r'b23\.tv/([a-z_a-Z0-9]+)',
                r'bilibili\.com/medialist/detail/([a-z_a-Z0-9]+)',
                r'bilibili\.com/bangumi/media/([a-z_a-Z0-9]+)',
            ],
            VideoPlatform.YOUTUBE: [
                r'youtube\.com/watch\?v=([a-z_a-Z0-9_-]{11})',
                r'youtu\.be/([a-z_a-Z0-9_-]{11})',
                r'youtube\.com/embed/([a-z_a-Z0-9_-]{11})',
                r'youtube\.com/v/([a-z_a-Z0-9_-]{11})',
                r'youtube\.com/shorts/([a-z_a-Z0-9_-]{11})',
            ],
            VideoPlatform.DOUYIN: [
                r'douyin\.com/video/([a-z_a-Z0-9]+)',
                r'v\.douyin\.com/([a-z_a-Z0-9]+)',
                r'iesdouyin\.com/share/video/([a-z_a-Z0-9]+)',
                r'douyin\.com/user/([a-z_a-Z0-9]+)/video/([a-z_a-Z0-9]+)',
            ],
            VideoPlatform.KUAISHOU: [
                r'kuaishou\.com/short-video/([a-z_a-Z0-9]+)',
                r'v\.kuaishou\.com/([a-z_a-Z0-9]+)',
                r'kuaishou\.com/profile/([a-z_a-Z0-9]+)',
            ],
        }
        
        # 编译正则表达式
        self.compiled_patterns = {}
        for platform, patterns in self.platform_patterns.items():
            self.compiled_patterns[platform] = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
        
        # 域名映射（用于快速检测）
        self.domain_mapping = {
            'bilibili.com': VideoPlatform.BILIBILI,
            'b23.tv': VideoPlatform.BILIBILI,
            'youtube.com': VideoPlatform.YOUTUBE,
            'youtu.be': VideoPlatform.YOUTUBE,
            'douyin.com': VideoPlatform.DOUYIN,
            'v.douyin.com': VideoPlatform.DOUYIN,
            'iesdouyin.com': VideoPlatform.DOUYIN,
            'kuaishou.com': VideoPlatform.KUAISHOU,
            'v.kuaishou.com': VideoPlatform.KUAISHOU,
        }
    
    def detect_platform(self, url: str) -> Tuple[VideoPlatform, Optional[str]]:
        """
        检测视频URL所属平台并提取视频ID
        
        Args:
            url: 视频URL
            
        Returns:
            (平台, 视频ID) 元组
        """
        if not url or not isinstance(url, str):
            return VideoPlatform.UNKNOWN, None
        
        try:
            # 预处理URL
            url = url.strip()
            
            # 解析URL
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # 移除www前缀
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # 快速域名检测
            if domain in self.domain_mapping:
                platform = self.domain_mapping[domain]
                video_id = self._extract_video_id_by_platform(url, platform)
                return platform, video_id
            
            # 正则匹配检测
            for platform, patterns in self.compiled_patterns.items():
                for pattern in patterns:
                    match = pattern.search(url)
                    if match:
                        video_id = match.group(1) if match.groups() else None
                        logger.debug(f"检测到平台: {platform}, 视频ID: {video_id}")
                        return platform, video_id
            
            logger.warning(f"未能识别的平台: {url}")
            return VideoPlatform.UNKNOWN, None
            
        except Exception as e:
            logger.error(f"平台检测失败: {url}, 错误: {str(e)}")
            return VideoPlatform.UNKNOWN, None
    
    def _extract_video_id_by_platform(self, url: str, platform: VideoPlatform) -> str | None:
        """
        根据平台提取视频ID
        
        Args:
            url: 视频URL
            platform: 平台
            
        Returns:
            视频ID
        """
        try:
            if platform not in self.compiled_patterns:
                return None
            
            patterns = self.compiled_patterns[platform]
            for pattern in patterns:
                match = pattern.search(url)
                if match:
                    video_id = match.group(1) if match.groups() else None
                    if video_id:
                        return self._normalize_video_id(video_id, platform)
            
            return None
            
        except Exception as e:
            logger.error(f"提取视频ID失败: {url}, 平台: {platform}, 错误: {str(e)}")
            return None
    
    def _normalize_video_id(self, video_id: str, platform: VideoPlatform) -> str:
        """
        标准化视频ID
        
        Args:
            video_id: 原始视频ID
            platform: 平台
            
        Returns:
            标准化后的视频ID
        """
        if not video_id:
            return video_id
        
        # 去除前后空格
        video_id = video_id.strip()
        
        # 根据平台进行特殊处理
        if platform == VideoPlatform.YOUTUBE:
            # YouTube视频ID标准化
            video_id = video_id.strip()
            # 移除可能的查询参数
            if '?' in video_id:
                video_id = video_id.split('?')[0]
        
        elif platform == VideoPlatform.BILIBILI:
            # B站视频ID标准化
            if video_id.startswith('BV') or video_id.startswith('av'):
                video_id = video_id[2:]
        
        elif platform == VideoPlatform.DOUYIN:
            # 抖音视频ID标准化
            video_id = video_id.strip()
        
        return video_id
    
    def is_supported_platform(self, url: str) -> bool:
        """
        检查是否支持该URL的平台
        
        Args:
            url: 视频URL
            
        Returns:
            是否支持
        """
        platform, _ = self.detect_platform(url)
        return platform != VideoPlatform.UNKNOWN
    
    def get_all_supported_domains(self) -> list:
        """获取所有支持的域名列表"""
        return list(self.domain_mapping.keys())
    
    def validate_url_format(self, url: str, platform: VideoPlatform | None = None) -> bool:
        """
        验证URL格式是否正确
        
        Args:
            url: 视频URL
            platform: 指定平台，不指定则自动检测
            
        Returns:
            是否有效
        """
        if not url or not isinstance(url, str):
            return False
        
        try:
            # 基本URL格式验证
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # 如果指定了平台，验证是否符合该平台格式
            if platform:
                detected_platform, video_id = self.detect_platform(url)
                return detected_platform == platform and video_id is not None
            else:
                # 自动检测并验证
                detected_platform, video_id = self.detect_platform(url)
                return video_id is not None
            
        except Exception as e:
            logger.error(f"URL格式验证失败: {url}, 错误: {str(e)}")
            return False
    
    def get_platform_info(self, platform: VideoPlatform) -> dict:
        """
        获取平台信息
        
        Args:
            platform: 平台
            
        Returns:
            平台信息字典
        """
        info = {
            'platform': platform.value,
            'supported': platform in self.platform_patterns,
            'domains': [],
            'patterns': [],
        }
        
        # 获取相关域名
        for domain, plat in self.domain_mapping.items():
            if plat == platform:
                info['domains'].append(domain)
        
        # 获取匹配模式
        if platform in self.platform_patterns:
            info['patterns'] = self.platform_patterns[platform]
        
        return info


class PlatformRouter:
    """平台路由器"""
    
    def __init__(self):
        self.detector = PlatformDetector()
        self.extractors = {}
        
    def register_extractor(self, platform: VideoPlatform, extractor_class) -> None:
        """
        注册平台提取器
        
        Args:
            platform: 平台
            extractor_class: 提取器类
        """
        self.extractors[platform] = extractor_class
        logger.info(f"注册提取器: {platform} -> {extractor_class.__name__}")
    
    def get_extractor(self, platform: VideoPlatform) -> Any | None:
        """
        获取平台提取器
        
        Args:
            platform: 平台
            
        Returns:
            提取器实例
        """
        if platform not in self.extractors:
            raise ValueError(f"未找到平台 {platform} 的提取器")
        
        extractor_class = self.extractors[platform]
        return extractor_class()
    
    def route_to_extractor(self, url: str) -> Any:
        """
        根据URL路由到相应的提取器
        
        Args:
            url: 视频URL
            
        Returns:
            提取器实例
        """
        platform, video_id = self.detector.detect_platform(url)
        
        if platform == VideoPlatform.UNKNOWN:
            raise ValueError(f"不支持的视频URL: {url}")
        
        if platform not in self.extractors:
            raise ValueError(f"未找到平台 {platform} 的提取器")
        
        extractor = self.get_extractor(platform)
        return extractor, platform, video_id
    
    def detect_and_validate(self, url: str, expected_platform: VideoPlatform | None = None) -> Tuple[VideoPlatform, Optional[str]]:
        """
        检测并验证URL
        
        Args:
            url: 视频URL
            expected_platform: 期望的平台
            
        Returns:
            (平台, 视频ID) 元组
        """
        platform, video_id = self.detector.detect_platform(url)
        
        # 验证平台是否支持
        if platform == VideoPlatform.UNKNOWN:
            raise ValueError(f"不支持的视频URL: {url}")
        
        # 验证期望的平台
        if expected_platform and platform != expected_platform:
            raise ValueError(f"URL平台不匹配: 期望 {expected_platform}, 实际 {platform}")
        
        # 验证视频ID
        if not video_id:
            raise ValueError(f"无法从URL提取视频ID: {url}")
        
        return platform, video_id
    
    def get_supported_platforms(self) -> list:
        """获取支持的平台列表"""
        return list(self.extractors.keys())
    
    def get_detector_stats(self) -> dict:
        """获取检测器统计信息"""
        return {
            'supported_platforms': self.get_supported_platforms(),
            'supported_domains': self.detector.get_all_supported_domains(),
            'registered_extractors': list(self.extractors.keys()),
            'platform_info': {
                platform.value: self.detector.get_platform_info(platform)
                for platform in VideoPlatform
                if platform != VideoPlatform.UNKNOWN
            }
        }


# 全局平台路由器实例
platform_router = PlatformRouter()


def detect_video_platform(url: str) -> Tuple[VideoPlatform, Optional[str]]:
    """
    检测视频平台并提取视频ID
    
    Args:
        url: 视频URL
        
    Returns:
        (平台, 视频ID) 元组
    """
    return platform_router.detector.detect_platform(url)


def is_supported_url(url: str) -> bool:
    """
    检查是否支持该URL
    
    Args:
        url: 视频URL
        
    Returns:
        是否支持
    """
    return platform_router.detector.is_supported_platform(url)


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    test_urls = [
        'https://www.bilibili.com/video/BV1234567890',
        'https://www.youtube.com/watch?v=d_qw4w9_wg_xc_q',
        'https://v.douyin.com/abcdef123456',
        'https://www.kuaishou.com/short-video/123456',
        'https://example.com/video/123456',
    ]
    
    logger.info('=== 平台检测测试 ===')
    for url in test_urls:
        platform, video_id = detect_video_platform(url)
        logger.info(f"URL: {url}")
        logger.info(f"平台: {platform.value if platform != VideoPlatform.UNKNOWN else '未知'}")
        logger.info(f"视频ID: {video_id}")
        logger.info(f"支持: {is_supported_url(url)}")
        logger.info(str('-' * 50))