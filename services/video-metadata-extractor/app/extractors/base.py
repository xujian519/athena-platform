"""
基础提取器抽象类
定义统一的提取器接口
"""
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from app.cookie_manager import get_cookie_header, validate_platform_cookies
from app.models import (
    ExtractionRequest,
    ExtractionResult,
    ExtractionStatus,
    VideoMetadata,
    VideoPlatform,
)

logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """视频元信息提取器基类"""

    def __init__(self, platform: VideoPlatform):
        """
        初始化提取器

        Args:
            platform: 所属平台
        """
        self.platform = platform
        self.session = None  # HTTP会话对象
        self.last_request_time = 0  # 上次请求时间
        self.min_request_interval = 1.0  # 最小请求间隔（秒）

    @abstractmethod
    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        """
        提取视频元信息

        Args:
            request: 提取请求

        Returns:
            提取结果
        """
        pass

    def _rate_limit(self) -> Any:
        """请求频率限制"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time

        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            logger.debug(f"请求频率限制，等待 {sleep_time:.2f} 秒")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _validate_cookies(self) -> bool:
        """
        验证Cookie是否有效

        Returns:
            是否有效
        """
        return validate_platform_cookies(self.platform)

    def _get_cookie_header(self, force_refresh: bool = False) -> str:
        """
        获取Cookie请求头

        Args:
            force_refresh: 是否强制刷新

        Returns:
            Cookie字符串
        """
        return get_cookie_header(self.platform, force_refresh)

    def _prepare_request_headers(self, force_refresh_cookies: bool = False) -> dict[str, str]:
        """
        准备请求头

        Args:
            force_refresh_cookies: 是否强制刷新Cookie

        Returns:
            请求头字典
        """
        headers = {
            'User-Agent': self._get_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }

        # 添加平台特定的请求头
        platform_headers = self._get_platform_headers()
        headers.update(platform_headers)

        # 添加Cookie（如果需要）
        if self._requires_cookies():
            cookie_header = self._get_cookie_header(force_refresh_cookies)
            if cookie_header:
                headers['Cookie'] = cookie_header
            else:
                logger.warning(f"未能获取 {self.platform} 的Cookie")

        return headers

    def _get_user_agent(self) -> str:
        """获取User-Agent"""
        return 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

    def _get_platform_headers(self) -> dict[str, str]:
        """获取平台特定的请求头"""
        return {}

    def _requires_cookies(self) -> bool:
        """是否需要Cookie"""
        return False

    def _parse_duration(self, duration_str: str) -> int | None:
        """
        解析时长字符串为秒数

        Args:
            duration_str: 时长字符串，如 '3:45', '02:15:30'

        Returns:
            时长（秒）
        """
        if not duration_str:
            return None

        try:
            # 处理格式: "3:45", "02:15:30"
            parts = duration_str.split(':')

            if len(parts) == 2:  # MM:SS
                minutes, seconds = int(parts[0]), int(parts[1])
                return minutes * 60 + seconds
            elif len(parts) == 3:  # HH:MM:SS
                hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
                return hours * 3600 + minutes * 60 + seconds
            else:
                logger.warning(f"不支持的时长格式: {duration_str}")
                return None

        except (ValueError, IndexError) as e:
            logger.error(f"解析时长失败: {duration_str}, 错误: {str(e)}")
            return None

    def _parse_view_count(self, view_str: str) -> int | None:
        """
        解析播放量字符串为数字

        Args:
            view_str: 播放量字符串，如 '1.2万', '3456'

        Returns:
            播放量
        """
        if not view_str:
            return None

        try:
            # 移除空格和中文单位
            view_str = view_str.strip().replace(' ', '')

            # 处理中文单位
            if '万' in view_str:
                number = float(view_str.replace('万', ''))
                return int(number * 10000)
            elif '千' in view_str or 'k' in view_str.lower():
                number = float(view_str.replace('千', '').replace('k', '').replace('K', ''))
                return int(number * 1000)
            elif '亿' in view_str:
                number = float(view_str.replace('亿', ''))
                return int(number * 100000000)
            else:
                # 纯数字
                return int(float(view_str))

        except (ValueError, TypeError) as e:
            logger.error(f"解析播放量失败: {view_str}, 错误: {str(e)}")
            return None

    def _clean_text(self, text: str) -> str:
        """
        清理文本内容

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        if not text:
            return ''

        # 移除多余的空白字符
        text = ' '.join(text.split())

        # 移除HTML标签（简单处理）
        import re
        text = re.sub(r'<[^>]+>', '', text)

        # 移除特殊字符
        text = text.replace('\xa0', ' ').replace('\u200b', '')

        return text.strip()

    def _create_metadata(self, video_data: dict[str, Any]) -> VideoMetadata:
        """
        创建视频元信息对象

        Args:
            video_data: 视频数据字典

        Returns:
            视频元信息对象
        """
        return VideoMetadata(
            video_id=video_data.get('video_id', ''),
            title=self._clean_text(video_data.get('title', '')),
            description=self._clean_text(video_data.get('description', '')),
            duration=video_data.get('duration'),
            platform=self.platform,
            author=self._clean_text(video_data.get('author', '')),
            author_id=video_data.get('author_id'),
            publish_date=video_data.get('publish_date'),
            view_count=video_data.get('view_count'),
            like_count=video_data.get('like_count'),
            cover_url=video_data.get('cover_url'),
            tags=video_data.get('tags', []),
            category=video_data.get('category'),
            language=video_data.get('language'),
            resolution=video_data.get('resolution'),
            file_size=video_data.get('file_size'),
            format=video_data.get('format'),
            raw_data=video_data.get('raw_data', {}),
            extracted_at=datetime.now()
        )

    def _create_result(self, request: ExtractionRequest, metadata: VideoMetadata | None = None,
                      error_message: str | None = None, extraction_time: float = 0.0,
                      cached: bool = False) -> ExtractionResult:
        """
        创建提取结果对象

        Args:
            request: 原始请求
            metadata: 视频元信息
            error_message: 错误信息
            extraction_time: 提取耗时
            cached: 是否来自缓存

        Returns:
            提取结果
        """
        if metadata:
            status = ExtractionStatus.SUCCESS
        elif error_message:
            status = ExtractionStatus.FAILED
        else:
            status = ExtractionStatus.PENDING

        return ExtractionResult(
            request_id=self._generate_request_id(),
            status=status,
            platform=self.platform,
            metadata=metadata,
            error_message=error_message,
            extraction_time=extraction_time,
            cached=cached,
            created_at=datetime.now()
        )

    def _generate_request_id(self) -> str:
        """生成请求ID"""
        import uuid
        return str(uuid.uuid4())

    def _handle_error(self, error: Exception, request: ExtractionRequest) -> ExtractionResult:
        """
        处理错误

        Args:
            error: 异常对象
            request: 原始请求

        Returns:
            错误结果
        """
        error_message = f"{self.platform} 提取失败: {str(error)}"
        logger.error(error_message)

        return self._create_result(
            request=request,
            error_message=error_message
        )

    def validate_request(self, request: ExtractionRequest) -> bool:
        """
        验证请求参数

        Args:
            request: 提取请求

        Returns:
            是否有效
        """
        if not request.url:
            logger.error('URL不能为空')
            return False

        if request.timeout <= 0:
            logger.error('超时时间必须大于0')
            return False

        return True

    def get_platform_info(self) -> dict[str, Any]:
        """
        获取平台信息

        Returns:
            平台信息字典
        """
        return {
            'platform': self.platform.value,
            'requires_cookies': self._requires_cookies(),
            'supports_cookie_refresh': True,
            'rate_limit': self.min_request_interval,
            'extractor_class': self.__class__.__name__,
        }
