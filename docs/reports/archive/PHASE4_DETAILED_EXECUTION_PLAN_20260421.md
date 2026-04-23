# 第4阶段深度优化 - 详细执行计划

> **制定时间**: 2026-04-21
> **执行周期**: 2026-04-22 ~ 2026-07-15 (12周)
> **风险级别**: ★★★★★ (极高)
> **预期收益**: ★★★★☆ (长期架构优化)

---

## 📋 执行摘要

### 背景

前3阶段已完成(第1阶段:安全清理,第2阶段:基础重构,第3阶段:核心整合),用2天时间完成了原计划5-6个月的工作。第4阶段是最后也是风险最高的阶段,涉及系统核心架构的深度优化。

### 核心目标

1. **建立测试基础设施**: 测试覆盖率从当前~40%提升至>80%
2. **合并Agent系统**: 统一小娜、小诺、云熙等Agent的实现
3. **明确Gateway-Core边界**: 清晰职责划分,消除重叠
4. **扁平化目录结构**: 文件嵌套深度从6层降至<4层

### 成功指标

| 指标 | 当前值 | 目标值 | 测量方式 |
|------|--------|--------|---------|
| 测试覆盖率 | ~40% | >80% | pytest-cov |
| 代码重复率 | ~15% | <5% | pylint/similar |
| 文件嵌套深度 | 6层 | <4层 | find命令 |
| 配置文件数量 | 260+ | <50个 | find命令 |
| API响应时间(P95) | ~150ms | <100ms | Apache Bench |
| 向量检索延迟 | ~80ms | <50ms | 性能测试 |
| 缓存命中率 | ~89.7% | >90% | Redis监控 |

---

## 🗓️ 总体时间表

```
Week 1-2  (2026-04-22 ~ 2026-05-05): 建立测试基础设施
Week 3-4  (2026-05-06 ~ 2026-05-19): 设计Agent统一接口
Week 5-10 (2026-05-20 ~ 2026-07-07): 逐步迁移Agent
Week 11   (2026-07-08 ~ 2026-07-14): 明确Gateway-Core边界
Week 12   (2026-07-15 ~ 2026-07-21): 扁平化目录结构
```

---

## 📊 Week 1-2: 建立测试基础设施 (2026-04-22 ~ 2026-05-05)

### 目标

建立完善的测试基础设施,确保后续重构有足够的测试覆盖。

### Day 1-2: 测试覆盖率基线分析

**任务**:
- [ ] 运行完整测试覆盖率报告
  ```bash
  # 生成HTML覆盖率报告
  pytest --cov=core --cov=services --cov=patents \
         --cov-report=html --cov-report=term \
         -v tests/

  # 查看HTML报告
  open htmlcov/index.html
  ```

- [ ] 识别测试盲区
  - 覆盖率<30%的模块: 列表
  - 覆盖率30-60%的模块: 列表
  - 未测试的关键路径: 列表

- [ ] 生成测试覆盖率分析报告
  ```markdown
  # 测试覆盖率分析报告

  ## 总体覆盖率
  - 当前: XX%
  - 目标: >80%

  ## 模块覆盖率排名
  | 模块 | 覆盖率 | 文件数 | 测试数 |
  |------|--------|--------|--------|
  | core/agents/ | XX% | XX | XX |
  | core/llm/ | XX% | XX | XX |

  ## 测试盲区
  - 模块A: 覆盖率10%, 需补充测试
  - 模块B: 覆盖率25%, 需补充测试

  ## 优先级
  ### P0 (核心功能)
  - core/agents/base_agent.py: XX% → >80%
  - core/llm/unified_llm_manager.py: XX% → >80%

  ### P1 (重要功能)
  - core/memory/: XX% → >70%
  - core/embedding/: XX% → >70%
  ```

**验证标准**:
- ✅ 覆盖率报告已生成
- ✅ 测试盲区已识别
- ✅ 优先级已确定

---

### Day 3-5: 补充核心模块测试

