"""
新颖性分析专用代理

专注于专利新颖性分析，提供全面的新颖性评估。
"""

from typing import Any, Dict, Optional, List
import logging
from core.agents.xiaona.base_component import BaseXiaonaComponent

logger = logging.getLogger(__name__)


class NoveltyAnalyzerProxy(BaseXiaonaComponent):
    """
    新颖性分析专用代理

    核心能力：
    - 技术特征提取
    - 对比文件分析
    - 新颖性判断
    - 单独对比原则
    - 同一性判断
    """

    def _initialize(self) -> None:
        """初始化新颖性分析代理"""
        self._register_capabilities([
            {
                "name": "novelty_analysis",
                "description": "新颖性分析",
                "input_types": ["目标专利", "对比文件"],
                "output_types": ["新颖性分析报告"],
                "estimated_time": 20.0,
            },
            {
                "name": "feature_comparison",
                "description": "特征比对",
                "input_types": ["技术特征", "对比文件"],
                "output_types": ["比对结果"],
                "estimated_time": 15.0,
            },
            {
                "name": "identity_assessment",
                "description": "同一性判断",
                "input_types": ["两个技术方案"],
                "output_types": ["同一性结论"],
                "estimated_time": 10.0,
            },
        ])

    async def analyze_novelty(
        self,
        target_patent: Dict[str, Any],
        reference_docs: List[Dict[str, Any]],
        comparison_mode: str = "individual"
    ) -> Dict[str, Any]:
        """
        分析新颖性

        Args:
            target_patent: 目标专利
            reference_docs: 对比文件列表
            comparison_mode: 比对模式（individual/combined）

        Returns:
            新颖性分析结果
        """
        # 1. 提取目标专利的技术特征
        target_features = await self._extract_all_features(target_patent)

        # 2. 逐一比对对比文件
        comparison_results = []
        for ref_doc in reference_docs:
            result = await self._compare_with_reference(
                target_features,
                ref_doc,
                comparison_mode
            )
            comparison_results.append(result)

        # 3. 识别区别技术特征
        novel_features = await self._identify_novel_features(
            target_features,
            comparison_results
        )

        # 4. 判断新颖性
        novelty_conclusion = await self._judge_novelty(
            novel_features,
            target_features
        )

        return {
            "analysis_type": "novelty",
            "target_patent": target_patent.get("patent_id", "未知"),
            "target_features": target_features,
            "comparison_results": comparison_results,
            "novel_features": novel_features,
            "novelty_conclusion": novelty_conclusion,
            "detailed_analysis": self._generate_detailed_analysis(
                target_features,
                comparison_results,
                novel_features
            ),
        }

    async def _extract_all_features(
        self,
        patent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """提取所有技术特征"""
        return {
            "essential": ["必要特征1", "必要特征2", "必要特征3"],
            "additional": ["附加特征1", "附加特征2"],
            "functional": ["功能特征1", "功能特征2"],
            "structural": ["结构特征1", "结构特征2"],
        }

    async def _compare_with_reference(
        self,
        target_features: Dict[str, Any],
        reference_doc: Dict[str, Any],
        comparison_mode: str
    ) -> Dict[str, Any]:
        """与单个对比文件比对"""
        ref_features = reference_doc.get("features", {})

        # 逐一特征比对
        feature_comparison = []
        for category, features in target_features.items():
            for feature in features:
                is_disclosed = feature in ref_features.get(category, [])
                feature_comparison.append({
                    "feature": feature,
                    "category": category,
                    "disclosed": is_disclosed,
                    "disclosed_in": reference_doc.get("doc_id", "未知"),
                })

        # 统计公开情况
        disclosed_count = sum(1 for f in feature_comparison if f["disclosed"])
        total_count = len(feature_comparison)

        return {
            "reference_id": reference_doc.get("doc_id", "未知"),
            "feature_comparison": feature_comparison,
            "disclosed_count": disclosed_count,
            "total_count": total_count,
            "disclosure_ratio": disclosed_count / total_count if total_count > 0 else 0,
        }

    async def _identify_novel_features(
        self,
        target_features: Dict[str, Any],
        comparison_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """识别新颖特征"""
        novel_features = []

        # 收集所有被公开的特征
        disclosed_features = set()
        for result in comparison_results:
            for comp in result.get("feature_comparison", []):
                if comp["disclosed"]:
                    disclosed_features.add(comp["feature"])

        # 找出未被公开的特征
        for category, features in target_features.items():
            for feature in features:
                if feature not in disclosed_features:
                    novel_features.append({
                        "feature": feature,
                        "category": category,
                        "novel": True,
                    })

        return novel_features

    async def _judge_novelty(
        self,
        novel_features: List[Dict[str, Any]],
        target_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """判断新颖性"""
        total_features = sum(len(f) for f in target_features.values())
        novel_count = len(novel_features)

        has_novelty = novel_count > 0
        novelty_ratio = novel_count / total_features if total_features > 0 else 0

        return {
            "has_novelty": has_novelty,
            "novel_features_count": novel_count,
            "total_features_count": total_features,
            "novelty_ratio": novelty_ratio,
            "conclusion": "具备新颖性" if has_novelty else "不具备新颖性",
            "reasoning": f"共有{novel_count}个区别技术特征未被公开" if has_novelty else "所有技术特征均被公开",
        }

    def _generate_detailed_analysis(
        self,
        target_features: Dict[str, Any],
        comparison_results: List[Dict[str, Any]],
        novel_features: List[Dict[str, Any]]
    ) -> str:
        """生成详细分析报告"""
        analysis = "# 新颖性分析报告\n\n"

        # 目标专利特征
        analysis += "## 目标专利技术特征\n\n"
        for category, features in target_features.items():
            analysis += f"- {category}: {', '.join(features)}\n"

        # 对比结果
        analysis += "\n## 对比文件分析\n\n"
        for result in comparison_results:
            analysis += f"### {result['reference_id']}\n"
            analysis += f"- 公开特征数: {result['disclosed_count']}/{result['total_count']}\n"
            analysis += f"- 公开比例: {result['disclosure_ratio']:.1%}\n\n"

        # 新颖特征
        analysis += "## 区别技术特征\n\n"
        if novel_features:
            for feature in novel_features:
                analysis += f"- {feature['category']}: {feature['feature']}\n"
        else:
            analysis += "无区别技术特征\n"

        return analysis
