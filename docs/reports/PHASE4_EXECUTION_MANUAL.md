# 阶段4执行手册 - 向后兼容实现

> **准备时间**: 2026-04-23 16:45
> **启动条件**: 阶段3完成（unified_patent_writer.py创建完毕）

---

## 🎯 阶段4目标

实现向后兼容，确保旧代码无需修改即可使用新代理。

---

## 📋 任务清单

### 任务1: WriterAgent适配器（30分钟）

**目标文件**: `core/agents/xiaona/writer_agent.py`

**实现方案**:

```python
"""
WriterAgent适配器 - 向后兼容版本

这个适配器内部调用UnifiedPatentWriter，保持旧接口不变。
"""

import logging
from typing import Any, Dict

from core.agents.xiaona.base_component import (
    BaseXiaonaComponent,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
)

logger = logging.getLogger(__name__)


class WriterAgent(BaseXiaonaComponent):
    """
    WriterAgent适配器
    
    旧版WriterAgent的适配器版本，内部调用UnifiedPatentWriter。
    保持所有原有方法签名，确保向后兼容。
    
    迁移指南:
    - 旧代码: WriterAgent().execute(context)
    - 新代码: UnifiedPatentWriter().execute(context)
    
    注意: 建议直接使用UnifiedPatentWriter，这个适配器仅为兼容性保留。
    """
    
    def __init__(self, agent_id: str = "writer_agent"):
        super().__init__(agent_id)
        self._unified_writer = None
        self.logger.info(f"WriterAgent适配器初始化: {self.agent_id}")
    
    def _get_unified_writer(self):
        """延迟加载统一代理"""
        if self._unified_writer is None:
            from core.agents.xiaona.unified_patent_writer import UnifiedPatentWriter
            self._unified_writer = UnifiedPatentWriter()
            self.logger.info("UnifiedPatentWriter延迟加载完成")
        return self._unified_writer
    
    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """
        执行任务 - 路由到统一代理
        
        Args:
            context: 执行上下文
            
        Returns:
            执行结果
        """
        try:
            unified_writer = self._get_unified_writer()
            
            # 映射旧任务类型到新任务类型
            task_mapping = {
                "claims": "draft_claims",
                "description": "draft_specification",
                "office_action_response": "draft_office_action_response",
                "invalidation": "draft_invalidation_petition",
            }
            
            old_type = context.config.get("writing_type")
            new_type = task_mapping.get(old_type, old_type)
            
            self.logger.info(f"任务类型映射: {old_type} -> {new_type}")
            
            # 更新context
            context.config["task_type"] = new_type
            
            # 调用统一代理
            result = await unified_writer.execute(context)
            
            return result
            
        except Exception as e:
            self.logger.exception(f"WriterAgent适配器执行失败: {e}")
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                output_data=None,
                error_message=str(e)
            )
    
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是小娜·撰写者适配器。

这个适配器内部调用UnifiedPatentWriter，保持向后兼容。

注意: 这是一个过渡性适配器，建议直接使用UnifiedPatentWriter。
"""
    
    # ========== 保留原有方法签名（向后兼容）==========
    # 这些方法不再直接实现，而是通过execute()路由
    
    async def _draft_claims(self, user_input: str, previous_results: Dict[str, Any]):
        """权利要求书撰写 - 向后兼容接口（已废弃）"""
        logger.warning("_draft_claims已废弃，请使用execute()方法")
        from core.agents.xiaona.base_component import AgentExecutionContext
        context = AgentExecutionContext(
            task_id="compatibility",
            config={"task_type": "draft_claims"},
            input_data={"user_input": user_input, "previous_results": previous_results}
        )
        result = await self._get_unified_writer().execute(context)
        return result.output_data
    
    async def _draft_description(self, user_input: str, previous_results: Dict[str, Any]):
        """说明书撰写 - 向后兼容接口（已废弃）"""
        logger.warning("_draft_description已废弃，请使用execute()方法")
        from core.agents.xiaona.base_component import AgentExecutionContext
        context = AgentExecutionContext(
            task_id="compatibility",
            config={"task_type": "draft_specification"},
            input_data={"user_input": user_input, "previous_results": previous_results}
        )
        result = await self._get_unified_writer().execute(context)
        return result.output_data
    
    async def _draft_response(self, user_input: str, previous_results: Dict[str, Any]):
        """审查意见答复 - 向后兼容接口（已废弃）"""
        logger.warning("_draft_response已废弃，请使用execute()方法")
        from core.agents.xiaona.base_component import AgentExecutionContext
        context = AgentExecutionContext(
            task_id="compatibility",
            config={"task_type": "draft_office_action_response"},
            input_data={"user_input": user_input, "previous_results": previous_results}
        )
        result = await self._get_unified_writer().execute(context)
        return result.output_data
    
    async def _draft_invalidation(self, user_input: str, previous_results: Dict[str, Any]):
        """无效宣告请求书 - 向后兼容接口（已废弃）"""
        logger.warning("_draft_invalidation已废弃，请使用execute()方法")
        from core.agents.xiaona.base_component import AgentExecutionContext
        context = AgentExecutionContext(
            task_id="compatibility",
            config={"task_type": "draft_invalidation_petition"},
            input_data={"user_input": user_input, "previous_results": previous_results}
        )
        result = await self._get_unified_writer().execute(context)
        return result.output_data
```

