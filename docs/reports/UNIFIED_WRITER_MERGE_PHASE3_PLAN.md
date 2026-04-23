# 阶段3执行计划 - 统一入口创建

> **准备时间**: 2026-04-23 16:30
> **依赖**: 阶段2完成（4个模块实现完毕）

---

## 🎯 阶段3目标

创建`unified_patent_writer.py`作为统一入口，整合4个模块的13个能力。

---

## 🏗️ 架构设计

### 文件结构

```
core/agents/xiaona/
└── unified_patent_writer.py    # 主文件（约500-600行）
```

### 类设计

```python
class UnifiedPatentWriter(BaseXiaonaComponent):
    """
    统一撰写代理 - 小娜撰写大师
    
    整合所有撰写能力：
    - 申请撰写（7个能力）
    - 答复撰写（2个能力）
    - 流程编排（2个能力）
    - 辅助工具（3个能力）
    """
    
    def __init__(self, agent_id: str = "unified_patent_writer"):
        super().__init__(agent_id)
        
        # 初始化4个子模块
        self.drafting_module = DraftingModule()
        self.response_module = ResponseModule()
        self.orchestration_module = OrchestrationModule()
        self.utility_module = UtilityModule()
    
    def _initialize(self) -> None:
        """注册13个核心能力"""
        capabilities = [
            # 模块1: 申请撰写（7个）
            {
                "name": "analyze_disclosure",
                "description": "分析技术交底书",
                "module": "drafting",
                "method": "analyze_disclosure"
            },
            {
                "name": "assess_patentability",
                "description": "评估可专利性",
                "module": "drafting",
                "method": "assess_patentability"
            },
            {
                "name": "draft_specification",
                "description": "撰写说明书",
                "module": "drafting",
                "method": "draft_specification"
            },
            {
                "name": "draft_claims",
                "description": "撰写权利要求书",
                "module": "drafting",
                "method": "draft_claims"
            },
            {
                "name": "optimize_protection_scope",
                "description": "优化保护范围",
                "module": "drafting",
                "method": "optimize_protection_scope"
            },
            {
                "name": "review_adequacy",
                "description": "审查充分公开",
                "module": "drafting",
                "method": "review_adequacy"
            },
            {
                "name": "detect_common_errors",
                "description": "检测常见错误",
                "module": "drafting",
                "method": "detect_common_errors"
            },
            
            # 模块2: 答复撰写（2个）
            {
                "name": "draft_office_action_response",
                "description": "审查意见答复",
                "module": "response",
                "method": "draft_office_action_response"
            },
            {
                "name": "draft_invalidation_petition",
                "description": "无效宣告请求书",
                "module": "response",
                "method": "draft_invalidation_petition"
            },
            
            # 模块3: 流程编排（2个）
            {
                "name": "draft_full_application",
                "description": "完整申请流程",
                "module": "orchestration",
                "method": "draft_full_application"
            },
            {
                "name": "orchestrate_response",
                "description": "答复流程编排",
                "module": "orchestration",
                "method": "orchestrate_response"
            },
            
            # 模块4: 辅助工具（3个）
            {
                "name": "format_document",
                "description": "文档格式化",
                "module": "utility",
                "method": "format_document"
            },
            {
                "name": "calculate_quality_score",
                "description": "质量评分",
                "module": "utility",
                "method": "calculate_quality_score"
            },
            {
                "name": "compare_versions",
                "description": "版本对比",
                "module": "utility",
                "method": "compare_versions"
            }
        ]
        
        self._register_capabilities(capabilities)
```

---

## 📋 实现步骤

### 步骤1: 创建基础结构（15分钟）

**任务**:
- 创建`unified_patent_writer.py`文件
- 定义类结构
- 导入4个模块
- 实现`__init__`方法

**验证**:
- 文件创建成功
- 导入无错误
- 类定义完整

### 步骤2: 实现路由逻辑（30分钟）

**任务**:
- 实现`execute()`方法
- 根据task_type路由到对应模块
- 实现错误处理

