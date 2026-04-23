#!/usr/bin/env python3
"""
小诺和小娜的LangExtract智能控制系统
AI助手完全控制的结构化信息提取系统
"""

import logging
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from common_tools.langextract_tool import ExtractionScenario, get_langextract_tool

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class ExtractionIntent(Enum):
    """提取意图枚举"""
    STRUCTURED_EXTRACTION = 'structured_extraction'
    ENTITY_RECOGNITION = 'entity_recognition'
    RELATION_EXTRACTION = 'relation_extraction'
    KEYWORD_ANALYSIS = 'keyword_analysis'
    SENTIMENT_ANALYSIS = 'sentiment_analysis'
    TOPIC_MODELING = 'topic_modeling'
    SUMMARIZATION = 'summarization'
    QUESTION_ANSWERING = 'question_answering'


@dataclass
class ExtractionRequest:
    """提取请求数据结构"""
    user_input: str
    context: dict[str, Any] = None
    confidence_threshold: float = 0.7
    max_execution_time: int = 300
    auto_approve: bool = True


@dataclass
class ExtractionAnalysis:
    """提取分析结果"""
    should_extract: bool
    confidence_score: float
    recommended_scenario: str
    extraction_intent: str
    estimated_complexity: str
    processing_time_estimate: int
    risk_assessment: str
    suggested_prompts: list[str]
    data_estimate: dict[str, Any]