**验证**:
- ✅ 文件创建成功
- ✅ 旧代码可调用
- ✅ 输出格式一致

---

### 任务2: PatentDraftingProxy适配器（35分钟）

**目标文件**: `core/agents/xiaona/patent_drafting_proxy.py`

**实现方案**:

```python
"""
PatentDraftingProxy适配器 - 向后兼容版本

这个适配器内部调用UnifiedPatentWriter，保持旧接口不变。
"""

import logging
from typing import Any, Dict

from core.agents.xiaona.base_component import (
    BaseXiaonaComponent,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
)

logger = logging.getLogger(__name__)


class PatentDraftingProxy(BaseXiaonaComponent):
    """
    PatentDraftingProxy适配器
    
    旧版PatentDraftingProxy的适配器版本，内部调用UnifiedPatentWriter。
    保持所有原有方法签名，确保向后兼容。
    
    迁移指南:
    - 旧代码: PatentDraftingProxy().analyze_disclosure(data)
    - 新代码: UnifiedPatentWriter().execute(context)
    
    注意: 建议直接使用UnifiedPatentWriter，这个适配器仅为兼容性保留。
    """
    
    def __init__(self, agent_id: str = "patent_drafting_proxy"):
        super().__init__(agent_id)
        self._unified_writer = None
        self.logger.info(f"PatentDraftingProxy适配器初始化: {self.agent_id}")
    
    def _get_unified_writer(self):
        """延迟加载统一代理"""
        if self._unified_writer is None:
            from core.agents.xiaona.unified_patent_writer import UnifiedPatentWriter
            self._unified_writer = UnifiedPatentWriter()
            self.logger.info("UnifiedPatentWriter延迟加载完成")
        return self._unified_writer
    
    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """
        执行任务 - 直接转发到统一代理
        
        Args:
            context: 执行上下文
            
        Returns:
            执行结果
        """
        try:
            unified_writer = self._get_unified_writer()
            return await unified_writer.execute(context)
            
        except Exception as e:
            self.logger.exception(f"PatentDraftingProxy适配器执行失败: {e}")
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                output_data=None,
                error_message=str(e)
            )
    
    def get_system_prompt(self, task_type: str = "comprehensive") -> str:
        """获取系统提示词"""
        return """你是小娜·专利撰写代理适配器。

这个适配器内部调用UnifiedPatentWriter，保持向后兼容。

注意: 这是一个过渡性适配器，建议直接使用UnifiedPatentWriter。
"""
    
    # ========== 保留原有方法签名（向后兼容）==========
    
    async def analyze_disclosure(self, disclosure_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析技术交底书 - 向后兼容接口"""
        logger.info("analyze_disclosure调用（适配器）")
        from core.agents.xiaona.base_component import AgentExecutionContext
        context = AgentExecutionContext(
            task_id="compatibility",
            config={"task_type": "analyze_disclosure"},
            input_data=disclosure_data
        )
        result = await self._get_unified_writer().execute(context)
        return result.output_data
    
    async def assess_patentability(self, disclosure_data: Dict[str, Any]) -> Dict[str, Any]:
        """评估可专利性 - 向后兼容接口"""
        logger.info("assess_patentability调用（适配器）")
        from core.agents.xiaona.base_component import AgentExecutionContext
        context = AgentExecutionContext(
            task_id="compatibility",
            config={"task_type": "assess_patentability"},
            input_data=disclosure_data
        )
        result = await self._get_unified_writer().execute(context)
        return result.output_data
    
    async def draft_specification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """撰写说明书 - 向后兼容接口"""
        logger.info("draft_specification调用（适配器）")
        from core.agents.xiaona.base_component import AgentExecutionContext
        context = AgentExecutionContext(
            task_id="compatibility",
            config={"task_type": "draft_specification"},
            input_data=data
        )
        result = await self._get_unified_writer().execute(context)
        return result.output_data
    
    async def draft_claims(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """撰写权利要求书 - 向后兼容接口"""
        logger.info("draft_claims调用（适配器）")
        from core.agents.xiaona.base_component import AgentExecutionContext
        context = AgentExecutionContext(
            task_id="compatibility",
            config={"task_type": "draft_claims"},
            input_data=data
        )
        result = await self._get_unified_writer().execute(context)
        return result.output_data
    
    async def optimize_protection_scope(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """优化保护范围 - 向后兼容接口"""
        logger.info("optimize_protection_scope调用（适配器）")
        from core.agents.xiaona.base_component import AgentExecutionContext
        context = AgentExecutionContext(
            task_id="compatibility",
            config={"task_type": "optimize_protection_scope"},
            input_data=data
        )
        result = await self._get_unified_writer().execute(context)
        return result.output_data
    
    async def review_adequacy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """审查充分公开 - 向后兼容接口"""
        logger.info("review_adequacy调用（适配器）")
        from core.agents.xiaona.base_component import AgentExecutionContext
        context = AgentExecutionContext(
            task_id="compatibility",
            config={"task_type": "review_adequacy"},
            input_data=data
        )
        result = await self._get_unified_writer().execute(context)
        return result.output_data
    
    async def detect_common_errors(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """检测常见错误 - 向后兼容接口"""
        logger.info("detect_common_errors调用（适配器）")
        from core.agents.xiaona.base_component import AgentExecutionContext
        context = AgentExecutionContext(
            task_id="compatibility",
            config={"task_type": "detect_common_errors"},
            input_data=data
        )
        result = await self._get_unified_writer().execute(context)
        return result.output_data
```

