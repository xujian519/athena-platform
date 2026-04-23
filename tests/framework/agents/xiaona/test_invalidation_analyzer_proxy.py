"""
无效宣告分析代理（InvalidationAnalyzerProxy）单元测试

测试内容：
1. 初始化测试
2. 能力注册测试
3. 系统提示词测试
4. 基本功能测试（使用mock）
"""

import pytest
from typing import Dict, List, Optional, Any

from unittest.mock import patch

from core.framework.agents.xiaona.invalidation_analyzer_proxy import InvalidationAnalyzerProxy
from core.framework.agents.xiaona.base_component import AgentExecutionContext


class TestInvalidationAnalyzerInitialization:
    """无效宣告分析代理初始化测试"""

    def test_invalidation_analyzer_initialization(self):
        """测试无效宣告分析代理初始化"""
        analyzer = InvalidationAnalyzerProxy()
        assert analyzer.agent_id == "invalidation_analyzer"
        assert analyzer.status.value == "idle"


class TestInvalidationAnalyzerCapabilities:
    """无效宣告分析代理能力注册测试"""

    def test_invalidation_analyzer_capabilities(self):
        """测试能力注册"""
        analyzer = InvalidationAnalyzerProxy()
        capabilities = analyzer.get_capabilities()
        capability_names = [c.name for c in capabilities]

        assert "invalidation_ground_analysis" in capability_names
        assert "evidence_collection_strategy" in capability_names
        assert "success_probability_assessment" in capability_names
        assert "invalidation_petition_support" in capability_names

    def test_invalidation_analyzer_capability_details(self):
        """测试能力详情"""
        analyzer = InvalidationAnalyzerProxy()
        capabilities = analyzer.get_capabilities()

        # 检查invalidation_ground_analysis能力
        grounds = next((c for c in capabilities if c.name == "invalidation_ground_analysis"), None)
        assert grounds is not None
        assert "无效理由分析" in grounds.description

    def test_invalidation_analyzer_has_capability(self):
        """测试能力检查方法"""
        analyzer = InvalidationAnalyzerProxy()
        assert analyzer.has_capability("invalidation_ground_analysis")
        assert analyzer.has_capability("evidence_collection_strategy")
        assert not analyzer.has_capability("nonexistent_capability")


class TestInvalidationAnalyzerSystemPrompt:
    """无效宣告分析代理系统提示词测试"""

    def test_get_system_prompt(self):
        """测试获取系统提示词"""
        analyzer = InvalidationAnalyzerProxy()
        prompt = analyzer.get_system_prompt()

        assert "专利无效宣告分析专家" in prompt
        assert "无效理由" in prompt
        assert "证据搜集" in prompt
        assert "成功概率" in prompt


class TestInvalidationAnalyzerExecute:
    """无效宣告分析代理基本功能测试"""

    @pytest.mark.asyncio
    async def test_execute_default_task(self):
        """测试默认任务执行（完整无效分析）"""
        analyzer = InvalidationAnalyzerProxy()

        context = AgentExecutionContext(
            session_id="test_session",
            task_id="test_task",
            input_data={
                "patent": {
                    "patent_id": "CN123456",
                    "title": "测试专利",
                    "claims": "1. 一种测试装置..."
                },
                "references": [
                    {"doc_id": "D1", "title": "对比文件1"},
                    {"doc_id": "D2", "title": "对比文件2"}
                ]
            },
            config={"analysis_depth": "comprehensive"},
            metadata={}
        )

        # Mock LLM调用，使用规则降级
        with patch.object(analyzer, '_call_llm_with_fallback', side_effect=Exception("LLM失败")):
            result = await analyzer.execute(context)

        assert "target_patent" in result
        assert "invalidation_grounds_analysis" in result

    @pytest.mark.asyncio
    async def test_analyze_invalidation(self):
        """测试完整无效宣告分析"""
        analyzer = InvalidationAnalyzerProxy()

        target_patent = {
            "patent_id": "CN123456",
            "title": "测试专利",
            "claims": "1. 一种测试装置..."
        }

        prior_art_references = [
            {"doc_id": "D1", "content": "对比文件1内容"},
            {"doc_id": "D2", "content": "对比文件2内容"}
        ]

        result = await analyzer.analyze_invalidation(target_patent, prior_art_references)

        assert result["target_patent"]["patent_id"] == "CN123456"
        assert "invalidation_grounds_analysis" in result
        assert "evidence_strategy" in result
        assert "success_probability" in result

    @pytest.mark.asyncio
    async def test_analyze_invalidation_grounds(self):
        """测试无效理由分析"""
        analyzer = InvalidationAnalyzerProxy()

        patent = {
            "patent_id": "CN123456",
            "claims": "1. 一种测试装置，包括特征A、特征B。"
        }

        references = [
            {"doc_id": "D1", "content": "包括特征A的装置"}
        ]

        result = await analyzer.analyze_invalidation_grounds(patent, references)

        assert "valid_grounds" in result
        assert "total_grounds" in result

    @pytest.mark.asyncio
    async def test_develop_evidence_strategy(self):
        """测试证据搜集策略"""
        analyzer = InvalidationAnalyzerProxy()

        valid_grounds = [
            {"ground_type": "lack_of_novelty"}
        ]

        existing_references = []

        result = await analyzer.develop_evidence_strategy(valid_grounds, existing_references)

        assert "evidence_categories" in result
        assert "collection_plan" in result

    @pytest.mark.asyncio
    async def test_assess_success_probability(self):
        """测试成功概率评估"""
        analyzer = InvalidationAnalyzerProxy()

        grounds_analysis = {
            "ground_strengths": [
                {"strength": "strong", "confidence": 0.8},
                {"strength": "moderate", "confidence": 0.6}
            ]
        }

        evidence_strategy = {
            "collection_plan": [
                {"actions": [{}, {}, {}]}  # 3个行动
            ]
        }

        result = await analyzer.assess_success_probability(grounds_analysis, evidence_strategy)

        assert "overall_probability" in result
        assert "confidence" in result

    @pytest.mark.asyncio
    async def test_generate_invalidation_petition(self):
        """测试生成无效请求书"""
        analyzer = InvalidationAnalyzerProxy()

        patent = {"patent_id": "CN123456", "title": "测试专利"}

        grounds_analysis = {
            "recommended_grounds": [
                {"ground_type": "lack_of_novelty", "description": "不具备新颖性", "analysis": {}}
            ]
        }

        evidence_strategy = {"collection_plan": []}
        probability_assessment = {"overall_probability": 0.75}

        result = await analyzer.generate_invalidation_petition(
            patent, grounds_analysis, evidence_strategy, probability_assessment
        )

        assert "petition_structure" in result
        assert "word_count" in result


