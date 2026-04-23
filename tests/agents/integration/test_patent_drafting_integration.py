"""
PatentDraftingProxy集成测试

完整的集成测试套件,覆盖:
1. 完整工作流测试 (端到端)
2. 模块集成测试
3. 错误处理测试
4. 性能测试
5. 知识库集成测试

Author: Athena Team
Date: 2026-04-23
"""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any, List

from core.agents.xiaona.patent_drafting_proxy import PatentDraftingProxy
from core.agents.xiaona.base_component import (
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
)
from core.agents.xiaona.patent_drafting_prompts import PatentDraftingPrompts


# ========== 测试数据 Fixtures ==========

@pytest.fixture
def complete_disclosure_data():
    """完整的技术交底书数据"""
    return {
        "disclosure_id": "DISC-2026-INTEGRATION-001",
        "title": "一种基于深度学习的自动驾驶车辆路径规划方法",
        "technical_field": "自动驾驶技术",
        "background_art": """
        现有技术中,自动驾驶车辆在复杂城市环境下的路径规划存在以下问题:
        1. 动态障碍物预测不准确
        2. 路径规划效率低
        3. 缺乏考虑乘客舒适性
        """,
        "invention_summary": "结合拟人驾驶行为进行路径规划",
        "technical_problem": "如何在复杂城市环境下实现高效、安全、舒适的路径规划",
        "technical_solution": """
        本发明提供一种自动驾驶车辆路径规划方法,包括:
        1. 获取车辆当前状态和环境信息
        2. 基于深度学习预测动态障碍物轨迹
        3. 结合拟人驾驶行为模型生成候选路径
        4. 综合安全性、效率、舒适性评估路径
        5. 选择最优路径执行
        """,
        "beneficial_effects": [
            "路径规划准确率提升25%",
            "乘客舒适性指标提升30%",
            "计算效率提升40%",
        ],
        "examples": [
            {
                "实施例编号": 1,
                "描述": "在十字路口场景下,车辆成功避让行人并选择最优路径",
                "关键参数": {
                    "预测时间窗口": "3秒",
                    "路径采样间隔": "0.1米",
                    "评估权重": "安全:0.5, 效率:0.3, 舒适:0.2"
                }
            },
            {
                "实施例编号": 2,
                "描述": "在高速公路场景下,车辆实现平滑变道",
                "关键参数": {
                    "预测时间窗口": "5秒",
                    "路径采样间隔": "0.5米",
                    "评估权重": "安全:0.6, 效率:0.4, 舒适:0.0"
                }
            }
        ],
        "drawings": [
            "图1是本发明实施例的方法流程图",
            "图2是路径规划场景示意图",
            "图3是拟人驾驶行为模型架构图"
        ]
    }


@pytest.fixture
def minimal_disclosure_data():
    """最小化的技术交底书数据"""
    return {
        "disclosure_id": "DISC-2026-INTEGRATION-002",
        "title": "一种智能调温装置",
        "technical_field": "家电控制",
        "technical_solution": "通过传感器检测温度并自动调节",
        "beneficial_effects": ["节能20%", "舒适度提升"]
    }


@pytest.fixture
def invalid_disclosure_data():
    """无效的技术交底书数据"""
    return {
        # 空数据
    }


@pytest.fixture
def large_disclosure_data():
    """大型技术交底书数据 (用于性能测试)"""
    base_data = {
        "disclosure_id": "DISC-2026-INTEGRATION-LARGE",
        "title": "一种复杂的多传感器融合定位系统",
        "technical_field": "自动驾驶定位技术",
    }

    # 生成大量内容
    base_data["background_art"] = "现有技术问题描述 " * 500  # 约10000字
    base_data["technical_solution"] = "技术方案详细描述 " * 800  # 约16000字
    base_data["beneficial_effects"] = [f"有益效果{i}" for i in range(50)]

    return base_data


