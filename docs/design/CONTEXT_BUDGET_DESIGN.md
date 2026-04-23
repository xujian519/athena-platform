# Context Budget 架构设计 (B3-Budget)

> 版本: v1.0  
> 状态: 设计 & 核心实现完成  
> 目标: 在融合链路中防止上下文 token 超限，并在必要时触发降级回滚。

---

## 1. 背景与问题

当前多源融合链路（法律条文 + 案例 + Wiki）在检索阶段可能返回大量证据。若直接拼接入 prompt，易导致：
- **Token 超限**：超出模型上下文窗口，触发 API 错误。
- **信息冗余**：低相关性证据稀释核心信息密度。
- **响应延迟**：过长上下文增加推理时间与首 token 延迟。

因此需要一套 **Context Budget Manager**，在 prompt 构建前对证据进行预算分配、裁剪与降级。

---

## 2. 设计目标

| 目标 | 说明 |
|------|------|
| Budget 分配 | 将总 token budget 拆分为 system / user / evidence / output / overhead |
| 动态调整 | 短 user_query 的剩余额度可转移给 evidence |
| 证据裁剪 | 按相关性排序，低分证据优先移除，保留核心条数 |
| 回滚触发 | 超限 / 证据不足 / 超时 三类场景自动降级为单源模式 |
| 可观测 | 输出 budget_usage_ratio、evidence_dropped_count、rollback_reason |
| 零侵入 | 不修改 `prompt_system_routes.py`，以独立 manager 提供集成点 |

---

## 3. 架构 overview

```
┌─────────────────────────────────────────────────────────────┐
│                    ContextBudgetManager                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ BudgetAlloc  │  │ EvidenceTrunc│  │RollbackTrigger│       │
│  │  (分配/校准)  │  │  (裁剪算法)   │  │  (降级决策)   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│         │                 │                  │                │
│         └─────────────────┴──────────────────┘                │
│                             │                                 │
│                    ┌─────────────────┐                        │
│                    │  BudgetMetrics  │                        │
│                    │ (观测指标输出)   │                        │
│                    └─────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. 模块详解

### 4.1 BudgetAllocation（预算分配模型）

```python
@dataclass
class BudgetAllocation:
    system_prompt: int   # 系统提示词预留
    user_query: int      # 用户输入预留
    evidence: int        # 证据块预留（动态可扩展）
    output_buffer: int   # 模型输出预留
    overhead: int        # 格式标记、换行、JSON 开销
```

**默认模板**（按总 budget 自动匹配）：

| 总 Budget | system | user | evidence | output | overhead |
|-----------|--------|------|----------|--------|----------|
| 8K        | 1024   | 512  | 4096     | 1024   | 512      |
| 16K       | 1536   | 1024 | 8192     | 2048   | 768      |
| 32K       | 2048   | 2048 | 18432    | 4096   | 1024     |

**动态校准逻辑**：
1. 用 `TokenEstimator` 测量实际 `system_prompt` 与 `user_query` 长度。
2. `system_prompt` 按实际值校准（上限为原配额 2 倍）。
3. `user_query` 若有剩余额度，且 `enable_dynamic_shift=True`，则转移至 `evidence`。
4. 最终各组件之和不超过 `total_budget`。

### 4.2 EvidenceTruncator（证据裁剪算法）

**输入**：`List[EvidenceItem]`，每条证据携带 `relevance_score`（0.0 ~ 1.0）。

**策略**：
1. **排序**：按 `relevance_score` 降序排列；同分按内容长度升序（短的优先保留）。
2. **累加**：依次计算 token，累加到 `target_budget` 为止。
3. **保底**：无条件保留 `min_core_count` 条（即使超限也不在此处截断，交由 RollbackTrigger 判定）。
4. **输出**：`TruncationResult`，包含 `kept`、`dropped`、`tokens_before`、`tokens_after`。

**复杂度**：O(n log n)，主要由排序决定；n 为证据条数，通常 < 100，性能可忽略。

### 4.3 RollbackTrigger（回滚触发器）

**三类触发条件及优先级**：

| 优先级 | 条件 | 降级模式 | 说明 |
|--------|------|----------|------|
| P0 | `elapsed_ms > timeout_ms`（默认 200ms） | `single_source` | 超时回滚，与 budget 联动 |
| P1 | `evidence_tokens > evidence_budget`（裁剪后仍超限） | `single_source` | Token 超限回滚 |
| P2 | `evidence_kept_count < min_core_threshold` | `single_source` | 证据不足回滚 |

**降级路径**：
```
multi_source (三源融合) ──► single_source (单源精简) ──► aborted (直接中止)
```
当前实现中 `single_source` 为默认降级目标；上层调用方可根据 `RollbackDecision.target_mode` 进一步处理。

### 4.4 TokenEstimator（Token 估算）

**双模策略**：
- **首选**：`tiktoken` (`cl100k_base`)，适用于 GPT-4 / Claude 等兼容 tokenizer。
- **回退**：字符启发式
  - ASCII: 4 字符 ≈ 1 token
  - CJK: 1.5 字符 ≈ 1 token
  - 其他: 2 字符 ≈ 1 token

回退方案在多数法律文本场景下误差 < 20%，足以支撑 budget 管理（无需精确到 1 token）。

---

## 5. 使用示例

```python
from core.prompt_engine.budget import ContextBudgetManager, EvidenceItem

