# Athena通信模块修复检查清单

> 📅 创建时间: 2026-01-25
> 🎯 目标: 全面修复通信模块问题，达到生产级别标准

---

## 📋 修复阶段总览

| 阶段 | 优先级 | 预计工期 | 状态 |
|------|--------|----------|------|
| 阶段1: 安全和稳定性 | P0 | 1-2周 | ⏳ 待启动 |
| 阶段2: 架构优化 | P1 | 3-4周 | ⏳ 待启动 |
| 阶段3: 功能增强 | P2 | 5-8周 | ⏳ 待启动 |

---

## 🔒 阶段1: 安全问题修复（P0）

### 1.1 移除硬编码敏感信息

#### 检查清单

- [ ] **扫描所有硬编码密钥**
  ```bash
  # 扫描命令
  grep -r "API_KEY\|SECRET\|PASSWORD\|TOKEN" core/communication/ core/orchestration/ core/mcp/
  ```

- [ ] **创建环境变量配置文件**
  ```bash
  # 创建 .env.example
  cp .env.example .env.local
  ```

- [ ] **修复文件列表**
  - [ ] `core/orchestration/improved_mcp_client.py:45` - AMAP_API_KEY
  - [ ] `core/orchestration/improved_mcp_client.py:162` - AMAP_API_KEY
  - [ ] `core/orchestration/unified_mcp_manager.py:162` - AMAP_API_KEY

- [ ] **更新文档**
  - [ ] 在 README.md 中说明环境变量配置
  - [ ] 在 .gitignore 中添加 .env.local

#### 验证标准

```bash
# 验证命令（应该返回空结果）
grep -r "4c98d375577d64cfce0d4d0dfee25fb9" core/

# 验证环境变量加载
python -c "import os; print(os.getenv('AMAP_API_KEY'))"
```

### 1.2 修复空的except块

#### 检查清单

- [ ] **扫描所有空的except块**
  ```bash
  grep -rn "except.*:.*pass" core/communication/ core/orchestration/ core/mcp/
  grep -rn "except:$" core/communication/ core/orchestration/ core/mcp/
  ```

- [ ] **修复文件列表**
  - [ ] `core/orchestration/improved_mcp_client.py:138-139` - JSON解析异常
  - [ ] 检查其他可能的空except块

- [ ] **标准异常处理模式**
  ```python
  # ✅ 正确的异常处理
  try:
      # 操作
  except SpecificError as e:
      logger.error(f"描述性错误信息: {e}")
      raise  # 或适当的处理
  except Exception as e:
      logger.error(f"未预期的错误: {e}", exc_info=True)
      raise
  ```

#### 验证标准

```bash
# 扫描确认无空except块（应该返回空）
! grep -rn "except.*:.*pass" core/communication/ core/orchestration/ core/mcp/
! grep -rn "except:$" core/communication/ core/orchestration/ core/mcp/
```

### 1.3 添加输入验证

#### 检查清单

- [ ] **创建验证模块**
  - [ ] `core/communication/utils/validation.py`
  - [ ] 实现消息验证器
  - [ ] 实现参数验证器

- [ ] **添加验证装饰器**
  ```python
  # core/communication/utils/validation.py
  from functools import wraps
  from typing import Type, Any
  import logging

  def validate_message(cls):
      """消息验证装饰器"""
      @wraps(cls)
      def wrapper(message):
          if not isinstance(message, dict):
              raise ValueError("消息必须是字典类型")
          if 'sender_id' not in message:
              raise ValueError("缺少sender_id字段")
          # 更多验证...
          return cls(message)
      return wrapper
  ```

- [ ] **应用验证到所有公共接口**
  - [ ] send_message()
  - [ ] receive_messages()
  - [ ] create_channel()
  - [ ] call_tool()

#### 验证标准

```python
# 测试验证器
def test_message_validation():
    # 有效消息应该通过
    valid_message = {"sender_id": "test", "content": "hello"}
    assert validate(valid_message) is True

    # 无效消息应该抛出异常
    invalid_message = {"sender_id": ""}  # 空sender_id
    with pytest.raises(ValueError):
        validate(invalid_message)
```

---

## 🧹 阶段1: 代码整合（P0）

### 1.4 移除冗余和备份文件

#### 检查清单

