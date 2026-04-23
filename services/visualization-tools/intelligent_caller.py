"""
智能可视化工具调用系统
Athena和小诺协作决策最佳可视化工具
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from langchain.tools import BaseTool
from langchain_tools import visualization_tool_manager
from visualization_insights import VisualizationAnalyzer

logger = logging.getLogger(__name__)

class CallStrategy(Enum):
    """调用策略"""
    SINGLE_TOOL = 'single_tool'          # 单一工具
    COLLABORATIVE = 'collaborative'       # 协作调用
    SEQUENTIAL = 'sequential'             # 顺序调用
    PARALLEL = 'parallel'                # 并行调用

@dataclass
class ScenarioContext:
    """场景上下文"""
    user_request: str
    intent: str                           # 用户意图
    data_type: str | None             # 数据类型
    audience: str | None              # 目标受众
    urgency: str                         # 紧急程度
    collaboration_needed: bool           # 是否需要协作
    aesthetic_preference: str            # 美学偏好

@dataclass
class ToolSelection:
    """工具选择结果"""
    primary_tool: BaseTool
    secondary_tools: list[BaseTool] = None
    strategy: CallStrategy = CallStrategy.SINGLE_TOOL
    confidence: float = 0.0
    reasoning: str = ''

class IntelligentVisualizationCaller:
    """智能可视化调用系统"""

    def __init__(self):
        self.tool_manager = visualization_tool_manager
        self.analyzer = VisualizationAnalyzer()
        self.call_history = []

        # 场景模式定义
        self.scenario_patterns = self._initialize_scenario_patterns()

        # 协作决策权重
        self.decision_weights = {
            'athena': {
                'technical_complexity': 0.4,
                'data_analysis': 0.3,
                'system_integration': 0.3
            },
            'xiaonuo': {
                'user_experience': 0.4,
                'aesthetic_quality': 0.3,
                'collaboration': 0.3
            }
        }

    def _initialize_scenario_patterns(self) -> dict[str, dict[str, Any]:
        """初始化场景模式"""
        return {
            'data_analysis': {
                'keywords': ['data', '数据', 'analysis', '分析', 'chart', '图表', 'dashboard', '仪表板'],
                'preferred_tool': 'echarts',
                'fallback_tool': 'drawio',
                'confidence_boost': 0.2
            },
            'system_design': {
                'keywords': ['architecture', '架构', 'system', '系统', 'design', '设计', 'flow', '流程'],
                'preferred_tool': 'drawio',
                'fallback_tool': 'excalidraw',
                'confidence_boost': 0.2
            },
            'creative_sketch': {
                'keywords': ['sketch', '草图', 'mockup', '原型', 'design', '设计', 'creative', '创意'],
                'preferred_tool': 'excalidraw',
                'fallback_tool': 'drawio',
                'confidence_boost': 0.2
            },
            'collaborative_work': {
                'keywords': ['collaborate', '协作', 'team', '团队', 'meeting', '会议', 'brainstorm', '头脑风暴'],
                'preferred_tool': 'excalidraw',
                'fallback_tool': 'drawio',
                'confidence_boost': 0.15
            }
        }

    async def analyze_request(self, user_request: str) -> ScenarioContext:
        """分析用户请求"""
        try:
            # 基础意图识别
            intent = self._identify_intent(user_request)

            # 数据类型检测
            data_type = self._detect_data_type(user_request)

            # 受众分析
            audience = self._analyze_audience(user_request)

            # 紧急程度评估
            urgency = self._assess_urgency(user_request)

            # 协作需求判断
            collaboration_needed = self._needs_collaboration(user_request)

            # 美学偏好识别
            aesthetic_preference = self._identify_aesthetic_preference(user_request)

            return ScenarioContext(
                user_request=user_request,
                intent=intent,
                data_type=data_type,
                audience=audience,
                urgency=urgency,
                collaboration_needed=collaboration_needed,
                aesthetic_preference=aesthetic_preference
            )

        except Exception as e:
            logger.error(f"请求分析失败: {e}")
            return ScenarioContext(
                user_request=user_request,
                intent='general',
                data_type='unknown',
                audience='internal',
                urgency='normal',
                collaboration_needed=False,
                aesthetic_preference='professional'
            )

    def _identify_intent(self, request: str) -> str:
        """识别用户意图"""
        request_lower = request.lower()

        # 意图映射
        intent_patterns = {
            'visualization': ['visualize', 'chart', 'graph', '图表', '可视化', '展示'],
            'documentation': ['document', 'diagram', '文档', '图解', '说明'],
            'design': ['design', 'mockup', '原型', '设计', '界面'],
            'analysis': ['analyze', 'analysis', '分析', '数据'],
            'collaboration': ['collaborate', 'team', '协作', '团队', '讨论']
        }

        for intent, keywords in intent_patterns.items():
            if any(keyword in request_lower for keyword in keywords):
                return intent

        return 'general'

    def _detect_data_type(self, request: str) -> str:
        """检测数据类型"""
        request_lower = request.lower()

        data_types = {
            'numerical': ['number', 'count', 'amount', '数字', '数量', '统计'],
            'categorical': ['category', 'type', '分类', '类型'],
            'time_series': ['time', 'date', 'trend', '时间', '日期', '趋势'],
            'geographical': ['map', 'location', '地理', '位置', '地图'],
            'hierarchical': ['tree', 'hierarchy', '层级', '结构', '组织']
        }

        for data_type, keywords in data_types.items():
            if any(keyword in request_lower for keyword in keywords):
                return data_type

        return 'mixed'

    def _analyze_audience(self, request: str) -> str:
        """分析目标受众"""
        request_lower = request.lower()

        audience_patterns = {
            'technical': ['developer', 'engineer', '技术', '开发', '工程'],
            'business': ['business', 'manager', 'stakeholder', '业务', '管理', '决策者'],
            'end_user': ['user', 'customer', '用户', '客户'],
            'executive': ['executive', 'leadership', '高管', '领导']
        }

        for audience, keywords in audience_patterns.items():
            if any(keyword in request_lower for keyword in keywords):
                return audience

        return 'general'

    def _assess_urgency(self, request: str) -> str:
        """评估紧急程度"""
        request_lower = request.lower()

        urgency_indicators = {
            'urgent': ['urgent', 'asap', 'immediate', '紧急', '立即', '马上'],
            'normal': ['normal', 'standard', '正常', '标准'],
            'low': ['low', 'flexible', '从容', '灵活']
        }

        for urgency, keywords in urgency_indicators.items():
            if any(keyword in request_lower for keyword in keywords):
                return urgency

        return 'normal'

    def _needs_collaboration(self, request: str) -> bool:
        """判断是否需要协作"""
        collaboration_keywords = [
            'collaborate', 'team', 'together', '协作', '团队', '一起',
            'brainstorm', 'discuss', 'meeting', '讨论', '会议', '头脑风暴'
        ]

        request_lower = request.lower()
        return any(keyword in request_lower for keyword in collaboration_keywords)

    def _identify_aesthetic_preference(self, request: str) -> str:
        """识别美学偏好"""
        request_lower = request.lower()

        aesthetic_patterns = {
            'professional': ['professional', 'formal', '专业', '正式'],
            'casual': ['casual', 'informal', '休闲', '非正式'],
            'creative': ['creative', 'artistic', '创意', '艺术'],
            'modern': ['modern', 'clean', '现代', '简洁'],
            'hand_drawn': ['sketch', 'hand', '手绘', '草图']
        }

        for preference, keywords in aesthetic_patterns.items():
            if any(keyword in request_lower for keyword in keywords):
                return preference

        return 'professional'

    async def select_optimal_tools(self, context: ScenarioContext) -> ToolSelection:
        """选择最优工具组合"""
        try:
            # 基于场景模式推荐
            primary_recommendation = self._recommend_by_scenario(context)

            # 基于上下文细化选择
            refined_selection = self._refine_selection(context, primary_recommendation)

            # 确定调用策略
            self._determine_strategy(context, refined_selection)

            return refined_selection

        except Exception as e:
            logger.error(f"工具选择失败: {e}")
            # 降级处理：返回默认工具
            return ToolSelection(
                primary_tool=self.tool_manager.tools[0],
                strategy=CallStrategy.SINGLE_TOOL,
                confidence=0.5,
                reasoning='系统错误，使用默认工具'
            )

    def _recommend_by_scenario(self, context: ScenarioContext) -> str:
        """基于场景推荐工具"""
        request_lower = context.user_request.lower()

        best_match = 'drawio'  # 默认推荐
        best_score = 0

        for _scenario, pattern in self.scenario_patterns.items():
            score = 0
            for keyword in pattern['keywords']:
                if keyword in request_lower:
                    score += 1

            if score > best_score:
                best_score = score
                best_match = pattern['preferred_tool']

        return best_match

    def _refine_selection(self, context: ScenarioContext, primary_tool_name: str) -> ToolSelection:
        """细化工具选择"""
        # 获取推荐的主要工具
        primary_tool = self.tool_manager.get_tool_by_name(primary_tool_name)

        if not primary_tool:
            primary_tool = self.tool_manager.tools[0]  # 降级

        confidence = 0.7  # 基础置信度

        # 基于上下文调整置信度
        if context.intent == 'data_analysis' and 'echarts' in primary_tool.name:
            confidence += 0.2
        elif context.intent == 'system_design' and 'drawio' in primary_tool.name:
            confidence += 0.2
        elif context.aesthetic_preference == 'hand_drawn' and 'excalidraw' in primary_tool.name:
            confidence += 0.2

        # 确定是否需要辅助工具
        secondary_tools = []
        if context.collaboration_needed:
            # 协作场景可以考虑使用Excalidraw作为辅助工具
            excalidraw = self.tool_manager.get_tool_by_name('excalidraw')
            if excalidraw and excalidraw != primary_tool:
                secondary_tools.append(excalidraw)

        reasoning = self._generate_reasoning(context, primary_tool, secondary_tools)

        return ToolSelection(
            primary_tool=primary_tool,
            secondary_tools=secondary_tools,
            strategy=CallStrategy.COLLABORATIVE if secondary_tools else CallStrategy.SINGLE_TOOL,
            confidence=min(1.0, confidence),
            reasoning=reasoning
        )

    def _determine_strategy(self, context: ScenarioContext, selection: ToolSelection) -> CallStrategy:
        """确定调用策略"""
        if context.collaboration_needed and selection.secondary_tools:
            return CallStrategy.COLLABORATIVE
        elif context.data_type == 'mixed' and context.intent == 'data_analysis':
            return CallStrategy.SEQUENTIAL
        elif context.urgency == 'urgent':
            return CallStrategy.SINGLE_TOOL
        else:
            return selection.strategy

    def _generate_reasoning(self, context: ScenarioContext, primary_tool: BaseTool, secondary_tools: list[BaseTool]) -> str:
        """生成选择推理"""
        reasoning_parts = [
            f"基于用户意图 '{context.intent}' 选择 {primary_tool.name}",
            f"目标受众为 '{context.audience}'，偏好 '{context.aesthetic_preference}' 风格"
        ]

        if secondary_tools:
            reasoning_parts.append(f"由于需要协作，额外选择了 {[tool.name for tool in secondary_tools]}")

        if context.data_type != 'unknown':
            reasoning_parts.append(f"数据类型 '{context.data_type}' 影响了工具选择")

        return '; '.join(reasoning_parts)

    async def execute_with_strategy(self, selection: ToolSelection, query: str) -> dict[str, Any]:
        """根据策略执行工具调用"""
        try:
            execution_start = datetime.now()

            if selection.strategy == CallStrategy.SINGLE_TOOL:
                result = await self._execute_single_tool(selection.primary_tool, query)
            elif selection.strategy == CallStrategy.COLLABORATIVE:
                result = await self._execute_collaborative(selection.primary_tool, selection.secondary_tools, query)
            elif selection.strategy == CallStrategy.SEQUENTIAL:
                result = await self._execute_sequential(selection.primary_tool, selection.secondary_tools, query)
            else:
                result = await self._execute_single_tool(selection.primary_tool, query)

            execution_time = datetime.now() - execution_start

            return {
                'success': True,
                'strategy': selection.strategy.value,
                'primary_tool': selection.primary_tool.name,
                'secondary_tools': [tool.name for tool in selection.secondary_tools] if selection.secondary_tools else [],
                'execution_time': str(execution_time),
                'result': result,
                'confidence': selection.confidence,
                'reasoning': selection.reasoning
            }

        except Exception as e:
            logger.error(f"工具执行失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'strategy': selection.strategy.value if selection else 'unknown'
            }

    async def _execute_single_tool(self, tool: BaseTool, query: str) -> str:
        """执行单一工具"""
        try:
            if hasattr(tool, '_arun'):
                return await tool._arun(query)
            else:
                return tool._run(query)
        except Exception as e:
            logger.error(f"工具 {tool.name} 执行失败: {e}")
            raise

    async def _execute_collaborative(self, primary_tool: BaseTool, secondary_tools: list[BaseTool], query: str) -> dict[str, Any]:
        """执行协作调用"""
        # 并行执行所有工具
        tasks = [self._execute_single_tool(primary_tool, query)]
        for tool in secondary_tools:
            tasks.append(self._execute_single_tool(tool, f"协作视角: {query}"))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            'primary_result': results[0] if not isinstance(results[0], Exception) else str(results[0]),
            'secondary_results': [
                result if not isinstance(result, Exception) else str(result)
                for result in results[1:]
            ]
        }

    async def _execute_sequential(self, primary_tool: BaseTool, secondary_tools: list[BaseTool], query: str) -> dict[str, Any]:
        """执行顺序调用"""
        results = []

        # 先执行主要工具
        try:
            primary_result = await self._execute_single_tool(primary_tool, query)
            results.append(primary_result)
        except Exception as e:
            logger.error(f"主要工具执行失败: {e}")
            results.append(str(e))

        # 依次执行辅助工具
        for _i, tool in enumerate(secondary_tools):
            try:
                # 基于前面结果调整查询
                enhanced_query = f"基于前序结果优化: {query}"
                result = await self._execute_single_tool(tool, enhanced_query)
                results.append(result)
            except Exception as e:
                logger.error(f"辅助工具 {tool.name} 执行失败: {e}")
                results.append(str(e))

        return {
            'sequential_results': results
        }

    async def learn_from_execution(self, execution_result: dict[str, Any], user_feedback: dict[str, Any] | None = None):
        """从执行结果中学习"""
        try:
            # 记录执行历史
            self.call_history.append({
                'timestamp': datetime.now().isoformat(),
                'result': execution_result,
                'feedback': user_feedback
            })

            # 基于反馈调整权重（简化实现）
            if user_feedback:
                if user_feedback.get('satisfaction', 0) > 0.8:
                    # 满意度高，增强该策略的权重
                    pass
                else:
                    # 满意度低，降低权重
                    pass

        except Exception as e:
            logger.error(f"学习过程失败: {e}")

    def get_performance_summary(self) -> dict[str, Any]:
        """获取性能摘要"""
        if not self.call_history:
            return {'message': '暂无执行历史'}

        total_calls = len(self.call_history)
        successful_calls = sum(1 for call in self.call_history if call['result'].get('success', False))

        strategy_usage = {}
        for call in self.call_history:
            strategy = call['result'].get('strategy', 'unknown')
            strategy_usage[strategy] = strategy_usage.get(strategy, 0) + 1

        return {
            'total_executions': total_calls,
            'success_rate': successful_calls / total_calls if total_calls > 0 else 0,
            'strategy_usage': strategy_usage,
            'most_used_strategy': max(strategy_usage.items(), key=lambda x: x[1])[0] if strategy_usage else 'none'
        }

# 全局智能调用器实例
intelligent_caller = IntelligentVisualizationCaller()