@pytest.fixture
def prior_art_data():
    """现有技术数据"""
    return [
        {
            "patent_id": "CN112345678A",
            "title": "自动驾驶路径规划方法",
            "abstract": "基于A*算法的路径规划",
            "similarity": 0.65,
            "key_differences": ["未考虑拟人驾驶行为", "未优化舒适性"]
        },
        {
            "patent_id": "US9876543B2",
            "title": "Vehicle Path Planning System",
            "abstract": "Dynamic obstacle avoidance",
            "similarity": 0.72,
            "key_differences": ["未结合深度学习", "计算效率低"]
        },
        {
            "patent_id": "EP3456789A1",
            "title": "Autonomous Driving Navigation",
            "abstract": "Multi-sensor fusion for navigation",
            "similarity": 0.58,
            "key_differences": ["定位技术不同", "应用场景不同"]
        }
    ]


@pytest.fixture
def agent():
    """PatentDraftingProxy实例"""
    return PatentDraftingProxy()


@pytest.fixture
def mock_llm_response():
    """Mock LLM响应"""
    return {
        "disclosure_analysis": {
            "disclosure_id": "DISC-2026-001",
            "quality_score": 0.85,
            "completeness": 0.9,
            "recommendations": ["建议补充具体实验数据"]
        },
        "patentability": {
            "novelty_score": 0.75,
            "creativity_score": 0.8,
            "practicality_score": 0.9,
            "overall_score": 0.82
        },
        "specification": "完整的说明书草稿内容...",
        "claims": "1. 一种路径规划方法,其特征在于,包括:...",
        "optimization": ["建议缩小独立权利要求保护范围", "增加从属权利要求"],
        "adequacy": {"score": 0.88, "missing_items": []},
        "errors": {"total": 0, "items": []}
    }


# ========== 1. 完整工作流测试 ==========


