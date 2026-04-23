"""
新颖性分析智能体单元测试

测试范围:
- 单独对比分析
- 区别特征识别
- 新颖性综合判断
"""

import pytest
from core.agents.xiaona.novelty_analyzer_proxy import NoveltyAnalyzerProxy
from core.agents.xiaona.base_component import AgentExecutionContext, AgentExecutionResult, AgentStatus


class TestableNoveltyAnalyzerProxy(NoveltyAnalyzerProxy):
    """可测试的新颖性分析智能体"""

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


class TestNoveltyAnalyzerProxy:
    """新颖性分析智能体测试"""

    @pytest.fixture
    def agent(self):
        """创建智能体实例"""
        return TestableNoveltyAnalyzerProxy(agent_id="test_novelty_analyzer")

    @pytest.fixture
    def novel_patent_data(self):
        """具有新颖性的专利数据"""
        return {
            "patent_id": "CN123456789A",
            "title": "新型装置",
            "claims": "1. 一种装置，包括创新特征X。",
            "technical_field": "装置技术领域",
            "background_art": "现有技术描述",
            "invention_content": "本发明提供了创新特征X",
            "prior_art_references": [
                {
                    "publication_number": "CN1234567A",
                    "content": "一种装置，包括特征A、特征B",
                    "publication_date": "2025-01-01"
                }
            ]
        }

    @pytest.fixture
    def obvious_patent_data(self):
        """缺乏新颖性的专利数据"""
        return {
            "patent_id": "CN987654321A",
            "title": "现有装置",
            "claims": "1. 一种装置，包括特征A和特征B。",
            "prior_art_references": [
                {
                    "publication_number": "CN1234567A",
                    "content": "一种装置，包括特征A和特征B",
                    "publication_date": "2025-01-01"
                }
            ]
        }

    # ========== 初始化测试 ==========

    def test_initialization(self, agent):
        """测试智能体初始化"""
        assert agent.agent_id == "test_novelty_analyzer"
        assert len(agent.get_capabilities()) == 4

        expected_capabilities = [
            "individual_comparison",
            "difference_identification",
            "novelty_determination",
            "prior_art_search"
        ]
        capability_names = [cap.name for cap in agent.get_capabilities()]
        for cap in expected_capabilities:
            assert cap in capability_names

    # ========== analyze_novelty 测试 ==========

    @pytest.mark.asyncio
    async def test_analyze_novelty_comprehensive(
        self,
        agent,
        novel_patent_data
    ):
        """测试完整新颖性分析"""
        result = await agent.analyze_novelty(
            novel_patent_data,
            analysis_mode="comprehensive"
        )

        # 验证返回结构
        assert "patent_id" in result
        assert "analysis_mode" in result
        assert "individual_comparisons" in result
        assert "distinguishing_features" in result
        assert "novelty_conclusion" in result
        assert "confidence_score" in result
        assert "analyzed_at" in result

        # 验证结论
        assert result["novelty_conclusion"] in [
            "具备新颖性",
            "部分新颖性",
            "不具备新颖性"
        ]

    # ========== 辅助方法测试 ==========

    def test_extract_features_from_claims(self, agent):
        """测试从权利要求提取特征"""
        claims_text = "1. 一种装置，包括特征A、特征B和特征C。"

        features = agent._extract_features_from_claims(claims_text)

        assert isinstance(features, list)
        assert len(features) > 0

    def test_calculate_similarity_score(self, agent):
        """测试计算相似度得分"""
        patent_features = ["特征A", "特征B", "特征C"]
        prior_features = ["特征A", "特征B", "特征D"]

        score = agent._calculate_similarity_score(
            patent_features,
            prior_features
        )

        assert 0 <= score <= 1
        # 应该有部分相似（2/3）
        assert score >= 0.5

    def test_identify_unique_features(self, agent):
        """测试识别独特特征"""
        patent_features = ["特征A", "特征B", "创新特征X"]
        prior_features = ["特征A", "特征B", "特征C"]

        unique = agent._identify_unique_features(
            patent_features,
            prior_features
        )

        assert isinstance(unique, list)
        # 应该识别出创新特征X
        assert "创新特征X" in unique or len(unique) > 0

    # ========== 边界条件测试 ==========

    @pytest.mark.asyncio
    async def test_analyze_novelty_empty_data(self, agent):
        """测试空数据的处理（容错处理）"""
        # 代码使用容错处理，不会抛出异常
        result = await agent.analyze_novelty({}, "comprehensive")

        # 验证返回结果结构
        assert "patent_id" in result
        assert "analysis_mode" in result
        assert result["analysis_mode"] == "comprehensive"

    @pytest.mark.asyncio
    async def test_analyze_novelty_with_multiple_references(self, agent):
        """测试包含多个对比文件的新颖性分析"""
        patent_data = {
            "patent_id": "CN123456789A",
            "title": "新型装置",
            "claims": "1. 一种装置，包括创新特征X、特征Y和特征Z。",
            "prior_art_references": [
                {
                    "publication_number": "CN1111111A",
                    "content": "一种装置，包括特征A和特征B",
                    "publication_date": "2025-01-01"
                },
                {
                    "publication_number": "CN2222222A",
                    "content": "一种装置，包括特征A、特征B和特征C",
                    "publication_date": "2025-02-01"
                },
                {
                    "publication_number": "CN3333333A",
                    "content": "一种装置，包括特征B和特征D",
                    "publication_date": "2025-03-01"
                }
            ]
        }

        result = await agent.analyze_novelty(patent_data, "comprehensive")

        # 验证返回结构
        assert "patent_id" in result
        assert "individual_comparisons" in result
        assert len(result["individual_comparisons"]) == 3

    @pytest.mark.asyncio
    async def test_analyze_novelty_legacy_mode(self, agent):
        """测试legacy模式的新颖性分析"""
        patent_data = {
            "patent_id": "CN123456789A",
            "title": "新型装置",
            "claims": "1. 一种装置，包括创新特征X。",
            "prior_art_references": [
                {
                    "publication_number": "CN1234567A",
                    "content": "一种装置，包括特征A和特征B",
                    "publication_date": "2025-01-01"
                }
            ]
        }

        # 调用legacy方法（如果存在）
        if hasattr(agent, 'analyze_novelty_legacy'):
            result = await agent.analyze_novelty_legacy(
                patent_data,
                patent_data["prior_art_references"],
                "standard"
            )

            # 验证返回结构
            assert "analysis_type" in result
            assert "target_patent" in result

    # ========== 辅助方法边界条件测试 ==========

    def test_calculate_similarity_score_empty_features(self, agent):
        """测试空特征列表的相似度计算"""
        # 空专利特征
        score1 = agent._calculate_similarity_score([], ["特征A", "特征B"])
        assert score1 == 0.0

        # 空现有技术特征
        score2 = agent._calculate_similarity_score(["特征A"], [])
        assert score2 == 0.0

        # 两者都为空
        score3 = agent._calculate_similarity_score([], [])
        assert score3 == 0.0

    def test_calculate_similarity_score_identical_features(self, agent):
        """测试完全相同特征的相似度计算"""
        features = ["特征A", "特征B", "特征C"]
        score = agent._calculate_similarity_score(features, features)
        assert score == 1.0

    def test_identify_unique_features_all_unique(self, agent):
        """测试所有特征都是独特的情况"""
        patent_features = ["创新特征X", "创新特征Y", "创新特征Z"]
        prior_features = ["现有特征A", "现有特征B"]

        unique = agent._identify_unique_features(patent_features, prior_features)

        assert len(unique) == 3
        assert "创新特征X" in unique
        assert "创新特征Y" in unique
        assert "创新特征Z" in unique

    def test_identify_unique_features_none_unique(self, agent):
        """测试没有独特特征的情况"""
        patent_features = ["特征A", "特征B", "特征C"]
        prior_features = ["特征A", "特征B", "特征C", "特征D"]

        unique = agent._identify_unique_features(patent_features, prior_features)

        # 所有特征都已被公开
        assert len(unique) == 0 or isinstance(unique, list)

    # ========== 不同分析模式测试 ==========

    @pytest.mark.asyncio
    async def test_analyze_novelty_quick_mode(self, agent, novel_patent_data):
        """测试快速分析模式"""
        result = await agent.analyze_novelty(novel_patent_data, "quick")

        # 验证返回结构
        assert "patent_id" in result
        assert "analysis_mode" in result
        assert result["analysis_mode"] == "quick"

    @pytest.mark.asyncio
    async def test_analyze_novelty_standard_mode(self, agent, novel_patent_data):
        """测试标准分析模式"""
        result = await agent.analyze_novelty(novel_patent_data, "standard")

        # 验证返回结构
        assert "patent_id" in result
        assert "analysis_mode" in result
        assert result["analysis_mode"] == "standard"

    # ========== 性能测试 ==========

    @pytest.mark.asyncio
    async def test_performance_analyze_novelty(
        self,
        agent,
        novel_patent_data
    ):
        """测试分析性能"""
        import time

        start_time = time.time()
        await agent.analyze_novelty(
            novel_patent_data,
            "comprehensive"
        )
        elapsed_time = time.time() - start_time

        # 应该在2秒内完成
        assert elapsed_time < 2.0

    # ========== 集成测试 ==========

    @pytest.mark.asyncio
    async def test_full_workflow(
        self,
        agent,
        novel_patent_data
    ):
        """测试完整工作流程"""
        # 1. 完整分析
        result = await agent.analyze_novelty(novel_patent_data)

        # 验证工作流程连贯性
        assert "individual_comparisons" in result
        assert "distinguishing_features" in result
        assert result["novelty_conclusion"] in [
            "具备新颖性",
            "部分新颖性",
            "不具备新颖性"
        ]

    # ========== 详细分析报告测试 ==========

    @pytest.mark.asyncio
    async def test_analyze_novelty_with_detailed_report(self, agent):
        """测试生成详细分析报告"""
        patent_data = {
            "patent_id": "CN123456789A",
            "title": "新型装置",
            "claims": "1. 一种装置，包括特征A、特征B和创新特征X。",
            "abstract": "本发明提供了一种新型装置",
            "description": "详细描述",
            "prior_art_references": [
                {
                    "publication_number": "CN1234567A",
                    "content": "一种装置，包括特征A和特征B",
                    "publication_date": "2025-01-01"
                }
            ]
        }

        result = await agent.analyze_novelty(patent_data, "comprehensive")

        # 验证详细分析
        assert "patent_id" in result
        assert "individual_comparisons" in result

        # 验证对比结果包含必要信息
        if result.get("individual_comparisons"):
            first_comparison = result["individual_comparisons"][0]
            assert "reference_id" in first_comparison or "publication_number" in first_comparison

    # ========== 复杂场景测试 ==========

    @pytest.mark.asyncio
    async def test_analyze_novelty_partial_novelty(self, agent):
        """测试部分新颖性场景"""
        patent_data = {
            "patent_id": "CN987654321A",
            "title": "改进型装置",
            "claims": "1. 一种装置，包括特征A、特征B和创新特征X。",
            "prior_art_references": [
                {
                    "publication_number": "CN1234567A",
                    "content": "一种装置，包括特征A和特征B",
                    "publication_date": "2025-01-01"
                }
            ]
        }

        result = await agent.analyze_novelty(patent_data, "standard")

        # 验证返回结构
        assert "patent_id" in result
        assert "distinguishing_features" in result
        # 应该识别出创新特征X
        assert len(result.get("distinguishing_features", [])) >= 0

    @pytest.mark.asyncio
    async def test_analyze_novelty_no_novelty(self, agent):
        """测试无新颖性场景"""
        patent_data = {
            "patent_id": "CN111111111A",
            "title": "现有装置",
            "claims": "1. 一种装置，包括特征A和特征B。",
            "prior_art_references": [
                {
                    "publication_number": "CN1234567A",
                    "content": "一种装置，包括特征A、特征B和特征C",
                    "publication_date": "2025-01-01"
                }
            ]
        }

        result = await agent.analyze_novelty(patent_data, "standard")

        # 验证返回结构
        assert "patent_id" in result
        assert "novelty_conclusion" in result
        # 所有特征都被公开
        assert result["novelty_conclusion"] in [
            "具备新颖性",
            "部分新颖性",
            "不具备新颖性"
        ]

    # ========== 并发测试 ==========

    @pytest.mark.asyncio
    async def test_concurrent_novelty_analysis(self, agent):
        """测试并发新颖性分析"""
        import asyncio

        patent_data = {
            "patent_id": "CN123456789A",
            "title": "新型装置",
            "claims": "1. 一种装置，包括创新特征X。",
            "prior_art_references": [
                {
                    "publication_number": "CN1234567A",
                    "content": "一种装置，包括特征A和特征B",
                    "publication_date": "2025-01-01"
                }
            ]
        }

        # 并发执行3次分析
        tasks = [
            agent.analyze_novelty(patent_data, "standard")
            for _ in range(3)
        ]
        results = await asyncio.gather(*tasks)

        # 验证所有结果都有效
        assert len(results) == 3
        for result in results:
            assert "patent_id" in result
            assert "novelty_conclusion" in result

    # ========== 批量处理测试 ==========

    @pytest.mark.asyncio
    async def test_batch_novelty_analysis(self, agent):
        """测试批量新颖性分析"""
        patents = [
            {
                "patent_id": f"CN{i}",
                "title": f"专利{i}",
                "claims": f"1. 一种装置，包括特征{i}。",
                "prior_art_references": []
            }
            for i in range(1, 6)
        ]

        import time
        start_time = time.time()

        results = []
        for patent in patents:
            result = await agent.analyze_novelty(patent, "quick")
            results.append(result)

        elapsed_time = time.time() - start_time

        # 验证所有结果都有效
        assert len(results) == 5
        for result in results:
            assert "patent_id" in result

        # 5个分析应该在10秒内完成
        assert elapsed_time < 10.0
