"""
InvalidationAnalyzerProxy LLM集成测试

测试无效宣告分析智能体的LLM调用功能。
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from core.agents.xiaona.invalidation_analyzer_proxy import InvalidationAnalyzerProxy


@pytest.fixture
def analyzer():
    """创建无效宣告分析智能体实例"""
    return InvalidationAnalyzerProxy(
        agent_id="test_invalidation_analyzer",
        config={"llm_config": {"model": "claude-3-5-sonnet-20241022"}}
    )


@pytest.fixture
def sample_patent():
    """示例专利数据"""
    return {
        "patent_id": "CN123456789A",
        "title": "一种基于深度学习的自动驾驶方法",
        "grant_date": "2023-05-15",
        "patentee": "某某科技有限公司",
        "claims": """
1. 一种基于深度学习的自动驾驶方法，其特征在于，包括：
    获取多模态环境数据，所述多模态环境数据包括视觉数据、激光雷达数据和毫米波雷达数据；
    采用多模态融合深度学习模型对所述多模态环境数据进行融合处理，得到融合特征；
    通过自适应权重调整机制动态调整各模态的权重；
    采用端到端学习框架进行环境感知和决策。

2. 根据权利要求1所述的方法，其特征在于，所述多模态融合深度学习模型采用注意力机制进行特征融合。
""",
        "specification": """
本发明涉及人工智能技术领域，具体涉及一种基于深度学习的自动驾驶方法。

背景技术：现有自动驾驶技术在复杂环境下感知准确率低，鲁棒性不足。

发明内容：本发明采用多模态融合深度学习模型，结合视觉、激光雷达和毫米波雷达数据进行环境感知，通过自适应权重调整机制优化感知效果。

具体实施方式：如图1所示，本发明系统包括数据采集模块、融合处理模块和决策模块...
""",
        "embodiments": [
            "实施例1：在城市道路环境下，采集摄像头、激光雷达和毫米波雷达数据...",
            "实施例2：在高速公路环境下，调整传感器权重..."
        ],
        "prosecution_history": []
    }


@pytest.fixture
def sample_references():
    """示例对比文件"""
    return [
        {
            "publication_number": "CN101234567A",
            "title": "一种车载视觉感知方法",
            "publication_date": "2020-01-15",
            "content": "采用单目摄像头进行环境感知，准确率75%"
        },
        {
            "publication_number": "US9876543B2",
            "title": "激光雷达点云处理方法",
            "publication_date": "2019-08-20",
            "content": "使用激光雷达进行3D目标检测"
        },
        {
            "publication_number": "JP2020123456A",
            "title": "毫米波雷达目标检测",
            "publication_date": "2020-03-10",
            "content": "采用毫米波雷达进行远距离目标检测"
        }
    ]


@pytest.fixture
def sample_patent_weak():
    """示例弱专利数据（容易被无效）"""
    return {
        "patent_id": "CN987654321B",
        "title": "一种水杯",
        "grant_date": "2022-03-10",
        "patentee": "某日用品公司",
        "claims": """
