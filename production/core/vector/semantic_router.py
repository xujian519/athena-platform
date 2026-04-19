#!/usr/bin/env python3
"""
智能语义路由器
Intelligent Semantic Router

基于查询内容智能路由到最适合的知识图谱和向量集合
"""

from __future__ import annotations
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from core.logging_config import setup_logging

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from sentence_transformers import SentenceTransformer

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("⚠️ sentence-transformers或numpy未安装")
    TRANSFORMERS_AVAILABLE = False

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class SemanticRouter:
    """智能语义路由器"""

    def __init__(self):
        self.embedding_model = None
        self.domain_classifiers = {}
        self.route_cache = {}
        self.cache_ttl = 3600  # 缓存1小时

        # 路由规则配置
        self.routing_rules = {
            "legal_domain": {
                "keywords": [
                    "法律",
                    "法条",
                    "法规",
                    "诉讼",
                    "法院",
                    "法官",
                    "律师",
                    "合同",
                    "侵权",
                    "赔偿",
                    "刑事责任",
                    "民事诉讼",
                    "司法",
                    "判决",
                    "裁定",
                    "执行",
                    "仲裁",
                    "调解",
                    "法律援助",
                    "民法典",
                    "刑法",
                    "民事诉讼法",
                    "行政诉讼法",
                ],
                "patterns": [
                    r".*法.*",
                    r".*诉讼.*",
                    r".*合同.*",
                    r".*侵权.*",
                    r".*赔偿.*",
                    r".*犯罪.*",
                    r".*判决.*",
                ],
                "collections": ["legal_main", "legal_contracts", "legal_ip"],
                "weight": 0.8,
            },
            "patent_domain": {
                "keywords": [
                    "专利",
                    "发明",
                    "实用新型",
                    "外观设计",
                    "创造性",
                    "新颖性",
                    "专利申请",
                    "专利权",
                    "专利侵权",
                    "专利检索",
                    "专利分析",
                    "知识产权",
                    "专利法",
                    "专利审查",
                    "专利授权",
                    "专利无效",
                    "技术方案",
                    "技术特征",
                    "背景技术",
                    "现有技术",
                ],
                "patterns": [
                    r".*专利.*",
                    r".*发明.*",
                    r".*实用新型.*",
                    r".*外观设计.*",
                    r".*申请.*",
                    r".*授权.*",
                    r".*侵权.*",
                ],
                "collections": ["patent_rules", "patent_applications", "patent_legal"],
                "weight": 0.8,
            },
            "mixed_domain": {
                "keywords": [
                    "专利诉讼",
                    "专利侵权",
                    "知识产权保护",
                    "商业秘密",
                    "不正当竞争",
                    "技术转让",
                    "许可合同",
                    "专利许可",
                    "知识产权纠纷",
                    "专利纠纷",
                    "商标侵权",
                    "版权保护",
                ],
                "patterns": [
                    r".*专利.*诉讼.*",
                    r".*知识产权.*",
                    r".*专利.*侵权.*",
                    r".*技术.*合同.*",
                ],
                "collections": [
                    "legal_main",
                    "legal_contracts",
                    "legal_ip",
                    "patent_rules",
                    "patent_applications",
                    "patent_legal",
                ],
                "weight": 0.6,
            },
        }

        # 初始化模型
        self._init_embedding_model()

    def _init_embedding_model(self):
        """初始化嵌入模型"""
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("⚠️ 嵌入模型不可用,使用基于关键词的路由")
            return

        try:
            # 优先使用本地converted模型
            model_paths = [
                "/Users/xujian/Athena工作平台/models/converted/BAAI/bge-m3",
                "/Users/xujian/Athena工作平台/models/BAAI/bge-m3",
            ]

            model_loaded = False
            for model_path in model_paths:
                if Path(model_path).exists():
                    self.embedding_model = SentenceTransformer(model_path)
                    logger.info(f"✅ BGE嵌入模型加载成功: {model_path}")
                    model_loaded = True
                    break

            if not model_loaded:
                logger.warning("⚠️ 本地BGE模型不存在,跳过嵌入模型加载")
                self.embedding_model = None
        except Exception as e:
            logger.error(f"❌ 嵌入模型初始化失败: {e}")
            self.embedding_model = None

    async def classify_query(self, query: str) -> dict[str, Any]:
        """查询分类"""
        # 检查缓存
        cache_key = f"route_{hash(query)}"
        if cache_key in self.route_cache:
            cached_result = self.route_cache[cache_key]
            if datetime.now().timestamp() - cached_result["timestamp"] < self.cache_ttl:
                logger.info("🎯 使用路由缓存结果")
                return cached_result["result"]

        try:
            # 多维分类
            keyword_score = self._keyword_classification(query)
            pattern_score = self._pattern_classification(query)
            semantic_score = await self._semantic_classification(query)

            # 综合评分
            final_scores = self._combine_scores(keyword_score, pattern_score, semantic_score)

            # 确定主要领域和次要领域
            primary_domain = max(final_scores.keys(), key=lambda x: final_scores[x])
            confidence = final_scores[primary_domain]

            # 确定目标集合
            target_collections = self._select_collections(final_scores, confidence)

            # 构建结果
            result = {
                "query": query,
                "primary_domain": primary_domain,
                "confidence": confidence,
                "all_scores": final_scores,
                "target_collections": target_collections,
                "routing_strategy": self._determine_strategy(final_scores),
                "processing_hints": self._generate_processing_hints(query, primary_domain),
            }

            # 缓存结果
            self.route_cache[cache_key] = {
                "result": result,
                "timestamp": datetime.now().timestamp(),
            }

            logger.info(f"🎯 路由结果: {primary_domain} (置信度: {confidence:.2f})")
            return result

        except Exception as e:
            logger.error(f"❌ 查询分类失败: {e}")
            # 回退到默认路由
            return {
                "query": query,
                "primary_domain": "mixed_domain",
                "confidence": 0.5,
                "all_scores": {"legal_domain": 0.5, "patent_domain": 0.5, "mixed_domain": 0.5},
                "target_collections": self._get_all_collections(),
                "routing_strategy": "fallback",
                "processing_hints": ["使用通用搜索策略"],
            }

    def _keyword_classification(self, query: str) -> dict[str, float]:
        """基于关键词的分类"""
        scores = {}

        for domain, config in self.routing_rules.items():
            keyword_matches = 0
            total_keywords = len(config["keywords"])

            for keyword in config["keywords"]:
                if keyword in query:
                    keyword_matches += 1

            # 关键词匹配分数
            scores[domain] = (keyword_matches / max(1, total_keywords)) * config["weight"]

        return scores

    def _pattern_classification(self, query: str) -> dict[str, float]:
        """基于正则模式的分类"""
        scores = {}

        for domain, config in self.routing_rules.items():
            pattern_matches = 0
            total_patterns = len(config["patterns"])

            for pattern in config["patterns"]:
                if re.search(pattern, query, re.IGNORECASE):
                    pattern_matches += 1

            # 模式匹配分数
            scores[domain] = (pattern_matches / max(1, total_patterns)) * config["weight"]

        return scores

    async def _semantic_classification(self, query: str) -> dict[str, float]:
        """基于语义的分类"""
        if self.embedding_model is None:
            return {"legal_domain": 0.0, "patent_domain": 0.0, "mixed_domain": 0.0}

        try:
            # 领域代表性文本
            domain_texts = {
                "legal_domain": "法律条文 司法解释 法院判决 合同纠纷 侵权责任 民事诉讼",
                "patent_domain": "专利申请 发明专利 实用新型 专利审查 技术方案 知识产权",
                "mixed_domain": "专利诉讼 知识产权纠纷 技术转让 专利侵权 商业秘密保护",
            }

            # 生成查询向量
            query_embedding = self.embedding_model.encode([query])

            scores = {}
            for domain, text in domain_texts.items():
                # 生成领域向量
                domain_embedding = self.embedding_model.encode([text])

                # 计算相似度
                similarity = np.dot(query_embedding, domain_embedding.T)[0][0]
                scores[domain] = float(similarity)

            return scores

        except Exception as e:
            logger.error(f"❌ 语义分类失败: {e}")
            return {"legal_domain": 0.0, "patent_domain": 0.0, "mixed_domain": 0.0}

    def _combine_scores(
        self,
        keyword_scores: dict[str, float],
        pattern_scores: dict[str, float],
        semantic_scores: dict[str, float],
    ) -> dict[str, float]:
        """综合评分"""
        combined_scores = {}

        for domain in self.routing_rules:
            # 加权组合
            combined_score = (
                keyword_scores.get(domain, 0.0) * 0.4  # 关键词权重40%
                + pattern_scores.get(domain, 0.0) * 0.3  # 模式权重30%
                + semantic_scores.get(domain, 0.0) * 0.3  # 语义权重30%
            )
            combined_scores[domain] = combined_score

        return combined_scores

    def _select_collections(self, scores: dict[str, float], confidence: float) -> list[str]:
        """选择目标集合"""
        # 根据置信度和分数选择集合
        if confidence > 0.7:
            # 高置信度:使用主要领域的集合
            primary_domain = max(scores.keys(), key=lambda x: scores[x])
            return self.routing_rules[primary_domain]["collections"]
        elif confidence > 0.5:
            # 中等置信度:使用主要领域+相关集合
            primary_domain = max(scores.keys(), key=lambda x: scores[x])
            base_collections = self.routing_rules[primary_domain]["collections"]

            # 添加相关集合
            if primary_domain == "legal_domain":
                base_collections.extend(["patent_legal"])
            elif primary_domain == "patent_domain":
                base_collections.extend(["legal_contracts", "legal_ip"])

            return list(set(base_collections))
        else:
            # 低置信度:使用所有集合
            return self._get_all_collections()

    def _get_all_collections(self) -> list[str]:
        """获取所有集合"""
        all_collections = []
        for config in self.routing_rules.values():
            all_collections.extend(config["collections"])
        return list(set(all_collections))

    def _determine_strategy(self, scores: dict[str, float]) -> str:
        """确定路由策略"""
        max_score = max(scores.values())
        min_score = min(scores.values())
        score_range = max_score - min_score

        if score_range > 0.3:
            return "domain_specific"  # 领域特定
        elif score_range > 0.1:
            return "hybrid_search"  # 混合搜索
        else:
            return "broad_search"  # 广泛搜索

    def _generate_processing_hints(self, query: str, domain: str) -> list[str]:
        """生成处理提示"""
        hints = []

        if domain == "legal_domain":
            hints.extend(
                ["优先搜索法律条文和司法解释", "关注案例判决和适用条件", "注意法律术语的标准化处理"]
            )
        elif domain == "patent_domain":
            hints.extend(
                ["重点分析技术特征和创新点", "关注专利的新颖性和创造性", "注意专利术语的专业表达"]
            )
        else:
            hints.extend(
                ["综合分析法律和技术层面", "关注交叉领域的特殊规定", "平衡不同利益相关方诉求"]
            )

        # 基于查询复杂度的额外提示
        if len(query) > 50:
            hints.append("查询较复杂,建议分步处理")
        if "如何" in query or "怎么" in query:
            hints.append("包含程序性问题,提供操作指导")
        if "为什么" in query:
            hints.append("包含原因分析,提供理论依据")

        return hints

    async def route_search(self, query: str) -> dict[str, Any]:
        """路由搜索请求"""
        classification_result = await self.classify_query(query)

        # 构建搜索配置
        search_config = {
            "query": query,
            "collections": classification_result["target_collections"],
            "strategy": classification_result["routing_strategy"],
            "domain": classification_result["primary_domain"],
            "confidence": classification_result["confidence"],
            "weights": self._calculate_search_weights(classification_result["all_scores"]),
            "hints": classification_result["processing_hints"],
        }

        return search_config

    def _calculate_search_weights(self, scores: dict[str, float]) -> dict[str, float]:
        """计算搜索权重"""
        total_score = sum(scores.values())
        if total_score == 0:
            return {"legal_domain": 0.5, "patent_domain": 0.5, "mixed_domain": 0.5}

        normalized_weights = {}
        for domain, score in scores.items():
            normalized_weights[domain] = score / total_score

        return normalized_weights

    def get_routing_stats(self) -> dict[str, Any]:
        """获取路由统计信息"""
        stats = {
            "total_routes": len(self.route_cache),
            "cache_hit_rate": 0.0,  # 需要实际统计
            "domain_distribution": {},
            "average_confidence": 0.0,
            "routing_strategies": {"domain_specific": 0, "hybrid_search": 0, "broad_search": 0},
        }

        if self.route_cache:
            confidences = []
            strategies = {"domain_specific": 0, "hybrid_search": 0, "broad_search": 0}
            domains = {}

            for cached_data in self.route_cache.values():
                result = cached_data["result"]
                confidences.append(result["confidence"])
                strategies[result["routing_strategy"]] += 1

                domain = result["primary_domain"]
                domains[domain] = domains.get(domain, 0) + 1

            stats["average_confidence"] = sum(confidences) / len(confidences)
            stats["routing_strategies"] = strategies
            stats["domain_distribution"] = domains

        return stats

    def clear_cache(self):
        """清除路由缓存"""
        self.route_cache.clear()
        logger.info("🧹 路由缓存已清除")


