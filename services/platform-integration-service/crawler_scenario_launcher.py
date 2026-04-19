#!/usr/bin/env python3
"""
爬虫场景识别和自动启动机制
智能识别用户意图并启动相应的爬虫场景
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from crawler_integration_service import get_crawler_integration_service

logger = logging.getLogger(__name__)

class CrawlerScenarioType(Enum):
    """爬虫场景类型枚举"""
    PATENT_SEARCH = 'patent_search'
    WEBSITE_SCRAPING = 'website_scraping'
    DATA_COLLECTION = 'data_collection'
    MARKET_RESEARCH = 'market_research'
    COMPETITOR_ANALYSIS = 'competitor_analysis'
    NEWS_MONITORING = 'news_monitoring'
    PRODUCT_INFO = 'product_info'
    SOCIAL_MEDIA = 'social_media'
    ACADEMIC_RESEARCH = 'academic_research'
    PRICE_TRACKING = 'price_tracking'

@dataclass
class CrawlerScenarioTrigger:
    """爬虫场景触发器"""
    scenario_type: CrawlerScenarioType
    keywords: list[str]
    patterns: list[str]
    url_patterns: list[str]
    confidence_threshold: float
    priority: int
    description: str
    data_sources: list[str]

@dataclass
class CrawlerExecutionPlan:
    """爬虫执行计划"""
    scenario_type: CrawlerScenarioType
    confidence: float
    execution_mode: str  # xiaonuo, direct, scheduled
    parameters: dict[str, Any]
    estimated_time: int  # 预估执行时间(秒)
    estimated_data_size: int  # 预估数据条数
    risk_level: str  # low, medium, high
    resource_requirements: dict[str, Any]

class CrawlerScenarioLauncher:
    """爬虫场景启动器"""

    def __init__(self):
        """初始化爬虫场景启动器"""
        self.crawler_service = get_crawler_integration_service()
        self.trigger_rules = self._initialize_trigger_rules()
        self.execution_history = []
        self.learning_enabled = True

        # 性能指标
        self.metrics = {
            'total_recognitions': 0,
            'successful_launches': 0,
            'scenario_usage': {},
            'accuracy_rate': 0.0,
            'avg_confidence': 0.0
        }

    def _initialize_trigger_rules(self) -> list[CrawlerScenarioTrigger]:
        """初始化爬虫触发规则"""
        return [
            CrawlerScenarioTrigger(
                scenario_type=CrawlerScenarioType.PATENT_SEARCH,
                keywords=['专利', '发明', '知识产权', 'patent', 'invention', '专利检索', '专利搜索'],
                patterns=[r".*专利.*', r'.*发明.*', r'.*知识产权.*', r'.*patent.*"],
                url_patterns=[
                    r"patents\.google\.com",
                    r"uspto\.gov",
                    r"espacenet\.com",
                    r".*patent.*"
                ],
                confidence_threshold=0.8,
                priority=3,
                description='专利信息检索和分析',
                data_sources=['google_patents', 'uspto', 'espacenet']
            ),

            CrawlerScenarioTrigger(
                scenario_type=CrawlerScenarioType.WEBSITE_SCRAPING,
                keywords=['网站', '网页', '抓取', '内容', 'scraping', 'crawl', '网站数据'],
                patterns=[r".*抓取.*网站', r'.*爬取.*网页', r'.*获取.*内容"],
                url_patterns=[
                    r"https?://[^/]*(?:\.com|\.org|\.net|\.gov)",
                    r".*website.*",
                    r".*scrape.*"
                ],
                confidence_threshold=0.6,
                priority=1,
                description='网站内容数据抓取',
                data_sources=['custom_websites']
            ),

            CrawlerScenarioTrigger(
                scenario_type=CrawlerScenarioType.DATA_COLLECTION,
                keywords=['数据', '收集', '采集', '汇总', '批量', '大规模', 'data', 'collect'],
                patterns=[r".*收集.*数据', r'.*采集.*信息', r'.*批量.*获取"],
                url_patterns=[
                    r".*api.*",
                    r".*data.*",
                    r".*list.*"
                ],
                confidence_threshold=0.7,
                priority=2,
                description='大规模数据收集和处理',
                data_sources=['multiple_sources']
            ),

            CrawlerScenarioTrigger(
                scenario_type=CrawlerScenarioType.MARKET_RESEARCH,
                keywords=['市场', '调研', '趋势', '行业', '分析', 'market', 'research', 'trend'],
                patterns=[r".*市场.*', r'.*调研.*', r'.*趋势.*"],
                url_patterns=[
                    r".*market.*",
                    r".*research.*",
                    r".*report.*"
                ],
                confidence_threshold=0.7,
                priority=3,
                description='市场研究和趋势分析',
                data_sources=['news_sites', 'industry_reports', 'market_data']
            ),

            CrawlerScenarioTrigger(
                scenario_type=CrawlerScenarioType.COMPETITOR_ANALYSIS,
                keywords=['竞品', '对手', '竞争', '同行', 'competitor', 'competition'],
                patterns=[r".*竞品.*', r'.*对手.*', r'.*竞争.*"],
                url_patterns=[
                    r".*competitor.*",
                    r".*rival.*",
                    r".*competition.*"
                ],
                confidence_threshold=0.8,
                priority=3,
                description='竞争对手分析',
                data_sources=['competitor_sites', 'review_sites', 'social_media']
            ),

            CrawlerScenarioTrigger(
                scenario_type=CrawlerScenarioType.NEWS_MONITORING,
                keywords=['新闻', '资讯', '动态', '消息', '监控', 'news', 'monitor', 'update'],
                patterns=[r".*新闻.*', r'.*资讯.*', r'.*监控.*"],
                url_patterns=[
                    r".*news.*",
                    r".*media.*",
                    r".*press.*"
                ],
                confidence_threshold=0.6,
                priority=2,
                description='新闻和资讯监控',
                data_sources=['news_portals', 'social_media', 'rss_feeds']
            ),

            CrawlerScenarioTrigger(
                scenario_type=CrawlerScenarioType.PRODUCT_INFO,
                keywords=['产品', '商品', '价格', '信息', 'product', 'item', 'price'],
                patterns=[r".*产品.*', r'.*商品.*', r'.*价格.*"],
                url_patterns=[
                    r".*product.*",
                    r".*item.*",
                    r".*shop.*",
                    r"amazon\.com",
                    r"taobao\.com",
                    r"jd\.com"
                ],
                confidence_threshold=0.7,
                priority=2,
                description='商品信息采集',
                data_sources=['e-commerce_sites', 'product_reviews']
            ),

            CrawlerScenarioTrigger(
                scenario_type=CrawlerScenarioType.SOCIAL_MEDIA,
                keywords=['微博', '微信', '抖音', '社交', '媒体', 'social', 'media', 'weibo', 'twitter'],
                patterns=[r".*社交.*', r'.*媒体.*', r'.*微博.*"],
                url_patterns=[
                    r".*social.*",
                    r".*weibo.*",
                    r".*twitter.*",
                    r".*facebook.*",
                    r".*linkedin.*"
                ],
                confidence_threshold=0.5,
                priority=1,
                description='社交媒体数据采集',
                data_sources=['weibo', 'twitter', 'linkedin', 'instagram']
            ),

            CrawlerScenarioTrigger(
                scenario_type=CrawlerScenarioType.ACADEMIC_RESEARCH,
                keywords=['学术', '论文', '研究', '文献', 'academic', 'paper', 'research', 'scholar'],
                patterns=[r".*学术.*', r'.*论文.*', r'.*研究.*"],
                url_patterns=[
                    r".*scholar.*",
                    r".*academic.*",
                    r".*research.*",
                    r".*pubmed.*",
                    r".*arxiv.*"
                ],
                confidence_threshold=0.8,
                priority=3,
                description='学术研究和文献采集',
                data_sources=['scholar', 'pubmed', 'arxiv', 'academic_databases']
            ),

            CrawlerScenarioTrigger(
                scenario_type=CrawlerScenarioType.PRICE_TRACKING,
                keywords=['价格', '追踪', '监控', '变化', 'price', 'track', 'monitor', 'change'],
                patterns=[r".*价格.*', r'.*追踪.*', r'.*监控.*"],
                url_patterns=[
                    r".*price.*",
                    r".*deal.*",
                    r".*discount.*"
                ],
                confidence_threshold=0.7,
                priority=2,
                description='价格变化监控',
                data_sources=['e-commerce_sites', 'price_comparison_sites']
            )
        ]

    async def recognize_scenario(self, user_input: str, context: dict[str, Any] | None = None) -> list[CrawlerExecutionPlan]:
        """识别爬虫场景并生成执行计划

        Args:
            user_input: 用户输入
            context: 上下文信息

        Returns:
            执行计划列表，按置信度排序
        """
        self.metrics['total_recognitions'] += 1
        logger.info(f"识别爬虫场景: {user_input}")

        plans = []

        # 遍历所有触发规则
        for trigger in self.trigger_rules:
            confidence = self._calculate_confidence(user_input, trigger, context)

            if confidence >= trigger.confidence_threshold:
                # 生成执行计划
                plan = await self._create_execution_plan(
                    trigger, confidence, user_input, context
                )
                plans.append(plan)

        # 按置信度和优先级排序
        plans.sort(key=lambda x: (x.confidence, -x.priority), reverse=True)

        # 记录识别结果
        self._record_recognition(user_input, plans)

        logger.info(f"识别到 {len(plans)} 个潜在爬虫场景")
        return plans

    def _calculate_confidence(self, user_input: str, trigger: CrawlerScenarioTrigger,
                            context: dict[str, Any] | None) -> float:
        """计算匹配置信度"""
        input_lower = user_input.lower()

        # 关键词匹配得分 (权重: 30%)
        keyword_score = 0.0
        matched_keywords = 0
        for keyword in trigger.keywords:
            if keyword in input_lower:
                matched_keywords += 1
        keyword_score = min(matched_keywords / len(trigger.keywords), 1.0) * 0.3

        # 模式匹配得分 (权重: 20%)
        pattern_score = 0.0
        for pattern in trigger.patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                pattern_score += 0.2
        pattern_score = min(pattern_score, 0.2)

        # URL匹配得分 (权重: 30%)
        url_score = 0.0
        urls = self._extract_urls(user_input)
        if urls:
            url_matches = 0
            for url in urls:
                for url_pattern in trigger.url_patterns:
                    if re.search(url_pattern, url, re.IGNORECASE):
                        url_matches += 1
                        break
            url_score = min(url_matches / max(len(urls), 1), 1.0) * 0.3
        else:
            # 没有URL时给予部分分数
            url_score = 0.1

        # 上下文相关性得分 (权重: 15%)
        context_score = self._calculate_context_score(user_input, trigger, context) * 0.15

        # 历史成功率得分 (权重: 5%)
        experience_score = self._calculate_experience_score(user_input, trigger) * 0.05

        return keyword_score + pattern_score + url_score + context_score + experience_score

    def _extract_urls(self, text: str) -> list[str]:
        """提取URL"""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(url_pattern, text)

    def _calculate_context_score(self, user_input: str, trigger: CrawlerScenarioTrigger,
                                context: dict[str, Any] | None) -> float:
        """计算上下文相关性得分"""
        if not context:
            return 0.5

        score = 0.0

        # 数据源相关性
        if 'data_sources' in context:
            context_sources = set(context['data_sources'])
            trigger_sources = set(trigger.data_sources)
            if context_sources & trigger_sources:
                score += 0.4

        # 时间相关性（某些场景适合特定时间）
        current_hour = datetime.now().hour
        if trigger.scenario_type in [CrawlerScenarioType.DATA_COLLECTION, CrawlerScenarioType.WEBSITE_SCRAPING]:
            if 2 <= current_hour <= 6:  # 凌晨时段适合大规模数据收集
                score += 0.3

        # 历史成功率
        if trigger.scenario_type.value in self.metrics['scenario_usage']:
            success_rate = self.metrics['scenario_usage'][trigger.scenario_type.value].get('success_rate', 0.5)
            score += success_rate * 0.3

        return min(score, 1.0)

    def _calculate_experience_score(self, user_input: str, trigger: CrawlerScenarioTrigger) -> float:
        """历史经验分析"""
        if not self.execution_history:
            return 0.5

        # 简单的历史相似度分析
        similar_executions = [
            d for d in self.execution_history[-20:]  # 最近20次执行
            if d['scenario_type'] == trigger.scenario_type.value
        ]

        if similar_executions:
            success_rate = sum(1 for d in similar_executions if d['success']) / len(similar_executions)
            return success_rate

        return 0.5

    async def _create_execution_plan(
        self,
        trigger: CrawlerScenarioTrigger,
        confidence: float,
        user_input: str,
        context: dict[str, Any] | None
    ) -> CrawlerExecutionPlan:
        """创建爬虫执行计划"""
        # 根据场景类型确定执行模式
        execution_mode = self._determine_execution_mode(trigger.scenario_type, confidence)

        # 提取参数
        parameters = self._extract_crawler_parameters(user_input, trigger.scenario_type, context)

        # 估算执行时间
        estimated_time = self._estimate_execution_time(trigger.scenario_type, parameters)

        # 估算数据规模
        estimated_data_size = self._estimate_data_size(trigger.scenario_type, parameters, user_input)

        # 评估资源需求
        resource_requirements = self._assess_resource_requirements(trigger.scenario_type, parameters)

        # 评估风险级别
        risk_level = self._assess_risk_level(trigger.scenario_type, user_input, parameters)

        return CrawlerExecutionPlan(
            scenario_type=trigger.scenario_type,
            confidence=confidence,
            execution_mode=execution_mode,
            parameters=parameters,
            estimated_time=estimated_time,
            estimated_data_size=estimated_data_size,
            risk_level=risk_level,
            resource_requirements=resource_requirements
        )

    def _determine_execution_mode(self, scenario_type: CrawlerScenarioType, confidence: float) -> str:
        """确定执行模式"""
        # 高置信度且复杂场景使用小诺
        if confidence > 0.8 and scenario_type in [
            CrawlerScenarioType.PATENT_SEARCH,
            CrawlerScenarioType.COMPETITOR_ANALYSIS,
            CrawlerScenarioType.ACADEMIC_RESEARCH,
            CrawlerScenarioType.MARKET_RESEARCH
        ]:
            return 'xiaonuo'

        # 大规模数据收集使用调度模式
        if scenario_type in [CrawlerScenarioType.DATA_COLLECTION]:
            return 'scheduled'

        # 简单场景直接执行
        if scenario_type in [CrawlerScenarioType.WEBSITE_SCRAPING, CrawlerScenarioType.PRODUCT_INFO]:
            return 'direct'

        # 默认使用小诺
        return 'xiaonuo'

    def _extract_crawler_parameters(self, user_input: str, scenario_type: CrawlerScenarioType,
                                   context: dict[str, Any] | None) -> dict[str, Any]:
        """提取爬虫参数"""
        parameters = {'user_input': user_input}

        # 提取URL
        urls = self._extract_urls(user_input)
        if urls:
            parameters['urls'] = urls

        # 根据场景类型提取特定参数
        if scenario_type == CrawlerScenarioType.PATENT_SEARCH:
            parameters.update(self._extract_patent_params(user_input))
        elif scenario_type == CrawlerScenarioType.NEWS_MONITORING:
            parameters.update(self._extract_news_params(user_input))
        elif scenario_type == CrawlerScenarioType.PRICE_TRACKING:
            parameters.update(self._extract_price_params(user_input))
        elif scenario_type == CrawlerScenarioType.COMPETITOR_ANALYSIS:
            parameters.update(self._extract_competitor_params(user_input))

        # 添加上下文信息
        if context:
            parameters.update(context)

        return parameters

    def _extract_patent_params(self, text: str) -> dict[str, Any]:
        """提取专利检索参数"""
        params = {}

        # 提取关键词
        if '人工智能' in text or 'AI' in text:
            params['keywords'] = ['artificial intelligence', 'AI']
        elif '机器学习' in text:
            params['keywords'] = ['machine learning']
        elif '深度学习' in text:
            params['keywords'] = ['deep learning']

        # 提取数量限制
        if '100' in text:
            params['max_results'] = 100
        elif '50' in text:
            params['max_results'] = 50

        # 提取时间范围
        if '最近' in text or '最新' in text:
            params['date_range'] = '2020-2024'

        return params

    def _extract_news_params(self, text: str) -> dict[str, Any]:
        """提取新闻监控参数"""
        params = {}

        # 提取关键词
        tech_keywords = ['科技', '技术', 'AI', '人工智能', '互联网']
        found_keywords = [kw for kw in tech_keywords if kw in text]
        if found_keywords:
            params['keywords'] = found_keywords

        # 提取时间范围
        if '今天' in text:
            params['time_range'] = '24h'
        elif '本周' in text:
            params['time_range'] = '7d'
        elif '最近' in text:
            params['time_range'] = '30d'

        return params

    def _extract_price_params(self, text: str) -> dict[str, Any]:
        """提取价格追踪参数"""
        params = {}

        # 提取商品名称
        product_names = ['i_phone', '华为', '小米', 'MacBook', '戴尔']
        found_products = [name for name in product_names if name in text]
        if found_products:
            params['products'] = found_products

        # 提取平台
        platforms = ['淘宝', '京东', '天猫', '亚马逊', 'Amazon']
        found_platforms = [platform for platform in platforms if platform in text]
        if found_platforms:
            params['platforms'] = found_platforms

        return params

    def _extract_competitor_params(self, text: str) -> dict[str, Any]:
        """提取竞品分析参数"""
        params = {}

        # 提取竞争对手名称
        companies = ['阿里巴巴', '腾讯', '百度', '字节跳动', '京东', '美团']
        found_companies = [company for company in companies if company in text]
        if found_companies:
            params['competitors'] = found_companies

        # 提取分析深度
        if '详细' in text or '深度' in text:
            params['analysis_depth'] = 'deep'
        else:
            params['analysis_depth'] = 'basic'

        return params

    def _estimate_execution_time(self, scenario_type: CrawlerScenarioType, parameters: dict[str, Any]) -> int:
        """估算执行时间"""
        base_times = {
            CrawlerScenarioType.PATENT_SEARCH: 120,
            CrawlerScenarioType.WEBSITE_SCRAPING: 60,
            CrawlerScenarioType.DATA_COLLECTION: 300,
            CrawlerScenarioType.MARKET_RESEARCH: 240,
            CrawlerScenarioType.COMPETITOR_ANALYSIS: 180,
            CrawlerScenarioType.NEWS_MONITORING: 90,
            CrawlerScenarioType.PRODUCT_INFO: 45,
            CrawlerScenarioType.SOCIAL_MEDIA: 150,
            CrawlerScenarioType.ACADEMIC_RESEARCH: 200,
            CrawlerScenarioType.PRICE_TRACKING: 30
        }

        base_time = base_times.get(scenario_type, 120)

        # 根据参数调整时间
        if 'urls' in parameters:
            base_time *= min(len(parameters['urls']) / 5, 3)  # 最多3倍

        if 'max_results' in parameters:
            base_time *= min(parameters['max_results'] / 50, 2)  # 最多2倍

        return int(base_time)

    def _estimate_data_size(self, scenario_type: CrawlerScenarioType, parameters: dict[str, Any], user_input: str) -> int:
        """估算数据规模"""
        base_sizes = {
            CrawlerScenarioType.PATENT_SEARCH: 50,
            CrawlerScenarioType.WEBSITE_SCRAPING: 20,
            CrawlerScenarioType.DATA_COLLECTION: 500,
            CrawlerScenarioType.MARKET_RESEARCH: 100,
            CrawlerScenarioType.COMPETITOR_ANALYSIS: 80,
            CrawlerScenarioType.NEWS_MONITORING: 200,
            CrawlerScenarioType.PRODUCT_INFO: 30,
            CrawlerScenarioType.SOCIAL_MEDIA: 300,
            CrawlerScenarioType.ACADEMIC_RESEARCH: 60,
            CrawlerScenarioType.PRICE_TRACKING: 10
        }

        base_size = base_sizes.get(scenario_type, 50)

        # 根据用户输入调整
        if '大量' in user_input or '批量' in user_input:
            base_size *= 5
        elif '少量' in user_input or '几个' in user_input:
            base_size = min(base_size, 10)

        # 根据参数调整
        if 'max_results' in parameters:
            base_size = parameters['max_results']

        if 'urls' in parameters:
            base_size *= min(len(parameters['urls']) / 3, 2)

        return int(base_size)

    def _assess_resource_requirements(self, scenario_type: CrawlerScenarioType, parameters: dict[str, Any]) -> dict[str, Any]:
        """评估资源需求"""
        requirements = {
            'cpu': 'medium',
            'memory': 'medium',
            'network': 'high',
            'storage': 'low'
        }

        # 根据场景调整
        if scenario_type == CrawlerScenarioType.DATA_COLLECTION:
            requirements.update({
                'cpu': 'high',
                'memory': 'high',
                'storage': 'medium'
            })
        elif scenario_type == CrawlerScenarioType.PATENT_SEARCH:
            requirements.update({
                'cpu': 'medium',
                'memory': 'low',
                'network': 'medium'
            })

        # 根据参数调整
        if parameters.get('urls'):
            if len(parameters['urls']) > 50:
                requirements['cpu'] = 'high'
                requirements['memory'] = 'high'

        return requirements

    def _assess_risk_level(self, scenario_type: CrawlerScenarioType, user_input: str, parameters: dict[str, Any]) -> str:
        """评估风险级别"""
        # 检查敏感词
        sensitive_words = ['破解', '攻击', '侵入', '非法', '未授权', '私密', '隐私']
        if any(word in user_input for word in sensitive_words):
            return 'high'

        # 检查某些场景的风险
        high_risk_scenarios = [CrawlerScenarioType.SOCIAL_MEDIA, CrawlerScenarioType.COMPETITOR_ANALYSIS]
        if scenario_type in high_risk_scenarios:
            return 'medium'

        # 检查数据规模
        if self._estimate_data_size(scenario_type, parameters, user_input) > 1000:
            return 'medium'

        return 'low'

    def _record_recognition(self, user_input: str, plans: list[CrawlerExecutionPlan]) -> Any:
        """记录识别结果"""
        record = {
            'input': user_input,
            'plans': [
                {
                    'scenario': plan.scenario_type.value,
                    'confidence': plan.confidence,
                    'mode': plan.execution_mode
                }
                for plan in plans
            ],
            'timestamp': datetime.now().isoformat()
        }
        self.execution_history.append(record)

        # 保持历史记录在合理范围内
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-500:]

    async def auto_launch(self, user_input: str, context: dict[str, Any] | None = None, auto_confirm: bool = False) -> dict[str, Any]:
        """自动识别并启动爬虫场景

        Args:
            user_input: 用户输入
            context: 上下文信息
            auto_confirm: 是否自动确认执行

        Returns:
            启动结果
        """
        logger.info(f"自动启动爬虫场景: {user_input}")

        # 1. 识别场景
        plans = await self.recognize_scenario(user_input, context)

        if not plans:
            return {
                'success': False,
                'reason': 'no_scenario_matched',
                'message': '没有识别到合适的爬虫场景',
                'suggestions': ['请提供更具体的爬虫需求', '可以指定目标URL或数据源']
            }

        # 2. 选择最佳计划
        best_plan = plans[0]

        # 3. 风险检查
        if best_plan.risk_level == 'high' and not auto_confirm:
            return {
                'success': False,
                'reason': 'high_risk',
                'message': '检测到高风险操作，需要人工确认',
                'plan': best_plan,
                'risk_details': '建议在安全模式下执行，并遵守相关法律法规'
            }

        # 4. 置信度检查
        if best_plan.confidence < 0.6 and not auto_confirm:
            return {
                'success': False,
                'reason': 'low_confidence',
                'message': f"置信度{best_plan.confidence:.2f}过低，请确认是否继续",
                'plan': best_plan,
                'alternatives': plans[1:3] if len(plans) > 1 else []
            }

        # 5. 执行最佳计划
        try:
            execution_result = await self._execute_plan(best_plan)

            # 6. 学习和优化
            if self.learning_enabled:
                await self._learn_from_execution(best_plan, execution_result)

            return {
                'success': True,
                'message': '爬虫场景启动成功',
                'plan': best_plan,
                'execution_result': execution_result,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"执行爬虫场景失败: {e}")
            return {
                'success': False,
                'reason': 'execution_failed',
                'message': f"执行失败: {str(e)}",
                'plan': best_plan
            }

    async def _execute_plan(self, plan: CrawlerExecutionPlan) -> dict[str, Any]:
        """执行爬虫计划"""
        request_params = {
            'user_input': plan.parameters.get('user_input', ''),
            'mode': plan.execution_mode,
            'context': plan.parameters,
            'scenario': plan.scenario_type.value,
            'urls': plan.parameters.get('urls', []),
            'config': plan.parameters
        }

        result = await self.crawler_service.process_request(request_params)
        return result

    async def _learn_from_execution(self, plan: CrawlerExecutionPlan, execution_result: dict[str, Any]):
        """从执行结果中学习"""
        # 简单的学习机制：根据执行结果调整决策权重
        success = execution_result.get('success', False)

        # 记录学习结果
        {
            'scenario_type': plan.scenario_type.value,
            'confidence': plan.confidence,
            'execution_mode': plan.execution_mode,
            'execution_success': success,
            'timestamp': datetime.now().isoformat()
        }

        # 更新指标
        scenario_key = plan.scenario_type.value
        if scenario_key not in self.metrics['scenario_usage']:
            self.metrics['scenario_usage'][scenario_key] = {
                'total': 0,
                'success': 0,
                'success_rate': 0.0,
                'avg_confidence': 0.0
            }

        usage = self.metrics['scenario_usage'][scenario_key]
        usage['total'] += 1
        if success:
            usage['success'] += 1
            self.metrics['successful_launches'] += 1

        usage['success_rate'] = usage['success'] / usage['total']

        # 更新平均置信度
        current_avg = usage['avg_confidence']
        new_avg = (current_avg * (usage['total'] - 1) + plan.confidence) / usage['total']
        usage['avg_confidence'] = new_avg

        # 计算总体准确率
        if self.metrics['total_recognitions'] > 0:
            self.metrics['accuracy_rate'] = self.metrics['successful_launches'] / self.metrics['total_recognitions']
            self.metrics['avg_confidence'] = sum(
                usage['avg_confidence'] for usage in self.metrics['scenario_usage'].values()
            ) / max(len(self.metrics['scenario_usage']), 1)

    def get_metrics(self) -> dict[str, Any]:
        """获取性能指标"""
        return {
            'metrics': self.metrics,
            'trigger_rules_count': len(self.trigger_rules),
            'execution_history_size': len(self.execution_history),
            'learning_enabled': self.learning_enabled
        }

    def get_available_scenarios(self) -> dict[str, Any]:
        """获取可用场景列表"""
        return {
            'scenarios': [
                {
                    'type': trigger.scenario_type.value,
                    'name': trigger.scenario_type.name,
                    'description': trigger.description,
                    'keywords': trigger.keywords,
                    'confidence_threshold': trigger.confidence_threshold,
                    'priority': trigger.priority,
                    'data_sources': trigger.data_sources
                }
                for trigger in self.trigger_rules
            ],
            'total_count': len(self.trigger_rules)
        }

# 全局实例
crawler_scenario_launcher: CrawlerScenarioLauncher | None = None

def get_crawler_scenario_launcher() -> CrawlerScenarioLauncher:
    """获取爬虫场景启动器实例"""
    global crawler_scenario_launcher
    if crawler_scenario_launcher is None:
        crawler_scenario_launcher = CrawlerScenarioLauncher()
    return crawler_scenario_launcher

# 测试函数
async def test_crawler_scenario_launcher():
    """测试爬虫场景启动器"""
    logger.info('🕷️ 测试爬虫场景识别和启动机制')
    logger.info(str('=' * 50))

    launcher = get_crawler_scenario_launcher()

    # 测试用例
    test_cases = [
        '帮我爬取Google Patents上的AI专利',
        '监控今天的热点新闻',
        '收集竞品分析数据',
        '抓取网站内容 https://example.com',
        '追踪iPhone价格变化',
        '学术研究论文搜索'
    ]

    for i, test_input in enumerate(test_cases, 1):
        logger.info(f"\n🧪 测试{i}: {test_input}")

        # 识别场景
        plans = await launcher.recognize_scenario(test_input)
        logger.info(f"   识别到 {len(plans)} 个场景")
        if plans:
            best = plans[0]
            logger.info(f"   最佳场景: {best.scenario_type.value}")
            logger.info(f"   置信度: {best.confidence:.2f}")
            logger.info(f"   执行模式: {best.execution_mode}")
            logger.info(f"   预估时间: {best.estimated_time}秒")
            logger.info(f"   预估数据: {best.estimated_data_size}条")

        # 自动启动
        result = await launcher.auto_launch(test_input, auto_confirm=True)
        logger.info(f"   启动成功: {result['success']}")
        if not result['success']:
            logger.info(f"   失败原因: {result.get('reason', 'unknown')}")

    # 显示指标
    metrics = launcher.get_metrics()
    logger.info("\n📊 性能指标:")
    logger.info(f"   总识别次数: {metrics['metrics']['total_recognitions']}")
    logger.info(f"   成功启动次数: {metrics['metrics']['successful_launches']}")
    logger.info(f"   准确率: {metrics['metrics']['accuracy_rate']:.2f}")
    logger.info(f"   平均置信度: {metrics['metrics']['avg_confidence']:.2f}")

    # 显示可用场景
    scenarios = launcher.get_available_scenarios()
    logger.info(f"\n🎯 可用场景数: {scenarios['total_count']}")

    logger.info("\n✅ 爬虫场景启动器测试完成")

if __name__ == '__main__':
    asyncio.run(test_crawler_scenario_launcher())