1. 一种水杯，包括杯体和杯盖，其特征在于，所述杯盖为红色。
""",
        "specification": "本发明涉及一种水杯，特别是杯盖为红色的水杯。",
        "embodiments": [],
        "prosecution_history": []
    }


class TestComprehensiveInvalidationAnalysisWithLLM:
    """测试完整无效宣告分析（LLM版本）"""

    @pytest.mark.asyncio
    async def test_comprehensive_analysis_with_llm_success(self, analyzer, sample_patent, sample_references):
        """测试LLM完整分析成功"""
        # Mock LLM响应
        mock_response = """```json
{
    "invalidation_grounds_analysis": {
        "valid_grounds": [
            {
                "ground_type": "lack_of_novelty",
                "description": "不具备新颖性",
                "analysis": {
                    "is_valid_ground": false,
                    "confidence": 0.3,
                    "detailed_reasoning": "对比文件未公开所有技术特征",
                    "suggested_evidence": []
                },
                "strength": "weak"
            },
            {
                "ground_type": "lack_of_creativity",
                "description": "不具备创造性",
                "analysis": {
                    "is_valid_ground": false,
                    "confidence": 0.4,
                    "detailed_reasoning": "多模态融合和自适应权重调整具有创造性",
                    "suggested_evidence": []
                },
                "strength": "weak"
            }
        ],
        "total_grounds": 2,
        "ground_strengths": [
            {"type": "lack_of_novelty", "strength": "weak", "confidence": 0.3},
            {"type": "lack_of_creativity", "strength": "weak", "confidence": 0.4}
        ],
        "recommended_grounds": []
    },
    "evidence_strategy": {
        "evidence_categories": [],
        "collection_plan": [],
        "priority_list": []
    },
    "success_probability": {
        "overall_probability": 0.25,
        "confidence": "low",
        "probability_breakdown": {
            "ground_strength": 0.3,
            "evidence_quality": 0.5,
            "legal_basis": 0.7
        },
        "prediction": {
            "predicted_outcome": "维持有效",
            "likelihood": "very_low",
            "reasoning": "无效理由强度不足"
        },
        "risk_factors": ["所有无效理由强度均较弱"],
        "recommended_strategy": "建议重新评估无效宣告的可行性"
    },
    "petition_support": {
        "petition_structure": {
            "title": "专利无效宣告请求书（CN123456789A）",
            "sections": []
        },
        "word_count": 500,
        "estimated_preparation_time": "1-2天",
        "recommended_evidence_count": 0,
        "completion_checklist": []
    },
    "overall_recommendation": "建议重新评估无效宣告的可行性，成功概率较低"
}
```"""

        # Mock LLM调用
        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        # 执行分析
        result = await analyzer.analyze_invalidation(
            target_patent=sample_patent,
            prior_art_references=sample_references,
            analysis_depth="comprehensive"
        )

        # 验证结果
        assert result["analysis_method"] == "llm"
        assert result["target_patent"]["patent_id"] == "CN123456789A"
        assert "invalidation_grounds_analysis" in result
        assert "evidence_strategy" in result
        assert "success_probability" in result
        assert result["success_probability"]["overall_probability"] < 0.3

    @pytest.mark.asyncio
    async def test_comprehensive_analysis_fallback_to_rules(self, analyzer, sample_patent, sample_references):
        """测试LLM失败时降级到规则-based分析"""
        # Mock LLM调用失败
        analyzer._call_llm_with_fallback = AsyncMock(side_effect=Exception("LLM service unavailable"))

        # 执行分析
        result = await analyzer.analyze_invalidation(
            target_patent=sample_patent,
            prior_art_references=sample_references,
            analysis_depth="comprehensive"
        )

        # 验证降级到规则-based
        assert result["analysis_method"] == "rule-based"
        assert "invalidation_grounds_analysis" in result
        assert "evidence_strategy" in result

    @pytest.mark.asyncio
    async def test_comprehensive_analysis_quick_mode(self, analyzer, sample_patent, sample_references):
        """测试快速分析模式"""
        mock_response = """```json
{
    "invalidation_grounds_analysis": {
        "valid_grounds": [],
        "total_grounds": 0,
        "ground_strengths": [],
        "recommended_grounds": []
    },
    "evidence_strategy": {
        "evidence_categories": [],
        "collection_plan": [],
        "priority_list": []
    },
    "success_probability": {
        "overall_probability": 0.2,
        "confidence": "low",
        "probability_breakdown": {
            "ground_strength": 0.2,
            "evidence_quality": 0.3,
            "legal_basis": 0.5
        },
        "prediction": {
            "predicted_outcome": "维持有效",
            "likelihood": "very_low",
            "reasoning": "无明显无效理由"
        },
        "risk_factors": [],
        "recommended_strategy": "不建议提交无效宣告"
    },
    "petition_support": {
        "petition_structure": {"title": "", "sections": []},
        "word_count": 200,
        "estimated_preparation_time": "1天",
        "recommended_evidence_count": 0,
        "completion_checklist": []
    },
    "overall_recommendation": "不建议提交无效宣告"
}
```"""

        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        result = await analyzer.analyze_invalidation(
            target_patent=sample_patent,
            prior_art_references=sample_references,
            analysis_depth="quick"
        )

        assert result["analysis_depth"] == "quick"


class TestInvalidationGroundsAnalysisWithLLM:
    """测试无效理由分析（LLM版本）"""

    @pytest.mark.asyncio
    async def test_grounds_analysis_novelty_only(self, analyzer, sample_patent, sample_references):
        """测试仅新颖性无效理由"""
        mock_response = """```json
{
    "valid_grounds": [
        {
            "ground_type": "lack_of_novelty",
            "description": "不具备新颖性",
            "analysis": {
                "is_valid_ground": true,
                "confidence": 0.85,
                "detailed_reasoning": "对比文件CN101234567A公开了所有技术特征",
                "suggested_evidence": ["CN101234567A"]
            },
            "strength": "strong"
        }
    ],
    "total_grounds": 1,
    "ground_strengths": [
        {"type": "lack_of_novelty", "strength": "strong", "confidence": 0.85}
    ],
    "recommended_grounds": [
        {
            "ground_type": "lack_of_novelty",
            "description": "不具备新颖性",
            "analysis": {},
            "strength": "strong"
        }
    ]
}
```"""

        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        result = await analyzer.analyze_invalidation_grounds(
            patent=sample_patent,
            references=sample_references
        )

        assert result["total_grounds"] == 1
        assert result["valid_grounds"][0]["ground_type"] == "lack_of_novelty"
        assert result["valid_grounds"][0]["strength"] == "strong"

    @pytest.mark.asyncio
    async def test_grounds_analysis_multiple_grounds(self, analyzer, sample_patent, sample_references):
        """测试多个无效理由"""
        mock_response = """```json
{
    "valid_grounds": [
        {
            "ground_type": "lack_of_novelty",
            "description": "不具备新颖性",
            "analysis": {
                "is_valid_ground": true,
                "confidence": 0.75,
                "detailed_reasoning": "对比文件公开了大部分技术特征",
                "suggested_evidence": ["CN101234567A"]
            },
            "strength": "moderate"
        },
        {
            "ground_type": "lack_of_creativity",
            "description": "不具备创造性",
            "analysis": {
                "is_valid_ground": true,
                "confidence": 0.8,
                "detailed_reasoning": "技术方案显而易见",
                "suggested_evidence": ["US9876543B2", "JP2020123456A"]
            },
            "strength": "strong"
        }
    ],
    "total_grounds": 2,
    "ground_strengths": [
        {"type": "lack_of_novelty", "strength": "moderate", "confidence": 0.75},
        {"type": "lack_of_creativity", "strength": "strong", "confidence": 0.8}
    ],
    "recommended_grounds": [
        {
            "ground_type": "lack_of_creativity",
            "description": "不具备创造性",
            "analysis": {},
            "strength": "strong"
        }
    ]
}
```"""

        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        result = await analyzer.analyze_invalidation_grounds(
            patent=sample_patent,
            references=sample_references
        )

        assert result["total_grounds"] == 2
        assert len(result["recommended_grounds"]) >= 1

    @pytest.mark.asyncio
    async def test_grounds_analysis_insufficient_disclosure(self, analyzer, sample_patent_weak):
        """测试公开不充分无效理由"""
        mock_response = """```json
{
    "valid_grounds": [
        {
            "ground_type": "insufficient_disclosure",
            "description": "说明书公开不充分",
            "analysis": {
                "is_valid_ground": true,
                "confidence": 0.7,
                "detailed_reasoning": "缺少具体实施方式",
                "suggested_evidence": []
            },
            "strength": "moderate"
        }
    ],
    "total_grounds": 1,
    "ground_strengths": [
        {"type": "insufficient_disclosure", "strength": "moderate", "confidence": 0.7}
    ],
    "recommended_grounds": []
}
```"""

        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        result = await analyzer.analyze_invalidation_grounds(
            patent=sample_patent_weak,
            references=[]
        )

        assert result["total_grounds"] == 1
        assert result["valid_grounds"][0]["ground_type"] == "insufficient_disclosure"


class TestNoveltyAnalysisWithLLM:
    """测试新颖性分析（LLM版本）"""

    @pytest.mark.asyncio
    async def test_novelty_analysis_destroyed(self, analyzer, sample_patent, sample_references):
        """测试新颖性被破坏"""
        mock_response = """```json
{
    "is_valid_ground": true,
    "confidence": 0.9,
    "detailed_reasoning": "对比文件CN101234567A公开了权利要求1的所有技术特征",
    "suggested_evidence": ["CN101234567A"],
    "feature_comparison": {
        "total_features": 8,
        "disclosed_features": 8,
        "undisclosed_features": []
    }
}
```"""

        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        result = await analyzer._analyze_novelty_ground(
            patent=sample_patent,
            references=sample_references
        )

        assert result["is_valid_ground"] is True
        assert result["confidence"] >= 0.8
        assert len(result["suggested_evidence"]) > 0

    @pytest.mark.asyncio
    async def test_novelty_analysis_not_destroyed(self, analyzer, sample_patent, sample_references):
        """测试新颖性未被破坏"""
        mock_response = """```json
{
    "is_valid_ground": false,
    "confidence": 0.75,
    "detailed_reasoning": "对比文件未公开自适应权重调整机制",
    "suggested_evidence": [],
    "feature_comparison": {
        "total_features": 8,
        "disclosed_features": 5,
        "undisclosed_features": ["自适应权重调整机制", "端到端学习框架"]
    }
}
```"""

        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        result = await analyzer._analyze_novelty_ground(
            patent=sample_patent,
            references=sample_references
        )

        assert result["is_valid_ground"] is False
        assert result["confidence"] >= 0.7

    @pytest.mark.asyncio
    async def test_novelty_analysis_fallback(self, analyzer, sample_patent, sample_references):
        """测试新颖性分析降级"""
        analyzer._call_llm_with_fallback = AsyncMock(side_effect=Exception("LLM error"))

        result = await analyzer._analyze_novelty_ground(
            patent=sample_patent,
            references=sample_references
        )

        # 应该降级到规则-based
        assert "is_valid_ground" in result
        assert "confidence" in result


class TestCreativityAnalysisWithLLM:
    """测试创造性分析（LLM版本）"""

    @pytest.mark.asyncio
    async def test_creativity_analysis_obvious(self, analyzer, sample_patent, sample_references):
        """测试显而易见"""
        mock_response = """```json
{
    "is_valid_ground": true,
    "confidence": 0.8,
    "detailed_reasoning": "多模态融合是本领域常规技术手段，组合显而易见",
    "suggested_evidence": ["CN101234567A", "US9876543B2"],
    "obviousness_analysis": {
        "disclosed_features": ["视觉数据", "激光雷达数据"],
        "undisclosed_features": ["自适应权重调整"],
        "teaching_away": "无相反教导",
        "combination_motivation": "提高感知准确率的常见需求"
    }
}
```"""

        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        result = await analyzer._analyze_creativity_ground(
            patent=sample_patent,
            references=sample_references
        )

        assert result["is_valid_ground"] is True
        assert result["confidence"] >= 0.7

    @pytest.mark.asyncio
    async def test_creativity_analysis_not_obvious(self, analyzer, sample_patent, sample_references):
        """测试非显而易见"""
        mock_response = """```json
{
    "is_valid_ground": false,
    "confidence": 0.7,
    "detailed_reasoning": "自适应权重调整机制带来了预料不到的技术效果",
    "suggested_evidence": [],
    "obviousness_analysis": {
        "disclosed_features": ["视觉数据", "激光雷达数据"],
        "undisclosed_features": ["自适应权重调整机制", "端到端学习框架"],
        "teaching_away": "现有技术倾向于使用固定权重",
        "combination_motivation": "无明确结合启示"
    }
}
```"""

        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        result = await analyzer._analyze_creativity_ground(
            patent=sample_patent,
            references=sample_references
        )

        assert result["is_valid_ground"] is False
        assert result["confidence"] >= 0.6

    @pytest.mark.asyncio
    async def test_creativity_analysis_fallback(self, analyzer, sample_patent, sample_references):
        """测试创造性分析降级"""
        analyzer._call_llm_with_fallback = AsyncMock(side_effect=Exception("LLM error"))

        result = await analyzer._analyze_creativity_ground(
            patent=sample_patent,
            references=sample_references
        )

        # 应该降级到规则-based
        assert "is_valid_ground" in result
        assert "confidence" in result


class TestInsufficientDisclosureAnalysisWithLLM:
    """测试公开不充分分析（LLM版本）"""

    @pytest.mark.asyncio
    async def test_disclosure_analysis_insufficient(self, analyzer, sample_patent_weak):
        """测试公开不充分"""
        mock_response = """```json
{
    "is_valid_ground": true,
    "confidence": 0.8,
    "detailed_reasoning": "说明书缺少具体实施方式，本领域技术人员无法实现",
    "missing_aspects": ["具体实施方式", "技术细节", "实现参数"],
    "disclosure_assessment": {
        "technical_field": "sufficient",
        "technical_solution": "insufficient",
        "enablement": "insufficient",
        "beneficial_effects": "insufficient"
    }
}
```"""

        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        result = await analyzer._analyze_insufficient_disclosure(
            patent=sample_patent_weak
        )

        assert result["is_valid_ground"] is True
        assert len(result["missing_aspects"]) > 0

    @pytest.mark.asyncio
    async def test_disclosure_analysis_sufficient(self, analyzer, sample_patent):
        """测试公开充分"""
        mock_response = """```json
{
    "is_valid_ground": false,
    "confidence": 0.7,
    "detailed_reasoning": "说明书公开较为充分，包含详细实施方式",
    "missing_aspects": [],
    "disclosure_assessment": {
        "technical_field": "sufficient",
        "technical_solution": "sufficient",
        "enablement": "sufficient",
        "beneficial_effects": "sufficient"
    }
}
```"""

        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        result = await analyzer._analyze_insufficient_disclosure(
            patent=sample_patent
        )

        assert result["is_valid_ground"] is False
        assert len(result["missing_aspects"]) == 0

    @pytest.mark.asyncio
    async def test_disclosure_analysis_fallback(self, analyzer, sample_patent):
        """测试公开不充分分析降级"""
        analyzer._call_llm_with_fallback = AsyncMock(side_effect=Exception("LLM error"))

        result = await analyzer._analyze_insufficient_disclosure(
            patent=sample_patent
        )

        # 应该降级到规则-based
        assert "is_valid_ground" in result
        assert "confidence" in result


class TestEvidenceStrategyWithLLM:
    """测试证据策略制定（LLM版本）"""

    @pytest.mark.asyncio
    async def test_evidence_strategy_novelty(self, analyzer, sample_references):
        """测试新颖性证据策略"""
        mock_response = """```json
{
    "evidence_categories": [
        {
            "category": "对比文件",
            "description": "能够破坏新颖性的对比文件",
            "sources": [
                "中国专利申请",
                "外国专利文献",
                "非专利文献"
            ],
            "search_keywords": ["自动驾驶", "多模态融合", "深度学习"]
        }
    ],
    "collection_plan": [
        {
            "priority": 1,
            "category": "对比文件",
            "actions": [
                {
                    "source": "中国专利申请",
                    "estimated_time": "3-5天",
                    "responsible": "检索者"
                },
                {
                    "source": "外国专利文献",
                    "estimated_time": "5-7天",
                    "responsible": "检索者"
                }
            ]
        }
    ],
    "priority_list": [
        {
            "ground": "lack_of_novelty",
            "priority": "high"
        }
    ]
}
```"""

        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        result = await analyzer.develop_evidence_strategy(
            valid_grounds=["lack_of_novelty"],
            existing_references=sample_references
        )

        assert len(result["evidence_categories"]) > 0
        assert len(result["collection_plan"]) > 0
        assert len(result["priority_list"]) > 0

    @pytest.mark.asyncio
    async def test_evidence_strategy_multiple_grounds(self, analyzer, sample_references):
        """测试多个无效理由的证据策略"""
        mock_response = """```json
{
    "evidence_categories": [
        {
            "category": "对比文件",
            "description": "破坏新颖性的对比文件",
            "sources": ["专利文献", "非专利文献"],
            "search_keywords": ["关键词1", "关键词2"]
        },
        {
            "category": "结合启示",
            "description": "现有技术的结合启示",
            "sources": ["教科书", "技术手册"],
            "search_keywords": ["技术启示", "结合动机"]
        }
    ],
    "collection_plan": [
        {
            "priority": 1,
            "category": "对比文件",
            "actions": [
                {"source": "专利文献", "estimated_time": "3-5天", "responsible": "检索者"}
            ]
        },
        {
            "priority": 2,
            "category": "结合启示",
            "actions": [
                {"source": "教科书", "estimated_time": "2-3天", "responsible": "检索者"}
            ]
        }
    ],
    "priority_list": [
        {"ground": "lack_of_novelty", "priority": "high"},
        {"ground": "lack_of_creativity", "priority": "medium"}
    ]
}
```"""

        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        result = await analyzer.develop_evidence_strategy(
            valid_grounds=["lack_of_novelty", "lack_of_creativity"],
            existing_references=sample_references
        )

        assert len(result["evidence_categories"]) == 2
        assert len(result["collection_plan"]) == 2
        assert len(result["priority_list"]) == 2

    @pytest.mark.asyncio
    async def test_evidence_strategy_fallback(self, analyzer, sample_references):
        """测试证据策略降级"""
        analyzer._call_llm_with_fallback = AsyncMock(side_effect=Exception("LLM error"))

        result = await analyzer.develop_evidence_strategy(
            valid_grounds=["lack_of_novelty"],
            existing_references=sample_references
        )

        # 应该降级到规则-based
        assert "evidence_categories" in result
        assert "collection_plan" in result
        assert "priority_list" in result


class TestEdgeCasesAndErrorHandling:
    """测试边界条件和错误处理"""

    @pytest.mark.asyncio
    async def test_empty_patent_data(self, analyzer):
        """测试空专利数据"""
        # 空数据不会抛出异常，而是返回默认结果
        result = await analyzer.analyze_invalidation(
            target_patent={},
            prior_art_references=[],
            analysis_depth="comprehensive"
        )

        # 验证返回结果结构完整
        assert "invalidation_grounds_analysis" in result
        assert "evidence_strategy" in result
        assert "success_probability" in result
        assert result["analysis_method"] == "rule-based"  # 应该降级到规则-based

    @pytest.mark.asyncio
    async def test_empty_references(self, analyzer, sample_patent):
        """测试空对比文件"""
        mock_response = """```json
{
    "invalidation_grounds_analysis": {
        "valid_grounds": [],
        "total_grounds": 0,
        "ground_strengths": [],
        "recommended_grounds": []
    },
    "evidence_strategy": {
        "evidence_categories": [],
        "collection_plan": [],
        "priority_list": []
    },
    "success_probability": {
        "overall_probability": 0.1,
        "confidence": "low",
        "probability_breakdown": {"ground_strength": 0, "evidence_quality": 0, "legal_basis": 0.5},
        "prediction": {"predicted_outcome": "维持有效", "likelihood": "very_low", "reasoning": "无对比文件"},
        "risk_factors": ["缺少对比文件"],
        "recommended_strategy": "建议先进行检索"
    },
    "petition_support": {
        "petition_structure": {"title": "", "sections": []},
        "word_count": 0,
        "estimated_preparation_time": "0天",
        "recommended_evidence_count": 0,
        "completion_checklist": []
    },
    "overall_recommendation": "需要先搜集对比文件"
}
```"""

        analyzer._call_llm_with_fallback = AsyncMock(return_value=mock_response)

        result = await analyzer.analyze_invalidation(
            target_patent=sample_patent,
            prior_art_references=[],
            analysis_depth="comprehensive"
        )

        assert result["success_probability"]["overall_probability"] < 0.2

    @pytest.mark.asyncio
    async def test_malformed_llm_response(self, analyzer, sample_patent, sample_references):
        """测试格式错误的LLM响应"""
        analyzer._call_llm_with_fallback = AsyncMock(return_value="This is not valid JSON")

        result = await analyzer.analyze_invalidation(
            target_patent=sample_patent,
            prior_art_references=sample_references,
            analysis_depth="comprehensive"
        )

        # 应该使用默认值
        assert "invalidation_grounds_analysis" in result

    @pytest.mark.asyncio
    async def test_llm_timeout(self, analyzer, sample_patent, sample_references):
        """测试LLM超时"""
        analyzer._call_llm_with_fallback = AsyncMock(
            side_effect=asyncio.TimeoutError("LLM timeout")
        )

        result = await analyzer.analyze_invalidation(
            target_patent=sample_patent,
            prior_art_references=sample_references,
            analysis_depth="comprehensive"
        )

        # 应该降级到规则-based
        assert result["analysis_method"] == "rule-based"

    @pytest.mark.asyncio
    async def test_large_references_list(self, analyzer, sample_patent):
        """测试大量对比文件"""
        large_references = [
            {
                "publication_number": f"CN{i:08d}A",
                "title": f"对比文件{i}",
                "content": f"技术内容{i}" * 100
            }
            for i in range(50)
        ]

        # 应该正常处理
        result = await analyzer.develop_evidence_strategy(
            valid_grounds=["lack_of_novelty"],
            existing_references=large_references
        )

        assert "evidence_categories" in result

    @pytest.mark.asyncio
    async def test_system_prompt_generation(self, analyzer):
        """测试系统提示词生成"""
        prompt = analyzer.get_system_prompt()

        assert "无效宣告分析专家" in prompt
        assert "专利法" in prompt
        assert "JSON格式" in prompt

    @pytest.mark.asyncio
    async def test_capability_registration(self, analyzer):
        """测试能力注册"""
        # 能力在_initialize中注册，通过_get_capability方法访问
        # 这里验证初始化是否成功
        assert analyzer.agent_id == "test_invalidation_analyzer"

        # 验证系统提示词存在
        prompt = analyzer.get_system_prompt()
        assert len(prompt) > 0
        assert "无效宣告分析专家" in prompt


class TestSuccessProbabilityAssessment:
    """测试成功概率评估"""

    @pytest.mark.asyncio
    async def test_high_success_probability(self, analyzer):
        """测试高成功概率"""
        grounds_analysis = {
            "ground_strengths": [
                {"type": "lack_of_novelty", "strength": "strong", "confidence": 0.9},
                {"type": "lack_of_creativity", "strength": "strong", "confidence": 0.85}
            ]
        }

        evidence_strategy = {
            "collection_plan": [
                {"priority": 1, "actions": [{"source": "专利文献"}]},
                {"priority": 2, "actions": [{"source": "教科书"}]},
                {"priority": 3, "actions": [{"source": "技术手册"}]}
            ]
        }

        result = await analyzer.assess_success_probability(
            grounds_analysis=grounds_analysis,
            evidence_strategy=evidence_strategy
        )

        assert result["overall_probability"] >= 0.7
        assert result["confidence"] in ["high", "medium", "low"]

    @pytest.mark.asyncio
    async def test_low_success_probability(self, analyzer):
        """测试低成功概率"""
        grounds_analysis = {
            "ground_strengths": [
                {"type": "lack_of_novelty", "strength": "weak", "confidence": 0.4}
            ]
        }

        evidence_strategy = {
            "collection_plan": []
        }

        result = await analyzer.assess_success_probability(
            grounds_analysis=grounds_analysis,
            evidence_strategy=evidence_strategy
        )

        assert result["overall_probability"] < 0.5

    @pytest.mark.asyncio
    async def test_probability_boundary_conditions(self, analyzer):
        """测试概率边界条件"""
        # 测试概率上限
        grounds_analysis = {
            "ground_strengths": [
                {"type": "lack_of_novelty", "strength": "strong", "confidence": 1.0},
                {"type": "lack_of_creativity", "strength": "strong", "confidence": 1.0}
            ]
        }

        evidence_strategy = {
            "collection_plan": [
                {"priority": i, "actions": []}
                for i in range(10)
            ]
        }

        result = await analyzer.assess_success_probability(
            grounds_analysis=grounds_analysis,
            evidence_strategy=evidence_strategy
        )

        # 概率应该在合理范围内
        assert 0.0 <= result["overall_probability"] <= 1.0
