# Agent-Budget (A5) 任务包

> 上下文预算与评估闭环智能体
> 负责范围: Context Budget 分配器、证据动态裁剪、质量指标、回滚机制、A/B 能力
> 启动条件: W11（依赖 Agent-Schema A4 完成变量治理）
> 并行关系: 最后阶段，串行于 A4 之后

---

## 上下文代码路径

| 文件 | 说明 |
|---|---|
| `core/api/prompt_system_routes.py:520-600` | 提示词生成后处理 |
| `core/legal_prompt_fusion/prompt_context_builder.py` | 融合上下文构建 |
| `core/legal_prompt_fusion/sync_manager.py` | 版本联动器 |
| `core/capabilities/prompt_template_cache.py` | 模板缓存 |

---

## 任务 4.1.1: 优先级槽位模型实现

**输出**: `core/prompt_engine/context_budget.py`

**具体要求**:
```python
from dataclasses import dataclass
from enum import IntEnum

class Priority(IntEnum):
    P0_REQUIRED = 0      # 基础身份、安全规则、任务目标、输出契约
    P1_HIGH_VALUE = 1    # 场景规则、必要业务流程、法条依据、融合证据
    P2_OPTIONAL = 2      # 相似案例、历史偏好、技术背景、长篇范例
    P3_DISPOSABLE = 3    # 宣传性描述、能力介绍、过多示例

@dataclass
class Slot:
    priority: Priority
    content: str
    estimated_tokens: int
    source: str           # 用于追踪和调试
    compressible: bool = False  # 是否允许截断/压缩

class ContextBudgetAllocator:
    def __init__(self, tokenizer=None):
        # tokenizer: 可选 tiktoken 编码器
        self.tokenizer = tokenizer
    
    def estimate_tokens(self, text: str) -> int:
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        # fallback: 字符数 / 4（中文场景近似）
        return len(text) // 4 + 1
    
    def allocate(self, slots: list[Slot], budget_tokens: int) -> list[Slot]:
        selected = []
        remaining = budget_tokens
        
        # 按优先级排序，同优先级按 estimated_tokens 升序（先装小的）
        sorted_slots = sorted(slots, key=lambda s: (s.priority, s.estimated_tokens))
        
        for slot in sorted_slots:
            if slot.estimated_tokens <= remaining:
                selected.append(slot)
                remaining -= slot.estimated_tokens
            elif slot.compressible and slot.priority <= Priority.P2_OPTIONAL:
                # 尝试压缩后装入
                compressed = self._compress_slot(slot, remaining)
                if compressed:
                    selected.append(compressed)
                    remaining -= compressed.estimated_tokens
        
        return selected
    
    def _compress_slot(self, slot: Slot, max_tokens: int) -> Slot | None:
        # 简单压缩：截断内容
        max_chars = max_tokens * 4  # 粗略估计
        if max_chars < 20:  # 太小的空间不值得装
            return None
        compressed_content = slot.content[:max_chars] + "..."
        return Slot(
            priority=slot.priority,
            content=compressed_content,
            estimated_tokens=self.estimate_tokens(compressed_content),
            source=f"{slot.source} (compressed)",
            compressible=False,
        )
    
    def build_prompt(self, selected_slots: list[Slot]) -> str:
        # 按原始优先级排序输出
        ordered = sorted(selected_slots, key=lambda s: s.priority)
        return "\n\n".join(s.content for s in ordered)
```

**复杂度分层预算**:
```python
COMPLEXITY_BUDGET = {
    "simple": 3000,
    "medium": 6000,
    "complex": 10000,
}
```

**验收检查清单**:
- [ ] P0 槽位在 budget 不足时仍全部保留
- [ ] P3 槽位在 budget 紧张时优先丢弃
- [ ] token 估算误差 < 10%（若使用 tiktoken）

---

## 任务 4.1.2: 三源融合证据动态裁剪

