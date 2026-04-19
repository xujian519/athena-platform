# Task Tool 使用示例

**版本**: v1.0.0
**创建日期**: 2026-04-05
**作者**: Agent-3 (domain-adapter-tester)

---

## 📋 概述

本目录包含Task Tool系统的完整使用示例,帮助开发者快速上手和理解系统功能。

### 示例列表

| 示例 | 文件 | 描述 | 难度 |
|------|------|------|------|
| 示例1 | `examples.py - example_1_basic_task_execution()` | 基础任务执行 | ⭐ |
| 示例2 | `examples.py - example_2_background_task()` | 异步后台任务 | ⭐⭐ |
| 示例3 | `examples.py - example_3_model_mapping()` | 模型选择和映射 | ⭐ |
| 示例4 | `examples.py - example_4_patent_agents()` | 专利代理类型使用 | ⭐⭐ |
| 示例5 | `examples.py - example_5_workflow_integration()` | 工作流集成 | ⭐⭐⭐ |
| 示例6 | `examples.py - example_6_error_handling()` | 错误处理和重试 | ⭐⭐ |
| 示例7 | `examples.py - example_7_task_monitoring()` | 任务状态监控 | ⭐⭐⭐ |
| 示例8 | `examples.py - example_8_resource_management()` | 资源管理 | ⭐⭐⭐ |

---

## 🚀 快速开始

### 1. 环境准备

确保已安装所有依赖:

```bash
cd /Users/xujian/Athena工作平台
pip install -r requirements.txt
```

### 2. 运行示例

运行单个示例:

```bash
python3 docs/examples/task_tool/examples.py
```

程序会显示所有可用示例,你可以选择运行其中一个:

```
╔══════════════════════════════════════════════════════════╗
║                    Task Tool 使用示例集                    ║
╚════════════════════════════════════════════════════════╝

可用示例:
  1. 基础任务执行
  2. 异步后台任务
  3. 模型选择和映射
  4. 专利代理类型使用
  5. 工作流集成
  6. 错误处理和重试
  7. 任务状态监控
  8. 资源管理

选择要运行的示例 (1-8, 或按Enter运行所有):
```

---

## 📖 详细说明

### 示例1: 基础任务执行

**文件**: `examples.py` - `example_1_basic_task_execution()`

**描述**: 演示TaskTool的基本使用方法

**内容**:
- 创建TaskTool实例
- 执行简单任务
- 获取任务结果

**输出**:
```
============================================================
示例1: 基础任务执行
============================================================

执行任务: 分析专利CN202310123456.7...

✅ 任务执行完成!
任务ID: 550e8400-e29b-41d4-a716-446655440000
状态: completed
代理ID: analysis-agent-12345678
使用模型: task

============================================================
```

**运行**:
```python
from docs.examples.task_tool import examples

examples.example_1_basic_task_execution()
```

### 示例2: 异步后台任务

**文件**: `examples.py` - `example_2_background_task()`

**描述**: 演示后台任务的使用

**内容**:
- 提交后台任务
- 查询任务状态
- 等待任务完成

**运行**:
```python
from docs.examples.task_tool import examples

examples.example_2_background_task()
```

### 示例3: 模型选择和映射

**文件**: `examples.py` - `example_3_model_mapping()`

**描述**: 演示ModelMapper的使用

**内容**:
- 创建ModelMapper实例
- 映射模型名称
- 获取模型配置
- 获取可用模型列表

**运行**:
```python
from docs.examples.task_tool import examples

examples.example_3_model_mapping()
```

### 示例4: 专利代理类型使用

**文件**: `examples.py` - `example_4_patent_agents()`

**描述**: 演示4种专利代理类型的使用

**内容**:
- patent-analyst: 专利分析师 (使用sonnet模型)
- patent-searcher: 专利检索专家 (使用haiku模型)
- legal-researcher: 法律研究员 (使用opus模型)
- patent-drafter: 专利撰写专家 (使用opus模型)

**运行**:
```python
from docs.examples.task_tool import examples

examples.example_4_patent_agents()
```

