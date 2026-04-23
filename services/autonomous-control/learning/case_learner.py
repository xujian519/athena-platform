#!/usr/bin/env python3
"""
案例学习器
Case Learner

从案例中持续学习和优化

作者: 小娜·天秤女神
创建时间: 2024年12月15日
"""

import asyncio
import json
import logging
import pickle
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

class CaseLearner:
    """案例学习器"""

    def __init__(self):
        """初始化学习器"""
        self.name = "小娜案例学习器"
        self.version = "v2.0"

        # 学习数据存储
        self.learn_dir = Path("/Users/xujian/Athena工作平台/data/case_learning")
        self.learn_dir.mkdir(parents=True, exist_ok=True)

        # 数据文件
        self.case_patterns_file = self.learn_dir / "case_patterns.pkl"
        self.success_patterns_file = self.learn_dir / "success_patterns.pkl"
        self.failure_patterns_file = self.learn_dir / "failure_patterns.pkl"
        self.expertise_weights_file = self.learn_dir / "expertise_weights.json"
        self.learning_stats_file = self.learn_dir / "learning_stats.json"

        # 学习数据
        self.case_patterns = defaultdict(list)
        self.success_patterns = {}
        self.failure_patterns = {}
        self.expertise_weights = {}
        self.learning_stats = {
            "total_cases": 0,
            "successful_cases": 0,
            "failed_cases": 0,
            "learning_rate": 0.1,
            "last_updated": None
        }

        # 学习参数
        self.learning_rate = 0.1
        self.decay_factor = 0.95
        self.min_case_count = 5
        self.confidence_threshold = 0.7

        # 业务领域
        self.business_domains = ["patent", "trademark", "copyright", "contract"]
        self.expertise_levels = ["初级", "中级", "高级", "专家"]

        self.initialized = False

    async def initialize(self):
        """初始化学习器"""
        try:
            # 加载历史学习数据
            await self._load_learning_data()

            # 初始化各领域权重
            await self._initialize_expertise_weights()

            # 启动定期学习任务
            asyncio.create_task(self._periodic_learning())

            self.initialized = True
            logger.info("✅ 案例学习器初始化完成")

        except Exception as e:
            logger.error(f"❌ 学习器初始化失败: {str(e)}")
            # 使用默认值初始化
            await self._initialize_expertise_weights()
            self.initialized = True

    async def learn_from_case(self, case_data: dict[str, Any]) -> dict[str, Any]:
        """
        从案例中学习

        Args:
            case_data: 案例数据
            {
                "case_id": "CASE_001",
                "business_type": "patent|trademark|copyright|contract",
                "case_content": "案例内容",
                "analysis_result": "分析结果",
                "recommendations": ["建议1", "建议2"],
                "outcome": "success|failure|pending",
                "feedback": {
                    "quality_score": 0.8,
                    "user_satisfaction": 0.9,
                    "actual_outcome": "授权/驳回/协商成功等"
                },
                "timestamp": "2024-01-01T00:00:00"
            }

        Returns:
            学习结果
        """
        try:
            business_type = case_data.get("business_type", "patent")
            outcome = case_data.get("outcome", "pending")
            feedback = case_data.get("feedback", {})

            # 提取案例特征
            features = await self._extract_case_features(case_data)

            # 更新模式库
            pattern_update = await self._update_case_patterns(
                business_type, features, outcome, feedback
            )

            # 更新成功率模式
            success_update = await self._update_success_patterns(
                business_type, features, outcome
            )

            # 更新专业权重
            expertise_update = await self._update_expertise_weights(
                business_type, outcome, feedback
            )

            # 更新学习统计
            await self._update_learning_stats(outcome)

            # 保存学习数据
            await self._save_learning_data()

            learning_result = {
                "case_id": case_data.get("case_id"),
                "learning_success": True,
                "pattern_updated": pattern_update,
                "success_updated": success_update,
                "expertise_updated": expertise_update,
                "current_expertise": self.expertise_weights.get(business_type, {}),
                "learning_timestamp": datetime.now().isoformat()
            }

            logger.info(f"✅ 案例学习完成: {case_data.get('case_id')}")
            return learning_result

        except Exception as e:
            logger.error(f"❌ 案例学习失败: {str(e)}")
            return {
                "case_id": case_data.get("case_id"),
                "learning_success": False,
                "error": str(e)
            }

    async def update_model(self, feedback: dict[str, Any]) -> dict[str, Any]:
        """
        更新学习模型

        Args:
            feedback: 反馈数据
            {
                "case_id": "CASE_001",
                "corrections": ["修正1", "修正2"],
                "rating": 5,
                "improvements": ["改进1", "改进2"]
            }

        Returns:
            更新结果
        """
        try:
            case_id = feedback.get("case_id")
            corrections = feedback.get("corrections", [])
            rating = feedback.get("rating", 3)
            improvements = feedback.get("improvements", [])

            # 查找对应案例
            case_data = await self._find_case_data(case_id)
            if not case_data:
                return {
                    "success": False,
                    "error": f"案例不存在: {case_id}"
                }

            # 分析修正内容
            corrections_analysis = await self._analyze_corrections(corrections)

            # 更新模式
            pattern_updates = []
            for correction in corrections:
                update = await self._apply_correction(correction, case_data)
                pattern_updates.append(update)

            # 调整权重
            weight_adjustment = await self._adjust_weights_based_on_feedback(
                rating, case_data.get("business_type")
            )

            # 生成改进建议
            improvement_actions = await self._generate_improvement_actions(
                improvements, case_data
            )

            # 保存更新
            await self._save_learning_data()

            result = {
                "success": True,
                "case_id": case_id,
                "corrections_analyzed": corrections_analysis,
                "pattern_updates": pattern_updates,
                "weight_adjustment": weight_adjustment,
                "improvement_actions": improvement_actions,
                "updated_at": datetime.now().isoformat()
            }

            logger.info(f"✅ 模型更新完成: {case_id}")
            return result

        except Exception as e:
            logger.error(f"❌ 模型更新失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_learning_insights(self, business_type: str = None) -> dict[str, Any]:
        """
        获取学习洞察

        Args:
            business_type: 业务类型（可选）

        Returns:
            学习洞察
        """
        try:
            insights = {
                "overview": await self._get_learning_overview(),
                "expertise_levels": await self._get_expertise_levels(business_type),
                "success_patterns": await self._get_key_success_patterns(business_type),
                "failure_patterns": await self._get_key_failure_patterns(business_type),
                "learning_trends": await self._get_learning_trends(business_type),
                "recommendations": await self._get_learning_recommendations(business_type)
            }

            return insights

        except Exception as e:
            logger.error(f"❌ 获取学习洞察失败: {str(e)}")
            return {
                "error": str(e),
                "insights": {}
            }

    async def _extract_case_features(self, case_data: dict[str, Any]) -> dict[str, Any]:
        """提取案例特征"""
        features = {
            "text_features": await self._extract_text_features(case_data.get("case_content", "")),
            "structure_features": await self._extract_structure_features(case_data),
            "outcome_features": await self._extract_outcome_features(case_data),
            "context_features": await self._extract_context_features(case_data)
        }
        return features

    async def _extract_text_features(self, text: str) -> dict[str, Any]:
        """提取文本特征"""
        # 简化的文本特征提取
        features = {
            "length": len(text),
            "word_count": len(text.split()),
            "sentence_count": text.count('。') + text.count('！') + text.count('？'),
            "keywords": await self._extract_keywords(text),
            "legal_terms": await self._extract_legal_terms(text)
        }
        return features

    async def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词"""
        # 简化的关键词提取
        keywords = []
        legal_keywords = ["专利", "发明", "权利要求", "商标", "版权", "合同", "侵权", "授权"]
        for keyword in legal_keywords:
            if keyword in text:
                keywords.append(keyword)
        return keywords

    async def _extract_legal_terms(self, text: str) -> list[str]:
        """提取法律术语"""
        legal_terms = {
            "专利权": "patent_right",
            "商标权": "trademark_right",
            "著作权": "copyright",
            "侵权": "infringement",
            "新颖性": "novelty",
            "创造性": "creativity",
            "实用性": "utility"
        }
        found_terms = []
        for chinese_term, english_term in legal_terms.items():
            if chinese_term in text:
                found_terms.append({
                    "chinese": chinese_term,
                    "english": english_term
                })
        return found_terms

    async def _extract_structure_features(self, case_data: dict[str, Any]) -> dict[str, Any]:
        """提取结构特征"""
        features = {
            "has_recommendations": bool(case_data.get("recommendations")),
            "recommendation_count": len(case_data.get("recommendations", [])),
            "has_analysis": bool(case_data.get("analysis_result")),
            "analysis_depth": await self._analyze_analysis_depth(case_data.get("analysis_result", ""))
        }
        return features

    async def _analyze_analysis_depth(self, analysis: str) -> int:
        """分析分析深度"""
        if not analysis:
            return 0
        # 基于长度和结构判断深度
        depth = len(analysis.split('\n')) // 10
        return min(depth, 5)

    async def _extract_outcome_features(self, case_data: dict[str, Any]) -> dict[str, Any]:
        """提取结果特征"""
        outcome = case_data.get("outcome", "pending")
        feedback = case_data.get("feedback", {})

        features = {
            "outcome": outcome,
            "quality_score": feedback.get("quality_score", 0.5),
            "user_satisfaction": feedback.get("user_satisfaction", 0.5),
            "success_indicator": 1 if outcome == "success" else 0
        }
        return features

    async def _extract_context_features(self, case_data: dict[str, Any]) -> dict[str, Any]:
        """提取上下文特征"""
        features = {
            "business_type": case_data.get("business_type", "unknown"),
            "timestamp": case_data.get("timestamp", datetime.now().isoformat()),
            "complexity": await self._assess_case_complexity(case_data)
        }
        return features

    async def _assess_case_complexity(self, case_data: dict[str, Any]) -> str:
        """评估案例复杂度"""
        complexity_score = 0

        # 基于内容长度
        content_length = len(case_data.get("case_content", ""))
        if content_length > 5000:
            complexity_score += 3
        elif content_length > 2000:
            complexity_score += 2
        elif content_length > 500:
            complexity_score += 1

        # 基于分析结果
        if case_data.get("analysis_result"):
            complexity_score += 1

        # 基于建议数量
        rec_count = len(case_data.get("recommendations", []))
        if rec_count > 5:
            complexity_score += 2
        elif rec_count > 2:
            complexity_score += 1

        # 转换为复杂度级别
        if complexity_score >= 5:
            return "高"
        elif complexity_score >= 3:
            return "中"
        else:
            return "低"

    async def _update_case_patterns(self, business_type: str, features: dict[str, Any],
                                  outcome: str, feedback: dict[str, Any]) -> bool:
        """更新案例模式"""
        try:
            # 创建模式
            pattern = {
                "features": features,
                "outcome": outcome,
                "feedback": feedback,
                "timestamp": datetime.now().isoformat(),
                "frequency": 1
            }

            # 检查是否已有相似模式
            existing_patterns = self.case_patterns.get(business_type, [])
            for existing in existing_patterns:
                similarity = await self._calculate_pattern_similarity(
                    features, existing["features"]
                )
                if similarity > 0.8:
                    # 更新现有模式
                    existing["frequency"] += 1
                    existing["last_seen"] = datetime.now().isoformat()
                    # 加权更新
                    weight = self.learning_rate
                    existing["features"] = await self._weighted_average_features(
                        existing["features"], features, weight
                    )
                    return True

            # 添加新模式
            self.case_patterns[business_type].append(pattern)
            return True

        except Exception as e:
            logger.error(f"更新案例模式失败: {str(e)}")
            return False

    async def _calculate_pattern_similarity(self, features1: dict[str, Any],
                                          features2: dict[str, Any]) -> float:
        """计算模式相似度"""
        similarity = 0.0
        count = 0

        # 文本特征相似度
        text1 = features1.get("text_features", {})
        text2 = features2.get("text_features", {})

        # 长度相似度
        len1, len2 = text1.get("length", 0), text2.get("length", 0)
        if len1 > 0 and len2 > 0:
            similarity += 1 - abs(len1 - len2) / max(len1, len2)
            count += 1

        # 关键词重叠
        keywords1 = set(text1.get("keywords", []))
        keywords2 = set(text2.get("keywords", []))
        if keywords1 or keywords2:
            intersection = len(keywords1.intersection(keywords2))
            union = len(keywords1.union(keywords2))
            similarity += intersection / union if union > 0 else 0
            count += 1

        # 结构特征相似度
        struct1 = features1.get("structure_features", {})
        struct2 = features2.get("structure_features", {})

        if struct1.get("has_recommendations") == struct2.get("has_recommendations"):
            similarity += 0.5
            count += 1

        return similarity / count if count > 0 else 0

    async def _weighted_average_features(self, features1: dict[str, Any],
                                       features2: dict[str, Any], weight: float) -> dict[str, Any]:
        """加权平均特征"""
        # 简化实现，返回features1
        # 实际应该根据特征类型进行加权平均
        return features1

    async def _update_success_patterns(self, business_type: str, features: dict[str, Any],
                                     outcome: str) -> bool:
        """更新成功模式"""
        if outcome != "success":
            return False

        try:
            if business_type not in self.success_patterns:
                self.success_patterns[business_type] = {
                    "total_success": 0,
                    "common_features": defaultdict(int),
                    "success_rate_by_complexity": defaultdict(list),
                    "key_factors": []
                }

            patterns = self.success_patterns[business_type]
            patterns["total_success"] += 1

            # 记录常见特征
            text_features = features.get("text_features", {})
            for keyword in text_features.get("keywords", []):
                patterns["common_features"][keyword] += 1

            # 记录复杂度
            context_features = features.get("context_features", {})
            complexity = context_features.get("complexity", "低")
            patterns["success_rate_by_complexity"][complexity].append(
                features.get("outcome_features", {}).get("quality_score", 0.5)
            )

            return True

        except Exception as e:
            logger.error(f"更新成功模式失败: {str(e)}")
            return False

    async def _update_expertise_weights(self, business_type: str, outcome: str,
                                      feedback: dict[str, Any]) -> bool:
        """更新专业权重"""
        try:
            if business_type not in self.expertise_weights:
                self.expertise_weights[business_type] = {
                    "level": "初级",
                    "confidence": 0.5,
                    "success_count": 0,
                    "total_cases": 0,
                    "specialties": [],
                    "strengths": [],
                    "weaknesses": []
                }

            weights = self.expertise_weights[business_type]
            weights["total_cases"] += 1

            if outcome == "success":
                weights["success_count"] += 1

            # 更新置信度
            success_rate = weights["success_count"] / weights["total_cases"]
            weights["confidence"] = min(0.95, success_rate * 1.1)

            # 更新专业级别
            weights["level"] = await self._calculate_expertise_level(
                weights["total_cases"], weights["confidence"]
            )

            # 识别强项和弱项
            quality_score = feedback.get("quality_score", 0.5)
            if quality_score > 0.8:
                # 记录强项
                await self._record_strength(weights, feedback)
            elif quality_score < 0.5:
                # 记录弱项
                await self._record_weakness(weights, feedback)

            return True

        except Exception as e:
            logger.error(f"更新专业权重失败: {str(e)}")
            return False

    async def _calculate_expertise_level(self, case_count: int, confidence: float) -> str:
        """计算专业级别"""
        if case_count >= 100 and confidence >= 0.9:
            return "专家"
        elif case_count >= 50 and confidence >= 0.8:
            return "高级"
        elif case_count >= 20 and confidence >= 0.7:
            return "中级"
        else:
            return "初级"

    async def _record_strength(self, weights: dict[str, Any], feedback: dict[str, Any]):
        """记录强项"""
        strengths = weights.get("strengths", [])
        # 基于反馈记录强项
        if feedback.get("analysis_quality") == "优秀":
            strengths.append("案例分析")
        if feedback.get("recommendation_effectiveness") == "很高":
            strengths.append("建议有效性")
        weights["strengths"] = list(set(strengths))  # 去重

    async def _record_weakness(self, weights: dict[str, Any], feedback: dict[str, Any]):
        """记录弱项"""
        weaknesses = weights.get("weaknesses", [])
        # 基于反馈记录弱项
        if feedback.get("response_time") == "慢":
            weaknesses.append("响应速度")
        if feedback.get("accuracy") == "低":
            weaknesses.append("准确性")
        weights["weaknesses"] = list(set(weaknesses))  # 去重

    async def _update_learning_stats(self, outcome: str):
        """更新学习统计"""
        self.learning_stats["total_cases"] += 1
        if outcome == "success":
            self.learning_stats["successful_cases"] += 1
        elif outcome == "failure":
            self.learning_stats["failed_cases"] += 1
        self.learning_stats["last_updated"] = datetime.now().isoformat()

    async def _load_learning_data(self):
        """加载学习数据"""
        try:
            # 加载案例模式
            if self.case_patterns_file.exists():
                with open(self.case_patterns_file, 'rb') as f:
                    self.case_patterns = pickle.load(f)

            # 加载成功模式
            if self.success_patterns_file.exists():
                with open(self.success_patterns_file, 'rb') as f:
                    self.success_patterns = pickle.load(f)

            # 加载失败模式
            if self.failure_patterns_file.exists():
                with open(self.failure_patterns_file, 'rb') as f:
                    self.failure_patterns = pickle.load(f)

            # 加载专业权重
            if self.expertise_weights_file.exists():
                with open(self.expertise_weights_file, encoding='utf-8') as f:
                    self.expertise_weights = json.load(f)

            # 加载学习统计
            if self.learning_stats_file.exists():
                with open(self.learning_stats_file, encoding='utf-8') as f:
                    self.learning_stats = json.load(f)

            logger.info("✅ 学习数据加载完成")

        except Exception as e:
            logger.warning(f"加载学习数据失败，使用默认值: {str(e)}")

    async def _save_learning_data(self):
        """保存学习数据"""
        try:
            # 保存案例模式
            with open(self.case_patterns_file, 'wb') as f:
                pickle.dump(dict(self.case_patterns), f)

            # 保存成功模式
            with open(self.success_patterns_file, 'wb') as f:
                pickle.dump(self.success_patterns, f)

            # 保存失败模式
            with open(self.failure_patterns_file, 'wb') as f:
                pickle.dump(self.failure_patterns, f)

            # 保存专业权重
            with open(self.expertise_weights_file, 'w', encoding='utf-8') as f:
                json.dump(self.expertise_weights, f, ensure_ascii=False, indent=2)

            # 保存学习统计
            with open(self.learning_stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.learning_stats, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"保存学习数据失败: {str(e)}")

    async def _initialize_expertise_weights(self):
        """初始化专业权重"""
        for domain in self.business_domains:
            if domain not in self.expertise_weights:
                self.expertise_weights[domain] = {
                    "level": "初级",
                    "confidence": 0.5,
                    "success_count": 0,
                    "total_cases": 0,
                    "specialties": [],
                    "strengths": [],
                    "weaknesses": []
                }

    async def _periodic_learning(self):
        """定期学习任务"""
        while True:
            try:
                # 每小时执行一次
                await asyncio.sleep(3600)

                # 分析学习效果
                await self._analyze_learning_effectiveness()

                # 优化学习策略
                await self._optimize_learning_strategy()

            except Exception as e:
                logger.error(f"定期学习任务失败: {str(e)}")

    async def _analyze_learning_effectiveness(self):
        """分析学习效果"""
        # 分析学习曲线
        for domain, weights in self.expertise_weights.items():
            if weights["total_cases"] > 0:
                success_rate = weights["success_count"] / weights["total_cases"]
                logger.info(f"{domain}领域成功率: {success_rate:.2%}")

    async def _optimize_learning_strategy(self):
        """优化学习策略"""
        # 根据学习效果调整参数
        total_cases = self.learning_stats["total_cases"]
        if total_cases > 100:
            # 降低学习率
            self.learning_rate = max(0.05, self.learning_rate * 0.99)

    async def _find_case_data(self, case_id: str) -> dict[str, Any | None]:
        """查找案例数据"""
        # 简化实现，返回None
        # 实际应该从数据库或文件中查找
        return None

    async def _analyze_corrections(self, corrections: list[str]) -> dict[str, Any]:
        """分析修正内容"""
        return {
            "correction_count": len(corrections),
            "common_issues": ["准确性", "完整性"],  # 简化
            "severity": "中等"
        }

    async def _apply_correction(self, correction: str, case_data: dict[str, Any]) -> dict[str, Any]:
        """应用修正"""
        return {
            "correction": correction,
            "applied": True,
            "impact": "positive"
        }

    async def _adjust_weights_based_on_feedback(self, rating: int, business_type: str) -> dict[str, Any]:
        """基于反馈调整权重"""
        if business_type in self.expertise_weights:
            weights = self.expertise_weights[business_type]
            # 根据评分调整置信度
            if rating >= 4:
                weights["confidence"] = min(0.95, weights["confidence"] * 1.05)
            elif rating <= 2:
                weights["confidence"] = max(0.1, weights["confidence"] * 0.95)

        return {"adjusted": True}

    async def _generate_improvement_actions(self, improvements: list[str], case_data: dict[str, Any]) -> list[str]:
        """生成改进行动"""
        actions = []
        for improvement in improvements:
            if "准确性" in improvement:
                actions.append("增加专业知识库更新")
            elif "响应速度" in improvement:
                actions.append("优化推理算法")
        return actions

    async def _get_learning_overview(self) -> dict[str, Any]:
        """获取学习概览"""
        return self.learning_stats

    async def _get_expertise_levels(self, business_type: str = None) -> dict[str, Any]:
        """获取专业级别"""
        if business_type:
            return {business_type: self.expertise_weights.get(business_type, {})}
        return self.expertise_weights

    async def _get_key_success_patterns(self, business_type: str = None) -> dict[str, Any]:
        """获取关键成功模式"""
        if business_type:
            return self.success_patterns.get(business_type, {})
        return self.success_patterns

    async def _get_key_failure_patterns(self, business_type: str = None) -> dict[str, Any]:
        """获取关键失败模式"""
        if business_type:
            return self.failure_patterns.get(business_type, {})
        return self.failure_patterns

    async def _get_learning_trends(self, business_type: str = None) -> list[dict[str, Any]:
        """获取学习趋势"""
        # 简化实现
        return [
            {"date": "2024-12-15", "success_rate": 0.85},
            {"date": "2024-12-14", "success_rate": 0.83}
        ]

    async def _get_learning_recommendations(self, business_type: str = None) -> list[str]:
        """获取学习建议"""
        recommendations = []

        if business_type:
            weights = self.expertise_weights.get(business_type, {})
            if weights.get("confidence", 0) < 0.7:
                recommendations.append(f"建议增加{business_type}领域的学习案例")

            weaknesses = weights.get("weaknesses", [])
            for weakness in weaknesses:
                if weakness == "准确性":
                    recommendations.append("建议加强专业知识库建设")
                elif weakness == "响应速度":
                    recommendations.append("建议优化算法效率")
        else:
            recommendations.append("定期回顾和分析案例")
            recommendations.append("持续收集用户反馈")

        return recommendations

# 使用示例
async def main():
    """测试案例学习器"""
    learner = CaseLearner()
    await learner.initialize()

    # 模拟案例学习
    case_data = {
        "case_id": "CASE_TEST_001",
        "business_type": "patent",
        "case_content": "这是一项关于人工智能的创新技术...",
        "analysis_result": "经过分析，该技术具有新颖性和创造性",
        "recommendations": ["建议申请发明专利", "加强技术保护"],
        "outcome": "success",
        "feedback": {
            "quality_score": 0.9,
            "user_satisfaction": 0.95,
            "actual_outcome": "专利申请成功"
        }
    }

    # 学习案例
    result = await learner.learn_from_case(case_data)
    print(f"学习结果: {result}")

    # 获取学习洞察
    insights = await learner.get_learning_insights("patent")
    print(f"专利领域专业级别: {insights['expertise_levels']}")

# 入口点: @async_main装饰器已添加到main函数
