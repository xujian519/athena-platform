#!/usr/bin/env python3

"""
智能记忆增强器
Intelligent Memory Enhancer

为Athena平台增加智能记忆功能:
- 自动记录偏好:从对话中提取和记录用户偏好
- 学习决策模式:分析历史决策,学习决策规律
- 个性化建议:基于记忆提供个性化建议

作者: 小诺·双鱼公主
创建时间: 2025-12-23
版本: v1.0.0 "智能记忆"
"""


import logging

# 导入基础记忆系统
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from core.logging_config import setup_logging

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.framework.memory.timeline_memory_system import TimelineMemory

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


@dataclass
class UserPreference:
    """用户偏好"""

    category: str
    key: str
    value: Any
    confidence: float = 0.5
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    access_count: int = 0
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionPattern:
    """决策模式"""

    scenario: str
    typical_choice: str
    factors: list[str]
    confidence: float = 0.5
    sample_count: int = 1


@dataclass
class PersonalizedSuggestion:
    """个性化建议"""

    suggestion: str
    reason: str
    confidence: float
    based_on: list[str]  # 基于哪些记忆


class PreferenceExtractor:
    """偏好提取器 - 从对话中提取用户偏好"""

    def __init__(self):
        """初始化偏好提取器"""
        # 偏好指示词
        self.preference_indicators = {
            # 直接表达偏好
            "direct": ["我喜欢", "我想要", "我希望", "我倾向于", "我偏好"],
            # 评价性表达
            "evaluative": ["很好", "不错", "太好了", "非常好", "不好", "太差"],
            # 选择性表达
            "selective": ["选择", "决定", "采用", "使用", "优先考虑"],
            # 频率表达
            "frequency": ["经常", "总是", "通常", "一般", "偶尔", "很少"],
        }

        # 偏好类别
        self.preference_categories = {
            "工作方式": ["效率", "速度", "质量", "详细", "简洁"],
            "沟通风格": ["正式", "随意", "详细", "简短"],
            "技术偏好": ["AI", "传统方法", "数据驱动", "经验驱动"],
            "决策风格": ["谨慎", "果断", "分析型", "直觉型"],
            "内容偏好": ["图表", "文字", "代码", "案例"],
        }

    def extract_from_conversation(
        self, user_input: str, context: Optional[dict[str, Any]] = None
    ) -> list[UserPreference]:
        """
        从对话中提取偏好

        Args:
            user_input: 用户输入
            context: 上下文信息

        Returns:
            提取到的偏好列表
        """
        preferences = []

        # 1. 检测直接偏好表达
        for indicator in self.preference_indicators["direct"]:
            if indicator in user_input:
                pref = self._extract_direct_preference(user_input, indicator)
                if pref:
                    preferences.append(pref)

        # 2. 检测评价性表达
        for indicator in self.preference_indicators["evaluative"]:
            if indicator in user_input:
                pref = self._extract_evaluative_preference(user_input, indicator)
                if pref:
                    preferences.append(pref)

        # 3. 检测选择模式
        for indicator in self.preference_indicators["selective"]:
            if indicator in user_input:
                pref = self._extract_selective_preference(user_input, indicator)
                if pref:
                    preferences.append(pref)

        return preferences

    def _extract_direct_preference(self, text: str, indicator: str) -> Optional[UserPreference]:
        """提取直接偏好"""
        try:
            start = text.find(indicator)
            if start == -1:
                return None
            content = text[start + len(indicator) :].strip()

            # 提取具体偏好内容
            if len(content) > 0 and len(content) < 100:
                # 分类偏好
                category = self._classify_preference(content)

                return UserPreference(
                    category=category,
                    key=f"偏好_{indicator}",
                    value=content,
                    confidence=0.8,
                    context={"indicator": indicator},
                )
        except Exception:
            logger.error("操作失败: e", exc_info=True)
            raise
        return None

    def _extract_evaluative_preference(self, text: str, indicator: str) -> Optional[UserPreference]:
        """提取评价性偏好"""
        # 查找被评价的对象
        # 简化实现:假设评价词前面的内容是被评价对象
        words = text.split()
        try:
            idx = text.find(indicator)
            if idx > 0:
                evaluated = words[idx - 1]

                return UserPreference(
                    category="评价",
                    key=f"对{evaluated}的态度",
                    value=indicator,
                    confidence=0.6,
                    context={"evaluated": evaluated},
                )
        except (ValueError, IndexError) as e:
            logger.error(f"捕获(ValueError, IndexError)异常: {e}", exc_info=True)

        return None

    def _extract_selective_preference(self, text: str, indicator: str) -> Optional[UserPreference]:
        """提取选择性偏好"""
        # 简化实现
        return None

    def _classify_preference(self, content: str) -> str:
        """对偏好进行分类"""
        for category, keywords in self.preference_categories.items():
            for keyword in keywords:
                if keyword in content:
                    return category

        return "一般偏好"


