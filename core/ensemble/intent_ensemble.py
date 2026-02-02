#!/usr/bin/env python3
"""
意图识别集成器 - 第二阶段
Intent Recognition Ensemble - Phase 2

核心功能:
1. 多模型意图识别集成
2. 动态权重调整
3. 置信度校准
4. 意图冲突解决

作者: 小诺·双鱼公主
版本: v1.0.0 "意图集成"
创建: 2026-01-12
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


logger = logging.getLogger(__name__)


class IntentModel(Enum):
    """意图模型类型"""

    BERT = "bert"  # BERT分类器
    BGE = "bge"  # BGE向量相似度
    RULES = "rules"  # 规则匹配
    KEYWORD = "keyword"  # 关键词匹配
    ENSEMBLE = "ensemble"  # 集成模型


@dataclass
class IntentPrediction:
    """意图预测结果"""

    model: IntentModel
    intent: str
    confidence: float
    logits: dict[str, float] | None = None  # 所有类别的概率
    reasoning: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class IntentEnsembleResult:
    """意图集成结果"""

    final_intent: str
    confidence: float
    method: str
    model_predictions: list[IntentPrediction]
    model_weights: dict[str, float]
    voting_distribution: dict[str, int]  # 投票分布
    confidence_calibration: float  # 置信度校准
    reasoning: str
    conflicts_resolved: list[str]  # 已解决的冲突


@dataclass
class IntentConflict:
    """意图冲突"""

    conflict_id: str
    conflicting_intents: list[str]
    conflicting_models: list[IntentModel]
    confidence_gap: float  # 置信度差距
    resolution_strategy: str
    resolution: str


class IntentEnsemble:
    """意图识别集成器"""

    def __init__(self):
        self.name = "意图识别集成器 v1.0"
        self.version = "1.0.0"

        # 模型注册表
        self.models: dict[IntentModel, Any] = {}

        # 模型权重(动态调整)
        self.model_weights: dict[str, float] = {
            "bert": 0.35,
            "bge": 0.35,
            "rules": 0.20,
            "keyword": 0.10,
        }

        # 模型性能历史
        self.model_performance: dict[str, list[float]] = defaultdict(list)

        # 意图冲突历史
        self.conflict_history: list[IntentConflict] = []

        # 意图映射表(标准化)
        self.intent_mapping = self._init_intent_mapping()

        # 置信度阈值
        self.confidence_threshold = 0.70

        # 统计信息
        self.stats = {
            "total_predictions": 0,
            "high_confidence": 0,
            "low_confidence": 0,
            "conflicts_detected": 0,
            "conflicts_resolved": 0,
            "ensemble_accuracy": 0.0,
        }

        logger.info(f"🎯 {self.name} 初始化完成")

    def _init_intent_mapping(self) -> dict[str, str]:
        """初始化意图映射表"""
        return {
            # 专利相关
            "patent_search": "patent_analysis",
            "patent_query": "patent_analysis",
            "patent_retrieval": "patent_analysis",
            "patent_analysis": "patent_analysis",
            # 编程相关
            "code_generation": "coding",
            "coding_assistant": "coding",
            "programming": "coding",
            "debug": "coding",
            "coding": "coding",
            # 闲聊相关
            "chat": "daily_chat",
            "greeting": "daily_chat",
            "casual_conversation": "daily_chat",
            "daily_chat": "daily_chat",
            # 法律相关
            "legal_query": "legal_consulting",
            "legal_advice": "legal_consulting",
            "law_query": "legal_consulting",
            "legal_consulting": "legal_consulting",
            # 数据分析
            "data_analysis": "data_analysis",
            "statistics": "data_analysis",
            "analytics": "data_analysis",
        }

    async def predict(
        self, text: str, context: dict[str, Any] | None = None, method: str = "weighted_voting"
    ) -> IntentEnsembleResult:
        """
        执行意图识别集成预测

        Args:
            text: 输入文本
            context: 上下文信息
            method: 集成方法 (weighted_voting, stacking, dynamic)

        Returns:
            IntentEnsembleResult: 集成结果
        """
        # 1. 获取各模型预测
        individual_predictions = await self._get_individual_predictions(text, context)

        # 2. 检测冲突
        conflicts = self._detect_conflicts(individual_predictions)
        if conflicts:
            self.stats["conflicts_detected"] += len(conflicts)

        # 3. 根据方法集成
        if method == "weighted_voting":
            result = self._weighted_voting_ensemble(individual_predictions)
        elif method == "stacking":
            result = self._stacking_ensemble(individual_predictions, text, context)
        elif method == "dynamic":
            result = self._dynamic_ensemble(individual_predictions, text, context)
        else:
            result = self._weighted_voting_ensemble(individual_predictions)

        # 4. 解决冲突
        if conflicts:
            result = self._resolve_conflicts(result, conflicts)

        # 5. 置信度校准
        result.confidence_calibration = self._calibrate_confidence(result)

        # 6. 更新统计
        self._update_stats(result)

        return result

    async def _get_individual_predictions(
        self, text: str, context: dict[str, Any]
    ) -> list[IntentPrediction]:
        """获取各模型的预测"""
        predictions = []

        # 1. BERT模型预测
        bert_pred = await self._bert_predict(text, context)
        if bert_pred:
            predictions.append(bert_pred)

        # 2. BGE模型预测
        bge_pred = await self._bge_predict(text, context)
        if bge_pred:
            predictions.append(bge_pred)

        # 3. 规则模型预测
        rules_pred = await self._rules_predict(text, context)
        if rules_pred:
            predictions.append(rules_pred)

        # 4. 关键词模型预测
        keyword_pred = await self._keyword_predict(text, context)
        if keyword_pred:
            predictions.append(keyword_pred)

        return predictions

    async def _bert_predict(
        self, text: str, context: dict[str, Any]
    ) -> IntentPrediction | None:
        """BERT模型预测"""
        try:
            # 模拟BERT预测
            # 实际应该调用: self.models[IntentModel.BERT].predict(text)

            # 基于文本特征的简化预测
            if any(kw in text.lower() for kw in ["专利", "申请", "公开号"]):
                intent = "patent_analysis"
                confidence = 0.95
            elif any(kw in text.lower() for kw in ["代码", "函数", "编程", "开发"]):
                intent = "coding"
                confidence = 0.92
            elif any(kw in text.lower() for kw in ["你好", "嗨", "在吗"]):
                intent = "daily_chat"
                confidence = 0.90
            elif any(kw in text.lower() for kw in ["法律", "法规", "侵权"]):
                intent = "legal_consulting"
                confidence = 0.88
            else:
                intent = "daily_chat"
                confidence = 0.75

            # 生成模拟的logits
            all_intents = [
                "patent_analysis",
                "coding",
                "daily_chat",
                "legal_consulting",
                "data_analysis",
            ]
            logits = {intent: np.random.rand() * 0.3 for intent in all_intents}
            logits[intent] = confidence

            return IntentPrediction(
                model=IntentModel.BERT,
                intent=intent,
                confidence=confidence,
                logits=logits,
                reasoning="BERT分类器基于语义理解",
                metadata={"model_version": "bert-base-chinese"},
            )

        except Exception as e:
            logger.error(f"❌ BERT预测失败: {e}")
            return None

    async def _bge_predict(
        self, text: str, context: dict[str, Any]
    ) -> IntentPrediction | None:
        """BGE模型预测(向量相似度)"""
        try:
            # 模拟BGE预测
            # 实际应该调用: self.models[IntentModel.BGE].predict(text)

            # 简化的向量相似度匹配
            intent_templates = {
                "patent_analysis": ["帮我查专利", "专利分析", "检索专利"],
                "coding": ["写代码", "开发功能", "编程帮助"],
                "daily_chat": ["你好", "在吗", "介绍一下"],
                "legal_consulting": ["法律咨询", "法规查询", "侵权分析"],
            }

            # 计算相似度(简化)
            max_similarity = 0.0
            best_intent = "daily_chat"

            for intent, templates in intent_templates.items():
                for template in templates:
                    # 简化的相似度计算
                    similarity = len(set(text) & set(template)) / max(len(text), len(template))
                    if similarity > max_similarity:
                        max_similarity = similarity
                        best_intent = intent

            confidence = min(0.98, max_similarity * 2 + 0.5)

            return IntentPrediction(
                model=IntentModel.BGE,
                intent=best_intent,
                confidence=confidence,
                reasoning=f"BGE向量相似度匹配,最高相似度: {max_similarity:.2f}",
                metadata={"similarity_score": max_similarity},
            )

        except Exception as e:
            logger.error(f"❌ BGE预测失败: {e}")
            return None

    async def _rules_predict(
        self, text: str, context: dict[str, Any]
    ) -> IntentPrediction | None:
        """规则模型预测"""
        try:
            # 定义规则
            rules = [
                # 专利分析规则
                {
                    "intent": "patent_analysis",
                    "patterns": [
                        r"专利.*?(查询|检索|分析|搜索)",
                        r"申请号.*?查询",
                        r"公开号.*?查询",
                    ],
                    "weight": 1.0,
                },
                # 编程规则
                {
                    "intent": "coding",
                    "patterns": [r"(写|生成|开发).+?代码", r"实现.+?功能", r"编程.*?(帮助|助手)"],
                    "weight": 1.0,
                },
                # 闲聊规则
                {
                    "intent": "daily_chat",
                    "patterns": [r"^(你好|嗨|hi|hello)", r"(在吗|在不在)", r"介绍.*?你自己"],
                    "weight": 0.9,
                },
                # 法律咨询规则
                {
                    "intent": "legal_consulting",
                    "patterns": [
                        r"法律.*?(咨询|查询|建议)",
                        r"(法规|法条).+?(查询|解释)",
                        r"侵权.*?(分析|判定)",
                    ],
                    "weight": 1.0,
                },
            ]

            import re

            best_match = None
            best_score = 0.0

            for rule in rules:
                for pattern in rule["patterns"]:
                    if re.search(pattern, text, re.IGNORECASE):
                        score = rule["weight"]
                        if score > best_score:
                            best_score = score
                            best_match = rule

            if best_match:
                return IntentPrediction(
                    model=IntentModel.RULES,
                    intent=best_match["intent"],
                    confidence=best_score,
                    reasoning=f"规则匹配: {best_match['intent']}",
                    metadata={"matched_rule": best_match["intent"]},
                )

            # 默认返回闲聊
            return IntentPrediction(
                model=IntentModel.RULES,
                intent="daily_chat",
                confidence=0.5,
                reasoning="无明确规则匹配,默认闲聊",
                metadata={"matched_rule": "default"},
            )

        except Exception as e:
            logger.error(f"❌ 规则预测失败: {e}")
            return None

    async def _keyword_predict(
        self, text: str, context: dict[str, Any]
    ) -> IntentPrediction | None:
        """关键词模型预测"""
        try:
            # 定义关键词
            keyword_intents = {
                "patent_analysis": ["专利", "申请号", "公开号", "发明", "实用新型"],
                "coding": ["代码", "函数", "编程", "开发", "调试", "算法"],
                "daily_chat": ["你好", "嗨", "聊天", "介绍", "帮助"],
                "legal_consulting": ["法律", "法规", "侵权", "诉讼", "判决"],
                "data_analysis": ["分析", "统计", "数据", "图表", "报告"],
            }

            # 统计关键词出现
            intent_scores = {}
            for intent, keywords in keyword_intents.items():
                score = sum(1 for kw in keywords if kw in text)
                if score > 0:
                    intent_scores[intent] = score

            if intent_scores:
                best_intent = max(intent_scores, key=intent_scores.get)
                confidence = min(0.95, 0.5 + intent_scores[best_intent] * 0.1)

                return IntentPrediction(
                    model=IntentModel.KEYWORD,
                    intent=best_intent,
                    confidence=confidence,
                    reasoning=f"关键词匹配: {list(intent_scores.items())}",
                    metadata={"keyword_scores": intent_scores},
                )

            return None

        except Exception as e:
            logger.error(f"❌ 关键词预测失败: {e}")
            return None

    def _weighted_voting_ensemble(
        self, predictions: list[IntentPrediction]
    ) -> IntentEnsembleResult:
        """加权投票集成"""
        # 标准化意图
        intent_votes = defaultdict(float)
        intent_details = defaultdict(list)

        for pred in predictions:
            # 标准化意图
            normalized_intent = self.intent_mapping.get(pred.intent, pred.intent)

            # 加权投票
            weight = self.model_weights.get(pred.model.value, 0.25)
            weighted_score = pred.confidence * weight

            intent_votes[normalized_intent] += weighted_score
            intent_details[normalized_intent].append(pred.model.value)

        # 选择最高分意图
        if not intent_votes:
            final_intent = "daily_chat"
            confidence = 0.5
        else:
            final_intent = max(intent_votes, key=intent_votes.get)
            confidence = min(0.98, intent_votes[final_intent])

        # 投票分布
        voting_distribution = {intent: int(vote * 100) for intent, vote in intent_votes.items()}

        return IntentEnsembleResult(
            final_intent=final_intent,
            confidence=confidence,
            method="weighted_voting",
            model_predictions=predictions,
            model_weights=self.model_weights.copy(),
            voting_distribution=voting_distribution,
            confidence_calibration=0.0,
            reasoning=f"加权投票: {dict(intent_votes)}",
            conflicts_resolved=[],
        )

    def _stacking_ensemble(
        self, predictions: list[IntentPrediction], text: str, context: dict[str, Any]
    ) -> IntentEnsembleResult:
        """堆叠集成"""
        # 简化实现: 使用元模型
        # 实际应该训练一个元模型

        # 收集所有预测的特征
        features = []
        for pred in predictions:
            features.append(
                [
                    pred.confidence,
                    self.model_weights.get(pred.model.value, 0.25),
                    len(pred.reasoning),
                ]
            )

        if not features:
            return IntentEnsembleResult(
                final_intent="daily_chat",
                confidence=0.5,
                method="stacking",
                model_predictions=predictions,
                model_weights=self.model_weights.copy(),
                voting_distribution={},
                confidence_calibration=0.0,
                reasoning="无有效预测",
                conflicts_resolved=[],
            )

        # 简化的元模型: 选择置信度最高的
        best_pred = max(predictions, key=lambda p: p.confidence)
        final_intent = self.intent_mapping.get(best_pred.intent, best_pred.intent)

        return IntentEnsembleResult(
            final_intent=final_intent,
            confidence=best_pred.confidence,
            method="stacking",
            model_predictions=predictions,
            model_weights=self.model_weights.copy(),
            voting_distribution={},
            confidence_calibration=0.0,
            reasoning=f"堆叠集成: 选择{best_pred.model.value}的预测",
            conflicts_resolved=[],
        )

    def _dynamic_ensemble(
        self, predictions: list[IntentPrediction], text: str, context: dict[str, Any]
    ) -> IntentEnsembleResult:
        """动态集成"""
        # 基于历史性能动态调整权重
        dynamic_weights = self._get_dynamic_weights()

        # 使用动态权重
        intent_scores = defaultdict(float)
        for pred in predictions:
            normalized_intent = self.intent_mapping.get(pred.intent, pred.intent)
            weight = dynamic_weights.get(pred.model.value, 0.25)
            intent_scores[normalized_intent] += pred.confidence * weight

        final_intent = max(intent_scores, key=intent_scores.get) if intent_scores else "daily_chat"
        confidence = min(0.98, intent_scores[final_intent]) if intent_scores else 0.5

        return IntentEnsembleResult(
            final_intent=final_intent,
            confidence=confidence,
            method="dynamic",
            model_predictions=predictions,
            model_weights=dynamic_weights,
            voting_distribution={},
            confidence_calibration=0.0,
            reasoning=f"动态集成: 权重={dynamic_weights}",
            conflicts_resolved=[],
        )

    def _get_dynamic_weights(self) -> dict[str, float]:
        """获取动态权重"""
        dynamic_weights = self.model_weights.copy()

        # 基于历史性能调整
        for model_name, perf_history in self.model_performance.items():
            if len(perf_history) >= 10:
                recent_perf = perf_history[-10:]
                avg_perf = sum(recent_perf) / len(recent_perf)

                if avg_perf > 0.95:
                    dynamic_weights[model_name] *= 1.2
                elif avg_perf < 0.80:
                    dynamic_weights[model_name] *= 0.8

        # 归一化
        total = sum(dynamic_weights.values())
        dynamic_weights = {k: v / total for k, v in dynamic_weights.items()}

        return dynamic_weights

    def _detect_conflicts(self, predictions: list[IntentPrediction]) -> list[IntentConflict]:
        """检测意图冲突"""
        if len(predictions) < 2:
            return []

        conflicts = []
        intent_groups = defaultdict(list)

        # 按意图分组
        for pred in predictions:
            normalized_intent = self.intent_mapping.get(pred.intent, pred.intent)
            intent_groups[normalized_intent].append(pred)

        # 检测冲突: 多个不同意图且置信度接近
        if len(intent_groups) > 1:
            confidences = [
                (intent, max(p.confidence for p in preds))
                for intent, preds in intent_groups.items()
            ]
            confidences.sort(key=lambda x: x[1], reverse=True)

            if len(confidences) >= 2:
                top_intent, top_conf = confidences[0]
                second_intent, second_conf = confidences[1]
                gap = top_conf - second_conf

                # 如果置信度差距小于0.15,认为存在冲突
                if gap < 0.15 and top_conf > 0.7:
                    conflict = IntentConflict(
                        conflict_id=f"conflict_{datetime.now().timestamp()}",
                        conflicting_intents=[top_intent, second_intent],
                        conflicting_models=[p.model for p in predictions],
                        confidence_gap=gap,
                        resolution_strategy="weighted_voting",
                        resolution="",
                    )
                    conflicts.append(conflict)

        return conflicts

    def _resolve_conflicts(
        self, result: IntentEnsembleResult, conflicts: list[IntentConflict]
    ) -> IntentEnsembleResult:
        """解决冲突"""
        resolved = []

        for conflict in conflicts:
            # 使用加权投票解决
            if conflict.resolution_strategy == "weighted_voting":
                # 已经在加权投票中解决
                resolution = f"使用加权投票选择: {result.final_intent}"
            else:
                resolution = f"使用{conflict.resolution_strategy}解决"

            conflict.resolution = resolution
            resolved.append(conflict.conflict_id)

        result.conflicts_resolved = resolved
        self.stats["conflicts_resolved"] += len(resolved)

        return result

    def _calibrate_confidence(self, result: IntentEnsembleResult) -> float:
        """校准置信度"""
        # 基于模型一致性校准
        if not result.model_predictions:
            return result.confidence

        # 计算预测一致性
        intents = [self.intent_mapping.get(p.intent, p.intent) for p in result.model_predictions]
        unique_intents = set(intents)
        consistency = 1.0 - (len(unique_intents) - 1) / len(intents)

        # 调整置信度
        calibrated = result.confidence * (0.7 + 0.3 * consistency)

        return min(0.98, calibrated)

    def _update_stats(self, result: IntentEnsembleResult) -> Any:
        """更新统计"""
        self.stats["total_predictions"] += 1

        if result.confidence >= 0.8:
            self.stats["high_confidence"] += 1
        else:
            self.stats["low_confidence"] += 1

    def update_model_performance(self, model_name: str, accuracy: float):
        """更新模型性能"""
        self.model_performance[model_name].append(accuracy)

        # 限制历史长度
        if len(self.model_performance[model_name]) > 100:
            self.model_performance[model_name] = self.model_performance[model_name][-50:]

        # 更新权重
        self._update_weights_based_on_performance()

    def _update_weights_based_on_performance(self) -> Any:
        """基于性能更新权重"""
        for model_name, perf_history in self.model_performance.items():
            if len(perf_history) >= 5:
                recent_avg = sum(perf_history[-5:]) / 5

                # 调整权重
                if recent_avg > 0.95:
                    self.model_weights[model_name] = min(0.5, self.model_weights[model_name] * 1.1)
                elif recent_avg < 0.80:
                    self.model_weights[model_name] = max(0.05, self.model_weights[model_name] * 0.9)

        # 归一化
        total = sum(self.model_weights.values())
        self.model_weights = {k: v / total for k, v in self.model_weights.items()}

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "model_count": len(self.models),
            "model_weights": self.model_weights,
            "conflict_history_size": len(self.conflict_history),
        }


# 全局实例
_ensemble_instance: IntentEnsemble | None = None


def get_intent_ensemble() -> IntentEnsemble:
    """获取意图识别集成器单例"""
    global _ensemble_instance
    if _ensemble_instance is None:
        _ensemble_instance = IntentEnsemble()
    return _ensemble_instance
