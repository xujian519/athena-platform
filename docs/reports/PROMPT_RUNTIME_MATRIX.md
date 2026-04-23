# Prompt Runtime 调用矩阵

> 生成时间: 2026-04-23
> 范围: 全仓库 Python 文件（排除测试和 __pycache__）
> 目的: 识别旧链路调用方，为主链路收口提供迁移依据

---

## 1. progressive_loader

| 调用方 | 行号 | 用途 | 迁移目标 | 工作量 | 阻塞 Phase 2 |
|---|---|---|---|---|---|
| `core/ai/prompts/__init__.py:18` | 导入导出 | 模块入口聚合 | 删除导入 | 低 | 否 |
| `core/prompts/__init__.py:19` | 导入导出 | 模块入口聚合（复制） | 删除导入 | 低 | 否 |
| `core/ai/prompts/test_optimization.py:23` | 测试 | 性能测试 | 删除或替换为 mock | 低 | 否 |
| `core/prompts/test_optimization.py:23` | 测试 | 性能测试（复制） | 删除或替换为 mock | 低 | 否 |

**结论**: `progressive_loader` 调用极少，主要被 `__init__.py` 聚合导出。清理 `__init__.py` 后即可标记为废弃。

---

## 2. unified_prompt_manager

| 调用方 | 行号 | 用途 | 迁移目标 | 工作量 | 阻塞 Phase 2 |
|---|---|---|---|---|---|
| `core/xiaonuo_enhanced_controller.py:46` | 业务 | 初始化 prompt_manager | 主链路 API | **高** | **是** |
| `core/llm/unified_llm_manager.py:111` | 业务 | 初始化 prompt_manager | 主链路 API | **高** | **是** |
| `core/ai/llm/unified_llm_manager.py:111` | 业务 | 初始化 prompt_manager（复制） | 主链路 API | **高** | **是** |
| `core/ai/prompts/integrated_prompt_generator.py:125` | 内部 | 作为参数传入 | 移除参数，使用主链路 | 中 | 否 |
| `core/ai/prompts/integrated_prompt_generator.py:209` | 内部 | Lyra optimize_prompt | 移除 Lyra 优化或迁移 | 中 | 否 |
| `core/ai/prompts/integrated_prompt_generator.py:257` | 内部 | 判断 unified_prompt_manager 是否存在 | 删除判断逻辑 | 低 | 否 |
| `core/ai/prompts/integrated_prompt_generator.py:276` | 内部 | load_prompt 加载角色 | 使用主链路场景规则 | 中 | 否 |
| `core/ai/prompts/capability_integrated_prompt_generator.py:36` | 内部 | 作为参数传入 | 移除参数 | 低 | 否 |
| `core/ai/prompts/capability_integrated_prompt_generator.py:147` | 内部 | Lyra optimize_prompt | 移除 Lyra 优化或迁移 | 中 | 否 |
| `core/ai/prompts/unified_prompt_manager_production.py:17` | 内部 | 继承 UnifiedPromptManager | 冻结，不新增调用 | - | - |
| `core/ai/prompts/unified_prompt_manager_extended.py:17` | 内部 | 继承 UnifiedPromptManager | 冻结，不新增调用 | - | - |

**结论**: `unified_prompt_manager` 被 2 个核心业务控制器（xiaonuo_enhanced_controller、unified_llm_manager）直接依赖，**是 Phase 2 的主要阻塞点**。建议：
1. 内部调用（integrated_prompt_generator、capability_integrated_prompt_generator）在 deprecated 标记后冻结，不主动迁移
2. 核心业务控制器的依赖需在 W5-W6 专门处理，评估是否可用主链路 `generate_prompt()` 替代

---

## 3. integrated_prompt_generator

| 调用方 | 行号 | 用途 | 迁移目标 | 工作量 | 阻塞 Phase 2 |
|---|---|---|---|---|---|
| `core/ai/prompts/capability_integrated_prompt_generator.py:15` | 内部 | 继承 IntegratedPromptGenerator | 冻结 | - | - |
| `core/ai/prompts/unified_prompt_manager_production.py:16` | 内部 | 实例化 IntegratedPromptGenerator | 冻结 | - | - |
| `core/ai/prompts/unified_prompt_manager_extended.py:16` | 内部 | 实例化 IntegratedPromptGenerator | 冻结 | - | - |
| `scripts/system/verify_dynamic_prompt_system.py:63` | 脚本 | 导入测试 | 更新为导入主链路 | 低 | 否 |
| `core/prompts/capability_integrated_prompt_generator.py:19` | 内部 | 继承（core/prompts 复制） | 冻结 | - | - |
| `core/prompts/unified_prompt_manager_production.py:28` | 内部 | 实例化（core/prompts 复制） | 冻结 | - | - |
| `core/prompts/unified_prompt_manager_extended.py:24` | 内部 | 实例化（core/prompts 复制） | 冻结 | - | - |

**结论**: `integrated_prompt_generator` 主要被 deprecated 模块内部调用，外部只有 `verify_dynamic_prompt_system.py` 脚本。更新脚本后即可标记废弃。

---

## 4. capability_integrated_prompt_generator

| 调用方 | 行号 | 用途 | 迁移目标 | 工作量 | 阻塞 Phase 2 |
|---|---|---|---|---|---|
| `scripts/system/verify_dynamic_prompt_system.py:66` | 脚本 | 导入测试 | 更新为导入主链路 | 低 | 否 |

**结论**: 仅被验证脚本导入，更新脚本后即可标记废弃。

---

## 5. unified_prompt_manager_extended / unified_prompt_manager_production

**结论**: 这两个模块没有外部调用方（除 deprecated 模块内部互相调用），标记 deprecated 后冻结即可。

---

## 迁移优先级

```
P0 (阻塞 Phase 2 完成):
  ├── core/xiaonuo_enhanced_controller.py 的 prompt_manager 依赖
  └── core/llm/unified_llm_manager.py 的 prompt_manager 依赖

P1 (应在 Phase 2 完成):
  ├── integrated_prompt_generator 内部 async 错配修复
  ├── capability_integrated_prompt_generator 内部 async 错配修复
  └── scripts/system/verify_dynamic_prompt_system.py 更新

P2 (可在 Phase 3 并行处理):
  ├── progressive_loader 完全移除
  └── __init__.py 导出列表清理
```
