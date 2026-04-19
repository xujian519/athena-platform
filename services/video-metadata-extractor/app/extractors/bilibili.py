"""
B站视频元信息提取器
基于yt-dlp和官方API获取B站视频信息
"""
import logging
import time
from datetime import datetime

import requests

# 配置日志 - 必须在导入检查之前
logger = logging.getLogger(__name__)

try:
    import yt_dlp
except ImportError:
    logger.info('需要安装 yt-dlp: pip install yt-dlp')
    yt_dlp = None

from app.extractors.base import BaseExtractor
from app.models import (
    ExtractionRequest,
    ExtractionResult,
    VideoMetadata,
    VideoPlatform,
)


class BilibiliExtractor(BaseExtractor):
    """B站视频元信息提取器"""

    def __init__(self):
        super().__init__(VideoPlatform.BILIBILI)
        self.api_base = 'https://api.bilibili.com/x/web-interface'
        self.min_request_interval = 0.5  # B站API限制较严格

    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        """
        提取B站视频元信息

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

            # 尝试多种方法提取信息
            metadata = None

            # 方法1: 使用yt-dlp（推荐）
            if yt_dlp:
                try:
                    metadata = self._extract_with_ytdlp(request)
                    logger.info('使用yt-dlp成功提取B站视频信息')
                except Exception as e:
                    logger.warning(f"yt-dlp提取失败: {str(e)}")

            # 方法2: 使用B站API（备选）
            if not metadata:
                try:
                    metadata = self._extract_with_api(request)
                    logger.info('使用B站API成功提取视频信息')
                except Exception as e:
                    logger.warning(f"B站API提取失败: {str(e)}")

            # 方法3: 网页解析（最后手段）
            if not metadata:
                try:
                    metadata = self._extract_with_webpage(request)
                    logger.info('使用网页解析成功提取视频信息')
                except Exception as e:
                    logger.warning(f"网页解析提取失败: {str(e)}")

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
                    error_message='所有提取方法都失败了',
                    extraction_time=extraction_time
                )

        except Exception as e:
            return self._handle_error(e, request)

    def _extract_with_ytdlp(self, request: ExtractionRequest) -> VideoMetadata | None:
        """使用yt-dlp提取视频信息"""
        if not yt_dlp:
            raise ImportError('yt-dlp未安装')

        # 配置yt-dlp选项
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'cookiefile': None,  # 不使用cookie文件
            'no_download': True,
        }

        # 如果有Cookie，添加到配置中
        cookie_header = self._get_cookie_header()
        if cookie_header:
            ydl_opts['http_headers'] = {'Cookie': cookie_header}

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
                    'raw_data': info if request.include_raw_data else {},
                }

                return self._create_metadata(video_data)

        except Exception as e:
            logger.error(f"yt-dlp提取失败: {str(e)}")
            raise

    def _extract_with_api(self, request: ExtractionRequest) -> VideoMetadata | None:
        """使用B站API提取视频信息"""
        # 从URL提取视频ID
        video_id = self._extract_video_id(request.url)
        if not video_id:
            raise ValueError('无法从URL提取视频ID')

        # 准备请求头
        headers = self._prepare_request_headers()

        # 获取视频基本信息
        api_url = f"{self.api_base}/view?bvid={video_id}"
        response = requests.get(api_url, headers=headers, timeout=request.timeout)

        if response.status_code != 200:
            raise Exception(f"API请求失败: {response.status_code}")

        data = response.json()

        if data.get('code') != 0:
            raise Exception(f"API返回错误: {data.get('message')}")

        video_info = data['data']

        # 解析视频数据
        video_data = {
            'video_id': video_id,
            'title': video_info.get('title', ''),
            'description': video_info.get('desc', ''),
            'duration': video_info.get('duration'),
            'author': video_info.get('owner', {}).get('name', ''),
            'author_id': str(video_info.get('owner', {}).get('mid', '')),
            'publish_date': datetime.fromtimestamp(video_info.get('pubdate', 0)),
            'view_count': video_info.get('stat', {}).get('view'),
            'like_count': video_info.get('stat', {}).get('like'),
            'cover_url': video_info.get('pic'),
            'tags': [tag.get('tag_name', '') for tag in video_info.get('tag', [])],
            'category': video_info.get('tname'),
            'raw_data': video_info if request.include_raw_data else {},
        }

        return self._create_metadata(video_data)

    def _extract_with_webpage(self, request: ExtractionRequest) -> VideoMetadata | None:
        """从网页HTML解析视频信息"""
        headers = self._prepare_request_headers()

        response = requests.get(request.url, headers=headers, timeout=request.timeout)

        if response.status_code != 200:
            raise Exception(f"网页请求失败: {response.status_code}")

        # 解析HTML，提取script中的视频信息
        html_content = response.text

        try:
            import json
            import re

            # 查找包含视频信息的script标签
            pattern = r'__INITIAL_STATE__\s*=\s*({.+?});'
            match = re.search(pattern, html_content)

            if match:
                initial_state = json.loads(match.group(1))

                # 提取视频信息
                video_data_path = initial_state.get('video_data', {})

                if video_data_path:
                    video_data = {
                        'video_id': video_data_path.get('bvid', ''),
                        'title': video_data_path.get('title', ''),
                        'description': video_data_path.get('desc', ''),
                        'duration': video_data_path.get('duration'),
                        'author': video_data_path.get('owner', {}).get('name', ''),
                        'author_id': str(video_data_path.get('owner', {}).get('mid', '')),
                        'publish_date': datetime.fromtimestamp(video_data_path.get('pubdate', 0)),
                        'view_count': video_data_path.get('stat', {}).get('view'),
                        'like_count': video_data_path.get('stat', {}).get('like'),
                        'cover_url': video_data_path.get('pic'),
                        'tags': [tag.get('tag_name', '') for tag in video_data_path.get('tag', [])],
                        'category': video_data_path.get('tname'),
                        'raw_data': video_data_path if request.include_raw_data else {},
                    }

                    return self._create_metadata(video_data)

            raise Exception('无法从网页中提取视频信息')

        except Exception as e:
            logger.error(f"网页解析失败: {str(e)}")
            raise

    def _extract_video_id(self, url: str) -> str | None:
        """从URL提取视频ID"""
        import re

        # BV号
        bv_match = re.search(r'BV([a-z_a-Z0-9]+)', url)
        if bv_match:
            return f"BV{bv_match.group(1)}"

        # AV号
        av_match = re.search(r'av(\d+)', url)
        if av_match:
            return f"BV{av_match.group(1)}"  # yt-dlp统一使用BV号

        return None

    def _parse_publish_date(self, upload_date: str | None) -> datetime | None:
        """解析发布日期"""
        if not upload_date:
            return None

        try:
            # yt-dlp返回的日期格式: YYYYMMDD
            return datetime.strptime(upload_date, '%Y%m%d')
        except ValueError:
            return None

    def _get_platform_headers(self) -> dict[str, str]:
        """获取B站特定的请求头"""
        return {
            'Referer': 'https://www.bilibili.com',
            'Origin': 'https://www.bilibili.com',
        }

    def _requires_cookies(self) -> bool:
        """B站API在有Cookie时能获取更多信息"""
        return True
