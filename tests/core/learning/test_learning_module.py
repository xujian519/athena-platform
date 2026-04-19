#!/usr/bin/env python3
"""
学习模块测试用例
Learning Module Tests

测试学习模块的核心功能，包括:
- 基础学习引擎
- 增强学习引擎
- 自主学习系统
- 在线学习
- 强化学习
- 元学习
- 不确定性量化

作者: Athena AI系统
版本: v1.0.0
创建时间: 2026-01-30
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


# =============================================================================
# === 基础学习引擎测试 ===
# =============================================================================

class TestLearningEngine:
    """基础学习引擎测试"""

    @pytest.fixture
    def engine(self):
        from core.learning import LearningEngine
        return LearningEngine(agent_id="test_agent", config={"test": True})

    def test_initialization(self, engine):
        """测试引擎初始化"""
        assert engine.agent_id == "test_agent"
        assert engine.config == {"test": True}
        assert engine.initialized is False

    @pytest.mark.asyncio
    async def test_initialize(self, engine):
        """测试引擎启动"""
        await engine.initialize()
        assert engine.initialized is True

    @pytest.mark.asyncio
    async def test_learn(self, engine):
        """测试学习功能"""
        await engine.initialize()
        result = await engine.learn({"test": "data"})
        assert result["status"] == "learned"

    def test_register_callback(self, engine):
        """测试注册回调函数"""
        callback = MagicMock()
        engine.register_callback("learning_complete", callback)
        assert "learning_complete" in engine._callbacks
        assert callback in engine._callbacks["learning_complete"]

    @pytest.mark.asyncio
    async def test_shutdown(self, engine):
        """测试引擎关闭"""
        await engine.initialize()
        await engine.shutdown()
        assert engine.initialized is False

    @pytest.mark.asyncio
    async def test_global_instance(self):
        """测试全局实例"""
        from core.learning import LearningEngine
        instance1 = await LearningEngine.initialize_global()
        instance2 = await LearningEngine.initialize_global()
        assert instance1 is instance2
        await LearningEngine.shutdown_global()


# =============================================================================
# === 模块化学习引擎测试 ===
# =============================================================================

class TestModularLearningEngine:
    """模块化学习引擎测试"""

    @pytest.fixture
    def modular_engine_available(self):
        try:
            from core.learning import ModularLearningEngine
            return True
        except ImportError:
            return False

    def test_modular_engine_import(self, modular_engine_available):
        """测试模块化学习引擎导入"""
        if not modular_engine_available:
            pytest.skip("ModularLearningEngine not available")
        from core.learning import (
            AdaptiveOptimizer,
            ExperienceStore,
            KnowledgeGraphUpdater,
            ModularLearningEngine,
            PatternRecognizer,
        )
        assert ModularLearningEngine is not None
        assert AdaptiveOptimizer is not None
        assert ExperienceStore is not None
        assert KnowledgeGraphUpdater is not None
        assert PatternRecognizer is not None

    @pytest.mark.asyncio
    async def test_experience_store(self, modular_engine_available):
        """测试经验存储"""
        if not modular_engine_available:
            pytest.skip("ModularLearningEngine not available")
        from core.learning import ExperienceStore
        store = ExperienceStore()
        await store.initialize()

        # 存储经验
        await store.add_experience({
            "context": {"task": "test"},
            "action": "test_action",
            "result": {"success": True},
            "reward": 1.0
        })

        # 获取经验
        experiences = await store.get_experiences(limit=10)
        assert len(experiences) > 0

        await store.shutdown()


# =============================================================================
# === 增强学习引擎测试 ===
# =============================================================================

class TestEnhancedLearningEngine:
    """增强学习引擎测试"""

    @pytest.fixture
    def enhanced_learning_available(self):
        try:
            from core.learning import EnhancedLearningEngine
            return True
        except ImportError:
            return False

    @pytest.mark.asyncio
    async def test_enhanced_learning(self, enhanced_learning_available):
        """测试增强学习引擎"""
        if not enhanced_learning_available:
            pytest.skip("EnhancedLearningEngine not available")
        from core.learning import EnhancedLearningEngine, LearningTask
        engine = EnhancedLearningEngine(agent_id="test_agent")
        await engine.initialize()

        task = LearningTask(
            id="test_task_001",
            task_type="classification",
            data={"features": [1, 2, 3]},
            labels=[0, 1, 0]
        )

        result = await engine.execute_task(task)
        assert result is not None

        await engine.shutdown()


# =============================================================================
# === 自主学习系统测试 ===
# =============================================================================

class TestAutonomousLearning:
    """自主学习系统测试"""

    @pytest.fixture
    def autonomous_learning_available(self):
        try:
            from core.learning import AutonomousLearningSystem
            return True
        except ImportError:
            return False

    def test_autonomous_learning_import(self, autonomous_learning_available):
        """测试自主学习系统导入"""
        if not autonomous_learning_available:
            pytest.skip("AutonomousLearningSystem not available")
        from core.learning import (
            AutonomousLearningSystem,
            LearningAutonomy,
            SelfImprovementCycle,
        )
        assert AutonomousLearningSystem is not None
        assert LearningAutonomy is not None
        assert SelfImprovementCycle is not None

    @pytest.mark.asyncio
    async def test_autonomous_learning(self, autonomous_learning_available):
        """测试自主学习"""
        if not autonomous_learning_available:
            pytest.skip("AutonomousLearningSystem not available")
        from core.learning import AutonomousLearningSystem
        system = AutonomousLearningSystem(agent_id="test_agent")
        await system.initialize()

        # 从经验中学习
        await system.learn_from_experience(
            context={"task": "test_task"},
            action="test_action",
            result={"success": True},
            reward=0.8
        )

        await system.shutdown()


# =============================================================================
# === 在线学习测试 ===
# =============================================================================

class TestOnlineLearning:
    """在线学习测试"""

    @pytest.fixture
    def online_learning_available(self):
        try:
            from core.learning import OnlineLearningEngine
            return True
        except ImportError:
            return False

    def test_online_learning_import(self, online_learning_available):
        """测试在线学习导入"""
        if not online_learning_available:
            pytest.skip("OnlineLearningEngine not available")
        from core.learning import (
            IncrementalLearner,
            OnlineLearningEngine,
            OnlineLearningSystem,
        )
        assert OnlineLearningSystem is not None
        assert OnlineLearningEngine is not None
        assert IncrementalLearner is not None

    @pytest.mark.asyncio
    async def test_incremental_learning(self, online_learning_available):
        """测试增量学习"""
        if not online_learning_available:
            pytest.skip("OnlineLearningEngine not available")
        from core.learning import IncrementalLearner
        learner = IncrementalLearner()
        await learner.initialize()

        # 增量学习
        for i in range(10):
            await self.learn_incremental(learner, {
                "features": [i, i+1, i+2],
                "label": i % 2
            })

        # 预测
        prediction = await learner.predict({"features": [5, 6, 7]})
        assert prediction is not None

        await learner.shutdown()

    @pytest.mark.asyncio
    async def learn_incremental(self, learner, data):
        """增量学习辅助方法"""
        await learner.learn(data)


# =============================================================================
# === 强化学习测试 ===
# =============================================================================

class TestReinforcementLearning:
    """强化学习测试"""

    @pytest.fixture
    def rl_available(self):
        try:
            from core.learning import ReinforcementLearningAgent
            return True
        except ImportError:
            return False

    def test_rl_import(self, rl_available):
        """测试强化学习导入"""
        if not rl_available:
            pytest.skip("ReinforcementLearningAgent not available")
        from core.learning import (
            ProductionRLIntegration,
            ReinforcementLearningAgent,
            RLPolicy,
            RLTrainer,
        )
        assert ReinforcementLearningAgent is not None
        assert RLPolicy is not None
        assert RLTrainer is not None
        assert ProductionRLIntegration is not None

    @pytest.mark.asyncio
    async def test_rl_agent(self, rl_available):
        """测试RL代理"""
        if not rl_available:
            pytest.skip("ReinforcementLearningAgent not available")
        from core.learning import ReinforcementLearningAgent
        agent = ReinforcementLearningAgent(
            state_space=4,
            action_space=2
        )
        await agent.initialize()

        # 选择动作
        state = [0.1, 0.2, 0.3, 0.4]
        action = await agent.select_action(state)
        assert action is not None

        # 学习
        await agent.learn(
            state=state,
            action=action,
            reward=1.0,
            next_state=[0.2, 0.3, 0.4, 0.5],
            done=False
        )

        await agent.shutdown()


# =============================================================================
# === 元学习测试 ===
# =============================================================================

class TestMetaLearning:
    """元学习测试"""

    @pytest.fixture
    def meta_learning_available(self):
        try:
            from core.learning import MetaLearningEngine
            return True
        except ImportError:
            return False

    def test_meta_learning_import(self, meta_learning_available):
        """测试元学习导入"""
        if not meta_learning_available:
            pytest.skip("MetaLearningEngine not available")
        from core.learning import (
            EnhancedMetaLearning,
            MetaLearningEngine,
            MetaLearningImplementation,
        )
        assert MetaLearningEngine is not None
        assert EnhancedMetaLearning is not None
        assert MetaLearningImplementation is not None


# =============================================================================
# === 不确定性量化测试 ===
# =============================================================================

class TestUncertaintyQuantification:
    """不确定性量化测试"""

    @pytest.fixture
    def uncertainty_available(self):
        try:
            from core.learning import UncertaintyQuantifier
            return True
        except ImportError:
            return False

    def test_uncertainty_import(self, uncertainty_available):
        """测试不确定性量化导入"""
        if not uncertainty_available:
            pytest.skip("UncertaintyQuantifier not available")
        from core.learning import (
            UncertaintyEstimate,
            UncertaintyQuantifier,
        )
        assert UncertaintyQuantifier is not None
        assert UncertaintyEstimate is not None

    @pytest.mark.asyncio
    async def test_uncertainty_quantification(self, uncertainty_available):
        """测试不确定性量化"""
        if not uncertainty_available:
            pytest.skip("UncertaintyQuantifier not available")
        from core.learning import UncertaintyQuantifier
        quantifier = UncertaintyQuantifier()
        await quantifier.initialize()

        # 量化不确定性
        prediction = {"class": 0, "probabilities": [0.7, 0.3]}
        uncertainty = await quantifier.quantify_uncertainty(prediction)
        assert uncertainty is not None
        assert "uncertainty_score" in uncertainty or "entropy" in uncertainty

        await quantifier.shutdown()


# =============================================================================
# === 知识蒸馏测试 ===
# =============================================================================

class TestKnowledgeDistillation:
    """知识蒸馏测试"""

    @pytest.fixture
    def distillation_available(self):
        try:
            from core.learning import KnowledgeDistillation
            return True
        except ImportError:
            return False

    def test_distillation_import(self, distillation_available):
        """测试知识蒸馏导入"""
        if not distillation_available:
            pytest.skip("KnowledgeDistillation not available")
        from core.learning import (
            KnowledgeDistillation,
            TeacherStudentModel,
        )
        assert KnowledgeDistillation is not None
        assert TeacherStudentModel is not None


# =============================================================================
# === 迁移学习测试 ===
# =============================================================================

class TestTransferLearning:
    """迁移学习测试"""

    @pytest.fixture
    def transfer_learning_available(self):
        try:
            from core.learning import TransferLearningFramework
            return True
        except ImportError:
            return False

    def test_transfer_learning_import(self, transfer_learning_available):
        """测试迁移学习导入"""
        if not transfer_learning_available:
            pytest.skip("TransferLearningFramework not available")
        from core.learning import (
            TransferLearningFramework,
            TransferStrategy,
        )
        assert TransferLearningFramework is not None
        assert TransferStrategy is not None


# =============================================================================
# === 模块可用性测试 ===
# =============================================================================

class TestModuleCapabilities:
    """模块可用性测试"""

    def test_get_module_capabilities(self):
        """测试获取模块能力"""
        from core.learning import get_module_capabilities
        capabilities = get_module_capabilities()
        assert isinstance(capabilities, dict)
        assert "modular_learning" in capabilities
        assert "enhanced_learning" in capabilities
        assert "autonomous_learning" in capabilities
        assert "online_learning" in capabilities
        assert "reinforcement_learning" in capabilities
        assert "meta_learning" in capabilities
        assert "uncertainty_quantification" in capabilities

    def test_get_available_features(self):
        """测试获取可用功能"""
        from core.learning import get_available_features
        features = get_available_features()
        assert isinstance(features, list)


# =============================================================================
# === 集成测试 ===
# =============================================================================

class TestLearningIntegration:
    """学习模块集成测试"""

    @pytest.mark.asyncio
    async def test_learning_pipeline(self):
        """测试完整学习流程"""
        from core.learning import LearningEngine
        engine = LearningEngine(agent_id="integration_test")

        # 初始化
        await engine.initialize()
        assert engine.initialized is True

        # 学习
        for i in range(5):
            data = {"sample": i, "value": i * 10}
            result = await engine.learn(data)
            assert result["status"] == "learned"

        # 关闭
        await engine.shutdown()
        assert engine.initialized is False


# =============================================================================
# === 性能测试 ===
# =============================================================================

class TestLearningPerformance:
    """学习模块性能测试"""

    @pytest.mark.asyncio
    @pytest.mark.benchmark(group="learning")
    async def test_learning_performance(self, benchmark):
        """测试学习性能"""
        from core.learning import LearningEngine
        engine = LearningEngine(agent_id="perf_test")
        await engine.initialize()

        async def learn_items():
            for i in range(100):
                await engine.learn({"item": i, "data": "test"})

        await benchmark(learn_items)
        await engine.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