- [ ] **识别需要删除的文件**
  ```bash
  # 查找备份文件
  find core/communication/ -name "*backup*" -o -name "*.bak" -o -name "*.bak2"

  # 查找重复文件
  ls -la core/communication/*.py | grep enhanced
  ls -la core/communication/*.py | grep optimized
  ```

- [ ] **文件删除清单**
  - [ ] `core/communication/enhanced_communication_module_backup.py`
  - [ ] `core/communication/logging_comm.py.bak2`
  - [ ] 其他 .bak 文件

- [ ] **归档而非直接删除**
  ```bash
  # 创建归档目录
  mkdir -p archive/communication

  # 移动文件到归档
  mv core/communication/*backup* archive/communication/
  mv core/communication/*.bak* archive/communication/
  ```

#### 验证标准

```bash
# 确认无备份文件
! find core/communication/ -name "*backup*" -o -name "*.bak"

# 确认核心文件存在
test -f core/communication/communication_engine.py
test -f core/communication/message_handler.py
```

### 1.5 修复模块导入错误

#### 检查清单

- [ ] **扫描所有导入错误**
  ```bash
  # 检查语法错误
  python -m py_compile core/communication/optimized_communication_module.py
  ```

- [ ] **修复导入列表**
  - [ ] `optimized_communication_module.py:41-43`
    ```python
    # ❌ 移除不存在的导入
    # from core.communication.channel_manager import ChannelManager
    # from core.communication.message_handler import MessageHandler
    # from core.communication.protocol_manager import ProtocolManager

    # ✅ 使用正确的导入
    from core.communication.communication_engine import CommunicationEngine
    from core.base_module import BaseModule
    ```

- [ ] **验证所有模块可导入**
  ```bash
  python -c "from core.communication.communication_engine import CommunicationEngine"
  python -c "from core.mcp.stateful_client import StatefulMCPClient"
  python -c "from core.mcp.stateless_client import StatelessMCPClient"
  ```

#### 验证标准

```bash
# 运行导入检查
for file in core/communication/*.py core/mcp/*.py; do
    python -m py_compile "$file" || echo "导入错误: $file"
done
```

---

## 🔍 阶段1: Pyright类型检查配置（P0）

### 1.6 配置Pyright

#### 检查清单

- [ ] **安装pyright**
  ```bash
  # 使用npm安装
  npm install -g pyright

  # 或使用pip安装pyright Python wrapper
  pip install pyright
  ```

- [ ] **创建pyright配置文件**
  - [ ] 创建 `pyproject.toml` 或更新现有配置
  - [ ] 创建 `pyrightconfig.json`

- [ ] **配置内容**
  ```toml
  # pyproject.toml
  [tool.pyright]
  include = ["core/communication", "core/mcp", "core/orchestration"]
  exclude = [
    "**/__pycache__",
    "**/.venv",
    "**/node_modules",
    "**/test_*.py",
    "**/archive"
  ]

  defineConstant = {
      DEBUG = true
  }

  reportMissingImports = true
  reportMissingTypeStubs = false
  reportIncompatibleVariableOverride = true
  reportIncompatibleMethodOverride = true
  reportOptionalMemberAccess = true
  reportOptionalCall = true
  reportOptionalIterable = true
  reportOptionalContextManager = true
  reportOptionalOperand = true
  reportUntypedFunctionDecorator = true
  reportUntypedClassDef = true
  reportUntypedBaseClass = true
  reportPrivateImportUsage = true
  reportUndefinedVariable = true

  pythonVersion = "3.14"
  pythonPlatform = "Darwin"
  typeCheckingMode = "strict"
  ```

  ```json
  // pyrightconfig.json
  {
    "include": [
      "core/communication",
      "core/mcp",
      "core/orchestration"
    ],
    "exclude": [
      "**/__pycache__",
      "**/.venv",
      "**/test_*.py",
      "**/archive"
    ],
    "defineConstant": {
      "DEBUG": true
    },
    "reportMissingImports": true,
    "reportMissingTypeStubs": false,
    "typeCheckingMode": "strict",
    "pythonVersion": "3.14",
    "pythonPlatform": "Darwin"
  }
  ```

- [ ] **添加类型存根（stub文件）**
  - [ ] 为第三方库创建类型存根（如需要）
  - [ ] `core/communication/stubs/` 目录