# 1. 初始化 manager（8K budget，至少保留 2 条核心证据）
mgr = ContextBudgetManager(
    total_budget=8192,
    min_core_evidence=2,
    timeout_ms=200.0,
)

# 2. 构造证据（通常由检索层提供）
evidence = [
    EvidenceItem(content="专利法第22条...", relevance_score=0.95, source="law"),
    EvidenceItem(content="案例A判决书摘要...", relevance_score=0.80, source="case"),
    EvidenceItem(content="背景知识...", relevance_score=0.30, source="wiki"),
]

# 3. 构建上下文
result = mgr.build_context(
    system_prompt="你是一名专利分析专家...",
    user_query="请分析方案X的创造性",
    evidence_list=evidence,
    elapsed_ms=45.0,  # 从上游传入实际耗时
)

# 4. 读取结果与指标
kept_evidence = result["evidence"]          # 裁剪后保留的证据
metrics = result["metrics"]                 # BudgetMetrics
rollback = result["rollback"]               # RollbackDecision

print(f"预算使用率: {metrics.budget_usage_ratio:.2%}")
print(f"丢弃证据数: {metrics.evidence_dropped_count}")
print(f"回滚原因: {metrics.rollback_reason}")
print(f"建议模式: {result['target_mode']}")
```

---

## 6. 指标与观测

`BudgetMetrics` 输出以下字段，便于接入 Prometheus / Grafana 或日志系统：

| 字段 | 类型 | 说明 |
|------|------|------|
| `budget_total` | int | 总 budget |
| `budget_used` | int | 实际使用估算 token |
| `budget_usage_ratio` | float | 使用率（0.0 ~ 1.0） |
| `evidence_count_before` | int | 原始证据条数 |
| `evidence_count_after` | int | 裁剪后证据条数 |
| `evidence_dropped_count` | int | 被丢弃证据条数 |
| `rollback_reason` | str \| None | 回滚原因枚举值或 None |
| `target_mode` | str | 建议执行模式 |
| `elapsed_ms` | float \| None | 上游传入的处理耗时 |

---

## 7. 测试覆盖

单元测试位于 `tests/prompt_engine/test_context_budget.py`，覆盖：

1. **TokenEstimator**：空文本、纯 ASCII、CJK、混合文本的估算。
2. **EvidenceTruncator**：
   - 高分证据优先保留
   - 低分证据被丢弃
   - `min_core_count` 保底
   - 同分短内容优先
   - 空列表边界
3. **RollbackTrigger**：
   - 健康状态（不回滚）
   - Token 超限回滚
   - 证据不足回滚
   - 超时回滚
   - 超时优先级高于超限
4. **ContextBudgetManager**：
   - 8K / 16K / 32K 默认分配
   - 自定义分配
   - 无证据场景
   - 正常多证据裁剪
   - 强制回滚（极紧 budget）
   - 动态 budget 转移
   - Metrics 采集
   - 超时联动

---

## 8. 约束与兼容性

- **Python 3.9**：使用 `typing.List`、`Optional`、`Dict` 等，不使用 `|` 联合语法。
- **无强制依赖**：`tiktoken` 为可选依赖；未安装时自动回退到近似估算。
- **模块隔离**：所有代码位于 `core/prompt_engine/budget/`，不修改现有路由文件。
- **线程安全**：`ContextBudgetManager` 实例本身无共享可变状态，可在多线程/协程中复用（但 `last_metrics` 会被覆盖，需按请求独立实例或加锁）。

---

## 9. 未来扩展

| 扩展点 | 说明 |
|--------|------|
| 模型级 tokenizer | 支持按具体模型（GPT-4 / Claude / 自研）选择 encoder |
| 多级降级 | `single_source` 可细分为 `law_only`、`case_only`、`wiki_only` |
| 自适应 budget | 根据历史命中率动态调整 evidence / output 比例 |
| 流式 evidence | 支持边检索边裁剪，而非全量拿到后再处理 |
| A/B 观测 | 将 metrics 写入实验平台，对比不同裁剪策略对回答质量的影响 |

---

## 10. 文件清单

| 文件 | 职责 |
|------|------|
| `core/prompt_engine/budget/__init__.py` | 模块导出入口 |
| `core/prompt_engine/budget/utils.py` | TokenEstimator（tiktoken + 近似回退） |
| `core/prompt_engine/budget/truncation.py` | EvidenceTruncator 裁剪算法 |
| `core/prompt_engine/budget/rollback.py` | RollbackTrigger 回滚触发器 |
| `core/prompt_engine/budget/manager.py` | ContextBudgetManager 主控 + BudgetMetrics |
| `tests/prompt_engine/test_context_budget.py` | 单元测试 |
| `docs/design/CONTEXT_BUDGET_DESIGN.md` | 本文档 |