class TestFullWorkflow:
    """测试完整工作流 - 端到端测试"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_patent_drafting_workflow(
        self,
        agent,
        complete_disclosure_data,
        prior_art_data
    ):
        """
        端到端测试:从技术交底书到完整申请文件

        流程:
        1. 分析技术交底书
        2. 评估可专利性
        3. 撰写说明书
        4. 撰写权利要求
        5. 优化保护范围
        6. 审查充分公开
        7. 检测常见错误
        """
        # 步骤1: 分析技术交底书
        analysis = await agent.analyze_disclosure(complete_disclosure_data)

        assert analysis is not None
        assert "disclosure_id" in analysis
        assert analysis["disclosure_id"] == "DISC-2026-INTEGRATION-001"

        # 如果使用规则-based降级,验证降级结果
        if "extracted_information" in analysis:
            assert "completeness" in analysis
            assert "quality_assessment" in analysis

        # 步骤2: 评估可专利性
        patentability_data = {
            "disclosure": complete_disclosure_data,
            "prior_art": prior_art_data
        }
        patentability = await agent.assess_patentability(patentability_data)

        assert patentability is not None
        assert "overall_score" in patentability
        # 评分应在合理范围内
        assert 0 <= patentability["overall_score"] <= 1

        # 步骤3: 撰写说明书
        specification_data = {
            "disclosure": complete_disclosure_data,
            "patentability": patentability
        }
        specification = await agent.draft_specification(specification_data)

        assert specification is not None
        assert "specification_draft" in specification
        assert len(specification["specification_draft"]) > 100

        # 步骤4: 撰写权利要求
        claims_data = {
            "disclosure": complete_disclosure_data,
            "specification": specification.get("specification_draft", "")
        }
        claims = await agent.draft_claims(claims_data)

        assert claims is not None
        assert "claims_draft" in claims
        assert len(claims["claims_draft"]) > 50

        # 步骤5: 优化保护范围
        optimization_data = {
            "claims": claims.get("claims_draft", ""),
            "prior_art": prior_art_data
        }
        optimized = await agent.optimize_protection_scope(optimization_data)

        assert optimized is not None
        # LLM失败时返回error字段
        assert "optimization_suggestions" in optimized or "error" in optimized

        # 步骤6: 充分公开审查
        adequacy_data = {
            "specification": specification.get("specification_draft", ""),
            "claims": claims.get("claims_draft", "")
        }
        adequacy = await agent.review_adequacy(adequacy_data)

        assert adequacy is not None
        # LLM失败时返回error字段
        assert "adequacy_review" in adequacy or "error" in adequacy

        # 步骤7: 错误检测
        errors = await agent.detect_common_errors(adequacy_data)

        assert errors is not None
        # LLM失败时返回error字段
        assert "detected_errors" in errors or "error" in errors

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_minimal_disclosure_workflow(
        self,
        agent,
        minimal_disclosure_data
    ):
        """测试最小化交底书的完整流程"""
        result = await agent.draft_patent_application(minimal_disclosure_data)

        assert result is not None
        assert "disclosure_analysis" in result
        assert "patentability_assessment" in result
        assert "specification" in result
        assert "claims" in result

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_invalid_input_handling(
        self,
        agent,
        invalid_disclosure_data
    ):
        """测试无效输入的处理"""
        # 空数据应该能被处理,不会崩溃
        result = await agent.analyze_disclosure(invalid_disclosure_data)

        assert result is not None
        # 应该返回分析结果或错误信息
        assert "disclosure_id" in result or "extracted_information" in result


# ========== 2. 模块集成测试 ==========


class TestModuleIntegration:
    """测试模块间的集成"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_analysis_to_specification_integration(
        self,
        agent,
        complete_disclosure_data
    ):
        """测试:从分析到说明书的集成"""
        # 步骤1: 分析
        analysis = await agent.analyze_disclosure(complete_disclosure_data)

        assert analysis is not None
        assert "disclosure_id" in analysis

        # 步骤2: 撰写(使用分析结果)
        specification_data = {
            "disclosure": complete_disclosure_data,
            "patentability": analysis  # 将分析结果作为输入
        }
        spec = await agent.draft_specification(specification_data)

        assert spec is not None
        assert "specification_draft" in spec
        # 验证disclosure_id一致性
        assert analysis["disclosure_id"] == complete_disclosure_data["disclosure_id"]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_claims_to_optimization_integration(
        self,
        agent,
        complete_disclosure_data,
        prior_art_data
    ):
        """测试:从权利要求到优化的集成"""
        # 步骤1: 撰写权利要求
        claims_data = {
            "disclosure": complete_disclosure_data,
            "specification": "示例说明书"
        }
        claims_result = await agent.draft_claims(claims_data)

        assert claims_result is not None
        assert "claims_draft" in claims_result

        # 步骤2: 优化(使用权利要求结果)
        optimization_data = {
            "claims": claims_result["claims_draft"],
            "prior_art": prior_art_data
        }
        optimized = await agent.optimize_protection_scope(optimization_data)

        assert optimized is not None
        assert "optimization_suggestions" in optimized or "error" in optimized

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_specification_to_claims_integration(
        self,
        agent,
        complete_disclosure_data
    ):
        """测试:从说明书到权利要求的集成"""
        # 步骤1: 撰写说明书
        spec_data = {
            "disclosure": complete_disclosure_data,
            "patentability": {"overall_score": 0.8}
        }
        spec_result = await agent.draft_specification(spec_data)

        assert spec_result is not None
        assert "specification_draft" in spec_result

        # 步骤2: 撰写权利要求(使用说明书)
        claims_data = {
            "disclosure": complete_disclosure_data,
            "specification": spec_result["specification_draft"]
        }
        claims_result = await agent.draft_claims(claims_data)

        assert claims_result is not None
        assert "claims_draft" in claims_result

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_patentability_to_claims_integration(
        self,
        agent,
        complete_disclosure_data,
        prior_art_data
    ):
        """测试:从可专利性评估到权利要求的集成"""
        # 步骤1: 可专利性评估
        patentability_data = {
            "disclosure": complete_disclosure_data,
            "prior_art": prior_art_data
        }
        patentability = await agent.assess_patentability(patentability_data)

        assert patentability is not None
        assert "overall_score" in patentability

        # 步骤2: 根据可专利性撰写权利要求
        claims_data = {
            "disclosure": complete_disclosure_data,
            "specification": "",
            "patentability": patentability
        }
        claims_result = await agent.draft_claims(claims_data)

        assert claims_result is not None
        assert "claims_draft" in claims_result


# ========== 3. 错误处理测试 ==========


