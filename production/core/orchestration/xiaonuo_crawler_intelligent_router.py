#!/usr/bin/env python3
"""
小诺·双鱼公主智能爬虫路由器
Xiaonuo·Pisces Princess Intelligent Crawler Router

智能路由爬虫任务到最合适的爬虫服务

作者: 小诺·双鱼公主
创建时间: 2025-12-14
版本: 1.0.0
"""

from __future__ import annotations
import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """任务复杂度"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class SiteComplexity(Enum):
    """网站复杂度"""

    STATIC = "static"  # 静态网站
    DYNAMIC = "dynamic"  # 动态网站(简单JS)
    HEAVY_JS = "heavy_js"  # 重JS网站
    SPA = "spa"  # 单页应用
    API_DRIVEN = "api_driven"  # API驱动
    PROTECTED = "protected"  # 有保护机制


@dataclass
class RoutingScore:
    """路由评分"""

    crawler_type: str
    score: float
    reasons: list[str]
    cost_estimate: float
    time_estimate: float
    confidence: float


class XiaonuoCrawlerIntelligentRouter:
    """小诺·双鱼公主智能爬虫路由器"""

    def __init__(self):
        self.name = "小诺·双鱼公主智能爬虫路由器"
        self.version = "1.0.0"

        # 网站特征库
        self.site_signatures = self._initialize_site_signatures()

        # 路由规则
        self.routing_rules = self._initialize_routing_rules()

        # 性能基准
        self.performance_benchmarks = {
            "universal": {"speed": 5, "cost": 0, "success_rate": 0.85, "anti_detection": 0.3},
            "patent": {"speed": 3, "cost": 0, "success_rate": 0.90, "anti_detection": 0.4},
            "browser_automation": {
                "speed": 2,
                "cost": 0.2,
                "success_rate": 0.75,
                "anti_detection": 0.8,
            },
            "distributed": {"speed": 8, "cost": 0.1, "success_rate": 0.80, "anti_detection": 0.6},
            "hybrid": {"speed": 6, "cost": 0.3, "success_rate": 0.88, "anti_detection": 0.9},
            "api": {"speed": 10, "cost": 0, "success_rate": 0.95, "anti_detection": 0.1},
        }

        print(f"🎯 {self.name} 初始化完成")

    def _initialize_site_signatures(self) -> dict[str, Any]:
        """初始化网站特征库"""
        return {
            # JavaScript框架特征
            "framework_patterns": {
                "react": [
                    r"react\.js",
                    r"react-dom\.js",
                    r"data-reactroot",
                    r"React.createElement",
                ],
                "vue": [r"vue\.js", r"vue\.min\.js", r"data-v-", r"v-"],
                "angular": [r"angular\.js", r"ng-app", r"ng-controller", r"\.ng-"],
                "jquery": [r"jquery\.js", r"jquery\.min\.js", r"$\(", r"jQuery"],
            },
            # 反爬虫特征
            "anti_bot_features": {
                "cloudflare": [r"cloudflare", r"cf-ray", r"__cfduid"],
                "akamai": [r"akamai", r"ak_bmsc"],
                "recaptcha": [r"recaptcha", r"grecaptcha"],
                "hcaptcha": [r"hcaptcha", r"h-captcha"],
                "distil": [r"distil", r"distil_cid"],
            },
            # 网站类型特征
            "site_types": {
                "ecommerce": [
                    r"product",
                    r"cart",
                    r"checkout",
                    r"add to cart",
                    r"price",
                    r"currency",
                    r"buy now",
                    r"shop",
                ],
                "social_media": [
                    r"like",
                    r"share",
                    r"comment",
                    r"follow",
                    r"tweet",
                    r"post",
                    r"timeline",
                ],
                "news": [
                    r"article",
                    r"news",
                    r"headline",
                    r"breaking",
                    r"author",
                    r"published",
                    r"category",
                ],
                "patent": [
                    r"patent",
                    r"invention",
                    r"claim",
                    r"prior art",
                    r"application",
                    r"grant",
                    r"citation",
                ],
            },
            # 动态内容特征
            "dynamic_indicators": [
                r"async",
                r"await",
                r"fetch\(",
                r"axios\.",
                r"XMLHttpRequest",
                r"websocket",
                r"socket\.io",
                r"/api/",
                r"/graphql",
                r"ajax",
            ],
        }

    def _initialize_routing_rules(self) -> dict[str, Any]:
        """初始化路由规则"""
        return {
            # 简单静态网站 -> 通用爬虫
            "simple_static": {
                "conditions": {
                    "site_complexity": ["static"],
                    "task_complexity": ["low"],
                    "no_anti_bot": True,
                },
                "recommendation": "universal",
                "weight": 1.0,
            },
            # 专利搜索 -> 专用爬虫
            "patent_search": {
                "conditions": {
                    "site_type": ["patent"],
                    "contains_keywords": ["patent", "专利", "invention", "发明"],
                },
                "recommendation": "patent",
                "weight": 1.0,
            },
            # 电商网站 -> 浏览器自动化
            "ecommerce": {
                "conditions": {"site_type": ["ecommerce"], "has_dynamic_content": True},
                "recommendation": "browser_automation",
                "weight": 0.9,
            },
            # 反爬虫网站 -> 混合爬虫
            "anti_bot": {
                "conditions": {"has_anti_bot": True, "anti_bot_strength": ["medium", "high"]},
                "recommendation": "hybrid",
                "weight": 0.95,
            },
            # 大规模爬取 -> 分布式
            "large_scale": {
                "conditions": {
                    "url_count": {"min": 100},
                    "estimated_time": {"min": 1800},  # 30分钟
                },
                "recommendation": "distributed",
                "weight": 0.85,
            },
            # API可用 -> API爬虫
            "api_available": {
                "conditions": {"has_api_endpoint": True, "api_accessible": True},
                "recommendation": "api",
                "weight": 1.0,
            },
            # 默认规则 -> 智能混合
            "default": {"recommendation": "hybrid", "weight": 0.5},
        }

    async def initialize(self):
        """初始化路由器"""
        logger.info("智能爬虫路由器初始化成功")

    async def route_task(self, task) -> dict[str, Any]:
        """路由任务到最合适的爬虫"""
        logger.info(f"开始路由任务: {task.task_id}")

        # 1. 分析URL特征
        url_analysis = await self._analyze_urls(task.target_urls)

        # 2. 分析任务特征
        task_analysis = await self._analyze_task(task)

        # 3. 评估爬虫选项
        crawler_scores = await self._evaluate_crawlers(url_analysis, task_analysis)

        # 4. 选择最佳爬虫
        best_crawler = self._select_best_crawler(crawler_scores)

        # 5. 生成配置建议
        config_suggestions = await self._generate_config_suggestions(
            best_crawler, url_analysis, task_analysis
        )

        logger.info(f"路由决策: {best_crawler.crawler_type} (评分: {best_crawler.score:.2f})")

        return {
            "service_type": best_crawler.crawler_type,
            "score": best_crawler.score,
            "confidence": best_crawler.confidence,
            "reasons": best_crawler.reasons,
            "cost_estimate": best_crawler.cost_estimate,
            "time_estimate": best_crawler.time_estimate,
            "config_overrides": config_suggestions,
            "alternative_options": [
                {
                    "crawler_type": cs.crawler_type,
                    "score": cs.score,
                    "reasons": cs.reasons[:2],  # 主要原因
                }
                for cs in sorted(crawler_scores, key=lambda x: x.score, reverse=True)[1:3]
            ],
        }

    async def _analyze_urls(self, urls: list[str]) -> dict[str, Any]:
        """分析URL特征"""
        if not urls:
            return {}

        analysis = {
            "domains": [],
            "site_types": [],
            "complexities": [],
            "anti_bot_detected": False,
            "anti_bot_strength": "none",
            "has_dynamic_content": False,
            "has_api_endpoint": False,
            "framework_detected": [],
        }

        # 分析每个URL
        for url in urls[:5]:  # 最多分析5个URL
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            analysis["domains"].append(domain)

            # 检测网站类型
            for site_type, patterns in self.site_signatures["site_types"].items():
                if any(re.search(p, url, re.I) for p in patterns):
                    analysis["site_types"].append(site_type)

            # 检测动态内容指标
            if any(re.search(p, url, re.I) for p in self.site_signatures["dynamic_indicators"]):
                analysis["has_dynamic_content"] = True

            # 检测API端点
            if "/api/" in url or "/graphql" in url:
                analysis["has_api_endpoint"] = True

        # 去重
        analysis["site_types"] = list(set(analysis["site_types"]))

        # 评估网站复杂度
        if analysis["has_dynamic_content"]:
            analysis["complexities"] = ["dynamic"]
        else:
            analysis["complexities"] = ["static"]

        return analysis

    async def _analyze_task(self, task) -> dict[str, Any]:
        """分析任务特征"""
        analysis = {
            "complexity": TaskComplexity.MEDIUM,
            "url_count": len(task.target_urls),
            "estimated_time": len(task.target_urls) * 10,  # 秒
            "requires_browser": False,
            "requires_javascript": False,
            "data_extraction_needs": "basic",
            "frequency": "once",
        }

        # 分析配置
        config = task.config or {}

        # 判断复杂度
        if len(task.target_urls) > 1000:
            analysis["complexity"] = TaskComplexity.EXTREME
        elif len(task.target_urls) > 100:
            analysis["complexity"] = TaskComplexity.HIGH
        elif len(task.target_urls) > 10:
            analysis["complexity"] = TaskComplexity.MEDIUM

        # 检查特殊需求
        if config.get("requires_browser"):
            analysis["requires_browser"] = True
        if config.get("requires_javascript"):
            analysis["requires_javascript"] = True
        if config.get("data_extraction_needs"):
            analysis["data_extraction_needs"] = config["data_extraction_needs"]

        return analysis

    async def _evaluate_crawlers(
        self, url_analysis: dict[str, Any], task_analysis: dict[str, Any]
    ) -> list[RoutingScore]:
        """评估所有爬虫选项"""
        scores = []

        # 评估每种爬虫类型
        for crawler_type, benchmark in self.performance_benchmarks.items():
            score, reasons, cost, time_est = await self._calculate_score(
                crawler_type, benchmark, url_analysis, task_analysis
            )

            scores.append(
                RoutingScore(
                    crawler_type=crawler_type,
                    score=score,
                    reasons=reasons,
                    cost_estimate=cost,
                    time_estimate=time_est,
                    confidence=min(score / 0.8, 1.0),  # 置信度基于评分
                )
            )

        return sorted(scores, key=lambda x: x.score, reverse=True)

    async def _calculate_score(
        self,
        crawler_type: str,
        benchmark: dict[str, Any],        url_analysis: dict[str, Any],        task_analysis: dict[str, Any],    ) -> tuple[float, list[str], float, float]:
        """计算爬虫评分"""
        score = 0.5  # 基础分
        reasons = []

        # 速度评分 (30%)
        if task_analysis["url_count"] > 100:
            speed_score = min(benchmark["speed"] / 10, 1.0) * 0.3
            score += speed_score
            if speed_score > 0.2:
                reasons.append(f"适合大规模爬取(速度{benchmark['speed']}/10)")
        else:
            speed_score = 0.15  # 小规模任务速度权重降低
            score += speed_score

        # 成本评分 (20%)
        cost_score = (1.0 - benchmark["cost"]) * 0.2
        score += cost_score
        if benchmark["cost"] == 0:
            reasons.append("无额外成本")

        # 成功率评分 (25%)
        success_score = benchmark["success_rate"] * 0.25
        score += success_score
        if benchmark["success_rate"] > 0.85:
            reasons.append("高成功率")

        # 反检测能力 (15%)
        anti_detection_score = benchmark["anti_detection"] * 0.15
        score += anti_detection_score
        if url_analysis.get("anti_bot_detected"):
            score += anti_detection_score * 2  # 反检测能力加倍
            reasons.append("有效应对反爬虫")

        # 特殊需求匹配 (10%)
        if crawler_type == "patent" and "patent" in url_analysis.get("site_types", []):
            score += 0.1
            reasons.append("专利爬虫专用")
        elif crawler_type == "browser_automation" and task_analysis.get("requires_browser"):
            score += 0.1
            reasons.append("需要浏览器渲染")
        elif crawler_type == "distributed" and task_analysis["url_count"] > 100:
            score += 0.1
            reasons.append("适合分布式处理")
        elif crawler_type == "api" and url_analysis.get("has_api_endpoint"):
            score += 0.1
            reasons.append("可以使用API")

        # 计算成本和时间
        base_time = task_analysis["estimated_time"]
        time_multiplier = 10 / benchmark["speed"]  # 速度越快时间越短
        time_estimate = base_time * time_multiplier

        cost_estimate = benchmark["cost"] * task_analysis["url_count"]

        return min(score, 1.0), reasons, cost_estimate, time_estimate

    def _select_best_crawler(self, scores: list[RoutingScore]) -> RoutingScore:
        """选择最佳爬虫"""
        if not scores:
            return RoutingScore("universal", 0.5, ["默认选择"], 0, 0, 0.5)

        # 如果最高分远高于第二名,直接选择
        if len(scores) > 1 and scores[0].score - scores[1].score > 0.2:
            return scores[0]

        # 否则考虑成本因素
        best_score = scores[0]
        for score in scores[:3]:  # 考虑前三名
            if score.cost_estimate < best_score.cost_estimate and score.score > 0.6:
                best_score = score

        return best_score

    async def _generate_config_suggestions(
        self,
        best_crawler: RoutingScore,
        url_analysis: dict[str, Any],        task_analysis: dict[str, Any],    ) -> dict[str, Any]:
        """生成配置建议"""
        config = {}

        # 基于爬虫类型的基础配置
        if best_crawler.crawler_type == "universal":
            config.update(
                {
                    "timeout": 30,
                    "max_retries": 3,
                    "rate_limit": 1.0,
                    "user_agent": "Mozilla/5.0 (compatible; XiaonuoCrawler/1.0)",
                }
            )
        elif best_crawler.crawler_type == "patent":
            config.update(
                {
                    "timeout": 60,
                    "include_claims": True,
                    "include_citations": True,
                    "date_range": "2020-2024",
                }
            )
        elif best_crawler.crawler_type == "browser_automation":
            config.update(
                {
                    "timeout": 120,
                    "headless": True,
                    "wait_for_selector": ".content",
                    "screenshot": False,
                }
            )
        elif best_crawler.crawler_type == "distributed":
            config.update(
                {
                    "workers": min(10, task_analysis["url_count"] // 10),
                    "chunk_size": 100,
                    "load_balance": True,
                }
            )
        elif best_crawler.crawler_type == "hybrid":
            config.update(
                {"fallback_enabled": True, "anti_detection": True, "adaptive_retry": True}
            )

        # 基于URL分析的调整
        if url_analysis.get("anti_bot_detected"):
            config["anti_detection"] = True
            config["random_delays"] = True
            config["proxy_rotation"] = True

        if url_analysis.get("has_dynamic_content"):
            config["wait_for_js"] = True
            config["render_timeout"] = 10

        # 基于任务分析的调整
        if task_analysis["complexity"] == TaskComplexity.HIGH:
            config["batch_size"] = 50
            config["checkpoint_interval"] = 100

        if task_analysis.get("requires_javascript"):
            config["javascript_enabled"] = True
            config["render_timeout"] = 30

        return config

    def get_routing_statistics(self) -> dict[str, Any]:
        """获取路由统计信息"""
        return {
            "router_info": {"name": self.name, "version": self.version},
            "available_crawlers": list(self.performance_benchmarks.keys()),
            "routing_rules_count": len(self.routing_rules),
            "site_signatures_count": len(self.site_signatures),
        }


# 导出主类
__all__ = ["XiaonuoCrawlerIntelligentRouter"]
