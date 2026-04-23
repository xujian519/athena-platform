"""
Chrome Cookie 自动获取和管理模块
支持从本地Chrome浏览器自动获取指定网站的Cookie
"""
import json
import logging

logger = logging.getLogger(__name__)
from datetime import datetime

from core.logging_config import setup_logging

try:
    import browser_cookie3 as bc3
except ImportError:
    logger.info('需要安装 browser_cookie3: pip install browser-cookie3')
    bc3 = None

from app.models import CookieInfo, VideoPlatform

logger = setup_logging()


class ChromeCookieManager:
    """Chrome Cookie 管理器"""

    def __init__(self, cache_duration: int = 3600):
        """
        初始化Cookie管理器

        Args:
            cache_duration: Cookie缓存时间（秒），默认1小时
        """
        self.cache_duration = cache_duration
        self._cookie_cache: dict[str, list[CookieInfo] = {}
        self._last_cache_update: dict[str, datetime] = {}

        # 平台对应的域名映射
        self.platform_domains = {
            VideoPlatform.BILIBILI: ['bilibili.com', 'www.bilibili.com', 'api.bilibili.com'],
            VideoPlatform.YOUTUBE: ['youtube.com', 'www.youtube.com', 'm.youtube.com'],
            VideoPlatform.DOUYIN: ['douyin.com', 'www.douyin.com', 'v.douyin.com', 'iesdouyin.com'],
            VideoPlatform.KUAISHOU: ['kuaishou.com', 'www.kuaishou.com', 'v.kuaishou.com'],
        }

    def get_cookies_for_platform(self, platform: VideoPlatform, force_refresh: bool = False) -> list[CookieInfo]:
        """
        获取指定平台的Cookie

        Args:
            platform: 视频平台
            force_refresh: 是否强制刷新缓存

        Returns:
            Cookie信息列表
        """
        if platform not in self.platform_domains:
            logger.warning(f"不支持的平台: {platform}")
            return []

        cache_key = platform.value

        # 检查缓存是否有效
        if not force_refresh and self._is_cache_valid(cache_key):
            logger.debug(f"从缓存获取Cookie: {platform}")
            return self._cookie_cache.get(cache_key, [])

        try:
            # 从Chrome获取Cookie
            cookies = self._extract_chrome_cookies(platform)

            # 更新缓存
            self._cookie_cache[cache_key] = cookies
            self._last_cache_update[cache_key] = datetime.now()

            logger.info(f"成功获取 {platform} Cookie: {len(cookies)} 个")
            return cookies

        except Exception as e:
            logger.error(f"获取 {platform} Cookie 失败: {str(e)}")
            # 如果失败但有缓存，返回缓存的Cookie
            if cache_key in self._cookie_cache:
                logger.warning(f"使用缓存的Cookie: {platform}")
                return self._cookie_cache[cache_key]
            return []

    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self._last_cache_update:
            return False

        age = datetime.now() - self._last_cache_update[cache_key]
        return age.total_seconds() < self.cache_duration

    def _extract_chrome_cookies(self, platform: VideoPlatform) -> list[CookieInfo]:
        """从Chrome提取Cookie"""
        if bc3 is None:
            raise ImportError('需要安装 browser_cookie3 库')

        domains = self.platform_domains[platform]
        cookies = []

        try:
            # 尝试从Chrome获取Cookie
            chrome_cookies = bc3.chrome(domain_name=domains[0])

            # 转换为CookieInfo对象
            for cookie in chrome_cookies:
                if any(domain in cookie.domain for domain in domains):
                    cookie_info = CookieInfo(
                        domain=cookie.domain,
                        name=cookie.name,
                        value=cookie.value,
                        expires=datetime.fromtimestamp(cookie.expires) if cookie.expires else None,
                        secure=cookie.secure or False,
                        http_only=cookie._attributes.get('HttpOnly', False)
                    )
                    cookies.append(cookie_info)

            # 如果主域名没有获取到，尝试其他域名
            if not cookies and len(domains) > 1:
                for domain in domains[1:]:
                    try:
                        chrome_cookies = bc3.chrome(domain_name=domain)
                        for cookie in chrome_cookies:
                            cookie_info = CookieInfo(
                                domain=cookie.domain,
                                name=cookie.name,
                                value=cookie.value,
                                expires=datetime.fromtimestamp(cookie.expires) if cookie.expires else None,
                                secure=cookie.secure or False,
                                http_only=cookie._attributes.get('HttpOnly', False)
                            )
                            cookies.append(cookie_info)
                    except Exception as e:
                        logger.warning(f"从域名 {domain} 获取Cookie失败: {str(e)}")
                        continue

            return cookies

        except Exception as e:
            logger.error(f"从Chrome提取Cookie失败: {str(e)}")
            raise

    def get_cookie_string(self, platform: VideoPlatform, force_refresh: bool = False) -> str:
        """
        获取Cookie字符串（用于HTTP请求头）

        Args:
            platform: 视频平台
            force_refresh: 是否强制刷新

        Returns:
            Cookie字符串，格式: 'name1=value1; name2=value2'
        """
        cookies = self.get_cookies_for_platform(platform, force_refresh)

        if not cookies:
            return ''

        # 过滤重要的Cookie
        important_cookies = self._filter_important_cookies(platform, cookies)

        # 构建Cookie字符串
        cookie_pairs = [f"{cookie.name}={cookie.value}" for cookie in important_cookies]
        return '; '.join(cookie_pairs)

    def _filter_important_cookies(self, platform: VideoPlatform, cookies: list[CookieInfo]) -> list[CookieInfo]:
        """过滤重要的Cookie"""
        # 定义各平台重要的Cookie名称
        important_cookie_names = {
            VideoPlatform.BILIBILI: [
                'SESSDATA', 'bili_jct', 'DedeUserID', 'DedeUserID__ckMd5',
                'sid', 'buvid3', 'buvid4', 'b_nut', 'b_lsid'
            ],
            VideoPlatform.YOUTUBE: [
                'PREF', 'VISITOR_INFO1_LIVE', 'YSC', 'LOGIN_INFO',
                'HSID', 'SSID', 'APISID', 'SAPISID', 'CONSENT'
            ],
            VideoPlatform.DOUYIN: [
                'ms_token', 'ttwid', 'passport_csrf_token', 's_v_web_id',
                'MONITOR_WEB_ID', 'odin_tt', '__ac_nonce', '__ac_signature'
            ],
            VideoPlatform.KUAISHOU: [
                'kpf', 'kpn', 'user_id', 'did', 'clientid', 'client_key'
            ]
        }

        important_names = important_cookie_names.get(platform, [])

        # 如果没有定义重要Cookie，返回所有Cookie
        if not important_names:
            return cookies

        # 过滤重要的Cookie
        filtered = [cookie for cookie in cookies if cookie.name in important_names]

        # 如果没有重要Cookie，返回所有Cookie（作为兜底）
        if not filtered:
            logger.warning(f"未找到 {platform} 的重要Cookie，返回所有Cookie")
            return cookies

        return filtered

    def get_cookie_dict(self, platform: VideoPlatform, force_refresh: bool = False) -> dict[str, str]:
        """
        获取Cookie字典

        Args:
            platform: 视频平台
            force_refresh: 是否强制刷新

        Returns:
            Cookie字典 {name: value}
        """
        cookies = self.get_cookies_for_platform(platform, force_refresh)
        important_cookies = self._filter_important_cookies(platform, cookies)

        return {cookie.name: cookie.value for cookie in important_cookies}

    def validate_cookies(self, platform: VideoPlatform) -> bool:
        """
        验证Cookie是否有效

        Args:
            platform: 视频平台

        Returns:
            是否有效
        """
        try:
            cookies = self.get_cookies_for_platform(platform)

            if not cookies:
                return False

            # 检查是否有重要的Cookie
            important_cookies = self._filter_important_cookies(platform, cookies)

            if not important_cookies:
                return False

            # 检查Cookie是否过期
            now = datetime.now()
            for cookie in important_cookies:
                if cookie.expires and cookie.expires < now:
                    logger.warning(f"Cookie {cookie.name} 已过期")
                    return False

            return True

        except Exception as e:
            logger.error(f"验证Cookie失败: {str(e)}")
            return False

    def clear_cache(self, platform: VideoPlatform | None = None) -> None:
        """
        清除Cookie缓存

        Args:
            platform: 指定平台，不指定则清除所有
        """
        if platform:
            cache_key = platform.value
            if cache_key in self._cookie_cache:
                del self._cookie_cache[cache_key]
            if cache_key in self._last_cache_update:
                del self._last_cache_update[cache_key]
            logger.info(f"已清除 {platform} 的Cookie缓存")
        else:
            self._cookie_cache.clear()
            self._last_cache_update.clear()
            logger.info('已清除所有Cookie缓存')

    def get_cache_info(self) -> dict[str, dict[str, any]:
        """获取缓存信息"""
        cache_info = {}

        for cache_key, update_time in self._last_cache_update.items():
            age = datetime.now() - update_time
            cookie_count = len(self._cookie_cache.get(cache_key, []))

            cache_info[cache_key] = {
                'last_update': update_time.isoformat(),
                'age_seconds': age.total_seconds(),
                'cookie_count': cookie_count,
                'valid': age.total_seconds() < self.cache_duration
            }

        return cache_info

    def export_cookies(self, platform: VideoPlatform, file_path: str) -> bool:
        """
        导出Cookie到文件

        Args:
            platform: 视频平台
            file_path: 导出文件路径

        Returns:
            是否成功
        """
        try:
            cookies = self.get_cookies_for_platform(platform)

            if not cookies:
                logger.warning(f"没有找到 {platform} 的Cookie")
                return False

            # 转换为可序列化的格式
            cookie_data = []
            for cookie in cookies:
                cookie_dict = {
                    'domain': cookie.domain,
                    'name': cookie.name,
                    'value': cookie.value,
                    'expires': cookie.expires.isoformat() if cookie.expires else None,
                    'secure': cookie.secure,
                    'http_only': cookie.http_only
                }
                cookie_data.append(cookie_dict)

            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'platform': platform.value,
                    'export_time': datetime.now().isoformat(),
                    'cookies': cookie_data
                }, f, indent=2, ensure_ascii=False)

            logger.info(f"已导出 {platform} Cookie到: {file_path}")
            return True

        except Exception as e:
            logger.error(f"导出Cookie失败: {str(e)}")
            return False


