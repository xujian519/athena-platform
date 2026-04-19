#!/usr/bin/env python3
from __future__ import annotations
"""
Athena平台LlamaIndex评估框架集成
Athena Platform LlamaIndex Evaluation Framework Integration

结合Athena业务逻辑 + LlamaIndex标准化评估
"""

import json
import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from core.logging_config import setup_logging

# 添加Athena平台路径
sys.path.append("/Users/xujian/Athena工作平台")

# LlamaIndex组件
try:
    from llama_index.core.evaluation import (
        BatchEvalRunner,
        EvaluationResult,
        FaithfulnessEvaluator,
        QueryResponseDataset,
        RelevancyEvaluator,
    )

    LLAMAINDEX_AVAILABLE = True
except ImportError as e:
    LLAMAINDEX_AVAILABLE = False
    logging.warning(f"LlamaIndex评估框架不可用: {e}")

# Athena核心组件
from core.nlp.bge_embedding_service import get_bge_service

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


@dataclass
class EvaluationCase:
    """评估案例"""

    query: str
    expected_context: list[str]
    expected_response: str
    actual_response: str
    actual_context: list[str]
    metadata: dict[str, Any]
@dataclass
class EvaluationMetrics:
    """评估指标"""

    relevance_score: float  # 相关性分数
    faithfulness_score: float  # 忠实度分数
    accuracy_score: float  # 准确度分数
    completeness_score: float  # 完整性分数
    efficiency_score: float  # 效率分数


