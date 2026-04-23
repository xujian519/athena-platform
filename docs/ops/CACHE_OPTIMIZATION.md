# Prompt System 缓存优化策略

> 基于 `reports/cprofile_stats.txt`（Python 3.11 cProfile）与 `reports/performance_profile.txt` 的代码级分析，制定 Athena Prompt System 的缓存优化方案。

## 一、当前热点分析（cProfile 关键发现）

根据 `python3.11 -m cProfile` 对 `generate_prompt` 关键路径的 500 次迭代分析（见 `reports/cprofile_stats.txt`）：

| 阶段 | cumtime 占比 | 单次开销（代码级） | 实际生产延迟（估算） | 瓶颈类型 |
|---|---|---|---|---|
| 场景识别 (`identify_scenario`) | ~53 % | ~0.17 ms（regex fallback） | **~50 ms**（BGE-M3 编码） | CPU / ML |
| 规则检索 (`retrieve_rule`) | ~20 % | ~0.07 ms（本地缓存命中） | **~30 ms**（Neo4j Cypher） | IO |
| 变量治理 (`sanitize_variables`) | ~18 % | ~0.07 ms | ~5 ms | CPU（regex） |
| 缓存查询 (`cache.get`) | ~3 % | ~0.01 ms | <1 ms | 内存 |
| 模板渲染 (`substitute_variables`) | ~2 % | ~0.006 ms | ~1 ms | CPU |
| 变量校验 (`validate`) | ~1 % | ~0.004 ms | <1 ms | CPU |

> **关键结论**：生产环境中 80% 以上延迟来自**场景识别（BGE-M3）**与**规则检索（Neo4j）**两大外部依赖，二者合计约 80 ms。本地代码开销（变量治理 + 渲染 + 校验）在 10 ms 以内。

---

## 二、三级缓存架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      三级缓存架构                            │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│   L1 意图   │  L2 规则    │  L3 提示词  │   L0 启动预热     │
│   缓存      │  缓存       │  模板缓存   │   （配置级）      │
├─────────────┼─────────────┼─────────────┼───────────────────┤
│ key: user_  │ key: domain │ key: domain │ 服务启动时读取    │
│ input SHA256│ +task_type  │ +task_type  │ config/prompt_    │
│ value:      │ +phase      │ +phase      │ fusion_rollout    │
│ domain/     │ value:      │ +variables  │ .yaml 中高频组合  │
│ task_type/  │ ScenarioRule│ hash        │ 预生成并写入 L3   │
│ phase/conf  │ 对象        │ value:      │                   │
│             │             │ system/user │                   │
├─────────────┼─────────────┼─────────────┼───────────────────┤
│ TTL: 600s   │ TTL: 300s   │ TTL: 3600s  │ 一次性，启动后    │
│ 容量: 2000  │ 容量: 500   │ 容量: 2000  │ 30s 内完成        │
│ 策略: LRU   │ 策略: LRU   │ 策略: LRU   │                   │
└─────────────┴─────────────┴─────────────┴───────────────────┘
```

---

## 三、热点规则预加载策略

### 3.1 预加载目标

在服务启动后 **30 秒内**将 L3（提示词模板缓存）命中率提升至 **> 85%**。

### 3.2 高频组合清单

基于 `tests/load/locustfile.py` 的压测权重与业务实际流量，定义以下高频 `domain + task_type + phase` 组合：

```yaml
# config/prompt_fusion_rollout.yaml 预加载配置段
preload_rules:
  - domain: patent
    task_type: office_action
    phase: examination
    weight: 0.50          # 对应 locust 50% 权重
    typical_variables:
      application_number: "CN202310000000.0"
      technical_field: "人工智能"
      office_action_type: "第一次审查意见通知书"

  - domain: patent
    task_type: creativity_analysis
    phase: examination
    weight: 0.30
    typical_variables:
      application_number: "CN202320000000.1"
      technical_field: "新能源材料"

  - domain: patent
    task_type: novelty_analysis
    phase: examination
    weight: 0.20
    typical_variables:
      application_number: "CN202330000000.2"
      technical_field: "半导体"
```

### 3.3 预热实现逻辑

```python
# 建议在 core/api/prompt_system_routes.py 或独立 lifespan 中调用

import asyncio
from core.capabilities.prompt_template_cache import get_prompt_cache
from core.legal_world_model.scenario_rule_retriever_optimized import ScenarioRuleRetrieverOptimized

PRELOAD_RULES = [...]  # 如上 YAML 解析结果

