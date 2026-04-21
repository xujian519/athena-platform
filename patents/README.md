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

### 核心模块
- [ ] core/patent/ → patents/core/ (53,617行)

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
| 核心模块 | core/patent/ | patents/core/ | 53,617 | ⏳ 进行中 |
| 检索引擎 | patent_hybrid_retrieval/ | patents/retrieval/ | 7,715 | ⏳ 待开始 |
| 平台应用 | patent-platform/ | patents/platform/ | 79,061 | ⏳ 待开始 |
| Web界面 | patent-retrieval-webui/ | patents/webui/ | - | ⏳ 待开始 |

---

**创建时间**: 2026-04-21
**迁移负责人**: Claude Code (OMC模式)
**预计完成时间**: 2026-04-24
