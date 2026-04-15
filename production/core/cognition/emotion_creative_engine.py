#!/usr/bin/env python3
"""
情感驱动创意引擎
Emotion-Driven Creative Engine

将小诺的情感智能与创意生成深度融合，产生更贴合用户需求的创意方案

作者: Athena平台团队
创建时间: 2025-12-31
版本: 1.0.0
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class UserEmotion(Enum):
    """用户情感类型"""
    FRUSTRATION = "frustration"  # 挫败感 - 需要解决方案
    URGENCY = "urgency"  # 紧迫感 - 需要快速方案
    UNCERTAINTY = "uncertainty"  # 不确定 - 需要解释指导
    SATISFACTION = "satisfaction"  # 满意 - 可以拓展
    NEUTRAL = "neutral"  # 中性 - 标准响应


class CreativityMode(Enum):
    """创意模式"""
    PROBLEM_SOLVING = "problem_solving"  # 问题解决型
    RAPID_PROTOTYPING = "rapid_prototyping"  # 快速原型型
    EXPLANATORY = "explanatory"  # 解释说明型
    EXPANSIVE = "expansive"  # 拓展创新型
    BALANCED = "balanced"  # 平衡型


@dataclass
class PracticalityMetrics:
    """实用性评估指标"""
    actionability: float = 0.0  # 可行动性 (0-1)
    resource_feasibility: float = 0.0  # 资源可行性 (0-1)
    time_to_value: float = 0.0  # 价值实现速度 (0-1, 越高越快)
    implementation_complexity: float = 0.0  # 实施复杂度 (0-1, 越低越简单)
    user_friendly_score: float = 0.0  # 用户友好度 (0-1)
    overall_practicality: float = 0.0  # 综合实用性 (0-1)

    def calculate_overall(self) -> float:
        """计算综合实用性"""
        weights = {
            "actionability": 0.30,
            "resource_feasibility": 0.20,
            "time_to_value": 0.15,
            "implementation_complexity": 0.20,  # 越低越好，需要反转
            "user_friendly_score": 0.15,
        }
        self.overall_practicality = (
            self.actionability * weights["actionability"] +
            self.resource_feasibility * weights["resource_feasibility"] +
            self.time_to_value * weights["time_to_value"] +
            (1.0 - self.implementation_complexity) * weights["implementation_complexity"] +
            self.user_friendly_score * weights["user_friendly_score"]
        )
        return self.overall_practicality


@dataclass
class CreativeIdea:
    """创意方案"""
    idea_id: str
    title: str
    description: str
    emotion_source: UserEmotion
    creativity_mode: CreativityMode
    practicality: PracticalityMetrics
    implementation_steps: list[str] = field(default_factory=list)
    resource_requirements: list[str] = field(default_factory=list)
    expected_outcomes: list[str] = field(default_factory=list)
    estimated_effort: str = ""
    risk_factors: list[str] = field(default_factory=list)
    confidence_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ImplementationRoadmap:
    """实施路线图"""
    idea_id: str
    phases: list[dict[str, Any]]
    total_estimated_time: str
    resource_summary: dict[str, Any]
    success_metrics: list[str]
    risk_mitigation: dict[str, str]


class EmotionCreativeEngine:
    """
    情感驱动创意引擎

    核心功能:
    1. 情感识别与映射
    2. 情感驱动的创意生成
    3. 实用性评估
    4. 实施路径生成
    5. 创意优化
    """

    # 情感-创意映射表
    EMOTION_CREATIVITY_MAP = {
        UserEmotion.FRUSTRATION: {
            "mode": CreativityMode.PROBLEM_SOLVING,
            "focus": "解决具体问题",
            "approach": "系统化分析+逐步解决",
            "tone": "supportive",
            "keywords": ["解决", "克服", "改善", "优化"],
        },
        UserEmotion.URGENCY: {
            "mode": CreativityMode.RAPID_PROTOTYPING,
            "focus": "快速见效",
            "approach": "最小可行方案+快速迭代",
            "tone": "efficient",
            "keywords": ["快速", "即时", "立即", "简便"],
        },
        UserEmotion.UNCERTAINTY: {
            "mode": CreativityMode.EXPLANATORY,
            "focus": "清晰解释",
            "approach": "教学式说明+实例演示",
            "tone": "educational",
            "keywords": ["理解", "明白", "掌握", "学习"],
        },
        UserEmotion.SATISFACTION: {
            "mode": CreativityMode.EXPANSIVE,
            "focus": "拓展创新",
            "approach": "创意发散+边界探索",
            "tone": "enthusiastic",
            "keywords": ["拓展", "创新", "突破", "升级"],
        },
        UserEmotion.NEUTRAL: {
            "mode": CreativityMode.BALANCED,
            "focus": "全面考虑",
            "approach": "平衡方案+多元选择",
            "tone": "professional",
            "keywords": ["优化", "改进", "提升", "完善"],
        },
    }

    def __init__(self):
        self.creative_history: list[CreativeIdea] = []
        self.domain_knowledge: dict[str, Any] = {}
        self.user_preferences: dict[str, Any] = {}

    async def initialize(self):
        """初始化引擎"""
        logger.info("🎨 初始化情感驱动创意引擎...")
        await self._load_domain_knowledge()
        await self._load_creative_templates()
        logger.info("✅ 情感驱动创意引擎初始化完成")

    async def _load_domain_knowledge(self):
        """加载领域知识"""
        self.domain_knowledge = {
            "patent_law": {
                "resources": ["专利数据库", "审查指南", "案例库"],
                "experts": ["专利律师", "专利代理人"],
                "typical_efforts": {"基础": "1-2周", "进阶": "2-4周", "专业": "1-2月"},
            },
            "technology": {
                "resources": ["开发环境", "技术文档", "测试数据"],
                "experts": ["架构师", "开发者"],
                "typical_efforts": {"基础": "几天", "进阶": "1-2周", "专业": "2-4周"},
            },
            "business": {
                "resources": ["市场数据", "行业报告", "专家咨询"],
                "experts": ["商业分析师", "战略顾问"],
                "typical_efforts": {"基础": "1周", "进阶": "2-3周", "专业": "1-2月"},
            },
        }

    async def _load_creative_templates(self):
        """加载创意模板"""
        self.creative_templates = {
            CreativityMode.PROBLEM_SOLVING: {
                "structure": ["问题诊断", "根因分析", "解决方案", "实施计划", "验证机制"],
                "focus_areas": ["可执行性", "效果保证", "风险控制"],
            },
            CreativityMode.RAPID_PROTOTYPING: {
                "structure": ["核心功能", "快速验证", "迭代优化", "扩展完善"],
                "focus_areas": ["速度", "简洁", "立即可用"],
            },
            CreativityMode.EXPLANATORY: {
                "structure": ["概念说明", "实例演示", "步骤指导", "常见问题"],
                "focus_areas": ["清晰度", "易懂性", "完整性"],
            },
            CreativityMode.EXPANSIVE: {
                "structure": ["现状分析", "创新方向", "拓展可能", "未来规划"],
                "focus_areas": ["创新性", "前瞻性", "突破性"],
            },
            CreativityMode.BALANCED: {
                "structure": ["需求分析", "方案设计", "实施建议", "评估标准"],
                "focus_areas": ["平衡性", "全面性", "灵活性"],
            },
        }

    async def generate_with_emotion(
        self,
        user_query: str,
        user_emotion: UserEmotion,
        domain: str = "general",
        context: dict[str, Any] | None = None,
    ) -> CreativeIdea:
        """
        结合用户情感生成创意

        Args:
            user_query: 用户查询
            user_emotion: 用户情感
            domain: 领域
            context: 上下文信息

        Returns:
            CreativeIdea: 生成的创意方案
        """
        logger.info(f"💭 生成情感驱动创意: {user_emotion.value} -> {domain}")

        # 1. 获取创意模式
        creativity_config = self.EMOTION_CREATIVITY_MAP.get(
            user_emotion, self.EMOTION_CREATIVITY_MAP[UserEmotion.NEUTRAL]
        )
        mode = creativity_config["mode"]

        # 2. 基于情感和领域生成创意
        idea = await self._generate_creative_idea(
            user_query, user_emotion, mode, domain, context or {}
        )

        # 3. 评估实用性
        idea.practicality = await self._assess_practicality(idea, domain)

        # 4. 生成实施路径
        idea.implementation_steps = await self._generate_implementation_steps(
            idea, mode, domain
        )

        # 5. 计算置信度
        idea.confidence_score = await self._calculate_confidence(idea, user_emotion)

        # 记录创意历史
        self.creative_history.append(idea)

        logger.info(
            f"✅ 创意生成完成: {idea.idea_id}, "
            f"实用性: {idea.practicality.overall_practicality:.2f}, "
            f"置信度: {idea.confidence_score:.2f}"
        )

        return idea

    async def _generate_creative_idea(
        self,
        query: str,
        emotion: UserEmotion,
        mode: CreativityMode,
        domain: str,
        context: dict[str, Any],    ) -> CreativeIdea:
        """生成创意的核心逻辑"""
        # 获取配置
        emotion_config = self.EMOTION_CREATIVITY_MAP[emotion]
        template = self.creative_templates.get(mode, self.creative_templates[CreativityMode.BALANCED])

        # 生成创意ID
        idea_id = f"CREA_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 基于情感和模式生成创意
        title = await self._generate_title(query, emotion, mode, domain)
        description = await self._generate_description(query, emotion, mode, domain, context)

        # 生成预期成果
        expected_outcomes = await self._generate_expected_outcomes(mode, domain)

        # 识别资源需求
        resource_requirements = await self._identify_resource_requirements(domain)

        # 估计实施难度
        estimated_effort = await self._estimate_effort(mode, domain)

        # 识别风险因素
        risk_factors = await self._identify_risks(mode, domain)

        idea = CreativeIdea(
            idea_id=idea_id,
            title=title,
            description=description,
            emotion_source=emotion,
            creativity_mode=mode,
            practicality=PracticalityMetrics(),  # 稍后评估
            implementation_steps=[],  # 稍后生成
            resource_requirements=resource_requirements,
            expected_outcomes=expected_outcomes,
            estimated_effort=estimated_effort,
            risk_factors=risk_factors,
        )

        return idea

    async def _generate_title(
        self, query: str, emotion: UserEmotion, mode: CreativityMode, domain: str
    ) -> str:
        """生成创意标题"""
        emotion_config = self.EMOTION_CREATIVITY_MAP[emotion]

        # 根据情感和模式生成不同的标题风格
        title_templates = {
            CreativityMode.PROBLEM_SOLVING: f"解决{query[:20]}的系统化方案",
            CreativityMode.RAPID_PROTOTYPING: f"快速实现{query[:20]}的MVP方案",
            CreativityMode.EXPLANATORY: f"理解{query[:20]}的完整指南",
            CreativityMode.EXPANSIVE: f"在{query[:20]}基础上的创新拓展",
            CreativityMode.BALANCED: f"关于{query[:20]}的综合优化方案",
        }

        return title_templates.get(mode, f"{query[:30]}的创意方案")

    async def _generate_description(
        self,
        query: str,
        emotion: UserEmotion,
        mode: CreativityMode,
        domain: str,
        context: dict[str, Any],    ) -> str:
        """生成创意描述"""
        emotion_config = self.EMOTION_CREATIVITY_MAP[emotion]

        description = f"""基于您{emotion_config['focus']}的需求，本方案采用{emotion_config['approach']}的方法。

