#!/usr/bin/env python3
"""
技术演化路径分析器
Technology Evolution Path Analyzer

追踪和分析专利技术特征的演化路径

功能:
- 时间序列分析: 追踪技术特征随时间的变化
- 技术谱系构建: 识别技术继承和演化关系
- 演化趋势预测: 预测未来技术发展方向
- 关键转折点识别: 识别技术突破点

作者: 小诺·双鱼公主
创建时间: 2026-01-26
版本: v0.1.0 "演化分析"
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

logger = setup_logging()


@dataclass
class EvolutionNode:
    """演化节点"""
    patent_id: str
    patent_number: str
    patent_title: str
    application_date: str
    technical_features: list[str]
    importance_score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "patent_id": self.patent_id,
            "patent_number": self.patent_number,
            "patent_title": self.patent_title,
            "application_date": self.application_date,
            "technical_features": self.technical_features,
            "importance_score": self.importance_score,
        }


@dataclass
class EvolutionPath:
    """演化路径"""
    path_id: str
    start_node: str  # 起始专利ID
    end_node: str  # 终点专利ID
    evolution_chain: list[str]  # 演化链条（专利ID列表）
    evolution_type: str  # "incremental", "breakthrough", "divergent"
    innovation_level: str  # "low", "medium", "high"
    time_span: float  # 时间跨度（年）
    key_features: list[str]  # 关键演化特征

    # 统计指标
    total_patents: int = 0
    avg_citation_count: float = 0.0
    breakthrough_score: float = 0.0


@dataclass
class EvolutionAnalysisResult:
    """演化分析结果"""
    patent_id: str
    evolution_paths: list[EvolutionPath] = field(default_factory=list)

    # 统计信息
    total_paths: int = 0
    avg_path_length: float = 0.0
    most_evolved_features: list[str] = field(default_factory=list)

    # 趋势预测
    future_trends: list[str] = field(default_factory=list)
    key_turning_points: list[dict[str, Any]] = field(default_factory=list)


class TechnologyEvolutionAnalyzer:
    """
    技术演化路径分析器

    特性:
    1. 基于引用关系构建演化图
    2. 识别技术演化路径类型
    3. 分析技术演化趋势
    4. 预测未来技术方向
    """

    def __init__(self):
        """初始化分析器"""
        self.name = "技术演化路径分析器"
        self.version = "v0.1.0"

        logger.info(f"🔬 {self.name} ({self.version}) 初始化完成")

    def analyze_evolution(
        self,
        target_patent: EvolutionNode,
        patent_family: list[EvolutionNode],
        citation_network: dict[str, list[str]] | None = None,
    ) -> EvolutionAnalysisResult:
        """
        分析技术演化路径

        Args:
            target_patent: 目标专利
            patent_family: 专利族/相关专利列表
            citation_network: 引用网络 {patent_id: [cited_patent_ids]}

        Returns:
            演化分析结果
        """
        logger.info(f"🔬 开始演化分析: {target_patent.patent_number}")

        result = EvolutionAnalysisResult(patent_id=target_patent.patent_id)

        # 1. 构建时间序列
        time_ordered = sorted(
            patent_family + [target_patent],
            key=lambda x: x.application_date or "9999-12-31",
        )

        # 2. 识别演化路径
        evolution_paths = self._identify_evolution_paths(
            target_patent, time_ordered, citation_network
        )
        result.evolution_paths = evolution_paths
        result.total_paths = len(evolution_paths)

        # 3. 分析演化统计
        result.total_paths = len(evolution_paths)
        if evolution_paths:
            result.avg_path_length = sum(
                len(path.evolution_chain) for path in evolution_paths
            ) / len(evolution_paths)

        # 4. 识别关键演化特征
        result.most_evolved_features = self._identify_evolved_features(
            evolution_paths, time_ordered
        )

        # 5. 预测未来趋势
        result.future_trends = self._predict_future_trends(
            evolution_paths, time_ordered
        )

        # 6. 识别关键转折点
        result.key_turning_points = self._identify_turning_points(
            evolution_paths, time_ordered
        )

        logger.info(f"✅ 演化分析完成: {result.total_paths}条路径")

        return result

    def _identify_evolution_paths(
        self,
        target_patent: EvolutionNode,
        time_ordered: list[EvolutionNode],
        citation_network: dict[str, list[str]],
    ) -> list[EvolutionPath]:
        """识别演化路径"""
        paths = []

        if citation_network is None:
            # 基于时间序列推断路径
            path = EvolutionPath(
                path_id=f"path_{len(time_ordered)}",
                start_node=time_ordered[0].patent_id,
                end_node=target_patent.patent_id,
                evolution_chain=[p.patent_id for p in time_ordered],
                evolution_type="incremental",
                innovation_level="medium",
                time_span=self._calculate_time_span(time_ordered),
                key_features=self._extract_common_features(time_ordered),
                total_patents=len(time_ordered),
            )
            paths.append(path)
        else:
            # 基于引用网络构建路径
            # TODO: 实现基于引用网络的路径搜索
            pass

        return paths

    def _identify_evolved_features(
        self, paths: list[EvolutionPath], patents: list[EvolutionNode]
    ) -> list[str]:
        """识别演化特征"""
        feature_evolution = {}

        for patent in patents:
            for feature in patent.technical_features:
                if feature not in feature_evolution:
                    feature_evolution[feature] = []
                feature_evolution[feature].append(
                    (patent.application_date, patent.importance_score)
                )

        # 找出演化最多的特征
        evolved_features = sorted(
            feature_evolution.items(),
            key=lambda x: len(x[1]),
            reverse=True,
        )[:5]

        return [f[0] for f in evolved_features]

    def _predict_future_trends(
        self, paths: list[EvolutionPath], patents: list[EvolutionNode]
    ) -> list[str]:
        """预测未来趋势"""
        trends = []

        # 分析特征出现频率
        feature_counts = {}
        for patent in patents:
            for feature in patent.technical_features:
                feature_counts[feature] = feature_counts.get(feature, 0) + 1

        # 识别高频特征
        high_freq_features = sorted(
            feature_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]

        for feature, count in high_freq_features:
            if count >= len(patents) * 0.5:  # 出现在50%以上的专利中
                trends.append(f"'{feature}' 可能成为未来技术发展方向")

        return trends

    def _identify_turning_points(
        self, paths: list[EvolutionPath], patents: list[EvolutionNode]
    ) -> list[dict[str, Any]]:
        """识别关键转折点"""
        turning_points = []

        # 分析重要性分数突变
        for i in range(1, len(patents)):
            prev_score = patents[i - 1].importance_score
            curr_score = patents[i].importance_score
            score_change = abs(curr_score - prev_score)

            if score_change > 0.3:  # 显著变化
                turning_points.append(
                    {
                        "patent_id": patents[i].patent_id,
                        "patent_number": patents[i].patent_number,
                        "application_date": patents[i].application_date,
                        "importance_change": score_change,
                        "type": "breakthrough" if curr_score > prev_score else "decline",
                        "new_features": patents[i].technical_features[:3],
                    }
                )

        return turning_points

    def _calculate_time_span(
        self, patents: list[EvolutionNode]
    ) -> float:
        """计算时间跨度"""
        if len(patents) < 2:
            return 0.0

        try:
            start = datetime.strptime(patents[0].application_date[:10], "%Y-%m-%d")
            end = datetime.strptime(patents[-1].application_date[:10], "%Y-%m-%d")
            return (end - start).days / 365.25
        except Exception:
            return 0.0

    def _extract_common_features(
        self, patents: list[EvolutionNode]
    ) -> list[str]:
        """提取共同特征"""
        if not patents:
            return []

        # 找出所有专利都有的特征
        common_features = set(patents[0].technical_features)
        for patent in patents[1:]:
            common_features &= set(patent.technical_features)

        return list(common_features)

    def visualize_evolution_path(
        self,
        evolution_path: EvolutionPath,
        output_path: str,
    ):
        """
        可视化演化路径

        Args:
            evolution_path: 演化路径
            output_path: 输出文件路径
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')

            # 创建图形
            fig, ax = plt.subplots(figsize=(16, 8))

            # 绘制时间线
            positions = list(range(len(evolution_path.evolution_chain)))
            ax.scatter(positions, [1] * len(positions), s=200, alpha=0.6)

            # 添加标签
            for i, node_id in enumerate(evolution_path.evolution_chain):
                ax.annotate(
                    f"专利{i+1}",
                    (i, 1),
                    xytext=(0, 10),
                    textcoords="offset points",
                    ha="center",
                )

            ax.set_title(
                f"技术演化路径: {evolution_path.evolution_type}\n"
                f"时间跨度: {evolution_path.time_span:.1f}年 | "
                f"创新水平: {evolution_path.innovation_level}"
            )

            ax.set_xlabel("演化步骤")
            ax.set_yticks([])
            ax.set_ylim([0, 2])

            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches="tight")
            plt.close(fig)

            logger.info(f"✅ 演化路径可视化已保存: {output_path}")

        except Exception as e:
            logger.warning(f"⚠️ 演化路径可视化失败: {e}")

    def to_markdown(
        self, result: EvolutionAnalysisResult
    ) -> str:
        """生成Markdown格式的演化分析报告"""
        md = []

        md.append("# 🔬 技术演化路径分析报告\n")
        md.append("---\n")

        # 演化路径
        md.append("## 📈 演化路径\n")
        for i, path in enumerate(result.evolution_paths, 1):
            md.append(f"### 路径 {i}: {path.evolution_type}\n")
            md.append(f"- **路径ID**: {path.path_id}\n")
            md.append(f"- **演化类型**: {path.evolution_type}\n")
            md.append(f"- **创新水平**: {path.innovation_level}\n")
            md.append(f"- **时间跨度**: {path.time_span:.1f}年\n")
            md.append(f"- **专利数量**: {path.total_patents}\n")
            md.append(f"- **关键特征**: {', '.join(path.key_features)}\n")
            md.append("")

        # 关键转折点
        if result.key_turning_points:
            md.append("## 🔄 关键转折点\n")
            for point in result.key_turning_points:
                md.append(f"### {point['patent_number']}\n")
                md.append(f"- **时间**: {point['application_date']}\n")
                md.append(f"- **类型**: {point['type']}\n")
                md.append(f"- **变化幅度**: {point['importance_change']:.2f}\n")
                md.append(f"- **新增特征**: {', '.join(point['new_features'])}\n")
                md.append("")

        # 未来趋势
        if result.future_trends:
            md.append("## 🔮 未来趋势预测\n")
            for trend in result.future_trends:
                md.append(f"- {trend}\n")
            md.append("")

        # 统计信息
        md.append("## 📊 统计信息\n")
        md.append(f"- **演化路径数**: {result.total_paths}\n")
        md.append(f"- **平均路径长度**: {result.avg_path_length:.1f}个专利\n")

        if result.most_evolved_features:
            md.append(f"- **高频演化特征**: {', '.join(result.most_evolved_features)}\n")

        return "".join(md)


