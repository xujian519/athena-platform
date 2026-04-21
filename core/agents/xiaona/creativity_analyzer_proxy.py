"""
创造性分析专用代理

专注于专利创造性分析，提供深入的创造性评估。
"""

from typing import Any, Dict, Optional
import logging
from core.agents.xiaona.base_component import BaseXiaonaComponent

logger = logging.getLogger(__name__)


class CreativityAnalyzerProxy(BaseXiaonaComponent):
    """
    创造性分析专用代理

    核心能力：
    - 技术特征分析
    - 现有技术评估
    - 区别特征识别
    - 显著进步判断
    - 预料不到效果评估
    """

    def _initialize(self) -> None:
        """初始化创造性分析代理"""
        self._register_capabilities([
            {
                "name": "creativity_analysis",
                "description": "创造性分析",
                "input_types": ["目标专利", "对比文件"],
                "output_types": ["创造性分析报告"],
                "estimated_time": 25.0,
            },
            {
                "name": "obviousness_assessment",
                "description": "显而易见性评估",
                "input_types": ["技术方案", "现有技术"],
                "output_types": ["显而易见性结论"],
                "estimated_time": 15.0,
            },
            {
                "name": "technical_progress_evaluation",
                "description": "技术进步评估",
                "input_types": ["发明", "技术领域"],
                "output_types": ["进步性分析"],
                "estimated_time": 20.0,
            },
        ])

    async def analyze_creativity(
        self,
        target_patent: Dict[str, Any],
        reference_docs: list[Dict[str, Any]],
        analysis_depth: str = "standard"
    ) -> Dict[str, Any]:
        """
        分析创造性

        Args:
            target_patent: 目标专利
            reference_docs: 对比文件列表
            analysis_depth: 分析深度（standard/deep）

        Returns:
            创造性分析结果
        """
        # 1. 提取技术特征
        features = await self._extract_technical_features(target_patent)

        # 2. 分析现有技术
        prior_art = await self._analyze_prior_art(reference_docs)

        # 3. 识别区别特征
        differences = await self._identify_differences(features, prior_art)

        # 4. 评估显而易见性
        obviousness = await self._assess_obviousness(differences, prior_art)

        # 5. 判断显著进步
        significant_progress = await self._evaluate_progress(differences)

        # 6. 评估预料不到的效果
        unexpected_effects = await self._assess_unexpected_effects(differences)

        return {
            "analysis_type": "creativity",
            "target_patent": target_patent.get("patent_id", "未知"),
            "technical_features": features,
            "differences": differences,
            "obviousness": obviousness,
            "significant_progress": significant_progress,
            "unexpected_effects": unexpected_effects,
            "conclusion": self._generate_creativity_conclusion(
                obviousness,
                significant_progress,
                unexpected_effects
            ),
        }

    async def _extract_technical_features(
        self,
        patent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """提取技术特征"""
        return {
            "essential_features": ["特征1", "特征2", "特征3"],
            "additional_features": ["特征4", "特征5"],
            "technical_field": patent.get("field", "未知领域"),
        }

    async def _analyze_prior_art(
        self,
        reference_docs: list[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析现有技术"""
        return {
            "closest_prior_art": reference_docs[0] if reference_docs else None,
            "disclosed_features": ["特征1", "特征2"],
            "technical_teachings": ["教导1", "教导2"],
        }

    async def _identify_differences(
        self,
        features: Dict[str, Any],
        prior_art: Dict[str, Any]
    ) -> list[Dict[str, Any]]:
        """识别区别特征"""
        return [
            {
                "feature": "特征3",
                "difference": "与现有技术的区别",
                "novel": True,
            }
        ]

    async def _assess_obviousness(
        self,
        differences: list[Dict[str, Any]],
        prior_art: Dict[str, Any]
    ) -> Dict[str, Any]:
        """评估显而易见性"""
        return {
            "is_obvious": False,
            "reasoning": "区别特征非显而易见",
            "evidence": ["证据1", "证据2"],
        }

    async def _evaluate_progress(
        self,
        differences: list[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """评估显著进步"""
        return {
            "has_significant_progress": True,
            "progress_type": "性能提升",
            "benefits": ["有益效果1", "有益效果2"],
        }

    async def _assess_unexpected_effects(
        self,
        differences: list[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """评估预料不到的效果"""
        return {
            "has_unexpected_effects": True,
            "effects": ["预料不到的效果1", "预料不到的效果2"],
        }

    def _generate_creativity_conclusion(
        self,
        obviousness: Dict[str, Any],
        progress: Dict[str, Any],
        effects: Dict[str, Any]
    ) -> str:
        """生成创造性结论"""
        if (not obviousness.get("is_obvious") and
            progress.get("has_significant_progress")):
            return "具备创造性"
        else:
            return "不具备创造性"
