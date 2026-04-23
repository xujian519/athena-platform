# Agent-QA (A6) 任务包

> 质量保障智能体
> 负责范围: 测试用例设计、回归测试、性能压测、灰度验证、稳定性保障
> 启动条件: 贯穿全程，W10 集中发力
> 并行关系: 与所有智能体协作，独立执行测试任务

---

## 上下文代码路径

| 文件 | 说明 |
|---|---|
| `tests/` | 现有测试目录 |
| `core/api/prompt_system_routes.py` | 主链路 API（测试重点）|
| `core/legal_prompt_fusion/` | 三源融合模块（测试重点）|
| `.github/workflows/` | CI 配置 |

---

## 贯穿全程的任务

### 测试用例设计（W1 开始，持续迭代）

**输出**: `tests/prompt_engine/` 测试套件

**核心测试场景**:

1. **主链路端到端测试** (`tests/prompt_engine/test_generate_prompt.py`):
   ```python
   class TestGeneratePrompt:
       def test_basic_flow(self, client):
           """基本流程: 场景识别 → 规则检索 → 提示词生成"""
           response = client.post("/api/v1/prompt-system/prompt/generate", json={
               "user_input": "分析这个审查意见",
               "additional_context": {"application_number": "CN20231001"}
           })
           assert response.status_code == 200
           data = response.json()
           assert "system_prompt" in data
           assert "user_prompt" in data
           assert data["domain"] == "patent"
       
       def test_fusion_enabled(self, client, monkeypatch):
           """融合开启时返回的证据块非空"""
           monkeypatch.setenv("LEGAL_PROMPT_FUSION_ENABLED", "true")
           response = client.post(...)
           assert "融合知识上下文" in response.json()["system_prompt"]
       
       def test_fusion_degradation(self, client, mock_broken_postgres):
           """PostgreSQL 故障时融合不阻断"""
           response = client.post(...)
           assert response.status_code == 200
       
       def test_cache_hit(self, client):
           """相同请求第二次命中缓存"""
           req = {...}
           r1 = client.post(..., json=req)
           r2 = client.post(..., json=req)
           assert r2.json()["cached"] is True
       
       def test_missing_variables(self, client):
           """缺失 required 变量返回 400"""
           response = client.post(..., json={"user_input": "分析"})  # 缺少 application_number
           assert response.status_code == 400
           assert "MISSING_VARIABLES" in response.json()["error"]
   ```

2. **三源融合测试** (`tests/prompt_engine/test_legal_prompt_fusion.py`):
   ```python
   class TestLegalPromptFusion:
       def test_postgres_retrieval(self):
           ...
       
       def test_neo4j_retrieval(self):
           ...
       
       def test_wiki_retrieval(self):
           ...
       
       def test_hybrid_ranking(self):
           """混合排序权重正确"""
           ...
       
       def test_source_degradation(self):
           """单源降级"""
           ...
   ```

3. **变量治理测试** (`tests/prompt_engine/test_validators.py`):
   ```python
   class TestVariableValidator:
       def test_required_missing(self):
           ...
       
       def test_type_mismatch(self):
           ...
       
       def test_max_length_exceeded(self):
           ...
       
       def test_injection_detected(self):
           ...
   ```

4. **Context Budget 测试** (`tests/prompt_engine/test_context_budget.py`):
   ```python
   class TestContextBudget:
       def test_p0_always_included(self):
           ...
       
       def test_budget_exceeded_drops_p3(self):
           ...
       
       def test_simple_complexity_limits_evidence(self):
           ...
   ```

---

## W1-W2 任务: 灰度试点验证

**配合 A2 执行**:

1. 准备灰度测试数据集:
   - 50 条 OA 解读请求（覆盖常见子场景）
   - 50 条创造性分析请求
   - 50 条新颖性分析请求

2. 自动化对比脚本:
   ```python
   def compare_fusion_on_off(test_cases: list[dict]) -> dict:
       results = {"fusion_on": [], "fusion_off": []}
       for case in test_cases:
           # 强制开启融合
           on_result = call_generate_prompt(case, force_fusion=True)
           # 强制关闭融合
           off_result = call_generate_prompt(case, force_fusion=False)
           results["fusion_on"].append(on_result)
           results["fusion_off"].append(off_result)
       return results
   ```