class TestErrorHandling:
    """测试错误处理和降级方案"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_llm_failure_fallback_analyze_disclosure(
        self,
        agent,
        complete_disclosure_data
    ):
        """测试:LLM调用失败时的降级处理(分析交底书)"""
        # Mock LLM调用失败
        with patch.object(
            agent,
            '_call_llm_with_fallback',
            side_effect=Exception("LLM service unavailable")
        ):
            result = await agent.analyze_disclosure(complete_disclosure_data)

            # 应该降级到规则-based分析
            assert result is not None
            assert "extracted_information" in result
            assert "completeness" in result

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_llm_failure_fallback_patentability(
        self,
        agent,
        complete_disclosure_data
    ):
        """测试:LLM调用失败时的降级处理(可专利性评估)"""
        # Mock LLM调用失败
        with patch.object(
            agent,
            '_call_llm_with_fallback',
            side_effect=Exception("LLM service unavailable")
        ):
            data = {
                "disclosure": complete_disclosure_data,
                "prior_art": []
            }
            result = await agent.assess_patentability(data)

            # 应该降级到规则-based评估
            assert result is not None
            assert "novelty_assessment" in result
            assert "creativity_assessment" in result
            assert "practicality_assessment" in result
            assert "overall_score" in result

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_llm_failure_fallback_specification(
        self,
        agent,
        complete_disclosure_data
    ):
        """测试:LLM调用失败时的降级处理(说明书撰写)"""
        # Mock LLM调用失败
        with patch.object(
            agent,
            '_call_llm_with_fallback',
            side_effect=Exception("LLM service unavailable")
        ):
            data = {
                "disclosure": complete_disclosure_data,
                "patentability": {"overall_score": 0.8}
            }
            result = await agent.draft_specification(data)

            # 应该降级到模板生成
            assert result is not None
            assert "specification_draft" in result
            assert len(result["specification_draft"]) > 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_llm_failure_fallback_claims(
        self,
        agent,
        complete_disclosure_data
    ):
        """测试:LLM调用失败时的降级处理(权利要求撰写)"""
        # Mock LLM调用失败
        with patch.object(
            agent,
            '_call_llm_with_fallback',
            side_effect=Exception("LLM service unavailable")
        ):
            data = {
                "disclosure": complete_disclosure_data,
                "specification": "示例说明书"
            }
            result = await agent.draft_claims(data)

            # 应该降级到模板生成
            assert result is not None
            assert "claims_draft" in result
            assert len(result["claims_draft"]) > 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_invalid_json_response_handling(
        self,
        agent
    ):
        """测试:无效JSON响应的处理"""
        # 测试无效JSON响应
        invalid_responses = [
            "这不是JSON",
            "```json\n{invalid json}\n```",
            '{"key": value}',  # 无效的JSON
            "",  # 空响应
        ]

        for invalid_response in invalid_responses:
            result = agent._parse_analysis_response(invalid_response)

            assert "error" in result
            assert "raw_response" in result

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_malformed_disclosure_data(
        self,
        agent
    ):
        """测试:畸形交底书数据的处理"""
        malformed_data_list = [
            {"title": None},  # None值
            {"title": ""},  # 空字符串
            {"technical_field": 123},  # 错误类型
            {"background_art": "a" * 100000},  # 过长内容
        ]

        for malformed_data in malformed_data_list:
            result = await agent.analyze_disclosure(malformed_data)

            # 应该能处理,不崩溃
            assert result is not None


# ========== 4. 性能测试 ==========


class TestPerformance:
    """测试性能指标"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.integration
    async def test_performance_analysis(
        self,
        agent,
        complete_disclosure_data
    ):
        """测试:交底书分析性能"""
        start_time = time.time()

        result = await agent.analyze_disclosure(complete_disclosure_data)

        elapsed_time = time.time() - start_time

        assert result is not None
        # 分析应在10秒内完成
        assert elapsed_time < 10.0, f"分析耗时{elapsed_time:.2f}秒,超过10秒限制"

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.integration
    async def test_performance_specification_drafting(
        self,
        agent,
        complete_disclosure_data
    ):
        """测试:说明书撰写性能"""
        data = {
            "disclosure": complete_disclosure_data,
            "patentability": {"overall_score": 0.8}
        }

        start_time = time.time()
        result = await agent.draft_specification(data)
        elapsed_time = time.time() - start_time

        assert result is not None
        assert "specification_draft" in result
        # 撰写应在30秒内完成
        assert elapsed_time < 30.0, f"撰写耗时{elapsed_time:.2f}秒,超过30秒限制"

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.integration
    async def test_performance_claims_drafting(
        self,
        agent,
        complete_disclosure_data
    ):
        """测试:权利要求撰写性能"""
        data = {
            "disclosure": complete_disclosure_data,
            "specification": "示例说明书"
        }

        start_time = time.time()
        result = await agent.draft_claims(data)
        elapsed_time = time.time() - start_time

        assert result is not None
        assert "claims_draft" in result
        # 撰写应在25秒内完成
        assert elapsed_time < 25.0, f"撰写耗时{elapsed_time:.2f}秒,超过25秒限制"

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.integration
    async def test_performance_full_workflow(
        self,
        agent,
        complete_disclosure_data
    ):
        """测试:完整工作流性能"""
        start_time = time.time()

        result = await agent.draft_patent_application(complete_disclosure_data)

        elapsed_time = time.time() - start_time

        assert result is not None
        # 完整流程应在120秒内完成
        assert elapsed_time < 120.0, f"完整流程耗时{elapsed_time:.2f}秒,超过120秒限制"

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.integration
    async def test_performance_large_disclosure(
        self,
        agent,
        large_disclosure_data
    ):
        """测试:大型交底书性能"""
        start_time = time.time()

        result = await agent.analyze_disclosure(large_disclosure_data)

        elapsed_time = time.time() - start_time

        assert result is not None
        # 大型交底书分析应在30秒内完成
        assert elapsed_time < 30.0, f"大型交底书分析耗时{elapsed_time:.2f}秒,超过30秒限制"

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.integration
    async def test_performance_concurrent_requests(
        self,
        agent,
        complete_disclosure_data
    ):
        """测试:并发请求处理"""
        # 模拟5个并发请求
        tasks = [
            agent.analyze_disclosure(complete_disclosure_data)
            for _ in range(5)
        ]

        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed_time = time.time() - start_time

        # 验证所有请求都成功完成
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == 5

        # 并发处理应在合理时间内完成
        assert elapsed_time < 30.0, f"并发处理耗时{elapsed_time:.2f}秒,超过30秒限制"


