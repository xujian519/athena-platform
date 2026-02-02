# Athena Tools 快速入门指南

> **5分钟上手 Athena 工具系统**

## 前置要求

```bash
# 确保已安装 Python 3.14+
python --version

# 克隆项目
cd /Users/xujian/Athena工作平台

# 安装依赖
pip install -e .
```

---

## 1️⃣ 基础使用：创建和调用工具

### 步骤 1: 定义工具处理函数

```python
from typing import Dict, Any, Optional

async def my_tool_handler(params: Dict[str, Any], context: Optional[Dict[str, Any]]) -> Any:
    """工具处理函数"""
    input_data = params.get("input", "")
    # 处理逻辑
    result = f"处理结果: {input_data}"
    return {"result": result}
```

### 步骤 2: 创建工具定义

```python
from core.tools.base import (
    ToolDefinition, ToolCategory, ToolCapability, ToolPriority
)

tool = ToolDefinition(
    tool_id="my_first_tool",
    name="我的第一个工具",
    category=ToolCategory.CODE_ANALYSIS,
    description="这是一个示例工具",
    capability=ToolCapability(
        input_types=["text"],
        output_types=["result"],
        domains=["all"],
        task_types=["processing"]
    ),
    required_params=["input"],
    optional_params=["option"],
    handler=my_tool_handler,
    timeout=30.0,
    priority=ToolPriority.MEDIUM
)
```

### 步骤 3: 注册并调用工具

```python
import asyncio
from core.tools.tool_call_manager import ToolCallManager, CallStatus

async def main():
    # 创建管理器
    manager = ToolCallManager()

    # 注册工具
    manager.register_tool(tool)

    # 调用工具
    result = await manager.call_tool(
        tool_name="my_first_tool",
        parameters={"input": "Hello Athena!"}
    )

    # 检查结果
    if result.status == CallStatus.SUCCESS:
        print(f"✅ 成功: {result.result}")
    else:
        print(f"❌ 失败: {result.error}")

asyncio.run(main())
```

---

## 2️⃣ 进阶使用：工具选择和策略

### 使用工具注册中心

```python
from core.tools.base import ToolRegistry

# 创建注册中心
registry = ToolRegistry()

# 批量注册工具
registry.register(tool1)
registry.register(tool2)
registry.register(tool3)

# 查找工具
all_tools = registry.list_tools()
code_tools = registry.find_by_category(ToolCategory.CODE_ANALYSIS)

# 获取统计信息
stats = registry.get_statistics()
print(f"总工具数: {stats['total_tools']}")
```

### 智能工具选择

```python
from core.tools.selector import ToolSelector, SelectionStrategy

# 创建选择器
selector = ToolSelector(
    registry=registry,
    strategy=SelectionStrategy.BALANCED  # 平衡策略
)

# 自动选择最适合的工具
tool = await selector.select_tool(
    task_type="analysis",
    domain="patent",
    input_data={"query": "专利搜索"}
)

if tool:
    print(f"推荐工具: {tool.name} (成功率: {tool.performance.success_rate:.2%})")
```

---

## 3️⃣ 高级特性：速率限制和监控

### 启用速率限制

```python
# 创建带速率限制的管理器
manager = ToolCallManager(
    enable_rate_limit=True,
    max_calls_per_minute=100,
    max_history=1000
)

# 调用工具（自动应用速率限制）
for i in range(150):
    result = await manager.call_tool("my_tool", {"input": f"test_{i}"})

    if result.status == CallStatus.FAILED and "速率限制" in result.error:
        print(f"⚠️ 第{i+1}次调用被限流")
        break
```

### 性能监控

```python
# 获取详细统计
stats = manager.get_stats()

print(f"""
📊 工具调用统计:
├─ 总调用数: {stats['total_calls']}
├─ 成功: {stats['successful_calls']}
├─ 失败: {stats['failed_calls']}
├─ 超时: {stats['timeout_calls']}
├─ 被限流: {stats['rate_limited_calls']}
├─ 成功率: {stats['success_rate']:.2%}
├─ 平均执行时间: {stats['avg_execution_time']:.3f}秒
└─ 工具数量: {stats['tool_count']}
""")

# 获取工具性能详情
perf = manager.get_tool_performance("my_tool")
print(f"工具详情:")
print(f"  调用次数: {perf['calls']}")
print(f"  成功率: {perf['successes'] / perf['calls']:.2%}")
print(f"  平均时间: {perf['avg_time']:.3f}秒")
```

---

## 4️⃣ 完整示例：构建专利分析工具

