# -*- coding: utf-8 -*-
"""
混合爬虫统一配置管理
"""

import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class CostLimits:
    """成本限制配置"""
    monthly_limit: float = 100.0      # 月度成本限制（美元）
    daily_limit: float = 10.0         # 日成本限制（美元）
    per_request_limit: float = 0.01   # 单次请求成本限制（美元）
    enable_cost_control: bool = True   # 启用成本控制


@dataclass
class RoutingConfig:
    """路由配置"""
    strategy: str = 'auto'            # 默认路由策略: auto, internal, crawl4ai, firecrawl
    confidence_threshold: float = 0.7 # 决策置信度阈值
    enable_smart_routing: bool = True # 启用智能路由
    prefer_internal_for: list = None  # 优先使用内部爬虫的域名列表
    force_external_for: list = None   # 强制使用外部工具的域名列表

    def __post_init__(self):
        if self.prefer_internal_for is None:
            self.prefer_internal_for = [
                'github.com',
                'stackoverflow.com',
                'wikipedia.org',
                'docs.python.org',
                'developer.mozilla.org'
            ]
        if self.force_external_for is None:
            self.force_external_for = [
                'linkedin.com',
                'twitter.com',
                'facebook.com',
                'instagram.com',
                'medium.com'
            ]


@dataclass
class Crawl4AIConfig:
    """Crawl4AI配置"""
    enabled: bool = True
    mode: str = 'basic'               # basic, ai_enhanced, llm_powered, semantic
    use_browser: bool = False
    headless: bool = True
    delay_before_return_html: float = 0.5
    js_code: str | None = None
    wait_for: str | None = None
    css_selector: str | None = None
    llm_extraction_prompt: str | None = None
    similarity_threshold: float = 0.7
    chunk_size: int = 1000
    overlap: int = 100
    max_concurrent: int = 3

    # LLM配置
    llm_provider: str = 'openai'
    llm_model: str = 'gpt-3.5-turbo'
    llm_api_key: str | None = None


@dataclass
class FireCrawlConfig:
    """FireCrawl配置"""
    enabled: bool = True
    api_key: str | None = None
    base_url: str = 'https://api.firecrawl.dev/v1'
    mode: str = 'scrape'              # scrape, crawl, search
    timeout: int = 30
    max_pages: int = 100
    include_paths: list = None
    exclude_paths: list = None
    allow_backlinks: bool = False
    ignore_sitemap: bool = False
    max_concurrent: int = 3

    # 爬取选项
    formats: list = None
    only_main_content: bool = True
    wait_for: int = 0
    screenshot: bool = False
    remove_base64_images: bool = True

    def __post_init__(self):
        if self.include_paths is None:
            self.include_paths = []
        if self.exclude_paths is None:
            self.exclude_paths = []
        if self.formats is None:
            self.formats = ['markdown', 'html']


@dataclass
class InternalCrawlerConfig:
    """内部爬虫配置"""
    enabled: bool = True
    max_concurrent: int = 5
    rate_limit: float = 1.0          # 每秒请求限制
    timeout: int = 10
    max_retries: int = 3
    cache_enabled: bool = True
    cache_ttl: int = 3600             # 缓存时间（秒）
    user_agent: str = 'Mozilla/5.0 (compatible; Athena-Crawler/1.0)'
    respect_robots_txt: bool = True

    # 请求头配置
    headers: dict = None

    def __post_init__(self):
        if self.headers is None:
            self.headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }


@dataclass
class HybridCrawlerConfig:
    """混合爬虫总配置"""
    # 子配置
    cost_limits: CostLimits
    routing: RoutingConfig
    crawl4ai: Crawl4AIConfig
    firecrawl: FireCrawlConfig
    internal: InternalCrawlerConfig

    # 全局配置
    default_strategy: str = 'auto'
    enable_logging: bool = True
    log_level: str = 'INFO'
    metrics_enabled: bool = True
    cache_directory: str = './cache'
    temp_directory: str = './temp'

    def __post_init__(self):
        # 确保目录存在
        Path(self.cache_directory).mkdir(parents=True, exist_ok=True)
        Path(self.temp_directory).mkdir(parents=True, exist_ok=True)