**任务**:
- [ ] 补充base_agent.py测试
  ```python
  # tests/test_base_agent.py
  import pytest
  from core.agents.base_agent import BaseAgent

  def test_agent_initialization():
      """测试Agent初始化"""
      agent = BaseAgent(name="test")
      assert agent.name == "test"
      assert agent.capabilities is not None

  def test_agent_process():
      """测试Agent处理逻辑"""
      agent = BaseAgent(name="test")
      result = agent.process({"task": "test"})
      assert result is not None

  def test_agent_memory_integration():
      """测试Agent与内存系统集成"""
      agent = BaseAgent(name="test")
      agent.memory.store("key", "value")
      retrieved = agent.memory.retrieve("key")
      assert retrieved == "value"
  ```

- [ ] 补充unified_llm_manager.py测试
  ```python
  # tests/test_unified_llm_manager.py
  import pytest
  from core.llm.unified_llm_manager import UnifiedLLMManager

  def test_llm_manager_initialization():
      """测试LLM管理器初始化"""
      manager = UnifiedLLMManager()
      assert manager.providers is not None

  @pytest.mark.asyncio
  async def test_llm_call():
      """测试LLM调用"""
      manager = UnifiedLLMManager()
      response = await manager.call(
          provider="anthropic",
          prompt="测试",
          model="claude-sonnet-4-6"
      )
      assert response is not None
      assert "content" in response
  ```

- [ ] 补充memory系统测试
  ```python
  # tests/test_memory_system.py
  import pytest
  from core.memory.four_tier_memory import FourTierMemory

  def test_memory_storage():
      """测试内存存储"""
      memory = FourTierMemory()
      memory.store("key1", "value1")
      assert memory.retrieve("key1") == "value1"

  def test_memory_tier_promotion():
      """测试内存层级提升"""
      memory = FourTierMemory()
      # HOT → WARM → COLD → ARCHIVE
      # 测试提升逻辑

  def test_memory_capacity_limits():
      """测试内存容量限制"""
      memory = FourTierMemory()
      # 测试HOT tier 100MB限制
      # 测试WARM tier 500MB限制
  ```

**验证标准**:
- ✅ base_agent.py覆盖率>80%
- ✅ unified_llm_manager.py覆盖率>80%
- ✅ memory系统覆盖率>70%
- ✅ 所有新测试通过

---

### Day 6-7: 建立CI/CD测试管道

**任务**:
- [ ] 配置GitHub Actions (或GitLab CI)
  ```yaml
  # .github/workflows/test.yml
  name: Test Suite

  on: [push, pull_request]

  jobs:
    test:
      runs-on: ubuntu-latest
      strategy:
        matrix:
          python-version: [3.9, 3.10, 3.11]

      steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install poetry
          poetry install

      - name: Run tests
        run: |
          poetry run pytest tests/ -v --cov

      - name: Upload coverage
        uses: codecov/codecov-action@v3
  ```

- [ ] 配置覆盖率门禁
  ```yaml
  # 在CI中添加覆盖率检查
  - name: Check coverage
        run: |
          coverage=$(pytest --cov --cov-report=term | grep TOTAL | awk '{print $4}' | sed 's/%//')
          if (( $(echo "$coverage < 70" | bc -l) )); then
            echo "覆盖率 ${coverage}% 低于门禁70%"
            exit 1
          fi
  ```

- [ ] 配置自动化测试报告
  ```yaml
  # 生成测试报告
  - name: Generate test report
        run: |
          pytest tests/ --html=test-report.html --self-contained-html

  - name: Upload test report
        uses: actions/upload-artifact@v3
        with:
          name: test-report
          path: test-report.html
  ```

**验证标准**:
- ✅ CI/CD管道已配置
- ✅ 每次push自动运行测试
- ✅ 覆盖率门禁已设置
- ✅ 测试报告自动生成

---

### Day 8-10: 性能基准测试

**任务**:
- [ ] API响应时间测试
  ```bash
  # 使用Apache Bench测试
  ab -n 1000 -c 10 http://localhost:8005/api/health

  # 使用wrk测试
  wrk -t4 -c100 -d30s http://localhost:8005/api/health

  # 记录P50, P95, P99延迟
  ```

- [ ] 向量检索延迟测试
  ```python
  # tests/test_retrieval_performance.py
  import pytest
  import time
  from patents.core.retrieval import HybridRetriever

  def test_retrieval_latency():
      """测试检索延迟"""
      retriever = HybridRetriever()

      latencies = []
      for i in range(100):
          start = time.time()
          results = retriever.search("人工智能专利", limit=10)
          latency = (time.time() - start) * 1000  # ms
          latencies.append(latency)

      # P95延迟应<50ms
      p95 = sorted(latencies)[94]
      assert p95 < 50, f"P95延迟 {p95}ms 超过目标50ms"
  ```

