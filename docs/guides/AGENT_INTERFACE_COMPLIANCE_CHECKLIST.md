# Agent接口合规性检查清单

> **版本**: v1.0
> **日期**: 2026-04-21
> **用途**: 确保Agent实现符合统一接口标准

---

## 📋 使用说明

本清单用于检查Agent实现是否符合统一Agent接口标准。

**检查方式**:
- ✅ 人工检查：代码Review时使用
- 🧪 自动检查：使用自动化测试工具
- 📊 CI/CD集成：集成到持续集成流程

---

## Part 1: 基础要求（必须全部满足）

### 1.1 类定义

- [ ] **继承自BaseXiaonaComponent**
  ```python
  class MyAgent(BaseXiaonaComponent):
      pass
  ```

- [ ] **有明确的agent_id**
  ```python
  agent = MyAgent(agent_id="my_agent_001")
  ```

- [ ] **有适当的文档字符串**
  ```python
  class MyAgent(BaseXiaonaComponent):
      """
      我的Agent

      负责XXX任务的Agent。
      """
  ```

### 1.2 必需方法实现

- [ ] **实现了_initialize()方法**
  ```python
  def _initialize(self) -> None:
      """Agent初始化钩子"""
      pass
  ```

- [ ] **实现了execute()方法**
  ```python
  async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
      """执行Agent任务"""
      pass
  ```

- [ ] **实现了get_system_prompt()方法**
  ```python
  def get_system_prompt(self) -> str:
      """获取系统提示词"""
      return "你是..."
  ```

### 1.3 能力注册

- [ ] **在_initialize()中注册了至少一个能力**
  ```python
  def _initialize(self) -> None:
      self._register_capabilities([
          AgentCapability(...),
      ])
  ```

- [ ] **能力描述完整**
  - [ ] name: 能力名称（小写+下划线）
  - [ ] description: 清晰的能力描述
  - [ ] input_types: 输入类型列表
  - [ ] output_types: 输出类型列表
  - [ ] estimated_time: 合理的时间估算

---

## Part 2: 代码质量（应该满足）

### 2.1 类型注解

- [ ] **所有公共方法有类型注解**
  ```python
  async def execute(
      self,
      context: AgentExecutionContext
  ) -> AgentExecutionResult:
      pass
  ```

- [ ] **所有参数有类型注解**
  ```python
  def my_method(
      self,
      param1: str,
      param2: Optional[int] = None
  ) -> Dict[str, Any]:
      pass
  ```

### 2.2 文档字符串

- [ ] **类有文档字符串**
  ```python
  class MyAgent(BaseXiaonaComponent):
      """
      我的Agent

      负责XXX任务的Agent。

      Attributes:
          config: 配置参数
      """
  ```

- [ ] **公共方法有文档字符串**
  ```python
  async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
      """
      执行Agent任务

      Args:
          context: 执行上下文

      Returns:
          执行结果
      """
      pass
  ```

- [ ] **文档字符串遵循Google风格**
  - 使用Args、Returns、Raises、Examples等章节

### 2.3 错误处理

- [ ] **execute()方法不抛出异常**
  ```python
  async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
      try:
          result = await self._do_work(context)
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
  ```

- [ ] **错误信息清晰明确**
  ```python
  error_message = f"检索失败: 数据库连接超时（{timeout}秒）"
  ```

- [ ] **记录了异常日志**
  ```python
  self.logger.exception(f"任务执行失败: {context.task_id}")
  ```

### 2.4 日志记录

- [ ] **使用了logger而非print**
  ```python
  self.logger.info("开始执行任务")
  # 不要使用: print("开始执行任务")
  ```

- [ ] **关键步骤有日志记录**
  - [ ] 任务开始: `logger.info(f"开始执行任务: {task_id}")`
  - [ ] 任务完成: `logger.info(f"任务完成: {task_id}")`
  - [ ] 任务失败: `logger.error(f"任务失败: {task_id}")`
  - [ ] 警告信息: `logger.warning(...)`

- [ ] **日志级别使用正确**
  - DEBUG: 调试信息
  - INFO: 正常流程
  - WARNING: 警告信息
  - ERROR: 错误信息
  - EXCEPTION: 异常信息

---

## Part 3: 测试要求（必须满足）

### 3.1 单元测试