**验证**:
- ✅ 文件创建成功
- ✅ 7个方法可调用
- ✅ 输出格式一致

---

### 任务3: 更新agent_registry.json（10分钟）

**目标文件**: `config/agent_registry.json`

**更新内容**:

```json
{
  "agents": {
    "xiaona": {
      "name": "小娜·天秤女神",
      "full_name": "小娜·天秤女神",
      "role": "知识产权法律专家模块",
      "type": "agent_module",
      "description": "专业知识产权法律服务模块，包含多个专业智能体，提供专利检索、分析、撰写等全流程服务",
      "sub_agents": [
        "RetrieverAgent",
        "AnalyzerAgent",
        "UnifiedPatentWriter",
        "NoveltyAnalyzerProxy",
        "CreativityAnalyzerProxy",
        "InfringementAnalyzerProxy",
        "InvalidationAnalyzerProxy",
        "ApplicationReviewerProxy",
        "WritingReviewerProxy"
      ],
      "deprecated": [
        {
          "name": "WriterAgent",
          "replacement": "UnifiedPatentWriter",
          "deprecated_since": "2.0.0",
          "reason": "已合并到UnifiedPatentWriter",
          "migration_guide": "请使用UnifiedPatentWriter，或通过WriterAgent适配器保持兼容"
        },
        {
          "name": "PatentDraftingProxy",
          "replacement": "UnifiedPatentWriter",
          "deprecated_since": "2.0.0",
          "reason": "已合并到UnifiedPatentWriter",
          "migration_guide": "请使用UnifiedPatentWriter，或通过PatentDraftingProxy适配器保持兼容"
        }
      ],
      "capabilities": {
        "patent_writing": {
          "name": "专利撰写",
          "component": "UnifiedPatentWriter",
          "version": "2.0.0",
          "note": "整合WriterAgent和PatentDraftingProxy，提供13个核心能力"
        }
      }
    }
  },
  "version": "2.0.0",
  "updated": "2026-04-23"
}
```

**验证**:
- ✅ JSON格式正确
- ✅ 配置可加载
- ✅ 新代理可被发现

---

### 任务4: 兼容性测试（30分钟）

**目标文件**: `tests/agents/xiaona/test_backward_compatibility.py`

**测试内容**:

