#!/usr/bin/env python3
from __future__ import annotations
"""
权威文档专用Reranker
Authoritative Document Reranker

针对专利法律文档特点定制的重排序引擎
作者: Athena AI Team
创建时间: 2026-01-19
版本: v1.0.0
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from core.reranking.bge_reranker import BGEReranker

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """文档类型"""

    LAW = "law"  # 法律 (最高权威性)
    GUIDELINE = "guideline"  # 审查指南 (高权威性)
    RULE = "rule"  # 规则 (中等权威性)
    DECISION = "decision"  # 决定 (案例参考)


@dataclass
class AuthorityConfig:
    """权威性配置"""

    # 文档类型权重
    law_weight: float = 1.0
    guideline_weight: float = 0.85
    rule_weight: float = 0.7
    decision_weight: float = 0.6

    # 特征权重
    bge_score_weight: float = 0.50  # BGE相关性分数
    authority_weight: float = 0.25  # 权威性权重
    citation_weight: float = 0.15  # 引用关系权重
    recency_weight: float = 0.10  # 时效性权重


class AuthoritativeDocumentReranker:
    """权威文档专用重排序引擎"""

    def __init__(
        self, bge_reranker: BGEReranker | None = None, config: AuthorityConfig | None = None
    ):
        """
        初始化权威文档重排序引擎

        Args:
            bge_reranker: BGE重排序引擎实例
            config: 权威性配置
        """
        self.config = config or AuthorityConfig()
        self.bge_reranker = bge_reranker or self._init_bge_reranker()

        # 文档类型权威性映射
        self.authority_map = {
            DocumentType.LAW: self.config.law_weight,
            DocumentType.GUIDELINE: self.config.guideline_weight,
            DocumentType.RULE: self.config.rule_weight,
            DocumentType.DECISION: self.config.decision_weight,
        }

        logger.info("✅ 权威文档Reranker初始化完成")
        logger.info(f"   BGE模型: {self.bge_reranker.name if self.bge_reranker else 'N/A'}")
        logger.info(f"   权威性权重: {self.authority_map}")

    def _init_bge_reranker(self) -> BGEReranker | None:
        """初始化BGE Reranker"""
        try:
            reranker = BGEReranker()
            if reranker.initialize():
                return reranker
        except Exception as e:
            logger.warning(f"⚠️ BGE Reranker初始化失败: {e}")
        return None

    def rerank(
        self, query: str, documents: list[dict[str, Any]], top_k: int = 10
    ) -> list[dict[str, Any]]:
        """
        重排序权威文档

        Args:
            query: 用户查询
            documents: 文档列表,每个文档包含:
                - content: 文档内容
                - article_type: 文档类型 (law/guideline/rule/decision)
                - metadata: 元数据 (引用关系、日期等)
                - score: 原始向量相似度分数
            top_k: 返回的top-k数量

        Returns:
            重排序后的文档列表
        """
        if not documents:
            return []

        logger.info(f"🔄 开始权威文档重排序: {len(documents)} -> {top_k}")

        # 1. BGE相关性打分 (如果可用)
        if self.bge_reranker:
            bge_result = self.bge_reranker.rerank(query, documents)
            bge_scores = bge_result.reranked_scores
            logger.info("   BGE打分完成")
        else:
            # 回退到原始分数
            bge_scores = [doc.get("score", 0.0) for doc in documents]
            logger.warning("   使用原始分数 (BGE不可用)")

        # 2. 计算多维特征分数
        feature_scores = self._compute_feature_scores(query, documents, bge_scores)

        # 3. 加权融合
        final_scores = self._weighted_scoring(feature_scores)

        # 4. 更新文档分数并排序
        for doc, score in zip(documents, final_scores, strict=False):
            doc["rerank_score"] = float(score)
            doc["feature_scores"] = feature_scores.get(doc.get("id", ""), {})

        # 5. 返回Top-K
        sorted_docs = sorted(documents, key=lambda x: x["rerank_score"], reverse=True)
        result = sorted_docs[:top_k]

        logger.info(f"✅ 重排序完成,返回Top-{len(result)}")
        logger.info(
            f"   分数范围: {result[0]['rerank_score']:.3f} - {result[-1]['rerank_score']:.3f}"
        )

        return result

    def _compute_feature_scores(
        self, query: str, documents: list[dict[str, Any]], bge_scores: list[float]
    ) -> dict[str, dict[str, float]]:
        """
        计算多维特征分数

        Returns:
            字典: {doc_id: {feature_name: score}}
        """
        feature_scores = {}

        for doc, bge_score in zip(documents, bge_scores, strict=False):
            doc_id = doc.get("id", doc.get("article_id", ""))

            # 1. BGE相关性分数 (已归一化)
            f_bge = bge_score

            # 2. 权威性分数
            doc_type = doc.get("article_type", "rule")
            f_authority = self._compute_authority_score(doc, doc_type)

            # 3. 引用关系分数
            f_citation = self._compute_citation_score(doc)

            # 4. 时效性分数
            f_recency = self._compute_recency_score(doc)

            feature_scores[doc_id] = {
                "bge": f_bge,
                "authority": f_authority,
                "citation": f_citation,
                "recency": f_recency,
            }

        return feature_scores

    def _compute_authority_score(self, doc: dict[str, Any], doc_type: str) -> float:
        """
        计算权威性分数

        考虑因素:
        - 文档类型 (law > guideline > rule > decision)
        - 层级深度 (高层级 > 低层级)
        - 内容质量 (长度 > 500字符加分)
        """
        # 基础权威性 (文档类型)
        try:
            doc_enum = DocumentType(doc_type)
            base_authority = self.authority_map[doc_enum]
        except ValueError:
            base_authority = 0.5  # 未知类型

        # 层级加成 (hierarchy_level越小越高层)
        hierarchy_level = doc.get("hierarchy_level", 0)
        level_bonus = max(0, (3 - hierarchy_level) * 0.05)

        # 内容质量加成
        content = doc.get("content", "")
        quality_bonus = 0.0
        if len(content) > 500:
            quality_bonus = min(0.1, (len(content) - 500) / 5000 * 0.1)

        authority_score = base_authority + level_bonus + quality_bonus

        # 归一化到0-1
        return min(1.0, authority_score)

    def _compute_citation_score(self, doc: dict[str, Any]) -> float:
        """
        计算引用关系分数 (P1-8修复: 修复计算方向)

        考虑因素:
        - 被引用次数 (越多越重要)
        - 引用深度 (距离源文档越近越重要)

        说明:
        - metadata.references 表示该文档引用了哪些文档
        - 被引用次数需要反向查询,这里使用引用数量作为代理指标
        - 实际生产环境应使用预计算的被引次数字段
        """
        metadata = doc.get("metadata", {}) or {}

        # P1-8修复: 明确引用关系
        # 当前: references表示该文档引用了其他文档的数量
        # 理想: 应该有cited_by字段表示被引用次数
        # 这里暂时使用引用数量作为权威性指标

        references = metadata.get("references", [])

        if not references:
            return 0.0

        # 使用引用数量作为权威性指标
        # 引用更多文档 = 可能更全面/重要
        citation_count = len(references)

        # 归一化:假设引用10个文档为满分
        citation_score = min(1.0, citation_count / 10.0)

        # P1-8改进说明:
        # 生产环境应添加被引用次数字段:
        # ALTER TABLE patent_rules_unified ADD COLUMN cited_count INTEGER DEFAULT 0;
        # 然后定期更新:
        # UPDATE patent_rules_unified SET cited_count = (
        #   SELECT COUNT(*) FROM ...
        #   WHERE metadata->'references' @> current_article_id
        # );

        return citation_score

    def _compute_recency_score(self, doc: dict[str, Any]) -> float:
        """
        计算时效性分数 (P1-7修复: 完整实现)

        考虑因素:
        - 创建/更新时间 (越新越重要)
        - 对于法律文档,修订版本更重要

        计算逻辑:
        - 30天内的文档: 1.0分
        - 30-365天: 线性衰减 1.0 -> 0.5
        - 365天以上: 0.5分 (最小值)
        """
        updated_at = doc.get("updated_at") or doc.get("created_at")
        metadata = doc.get("metadata", {}) or {}

        # 也尝试从metadata中获取时间
        if not updated_at:
            updated_at = metadata.get("updated_at") or metadata.get("created_at")

        if not updated_at:
            return 0.5  # 默认中性分数

        try:
            from datetime import datetime, timezone

            # 解析时间
            if isinstance(updated_at, str):
                # 尝试多种时间格式
                for fmt in [
                    "%Y-%m-%d %H:%M:%S.%f",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d_t%H:%M:%S",
                    "%Y-%m-%d_t%H:%M:%S.%f",
                    "%Y-%m-%d",
                ]:
                    try:
                        updated_at = datetime.strptime(updated_at, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    # 无法解析,返回默认值
                    return 0.5

            # 确保有时区信息
            if updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=timezone.utc)

            # 计算时间差
            now = datetime.now(timezone.utc)
            days_old = (now - updated_at).days

            # 衰减函数实现
            if days_old <= 30:
                # 30天内: 1.0分
                return 1.0
            elif days_old <= 365:
                # 30-365天: 线性衰减 1.0 -> 0.5
                return 1.0 - ((days_old - 30) / 335 * 0.5)
            else:
                # 365天以上: 0.5分 (最小值)
                return 0.5

        except Exception as e:
            # 计算失败,返回默认值
            logger.debug(f"时效性计算失败: {e}")
            return 0.5

    def _weighted_scoring(self, feature_scores: dict[str, dict[str, float]]) -> list[float]:
        """
        加权融合多维特征

        分数 = w1*BGE + w2*Authority + w3*Citation + w4*Recency
        """
        final_scores = []

        for _doc_id, features in feature_scores.items():
            score = (
                self.config.bge_score_weight * features["bge"]
                + self.config.authority_weight * features["authority"]
                + self.config.citation_weight * features["citation"]
                + self.config.recency_weight * features["recency"]
            )
            final_scores.append(score)

        return final_scores

    def get_config(self) -> AuthorityConfig:
        """获取当前配置"""
        return self.config

    def update_config(self, **kwargs) -> None:
        """
        更新配置

        Example:
            reranker.update_config(
                bge_score_weight=0.6,
                authority_weight=0.2
            )
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"   配置更新: {key} = {value}")
            else:
                logger.warning(f"   未知配置项: {key}")