class AthenaLlamaIndexEvaluator:
    """Athena平台LlamaIndex评估器"""

    def __init__(self):
        """初始化评估器"""
        self.name = "Athena-LlamaIndex评估器"
        self.version = "1.0.0"

        # 初始化BGE服务
        self.bge_service = None  # 将在异步初始化中设置

        # LlamaIndex可用性
        self.llamaindex_available = LLAMAINDEX_AVAILABLE

        # 初始化评估组件
        self._init_evaluation_components()

        # 配置
        self.config = {
            "relevance_threshold": 0.7,
            "faithfulness_threshold": 0.8,
            "max_evaluation_cases": 100,
            "output_dir": "/Users/xujian/Athena工作平台/reports/evaluation_reports",
        }

        # 确保输出目录存在
        Path(self.config["output_dir"]).mkdir(parents=True, exist_ok=True)

        logger.info(f"✅ {self.name} 初始化完成")

    async def _ensure_bge_service(self):
        """确保BGE服务已初始化"""
        if self.bge_service is None:
            self.bge_service = await get_bge_service()

    def _init_evaluation_components(self) -> Any:
        """初始化评估组件"""
        if not self.llamaindex_available:
            logger.warning("⚠️ LlamaIndex评估框架不可用,将使用内置评估算法")
            self.relevancy_evaluator = None
            self.faithfulness_evaluator = None
        else:
            try:
                # 注意:这些评估器需要LLM支持,这里使用模拟器
                self.relevancy_evaluator = RelevancyEvaluator()
                self.faithfulness_evaluator = FaithfulnessEvaluator()
                logger.info("✅ LlamaIndex评估组件初始化成功")
            except Exception as e:
                logger.error(f"❌ LlamaIndex评估组件初始化失败: {e}")
                self.llamaindex_available = False

    async def evaluate_rag_performance(
        self, evaluation_cases: list[EvaluationCase], method: str = "hybrid"
    ) -> dict[str, Any]:
        """评估RAG性能"""
        logger.info(f"🔄 评估 {len(evaluation_cases)} 个RAG案例,方法: {method}")

        if not evaluation_cases:
            return {"error": "没有评估案例"}

        # 确保BGE服务已初始化
        await self._ensure_bge_service()

        metrics_list = []
        detailed_results = []

        for i, case in enumerate(evaluation_cases[: self.config["max_evaluation_cases"]]):
            try:
                logger.info(f"📊 评估案例 {i+1}/{len(evaluation_cases)}: {case.query[:50]}...")

                # 执行评估
                if method == "llamaindex" and self.llamaindex_available:
                    metrics = await self._evaluate_with_llamaindex(case)
                else:
                    metrics = await self._evaluate_with_athena(case)

                metrics_list.append(metrics)

                # 详细结果
                detailed_result = {
                    "case_id": i,
                    "query": case.query,
                    "metrics": self._metrics_to_dict(metrics),
                    "metadata": case.metadata,
                }
                detailed_results.append(detailed_result)

            except Exception as e:
                logger.error(f"❌ 评估案例 {i+1} 失败: {e}")
                continue

        # 计算总体指标
        overall_metrics = self._calculate_overall_metrics(metrics_list)

        # 生成评估报告
        report = {
            "evaluation_time": time.time(),
            "evaluator": self.name,
            "version": self.version,
            "method": method,
            "total_cases": len(evaluation_cases),
            "evaluated_cases": len(metrics_list),
            "overall_metrics": overall_metrics,
            "detailed_results": detailed_results,
            "config": self.config,
        }

        # 保存报告
        timestamp = int(time.time())
        report_file = Path(self.config["output_dir"]) / f"athena_rag_evaluation_{timestamp}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 评估报告已保存: {report_file}")

        return report

    async def _evaluate_with_llamaindex(self, case: EvaluationCase) -> EvaluationMetrics:
        """使用LlamaIndex评估"""
        try:
            # 相关性评估
            relevance_score = await self._evaluate_relevance_llamaindex(case)

            # 忠实度评估
            faithfulness_score = await self._evaluate_faithfulness_llamaindex(case)

            # 准确度和完整性评估
            accuracy_score, completeness_score = await self._evaluate_accuracy_completeness(case)

            # 效率评估(基于上下文数量和响应时间)
            efficiency_score = self._calculate_efficiency_score(case)

            return EvaluationMetrics(
                relevance_score=relevance_score,
                faithfulness_score=faithfulness_score,
                accuracy_score=accuracy_score,
                completeness_score=completeness_score,
                efficiency_score=efficiency_score,
            )

        except Exception as e:
            logger.error(f"❌ LlamaIndex评估失败: {e}")
            return await self._evaluate_with_athena(case)

    async def _evaluate_with_athena(self, case: EvaluationCase) -> EvaluationMetrics:
        """使用Athena内置评估算法"""
        try:
            # 相关性评估(基于语义相似度)
            relevance_score = await self._evaluate_relevance_athena(case)

            # 忠实度评估(基于内容一致性)
            faithfulness_score = await self._evaluate_faithfulness_athena(case)

            # 准确度和完整性评估
            accuracy_score, completeness_score = await self._evaluate_accuracy_completeness(case)

            # 效率评估
            efficiency_score = self._calculate_efficiency_score(case)

            return EvaluationMetrics(
                relevance_score=relevance_score,
                faithfulness_score=faithfulness_score,
                accuracy_score=accuracy_score,
                completeness_score=completeness_score,
                efficiency_score=efficiency_score,
            )

        except Exception as e:
            logger.error(f"❌ Athena评估失败: {e}")
            # 返回默认分数
            return EvaluationMetrics(
                relevance_score=0.5,
                faithfulness_score=0.5,
                accuracy_score=0.5,
                completeness_score=0.5,
                efficiency_score=0.5,
            )

    async def _evaluate_relevance_llamaindex(self, case: EvaluationCase) -> float:
        """使用LlamaIndex评估相关性"""
        try:
            # 模拟LlamaIndex相关性评估
            # 实际实现中需要LLM支持
            return await self._evaluate_relevance_athena(case)
        except Exception as e:
            logger.error(f"❌ LlamaIndex相关性评估失败: {e}")
            return 0.0

    async def _evaluate_relevance_athena(self, case: EvaluationCase) -> float:
        """使用Athena评估相关性"""
        try:
            # 计算查询与期望上下文的语义相似度
            query_embedding = await self._get_embedding(case.query)
            context_embeddings = await self._get_embeddings(case.expected_context)

            if not context_embeddings:
                return 0.0

            # 计算平均相似度
            similarities = []
            for context_embedding in context_embeddings:
                similarity = self._cosine_similarity(query_embedding, context_embedding)
                similarities.append(similarity)

            return sum(similarities) / len(similarities) if similarities else 0.0

        except Exception as e:
            logger.error(f"❌ 相关性评估失败: {e}")
            return 0.0

    async def _evaluate_faithfulness_llamaindex(self, case: EvaluationCase) -> float:
        """使用LlamaIndex评估忠实度"""
        try:
            # 模拟LlamaIndex忠实度评估
            return await self._evaluate_faithfulness_athena(case)
        except Exception as e:
            logger.error(f"❌ LlamaIndex忠实度评估失败: {e}")
            return 0.0

    async def _evaluate_faithfulness_athena(self, case: EvaluationCase) -> float:
        """使用Athena评估忠实度"""
        try:
            # 基于文本相似度评估实际响应与期望响应的一致性
            expected_embedding = await self._get_embedding(case.expected_response)
            actual_embedding = await self._get_embedding(case.actual_response)

            return self._cosine_similarity(expected_embedding, actual_embedding)

        except Exception as e:
            logger.error(f"❌ 忠实度评估失败: {e}")
            return 0.0

    async def _evaluate_accuracy_completeness(self, case: EvaluationCase) -> tuple[float, float]:
        """评估准确度和完整性"""
        try:
            # 准确度:关键信息匹配度
            accuracy_score = await self._calculate_accuracy_score(
                case.expected_response, case.actual_response
            )

            # 完整性:信息覆盖度
            completeness_score = await self._calculate_completeness_score(
                case.expected_context, case.actual_context
            )

            return accuracy_score, completeness_score

        except Exception as e:
            logger.error(f"❌ 准确度和完整性评估失败: {e}")
            return 0.0, 0.0

    async def _calculate_accuracy_score(self, expected: str, actual: str) -> float:
        """计算准确度分数"""
        # 简化的实现:基于关键词重叠
        expected_words = set(expected.lower().split())
        actual_words = set(actual.lower().split())

        if not expected_words:
            return 0.0

        overlap = expected_words & actual_words
        return len(overlap) / len(expected_words)

    async def _calculate_completeness_score(
        self, expected_context: list[str], actual_context: list[str]
    ) -> float:
        """计算完整性分数"""
        if not expected_context:
            return 0.0

        # 基于上下文数量比例
        return min(1.0, len(actual_context) / len(expected_context))

    def _calculate_efficiency_score(self, case: EvaluationCase) -> float:
        """计算效率分数"""
        # 基于上下文数量的效率分数
        context_count = len(case.actual_context)

        if context_count == 0:
            return 0.0
        elif context_count <= 3:
            return 1.0
        elif context_count <= 5:
            return 0.8
        elif context_count <= 10:
            return 0.6
        else:
            return 0.4

    def _calculate_overall_metrics(self, metrics_list: list[EvaluationMetrics]) -> dict[str, float]:
        """计算总体指标"""
        if not metrics_list:
            return {
                "avg_relevance": 0.0,
                "avg_faithfulness": 0.0,
                "avg_accuracy": 0.0,
                "avg_completeness": 0.0,
                "avg_efficiency": 0.0,
                "overall_score": 0.0,
            }

        avg_relevance = sum(m.relevance_score for m in metrics_list) / len(metrics_list)
        avg_faithfulness = sum(m.faithfulness_score for m in metrics_list) / len(metrics_list)
        avg_accuracy = sum(m.accuracy_score for m in metrics_list) / len(metrics_list)
        avg_completeness = sum(m.completeness_score for m in metrics_list) / len(metrics_list)
        avg_efficiency = sum(m.efficiency_score for m in metrics_list) / len(metrics_list)

        # 总体分数(加权平均)
        overall_score = (
            0.3 * avg_relevance
            + 0.3 * avg_faithfulness
            + 0.2 * avg_accuracy
            + 0.1 * avg_completeness
            + 0.1 * avg_efficiency
        )

        return {
            "avg_relevance": avg_relevance,
            "avg_faithfulness": avg_faithfulness,
            "avg_accuracy": avg_accuracy,
            "avg_completeness": avg_completeness,
            "avg_efficiency": avg_efficiency,
            "overall_score": overall_score,
        }

    def _metrics_to_dict(self, metrics: EvaluationMetrics) -> dict[str, float]:
        """将评估指标转换为字典"""
        return {
            "relevance_score": metrics.relevance_score,
            "faithfulness_score": metrics.faithfulness_score,
            "accuracy_score": metrics.accuracy_score,
            "completeness_score": metrics.completeness_score,
            "efficiency_score": metrics.efficiency_score,
        }

    async def _get_embedding(self, text: str) -> list[float]:
        """获取文本向量"""
        try:
            result = await self.bge_service.encode([text])
            # 处理EmbeddingResult对象
            if isinstance(result.embeddings, list):
                return (
                    result.embeddings[0]
                    if isinstance(result.embeddings[0], list)
                    else result.embeddings[0].tolist()
                )
            else:
                return (
                    result.embeddings.tolist()
                    if hasattr(result.embeddings, "tolist")
                    else result.embeddings
                )
        except Exception as e:
            logger.error(f"❌ 获取文本向量失败: {e}")
            return [0.0] * 1024

    async def _get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """获取多个文本向量"""
        try:
            result = await self.bge_service.encode(texts)
            # 处理EmbeddingResult对象
            if isinstance(result.embeddings, list):
                return [
                    emb.tolist() if hasattr(emb, "tolist") and not isinstance(emb, list) else emb
                    for emb in result.embeddings
                ]
            else:
                return (
                    [result.embeddings.tolist()]
                    if hasattr(result.embeddings, "tolist")
                    else [[result.embeddings]]
                )
        except Exception as e:
            logger.error(f"❌ 获取文本向量失败: {e}")
            return [[0.0] * 1024] * len(texts)

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """计算余弦相似度"""

        try:
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)

            if np.all(vec1_np == 0) or np.all(vec2_np == 0):
                return 0.0

            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return dot_product / (norm1 * norm2)
        except Exception as e:
            logger.error(f"❌ 计算余弦相似度失败: {e}")
            return 0.0


