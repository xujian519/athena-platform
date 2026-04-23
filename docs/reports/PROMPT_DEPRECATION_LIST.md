# Prompt 模块废弃清单

> 生成时间: 2026-04-23
> 废弃策略: 标记 deprecated → 冻结新功能 → 迁移调用方 → 移除

---

## 废弃模块清单

| 模块路径 | 废弃时间 | 预计移除版本 | 替代方案 | 状态 |
|---|---|---|---|---|
| `core/ai/prompts/progressive_loader.py` | 2026-04-23 | v3.0 | `core.api.prompt_system_routes.generate_prompt()` | 已标记 |
| `core/ai/prompts/unified_prompt_manager.py` | 2026-04-23 | v3.0 | `core.api.prompt_system_routes.generate_prompt()` | 已标记 |
| `core/ai/prompts/unified_prompt_manager_extended.py` | 2026-04-23 | v3.0 | `core.api.prompt_system_routes.generate_prompt()` | 已标记 |
| `core/ai/prompts/unified_prompt_manager_production.py` | 2026-04-23 | v3.0 | `core.api.prompt_system_routes.generate_prompt()` | 已标记 |
| `core/ai/prompts/integrated_prompt_generator.py` | 2026-04-23 | v3.0 | `core.api.prompt_system_routes.generate_prompt()` | 已标记 |
| `core/ai/prompts/capability_integrated_prompt_generator.py` | 2026-04-23 | v3.0 | `core.api.prompt_system_routes.generate_prompt()` | 已标记 |
| `core/prompts/` 目录（复制） | 2026-04-23 | v3.0 | `core.ai.prompts/` | 已标记 |

---

## 关键调用方迁移进度

| 调用方 | 依赖模块 | 迁移目标 | 工作量 | 计划完成 |
|---|---|---|---|---|
| `core/xiaonuo_enhanced_controller.py` | `unified_prompt_manager` | 主链路 API | 高 | W5-W6 |
| `core/llm/unified_llm_manager.py` | `unified_prompt_manager` | 主链路 API | 高 | W5-W6 |
| `scripts/system/verify_dynamic_prompt_system.py` | `integrated_prompt_generator` 等 | 更新为验证主链路 | 低 | W4 |

---

## 废弃后行为

1. **导入时**: 产生 `DeprecationWarning`，不阻断执行
2. **运行时**: 功能仍可用（含 async/sync 错配修复）
3. **日志**: 每次导入记录 warning，便于追踪剩余调用方
4. **CI**: 允许 deprecation warning，不阻断构建

---

## 移除条件

以下全部达成后，方可移除废弃模块：
- [ ] 核心业务控制器（xiaonuo_enhanced_controller、unified_llm_manager）不再依赖
- [ ] 全量测试通过且无 deprecated 模块导入
- [ ] 主链路已承载 100% 生产流量 ≥ 2 周
- [ ] 回滚方案就绪（万一移除后发现问题可快速恢复）
