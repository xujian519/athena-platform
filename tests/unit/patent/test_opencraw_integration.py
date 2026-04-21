#!/usr/bin/env python3
"""
OpenClaw功能集成单元测试

测试范围:
- TaskStateManager: 任务状态管理
- SpecificationQualityReviewer: 质量审查
- data_structures: 数据结构
- API端点: REST API集成

作者: Athena平台团队
创建时间: 2026-03-27
"""

import shutil
import tempfile

import pytest


class TestTaskStateManager:
    """任务状态管理器测试"""

    @pytest.fixture
    def temp_storage(self):
        """创建临时存储目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def manager(self, temp_storage):
        """创建管理器实例"""
        from core.patents.task_state_manager import TaskStateManager
        return TaskStateManager(storage_dir=temp_storage)

    def test_create_task(self, manager):
        """测试创建任务"""
        task = manager.create_task(
            task_id="TEST-001",
            client="测试客户"
        )

        assert task.task_id == "TEST-001"
        assert task.client == "测试客户"
        assert task.status == "pending"
        assert len(task.phases) == 9  # 9阶段流程

    def test_load_task(self, manager):
        """测试加载任务"""
        # 创建任务
        manager.create_task(task_id="TEST-002")

        # 加载任务
        task = manager.load_task("TEST-002")

        assert task is not None
        assert task.task_id == "TEST-002"

    def test_update_phase(self, manager):
        """测试更新阶段状态"""
        manager.create_task(task_id="TEST-003")

        # 更新阶段
        manager.update_phase("TEST-003", 0, "completed")

        # 验证
        task = manager.load_task("TEST-003")
        assert task.phases[0]["status"] == "completed"

    def test_pause_resume_task(self, manager):
        """测试暂停和恢复任务"""
        manager.create_task(task_id="TEST-004")

        # 暂停
        manager.pause_task("TEST-004", "测试暂停")
        task = manager.load_task("TEST-004")
        assert task.status == "paused"

        # 恢复
        manager.resume_task("TEST-004")
        task = manager.load_task("TEST-004")
        assert task.status == "in_progress"

    def test_get_progress(self, manager):
        """测试获取进度"""
        manager.create_task(task_id="TEST-005")
        manager.update_phase("TEST-005", 0, "completed")

        progress = manager.get_progress("TEST-005")

        assert progress["task_id"] == "TEST-005"
        assert progress["completed_phases"] == 1
        assert progress["total_phases"] == 9

    def test_delete_task(self, manager):
        """测试删除任务"""
        manager.create_task(task_id="TEST-006")

        # 删除
        success = manager.delete_task("TEST-006")
        assert success is True

        # 验证已删除
        task = manager.load_task("TEST-006")
        assert task is None


class TestSpecificationQualityReviewer:
    """说明书质量审查器测试"""

    @pytest.fixture
    def reviewer(self):
        """创建审查器实例"""
        from core.patents.specification_quality_reviewer import SpecificationQualityReviewer
        return SpecificationQualityReviewer()

    @pytest.fixture
    def sample_specification(self):
        """示例说明书"""
        return {
            "case_id": "TEST-CASE-001",
            "invention_title": "一种智能床垫",
            "detailed_description": {
                "content": "本实施例提供了一种智能床垫，包括床垫主体、压力传感器、控制器等组件。"
                           "压力传感器安装在床垫主体内部，用于检测用户的睡姿。"
                           "控制器与压力传感器连接，用于处理检测数据。" * 50
            },
            "invention_content": {
                "content": "本发明提供了一种智能床垫，有益效果包括：睡姿监测准确、响应速度快、使用寿命长。"
            }
        }

    @pytest.fixture
    def sample_claims(self):
        """示例权利要求"""
        return {
            "claims": [
                {
                    "claim_number": 1,
                    "claim_type": "independent",
                    "content": "一种智能床垫，包括床垫主体和压力传感器。"
                },
                {
                    "claim_number": 2,
                    "claim_type": "dependent",
                    "content": "根据权利要求1所述的床垫，所述压力传感器为压电传感器。"
                }
            ]
        }

    def test_review_basic(self, reviewer, sample_specification, sample_claims):
        """测试基本审查功能"""
        report = reviewer.review(sample_specification, sample_claims)

        assert report.case_id == "TEST-CASE-001"
        assert report.overall_risk is not None
        assert report.authorization_probability >= 0
        assert report.authorization_probability <= 1

    def test_detect_unclear_patterns(self, reviewer, sample_specification):
        """测试检测不确定表述"""
        claims_with_issues = {
            "claims": [
                {
                    "claim_number": 1,
                    "claim_type": "independent",
                    "content": "一种装置，包括处理器之类组件。"
                }
            ]
        }

        report = reviewer.review(sample_specification, claims_with_issues)

        # 应该检测到"之类"
        assert report.p1_count >= 1 or report.p2_count >= 1

    def test_check_sufficiency(self, reviewer, sample_claims):
        """测试公开充分性检查"""
        # 内容过短的说明书
        short_spec = {
            "case_id": "TEST-002",
            "invention_title": "测试发明",
            "detailed_description": {"content": "简短内容"},
            "invention_content": {"content": "无效果描述"}
        }

        report = reviewer.review(short_spec, sample_claims)

        # 应该发现问题
        assert len(report.issues) > 0

    def test_report_to_markdown(self, reviewer, sample_specification, sample_claims):
        """测试报告Markdown输出"""
        report = reviewer.review(sample_specification, sample_claims)
        md = report.to_markdown()

        assert "质量审查报告" in md
        assert "授权概率" in md


class TestDataStructures:
    """数据结构测试"""

    def test_technical_feature(self):
        """测试技术特征"""
        from core.patents.data_structures import FeatureType, TechnicalFeature

        feature = TechnicalFeature(
            id="F1",
            description="压力传感器",
            feature_type=FeatureType.ESSENTIAL,
            component="床垫主体",
            function="检测睡姿"
        )

        assert feature.id == "F1"
        assert feature.feature_type == FeatureType.ESSENTIAL

        # 测试字典转换
        d = feature.to_dict()
        assert d["id"] == "F1"
        assert d["feature_type"] == "essential"

    def test_invention_understanding(self):
        """测试发明理解结构"""
        from core.patents.data_structures import (
            FeatureType,
            InventionType,
            InventionUnderstanding,
            TechnicalFeature,
        )

        # data_structures.py中的InventionUnderstanding不包含prior_art_issues和differentiation
        understanding = InventionUnderstanding(
            invention_title="智能床垫",
            invention_type=InventionType.DEVICE,
            technical_field="智能家居",
            core_innovation="基于压力传感器的睡姿监测",
            technical_problem="无法准确监测睡姿",
            technical_solution="使用压力传感器阵列",
            technical_effects=["监测准确", "响应快"],
            essential_features=[
                TechnicalFeature(
                    id="F1",
                    description="压力传感器",
                    feature_type=FeatureType.ESSENTIAL
                )
            ],
            optional_features=[],
            confidence_score=0.85
        )

        assert understanding.invention_title == "智能床垫"
        assert understanding.invention_type == InventionType.DEVICE
        assert len(understanding.essential_features) == 1

    def test_claims_set(self):
        """测试权利要求集合"""
        from core.patents.ai_services.autospec_drafter import SpecificationDraft

        draft = SpecificationDraft(
            draft_id="test-draft",
            invention_title="测试发明",
            claims=[
                "1. 一种装置，包括组件A。",
                "2. 根据权利要求1所述的装置，组件A为B。"
            ]
        )

        assert draft.invention_title == "测试发明"
        assert len(draft.claims) == 2

        # 测试完整说明书输出
        full_spec = draft.get_full_specification()
        assert "测试发明" in full_spec


class TestAutoSpecDrafterIntegration:
    """AutoSpecDrafter集成测试"""

    @pytest.fixture
    def temp_storage(self):
        """临时存储"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_full_workflow(self, temp_storage):
        """测试完整9阶段流程"""
        from core.patents.ai_services.autospec_drafter import AutoSpecDrafter

        drafter = AutoSpecDrafter(
            llm_manager=None,
            storage_dir=temp_storage
        )

        disclosure = """
发明名称：一种智能床垫

技术领域：智能家居

技术问题：现有床垫无法准确监测用户睡姿

技术方案：
1. 床垫主体
2. 压力传感器，安装在床垫主体内
3. 控制器，与压力传感器连接

技术效果：
1. 实现精准睡姿监测
2. 响应速度快
"""

        result = await drafter.draft_specification_full(
            disclosure=disclosure,
            task_id="INTEGRATION-TEST-001",
            client="测试客户",
            enable_examiner_simulation=True
        )

        assert result.task_id == "INTEGRATION-TEST-001"
        assert result.status == "completed"
        assert len(result.phases_completed) == 9
        assert result.draft is not None

    @pytest.mark.asyncio
    async def test_task_persistence(self, temp_storage):
        """测试任务持久化"""
        from core.patents.ai_services.autospec_drafter import AutoSpecDrafter

        drafter = AutoSpecDrafter(
            llm_manager=None,
            storage_dir=temp_storage
        )

        # 创建并暂停任务
        disclosure = "测试技术交底书"
        _ = await drafter.draft_specification_full(
            disclosure=disclosure,
            task_id="PERSIST-TEST-001"
        )

        # 验证任务状态已保存
        from core.patents.task_state_manager import TaskStateManager
        manager = TaskStateManager(storage_dir=temp_storage)
        task = manager.load_task("PERSIST-TEST-001")

        assert task is not None
        assert task.task_id == "PERSIST-TEST-001"


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
