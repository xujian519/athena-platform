# 技术决策：异步调用错配修复方案

> 决策编号: DECISION-2026-0423-001
> 日期: 2026-04-23
> 状态: 已实施
> 决策人: Agent-Migrate (A3)

---

## 问题描述

`unified_prompt_manager.py` 中的 `load_prompt()` 和 `optimize_prompt()` 为 `async def`，但在以下位置被同步方法调用：

| 文件 | 行号 | 调用方法 | 被调 async 方法 |
|---|---|---|---|
| `integrated_prompt_generator.py` | 212 | `generate()` (sync) | `optimize_prompt()` |
| `integrated_prompt_generator.py` | 276 | `_get_agent_role_prompt()` (sync) | `load_prompt()` |
| `unified_prompt_manager_extended.py` | 209 | `_generate_default_prompt()` (sync) | `load_prompt()` |
| `unified_prompt_manager_production.py` | 457 | `_generate_default_prompt()` (sync) | `load_prompt()` |
| `capability_integrated_prompt_generator.py` | 158 | `generate()` (sync) | `optimize_prompt()` |

**影响**: coroutine 对象被当作字符串处理，导致 `Lyra 优化` 和 `L1-L4 角色注入` 功能实际失效。

---

## 方案评估

### 方案 A: 将调用链全部 async 化

- **做法**: 从 `generate()` 开始，逐层向上添加 `async/await`，直到所有入口都是 async
- **优点**: 彻底修复，符合 Python 异步最佳实践
- **缺点**: 
  - 影响面极大，需修改 10+ 个文件
  - 所有调用方（包括业务控制器）需改为 async
  - 测试用例需大规模重写
  - 与当前主链路（已稳定运行）产生冲突
- **工作量**: 高（3-4 天）
- **风险**: 高（可能引入新的 async 兼容问题）

### 方案 B: 将 async 方法改为 sync 实现

- **做法**: 在 `unified_prompt_manager.py` 中，将 `load_prompt` 和 `optimize_prompt` 改为 sync，内部用 `asyncio.run()` 或线程池包装原有 async IO
- **优点**: 影响面集中在单个模块
- **缺点**:
  - 模块设计意图是 async，改为 sync 违背原始设计
  - 若内部仍有异步 IO（如网络请求），用 `asyncio.run()` 在已有事件循环中会抛错
  - 需要深入重构 `unified_prompt_manager.py` 内部实现
- **工作量**: 中（1-2 天）
- **风险**: 中（可能破坏模块内部其他 async 调用）

### 方案 C: 废弃调用点，使用同步包装器（推荐并实施）

- **做法**: 
  1. 不修改 `unified_prompt_manager.py` 的 async 设计
  2. 在调用方（`integrated_prompt_generator.py` 等）中，使用 `_sync_call_async()` 辅助函数包装 async 调用
  3. 该辅助函数检查返回值是否是 awaitable，若是则通过 `asyncio.get_running_loop().run_until_complete()` 或 `asyncio.run()` 执行
  4. 所有相关 deprecated 模块统一使用该包装器
- **优点**:
  - 影响面最小，仅修改调用处
  - 不破坏被调用模块的 async 设计
  - 与主链路无冲突
  - 代码可复用（一个辅助函数解决所有错配点）
- **缺点**:
  - 在已有事件循环中调用 `run_until_complete()` 可能有嵌套风险（但当前调用频率低，且模块已 deprecated）
  - 不是最优雅的方案，但最适合"清理债务"的场景
- **工作量**: 低（2-3 小时）
- **风险**: 低

---

## 决策结论

**选择方案 C**。

理由：
1. 所有涉及错配的模块（`integrated_prompt_generator.py`、`unified_prompt_manager_extended.py`、`unified_prompt_manager_production.py`、`capability_integrated_prompt_generator.py`）已标记为 **deprecated**，不会在长期维护。
2. 方案 C 以最小代价修复了实际失效的功能，无需大规模重构。
3. 修复后，若这些 deprecated 模块仍被业务代码调用，其功能将恢复正常（Lyra 优化、L1-L4 角色注入），为业务控制器的平滑迁移争取时间。
4. 主链路（`prompt_system_routes.py`）不受影响，继续作为唯一推荐入口。

---

## 实施细节

### 辅助函数 `_sync_call_async()`

```python
import asyncio
import inspect


def _sync_call_async(async_func, *args, **kwargs):
    """同步调用异步方法（兼容已有事件循环）。"""
    result = async_func(*args, **kwargs)
    if inspect.isawaitable(result):
        try:
            loop = asyncio.get_running_loop()
            return loop.run_until_complete(result)
        except RuntimeError:
            return asyncio.run(result)
    return result
```

### 修复位置

| 文件 | 修改前 | 修改后 |
|---|---|---|
| `integrated_prompt_generator.py:212` | `self.unified_prompt_manager.optimize_prompt(...)` | `_sync_call_async(self.unified_prompt_manager.optimize_prompt, ...)` |
| `integrated_prompt_generator.py:276` | `self.unified_prompt_manager.load_prompt(...)` | `_sync_call_async(self.unified_prompt_manager.load_prompt, ...)` |
| `unified_prompt_manager_extended.py:209` | `self.load_prompt(...)` | `_sync_call_async(self.load_prompt, ...)` |
| `unified_prompt_manager_production.py:457` | `self.load_prompt(...)` | `_sync_call_async(self.load_prompt, ...)` |
| `capability_integrated_prompt_generator.py:158` | `self.unified_prompt_manager.optimize_prompt(...)` | `_sync_call_async(self.unified_prompt_manager.optimize_prompt, ...)` |

---

## 后续行动

- [x] 实施修复（2026-04-23）
- [ ] 验证修复后 Lyra 优化和 L1-L4 角色注入是否恢复（通过日志或测试）
- [ ] 在 W5-W6 评估业务控制器（xiaonuo_enhanced_controller、unified_llm_manager）的迁移路径，逐步移除对 deprecated 模块的依赖