# 便捷函数
def get_authoritative_reranker(
    bge_reranker: BGEReranker | None = None, config: AuthorityConfig | None = None
) -> AuthoritativeDocumentReranker:
    """
    获取权威文档重排序引擎实例

    Args:
        bge_reranker: BGE重排序引擎
        config: 权威性配置

    Returns:
        AuthoritativeDocumentReranker实例
    """
    return AuthoritativeDocumentReranker(bge_reranker, config)


# 使用示例
if __name__ == "__main__":
    print("=" * 80)
    print("🧪 权威文档Reranker测试")
    print("=" * 80)
    print()

    # 创建测试数据
    query = "专利创造性判断标准"

    documents = [
        {
            "id": "1",
            "article_id": "L1_2",
            "article_type": "law",
            "content": "专利法规定,授予专利权的发明和实用新型,应当具备新颖性、创造性和实用性。",
            "hierarchy_level": 0,
            "score": 0.75,
            "metadata": {"references": []},
        },
        {
            "id": "2",
            "article_id": "L2_2_3",
            "article_type": "guideline",
            "content": "创造性是指与现有技术相比,该发明有突出的实质性特点和显著的进步。",
            "hierarchy_level": 1,
            "score": 0.85,
            "metadata": {"references": ["L1_2", "L2_2_1"]},
        },
        {
            "id": "3",
            "article_id": "L3_2_3_1",
            "article_type": "guideline",
            "content": "判断发明是否具有创造性,应当考虑所属技术领域、现有技术状况等因素。",
            "hierarchy_level": 2,
            "score": 0.80,
            "metadata": {"references": ["L2_2_3"]},
        },
        {
            "id": "4",
            "article_id": "R1",
            "article_type": "rule",
            "content": "专利审查指南具体规定了创造性判断的步骤和方法。",
            "hierarchy_level": 1,
            "score": 0.70,
            "metadata": {"references": []},
        },
    ]

    print(f"查询: {query}")
    print(f"文档数: {len(documents)}")
    print()

    # 执行重排序
    reranker = get_authoritative_reranker()
    result = reranker.rerank(query, documents, top_k=3)

    print("重排序结果 (Top-3):")
    print("-" * 80)
    for i, doc in enumerate(result, 1):
        print(f"{i}. [{doc['article_id']}] {doc['article_type'].upper()}")
        print(f"   内容: {doc['content'][:60]}...")
        print(f"   综合分数: {doc['rerank_score']:.3f}")
        if "feature_scores" in doc:
            fs = doc["feature_scores"]
            print(
                f"   特征分数: BGE={fs['bge']:.2f}, Authority={fs['authority']:.2f}, "
                f"Citation={fs['citation']:.2f}, Recency={fs['recency']:.2f}"
            )
        print()

    print("=" * 80)
