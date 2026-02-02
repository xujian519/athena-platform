#!/usr/bin/env python3
"""
推理模式库分析器 - Pattern Library Analyzer
分析和可视化推理模式库

功能:
1. 加载推理模式库
2. 统计分析
3. 模式聚类
4. 可视化展示
5. 导出报告

版本: 1.0.0
创建时间: 2026-01-23
"""

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class PatternLibraryAnalyzer:
    """推理模式库分析器"""

    def __init__(self, patterns_file: str):
        """
        初始化分析器

        Args:
            patterns_file: 推理模式库JSON文件路径
        """
        self.patterns_file = Path(patterns_file)
        self.patterns: list[dict[str, Any]] = []
        self.statistics: dict[str, Any] = {}

        logger.info(f"📂 模式库文件: {self.patterns_file}")

    def load_patterns(self) -> bool:
        """
        加载推理模式库

        Returns:
            是否成功加载
        """
        logger.info("=" * 70)
        logger.info("📊 加载推理模式库...")
        logger.info("=" * 70)

        try:
            with open(self.patterns_file, encoding="utf-8") as f:
                self.patterns = json.load(f)

            logger.info(f"✅ 成功加载 {len(self.patterns):,} 个推理模式")
            return True

        except Exception as e:
            logger.error(f"❌ 加载失败: {e}")
            return False

    def analyze(self) -> dict[str, Any]:
        """
        执行完整分析

        Returns:
            分析结果
        """
        if not self.patterns:
            logger.error("❌ 模式库为空,请先加载")
            return {}

        logger.info("\n" + "=" * 70)
        logger.info("🔍 开始分析推理模式库...")
        logger.info("=" * 70)

        # 基础统计
        self.statistics["basic"] = self._basic_statistics()

        # 技术领域分析
        self.statistics["field_analysis"] = self._analyze_technical_fields()

        # 创造性等级分析
        self.statistics["creativity_analysis"] = self._analyze_creativity_levels()

        # 三步法完整性分析
        self.statistics["completeness_analysis"] = self._analyze_completeness()

        # 置信度分析
        self.statistics["confidence_analysis"] = self._analyze_confidence()

        # 模式聚类分析
        self.statistics["clustering_analysis"] = self._analyze_patterns_clustering()

        # 关键词提取
        self.statistics["keywords_analysis"] = self._extract_keywords()

        return self.statistics

    def _basic_statistics(self) -> dict[str, Any]:
        """基础统计"""
        total = len(self.patterns)

        field_counts = Counter(p["technical_field"] for p in self.patterns)
        conclusion_counts = Counter(p["conclusion"] for p in self.patterns)

        return {
            "total_patterns": total,
            "unique_fields": len(field_counts),
            "unique_sources": len({p["source_document"] for p in self.patterns}),
            "avg_confidence": (
                sum(p["confidence"] for p in self.patterns) / total if total > 0 else 0
            ),
            "field_distribution": dict(field_counts.most_common()),
            "conclusion_distribution": dict(conclusion_counts.most_common()),
        }

    def _analyze_technical_fields(self) -> dict[str, Any]:
        """技术领域分析"""
        field_patterns = defaultdict(list)

        for pattern in self.patterns:
            field = pattern["technical_field"]
            field_patterns[field].append(pattern)

        analysis = {}
        for field, patterns in field_patterns.items():
            field_stats = {
                "count": len(patterns),
                "avg_confidence": sum(p["confidence"] for p in patterns) / len(patterns),
                "creativity_distribution": dict(Counter(p["conclusion"] for p in patterns)),
                "has_step1": sum(1 for p in patterns if p.get("step1_distinguishing")),
                "has_step2": sum(1 for p in patterns if p.get("step2_problem")),
                "has_step3": sum(1 for p in patterns if p.get("step3_hint")),
            }

            analysis[field] = field_stats

        return analysis

    def _analyze_creativity_levels(self) -> dict[str, Any]:
        """创造性等级分析"""
        creativity_patterns = defaultdict(list)

        for pattern in self.patterns:
            conclusion = pattern["conclusion"]
            creativity_patterns[conclusion].append(pattern)

        analysis = {}
        for level, patterns in creativity_patterns.items():
            level_stats = {
                "count": len(patterns),
                "percentage": len(patterns) / len(self.patterns) * 100,
                "avg_confidence": sum(p["confidence"] for p in patterns) / len(patterns),
                "field_distribution": dict(Counter(p["technical_field"] for p in patterns)),
            }

            analysis[level] = level_stats

        return analysis

    def _analyze_completeness(self) -> dict[str, Any]:
        """三步法完整性分析"""
        completeness = {
            "complete_all_three": 0,
            "has_step1_and_step2": 0,
            "has_step2_and_step3": 0,
            "has_step1_and_step3": 0,
            "only_step1": 0,
            "only_step2": 0,
            "only_step3": 0,
        }

        for pattern in self.patterns:
            has_step1 = bool(pattern.get("step1_distinguishing"))
            has_step2 = bool(pattern.get("step2_problem"))
            has_step3 = bool(pattern.get("step3_hint"))

            if has_step1 and has_step2 and has_step3:
                completeness["complete_all_three"] += 1
            elif has_step1 and has_step2:
                completeness["has_step1_and_step2"] += 1
            elif has_step2 and has_step3:
                completeness["has_step2_and_step3"] += 1
            elif has_step1 and has_step3:
                completeness["has_step1_and_step3"] += 1
            elif has_step1:
                completeness["only_step1"] += 1
            elif has_step2:
                completeness["only_step2"] += 1
            elif has_step3:
                completeness["only_step3"] += 1

        return completeness

    def _analyze_confidence(self) -> dict[str, Any]:
        """置信度分析"""
        confidences = [p["confidence"] for p in self.patterns]

        if not confidences:
            return {}

        confidences.sort()

        return {
            "min": min(confidences),
            "max": max(confidences),
            "avg": sum(confidences) / len(confidences),
            "median": confidences[len(confidences) // 2],
            "distribution": {
                "high (>0.7)": sum(1 for c in confidences if c > 0.7),
                "medium (0.4-0.7)": sum(1 for c in confidences if 0.4 <= c <= 0.7),
                "low (<0.4)": sum(1 for c in confidences if c < 0.4),
            },
        }

    def _analyze_patterns_clustering(self) -> dict[str, Any]:
        """模式聚类分析"""
        # 基于技术领域和创造性等级进行聚类
        clusters = defaultdict(lambda: defaultdict(list))

        for pattern in self.patterns:
            field = pattern["technical_field"]
            conclusion = pattern["conclusion"]
            clusters[field][conclusion].append(pattern)

        analysis = {}
        for field, conclusions in clusters.items():
            analysis[field] = {
                conclusion: len(patterns) for conclusion, patterns in conclusions.items()
            }

        return analysis

    def _extract_keywords(self) -> dict[str, list[str]]:
        """提取关键词"""
        # 收集所有step1区别特征
        step1_features = []
        for pattern in self.patterns:
            if pattern.get("step1_distinguishing"):
                step1_features.extend(pattern["step1_distinguishing"])

        # 简单的关键词提取(频率统计)
        feature_counter = Counter(step1_features)

        return {
            "top_distinguishing_features": [
                {"feature": feature, "count": count}
                for feature, count in feature_counter.most_common(20)
            ]
        }

    def print_report(self) -> None:
        """打印分析报告"""
        logger.info("\n" + "=" * 70)
        logger.info("📊 推理模式库分析报告")
        logger.info("=" * 70)

        # 基础统计
        basic = self.statistics.get("basic", {})
        logger.info("\n📈 基础统计:")
        logger.info(f"  总模式数:       {basic.get('total_patterns', 0):,}")
        logger.info(f"  技术领域数:     {basic.get('unique_fields', 0)}")
        logger.info(f"  来源文档数:     {basic.get('unique_sources', 0)}")
        logger.info(f"  平均置信度:     {basic.get('avg_confidence', 0):.2%}")

        # 技术领域分布
        logger.info("\n🏭 技术领域分布:")
        field_dist = basic.get("field_distribution", {})
        for field, count in list(field_dist.items())[:10]:
            percentage = count / basic.get("total_patterns", 1) * 100
            logger.info(f"  {field}: {count:,} ({percentage:.1f}%)")

        # 创造性等级分布
        logger.info("\n🎯 创造性等级分布:")
        conclusion_dist = basic.get("conclusion_distribution", {})
        for level, count in conclusion_dist.items():
            percentage = count / basic.get("total_patterns", 1) * 100
            logger.info(f"  {level}: {count:,} ({percentage:.1f}%)")

        # 三步法完整性
        logger.info("\n📋 三步法完整性:")
        completeness = self.statistics.get("completeness_analysis", {})
        for category, count in completeness.items():
            if count > 0:
                percentage = count / basic.get("total_patterns", 1) * 100
                logger.info(f"  {category}: {count:,} ({percentage:.1f}%)")

        # 置信度分布
        logger.info("\n📊 置信度分布:")
        confidence = self.statistics.get("confidence_analysis", {})
        if confidence:
            logger.info(f"  最小值: {confidence.get('min', 0):.2%}")
            logger.info(f"  最大值: {confidence.get('max', 0):.2%}")
            logger.info(f"  平均值: {confidence.get('avg', 0):.2%}")
            logger.info(f"  中位数: {confidence.get('median', 0):.2%}")

        # 关键词
        logger.info("\n🔑 高频区别特征 (Top 10):")
        keywords = self.statistics.get("keywords_analysis", {})
        top_features = keywords.get("top_distinguishing_features", [])[:10]
        for item in top_features:
            logger.info(f"  {item['feature'][:50]}...: {item['count']}次")

        logger.info("\n" + "=" * 70)

    def export_report(self, output_file: str) -> None:
        """
        导出分析报告

        Args:
            output_file: 输出文件路径
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        report = {
            "generated_at": datetime.now().isoformat(),
            "source_file": str(self.patterns_file),
            "total_patterns": len(self.patterns),
            "statistics": self.statistics,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 分析报告已保存到: {output_path}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="推理模式库分析器")
    parser.add_argument(
        "--patterns-file",
        type=str,
        default="/Users/xujian/Athena工作平台/data/reasoning_patterns/patterns_final.json",
        help="推理模式库文件路径",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="/Users/xujian/Athena工作平台/data/reasoning_patterns/analysis_report.json",
        help="输出报告文件路径",
    )

    args = parser.parse_args()

    # 创建分析器
    analyzer = PatternLibraryAnalyzer(args.patterns_file)

    # 加载模式库
    if not analyzer.load_patterns():
        sys.exit(1)

    # 执行分析
    analyzer.analyze()

    # 打印报告
    analyzer.print_report()

    # 导出报告
    analyzer.export_report(args.output)

    logger.info("✅ 分析完成")


if __name__ == "__main__":
    main()