- [ ] 数据库查询性能测试
  ```python
  # tests/test_database_performance.py
  import pytest
  import time
  from core.database.connection_pool import get_connection

  def test_query_latency():
      """测试数据库查询延迟"""
      conn = get_connection()

      latencies = []
      for i in range(100):
          start = time.time()
          result = conn.execute("SELECT * FROM patents LIMIT 10")
          latency = (time.time() - start) * 1000
          latencies.append(latency)

      avg_latency = sum(latencies) / len(latencies)
      assert avg_latency < 10, f"平均延迟 {avg_latency}ms 超过目标10ms"
  ```

- [ ] 生成性能基准报告
  ```markdown
  # 性能基准测试报告

  ## API响应时间
  - P50: XXms
  - P95: XXms (目标: <100ms)
  - P99: XXms

  ## 向量检索延迟
  - P50: XXms
  - P95: XXms (目标: <50ms)
  - P99: XXms

  ## 数据库查询延迟
  - P50: XXms
  - P95: XXms (目标: <10ms)
  - P99: XXms

  ## 缓存命中率
  - 当前: XX%
  - 目标: >90%
  ```

**验证标准**:
- ✅ 性能基准已建立
- ✅ 性能报告已生成
- ✅ 性能瓶颈已识别
- ✅ 优化建议已提出

---

### Day 11-14: 代码质量分析

**任务**:
- [ ] 代码重复率分析
  ```bash
  # 使用pylint分析重复代码
  pylint --similarities=. --enable=similarities \
         core/ services/ patents/ > similarities.txt

  # 或使用jscpd
  jscpd core/ services/ patents/ \
    --format html \
    --reporters html \
    --output jscpd-report/
  ```

- [ ] 配置文件数量统计
  ```bash
  # 统计配置文件
  find config/ -name "*.yml" -o -name "*.yaml" -o -name "*.json" | wc -l

  # 按类型统计
  find config/ -name "*.yml" | wc -l
  find config/ -name "*.yaml" | wc -l
  find config/ -name "*.json" | wc -l
  ```

- [ ] 文件嵌套深度分析
  ```bash
  # 分析文件嵌套深度
  find . -name "*.py" | awk '{
    depth = gsub(/\//, "&")
    print depth, $0
  }' | sort -n | tail -20
  ```

- [ ] 生成代码质量报告
  ```markdown
  # 代码质量分析报告

  ## 代码重复率
  - 当前: XX%
  - 目标: <5%
  - 重复代码块: XX个
  - 重复行数: XX行

  ## 配置文件数量
  - 当前: XX个
  - 目标: <50个
  - 冗余配置: XX个

  ## 文件嵌套深度
  - 最大深度: XX层
  - 目标: <4层
  - 超过4层的文件: XX个

  ## 代码复杂度
  - 高复杂度函数: XX个
  - 建议重构: XX个
  ```

**验证标准**:
- ✅ 代码重复率已统计
- ✅ 配置文件数量已统计
- ✅ 文件嵌套深度已分析
- ✅ 代码质量报告已生成

---

### Week 1-2 检查点

- [ ] 测试覆盖率从40%提升至>70%
- [ ] CI/CD测试管道已建立
- [ ] 性能基准已建立
- [ ] 代码质量基线已确定
- [ ] 测试补充计划已制定

---

## 🤖 Week 3-4: 设计Agent统一接口 (2026-05-06 ~ 2026-05-19)

### 目标

设计统一的Agent接口,为后续Agent合并做准备。

### Day 15-17: Agent系统现状调研

**任务**:
- [ ] 分析所有Agent实现
  ```bash
  # 查找所有Agent文件
  find core/agents/ -name "*agent*.py" | sort

  # 统计Agent数量
  find core/agents/ -name "*agent*.py" | wc -l
  ```

- [ ] 识别Agent共同模式
  - 共同方法: 列表
  - 共同属性: 列表
  - 共同依赖: 列表

- [ ] 识别Agent差异
  - 小娜特有功能: 列表
  - 小诺特有功能: 列表
  - 云熙特有功能: 列表

