"""
抖音视频元信息提取器
基于BiliNote的抖音提取逻辑，集成Cookie自动获取
"""
import hashlib
import json
import logging
import random
import string
import time
from datetime import datetime
from typing import Any, Dict, Optional
from urllib.parse import quote, urlencode

import requests
from app.extractors.base import BaseExtractor
from app.models import ExtractionRequest, ExtractionResult, VideoMetadata, VideoPlatform

logger = logging.getLogger(__name__)


class DouyinExtractor(BaseExtractor):
    """抖音视频元信息提取器"""
    
    def __init__(self):
        super().__init__(VideoPlatform.DOUYIN)
        self.api_base = 'https://www.douyin.com'
        self.min_request_interval = 2.0  # 抖音反爬严格，需要更长间隔
        self._ms_token_cache = {}
        
    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        """
        提取抖音视频元信息
        
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
            
            # 抖音必须有有效的Cookie
            if not self._validate_cookies():
                logger.warning('抖音Cookie无效，尝试刷新...')
                # 尝试强制刷新Cookie
                self._get_cookie_header(force_refresh=True)
                
                if not self._validate_cookies():
                    return self._create_result(
                        request=request,
                        error_message='抖音Cookie无效或已过期，请先在浏览器中登录抖音'
                    )
            
            # 使用抖音API提取信息
            metadata = self._extract_with_api(request)
            
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
                    error_message='无法提取抖音视频信息',
                    extraction_time=extraction_time
                )
                
        except Exception as e:
            return self._handle_error(e, request)
    
    def _extract_with_api(self, request: ExtractionRequest) -> VideoMetadata | None:
        """使用抖音API提取视频信息"""
        # 提取视频ID
        video_id = self._extract_video_id(request.url)
        if not video_id:
            raise ValueError('无法从URL提取视频ID')
        
        # 准备请求参数
        params = self._prepare_api_params(video_id)
        headers = self._prepare_request_headers(force_refresh_cookies=False)
        
        # 构造请求URL
        full_url = f"{self.api_base}/aweme/v1/web/aweme/detail/"
        
        try:
            response = requests.get(
                full_url, 
                params=params, 
                headers=headers, 
                timeout=request.timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"API请求失败: {response.status_code}")
            
            data = response.json()
            
            # 检查API响应
            if not data.get('aweme_detail'):
                # 尝试解析错误信息
                if data.get('status_msg'):
                    raise Exception(f"抖音API错误: {data.get('status_msg')}")
                else:
                    raise Exception('抖音API返回的数据格式异常')
            
            video_info = data['aweme_detail']
            
            # 解析视频数据
            video_data = {
                'video_id': video_id,
                'title': self._extract_title(video_info),
                'description': self._extract_description(video_info),
                'duration': video_info.get('video', {}).get('duration', 0) // 1000,  # 毫秒转秒
                'author': video_info.get('author', {}).get('nickname', ''),
                'author_id': str(video_info.get('author', {}).get('unique_id', '')),
                'publish_date': self._parse_publish_date(video_info.get('create_time')),
                'view_count': video_info.get('statistics', {}).get('play_count'),
                'like_count': video_info.get('statistics', {}).get('digg_count'),
                'cover_url': self._extract_cover_url(video_info),
                'tags': self._extract_tags(video_info),
                'category': self._extract_category(video_info),
                'music_title': video_info.get('music', {}).get('title', ''),
                'raw_data': video_info if request.include_raw_data else {},
            }
            
            return self._create_metadata(video_data)
            
        except requests.RequestException as e:
            logger.error(f"抖音API请求异常: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"解析抖音视频数据失败: {str(e)}")
            raise
    
    def _prepare_api_params(self, video_id: str) -> Dict[str, Any]:
        """准备API请求参数"""
        # 基础参数
        params = {
            'device_platform': 'webapp',
            'aid': '6383',
            'channel': 'channel_pc_web',
            'pc_client_type': 1,
            'version_code': '290100',
            'version_name': '29.1.0',
            'cookie_enabled': 'true',
            'screen_width': '1920',
            'screen_height': '1080',
            'browser_language': 'zh-CN',
            'browser_platform': 'Win32',
            'browser_name': 'Chrome',
            'browser_version': '120.0.0.0',
            'browser_online': 'true',
            'engine_name': 'Blink',
            'engine_version': '120.0.0.0',
            'os_name': 'Windows',
            'os_version': '10',
            'cpu_core_num': '12',
            'device_memory': '8',
            'platform': 'PC',
            'downlink': '10',
            'effective_type': '4g',
            'from_user_page': '1',
            'locate_query': 'false',
            'need_time_list': '1',
            'pc_libra_divert': 'Windows',
            'publish_video_strategy_type': '2',
            'round_trip_time': '0',
            'show_live_replay_strategy': '1',
            'time_list_query': '0',
            'whale_cut_token': '',
            'update_version_code': '170400',
            'ms_token': self._generate_ms_token(),
            'aweme_id': video_id,
        }
        
        # 生成a_bogus参数
        a_bogus = self._generate_a_bogus(params)
        params['a_bogus'] = quote(a_bogus, safe='')
        
        return params
    
    def _generate_ms_token(self) -> str:
        """生成msToken（简化版本）"""
        # 检查缓存
        cache_key = 'douyin_ms_token'
        if cache_key in self._ms_token_cache:
            token, timestamp = self._ms_token_cache[cache_key]
            # 如果缓存未过期（1小时），直接返回
            if time.time() - timestamp < 3600:
                return token
        
        # 生成新的msToken
        # 这里使用简化的生成逻辑，实际项目中可能需要更复杂的算法
        chars = string.ascii_letters + string.digits + '-_'
        token = ''.join(random.choices(chars, k=126))  # 抖音msToken通常是126位
        
        # 缓存token
        self._ms_token_cache[cache_key] = (token, time.time())
        
        return token
    
    def _generate_a_bogus(self, params: Dict[str, Any]) -> str:
        """生成a_bogus参数（简化版本）"""
        # 这是一个简化的实现，实际BiliNote中使用了更复杂的算法
        param_str = json.dumps(params, separators=(',', ':'), sort_keys=True)
        
        # 使用MD5生成签名（实际抖音算法更复杂）
        md5_hash = hashlib.md5(param_str.encode(), usedforsecurity=False).hexdigest()
        
        # 添加随机字符
        random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        a_bogus = f"DFSzsKNyeB8jQ{md5_hash[:16]}{random_part}7"
        
        return a_bogus
    
    def _extract_video_id(self, url: str) -> str | None:
        """从URL提取视频ID"""
        import re

        # 匹配各种抖音URL格式
        patterns = [
            r'/video/([a-z_a-Z0-9]+)',
            r'aweme_id=([a-z_a-Z0-9]+)',
            r'v\.douyin\.com/([a-z_a-Z0-9]+)',
            r'iesdouyin\.com/share/video/([a-z_a-Z0-9]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_title(self, video_info: Dict[str, Any]) -> str:
        """提取视频标题"""
        # 抖音视频通常没有独立的标题，使用描述作为标题
        desc = video_info.get('desc', '')
        
        # 如果描述太长，截取前50个字符
        if len(desc) > 50:
            desc = desc[:47] + '...'
        
        return desc
    
    def _extract_description(self, video_info: Dict[str, Any]) -> str:
        """提取视频描述"""
        return video_info.get('desc', '')
    
    def _extract_cover_url(self, video_info: Dict[str, Any]) -> str | None:
        """提取封面URL"""
        video_data = video_info.get('video', {})
        
        # 尝试获取不同尺寸的封面
        if 'cover_original_scale' in video_data:
            return video_data['cover_original_scale'].get('url_list', [''])[0]
        elif 'cover' in video_data:
            return video_data['cover'].get('url_list', [''])[0]
        elif 'origin_cover' in video_data:
            return video_data['origin_cover'].get('url_list', [''])[0]
        
        return None
    
    def _extract_tags(self, video_info: Dict[str, Any]) -> list:
        """提取视频标签"""
        tags = []
        
        # 从视频标签提取
        video_tags = video_info.get('video_tag', [])
        for tag in video_tags:
            tag_name = tag.get('tag_name')
            if tag_name:
                tags.append(tag_name)
        
        # 从话题标签提取
        text_extra = video_info.get('text_extra', [])
        for extra in text_extra:
            hashtag = extra.get('hashtag', {})
            hashtag_name = hashtag.get('name')
            if hashtag_name and hashtag_name not in tags:
                tags.append(hashtag_name)
        
        return tags
    
    def _extract_category(self, video_info: Dict[str, Any]) -> str | None:
        """提取视频分类"""
        # 抖音的分类信息可能在不同位置
        if 'category' in video_info:
            return video_info['category']
        
        # 尝试从第一个标签获取分类信息
        tags = video_info.get('video_tag', [])
        if tags and len(tags) > 0:
            return tags[0].get('tag_name')
        
        return None
    
    def _parse_publish_date(self, create_time: Optional[int]) -> datetime | None:
        """解析发布日期"""
        if not create_time:
            return None
        
        try:
            # 抖音的时间戳是秒级
            return datetime.fromtimestamp(create_time)
        except (ValueError, OSError):
            return None
    
    def _get_platform_headers(self) -> Dict[str, str]:
        """获取抖音特定的请求头"""
        return {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.douyin.com/',
            'Origin': 'https://www.douyin.com',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
    
    def _requires_cookies(self) -> bool:
        """抖音必须有有效Cookie"""
        return True
    
    def _validate_cookies(self) -> bool:
        """验证Cookie有效性"""
        try:
            # 尝试访问抖音首页验证Cookie
            headers = self._prepare_request_headers()
            response = requests.get(
                'https://www.douyin.com/',
                headers=headers,
                timeout=10
            )
            
            # 检查是否被重定向到登录页面
            if 'login' in response.url or response.status_code != 200:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"验证抖音Cookie失败: {str(e)}")
            return False