#### 验证标准

```bash
# 运行pyright检查
pyright core/communication/

# 应该看到类似输出（无严重错误）
# 0 errors, 0 warnings, 0 informations
```

### 1.7 修复Pyright类型错误

#### 检查清单

- [ ] **运行初始扫描**
  ```bash
  # 生成类型错误报告
  pyright core/communication/ > pyright-report.txt 2>&1
  ```

- [ ] **分类修复类型错误**

  **P0级别错误（必须修复）：**
  - [ ] reportUndefinedVariable - 未定义变量
  - [ ] reportOptionalMemberAccess - 可选成员访问
  - [ ] reportOptionalCall - 可选调用

  **P1级别错误（应该修复）：**
  - [ ] reportMissingImports - 缺失导入
  - [ ] reportIncompatibleMethodOverride - 不兼容的方法重写

  **P2级别错误（可选修复）：**
  - [ ] reportUntypedFunctionDecorator - 未类型化的装饰器
  - [ ] reportPrivateImportUsage - 私有导入使用

- [ ] **添加类型注解模板**
  ```python
  # ✅ 完整类型注解示例
  from typing import Any, Dict, List, Optional, Union

  async def send_message(
      self,
      receiver_id: str,
      content: Any,
      message_type: str = 'text',
      channel_id: Optional[str] = None,
      metadata: Optional[Dict[str, Any]] = None
  ) -> str:
      """发送消息到指定接收者

      Args:
          receiver_id: 接收者ID
          content: 消息内容
          message_type: 消息类型
          channel_id: 通道ID（可选）
          metadata: 元数据（可选）

      Returns:
          str: 消息ID

      Raises:
          ValueError: 参数验证失败
          ConnectionError: 连接失败
      """
      # 实现...
      return message_id
  ```

#### 验证标准

```bash
# 最终验证
pyright core/communication/ core/mcp/ core/orchestration/

# 预期输出
# No errors found
```

---

## ⚡ 阶段2: 异步编程一致性（P1）

### 2.1 统一异步编程

#### 检查清单

- [ ] **扫描threading使用**
  ```bash
  grep -rn "import threading\|from threading" core/communication/
  grep -rn "import queue\|from queue import Queue" core/communication/
  ```

- [ ] **修复文件列表**
  - [ ] `optimized_communication_module.py:332-334`
    ```python
    # ❌ 错误
    from queue import Queue
    import threading

    self.batch_queues = defaultdict(queue.Queue)
    self.batch_locks = defaultdict(threading.Lock)
    self.batch_timers = {}  # 使用threading.Timer

    # ✅ 正确
    import asyncio
    from collections import defaultdict

    self.batch_queues = defaultdict(asyncio.Queue)
    self.batch_locks = defaultdict(asyncio.Lock)
    self.batch_timers = {}  # 使用asyncio.create_task和asyncio.sleep
    ```

- [ ] **重写批处理器**
  ```python
  # core/communication/engine/batch_processor.py
  class AsyncBatchProcessor:
      """异步批处理器"""

      def __init__(self, config: Dict[str, Any]):
          self.batch_size = config.get('batch_size', 100)
          self.batch_timeout = config.get('batch_timeout', 1.0)
          self.queues: Dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
          self.locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
          self._tasks: List[asyncio.Task] = []

      async def add_message(self, message: Message) -> None:
          """添加消息到批处理队列"""
          async with self.locks[message.receiver_id]:
              await self.queues[message.receiver_id].put(message)

      async def _process_batch(self, receiver_id: str) -> None:
          """处理批次"""
          while True:
              try:
                  messages = []
                  # 收集消息
                  for _ in range(self.batch_size):
                      try:
                          msg = await asyncio.wait_for(
                              self.queues[receiver_id].get(),
                              timeout=self.batch_timeout
                          )
                          messages.append(msg)
                      except asyncio.TimeoutError:
                          break

                  if messages:
                      await self._send_batch(messages)

              except Exception as e:
                  logger.error(f"批处理失败: {e}")

      async def start(self) -> None:
          """启动批处理器"""
          for receiver_id in self.queues.keys():
              task = asyncio.create_task(self._process_batch(receiver_id))
              self._tasks.append(task)

      async def stop(self) -> None:
          """停止批处理器"""
          for task in self._tasks:
              task.cancel()
          await asyncio.gather(*self._tasks, return_exceptions=True)
  ```

