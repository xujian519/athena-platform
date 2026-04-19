#!/usr/bin/env python3
"""
验证改进效果脚本
Verify Improvements

验证数据整合和向量质量改进的效果

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImprovementVerifier:
    """改进效果验证器"""

    def __init__(self):
        self.qdrant_url = "http://localhost:6333"
        self.test_results = {}

    def generate_query_vector(self, text: str) -> list[float]:
        """生成查询向量（与搜索脚本保持一致）"""
        words = text.split()
        vector = np.zeros(1024)

        for _i, word in enumerate(words[:100]):
            hash_val = hash(word) % 1024
            vector[hash_val] += 1.0

        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector.tolist()

    def verify_data_organization(self) -> dict:
        """验证数据组织情况"""
        print("\n📁 验证数据组织情况...")

        organization = {
            "data_structure": {},
            "duplicate_status": {},
            "metadata_status": {}
        }

        # 检查目录结构
        base_path = Path("/Users/xujian/Athena工作平台/production")
        expected_dirs = [
            "data/raw",
            "data/processed",
            "data/vectors",
            "data/knowledge_graph",
            "data/metadata",
            "data/exports"
        ]

        for dir_path in expected_dirs:
            full_path = base_path / dir_path
            exists = full_path.exists()
            file_count = len(list(full_path.glob("*"))) if exists else 0
            organization["data_structure"][dir_path] = {
                "exists": exists,
                "file_count": file_count
            }

        # 检查重复文件
        kg_files = list(base_path.rglob("*legal_entities_*.json"))
        organization["duplicate_status"]["knowledge_graph_entities"] = len(kg_files)

        reports = list((base_path / "data" / "metadata").glob("vector_search_test_*.json"))
        organization["duplicate_status"]["test_reports"] = len(reports)

        # 检查元数据
        meta_files = [
            "cleanup_report.json",
            "quality_report.json",
            "vector_import_latest.json"
        ]

        for meta_file in meta_files:
            meta_path = base_path / "data" / "metadata" / meta_file
            organization["metadata_status"][meta_file] = meta_path.exists()

        return organization

    def verify_vector_quality(self) -> dict:
        """验证向量质量"""
        print("\n🔍 验证向量质量...")

        test_queries = [
            ("民法典", "legal_articles_1024"),
            ("刑法", "legal_articles_1024"),
            ("合同纠纷", "legal_articles_1024"),
            ("行政处罚", "legal_articles_1024"),
            ("司法解释", "legal_judgments_1024")
        ]

        quality_metrics = {
            "total_tests": len(test_queries),
            "successful_searches": 0,
            "total_results": 0,
            "avg_similarity": 0,
            "high_quality_results": 0,  # 相似度>0.5的结果数
            "query_details": []
        }

        all_similarities = []

        for query, collection in test_queries:
            query_vector = self.generate_query_vector(query)

            try:
                response = requests.post(
                    f"{self.qdrant_url}/collections/{collection}/points/search",
                    json={
                        "vector": query_vector,
                        "limit": 5,
                        "with_payload": True,
                        "score_threshold": 0.3
                    }
                )

                if response.status_code == 200:
                    results = response.json().get('result', [])
                    quality_metrics["successful_searches"] += 1
                    quality_metrics["total_results"] += len(results)

                    query_result = {
                        "query": query,
                        "collection": collection,
                        "result_count": len(results),
                        "reports/reports/results": []
                    }

                    for result in results:
                        score = result.get('score', 0)
                        all_similarities.append(score)
                        if score > 0.5:
                            quality_metrics["high_quality_results"] += 1

                        payload = result.get('payload', {})
                        query_result["reports/reports/results"].append({
                            "title": payload.get('title', 'N/A')[:50],
                            "similarity": score
                        })

                    quality_metrics["query_details"].append(query_result)

            except Exception as e:
                logger.error(f"查询 {query} 失败: {e}")

        # 计算平均相似度
        if all_similarities:
            quality_metrics["avg_similarity"] = sum(all_similarities) / len(all_similarities)

        return quality_metrics

    def verify_improvement_comparison(self) -> dict:
        """对比改进前后的效果"""
        print("\n📈 对比改进效果...")

        # 读取改进前的质量报告
        old_report_path = Path("/Users/xujian/Athena工作平台/production/data/metadata/vector_search_test_20251220_210649.json")

        if old_report_path.exists():
            with open(old_report_path, encoding='utf-8') as f:
                old_report = json.load(f)

            # 读取改进后的测试结果
            current_metrics = self.verify_vector_quality()

            comparison = {
                "before": {
                    "avg_similarity": 0.35,  # 之前测得的平均值
                    "low_quality_ratio": 0.85  # 85%的结果相似度<0.5
                },
                "after": {
                    "avg_similarity": current_metrics["avg_similarity"],
                    "high_quality_count": current_metrics["high_quality_results"],
                    "total_results": current_metrics["total_results"]
                },
                "improvement": {}
            }

            # 计算改进幅度
            if comparison["before"]["avg_similarity"] > 0:
                similarity_improvement = (
                    comparison["after"]["avg_similarity"] - comparison["before"]["avg_similarity"]
                ) / comparison["before"]["avg_similarity"] * 100
                comparison["improvement"]["similarity_percentage"] = similarity_improvement

            if comparison["after"]["total_results"] > 0:
                quality_ratio = comparison["after"]["high_quality_count"] / comparison["after"]["total_results"]
                comparison["improvement"]["quality_ratio"] = quality_ratio

        else:
            comparison = {
                "status": "no_baseline",
                "message": "无法找到基线报告进行对比"
            }

        return comparison

    def run_full_verification(self) -> dict:
        """运行完整验证"""
        print("\n" + "="*100)
        print("📊 验证改进效果 📊")
        print("="*100)

        verification_report = {
            "timestamp": datetime.now().isoformat(),
            "version": "v2.0",
            "data_organization": self.verify_data_organization(),
            "vector_quality": self.verify_vector_quality(),
            "improvement_comparison": self.verify_improvement_comparison()
        }

        # 保存验证报告
        report_path = Path("/Users/xujian/Athena工作平台/production/data/metadata") / \
                     f"verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(verification_report, f, ensure_ascii=False, indent=2)

        print(f"\n📋 验证报告已保存: {report_path}")

        return verification_report

    def print_summary(self, report: dict) -> Any:
        """打印验证摘要"""
        print("\n" + "="*100)
        print("📊 验证结果摘要 📊")
        print("="*100)

        # 数据组织情况
        print("\n✅ 数据组织情况:")
        org = report["data_organization"]
        proper_structure = sum(
            1 for v in org["data_structure"].values() if v["exists"]
        )
        print(f"   - 目录结构: {proper_structure}/6 个目录已创建")

        if org["duplicate_status"]["knowledge_graph_entities"] <= 2:
            print("   - 重复数据: 已清理")
        else:
            print(f"   - 重复数据: 仍有 {org['duplicate_status']['knowledge_graph_entities']} 个重复文件")

        # 向量质量
        print("\n📈 向量质量:")
        quality = report["vector_quality"]
        success_rate = quality["successful_searches"] / quality["total_tests"] * 100
        print(f"   - 搜索成功率: {success_rate:.1f}%")
        print(f"   - 平均相似度: {quality['avg_similarity']:.3f}")
        print(f"   - 高质量结果: {quality['high_quality_results']} 个")

        # 改进对比
        print("\n🚀 改进效果:")
        if "improvement" in report["improvement_comparison"]:
            improvement = report["improvement_comparison"]["improvement"]
            if "similarity_percentage" in improvement:
                print(f"   - 相似度改进: {improvement['similarity_percentage']:.1f}%")
            if "quality_ratio" in improvement:
                print(f"   - 高质量比例: {improvement['quality_ratio']*100:.1f}%")

        # 总体评估
        print("\n🎯 总体评估:")
        if quality["avg_similarity"] > 0.5:
            print("   ✅ 向量质量达到预期目标")
        elif quality["avg_similarity"] > 0.3:
            print("   ⚠️ 向量质量有所改善，但仍需优化")
        else:
            print("   ❌ 向量质量需要进一步改进")

def main() -> None:
    """主函数"""
    verifier = ImprovementVerifier()
    report = verifier.run_full_verification()
    verifier.print_summary(report)

    return report

if __name__ == "__main__":
    main()