# 全局Cookie管理器实例
cookie_manager = ChromeCookieManager()


def get_cookies_for_request(platform: VideoPlatform, force_refresh: bool = False) -> dict[str, str]:
    """
    获取用于HTTP请求的Cookie字典

    Args:
        platform: 视频平台
        force_refresh: 是否强制刷新

    Returns:
        Cookie字典
    """
    return cookie_manager.get_cookie_dict(platform, force_refresh)


def get_cookie_header(platform: VideoPlatform, force_refresh: bool = False) -> str:
    """
    获取用于HTTP请求头的Cookie字符串

    Args:
        platform: 视频平台
        force_refresh: 是否强制刷新

    Returns:
        Cookie字符串
    """
    return cookie_manager.get_cookie_string(platform, force_refresh)


def validate_platform_cookies(platform: VideoPlatform) -> bool:
    """
    验证平台Cookie是否有效

    Args:
        platform: 视频平台

    Returns:
        是否有效
    """
    return cookie_manager.validate_cookies(platform)


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    for platform in [VideoPlatform.BILIBILI, VideoPlatform.YOUTUBE, VideoPlatform.DOUYIN]:
        logger.info(f"\n=== {platform.value} Cookie 状态 ===")

        # 验证Cookie
        is_valid = validate_platform_cookies(platform)
        logger.info(f"Cookie有效性: {is_valid}")

        if is_valid:
            # 获取Cookie字符串
            cookie_str = get_cookie_header(platform)
            logger.info(f"Cookie字符串: {cookie_str[:100]}...")

            # 获取Cookie字典
            cookie_dict = get_cookies_for_request(platform)
            logger.info(f"Cookie数量: {len(cookie_dict)}")

        # 缓存信息
        cache_info = cookie_manager.get_cache_info()
        if platform.value in cache_info:
            info = cache_info[platform.value]
            logger.info(f"缓存状态: {info}")
