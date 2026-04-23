#!/usr/bin/env python3

"""
小诺用户偏好学习系统
Xiaonuo User Preference Learning System

实现用户行为学习、个性化权重调整和用户画像构建

作者: Athena平台团队
创建时间: 2025-12-18
版本: v1.0.0 "智能用户偏好学习"
"""

import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import jieba

# 安全修复: 使用joblib替代pickle序列化scikit-learn模型
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# 机器学习库
from sklearn.preprocessing import StandardScaler

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class UserPersona(Enum):
    """用户画像类型"""

    TECH_EXPERT = "tech_expert"  # 技术专家
    BUSINESS_ANALYST = "business_analyst"  # 业务分析师
    CREATIVE_THINKER = "creative_thinker"  # 创意思考者
    FAMILY_ORIENTED = "family_oriented"  # 家庭导向型
    QUICK_LEARNER = "quick_learner"  # 快速学习者
    METHODICAL_PLANNER = "methodical_planner"  # 方法型规划者
    EMOTIONAL_USER = "emotional_user"  # 情感用户
    ENTREPRENEUR = "entrepreneur"  # 创业者


@dataclass
class UserInteraction:
    """用户交互记录"""

    user_id: str
    timestamp: datetime
    intent: str
    selected_tools: list[str]
    text_input: str
    success: bool
    satisfaction_score: float  # 0-1
    response_time: float
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class UserProfile:
    """用户画像"""

    user_id: str
    persona: UserPersona
    tool_preferences: dict[str, float] = field(default_factory=dict)
    intent_tool_patterns: dict[str, list[str] = field(default_factory=dict)
    time_patterns: dict[str, float] = field(default_factory=dict)
    complexity_preference: float = 0.5  # 0-1,偏好复杂度
    response_time_preference: float = 0.5  # 0-1,偏好响应速度
    learning_style: str = "balanced"  # visual, auditory, kinesthetic, balanced
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class PreferenceConfig:
    """偏好学习配置"""

    # 学习参数
    learning_rate: float = 0.1
    decay_factor: float = 0.95  # 时间衰减
    min_interactions: int = 5  # 最少交互次数
    preference_threshold: float = 0.6  # 偏好阈值

    # 聚类参数
    n_personas: int = 8
    clustering_features: int = 20

    # 路径配置
    model_dir: str = "models/user_preference"
    data_dir: str = "data/user_preference"


class XiaonuoUserPreferenceLearner:
    """小诺用户偏好学习器"""

    def __init__(self, config: PreferenceConfig = None):
        self.config = config or PreferenceConfig()

        # 创建必要目录
        os.makedirs(self.config.model_dir, exist_ok=True)
        os.makedirs(self.config.data_dir, exist_ok=True)

        # 用户数据存储
        self.user_profiles: dict[str, UserProfile] = {}
        self.interaction_history: dict[str, list[UserInteraction] = defaultdict(list)
        self.persona_templates: dict[UserPersona, dict[str, Any] = {}

        # 机器学习模型
        self.preference_classifier = None
        self.persona_classifier = None
        self.feature_scaler = None
        self.text_vectorizer = None

        # 初始化
        self._init_persona_templates()
        self._init_jieba()

        logger.info("👤 小诺用户偏好学习器初始化完成")
        logger.info(f"🎭 用户画像类型: {len(UserPersona)}")

    def _init_persona_templates(self) -> Any:
        """初始化用户画像模板"""
        self.persona_templates = {
            UserPersona.TECH_EXPERT: {
                "description": "技术专家,偏好代码分析、系统架构等技术工具",
                "tool_weights": {
                    "code_analyzer": 0.95,
                    "performance_profiler": 0.90,
                    "api_tester": 0.85,
                    "api_gateway": 0.80,
                    "system_monitor": 0.75,
                },
                "intent_preferences": ["technical", "command", "query"],
                "characteristics": ["理性", "精确", "效率导向", "技术导向"],
            },
            UserPersona.BUSINESS_ANALYST: {
                "description": "业务分析师,偏好决策支持、项目管理等工具",
                "tool_weights": {
                    "decision_engine": 0.95,
                    "project_manager": 0.90,
                    "risk_analyzer": 0.85,
                    "content_summarizer": 0.80,
                    "web_search": 0.75,
                },
                "intent_preferences": ["work", "coordination", "query"],
                "characteristics": ["分析型", "规划导向", "结果驱动", "商业思维"],
            },
            UserPersona.CREATIVE_THINKER: {
                "description": "创意思考者,偏好聊天、娱乐、内容生成等工具",
                "tool_weights": {
                    "chat_companion": 0.95,
                    "content_summarizer": 0.85,
                    "semantic_search": 0.80,
                    "web_search": 0.75,
                    "research_assistant": 0.70,
                },
                "intent_preferences": ["entertainment", "emotional", "learning"],
                "characteristics": ["创新思维", "想象力丰富", "好奇心强", "艺术感"],
            },
            UserPersona.FAMILY_ORIENTED: {
                "description": "家庭导向型,偏好情感交流、家庭管理等工具",
                "tool_weights": {
                    "emotional_support": 0.95,
                    "chat_companion": 0.90,
                    "team_collaborator": 0.80,
                    "project_manager": 0.75,
                    "health_checker": 0.70,
                },
                "intent_preferences": ["family", "emotional", "health"],
                "characteristics": ["情感丰富", "关爱他人", "家庭责任", "温暖体贴"],
            },
            UserPersona.QUICK_LEARNER: {
                "description": "快速学习者,偏好知识获取、技能提升等工具",
                "tool_weights": {
                    "knowledge_graph": 0.95,
                    "web_search": 0.90,
                    "research_assistant": 0.85,
                    "semantic_search": 0.80,
                    "content_summarizer": 0.75,
                },
                "intent_preferences": ["learning", "query", "technical"],
                "characteristics": ["学习能力强", "好奇心强", "知识追求", "成长导向"],
            },
            UserPersona.METHODICAL_PLANNER: {
                "description": "方法型规划者,偏好项目管理、决策支持等工具",
                "tool_weights": {
                    "project_manager": 0.95,
                    "decision_engine": 0.90,
                    "risk_analyzer": 0.85,
                    "team_collaborator": 0.80,
                    "service_orchestrator": 0.75,
                },
                "intent_preferences": ["coordination", "work", "family"],
                "characteristics": ["有条理", "规划性强", "细节导向", "系统性思维"],
            },
            UserPersona.EMOTIONAL_USER: {
                "description": "情感用户,偏好情感支持、聊天交流等工具",
                "tool_weights": {
                    "emotional_support": 0.95,
                    "chat_companion": 0.90,
                    "health_checker": 0.80,
                    "team_collaborator": 0.75,
                    "content_summarizer": 0.70,
                },
                "intent_preferences": ["emotional", "family", "entertainment"],
                "characteristics": ["情感丰富", "表达欲强", "社交需求", "感性思维"],
            },
            UserPersona.ENTREPRENEUR: {
                "description": "创业者,偏好决策支持、风险分析、项目管理等工具",
                "tool_weights": {
                    "decision_engine": 0.95,
                    "risk_analyzer": 0.90,
                    "project_manager": 0.85,
                    "market_analyzer": 0.80,
                    "business_planner": 0.75,
                },
                "intent_preferences": ["work", "coordination", "query"],
                "characteristics": ["冒险精神", "创新思维", "目标导向", "执行力强"],
            },
        }

    def _init_jieba(self) -> Any:
        """初始化jieba分词"""
        # 添加用户行为相关词汇
        user_words = [
            "偏好",
            "习惯",
            "喜欢",
            "经常",
            "总是",
            "通常",
            "倾向",
            "专业",
            "业余",
            "工作",
            "学习",
            "娱乐",
            "生活",
            "家庭",
            "快速",
            "详细",
            "简单",
            "复杂",
            "深入",
            "浅层",
            "全面",
        ]

        for word in user_words:
            jieba.add_word(word, freq=1000)

    def record_interaction(
        self,
        user_id: str,
        intent: str,
        selected_tools: list[str],
        text_input: str,
        success: bool,
        satisfaction_score: float,
        response_time: float,
        context: Optional[dict[str, Any]] = None,
    ):
        """记录用户交互"""
        interaction = UserInteraction(
            user_id=user_id,
            timestamp=datetime.now(),
            intent=intent,
            selected_tools=selected_tools,
            text_input=text_input,
            success=success,
            satisfaction_score=satisfaction_score,
            response_time=response_time,
            context=context or {},
        )

        self.interaction_history[user_id].append(interaction)

        # 更新用户偏好
        self._update_user_preferences(user_id, interaction)

        logger.info(f"📝 记录用户交互: {user_id} - {intent} - 满意度: {satisfaction_score:.2f}")

    def _update_user_preferences(self, user_id: str, interaction: UserInteraction) -> Any:
        """更新用户偏好"""
        # 初始化用户画像(如果不存在)
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(
                user_id=user_id, persona=UserPersona.TECH_EXPERT  # 默认画像
            )

        profile = self.user_profiles[user_id]

        # 更新工具偏好
        for tool in interaction.selected_tools:
            current_pref = profile.tool_preferences.get(tool, 0.5)

            # 基于满意度调整偏好
            if interaction.success:
                new_pref = current_pref + self.config.learning_rate * (
                    interaction.satisfaction_score - current_pref
                )
            else:
                new_pref = max(current_pref - self.config.learning_rate * 0.2, 0.0)

            profile.tool_preferences[tool] = min(new_pref, 1.0)

        # 更新意图-工具模式
        if interaction.intent not in profile.intent_tool_patterns:
            profile.intent_tool_patterns[interaction.intent]] = []

        # 记录成功选择的工具
        if interaction.success:
            for tool in interaction.selected_tools:
                if tool not in profile.intent_tool_patterns[interaction.intent]:
                    profile.intent_tool_patterns[interaction.intent].append(tool)

        # 更新时间模式
        hour = interaction.timestamp.hour
        time_key = f"hour_{hour}"
        profile.time_patterns[time_key] = profile.time_patterns.get(time_key, 0) + 1

        # 更新复杂度偏好
        self._update_complexity_preference(profile, interaction)

        # 更新响应时间偏好
        self._update_response_time_preference(profile, interaction)

        profile.last_updated = datetime.now()

    def _update_complexity_preference(
        self, profile: UserProfile, interaction: UserInteraction
    ) -> Any:
        """更新复杂度偏好"""
        # 基于交互复杂度推断偏好
        text_complexity = len(interaction.text_input.split())
        tool_complexity = sum(
            1
            for tool in interaction.selected_tools
            if "analyzer" in tool or "profiler" in tool or "orchestrator" in tool
        )

        complexity_score = (text_complexity + tool_complexity * 2) / 10
        complexity_score = min(complexity_score, 1.0)

        # 基于满意度调整复杂度偏好
        if interaction.satisfaction_score > 0.7:
            profile.complexity_preference = (
                profile.complexity_preference * 0.8 + complexity_score * 0.2
            )

    def _update_response_time_preference(
        self, profile: UserProfile, interaction: UserInteraction
    ) -> Any:
        """更新响应时间偏好"""
        # 响应时间偏好(0表示偏好快速,1表示偏好慢速细致)
        time_preference = 1.0 - min(interaction.response_time / 10.0, 1.0)

        if interaction.satisfaction_score > 0.7:
            profile.response_time_preference = (
                profile.response_time_preference * 0.8 + time_preference * 0.2
            )

    def infer_user_persona(self, user_id: str) -> UserPersona:
        """推断用户画像"""
        if user_id not in self.user_profiles:
            return UserPersona.TECH_EXPERT

        profile = self.user_profiles[user_id]

        # 如果交互次数太少,返回默认画像
        if len(self.interaction_history[user_id]) < self.config.min_interactions:
            return profile.persona

        # 计算与各画像的相似度
        persona_scores = {}

        for persona, template in self.persona_templates.items():
            score = self._calculate_persona_similarity(profile, template)
            persona_scores[persona] = score

        # 选择最匹配的画像
        best_persona = max(persona_scores.items(), key=lambda x: x[1])

        # 如果分数超过阈值,更新画像
        if best_persona[1] > self.config.preference_threshold:
            profile.persona = best_persona[0]
            logger.info(
                f"🎭 更新用户 {user_id} 画像: {best_persona[0].value} (相似度: {best_persona[1]:.3f})"
            )

        return profile.persona

    def _calculate_persona_similarity(
        self, profile: UserProfile, template: dict[str, Any]]
    ) -> float:
        """计算用户与画像模板的相似度"""
        similarity_score = 0.0
        factor_count = 0

        # 工具偏好相似度
        if profile.tool_preferences and template["tool_weights"]:
            tool_similarity = 0.0
            common_tools = set(profile.tool_preferences.keys()) & set(
                template["tool_weights"].keys()
            )

            if common_tools:
                for tool in common_tools:
                    user_pref = profile.tool_preferences[tool]
                    template_pref = template["tool_weights"][tool]
                    tool_similarity += 1.0 - abs(user_pref - template_pref)

                tool_similarity /= len(common_tools)
                similarity_score += tool_similarity
                factor_count += 1

        # 意图偏好相似度
        if profile.intent_tool_patterns:
            user_intents = set(profile.intent_tool_patterns.keys())
            template_intents = set(template["intent_preferences"])
            intent_similarity = len(user_intents & template_intents) / len(
                user_intents | template_intents
            )

            similarity_score += intent_similarity
            factor_count += 1

        # 复杂度偏好相似度
        if profile.complexity_preference is not None:
            template_complexity = 0.6  # 默认中等复杂度
            complexity_similarity = 1.0 - abs(profile.complexity_preference - template_complexity)
            similarity_score += complexity_similarity
            factor_count += 1

        return similarity_score / factor_count if factor_count > 0 else 0.0

    def get_personalized_tool_suggestions(
        self, user_id: str, intent: str, available_tools: list[str]
    ) -> list[tuple[str, float]]:
        """获取个性化工具建议"""
        if user_id not in self.user_profiles:
            # 新用户,返回平均权重
            return [(tool, 0.5) for tool in available_tools]

        profile = self.user_profiles[user_id]
        tool_scores = []

        for tool in available_tools:
            score = 0.0

            # 用户历史偏好权重
            user_weight = profile.tool_preferences.get(tool, 0.5)
            score += user_weight * 0.4

            # 画像模板权重
            template = self.persona_templates.get(profile.persona, {})
            template_weight = template.get("tool_weights", {}).get(tool, 0.5)
            score += template_weight * 0.3

            # 意图-工具历史模式权重
            intent_tools = profile.intent_tool_patterns.get(intent, [])
            if tool in intent_tools:
                score += 0.3
            elif intent_tools:  # 有历史模式但不在其中
                score += 0.1

            tool_scores.append((tool, min(score, 1.0)))

        # 按分数排序
        tool_scores.sort(key=lambda x: x[1], reverse=True)

        return tool_scores

    def learn_from_feedback(
        self,
        user_id: str,
        tool_name: str,
        success: bool,
        satisfaction: float,
        context: dict[str, Any],    ):
        """从反馈中学习"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(
                user_id=user_id, persona=UserPersona.TECH_EXPERT
            )

        profile = self.user_profiles[user_id]

        # 更新工具偏好
        current_pref = profile.tool_preferences.get(tool_name, 0.5)

        # 基于反馈调整偏好
        if success:
            adjustment = self.config.learning_rate * (satisfaction - current_pref)
        else:
            adjustment = -self.config.learning_rate * (1 - satisfaction) * 0.5

        new_pref = max(0.0, min(1.0, current_pref + adjustment))
        profile.tool_preferences[tool_name] = new_pref

        # 记录学习事件
        logger.info(
            f"🎓 用户偏好学习: {user_id} - {tool_name}: {current_pref:.3f} -> {new_pref:.3f}"
        )

    def train_preference_models(self) -> Any:
        """训练偏好学习模型"""
        logger.info("🚀 开始训练用户偏好学习模型...")

        # 准备训练数据
        training_data = []
        labels = []

        for user_id, interactions in self.interaction_history.items():
            if len(interactions) < self.config.min_interactions:
                continue

            profile = self.user_profiles.get(user_id)
            if not profile:
                continue

            for interaction in interactions:
                # 构建特征向量
                features = self._extract_interaction_features(interaction, profile)
                training_data.append(features)

                # 使用满意度作为标签
                label = 1 if interaction.satisfaction_score > 0.7 else 0
                labels.append(label)

        if len(training_data) == 0:
            logger.warning("⚠️ 没有足够的训练数据")
            return

        # 转换为numpy数组
        X = np.array(training_data)
        y = np.array(labels)

        # 特征缩放
        self.feature_scaler = StandardScaler()
        X_scaled = self.feature_scaler.fit_transform(X)

        # 训练分类器
        self.preference_classifier = RandomForestClassifier(
            n_estimators=100, max_depth=10, random_state=42
        )

        self.preference_classifier.fit(X_scaled, y)

        logger.info(f"✅ 偏好学习模型训练完成,样本数: {len(training_data)}")

    def _extract_interaction_features(
        self, interaction: UserInteraction, profile: UserProfile
    ) -> list[float]:
        """提取交互特征"""
        features = []

        # 基础特征
        features.append(len(interaction.text_input.split()))  # 文本长度
        features.append(len(interaction.selected_tools))  # 工具数量
        features.append(1 if interaction.success else 0)  # 是否成功
        features.append(interaction.response_time)  # 响应时间

        # 时间特征
        features.append(interaction.timestamp.hour / 24.0)  # 小时(归一化)
        features.append(interaction.timestamp.weekday() / 7.0)  # 星期(归一化)

        # 用户画像特征
        features.append(profile.complexity_preference or 0.5)
        features.append(profile.response_time_preference or 0.5)

        # 工具偏好特征
        tool_prefs = [
            profile.tool_preferences.get(tool, 0.5)
            for tool in ["code_analyzer", "chat_companion", "web_search"]
        ]
        features.extend(tool_prefs)

        return features

    def analyze_user_behavior(self, user_id: str) -> dict[str, Any]:
        """分析用户行为"""
        if user_id not in self.user_profiles:
            return {"error": "用户不存在"}

        profile = self.user_profiles[user_id]
        interactions = self.interaction_history.get(user_id, [])

        if not interactions:
            return {"error": "没有交互记录"}

        # 统计分析
        analysis = {
            "user_id": user_id,
            "persona": profile.persona.value,
            "total_interactions": len(interactions),
            "success_rate": sum(1 for i in interactions if i.success) / len(interactions),
            "avg_satisfaction": np.mean([i.satisfaction_score for i in interactions]),
            "avg_response_time": np.mean([i.response_time for i in interactions]),
            "most_used_tools": self._get_most_used_tools(interactions),
            "preferred_intents": self._get_preferred_intents(interactions),
            "time_patterns": self._analyze_time_patterns(interactions),
            "learning_progress": self._calculate_learning_progress(user_id),
        }

        return analysis

    def _get_most_used_tools(self, interactions: list[UserInteraction]) -> list[tuple[str, int]]:
        """获取最常用工具"""
        tool_counts = defaultdict(int)
        for interaction in interactions:
            for tool in interaction.selected_tools:
                tool_counts[tool] += 1

        return sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    def _get_preferred_intents(self, interactions: list[UserInteraction]) -> list[tuple[str, int]]:
        """获取偏好意图"""
        intent_counts = defaultdict(int)
        for interaction in interactions:
            intent_counts[interaction.intent] += 1

        return sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)

    def _analyze_time_patterns(self, interactions: list[UserInteraction]) -> dict[str, Any]:
        """分析时间模式"""
        hours = [i.timestamp.hour for i in interactions]
        weekdays = [i.timestamp.weekday() for i in interactions]

        return {
            "peak_hour": max(set(hours), key=hours.count),
            "peak_weekday": max(set(weekdays), key=weekdays.count),
            "avg_interactions_per_hour": len(hours) / 24.0,
        }

    def _calculate_learning_progress(self, user_id: str) -> float:
        """计算学习进度"""
        interactions = self.interaction_history.get(user_id, [])
        if len(interactions) < 10:
            return 0.0

        # 比较最近10次和前10次的满意度
        recent_interactions = interactions[-10:]
        earlier_interactions = interactions[-20:-10] if len(interactions) >= 20 else []

        if earlier_interactions:
            recent_avg = np.mean([i.satisfaction_score for i in recent_interactions])
            earlier_avg = np.mean([i.satisfaction_score for i in earlier_interactions])

            progress = (recent_avg - earlier_avg) * 10  # 放大进度
            return max(0.0, min(1.0, progress))

        return 0.5  # 默认中等进度

    def save_models(self) -> None:
        """保存模型"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = os.path.join(self.config.model_dir, f"preference_models_{timestamp}.joblib")

        model_data = {
            "user_profiles": self.user_profiles,
            "interaction_history": dict(self.interaction_history),
            "preference_classifier": self.preference_classifier,
            "feature_scaler": self.feature_scaler,
            "config": self.config,
        }

        # 安全修复: 使用joblib替代pickle
        joblib.dump(model_data, model_path)

        # 保存最新模型
        latest_path = os.path.join(self.config.model_dir, "latest_preference_models.joblib")
        joblib.dump(model_data, latest_path)

        logger.info(f"💾 用户偏好学习模型已保存: {model_path}")

    def load_models(self, model_path: Optional[str] = None) -> Optional[Any]:
        """加载模型"""
        if model_path is None:
            model_path = os.path.join(self.config.model_dir, "latest_preference_models.joblib")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")

        # 安全修复: 使用joblib替代pickle
        model_data = joblib.load(model_path)

        self.user_profiles = model_data["user_profiles"]
        self.interaction_history = defaultdict(list, model_data["interaction_history"])
        self.preference_classifier = model_data.get("preference_classifier")
        self.feature_scaler = model_data.get("feature_scaler")
        self.config = model_data["config"]

        logger.info(f"✅ 用户偏好学习模型已加载: {model_path}")


def main() -> None:
    """主函数"""
    logger.info("👤 小诺用户偏好学习器测试开始")

    # 创建配置
    config = PreferenceConfig()

    # 创建偏好学习器
    preference_learner = XiaonuoUserPreferenceLearner(config)

    # 模拟用户交互
    try:
        # 模拟爸爸的交互行为
        user_id = "dad"

        # 技术类交互
        preference_learner.record_interaction(
            user_id=user_id,
            intent="technical",
            selected_tools=["code_analyzer"],
            text_input="帮我分析这段Python代码",
            success=True,
            satisfaction_score=0.9,
            response_time=2.5,
        )

        preference_learner.record_interaction(
            user_id=user_id,
            intent="technical",
            selected_tools=["performance_profiler"],
            text_input="程序性能太慢了",
            success=True,
            satisfaction_score=0.8,
            response_time=3.0,
        )

        # 情感类交互
        preference_learner.record_interaction(
            user_id=user_id,
            intent="emotional",
            selected_tools=["chat_companion"],
            text_input="今天工作很累,想聊聊",
            success=True,
            satisfaction_score=0.95,
            response_time=1.2,
        )

        # 家庭类交互
        preference_learner.record_interaction(
            user_id=user_id,
            intent="family",
            selected_tools=["emotional_support"],
            text_input="想念家人了",
            success=True,
            satisfaction_score=0.9,
            response_time=1.0,
        )

        # 推断用户画像
        persona = preference_learner.infer_user_persona(user_id)
        logger.info(f"🎭 推断的用户画像: {persona.value}")

        # 获取个性化建议
        suggestions = preference_learner.get_personalized_tool_suggestions(
            user_id=user_id,
            intent="technical",
            available_tools=["code_analyzer", "chat_companion", "web_search", "emotional_support"],
        )
        logger.info("💡 个性化工具建议:")
        for tool, score in suggestions:
            logger.info(f"  - {tool}: {score:.3f}")

        # 从反馈学习
        preference_learner.learn_from_feedback(
            user_id=user_id,
            tool_name="code_analyzer",
            success=True,
            satisfaction=0.85,
            context={"task_type": "analysis"},
        )

        # 分析用户行为
        behavior_analysis = preference_learner.analyze_user_behavior(user_id)
        logger.info("\n📊 用户行为分析:")
        for key, value in behavior_analysis.items():
            if key != "user_id":
                logger.info(f"  {key}: {value}")

        # 训练偏好模型
        preference_learner.train_preference_models()

        # 保存模型
        preference_learner.save_models()

        logger.info("🎉 用户偏好学习测试完成!")

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

