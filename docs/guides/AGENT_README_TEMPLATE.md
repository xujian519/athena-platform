# Agent README 模板

> **Agent名称**: [Agent Display Name]
> **版本**: [版本号]
> **作者**: [作者名称]
> **最后更新**: [日期]

---

## 📖 简介

[Agent简介 - 1-2句话描述Agent的核心功能和用途]

## ✨ 核心功能

- **[功能1]**: [描述]
- **[功能2]**: [描述]
- **[功能3]**: [描述]

## 🎯 能力列表

| 能力名称 | 描述 | 输入类型 | 输出类型 |
|---------|------|---------|---------|
| [capability_1] | [描述] | [类型] | [类型] |
| [capability_2] | [描述] | [类型] | [类型] |

## 📦 安装

### 前置要求

- Python 3.11+
- [依赖1]
- [依赖2]

### 安装步骤

```bash
# 克隆仓库
git clone [repository_url]

# 安装依赖
pip install -r requirements.txt
```

## ⚙️ 配置

### 环境变量

```bash
# .env 文件
export [CONFIG_VAR_1]=[value]
export [CONFIG_VAR_2]=[value]
```

### 配置参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| [param_1] | [type] | [default] | [描述] |
| [param_2] | [type] | [default] | [描述] |

## 🚀 使用方法

### 基础使用

```python
from core.agents.[agent_module] import [AgentClass]

# 创建Agent实例
agent = [AgentClass]()

# 执行Agent
result = await agent.execute(context)
```

### 高级使用

#### 使用特定能力

```python
# 示例代码
```

#### 与其他Agent协作

```python
# 示例代码
```

## 📚 API 文档

### 主要方法

#### `initialize()`

初始化Agent。

**签名**: `def initialize(self) -> None`

**示例**:
```python
agent = [AgentClass]()
agent.initialize()
```

#### `execute()`

执行Agent核心逻辑。

**签名**: `async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult`

**参数**:
- `context` (AgentExecutionContext): 执行上下文

**返回**:
- `AgentExecutionResult`: 执行结果

**示例**:
```python
from core.agents.xiaona.base_component import AgentExecutionContext

context = AgentExecutionContext(
    session_id="session_001",
    task_id="task_001",
    parameters={"query": "test"}
)

result = await agent.execute(context)
```

#### `get_info()`

获取Agent信息。

**签名**: `def get_info(self) -> AgentInfo`

**返回**:
- `AgentInfo`: Agent信息对象

#### `get_capabilities()`

获取Agent能力列表。

**签名**: `def get_capabilities(self) -> List[AgentCapability]`

**返回**:
- `List[AgentCapability]`: 能力列表

## 🔗 依赖项

### Python包

```
[package1]==[version]
[package2]==[version]
```

### 内部依赖

- [dependency1]
- [dependency2]

## ⚠️ 注意事项

1. **[注意事项1]**
2. **[注意事项2]**
3. **[注意事项3]**

## 🧪 测试

```bash
# 运行测试
pytest tests/agents/test_[agent_name].py -v

# 运行测试并查看覆盖率
pytest tests/agents/test_[agent_name].py --cov=[agent_module] --cov-report=html
```

## 📊 性能

| 指标 | 目标值 |
|------|--------|
| 初始化时间 | <100ms (P95) |
| 执行时间 | <5s (P95) |
| 内存占用 | <500MB |

## 🤝 贡献

欢迎贡献！请阅读 [CONTRIBUTING.md] 贡献指南。

## 📝 更新日志

### [版本] - [日期]

#### 新增
- [新增1]
- [新增2]

#### 改进
- [改进1]
- [改进2]

#### 修复
- [修复1]
- [修复2]

## 📄 许可证

[License信息]

## 👥 作者

[Author Name] - [Email]

## 🙏 致谢

- [Athena平台团队]
- [其他贡献者]

---

**文档版本**: [版本]
**最后更新**: [日期]

**相关文档**:
- [Agent接口标准](../../design/UNIFIED_AGENT_INTERFACE_STANDARD.md)
- [Agent开发指南](../../guides/AGENT_INTERFACE_IMPLEMENTATION_GUIDE.md)
- [Agent最佳实践](../../guides/AGENT_INTERFACE_BEST_PRACTICES.md)
