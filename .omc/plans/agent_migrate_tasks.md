# Agent-Migrate (A3) 任务包

> 旧链路清理与资产迁移智能体
> 负责范围: 调用矩阵梳理、deprecated 标记、异步错配修复、v4 资产迁移、调用方迁移、债务清理
> 启动条件: W3（依赖 Agent-Core A2 完成主链路改造）
> 并行关系: 可与 Agent-Schema (A4) 后半段并行

---

## 上下文代码路径

| 文件 | 说明 |
|---|---|
| `core/ai/prompts/progressive_loader.py` | 渐进式加载器（遗留）|
| `core/ai/prompts/unified_prompt_manager.py` | 统一管理器（遗留，含 async load_prompt / optimize_prompt）|
| `core/ai/prompts/unified_prompt_manager_extended.py` | 扩展管理器（遗留）|
| `core/ai/prompts/unified_prompt_manager_production.py` | 生产管理器（遗留）|
| `core/ai/prompts/integrated_prompt_generator.py` | 集成生成器（遗留）|
| `core/ai/prompts/capability_integrated_prompt_generator.py` | 能力集成生成器（遗留）|
| `prompts/foundation/hitl_protocol_v4_constraint_repeat.md` | v4 资产 |
| `prompts/capability/cap04_inventive_v2_with_whenToUse.md` | v4 资产 |
| `prompts/business/task_2_1_oa_analysis_v2_with_parallel.md` | v4 资产 |
| `domains/legal/core_modules/legal_world_model/scenario_rule_retriever_optimized.py` | 场景规则检索器（目标迁移地）|

---

## 任务 2.1.1: 全量调用矩阵梳理

**输出**: `docs/reports/PROMPT_RUNTIME_MATRIX.md`

**具体操作步骤**:
1. 在项目根目录执行以下 grep 命令:
   ```bash
   grep -rn "progressive_loader" --include="*.py" . | grep -v "__pycache__" | grep -v ".pyc" > /tmp/calls_progressive.txt
   grep -rn "unified_prompt_manager" --include="*.py" . | grep -v "__pycache__" | grep -v ".pyc" > /tmp/calls_upm.txt
   grep -rn "integrated_prompt_generator" --include="*.py" . | grep -v "__pycache__" | grep -v ".pyc" > /tmp/calls_ipg.txt
   grep -rn "capability_integrated_prompt_generator" --include="*.py" . | grep -v "__pycache__" | grep -v ".pyc" > /tmp/calls_cipg.txt
   ```
2. 按调用方分类统计:
   - 业务模块（core/framework/agents/ 等）
   - 测试文件（tests/）
   - 脚本（scripts/）
   - 其他
3. 对每个调用方标注:
   - 当前功能描述（一句话）
   - 迁移目标（主链路 API / 场景规则 / 直接删除）
   - 预估工作量（高/中/低）
   - 是否阻塞 Phase 2 完成

**验收检查清单**:
- [ ] 调用矩阵覆盖 100% 的导入点
- [ ] 每个调用方标注完整

---

## 任务 2.1.2: 标记 Deprecated

**输出**: PR（纯标记，不改逻辑）

**具体操作**:
1. 在以下文件顶部添加 deprecation warning:
   ```python
   import warnings
   
   warnings.warn(
       "This module is deprecated and will be removed in v3.0. "
       "Use core.api.prompt_system_routes.generate_prompt() instead.",
       DeprecationWarning,
       stacklevel=2,
   )
   ```
   - `core/ai/prompts/progressive_loader.py`
   - `core/ai/prompts/unified_prompt_manager.py`
   - `core/ai/prompts/unified_prompt_manager_extended.py`
   - `core/ai/prompts/unified_prompt_manager_production.py`
   - `core/ai/prompts/integrated_prompt_generator.py`
   - `core/ai/prompts/capability_integrated_prompt_generator.py`
2. 在 `core/ai/prompts/__init__.py` 中注释说明:
   ```python
   __all__ = [
       # ...
       "evaluate_prompt_file",  # TODO: deprecated, use core.prompt_engine.validators
       # ...
   ]
   ```
3. 新建 `docs/reports/PROMPT_DEPRECATION_LIST.md`，列出所有 deprecated 模块和迁移路径

**验收检查清单**:
- [ ] 导入 deprecated 模块时产生 `DeprecationWarning`
- [ ] CI 不因此失败

---

## 任务 2.1.3: 异步调用错配修复决策

**输出**: `docs/decisions/ASYNC_FIX_DECISION.md`

**问题定位**:

| 文件 | 行号 | 问题 |
|---|---|---|
| `integrated_prompt_generator.py` | 212 | `self.unified_prompt_manager.optimize_prompt(...)` 同步调用 async 方法 |
| `integrated_prompt_generator.py` | 276 | `self.unified_prompt_manager.load_prompt(...)` 同步调用 async 方法 |
| `unified_prompt_manager_extended.py` | 209 | `self.load_prompt(...)` 同步调用 async 方法 |
| `unified_prompt_manager_production.py` | 457 | `self.load_prompt(...)` 同步调用 async 方法 |

**方案评估**:

| 方案 | 优点 | 缺点 | 推荐度 |
|---|---|---|---|
| A: 加 await | 正确修复，保留原设计 | 需将整条调用链改为 async，影响面极大 | ★★☆ |
| B: 改为 sync | 影响面小，快速修复 | 内部可能仍有异步 IO，需用 asyncio.run 包装 | ★★★ |
| C: 废弃调用点 | 彻底清理旧链路，推动迁移 | 需确保主链路能替代这些功能 | ★★★★（推荐）|