class DecisionPatternLearner:
    """决策模式学习器 - 从历史决策中学习模式"""

    def __init__(self, memory: TimelineMemory):
        """
        初始化决策模式学习器

        Args:
            memory: 时间线记忆系统
        """
        self.memory = memory
        self.decision_history: list[dict] = []
        self.patterns: dict[str, DecisionPattern] = {}

    def learn_from_history(self, limit: int = 50) -> dict[str, DecisionPattern]:
        """
        从历史记忆中学习决策模式

        Args:
            limit: 分析的记忆数量

        Returns:
            学习到的决策模式
        """
        logger.info(f"📚 从历史记忆中学习决策模式(最近{limit}条)...")

        # 获取历史记忆
        all_memories = self.memory.get_all_memories()[:limit]

        # 分析决策相关记忆
        decisions = []
        for mem in all_memories:
            if mem.get("type") == "episodic":
                content = mem.get("content", "")
                # 简单判断是否包含决策相关关键词
                if any(word in content for word in ["决定", "选择", "采用", "建议", "确定"]):
                    decisions.append(mem)

        # 提取决策模式
        self._extract_patterns(decisions)

        logger.info(f"✅ 学习到 {len(self.patterns)} 种决策模式")

        return self.patterns

    def _extract_patterns(self, decisions: list[dict]) -> None:
        """提取决策模式"""
        scenario_counter = Counter()
        choice_counter = defaultdict(Counter)

        for decision in decisions:
            # 简化实现:基于关键词提取场景和选择
            content = decision.get("content", "")

            # 提取场景(简化)
            if "专利" in content:
                scenario = "专利相关决策"
            elif "法律" in content:
                scenario = "法律相关决策"
            elif "技术" in content:
                scenario = "技术相关决策"
            else:
                scenario = "一般决策"

            scenario_counter[scenario] += 1

            # 提取选择(简化)
            if "建议" in content:
                if "申请" in content:
                    choice_counter[scenario]["建议申请"] += 1
                elif "不申请" in content or "放弃" in content:
                    choice_counter[scenario]["建议不申请"] += 1

        # 生成模式
        for scenario, choices in choice_counter.items():
            if choices:
                typical_choice = choices.most_common(1)[0][0]
                confidence = choices[typical_choice] / scenario_counter[scenario]

                self.patterns[scenario] = DecisionPattern(
                    scenario=scenario,
                    typical_choice=typical_choice,
                    factors=[],
                    confidence=confidence,
                    sample_count=scenario_counter[scenario],
                )

    def predict_decision(self, scenario: str) -> Optional[DecisionPattern]:
        """
        预测给定场景下的可能决策

        Args:
            scenario: 决策场景

        Returns:
            预测的决策模式
        """
        # 查找匹配的模式
        for pattern_scenario, pattern in self.patterns.items():
            if pattern_scenario in scenario or scenario in pattern_scenario:
                return pattern

        return None


