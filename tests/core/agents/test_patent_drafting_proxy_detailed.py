"""
PatentDraftingProxy详细功能测试

测试Task #3-5的详细功能实现：
- Task #3: TechnicalDisclosureAnalyzer详细逻辑
- Task #4: SpecificationGenerator详细逻辑
- Task #5: ClaimGenerator详细逻辑
"""

import pytest
from core.agents.xiaona.patent_drafting_proxy import PatentDraftingProxy


class TestPatentDraftingProxyDetailed:
    """PatentDraftingProxy详细功能测试"""

    @pytest.fixture
    def agent(self):
        """创建代理实例"""
        return PatentDraftingProxy()

    @pytest.fixture
    def sample_disclosure(self):
        """示例技术交底书"""
        return {
            "disclosure_id": "TEST_001",
            "title": "一种智能包装机物料限位板自动调节装置",
            "technical_field": "包装机械技术领域",
            "background_art": "现有包装机在使用过程中，不同规格的物料需要手动调节限位板，效率低下，精度差。",
            "technical_problem": "解决手动调节效率低、精度差的问题",
            "technical_solution": "包括机架、限位板、驱动电机、传感器和控制器，传感器检测物料宽度，控制器根据检测结果控制驱动电机调节限位板位置",
            "beneficial_effects": [
                "提高调节效率，减少人工干预",
                "提高调节精度，误差小于0.5mm",
                "实现自动化控制，降低劳动强度"
            ],
            "examples": [
                {
                    "实施例编号": 1,
                    "描述": "采用步进电机作为驱动电机，光电传感器作为检测传感器",
                }
            ]
        }

    # ========== Task #3: TechnicalDisclosureAnalyzer测试 ==========

    def test_analyze_disclosure_by_rules(self, agent, sample_disclosure):
        """测试基于规则的交底书分析"""
        result = agent._analyze_disclosure_by_rules(sample_disclosure)

        # 验证基本结构
        assert "disclosure_id" in result
        assert "extracted_information" in result
        assert "completeness" in result
        assert "quality_assessment" in result
        assert "recommendations" in result

        # 验证提取的信息
        extracted = result["extracted_information"]
        assert "发明名称" in extracted
        assert "技术领域" in extracted
        assert "背景技术" in extracted
        assert "技术问题" in extracted
        assert "技术方案" in extracted
        assert "有益效果" in extracted
        assert "实施例" in extracted

        # 验证发明名称提取
        assert "智能包装机" in extracted["发明名称"]

    def test_extract_invention_name(self, agent, sample_disclosure):
        """测试发明名称提取"""
        name = agent._extract_invention_name("", sample_disclosure)
        assert "智能包装机" in name
        assert "自动调节" in name

    def test_identify_technical_field(self, agent, sample_disclosure):
        """测试技术领域识别"""
        field_info = agent._identify_technical_field("", sample_disclosure)
        assert "技术领域" in field_info
        assert "包装机械" in field_info["技术领域"]
        assert "IPC分类" in field_info

    def test_extract_technical_solution(self, agent, sample_disclosure):
        """测试技术方案提取"""
        solution = agent._extract_technical_solution("", sample_disclosure)
        assert "技术方案概述" in solution
        assert "核心特征" in solution
        assert len(solution["核心特征"]) > 0

    def test_check_completeness(self, agent, sample_disclosure):
        """测试完整性检查"""
        extracted_info = {
            "发明名称": "测试发明",
            "技术领域": {"技术领域": "测试领域"},
            "背景技术": {"现有技术描述": "测试背景"},
            "技术问题": "测试问题",
            "技术方案": {"技术方案概述": "测试方案"},
            "有益效果": ["效果1", "效果2"],
            "实施例": [{"实施例编号": 1}]
        }

        completeness = agent._check_completeness(extracted_info)

        assert all(v["完整"] for v in completeness.values())

    def test_assess_quality(self, agent, sample_disclosure):
        """测试质量评估"""
        extracted_info = {
            "发明名称": "测试发明",
            "技术领域": {"技术领域": "测试领域"},
            "技术问题": "测试问题",
            "技术方案": {"技术方案概述": "测试方案", "核心特征": ["特征1", "特征2"]},
            "有益效果": ["效果1", "效果2"],
        }

        completeness = {
            k: {"完整": True}
            for k in extracted_info.keys()
        }

        quality = agent._assess_quality(extracted_info, completeness)

        assert "完整性评分" in quality
        assert "详细程度评分" in quality
        assert "清晰度评分" in quality
        assert "综合评分" in quality
        assert "质量等级" in quality

    # ========== Task #4: SpecificationGenerator测试 ==========

    def test_draft_specification_by_template(self, agent, sample_disclosure):
        """测试基于模板的说明书撰写"""
        result = agent._draft_specification_by_template({"disclosure": sample_disclosure})

        assert "specification_draft" in result
        assert "specification_parts" in result

        # 验证各部分
        parts = result["specification_parts"]
        assert "发明名称" in parts
        assert "技术领域" in parts
        assert "背景技术" in parts
        assert "发明内容" in parts
        assert "附图说明" in parts
        assert "具体实施方式" in parts

    def test_generate_title(self, agent, sample_disclosure):
        """测试发明名称生成"""
        title = agent._generate_title(sample_disclosure)
        assert "智能包装机" in title
        assert "自动调节" in title
        assert "新型" not in title  # 应该过滤掉"新型"

    def test_draft_technical_field(self, agent, sample_disclosure):
        """测试技术领域撰写"""
        field = agent._draft_technical_field(sample_disclosure)
        assert "本发明涉及" in field
        assert "包装机械" in field

    def test_draft_invention_content(self, agent, sample_disclosure):
        """测试发明内容撰写"""
        content = agent._draft_invention_content(sample_disclosure)
        assert "为了解决" in content
        assert "技术问题" in content or "技术方案" in content
        assert "有益效果" in content or "与现有技术相比" in content

    def test_assemble_specification(self, agent):
        """测试说明书组装"""
        parts = {
            "发明名称": "测试发明",
            "技术领域": "本发明涉及测试领域。",
            "背景技术": "现有技术存在问题。",
            "发明内容": "本发明提供解决方案。",
            "附图说明": "图1是示意图。",
            "具体实施方式": "具体实施如下。",
        }

        spec = agent._assemble_specification(parts)

        assert "【发明名称】" in spec
        assert "【技术领域】" in spec
        assert "【背景技术】" in spec
        assert "【发明内容】" in spec

    # ========== Task #5: ClaimGenerator测试 ==========

    def test_draft_claims_by_template(self, agent, sample_disclosure):
        """测试基于模板的权利要求书撰写"""
        result = agent._draft_claims_by_template({"disclosure": sample_disclosure})

        assert "claims_draft" in result
        assert "独立权利要求" in result
        assert "从属权利要求数量" in result
        assert "必要技术特征" in result
        assert "优选技术特征" in result

    def test_extract_essential_features(self, agent, sample_disclosure):
        """测试必要技术特征提取"""
        features = agent._extract_essential_features(sample_disclosure)
        assert isinstance(features, list)
        # 应该提取到包含"包括"、"设置"等关键词的特征

    def test_generate_independent_claim(self, agent, sample_disclosure):
        """测试独立权利要求生成"""
        essential_features = [
            "包括机架",
            "设置限位板",
            "配置驱动电机",
        ]

        claim = agent._generate_independent_claim(sample_disclosure, essential_features)

        assert "一种" in claim
        assert "其特征在于" in claim
        assert "包括" in claim

    def test_determine_claim_type(self, agent, sample_disclosure):
        """测试权利要求类型判断"""
        claim_type = agent._determine_claim_type(sample_disclosure)
        assert claim_type in ["method", "device"]

        # 测试方法类
        method_disclosure = {
            "technical_solution": "包括以下步骤：步骤1、步骤2、步骤3"
        }
        assert agent._determine_claim_type(method_disclosure) == "method"

    def test_format_independent_device_claim(self, agent):
        """测试装置独立权利要求格式化"""
        title = "测试装置"
        features = ["特征1", "特征2", "特征3"]

        claim = agent._format_independent_device_claim(title, features)

        assert "一种测试装置" in claim
        assert "其特征在于" in claim
        assert "特征1" in claim
        assert "特征2" in claim
        assert "特征3" in claim

    def test_format_independent_method_claim(self, agent):
        """测试方法独立权利要求格式化"""
        title = "测试方法"
        features = ["步骤1", "步骤2", "步骤3"]

        claim = agent._format_independent_method_claim(title, features)

        assert "一种测试方法" in claim
        assert "包括" in claim
        assert "步骤1" in claim

    def test_generate_dependent_claims(self, agent):
        """测试从属权利要求生成"""
        preferred_features = ["优选特征1", "优选特征2"]

        claims = agent._generate_dependent_claims(preferred_features, start_number=2)

        assert len(claims) == 2
        assert "根据权利要求1" in claims[0]
        assert "根据权利要求2" in claims[1]

    def test_number_claims(self, agent):
        """测试权利要求编号"""
        claims = [
            "权利要求1",
            "权利要求2",
            "权利要求3",
        ]

        numbered = agent._number_claims(claims)

        assert numbered[0].startswith("1.")
        assert numbered[1].startswith("2.")
        assert numbered[2].startswith("3.")


