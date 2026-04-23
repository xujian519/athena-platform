from __future__ import annotations
"""
维特根斯坦逻辑哲学守护 - AI防幻觉核心模块
Wittgensteinian Logic Philosophy Guardian - Anti-Hallucination Core

基于维特根斯坦《哲学研究》的核心概念:
- 语言游戏 (Language Games, PI §23)
- 意义即使用 (Meaning as Use, PI §43)
- 家族相似性 (Family Resemblances, PI §§65-71)
- 私人语言不可能性 (Impossibility of Private Language, PI §§243-315)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ConfidenceLevel(Enum):
    """置信度等级"""

    CRITICAL = 0.95  # 关键:医疗、安全等
    HIGH = 0.85  # 高:专业建议
    MEDIUM = 0.70  # 中:常规问答
    LOW = 0.50  # 低:探索性
    SPECULATIVE = 0.30  # 推测性


class PatternType(Enum):
    """模式类型"""

    STRICT = "strict"  # 严格匹配
    FUZZY = "fuzzy"  # 模糊匹配
    LEARNED = "learned"  # 学习获得
    CONTEXT_SENSITIVE = "context_sensitive"  # 上下文敏感


@dataclass
class GamePattern:
    """语言游戏模式"""

    pattern_id: str
    text: str  # 模式文本
    pattern_type: PatternType  # 模式类型
    confidence_level: ConfidenceLevel  # 置信度要求
    examples: list[str] = field(default_factory=list)  # 示例
    metadata: dict[str, Any] = field(default_factory=dict)

    def matches(self, query: str, similarity_threshold: float = 0.8) -> tuple[bool, float]:
        """检查查询是否匹配此模式"""
        if self.pattern_type == PatternType.STRICT:
            # 严格匹配
            match = self.text.lower() in query.lower()
            return match, 1.0 if match else 0.0

        elif self.pattern_type == PatternType.FUZZY:
            # 模糊匹配 - 简化版,实际应使用语义相似度
            words_query = set(query.lower().split())
            words_pattern = set(self.text.lower().split())
            intersection = words_query.intersection(words_pattern)
            union = words_query.union(words_pattern)
            similarity = len(intersection) / len(union) if union else 0.0
            return similarity >= similarity_threshold, similarity

        elif self.pattern_type == PatternType.CONTEXT_SENSITIVE:
            # 上下文敏感 - 需要外部计算
            return False, 0.0

        return False, 0.0


@dataclass
class LanguageGame:
    """语言游戏

    定义一个有边界的对话领域,如专利检索、医疗分诊、法律咨询等
    """

    game_id: str
    name: str
    description: str
    domain: str  # 领域:patent, medical, legal等
    patterns: list[GamePattern] = field(default_factory=list)
    confidence_threshold: float = 0.7  # 默认置信度阈值
    uncertainty_strategy: str = "negotiate"  # negotiate, escalate, refuse
    escalation_path: Optional[str] = None
    capabilities: list[str] = field(default_factory=list)  # 可调用的能力
    metadata: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

    def add_pattern(self, pattern: GamePattern) -> None:
        """添加模式"""
        self.patterns.append(pattern)

    def evaluate_query(self, query: str) -> dict[str, Any]:
        """评估查询是否在游戏范围内"""
        if not self.enabled:
            return {"in_scope": False, "reason": "游戏未启用", "confidence": 0.0}

        best_match = None
        best_confidence = 0.0

        for pattern in self.patterns:
            matches, confidence = pattern.matches(query)
            if matches and confidence > best_confidence:
                best_match = pattern
                best_confidence = confidence

        # 检查是否达到阈值
        in_scope = best_confidence >= self.confidence_threshold

        return {
            "in_scope": in_scope,
            "confidence": best_confidence,
            "threshold": self.confidence_threshold,
            "matched_pattern": best_match.pattern_id if best_match else None,
            "action": self.uncertainty_strategy if not in_scope else "proceed",
            "escalation_path": self.escalation_path if not in_scope else None,
        }


class WittgensteinGuard:
    """维特根斯坦守护

    防止AI幻觉的核心模块,基于语言游戏理论
    """

    def __init__(self):
        self.language_games: dict[str, LanguageGame] = {}
        self.global_confidence_threshold = 0.7
        self.default_uncertainty_strategy = "negotiate"
        self._register_default_games()

    def _register_default_games(self) -> Any:
        """注册默认语言游戏"""

        # 1. 专利检索游戏
        patent_game = LanguageGame(
            game_id="patent_search",
            name="专利检索语言游戏",
            description="处理专利检索、分析、无效宣告相关问题",
            domain="patent",
            confidence_threshold=0.75,
            uncertainty_strategy="negotiate",
            escalation_path="human_patent_attorney",
            capabilities=[
                "search_patents",
                "analyze_claims",
                "compare_prior_art",
                "assess_novelty",
            ],
        )

        patent_game.add_pattern(
            GamePattern(
                pattern_id="search_query",
                text="检索专利",
                pattern_type=PatternType.FUZZY,
                confidence_level=ConfidenceLevel.HIGH,
                examples=["搜索专利", "检索专利", "找相关专利", "现有技术检索"],
            )
        )

        patent_game.add_pattern(
            GamePattern(
                pattern_id="invalidity_analysis",
                text="无效宣告",
                pattern_type=PatternType.FUZZY,
                confidence_level=ConfidenceLevel.CRITICAL,
                examples=["无效分析", "无效宣告", "专利无效", "宣告无效"],
            )
        )

        patent_game.add_pattern(
            GamePattern(
                pattern_id="claim_analysis",
                text="权利要求分析",
                pattern_type=PatternType.FUZZY,
                confidence_level=ConfidenceLevel.HIGH,
                examples=["分析权利要求", "权利要求解释", "保护范围"],
            )
        )

        self.language_games["patent_search"] = patent_game

        # 2. 医疗分诊游戏
        medical_game = LanguageGame(
            game_id="medical_triage",
            name="医疗分诊语言游戏",
            description="医疗症状评估和分诊",
            domain="medical",
            confidence_threshold=0.85,  # 更高阈值
            uncertainty_strategy="escalate",  # 不确定时立即升级
            escalation_path="human_medical_professional",
            capabilities=[
                "assess_symptoms",
                "measure_vitals",
                "notify_physician",
                "provide_general_info",
            ],
        )

        medical_game.add_pattern(
            GamePattern(
                pattern_id="chest_pain",
                text="胸痛",
                pattern_type=PatternType.FUZZY,
                confidence_level=ConfidenceLevel.CRITICAL,
                examples=["胸痛", "胸口疼", "心前区疼痛", "胸闷"],
            )
        )

        medical_game.add_pattern(
            GamePattern(
                pattern_id="breathing_difficulty",
                text="呼吸困难",
                pattern_type=PatternType.FUZZY,
                confidence_level=ConfidenceLevel.CRITICAL,
                examples=["呼吸困难", "喘不上气", "呼吸急促", "无法呼吸"],
            )
        )

        self.language_games["medical_triage"] = medical_game

        # 3. 法律咨询游戏
        legal_game = LanguageGame(
            game_id="legal_consultation",
            name="法律咨询语言游戏",
            description="一般法律问题咨询",
            domain="legal",
            confidence_threshold=0.75,
            uncertainty_strategy="negotiate",
            escalation_path="human_attorney",
            capabilities=["provide_general_info", "explain_concepts", "suggest_resources"],
        )

        legal_game.add_pattern(
            GamePattern(
                pattern_id="legal_question",
                text="法律问题",
                pattern_type=PatternType.FUZZY,
                confidence_level=ConfidenceLevel.HIGH,
                examples=["法律咨询", "法律问题", "是否违法", "法律责任"],
            )
        )

        self.language_games["legal_consultation"] = legal_game

        # 4. 通用对话游戏
        general_game = LanguageGame(
            game_id="general_conversation",
            name="通用对话语言游戏",
            description="日常对话和一般性问题",
            domain="general",
            confidence_threshold=0.60,  # 较低阈值
            uncertainty_strategy="negotiate",
            capabilities=["general_response"],
        )

        general_game.add_pattern(
            GamePattern(
                pattern_id="greeting",
                text="你好",
                pattern_type=PatternType.STRICT,
                confidence_level=ConfidenceLevel.MEDIUM,
                examples=["你好", "您好", "hi", "hello"],
            )
        )

        self.language_games["general_conversation"] = general_game

    def register_game(self, game: LanguageGame) -> Any:
        """注册新的语言游戏"""
        self.language_games[game.game_id] = game

    def get_game(self, game_id: str) -> LanguageGame | None:
        """获取指定语言游戏"""
        return self.language_games.get(game_id)

    def list_games(self) -> list[str]:
        """列出所有语言游戏"""
        return list(self.language_games.keys())

    def evaluate_query(self, query: str, game_id: Optional[str] = None) -> dict[str, Any]:
        """评估查询

        Args:
            query: 用户查询
            game_id: 指定的语言游戏ID,如果为None则自动检测

        Returns:
            评估结果字典
        """
        if game_id:
            # 使用指定的游戏
            game = self.language_games.get(game_id)
            if not game:
                return {
                    "valid": False,
                    "reason": f"语言游戏不存在: {game_id}",
                    "action": "escalate",
                    "confidence": 0.0,
                }
            return game.evaluate_query(query)

        # 自动检测游戏
        best_game = None
        best_result = None
        best_confidence = 0.0

        for game in self.language_games.values():
            if not game.enabled:
                continue

            result = game.evaluate_query(query)
            if result["confidence"] > best_confidence:
                best_confidence = result["confidence"]
                best_game = game
                best_result = result

        # 修复None引用风险:同时检查best_game和best_result
        if best_game and best_result is not None:
            best_result["game_id"] = best_game.game_id
            best_result["game_name"] = best_game.name
            return best_result

        # 没有匹配的游戏
        return {
            "valid": False,
            "reason": "查询不在任何已注册的语言游戏范围内",
            "action": "negotiate",
            "confidence": 0.0,
            "suggestion": "请澄清您的需求或选择合适的对话领域",
        }

    def check_epistemic_honesty(
        self, claim: str, confidence: float, threshold: Optional[float] = None
    ) -> dict[str, Any]:
        """检查认识论诚实

        根据维特根斯坦的"公共正确性标准"判断主张是否诚实
        """
        if threshold is None:
            threshold = self.global_confidence_threshold

        if confidence < threshold:
            return {
                "honest": False,
                "confidence": confidence,
                "threshold": threshold,
                "action": "express_uncertainty",
                "message": f"我不确定(置信度:{confidence:.1%}),建议:",
            }

        return {
            "honest": True,
            "confidence": confidence,
            "threshold": threshold,
            "action": "proceed",
        }

    def suggest_negotiation(self, query: str, evaluation: dict[str, Any]) -> str:
        """建议协商策略"""
        action = evaluation.get("action", "negotiate")

        if action == "escalate":
            path = evaluation.get("escalation_path", "human_expert")
            return f"我需要将您的问题升级给{path}。您的需求超出了我的能力范围。"

        elif action == "negotiate":
            game_id = evaluation.get("game_id")
            game = self.language_games.get(game_id) if game_id else None

            if game and game.patterns:
                examples = []
                for pattern in game.patterns[:3]:
                    examples.extend(pattern.examples[:2])

                return "我不太确定您的需求。您是否想了解:\n" + "\n".join(
                    [f"- {ex}" for ex in examples[:5]]
                )

        return "我不太理解您的需求。能否用更具体的方式描述?"

    def detect_family_resemblance(self, query: str, concept: str, examples: list[str]) -> float:
        """检测家族相似性

        计算查询与概念示例之间的相似度
        """
        # 简化版实现
        query_words = set(query.lower().split())
        similarities = []

        for example in examples:
            example_words = set(example.lower().split())
            intersection = query_words.intersection(example_words)
            union = query_words.union(example_words)
            similarity = len(intersection) / len(union) if union else 0.0
            similarities.append(similarity)

        return max(similarities) if similarities else 0.0

    def get_status(self) -> dict[str, Any]:
        """获取守护状态"""
        return {
            "total_games": len(self.language_games),
            "enabled_games": len([g for g in self.language_games.values() if g.enabled]),
            "games": [
                {
                    "id": g.game_id,
                    "name": g.name,
                    "domain": g.domain,
                    "enabled": g.enabled,
                    "patterns_count": len(g.patterns),
                    "threshold": g.confidence_threshold,
                }
                for g in self.language_games.values()
            ],
        }


# 便捷函数
def create_wittgenstein_guard() -> WittgensteinGuard:
    """创建维特根斯坦守护实例"""
    return WittgensteinGuard()
