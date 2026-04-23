#!/usr/bin/env python3
"""
简化的嵌入模型对比测试
Simplified Embedding Model Comparison Test

对比BGE-M3和PatentSBERTa在专利检索任务上的性能

Author: Athena Team
Version: 1.0.0
Date: 2026-02-26
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

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


# ========== 测试用例 ==========


TEST_QUERIES = [
    {
        "query": "深度学习图像识别卷积神经网络",
        "relevant": [
            "一种基于卷积神经网络的图像识别方法",
            "使用深度学习进行图像分类的系统",
            "CNN在计算机视觉中的应用",
        ],
        "irrelevant": [
            "一种新型机械传动装置",
            "化工原料合成工艺",
        ],
        "category": "software"
    },
    {
        "query": "聚合物合成催化剂",
        "relevant": [
            "一种高效聚合物合成催化剂及其制备方法",
            "新型催化体系在聚合反应中的应用",
            "催化剂对聚合物分子量的控制方法",
        ],
        "irrelevant": [
            "移动应用界面设计",
            "数据库索引优化方法",
        ],
        "category": "chemical"
    },
    {
        "query": "齿轮传动装置",
        "relevant": [
            "一种精密齿轮传动机构",
            "齿轮箱的减震设计",
            "传动装置的润滑系统",
        ],
        "irrelevant": [
            "神经网络训练方法",
            "药物制剂配方",
        ],
        "category": "mechanical"
    },
]


# ========== 对比测试器 ==========


class SimpleEmbeddingComparison:
    """简化的嵌入对比测试"""

    def __init__(self, output_dir: str = "tests/results/embedding_comparison"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = {}

    async def test_bge_m3(self):
        """测试BGE-M3嵌入"""
        logger.info("🧪 测试BGE-M3嵌入模型")

        try:
            from core.ai.embedding.unified_embedding_service import get_unified_embedding_service

            service = await get_unified_embedding_service()

            def encode_fn(text: str) -> np.ndarray:
                result = service.encode([text])
                embedding = result.get("embedding", np.zeros(1024))
                return np.array(embedding).flatten()

            scores = self._evaluate_retrieval(encode_fn)

            self.results["BGE-M3"] = scores
            self._print_scores("BGE-M3", scores)

        except Exception as e:
            logger.error(f"   ❌ BGE-M3测试失败: {e}")

    async def test_patent_sberta(self):
        """测试PatentSBERTa嵌入"""
        logger.info("🧪 测试PatentSBERTa嵌入模型")

        try:
            from core.ai.embedding.patent_sberta_encoder import get_patent_encoder

            encoder = get_patent_encoder(use_patent_sberta=True, fallback=True)

            def encode_fn(text: str) -> np.ndarray:
                return encoder.encode(text, normalize=True)

            scores = self._evaluate_retrieval(encode_fn)

            self.results["PatentSBERTa"] = scores
            self._print_scores("PatentSBERTa", scores)

        except Exception as e:
            logger.error(f"   ❌ PatentSBERTa测试失败: {e}")

    def _evaluate_retrieval(self, encode_fn) -> dict:
        """评估检索性能"""
        precisions_at_1 = []
        precisions_at_5 = []
        recalls_at_5 = []
        reciprocal_ranks = []

        for case in TEST_QUERIES:
            # 编码查询
            query_emb = encode_fn(case["query"])

            # 编码候选文档
            all_docs = case["relevant"] + case["irrelevant"]
            doc_embeddings = [encode_fn(doc) for doc in all_docs]

            # 计算相似度
            similarities = [
                self._cosine_similarity(query_emb, doc_emb)
                for doc_emb in doc_embeddings
            ]

            # 排序
            sorted_indices = np.argsort(similarities)[::-1]

            relevant_count = len(case["relevant"])
            relevant_indices = set(range(relevant_count))

            # Precision@1
            if 0 in sorted_indices[:1]:
                precisions_at_1.append(1.0)
            else:
                precisions_at_1.append(0.0)

            # Precision@5
            top_5_relevant = len(set(sorted_indices[:5]) & relevant_indices)
            precisions_at_5.append(top_5_relevant / 5)

            # Recall@5
            recalls_at_5.append(top_5_relevant / relevant_count)

            # MRR
            for rank, idx in enumerate(sorted_indices, 1):
                if idx < relevant_count:
                    reciprocal_ranks.append(1.0 / rank)
                    break
            else:
                reciprocal_ranks.append(0.0)

        return {
            "precision_at_1": np.mean(precisions_at_1),
            "precision_at_5": np.mean(precisions_at_5),
            "recall_at_5": np.mean(recalls_at_5),
            "mrr": np.mean(reciprocal_ranks),
        }

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))

    def _print_scores(self, model_name: str, scores: dict):
        """打印分数"""
        logger.info(f"   📊 {model_name}:")
        logger.info(f"      P@1:   {scores['precision_at_1']:.3f}")
        logger.info(f"      P@5:   {scores['precision_at_5']:.3f}")
        logger.info(f"      R@5:   {scores['recall_at_5']:.3f}")
        logger.info(f"      MRR:   {scores['mrr']:.3f}")

    def compare(self):
        """对比结果"""
        if len(self.results) < 2:
            logger.warning("需要至少两个模型的结果")
            return

        logger.info("")
        logger.info("📊 对比结果:")

        baseline = self.results.get("BGE-M3")
        candidate = self.results.get("PatentSBERTa")

        if baseline and candidate:
            improvements = {}
            for metric in ["precision_at_1", "precision_at_5", "recall_at_5", "mrr"]:
                baseline_val = baseline.get(metric, 0)
                candidate_val = candidate.get(metric, 0)
                if baseline_val > 0:
                    improvement = (candidate_val - baseline_val) / baseline_val * 100
                    improvements[metric] = improvement

            for metric, improvement in improvements.items():
                status = "✅" if improvement > 0 else "❌"
                logger.info(f"   {status} {metric}: {improvement:+.1f}%")

    def save_results(self):
        """保存结果"""
        output_file = self.output_dir / f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        output_data = {
            "timestamp": datetime.now().isoformat(),
            "results": self.results,
            "test_cases_count": len(TEST_QUERIES),
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 结果已保存: {output_file}")


# ========== 主函数 ==========


async def main():
    """主函数"""
    logger.info("🚀 简化的嵌入对比测试")
    logger.info("=" * 60)

    tester = SimpleEmbeddingComparison()

    # 测试BGE-M3
    await tester.test_bge_m3()
    logger.info("")

    # 测试PatentSBERTa
    await tester.test_patent_sberta()
    logger.info("")

    # 对比
    tester.compare()
    logger.info("")

    # 保存
    tester.save_results()

    logger.info("=" * 60)
    logger.info("✅ 测试完成")


if __name__ == "__main__":
    asyncio.run(main())
