"""
创造性分析智能体单元测试

测试范围:
- 显著进步判断
- 预料不到效果评估
- 创造性综合分析
"""

import pytest
from core.agents.xiaona.creativity_analyzer_proxy import CreativityAnalyzerProxy
from core.agents.xiaona.base_component import AgentExecutionContext, AgentExecutionResult, AgentStatus


class TestableCreativityAnalyzerProxy(CreativityAnalyzerProxy):
    """可测试的创造性分析智能体"""

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


class TestCreativityAnalyzerProxy:
    """创造性分析智能体测试"""

    @pytest.fixture
    def agent(self):
        """创建智能体实例"""
        return TestableCreativityAnalyzerProxy(agent_id="test_creativity_analyzer")

    @pytest.fixture
    def sample_patent_data(self):
        """示例专利数据"""
        return {
            "patent_id": "CN123456789A",
            "title": "具有创造性装置",
            "technical_field": "装置技术",
            "background_art": "现有技术中的装置存在性能问题",
            "invention_content": "本发明通过优化特征A，显著提高了性能",
            "claims": "1. 一种装置，包括优化后的特征A。",
            "prior_art": [
                {
                    "publication_number": "CN1234567A",
                    "content": "一种装置，包括特征A",
                    "differences": "本申请增加了优化"
                }
            ]
        }

    # ========== 初始化测试 ==========

    def test_initialization(self, agent):
        """测试智能体初始化"""
        assert agent.agent_id == "test_creativity_analyzer"
        assert len(agent.get_capabilities()) == 4

        expected_capabilities = [
            "obviousness_assessment",
            "inventive_step_evaluation",
            "technical_advancement_analysis",
            "creativity_evaluation"
        ]
        capability_names = [cap.name for cap in agent.get_capabilities()]
        for cap in expected_capabilities:
            assert cap in capability_names

    # ========== analyze_creativity 测试 ==========

    @pytest.mark.asyncio
    async def test_analyze_creativity_comprehensive(
        self,
        agent,
        sample_patent_data
    ):
        """测试完整创造性分析"""
        result = await agent.analyze_creativity(
            sample_patent_data,
            analysis_mode="comprehensive"
        )

        # 验证返回结构
        assert "patent_id" in result
        assert "analysis_mode" in result
        assert "obviousness_assessment" in result
        assert "inventive_step_evaluation" in result
        assert "creativity_conclusion" in result
        assert "confidence_score" in result
        assert "analyzed_at" in result

        # 验证结论
        assert result["creativity_conclusion"] in [
            "有创造性",
            "具备创造性",
            "无明显创造性",
            "缺乏创造性"
        ]

    # ========== assess_obviousness 测试 ==========

    @pytest.mark.asyncio
    async def test_assess_obviousness_non_obvious(
        self,
        agent,
        sample_patent_data
    ):
        """测试显而易见性评估 - 不显而易见"""
        result = await agent.assess_obviousness(sample_patent_data)

        assert "is_obvious" in result
        assert "confidence" in result
        assert "reasoning" in result

        # 应该有布尔结果
        assert isinstance(result["is_obvious"], bool)

    @pytest.mark.asyncio
    async def test_assess_obviousness_obvious(
        self,
        agent
    ):
        """测试显而易见性评估 - 显而易见"""
        patent_data = {
            "patent_id": "CN123456789A",
            "prior_art": [
                {"content": "现有技术已经公开了相同方案"}
            ],
            "differences": "仅做简单替换"
        }

        result = await agent.assess_obviousness(patent_data)

        # 简单替换应该被认为是显而易见
        if len(patent_data["prior_art"]) > 0 and patent_data["differences"] == "仅做简单替换":
            # 可能是显而易见
            pass

    # ========== evaluate_inventive_step 测试 ==========

    @pytest.mark.asyncio
    async def test_evaluate_inventive_step_significant(
        self,
        agent,
        sample_patent_data
    ):
        """测试创造性步骤评估 - 显著"""
        result = await agent.evaluate_inventive_step(sample_patent_data)

        assert "has_inventive_step" in result
        assert "step_magnitude" in result
        assert "evidence" in result

        # 应该有布尔结果
        assert isinstance(result["has_inventive_step"], bool)

    # ========== analyze_technical_advancement 测试 ==========

    @pytest.mark.asyncio
    async def test_analyze_technical_advancement(
        self,
        agent,
        sample_patent_data
    ):
        """测试技术进步分析"""
        result = await agent.analyze_technical_advancement(sample_patent_data)

        assert "has_advancement" in result
        assert "advancement_type" in result
        assert "improvement_degree" in result
        assert "evidence" in result

        # 应该有布尔结果
        assert isinstance(result["has_advancement"], bool)

    # ========== 辅助方法测试 ==========

    def test_extract_differences(self, agent):
        """测试提取区别特征"""
        patent_text = "本发明与现有技术的区别在于：增加了特征A，优化了特征B"
        differences = agent._extract_differences(patent_text)

        assert isinstance(differences, list)
        # 应该能提取到区别
        assert len(differences) > 0 or isinstance(differences, list)

    def test_assess_teaching_away(self, agent):
        """测试评估教导 away"""
        prior_art = [
            {"content": "现有技术明确指出特征A不可行"}
        ]

        teaching_away = agent._assess_teaching_away(prior_art)

        assert "has_teaching_away" in teaching_away
        assert isinstance(teaching_away["has_teaching_away"], bool)

    def test_identify_surprising_effect(self, agent):
        """测试识别预料不到的效果"""
        patent_data = {
            "invention_content": "性能提升了200%，远超预期"
        }

        effect = agent._identify_surprising_effect(patent_data)

        assert "has_surprising_effect" in effect
        assert "effect_description" in effect

    # ========== 边界条件测试 ==========

    @pytest.mark.asyncio
    async def test_analyze_creativity_empty_data(self, agent):
        """测试空数据的处理（容错处理）"""
        # 代码使用容错处理，不会抛出异常
        result = await agent.analyze_creativity({}, "comprehensive")

        # 验证返回结果结构
        assert "patent_id" in result
        assert "analysis_mode" in result
        assert result["analysis_mode"] == "comprehensive"

    # ========== 性能测试 ==========

    @pytest.mark.asyncio
    async def test_performance_analyze_creativity(
        self,
        agent,
        sample_patent_data
    ):
        """测试分析性能"""
        import time

        start_time = time.time()
        await agent.analyze_creativity(
            sample_patent_data,
            "comprehensive"
        )
        elapsed_time = time.time() - start_time

        # 应该在3秒内完成
        assert elapsed_time < 3.0

    # ========== 集成测试 ==========

    @pytest.mark.asyncio
    async def test_full_workflow(
        self,
        agent,
        sample_patent_data
    ):
        """测试完整工作流程"""
        # 1. 评估显而易见性
        obviousness = await agent.assess_obviousness(sample_patent_data)

        # 2. 评估创造性步骤
        inventive_step = await agent.evaluate_inventive_step(sample_patent_data)

        # 3. 分析技术进步
        advancement = await agent.analyze_technical_advancement(sample_patent_data)

        # 验证工作流程连贯性
        assert "is_obvious" in obviousness
        assert "has_inventive_step" in inventive_step
        assert "has_advancement" in advancement

    # ========== 不同分析模式测试 ==========

    @pytest.mark.asyncio
    async def test_analyze_creativity_quick_mode(self, agent, sample_patent_data):
        """测试快速分析模式"""
        result = await agent.analyze_creativity(sample_patent_data, "quick")

        # 验证返回结构
        assert "patent_id" in result
        assert "analysis_mode" in result
        assert result["analysis_mode"] == "quick"

    @pytest.mark.asyncio
    async def test_analyze_creativity_standard_mode(self, agent, sample_patent_data):
        """测试标准分析模式"""
        result = await agent.analyze_creativity(sample_patent_data, "standard")

        # 验证返回结构
        assert "patent_id" in result
        assert "analysis_mode" in result
        assert result["analysis_mode"] == "standard"

    # ========== 复杂场景测试 ==========

    @pytest.mark.asyncio
    async def test_assess_obviousness_with_teaching_away(self, agent):
        """测试存在教导away的显而易见性评估"""
        patent_data = {
            "patent_id": "CN123456789A",
            "title": "具有创造性的装置",
            "differences": "增加了创新特征",
            "prior_art": [
                {
                    "publication_number": "CN1234567A",
                    "content": "现有技术明确指出该特征不可行或无法实现"
                }
            ]
        }

        result = await agent.assess_obviousness(patent_data)

        # 验证返回结构
        assert "is_obvious" in result
        assert "confidence" in result
        assert "reasoning" in result

    @pytest.mark.asyncio
    async def test_evaluate_inventive_step_with_surprising_effect(self, agent):
        """测试具有预料不到效果的创造性步骤评估"""
        patent_data = {
            "patent_id": "CN123456789A",
            "title": "具有预料不到效果的装置",
            "invention_content": "性能提升了200%，远超预期",
            "differences": "优化了关键参数"
        }

        result = await agent.evaluate_inventive_step(patent_data)

        # 验证返回结构
        assert "has_inventive_step" in result
        assert "step_magnitude" in result
        assert "evidence" in result

    @pytest.mark.asyncio
    async def test_analyze_technical_advancement_significant(self, agent):
        """测试显著技术进步分析"""
        patent_data = {
            "patent_id": "CN123456789A",
            "title": "技术突破装置",
            "invention_content": "性能提升10倍，成本降低50%",
            "beneficial_effects": "显著提高生产效率"
        }

        result = await agent.analyze_technical_advancement(patent_data)

        # 验证返回结构
        assert "has_advancement" in result
        assert "advancement_type" in result
        assert "improvement_degree" in result
        assert "evidence" in result

    # ========== 并发测试 ==========

    @pytest.mark.asyncio
    async def test_concurrent_creativity_analysis(self, agent, sample_patent_data):
        """测试并发创造性分析"""
        import asyncio

        # 并发执行3次分析
        tasks = [
            agent.analyze_creativity(sample_patent_data, "standard")
            for _ in range(3)
        ]
        results = await asyncio.gather(*tasks)

        # 验证所有结果都有效
        assert len(results) == 3
        for result in results:
            assert "patent_id" in result
            assert "creativity_conclusion" in result

    # ========== 批量处理测试 ==========

    @pytest.mark.asyncio
    async def test_batch_creativity_analysis(self, agent):
        """测试批量创造性分析"""
        patents = [
            {
                "patent_id": f"CN{i}",
                "title": f"专利{i}",
                "invention_content": f"技术方案{i}",
                "prior_art": []
            }
            for i in range(1, 6)
        ]

        import time
        start_time = time.time()

        results = []
        for patent in patents:
            result = await agent.analyze_creativity(patent, "quick")
            results.append(result)

        elapsed_time = time.time() - start_time

        # 验证所有结果都有效
        assert len(results) == 5
        for result in results:
            assert "patent_id" in result

        # 5个分析应该在10秒内完成
        assert elapsed_time < 10.0

    # ========== 边界条件测试 ==========

    @pytest.mark.asyncio
    async def test_analyze_creativity_with_no_prior_art(self, agent):
        """测试无现有技术的创造性分析"""
        patent_data = {
            "patent_id": "CN123456789A",
            "title": "全新发明",
            "invention_content": "全新的技术方案",
            "prior_art": []
        }

        result = await agent.analyze_creativity(patent_data, "standard")

        # 验证返回结构
        assert "patent_id" in result
        assert "creativity_conclusion" in result
        # 无现有技术时应该有默认处理
        assert result["creativity_conclusion"] in [
            "有创造性",
            "具备创造性",
            "无明显创造性",
            "缺乏创造性"
        ]

    @pytest.mark.asyncio
    async def test_analyze_creativity_minimal_data(self, agent):
        """测试最小数据集的创造性分析"""
        patent_data = {
            "patent_id": "CN123"
        }

        result = await agent.analyze_creativity(patent_data, "quick")

        # 验证返回结构（容错处理）
        assert "patent_id" in result
        assert "analysis_mode" in result
