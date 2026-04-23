"""
新颖性分析代理（NoveltyAnalyzerProxy）单元测试

测试内容：
1. 初始化测试
2. 能力注册测试
3. 系统提示词测试
4. 基本功能测试（使用mock）
"""

import pytest
from typing import Dict, List, Optional, Any

from unittest.mock import patch

from core.framework.agents.xiaona.novelty_analyzer_proxy import NoveltyAnalyzerProxy
from core.framework.agents.xiaona.base_component import AgentExecutionContext


class TestNoveltyAnalyzerInitialization:
    """新颖性分析代理初始化测试"""

    def test_novelty_analyzer_initialization(self):
        """测试新颖性分析代理初始化"""
        analyzer = NoveltyAnalyzerProxy()
        assert analyzer.agent_id == "novelty_analyzer"
        assert analyzer.status.value == "idle"


class TestNoveltyAnalyzerCapabilities:
    """新颖性分析代理能力注册测试"""

    def test_novelty_analyzer_capabilities(self):
        """测试能力注册"""
        analyzer = NoveltyAnalyzerProxy()
        capabilities = analyzer.get_capabilities()
        capability_names = [c.name for c in capabilities]

        assert "individual_comparison" in capability_names
        assert "difference_identification" in capability_names
        assert "novelty_determination" in capability_names
        assert "prior_art_search" in capability_names

    def test_novelty_analyzer_capability_details(self):
        """测试能力详情"""
        analyzer = NoveltyAnalyzerProxy()
        capabilities = analyzer.get_capabilities()

        # 检查individual_comparison能力
        individual = next((c for c in capabilities if c.name == "individual_comparison"), None)
        assert individual is not None
        assert individual.description == "单独对比"
        assert "目标专利" in individual.input_types

    def test_novelty_analyzer_has_capability(self):
        """测试能力检查方法"""
        analyzer = NoveltyAnalyzerProxy()
        assert analyzer.has_capability("individual_comparison")
        assert not analyzer.has_capability("nonexistent_capability")


class TestNoveltyAnalyzerSystemPrompt:
    """新颖性分析代理系统提示词测试"""

    def test_get_system_prompt(self):
        """测试获取系统提示词"""
        analyzer = NoveltyAnalyzerProxy()
        prompt = analyzer.get_system_prompt()

        assert "专利新颖性分析专家" in prompt
        assert "对比文件技术特征分析" in prompt
        assert "区别技术特征识别" in prompt
        assert "新颖性判断" in prompt

    def test_default_system_prompt(self):
        """测试默认系统提示词"""
        analyzer = NoveltyAnalyzerProxy()
        prompt = analyzer._get_default_system_prompt()

        assert "专利新颖性分析专家" in prompt


class TestNoveltyAnalyzerExecute:
    """新颖性分析代理基本功能测试"""

    @pytest.mark.asyncio
    async def test_execute_default_task(self):
        """测试默认任务执行"""
        analyzer = NoveltyAnalyzerProxy()

        context = AgentExecutionContext(
            session_id="test_session",
            task_id="test_task",
            input_data={
                "patent_id": "CN123456",
                "claims": "1. 一种测试装置...",
                "prior_art_references": []
            },
            config={},
            metadata={}
        )

        # Mock LLM调用，使用规则降级
        with patch.object(analyzer, '_call_llm_with_fallback', side_effect=Exception("LLM失败")):
            result = await analyzer.execute(context)

        assert result["patent_id"] == "CN123456"
        assert "analysis_method" in result

    @pytest.mark.asyncio
    async def test_analyze_novelty_with_rules(self):
        """测试基于规则的新颖性分析"""
        analyzer = NoveltyAnalyzerProxy()

        patent_data = {
            "patent_id": "CN123456",
            "claims": "1. 一种测试装置，包括特征A、特征B和特征C。",
            "prior_art_references": [
                {"doc_id": "D1", "content": "包括特征A和特征B的装置"},
                {"doc_id": "D2", "content": "包括特征A的装置"}
            ]
        }

        result = await analyzer.analyze_novelty(patent_data)

        assert result["patent_id"] == "CN123456"
        assert "individual_comparisons" in result
        assert "novelty_conclusion" in result

    @pytest.mark.asyncio
    async def test_compare_with_reference(self):
        """测试与对比文件比对"""
        analyzer = NoveltyAnalyzerProxy()

        target_features = {
            "essential": ["特征A", "特征B", "特征C"],
            "additional": ["特征D"]
        }

        reference_doc = {
            "doc_id": "D1",
            "features": {
                "essential": ["特征A", "特征B"],
                "additional": []
            }
        }

        result = await analyzer._compare_with_reference(target_features, reference_doc, "individual")

        assert result["reference_id"] == "D1"
        assert "disclosed_count" in result
        assert "undisclosed_count" in result

    @pytest.mark.asyncio
    async def test_judge_novelty(self):
        """测试新颖性判断"""
        analyzer = NoveltyAnalyzerProxy()

        novel_features = [
            {"feature": "特征C", "category": "essential", "novel": True}
        ]

        target_features = {
            "essential": ["特征A", "特征B", "特征C"],
            "additional": ["特征D"]
        }

        result = await analyzer._judge_novelty(novel_features, target_features)

        assert "has_novelty" in result
        assert "novelty_ratio" in result
        assert "conclusion" in result


