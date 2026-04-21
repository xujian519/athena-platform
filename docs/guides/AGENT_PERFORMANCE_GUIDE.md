# Agent性能基准指南

> **版本**: v1.0.0
> **创建时间**: 2026-04-21
> **维护者**: Athena平台团队

---

## 目录

1. [概述](#概述)
2. [性能基准目标](#性能基准目标)
3. [测试方法](#测试方法)
4. [本地运行测试](#本地运行测试)
5. [CI/CD集成](#cicd集成)
6. [性能优化建议](#性能优化建议)
7. [性能基准数据](#性能基准数据)

---

## 概述

Agent性能基准测试系统用于监控和确保Athena平台中所有Agent的性能表现。该系统覆盖Agent生命周期的各个方面，包括初始化、执行、吞吐量和资源使用。

### 测试覆盖范围

| 测试类别 | 测试内容 | 目标 |
|---------|---------|------|
| **初始化性能** | Agent创建和初始化时间 | <100ms (P95) |
| **执行性能** | Agent处理请求的时间 | <5s (P95) |
| **能力发现** | `get_capabilities()` 调用时间 | <5ms (P95) |
| **输入验证** | `validate_input()` 调用时间 | <50ms (P95) |
| **内存使用** | 单Agent实例内存占用 | <500MB |
| **吞吐量** | 并发处理能力 | >10 QPS |

### 已迁移Agent

以下Agent已纳入性能测试体系：

| Agent | 状态 | 测试覆盖 |
|-------|------|---------|
| `RetrieverAgent` | ✅ 已迁移 | 完整 |
| `AnalyzerAgent` | ✅ 已迁移 | 完整 |
| `WriterAgent` | ✅ 已迁移 | 完整 |
| `XiaonuoAgentV2` | ✅ 已迁移 | 完整 |
| `PatentSearchAgentV2` | ✅ 已迁移 | 完整 |
| `YunxiIPAgentV3` | ✅ 已迁移 | 完整 |

---

## 性能基准目标

### 响应时间目标

```
┌─────────────────────────────────────────────────────────┐
│  响应时间分布图 (目标值)                                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Agent初始化                                            │
│  ├─ P50:  50ms   ██████████                            │
│  ├─ P95: 100ms   ███████████████████                   │
│  └─ P99: 150ms   █████████████████████████             │
│                                                         │
│  Agent执行                                              │
│  ├─ P50: 2000ms  ████████████████████████████████████  │
│  ├─ P95: 5000ms  ████████████████████████████████████████████████████████████████████  │
│  └─ P99: 8000ms  (长尾情况)                             │
│                                                         │
│  能力发现                                               │
│  ├─ P50:   1ms   █                                     │
│  ├─ P95:   5ms   ██████                                │
│  └─ P99:  10ms   ██████████                            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 吞吐量目标

| 指标 | 目标 | 说明 |
|------|------|------|
| Agent创建 | >10 agents/s | 顺序创建Agent的速率 |
| 并发初始化 | >10 QPS | 并发创建Agent的速率 |
| 能力发现 | >100 ops/s | `get_capabilities()` 调用速率 |
| Agent操作 | >100 ops/s | 一般Agent操作速率 |

### 资源使用目标

| 资源 | 限制 | 说明 |
|------|------|------|
| 内存 | <500MB/Agent | 单Agent实例内存占用 |
| CPU | <50%/Agent | 单Agent处理时的CPU使用 |

---

## 测试方法

### 测试架构

```
┌─────────────────────────────────────────────────────────┐
│                   性能测试架构                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  pytest ──→ test_agent_performance.py                   │
│                  │                                      │
│                  ├─ TestAgentInitializationPerformance  │
│                  ├─ TestCapabilityDiscoveryPerformance  │
│                  ├─ TestAgentInfoPerformance            │
│                  ├─ TestInputValidationPerformance      │
│                  ├─ TestMemoryUsage                     │
│                  ├─ TestAgentThroughput                 │
│                  ├─ TestEndToEndPerformance             │
│                  └─ TestPerformanceBaseline             │
│                                                         │
│  测试标记 (markers):                                    │
│  ├── @pytest.mark.performance - 性能测试标记            │
│  ├── @pytest.mark.initialization - 初始化测试           │
│  ├── @pytest.mark.capability - 能力测试                 │
│  ├── @pytest.mark.throughput - 吞吐量测试               │
│  ├── @pytest.mark.memory - 内存测试                    │
│  └── @pytest.mark.e2e - 端到端测试                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 性能指标计算

```python
# 性能指标数据结构
@dataclass
class PerformanceMetrics:
    name: str
    samples: list[float] = field(default_factory=list)

    # 统计指标
    @property
    def min(self) -> float: ...      # 最小值
    @property
    def max(self) -> float: ...      # 最大值
    @property
    def avg(self) -> float: ...      # 平均值
    @property
    def median(self) -> float: ...   # 中位数 (P50)
    @property
    def p95(self) -> float: ...      # 95分位数
    @property
    def p99(self) -> float: ...      # 99分位数
    @property
    def std_dev(self) -> float: ...  # 标准差
```

### 基准比较逻辑

```python
def check_benchmark(metrics, benchmark):
    """检查是否符合基准"""
    return {
        "p50_pass": metrics.median <= benchmark.target_p50,
        "p95_pass": metrics.p95 <= benchmark.target_p95,
        "p99_pass": metrics.p99 <= benchmark.target_p99,
        "overall_pass": (
            metrics.median <= benchmark.target_p50 and
            metrics.p95 <= benchmark.target_p95 and
            metrics.p99 <= benchmark.target_p99
        )
    }
```

---

## 本地运行测试

### 快速开始

```bash
# 运行所有性能测试
pytest tests/performance/test_agent_performance.py -v

# 只运行性能测试（使用marker）
pytest tests/performance/test_agent_performance.py -m performance

# 运行特定类别的测试
pytest tests/performance/test_agent_performance.py::TestAgentInitializationPerformance -v
pytest tests/performance/test_agent_performance.py -m "initialization" -v
pytest tests/performance/test_agent_performance.py -m "throughput" -v

# 运行特定Agent的测试
pytest tests/performance/test_agent_performance.py -k "RetrieverAgent" -v

# 生成详细输出
pytest tests/performance/test_agent_performance.py -v -s
```

### 使用pytest-benchmark

```bash
# 安装依赖
pip install pytest-benchmark

# 运行基准测试
pytest tests/performance/test_agent_performance.py --benchmark-only

# 生成基准报告
pytest tests/performance/test_agent_performance.py \
  --benchmark-only \
  --benchmark-autosave \
  --benchmark-save-data

# 比较基准数据
pytest tests/performance/test_agent_performance.py \
  --benchmark-only \
  --benchmark-compare \
  --benchmark-load=previous_run.json
```

### 直接运行

```bash
# 作为脚本运行
python tests/performance/test_agent_performance.py
```

---

## CI/CD集成

### GitHub Actions工作流

性能测试通过GitHub Actions自动运行：

**触发条件**:
- 推送到 `main` 或 `develop` 分支
- 针对 `main` 或 `develop` 的PR
- 每天UTC 4:00 (北京时间12:00)
- 手动触发

**测试任务**:
```
┌──────────────────────────────────────────────────┐
│  agent-performance.yml 工作流                    │
├──────────────────────────────────────────────────┤
│                                                  │
│  ⚡ initialization-performance                  │
│  ├─ 安装依赖                                     │
│  ├─ 运行初始化性能测试                           │
│  └─ 上传结果                                     │
│                                                  │
│  🚀 execution-performance                       │
│  ├─ 启动PostgreSQL和Redis服务                   │
│  ├─ 运行执行性能测试                             │
│  └─ 上传结果                                     │
│                                                  │
│  📊 throughput-test                             │
│  ├─ 运行吞吐量测试                               │
│  └─ 上传结果                                     │
│                                                  │
│  💾 memory-test                                 │
│  ├─ 运行内存使用测试                             │
│  └─ 上传结果                                     │
│                                                  │
│  🔍 capability-test                             │
│  ├─ 运行能力发现测试                             │
│  └─ 上传结果                                     │
│                                                  │
│  🔄 e2e-test                                    │
│  ├─ 运行端到端测试                               │
│  └─ 上传结果                                     │
│                                                  │
│  📈 baseline-comparison                         │
│  ├─ 下载所有测试结果                             │
│  ├─ 生成性能报告                                 │
│  └─ 发布摘要到GitHub                            │
│                                                  │
│  🔍 regression-check                           │
│  └─ PR时检测性能回归                            │
│                                                  │
│  🏆 badge-generation                            │
│  └─ 更新性能徽章                                 │
│                                                  │
└──────────────────────────────────────────────────┘
```

### 查看测试结果

1. **GitHub Actions页面**: 查看工作流运行详情
2. **Pull Request检查**: 自动显示性能测试状态
3. **性能徽章**: `docs/badges/agent-performance.svg`
4. **性能报告**: `reports/agent_performance_report.json`

---

## 性能优化建议

### 初始化性能优化

**问题**: Agent初始化时间超过100ms

**可能原因**:
1. 复杂的依赖注入
2. 重量级资源加载（模型、配置）
3. 同步I/O操作

**解决方案**:
```python
# ❌ 不好的做法
class SlowAgent(BaseXiaonaComponent):
    def _initialize(self):
        # 同步加载大型配置
        with open("large_config.json") as f:
            self.config = json.load(f)
        # 加载模型
        self.model = load_large_model()

# ✅ 好的做法
class FastAgent(BaseXiaonaComponent):
    def _initialize(self):
        # 延迟初始化配置
        self._config_path = "large_config.json"
        self._model = None
        self._config_cache = None

    @property
    def config(self):
        if self._config_cache is None:
            with open(self._config_path) as f:
                self._config_cache = json.load(f)
        return self._config_cache

    @property
    def model(self):
        if self._model is None:
            self._model = load_large_model()
        return self._model
```

### 能力发现优化

**问题**: `get_capabilities()` 调用时间超过5ms

**解决方案**:
```python
# ✅ 缓存能力列表
class OptimizedAgent(BaseXiaonaComponent):
    def _initialize(self):
        self._register_capabilities([...])
        # 第一次调用后缓存结果
        self._capabilities_cache = None

    def get_capabilities(self) -> list[AgentCapability]:
        if self._capabilities_cache is None:
            self._capabilities_cache = super().get_capabilities()
        return self._capabilities_cache
```

### 内存使用优化

**问题**: Agent内存使用超过500MB

**解决方案**:
```python
# ✅ 使用弱引用和限制缓存大小
import weakref
from functools import lru_cache

class MemoryEfficientAgent(BaseXiaonaComponent):
    def __init__(self, agent_id: str, config: dict | None = None):
        super().__init__(agent_id, config)
        # 限制缓存大小
        self._result_cache = lru_cache(maxsize=100)(self._compute_result)
        # 使用弱引用
        self._weak_refs = weakref.WeakValueDictionary()

    def _compute_result(self, key: str):
        # 实际计算逻辑
        pass
```

### 并发性能优化

**问题**: 吞吐量低于10 QPS

**解决方案**:
```python
# ✅ 使用异步处理
import asyncio

class AsyncOptimizedAgent(BaseXiaonaComponent):
    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        # 并发处理多个任务
        results = await asyncio.gather(
            self._process_task1(context),
            self._process_task2(context),
            self._process_task3(context),
        )
        return self._aggregate_results(results)
```

---

## 性能基准数据

### 当前基准数据

**数据文件**: `tests/data/agent_performance_baseline.json`

```json
{
  "timestamp": "2026-04-21T00:00:00",
  "benchmarks": {
    "agent_initialization": {
      "target_p50": 50,
      "target_p95": 100,
      "target_p99": 150
    },
    "agent_execution": {
      "target_p50": 2000,
      "target_p95": 5000,
      "target_p99": 8000
    },
    "capability_discovery": {
      "target_p50": 1,
      "target_p95": 5,
      "target_p99": 10
    }
  }
}
```

### 更新基准数据

```bash
# 运行基准测试并保存结果
pytest tests/performance/test_agent_performance.py::TestPerformanceBaseline::test_save_current_metrics -v -s
```

### 性能历史数据

性能历史数据保存在 `reports/agent_performance_report.json`，包含：

- 时间戳
- 工作流ID
- 各测试任务状态
- 实际性能指标
- 与基准的对比

---

## 附录

### 依赖项

```toml
[tool.poetry.dev-dependencies]
pytest = "^7.0"
pytest-benchmark = "^4.0"
pytest-asyncio = "^0.21"
psutil = "^5.9"
```

### 测试标记定义

```ini
# pytest.ini
[pytest]
markers =
    performance: 性能基准测试
    initialization: Agent初始化性能测试
    execution: Agent执行性能测试
    capability: 能力发现性能测试
    throughput: 吞吐量测试
    memory: 内存使用测试
    e2e: 端到端性能测试
    benchmark: 基准数据管理测试
```

### 故障排除

**问题1**: 测试失败因为LLM服务不可用

```bash
# 设置mock模式
export ATHENA_MOCK_MODE=true
pytest tests/performance/test_agent_performance.py -v
```

**问题2**: 内存测试不稳定

```python
# 在测试前强制垃圾回收
gc.collect()
baseline_memory = get_memory_mb()
```

**问题3**: 性能波动大

```bash
# 增加样本数量
pytest tests/performance/test_agent_performance.py -v \
  --benchmark-min-rounds=10 \
  --benchmark-max-time=30
```

---

**维护者**: Athena平台团队
**最后更新**: 2026-04-21