- [ ] **测试覆盖率 > 80%**
  ```bash
  pytest tests/agents/test_my_agent.py --cov=core.agents.my_agent --cov-report=html
  ```

- [ ] **测试正常流程**
  ```python
  async def test_execute_success():
      agent = MyAgent(agent_id="test_agent")
      context = AgentExecutionContext(...)
      result = await agent.execute(context)
      assert result.status == AgentStatus.COMPLETED
  ```

- [ ] **测试异常流程**
  ```python
  async def test_execute_failure():
      agent = MyAgent(agent_id="test_agent")
      context = AgentExecutionContext(...)
      result = await agent.execute(context)
      assert result.status == AgentStatus.ERROR
      assert result.error_message is not None
  ```

- [ ] **测试边界情况**
  - 空输入
  - 超大输入
  - 特殊字符
  - 并发执行

### 3.2 集成测试

- [ ] **测试与其他Agent的协作**
  ```python
  async def test_agent_collaboration():
      retriever = RetrieverAgent(agent_id="retriever")
      analyzer = AnalyzerAgent(agent_id="analyzer")

      # 检索
      context1 = AgentExecutionContext(...)
      result1 = await retriever.execute(context1)

      # 分析（使用检索结果）
      context2 = AgentExecutionContext(
          input_data={
              "previous_results": {
                  "retriever": result1.output_data
              }
          }
      )
      result2 = await analyzer.execute(context2)

      assert result2.status == AgentStatus.COMPLETED
  ```

### 3.3 性能测试

- [ ] **测试执行时间**
  ```python
  async def test_execution_time():
      agent = MyAgent(agent_id="test_agent")
      context = AgentExecutionContext(...)

      start = time.time()
      result = await agent.execute(context)
      execution_time = time.time() - start

      assert execution_time < 10.0  # 应该在10秒内完成
      assert result.execution_time > 0
  ```

- [ ] **测试内存使用**
  ```python
  def test_memory_usage():
      import tracemalloc
      tracemalloc.start()

      agent = MyAgent(agent_id="test_agent")
      # ... 执行任务

      current, peak = tracemalloc.get_traced_memory()
      assert peak < 100 * 1024 * 1024  # 峰值内存 < 100MB
  ```

---

## Part 4: 安全要求（应该满足）

### 4.1 输入验证

- [ ] **验证了session_id**
  ```python
  if not context.session_id:
      self.logger.error("缺少session_id")
      return AgentExecutionResult(...)
  ```

- [ ] **验证了task_id**
  ```python
  if not context.task_id:
      self.logger.error("缺少task_id")
      return AgentExecutionResult(...)
  ```

- [ ] **验证了input_data**
  ```python
  if not isinstance(context.input_data, dict):
      self.logger.error("input_data必须是字典")
      return AgentExecutionResult(...)
  ```

### 4.2 敏感信息保护

- [ ] **不在日志中输出敏感信息**
  ```python
  # ❌ 错误
  self.logger.info(f"API密钥: {api_key}")

  # ✅ 正确
  self.logger.info(f"使用API密钥: {api_key[:8]}...")
  ```

- [ ] **不在错误消息中暴露内部信息**
  ```python
  # ❌ 错误
  error_message = f"数据库连接失败: {connection_string}"

  # ✅ 正确
  error_message = "数据库连接失败，请检查配置"
  ```

### 4.3 权限控制

- [ ] **检查了用户权限**（如果需要）
  ```python
  user_role = context.metadata.get("user_role", "guest")
  if user_role == "guest" and self.requires_premium():
      return AgentExecutionResult(
          status=AgentStatus.ERROR,
          error_message="该功能需要Premium权限",
      )
  ```

---

## Part 5: 性能要求（应该满足）

### 5.1 异步执行

- [ ] **execute()方法是异步的**
  ```python
  async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
      pass
  ```

- [ ] **IO操作使用异步**
  ```python
  # ✅ 使用异步
  result = await async_function()

  # ❌ 不要阻塞
  result = blocking_function()
  ```

- [ ] **并行执行独立任务**
  ```python
  # 并行执行多个独立任务
  results = await asyncio.gather(
      self._task1(),
      self._task2(),
      self._task3(),
  )
  ```

### 5.2 资源管理