# 全局单例
_analyzer_instance: TechnologyEvolutionAnalyzer | None = None


def get_evolution_analyzer() -> TechnologyEvolutionAnalyzer:
    """获取分析器单例"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = TechnologyEvolutionAnalyzer()
    return _analyzer_instance


# 测试代码
async def main():
    """测试技术演化路径分析器"""

    print("\n" + "=" * 70)
    print("🔬 技术演化路径分析器测试")
    print("=" * 70 + "\n")

    analyzer = get_evolution_analyzer()

    # 模拟测试数据
    target_patent = EvolutionNode(
        patent_id="patent_5",
        patent_number="CN202310000005.X",
        patent_title="第五代图像识别方法",
        application_date="2023-10-15",
        technical_features=["深度学习", "卷积神经网络", "注意力机制"],
        importance_score=0.9,
    )

    patent_family = [
        EvolutionNode(
            patent_id="patent_1",
            patent_number="CN202310000001.X",
            patent_title="第一代图像识别方法",
            application_date="2020-01-10",
            technical_features=["传统算法", "特征提取"],
            importance_score=0.5,
        ),
        EvolutionNode(
            patent_id="patent_2",
            patent_number="CN202310000002.X",
            patent_title="第二代图像识别方法",
            application_date="2021-03-15",
            technical_features=["传统算法", "机器学习"],
            importance_score=0.6,
        ),
        EvolutionNode(
            patent_id="patent_3",
            patent_number="CN202310000003.X",
            patent_title="第三代图像识别方法",
            application_date="2022-05-20",
            technical_features=["机器学习", "神经网络"],
            importance_score=0.7,
        ),
        EvolutionNode(
            patent_id="patent_4",
            patent_number="CN202310000004.X",
            patent_title="第四代图像识别方法",
            application_date="2023-01-10",
            technical_features=["深度学习", "卷积神经网络"],
            importance_score=0.8,
        ),
    ]

    # 执行分析
    result = analyzer.analyze_evolution(
        target_patent=target_patent,
        patent_family=patent_family,
    )

    # 输出结果
    print(analyzer.to_markdown(result))

    print("\n✅ 测试完成!")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