#### 验证标准

```bash
# 确认无threading使用（除特殊情况）
! grep -rn "import threading" core/communication/ | grep -v test
! grep -rn "from queue import Queue" core/communication/ | grep -v asyncio

# 异步代码检查
python -m py_compile core/communication/engine/batch_processor.py
```

### 2.2 优化连接池管理

#### 检查清单

- [ ] **实现动态连接池**
  ```python
  # core/communication/engine/connection_pool.py
  from typing import Dict, Optional
  import asyncio
  from datetime import datetime, timedelta

  class DynamicConnectionPool:
      """动态连接池"""

      def __init__(
          self,
          min_size: int = 5,
          max_size: int = 50,
          idle_timeout: float = 300.0,
          health_check_interval: float = 60.0
      ):
          self.min_size = min_size
          self.max_size = max_size
          self.idle_timeout = idle_timeout
          self.health_check_interval = health_check_interval

          self._pool: asyncio.Queue = asyncio.Queue(maxsize=max_size)
          self._connections: Dict[str, Dict] = {}
          self._lock = asyncio.Lock()
          self._health_check_task: Optional[asyncio.Task] = None

      async def acquire(self, timeout: float = 30.0) -> Any:
          """获取连接"""
          try:
              # 尝试从池中获取
              conn = await asyncio.wait_for(
                  self._pool.get(),
                  timeout=timeout
              )
              return conn
          except asyncio.TimeoutError:
              # 池中无可用连接，创建新连接
              return await self._create_connection()

      async def release(self, conn: Any) -> None:
          """释放连接回池"""
          if self._pool.qsize() < self.max_size:
              await self._pool.put(conn)
          else:
              # 池已满，关闭连接
              await self._close_connection(conn)

      async def _create_connection(self) -> Any:
          """创建新连接"""
          # 实现连接创建逻辑
          pass

      async def _close_connection(self, conn: Any) -> None:
          """关闭连接"""
          # 实现连接关闭逻辑
          pass

      async def start_health_check(self) -> None:
          """启动健康检查"""
          async def health_check_loop():
              while True:
                  await self._health_check()
                  await asyncio.sleep(self.health_check_interval)

          self._health_check_task = asyncio.create_task(health_check_loop())

      async def _health_check(self) -> None:
          """执行健康检查"""
          async with self._lock:
              now = datetime.now()
              expired_conns = []

              # 检查空闲连接
              for conn_id, conn_info in self._connections.items():
                  idle_time = (now - conn_info['last_used']).total_seconds()
                  if idle_time > self.idle_timeout:
                      expired_conns.append(conn_id)

              # 清理过期连接
              for conn_id in expired_conns:
                  await self._remove_connection(conn_id)

      async def stop(self) -> None:
          """停止连接池"""
          if self._health_check_task:
              self._health_check_task.cancel()

          # 关闭所有连接
          async with self._lock:
              for conn in self._connections.values():
                  await self._close_connection(conn['connection'])
              self._connections.clear()
  ```

#### 验证标准

```python
# 测试连接池
async def test_connection_pool():
    pool = DynamicConnectionPool(min_size=5, max_size=10)

    # 测试获取连接
    conn1 = await pool.acquire()
    conn2 = await pool.acquire()
    assert conn1 is not None
    assert conn2 is not None

    # 测试释放连接
    await pool.release(conn1)
    await pool.release(conn2)

    # 测试健康检查
    await pool.start_health_check()
    await asyncio.sleep(2)
    await pool.stop()

    print("✅ 连接池测试通过")
```

---

## 🧪 阶段2: 测试覆盖（P1）

### 2.3 编写单元测试

#### 检查清单

- [ ] **创建测试目录结构**
  ```
  tests/
  ├── unit/
  │   ├── communication/
  │   │   ├── test_communication_engine.py
  │   │   ├── test_message_queue.py
  │   │   ├── test_protocol_adapter.py
  │   │   ├── test_websocket_manager.py
  │   │   └── test_batch_processor.py
  │   ├── mcp/
  │   │   ├── test_stateful_client.py
  │   │   ├── test_stateless_client.py
  │   │   └── test_mcp_manager.py
  │   └── orchestration/
  │       └── test_unified_mcp_manager.py
  ├── integration/
  │   ├── test_communication_integration.py
  │   └── test_mcp_integration.py
  └── performance/
      ├── test_message_throughput.py
      └── test_connection_pool.py
  ```

