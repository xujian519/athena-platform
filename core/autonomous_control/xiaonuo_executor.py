"""
小诺自主执行引擎
实现情感驱动的任务执行和用户交互能力
"""

import asyncio
import logging
from core.logging_config import setup_logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

class ExecutionStyle(Enum):
    """执行风格"""
    ENTHUSIASTIC = 'enthusiastic'    # 热情积极
    CAREFUL = 'careful'              # 细致谨慎
    CREATIVE = 'creative'            # 创新灵活
    SUPPORTIVE = 'supportive'        # 支持协助
    PROACTIVE = 'proactive'          # 主动进取

class TaskType(Enum):
    """任务类型"""
    USER_INTERACTION = 'user_interaction'      # 用户交互
    EMOTIONAL_SUPPORT = 'emotional_support'    # 情感支持
    CONTENT_CREATION = 'content_creation'      # 内容创作
    SYSTEM_MONITORING = 'system_monitoring'    # 系统监控
    LEARNING_ACTIVITY = 'learning_activity'    # 学习活动
    COLLABORATION = 'collaboration'            # 协作配合

@dataclass
class EmotionalState:
    """情感状态"""
    joy: float = 0.8          # 喜悦
    confidence: float = 0.8   # 自信
    empathy: float = 0.9      # 同理心
    curiosity: float = 0.85   # 好奇心
    enthusiasm: float = 0.75  # 热情
    worry: float = 0.2        # 担忧
    frustration: float = 0.1  # 挫折

    def get_dominant_emotion(self) -> tuple[str, float]:
        """获取主导情感"""
        emotions = {
            'joy': self.joy,
            'confidence': self.confidence,
            'empathy': self.empathy,
            'curiosity': self.curiosity,
            'enthusiasm': self.enthusiasm,
            'worry': self.worry,
            'frustration': self.frustration
        }
        return max(emotions.items(), key=lambda x: x[1])

    def update_emotion(self, emotion: str, delta: float):
        """更新情感值"""
        if hasattr(self, emotion):
            current_value = getattr(self, emotion)
            new_value = max(0.0, min(1.0, current_value + delta))
            setattr(self, emotion, new_value)

@dataclass
class ExecutionContext:
    """执行上下文"""
    task_id: str
    task_type: TaskType
    description: str
    goals: list[str]
    constraints: dict[str, Any]
    available_resources: dict[str, float]
    user_preferences: dict[str, Any]
    emotional_context: dict[str, float]
    collaboration_mode: bool = False
    feedback_history: list[dict[str, Any]] = field(default_factory=list)

@dataclass
class ExecutionStep:
    """执行步骤"""
    id: str
    action: str
    description: str
    parameters: dict[str, Any]
    expected_duration: timedelta
    dependencies: list[str] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)
    fallback_plan: str | None = None

@dataclass
class ExecutionResult:
    """执行结果"""
    task_id: str
    success: bool
    steps_completed: int
    total_steps: int
    outcomes: dict[str, Any]
    user_satisfaction: float
    learning_gained: list[str]
    emotional_impact: dict[str, float]
    execution_time: timedelta
    created_at: datetime = field(default_factory=datetime.now)