3. 质量评估维度:
   - 响应时间对比
   - 输出格式稳定性
   - 法条引用准确率（人工抽检）
   - 用户满意度（如有反馈数据）

---

## W6 任务: 主链路唯一化验证

**配合 A3 执行**:

1. 导入检查:
   ```bash
   # 验证非测试/非 deprecated 代码中无旧链路导入
   grep -rn "from core.ai.prompts.progressive_loader" core/ --include="*.py" | grep -v "test" | grep -v "deprecated"
   grep -rn "from core.ai.prompts.unified_prompt_manager" core/ --include="*.py" | grep -v "test" | grep -v "deprecated"
   ```

2. 集成测试:
   - 全量 pytest 通过
   - 端到端测试覆盖 10 个核心场景

3. 压测:
   ```bash
   # 使用 locust 或 k6
   locust -f tests/load/locustfile.py --host=http://localhost:8000
   ```
   - QPS: 10 → 50 → 100
   - 持续时间: 10 分钟
   - 目标: P95 延迟 < 1000ms，错误率 < 0.1%

---

## W9 任务: Phase 3 验收测试

**配合 A4 执行**:

1. Jinja2 渲染器对比测试:
   - 将现有 `{var}` 模板和升级后的 `{{ var }}` 模板用相同变量渲染
   - 100% 对比通过（除空格外完全一致）

2. 变量校验器压力测试:
   - 1000 条随机变量组合，校验器不崩溃
   - 所有 required 缺失场景被正确拦截

3. 注入安全测试:
   - 准备 20 条 injection 测试用例（含 10 种已知模式 + 10 种变体）
   - 准备 100 条正常业务输入
   - 检测率 > 80%，误报率 < 5%

---

## W10 任务: 稳定性保障周（集中发力）

### 全链路回归测试

**执行清单**:
- [ ] 单元测试: `pytest tests/unit/prompt_engine/ -v`
- [ ] 集成测试: `pytest tests/integration/prompt_engine/ -v`
- [ ] 端到端测试: `pytest tests/e2e/test_prompt_generation.py -v`
- [ ] 旧链路回归: 确认 deprecated 模块的 warning 正常产生但不影响功能

### 性能基线建立

**压测配置** (`tests/load/locustfile.py`):
```python
from locust import HttpUser, task, between

class PromptSystemUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def generate_prompt_oa(self):
        self.client.post("/api/v1/prompt-system/prompt/generate", json={
            "user_input": "分析这个审查意见，申请号 CN20231001",
            "additional_context": {"application_number": "CN20231001"}
        })
    
    @task(1)
    def generate_prompt_inventive(self):
        self.client.post("/api/v1/prompt-system/prompt/generate", json={
            "user_input": "评估这个方案的创造性",
        })
```

**压测执行**:
```bash
# 基线测试
locust -f tests/load/locustfile.py --host=http://staging.example.com -u 10 -r 2 -t 10m

# 逐步加压
locust -f tests/load/locustfile.py --host=http://staging.example.com -u 50 -r 5 -t 10m

# 峰值测试
locust -f tests/load/locustfile.py --host=http://staging.example.com -u 100 -r 10 -t 5m
```

**记录指标**:
| 指标 | 10用户 | 50用户 | 100用户 |
|---|---|---|---|
| RPS | | | |
| P50 延迟 | | | |
| P95 延迟 | | | |
| P99 延迟 | | | |
| 错误率 | | | |
| CPU 使用率 | | | |
| 内存使用 | | | |

### 故障演练

**演练场景**:
1. **PostgreSQL 故障**: 断掉 PG 连接，验证融合降级 + 告警触发
2. **Wiki 索引损坏**: 模拟 Wiki 目录为空，验证 evidence_hit_rate 下降 + 告警
3. **缓存雪崩**: 批量清除缓存，验证系统不崩溃、延迟可恢复
4. **配置热重载失败**: 写入非法 YAML，验证系统使用旧配置继续运行

---

## W12 任务: 结项验收

**验收检查清单**:
- [ ] 全阶段验收标准 100% 达成（对照 MASTER_CHECKLIST）
- [ ] 性能基线对比：P95 延迟不劣于项目启动前
- [ ] 代码覆盖率：核心模块 > 80%
- [ ] 文档完整性：架构文档、运维手册、API 文档已更新
- [ ] 知识沉淀：技术决策文档、经验教训已归档