**输出**: PR（改动 `core/api/prompt_system_routes.py` 和 `core/prompt_engine/context_budget.py`）

**具体要求**:
1. 将融合证据块拆解为独立 Slot:
   ```python
   slots = []
   
   # P0: 基础身份（来自场景规则 system_prompt_template 的基础部分）
   slots.append(Slot(Priority.P0_REQUIRED, base_identity, estimated_tokens, "base_identity"))
   
   # P0: 安全规则（HITL 等）
   slots.append(Slot(Priority.P0_REQUIRED, safety_rules, estimated_tokens, "safety"))
   
   # P0: 任务目标
   slots.append(Slot(Priority.P0_REQUIRED, task_objective, estimated_tokens, "objective"))
   
   # P1: 场景规则详情
   slots.append(Slot(Priority.P1_HIGH_VALUE, scenario_details, estimated_tokens, "scenario"))
   
   # P1: 融合证据（动态裁剪重点）
   for article in fusion_result.context.legal_articles:
       content = f"### 法律条文\n- {article.headline}: {article.summary}"
       slots.append(Slot(Priority.P1_HIGH_VALUE, content, estimate_tokens(content), "fusion_postgres", compressible=True))
   
   for relation in fusion_result.context.graph_relations:
       content = f"### 图谱关系\n- {relation.headline}: {relation.summary}"
       slots.append(Slot(Priority.P1_HIGH_VALUE, content, estimate_tokens(content), "fusion_neo4j", compressible=True))
   
   for wiki in fusion_result.context.wiki_background:
       content = f"### Wiki 背景\n- {wiki.headline}: {wiki.summary}"
       slots.append(Slot(Priority.P1_HIGH_VALUE, content, estimate_tokens(content), "fusion_wiki", compressible=True))
   ```

2. 根据 complexity 限制证据数量:
   ```python
   complexity = request.additional_context.get("complexity", "medium")
   max_evidence = {"simple": 3, "medium": 8, "complex": 12}[complexity]
   
   # 先按相关性排序（使用 fusion_result 中的 score）
   all_evidence = sorted(all_evidence, key=lambda e: e.score, reverse=True)
   all_evidence = all_evidence[:max_evidence]
   ```

3. 超出 budget 时的裁剪策略:
   - 优先截断 summary（保留 headline 和 citation）
   - 极端情况下降级为列表形式："相关法条: X 条，详见知识库"

**验收检查清单**:
- [ ] simple 任务 system_prompt 总 token < 3000（抽样验证）
- [ ] complex 任务保留全部关键证据，无 truncation 导致信息丢失
- [ ] 按 complexity 的证据上限生效

---

## 任务 4.1.3: Token 估算器集成

**输出**: PR

**具体要求**:
1. 安装 tiktoken（若尚未安装）: `pip install tiktoken`
2. 在 `ContextBudgetAllocator` 中集成:
   ```python
   import tiktoken
   
   class ContextBudgetAllocator:
       def __init__(self, model: str = "gpt-4"):
           try:
               self.tokenizer = tiktoken.encoding_for_model(model)
           except KeyError:
               self.tokenizer = tiktoken.get_encoding("cl100k_base")
       
       def estimate_tokens(self, text: str) -> int:
           return len(self.tokenizer.encode(text))
   ```
3. 在 `generate_prompt()` 返回前估算总 token:
   ```python
   total_tokens = allocator.estimate_tokens(system_prompt) + allocator.estimate_tokens(user_prompt)
   if total_tokens > budget:
       logger.warning(f"Token budget exceeded: {total_tokens} > {budget}")
   ```

**验收检查清单**:
- [ ] token 估算误差 < 10%（对比实际 API 消耗的 usage.prompt_tokens）

---

## 任务 4.2.1: 线上质量指标埋点

**输出**: 指标埋点 PR + Dashboard