- [ ] 绘制Agent依赖关系图
  ```mermaid
  graph TD
      BaseAgent --> XiaonaAgent
      BaseAgent --> XiaonuoAgent
      BaseAgent --> YunxiAgent

      XiaonaAgent --> PatentAnalyzer
      XiaonaAgent --> LegalKnowledge

      XiaonuoAgent --> TaskScheduler
      XiaonuoAgent --> AgentOrchestrator

      YunxiAgent --> ClientManager
      YunxiAgent --> ProjectManager
  ```

**验证标准**:
- ✅ 所有Agent已识别
- ✅ 共同模式已提取
- ✅ Agent差异已分析
- ✅ 依赖关系图已绘制

---

### Day 18-19: 设计统一Agent接口

**任务**:
- [ ] 设计BaseAgent v2接口
  ```python
  # core/agents/base_agent_v2.py
  from abc import ABC, abstractmethod
  from typing import Dict, Any, List, Optional
  from pydantic import BaseModel

  class AgentConfig(BaseModel):
      """Agent配置"""
      name: str
      version: str = "1.0.0"
      capabilities: List[str] = []
      max_concurrent_tasks: int = 1
      timeout: int = 30

  class AgentContext(BaseModel):
      """Agent上下文"""
      session_id: str
      user_id: Optional[str] = None
      metadata: Dict[str, Any] = {}

  class AgentResponse(BaseModel):
      """Agent响应"""
      success: bool
      result: Optional[Dict[str, Any]] = None
      error: Optional[str] = None
      metadata: Dict[str, Any] = {}

  class BaseAgentV2(ABC):
      """统一Agent基类 v2.0"""

      def __init__(self, config: AgentConfig):
          self.config = config
          self._context: Optional[AgentContext] = None

      @abstractmethod
      async def process(
          self,
          request: Dict[str, Any],
          context: Optional[AgentContext] = None
      ) -> AgentResponse:
          """处理请求"""
          pass

      @abstractmethod
      async def validate_request(self, request: Dict[str, Any]) -> bool:
          """验证请求"""
          pass

      @abstractmethod
      def get_capabilities(self) -> List[str]:
          """获取能力列表"""
          pass

      async def health_check(self) -> bool:
          """健康检查"""
          return True

      async def shutdown(self):
          """优雅关闭"""
          pass
  ```

- [ ] 设计Agent生命周期管理
  ```python
  # core/agents/agent_lifecycle.py
  from enum import Enum

  class AgentState(str, Enum):
      """Agent状态"""
      INITIALIZING = "initializing"
      IDLE = "idle"
      BUSY = "busy"
      ERROR = "error"
      SHUTTING_DOWN = "shutting_down"
      TERMINATED = "terminated"

  class AgentLifecycleManager:
      """Agent生命周期管理器"""

      def __init__(self, agent: BaseAgentV2):
          self.agent = agent
          self.state = AgentState.INITIALIZING
          self.transitions = []

      async def transition_to(self, new_state: AgentState):
          """状态转换"""
          # 验证状态转换合法性
          # 记录转换历史
          # 触发状态变更回调
          pass
  ```

- [ ] 设计Agent通信协议
  ```python
  # core/agents/agent_communication.py
  from pydantic import BaseModel

  class AgentMessage(BaseModel):
      """Agent间消息"""
      from_agent: str
      to_agent: str
      message_type: str  # request, response, notification
      payload: Dict[str, Any]
      timestamp: float
      correlation_id: Optional[str] = None

  class MessageBus:
      """Agent消息总线"""

      async def send(self, message: AgentMessage):
          """发送消息"""
          pass

      async def receive(self, agent_name: str) -> List[AgentMessage]:
          """接收消息"""
          pass
  ```

**验证标准**:
- ✅ BaseAgentV2接口已设计
- ✅ 生命周期管理已设计
- ✅ 通信协议已定义
- ✅ 设计文档已完成

---

### Day 20-21: 编写Agent迁移指南

**任务**:
- [ ] 编写迁移步骤
  ```markdown
  # Agent迁移指南

  ## 迁移步骤

  ### 1. 创建新Agent类
  ```python
  # 从旧BaseAgent迁移到BaseAgentV2
  from core.agents.base_agent_v2 import BaseAgentV2

  class XiaonaAgentV2(BaseAgentV2):
      def __init__(self, config: AgentConfig):
          super().__init__(config)
          # 迁移初始化逻辑
  ```

  ### 2. 实现必需方法
  - process()
  - validate_request()
  - get_capabilities()

  ### 3. 迁移业务逻辑
  - 保留核心功能
  - 适配新接口

  ### 4. 测试验证
  - 单元测试
  - 集成测试
  - 性能测试

  ### 5. 灰度发布
  - 特性开关控制
  - 流量逐步切换
  - 监控指标
  ```

