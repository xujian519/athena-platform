# Docs目录第二轮整理报告

> **生成时间**: 2026-04-22 18:57:10
> **执行脚本**: scripts/docs_cleanup_phase2.sh

---

## 📊 整理统计

| 项目 | 数量 |
|-----|------|
| 已移动文件 | 81 |
| 跳过文件 | 0 |
| 错误文件 | 0 |
| 总计处理 | 81 |

---

## 🗂️ 整理详情

### 1. 中文文档归档
- 多模态文档 → `projects/multimodal/`
- 技术图纸文档 → `projects/patents/zh-cn/`
- 小娜专利检索 → `projects/patents/zh-cn/`
- 星河系列设计 → `archive/design-legacy/`

### 2. 历史设计文档归档
- 系统设计文档 → `archive/design-2025/`
- 集成方案 → `archive/design-2025/`
- 自动演进相关 → `archive/design-2025/`
- 架构优化建议 → `archive/design-2025/`
- NLP相关 → `archive/nlp-legacy/`

### 3. 临时报告归档
- 系统验证报告 → `archive/temp-reports/2026-02/`
- 语法修复报告 → `archive/temp-reports/2026-02/`
- 项目清理报告 → `archive/temp-reports/`

### 4. 迁移文档整理
- Migration相关 → `deployment/migration/`
- Service Mesh相关 → `deployment/migration/`

### 5. 身份配置文档
- 身份相关 → `reference/identity/`
- 外部依赖 → `reference/dependencies/`

### 6. 性能文档
- 性能相关 → `reports/performance/`

### 7. 安全文档
- 安全相关 → `security/`
- TLS相关 → `security/`
- SPIFFE相关 → `security/`

### 8. 项目结构文档
- 项目结构相关 → `reference/project-structure/`

### 9. 计划和任务
- 计划文档 → `plans/`
- 任务跟踪 → `plans/`

### 10. 感知模块
- 感知模块相关 → `guides/perception/`

### 11. 知识图谱
- 知识图谱相关 → `architecture/knowledge-graph/`

### 12. 代理文档
- 代理相关 → `agents/`

### 13. 记忆系统
- 记忆系统相关 → `architecture/memory/`

### 14. 部署文档
- 部署相关 → `deployment/`

### 15. 模型和AI
- AI模型相关 → `guides/ai-models/`

### 16. 工具和服务
- 工具相关 → `guides/tools/`

---

## ✅ 下一步

1. **检查整理结果**
   ```bash
   ls -lh docs/
   ls -lh docs/archive/
   ```

2. **更新文档索引**
   - 更新 `docs/README.md`
   - 更新 `docs/INDEX.md`

3. **建立维护规范**
   - 新文档按分类存放
   - 定期归档临时报告
   - 保持根目录整洁（<30个文件）

---

**脚本版本**: 2.0.0
**执行者**: xujian
**主机**: m4pro.local
