#!/usr/bin/env python3
"""
嵌入模型对比测试框架
Embedding Model Comparison Test Framework

对比BGE-M3和PatentSBERTa在专利检索任务上的性能

Author: Athena Team
Version: 1.0.0
Date: 2026-02-26
"""

import asyncio
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ========== 测试数据结构 ==========


@dataclass
class PatentTestCase:
    """专利测试用例"""
    query: str
    relevant_patents: list[str]  # 相关专利的标题/摘要
    irrelevant_patents: list[str] = field(default_factory=list)
    category: str = "general"  # general, chemical, software, mechanical


@dataclass
class EmbeddingResult:
    """嵌入结果"""
    model_name: str
    query_embedding: np.ndarray
    patent_embeddings: list[np.ndarray]
    compute_time_ms: float


@dataclass
class ComparisonResult:
    """对比结果"""
    model_name: str
    precision_at_k: dict[int, float]  # P@1, P@5, P@10
    recall_at_k: dict[int, float]
    mrr: float  # Mean Reciprocal Rank
    ndcg_at_k: dict[int, float]
    avg_compute_time_ms: float


# ========== 对比测试器 ==========


class EmbeddingComparisonTester:
    """
    嵌入模型对比测试器

    对比不同嵌入模型在专利检索任务上的性能
    """

    def __init__(
        self,
        test_cases: list[PatentTestCase] | None = None,
        output_dir: str = "tests/results/embedding_comparison",
    ):
        """
        初始化测试器

        Args:
            test_cases: 测试用例列表
            output_dir: 结果输出目录
        """
        self.test_cases = test_cases or self._create_default_test_cases()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 测试结果
        self.results: dict[str, ComparisonResult] = {}

        logger.info(f"🧪 嵌入对比测试器初始化: {len(self.test_cases)} 个测试用例")

    def _create_default_test_cases(self) -> list[PatentTestCase]:
        """创建默认测试用例"""
        return [
            # 软件领域
            PatentTestCase(
                query="深度学习图像识别卷积神经网络",
                relevant_patents=[
                    "一种基于卷积神经网络的图像识别方法",
                    "使用深度学习进行图像分类的系统",
                    "CNN在计算机视觉中的应用",
                ],
                irrelevant_patents=[
                    "一种新型机械传动装置",
                    "化工原料合成工艺",
                ],
                category="software",
            ),
            # 化学领域
            PatentTestCase(
                query="聚合物合成催化剂",
                relevant_patents=[
                    "一种高效聚合物合成催化剂及其制备方法",
                    "新型催化体系在聚合反应中的应用",
                    "催化剂对聚合物分子量的控制方法",
                ],
                irrelevant_patents=[
                    "移动应用界面设计",
                    "数据库索引优化方法",
                ],
                category="chemical",
            ),
            # 机械领域
            PatentTestCase(
                query="齿轮传动装置",
                relevant_patents=[
                    "一种精密齿轮传动机构",
                    "齿轮箱的减震设计",
                    "传动装置的润滑系统",
                ],
                irrelevant_patents=[
                    "神经网络训练方法",
                    "药物制剂配方",
                ],
                category="mechanical",
            ),
        ]

    async def test_model(
        self,
        model_name: str,
        encode_fn,
    ) -> ComparisonResult:
        """
        测试单个模型

        Args:
            model_name: 模型名称
            encode_fn: 编码函数 (接收文本列表，返回嵌入向量列表)

        Returns:
            ComparisonResult: 测试结果
        """
        logger.info(f"🧪 测试模型: {model_name}")

        import time

        all_precisions = {1: [], 5: [], 10: []}
        all_recalls = {1: [], 5: [], 10: []}
        all_rrs = []  # Reciprocal Ranks
        all_ndcgs = {5: [], 10: []}
        compute_times = []

        for case in self.test_cases:
            # 编码查询
            start_time = time.time()
            query_emb = encode_fn(case.query)
            compute_time = (time.time() - start_time) * 1000
            compute_times.append(compute_time)

            # 编码候选专利
            candidate_texts = case.relevant_patents + case.irrelevant_patents
            candidate_embs = [encode_fn(text) for text in candidate_texts]

            # 计算相似度
            similarities = [
                self._cosine_similarity(query_emb, emb)
                for emb in candidate_embs
            ]

            # 排序 (降序)
            sorted_indices = np.argsort(similarities)[::-1]

            # 评估指标
            relevant_count = len(case.relevant_patents)
            relevant_indices = set(range(relevant_count))

            # Precision@K
            for k in [1, 5, 10]:
                if k <= len(sorted_indices):
                    top_k_indices = set(sorted_indices[:k])
                    precision = len(top_k_indices & relevant_indices) / k
                    all_precisions[k].append(precision)

            # Recall@K
            for k in [1, 5, 10]:
                if k <= len(sorted_indices):
                    top_k_indices = set(sorted_indices[:k])
                    recall = len(top_k_indices & relevant_indices) / relevant_count
                    all_recalls[k].append(recall)

            # MRR (Mean Reciprocal Rank)
            for rank, idx in enumerate(sorted_indices, 1):
                if idx < relevant_count:  # 是相关专利
                    all_rrs.append(1.0 / rank)
                    break
            else:
                all_rrs.append(0.0)  # 没有相关专利在结果中

            # NDCG@K (简化版本，使用二元相关性)
            for k in [5, 10]:
                dcg = 0.0
                for i, idx in enumerate(sorted_indices[:k]):
                    if idx < relevant_count:
                        dcg += 1.0 / np.log2(i + 2)  # DCG

                # 理想DCG (所有相关结果排在前面)
                idcg = sum(1.0 / np.log2(i + 2) for i in range(min(k, relevant_count)))
                ndcg = dcg / idcg if idcg > 0 else 0.0
                all_ndcgs[k].append(ndcg)

        # 聚合结果
        result = ComparisonResult(
            model_name=model_name,
            precision_at_k={
                k: np.mean(values) for k, values in all_precisions.items()
            },
            recall_at_k={
                k: np.mean(values) for k, values in all_recalls.items()
            },
            mrr=np.mean(all_rrs),
            ndcg_at_k={
                k: np.mean(values) for k, values in all_ndcgs.items()
            },
            avg_compute_time_ms=np.mean(compute_times),
        )

        self.results[model_name] = result

        # 打印结果
        self._print_result(result)

        return result

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    def _print_result(self, result: ComparisonResult) -> None:
        """打印测试结果"""
        logger.info(f"   📊 {result.model_name} 测试结果:")
        logger.info(f"      Precision@1:  {result.precision_at_k[1]:.3f}")
        logger.info(f"      Precision@5:  {result.precision_at_k[5]:.3f}")
        logger.info(f"      Precision@10: {result.precision_at_k[10]:.3f}")
        logger.info(f"      Recall@1:     {result.recall_at_k[1]:.3f}")
        logger.info(f"      Recall@5:     {result.recall_at_k[5]:.3f}")
        logger.info(f"      MRR:          {result.mrr:.3f}")
        logger.info(f"      NDCG@5:       {result.ndcg_at_k[5]:.3f}")
        logger.info(f"      NDCG@10:      {result.ndcg_at_k[10]:.3f}")
        logger.info(f"      平均计算时间:  {result.avg_compute_time_ms:.1f}ms")

    def compare_models(self) -> dict[str, Any]:
        """
        对比所有测试的模型

        Returns:
            Dict: 对比结果
        """
        if len(self.results) < 2:
            logger.warning("需要至少两个模型的结果才能进行对比")
            return {}

        comparison = {
            "models": list(self.results.keys()),
            "metrics": {},
            "winner": {},
        }

        # 找出每个指标的获胜者
        metrics_to_compare = [
            ("precision_at_1", lambda r: r.precision_at_k[1]),
            ("precision_at_5", lambda r: r.precision_at_k[5]),
            ("mrr", lambda r: r.mrr),
            ("ndcg_at_10", lambda r: r.ndcg_at_k[10]),
        ]

        for metric_name, metric_fn in metrics_to_compare:
            best_model = max(
                self.results.keys(),
                key=lambda m: metric_fn(self.results[m])
            )
            comparison["winner"][metric_name] = best_model

        # 计算相对提升
        model_names = list(self.results.keys())
        if len(model_names) == 2:
            baseline = self.results[model_names[0]
            candidate = self.results[model_names[1]

            comparison["improvements"] = {
                "precision_at_1": (candidate.precision_at_k[1] - baseline.precision_at_k[1]) / baseline.precision_at_k[1] * 100,
                "mrr": (candidate.mrr - baseline.mrr) / baseline.mrr * 100 if baseline.mrr > 0 else 0,
            }

        return comparison

    def save_results(self) -> None:
        """保存测试结果到JSON文件"""
        output_file = self.output_dir / f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # 转换结果为可序列化格式
        serializable_results = {}
        for model_name, result in self.results.items():
            serializable_results[model_name] = {
                "precision_at_k": result.precision_at_k,
                "recall_at_k": result.recall_at_k,
                "mrr": result.mrr,
                "ndcg_at_k": result.ndcg_at_k,
                "avg_compute_time_ms": result.avg_compute_time_ms,
            }

        output_data = {
            "test_cases_count": len(self.test_cases),
            "results": serializable_results,
            "comparison": self.compare_models(),
            "timestamp": datetime.now().isoformat(),
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 结果已保存到: {output_file}")


# ========== 主测试函数 ==========


async def main():
    """主测试函数"""
    logger.info("🚀 开始嵌入模型对比测试")
    logger.info("=" * 60)

    # 创建测试器
    tester = EmbeddingComparisonTester()

    # 测试BGE-M3
    try:
        from core.ai.nlp.bge_m3_loader import get_bgem3_loader

        bge_loader = get_bgem3_loader()

        def bge_encode(text: str) -> np.ndarray:
            # BGE-M3的encode方法返回的是一个列表或数组
            result = bge_loader.encode([text], normalize=True)
            # 如果是列表，取第一个元素
            if isinstance(result, list) and len(result) > 0:
                return np.array(result[0])
            return np.array(result)

        await tester.test_model("BGE-M3", bge_encode)

    except Exception as e:
        logger.error(f"❌ BGE-M3测试失败: {e}")

    logger.info("")

    # 测试PatentSBERTa
    try:
        from core.ai.embedding.patent_sberta_encoder import get_patent_encoder

        patent_encoder = get_patent_encoder(use_patent_sberta=True, fallback=True)

        def patent_sberta_encode(text: str) -> np.ndarray:
            return patent_encoder.encode(text, normalize=True)

        await tester.test_model("PatentSBERTa", patent_sberta_encode)

    except Exception as e:
        logger.error(f"❌ PatentSBERTa测试失败: {e}")

    logger.info("")
    logger.info("=" * 60)

    # 对比结果
    comparison = tester.compare_models()
    if comparison:
        logger.info("📊 模型对比结果:")
        for metric, winner in comparison.get("winner", {}).items():
            logger.info(f"   {metric}: {winner}")

        if "improvements" in comparison:
            logger.info("")
            logger.info("📈 相对提升:")
            for metric, improvement in comparison["improvements"].items():
                logger.info(f"   {metric}: {improvement:+.1f}%")

    # 保存结果
    tester.save_results()

    logger.info("=" * 60)
    logger.info("✅ 对比测试完成")


if __name__ == "__main__":
    asyncio.run(main())
