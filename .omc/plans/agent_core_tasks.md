# Agent-Core (A2) 任务包

> 主链路核心改造智能体
> 负责范围: 主链路改造、灰度开关接入、紧急修复、缓存优化、小流量灰度试点
> 启动条件: 立即启动（W1）
> 并行关系: 与 Agent-Infra (A1) 并行

---

## 上下文代码路径

| 文件 | 说明 |
|---|---|
| `core/api/prompt_system_routes.py:187-213` | 现有布尔开关 |
| `core/api/prompt_system_routes.py:429-600` | `generate_prompt()` 完整流程 |
| `core/api/prompt_system_routes.py:484-578` | 三源融合注入点 |
| `core/ai/prompts/__init__.py:155-165` | `evaluate_prompt_file()` 递归问题 |
| `core/capabilities/prompt_template_cache.py` | 提示词模板缓存 |
| `domains/legal/core_modules/legal_world_model/scenario_rule_retriever_optimized.py` | 场景规则检索器 |
| `domains/legal/core_modules/legal_world_model/scenario_identifier_optimized.py` | 场景识别器 |

---

## 任务 1.1.2: 替换原有布尔开关

**输出**: PR（改动 `core/api/prompt_system_routes.py`，接入 A1 的 `FusionRolloutConfig`）

**具体要求**:
1. 删除 `is_legal_prompt_fusion_enabled()` 的纯环境变量判断逻辑
2. 接入 A1 实现的 `FusionRolloutConfig`:
   ```python
   from core.legal_prompt_fusion.rollout_config import FusionRolloutConfig
   
   _rollout_config = FusionRolloutConfig.from_file("config/prompt_fusion_rollout.yaml")
   
   # 在 generate_prompt() 中使用
   if _rollout_config.should_enable(
       domain=context.domain.value,
       task_type=context.task_type.value,
       user_id=request.additional_context.get("user_id", "")
   ):
       # 启用融合
   ```
3. 向后兼容: `LEGAL_PROMPT_FUSION_ENABLED=true` 时，自动设置 `global_enabled=true, traffic_percentage=100`
4. 在 `generate_prompt()` 的第 484 行附近替换判断逻辑
5. 确保 `request.additional_context` 中可传递 `user_id` 用于 hash 分流

**验收检查清单**:
- [ ] 原有 `LEGAL_PROMPT_FUSION_ENABLED=true` 行为不变
- [ ] 新增配置文件可覆盖环境变量
- [ ] 单元测试通过（含向后兼容场景）
- [ ] 代码审查通过

---

## 任务 1.1.4: 主链路埋点实现

**输出**: PR（改动 `core/api/prompt_system_routes.py`）

**具体要求**:
1. 在 `generate_prompt()` 中增加融合指标收集:
   ```python
   fusion_metrics = FusionMetrics(
       request_id=request_id,
       domain=context.domain.value,
       task_type=context.task_type.value,
   )
   
   # 融合调用前
   fusion_start = time.monotonic()
   
   try:
       fusion_result = fusion_builder.build(...)
       fusion_metrics.latency_ms = (time.monotonic() - fusion_start) * 1000
       fusion_metrics.evidence_count = len(fusion_result.context.evidence)
       fusion_metrics.evidence_by_source = {
           "postgres": len(fusion_result.context.legal_articles),
           "neo4j": len(fusion_result.context.graph_relations),
           "wiki": len(fusion_result.context.wiki_background),
       }
       fusion_metrics.wiki_revision = fusion_result.context.freshness.get("wiki_revision", "unknown")
       fusion_metrics.template_version = fusion_result.template_version
   except Exception as e:
       fusion_metrics.latency_ms = (time.monotonic() - fusion_start) * 1000
       fusion_metrics.error = str(e)
   
   # 缓存命中状态
   fusion_metrics.cache_hit = cached_prompts is not None
   
   # 异步发送指标（不阻塞）
   asyncio.create_task(_send_metrics_async(fusion_metrics))
   ```
2. 指标发送失败不阻断主链路（try/except + warning 日志）
3. 融合关闭的请求也产生基线记录（fusion_enabled=false, latency_ms=0, evidence_count=0）

---

## 任务 1.2.3: OA 解读场景 5% 灰度试点

**输出**: 灰度运行报告

**具体要求**:
1. 与 A1 协作，配置灰度策略:
   ```yaml
   global_enabled: true
   domain_whitelist: [patent]
   task_type_whitelist: [office_action]
   traffic_percentage: 5
   ```
2. 部署到生产环境后持续观察 24 小时
3. 从日志或数据库中提取:
   - 开启融合的 20 条请求的 system_prompt 和响应
   - 未开启融合的 20 条请求的 system_prompt 和响应
4. 人工对比检查:
   - 融合证据块是否干扰输出格式
   - 响应质量是否有提升
   - 是否有异常延迟或错误
5. 记录 Dashboard 截图:
   - `fusion_avg_latency_ms` P95
   - `fusion_evidence_hit_rate`
   - `fusion_cache_hit_rate`
   - 错误率

**验收检查清单**:
- [ ] `fusion_avg_latency_ms` P95 < 300ms
- [ ] 无 500 错误归因于融合模块
- [ ] 人工抽检无"融合证据块干扰模型输出格式"案例
- [ ] 产出灰度运行报告（含数据、结论、下一步建议）

---

## 任务 1.2.4: 修复 `evaluate_prompt_file()` 递归问题

**输出**: Hotfix PR

**Bug 定位**: `core/ai/prompts/__init__.py` 第 155-165 行

```python
# 当前代码（有 bug）
def evaluate_prompt_file(file_path: str) -> QualityReport:
    return evaluate_prompt_file(Path(file_path))  # ← 无限递归！
```

**修复方案**（三选一，推荐方案 1）:

**方案 1**: 函数重命名
```python
def evaluate_prompt_file_path(file_path: str) -> QualityReport:
    return evaluate_prompt(Path(file_path))  # 或读取文件后调用 evaluate_prompt
```

**方案 2**: 使用完整 import 避免遮蔽
```python
from pathlib import Path as _Path

def evaluate_prompt_file(file_path: str) -> QualityReport:
    return evaluate_prompt(_Path(file_path))
```

**方案 3**: 合并为一个函数
```python
def evaluate_prompt_file(file_path: str | Path) -> QualityReport:
    path = Path(file_path)
    content = path.read_text(encoding="utf-8")
    return evaluate_prompt(content)
```

**验收检查清单**:
- [ ] 调用 `evaluate_prompt_file("some.md")` 不再递归溢出
- [ ] 单元测试通过（含正常路径、文件不存在路径）
- [ ] 回归测试通过