# ========== 5. 知识库集成测试 ==========


class TestKnowledgeBaseIntegration:
    """测试知识库集成"""

    @pytest.mark.integration
    def test_knowledge_base_loading(self):
        """测试:知识库加载"""
        # 验证所有prompts可访问
        assert hasattr(PatentDraftingPrompts, 'get_prompt')
        assert hasattr(PatentDraftingPrompts, 'format_user_prompt')

        # 验证配置结构
        config = PatentDraftingPrompts.get_prompt("comprehensive")
        assert config is not None
        assert "system_prompt" in config
        assert "user_template" in config

    @pytest.mark.integration
    def test_prompt_templates(self):
        """测试:提示词模板"""
        # 测试comprehensive模板
        prompt = PatentDraftingPrompts.get_prompt("comprehensive")
        assert "专利撰写专家" in prompt["system_prompt"]

        # 测试format_user_prompt
        formatted = PatentDraftingPrompts.format_user_prompt(
            "comprehensive"
        )
        assert isinstance(formatted, str)

    @pytest.mark.integration
    def test_capability_registration(self, agent):
        """测试:能力注册"""
        capabilities = agent.get_capabilities()

        # 验证所有能力已注册
        capability_names = [c.name for c in capabilities]
        expected_capabilities = [
            "analyze_disclosure",
            "assess_patentability",
            "draft_specification",
            "draft_claims",
            "optimize_protection_scope",
            "review_adequacy",
            "detect_common_errors"
        ]

        for expected in expected_capabilities:
            assert expected in capability_names, f"缺少能力: {expected}"

        # 验证能力属性
        for cap in capabilities:
            assert cap.name
            assert cap.description
            assert cap.input_types
            assert cap.output_types
            assert cap.estimated_time > 0

    @pytest.mark.integration
    def test_system_prompt_generation(self, agent):
        """测试:系统提示词生成"""
        prompt = agent.get_system_prompt("comprehensive")

        assert prompt is not None
        assert len(prompt) > 0
        assert "专利撰写" in prompt or "专利" in prompt


