#!/usr/bin/env python3
"""
小诺智能爬虫控制接口
智能决策何时使用爬虫工具获取信息
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import Any

# 导入爬虫工具
from common_tools.crawler_tool import CrawlerScenario, get_crawler_tool

logger = logging.getLogger(__name__)

class XiaoNuoCrawlerController:
    """小诺智能爬虫控制器"""

    def __init__(self):
        """初始化控制器"""
        self.crawler_tool = get_crawler_tool()
        self.decision_history = []
        self.learning_enabled = True

        # 智能决策配置
        self.decision_config = {
            'confidence_threshold': 0.7,  # 行动置信度阈值
            'learning_rate': 0.1,         # 学习率
            'max_execution_time': 600,    # 最大执行时间(秒)
            'auto_approve': True,         # 自动审批模式
            'safe_mode': True,           # 安全模式
            'data_size_limit': 10000,    # 数据大小限制
            'url_limit': 100            # URL数量限制
        }

        # 爬虫场景触发规则
        self.crawler_trigger_rules = self._initialize_trigger_rules()

        # 启动爬虫工具
        asyncio.create_task(self._initialize_crawler_tool())

    async def _initialize_crawler_tool(self):
        """初始化爬虫工具"""
        try:
            await self.crawler_tool.initialize()
            logger.info('小诺爬虫控制器初始化成功')
        except Exception as e:
            logger.error(f"初始化爬虫工具失败: {e}")

    def _initialize_trigger_rules(self) -> dict[str, Any]:
        """初始化爬虫触发规则"""
        return {
            # 数据获取类
            'data_acquisition': {
                'keywords': ['获取', '收集', '抓取', '采集', '爬取', '提取'],
                'patterns': [r".*获取.*数据', r'.*收集.*信息', r'.*爬取.*网站"],
                'weight': 0.8,
                'scenarios': [CrawlerScenario.DATA_COLLECTION, CrawlerScenario.WEBSITE_SCRAPING]
            },

            # 搜索检索类
            'search_retrieval': {
                'keywords': ['搜索', '查找', '检索', '寻找', '找出'],
                'patterns': [r".*搜索.*', r'.*查找.*', r'.*检索.*"],
                'weight': 0.7,
                'scenarios': [CrawlerScenario.PATENT_SEARCH, CrawlerScenario.ACADEMIC_RESEARCH]
            },

            # 监控追踪类
            'monitoring_tracking': {
                'keywords': ['监控', '追踪', '关注', '留意', '跟踪'],
                'patterns': [r".*监控.*', r'.*追踪.*', r'.*关注.*"],
                'weight': 0.6,
                'scenarios': [CrawlerScenario.NEWS_MONITORING, CrawlerScenario.PRICE_TRACKING]
            },

            # 分析研究类
            'analysis_research': {
                'keywords': ['分析', '研究', '调研', '了解', '调查'],
                'patterns': [r".*分析.*', r'.*研究.*', r'.*调研.*"],
                'weight': 0.5,
                'scenarios': [CrawlerScenario.MARKET_RESEARCH, CrawlerScenario.COMPETITOR_ANALYSIS]
            },

            # 专利类
            'patent_related': {
                'keywords': ['专利', '发明', '知识产权', '专利检索', '专利申请'],
                'patterns': [r".*专利.*', r'.*发明.*', r'.*知识产权.*"],
                'weight': 0.9,
                'scenarios': [CrawlerScenario.PATENT_SEARCH]
            },

            # 学术类
            'academic_related': {
                'keywords': ['论文', '学术', '研究', '文献', '期刊'],
                'patterns': [r".*论文.*', r'.*学术.*', r'.*文献.*"],
                'weight': 0.8,
                'scenarios': [CrawlerScenario.ACADEMIC_RESEARCH]
            },

            # 新闻资讯类
            'news_related': {
                'keywords': ['新闻', '资讯', '动态', '消息', '报道'],
                'patterns': [r".*新闻.*', r'.*资讯.*', r'.*动态.*"],
                'weight': 0.6,
                'scenarios': [CrawlerScenario.NEWS_MONITORING]
            },

            # 价格商品类
            'price_product': {
                'keywords': ['价格', '商品', '产品', '多少钱', '费用'],
                'patterns': [r".*价格.*', r'.*商品.*', r'.*多少钱.*"],
                'weight': 0.7,
                'scenarios': [CrawlerScenario.PRODUCT_INFO, CrawlerScenario.PRICE_TRACKING]
            },

            # 社交媒体类
            'social_media': {
                'keywords': ['微博', '微信', '抖音', '社交', '媒体'],
                'patterns': [r".*微博.*', r'.*微信.*', r'.*抖音.*"],
                'weight': 0.5,
                'scenarios': [CrawlerScenario.SOCIAL_MEDIA]
            },

            # 竞品类
            'competitor': {
                'keywords': ['竞品', '对手', '竞争', '同行', '其他家'],
                'patterns': [r".*竞品.*', r'.*对手.*', r'.*竞争.*"],
                'weight': 0.8,
                'scenarios': [CrawlerScenario.COMPETITOR_ANALYSIS]
            }
        }

    async def analyze_request(self, user_input: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """分析用户请求，判断是否需要使用爬虫

        Args:
            user_input: 用户输入
            context: 上下文信息

        Returns:
            分析结果
        """
        logger.info(f"小诺分析爬虫请求: {user_input}")

        # 关键词触发检测
        trigger_matches = self._match_keywords(user_input)

        # 模式匹配检测
        pattern_matches = self._match_patterns(user_input)

        # URL检测
        url_matches = self._extract_urls(user_input)

        # 语义分析
        semantic_score = self._semantic_analysis(user_input)

        # 上下文分析
        context_score = self._analyze_context(user_input, context)

        # 历史经验分析
        experience_score = self._analyze_historical_experience(user_input)

        # 综合评分
        confidence_score = self._calculate_confidence(
            trigger_matches, pattern_matches, url_matches,
            semantic_score, context_score, experience_score
        )

        # 推荐场景
        recommended_scenario = self._recommend_scenario(user_input, trigger_matches)

        # 数据规模预估
        data_estimate = self._estimate_data_scale(user_input, url_matches)

        # 风险评估
        risk_assessment = self._assess_risk(user_input, recommended_scenario, data_estimate)

        result = {
            'should_use_crawler': confidence_score >= self.decision_config['confidence_threshold'],
            'confidence_score': confidence_score,
            'trigger_matches': trigger_matches,
            'pattern_matches': pattern_matches,
            'url_matches': url_matches,
            'recommended_scenario': recommended_scenario,
            'data_estimate': data_estimate,
            'risk_assessment': risk_assessment,
            'analysis_details': {
                'semantic_score': semantic_score,
                'context_score': context_score,
                'experience_score': experience_score
            },
            'timestamp': datetime.now().isoformat()
        }

        # 记录决策历史
        self.decision_history.append(result)

        logger.info(f"分析完成 - 置信度: {confidence_score:.2f}, 推荐场景: {recommended_scenario}")

        return result

    def _match_keywords(self, text: str) -> dict[str, int]:
        """匹配关键词"""
        matches = {}
        text_lower = text.lower()

        for category, rule in self.crawler_trigger_rules.items():
            count = 0
            for keyword in rule['keywords']:
                if keyword in text_lower:
                    count += 1
            if count > 0:
                matches[category] = count

        return matches

    def _match_patterns(self, text: str) -> list[str]:
        """匹配模式"""
        matches = []

        for category, rule in self.crawler_trigger_rules.items():
            for pattern in rule['patterns']:
                if re.search(pattern, text, re.IGNORECASE):
                    matches.append(category)
                    break

        return matches

    def _extract_urls(self, text: str) -> list[str]:
        """提取URL"""
        # 简单的URL正则表达式
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        return urls

    def _semantic_analysis(self, user_input: str) -> float:
        """语义分析"""
        score = 0.0

        # 数据获取意图
        data_acquisition_words = ['获取', '收集', '抓取', '提取', '下载']
        for word in data_acquisition_words:
            if word in user_input:
                score += 0.3

        # 搜索意图
        search_words = ['搜索', '查找', '检索', '寻找']
        for word in search_words:
            if word in user_input:
                score += 0.2

        # 监控意图
        monitoring_words = ['监控', '追踪', '关注', '跟踪']
        for word in monitoring_words:
            if word in user_input:
                score += 0.2

        # 分析意图
        analysis_words = ['分析', '研究', '调研', '了解']
        for word in analysis_words:
            if word in user_input:
                score += 0.1

        return min(score, 1.0)

    def _analyze_context(self, user_input: str, context: dict[str, Any] | None) -> float:
        """上下文分析"""
        if not context:
            return 0.5

        score = 0.0

        # 如果上下文中有爬虫相关活动
        if context.get('last_action') == 'crawling':
            score += 0.3

        # 如果用户之前问过类似问题
        if context.get('similar_questions', 0) > 0:
            score += 0.2

        # 如果是工作时间（更适合进行大规模数据收集）
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 18:
            score += 0.1

        return min(score, 1.0)

    def _analyze_historical_experience(self, user_input: str) -> float:
        """历史经验分析"""
        if not self.decision_history:
            return 0.5

        # 简单的历史相似度分析
        similar_decisions = [
            d for d in self.decision_history[-10:]  # 最近10次决策
            if any(kw in user_input.lower() for kw in ['爬取', '收集', '搜索', '专利'])
        ]

        if similar_decisions:
            success_rate = sum(1 for d in similar_decisions if d.get('should_use_crawler', False)) / len(similar_decisions)
            return success_rate

        return 0.5

    def _calculate_confidence(self, trigger_matches: dict, pattern_matches: list,
                            url_matches: list, semantic_score: float,
                            context_score: float, experience_score: float) -> float:
        """计算综合置信度"""
        # 关键词匹配权重: 30%
        keyword_score = min(len(trigger_matches) * 0.1, 1.0) * 0.3

        # 模式匹配权重: 20%
        pattern_score = min(len(pattern_matches) * 0.2, 1.0) * 0.2

        # URL存在权重: 20%
        url_score = min(len(url_matches) * 0.3, 1.0) * 0.2

        # 语义分析权重: 15%
        semantic_weighted = semantic_score * 0.15

        # 上下文分析权重: 10%
        context_weighted = context_score * 0.1

        # 历史经验权重: 5%
        experience_weighted = experience_score * 0.05

        return keyword_score + pattern_score + url_score + semantic_weighted + context_weighted + experience_weighted

    def _recommend_scenario(self, user_input: str, trigger_matches: dict[str, int]) -> str | None:
        """推荐场景"""
        if not trigger_matches:
            return None

        # 获取最高权重的类别
        best_category = max(trigger_matches.items(), key=lambda x: x[1])[0]

        # 从触发规则中获取推荐场景
        scenarios = self.crawler_trigger_rules[best_category]['scenarios']
        return scenarios[0].value if scenarios else None

    def _estimate_data_scale(self, user_input: str, url_matches: list[str]) -> dict[str, Any]:
        """预估数据规模"""
        # 基础规模
        base_scale = len(url_matches) * 10 if url_matches else 50

        # 关键词调整
        if '大量' in user_input or '批量' in user_input:
            base_scale *= 5
        elif '少量' in user_input or '几个' in user_input:
            base_scale = min(base_scale, 20)

        # 时间范围调整
        if '最近' in user_input or '实时' in user_input:
            base_scale *= 0.5

        return {
            'estimated_records': base_scale,
            'data_size_mb': base_scale * 0.1,  # 估算数据大小
            'processing_time_minutes': base_scale * 0.02  # 估算处理时间
        }

    def _assess_risk(self, user_input: str, scenario: str | None, data_estimate: dict[str, Any]) -> dict[str, Any]:
        """风险评估"""
        risk_level = 'low'
        risk_factors = []

        # 检查敏感词
        sensitive_words = ['破解', '攻击', '侵入', '非法', '未授权']
        if any(word in user_input for word in sensitive_words):
            risk_level = 'high'
            risk_factors.append('sensitive_operations')

        # 检查数据规模
        if data_estimate['estimated_records'] > self.decision_config['data_size_limit']:
            risk_level = max(risk_level, 'medium')
            risk_factors.append('large_data_volume')

        # 检查URL数量
        url_count = len(re.findall(r'https?://[^\s]+', user_input))
        if url_count > self.decision_config['url_limit']:
            risk_level = max(risk_level, 'medium')
            risk_factors.append('too_many_urls')

        # 检查特定场景风险
        high_risk_scenarios = ['social_media', 'competitor_analysis']
        if scenario in high_risk_scenarios:
            risk_level = max(risk_level, 'medium')
            risk_factors.append('sensitive_scenario')

        return {
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'recommendations': self._get_risk_recommendations(risk_level)
        }

    def _get_risk_recommendations(self, risk_level: str) -> list[str]:
        """获取风险建议"""
        recommendations = {
            'low': ['可以安全执行爬虫任务'],
            'medium': ['建议限制数据采集范围', '建议设置合理的频率限制', '确保遵守robots.txt'],
            'high': ['需要人工审核', '建议咨询法律意见', '确保符合相关法律法规']
        }
        return recommendations.get(risk_level, ['谨慎执行'])

    async def smart_crawler_execution(self, user_input: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """智能执行爬虫任务

        Args:
            user_input: 用户输入
            context: 上下文信息

        Returns:
            执行结果
        """
        logger.info(f"小诺智能执行爬虫任务: {user_input}")

        # 1. 分析请求
        analysis = await self.analyze_request(user_input, context)

        if not analysis['should_use_crawler']:
            return {
                'success': False,
                'reason': 'confidence_too_low',
                'message': f"置信度{analysis['confidence_score']:.2f}低于阈值{self.decision_config['confidence_threshold']}",
                'analysis': analysis,
                'suggestions': self._generate_alternative_suggestions(user_input)
            }

        # 2. 风险检查
        if analysis['risk_assessment']['risk_level'] == 'high' and not self.decision_config['safe_mode']:
            return {
                'success': False,
                'reason': 'high_risk',
                'message': '检测到高风险操作，安全模式下拒绝执行',
                'analysis': analysis,
                'risk_details': analysis['risk_assessment']
            }

        # 3. 自动审批检查
        if not self.decision_config['auto_approve']:
            # 在实际应用中，这里可以请求人工审批
            logger.info('等待人工审批...')

        # 4. 提取URL和配置参数
        urls = analysis['url_matches']
        if not urls:
            # 根据场景生成默认URL
            urls = self._generate_default_urls(user_input, analysis['recommended_scenario'])

        # 5. 构建爬虫配置
        crawler_config = self._build_crawler_config(user_input, analysis['recommended_scenario'], analysis)

        # 6. 执行爬虫任务
        try:
            if analysis['recommended_scenario']:
                # 使用预定义场景
                execution_result = await self.crawler_tool.execute_scenario(
                    CrawlerScenario(analysis['recommended_scenario']),
                    {
                        'urls': urls,
                        **crawler_config
                    }
                )
            else:
                # 使用自定义任务
                execution_result = await self.crawler_tool.execute_custom_task(urls, crawler_config)

            # 7. 学习和优化
            if self.learning_enabled:
                await self._learn_from_execution(analysis, execution_result)

            return {
                'success': True,
                'message': '爬虫任务执行成功',
                'analysis': analysis,
                'execution_result': {
                    'task_id': execution_result.task_id,
                    'success': execution_result.success,
                    'data_count': len(execution_result.data),
                    'execution_time': execution_result.execution_time,
                    'stats': execution_result.stats
                },
                'data_preview': execution_result.data[:3] if execution_result.data else [],  # 预览前3条数据
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"执行爬虫任务失败: {e}")
            return {
                'success': False,
                'reason': 'execution_error',
                'message': f"执行失败: {str(e)}",
                'analysis': analysis,
                'error_details': str(e)
            }

    def _generate_default_urls(self, user_input: str, scenario: str | None) -> list[str]:
        """根据场景生成默认URL"""
        url_templates = {
            'patent_search': [
                'https://patents.google.com/search?q=artificial+intelligence',
                'https://patents.google.com/search?q=machine+learning'
            ],
            'website_scraping': [
                'https://example.com',
                'https://example.org'
            ],
            'news_monitoring': [
                'https://news.google.com',
                'https://news.baidu.com'
            ],
            'product_info': [
                'https://www.amazon.com',
                'https://www.taobao.com'
            ],
            'competitor_analysis': [
                'https://www.google.com/search?q=competitor'
            ]
        }

        return url_templates.get(scenario, ['https://example.com'])

    def _build_crawler_config(self, user_input: str, scenario: str | None, analysis: dict[str, Any]) -> dict[str, Any]:
        """构建爬虫配置"""
        config = {}

        # 基础配置
        config['max_results'] = min(analysis['data_estimate']['estimated_records'], 1000)
        config['timeout'] = min(analysis['data_estimate']['processing_time_minutes'] * 60, 300)
        config['parallel_requests'] = min(10, max(1, config['max_results'] // 10))

        # 场景特定配置
        if scenario == 'patent_search':
            config.update({
                'include_claims': True,
                'include_citations': True,
                'date_range': '2020-2024'
            })
        elif scenario == 'news_monitoring':
            config.update({
                'real_time': True,
                'sentiment_analysis': True
            })
        elif scenario == 'price_tracking':
            config.update({
                'price_history': True,
                'alert_changes': True
            })

        # 根据用户输入调整配置
        if '最近' in user_input:
            config['time_range'] = '7d'
        if '详细' in user_input:
            config['include_details'] = True

        return config

    def _generate_alternative_suggestions(self, user_input: str) -> list[str]:
        """生成替代建议"""
        suggestions = [
            '我可以帮您分析如何获取这些信息',
            '建议使用官方API或公开数据接口',
            '可以考虑手动搜索相关信息'
        ]
        return suggestions[:2]

    async def _learn_from_execution(self, analysis: dict[str, Any], execution_result: Any):
        """从执行结果中学习"""
        # 简单的学习机制：根据执行结果调整决策权重
        success = execution_result.success if hasattr(execution_result, 'success') else False

        # 记录学习结果
        {
            'analysis': analysis,
            'execution_success': success,
            'confidence': analysis['confidence_score'],
            'timestamp': datetime.now().isoformat()
        }

        # 这里可以实现更复杂的学习算法
        logger.info(f"学习记录: 成功={success}, 置信度={analysis['confidence_score']:.2f}")

    def get_status(self) -> dict[str, Any]:
        """获取控制器状态"""
        return {
            'controller': 'XiaoNuoCrawlerController',
            'crawler_tool_status': self.crawler_tool.get_status(),
            'learning_enabled': self.learning_enabled,
            'decision_count': len(self.decision_history),
            'success_rate': self._calculate_success_rate(),
            'config': self.decision_config,
            'trigger_rules_count': len(self.crawler_trigger_rules),
            'timestamp': datetime.now().isoformat()
        }

    def _calculate_success_rate(self) -> float:
        """计算成功率"""
        if not self.decision_history:
            return 0.0

        successful = sum(1 for d in self.decision_history if d.get('should_use_crawler', False))
        return successful / len(self.decision_history)

    def update_config(self, new_config: dict[str, Any]) -> None:
        """更新配置"""
        self.decision_config.update(new_config)
        logger.info(f"小诺爬虫控制器配置已更新: {new_config}")

# 全局实例
xiaonuo_crawler_controller: XiaoNuoCrawlerController | None = None

def get_xiaonuo_crawler_controller() -> XiaoNuoCrawlerController:
    """获取小诺爬虫控制器实例"""
    global xiaonuo_crawler_controller
    if xiaonuo_crawler_controller is None:
        xiaonuo_crawler_controller = XiaoNuoCrawlerController()
    return xiaonuo_crawler_controller

# 测试函数
async def test_xiaonuo_crawler_controller():
    """测试小诺爬虫控制器"""
    logger.info('🕷️ 测试小诺智能爬虫控制器')
    logger.info(str('=' * 50))

    controller = get_xiaonuo_crawler_controller()

    # 等待初始化
    await asyncio.sleep(2)

    # 测试场景
    test_cases = [
        {
            'input': '帮我爬取Google Patents上的AI相关专利',
            'context': {'user': 'test_user', 'last_action': 'search'}
        },
        {
            'input': '监控最近的新闻动态',
            'context': {'last_action': 'monitoring'}
        },
        {
            'input': '从 https://example.com 获取产品信息',
            'context': {'url_provided': True}
        },
        {
            'input': '今天天气怎么样',
            'context': {}
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n🧪 测试{i}: {test_case['input']}")

        # 分析请求
        analysis = await controller.analyze_request(
            test_case['input'],
            test_case['context']
        )
        logger.info(f"   应该使用爬虫: {analysis['should_use_crawler']}")
        logger.info(f"   置信度: {analysis['confidence_score']:.2f}")
        logger.info(f"   推荐场景: {analysis['recommended_scenario']}")
        logger.info(f"   数据规模预估: {analysis['data_estimate']['estimated_records']}条")

        # 智能执行
        result = await controller.smart_crawler_execution(
            test_case['input'],
            test_case['context']
        )
        logger.info(f"   执行成功: {result['success']}")
        if result['success']:
            logger.info(f"   数据量: {result.get('execution_result', {}).get('data_count', 0)}条")
        elif not result['success']:
            logger.info(f"   失败原因: {result.get('reason', 'unknown')}")

    # 显示状态
    status = controller.get_status()
    logger.info("\n📊 控制器状态:")
    logger.info(f"   决策次数: {status['decision_count']}")
    logger.info(f"   成功率: {status['success_rate']:.2f}")

    logger.info("\n✅ 小诺爬虫控制器测试完成")

if __name__ == '__main__':
    asyncio.run(test_xiaonuo_crawler_controller())