class TestPatentDraftingProxyIntegration:
    """集成测试"""

    @pytest.fixture
    def agent(self):
        """创建代理实例"""
        return PatentDraftingProxy()

    @pytest.fixture
    def complete_disclosure(self):
        """完整技术交底书"""
        return {
            "disclosure_id": "INTEGRATION_001",
            "title": "一种基于深度学习的图像识别方法",
            "technical_field": "人工智能和图像处理技术领域",
            "background_art": "现有图像识别方法在复杂场景下准确率低，计算量大。",
            "technical_problem": "提高图像识别准确率，降低计算复杂度",
            "technical_solution": "构建卷积神经网络，包括特征提取层、注意力机制和分类器，使用迁移学习优化模型参数",
            "beneficial_effects": [
                "识别准确率提升15%",
                "计算速度提高2倍",
                "适应复杂场景能力强"
            ],
            "examples": [
                {
                    "实施例编号": 1,
                    "描述": "使用ResNet50作为基础网络，添加SE注意力模块",
                },
                {
                    "实施例编号": 2,
                    "描述": "在ImageNet数据集上进行预训练，然后在目标数据集微调",
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_full_disclosure_analysis_workflow(
        self,
        agent,
        complete_disclosure
    ):
        """测试完整交底书分析工作流"""
        result = await agent.analyze_disclosure(complete_disclosure)

        assert "disclosure_id" in result
        assert "completeness" in result or "extracted_information" in result

    @pytest.mark.asyncio
    async def test_full_specification_draft_workflow(
        self,
        agent,
        complete_disclosure
    ):
        """测试完整说明书撰写工作流"""
        result = await agent.draft_specification({"disclosure": complete_disclosure})

        assert "specification_draft" in result
        assert len(result["specification_draft"]) > 0

    @pytest.mark.asyncio
    async def test_full_claims_draft_workflow(
        self,
        agent,
        complete_disclosure
    ):
        """测试完整权利要求书撰写工作流"""
        result = await agent.draft_claims({"disclosure": complete_disclosure})

        assert "claims_draft" in result
        assert len(result["claims_draft"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