```python
import asyncio
from typing import Dict, Any, Optional
from core.tools.base import (
    ToolDefinition, ToolCategory, ToolCapability,
    ToolRegistry, ToolPriority
)
from core.tools.tool_call_manager import ToolCallManager, CallStatus
from core.tools.selector import ToolSelector, SelectionStrategy

# 1. 定义专利分析处理器
async def patent_analyzer_handler(params: Dict[str, Any], context: Optional[Dict[str, Any]]) -> Any:
    """专利分析处理器"""
    patent_id = params.get("patent_id")
    analysis_type = params.get("analysis_type", "basic")

    # 模拟分析逻辑
    await asyncio.sleep(0.1)

    return {
        "patent_id": patent_id,
        "analysis_type": analysis_type,
        "score": 0.85,
        "recommendation": "高价值专利",
        "key_features": ["创新性强", "市场前景好"]
    }

# 2. 创建工具定义
patent_analyzer = ToolDefinition(
    tool_id="patent_analyzer",
    name="专利分析器",
    category=ToolCategory.CODE_ANALYSIS,
    description="专业的专利价值分析工具",
    capability=ToolCapability(
        input_types=["patent_id"],
        output_types=["analysis_report"],
        domains=["patent", "legal"],
        task_types=["analysis", "evaluation"]
    ),
    required_params=["patent_id"],
    optional_params=["analysis_type", "include_similar"],
    handler=patent_analyzer_handler,
    timeout=60.0,
    priority=ToolPriority.HIGH
)

# 3. 构建工具系统
async def main():
    # 创建注册中心
    registry = ToolRegistry()
    registry.register(patent_analyzer)

    # 创建选择器
    selector = ToolSelector(
        registry=registry,
        strategy=SelectionStrategy.QUALITY
    )

    # 选择最适合的工具
    tool = await selector.select_tool(
        task_type="analysis",
        domain="patent"
    )

    print(f"✅ 选中工具: {tool.name}")

    # 创建调用管理器
    manager = ToolCallManager(
        enable_rate_limit=True,
        max_calls_per_minute=50
    )
    manager.register_tool(tool)

    # 执行分析
    result = await manager.call_tool(
        tool_name="patent_analyzer",
        parameters={
            "patent_id": "CN123456789A",
            "analysis_type": "comprehensive"
        }
    )

    # 处理结果
    if result.status == CallStatus.SUCCESS:
        analysis = result.result
        print(f"""
📊 专利分析结果:
├─ 专利号: {analysis['patent_id']}
├─ 分析类型: {analysis['analysis_type']}
├─ 价值评分: {analysis['score']:.2f}
├─ 建议: {analysis['recommendation']}
└─ 关键特性: {', '.join(analysis['key_features'])}
        """)
    else:
        print(f"❌ 分析失败: {result.error}")

    # 显示性能统计
    stats = manager.get_stats()
    print(f"📈 系统统计: 成功率 {stats['success_rate']:.2%}, "
          f"平均耗时 {stats['avg_execution_time']:.3f}秒")

asyncio.run(main())
```

---

## 5️⃣ 测试你的工具

### 单元测试

```python
import pytest
from core.tools.base import ToolDefinition, ToolCategory

@pytest.mark.asyncio
async def test_my_tool():
    # 创建测试工具
    tool = ToolDefinition(
        tool_id="test_tool",
        name="测试工具",
        category=ToolCategory.CODE_ANALYSIS,
        description="测试"
    )

    # 测试注册
    manager = ToolCallManager()
    manager.register_tool(tool)

    # 测试调用
    result = await manager.call_tool(
        tool_name="test_tool",
        parameters={"input": "test"}
    )

    # 验证结果
    assert result.status == CallStatus.SUCCESS
    assert result.result is not None
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行单元测试
pytest -m unit

# 运行集成测试
pytest -m integration

# 查看覆盖率
pytest --cov=core/tools --cov-report=html
```

---

## 6️⃣ 常见问题

### Q: 如何处理工具执行超时？

```python
# 方案1: 在工具定义中设置超时
tool = ToolDefinition(
    tool_id="slow_tool",
    timeout=120.0  # 2分钟超时
)

# 方案2: 调用时动态设置超时
result = await manager.call_tool(
    tool_name="slow_tool",
    parameters={},
    timeout=60.0  # 1分钟超时
)
```

### Q: 如何实现工具重试？

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def robust_handler(params, context):
    # 会自动重试的处理逻辑
    return await process(params)

tool = ToolDefinition(
    tool_id="robust_tool",
    handler=robust_handler
)
```

### Q: 如何监控工具调用？

```python
# 1. 启用日志
manager = ToolCallManager(
    log_dir="logs/tool_calls"
)

# 2. 查看历史记录
recent_calls = manager.get_recent_calls(limit=10)
for call in recent_calls:
    print(f"{call.timestamp}: {call.tool_name} - {call.status}")

# 3. 查看日志文件
import json
with open("logs/tool_calls/tool_calls_20260125.jsonl") as f:
    for line in f:
        log = json.loads(line)
        print(log)
```

---

## 7️⃣ 下一步

- 📖 阅读完整 [API 参考文档](./tools-api-reference.md)
- 🧪 查看 [测试示例](../../tests/unit/tools/)
- 🔧 探索 [生产工具实现](../../core/tools/production_tool_implementations.py)
- 📊 了解 [性能优化技巧](../../docs/quality/performance-optimization.md)

---

## 获取帮助

- 💬 提交问题: [GitHub Issues](https://github.com/athena-platform/athena/issues)
- 📧 邮件支持: xujian519@gmail.com
- 📚 文档中心: [docs/](../../docs/)

---

**祝您使用愉快！** 🚀