async def _preload_hot_prompts(retriever: ScenarioRuleRetrieverOptimized):
    """异步预热高频提示词模板（不阻塞服务启动）。"""
    cache = get_prompt_cache()
    for rule_spec in PRELOAD_RULES:
        rule = retriever.retrieve_rule(
            rule_spec.domain,
            rule_spec.task_type,
            rule_spec.phase,
        )
        if not rule:
            continue
        # 使用典型变量构造缓存键并预渲染
        system_prompt, user_prompt = rule.substitute_variables(
            rule_spec.typical_variables
        )
        cache.set(
            domain=rule_spec.domain,
            task_type=rule_spec.task_type,
            phase=rule_spec.phase,
            variables=rule_spec.typical_variables,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            scenario_rule_id=rule.rule_id,
        )
    logger.info(f"预热完成: 已预加载 {len(PRELOAD_RULES)} 条高频规则")
```

### 3.4 预热验证

```bash
# 启动后检查缓存命中率
curl -s http://localhost:8000/api/v1/prompt-system/cache/stats | jq '.hit_rate'
# 预期: 启动后立即 > 80%
```

---

## 四、TTL 与失效策略

| 缓存层级 | TTL | 失效触发条件 | 主动刷新策略 |
|---|---|---|---|
| L1 意图缓存 | **600 s** | 新领域/任务类型上线 | 蓝绿部署时全量清空 |
| L2 规则缓存 | **300 s** | Neo4j 规则更新 | 规则编辑后发送 `cache-invalidate` 事件 |
| L3 提示词模板 | **3600 s** | 模板版本变更 | 模板发布流水线自动清空对应 domain 缓存 |
| L0 启动预热 | 无（常驻） | 服务重启 | 每次启动重新执行 |

### 4.1 分层失效原则

1. **L2 规则更新** → 级联清空该 `domain+task_type+phase` 对应的 L3 条目，避免旧模板与新规则不匹配。
2. **L1 意图更新** → 无需级联，因为 L1 仅缓存识别结果，不影响规则与模板正确性。
3. **L3 模板更新** → 仅清空自身，不影响 L1/L2。

### 4.2 兜底失效（Emergency Purge）

```bash
# 紧急清空全部缓存（线上发现异常输出时）
curl -X POST http://localhost:8000/api/v1/prompt-system/cache/clear

# 清空指定 domain 缓存（细粒度）
curl -X POST http://localhost:8000/api/v1/prompt-system/cache/clear \
  -H "Content-Type: application/json" \
  -d '{"domain": "patent", "task_type": "office_action"}'
```

---

## 五、缓存命中率预测

基于 cProfile 分析中各组件开销与压测任务权重，预测不同并发下的缓存表现：

| 并发用户 | L1 意图命中 | L2 规则命中 | L3 模板命中 | **综合命中** | 说明 |
|---|---|---|---|---|---|
| 10 | 55 % | 80 % | 65 % | **~65 %** | 冷启动后首次压测，预热尚不充分 |
| 50 | 68 % | 88 % | 72 % | **~72 %** | 用户输入多样性增加，L1 命中下降 |
| 100 | 75 % | 92 % | 78 % | **~78 %** | 高频意图收敛，但长尾输入拉高 miss |
| 200 | 78 % | 94 % | 82 % | **~82 %** | 缓存充分预热，接近理论上限 |

> **优化目标**：实施 L0 启动预热 + L1 意图缓存后，100 并发下综合命中率应从 78% 提升至 **> 85%**。

---

## 六、优化建议优先级

| 优先级 | 优化项 | 预期收益 | 实施难度 | 负责人 |
|---|---|---|---|---|
| P0 | 引入 L1 意图识别缓存（SHA256 key, TTL 600s） | P50 降低 ~45 ms | 低 | 研发 |
| P0 | 引入 L2 规则缓存（LRU 500, TTL 300s） | P50 降低 ~25 ms | 低 | 研发 |
| P1 | L0 启动预热（高频 3 组合预加载） | 缓存命中率 +10% | 低 | 研发 |
| P1 | 变量治理 regex 预编译（已在 sanitizer 实现） | CPU 降低 ~5% | 已落地 | — |
| P2 | L3 容量扩容（1000 → 2000） | 长尾命中 +3% | 极低 | 研发 |
| P2 | 异步并行预热（非阻塞服务启动） | 启动时间不变 | 中 | 研发 |

---

## 七、附录：cProfile 命令参考

```bash
# 生成原始 stats（可用 snakeviz 可视化）
python3.11 -m cProfile -o reports/cprofile_stats.raw scripts/cprofile_generate_prompt.py

# 直接查看文本报告
python3.11 -m cProfile -s cumulative scripts/cprofile_generate_prompt.py

# 使用 snakeviz 交互式火焰图（需安装）
pip install snakeviz
snakeviz reports/cprofile_stats.raw
```

---

> 本文档版本: v1.0  
> 最后更新: 2026-04-23  
> 基于: Python 3.11 cProfile + `reports/performance_profile.txt`  