- [ ] **配置pytest**
  ```ini
  # pytest.ini
  [pytest]
  testpaths = tests
  python_files = test_*.py
  python_classes = Test*
  python_functions = test_*
  addopts =
      -v
      --strict-markers
      --cov=core/communication
      --cov=core/mcp
      --cov-report=html
      --cov-report=term-missing
      --asyncio-mode=auto
  markers =
      unit: Unit tests
      integration: Integration tests
      performance: Performance tests
      slow: Slow running tests
  ```

- [ ] **核心测试用例清单**
  - [ ] `test_communication_engine.py`
    - [ ] test_send_message()
    - [ ] test_broadcast_message()
    - [ ] test_create_channel()
    - [ ] test_create_session()
    - [ ] test_get_messages()
    - [ ] test_websocket_register()
    - [ ] test_protocol_serialization()

  - [ ] `test_stateful_client.py`
    - [ ] test_connect_to_server()
    - [ ] test_call_tool()
    - [ ] test_read_resource()
    - [ ] test_session_timeout()
    - [ ] test_keepalive()

  - [ ] `test_stateless_client.py`
    - [ ] test_connect_to_server()
    - [ ] test_call_tool()
    - [ ] test_connection_pool()
    - [ ] test_timeout_handling()

#### 验证标准

```bash
# 运行测试
pytest tests/unit/communication/ -v --cov=core/communication

# 预期输出
# ========== coverage: platform darwin, python 3.14 ==========
# Name                                              Stmts   Miss  Cover
# ------------------------------------------------------------------------
# core/communication/__init__.py                         4      0   100%
# core/communication/communication_engine.py           280     45    84%
# core/communication/message_handler.py                 85     12    86%
# ------------------------------------------------------------------------
# TOTAL                                                 369     57    85%
```

### 2.4 集成测试

#### 检查清单

- [ ] **端到端通信测试**
  ```python
  # tests/integration/test_communication_integration.py
  import pytest
  from core.communication.communication_engine import CommunicationEngine

  @pytest.mark.asyncio
  @pytest.mark.integration
  class TestCommunicationIntegration:
      """通信集成测试"""

      @pytest.fixture
      async def engine(self):
          """创建测试引擎"""
          engine = CommunicationEngine("test_agent")
          await engine.initialize()
          yield engine
          await engine.shutdown()

      async def test_send_receive_cycle(self, engine):
          """测试发送接收循环"""
          # 发送消息
          msg_id = await engine.send_message(
              receiver_id="receiver",
              content="Hello",
              message_type=MessageType.TEXT
          )

          # 接收消息
          messages = await engine.get_messages(limit=10)
          assert len(messages) > 0
          assert messages[0].id == msg_id

      async def test_channel_lifecycle(self, engine):
          """测试通道生命周期"""
          # 创建通道
          channel = await engine.create_channel(
              channel_id="test_channel",
              name="Test Channel",
              channel_type=ChannelType.DIRECT,
              participants=["agent1", "agent2"]
          )

          assert channel.id == "test_channel"
          assert len(channel.participants) == 2

          # 广播消息
          await engine.broadcast_message(
              content="Broadcast",
              channel_id="test_channel"
          )
  ```

#### 验证标准

```bash
# 运行集成测试
pytest tests/integration/ -v -m integration

# 预期输出
# tests/integration/test_communication_integration.py::TestCommunicationIntegration::test_send_receive_cycle PASSED
# tests/integration/test_communication_integration.py::TestCommunicationIntegration::test_channel_lifecycle PASSED
```

---

## 📊 阶段3: 监控和文档（P2）

### 3.1 添加Prometheus指标

#### 检查清单

- [ ] **安装prometheus_client**
  ```bash
  pip install prometheus-client
  ```

