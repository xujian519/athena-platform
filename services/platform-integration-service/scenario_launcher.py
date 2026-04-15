#!/usr/bin/env python3
"""
场景识别和自动启动机制
智能识别用户意图并启动相应的浏览器自动化场景
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from browser_integration_service import get_integration_service

logger = logging.getLogger(__name__)

class ScenarioType(Enum):
    """场景类型枚举"""
    PRICE_MONITOR = 'price_monitor'
    COMPETITOR_MONITOR = 'competitor_monitor'
    DATA_COLLECTION = 'data_collection'
    PATENT_SEARCH = 'patent_search'
    INFORMATION_SEARCH = 'information_search'
    AUTOMATION = 'automation'
    SOCIAL_MEDIA = 'social_media'
    NEWS_MONITORING = 'news_monitoring'
    MARKET_RESEARCH = 'market_research'
    ACADEMIC_RESEARCH = 'academic_research'

@dataclass
class ScenarioTrigger:
    """场景触发器"""
    scenario_type: ScenarioType
    keywords: list[str]
    patterns: list[str]
    confidence_threshold: float
    priority: int
    description: str

@dataclass
class ExecutionPlan:
    """执行计划"""
    scenario_type: ScenarioType
    confidence: float
    execution_mode: str  # xiaonuo, athena, direct
    parameters: dict[str, Any]
    estimated_time: int  # 预估执行时间(秒)
    risk_level: str  # low, medium, high

class ScenarioLauncher:
    """场景启动器"""

    def __init__(self):
        """初始化场景启动器"""
        self.integration_service = get_integration_service()
        self.trigger_rules = self._initialize_trigger_rules()
        self.execution_history = []
        self.learning_enabled = True

        # 性能指标
        self.metrics = {
            'total_recognitions': 0,
            'successful_launches': 0,
            'scenario_usage': {},
            'accuracy_rate': 0.0
        }

    def _initialize_trigger_rules(self) -> list[ScenarioTrigger]:
        """初始化触发规则"""
        return [
            ScenarioTrigger(
                scenario_type=ScenarioType.PRICE_MONITOR,
                keywords=['价格', '多少钱', '费用', '成本', '优惠', '折扣', '比价', '降价', '涨价'],
                patterns=[r".*价格.*', r'.*多少钱.*', r'.*成本.*"],
                confidence_threshold=0.6,
                priority=1,
                description='监控商品价格变化'
            ),
            ScenarioTrigger(
                scenario_type=ScenarioType.COMPETITOR_MONITOR,
                keywords=['竞品', '竞争对手', '同行', '其他家', '市面上', '竞对'],
                patterns=[r".*竞品.*', r'.*对手.*', r'.*同行.*"],
                confidence_threshold=0.7,
                priority=2,
                description='监控竞争对手动态'
            ),
            ScenarioTrigger(
                scenario_type=ScenarioType.PATENT_SEARCH,
                keywords=['专利', '发明', '知识产权', '专利检索', '专利搜索', '专利申请'],
                patterns=[r".*专利.*', r'.*发明.*', r'.*知识产权.*"],
                confidence_threshold=0.8,
                priority=3,
                description='检索和分析专利信息'
            ),
            ScenarioTrigger(
                scenario_type=ScenarioType.DATA_COLLECTION,
                keywords=['数据', '统计', '收集', '整理', '汇总', '爬取', '抓取'],
                patterns=[r".*收集.*数据.*', r'.*统计.*', r'.*爬取.*"],
                confidence_threshold=0.6,
                priority=2,
                description='收集和整理数据'
            ),
            ScenarioTrigger(
                scenario_type=ScenarioType.SOCIAL_MEDIA,
                keywords=['微博', '微信', '抖音', '小红书', '社交媒体', '社交平台'],
                patterns=[r".*微博.*', r'.*微信.*', r'.*抖音.*"],
                confidence_threshold=0.5,
                priority=1,
                description='社交媒体内容监控'
            ),
            ScenarioTrigger(
                scenario_type=ScenarioType.NEWS_MONITORING,
                keywords=['新闻', '资讯', '动态', '消息', '报道', '新闻稿'],
                patterns=[r".*新闻.*', r'.*资讯.*', r'.*动态.*"],
                confidence_threshold=0.5,
                priority=2,
                description='监控新闻和资讯'
            ),
            ScenarioTrigger(
                scenario_type=ScenarioType.MARKET_RESEARCH,
                keywords=['市场', '调研', '分析', '报告', '趋势', '行业'],
                patterns=[r".*市场.*', r'.*调研.*', r'.*趋势.*"],
                confidence_threshold=0.6,
                priority=3,
                description='市场调研和分析'
            ),
            ScenarioTrigger(
                scenario_type=ScenarioType.ACADEMIC_RESEARCH,
                keywords=['论文', '学术', '研究', '期刊', '文献', '学术搜索'],
                patterns=[r".*论文.*', r'.*学术.*', r'.*研究.*"],
                confidence_threshold=0.7,
                priority=3,
                description='学术文献检索'
            ),
            ScenarioTrigger(
                scenario_type=ScenarioType.INFORMATION_SEARCH,
                keywords=['搜索', '查找', '找一下', '看看有没有', '信息', '资料'],
                patterns=[r".*搜索.*', r'.*查找.*', r'.*找.*"],
                confidence_threshold=0.4,
                priority=1,
                description='一般信息搜索'
            ),
            ScenarioTrigger(
                scenario_type=ScenarioType.AUTOMATION,
                keywords=['自动', '帮我', '代替', '批量', '重复', '定时'],
                patterns=[r".*自动.*', r'.*帮我.*', r'.*批量.*"],
                confidence_threshold=0.5,
                priority=2,
                description='自动化任务'
            )
        ]

    async def recognize_scenario(self, user_input: str, context: dict[str, Any] | None = None) -> list[ExecutionPlan]:
        """识别场景并生成执行计划

        Args:
            user_input: 用户输入
            context: 上下文信息

        Returns:
            执行计划列表，按置信度排序
        """
        self.metrics['total_recognitions'] += 1
        logger.info(f"识别场景: {user_input}")

        plans = []

        # 遍历所有触发规则
        for trigger in self.trigger_rules:
            confidence = self._calculate_confidence(user_input, trigger)

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

        logger.info(f"识别到 {len(plans)} 个潜在场景")
        return plans

    def _calculate_confidence(self, user_input: str, trigger: ScenarioTrigger) -> float:
        """计算匹配置信度"""
        input_lower = user_input.lower()

        # 关键词匹配得分 (权重: 50%)
        keyword_score = 0.0
        matched_keywords = 0
        for keyword in trigger.keywords:
            if keyword in input_lower:
                matched_keywords += 1
        keyword_score = matched_keywords / len(trigger.keywords) * 0.5

        # 模式匹配得分 (权重: 30%)
        pattern_score = 0.0
        import re
        for pattern in trigger.patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                pattern_score += 0.3
        pattern_score = min(pattern_score, 0.3)

        # 上下文相关性得分 (权重: 20%)
        context_score = self._calculate_context_score(user_input, trigger) * 0.2

        return keyword_score + pattern_score + context_score

    def _calculate_context_score(self, user_input: str, trigger: ScenarioTrigger) -> float:
        """计算上下文相关性得分"""
        # 简单的上下文评分逻辑
        score = 0.0

        # 时间相关性
        current_hour = datetime.now().hour
        if trigger.scenario_type in [ScenarioType.PRICE_MONITOR, ScenarioType.NEWS_MONITORING]:
            if 9 <= current_hour <= 18:  # 工作时间
                score += 0.3

        # 历史成功率
        if trigger.scenario_type.value in self.metrics['scenario_usage']:
            success_rate = self.metrics['scenario_usage'][trigger.scenario_type.value].get('success_rate', 0.5)
            score += success_rate * 0.4

        return min(score, 1.0)

    async def _create_execution_plan(
        self,
        trigger: ScenarioTrigger,
        confidence: float,
        user_input: str,
        context: dict[str, Any] | None
    ) -> ExecutionPlan:
        """创建执行计划"""
        # 根据场景类型确定执行模式
        execution_mode = self._determine_execution_mode(trigger.scenario_type, confidence)

        # 提取参数
        parameters = self._extract_parameters(user_input, trigger.scenario_type, context)

        # 估算执行时间
        estimated_time = self._estimate_execution_time(trigger.scenario_type, parameters)

        # 评估风险级别
        risk_level = self._assess_risk_level(trigger.scenario_type, user_input)

        return ExecutionPlan(
            scenario_type=trigger.scenario_type,
            confidence=confidence,
            execution_mode=execution_mode,
            parameters=parameters,
            estimated_time=estimated_time,
            risk_level=risk_level
        )

    def _determine_execution_mode(self, scenario_type: ScenarioType, confidence: float) -> str:
        """确定执行模式"""
        # 高置信度且复杂场景使用小诺
        if confidence > 0.8 and scenario_type in [
            ScenarioType.COMPETITOR_MONITOR,
            ScenarioType.MARKET_RESEARCH,
            ScenarioType.ACADEMIC_RESEARCH
        ]:
            return 'xiaonuo'

        # 专利检索使用Athena专业代理
        if scenario_type == ScenarioType.PATENT_SEARCH:
            return 'athena'

        # 简单场景直接执行
        if scenario_type in [ScenarioType.PRICE_MONITOR, ScenarioType.INFORMATION_SEARCH]:
            return 'direct'

        # 默认使用小诺
        return 'xiaonuo'

    def _extract_parameters(self, user_input: str, scenario_type: ScenarioType, context: dict[str, Any] | None) -> dict[str, Any]:
        """提取场景参数"""
        parameters = {'user_input': user_input}

        if scenario_type == ScenarioType.PRICE_MONITOR:
            # 提取商品名称
            products = self._extract_products(user_input)
            parameters['products'] = products

        elif scenario_type == ScenarioType.COMPETITOR_MONITOR:
            # 提取竞争对手名称
            competitors = self._extract_competitors(user_input)
            parameters['competitors'] = competitors

        elif scenario_type == ScenarioType.PATENT_SEARCH:
            # 提取专利关键词
            keywords = self._extract_patent_keywords(user_input)
            parameters['keywords'] = keywords

        # 添加上下文信息
        if context:
            parameters.update(context)

        return parameters

    def _extract_products(self, text: str) -> list[str]:
        """提取商品名称"""
        # 简单的商品名称提取逻辑
        common_products = ['i_phone', '华为', '小米', '三星', 'MacBook', '戴尔', '联想']
        found = []
        for product in common_products:
            if product in text:
                found.append(product)
        return found or ['通用商品']

    def _extract_competitors(self, text: str) -> list[str]:
        """提取竞争对手名称"""
        common_companies = ['阿里巴巴', '腾讯', '百度', '字节跳动', '京东', '美团']
        found = []
        for company in common_companies:
            if company in text:
                found.append(company)
        return found or ['主要竞争对手']

    def _extract_patent_keywords(self, text: str) -> list[str]:
        """提取专利关键词"""
        # 简单的关键词提取
        keywords = []
        if '人工智能' in text:
            keywords.append('人工智能')
        if '机器学习' in text:
            keywords.append('机器学习')
        if '深度学习' in text:
            keywords.append('深度学习')
        return keywords or ['技术创新']

    def _estimate_execution_time(self, scenario_type: ScenarioType, parameters: dict[str, Any]) -> int:
        """估算执行时间"""
        base_times = {
            ScenarioType.PRICE_MONITOR: 30,
            ScenarioType.COMPETITOR_MONITOR: 120,
            ScenarioType.PATENT_SEARCH: 60,
            ScenarioType.DATA_COLLECTION: 180,
            ScenarioType.INFORMATION_SEARCH: 20,
            ScenarioType.SOCIAL_MEDIA: 45,
            ScenarioType.NEWS_MONITORING: 60,
            ScenarioType.MARKET_RESEARCH: 300,
            ScenarioType.ACADEMIC_RESEARCH: 240,
            ScenarioType.AUTOMATION: 90
        }

        base_time = base_times.get(scenario_type, 60)

        # 根据参数调整时间
        if 'products' in parameters and len(parameters['products']) > 1:
            base_time *= len(parameters['products'])

        if 'competitors' in parameters and len(parameters['competitors']) > 1:
            base_time *= len(parameters['competitors'])

        return base_time

    def _assess_risk_level(self, scenario_type: ScenarioType, user_input: str) -> str:
        """评估风险级别"""
        # 检查敏感词
        sensitive_words = ['密码', '支付', '转账', '删除', '修改', '破解']
        if any(word in user_input for word in sensitive_words):
            return 'high'

        # 某些场景风险较高
        high_risk_scenarios = [ScenarioType.SOCIAL_MEDIA, ScenarioType.AUTOMATION]
        if scenario_type in high_risk_scenarios:
            return 'medium'

        return 'low'

    async def auto_launch(self, user_input: str, context: dict[str, Any] | None = None, auto_confirm: bool = False) -> dict[str, Any]:
        """自动识别并启动场景

        Args:
            user_input: 用户输入
            context: 上下文信息
            auto_confirm: 是否自动确认执行

        Returns:
            启动结果
        """
        logger.info(f"自动启动场景: {user_input}")

        # 识别场景
        plans = await self.recognize_scenario(user_input, context)

        if not plans:
            return {
                'success': False,
                'reason': 'no_scenario_matched',
                'message': '没有识别到合适的场景',
                'suggestions': ['请更详细地描述您的需求']
            }

        # 选择最佳计划
        best_plan = plans[0]

        # 风险检查
        if best_plan.risk_level == 'high' and not auto_confirm:
            return {
                'success': False,
                'reason': 'high_risk',
                'message': '检测到高风险操作，需要人工确认',
                'plan': best_plan,
                'risk_details': '建议在安全模式下执行'
            }

        # 置信度检查
        if best_plan.confidence < 0.6 and not auto_confirm:
            return {
                'success': False,
                'reason': 'low_confidence',
                'message': f"置信度{best_plan.confidence:.2f}过低，请确认是否继续",
                'plan': best_plan,
                'alternatives': plans[1:3] if len(plans) > 1 else []
            }

        # 执行最佳计划
        try:
            execution_result = await self._execute_plan(best_plan)

            # 更新指标
            self._update_metrics(best_plan.scenario_type, True)

            return {
                'success': True,
                'message': '场景启动成功',
                'plan': best_plan,
                'execution_result': execution_result,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"执行场景失败: {e}")
            self._update_metrics(best_plan.scenario_type, False)

            return {
                'success': False,
                'reason': 'execution_failed',
                'message': f"执行失败: {str(e)}",
                'plan': best_plan
            }

    async def _execute_plan(self, plan: ExecutionPlan) -> dict[str, Any]:
        """执行计划"""
        request_params = {
            'user_input': plan.parameters.get('user_input', ''),
            'mode': plan.execution_mode,
            'context': plan.parameters,
            'scenario': plan.scenario_type.value
        }

        result = await self.integration_service.process_request(request_params)
        return result

    def _record_recognition(self, user_input: str, plans: list[ExecutionPlan]) -> Any:
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

    def _update_metrics(self, scenario_type: ScenarioType, success: bool) -> Any:
        """更新性能指标"""
        scenario_key = scenario_type.value

        if scenario_key not in self.metrics['scenario_usage']:
            self.metrics['scenario_usage'][scenario_key] = {
                'total': 0,
                'success': 0,
                'success_rate': 0.0
            }

        self.metrics['scenario_usage'][scenario_key]['total'] += 1
        if success:
            self.metrics['scenario_usage'][scenario_key]['success'] += 1
            self.metrics['successful_launches'] += 1

        # 计算成功率
        usage = self.metrics['scenario_usage'][scenario_key]
        usage['success_rate'] = usage['success'] / usage['total']

        # 计算总体准确率
        if self.metrics['total_recognitions'] > 0:
            self.metrics['accuracy_rate'] = self.metrics['successful_launches'] / self.metrics['total_recognitions']

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
                    'priority': trigger.priority
                }
                for trigger in self.trigger_rules
            ],
            'total_count': len(self.trigger_rules)
        }

# 全局实例
scenario_launcher: ScenarioLauncher | None = None

def get_scenario_launcher() -> ScenarioLauncher:
    """获取场景启动器实例"""
    global scenario_launcher
    if scenario_launcher is None:
        scenario_launcher = ScenarioLauncher()
    return scenario_launcher

# 测试函数
async def test_scenario_launcher():
    """测试场景启动器"""
    logger.info('🎯 测试场景识别和启动机制')
    logger.info(str('=' * 50))

    launcher = get_scenario_launcher()

    # 测试用例
    test_cases = [
        '帮我监控iPhone 15的价格变化',
        '我想了解一下阿里巴巴的最新动态',
        '搜索人工智能相关的专利',
        '收集市场上的竞争对手信息',
        '查看今天的新闻头条',
        '找一些学术论文资料'
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

    # 显示可用场景
    scenarios = launcher.get_available_scenarios()
    logger.info(f"\n🎯 可用场景数: {scenarios['total_count']}")

    logger.info("\n✅ 场景启动器测试完成")

if __name__ == '__main__':
    asyncio.run(test_scenario_launcher())