**核心思路**:
{emotion_config['keywords'][0]}: 针对您的问题提供直接有效的解决路径
{emotion_config['keywords'][1]}: 确保方案的可行性和实用性
{emotion_config['keywords'][2]}: 在实施过程中持续优化改进

**适用场景**: {domain}领域的相关需求
**方案特点**: 以{emotion_config['tone']}的方式，帮助您{emotion_config['focus']}
"""

        return description

    async def _generate_expected_outcomes(
        self, mode: CreativityMode, domain: str
    ) -> list[str]:
        """生成预期成果"""
        outcomes_map = {
            CreativityMode.PROBLEM_SOLVING: [
                "问题得到系统性解决",
                "建立长期预防机制",
                "提升处理类似问题的能力",
            ],
            CreativityMode.RAPID_PROTOTYPING: [
                "快速验证核心想法",
                "获得即时反馈",
                "为后续迭代奠定基础",
            ],
            CreativityMode.EXPLANATORY: [
                "完全理解相关概念",
                "掌握关键操作方法",
                "建立清晰的知识体系",
            ],
            CreativityMode.EXPANSIVE: [
                "发现新的可能性",
                "拓展思考边界",
                "建立创新方向",
            ],
            CreativityMode.BALANCED: [
                "全面了解解决方案",
                "平衡各方需求",
                "灵活应对变化",
            ],
        }

        return outcomes_map.get(mode, ["达到预期目标"])

    async def _identify_resource_requirements(self, domain: str) -> list[str]:
        """识别资源需求"""
        if domain in self.domain_knowledge:
            return self.domain_knowledge[domain]["resources"]
        return ["基础资源", "执行时间", "持续关注"]

    async def _estimate_effort(self, mode: CreativityMode, domain: str) -> str:
        """估计实施难度"""
        effort_map = {
            CreativityMode.PROBLEM_SOLVING: "2-4周",
            CreativityMode.RAPID_PROTOTYPING: "几天到1周",
            CreativityMode.EXPLANATORY: "1-2小时学习和理解",
            CreativityMode.EXPANSIVE: "持续探索和迭代",
            CreativityMode.BALANCED: "1-3周",
        }

        if domain in self.domain_knowledge:
            base_effort = effort_map.get(mode, "1-2周")
            return f"{base_effort}（根据{domain}领域特点）"

        return effort_map.get(mode, "1-2周")

    async def _identify_risks(self, mode: CreativityMode, domain: str) -> list[str]:
        """识别风险因素"""
        common_risks = ["资源不足", "时间压力", "需求变更"]

        domain_specific = {
            "patent_law": ["法律政策变化", "审查标准调整", "现有技术限制"],
            "technology": ["技术选型风险", "兼容性问题", "性能瓶颈"],
            "business": ["市场变化", "竞争加剧", "用户偏好改变"],
        }

        return common_risks + domain_specific.get(domain, [])

    async def _assess_practicality(
        self, idea: CreativeIdea, domain: str
    ) -> PracticalityMetrics:
        """评估创意的实用性"""
        metrics = PracticalityMetrics()

        # 可行动性: 基于实施步骤的明确性
        metrics.actionability = 0.85 if idea.implementation_steps else 0.70

        # 资源可行性: 基于资源需求是否清晰
        metrics.resource_feasibility = 0.80 if idea.resource_requirements else 0.60

        # 价值实现速度: 基于创意模式
        speed_map = {
            CreativityMode.RAPID_PROTOTYPING: 0.95,
            CreativityMode.PROBLEM_SOLVING: 0.75,
            CreativityMode.BALANCED: 0.70,
            CreativityMode.EXPLANATORY: 0.85,
            CreativityMode.EXPANSIVE: 0.50,
        }
        metrics.time_to_value = speed_map.get(idea.creativity_mode, 0.70)

        # 实施复杂度: 基于风险因素数量
        base_complexity = 0.3
        complexity_increase = len(idea.risk_factors) * 0.05
        metrics.implementation_complexity = min(1.0, base_complexity + complexity_increase)

        # 用户友好度: 基于情感匹配
        friendliness_map = {
            UserEmotion.FRUSTRATION: 0.90,  # 支持性高
            UserEmotion.URGENCY: 0.85,  # 高效友好
            UserEmotion.UNCERTAINTY: 0.95,  # 教育友好
            UserEmotion.SATISFACTION: 0.75,
            UserEmotion.NEUTRAL: 0.80,
        }
        metrics.user_friendly_score = friendliness_map.get(idea.emotion_source, 0.80)

        # 计算综合得分
        metrics.calculate_overall()

        return metrics

    async def _generate_implementation_steps(
        self, idea: CreativeIdea, mode: CreativityMode, domain: str
    ) -> list[str]:
        """生成实施步骤"""
        template = self.creative_templates.get(mode, self.creative_templates[CreativityMode.BALANCED])
        structure = template["structure"]

        # 基于结构生成具体步骤
        steps = []
        for i, phase in enumerate(structure, 1):
            step = f"{i}. {phase}"

            # 根据领域添加具体指导
            if domain == "patent_law" and "分析" in phase:
                step += " - 进行现有技术检索和法律分析"
            elif domain == "technology" and "实施" in phase:
                step += " - 开发核心功能并进行测试"
            elif domain == "business" and "规划" in phase:
                step += " - 制定商业计划和执行路线"

            steps.append(step)

        return steps

    async def _calculate_confidence(
        self, idea: CreativeIdea, emotion: UserEmotion
    ) -> float:
        """计算创意的置信度"""
        base_confidence = 0.75

        # 基于实用性调整
        practicality_boost = idea.practicality.overall_practicality * 0.15

        # 基于情感匹配度调整
        emotion_match = {
            UserEmotion.FRUSTRATION: 0.05,  # 高匹配
            UserEmotion.URGENCY: 0.05,
            UserEmotion.UNCERTAINTY: 0.05,
            UserEmotion.SATISFACTION: 0.03,
            UserEmotion.NEUTRAL: 0.00,
        }
        emotion_boost = emotion_match.get(emotion, 0.00)

        # 基于风险调整
        risk_penalty = len(idea.risk_factors) * 0.02

        confidence = base_confidence + practicality_boost + emotion_boost - risk_penalty

        return max(0.5, min(1.0, confidence))  # 限制在[0.5, 1.0]范围内

    async def generate_roadmap(
        self, idea: CreativeIdea, domain: str = "general"
    ) -> ImplementationRoadmap:
        """
        为创意生成详细实施路线图

        Args:
            idea: 创意方案
            domain: 领域

        Returns:
            ImplementationRoadmap: 实施路线图
        """
        logger.info(f"🗺️  生成实施路线图: {idea.idea_id}")

        # 获取领域典型时间
        if domain in self.domain_knowledge:
            typical_efforts = self.domain_knowledge[domain]["typical_efforts"]
        else:
            typical_efforts = {"基础": "1周", "进阶": "2周", "专业": "4周"}

        # 生成分阶段实施计划
        phases = [
            {
                "phase": "阶段一：准备与规划",
                "duration": typical_efforts["基础"],
                "objectives": [
                    "明确具体目标和范围",
                    "收集必要信息和资源",
                    "制定详细执行计划",
                ],
                "deliverables": ["需求文档", "资源清单", "时间计划"],
                "tasks": [
                    "与相关方确认需求",
                    "准备所需工具和环境",
                    "建立评估标准",
                ],
            },
            {
                "phase": "阶段二：核心实施",
                "duration": typical_efforts["进阶"],
                "objectives": [
                    "执行核心方案",
                    "实现关键功能",
                    "达成预期成果",
                ],
                "deliverables": ["实施方案", "执行结果", "进度报告"],
                "tasks": idea.implementation_steps[:3] if idea.implementation_steps else [
                    "执行计划步骤",
                    "监控执行进度",
                    "及时调整方案"
                ],
            },
            {
                "phase": "阶段三：优化与完善",
                "duration": typical_efforts["专业"],
                "objectives": [
                    "优化实施效果",
                    "建立长效机制",
                    "总结经验教训",
                ],
                "deliverables": ["优化报告", "操作手册", "总结文档"],
                "tasks": [
                    "评估实施效果",
                    "收集反馈意见",
                    "持续改进优化",
                ],
            },
        ]

        # 资源汇总
        resource_summary = {
            "required": idea.resource_requirements,
            "optional": ["外部咨询", "培训学习", "工具升级"],
            "estimated_cost": "根据具体情况确定",
        }

        # 成功指标
        success_metrics = idea.expected_outcomes + [
            "按计划完成各阶段目标",
            "资源使用在预算范围内",
            "相关方满意度达到预期",
        ]

        # 风险缓解
        risk_mitigation = dict.fromkeys(idea.risk_factors, "制定应对预案，持续监控")

        # 计算总时间
        total_time = f"{sum([self._parse_duration(p['duration']) for p in phases])}周"

        roadmap = ImplementationRoadmap(
            idea_id=idea.idea_id,
            phases=phases,
            total_estimated_time=total_time,
            resource_summary=resource_summary,
            success_metrics=success_metrics,
            risk_mitigation=risk_mitigation,
        )

        logger.info(f"✅ 路线图生成完成: {len(phases)}个阶段")

        return roadmap

    def _parse_duration(self, duration_str: str) -> int:
        """解析时间字符串为周数"""
        if "天" in duration_str or "day" in duration_str.lower():
            return 1
        elif "月" in duration_str or "month" in duration_str.lower():
            return 4
        elif "小时" in duration_str or "hour" in duration_str.lower():
            return 0
        else:
            # 尝试提取数字
            import re
            match = re.search(r'\d+', duration_str)
            if match:
                return int(match.group())
            return 2

    async def optimize_idea(
        self, idea: CreativeIdea, feedback: str | None = None
    ) -> CreativeIdea:
        """
        基于反馈优化创意

        Args:
            idea: 原始创意
            feedback: 反馈意见

        Returns:
            CreativeIdea: 优化后的创意
        """
        logger.info(f"🔄 优化创意: {idea.idea_id}")

        # 创建优化的创意副本
        optimized = CreativeIdea(
            idea_id=f"{idea.idea_id}_OPT",
            title=idea.title,
            description=idea.description,
            emotion_source=idea.emotion_source,
            creativity_mode=idea.creativity_mode,
            practicality=PracticalityMetrics(),
            implementation_steps=list(idea.implementation_steps),
            resource_requirements=list(idea.resource_requirements),
            expected_outcomes=list(idea.expected_outcomes),
            estimated_effort=idea.estimated_effort,
            risk_factors=list(idea.risk_factors),
        )

        # 基于反馈优化
        if feedback:
            if "简单" in feedback or "simple" in feedback.lower():
                # 简化方案
                optimized.implementation_steps = optimized.implementation_steps[:3]
                optimized.estimated_effort = self._reduce_effort(optimized.estimated_effort)
            elif "详细" in feedback or "detailed" in feedback.lower():
                # 增加细节
                optimized.implementation_steps = await self._expand_steps(optimized.implementation_steps)
            elif "风险" in feedback or "risk" in feedback.lower():
                # 降低风险
                optimized.risk_factors = await self._add_mitigation(optimized.risk_factors)

        # 重新评估实用性
        optimized.practicality = await self._assess_practicality(optimized, "general")
        optimized.confidence_score = await self._calculate_confidence(optimized, idea.emotion_source)

        logger.info(f"✅ 创意优化完成: 实用性 {optimized.practicality.overall_practicality:.2f}")

        return optimized

    def _reduce_effort(self, effort_str: str) -> str:
        """减少工作量估计"""
        if "月" in effort_str:
            return "2-3周"
        elif "周" in effort_str:
            return "1-2周"
        return effort_str

    async def _expand_steps(self, steps: list[str]) -> list[str]:
        """扩展步骤细节"""
        expanded = []
        for step in steps:
            expanded.append(step)
            expanded.append(f"  - 详细执行: {step}的具体操作")
        return expanded

    async def _add_mitigation(self, risks: list[str]) -> list[str]:
        """为风险添加缓解措施"""
        return [f"{risk} (已制定应对预案)" for risk in risks]

    async def get_creative_statistics(self) -> dict[str, Any]:
        """获取创意统计信息"""
        if not self.creative_history:
            return {"message": "暂无创意历史"}

        total = len(self.creative_history)
        emotions = [idea.emotion_source for idea in self.creative_history]
        modes = [idea.creativity_mode for idea in self.creative_history]

        emotion_distribution = {e.value: emotions.count(e) for e in set(emotions)}
        mode_distribution = {m.value: modes.count(m) for m in set(modes)}

        avg_practicality = sum(
            idea.practicality.overall_practicality for idea in self.creative_history
        ) / total
        avg_confidence = sum(idea.confidence_score for idea in self.creative_history) / total

        return {
            "total_ideas": total,
            "emotion_distribution": emotion_distribution,
            "mode_distribution": mode_distribution,
            "average_practicality": avg_practicality,
            "average_confidence": avg_confidence,
            "recent_ideas": [
                {
                    "id": idea.idea_id,
                    "title": idea.title,
                    "practicality": idea.practicality.overall_practicality,
                    "confidence": idea.confidence_score,
                }
                for idea in self.creative_history[-5:]
            ],
        }

    async def shutdown(self):
        """关闭引擎"""
        logger.info("🛑 关闭情感驱动创意引擎...")
        logger.info(f"📊 本次运行生成 {len(self.creative_history)} 个创意")
        logger.info("✅ 情感驱动创意引擎已关闭")


# 便捷函数
_emotion_creative_engine: EmotionCreativeEngine | None = None


async def get_emotion_creative_engine() -> EmotionCreativeEngine:
    """获取情感驱动创意引擎单例"""
    global _emotion_creative_engine
    if _emotion_creative_engine is None:
        _emotion_creative_engine = EmotionCreativeEngine()
        await _emotion_creative_engine.initialize()
    return _emotion_creative_engine