```python
async def execute(self, context) -> AgentExecutionResult:
    """统一执行入口"""
    try:
        # 验证输入
        if not self.validate_input(context):
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                output_data=None,
                error_message="输入验证失败"
            )
        
        # 获取任务类型
        task_type = context.config.get("task_type")
        
        # 路由到对应模块
        if task_type in ["analyze_disclosure", "assess_patentability", 
                         "draft_specification", "draft_claims",
                         "optimize_protection_scope", "review_adequacy", 
                         "detect_common_errors"]:
            # 路由到drafting_module
            result = await self._route_to_drafting_module(task_type, context)
            
        elif task_type in ["draft_office_action_response", 
                           "draft_invalidation_petition"]:
            # 路由到response_module
            result = await self._route_to_response_module(task_type, context)
            
        elif task_type in ["draft_full_application", "orchestrate_response"]:
            # 路由到orchestration_module
            result = await self._route_to_orchestration_module(task_type, context)
            
        elif task_type in ["format_document", "calculate_quality_score", 
                           "compare_versions"]:
            # 路由到utility_module
            result = await self._route_to_utility_module(task_type, context)
            
        else:
            # 未知任务类型
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                output_data=None,
                error_message=f"未知任务类型: {task_type}"
            )
        
        return result
        
    except Exception as e:
        self.logger.exception(f"执行任务失败: {e}")
        return AgentExecutionResult(
            agent_id=self.agent_id,
            status=AgentStatus.ERROR,
            output_data=None,
            error_message=str(e)
        )
```

**验证**:
- 路由逻辑正确
- 错误处理完整
- 所有13个task_type可路由

### 步骤3: 实现模块路由方法（15分钟）

```python
async def _route_to_drafting_module(self, task_type: str, context):
    """路由到撰写模块"""
    method = getattr(self.drafting_module, task_type)
    return await method(context.input_data)

async def _route_to_response_module(self, task_type: str, context):
    """路由到答复模块"""
    method = getattr(self.response_module, task_type.replace("draft_", ""))
    return await method(context.input_data)

async def _route_to_orchestration_module(self, task_type: str, context):
    """路由到编排模块"""
    method = getattr(self.orchestration_module, task_type)
    return await method(context.input_data)

async def _route_to_utility_module(self, task_type: str, context):
    """路由到工具模块"""
    method = getattr(self.utility_module, task_type)
    return await method(context.input_data)
```

**验证**:
- 所有路由方法实现
- 方法调用正确

---

## 👥 团队配置

### 新增Teammates（1个）

| 成员 | 角色 | 任务 | 预计时间 |
|------|------|------|---------|
| unified-entry-builder | 统一入口构建师 | 创建unified_patent_writer.py | 60分钟 |

---

## 📝 任务清单

### 任务1: 创建基础结构
- [ ] 创建`unified_patent_writer.py`文件
- [ ] 定义`UnifiedPatentWriter`类
- [ ] 导入4个模块
- [ ] 实现`__init__`方法
- [ ] 初始化4个子模块实例

### 任务2: 实现路由逻辑
- [ ] 实现`execute()`主方法
- [ ] 实现`validate_input()`方法
- [ ] 实现4个路由方法
- [ ] 添加错误处理
- [ ] 添加日志记录

### 任务3: 注册能力
- [ ] 注册13个核心能力
- [ ] 添加能力描述
- [ ] 添加输入输出类型
- [ ] 添加预计时间

### 任务4: 集成测试
- [ ] 创建测试文件
- [ ] 测试所有13个能力
- [ ] 测试路由逻辑
- [ ] 测试错误处理

---

## ✅ 完成标准

### 功能完整性
- [ ] 13个核心能力全部可调用
- [ ] 路由逻辑正确
- [ ] 错误处理完整

### 代码质量
- [ ] 无ruff错误
- [ ] 无mypy错误
- [ ] 符合PEP 8规范

### 测试覆盖
- [ ] 13个能力的单元测试
- [ ] 路由逻辑测试
- [ ] 错误处理测试
- [ ] 测试覆盖率>80%

---

## 🚀 启动指令

**条件**: 阶段2全部完成

**启动命令**:
```python
Agent(
    subagent_type="general-purpose",
    name="unified-entry-builder",
    description="创建统一入口unified_patent_writer.py",
    team_name="unified-writer-merge",
    prompt="创建unified_patent_writer.py，整合4个模块的13个能力..."
)
```

---

## ⏱️ 时间估算

| 步骤 | 任务 | 时间 |
|------|------|------|
| 1 | 创建基础结构 | 15分钟 |
| 2 | 实现路由逻辑 | 30分钟 |
| 3 | 实现路由方法 | 15分钟 |
| 4 | 集成测试 | 30分钟 |
| **总计** | **阶段3** | **90分钟** |

---

## 📊 阶段3完成后

### 输出文件
```
core/agents/xiaona/
└── unified_patent_writer.py    ✅ 创建（约500-600行）
```

### 测试文件
```
tests/agents/xiaona/
└── test_unified_patent_writer.py    ✅ 创建
```

### 下一步
- 启动阶段4：创建向后兼容适配器
- 更新agent_registry.json配置

---

**准备就绪**: 等待阶段2完成通知
**预计完成**: T0 + 90分钟