class TestNoveltyAnalyzerHelperMethods:
    """新颖性分析代理辅助方法测试"""

    def test_extract_all_features(self):
        """测试提取所有技术特征"""
        analyzer = NoveltyAnalyzerProxy()

        patent = {
            "claims": "1. 一种测试装置，其特征在于包括：特征A、特征B和特征C。"
        }

        # 使用同步方法调用
        features = analyzer._extract_all_features(patent)

        assert "essential" in features
        assert "additional" in features

    def test_extract_features_by_type(self):
        """测试按类型提取特征"""
        analyzer = NoveltyAnalyzerProxy()

        claims_text = "包括特征A、特征B和特征C"

        features = analyzer._extract_features_by_type(claims_text, ["包括"])

        assert isinstance(features, list)

    def test_identify_novel_features(self):
        """测试识别新颖特征"""
        analyzer = NoveltyAnalyzerProxy()

        target_features = {
            "essential": ["特征A", "特征B", "特征C"],
            "additional": ["特征D"]
        }

        comparison_results = [
            {
                "feature_comparison": [
                    {"feature": "特征A", "disclosed": True},
                    {"feature": "特征B", "disclosed": True},
                    {"feature": "特征C", "disclosed": False}
                ]
            }
        ]

        # 使用同步方法调用
        novel_features = analyzer._identify_novel_features(target_features, comparison_results)

        assert len(novel_features) > 0
        assert novel_features[0]["novel"] is True

    def test_calculate_novelty_confidence(self):
        """测试计算新颖性置信度"""
        analyzer = NoveltyAnalyzerProxy()

        novel_features = [
            {"feature": "特征C", "category": "essential"}
        ]

        target_features = {
            "essential": ["特征A", "特征B", "特征C"],
            "additional": ["特征D"]
        }

        confidence = analyzer._calculate_novelty_confidence(novel_features, target_features)

        assert 0 <= confidence <= 1

    def test_get_timestamp(self):
        """测试获取时间戳"""
        analyzer = NoveltyAnalyzerProxy()
        timestamp = analyzer._get_timestamp()

        assert isinstance(timestamp, str)
        assert len(timestamp) > 0


class TestNoveltyAnalyzerInfo:
    """新颖性分析代理信息测试"""

    def test_get_info(self):
        """测试获取代理信息"""
        analyzer = NoveltyAnalyzerProxy()
        info = analyzer.get_info()

        assert info["agent_id"] == "novelty_analyzer"
        assert info["agent_type"] == "NoveltyAnalyzerProxy"
        assert "capabilities" in info

    def test_repr(self):
        """测试代理字符串表示"""
        analyzer = NoveltyAnalyzerProxy()
        repr_str = repr(analyzer)

        assert "NoveltyAnalyzerProxy" in repr_str