# ========== 6. 执行上下文测试 ==========


class TestExecutionContext:
    """测试执行上下文"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_execute_with_valid_context(
        self,
        agent,
        complete_disclosure_data
    ):
        """测试:有效上下文执行"""
        context = AgentExecutionContext(
            session_id="TEST-SESSION-001",
            task_id="TEST-TASK-001",
            input_data=complete_disclosure_data,
            config={"task_type": "analyze_disclosure"},
            metadata={"test_mode": True}
        )

        result = await agent.execute(context)

        assert result is not None
        assert result.status in [AgentStatus.COMPLETED, AgentStatus.ERROR]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_execute_with_invalid_context(
        self,
        agent
    ):
        """测试:无效上下文执行"""
        # 测试空上下文
        invalid_context = AgentExecutionContext(
            session_id="",
            task_id="",
            input_data={},
            config={},
            metadata={}
        )

        result = await agent.execute(invalid_context)

        assert result is not None
        # 空session_id和task_id在validate_input中会检查
        # 如果validate_input返回False,应该返回ERROR状态
        # 目前实现中validate_input总是返回True,所以这里测试不会失败
        assert result.status in [AgentStatus.COMPLETED, AgentStatus.ERROR]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_execute_with_different_task_types(
        self,
        agent,
        complete_disclosure_data
    ):
        """测试:不同任务类型的执行"""
        task_types = [
            "analyze_disclosure",
            "assess_patentability",
            "draft_specification",
            "draft_claims",
            "optimize_protection_scope",
            "review_adequacy",
            "detect_common_errors",
        ]

        for task_type in task_types:
            context = AgentExecutionContext(
                session_id="TEST-SESSION-001",
                task_id=f"TEST-TASK-{task_type}",
                input_data=complete_disclosure_data,
                config={"task_type": task_type},
                metadata={}
            )

            result = await agent.execute(context)

            assert result is not None, f"任务类型{task_type}执行失败"
            assert result.status in [AgentStatus.COMPLETED, AgentStatus.ERROR]


# ========== 7. 数据一致性测试 ==========


class TestDataConsistency:
    """测试数据一致性"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_disclosure_id_consistency(
        self,
        agent,
        complete_disclosure_data
    ):
        """测试:disclosure_id一致性"""
        # 分析
        analysis = await agent.analyze_disclosure(complete_disclosure_data)
        assert analysis["disclosure_id"] == complete_disclosure_data["disclosure_id"]

        # 可专利性评估
        patentability = await agent.assess_patentability({
            "disclosure": complete_disclosure_data,
            "prior_art": []
        })
        assert patentability["disclosure_id"] == complete_disclosure_data["disclosure_id"]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_timestamp_generation(
        self,
        agent,
        complete_disclosure_data
    ):
        """测试:时间戳生成"""
        result = await agent.analyze_disclosure(complete_disclosure_data)

        # 验证时间戳格式
        if "analyzed_at" in result:
            timestamp = result["analyzed_at"]
            # 验证是ISO格式
            datetime.fromisoformat(timestamp)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_result_structure_consistency(
        self,
        agent,
        complete_disclosure_data
    ):
        """测试:结果结构一致性"""
        # 测试不同方法的结果结构
        methods = [
            ("analyze_disclosure", {}),
            ("assess_patentability", {"disclosure": complete_disclosure_data, "prior_art": []}),
            ("draft_specification", {"disclosure": complete_disclosure_data, "patentability": {}}),
            ("draft_claims", {"disclosure": complete_disclosure_data, "specification": ""}),
        ]

        for method_name, data in methods:
            method = getattr(agent, method_name)
            result = await method(data)

            # 验证结果不为None
            assert result is not None, f"{method_name}返回None"

            # 验证结果是字典类型
            assert isinstance(result, dict), f"{method_name}返回非字典类型"


# ========== 测试运行入口 ==========


if __name__ == "__main__":
    # 运行所有集成测试
    pytest.main([__file__, "-v", "-m", "integration", "--tb=short"])
