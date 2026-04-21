# Agent示例库

> **目录**: `examples/agents/`
> **说明**: 包含各种Agent示例，帮助开发者快速学习Agent开发

---

## 示例列表

| 示例 | 文件 | 描述 | 难度 |
|------|------|------|------|
| HelloAgent | hello_agent_example.py | 最简单的Agent示例 | 入门 |
| ChatAgent | chat_agent_example.py | 使用LLM的Agent | 中级 |
| ToolAgent | tool_agent_example.py | 使用工具的Agent | 中级 |
| AnalyzerAgent | analyzer_agent_example.py | 分析型Agent | 高级 |
| WorkflowAgent | workflow_agent_example.py | 工作流Agent | 高级 |

---

## 使用示例

### HelloAgent - 最简单的Agent

```bash
# 运行示例
python examples/agents/hello_agent_example.py
```

**功能**: 返回问候语
**学习点**:
- Agent基本结构
- 能力注册
- execute方法实现

### ChatAgent - 使用LLM

```bash
# 运行示例
python examples/agents/chat_agent_example.py
```

**功能**: 使用LLM进行智能对话
**学习点**:
- LLM初始化和调用
- 提示词构建
- 响应解析

---

## 快速开始

### 1. 查看示例代码

```bash
# 查看HelloAgent
cat examples/agents/hello_agent_example.py

# 查看ChatAgent
cat examples/agents/chat_agent_example.py
```

### 2. 运行示例

```bash
# 运行HelloAgent
python examples/agents/hello_agent_example.py

# 运行ChatAgent
python examples/agents/chat_agent_example.py
```

### 3. 创建你自己的Agent

```bash
# 使用脚手架工具
python -m tools.agent_scaffold.agent_scaffold create MyAgent

# 或
python tools/agent_scaffold/agent_scaffold.py create MyAgent
```

---

## 示例结构

每个示例都包含：

1. **Agent类定义**
   - 继承自BaseXiaonaComponent
   - 实现_initialize、execute、get_system_prompt

2. **能力注册**
   - 使用_register_capabilities注册能力

3. **测试入口**
   - main()函数用于测试

4. **便捷函数**
   - create_xxx_agent()函数用于快速创建实例

---

## 开发指南

### 从示例学习

1. **阅读代码**: 理解Agent的结构和接口
2. **运行示例**: 观察Agent的行为
3. **修改代码**: 尝试添加新功能
4. **创建新Agent**: 使用脚手架工具

### 最佳实践

- ✅ 继承BaseXiaonaComponent
- ✅ 在_initialize中注册能力
- ✅ 在execute中返回AgentExecutionResult
- ✅ 使用logger记录日志
- ✅ 处理所有异常

### 常见错误

- ❌ 忘记注册能力
- ❌ 返回异常而非结果
- ❌ 同步调用异步方法
- ❌ 缺少输入验证

---

## 相关文档

- [统一Agent接口标准](../../docs/design/UNIFIED_AGENT_INTERFACE_STANDARD.md)
- [Agent实现指南](../../docs/guides/AGENT_INTERFACE_IMPLEMENTATION_GUIDE.md)
- [Agent开发FAQ](../../docs/guides/AGENT_DEVELOPMENT_FAQ.md)

---

**最后更新**: 2026-04-21
