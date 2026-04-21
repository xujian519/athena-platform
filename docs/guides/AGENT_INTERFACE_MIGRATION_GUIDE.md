# Agent接口迁移指南

> **版本**: v1.0
> **日期**: 2026-04-21
> **目标受众**: 需要将现有Agent迁移到统一接口的开发者

---

## 📋 目录

1. [概述](#概述)
2. [迁移准备](#迁移准备)
3. [迁移步骤](#迁移步骤)
4. [常见迁移场景](#常见迁移场景)
5. [验证与测试](#验证与测试)
6. [回滚计划](#回滚计划)

---

## 概述

### 迁移目标

本指南帮助你：
- ✅ 将现有Agent迁移到统一接口标准
- ✅ 保持向后兼容性
- ✅ 平滑过渡，不影响现有功能
- ✅ 提升代码质量和可维护性

### 迁移范围

适用于：
- 旧版本的Agent实现
- 不符合统一接口标准的Agent
- 需要重构的Agent

### 迁移原则

**DO** ✅:
- ✅ 先测试，后迁移
- ✅ 小步迭代，逐步迁移
- ✅ 保持向后兼容
- ✅ 充分测试后再部署

**DON'T** ❌:
- ❌ 大规模一次性重构
- ❌ 不测试直接部署
- ❌ 破坏现有功能
- ❌ 忽略性能影响

---

## 迁移准备

### Step 1: 分析现有Agent

**分析清单**:

- [ ] 当前Agent的文件位置
- [ ] 当前Agent的依赖关系
- [ ] 当前Agent的接口定义
- [ ] 当前Agent的使用场景
- [ ] 当前Agent的测试覆盖

**分析工具**:

```python
# 使用grep查找Agent文件
find core/agents/ -name "*_agent.py" -type f

# 分析Agent的接口
python -c "
from core.agents.old_agent import OldAgent
import inspect

# 列出所有方法
methods = [m for m in dir(OldAgent) if not m.startswith('_')]
print('公共方法:', methods)

# 查看方法签名
for method in methods:
    func = getattr(OldAgent, method)
    if callable(func):
        sig = inspect.signature(func)
        print(f'{method}: {sig}')
"
```

### Step 2: 创建备份

**备份文件**:

```bash
# 创建备份目录
mkdir -p .backup/before_migration

# 备份Agent文件
cp core/agents/old_agent.py .backup/before_migration/

# 备份测试文件
cp tests/agents/test_old_agent.py .backup/before_migration/
```

**创建Git分支**:

```bash
# 创建迁移分支
git checkout -b feature/migrate-to-unified-interface

# 确认分支
git branch
```

### Step 3: 评估迁移复杂度

**复杂度评估**:

| 复杂度 | Agent数量 | 文件数量 | 预计时间 |
|--------|---------|---------|---------|
| **低** | 1-2个 | 1-5个 | 1-2天 |
| **中** | 3-5个 | 6-15个 | 3-5天 |
| **高** | 6+个 | 16+个 | 1-2周 |

---

## 迁移步骤

### Step 1: 创建统一接口包装器（向后兼容）

**目标**: 保持旧接口可用，同时实现新接口

```python
"""
旧Agent迁移示例 - 向后兼容包装器
"""

from typing import Any, Dict
from core.agents.xiaona.base_component import (
    BaseXiaonaComponent,
    AgentCapability,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
)


class OldAgentAdapter(BaseXiaonaComponent):
    """
    旧Agent适配器
    
    将旧Agent适配到统一接口标准。
    """

    def _initialize(self) -> None:
        """初始化适配器"""
        # 导入旧Agent
        from core.agents.old_agent import OldAgent
        
        # 创建旧Agent实例
        self.old_agent = OldAgent()
        
        # 注册能力（从旧Agent映射）
        self._register_capabilities([
            AgentCapability(
                name="old_capability",
                description="从旧Agent迁移的能力",
                input_types=["输入"],
                output_types=["输出"],
                estimated_time=5.0,
            ),
        ])
        
        self.logger.info(f"旧Agent适配器初始化完成: {self.agent_id}")

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        # 从旧Agent获取提示词（如果有）
        if hasattr(self.old_agent, 'get_prompt'):
            return self.old_agent.get_prompt()
        else:
            return "你是旧Agent，负责XXX任务。"

    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """
        执行任务 - 适配旧Agent接口
        
        Args:
            context: 执行上下文

        Returns:
            执行结果
        """
        try:
            # 转换输入格式
            old_input = self._convert_to_old_format(context)
            
            # 调用旧Agent
            old_output = await self._call_old_agent(old_input)
            
            # 转换输出格式
            new_output = self._convert_from_old_format(old_output)
            
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.COMPLETED,
                output_data=new_output,
            )
            
        except Exception as e:
            self.logger.exception(f"任务执行失败: {context.task_id}")
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                error_message=str(e),
            )

    def _convert_to_old_format(self, context: AgentExecutionContext) -> Dict[str, Any]:
        """转换输入格式"""
        # 将新格式转换为旧格式
        return {
            "input": context.input_data.get("user_input"),
            "config": context.config,
        }

    async def _call_old_agent(self, old_input: Dict[str, Any]) -> Any:
        """调用旧Agent"""
        # 根据旧Agent的接口调用
        if hasattr(self.old_agent, 'process'):
            # 旧Agent有process方法
            return await self.old_agent.process(old_input)
        elif hasattr(self.old_agent, 'execute'):
            # 旧Agent有execute方法
            return await self.old_agent.execute(old_input)
        else:
            raise NotImplementedError("旧Agent没有可调用的方法")

    def _convert_from_old_format(self, old_output: Any) -> Dict[str, Any]:
        """转换输出格式"""
        # 将旧格式转换为新格式
        if isinstance(old_output, dict):
            return old_output
        elif isinstance(old_output, str):
            return {"result": old_output}
        else:
            return {"data": old_output}
```

### Step 2: 重构核心逻辑

**目标**: 将旧Agent的核心逻辑迁移到新接口

```python
class MyAgent(BaseXiaonaComponent):
    """
    迁移后的Agent
    
    使用统一接口标准重新实现。
    """

    def _initialize(self) -> None:
        """初始化"""
        # 注册能力
        self._register_capabilities([
            AgentCapability(
                name="my_capability",
                description="我的能力",
                input_types=["输入"],
                output_types=["输出"],
                estimated_time=5.0,
            ),
        ])

    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """执行任务"""
        try:
            # 核心逻辑
            result = await self._core_logic(context)
            
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.COMPLETED,
                output_data=result,
            )
        except Exception as e:
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                error_message=str(e),
            )

    async def _core_logic(self, context: AgentExecutionContext) -> Dict[str, Any]:
        """
        核心逻辑
        
        这是旧Agent的核心逻辑，直接迁移过来。
        """
        # 从旧Agent迁移的核心逻辑
        # ...
        return {"result": "success"}
```

### Step 3: 更新调用方

**目标**: 更新所有调用旧Agent的代码

**查找调用方**:

```bash
# 查找所有使用旧Agent的地方
grep -r "OldAgent" core/ --include="*.py"
grep -r "from core.agents.old_agent" . --include="*.py"
```

**更新调用**:

```python
# 旧代码
from core.agents.old_agent import OldAgent

agent = OldAgent()
result = await agent.process(input_data)

# 新代码
from core.agents.my_agent import MyAgent

agent = MyAgent(agent_id="my_agent")
context = AgentExecutionContext(
    session_id="SESSION_001",
    task_id="TASK_001",
    input_data={"user_input": input_data},
    config={},
    metadata={},
)
result = await agent.execute(context)
```

### Step 4: 删除旧代码

**目标**: 在确认新代码正常工作后，删除旧代码

**删除步骤**:

1. 确认所有测试通过
2. 确认所有调用方已更新
3. 删除旧Agent文件
4. 删除旧测试文件

```bash
# 删除旧Agent
rm core/agents/old_agent.py

# 删除旧测试
rm tests/agents/test_old_agent.py

# 提交删除
git add core/agents/old_agent.py tests/agents/test_old_agent.py
git commit -m "refactor: 删除旧Agent，使用统一接口版本"
```

---

## 常见迁移场景

### 场景1: 简单Agent迁移

**情况**: Agent只有几个方法，使用简单

**迁移步骤**:

1. **创建新Agent**（继承BaseXiaonaComponent）
2. **迁移核心逻辑**（直接复制粘贴）
3. **调整接口**（符合新标准）
4. **编写测试**
5. **切换调用方**

**预计时间**: 1-2天

**示例**:

```python
# 旧Agent
class SimpleAgent:
    def process(self, input_data):
        return {"result": self._do_work(input_data)}

# 新Agent
class SimpleAgent(BaseXiaonaComponent):
    def _initialize(self):
        self._register_capabilities([...])
    
    async def execute(self, context):
        result = self._do_work(context.input_data["user_input"])
        return AgentExecutionResult(
            agent_id=self.agent_id,
            status=AgentStatus.COMPLETED,
            output_data=result,
        )
```

### 场景2: 复杂Agent迁移

**情况**: Agent有很多依赖，使用复杂

**迁移步骤**:

1. **创建适配器**（保持向后兼容）
2. **逐步重构**（分模块迁移）
3. **双轨运行**（新旧并行）
4. **切换流量**（逐步切换）
5. **删除旧代码**

**预计时间**: 3-5天

**示例**:

```python
# 阶段1: 创建适配器
class ComplexAgentAdapter(BaseXiaonaComponent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.old_agent = OldAgent()

# 阶段2: 逐步迁移模块
class ComplexAgent(BaseXiaonaComponent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        # 新模块
        self.new_module = NewModule()
        # 旧模块
        self.old_module = OldModule()
    
    async def execute(self, context):
        # 使用新模块
        if context.config.get("use_new", False):
            return await self._execute_with_new(context)
        else:
            return await self._execute_with_old(context)

# 阶段3: 完全迁移
class ComplexAgent(BaseXiaonaComponent):
    async def execute(self, context):
        # 只使用新模块
        return await self._execute_with_new(context)
```

### 场景3: 批量Agent迁移

**情况**: 需要迁移多个Agent

**迁移策略**:

1. **优先级排序**（先迁移简单的）
2. **批量测试**（统一测试套件）
3. **分批迁移**（每批2-3个Agent）
4. **统一验证**（确保所有Agent通过测试）

**迁移顺序**:

```
第1批: 简单Agent（1-2天）
  ├─ AgentA
  └─ AgentB

第2批: 中等Agent（2-3天）
  ├─ AgentC
  ├─ AgentD
  └─ AgentE

第3批: 复杂Agent（3-5天）
  ├─ AgentF
  └─ AgentG
```

---

## 验证与测试

### 1. 接口合规性测试

```python
from tests.agents.test_interface_compliance_simple import InterfaceComplianceChecker

def test_migrated_agent_compliance():
    """测试迁移后的Agent是否符合接口标准"""
    agent = MyAgent(agent_id="test")
    
    checker = InterfaceComplianceChecker()
    results = checker.check_agent_instance(agent)
    
    # 打印结果
    print("\n=== 接口合规性检查 ===")
    for result in results["passed"]:
        print(f"✅ {result['check']}: {result['message']}")
    for result in results["failed"]:
        print(f"❌ {result['check']}: {result['message']}")
    
    # 断言：应该没有失败项
    assert len(results["failed"]) == 0
```

### 2. 功能对比测试

```python
@pytest.mark.asyncio
async def test_functional_parity():
    """测试新旧Agent功能一致性"""
    # 旧Agent
    old_agent = OldAgent()
    old_input = {"input": "test"}
    old_result = old_agent.process(old_input)
    
    # 新Agent
    new_agent = MyAgent(agent_id="test")
    context = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_001",
        input_data={"user_input": "test"},
        config={},
        metadata={},
    )
    new_result = await new_agent.execute(context)
    
    # 验证结果一致
    assert old_result == new_result.output_data
```

### 3. 性能对比测试

```python
@pytest.mark.asyncio
async def test_performance_comparison():
    """测试新旧Agent性能"""
    import time
    
    # 旧Agent
    old_agent = OldAgent()
    start = time.time()
    old_result = old_agent.process({"input": "test"})
    old_time = time.time() - start
    
    # 新Agent
    new_agent = MyAgent(agent_id="test")
    context = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_001",
        input_data={"user_input": "test"},
        config={},
        metadata={},
    )
    start = time.time()
    new_result = await new_agent.execute(context)
    new_time = time.time() - start
    
    # 性能应该在合理范围内
    assert new_time < old_time * 2  # 新Agent不应该比旧Agent慢2倍以上
    
    print(f"\n性能对比:")
    print(f"旧Agent: {old_time:.2f}秒")
    print(f"新Agent: {new_time:.2f}秒")
```

### 4. 运行完整测试套件

```bash
# 运行所有测试
pytest tests/agents/test_my_agent.py -v

# 生成覆盖率报告
pytest tests/agents/test_my_agent.py --cov=core.agents.my_agent --cov-report=html

# 检查测试覆盖率
# 应该 > 80%
```

---

## 回滚计划

### 触发条件

如果出现以下情况，考虑回滚：

- ❌ 测试失败率 > 20%
- ❌ 性能下降 > 50%
- ❌ 功能回归（原有功能失效）
- ❌ 严重错误（影响生产环境）

### 回滚步骤

1. **立即回滚代码**
   ```bash
   # 切换回旧分支
   git checkout main
   
   # 删除迁移分支
   git branch -D feature/migrate-to-unified-interface
   ```

2. **恢复备份文件**
   ```bash
   # 恢复备份
   cp .backup/before_migration/old_agent.py core/agents/
   cp .backup/before_migration/test_old_agent.py tests/agents/
   ```

3. **验证恢复**
   ```bash
   # 运行测试
   pytest tests/agents/test_old_agent.py -v
   
   # 检查功能
   python -c "
   from core.agents.old_agent import OldAgent
   agent = OldAgent()
   result = agent.process({'input': 'test'})
   print('OK')
   "
   ```

4. **分析失败原因**
   - 收集错误日志
   - 分析失败原因
   - 制定修复计划

5. **重新迁移**
   - 基于失败原因调整迁移策略
   - 重新执行迁移步骤

---

## 常见问题

### Q1: 迁移会影响性能吗？

**A**: 可能会有轻微影响，但通常可以忽略：

**原因**:
- 新接口增加了封装层
- 异步调用可能有额外开销

**优化**:
- ✅ 使用高效的序列化
- ✅ 减少不必要的数据转换
- ✅ 使用连接池和缓存

**数据**:
```
新接口通常比旧接口慢5-10%，
但这个差异通常在实际应用中不可察觉。
```

### Q2: 如何保证向后兼容？

**A**: 使用适配器模式：

```python
class BackwardCompatibleAgent(BaseXiaonaComponent):
    """向后兼容的Agent"""
    
    async def execute(self, context: AgentExecutionContext):
        # 检查是否使用旧接口
        if context.metadata.get("use_legacy_interface", False):
            return await self._execute_legacy(context)
        else:
            return await self._execute_new(context)
```

### Q3: 迁移需要多长时间？

**A**: 取决于Agent复杂度：

| 复杂度 | Agent数量 | 预计时间 |
|--------|---------|---------|
| **低** | 1-2个 | 1-2天 |
| **中** | 3-5个 | 3-5天 |
| **高** | 6+个 | 1-2周 |

### Q4: 如何验证迁移成功？

**A**: 三步验证：

1. **接口合规性检查** - 确保符合新标准
2. **功能对比测试** - 确保功能一致
3. **性能对比测试** - 确保性能可接受

---

## 附录

### A. 迁移检查清单

**迁移前**:
- [ ] 创建备份
- [ ] 创建Git分支
- [ ] 分析现有Agent
- [ ] 评估迁移复杂度

**迁移中**:
- [ ] 创建适配器（如需要）
- [ ] 重构核心逻辑
- [ ] 更新调用方
- [ ] 编写测试

**迁移后**:
- [ ] 接口合规性检查
- [ ] 功能对比测试
- [ ] 性能对比测试
- [ ] 运行完整测试套件

### B. 相关文档

- [统一Agent接口标准](../design/UNIFIED_AGENT_INTERFACE_STANDARD.md)
- [Agent接口实现指南](AGENT_INTERFACE_IMPLEMENTATION_GUIDE.md)
- [接口合规性检查清单](AGENT_INTERFACE_COMPLIANCE_CHECKLIST.md)

### C. 迁移示例

- [RetrieverAgent迁移示例](../../core/agents/xiaona/retriever_agent.py)
- [AnalyzerAgent迁移示例](../../core/agents/xiaona/analyzer_agent.py)

---

**祝你迁移顺利！** 🎉

如有问题，请查阅完整文档或提交Issue。