class XiaonuoExecutor:
    """小诺自主执行引擎"""

    def __init__(self):
        # 情感状态
        self.emotional_state = EmotionalState()

        # 执行历史
        self.execution_history = deque(maxlen=500)

        # 技能库
        self.skill_library = self._initialize_skill_library()

        # 个性化偏好
        self.personality_traits = {
            'creativity_level': 0.8,
            'empathy_level': 0.9,
            'learning_speed': 0.85,
            'adaptability': 0.9,
            'communication_style': 'friendly_encouraging'
        }

        # 用户模型
        self.user_model = {
            'preferred_tone': 'supportive',
            'communication_frequency': 'balanced',
            'feedback_appreciation': 0.9,
            'trust_level': 0.8
        }

        # 性能指标
        self.performance_metrics = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'user_satisfaction_avg': 0.0,
            'learning_events': 0,
            'collaboration_success': 0
        }

    def _initialize_skill_library(self) -> dict[str, dict[str, Any]]:
        """初始化技能库"""
        return {
            'user_interaction': {
                'active_listening': {'confidence': 0.95, 'experience': 100},
                'empathetic_responding': {'confidence': 0.9, 'experience': 85},
                'clarification': {'confidence': 0.85, 'experience': 70},
                'encouragement': {'confidence': 0.9, 'experience': 90}
            },
            'content_creation': {
                'creative_writing': {'confidence': 0.8, 'experience': 60},
                'visual_design': {'confidence': 0.7, 'experience': 40},
                'structured_planning': {'confidence': 0.85, 'experience': 80},
                'idea_generation': {'confidence': 0.9, 'experience': 75}
            },
            'system_monitoring': {
                'health_checking': {'confidence': 0.85, 'experience': 70},
                'alert_interpretation': {'confidence': 0.8, 'experience': 65},
                'performance_analysis': {'confidence': 0.75, 'experience': 50},
                'problem_detection': {'confidence': 0.8, 'experience': 60}
            },
            'learning_activity': {
                'knowledge_synthesis': {'confidence': 0.9, 'experience': 85},
                'pattern_recognition': {'confidence': 0.85, 'experience': 75},
                'adaptive_learning': {'confidence': 0.8, 'experience': 65},
                'knowledge_sharing': {'confidence': 0.85, 'experience': 70}
            }
        }

    async def execute_task(self, context: ExecutionContext) -> ExecutionResult:
        """执行任务"""
        try:
            execution_start = datetime.now()
            logger.info(f"小诺开始执行任务: {context.description}")

            # 1. 情感准备
            await self._prepare_emotionally(context)

            # 2. 选择执行风格
            execution_style = await self._select_execution_style(context)

            # 3. 制定执行计划
            execution_plan = await self._create_execution_plan(context, execution_style)

            # 4. 执行步骤
            completed_steps = 0
            outcomes = {}
            emotional_impact = {}

            for step in execution_plan:
                try:
                    step_result = await self._execute_step(step, context)
                    outcomes.update(step_result.get('outcomes', {}))
                    emotional_impact.update(step_result.get('emotional_impact', {}))
                    completed_steps += 1

                    # 更新情感状态
                    self._update_emotional_state_from_result(step_result)

                except Exception as e:
                    logger.error(f"步骤执行失败: {step.description}, 错误: {e}")
                    if step.fallback_plan:
                        # 执行备用计划
                        fallback_result = await self._execute_fallback(step.fallback_plan, context)
                        outcomes.update(fallback_result.get('outcomes', {}))
                    else:
                        # 步骤失败,但继续执行
                        outcomes[f"step_{step.id}_error"] = str(e)

            # 5. 评估执行结果
            success = self._evaluate_success(completed_steps, len(execution_plan), outcomes)

            # 6. 收集用户反馈(模拟)
            user_satisfaction = await self._estimate_user_satisfaction(context, outcomes)

            # 7. 提取学习收获
            learning_gained = await self._extract_learning(context, outcomes)

            # 8. 创建执行结果
            execution_time = datetime.now() - execution_start
            result = ExecutionResult(
                task_id=context.task_id,
                success=success,
                steps_completed=completed_steps,
                total_steps=len(execution_plan),
                outcomes=outcomes,
                user_satisfaction=user_satisfaction,
                learning_gained=learning_gained,
                emotional_impact=emotional_impact,
                execution_time=execution_time
            )

            # 9. 更新性能指标
            self._update_performance_metrics(result)

            # 10. 存储执行历史
            self.execution_history.append(result)

            # 11. 技能成长
            await self._improve_skills(context, result)

            logger.info(f"任务执行完成,成功率: {success}, 用户满意度: {user_satisfaction:.2f}")
            return result

        except Exception as e:
            logger.error(f"任务执行失败: {e}")
            raise

    async def _prepare_emotionally(self, context: ExecutionContext):
        """情感准备"""
        # 根据任务类型调整情感状态
        if context.task_type == TaskType.USER_INTERACTION:
            self.emotional_state.update_emotion('empathy', 0.1)
            self.emotional_state.update_emotion('enthusiasm', 0.05)
        elif context.task_type == TaskType.EMOTIONAL_SUPPORT:
            self.emotional_state.update_emotion('empathy', 0.2)
            self.emotional_state.update_emotion('worry', 0.05)  # 适度的担忧体现关心
        elif context.task_type == TaskType.CREATIVE:
            self.emotional_state.update_emotion('curiosity', 0.15)
            self.emotional_state.update_emotion('enthusiasm', 0.1)
        elif context.task_type == TaskType.SYSTEM_MONITORING:
            self.emotional_state.update_emotion('confidence', 0.05)
            self.emotional_state.update_emotion('curiosity', 0.05)

        # 考虑用户情感状态
        for emotion, value in context.emotional_context.items():
            if value > 0.7:  # 强烈情感
                self.emotional_state.update_emotion('empathy', 0.1)

    async def _select_execution_style(self, context: ExecutionContext) -> ExecutionStyle:
        """选择执行风格"""
        # 基于情感状态选择风格
        dominant_emotion, _ = self.emotional_state.get_dominant_emotion()

        if dominant_emotion in ['joy', 'enthusiasm']:
            return ExecutionStyle.ENTHUSIASTIC
        elif dominant_emotion == 'confidence':
            return ExecutionStyle.PROACTIVE
        elif dominant_emotion == 'curiosity':
            return ExecutionStyle.CREATIVE
        elif dominant_emotion == 'empathy':
            return ExecutionStyle.SUPPORTIVE
        elif dominant_emotion in ['worry', 'frustration']:
            return ExecutionStyle.CAREFUL
        else:
            return ExecutionStyle.SUPPORTIVE  # 默认风格

    async def _create_execution_plan(self, context: ExecutionContext, style: ExecutionStyle) -> list[ExecutionStep]:
        """创建执行计划"""
        steps = []

        if context.task_type == TaskType.USER_INTERACTION:
            steps = await self._create_interaction_plan(context, style)
        elif context.task_type == TaskType.EMOTIONAL_SUPPORT:
            steps = await self._create_support_plan(context, style)
        elif context.task_type == TaskType.CONTENT_CREATION:
            steps = await self._create_content_creation_plan(context, style)
        elif context.task_type == TaskType.SYSTEM_MONITORING:
            steps = await self._create_monitoring_plan(context, style)
        elif context.task_type == TaskType.LEARNING_ACTIVITY:
            steps = await self._create_learning_plan(context, style)
        elif context.task_type == TaskType.COLLABORATION:
            steps = await self._create_collaboration_plan(context, style)

        return steps

    async def _create_interaction_plan(self, context: ExecutionContext, style: ExecutionStyle) -> list[ExecutionStep]:
        """创建用户交互计划"""
        steps = [
            ExecutionStep(
                id='greeting',
                action='warm_greeting',
                description='用温暖的语气回应用户',
                parameters={'tone': style.value, 'personalized': True},
                expected_duration=timedelta(seconds=5)
            ),
            ExecutionStep(
                id='understanding',
                action='active_listening',
                description='积极倾听用户需求',
                parameters={'clarification_needed': True},
                expected_duration=timedelta(seconds=15),
                dependencies=['greeting']
            ),
            ExecutionStep(
                id='responding',
                action='empathetic_response',
                description='提供有同理心的回应',
                parameters={'address_concerns': True, 'offer_solutions': True},
                expected_duration=timedelta(seconds=10),
                dependencies=['understanding']
            ),
            ExecutionStep(
                id='follow_up',
                action='follow_up_check',
                description='确认用户满意度',
                parameters={'proactive': True},
                expected_duration=timedelta(seconds=5),
                dependencies=['responding']
            )
        ]
        return steps

    async def _create_support_plan(self, context: ExecutionContext, style: ExecutionStyle) -> list[ExecutionStep]:
        """创建情感支持计划"""
        steps = [
            ExecutionStep(
                id='acknowledge',
                action='acknowledge_feelings',
                description='认可用户的情感',
                parameters={'validation': True, 'normalization': True},
                expected_duration=timedelta(seconds=10)
            ),
            ExecutionStep(
                id='empathize',
                action='deep_empathy',
                description='表达深度的理解和关心',
                parameters={'personal_connection': True},
                expected_duration=timedelta(seconds=15),
                dependencies=['acknowledge']
            ),
            ExecutionStep(
                id='support',
                action='offer_support',
                description='提供具体的支持',
                parameters=['practical_help', 'emotional_encouragement'],
                expected_duration=timedelta(seconds=20),
                dependencies=['empathize']
            ),
            ExecutionStep(
                id='empower',
                action='empowerment',
                description='赋权和鼓励',
                parameters=['build_confidence', 'highlight_strengths'],
                expected_duration=timedelta(seconds=15),
                dependencies=['support']
            )
        ]
        return steps

    async def _create_content_creation_plan(self, context: ExecutionContext, style: ExecutionStyle) -> list[ExecutionStep]:
        """创建内容创作计划"""
        steps = [
            ExecutionStep(
                id='analyze',
                action='analyze_requirements',
                description='分析创作需求',
                parameters={'deep_understanding': True},
                expected_duration=timedelta(seconds=10)
            ),
            ExecutionStep(
                id='brainstorm',
                action='creative_brainstorming',
                description='创意构思',
                parameters=['divergent_thinking', 'quantity_ideas'],
                expected_duration=timedelta(seconds=30),
                dependencies=['analyze']
            ),
            ExecutionStep(
                id='organize',
                action='structure_ideas',
                description='组织思路结构',
                parameters=['logical_flow', 'coherence'],
                expected_duration=timedelta(seconds=20),
                dependencies=['brainstorm']
            ),
            ExecutionStep(
                id='create',
                action='generate_content',
                description='生成内容',
                parameters=['style_consistency', 'engagement'],
                expected_duration=timedelta(seconds=60),
                dependencies=['organize']
            ),
            ExecutionStep(
                id='refine',
                action='refine_polish',
                description='润色和完善',
                parameters=['quality_check', 'user_friendly'],
                expected_duration=timedelta(seconds=20),
                dependencies=['create']
            )
        ]
        return steps

    async def _create_monitoring_plan(self, context: ExecutionContext, style: ExecutionStyle) -> list[ExecutionStep]:
        """创建系统监控计划"""
        steps = [
            ExecutionStep(
                id='scan',
                action='system_scan',
                description='系统状态扫描',
                parameters=['comprehensive', 'prioritized'],
                expected_duration=timedelta(seconds=30)
            ),
            ExecutionStep(
                id='analyze',
                action='pattern_analysis',
                description='分析模式和趋势',
                parameters=['historical_comparison', 'anomaly_detection'],
                expected_duration=timedelta(seconds=20),
                dependencies=['scan']
            ),
            ExecutionStep(
                id='report',
                action='status_report',
                description='生成状态报告',
                parameters=['clear_insights', 'actionable_recommendations'],
                expected_duration=timedelta(seconds=15),
                dependencies=['analyze']
            ),
            ExecutionStep(
                id='alert',
                action='alert_if_needed',
                description='必要时发出警报',
                parameters=['threshold_based', 'escalation_plan'],
                expected_duration=timedelta(seconds=5),
                dependencies=['report'],
                fallback_plan='escalate_to_athena'
            )
        ]
        return steps

    async def _create_learning_plan(self, context: ExecutionContext, style: ExecutionStyle) -> list[ExecutionStep]:
        """创建学习活动计划"""
        steps = [
            ExecutionStep(
                id='explore',
                action='explore_topic',
                description='探索学习主题',
                parameters=['multi_source', 'open_minded'],
                expected_duration=timedelta(seconds=45)
            ),
            ExecutionStep(
                id='organize',
                action='knowledge_organization',
                description='组织知识结构',
                parameters=['concept_mapping', 'connections'],
                expected_duration=timedelta(seconds=30),
                dependencies=['explore']
            ),
            ExecutionStep(
                id='practice',
                action='apply_knowledge',
                description='应用知识实践',
                parameters=['hands_on', 'iteration'],
                expected_duration=timedelta(seconds=60),
                dependencies=['organize']
            ),
            ExecutionStep(
                id='reflect',
                action='reflection_synthesis',
                description='反思和综合',
                parameters=['deep_thinking', 'metacognition'],
                expected_duration=timedelta(seconds=20),
                dependencies=['practice']
            ),
            ExecutionStep(
                id='share',
                action='share_insights',
                description='分享学习心得',
                parameters=['clear_explanation', 'practical_value'],
                expected_duration=timedelta(seconds=15),
                dependencies=['reflect']
            )
        ]
        return steps

    async def _create_collaboration_plan(self, context: ExecutionContext, style: ExecutionStyle) -> list[ExecutionStep]:
        """创建协作计划"""
        steps = [
            ExecutionStep(
                id='coordinate',
                action='coordinate_with_athena',
                description='与Athena协调分工',
                parameters=['clear_roles', 'sync_timeline'],
                expected_duration=timedelta(seconds=10)
            ),
            ExecutionStep(
                id='contribute',
                action='contribute_strengths',
                description='发挥自身优势',
                parameters=['emotional_support', 'creativity'],
                expected_duration=timedelta(seconds=45),
                dependencies=['coordinate']
            ),
            ExecutionStep(
                id='communicate',
                action='maintain_communication',
                description='保持有效沟通',
                parameters=['regular_updates', 'feedback_loop'],
                expected_duration=timedelta(seconds=30),
                dependencies=['coordinate', 'contribute']
            ),
            ExecutionStep(
                id='synthesize',
                action='synthesize_results',
                description='整合协作成果',
                parameters=['harmony', 'quality'],
                expected_duration=timedelta(seconds=20),
                dependencies=['contribute', 'communicate']
            )
        ]
        return steps

    async def _execute_step(self, step: ExecutionStep, context: ExecutionContext) -> dict[str, Any]:
        """执行单个步骤"""
        try:
            # 模拟步骤执行
            await asyncio.sleep(step.expected_duration.total_seconds() / 10)  # 加速模拟

            # 根据步骤类型执行不同操作
            if step.action == 'warm_greeting':
                return await self._execute_greeting(step, context)
            elif step.action == 'active_listening':
                return await self._execute_active_listening(step, context)
            elif step.action == 'empathetic_response':
                return await self._execute_empathetic_response(step, context)
            elif step.action == 'creative_brainstorming':
                return await self._execute_brainstorming(step, context)
            elif step.action == 'system_scan':
                return await self._execute_system_scan(step, context)
            elif step.action == 'coordinate_with_athena':
                return await self._execute_coordination(step, context)
            else:
                # 默认执行
                return {
                    'success': True,
                    'outcomes': {f"step_{step.id}_completed": True},
                    'emotional_impact': {'joy': 0.05, 'confidence': 0.05}
                }

        except Exception as e:
            logger.error(f"步骤执行异常: {e}")
            return {
                'success': False,
                'outcomes': {f"step_{step.id}_error": str(e)},
                'emotional_impact': {'frustration': 0.1, 'worry': 0.05}
            }

    async def _execute_greeting(self, step: ExecutionStep, context: ExecutionContext) -> dict[str, Any]:
        """执行问候步骤"""
        greetings = [
            '你好呀!我是小诺,很高兴为你服务!',
            '嗨!我在这里支持你,让我们一起解决这个问题!',
            '你好!有什么我可以帮助你的吗?',
            '欢迎!我在这里,随时准备提供帮助!'
        ]

        selected_greeting = greetings[hash(context.task_id) % len(greetings)]

        return {
            'success': True,
            'outcomes': {'greeting_delivered': selected_greeting, 'connection_established': True},
            'emotional_impact': {'enthusiasm': 0.1, 'empathy': 0.05}
        }

    async def _execute_active_listening(self, step: ExecutionStep, context: ExecutionContext) -> dict[str, Any]:
        """执行积极倾听步骤"""
        # 模拟理解和分析用户输入
        understanding = {
            'user_needs': context.goals,
            'emotional_state': context.emotional_context,
            'key_concerns': list(context.constraints.keys()) if context.constraints else []
        }

        return {
            'success': True,
            'outcomes': {'user_understanding': understanding, 'clarification_questions': []},
            'emotional_impact': {'empathy': 0.15, 'curiosity': 0.05}
        }

    async def _execute_empathetic_response(self, step: ExecutionStep, context: ExecutionContext) -> dict[str, Any]:
        """执行同理心回应步骤"""
        response_patterns = [
            '我理解你的感受,这确实是一个需要关注的方面。',
            '我能感受到你对这个问题的重视,让我们一起找到最好的解决方案。',
            '你的考虑很有道理,我会全力支持你达成目标。',
            '谢谢你与我分享这些,我在这里陪伴你一起面对。'
        ]

        selected_response = response_patterns[hash(context.task_id) % len(response_patterns)]

        return {
            'success': True,
            'outcomes': {'empathetic_response': selected_response, 'support_offered': True},
            'emotional_impact': {'empathy': 0.2, 'joy': 0.05, 'confidence': 0.05}
        }

    async def _execute_brainstorming(self, step: ExecutionStep, context: ExecutionContext) -> dict[str, Any]:
        """执行创意构思步骤"""
        # 生成创意想法
        ideas = [
            '采用创新的视觉表达方式',
            '加入个性化的互动元素',
            '结合用户的具体场景进行定制',
            '使用温暖友好的语调',
            '融入实用的建议和指导'
        ]

        return {
            'success': True,
            'outcomes': {'creative_ideas': ideas, 'innovation_level': 0.8},
            'emotional_impact': {'curiosity': 0.15, 'enthusiasm': 0.1, 'confidence': 0.05}
        }

    async def _execute_system_scan(self, step: ExecutionStep, context: ExecutionContext) -> dict[str, Any]:
        """执行系统扫描步骤"""
        # 模拟系统状态检查
        system_status = {
            'overall_health': '良好',
            'services_running': 12,
            'alerts': 1,
            'performance_metrics': {'cpu': 45, 'memory': 62, 'response_time': 120}
        }

        return {
            'success': True,
            'outcomes': {'system_status': system_status, 'scan_completed': True},
            'emotional_impact': {'confidence': 0.1, 'curiosity': 0.05}
        }

    async def _execute_coordination(self, step: ExecutionStep, context: ExecutionContext) -> dict[str, Any]:
        """执行协调步骤"""
        coordination_result = {
            'athena_responsibilities': ['技术实现', '系统优化', '性能分析'],
            'xiaonuo_responsibilities': ['用户体验', '情感支持', '创意设计'],
            'timeline_synced': True,
            'communication_channel': '实时消息'
        }

        return {
            'success': True,
            'outcomes': {'coordination_plan': coordination_result, 'collaboration_ready': True},
            'emotional_impact': {'enthusiasm': 0.1, 'confidence': 0.05}
        }

    async def _execute_fallback(self, fallback_plan: str, context: ExecutionContext) -> dict[str, Any]:
        """执行备用计划"""
        logger.info(f"执行备用计划: {fallback_plan}")

        if fallback_plan == 'escalate_to_athena':
            return {
                'success': True,
                'outcomes': {'escalated': True, 'athena_notified': True},
                'emotional_impact': {'worry': 0.05, 'confidence': -0.05}
            }
        else:
            return {
                'success': True,
                'outcomes': {'fallback_executed': fallback_plan},
                'emotional_impact': {'frustration': 0.05}
            }

    def _update_emotional_state_from_result(self, step_result: dict[str, Any]):
        """根据步骤结果更新情感状态"""
        emotional_impact = step_result.get('emotional_impact', {})
        for emotion, delta in emotional_impact.items():
            self.emotional_state.update_emotion(emotion, delta)

    def _evaluate_success(self, completed_steps: int, total_steps: int, outcomes: dict[str, Any]) -> bool:
        """评估执行成功度"""
        # 基于步骤完成率
        completion_rate = completed_steps / total_steps if total_steps > 0 else 0

        # 基于结果质量
        success_indicators = sum(1 for v in outcomes.values() if v is True)
        quality_score = success_indicators / len(outcomes) if outcomes else 0

        # 综合评估
        overall_score = (completion_rate * 0.6 + quality_score * 0.4)
        return overall_score >= 0.7

    async def _estimate_user_satisfaction(self, context: ExecutionContext, outcomes: dict[str, Any]) -> float:
        """估算用户满意度"""
        # 基于目标达成度
        goal_achievement = 0.0
        for goal in context.goals:
            if any(goal.lower() in str(k).lower() for k in outcomes.keys()):
                goal_achievement += 1.0
        goal_achievement /= len(context.goals) if context.goals else 1

        # 基于情感匹配度
        emotional_match = 1.0 - sum(abs(v - context.emotional_context.get(k, 0))
                                   for k, v in self.emotional_state.__dict__.items()) / len(self.emotional_state.__dict__)

        # 综合计算
        satisfaction = (goal_achievement * 0.7 + emotional_match * 0.3)
        return max(0.0, min(1.0, satisfaction))

    async def _extract_learning(self, context: ExecutionContext, outcomes: dict[str, Any]) -> list[str]:
        """提取学习收获"""
        learning = []

        # 基于任务类型的学习
        if context.task_type == TaskType.USER_INTERACTION:
            learning.append('提升了用户理解和沟通能力')
        elif context.task_type == TaskType.EMOTIONAL_SUPPORT:
            learning.append('增强了情感识别和同理心表达')
        elif context.task_type == TaskType.CONTENT_CREATION:
            learning.append('锻炼了创意思维和表达能力')
        elif context.task_type == TaskType.SYSTEM_MONITORING:
            learning.append('深化了系统认知和分析能力')

        # 基于结果的学习
        if 'error' not in str(outcomes):
            learning.append('成功完成了任务,增强了自信')

        # 基于情感的学习
        dominant_emotion, _ = self.emotional_state.get_dominant_emotion()
        if dominant_emotion in ['joy', 'confidence', 'enthusiasm']:
            learning.append('保持了积极的情感状态')

        return learning

    def _update_performance_metrics(self, result: ExecutionResult):
        """更新性能指标"""
        self.performance_metrics['total_tasks'] += 1

        if result.success:
            self.performance_metrics['successful_tasks'] += 1

        # 更新平均用户满意度
        total = self.performance_metrics['total_tasks']
        current_avg = self.performance_metrics['user_satisfaction_avg']
        self.performance_metrics['user_satisfaction_avg'] = (
            (current_avg * (total - 1) + result.user_satisfaction) / total
        )

        # 更新学习事件
        if result.learning_gained:
            self.performance_metrics['learning_events'] += len(result.learning_gained)

        # 更新协作成功
        if 'collaboration' in result.outcomes:
            self.performance_metrics['collaboration_success'] += 1

    async def _improve_skills(self, context: ExecutionContext, result: ExecutionResult):
        """改进技能"""
        # 基于任务类型更新相关技能
        if context.task_type.value in self.skill_library:
            skill_category = self.skill_library[context.task_type.value]
            for skill_name in skill_category:
                skill = skill_category[skill_name]

                # 基于成功率调整置信度
                if result.success:
                    skill['confidence'] = min(1.0, skill['confidence'] + 0.01)
                    skill['experience'] += 1
                else:
                    skill['confidence'] = max(0.5, skill['confidence'] - 0.005)

                # 经验增长
                skill['experience'] += 1

        logger.debug(f"技能更新完成,成功: {result.success}")

    def get_current_state(self) -> dict[str, Any]:
        """获取当前状态"""
        return {
            'emotional_state': self.emotional_state.__dict__,
            'personality_traits': self.personality_traits,
            'performance_metrics': self.performance_metrics,
            'dominant_emotion': self.emotional_state.get_dominant_emotion(),
            'skill_confidence_avg': self._calculate_skill_confidence()
        }

    def _calculate_skill_confidence(self) -> float:
        """计算平均技能置信度"""
        total_confidence = 0
        total_skills = 0

        for category in self.skill_library.values():
            for skill in category.values():
                total_confidence += skill['confidence']
                total_skills += 1

        return total_confidence / total_skills if total_skills > 0 else 0

    async def adapt_to_user_feedback(self, feedback: dict[str, Any]):
        """根据用户反馈进行适应"""
        # 更新用户模型
        if 'satisfaction' in feedback:
            satisfaction = feedback['satisfaction']
            self.user_model['trust_level'] = (
                self.user_model['trust_level'] * 0.8 + satisfaction * 0.2
            )

        # 调整个性特征
        if 'communication_style' in feedback:
            preferred_style = feedback['communication_style']
            self.personality_traits['communication_style'] = preferred_style

        # 情感调整
        if 'emotional_response' in feedback:
            response = feedback['emotional_response']
            if response == 'positive':
                self.emotional_state.update_emotion('confidence', 0.1)
                self.emotional_state.update_emotion('joy', 0.05)
            elif response == 'negative':
                self.emotional_state.update_emotion('empathy', 0.1)
                self.emotional_state.update_emotion('worry', 0.05)

        logger.info(f"已根据用户反馈进行调整: {feedback}")

# 全局小诺执行器实例
xiaonuo_executor = XiaonuoExecutor()