class XiaoNuoLangExtractController:
    """小诺和小娜LangExtract智能控制器"""

    def __init__(self):
        """初始化控制器"""
        self.langextract_tool = get_langextract_tool()
        self.intent_patterns = self._load_intent_patterns()
        self.scenario_keywords = self._load_scenario_keywords()
        self.extraction_history = []
        self.learning_model = {}

        logger.info('小诺LangExtract控制器初始化完成')

    def _load_intent_patterns(self) -> dict[str, list[str]:
        """加载意图识别模式"""
        return {
            ExtractionIntent.STRUCTURED_EXTRACTION.value: [
                r"提取.*信息', r'抽取.*数据', r'识别.*内容', r'解析.*文档",
                r"分析.*文本', r'处理.*资料', r'整理.*内容', r'结构化.*"
            ],
            ExtractionIntent.ENTITY_RECOGNITION.value: [
                r"识别.*实体', r'找出.*名称', r'提取.*关键词', r'发现.*名词",
                r"标注.*实体', r'标记.*对象', r'定位.*项目"
            ],
            ExtractionIntent.RELATION_EXTRACTION.value: [
                r"分析.*关系', r'找出.*联系', r'识别.*依赖', r'提取.*关联",
                r"发现.*连接', r'确定.*关系', r'分析.*网络"
            ],
            ExtractionIntent.KEYWORD_ANALYSIS.value: [
                r"关键词.*分析', r'重要.*词汇', r'核心.*概念', r'主题.*词",
                r"热词.*提取', r'词汇.*统计', r'词频.*分析"
            ],
            ExtractionIntent.SENTIMENT_ANALYSIS.value: [
                r"情感.*分析', r'情绪.*识别', r'态度.*判断', r'观点.*提取",
                r"正面.*负面', r'评价.*分析', r'感受.*识别"
            ],
            ExtractionIntent.TOPIC_MODELING.value: [
                r"主题.*分析', r'话题.*识别', r'分类.*分析', r'聚类.*分析",
                r"主题.*划分', r'类别.*识别', r'群体.*分析"
            ],
            ExtractionIntent.SUMMARIZATION.value: [
                r"总结.*内容', r'摘要.*生成', r'要点.*提取', r'概括.*信息",
                r"精简.*内容', r'核心.*观点', r'主要.*内容"
            ],
            ExtractionIntent.QUESTION_ANSWERING.value: [
                r"回答.*问题', r'解答.*疑问', r'提供.*答案', r'信息.*查询",
                r"具体.*问题', r'详细.*解答', r'事实.*查询"
            ]
        }

    def _load_scenario_keywords(self) -> dict[str, list[str]:
        """加载场景关键词"""
        return {
            ExtractionScenario.PATENT_ANALYSIS.value: [
                '专利', '发明', '权利要求', '技术方案', '创新点', '说明书',
                '专利号', '申请人', '发明人', '专利局', '知识产权', '技术特征'
            ],
            ExtractionScenario.CONTRACT_REVIEW.value: [
                '合同', '协议', '条款', '当事人', '权利', '义务', '违约',
                '法律责任', '有效期', '签署', '盖章', '法律效力', '约束力'
            ],
            ExtractionScenario.MEDICAL_REPORT.value: [
                '医疗', '诊断', '病历', '检查', '症状', '治疗', '用药',
                '患者', '医生', '医院', '健康', '疾病', '康复', '处方'
            ],
            ExtractionScenario.FINANCIAL_STATEMENT.value: [
                '财务', '报表', '收入', '利润', '资产', '负债', '现金流',
                '财报', '业绩', '营收', '成本', '投资', '收益', '亏损'
            ],
            ExtractionScenario.ACADEMIC_PAPER.value: [
                '论文', '学术', '研究', '实验', '方法', '结果', '结论',
                '期刊', '会议', '作者', '引用', '文献', '学术期刊', '研究方法'
            ],
            ExtractionScenario.NEWS_ARTICLE.value: [
                '新闻', '报道', '事件', '消息', '记者', '新闻稿', '媒体',
                '时事', '热点', '头条', '新闻发布', '报道时间', '新闻媒体'
            ],
            ExtractionScenario.PRODUCT_REVIEW.value: [
                '产品', '评测', '评价', '使用', '体验', '功能', '性能',
                '优缺点', '推荐', '购买', '价格', '质量', '品牌', '型号'
            ],
            ExtractionScenario.LEGAL_DOCUMENT.value: [
                '法律', '法规', '法条', '法案', '司法解释', '法律文书',
                '法院', '判决', '诉讼', '律师', '法律程序', '法规制度'
            ],
            ExtractionScenario.TECHNICAL_DOCUMENT.value: [
                '技术', '文档', '说明', '手册', '规范', '标准', '流程',
                '技术规格', 'API', '接口', '系统', '架构', '设计', '开发'
            ],
            ExtractionScenario.BUSINESS_REPORT.value: [
                '商业', '报告', '分析', '市场', '业务', '战略', '营销',
                '销售', '客户', '竞争', '市场分析', '商业计划', '企业报告'
            ],
            ExtractionScenario.USER_FEEDBACK.value: [
                '用户', '反馈', '意见', '建议', '评论', '投诉', '评价',
                '满意度', '用户体验', '客户服务', '用户需求', '改进建议'
            ],
            ExtractionScenario.MARKET_RESEARCH.value: [
                '市场', '调研', '调查', '问卷', '数据', '统计', '分析',
                '趋势', '预测', '消费者', '行为', '偏好', '市场研究'
            ]
        }

    async def initialize(self) -> bool:
        """初始化控制器"""
        try:
            # 初始化LangExtract工具
            success = await self.langextract_tool.initialize()
            if not success:
                logger.warning('LangExtract工具初始化失败，将使用降级模式')

            logger.info('小诺LangExtract控制器初始化成功')
            return True

        except Exception as e:
            logger.error(f"小诺LangExtract控制器初始化失败: {e}")
            return False

    def get_status(self) -> dict[str, Any]:
        """获取控制器状态"""
        return {
            'controller': '小诺LangExtract智能控制器',
            'status': 'running',
            'tool_available': self.langextract_tool.is_available,
            'supported_intents': len(self.intent_patterns),
            'supported_scenarios': len(self.scenario_keywords),
            'extraction_history': len(self.extraction_history),
            'learning_enabled': True,
            'version': '1.0.0'
        }

    async def analyze_request(self, user_input: str, context: dict[str, Any] = None) -> ExtractionAnalysis:
        """分析用户的提取请求"""
        try:
            logger.info(f"开始分析用户请求: {user_input[:100]}...")

            # 1. 意图识别
            extraction_intent = self._identify_intent(user_input)

            # 2. 场景匹配
            recommended_scenario = self._match_scenario(user_input)

            # 3. 置信度评估
            confidence_score = self._calculate_confidence(
                user_input, extraction_intent, recommended_scenario
            )

            # 4. 复杂度评估
            estimated_complexity = self._assess_complexity(user_input, extraction_intent)

            # 5. 处理时间估算
            processing_time_estimate = self._estimate_processing_time(
                user_input, estimated_complexity
            )

            # 6. 风险评估
            risk_assessment = self._assess_risk(user_input, context)

            # 7. 生成提示建议
            suggested_prompts = self._generate_prompt_suggestions(
                extraction_intent, recommended_scenario, user_input
            )

            # 8. 数据量估算
            data_estimate = self._estimate_data_volume(user_input)

            # 9. 决定是否应该执行提取
            should_extract = confidence_score >= 0.6 and risk_assessment != 'high'

            analysis = ExtractionAnalysis(
                should_extract=should_extract,
                confidence_score=confidence_score,
                recommended_scenario=recommended_scenario,
                extraction_intent=extraction_intent,
                estimated_complexity=estimated_complexity,
                processing_time_estimate=processing_time_estimate,
                risk_assessment=risk_assessment,
                suggested_prompts=suggested_prompts,
                data_estimate=data_estimate
            )

            # 记录分析历史
            self.extraction_history.append({
                'timestamp': datetime.now().isoformat(),
                'user_input': user_input,
                'analysis': analysis.__dict__
            })

            logger.info(f"请求分析完成，置信度: {confidence_score:.2f}, 推荐场景: {recommended_scenario}")

            return analysis

        except Exception as e:
            logger.error(f"请求分析失败: {e}")
            return ExtractionAnalysis(
                should_extract=False,
                confidence_score=0.0,
                recommended_scenario='',
                extraction_intent='unknown',
                estimated_complexity='unknown',
                processing_time_estimate=0,
                risk_assessment='high',
                suggested_prompts=[],
                data_estimate={'estimated_records': 0}
            )

    def _identify_intent(self, user_input: str) -> str:
        """识别用户意图"""
        text = user_input.lower()

        # 计算每个意图的匹配分数
        intent_scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    score += 1
            intent_scores[intent] = score

        # 返回得分最高的意图
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            if intent_scores[best_intent] > 0:
                return best_intent

        # 如果没有匹配到具体意图，返回结构化提取
        return ExtractionIntent.STRUCTURED_EXTRACTION.value

    def _match_scenario(self, user_input: str) -> str:
        """匹配最佳提取场景"""
        text = user_input.lower()

        # 计算每个场景的匹配分数
        scenario_scores = {}
        for scenario, keywords in self.scenario_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            scenario_scores[scenario] = score

        # 返回得分最高的场景
        if scenario_scores:
            best_scenario = max(scenario_scores, key=scenario_scores.get)
            if scenario_scores[best_scenario] > 0:
                return best_scenario

        # 如果没有匹配到具体场景，返回通用业务报告场景
        return ExtractionScenario.BUSINESS_REPORT.value

    def _calculate_confidence(
        self,
        user_input: str,
        extraction_intent: str,
        recommended_scenario: str
    ) -> float:
        """计算置信度分数"""
        confidence = 0.0

        # 基础置信度
        confidence += 0.3

        # 意图明确性加分
        if extraction_intent != ExtractionIntent.STRUCTURED_EXTRACTION.value:
            confidence += 0.2

        # 场景匹配度加分
        if recommended_scenario != ExtractionScenario.BUSINESS_REPORT.value:
            confidence += 0.2

        # 输入长度和复杂度加分
        if len(user_input) > 50:
            confidence += 0.1

        # 包含特定关键词加分
        extraction_keywords = ['提取', '分析', '识别', '解析', '处理']
        if any(keyword in user_input for keyword in extraction_keywords):
            confidence += 0.1

        # 历史学习加分
        if self._has_similar_requests(user_input):
            confidence += 0.1

        return min(confidence, 1.0)

    def _assess_complexity(self, user_input: str, extraction_intent: str) -> str:
        """评估处理复杂度"""
        text_length = len(user_input)

        if text_length < 100:
            return 'low'
        elif text_length < 500:
            return 'medium'
        elif text_length < 2000:
            return 'high'
        else:
            return 'very_high'

    def _estimate_processing_time(self, user_input: str, complexity: str) -> int:
        """估算处理时间（秒）"""
        base_time = 10

        complexity_multipliers = {
            'low': 1.0,
            'medium': 1.5,
            'high': 2.0,
            'very_high': 3.0
        }

        estimated_time = base_time * complexity_multipliers.get(complexity, 1.0)
        return int(estimated_time)

    def _assess_risk(self, user_input: str, context: dict[str, Any] = None) -> str:
        """评估风险等级"""
        # 敏感信息检测
        sensitive_patterns = [
            r"身份证号', r'手机号', r'银行账号', r'密码', r'私密",
            r"机密', r'绝密', r'内部', r'保密"
        ]

        for pattern in sensitive_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return 'high'

        # 上下文风险评估
        if context:
            if context.get('sensitive_content', False):
                return 'high'
            if context.get('high_stakes', False):
                return 'medium'

        return 'low'

    def _generate_prompt_suggestions(
        self,
        extraction_intent: str,
        recommended_scenario: str,
        user_input: str
    ) -> list[str]:
        """生成提示建议"""
        suggestions = []

        # 基于场景的提示建议
        scenario_prompts = {
            ExtractionScenario.PATENT_ANALYSIS.value: [
                '提取技术特征和创新点',
                '分析权利要求保护范围',
                '识别实施方式和技术效果'
            ],
            ExtractionScenario.CONTRACT_REVIEW.value: [
                '提取关键条款和条件',
                '识别当事人权利义务',
                '分析违约责任和风险'
            ],
            ExtractionScenario.MEDICAL_REPORT.value: [
                '提取诊断信息和检查结果',
                '识别治疗方案和用药信息',
                '分析症状和体征'
            ]
        }

        if recommended_scenario in scenario_prompts:
            suggestions.extend(scenario_prompts[recommended_scenario])

        # 基于意图的提示建议
        intent_prompts = {
            ExtractionIntent.ENTITY_RECOGNITION.value: [
                '识别文中提到的所有实体名称',
                '标注关键人物、地点、时间',
                '提取专业术语和概念'
            ],
            ExtractionIntent.RELATION_EXTRACTION.value: [
                '分析实体之间的关系',
                '识别因果关系和依赖关系',
                '提取交互和关联信息'
            ],
            ExtractionIntent.SENTIMENT_ANALYSIS.value: [
                '分析文本的情感倾向',
                '识别观点和态度',
                '评估正面负面情绪'
            ]
        }

        if extraction_intent in intent_prompts:
            suggestions.extend(intent_prompts[extraction_intent])

        return suggestions[:5]  # 最多返回5个建议

    def _estimate_data_volume(self, user_input: str) -> dict[str, Any]:
        """估算数据量"""
        text_length = len(user_input)

        estimated_records = min(max(text_length // 100, 1), 50)
        data_size_kb = text_length // 1024 + 1

        return {
            'estimated_records': estimated_records,
            'data_size_kb': data_size_kb,
            'processing_complexity': 'medium' if data_size_kb < 10 else 'high'
        }

    def _has_similar_requests(self, user_input: str) -> bool:
        """检查是否有相似的历史请求"""
        # 简单的关键词匹配
        user_keywords = set(user_input.lower().split())

        for history_item in self.extraction_history[-10:]:  # 只检查最近10条
            history_input = history_item['user_input'].lower()
            history_keywords = set(history_input.split())

            # 计算关键词重叠度
            overlap = len(user_keywords & history_keywords)
            if overlap > 2:  # 如果有超过2个相同关键词
                return True

        return False

    async def smart_extraction_execution(
        self,
        user_input: str,
        context: dict[str, Any] = None,
        text_or_documents: str = None
    ) -> dict[str, Any]:
        """智能提取执行"""
        try:
            logger.info(f"开始智能提取执行: {user_input[:50]}...")

            # 1. 分析用户请求
            analysis = await self.analyze_request(user_input, context)

            # 2. 决策是否执行
            if not analysis.should_extract:
                return {
                    'success': False,
                    'reason': 'confidence_too_low',
                    'message': '请求置信度不足，建议提供更具体的提取要求',
                    'analysis': analysis.__dict__
                }

            # 3. 准备待提取的文本
            if text_or_documents is None:
                # 如果没有提供文本，需要用户提供
                return {
                    'success': False,
                    'reason': 'missing_text',
                    'message': '请提供需要提取的文本或文档',
                    'analysis': analysis.__dict__,
                    'suggested_prompts': analysis.suggested_prompts
                }

            # 4. 执行提取
            if analysis.recommended_scenario in [s.value for s in ExtractionScenario]:
                # 使用预定义场景
                result = await self.langextract_tool.execute_scenario(
                    scenario=analysis.recommended_scenario,
                    text_or_documents=text_or_documents,
                    config={
                        'intent': analysis.extraction_intent,
                        'complexity': analysis.estimated_complexity
                    }
                )
            else:
                # 使用自定义提取
                result = await self.langextract_tool.execute_custom_extraction(
                    text_or_documents=text_or_documents,
                    prompt_description=user_input,
                    model_id='gemini-2.5-flash'
                )

            # 5. 构建返回结果
            execution_result = {
                'success': result.success,
                'task_id': result.task_id,
                'execution_time': result.execution_time,
                'analysis': analysis.__dict__,
                'result': {
                    'extractions_count': len(result.extractions),
                    'extractions': result.extractions,
                    'stats': result.stats,
                    'data': result.data
                }
            }

            if not result.success:
                execution_result['error'] = result.error
                execution_result['message'] = f"提取执行失败: {result.error}"
            else:
                execution_result['message'] = f"成功提取 {len(result.extractions)} 个实体"

            logger.info(f"智能提取执行完成: {result.success}, 提取数量: {len(result.extractions)}")

            return execution_result

        except Exception as e:
            logger.error(f"智能提取执行失败: {e}")
            return {
                'success': False,
                'reason': 'execution_error',
                'message': f"执行过程中出现错误: {str(e)}",
                'error': str(e)
            }

    async def learn_from_feedback(self, task_id: str, feedback: dict[str, Any]) -> bool:
        """从反馈中学习"""
        try:
            # 记录反馈信息
            {
                'task_id': task_id,
                'timestamp': datetime.now().isoformat(),
                'feedback': feedback
            }

            # 更新学习模型
            if 'accuracy_rating' in feedback:
                accuracy = feedback['accuracy_rating']
                # 这里可以实现更复杂的学习逻辑
                if accuracy > 0.8:
                    logger.info(f"任务 {task_id} 获得高评价: {accuracy}")
                else:
                    logger.info(f"任务 {task_id} 需要改进: {accuracy}")

            # 更新场景和意图的权重
            self._update_weights_from_feedback(feedback)

            logger.info(f"反馈学习完成: {task_id}")
            return True

        except Exception as e:
            logger.error(f"反馈学习失败: {e}")
            return False

    def _update_weights_from_feedback(self, feedback: dict[str, Any]) -> Any:
        """根据反馈更新权重"""
        # 简化的权重更新逻辑
        # 在实际应用中，这里可以实现更复杂的机器学习算法
        pass

    async def get_extraction_statistics(self) -> dict[str, Any]:
        """获取提取统计信息"""
        if not self.extraction_history:
            return {
                'total_requests': 0,
                'successful_extractions': 0,
                'average_confidence': 0.0,
                'popular_scenarios': [],
                'recent_activity': []
            }

        total_requests = len(self.extraction_history)
        successful_extractions = sum(
            1 for h in self.extraction_history
            if h['analysis'].get('should_extract', False)
        )

        average_confidence = sum(
            h['analysis'].get('confidence_score', 0.0)
            for h in self.extraction_history
        ) / total_requests

        # 统计热门场景
        scenario_counts = {}
        for h in self.extraction_history:
            scenario = h['analysis'].get('recommended_scenario', 'unknown')
            scenario_counts[scenario] = scenario_counts.get(scenario, 0) + 1

        popular_scenarios = sorted(
            scenario_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        # 最近活动
        recent_activity = self.extraction_history[-10:]

        return {
            'total_requests': total_requests,
            'successful_extractions': successful_extractions,
            'success_rate': successful_extractions / total_requests,
            'average_confidence': average_confidence,
            'popular_scenarios': popular_scenarios,
            'recent_activity': recent_activity
        }


# 全局实例
_xiaonuo_langextract_controller = None

def get_xiaonuo_langextract_controller() -> XiaoNuoLangExtractController:
    """获取小诺LangExtract控制器实例"""
    global _xiaonuo_langextract_controller
    if _xiaonuo_langextract_controller is None:
        _xiaonuo_langextract_controller = XiaoNuoLangExtractController()
    return _xiaonuo_langextract_controller
