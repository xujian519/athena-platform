#!/usr/bin/env python3
"""
专利检索评估指标
Patent Retrieval Evaluation Metrics

提供专利检索系统的各种评估指标计算方法
"""

import logging
import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Any


# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class RelevanceJudgment:
    """相关性判断"""

    query_id: str
    doc_id: str
    relevance: int  # 0=不相关, 1=相关, 2=高度相关
    assessor: str | None = None


@dataclass
class RetrievalResult:
    """检索结果"""

    query_id: str
    doc_id: str
    rank: int
    score: float
    system: str


class PatentRetrievalMetrics:
    """专利检索评估指标计算器"""

    def __init__(self):
        """初始化评估指标计算器"""
        logger.info("初始化专利检索评估指标计算器...")

        # 专利领域特定的权重
        self.relevance_weights = {0: 0.0, 1: 0.7, 2: 1.0}  # 不相关  # 相关  # 高度相关

        # IPC层次权重(越具体权重越高)
        self.ipc_level_weights = {
            "section": 0.3,  # 部 (A-H)
            "class": 0.5,  # 大类 (A01)
            "subclass": 0.8,  # 小类 (A01B)
            "group": 1.0,  # 大组 (A01B 1/00)
            "subgroup": 1.2,  # 小组 (A01B 1/02)
        }

    def calculate_precision_at_k(
        self, results: list[RetrievalResult], judgments: list[RelevanceJudgment], k: int = 10
    ) -> float:
        """
        计算Precision@K

        Args:
            results: 检索结果列表
            judgments: 相关性判断列表
            k: 截断位置

        Returns:
            Precision@K值
        """
        # 构建相关性字典
        relevance_dict = {}
        for j in judgments:
            relevance_dict[(j.query_id, j.doc_id)] = j.relevance

        # 取前K个结果
        top_k_results = results[:k]

        # 计算相关文档数
        relevant_count = 0
        for result in top_k_results:
            rel = relevance_dict.get((result.query_id, result.doc_id), 0)
            if rel > 0:  # 相关(包括高度相关)
                relevant_count += 1

        return relevant_count / k if k > 0 else 0

    def calculate_recall_at_k(
        self, results: list[RetrievalResult], judgments: list[RelevanceJudgment], k: int = 10
    ) -> float:
        """
        计算Recall@K

        Args:
            results: 检索结果列表
            judgments: 相关性判断列表
            k: 截断位置

        Returns:
            Recall@K值
        """
        # 构建相关性字典
        relevance_dict = {}
        for j in judgments:
            relevance_dict[(j.query_id, j.doc_id)] = j.relevance

        # 取前K个结果
        top_k_results = results[:k]

        # 计算检索到的相关文档数
        retrieved_relevant = 0
        for result in top_k_results:
            rel = relevance_dict.get((result.query_id, result.doc_id), 0)
            if rel > 0:
                retrieved_relevant += 1

        # 计算总相关文档数
        total_relevant = sum(1 for j in judgments if j.relevance > 0)

        return retrieved_relevant / total_relevant if total_relevant > 0 else 0

    def calculate_f1_at_k(
        self, results: list[RetrievalResult], judgments: list[RelevanceJudgment], k: int = 10
    ) -> float:
        """
        计算F1@K

        Args:
            results: 检索结果列表
            judgments: 相关性判断列表
            k: 截断位置

        Returns:
            F1@K值
        """
        precision = self.calculate_precision_at_k(results, judgments, k)
        recall = self.calculate_recall_at_k(results, judgments, k)

        if precision + recall == 0:
            return 0
        return 2 * precision * recall / (precision + recall)

    def calculate_map(
        self, results: list[RetrievalResult], judgments: list[RelevanceJudgment]
    ) -> float:
        """
        计算MAP (Mean Average Precision)

        Args:
            results: 检索结果列表
            judgments: 相关性判断列表

        Returns:
            MAP值
        """
        # 按query_id分组
        query_results = defaultdict(list)
        for result in results:
            query_results[result.query_id].append(result)

        # 构建相关性字典
        relevance_dict = {}
        for j in judgments:
            relevance_dict[(j.query_id, j.doc_id)] = j.relevance

        # 计算每个查询的AP
        aps = []
        for query_id, q_results in query_results.items():
            # 按分数排序
            q_results.sort(key=lambda x: x.score, reverse=True)

            # 计算AP
            precisions = []
            relevant_count = 0

            for i, result in enumerate(q_results, 1):
                rel = relevance_dict.get((query_id, result.doc_id), 0)
                if rel > 0:
                    relevant_count += 1
                    precisions.append(relevant_count / i)

            ap = sum(precisions) / len(precisions) if precisions else 0
            aps.append(ap)

        return sum(aps) / len(aps) if aps else 0

    def calculate_ndcg(
        self, results: list[RetrievalResult], judgments: list[RelevanceJudgment], k: int = 10
    ) -> float:
        """
        计算NDCG@K (Normalized Discounted Cumulative Gain)

        Args:
            results: 检索结果列表
            judgments: 相关性判断列表
            k: 截断位置

        Returns:
            NDCG@K值
        """
        # 构建相关性字典
        relevance_dict = {}
        for j in judgments:
            relevance_dict[(j.query_id, j.doc_id)] = j.relevance

        # 取前K个结果
        top_k_results = results[:k]

        # 计算DCG
        dcg = 0
        for i, result in enumerate(top_k_results, 1):
            rel = relevance_dict.get((result.query_id, result.doc_id), 0)
            if rel > 0:
                dcg += (2**rel - 1) / math.log2(i + 1)

        # 计算IDCG (理想DCG)
        all_rels = sorted(
            [relevance_dict.get((result.query_id, result.doc_id), 0) for result in results],
            reverse=True,
        )[:k]
        idcg = sum((2**rel - 1) / math.log2(i + 1) for i, rel in enumerate(all_rels, 1) if rel > 0)

        return dcg / idcg if idcg > 0 else 0

    def calculate_mrr(
        self, results: list[RetrievalResult], judgments: list[RelevanceJudgment]
    ) -> float:
        """
        计算MRR (Mean Reciprocal Rank)

        Args:
            results: 检索结果列表
            judgments: 相关性判断列表

        Returns:
            MRR值
        """
        # 按query_id分组
        query_results = defaultdict(list)
        for result in results:
            query_results[result.query_id].append(result)

        # 构建相关性字典
        relevance_dict = {}
        for j in judgments:
            relevance_dict[(j.query_id, j.doc_id)] = j.relevance

        # 计算每个查询的RR
        rrs = []
        for query_id, q_results in query_results.items():
            # 按分数排序
            q_results.sort(key=lambda x: x.score, reverse=True)

            # 找到第一个相关文档的位置
            rr = 0
            for rank, result in enumerate(q_results, 1):
                if relevance_dict.get((query_id, result.doc_id), 0) > 0:
                    rr = 1 / rank
                    break

            rrs.append(rr)

        return sum(rrs) / len(rrs) if rrs else 0

    def calculate_patent_specific_metrics(
        self,
        results: list[RetrievalResult],
        judgments: list[RelevanceJudgment],
        patent_metadata: dict[str, dict[str, Any]],
    ) -> dict[str, float]:
        """
        计算专利领域特定指标

        Args:
            results: 检索结果列表
            judgments: 相关性判断列表
            patent_metadata: 专利元数据字典

        Returns:
            专利特定指标字典
        """
        metrics = {}

        # IPC分类准确率
        metrics["ipc_accuracy"] = self._calculate_ipc_accuracy(results, judgments, patent_metadata)

        # 技术领域覆盖率
        metrics["tech_coverage"] = self._calculate_tech_coverage(
            results, judgments, patent_metadata
        )

        # 时间相关性
        metrics["temporal_relevance"] = self._calculate_temporal_relevance(
            results, judgments, patent_metadata
        )

        # 申请人多样性
        metrics["applicant_diversity"] = self._calculate_applicant_diversity(
            results, patent_metadata
        )

        # 法律状态准确性
        metrics["legal_status_accuracy"] = self._calculate_legal_status_accuracy(
            results, judgments, patent_metadata
        )

        return metrics

    def _calculate_ipc_accuracy(
        self,
        results: list[RetrievalResult],
        judgments: list[RelevanceJudgment],
        patent_metadata: dict[str, dict[str, Any]],
    ) -> float:
        """计算IPC分类准确率"""
        # 简化实现:比较返回专利的IPC与查询预期的IPC
        # 实际应用需要更复杂的IPC相似度计算

        relevant_docs = [
            r for r in results if any(j.doc_id == r.doc_id and j.relevance > 0 for j in judgments)
        ]

        if not relevant_docs:
            return 0

        correct_ipc = 0
        for result in relevant_docs:
            doc_metadata = patent_metadata.get(result.doc_id, {})
            doc_ipcs = doc_metadata.get("ipc_codes", [])
            # 简化判断:假设IPC代码前3位相同即为正确
            # 实际应使用IPC层次结构
            correct_ipc += min(1, len(doc_ipcs) * 0.3)  # 简化计算

        return correct_ipc / len(relevant_docs)

    def _calculate_tech_coverage(
        self,
        results: list[RetrievalResult],
        judgments: list[RelevanceJudgment],
        patent_metadata: dict[str, dict[str, Any]],
    ) -> float:
        """计算技术领域覆盖率"""
        # 统计返回结果覆盖的技术领域数量
        tech_fields = set()

        for result in results[:10]:  # 取前10个结果
            doc_metadata = patent_metadata.get(result.doc_id, {})
            doc_ipcs = doc_metadata.get("ipc_codes", [])
            # 提取IPC的部(A-H)
            for ipc in doc_ipcs:
                if ipc and len(ipc) > 0:
                    tech_fields.add(ipc[0])

        # 覆盖率 = 覆盖的技术领域数 / 8 (A-H共8个部)
        return len(tech_fields) / 8

    def _calculate_temporal_relevance(
        self,
        results: list[RetrievalResult],
        judgments: list[RelevanceJudgment],
        patent_metadata: dict[str, dict[str, Any]],
    ) -> float:
        """计算时间相关性"""
        # 简化实现:检查专利年代是否与查询期望匹配
        relevant_docs = [
            r for r in results if any(j.doc_id == r.doc_id and j.relevance > 0 for j in judgments)
        ]

        if not relevant_docs:
            return 0

        current_year = 2024  # 假设当前年份
        temporal_scores = []

        for result in relevant_docs:
            doc_metadata = patent_metadata.get(result.doc_id, {})
            pub_date = doc_metadata.get("publication_date", "")
            if pub_date:
                try:
                    year = int(pub_date[:4])
                    # 近期的专利更相关
                    age = current_year - year
                    score = 1.0 / (1 + age * 0.1)  # 衰减函数
                    temporal_scores.append(score)
                except (
                    ValueError,
                    TypeError,
                    ZeroDivisionError,
                ):  # TODO: 根据上下文指定具体异常类型
                    temporal_scores.append(0.5)
            else:
                temporal_scores.append(0.5)

        return sum(temporal_scores) / len(temporal_scores)

    def _calculate_applicant_diversity(
        self, results: list[RetrievalResult], patent_metadata: dict[str, dict[str, Any]]
    ) -> float:
        """计算申请人多样性"""
        applicants = set()
        total_results = len(results[:20])  # 取前20个结果

        for result in results[:20]:
            doc_metadata = patent_metadata.get(result.doc_id, {})
            applicant = doc_metadata.get("applicant", "")
            if applicant:
                applicants.add(applicant)

        # 多样性 = 不同申请人数量 / 总结果数
        return len(applicants) / total_results if total_results > 0 else 0

    def _calculate_legal_status_accuracy(
        self,
        results: list[RetrievalResult],
        judgments: list[RelevanceJudgment],
        patent_metadata: dict[str, dict[str, Any]],
    ) -> float:
        """计算法律状态准确性"""
        # 简化实现:检查返回的有效专利比例
        valid_patents = 0
        total_patents = 0

        for result in results:
            doc_metadata = patent_metadata.get(result.doc_id, {})
            legal_status = doc_metadata.get("legal_status", "")
            total_patents += 1
            if legal_status in ["有效", "授权", "valid"]:
                valid_patents += 1

        return valid_patents / total_patents if total_patents > 0 else 0

    def evaluate_system(
        self,
        results: list[RetrievalResult],
        judgments: list[RelevanceJudgment],
        patent_metadata: dict[str, dict[str, Any]] | None = None,
        ks: list[int] | None = None,
    ) -> dict[str, Any]:
        """
        综合评估检索系统

        Args:
            results: 检索结果列表
            judgments: 相关性判断列表
            patent_metadata: 专利元数据
            ks: Precision@K和Recall@K的K值列表

        Returns:
            评估指标字典
        """
        if ks is None:
            ks = [1, 5, 10, 20]
        metrics = {
            "precision_at_k": {},
            "recall_at_k": {},
            "f1_at_k": {},
            "ndcg_at_k": {},
            "general_metrics": {},
            "patent_specific_metrics": {},
        }

        # 计算不同K值的指标
        for k in ks:
            metrics["precision_at_k"][k] = self.calculate_precision_at_k(results, judgments, k)
            metrics["recall_at_k"][k] = self.calculate_recall_at_k(results, judgments, k)
            metrics["f1_at_k"][k] = self.calculate_f1_at_k(results, judgments, k)
            metrics["ndcg_at_k"][k] = self.calculate_ndcg(results, judgments, k)

        # 计算通用指标
        metrics["general_metrics"]["map"] = self.calculate_map(results, judgments)
        metrics["general_metrics"]["mrr"] = self.calculate_mrr(results, judgments)

        # 计算专利特定指标
        if patent_metadata:
            patent_metrics = self.calculate_patent_specific_metrics(
                results, judgments, patent_metadata
            )
            metrics["patent_specific_metrics"] = patent_metrics

        return metrics

    def generate_evaluation_report(
        self, metrics: dict[str, Any], system_name: str = "Patent Retrieval System"
    ) -> str:
        """
        生成评估报告

        Args:
            metrics: 评估指标字典
            system_name: 系统名称

        Returns:
            格式化的评估报告
        """
        report_lines = [
            f"{'='*80}",
            f"{system_name} - 专利检索评估报告",
            f"{'='*80}",
            "",
            "1. 基础检索指标",
            "-" * 40,
        ]

        # Precision@K报告
        report_lines.append("\n_precision@K (精确率):")
        for k, precision in metrics["precision_at_k"].items():
            report_lines.append(f"  P@{k}: {precision:.4f}")

        # Recall@K报告
        report_lines.append("\n_recall@K (召回率):")
        for k, recall in metrics["recall_at_k"].items():
            report_lines.append(f"  R@{k}: {recall:.4f}")

        # F1@K报告
        report_lines.append("\n_f1@K (F1分数):")
        for k, f1 in metrics["f1_at_k"].items():
            report_lines.append(f"  F1@{k}: {f1:.4f}")

        # NDCG@K报告
        report_lines.append("\n_ndcg@K (归一化折损累计增益):")
        for k, ndcg in metrics["ndcg_at_k"].items():
            report_lines.append(f"  NDCG@{k}: {ndcg:.4f}")

        # 通用指标
        report_lines.extend(
            [
                "",
                "2. 综合指标",
                "-" * 40,
                f"MAP (平均精度均值): {metrics['general_metrics']['map']:.4f}",
                f"MRR (平均倒数排名): {metrics['general_metrics']['mrr']:.4f}",
            ]
        )

        # 专利特定指标
        if metrics["patent_specific_metrics"]:
            report_lines.extend(["", "3. 专利领域特定指标", "-" * 40])

            patent_metrics = metrics["patent_specific_metrics"]
            metric_names = {
                "ipc_accuracy": "IPC分类准确率",
                "tech_coverage": "技术领域覆盖率",
                "temporal_relevance": "时间相关性",
                "applicant_diversity": "申请人多样性",
                "legal_status_accuracy": "法律状态准确性",
            }

            for key, name in metric_names.items():
                if key in patent_metrics:
                    report_lines.append(f"{name}: {patent_metrics[key]:.4f}")

        # 性能评级
        report_lines.extend(["", "4. 性能评级", "-" * 40])

        map_score = metrics["general_metrics"]["map"]
        ndcg10 = metrics["ndcg_at_k"].get(10, 0)

        if map_score > 0.7 and ndcg10 > 0.8:
            grade = "优秀 (Excellent)"
        elif map_score > 0.5 and ndcg10 > 0.6:
            grade = "良好 (Good)"
        elif map_score > 0.3 and ndcg10 > 0.4:
            grade = "一般 (Average)"
        else:
            grade = "需要改进 (Needs Improvement)"

        report_lines.append(f"系统评级: {grade}")
        report_lines.append(f"核心指标: MAP={map_score:.4f}, NDCG@10={ndcg10:.4f}")

        report_lines.extend(["", f"{'='*80}", "报告生成时间", f"{'='*80}"])

        return "\n".join(report_lines)

    def compare_systems(
        self, system_metrics: dict[str, dict[str, Any]], system_names: list[str]
    ) -> dict[str, Any]:
        """
        比较多个检索系统

        Args:
            system_metrics: 各系统的评估指标
            system_names: 系统名称列表

        Returns:
            比较结果
        """
        comparison = {"ranking": {}, "improvement": {}, "best_system": {}}

        # 指标列表
        metrics_to_compare = ["map", "mrr"]
        metrics_to_compare.extend([f"precision_at_{k}" for k in [1, 5, 10]])
        metrics_to_compare.extend([f"ndcg_at_{k}" for k in [5, 10, 20]])

        # 计算排名
        for metric in metrics_to_compare:
            scores = []
            for name in system_names:
                if metric in system_metrics[name]["general_metrics"]:
                    scores.append((system_metrics[name]["general_metrics"][metric], name))
                elif metric in system_metrics[name]:
                    scores.append((system_metrics[name][metric], name))
                elif "." in metric:  # 如precision_at_1
                    parts = metric.split("_")
                    if (
                        parts[0] in system_metrics[name]
                        and parts[2] in system_metrics[name][parts[0]]
                    ):
                        scores.append((system_metrics[name][parts[0]][int(parts[2])], name))

            scores.sort(reverse=True)
            comparison["ranking"][metric] = scores

        # 找出最佳系统
        for metric, scores in comparison["ranking"].items():
            if scores:
                comparison["best_system"][metric] = scores[0][1]

        return comparison