- [ ] **创建指标收集器**
  ```python
  # core/communication/utils/metrics.py
  from prometheus_client import Counter, Histogram, Gauge, start_http_server
  import time

  # 消息计数器
  messages_sent = Counter(
      'communication_messages_sent_total',
      'Total number of messages sent',
      ['agent_id', 'message_type', 'status']
  )

  messages_received = Counter(
      'communication_messages_received_total',
      'Total number of messages received',
      ['agent_id', 'message_type']
  )

  # 消息延迟直方图
  message_latency = Histogram(
      'communication_message_latency_seconds',
      'Message latency in seconds',
      ['agent_id', 'message_type']
  )

  # 活跃连接数
  active_connections = Gauge(
      'communication_active_connections',
      'Number of active connections',
      ['agent_id', 'connection_type']
  )

  # 队列大小
  queue_size = Gauge(
      'communication_queue_size',
      'Current queue size',
      ['agent_id', 'queue_type']
  )

  def start_metrics_server(port: int = 9090):
      """启动指标服务器"""
      start_http_server(port)
  ```

- [ ] **集成指标到通信引擎**
  ```python
  # core/communication/communication_engine.py
  from core.communication.utils.metrics import (
      messages_sent,
      messages_received,
      message_latency,
      active_connections,
      queue_size
  )

  class CommunicationEngine:
      async def send_message(self, ...) -> str:
          start_time = time.time()
          try:
              # 发送逻辑
              message_id = str(uuid.uuid4())
              await self.message_queue.enqueue(message)

              # 记录指标
              messages_sent.labels(
                  agent_id=self.agent_id,
                  message_type=message_type.value,
                  status='success'
              ).inc()

              return message_id
          except Exception as e:
              messages_sent.labels(
                  agent_id=self.agent_id,
                  message_type=message_type.value,
                  status='error'
              ).inc()
              raise
          finally:
              latency = time.time() - start_time
              message_latency.labels(
                  agent_id=self.agent_id,
                  message_type=message_type.value
              ).observe(latency)
  ```

#### 验证标准

```bash
# 启动服务后访问指标
curl http://localhost:9090/metrics

# 预期输出
# HELP communication_messages_sent_total Total number of messages sent
# TYPE communication_messages_sent_total counter
# communication_messages_sent_total{agent_id="test",message_type="text",status="success"} 42.0
```

### 3.2 更新文档

#### 检查清单

- [ ] **API文档生成**
  ```bash
  # 安装Sphinx
  pip install sphinx sphinx-rtd-theme sphinx-asyncio

  # 生成文档
  cd docs/communication
  make html
  ```

- [ ] **必需文档章节**
  - [ ] 快速开始
  - [ ] 架构概述
  - [ ] API参考
  - [ ] 配置说明
  - [ ] 性能调优
  - [ ] 故障排除

#### 验证标准

```bash
# 文档构建成功
cd docs/communication && make html

# 无警告和错误
# Build finished. The HTML pages are in _build/html.
```

---

## ✅ 最终验证清单

### 完整性检查

- [ ] **安全检查**
  ```bash
  # 无硬编码密钥
  ! grep -r "4c98d375577d64cfce0d4d0dfee25fb9" core/

  # 无空except块
  ! grep -rn "except.*:.*pass" core/communication/ core/orchestration/ core/mcp/
  ```

- [ ] **类型检查**
  ```bash
  # Pyright无错误
  pyright core/communication/ core/mcp/ core/orchestration/
  # 预期: 0 errors
  ```

- [ ] **代码质量**
  ```bash
  # 类型检查
  mypy core/communication/ --strict

  # 代码格式
  black --check core/communication/

  # 导入排序
  isort --check-only core/communication/

  # 代码复杂度
  radon mi core/communication/ -n -a
  ```

- [ ] **测试覆盖**
  ```bash
  # 单元测试覆盖率 >= 80%
  pytest tests/unit/ --cov=core/communication --cov-report=term-missing

  # 集成测试通过
  pytest tests/integration/ -v

  # 性能测试
  pytest tests/performance/ -v -m performance
  ```