async def main():
    """测试语义路由器"""
    print("🧭 测试智能语义路由器...")

    router = SemanticRouter()

    # 测试查询
    test_queries = [
        "专利侵权应该如何赔偿?",
        "劳动合同的解除条件是什么?",
        "发明专利的新颖性如何判断?",
        "技术转让合同需要注意哪些法律问题?",
        "如何申请外观设计专利?",
    ]

    print("\n" + "=" * 60)
    print("📊 语义路由测试结果:")
    print("=" * 60)

    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. 查询: {query}")

        # 路由分类
        classification = await router.classify_query(query)

        print(f"   主要领域: {classification['primary_domain']}")
        print(f"   置信度: {classification['confidence']:.2f}")
        print(f"   目标集合: {', '.join(classification['target_collections'])}")
        print(f"   路由策略: {classification['routing_strategy']}")
        print(
            f"   处理提示: {classification['processing_hints'][0] if classification['processing_hints'] else '无'}"
        )

    # 显示路由统计
    stats = router.get_routing_stats()
    print("\n📈 路由统计:")
    print(f"   总路由数: {stats['total_routes']}")
    print(f"   平均置信度: {stats['average_confidence']:.2f}")
    print(f"   策略分布: {stats['routing_strategies']}")

    print("\n🎉 语义路由器测试完成!")


# 入口点: @async_main装饰器已添加到main函数
