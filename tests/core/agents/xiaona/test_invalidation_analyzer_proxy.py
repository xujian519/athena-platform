"""
无效宣告分析智能体单元测试

测试范围:
- 无效理由分析
- 证据搜集策略
- 成功概率评估
- 无效请求书生成
"""


import pytest

from core.framework.agents.xiaona.base_component import (
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
)
from core.framework.agents.xiaona.invalidation_analyzer_proxy import InvalidationAnalyzerProxy


class TestableInvalidationAnalyzerProxy(InvalidationAnalyzerProxy):
    """可测试的无效宣告分析智能体"""

    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """执行任务（测试用）"""
        return AgentExecutionResult(
            agent_id=self.agent_id,
            status=AgentStatus.COMPLETED,
            output_data={"test": "result"},
            execution_time=0.1
        )

    def get_system_prompt(self) -> str:
        """获取系统提示词（测试用）"""
        return "测试系统提示词"


class TestInvalidationAnalyzerProxy:
    """无效宣告分析智能体测试"""

    @pytest.fixture
    def agent(self):
        """创建智能体实例"""
        return TestableInvalidationAnalyzerProxy(agent_id="test_invalidation_analyzer")

    @pytest.fixture
    def sample_patent(self):
        """示例专利数据"""
        return {
            "patent_id": "CN123456789A",
            "title": "测试专利",
            "grant_date": "2026-01-01",
            "patentee": "测试公司",
            "claims": "1. 一种装置，包括特征A、特征B和特征C。",
            "specification": "本发明涉及一种装置技术领域...",
            "embodiments": [
                {"description": "实施例1"}
            ],
            "best_mode": "最佳实施方式",
            "drawings": ["图1", "图2"]
        }

    @pytest.fixture
    def sample_references(self):
        """示例对比文件"""
        return [
            {
                "publication_number": "CN1234567A",
                "content": "一种装置，包括特征A、特征B和特征C",
                "publication_date": "2025-01-01"
            },
            {
                "publication_number": "CN1234568A",
                "content": "另一种装置，包括特征A和特征D",
                "publication_date": "2025-06-01"
            }
        ]

    # ========== 初始化测试 ==========

    def test_initialization(self, agent):
        """测试智能体初始化"""
        assert agent.agent_id == "test_invalidation_analyzer"
        assert len(agent.get_capabilities()) == 4

        expected_capabilities = [
            "invalidation_ground_analysis",
            "evidence_collection_strategy",
            "success_probability_assessment",
            "invalidation_petition_support"
        ]
        capability_names = [cap.name for cap in agent.get_capabilities()]
        for cap in expected_capabilities:
            assert cap in capability_names

    # ========== analyze_invalidation 测试 ==========

    @pytest.mark.asyncio
    async def test_analyze_information_comprehensive(
        self,
        agent,
        sample_patent,
        sample_references
    ):
        """测试完整无效宣告分析流程"""
        result = await agent.analyze_invalidation(
            sample_patent,
            sample_references,
            analysis_depth="comprehensive"
        )

        # 验证返回结构
        assert "target_patent" in result
        assert "analysis_depth" in result
        assert result["analysis_depth"] == "comprehensive"
        assert "invalidation_grounds_analysis" in result
        assert "evidence_strategy" in result
        assert "success_probability" in result
        assert "petition_support" in result
        assert "overall_recommendation" in result
        assert "analyzed_at" in result

        # 验证目标专利信息
        assert result["target_patent"]["patent_id"] == "CN123456789A"

    @pytest.mark.asyncio
    async def test_analyze_invalidation_quick(
        self,
        agent,
        sample_patent,
        sample_references
    ):
        """测试快速分析模式"""
        result = await agent.analyze_invalidation(
            sample_patent,
            sample_references,
            analysis_depth="quick"
        )

        assert result["analysis_depth"] == "quick"
        assert "invalidation_grounds_analysis" in result

    # ========== analyze_invalidation_grounds 测试 ==========

    @pytest.mark.asyncio
    async def test_analyze_invalidation_grounds_with_novelty(
        self,
        agent,
        sample_patent,
        sample_references
    ):
        """测试分析无效理由 - 新颖性"""
        result = await agent.analyze_invalidation_grounds(
            sample_patent,
            sample_references
        )

        assert "valid_grounds" in result
        assert "total_grounds" in result
        assert "ground_strengths" in result
        assert "recommended_grounds" in result

        # 验证返回的无效理由
        valid_grounds = result["valid_grounds"]
        assert len(valid_grounds) > 0

        # 验证理由类型
        ground_types = [g["ground_type"] for g in valid_grounds]
        assert "lack_of_novelty" in ground_types or "lack_of_creativity" in ground_types

    @pytest.mark.asyncio
    async def test_analyze_invalidation_grounds_empty_references(
        self,
        agent,
        sample_patent
    ):
        """测试无对比文件时的分析"""
        result = await agent.analyze_invalidation_grounds(
            sample_patent,
            []
        )

        # 即使没有对比文件，也应该返回结果
        assert "valid_grounds" in result
        assert isinstance(result["valid_grounds"], list)

    # ========== develop_evidence_strategy 测试 ==========

    @pytest.mark.asyncio
    async def test_develop_evidence_strategy_novelty(
        self,
        agent
    ):
        """测试制定证据搜集策略 - 新颖性"""
        valid_grounds = ["lack_of_novelty"]
        existing_references = []

        result = await agent.develop_evidence_strategy(
            valid_grounds,
            existing_references
        )

        assert "evidence_categories" in result
        assert "collection_plan" in result
        assert "priority_list" in result

        # 验证证据类别
        categories = result["evidence_categories"]
        assert len(categories) > 0

        # 验证搜集计划
        plan = result["collection_plan"]
        assert len(plan) > 0

    @pytest.mark.asyncio
    async def test_develop_evidence_strategy_creativity(
        self,
        agent
    ):
        """测试制定证据搜集策略 - 创造性"""
        valid_grounds = ["lack_of_creativity"]
        existing_references = []

        result = await agent.develop_evidence_strategy(
            valid_grounds,
            existing_references
        )

        assert "evidence_categories" in result
        # 创造性应该有"结合启示"类别
        categories = result["evidence_categories"]
        category_descs = [c["description"] for c in categories]
        assert any("结合" in desc or "启示" in desc for desc in category_descs)

    # ========== assess_success_probability 测试 ==========

    @pytest.mark.asyncio
    async def test_assess_success_probability_high(
        self,
        agent
    ):
        """测试成功概率评估 - 高概率"""
        grounds_analysis = {
            "ground_strengths": [
                {"strength": "strong", "confidence": 0.9},
                {"strength": "strong", "confidence": 0.85}
            ]
        }
        evidence_strategy = {
            "collection_plan": [
                {"actions": ["action1", "action2", "action3"]},
                {"actions": ["action4"]}
            ]
        }

        result = await agent.assess_success_probability(
            grounds_analysis,
            evidence_strategy
        )

        assert "overall_probability" in result
        assert "confidence" in result
        assert "probability_breakdown" in result
        assert "prediction" in result

        # 高概率应该是>= 0.8
        assert result["overall_probability"] >= 0.8
        assert result["confidence"] == "high"

    @pytest.mark.asyncio
    async def test_assess_success_probability_low(
        self,
        agent
    ):
        """测试成功概率评估 - 低概率"""
        grounds_analysis = {
            "ground_strengths": [
                {"strength": "weak", "confidence": 0.4},
                {"strength": "weak", "confidence": 0.3}
            ]
        }
        evidence_strategy = {
            "collection_plan": []
        }

        result = await agent.assess_success_probability(
            grounds_analysis,
            evidence_strategy
        )

        assert "overall_probability" in result
        # 低概率应该<= 0.5
        assert result["overall_probability"] <= 0.5

    # ========== generate_invalidation_petition 测试 ==========

    @pytest.mark.asyncio
    async def test_generate_invalidation_petition(
        self,
        agent,
        sample_patent
    ):
        """测试生成无效请求书"""
        grounds_analysis = {
            "recommended_grounds": [
                {
                    "ground_type": "lack_of_novelty",
                    "description": "不具备新颖性",
                    "analysis": {
                        "confidence": 0.8,
                        "detailed_reasoning": "详细理由"
                    }
                }
            ]
        }
        evidence_strategy = {
            "collection_plan": [
                {"actions": ["action1", "action2"]}
            ]
        }
        probability_assessment = {
            "overall_probability": 0.75,
            "prediction": {
                "predicted_outcome": "部分无效"
            }
        }

        result = await agent.generate_invalidation_petition(
            sample_patent,
            grounds_analysis,
            evidence_strategy,
            probability_assessment
        )

        assert "petition_structure" in result
        assert "word_count" in result
        assert "estimated_preparation_time" in result
        assert "recommended_evidence_count" in result
        assert "completion_checklist" in result

        # 验证请求书结构
        structure = result["petition_structure"]
        assert "title" in structure
        assert "sections" in structure
        assert len(structure["sections"]) > 0

    # ========== 辅助方法测试 ==========

    def test_assess_ground_strength_strong(self, agent):
        """测试评估理由强度 - 强"""
        ground = {
            "analysis": {
                "confidence": 0.9
            }
        }
        strength = agent._assess_ground_strength(ground)
        assert strength == "strong"

    def test_assess_ground_strength_moderate(self, agent):
        """测试评估理由强度 - 中等"""
        ground = {
            "analysis": {
                "confidence": 0.7
            }
        }
        strength = agent._assess_ground_strength(ground)
        assert strength == "moderate"

    def test_assess_ground_strength_weak(self, agent):
        """测试评估理由强度 - 弱"""
        ground = {
            "analysis": {
                "confidence": 0.4
            }
        }
        strength = agent._assess_ground_strength(ground)
        assert strength == "weak"

    def test_extract_features(self, agent):
        """测试提取技术特征"""
        text = "一种装置，包括特征A、特征B和特征C，用于实现功能D"
        features = agent._extract_features(text)

        assert isinstance(features, list)
        assert len(features) > 0
        # 应该能提取到中文词汇
        assert all(isinstance(f, str) for f in features)

    def test_select_best_grounds(self, agent):
        """测试选择最佳无效理由"""
        valid_grounds = [
            {
                "ground_type": "ground1",
                "analysis": {"confidence": 0.6}
            },
            {
                "ground_type": "ground2",
                "analysis": {"confidence": 0.9}
            },
            {
                "ground_type": "ground3",
                "analysis": {"confidence": 0.7}
            }
        ]

        best = agent._select_best_grounds(valid_grounds)

        assert isinstance(best, list)
        assert len(best) <= 3  # 最多返回3个
        # 应该按置信度排序
        if len(best) >= 2:
            assert best[0]["analysis"]["confidence"] >= best[1]["analysis"]["confidence"]

    def test_generate_search_keywords(self, agent):
        """测试生成检索关键词"""
        keywords = agent._generate_search_keywords("lack_of_novelty")

        assert isinstance(keywords, list)
        assert len(keywords) > 0
        # 应该包含相关关键词
        assert any("技术" in k or "方案" in k for k in keywords)

    def test_generate_outcome_prediction(self, agent):
        """测试生成结果预测"""
        ground_strengths = [
            {"strength": "strong", "type": "novelty"}
        ]

        # 高概率
        prediction = agent._generate_outcome_prediction(0.85, ground_strengths)
        assert prediction["predicted_outcome"] == "全部无效"
        assert prediction["likelihood"] == "high"

        # 中等概率
        prediction = agent._generate_outcome_prediction(0.65, ground_strengths)
        assert prediction["predicted_outcome"] == "部分无效"
        assert prediction["likelihood"] == "medium"

        # 低概率
        prediction = agent._generate_outcome_prediction(0.3, ground_strengths)
        assert prediction["predicted_outcome"] in ["可能维持", "维持有效"]

    def test_identify_missing_disclosure_aspects(self, agent):
        """测试识别缺失的披露内容"""
        patent = {
            "embodiments": [],
            "best_mode": None,
            "drawings": []
        }

        missing = agent._identify_missing_disclosure_aspects(patent)

        assert isinstance(missing, list)
        assert len(missing) > 0
        assert any("实施方式" in m for m in missing)

    # ========== 边界条件测试 ==========

    @pytest.mark.asyncio
    async def test_analyze_invalidation_empty_patent(
        self,
        agent
    ):
        """测试空专利数据的处理（容错处理）"""
        # 代码使用容错处理，不会抛出异常
        result = await agent.analyze_invalidation({}, [], "comprehensive")

        # 验证返回结果结构
        assert "target_patent" in result
        assert "analysis_depth" in result
        assert result["analysis_depth"] == "comprehensive"

    @pytest.mark.asyncio
    async def test_assess_success_probability_empty_grounds(
        self,
        agent
    ):
        """测试无效理由为空时的概率评估"""
        result = await agent.assess_success_probability(
            {"ground_strengths": []},
            {"collection_plan": []}
        )

        assert result["overall_probability"] == 0.0
        assert result["confidence"] == "low"

    # ========== 性能测试 ==========

    @pytest.mark.asyncio
    async def test_performance_analyze_invalidation(
        self,
        agent,
        sample_patent,
        sample_references
    ):
        """测试分析性能 - 应该在合理时间内完成"""
        import time

        start_time = time.time()
        await agent.analyze_invalidation(
            sample_patent,
            sample_references,
            "comprehensive"
        )
        elapsed_time = time.time() - start_time

        # 完整分析应该在5秒内完成
        assert elapsed_time < 5.0

    # ========== 集成测试 ==========

    @pytest.mark.asyncio
    async def test_full_workflow(
        self,
        agent,
        sample_patent,
        sample_references
    ):
        """测试完整工作流程"""
        # 1. 分析无效理由
        grounds = await agent.analyze_invalidation_grounds(
            sample_patent,
            sample_references
        )

        # 2. 制定证据策略
        strategy = await agent.develop_evidence_strategy(
            [g["ground_type"] for g in grounds["valid_grounds"],
            sample_references
        )

        # 3. 评估成功概率
        probability = await agent.assess_success_probability(
            grounds,
            strategy
        )

        # 4. 生成请求书
        petition = await agent.generate_invalidation_petition(
            sample_patent,
            grounds,
            strategy,
            probability
        )

        # 验证工作流程连贯性
        assert grounds["total_grounds"] >= 0
        assert len(strategy["collection_plan"]) >= 0
        assert 0 <= probability["overall_probability"] <= 1
        assert petition["petition_structure"] is not None