- [ ] **及时释放资源**
  ```python
  async def execute(self, context: AgentExecutionContext):
      # 使用上下文管理器
      async with self.db_pool.acquire() as conn:
          result = await conn.fetch(query)
      # 资源自动释放
  ```

- [ ] **限制了并发数**
  ```python
  # 使用信号量限制并发
  semaphore = asyncio.Semaphore(10)

  async def _process_item(self, item):
      async with semaphore:
          return await self._do_work(item)
  ```

---

## Part 6: 文档要求（应该满足）

### 6.1 README文档

- [ ] **有Agent的README文档**
  - Agent功能说明
  - 使用示例
  - 配置参数说明
  - 依赖列表

### 6.2 API文档

- [ ] **公共方法有完整的API文档**
  - 方法签名
  - 参数说明
  - 返回值说明
  - 异常说明
  - 使用示例

### 6.3 示例代码

- [ ] **提供了可运行的示例**
  ```python
  # examples/my_agent_example.py
  async def main():
      agent = MyAgent(agent_id="example_agent")
      context = AgentExecutionContext(...)
      result = await agent.execute(context)
      print(result)
  ```

---

## 自动化检查工具

### pytest插件

```python
# tests/agents/conftest.py
import pytest
from core.agents.xiaona.base_component import BaseXiaonaComponent

def pytest_collection_modifyitems(config, items):
    """自动收集并检查所有Agent"""
    for item in items:
        # 检查是否是Agent测试
        if hasattr(item, "obj"):
            obj = item.obj
            if isinstance(obj, type) and issubclass(obj, BaseXiaonaComponent):
                # 添加接口合规性检查
                item.add_marker(
                    pytest.mark.compliance(
                        agent_class=obj
                    )
                )
```

### 自动化检查脚本

```python
# scripts/check_agent_compliance.py
import ast
import sys
from pathlib import Path

def check_agent_compliance(agent_file: Path):
    """检查Agent文件是否符合接口标准"""
    with open(agent_file) as f:
        tree = ast.parse(f.read())

    # 检查是否继承自BaseXiaonaComponent
    # 检查是否实现了必需方法
    # 检查是否有类型注解
    # ...

    return compliance_report

if __name__ == "__main__":
    agent_files = Path("core/agents").rglob("*_agent.py")
    for agent_file in agent_files:
        report = check_agent_compliance(agent_file)
        print(report)
```

---

## 检查清单使用示例

### 人工检查

```bash
# 打印检查清单
cat docs/guides/AGENT_INTERFACE_COMPLIANCE_CHECKLIST.md

# 逐项检查Agent实现
python -m core.agents.xiaona.retiever_agent
```

### 自动化检查

```bash
# 运行接口合规性测试
pytest tests/agents/test_interface_compliance.py -v

# 检查特定Agent
pytest tests/agents/test_retriever_agent.py --compliance -v

# 生成合规性报告
pytest tests/agents/ --compliance-report=compliance_report.html
```

### CI/CD集成

```yaml
# .github/workflows/agent_compliance.yml
name: Agent Compliance Check

on: [push, pull_request]

jobs:
  compliance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run compliance checks
        run: |
          pytest tests/agents/ --compliance --compliance-report=report.html
      - name: Upload report
        uses: actions/upload-artifact@v2
        with:
          name: compliance-report
          path: report.html
```

---

## 附录

### A. 常见问题

**Q1: 如何快速检查一个Agent是否符合标准？**

A: 运行以下命令：
```bash
pytest tests/agents/test_<agent_name>.py --compliance -v
```

**Q2: 如果检查失败怎么办？**

A: 查看检查报告，根据失败原因修改代码，然后重新检查。

**Q3: 可以跳过某些检查项吗？**

A: 可以，但不推荐。如果必须跳过，请说明原因。

### B. 相关文档

- [统一Agent接口标准](../design/UNIFIED_AGENT_INTERFACE_STANDARD.md)
- [Agent通信协议规范](../design/AGENT_COMMUNICATION_PROTOCOL_SPEC.md)
- [接口实现指南](AGENT_INTERFACE_IMPLEMENTATION_GUIDE.md)

---

**文档维护**: 本文档应随接口标准演进持续更新。

**反馈渠道**: 如有问题或建议，请提交Issue或PR。