class PersonalizedRecommender:
    """个性化推荐器 - 基于记忆提供个性化建议"""

    def __init__(self, memory: TimelineMemory):
        """
        初始化个性化推荐器

        Args:
            memory: 时间线记忆系统
        """
        self.memory = memory
        self.preference_extractor = PreferenceExtractor()
        self.pattern_learner = DecisionPatternLearner(memory)
        self.user_preferences: dict[str, UserPreference] = {}

        # 加载已有偏好
        self._load_preferences()

    def _load_preferences(self) -> None:
        """从记忆中加载用户偏好"""
        try:
            semantic_memories = self.memory.get_memories_by_type("semantic")
            for mem in semantic_memories:
                if mem.get("type") == "semantic":
                    category = mem.get("category", "")
                    if "偏好" in category:
                        key = mem.get("key", "")
                        value = mem.get("value", "")
                        self.user_preferences[key] = UserPreference(
                            category=category,
                            key=key,
                            value=value,
                            confidence=mem.get("confidence", 0.5),
                            last_updated=mem.get("updated_at", ""),
                        )
        except Exception:
            logger.error("操作失败: e", exc_info=True)
            raise
    async def process_conversation(
        self, user_input: str, xiaonuo_response: str, context: Optional[dict[str, Any]] = None
    ) -> list[PersonalizedSuggestion]:
        """
        处理对话,提供个性化建议

        Args:
            user_input: 用户输入
            xiaonuo_response: 小诺的响应
            context: 上下文

        Returns:
            个性化建议列表
        """
        suggestions = []

        # 1. 提取并记录偏好
        preferences = self.preference_extractor.extract_from_conversation(user_input, context)
        for pref in preferences:
            # 记录到记忆系统
            self.memory.add_semantic_memory(
                category=pref.category,
                key=pref.key,
                value=pref.value,
                confidence=pref.confidence,
                tags=["偏好", "自动提取"],
            )

            # 更新本地缓存
            self.user_preferences[pref.key] = pref

            logger.info(f"📝 记录偏好: {pref.key} = {pref.value}")

        # 2. 基于偏好生成建议
        if preferences:
            pref_suggestions = self._generate_preference_based_suggestions(preferences, user_input)
            suggestions.extend(pref_suggestions)

        # 3. 基于历史模式生成建议
        # 重新学习模式(获取最新)
        self.pattern_learner.learn_from_history(limit=20)

        # 预测当前场景
        current_scenario = self._identify_scenario(user_input)
        if current_scenario:
            pattern = self.pattern_learner.predict_decision(current_scenario)
            if pattern and pattern.confidence > 0.6:
                suggestions.append(
                    PersonalizedSuggestion(
                        suggestion=f"根据您在'{pattern.scenario}'场景的决策习惯,您通常倾向于:{pattern.typical_choice}",
                        reason=f"基于{pattern.sample_count}次类似决策的分析,置信度{pattern.confidence:.0%}",
                        confidence=pattern.confidence,
                        based_on=["历史决策模式"],
                    )
                )

        # 4. 基于时间上下文的建议
        contextual_suggestions = self._generate_contextual_suggestions(user_input, context)
        suggestions.extend(contextual_suggestions)

        return suggestions

    def _generate_preference_based_suggestions(
        self, preferences: list[UserPreference], current_input: str
    ) -> list[PersonalizedSuggestion]:
        """基于偏好生成建议"""
        suggestions = []

        for pref in preferences:
            if pref.category == "工作方式":
                if "效率" in str(pref.value):
                    suggestions.append(
                        PersonalizedSuggestion(
                            suggestion="根据您对效率的偏好,建议使用快捷操作和批量处理功能",
                            reason=f"您曾表达:{pref.value}",
                            confidence=0.7,
                            based_on=["偏好记录"],
                        )
                    )
                elif "详细" in str(pref.value):
                    suggestions.append(
                        PersonalizedSuggestion(
                            suggestion="根据您对详细信息的需求,我可以提供更详细的分析报告",
                            reason=f"您曾表达:{pref.value}",
                            confidence=0.7,
                            based_on=["偏好记录"],
                        )
                    )

            elif pref.category == "技术偏好":
                if "数据驱动" in str(pref.value) or "数据" in str(pref.value):
                    suggestions.append(
                        PersonalizedSuggestion(
                            suggestion="根据您对数据的重视,我会在分析时提供更多数据支撑",
                            reason=f"您曾表达:{pref.value}",
                            confidence=0.75,
                            based_on=["偏好记录"],
                        )
                    )

        return suggestions

    def _identify_scenario(self, user_input: str) -> Optional[str]:
        """识别当前场景"""
        if "专利" in user_input:
            return "专利相关决策"
        elif "分析" in user_input:
            return "分析相关决策"
        elif "申请" in user_input:
            return "申请相关决策"
        else:
            return None

    def _generate_contextual_suggestions(
        self, user_input: str, context: dict[str, Any]]
    ) -> list[PersonalizedSuggestion]:
        """基于上下文生成建议"""
        suggestions = []

        # 时间相关建议
        current_hour = datetime.now().hour
        if current_hour < 9:
            suggestions.append(
                PersonalizedSuggestion(
                    suggestion="早上好!新的一天开始了,需要小诺帮您处理什么重要事项吗?",
                    reason="早晨时段",
                    confidence=0.5,
                    based_on=["时间上下文"],
                )
            )
        elif current_hour > 18:
            suggestions.append(
                PersonalizedSuggestion(
                    suggestion="晚上好!一天的辛苦工作后,需要小诺帮您总结今天的重要事项吗?",
                    reason="晚间时段",
                    confidence=0.5,
                    based_on=["时间上下文"],
                )
            )

        return suggestions

    def get_user_profile(self) -> dict[str, Any]:
        """获取用户画像"""
        return {
            "preferences": {
                key: {
                    "category": pref.category,
                    "value": pref.value,
                    "confidence": pref.confidence,
                    "last_updated": pref.last_updated,
                }
                for key, pref in self.user_preferences.items()
            },
            "decision_patterns": {
                scenario: {
                    "typical_choice": pattern.typical_choice,
                    "confidence": pattern.confidence,
                    "sample_count": pattern.sample_count,
                }
                for scenario, pattern in self.pattern_learner.patterns.items()
            },
            "profile_summary": self._generate_profile_summary(),
        }

    def _generate_profile_summary(self) -> str:
        """生成画像摘要"""
        pref_count = len(self.user_preferences)
        pattern_count = len(self.pattern_learner.patterns)

        summary_parts = []
        if pref_count > 0:
            list(self.user_preferences.values())[:3]
            summary_parts.append(f"已记录{pref_count}项偏好")

        if pattern_count > 0:
            summary_parts.append(f"已识别{pattern_count}种决策模式")

        return "、".join(summary_parts) if summary_parts else "新用户,正在学习中"