- [ ] 编写测试清单
  ```markdown
  # Agent迁移测试清单

  ## 单元测试
  - [ ] 初始化测试
  - [ ] 请求处理测试
  - [ ] 错误处理测试
  - [ ] 生命周期测试

  ## 集成测试
  - [ ] Agent间通信测试
  - [ ] 与Gateway集成测试
  - [ ] 与数据库集成测试

  ## 性能测试
  - [ ] 响应时间测试
  - [ ] 并发处理测试
  - [ ] 内存使用测试
  ```

**验证标准**:
- ✅ 迁移指南已完成
- ✅ 测试清单已完成
- ✅ 风险评估已完成

---

### Week 3-4 检查点

- [ ] Agent系统现状已调研
- [ ] 统一Agent接口已设计
- [ ] 迁移指南已完成
- [ ] 测试框架已准备

---

## 🔄 Week 5-10: 逐步迁移Agent (2026-05-20 ~ 2026-07-07)

### 目标

逐步将现有Agent迁移到统一接口,每次迁移一个Agent,确保系统稳定。

### Week 5-6: 迁移小娜Agent (2026-05-20 ~ 2026-06-02)

**任务**:
- [ ] 创建XiaonaAgentV2
  ```python
  # core/agents/xiaona_agent_v2.py
  from core.agents.base_agent_v2 import BaseAgentV2
  from core.agents.agent_models import AgentConfig, AgentResponse

  class XiaonaAgentV2(BaseAgentV2):
      """小娜Agent v2 - 法律专家"""

      def __init__(self, config: AgentConfig):
          super().__init__(config)
          # 初始化专利分析器
          # 初始化法律知识库
          # 初始化LLM客户端

      async def process(
          self,
          request: Dict[str, Any],
          context: Optional[AgentContext] = None
      ) -> AgentResponse:
          """处理法律分析请求"""
          # 1. 验证请求
          if not await self.validate_request(request):
              return AgentResponse(
                  success=False,
                  error="Invalid request"
              )

          # 2. 分析请求类型
          task_type = request.get("task_type")
          if task_type == "patent_analysis":
              return await self._analyze_patent(request)
          elif task_type == "legal_research":
              return await self._legal_research(request)
          else:
              return AgentResponse(
                  success=False,
                  error=f"Unknown task type: {task_type}"
              )

      async def validate_request(self, request: Dict[str, Any]) -> bool:
          """验证请求"""
          required_fields = ["task_type", "data"]
          return all(field in request for field in required_fields)

      def get_capabilities(self) -> List[str]:
          """获取能力列表"""
          return [
              "patent_analysis",
              "legal_research",
              "case_analysis",
              "document_generation"
          ]
  ```

- [ ] 迁移小娜核心功能
  - 专利分析
  - 法律检索
  - 案例分析
  - 文档生成

- [ ] 编写测试
  ```python
  # tests/test_xiaona_agent_v2.py
  import pytest
  from core.agents.xiaona_agent_v2 import XiaonaAgentV2
  from core.agents.agent_models import AgentConfig

  @pytest.mark.asyncio
  async def test_patent_analysis():
      """测试专利分析"""
      config = AgentConfig(name="xiaona")
      agent = XiaonaAgentV2(config)

      response = await agent.process({
          "task_type": "patent_analysis",
          "data": {"patent_id": "CN123456789A"}
      })

      assert response.success is True
      assert "analysis" in response.result
  ```

- [ ] 灰度发布
  ```python
  # 使用特性开关控制
  from core.features import feature_flag

  async def get_xiaona_agent():
      """获取小娜Agent实例"""
      if feature_flag.is_enabled("xiaona_v2", default=False):
          return XiaonaAgentV2(config)
      else:
          return XiaonaAgent(config)  # 旧版本
  ```

**验证标准**:
- ✅ XiaonaAgentV2实现完成
- ✅ 所有测试通过
- ✅ 性能无明显下降
- ✅ 灰度发布正常