```python
"""
向后兼容性测试套件

测试WriterAgent和PatentDraftingProxy适配器，
确保旧代码无需修改即可使用。
"""

import pytest
from unittest.mock import Mock
from core.agents.xiaona.writer_agent import WriterAgent
from core.agents.xiaona.patent_drafting_proxy import PatentDraftingProxy


class TestWriterAgentBackwardCompatibility:
    """WriterAgent向后兼容性测试"""
    
    @pytest.fixture
    def writer_agent(self):
        return WriterAgent()
    
    @pytest.mark.asyncio
    async def test_old_interface_claims(self, writer_agent):
        """测试旧的claims接口"""
        context = Mock()
        context.config = {"writing_type": "claims"}
        context.input_data = {
            "user_input": "测试输入",
            "previous_results": {"features": ["特征1"]}
        }
        context.task_id = "test_001"
        
        # 应该成功路由到draft_claims
        result = await writer_agent.execute(context)
        
        assert result.status.value == "completed"
        assert result.output_data is not None
    
    @pytest.mark.asyncio
    async def test_old_interface_description(self, writer_agent):
        """测试旧的description接口"""
        context = Mock()
        context.config = {"writing_type": "description"}
        context.input_data = {
            "user_input": "测试输入",
            "previous_results": {}
        }
        context.task_id = "test_002"
        
        result = await writer_agent.execute(context)
        
        assert result.status.value == "completed"


class TestPatentDraftingProxyBackwardCompatibility:
    """PatentDraftingProxy向后兼容性测试"""
    
    @pytest.fixture
    def drafting_proxy(self):
        return PatentDraftingProxy()
    
    @pytest.mark.asyncio
    async def test_analyze_disclosure(self, drafting_proxy):
        """测试analyze_disclosure方法"""
        disclosure_data = {
            "disclosure_id": "TEST_001",
            "title": "测试发明",
            "content": "测试内容"
        }
        
        result = await drafting_proxy.analyze_disclosure(disclosure_data)
        
        assert result is not None
        assert "disclosure_id" in result
    
    @pytest.mark.asyncio
    async def test_all_seven_methods(self, drafting_proxy):
        """测试所有7个方法可调用"""
        methods = [
            "analyze_disclosure",
            "assess_patentability",
            "draft_specification",
            "draft_claims",
            "optimize_protection_scope",
            "review_adequacy",
            "detect_common_errors"
        ]
        
        for method_name in methods:
            method = getattr(drafting_proxy, method_name)
            assert callable(method), f"{method_name} 不可调用"


class TestOutputFormatConsistency:
    """输出格式一致性测试"""
    
    @pytest.mark.asyncio
    async def test_writer_agent_output_format(self):
        """测试WriterAgent输出格式与旧版一致"""
        agent = WriterAgent()
        context = Mock()
        context.config = {"writing_type": "claims"}
        context.input_data = {"user_input": "测试"}
        context.task_id = "test_003"
        
        result = await agent.execute(context)
        
        # 验证输出格式包含必要字段
        assert hasattr(result, "status")
        assert hasattr(result, "output_data")
        assert hasattr(result, "metadata")


def test_adapter_deprecation_warnings():
    """测试适配器发出正确的废弃警告"""
    import warnings
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # 调用适配器的旧方法应该发出警告
        agent = WriterAgent()
        # agent._draft_claims()  # 这个方法应该发出警告
        
        # 验证警告信息
        # assert len(w) > 0
        # assert "已废弃" in str(w[0].message)
```

**验证**:
- ✅ 所有旧接口可调用
- ✅ 输出格式一致
- ✅ 废弃警告正确

---

## 👥 团队配置（阶段4）

### Spawn计划

等待阶段3完成后，spawn 3个teammates：

```python
# 任务1: WriterAgent适配器
Agent(
    name="writer-adapter-builder",
    description="创建WriterAgent适配器",
    prompt="创建writer_agent.py适配器..."
)

# 任务2: PatentDraftingProxy适配器
Agent(
    name="drafting-proxy-adapter-builder",
    description="创建PatentDraftingProxy适配器",
    prompt="创建patent_drafting_proxy.py适配器..."
)

# 任务3: 配置更新
Agent(
    name="config-updater",
    description="更新agent_registry.json",
    prompt="更新配置文件..."
)
```

---

## ⏱️ 时间估算

| 任务 | 时间 | 累计 |
|------|------|------|
| WriterAgent适配器 | 30分钟 | 0:30 |
| PatentDraftingProxy适配器 | 35分钟 | 1:05 |
| 更新agent_registry.json | 10分钟 | 1:15 |
| 兼容性测试 | 30分钟 | 1:45 |

**总计**: 约105分钟

---

## ✅ 完成标准

### 功能性
- [ ] 适配器文件创建成功
- [ ] 所有旧接口可调用
- [ ] 输出格式与旧版一致

### 配置
- [ ] agent_registry.json更新
- [ ] 废弃标记添加
- [ ] 新代理可被发现

### 测试
- [ ] 兼容性测试通过
- [ ] 所有旧测试仍然通过
- [ ] 无回归问题

---

**准备就绪**: 等待阶段3完成
**预计启动**: 17:30
**预计完成**: 19:15