### 示例5: 工作流集成

**文件**: `examples.py` - `example_5_workflow_integration()`

**描述**: 演示工作流的完整使用流程

**内容**:
- AnalysisWorkflow: 专利分析工作流
- SearchWorkflow: 专利检索工作流
- LegalWorkflow: 法律研究工作流

**注意**: 工作流实现将在T3-3, T3-4, T3-5中完成

**运行**:
```python
from docs.examples.task_tool import examples

examples.example_5_workflow_integration()
```

### 示例6: 错误处理和重试

**文件**: `examples.py` - `example_6_error_handling()`

**描述**: 演示错误处理和重试机制

**内容**:
- 输入验证错误
- 任务执行错误
- 超时处理
- 重试机制

**运行**:
```python
from docs.examples.task_tool import examples

examples.example_6_error_handling()
```

### 示例7: 任务状态监控

**文件**: `examples.py` - `example_7_task_monitoring()`

**描述**: 演示任务状态的持续监控

**内容**:
- 定期查询任务状态
- 状态变化通知
- 完成后处理

**运行**:
```python
from docs.examples.task_tool import examples

examples.example_7_task_monitoring()
```

### 示例8: 资源管理

**文件**: `examples.py` - `example_8_resource_management()`

**描述**: 演示正确的资源管理

**内容**:
- 使用上下文管理器
- 及时释放资源
- 并发控制

**运行**:
```python
from docs.examples.task_tool import examples

examples.example_8_resource_management()
```

---

## 💡 最佳实践

### 1. 使用上下文管理器

**推荐**:
```python
with BackgroundTaskManager(max_workers=10) as manager:
    # 提交任务
    task = manager.submit(func=my_task)
    # ... 其他操作
# 管理器自动关闭
```

**不推荐**:
```python
manager = BackgroundTaskManager(max_workers=10)
try:
    task = manager.submit(func=my_task)
    # ... 其他操作
finally:
    manager.shutdown()  # 容易忘记
```

### 2. 模型选择原则

- **快速任务**: 使用`haiku`模型
- **标准任务**: 使用`sonnet`模型
- **复杂任务**: 使用`opus`模型

### 3. 错误处理

```python
try:
    result = task_tool.execute(
        prompt="执行任务",
        tools=["tool1", "tool2"],
    )
except ValueError as e:
    print(f"输入验证错误: {e}")
except RuntimeError as e:
    print(f"运行时错误: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

### 4. 异步任务使用场景

**适合异步**:
- 长时间运行的任务 (>30秒)
- 需要立即返回的场景
- 需要高并发的场景

**适合同步**:
- 快速执行的任务 (<10秒)
- 需要立即获取结果的场景
- 串行依赖的任务

---

## 🔧 故障排除

### 问题1: 找不到模块

**错误信息**:
```
ModuleNotFoundError: No module named 'core.agents.task_tool'
```

**解决方案**:
```bash
export PYTHONPATH=/Users/xujian/Athena工作平台:$PYTHONPATH
```

### 问题2: 配置文件不存在

**错误信息**:
```
FileNotFoundError: config/patent/patent_agents.yaml
```

**解决方案**:
确保配置文件存在:
```bash
ls -la config/patent/patent_agents.yaml
```

### 问题3: 任务超时

**错误信息**:
```
TimeoutError: Task xxx timed out after 60 seconds
```

**解决方案**:
增加超时时间或优化任务:
```python
result = task_manager.wait_get_task(
    task_id=task_id,
    timeout=120,  # 增加超时时间
)
```

---

## 📚 相关文档

- API文档: `/docs/api/task_tool/API.md`
- 专利领域需求分析: `/docs/reports/task-tool-system-implementation/domain-analysis/T3-1-patent-domain-requirements-analysis.md`
- 代理类型配置: `/config/patent/patent_agents.yaml`

---

## 🤝 贡献

如果你发现了问题或有改进建议,欢迎提交Issue或Pull Request。

---

**示例版本**: v1.0.0
**最后更新**: 2026-04-05
**维护者**: Agent-3 (domain-adapter-tester)