class TestInvalidationAnalyzerHelperMethods:
    """无效宣告分析代理辅助方法测试"""

    def test_assess_ground_strength(self):
        """测试评估理由强度"""
        analyzer = InvalidationAnalyzerProxy()

        strong_ground = {
            "analysis": {"confidence": 0.85}
        }

        weak_ground = {
            "analysis": {"confidence": 0.5}
        }

        strong_strength = analyzer._assess_ground_strength(strong_ground)
        weak_strength = analyzer._assess_ground_strength(weak_ground)

        assert strong_strength == "strong"
        assert weak_strength == "weak"

    def test_select_best_grounds(self):
        """测试选择最佳无效理由"""
        analyzer = InvalidationAnalyzerProxy()

        valid_grounds = [
            {"ground_type": "A", "analysis": {"confidence": 0.7}},
            {"ground_type": "B", "analysis": {"confidence": 0.9}},
            {"ground_type": "C", "analysis": {"confidence": 0.5}}
        ]

        best = analyzer._select_best_grounds(valid_grounds)

        assert len(best) <= 3
        assert best[0]["ground_type"] == "B"  # 最高置信度

    def test_generate_search_keywords(self):
        """测试生成检索关键词"""
        analyzer = InvalidationAnalyzerProxy()

        keywords1 = analyzer._generate_search_keywords("lack_of_novelty")
        keywords2 = analyzer._generate_search_keywords("lack_of_creativity")

        assert isinstance(keywords1, list)
        assert isinstance(keywords2, list)

    def test_calculate_ground_strength_score(self):
        """测试计算理由强度得分"""
        analyzer = InvalidationAnalyzerProxy()

        ground_strengths = [
            {"strength": "strong", "confidence": 0.8},
            {"strength": "moderate", "confidence": 0.6}
        ]

        score = analyzer._calculate_ground_strength_score(ground_strengths)

        assert 0 <= score <= 1

    def test_assess_evidence_quality(self):
        """测试评估证据质量"""
        analyzer = InvalidationAnalyzerProxy()

        strategy = {
            "collection_plan": [
                {"actions": [{}, {}, {}]},  # 3个来源
                {"actions": [{}, {}]}     # 2个来源
            ]
        }

        quality = analyzer._assess_evidence_quality(strategy)

        assert 0 <= quality <= 1

    def test_generate_outcome_prediction(self):
        """测试生成结果预测"""
        analyzer = InvalidationAnalyzerProxy()

        # 高概率
        prediction_high = analyzer._generate_outcome_prediction(0.85, [])
        assert prediction_high["predicted_outcome"] in ["全部无效", "部分无效"]

        # 低概率
        prediction_low = analyzer._generate_outcome_prediction(0.3, [])
        assert prediction_low["predicted_outcome"] in ["可能维持", "维持有效"]

    def test_identify_risk_factors(self):
        """测试识别风险因素"""
        analyzer = InvalidationAnalyzerProxy()

        ground_strengths = [
            {"strength": "weak", "type": "type1"},
            {"strength": "weak", "type": "type2"}
        ]

        risks = analyzer._identify_risk_factors(ground_strengths)

        assert len(risks) > 0

    def test_extract_features(self):
        """测试提取技术特征"""
        analyzer = InvalidationAnalyzerProxy()

        text = "该装置包括特征A、特征B和特征C，用于实现功能X。"

        features = analyzer._extract_features(text)

        assert isinstance(features, list)

    def test_identify_missing_disclosure_aspects(self):
        """测试识别缺失披露内容"""
        analyzer = InvalidationAnalyzerProxy()

        patent = {
            "embodiments": [],
            "best_mode": None,
            "drawings": []
        }

        missing = analyzer._identify_missing_disclosure_aspects(patent)

        assert len(missing) > 0
        assert any("实施方式" in m for m in missing)

    def test_get_timestamp(self):
        """测试获取时间戳"""
        analyzer = InvalidationAnalyzerProxy()
        timestamp = analyzer._get_timestamp()

        assert isinstance(timestamp, str)
        assert len(timestamp) > 0


class TestInvalidationAnalyzerInfo:
    """无效宣告分析代理信息测试"""

    def test_get_info(self):
        """测试获取代理信息"""
        analyzer = InvalidationAnalyzerProxy()
        info = analyzer.get_info()

        assert info["agent_id"] == "invalidation_analyzer"
        assert info["agent_type"] == "InvalidationAnalyzerProxy"
        assert "capabilities" in info

    def test_repr(self):
        """测试代理字符串表示"""
        analyzer = InvalidationAnalyzerProxy()
        repr_str = repr(analyzer)

        assert "InvalidationAnalyzerProxy" in repr_str
