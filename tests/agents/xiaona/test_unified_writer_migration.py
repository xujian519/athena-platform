"""
统一撰写代理迁移测试套件

测试WriterAgent和PatentDraftingProxy的所有功能，
确保合并为UnifiedPatentWriter后功能保持一致。

运行: pytest tests/agents/xiaona/test_unified_writer_migration.py -v
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from core.agents.xiaona.writer_agent import WriterAgent
from core.agents.xiaona.patent_drafting_proxy import PatentDraftingProxy


# ============================================================================
# WriterAgent 测试用例 (4个)
# ============================================================================

class TestWriterAgent:
    """WriterAgent功能测试"""

    @pytest.fixture
    def writer_agent(self):
        """创建WriterAgent实例"""
        return WriterAgent()

    @pytest.mark.asyncio
    async def test_writer_agent_claims_drafting(self, writer_agent):
        """测试权利要求书撰写"""
        # 准备测试数据
        context = Mock()
        context.config = {"writing_type": "claims"}
        context.input_data = {
            "user_input": "一种基于深度学习的图像识别方法",
            "previous_results": {
                "features": ["卷积神经网络", "特征提取", "分类器"]
            }
        }
        context.task_id = "test_task_001"

        # Mock LLM调用
        with patch.object(writer_agent, '_draft_claims') as mock_draft:
            mock_draft.return_value = {
                "document_type": "claims",
                "content": {
                    "independent_claim": "1. 一种基于深度学习的图像识别方法...",
                    "dependent_claims": ["2. 根据权利要求1所述的方法..."]
                }
            }

            # 执行
            result = await writer_agent.execute(context)

            # 验证
            assert result.status.value == "completed"
            assert result.output_data is not None
            assert "claims" in str(result.output_data).lower()

    @pytest.mark.asyncio
    async def test_writer_agent_description_drafting(self, writer_agent):
        """测试说明书撰写"""
        context = Mock()
        context.config = {"writing_type": "description"}
        context.input_data = {
            "user_input": "一种基于深度学习的图像识别方法",
            "previous_results": {
                "features": ["深度学习模型", "图像处理"],
                "claims": ["权利要求1", "权利要求2"]
            }
        }
        context.task_id = "test_task_002"

        # Mock LLM调用
        with patch.object(writer_agent, '_draft_description') as mock_draft:
            mock_draft.return_value = {
                "document_type": "description",
                "content": {
                    "title": "基于深度学习的图像识别方法",
                    "technical_field": "本发明涉及图像处理技术领域..."
                }
            }

            # 执行
            result = await writer_agent.execute(context)

            # 验证
            assert result.status.value == "completed"
            assert result.output_data is not None

    @pytest.mark.asyncio
    async def test_writer_agent_office_action_response(self, writer_agent):
        """测试审查意见答复"""
        context = Mock()
        context.config = {"writing_type": "office_action_response"}
        context.input_data = {
            "user_input": "审查意见：权利要求1不具备新颖性",
            "previous_results": {
                "analysis": "D1公开了类似技术方案"
            }
        }
        context.task_id = "test_task_003"

        # Mock LLM调用
        with patch.object(writer_agent, '_draft_response') as mock_draft:
            mock_draft.return_value = {
                "document_type": "office_action_response",
                "content": {
                    "introduction": "针对审查意见，申请人陈述如下...",
                    "responses": [
                        {
                            "issue": "权利要求1不具备新颖性",
                            "response": "申请人不同意该审查意见..."
                        }
                    ]
                }
            }

            # 执行
            result = await writer_agent.execute(context)

            # 验证
            assert result.status.value == "completed"
            assert result.output_data is not None

    @pytest.mark.asyncio
    async def test_writer_agent_invalidation_petition(self, writer_agent):
        """测试无效宣告请求书"""
        context = Mock()
        context.config = {"writing_type": "invalidation"}
        context.input_data = {
            "user_input": "CN123456A",
            "previous_results": {
                "xiaona_retriever": {
                    "patents": ["D1", "D2", "D3"]
                },
                "xiaona_analyzer": {
                    "analysis": "D1+D2组合可破坏创造性"
                }
            }
        }
        context.task_id = "test_task_004"

        # Mock LLM调用
        with patch.object(writer_agent, '_draft_invalidation') as mock_draft:
            mock_draft.return_value = {
                "document_type": "invalidation_petition",
                "content": {
                    "petition_title": "无效宣告请求书",
                    "target_patent": "CN123456A",
                    "ground_for_invalidity": "权利要求1不具备创造性"
                }
            }

            # 执行
            result = await writer_agent.execute(context)

            # 验证
            assert result.status.value == "completed"
            assert result.output_data is not None


# ============================================================================
# PatentDraftingProxy 测试用例 (7个)
# ============================================================================

class TestPatentDraftingProxy:
    """PatentDraftingProxy功能测试"""

    @pytest.fixture
    def drafting_proxy(self):
        """创建PatentDraftingProxy实例"""
        return PatentDraftingProxy()

    @pytest.mark.asyncio
    async def test_patent_drafting_analyze_disclosure(self, drafting_proxy):
        """测试技术交底书分析"""
        # 准备测试数据
        disclosure_data = {
            "disclosure_id": "DISC_001",
            "title": "基于深度学习的图像识别方法",
            "technical_field": "G06F",
            "content": "本发明涉及一种基于深度学习的图像识别方法..."
        }

        # Mock LLM调用
        with patch.object(drafting_proxy, '_call_llm_with_fallback') as mock_llm:
            mock_llm.return_value = '{"extracted_information": {"title": "..."}, "completeness": {"score": 85}}'

            # 执行
            result = await drafting_proxy.analyze_disclosure(disclosure_data)

            # 验证
            assert result is not None
            assert "disclosure_id" in result
            assert result["disclosure_id"] == "DISC_001"

    @pytest.mark.asyncio
    async def test_patent_drafting_assess_patentability(self, drafting_proxy):
        """测试可专利性评估"""
        disclosure_data = {
            "disclosure_id": "DISC_001",
            "title": "创新技术方案",
            "technical_field": "G06F"
        }

        # Mock LLM调用
        with patch.object(drafting_proxy, '_call_llm_with_fallback') as mock_llm:
            mock_llm.return_value = '{"novelty": "有新颖性", "creativity": "有创造性", "practical_applicability": "符合"}'

            # 执行
            result = await drafting_proxy.assess_patentability(disclosure_data)

            # 验证
            assert result is not None
            assert "novelty" in str(result).lower() or "novelty" in result

    @pytest.mark.asyncio
    async def test_patent_drafting_claims(self, drafting_proxy):
        """测试权利要求书撰写"""
        input_data = {
            "disclosure_analysis": {
                "technical_features": ["特征1", "特征2", "特征3"]
            },
            "patentability_assessment": {
                "novelty": "有新颖性"
            }
        }

        # Mock LLM调用
        with patch.object(drafting_proxy, '_call_llm_with_fallback') as mock_llm:
            mock_llm.return_value = '{"independent_claim": "1. 一种技术方案...", "dependent_claims": ["2. 根据权利要求1..."]}'

            # 执行
            result = await drafting_proxy.draft_claims(input_data)

            # 验证
            assert result is not None
            assert "claim" in str(result).lower()

    @pytest.mark.asyncio
    async def test_patent_drafting_specification(self, drafting_proxy):
        """测试说明书撰写"""
        input_data = {
            "disclosure_analysis": {
                "technical_features": ["特征1", "特征2"]
            },
            "claims": ["权利要求1", "权利要求2"]
        }

        # Mock LLM调用
        with patch.object(drafting_proxy, '_call_llm_with_fallback') as mock_llm:
            mock_llm.return_value = '{"title": "技术方案", "technical_field": "本发明涉及...", "detailed_description": "具体实施方式..."}'

            # 执行
            result = await drafting_proxy.draft_specification(input_data)

            # 验证
            assert result is not None
            assert "specification" in str(result).lower() or "description" in str(result).lower()

    @pytest.mark.asyncio
    async def test_patent_drafting_optimize_scope(self, drafting_proxy):
        """测试保护范围优化"""
        input_data = {
            "claims": ["权利要求1", "权利要求2"],
            "prior_art": ["D1", "D2"]
        }

        # Mock LLM调用
        with patch.object(drafting_proxy, '_call_llm_with_fallback') as mock_llm:
            mock_llm.return_value = '{"optimization_suggestions": ["建议扩大特征1的范围", "建议添加上位概念"]}'

            # 执行
            result = await drafting_proxy.optimize_protection_scope(input_data)

            # 验证
            assert result is not None

    @pytest.mark.asyncio
    async def test_patent_drafting_review_adequacy(self, drafting_proxy):
        """测试充分公开审查"""
        input_data = {
            "specification": "说明书内容...",
            "claims": ["权利要求1", "权利要求2"]
        }

        # Mock LLM调用
        with patch.object(drafting_proxy, '_call_llm_with_fallback') as mock_llm:
            mock_llm.return_value = '{"adequacy_score": 85, "issues": [], "recommendations": []}'

            # 执行
            result = await drafting_proxy.review_adequacy(input_data)

            # 验证
            assert result is not None

    @pytest.mark.asyncio
    async def test_patent_drafting_detect_errors(self, drafting_proxy):
        """测试常见错误检测"""
        input_data = {
            "specification": "说明书内容...",
            "claims": ["权利要求1", "权利要求2"]
        }

        # Mock LLM调用
        with patch.object(drafting_proxy, '_call_llm_with_fallback') as mock_llm:
            mock_llm.return_value = '{"errors": [], "warnings": ["术语不统一"], "quality_score": 90}'

            # 执行
            result = await drafting_proxy.detect_common_errors(input_data)

            # 验证
            assert result is not None


# ============================================================================
# 集成测试
# ============================================================================

class TestMigrationIntegration:
    """迁移集成测试"""

    @pytest.mark.asyncio
    async def test_all_writer_agent_capabilities(self):
        """测试WriterAgent所有4个能力可调用"""
        agent = WriterAgent()

        capabilities = agent.get_capabilities()
        assert len(capabilities) >= 4

        capability_names = [cap.name for cap in capabilities]
        assert "claim_drafting" in capability_names
        assert "description_drafting" in capability_names
        assert "office_action_response" in capability_names
        assert "invalidation_petition" in capability_names

    @pytest.mark.asyncio
    async def test_all_patent_drafting_capabilities(self):
        """测试PatentDraftingProxy所有7个能力可调用"""
        proxy = PatentDraftingProxy()

        capabilities = proxy.get_capabilities()
        assert len(capabilities) >= 7

        capability_names = [cap["name"] for cap in capabilities]
        assert "analyze_disclosure" in capability_names
        assert "assess_patentability" in capability_names
        assert "draft_specification" in capability_names
        assert "draft_claims" in capability_names
        assert "optimize_protection_scope" in capability_names
        assert "review_adequacy" in capability_names
        assert "detect_common_errors" in capability_names

    def test_backup_files_exist(self):
        """测试备份文件存在"""
        import os
        base_path = "/Users/xujian/Athena工作平台/core/agents/xiaona"

        # 检查备份文件
        assert os.path.exists(f"{base_path}/writer_agent.py.backup")
        assert os.path.exists(f"{base_path}/patent_drafting_proxy.py.backup")

        # 验证文件大小
        original_size = os.path.getsize(f"{base_path}/writer_agent.py")
        backup_size = os.path.getsize(f"{base_path}/writer_agent.py.backup")
        assert original_size == backup_size

        original_size = os.path.getsize(f"{base_path}/patent_drafting_proxy.py")
        backup_size = os.path.getsize(f"{base_path}/patent_drafting_proxy.py.backup")
        assert original_size == backup_size

    def test_modules_directory_structure(self):
        """测试modules目录结构"""
        import os
        modules_path = "/Users/xujian/Athena工作平台/core/agents/xiaona/modules"

        # 检查目录存在
        assert os.path.exists(modules_path)

        # 检查所有模块文件
        expected_files = [
            "__init__.py",
            "drafting_module.py",
            "response_module.py",
            "orchestration_module.py",
            "utility_module.py"
        ]

        for filename in expected_files:
            file_path = os.path.join(modules_path, filename)
            assert os.path.exists(file_path), f"{filename} 不存在"

            # 验证文件不为空
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert len(content) > 0, f"{filename} 内容为空"


# ============================================================================
# 运行配置
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