---

### Week 7-8: 迁移小诺Agent (2026-06-03 ~ 2026-06-16)

**任务**:
- [ ] 创建XiaonuoAgentV2
  ```python
  # core/agents/xiaonuo_agent_v2.py
  from core.agents.base_agent_v2 import BaseAgentV2

  class XiaonuoAgentV2(BaseAgentV2):
      """小诺Agent v2 - 协调器"""

      def __init__(self, config: AgentConfig):
          super().__init__(config)
          # 初始化任务调度器
          # 初始化Agent编排器

      async def process(
          self,
          request: Dict[str, Any],
          context: Optional[AgentContext] = None
      ) -> AgentResponse:
          """处理协调请求"""
          task_type = request.get("task_type")

          if task_type == "coordinate_agents":
              return await self._coordinate_agents(request)
          elif task_type == "schedule_task":
              return await self._schedule_task(request)
          else:
              return AgentResponse(
                  success=False,
                  error=f"Unknown task type: {task_type}"
              )

      async def _coordinate_agents(self, request: Dict[str, Any]) -> AgentResponse:
          """协调多个Agent"""
          # 1. 解析任务
          # 2. 选择合适的Agent
          # 3. 分配任务
          # 4. 聚合结果
          pass
  ```

- [ ] 迁移小诺核心功能
  - 任务调度
  - Agent编排
  - 资源分配
  - 结果聚合

**验证标准**:
- ✅ XiaonuoAgentV2实现完成
- ✅ 所有测试通过
- ✅ 与其他Agent集成正常

---

### Week 9-10: 迁移云熙Agent及其他Agent (2026-06-17 ~ 2026-07-07)

**任务**:
- [ ] 迁移云熙Agent
- [ ] 迁移其他辅助Agent
- [ ] 验证所有Agent协同工作

**验证标准**:
- ✅ 所有Agent已迁移
- ✅ Agent间通信正常
- ✅ 系统功能完整

---

### Week 5-10 检查点

- [ ] 所有Agent已迁移到v2接口
- [ ] 测试覆盖率>75%
- [ ] 性能无明显下降
- [ ] 灰度发布完成

---

## 🏗️ Week 11: 明确Gateway-Core边界 (2026-07-08 ~ 2026-07-14)

### 目标

明确Gateway和Core的职责边界,消除重叠和模糊区域。

### Day 1-2: 分析Gateway和Core职责

**任务**:
- [ ] 分析Gateway职责
  - 路由和转发
  - 认证和授权
  - 限流和熔断
  - WebSocket管理

- [ ] 分析Core职责
  - 业务逻辑
  - 数据处理
  - Agent管理
  - 知识存储

- [ ] 识别重叠区域
  - 配置管理
  - 日志记录
  - 监控指标
  - 错误处理

**验证标准**:
- ✅ Gateway职责已明确
- ✅ Core职责已明确
- ✅ 重叠区域已识别

---

### Day 3-4: 设计清晰边界

**任务**:
- [ ] 定义Gateway职责
  ```yaml
  # Gateway职责定义
  gateway:
    routing:
      - 路径匹配
      - 负载均衡
      - 服务发现
    security:
      - 认证
      - 授权
      - API密钥验证
    control:
      - WebSocket管理
      - 会话管理
      - Canvas服务
    observability:
      - 访问日志
      - 性能指标
      - 健康检查
  ```

- [ ] 定义Core职责
  ```yaml
  # Core职责定义
  core:
    business_logic:
      - Agent管理
      - 任务处理
      - 工作流执行
    data:
      - 数据库操作
      - 缓存管理
      - 向量检索
    integration:
      - LLM调用
      - MCP服务器
      - 外部API
    domain:
      - 专利处理
      - 法律分析
      - 知识图谱
  ```

- [ ] 消除重叠
  - 配置管理: 统一到Core
  - 日志记录: Core负责业务日志,Gateway负责访问日志
  - 监控指标: Gateway提供基础设施指标,Core提供业务指标

**验证标准**:
- ✅ 职责边界已清晰定义
- ✅ 重叠已消除
- ✅ 设计文档已完成

---

### Day 5-7: 重构实现

**任务**:
- [ ] 重构配置管理
- [ ] 重构日志系统
- [ ] 重构监控指标

