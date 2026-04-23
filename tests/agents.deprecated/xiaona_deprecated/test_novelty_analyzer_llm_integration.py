"""
NoveltyAnalyzerProxy LLM集成测试

测试新颖性分析智能体的LLM增强功能。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.framework.agents.xiaona.novelty_analyzer_proxy import NoveltyAnalyzerProxy


class TestNoveltyAnalyzerLLMIntegration:
    """NoveltyAnalyzerProxy LLM集成测试套件"""

    @pytest.fixture
    def analyzer(self):
        """创建NoveltyAnalyzerProxy实例"""
        analyzer = NoveltyAnalyzerProxy(agent_id="test_novelty_analyzer")
        analyzer.logger = MagicMock()
        return analyzer

    @pytest.fixture
    def sample_patent_data(self):
        """示例专利数据"""
        return {
            "patent_id": "CN123456789A",
            "claims": "1. 一种智能控制系统，包括处理器、传感器和执行器，其特征在于：所述处理器采用深度学习算法进行决策。\n2. 根据权利要求1所述的系统，其特征在于：所述传感器为多模态传感器。",
            "prior_art_references": [
                {
                    "doc_id": "D1",
                    "title": "传统控制系统",
                    "abstract": "一种基于规则的传统控制系统",
                    "features": {
                        "essential": ["处理器", "传感器"],
                        "additional": ["执行器"],
                    }
                },
                {
                    "doc_id": "D2",
                    "title": "智能控制方法",
                    "abstract": "使用机器学习的控制方法",
                    "features": {
                        "functional": ["机器学习算法"],
                    }
                }
            ]
        }

    @pytest.fixture
    def sample_target_features(self):
        """示例目标特征"""
        return {
            "essential": ["处理器", "传感器", "执行器"],
            "additional": ["深度学习算法"],
            "functional": ["智能决策"],
            "structural": ["模块化设计"],
        }

    @pytest.mark.asyncio
    async def test_analyze_novelty_with_llm_success(self, analyzer, sample_patent_data):
        """测试LLM新颖性分析成功场景"""
        # Mock LLM响应
        mock_response = '''```json
{
    "target_patent": "CN123456789A",
    "total_features_count": 6,
    "individual_comparisons": [
        {
            "reference_id": "D1",
            "disclosed_features": ["处理器", "传感器"],
            "undisclosed_features": ["深度学习算法"],
            "disclosure_ratio": 0.5
        }
    ],
    "distinguishing_features": [
        {
            "feature": "深度学习算法",
            "category": "additional",
            "importance": "high"
        }
    ],
    "novelty_conclusion": {
        "has_novelty": true,
        "conclusion": "具备新颖性",
        "strength": "strong"
    },
    "confidence_assessment": {
        "confidence_score": 0.85,
        "confidence_level": "high"
    }
}
```'''

        with patch.object(analyzer, '_call_llm_with_fallback', new=AsyncMock(return_value=mock_response)):
            result = await analyzer.analyze_novelty(sample_patent_data)

            # 验证结果
            assert result["patent_id"] == "CN123456789A"
            assert result["analysis_method"] == "llm"
            # novelty_conclusion是一个字典
            assert result["novelty_conclusion"]["conclusion"] == "具备新颖性"
            assert result["confidence_assessment"]["confidence_level"] == "high"

    @pytest.mark.asyncio
    async def test_analyze_novelty_llm_fallback_to_rules(self, analyzer, sample_patent_data):
        """测试LLM失败降级到规则-based分析"""
        # Mock LLM失败
        with patch.object(analyzer, '_call_llm_with_fallback', new=AsyncMock(side_effect=Exception("LLM服务不可用"))):
            result = await analyzer.analyze_novelty(sample_patent_data)

            # 验证降级到规则-based
            assert result["analysis_method"] == "rule-based"
            assert result["patent_id"] == "CN123456789A"
            assert "novelty_conclusion" in result

    @pytest.mark.asyncio
    async def test_compare_with_reference_llm_success(self, analyzer, sample_target_features):
        """测试LLM特征对比成功"""
        reference_doc = {
            "doc_id": "D1",
            "title": "对比文件1",
            "abstract": "包含处理器和传感器"
        }

        mock_response = '''```json
{
    "reference_id": "D1",
    "feature_comparison": [
        {
            "feature": "处理器",
            "category": "essential",
            "disclosed": true
        },
        {
            "feature": "深度学习算法",
            "category": "additional",
            "disclosed": false
        }
    ],
    "disclosed_count": 1,
    "undisclosed_count": 3,
    "total_count": 4,
    "disclosure_ratio": 0.25
}
```'''

        with patch.object(analyzer, '_call_llm_with_fallback', new=AsyncMock(return_value=mock_response)):
            result = await analyzer._compare_with_reference(
                sample_target_features,
                reference_doc,
                "individual"
            )

            # 验证结果
            assert result["reference_id"] == "D1"
            assert result["disclosed_count"] == 1
            assert result["disclosure_ratio"] == 0.25

    @pytest.mark.asyncio
    async def test_compare_with_reference_fallback_to_rules(self, analyzer, sample_target_features):
        """测试特征对比LLM失败降级"""
        reference_doc = {
            "doc_id": "D1",
            "features": {
                "essential": ["处理器"],
                "additional": []
            }
        }

        with patch.object(analyzer, '_call_llm_with_fallback', new=AsyncMock(side_effect=Exception("LLM错误"))):
            result = await analyzer._compare_with_reference(
                sample_target_features,
                reference_doc,
                "individual"
            )

            # 验证规则-based结果
            assert result["reference_id"] == "D1"
            assert "disclosed_count" in result
            assert "disclosure_ratio" in result

    @pytest.mark.asyncio
    async def test_judge_novelty_llm_success(self, analyzer):
        """测试LLM新颖性判断成功"""
        novel_features = [
            {"feature": "深度学习算法", "category": "additional", "importance": "high"},
            {"feature": "模块化设计", "category": "structural", "importance": "medium"}
        ]
        target_features = {
            "essential": ["处理器", "传感器"],
            "additional": ["深度学习算法"],
            "structural": ["模块化设计"]
        }

        mock_response = '''```json
{
    "has_novelty": true,
    "novelty_conclusion": "具备新颖性",
    "strength": "strong",
    "reasoning": "存在2个重要区别技术特征",
    "legal_basis": "专利法第22条第2款"
}
```'''

        with patch.object(analyzer, '_call_llm_with_fallback', new=AsyncMock(return_value=mock_response)):
            result = await analyzer._judge_novelty(novel_features, target_features)

            # 验证结果
            assert result["has_novelty"] is True
            assert result["strength"] == "strong"
            assert "专利法第22条第2款" in result["legal_basis"]

    @pytest.mark.asyncio
    async def test_judge_novelty_fallback_to_rules(self, analyzer):
        """测试新颖性判断LLM失败降级"""
        novel_features = [
            {"feature": "深度学习算法", "category": "additional"}
        ]
        target_features = {
            "essential": ["处理器"],
            "additional": ["深度学习算法"]
        }

        with patch.object(analyzer, '_call_llm_with_fallback', new=AsyncMock(side_effect=Exception("LLM错误"))):
            result = await analyzer._judge_novelty(novel_features, target_features)

            # 验证规则-based结果
            assert result["has_novelty"] is True
            assert result["novel_features_count"] == 1
            assert "conclusion" in result

    def test_parse_novelty_analysis_response_valid_json(self, analyzer):
        """测试解析有效的LLM新颖性分析响应"""
        response = '''```json
{
    "target_patent": "CN123456789A",
    "individual_comparisons": [],
    "distinguishing_features": [],
    "novelty_conclusion": {
        "has_novelty": true
    },
    "confidence_assessment": {
        "confidence_score": 0.8
    }
}
```'''

        result = analyzer._parse_novelty_analysis_response(response, {"patent_id": "CN123456789A"})

        assert result["patent_id"] == "CN123456789A"
        assert result["analysis_method"] == "llm"
        assert result["novelty_conclusion"]["has_novelty"] is True

    def test_parse_novelty_analysis_response_invalid_json(self, analyzer):
        """测试解析无效的LLM响应"""
        response = "这不是有效的JSON响应"

        with pytest.raises(Exception):
            analyzer._parse_novelty_analysis_response(response, {"patent_id": "CN123456789A"})

    def test_parse_feature_comparison_response_valid_json(self, analyzer):
        """测试解析有效的特征对比响应"""
        response = '''```json
{
    "reference_id": "D1",
    "feature_comparison": [],
    "disclosed_count": 2,
    "undisclosed_count": 1,
    "total_count": 3,
    "disclosure_ratio": 0.67
}
```'''

        result = analyzer._parse_feature_comparison_response(response, {"doc_id": "D1"})

        assert result["reference_id"] == "D1"
        assert result["disclosed_count"] == 2
        assert result["disclosure_ratio"] == 0.67

    def test_parse_novelty_judgment_response_valid_json(self, analyzer):
        """测试解析有效的新颖性判断响应"""
        response = '''```json
{
    "has_novelty": true,
    "novelty_conclusion": "具备新颖性",
    "strength": "strong",
    "reasoning": "存在重要区别特征"
}
```'''

        result = analyzer._parse_novelty_judgment_response(response)

        assert result["has_novelty"] is True
        assert result["strength"] == "strong"

    @pytest.mark.asyncio
    async def test_compare_by_rules_basic(self, analyzer, sample_target_features):
        """测试基于规则的特征对比基本功能"""
        reference_doc = {
            "doc_id": "D1",
            "title": "对比文件",
            "features": {
                "essential": ["处理器", "传感器"],
                "additional": []
            }
        }

        result = await analyzer._compare_by_rules(sample_target_features, reference_doc)

        assert result["reference_id"] == "D1"
        assert result["disclosed_count"] == 2
        # total_count包含所有类别的特征
        assert result["total_count"] >= 5
        assert result["disclosure_ratio"] > 0

    @pytest.mark.asyncio
    async def test_judge_novelty_by_rules_with_novelty(self, analyzer):
        """测试基于规则的新颖性判断（有新颖性）"""
        novel_features = [
            {"feature": "深度学习算法", "category": "additional"},
            {"feature": "模块化设计", "category": "structural"}
        ]
        target_features = {
            "essential": ["处理器"],
            "additional": ["深度学习算法"],
            "structural": ["模块化设计"]
        }

        result = analyzer._judge_novelty_by_rules(novel_features, target_features)

        assert result["has_novelty"] is True
        assert result["novel_features_count"] == 2
        assert result["novelty_ratio"] == 2/3
        assert result["strength"] == "strong"

    @pytest.mark.asyncio
    async def test_judge_novelty_by_rules_no_novelty(self, analyzer):
        """测试基于规则的新颖性判断（无新颖性）"""
        novel_features = []
        target_features = {
            "essential": ["处理器", "传感器"],
            "additional": []
        }

        result = analyzer._judge_novelty_by_rules(novel_features, target_features)

        assert result["has_novelty"] is False
        assert result["novel_features_count"] == 0
        assert result["conclusion"] == "不具备新颖性"
        assert result["strength"] == "none"

    @pytest.mark.asyncio
    async def test_analyze_novelty_empty_references(self, analyzer):
        """测试空对比文件列表的新颖性分析"""
        patent_data = {
            "patent_id": "CN123456789A",
            "claims": "1. 一种系统。",
            "prior_art_references": []
        }

        result = await analyzer.analyze_novelty(patent_data)

        assert result["patent_id"] == "CN123456789A"
        # 空对比文件应该返回默认结果

    def test_calculate_novelty_confidence(self, analyzer):
        """测试新颖性置信度计算"""
        novel_features = [
            {"feature": "特征1"},
            {"feature": "特征2"},
            {"feature": "特征3"}
        ]
        target_features = {
            "essential": ["特征1", "特征2", "特征3", "特征4", "特征5"],
            "additional": []
        }

        confidence = analyzer._calculate_novelty_confidence(novel_features, target_features)

        # 3/5 = 0.6, *1.5 = 0.9 (允许浮点误差)
        assert abs(confidence - 0.9) < 0.01

    def test_calculate_novelty_confidence_no_features(self, analyzer):
        """测试无特征时的置信度计算"""
        confidence = analyzer._calculate_novelty_confidence([], {})
        assert confidence == 0.0

    @pytest.mark.asyncio
    async def test_legacy_interface_compatibility(self, analyzer):
        """测试旧接口兼容性"""
        target_patent = {
            "patent_id": "CN123456789A",
            "claims": "1. 一种系统。"
        }
        reference_docs = [
            {"doc_id": "D1", "title": "对比文件1"}
        ]

        result = await analyzer.analyze_novelty_legacy(
            target_patent,
            reference_docs,
            "individual"
        )

        assert result["patent_id"] == "CN123456789A"
        assert "analysis_method" in result


class TestNoveltyAnalyzerPrompts:
    """NoveltyAnalyzer提示词测试"""

    @pytest.fixture
    def analyzer(self):
        """创建NoveltyAnalyzerProxy实例"""
        analyzer = NoveltyAnalyzerProxy(agent_id="test_novelty_analyzer")
        return analyzer

    def test_default_system_prompt(self, analyzer):
        """测试默认系统提示词"""
        prompt = analyzer._get_default_system_prompt()

        assert "专利新颖性分析专家" in prompt
        assert "单独对比原则" in prompt
        assert "JSON格式" in prompt

    def test_default_build_novelty_analysis_prompt(self, analyzer):
        """测试默认新颖性分析提示词构建"""
        patent_data = {
            "patent_id": "CN123456789A",
            "claims": "1. 一种系统。"
        }
        reference_docs = [{"doc_id": "D1"}]

        prompt = analyzer._default_build_novelty_analysis_prompt(
            patent_data,
            reference_docs
        )

        assert "CN123456789A" in prompt
        assert "1. 一种系统。" in prompt
        assert "1篇" in prompt

    def test_default_build_feature_comparison_prompt(self, analyzer):
        """测试默认特征对比提示词构建"""
        target_features = {"essential": ["特征1"]}
        reference_doc = {"doc_id": "D1"}

        prompt = analyzer._default_build_feature_comparison_prompt(
            target_features,
            reference_doc
        )

        assert "D1" in prompt
        assert "特征1" in prompt

    def test_default_build_novelty_judgment_prompt(self, analyzer):
        """测试默认新颖性判断提示词构建"""
        distinguishing_features = [{"feature": "特征1"}]
        target_features = {"essential": ["特征1", "特征2"]}

        prompt = analyzer._default_build_novelty_judgment_prompt(
            distinguishing_features,
            target_features
        )

        assert "1" in prompt  # 区别特征数量
        assert "2" in prompt  # 总特征数量