**推荐方案 C 的具体路径**:
1. `load_prompt("xiaona", PromptFormat.MARKDOWN)` → 迁移为主链路的 L1-L4 角色注入
2. `optimize_prompt(content, target)` → Lyra 优化能力评估是否仍在使用，若使用则迁移为主链路的可选后处理步骤
3. 若某些调用方确实仍需旧链路功能，则选择方案 B 作为过渡修复

**验收检查清单**:
- [ ] 决策文档通过技术评审
- [ ] 明确每个错配点的修复路径

---

## 任务 2.2.1: 执行异步错配修复

**输出**: PR

**按决策执行**:
- 若选方案 B（改为 sync）:
  ```python
  # unified_prompt_manager.py 中
  def load_prompt(self, name: str, format: PromptFormat) -> str:
      # 将 async 实现改为 sync，内部若需 await 则使用 asyncio.run() 或重构为 sync IO
      ...
  ```
- 若选方案 C（废弃调用点）:
  1. 在 `integrated_prompt_generator.py` 中移除对 `unified_prompt_manager` 的调用
  2. 用主链路 `generate_prompt()` 替代
  3. 若 `Lyra 优化` 仍需保留，则在主链路中增加可选的后处理步骤

**验收检查清单**:
- [ ] 修复后异步方法不再被同步调用（`grep -n "\.load_prompt\|\.optimize_prompt"` 验证是否都在 async 函数中）
- [ ] 相关单元测试通过
- [ ] 无新增 500 错误

---

## 任务 2.2.2: v4 资产转化为场景规则模板

**输出**: Neo4j 场景规则模板（3 个）

**具体操作**:

1. **HITL Protocol v4 → Safety 基础块**:
   - 读取 `prompts/foundation/hitl_protocol_v4_constraint_repeat.md`
   - 将内容作为 `safety_block` 字段，附加到全部场景规则的 `system_prompt_template` 末尾
   - 不单独建场景规则，而是作为通用注入块

2. **Cap04 Inventive v2 → 创造性分析场景规则**:
   - 读取 `prompts/capability/cap04_inventive_v2_with_whenToUse.md`
   - 拆分为 `system_prompt_template` 和 `user_prompt_template`
   - 提取 `whenToUse` 条件作为场景触发条件
   - 变量占位符替换为 `{var}` 格式（先兼容当前主链路，Phase 3 再统一升级 Jinja2）
   - 写入 Neo4j: `domain="patent"`, `task_type="inventive_analysis"`

3. **Task 2.1 OA Analysis v2 → OA 解读场景规则**:
   - 读取 `prompts/business/task_2_1_oa_analysis_v2_with_parallel.md`
   - 同上处理
   - 写入 Neo4j: `domain="patent"`, `task_type="office_action"`

**场景规则数据结构参考**:
```python
@dataclass
class ScenarioRule:
    rule_id: str
    domain: str
    task_type: str
    phase: str
    system_prompt_template: str
    user_prompt_template: str
    capability_invocations: list[str]
    # 新增字段（用于后续 PromptSpec 兼容）
    template_version: str = "1.0.0"
    variable_schema: dict = field(default_factory=dict)
```

**验收检查清单**:
- [ ] 3 个模板可通过 `ScenarioRuleRetrieverOptimized.retrieve_rule()` 正常检索
- [ ] `substitute_variables()` 替换后输出与原 Markdown 语义一致
- [ ] 人工验证 5 条请求的 system_prompt 质量不低于原静态模板

---

## 任务 2.3.1: 低风险调用方迁移

**输出**: PR

**具体操作**:
1. 从调用矩阵中筛选:
   - 仅导入但未实际使用的代码点 → 直接删除导入
   - 单元测试中调用旧链路 → 替换为直接 mock 或调用主链路 API
   - 脚本/工具中调用旧链路 → 评估是否仍在使用，废弃的删除
2. 每次改动后跑 `pytest` 确认无回归

---

## 任务 2.3.2: 中风险调用方迁移

**输出**: PR

**具体操作**:
1. 选取 2-3 个核心业务代理，例如:
   - `core/framework/agents/xiaona/patent_drafting_prompts.py`
   - `prompts/agents/xiaona/novelty_analyzer_prompts.py`
2. 分析其 `get_system_prompt()` 方法:
   - 若内容较简单 → 直接替换为对主链路 `generate_prompt()` 的调用
   - 若内容复杂且有独特逻辑 → 提取为 Markdown，接入场景规则库，然后替换调用
3. 对比迁移前后的输出:
   ```python
   # 自动化 diff 测试
   def test_migration_parity():
       old_output = old_get_system_prompt(case)
       new_output = new_get_system_prompt(case)
       similarity = compute_similarity(old_output, new_output)
       assert similarity > 0.95
   ```

---

## 任务 3.5.3: 技术债务清理（W10）

**输出**: 债务清理 PR

**具体操作**:
1. 删除已确认无调用的 dead code（根据调用矩阵和 deprecated 标记）
2. 补齐核心模块 docstring（`core/legal_prompt_fusion/` 全部模块）
3. 修复 ruff/mypy 警告:
   ```bash
   ruff check core/legal_prompt_fusion/ core/api/prompt_system_routes.py
   mypy core/legal_prompt_fusion/ core/api/prompt_system_routes.py
   ```
4. 更新架构文档 `docs/architecture/prompt-system.md`:
   - 更新架构图（包含三源融合）
   - 描述主链路流程
   - 标注 deprecated 模块
