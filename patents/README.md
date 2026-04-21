# 专利处理统一模块

> **整合时间**: 2026-04-21
> **状态**: 迁移中

---

## 📋 目录结构

- `core/`: 核心专利处理功能
- `retrieval/`: 专利检索引擎
- `platform/`: 平台应用
- `webui/`: Web界面
- `workflows/`: 工作流
- `integrations/`: 第三方集成
- `services/`: 服务层
- `tools/`: 工具集
- `tests/`: 测试
- `docs/`: 文档

---

## 🚧 迁移状态

### 总体进度: 30% (1/3批次完成)

**已完成**: Batch 1 - 核心模块 (53,617行)
**进行中**: Batch 2 - 检索引擎和平台应用 (~87,731行)
**待开始**: Batch 3 - 剩余模块

### ✅ Batch 1 - 核心模块 (已完成 2026-04-21)

- [x] core/patent/ → patents/core/ (53,617行)
- [x] 创建子模块__init__.py (7个)
- [x] 批量更新导入路径 (110文件, 286处)
- [x] 创建符号链接向后兼容
- [x] 运行测试验证 (37 passed)
- [x] Git提交 (204文件)

**执行时间**: 9分钟 (原计划75分钟, 效率提升88%)

### 检索引擎
- [ ] patent_hybrid_retrieval/ → patents/retrieval/ (7,715行)

### 平台应用
- [ ] patent-platform/ → patents/platform/ (79,061行)
- [ ] apps/patent-platform/ → patents/platform/ (955行)

### Web界面
- [ ] patent-retrieval-webui/ → patents/webui/

### 工作流
- [ ] openspec-oa-workflow/ → patents/workflows/

### 集成
- [ ] services/pqai-integration/ → patents/integrations/pqai/
- [ ] mcp-servers/patent_* → patents/services/

---

## 📝 迁移原则

1. **保持功能不变**: 代码功能完全保持
2. **更新导入路径**: 所有导入路径更新为新路径
3. **测试验证**: 每步迁移后都要测试
4. **符号链接**: 迁移期间使用符号链接保持向后兼容
5. **分步提交**: 每个模块迁移完成后独立提交

---

## 🔄 回滚计划

如果迁移出现问题：
1. 删除符号链接
2. 恢复旧目录
3. 回滚导入路径更新
4. 验证系统恢复正常

---

## 📊 迁移统计

| 模块 | 原路径 | 新路径 | 代码行数 | 状态 |
|------|--------|--------|---------|------|
| 核心模块 | core/patent/ | patents/core/ | 53,617 | ✅ 完成 (Batch 1) |
| 检索引擎 | patent_hybrid_retrieval/ | patents/retrieval/ | 7,715 | ⏳ 待开始 |
| 平台应用 | patent-platform/ | patents/platform/ | 79,061 | ⏳ 待开始 |
| Web界面 | patent-retrieval-webui/ | patents/webui/ | - | ⏳ 待开始 |

---

**创建时间**: 2026-04-21
**迁移负责人**: Claude Code (OMC模式)
**预计完成时间**: 2026-04-24