**具体要求**:
1. 在 LLM 调用后收集响应质量信号:
   ```python
   # 在调用 LLM API 后
   quality_signals = {
       "request_id": request_id,
       "prompt_version": rule.template_version,
       "fusion_enabled": fusion_enabled,
       "response_length": len(response_content),
       "has_json": _has_json_structure(response_content),
       "has_citations": _has_citations(response_content),
   }
   ```

2. 用户反馈收集（若产品层面有反馈入口）:
   ```python
   # 用户点赞/点踩
   user_feedback = {
       "request_id": request_id,
       "rating": 1 | -1 | None,  # 点赞/点踩/无反馈
       "edited": bool,  # 用户是否编辑了回答
       "followup_count": int,  # 追问次数
   }
   ```

3. 定义以下指标的计算方式:
   - `first_answer_acceptance_rate` = 无追问且未编辑的回答数 / 总回答数
   - `followup_rate` = 有追问的回答数 / 总回答数
   - `json_contract_pass_rate` = 输出通过 JSON schema 验证的次数 / 总 JSON 输出请求数
   - `tool_call_success_rate` = 工具调用成功次数 / 总工具调用次数
   - `user_satisfaction_score` = 平均显式评分（如有）或隐式信号加权

4. 接入现有 BI 系统，Dashboard 支持按 prompt version 对比

---

## 任务 4.2.2: Prompt Version Rollback 机制

**输出**: 回滚 API + 脚本 + 手册

**具体要求**:
1. 版本存储:
   ```python
   # 每次更新场景规则时，将旧版本存入版本存储
   class PromptVersionStore:
       def save_version(self, rule_id: str, template_version: str, 
                        system_template: str, user_template: str):
           # 存储到对象存储（S3/MinIO）或数据库 blob
           ...
       
       def get_version(self, rule_id: str, template_version: str) -> dict:
           ...
       
       def list_versions(self, rule_id: str, limit: int = 10) -> list[str]:
           ...
   ```

2. 回滚 API:
   ```python
   @router.post("/rules/rollback")
   async def rollback_rule(request: RollbackRequest):
       store = PromptVersionStore()
       old_version = store.get_version(request.rule_id, request.target_version)
       
       # 更新 Neo4j 中的规则模板
       db_manager.update_rule_template(
           request.rule_id,
           old_version["system_template"],
           old_version["user_template"],
           old_version["template_version"],
       )
       
       # 清除缓存
       prompt_cache.clear_rule(request.rule_id)
       
       # 审计日志
       audit_log.info(f"Rule {request.rule_id} rolled back to {request.target_version} by {current_user}")
       
       return {"success": True, "rule_id": request.rule_id, "version": request.target_version}
   ```

3. 回滚 CLI 工具:
   ```bash
   python scripts/prompt_rollback.py --rule-id patent.oa.analysis --version patent.oa.analysis:abc123
   ```

**验收检查清单**:
- [ ] 回滚操作在 30 秒内生效
- [ ] 回滚后缓存不返回旧版本内容
- [ ] 回滚操作记录审计日志

---

## 任务 4.2.3: A/B 测试能力

**输出**: A/B 配置模块

**具体要求**:
1. 在灰度配置基础上扩展:
   ```yaml
   # config/prompt_fusion_rollout.yaml 扩展
   experiments:
     - name: oa_analysis_v3
       rule_id: patent.oa.analysis
       control_version: "2.1.0"
       treatment_version: "3.0.0"
       traffic_split: [50, 50]  # control, treatment
       auto_terminate:
         enabled: true
         error_rate_threshold: 0.05  # treatment 错误率比 control 高 5% 时自动终止
   ```

2. 在 `generate_prompt()` 中根据实验配置选择版本:
   ```python
   experiment = experiment_config.get_experiment(rule.rule_id)
   if experiment and experiment.is_active():
       variant = experiment.assign_variant(request.user_id or request_id)
       rule = version_store.get_version(rule.rule_id, variant.version)
   ```

3. 实验报告自动生成:
   - 每日对比 control vs treatment 的核心指标
   - 实验终止时自动切回 control 并通知