class IntelligentMemoryEnhancer:
    """智能记忆增强器 - 统一入口"""

    def __init__(self):
        """初始化智能记忆增强器"""
        self.memory = TimelineMemory()
        self.recommender = PersonalizedRecommender(self.memory)
        self.enabled = True

        logger.info("🧠 智能记忆增强器已启动")

    async def enhance_conversation(
        self, user_input: str, xiaonuo_response: str, context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        增强对话(自动记录偏好、学习模式、提供个性化建议)

        Args:
            user_input: 用户输入
            xiaonuo_response: 小诺响应
            context: 上下文

        Returns:
            增强结果
        """
        if not self.enabled:
            return {"enhanced": False, "reason": "记忆增强未启用"}

        result = {
            "enhanced": True,
            "preferences_recorded": [],
            "suggestions": [],
            "user_profile": {},
        }

        # 1. 处理对话(记录偏好、生成建议)
        suggestions = await self.recommender.process_conversation(
            user_input, xiaonuo_response, context
        )

        # 2. 记录对话到记忆
        self.memory.record_conversation(
            user_input=user_input,
            xiaonuo_response=xiaonuo_response,
            emotional_tone=context.get("emotional_tone", "friendly") if context else "friendly",
        )

        # 3. 获取用户画像
        profile = self.recommender.get_user_profile()

        result["suggestions"]] = [
            {
                "suggestion": s.suggestion,
                "reason": s.reason,
                "confidence": s.confidence,
                "based_on": s.based_on,
            }
            for s in suggestions
        ]

        result["user_profile"] = profile

        # 记录增强事件
        if suggestions:
            logger.info(f"💡 生成了 {len(suggestions)} 条个性化建议")

        return result

    def learn_decision_patterns(self, limit: int = 50) -> dict[str, DecisionPattern]:
        """学习决策模式"""
        return self.recommender.pattern_learner.learn_from_history(limit)

    def get_user_profile(self) -> dict[str, Any]:
        """获取用户画像"""
        return self.recommender.get_user_profile()


# 全局单例
_enhancer_instance = None


def get_memory_enhancer() -> IntelligentMemoryEnhancer:
    """获取智能记忆增强器单例"""
    global _enhancer_instance
    if _enhancer_instance is None:
        _enhancer_instance = IntelligentMemoryEnhancer()
    return _enhancer_instance


# 测试代码
async def main():
    """测试智能记忆增强功能"""

    print("\n" + "=" * 60)
    print("🧠 智能记忆增强器测试")
    print("=" * 60 + "\n")

    enhancer = get_memory_enhancer()

    # 测试1:处理包含偏好的对话
    print("📝 测试1: 处理包含偏好的对话")
    result_1 = await enhancer.enhance_conversation(
        user_input="我喜欢详细的分析报告,这样能更好地做决策",
        xiaonuo_response="好的爸爸,小诺会为您提供详细的分析报告。",
        context={"emotional_tone": "friendly"},
    )

    print(f"✅ 已记录偏好: {len(result_1['user_profile']['preferences'])} 项")
    print(f"💡 个性化建议: {len(result_1['suggestions'])} 条")
    for suggestion in result_1["suggestions"]:
        print(f"   • {suggestion['suggestion']}")
        print(f"     原因: {suggestion['reason']}")

    # 测试2:学习决策模式
    print("\n\n📚 测试2: 学习决策模式")
    patterns = enhancer.learn_decision_patterns(limit=20)
    print(f"✅ 学习到 {len(patterns)} 种决策模式")
    for scenario, pattern in patterns.items():
        print(f"   • {scenario}: {pattern.typical_choice} (置信度: {pattern.confidence:.0%})")

    # 测试3:获取用户画像
    print("\n\n👤 测试3: 获取用户画像")
    profile = enhancer.get_user_profile()
    print(f"📊 用户画像摘要: {profile['profile_summary']}")

    print("\n\n✅ 测试完成!")


# 入口点: @async_main装饰器已添加到main函数

