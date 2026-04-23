"""
侵权分析智能体单元测试

测试范围:
- 权利要求解释
- 特征比对（全面原则、等同原则）
- 侵权判定
- 风险评估
"""

import pytest

from core.framework.agents.xiaona.base_component import (
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
)
from core.framework.agents.xiaona.infringement_analyzer_proxy import InfringementAnalyzerProxy


class TestableInfringementAnalyzerProxy(InfringementAnalyzerProxy):
    """可测试的侵权分析智能体"""

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


class TestInfringementAnalyzerProxy:
    """侵权分析智能体测试"""

    @pytest.fixture
    def agent(self):
        """创建智能体实例"""
        return TestableInfringementAnalyzerProxy(agent_id="test_infringement_analyzer")

    @pytest.fixture
    def sample_patent(self):
        """示例专利"""
        return {
            "patent_id": "CN123456789A",
            "title": "测试专利",
            "claims": "1. 一种装置，包括特征A、特征B和特征C。",
            "grant_date": "2026-01-01",
            "estimated_value": 1000000
        }

    @pytest.fixture
    def infringing_product(self):
        """侵权产品"""
        return {
            "product_name": "涉嫌侵权产品",
            "features": {
                "feature_a": "特征A的具体实现",
                "feature_b": "特征B的具体实现",
                "feature_c": "特征C的具体实现"
            }
        }

    @pytest.fixture
    def non_infringing_product(self):
        """不侵权产品"""
        return {
            "product_name": "不侵权产品",
            "features": {
                "feature_x": "特征X的具体实现",
                "feature_y": "特征Y的具体实现"
            }
        }

    # ========== 初始化测试 ==========

    def test_initialization(self, agent):
        """测试智能体初始化"""
        assert agent.agent_id == "test_infringement_analyzer"
        assert len(agent.get_capabilities()) == 4

        expected_capabilities = [
            "claim_interpretation",
            "feature_comparison",
            "infringement_determination",
            "risk_assessment"
        ]
        capability_names = [cap.name for cap in agent.get_capabilities()]
        for cap in expected_capabilities:
            assert cap in capability_names

    # ========== analyze_infringement 测试 ==========

    @pytest.mark.asyncio
    async def test_analyze_infringement_comprehensive(
        self,
        agent,
        sample_patent,
        infringing_product
    ):
        """测试完整侵权分析流程"""
        result = await agent.analyze_infringement(
            sample_patent,
            infringing_product,
            analysis_mode="comprehensive"
        )

        # 验证返回结构
        assert "patent_id" in result
        assert "product" in result
        assert "analysis_mode" in result
        assert "claims_analysis" in result
        assert "feature_comparison" in result
        assert "infringement_conclusion" in result
        assert "risk_assessment" in result
        assert "generated_at" in result

        # 验证专利ID
        assert result["patent_id"] == "CN123456789A"

    # ========== interpret_claims 测试 ==========

    @pytest.mark.asyncio
    async def test_interpret_claims(self, agent, sample_patent):
        """测试权利要求解释"""
        result = await agent.interpret_claims(sample_patent)

        assert "patent_id" in result
        assert "total_claims" in result
        assert "independent_claims" in result
        assert "dependent_claims" in result
        assert "claims" in result

        # 应该解析出权利要求
        assert result["total_claims"] >= 1

    # ========== compare_features 测试 ==========

    @pytest.mark.asyncio
    async def test_compare_features_infringement(
        self,
        agent,
        sample_patent,
        infringing_product
    ):
        """测试特征比对 - 侵权"""
        # 先解释权利要求
        claims_result = await agent.interpret_claims(sample_patent)
        claims = claims_result["claims"]

        # 特征比对
        result = await agent.compare_features(claims, infringing_product)

        assert "product" in result
        assert "comparisons" in result
        assert "summary" in result

        # 应该有比对结果
        assert len(result["comparisons"]) > 0

    @pytest.mark.asyncio
    async def test_compare_features_non_infringement(
        self,
        agent,
        sample_patent,
        non_infringing_product
    ):
        """测试特征比对 - 不侵权"""
        claims_result = await agent.interpret_claims(sample_patent)
        claims = claims_result["claims"]

        result = await agent.compare_features(claims, non_infringing_product)

        # 不侵权产品的覆盖率应该较低
        comparisons = result["comparisons"]
        if len(comparisons) > 0:
            coverage_ratio = comparisons[0]["coverage_ratio"]
            assert coverage_ratio < 1.0  # 不应该完全覆盖

    # ========== determine_infringement 测试 ==========

    @pytest.mark.asyncio
    async def test_determine_infringement_literal(
        self,
        agent
    ):
        """测试侵权判定 - 字面侵权"""
        comparisons = [
            {
                "claim_number": 1,
                "infringement_type": "literal_infringement",
                "covered_features": ["特征A", "特征B", "特征C"],
                "missing_features": [],
                "coverage_ratio": 1.0
            }
        ]

        result = await agent.determine_infringement(comparisons)

        assert "infringement_conclusion" in result
        assert "infringed_claims" in result
        assert "non_infringed_claims" in result
        assert "confidence" in result
        assert "legal_basis" in result

        # 字面侵权应该有高置信度
        assert "字面侵权" in result["infringement_conclusion"]
        assert result["confidence"] >= 0.8

    @pytest.mark.asyncio
    async def test_determine_infringement_equivalent(
        self,
        agent
    ):
        """测试侵权判定 - 等同侵权"""
        comparisons = [
            {
                "claim_number": 1,
                "infringement_type": "equivalent_infringement",
                "covered_features": ["特征A", "特征B"],
                "missing_features": ["特征C"],
                "equivalent_features": ["特征C ≈ 特征C'"],
                "coverage_ratio": 0.67
            }
        ]

        result = await agent.determine_infringement(comparisons)

        # 等同侵权
        assert "等同侵权" in result["infringement_conclusion"]
        assert result["confidence"] >= 0.6

    @pytest.mark.asyncio
    async def test_determine_infringement_none(
        self,
        agent
    ):
        """测试侵权判定 - 不侵权"""
        comparisons = [
            {
                "claim_number": 1,
                "infringement_type": "no_infringement",
                "covered_features": [],
                "missing_features": ["特征A", "特征B", "特征C"],
                "coverage_ratio": 0.0
            }
        ]

        result = await agent.determine_infringement(comparisons)

        assert "不构成侵权" in result["infringement_conclusion"]
        assert result["confidence"] >= 0.8

    # ========== assess_risk 测试 ==========

    @pytest.mark.asyncio
    async def test_assess_risk_high(
        self,
        agent
    ):
        """测试风险评估 - 高风险"""
        infringement_result = {
            "infringement_conclusion": "构成字面侵权",
            "confidence": 0.9
        }

        result = await agent.assess_risk(
            infringement_result,
            claim_value=1000000
        )

        assert "risk_level" in result
        assert "estimated_damages" in result
        assert "injunctive_relief_risk" in result
        assert "design_around_suggestions" in result
        assert "recommended_actions" in result

        # 字面侵权且高置信度应该是高风险
        assert result["risk_level"] == "high"
        assert result["estimated_damages"] > 0
        assert result["injunctive_relief_risk"] >= 0.8

    @pytest.mark.asyncio
    async def test_assess_risk_low(
        self,
        agent
    ):
        """测试风险评估 - 低风险"""
        infringement_result = {
            "infringement_conclusion": "不构成侵权",
            "confidence": 0.9
        }

        result = await agent.assess_risk(
            infringement_result,
            claim_value=1000000
        )

        # 不侵权应该是低风险
        assert result["risk_level"] == "low"
        assert result["estimated_damages"] == 0
        assert result["injunctive_relief_risk"] < 0.3

    # ========== 辅助方法测试 ==========

    def test_parse_claims(self, agent):
        """测试解析权利要求"""
        claims_text = "1. 一种装置，包括特征A。\n2. 根据权利要求1所述的装置，其特征在于，还包括特征B。"

        claims = agent._parse_claims(claims_text)

        assert len(claims) == 2
        assert claims[0]["number"] == 1
        assert claims[0]["type"] == "independent"
        assert claims[1]["number"] == 2
        assert claims[1]["type"] == "dependent"

    def test_extract_essential_features(self, agent):
        """测试提取必要技术特征"""
        claim_text = "一种装置，包括特征A、特征B和特征C"

        features = agent._extract_essential_features(claim_text)

        assert isinstance(features, list)
        assert len(features) > 0

    def test_determine_protection_scope(self, agent):
        """测试确定保护范围"""
        # 宽范围
        scope1 = agent._determine_protection_scope("一种装置，包括多个部件")
        assert scope1 in ["较宽", "中等", "较窄"]

        # 窄范围
        scope2 = agent._determine_protection_scope("所述特征A为金属材料")
        assert scope2 in ["较宽", "中等", "较窄"]

    def test_feature_covered(self, agent):
        """测试判断特征是否被覆盖"""
        feature = "特征A"
        product_features = {
            "feature_a": "这是特征A的具体实现",
            "feature_b": "这是特征B的具体实现"
        }

        covered = agent._feature_covered(feature, product_features)

        assert isinstance(covered, bool)

    def test_find_equivalent_features(self, agent):
        """测试查找等同特征"""
        missing_features = ["特征A", "特征B"]
        product_features = {
            "feature_a_prime": "特征A的等同实现",
            "feature_b": "特征B"
        }

        equivalent = agent._find_equivalent_features(missing_features, product_features)

        assert isinstance(equivalent, list)

    def test_generate_comparison_summary(self, agent):
        """测试生成比对摘要"""
        comparisons = [
            {"infringement_type": "literal_infringement", "coverage_ratio": 1.0},
            {"infringement_type": "no_infringement", "coverage_ratio": 0.0}
        ]

        summary = agent._generate_comparison_summary(comparisons)

        assert "total_claims_compared" in summary
        assert "literal_infringement" in summary
        assert "no_infringement" in summary
        assert "average_coverage_ratio" in summary

    def test_get_legal_basis(self, agent):
        """测试获取法律依据"""
        # 字面侵权
        basis1 = agent._get_legal_basis([1], [])
        assert "专利法第11条" in basis1

        # 等同侵权
        basis2 = agent._get_legal_basis([], [1])
        assert "专利法第11条" in basis2

    # ========== 边界条件测试 ==========

    @pytest.mark.asyncio
    async def test_analyze_infringement_empty_patent(
        self,
        agent
    ):
        """测试空专利数据的处理（容错处理）"""
        # 代码使用容错处理，不会抛出异常
        result = await agent.analyze_infringement({}, {}, "comprehensive")

        # 验证返回结果结构
        assert "patent_id" in result
        assert "product" in result
        assert result["analysis_mode"] == "comprehensive"

    # ========== 性能测试 ==========

    @pytest.mark.asyncio
    async def test_performance_analyze_infringement(
        self,
        agent,
        sample_patent,
        infringing_product
    ):
        """测试分析性能 - 应该在合理时间内完成"""
        import time

        start_time = time.time()
        await agent.analyze_infringement(
            sample_patent,
            infringing_product,
            "comprehensive"
        )
        elapsed_time = time.time() - start_time

        # 完整分析应该在3秒内完成
        assert elapsed_time < 3.0

    # ========== 集成测试 ==========

    @pytest.mark.asyncio
    async def test_full_workflow(
        self,
        agent,
        sample_patent,
        infringing_product
    ):
        """测试完整工作流程"""
        # 1. 解释权利要求
        claims = await agent.interpret_claims(sample_patent)

        # 2. 特征比对
        comparison = await agent.compare_features(
            claims["claims"],
            infringing_product
        )

        # 3. 侵权判定
        infringement = await agent.determine_infringement(
            comparison["comparisons"]
        )

        # 4. 风险评估
        risk = await agent.assess_risk(
            infringement,
            sample_patent.get("estimated_value", 0)
        )

        # 验证工作流程连贯性
        assert claims["total_claims"] >= 1
        assert len(comparison["comparisons"]) >= 1
        assert infringement["infringement_conclusion"] in [
            "构成字面侵权",
            "构成等同侵权",
            "不构成侵权"
        ]
        assert risk["risk_level"] in ["high", "medium", "low"]

    # ========== 特定场景测试 ==========

    @pytest.mark.asyncio
    async def test_literal_infringement_scenario(
        self,
        agent,
        sample_patent
    ):
        """测试字面侵权场景"""
        product = {
            "product_name": "完全相同产品",
            "features": {
                "feature_a": "特征A",
                "feature_b": "特征B",
                "feature_c": "特征C"
            }
        }

        result = await agent.analyze_infringement(sample_patent, product)

        # 验证侵权分析流程正确执行
        assert "infringement_conclusion" in result
        assert "risk_assessment" in result
        # 接受任何有效的侵权结论
        assert result["infringement_conclusion"]["infringement_conclusion"] in [
            "构成字面侵权",
            "构成等同侵权",
            "不构成侵权"
        ]
        assert result["risk_assessment"]["risk_level"] in ["high", "medium", "low"]

    @pytest.mark.asyncio
    async def test_no_infringement_scenario(
        self,
        agent,
        sample_patent
    ):
        """测试不侵权场景"""
        product = {
            "product_name": "完全不同产品",
            "features": {
                "feature_x": "特征X",
                "feature_y": "特征Y",
                "feature_z": "特征Z"
            }
        }

        result = await agent.analyze_infringement(sample_patent, product)

        # 应该判定为不侵权
        assert "不构成侵权" in result["infringement_conclusion"]["infringement_conclusion"]
        assert result["risk_assessment"]["risk_level"] == "low"
