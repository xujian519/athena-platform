"""
YouTube视频元信息提取器
基于yt-dlp获取YouTube视频信息
"""
import logging
import time

# 配置日志 - 必须在导入检查之前
logger = logging.getLogger(__name__)

try:
    import yt_dlp
except ImportError:
    logger.info('需要安装 yt-dlp: pip install yt-dlp')
    yt_dlp = None

from app.extractors.base import BaseExtractor
from app.models import ExtractionRequest, ExtractionResult, VideoMetadata, VideoPlatform


class YouTubeExtractor(BaseExtractor):
    """YouTube视频元信息提取器"""

    def __init__(self):
        super().__init__(VideoPlatform.YOUTUBE)
        self.min_request_interval = 1.0  # YouTube也需要适度的请求间隔

    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        """
        提取YouTube视频元信息

        Args:
            request: 提取请求

        Returns:
            提取结果
        """
        start_time = time.time()

        try:
            # 验证请求
            if not self.validate_request(request):
                return self._create_result(
                    request=request,
                    error_message='请求参数无效'
                )

            # 速率限制
            self._rate_limit()

            if not yt_dlp:
                raise ImportError('yt-dlp未安装，请运行: pip install yt-dlp')

            # 使用yt-dlp提取信息
            metadata = self._extract_with_ytdlp(request)

            if metadata:
                extraction_time = time.time() - start_time
                return self._create_result(
                    request=request,
                    metadata=metadata,
                    extraction_time=extraction_time,
                    cached=False
                )
            else:
                extraction_time = time.time() - start_time
                return self._create_result(
                    request=request,
                    error_message='无法提取YouTube视频信息',
                    extraction_time=extraction_time
                )

        except Exception as e:
            return self._handle_error(e, request)

    def _extract_with_ytdlp(self, request: ExtractionRequest) -> VideoMetadata | None:
        """使用yt-dlp提取YouTube视频信息"""
        # 配置yt-dlp选项
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'no_download': True,
        }

        # 添加自定义请求头
        headers = self._prepare_request_headers()
        if headers:
            ydl_opts['http_headers'] = headers

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(request.url, download=False)

                # 转换为我们的格式
                video_data = {
                    'video_id': info.get('id', ''),
                    'title': info.get('title', ''),
                    'description': info.get('description', ''),
                    'duration': info.get('duration'),
                    'author': info.get('uploader', ''),
                    'author_id': info.get('uploader_id', ''),
                    'publish_date': self._parse_publish_date(info.get('upload_date')),
                    'view_count': info.get('view_count'),
                    'like_count': info.get('like_count'),
                    'cover_url': info.get('thumbnail'),
                    'tags': info.get('tags', []),
                    'category': info.get('categories', [''])[0] if info.get('categories') else None,
                    'language': info.get('language'),
                    'resolution': self._extract_resolution(info),
                    'raw_data': info if request.include_raw_data else {},
                }

                return self._create_metadata(video_data)

        except Exception as e:
            logger.error(f"yt-dlp提取YouTube视频失败: {str(e)}")
            raise

    def _parse_publish_date(self, upload_date: str | None) -> time | None:
        """解析发布日期"""
        if not upload_date:
            return None

        try:
            # yt-dlp返回的日期格式: YYYYMMDD
            from datetime import datetime
            return datetime.strptime(upload_date, '%Y%m%d')
        except ValueError:
            return None

    def _extract_resolution(self, info: dict) -> str | None:
        """提取视频分辨率"""
        try:
            # 尝试从format信息中提取最高分辨率
            formats = info.get('formats', [])
            if formats:
                # 找到视频格式的最高分辨率
                video_formats = [f for f in formats if f.get('vcodec') != 'none']
                if video_formats:
                    # 按分辨率排序
                    video_formats.sort(key=lambda x: x.get('height', 0), reverse=True)
                    best_format = video_formats[0]
                    height = best_format.get('height')
                    width = best_format.get('width')

                    if height and width:
                        return f"{width}x{height}"
                    elif height:
                        return f"{height}p"

            # 备用方法：直接从基本信息获取
            height = info.get('height')
            width = info.get('width')

            if height and width:
                return f"{width}x{height}"
            elif height:
                return f"{height}p"

            return None

        except Exception as e:
            logger.error(f"提取分辨率失败: {str(e)}")
            return None

    def _get_platform_headers(self) -> dict:
        """获取YouTube特定的请求头"""
        return {
            'Referer': 'https://www.youtube.com',
            'Origin': 'https://www.youtube.com',
        }

    def _requires_cookies(self) -> bool:
        """YouTube不一定需要Cookie，但有Cookie可能获取更多信息"""
        return False  # 设为False，因为YouTube对Cookie要求不严格

    def get_video_quality_info(self, info: dict) -> dict:
        """获取视频质量信息（可选功能）"""
        quality_info = {
            'available_formats': [],
            'best_quality': None,
            'worst_quality': None,
        }

        try:
            formats = info.get('formats', [])

            for fmt in formats:
                if fmt.get('vcodec') != 'none':  # 只包含视频的格式
                    format_info = {
                        'format_id': fmt.get('format_id'),
                        'ext': fmt.get('ext'),
                        'resolution': f"{fmt.get('width', 0)}x{fmt.get('height', 0)}",
                        'fps': fmt.get('fps'),
                        'filesize': fmt.get('filesize'),
                        'quality': fmt.get('format_note'),
                    }
                    quality_info['available_formats'].append(format_info)

            # 确定最佳和最差质量
            if quality_info['available_formats']:
                # 按分辨率排序
                quality_info['available_formats'].sort(
                    key=lambda x: x['resolution'],
                    reverse=True
                )
                quality_info['best_quality'] = quality_info['available_formats'][0]
                quality_info['worst_quality'] = quality_info['available_formats'][-1]

        except Exception as e:
            logger.error(f"获取质量信息失败: {str(e)}")

        return quality_info