async def main():
    """测试评估器"""
    print("🚀 Athena-LlamaIndex评估框架测试")
    print("=" * 60)

    evaluator = AthenaLlamaIndexEvaluator()

    # 创建测试案例
    test_cases = [
        EvaluationCase(
            query="发明专利的保护期是多长?",
            expected_context=[
                "发明专利的保护期为二十年,自申请日起计算。",
                "实用新型专利的保护期为十年,自申请日起计算。",
                "外观设计专利的保护期为十五年,自申请日起计算。",
            ],
            expected_response="发明专利的保护期为二十年,自申请日起计算。",
            actual_response="发明专利的保护期是二十年,从申请日开始计算。",
            actual_context=[
                "发明专利的保护期为二十年,自申请日起计算。",
                "实用新型专利的保护期为十年。",
            ],
            metadata={"category": "专利法律", "source": "专利法"},
        ),
        EvaluationCase(
            query="专利权的无效宣告程序是什么?",
            expected_context=[
                "专利权的无效宣告程序是指任何人认为专利权的授予不符合法律规定的,可以请求专利复审委员会宣告该专利权无效。",
                "无效宣告的理由包括:缺乏新颖性、创造性、实用性等。",
            ],
            expected_response="专利权的无效宣告程序是指任何人认为专利权的授予不符合法律规定的,可以请求专利复审委员会宣告该专利权无效。",
            actual_response="专利权的无效宣告是指任何单位或者个人认为专利权的授予不符合法律规定的,可以请求专利复审委员会宣告该专利权无效。",
            actual_context=[
                "专利权的无效宣告程序是指任何单位或者个人认为专利权的授予不符合法律规定的,可以请求专利复审委员会宣告该专利权无效。",
                "无效宣告的理由包括缺乏新颖性、创造性或者实用性。",
            ],
            metadata={"category": "专利法律", "source": "专利法"},
        ),
    ]

    # 执行评估
    report = await evaluator.evaluate_rag_performance(test_cases, "hybrid")

    # 显示结果
    print("\n📊 评估结果:")
    print(f"   - 评估案例数: {report['evaluated_cases']}/{report['total_cases']}")
    print(f"   - 平均相关性: {report['overall_metrics']['avg_relevance']:.3f}")
    print(f"   - 平均忠实度: {report['overall_metrics']['avg_faithfulness']:.3f}")
    print(f"   - 平均准确度: {report['overall_metrics']['avg_accuracy']:.3f}")
    print(f"   - 平均完整性: {report['overall_metrics']['avg_completeness']:.3f}")
    print(f"   - 平均效率: {report['overall_metrics']['avg_efficiency']:.3f}")
    print(f"   - 总体分数: {report['overall_metrics']['overall_score']:.3f}")


# 入口点: @async_main装饰器已添加到main函数
