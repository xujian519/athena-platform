"""
创造性分析代理（CreativityAnalyzerProxy）单元测试

测试内容：
1. 初始化测试
2. 能力注册测试
3. 系统提示词测试
4. 基本功能测试（使用mock）
"""

import pytest
from typing import Dict, List, Optional, Any

from unittest.mock import patch

from core.framework.agents.xiaona.creativity_analyzer_proxy import CreativityAnalyzerProxy
from core.framework.agents.xiaona.base_component import AgentExecutionContext


class TestCreativityAnalyzerInitialization:
    """创造性分析代理初始化测试"""

    def test_creativity_analyzer_initialization(self):
        """测试创造性分析代理初始化"""
        analyzer = CreativityAnalyzerProxy()
        assert analyzer.agent_id == "creativity_analyzer"
        assert analyzer.status.value == "idle"


class TestCreativityAnalyzerCapabilities:
    """创造性分析代理能力注册测试"""

    def test_creativity_analyzer_capabilities(self):
        """测试能力注册"""
        analyzer = CreativityAnalyzerProxy()
        capabilities = analyzer.get_capabilities()
        capability_names = [c.name for c in capabilities]

        assert "obviousness_assessment" in capability_names
        assert "inventive_step_evaluation" in capability_names
        assert "technical_advancement_analysis" in capability_names
        assert "creativity_evaluation" in capability_names

    def test_creativity_analyzer_capability_details(self):
        """测试能力详情"""
        analyzer = CreativityAnalyzerProxy()
        capabilities = analyzer.get_capabilities()

        # 检查obviousness_assessment能力
        obviousness = next((c for c in capabilities if c.name == "obviousness_assessment"), None)
        assert obviousness is not None
        assert "显而易见性评估" in obviousness.description
        assert "技术方案" in obviousness.input_types

    def test_creativity_analyzer_has_capability(self):
        """测试能力检查方法"""
        analyzer = CreativityAnalyzerProxy()
        assert analyzer.has_capability("obviousness_assessment")
        assert analyzer.has_capability("creativity_evaluation")
        assert not analyzer.has_capability("nonexistent_capability")


class TestCreativityAnalyzerSystemPrompt:
    """创造性分析代理系统提示词测试"""

    def test_get_system_prompt(self):
        """测试获取系统提示词"""
        analyzer = CreativityAnalyzerProxy()
        prompt = analyzer.get_system_prompt()

        assert "专利创造性分析专家" in prompt
        assert "显而易见性" in prompt
        assert "创造性步骤" in prompt
        assert "技术进步" in prompt


class TestCreativityAnalyzerExecute:
    """创造性分析代理基本功能测试"""

    @pytest.mark.asyncio
    async def test_execute_default_task(self):
        """测试默认任务执行"""
        analyzer = CreativityAnalyzerProxy()

        context = AgentExecutionContext(
            session_id="test_session",
            task_id="test_task",
            input_data={
                "patent_id": "CN123456",
                "claims": "1. 一种测试装置...",
                "prior_art": []
            },
            config={},
            metadata={}
        )

        # 使用规则降级
        with patch.object(analyzer, '_call_llm_with_fallback', side_effect=Exception("LLM失败")):
            result = await analyzer.execute(context)

        assert "obviousness_assessment" in result or "creativity_conclusion" in result

    @pytest.mark.asyncio
    async def test_analyze_creativity_with_rules(self):
        """测试基于规则的创造性分析"""
        analyzer = CreativityAnalyzerProxy()

        patent_data = {
            "patent_id": "CN123456",
            "differences": ["区别特征1", "区别特征2", "区别特征3"],
            "prior_art": []
        }

        result = await analyzer.analyze_creativity(patent_data)

        assert result["patent_id"] == "CN123456"
        assert "obviousness_assessment" in result
        assert "inventive_step_evaluation" in result

    @pytest.mark.asyncio
    async def test_assess_obviousness(self):
        """测试显而易见性评估"""
        analyzer = CreativityAnalyzerProxy()

        patent_data = {
            "differences": ["区别1", "区别2", "区别3"],
            "prior_art": [],
            "invention_content": "该方案具有预料不到的效果",
            "beneficial_effects": "效果显著提高"
        }

        result = await analyzer.assess_obviousness(patent_data)

        assert "is_obvious" in result
        assert "confidence" in result
        assert "reasoning" in result

    @pytest.mark.asyncio
    async def test_evaluate_inventive_step(self):
        """测试创造性步骤评估"""
        analyzer = CreativityAnalyzerProxy()

        patent_data = {
            "differences": ["区别1", "区别2", "区别3"]
        }

        result = await analyzer.evaluate_inventive_step(patent_data)

        assert "has_inventive_step" in result
        assert "step_magnitude" in result
        assert "confidence" in result

    @pytest.mark.asyncio
    async def test_analyze_technical_advancement(self):
        """测试技术进步分析"""
        analyzer = CreativityAnalyzerProxy()

        patent_data = {
            "beneficial_effects": "该技术方案显著提高了性能，大幅降低了成本",
            "invention_content": "技术方案描述"
        }

        result = await analyzer.analyze_technical_advancement(patent_data)

        assert "has_advancement" in result
        assert "improvement_degree" in result