**验证标准**:
- ✅ 重构完成
- ✅ 测试通过
- ✅ 性能无明显影响

---

### Week 11 检查点

- [ ] Gateway-Core边界清晰
- [ ] 职责无重叠
- [ ] 文档完整

---

## 📁 Week 12: 扁平化目录结构 (2026-07-15 ~ 2026-07-21)

### 目标

扁平化目录结构,将文件嵌套深度从6层降至<4层。

### Day 1-2: 分析目录深度

**任务**:
- [ ] 统计所有目录层级
- [ ] 识别深度>4的目录
- [ ] 分析目录职责划分

**验证标准**:
- ✅ 深度统计完成
- ✅ 需要调整的目录已识别

---

### Day 3-5: 设计扁平化方案

**任务**:
- [ ] 设计新目录结构
  ```
  athena/
  ├── agents/              # Agent实现 (扁平化)
  │   ├── xiaona/
  │   ├── xiaonuo/
  │   └── yunxi/
  ├── core/               # 核心功能 (扁平化)
  │   ├── llm/
  │   ├── memory/
  │   ├── embedding/
  │   └── nlp/
  ├── patents/            # 专利处理 (已扁平化)
  ├── services/           # 服务 (扁平化)
  ├── gateway/            # Gateway (独立)
  └── shared/             # 共享工具
      ├── database/
      ├── cache/
      └── monitoring/
  ```

- [ ] 制定迁移计划

**验证标准**:
- ✅ 新结构已设计
- ✅ 迁移计划已制定

---

### Day 6-7: 执行扁平化

**任务**:
- [ ] 创建新目录结构
- [ ] 迁移文件
- [ ] 更新导入路径
- [ ] 运行测试

**验证标准**:
- ✅ 目录已扁平化
- ✅ 所有测试通过
- ✅ 最大深度<4层

---

### Week 12 检查点

- [ ] 目录结构扁平化
- [ ] 最大深度<4层
- ✅ 所有功能正常

---

## 📊 第4阶段总体验收标准

### 测试覆盖率

- [ ] 总体覆盖率>80%
- [ ] 核心模块覆盖率>90%
- [ ] CI/CD自动化测试通过

### Agent系统

- [ ] 所有Agent使用统一接口
- [ ] Agent间通信标准化
- [ ] Agent生命周期管理完善

### 架构清晰

- [ ] Gateway-Core边界清晰
- [ ] 职责无重叠
- [ ] 文档完整

### 代码质量

- [ ] 代码重复率<5%
- [ ] 文件嵌套深度<4层
- [ ] 配置文件数量<50个

### 性能指标

- [ ] API响应时间(P95)<100ms
- [ ] 向量检索延迟<50ms
- [ ] 缓存命中率>90%

---

## 🚨 风险管理

### 高风险任务

1. **Agent迁移** (Week 5-10)
   - 风险: 可能影响业务功能
   - 缓解: 灰度发布,特性开关

2. **Gateway-Core重构** (Week 11)
   - 风险: 可能影响系统集成
   - 缓解: 充分测试,逐步迁移

### 回滚计划

每个Agent迁移都是独立的,可以单独回滚:
```bash
# 回滚特定Agent
git revert <xiaona-v2-commit>
git revert <xiaonuo-v2-commit>
```

---

## 📝 交付物

### 文档

- [ ] PHASE4_DETAILED_EXECUTION_PLAN_20260421.md (本文档)
- [ ] TEST_COVERAGE_ANALYSIS_20260421.md
- [ ] AGENT_SYSTEM_ANALYSIS_20260421.md
- [ ] GATEWAY_CORE_BOUNDARY_ANALYSIS_20260421.md
- [ ] DIRECTORY_STRUCTURE_ANALYSIS_20260421.md
- [ ] PERFORMANCE_BASELINE_REPORT_20260421.md

### 代码

- [ ] 测试代码 (覆盖率>80%)
- [ ] AgentV2实现
- [ ] 重构后的Gateway-Core
- [ ] 扁平化后的目录结构

### 报告

- [ ] 周报 (每周)
- [ ] 阶段总结 (每2周)
- [ ] 最终验收报告

---

**计划制定时间**: 2026-04-21
**计划执行周期**: 2026-04-22 ~ 2026-07-21 (12周)
**负责人**: Claude Code (OMC模式)
**状态**: ✅ 已完成,待审核