- [ ] **性能基准**
  ```python
  # tests/performance/benchmarks.py
  import pytest
  import asyncio
  from core.communication.communication_engine import CommunicationEngine

  @pytest.mark.performance
  class TestPerformance:
      async def test_message_throughput(self):
          """测试消息吞吐量"""
          engine = CommunicationEngine("perf_test")
          await engine.initialize()

          start_time = time.time()
          message_count = 1000

          for i in range(message_count):
              await engine.send_message(
                  receiver_id="test",
                  content=f"Message {i}"
              )

          elapsed = time.time() - start_time
          throughput = message_count / elapsed

          # 目标: >= 1000 msg/s
          assert throughput >= 1000, f"吞吐量不足: {throughput:.2f} msg/s"

          await engine.shutdown()

      async def test_message_latency(self):
          """测试消息延迟"""
          engine = CommunicationEngine("latency_test")
          await engine.initialize()

          latencies = []
          for _ in range(100):
              start = time.time()
              await engine.send_message(
                  receiver_id="test",
                  content="Test message"
              )
              latencies.append(time.time() - start)

          avg_latency = sum(latencies) / len(latencies)
          p99_latency = sorted(latencies)[98]  # 99th percentile

          # 目标: 平均延迟 < 10ms, P99 < 50ms
          assert avg_latency < 0.01, f"平均延迟过高: {avg_latency*1000:.2f}ms"
          assert p99_latency < 0.05, f"P99延迟过高: {p99_latency*1000:.2f}ms"

          await engine.shutdown()
  ```

### 部署前检查

- [ ] **环境变量配置**
  ```bash
  # 验证所有必需的环境变量
  cat > .env.production << EOF
  # MCP服务配置
  AMAP_API_KEY=${AMAP_API_KEY}
  MCP_LOG_LEVEL=INFO

  # 通信服务配置
  COMMUNICATION_MAX_QUEUE_SIZE=10000
  COMMUNICATION_MAX_CONNECTIONS=1000
  COMMUNICATION_MESSAGE_TIMEOUT=30

  # 监控配置
  PROMETHEUS_PORT=9090
  EOF
  ```

- [ ] **健康检查端点**
  ```python
  # core/communication/health.py
  from fastapi import FastAPI
  from prometheus_client import generate_latest

  app = FastAPI()

  @app.get("/health")
  async def health_check():
      """健康检查端点"""
      return {
          "status": "healthy",
          "timestamp": datetime.now().isoformat()
      }

  @app.get("/metrics")
  async def metrics():
      """Prometheus指标端点"""
      return Response(content=generate_latest(), media_type="text/plain")
  ```

---

## 📈 进度跟踪

| 任务编号 | 任务描述 | 负责人 | 状态 | 完成日期 |
|---------|---------|--------|------|----------|
| 1.1 | 移除硬编码API密钥 | | ⏳ | |
| 1.2 | 修复空except块 | | ⏳ | |
| 1.3 | 添加输入验证 | | ⏳ | |
| 1.4 | 移除冗余文件 | | ⏳ | |
| 1.5 | 修复导入错误 | | ⏳ | |
| 1.6 | 配置Pyright | | ⏳ | |
| 1.7 | 修复类型错误 | | ⏳ | |
| 2.1 | 统一异步编程 | | ⏳ | |
| 2.2 | 优化连接池 | | ⏳ | |
| 2.3 | 编写单元测试 | | ⏳ | |
| 2.4 | 集成测试 | | ⏳ | |
| 3.1 | 添加Prometheus指标 | | ⏳ | |
| 3.2 | 更新文档 | | ⏳ |

---

## 🎯 验收标准

### 阶段1验收（P0）

- [ ] 安全扫描通过（无硬编码密钥，无空except块）
- [ ] Pyright类型检查0错误
- [ ] 所有模块可正常导入
- [ ] 代码覆盖率 >= 60%

### 阶段2验收（P1）

- [ ] 无threading混用（全部使用asyncio）
- [ ] 单元测试覆盖率 >= 80%
- [ ] 集成测试通过
- [ ] 性能基准测试通过

### 阶段3验收（P2）

- [ ] Prometheus指标正常暴露
- [ ] 文档完整（API参考、架构图）
- [ ] 健康检查端点正常
- [ ] 综合评分 >= 8.5/10

---

## 📞 支持和反馈

如有问题或建议，请：
- 提交Issue到项目仓库
- 联系项目负责人：徐健 (xujian519@gmail.com)
- 查看详细文档：`docs/communication/`

---

**最后更新：** 2026-01-25
**版本：** v1.0.0
**状态：** 📋 执行中