class HybridConfigManager:
    """混合爬虫配置管理器"""

    def __init__(self, config_path: str | None = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config: HybridCrawlerConfig | None = None
        self.load_config()

    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        # 尝试多个可能的配置文件位置
        possible_paths = [
            './config/hybrid_crawler_config.json',
            './config/default_config.json',
            './hybrid_crawler_config.json',
            os.path.expanduser('~/.athena/hybrid_crawler_config.json')
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # 如果都不存在，使用第一个作为默认路径
        return possible_paths[0]

    def load_config(self) -> Any | None:
        """加载配置"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.config = self._parse_config(config_data)
                logger.info(f"配置已从 {self.config_path} 加载")
            else:
                self.config = self._create_default_config()
                self.save_config()
                logger.info('使用默认配置并已保存')
        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            self.config = self._create_default_config()

    def _parse_config(self, config_data: Dict[str, Any]) -> HybridCrawlerConfig:
        """解析配置数据"""
        return HybridCrawlerConfig(
            cost_limits=CostLimits(**config_data.get('cost_limits', {})),
            routing=RoutingConfig(**config_data.get('routing', {})),
            crawl4ai=Crawl4AIConfig(**config_data.get('crawl4ai', {})),
            firecrawl=FireCrawlConfig(**config_data.get('firecrawl', {})),
            internal=InternalCrawlerConfig(**config_data.get('internal', {})),
            **{k: v for k, v in config_data.items()
               if k not in ['cost_limits', 'routing', 'crawl4ai', 'firecrawl', 'internal']}
        )

    def _create_default_config(self) -> HybridCrawlerConfig:
        """创建默认配置"""
        return HybridCrawlerConfig(
            cost_limits=CostLimits(),
            routing=RoutingConfig(),
            crawl4ai=Crawl4AIConfig(),
            firecrawl=FireCrawlConfig(),
            internal=InternalCrawlerConfig()
        )

    def save_config(self) -> None:
        """保存配置"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

            config_dict = asdict(self.config)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            logger.info(f"配置已保存到 {self.config_path}")
        except Exception as e:
            logger.error(f"配置保存失败: {e}")

    def get_config(self) -> HybridCrawlerConfig:
        """获取配置"""
        return self.config

    def update_config(self, updates: Dict[str, Any]) -> None:
        """更新配置"""
        try:
            config_dict = asdict(self.config)
            self._deep_update(config_dict, updates)
            self.config = self._parse_config(config_dict)
            logger.info('配置已更新')
        except Exception as e:
            logger.error(f"配置更新失败: {e}")

    def _deep_update(self, target: dict, source: dict) -> Any:
        """深度更新字典"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value

    def get_crawler_config(self, crawler_type: str) -> Dict[str, Any]:
        """获取特定爬虫的配置"""
        if crawler_type == 'internal':
            return asdict(self.config.internal)
        elif crawler_type == 'crawl4ai':
            return asdict(self.config.crawl4ai)
        elif crawler_type == 'firecrawl':
            return asdict(self.config.firecrawl)
        else:
            raise ValueError(f"未知的爬虫类型: {crawler_type}")

    def is_crawler_enabled(self, crawler_type: str) -> bool:
        """检查爬虫是否启用"""
        if crawler_type == 'internal':
            return self.config.internal.enabled
        elif crawler_type == 'crawl4ai':
            return self.config.crawl4ai.enabled
        elif crawler_type == 'firecrawl':
            return self.config.firecrawl.enabled
        else:
            return False

    def get_cost_limits(self) -> CostLimits:
        """获取成本限制配置"""
        return self.config.cost_limits

    def get_routing_config(self) -> RoutingConfig:
        """获取路由配置"""
        return self.config.routing

    def validate_config(self) -> list:
        """验证配置，返回错误列表"""
        errors = []

        # 验证成本限制
        if self.config.cost_limits.monthly_limit <= 0:
            errors.append('月度成本限制必须大于0')
        if self.config.cost_limits.daily_limit <= 0:
            errors.append('日成本限制必须大于0')
        if self.config.cost_limits.daily_limit > self.config.cost_limits.monthly_limit:
            errors.append('日成本限制不能超过月度限制')

        # 验证路由配置
        if self.config.routing.strategy not in ['auto', 'internal', 'crawl4ai', 'firecrawl']:
            errors.append('路由策略必须是: auto, internal, crawl4ai, firecrawl 之一')

        # 验证Crawl4AI配置
        if self.config.crawl4ai.enabled and self.config.crawl4ai.mode == 'llm_powered':
            if not self.config.crawl4ai.llm_api_key:
                errors.append('LLM模式需要提供API密钥')

        # 验证FireCrawl配置
        if self.config.firecrawl.enabled:
            if not self.config.firecrawl.api_key and not os.getenv('FIRECRAWL_API_KEY'):
                errors.append('FireCrawl需要提供API密钥')

        # 验证内部爬虫配置
        if self.config.internal.rate_limit <= 0:
            errors.append('内部爬虫频率限制必须大于0')
        if self.config.internal.timeout <= 0:
            errors.append('内部爬虫超时时间必须大于0')

        return errors

    def get_env_overrides(self) -> Dict[str, Any]:
        """获取环境变量覆盖"""
        overrides = {}

        # FireCrawl API密钥
        firecrawl_key = os.getenv('FIRECRAWL_API_KEY')
        if firecrawl_key:
            overrides.setdefault('firecrawl', {})['api_key'] = firecrawl_key

        # Crawl4AI LLM API密钥
        crawl4ai_key = os.getenv('CRAWL4AI_LLM_API_KEY')
        if crawl4ai_key:
            overrides.setdefault('crawl4ai', {})['llm_api_key'] = crawl4ai_key

        # 成本限制环境变量
        monthly_limit = os.getenv('CRAWLER_MONTHLY_LIMIT')
        if monthly_limit:
            try:
                overrides.setdefault('cost_limits', {})['monthly_limit'] = float(monthly_limit)
            except ValueError:
                logger.error(f"Error: {e}", exc_info=True)

        daily_limit = os.getenv('CRAWLER_DAILY_LIMIT')
        if daily_limit:
            try:
                overrides.setdefault('cost_limits', {})['daily_limit'] = float(daily_limit)
            except ValueError:
                logger.error(f"Error: {e}", exc_info=True)

        return overrides

    def apply_env_overrides(self) -> Any:
        """应用环境变量覆盖"""
        overrides = self.get_env_overrides()
        if overrides:
            self.update_config(overrides)
            logger.info('已应用环境变量配置覆盖')


# 全局配置管理器实例
_config_manager: HybridConfigManager | None = None


def get_config_manager(config_path: str | None = None) -> HybridConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = HybridConfigManager(config_path)
        _config_manager.apply_env_overrides()
    return _config_manager


def get_config() -> HybridCrawlerConfig:
    """获取当前配置"""
    return get_config_manager().get_config()


def reload_config(config_path: str | None = None) -> Any:
    """重新加载配置"""
    global _config_manager
    _config_manager = HybridConfigManager(config_path)
    _config_manager.apply_env_overrides()