class TestCreativityAnalyzerHelperMethods:
    """创造性分析代理辅助方法测试"""

    def test_extract_differences(self):
        """测试提取区别特征"""
        analyzer = CreativityAnalyzerProxy()

        patent_text = "本发明与现有技术的区别在于：采用了新的结构，提高了效率。"
        differences = analyzer._extract_differences(patent_text)

        assert isinstance(differences, list)

    def test_assess_teaching_away(self):
        """测试评估教导away"""
        analyzer = CreativityAnalyzerProxy()

        prior_art = [
            {"content": "该方案不可行"},
            {"content": "常规技术方案"}
        ]

        result = analyzer._assess_teaching_away(prior_art)

        assert "has_teaching_away" in result
        assert "evidence" in result

    def test_identify_surprising_effect(self):
        """测试识别预料不到的效果"""
        analyzer = CreativityAnalyzerProxy()

        patent_data = {
            "invention_content": "该方案产生了预料不到的效果",
            "beneficial_effects": "性能大幅提升"
        }

        result = analyzer._identify_surprising_effect(patent_data)

        assert "has_surprising_effect" in result
        assert "effect_description" in result

    def test_calculate_confidence_score(self):
        """测试计算置信度分数"""
        analyzer = CreativityAnalyzerProxy()

        obviousness = {"is_obvious": False}
        progress = {"has_significant_progress": True}
        effects = {"has_unexpected_effects": True}

        score = analyzer._calculate_confidence_score(obviousness, progress, effects)

        assert 0 <= score <= 1

    def test_get_timestamp(self):
        """测试获取时间戳"""
        analyzer = CreativityAnalyzerProxy()
        timestamp = analyzer._get_timestamp()

        assert isinstance(timestamp, str)
        assert len(timestamp) > 0


class TestCreativityAnalyzerRuleBasedMethods:
    """创造性分析代理规则方法测试"""

    @pytest.mark.asyncio
    async def test_assess_obviousness_by_rules(self):
        """测试基于规则的显而易见性评估"""
        analyzer = CreativityAnalyzerProxy()

        patent_data = {
            "differences": ["区别1", "区别2", "区别3"],
            "prior_art": [],
            "invention_content": "具有预料不到的效果",
            "beneficial_effects": "效果显著提高"
        }

        result = await analyzer._assess_obviousness_by_rules(patent_data)

        assert "is_obvious" in result
        assert "reasoning" in result

    @pytest.mark.asyncio
    async def test_evaluate_inventive_step_by_rules(self):
        """测试基于规则的创造性步骤评估"""
        analyzer = CreativityAnalyzerProxy()

        patent_data = {
            "differences": ["区别1", "区别2", "区别3"]
        }

        result = await analyzer._evaluate_inventive_step_by_rules(patent_data)

        assert "has_inventive_step" in result
        assert "step_magnitude" in result

    @pytest.mark.asyncio
    async def test_analyze_technical_advancement_by_rules(self):
        """测试基于规则的技术进步分析"""
        analyzer = CreativityAnalyzerProxy()

        patent_data = {
            "beneficial_effects": "该方案显著提高了性能",
            "invention_content": "技术方案"
        }

        result = await analyzer._analyze_technical_advancement_by_rules(patent_data)

        assert "has_advancement" in result
        assert "improvement_degree" in result


class TestCreativityAnalyzerInfo:
    """创造性分析代理信息测试"""

    def test_get_info(self):
        """测试获取代理信息"""
        analyzer = CreativityAnalyzerProxy()
        info = analyzer.get_info()

        assert info["agent_id"] == "creativity_analyzer"
        assert info["agent_type"] == "CreativityAnalyzerProxy"
        assert "capabilities" in info

    def test_repr(self):
        """测试代理字符串表示"""
        analyzer = CreativityAnalyzerProxy()
        repr_str = repr(analyzer)

        assert "CreativityAnalyzerProxy" in repr_str
