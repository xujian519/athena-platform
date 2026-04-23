#!/usr/bin/env python3
"""
小诺智能浏览器控制接口
智能决策何时使用浏览器自动化工具
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

# 导入浏览器自动化工具
from common_tools.browser_automation_tool import get_browser_tool

try:
    from .browser_automation.athena_browser_glm import AthenaBrowserGLMAgent
except ImportError:
    # 如果直接从services目录运行
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent / 'browser-automation'))
    from athena_browser_glm import AthenaBrowserGLMAgent

# 导入安全配置
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "core"))

logger = logging.getLogger(__name__)


class XiaoNuoBrowserController:
    """小诺智能浏览器控制器"""

    def __init__(self, glm_api_key: str):
        """初始化控制器

        Args:
            glm_api_key: GLM API密钥
        """
        self.glm_api_key = glm_api_key
        self.browser_tool = get_browser_tool()
        self.athena_agent = None
        self.decision_history = []
        self.learning_enabled = True

        # 智能决策配置
        self.decision_config = {
            'confidence_threshold': 0.7,  # 行动置信度阈值
            'learning_rate': 0.1,         # 学习率
            'max_execution_time': 300,    # 最大执行时间(秒)
            'auto_approve': True,         # 自动审批模式
            'safe_mode': True            # 安全模式
        }

        # 启动Athena代理
        asyncio.create_task(self._initialize_athena_agent())

    async def _initialize_athena_agent(self):
        """初始化Athena浏览器代理"""
        try:
            self.athena_agent = AthenaBrowserGLMAgent(api_key=self.glm_api_key)
            await self.athena_agent.start_session()
            logger.info('小诺浏览器控制器初始化成功')
        except Exception as e:
            logger.error(f"初始化Athena代理失败: {e}")

    async def analyze_request(self, user_input: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """分析用户请求，判断是否需要浏览器自动化

        Args:
            user_input: 用户输入
            context: 上下文信息

        Returns:
            分析结果
        """
        logger.info(f"小诺分析请求: {user_input}")

        # 关键词触发检测
        trigger_keywords = self._get_trigger_keywords()
        keyword_matches = self._match_keywords(user_input, trigger_keywords)

        # 语义分析
        semantic_score = await self._semantic_analysis(user_input)

        # 上下文分析
        context_score = self._analyze_context(user_input, context)

        # 历史经验分析
        experience_score = self._analyze_historical_experience(user_input)

        # 综合评分
        confidence_score = self._calculate_confidence(
            keyword_matches, semantic_score, context_score, experience_score
        )

        # 推荐场景
        recommended_scenario = self._recommend_scenario(user_input, keyword_matches)

        # 风险评估
        risk_assessment = self._assess_risk(user_input, recommended_scenario)

        result = {
            'should_use_browser': confidence_score >= self.decision_config['confidence_threshold'],
            'confidence_score': confidence_score,
            'keyword_matches': keyword_matches,
            'recommended_scenario': recommended_scenario,
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

    async def smart_task_execution(self, user_input: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """智能任务执行

        Args:
            user_input: 用户输入
            context: 上下文信息

        Returns:
            执行结果
        """
        logger.info(f"小诺智能执行任务: {user_input}")

        # 1. 分析请求
        analysis = await self.analyze_request(user_input, context)

        if not analysis['should_use_browser']:
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

        # 4. 执行浏览器自动化任务
        try:
            # 获取推荐场景
            scenario = analysis['recommended_scenario']
            if scenario:
                # 使用预定义场景
                execution_result = await self.browser_tool.execute_scenario(
                    scenario,
                    {'query': user_input, 'context': context}
                )
            else:
                # 使用自定义任务
                if self.athena_agent:
                    execution_result = await self.athena_agent.execute_task(user_input)
                else:
                    execution_result = await self.browser_tool.execute_custom_task(user_input)

            # 5. 学习和优化
            if self.learning_enabled:
                await self._learn_from_execution(analysis, execution_result)

            return {
                'success': True,
                'message': '浏览器自动化任务执行成功',
                'analysis': analysis,
                'execution_result': execution_result,
                'execution_time': execution_result.get('execution_time', 0),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"执行浏览器任务失败: {e}")
            return {
                'success': False,
                'reason': 'execution_error',
                'message': f"执行失败: {str(e)}",
                'analysis': analysis,
                'error_details': str(e)
            }

    def _get_trigger_keywords(self) -> dict[str, list[str]:
        """获取触发关键词"""
        return {
            'price_monitor': ['价格', '多少钱', '费用', '成本', '优惠', '折扣', '比价'],
            'competitor_monitor': ['竞品', '竞争对手', '同行', '其他家', '市面上'],
            'data_collection': ['数据', '统计', '收集', '整理', '汇总', '爬取'],
            'information_search': ['搜索', '查找', '找一下', '看看有没有', '信息'],
            'automation': ['自动', '帮我', '代替', '批量', '重复'],
            'monitor': ['监控', '关注', '留意', '通知', '提醒']
        }

    def _match_keywords(self, text: str, keywords: dict[str, list[str]) -> dict[str, int]:
        """匹配关键词"""
        matches = {}
        text_lower = text.lower()

        for category, kw_list in keywords.items():
            count = sum(1 for kw in kw_list if kw in text_lower)
            if count > 0:
                matches[category] = count

        return matches

    async def _semantic_analysis(self, user_input: str) -> float:
        """语义分析"""
        # 这里可以集成真正的语义理解模型
        # 目前使用基于规则的评分

        semantic_patterns = {
            'browser_action': ['访问', '打开', '点击', '输入', '搜索'],
            'information_retrieval': ['获取', '查看', '了解', '知道'],
            'comparison': ['对比', '比较', '差异', '区别'],
            'monitoring': ['关注', '监控', '留意', '跟踪']
        }

        score = 0.0
        for _pattern, words in semantic_patterns.items():
            if any(word in user_input for word in words):
                score += 0.2

        return min(score, 1.0)

    def _analyze_context(self, user_input: str, context: dict[str, Any] | None) -> float:
        """上下文分析"""
        if not context:
            return 0.5  # 默认分数

        score = 0.0

        # 如果上下文中有浏览器相关活动
        if context.get('last_action') == 'browser_automation':
            score += 0.3

        # 如果用户之前问过类似问题
        if context.get('similar_questions', 0) > 0:
            score += 0.2

        # 如果是工作时间
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 18:
            score += 0.1

        return min(score, 1.0)

    def _analyze_historical_experience(self, user_input: str) -> float:
        """历史经验分析"""
        if not self.decision_history:
            return 0.5  # 没有历史记录时返回默认分数

        # 简单的历史相似度分析
        similar_decisions = [
            d for d in self.decision_history[-10:]  # 最近10次决策
            if any(kw in user_input.lower() for kw in ['价格', '监控', '搜索'])
        ]

        if similar_decisions:
            success_rate = sum(1 for d in similar_decisions if d.get('success', False)) / len(similar_decisions)
            return success_rate

        return 0.5

    def _calculate_confidence(self, keyword_matches: dict, semantic_score: float,
                            context_score: float, experience_score: float) -> float:
        """计算综合置信度"""
        # 关键词匹配权重: 40%
        keyword_score = min(len(keyword_matches) * 0.2, 1.0) * 0.4

        # 语义分析权重: 25%
        semantic_weighted = semantic_score * 0.25

        # 上下文分析权重: 20%
        context_weighted = context_score * 0.2

        # 历史经验权重: 15%
        experience_weighted = experience_score * 0.15

        return keyword_score + semantic_weighted + context_weighted + experience_weighted

    def _recommend_scenario(self, user_input: str, keyword_matches: dict[str, int]) -> str | None:
        """推荐场景"""
        if not keyword_matches:
            return None

        # 返回匹配度最高的场景
        return max(keyword_matches.items(), key=lambda x: x[1])[0]

    def _assess_risk(self, user_input: str, scenario: str | None) -> dict[str, Any]:
        """风险评估"""
        risk_level = 'low'
        risk_factors = []

        # 检查敏感词
        sensitive_words = ['密码', '支付', '转账', '删除', '修改']
        if any(word in user_input for word in sensitive_words):
            risk_level = 'high'
            risk_factors.append('sensitive_operations')

        # 检查未知网站
        if 'http' in user_input and not any(site in user_input for site in ['淘宝', '京东', '百度']):
            risk_level = 'medium'
            risk_factors.append('unknown_website')

        # 检查批量操作
        if any(word in user_input for word in ['批量', '全部', '所有']):
            risk_level = max(risk_level, 'medium')
            risk_factors.append('batch_operations')

        return {
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'recommendations': self._get_risk_recommendations(risk_level)
        }

    def _get_risk_recommendations(self, risk_level: str) -> list[str]:
        """获取风险建议"""
        recommendations = {
            'low': ['可以安全执行'],
            'medium': ['建议用户确认后执行', '限制操作范围'],
            'high': ['需要人工审批', '建议在安全模式下执行', '记录详细日志']
        }
        return recommendations.get(risk_level, [])

    def _generate_alternative_suggestions(self, user_input: str) -> list[str]:
        """生成替代建议"""
        suggestions = [
            '您可以手动访问相关网站',
            '我可以帮您分析如何获取这些信息',
            '建议使用官方API或数据接口'
        ]
        return suggestions[:2]  # 返回前2个建议

    async def _learn_from_execution(self, analysis: dict[str, Any], execution_result: dict[str, Any]):
        """从执行结果中学习"""
        # 简单的学习机制：根据执行结果调整决策权重
        success = execution_result.get('success', False)

        # 记录学习结果
        {
            'analysis': analysis,
            'execution_result': execution_result,
            'success': success,
            'timestamp': datetime.now().isoformat()
        }

        # 这里可以实现更复杂的学习算法
        logger.info(f"学习记录: {success}")

    def get_status(self) -> dict[str, Any]:
        """获取控制器状态"""
        return {
            'controller': 'XiaoNuoBrowserController',
            'initialized': self.athena_agent is not None,
            'learning_enabled': self.learning_enabled,
            'decision_count': len(self.decision_history),
            'success_rate': self._calculate_success_rate(),
            'config': self.decision_config,
            'timestamp': datetime.now().isoformat()
        }

    def _calculate_success_rate(self) -> float:
        """计算成功率"""
        if not self.decision_history:
            return 0.0

        successful = sum(1 for d in self.decision_history if d.get('success', False))
        return successful / len(self.decision_history)

    def update_config(self, new_config: dict[str, Any]) -> None:
        """更新配置"""
        self.decision_config.update(new_config)
        logger.info(f"配置已更新: {new_config}")


# 全局实例
xiaonuo_controller: XiaoNuoBrowserController | None = None


def get_xiaonuo_controller(glm_api_key: str = '9efe5766a7cd4bb687e40082ee4032b6.0mYTotbC7aRmoNCe') -> XiaoNuoBrowserController:
    """获取小诺控制器实例"""
    global xiaonuo_controller
    if xiaonuo_controller is None:
        xiaonuo_controller = XiaoNuoBrowserController(glm_api_key=glm_api_key)
    return xiaonuo_controller


# 测试函数
async def test_xiaonuo_controller():
    """测试小诺控制器"""
    logger.info('🤖 测试小诺智能浏览器控制器')
    logger.info(str('=' * 50))

    controller = get_xiaonuo_controller()

    # 测试场景
    test_cases = [
        {
            'input': '帮我监控淘宝上iPhone 15的价格',
            'context': {'user': 'test_user', 'last_action': 'search'}
        },
        {
            'input': '我想了解竞品的最新动态',
            'context': {'last_action': 'browser_automation'}
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
        logger.info(f"   应该使用浏览器: {analysis['should_use_browser']}")
        logger.info(f"   置信度: {analysis['confidence_score']:.2f}")
        logger.info(f"   推荐场景: {analysis['recommended_scenario']}")

        # 智能执行
        result = await controller.smart_task_execution(
            test_case['input'],
            test_case['context']
        )
        logger.info(f"   执行成功: {result['success']}")
        if not result['success']:
            logger.info(f"   原因: {result.get('reason', 'unknown')}")

    # 显示状态
    status = controller.get_status()
    logger.info("\n📊 控制器状态:")
    logger.info(f"   决策次数: {status['decision_count']}")
    logger.info(f"   成功率: {status['success_rate']:.2f}")

    logger.info("\n✅ 测试完成")


if __name__ == '__main__':
    asyncio.run(test_xiaonuo_controller())
