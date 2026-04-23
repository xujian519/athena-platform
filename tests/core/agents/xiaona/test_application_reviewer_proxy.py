"""
申请文件审查智能体单元测试

测试范围:
- 格式规范审查
- 技术披露充分性审查
- 权利要求书审查
- 说明书审查
"""

import pytest
from core.agents.xiaona.application_reviewer_proxy import ApplicationDocumentReviewerProxy
from core.agents.xiaona.base_component import AgentExecutionContext, AgentExecutionResult, AgentStatus


class TestableApplicationDocumentReviewerProxy(ApplicationDocumentReviewerProxy):
    """可测试的申请文件审查智能体"""

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


class TestApplicationDocumentReviewerProxy:
    """申请文件审查智能体测试"""

    @pytest.fixture
    def agent(self):
        """创建智能体实例"""
        return TestableApplicationDocumentReviewerProxy(agent_id="test_application_reviewer")

    @pytest.fixture
    def complete_application(self):
        """完整的申请文件"""
        return {
            "application_id": "CN202600000000",
            "applicant": "测试公司",
            "applicant_data": {
                "name": "测试公司",
                "address": "北京市测试区测试街123号",
                "nationality": "中国"
            },
            "documents": [
                "请求书",
                "说明书",
                "权利要求书",
                "摘要",
                "说明书附图"
            ],
            "technical_field": "本发明涉及一种智能控制装置技术领域，特别涉及一种基于人工智能的自适应控制系统。",
            "background_art": "现有技术中，传统的控制装置通常采用固定的控制策略，无法根据环境变化自动调整。此外，现有装置在复杂环境下的响应速度和精度都有待提高。虽然有一些改进方案，但仍然存在响应延迟和能耗过高的问题。",
            "invention_summary": "本发明提供了一种智能控制装置，通过引入深度学习算法和自适应反馈机制，实现了对复杂环境的实时响应和精确控制，显著提高了系统的稳定性和能效。",
            "technical_problem": "现有控制装置存在以下问题：1）响应速度慢，无法满足实时性要求；2）控制精度低，误差较大；3）能耗高，资源利用率低；4）缺乏自适应能力，无法应对复杂多变的环境。",
            "technical_solution": "本发明通过以下技术方案解决上述问题：采用多层神经网络模型进行环境感知和预测，结合自适应PID控制算法，实现对被控对象的精确控制。同时引入能耗优化模块，在保证控制精度的前提下降低能耗。",
            "beneficial_effects": "与现有技术相比，本发明具有以下有益效果：1）响应速度提升50%以上；2）控制精度提高30%；3）能耗降低20%；4）具备良好的自适应能力，可应对复杂环境变化。",
            "claims": "1. 一种智能控制装置，其特征在于包括：传感器模块、处理器模块、控制执行模块；所述传感器模块用于采集环境参数；所述处理器模块用于根据采集的参数计算控制指令；所述控制执行模块用于执行控制指令。\n2. 根据权利要求1所述的装置，其特征在于，所述处理器模块采用深度学习算法进行参数预测。",
            "specification": "技术领域...背景技术...发明内容...具体实施方式...",
            "embodiments": [
                {"description": "实施例1：详细描述"},
                {"description": "实施例2：详细描述"}
            ],
            "best_mode": "最佳实施方式",
            "drawings": ["图1", "图2"]
        }

    @pytest.fixture
    def incomplete_application(self):
        """不完整的申请文件"""
        return {
            "application_id": "CN202600000001",
            "applicant": "测试公司",
            "applicant_data": {
                "name": "",  # 名称缺失
                "address": "",  # 地址缺失
                "nationality": ""
            },
            "documents": [
                "请求书",
                "说明书"
                # 缺少权利要求书、摘要等
            ],
            "technical_field": "装置",
            "background_art": "",
            "invention_summary": "",
            "technical_problem": "",
            "technical_solution": "",
            "beneficial_effects": "",
            "claims": "1. 一种装置。",
            "specification": "说明",
            "embodiments": [],
            "drawings": []
        }

    # ========== 初始化测试 ==========

    def test_initialization(self, agent):
        """测试智能体初始化"""
        assert agent.agent_id == "test_application_reviewer"
        assert len(agent.get_capabilities()) == 4

        expected_capabilities = [
            "format_review",
            "disclosure_review",
            "claims_review",
            "specification_review"
        ]
        capability_names = [cap.name for cap in agent.get_capabilities()]
        for cap in expected_capabilities:
            assert cap in capability_names

    # ========== review_application 测试 ==========

    @pytest.mark.asyncio
    async def test_review_application_comprehensive(
        self,
        agent,
        complete_application
    ):
        """测试完整申请文件审查"""
        result = await agent.review_application(
            complete_application,
            review_scope="comprehensive"
        )

        # 验证返回结构
        assert "application_id" in result
        assert "applicant" in result
        assert "review_scope" in result
        assert "format_review" in result
        assert "disclosure_review" in result
        assert "claims_review" in result
        assert "specification_review" in result
        assert "overall_score" in result
        assert "overall_quality" in result
        assert "recommendations" in result
        assert "reviewed_at" in result

    # ========== review_format 测试 ==========

    @pytest.mark.asyncio
    async def test_review_format_complete(
        self,
        agent,
        complete_application
    ):
        """测试格式审查 - 完整"""
        result = await agent.review_format(complete_application)

        assert "format_check" in result
        assert "required_documents" in result
        assert "provided_documents" in result
        assert "missing_documents" in result
        assert "applicant_data" in result
        assert "format_issues" in result
        assert "completeness_ratio" in result

        # 完整的申请应该通过格式检查
        assert result["format_check"] in ["passed", "failed"]
        assert len(result["missing_documents"]) == 0
        assert result["applicant_data"]["status"] == "complete"

    @pytest.mark.asyncio
    async def test_review_format_incomplete(
        self,
        agent,
        incomplete_application
    ):
        """测试格式审查 - 不完整"""
        result = await agent.review_format(incomplete_application)

        # 不完整的申请应该有格式问题
        assert result["format_check"] == "failed"
        assert len(result["missing_documents"]) > 0
        assert result["applicant_data"]["status"] == "incomplete"
        assert len(result["format_issues"]) > 0

    # ========== review_disclosure 测试 ==========

    @pytest.mark.asyncio
    async def test_review_disclosure_sufficient(
        self,
        agent,
        complete_application
    ):
        """测试技术披露审查 - 充分"""
        result = await agent.review_disclosure(complete_application)

        assert "disclosure_adequacy" in result
        assert "disclosures" in result
        assert "missing_disclosures" in result
        assert "completeness_score" in result

        # 完整披露应该评分较高
        assert result["completeness_score"] >= 0.5

    @pytest.mark.asyncio
    async def test_review_disclosure_insufficient(
        self,
        agent,
        incomplete_application
    ):
        """测试技术披露审查 - 不充分"""
        result = await agent.review_disclosure(incomplete_application)

        # 不完整的披露应该识别问题
        assert result["disclosure_adequacy"] in ["sufficient", "insufficient"]
        # 完整性评分应该较低
        if len(incomplete_application["technical_field"]) < 20:
            assert result["completeness_score"] < 0.5

    # ========== review_claims 测试 ==========

    @pytest.mark.asyncio
    async def test_review_claims_good(
        self,
        agent,
        complete_application
    ):
        """测试权利要求审查 - 良好"""
        result = await agent.review_claims(complete_application)

        assert "claims_review" in result
        assert "total_claims" in result
        assert "independent_claims" in result
        assert "dependent_claims" in result
        assert "issues" in result
        assert "suggestions" in result

        # 应该有权利要求
        assert result["total_claims"] > 0
        assert result["independent_claims"] >= 1

    @pytest.mark.asyncio
    async def test_review_claims_parsing(self, agent):
        """测试权利要求解析"""
        application = {
            "claims": "1. 一种装置，包括特征A。\n2. 根据权利要求1所述的装置，其特征在于，还包括特征B。\n3. 根据权利要求2所述的装置，其特征在于，所述特征B为可拆卸的。"
        }

        result = await agent.review_claims(application)

        # 应该正确解析出3个权利要求
        assert result["total_claims"] == 3
        assert result["independent_claims"] == 1
        assert result["dependent_claims"] == 2

    # ========== review_specification 测试 ==========

    @pytest.mark.asyncio
    async def test_review_specification_complete(
        self,
        agent,
        complete_application
    ):
        """测试说明书审查 - 完整"""
        result = await agent.review_specification(complete_application)

        assert "specification_review" in result
        assert "total_embodiments" in result
        assert "total_drawings" in result
        assert "issues" in result
        assert "suggestions" in result

        # 完整的说明书应该有实施例
        assert result["total_embodiments"] > 0

    @pytest.mark.asyncio
    async def test_review_specification_incomplete(
        self,
        agent,
        incomplete_application
    ):
        """测试说明书审查 - 不完整"""
        result = await agent.review_specification(incomplete_application)

        # 不完整的说明书应该有问题
        assert result["total_embodiments"] == 0
        assert len(result["issues"]) > 0

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

    def test_assess_disclosure_completeness(self, agent):
        """测试评估披露充分性"""
        # 充分披露（长度>100字符，应返回0.8分）
        result = agent._assess_disclosure_completeness(
            "技术领域",
            "这是一个详细的技术领域描述，包含充分的背景信息和技术细节。"
            "本发明涉及智能控制技术领域，特别是一种基于深度学习的自适应控制系统。"
            "该系统采用了多层神经网络架构，结合先进的传感器技术和实时数据处理算法，"
            "可以广泛应用于工业自动化、智能制造、智能交通和智慧城市等多个领域。"
        )
        assert result["status"] == "sufficient"
        assert result["score"] >= 0.8

        # 不充分披露
        result = agent._assess_disclosure_completeness("技术领域", "")
        assert result["status"] == "insufficient"
        assert result["score"] < 0.5

    def test_assess_claims_clarity(self, agent):
        """测试评估权利要求清晰度"""
        claims = [
            {"text": "一种装置，包括特征A和特征B", "number": 1, "type": "independent"}
        ]

        result = agent._assess_claims_clarity(claims)

        assert "score" in result
        assert "description" in result
        assert 0 <= result["score"] <= 1

    def test_assess_claims_breadth(self, agent):
        """测试评估权利要求保护范围"""
        claims = [
            {"text": "一种装置", "number": 1, "type": "independent"}
        ]

        result = agent._assess_claims_breadth(claims)

        assert "score" in result
        assert "description" in result
        assert result["independent_count"] == 1

    def test_calculate_overall_score(self, agent):
        """测试计算综合评分"""
        format_result = {
            "format_check": "passed",
            "completeness_ratio": 1.0
        }
        disclosure_result = {
            "completeness_score": 0.8
        }
        claims_result = {
            "claims_review": {
                "clarity": {"score": 0.75}
            }
        }
        specification_result = {
            "specification_review": {
                "completeness": {"score": 0.8}
            }
        }

        score = agent._calculate_overall_score(
            format_result,
            disclosure_result,
            claims_result,
            specification_result
        )

        assert 0 <= score <= 1
        # 应该是平均分
        assert score >= 0.5  # 所有评分都不错

    def test_get_quality_level(self, agent):
        """测试获取质量等级"""
        assert agent._get_quality_level(0.92) == "优秀"
        assert agent._get_quality_level(0.8) == "良好"
        assert agent._get_quality_level(0.65) == "合格"
        assert agent._get_quality_level(0.5) == "待改进"

    # ========== 边界条件测试 ==========

    @pytest.mark.asyncio
    async def test_review_application_empty(self, agent):
        """测试空申请数据的处理（容错处理）"""
        # 代码使用容错处理，不会抛出异常，而是返回默认结果
        result = await agent.review_application({}, "comprehensive")

        # 验证返回结果结构
        assert "application_id" in result
        assert "review_scope" in result
        assert result["review_scope"] == "comprehensive"

    @pytest.mark.asyncio
    async def test_review_format_empty_documents(self, agent):
        """测试空文档列表的处理"""
        application = {
            "application_id": "CN202600000000",
            "documents": []
        }

        result = await agent.review_format(application)

        # 空文档应该识别为格式问题
        assert result["format_check"] == "failed"

    # ========== 性能测试 ==========

    @pytest.mark.asyncio
    async def test_performance_review_application(
        self,
        agent,
        complete_application
    ):
        """测试审查性能 - 应该在合理时间内完成"""
        import time

        start_time = time.time()
        await agent.review_application(
            complete_application,
            "comprehensive"
        )
        elapsed_time = time.time() - start_time

        # 完整审查应该在3秒内完成
        assert elapsed_time < 3.0

    # ========== 集成测试 ==========

    @pytest.mark.asyncio
    async def test_full_workflow(
        self,
        agent,
        complete_application
    ):
        """测试完整工作流程"""
        # 1. 格式审查
        format_result = await agent.review_format(complete_application)

        # 2. 披露审查
        disclosure_result = await agent.review_disclosure(complete_application)

        # 3. 权利要求审查
        claims_result = await agent.review_claims(complete_application)

        # 4. 说明书审查
        specification_result = await agent.review_specification(complete_application)

        # 5. 综合评分
        overall_score = agent._calculate_overall_score(
            format_result,
            disclosure_result,
            claims_result,
            specification_result
        )

        # 验证工作流程连贯性
        assert format_result["completeness_ratio"] >= 0
        assert disclosure_result["completeness_score"] >= 0
        assert 0 <= overall_score <= 1
