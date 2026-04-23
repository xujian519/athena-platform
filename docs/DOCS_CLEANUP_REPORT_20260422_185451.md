# Docs目录整理报告

> **生成时间**: 2026-04-22 18:54:51
> **执行脚本**: scripts/docs_cleanup.sh

---

## 📊 整理统计

| 项目 | 数量 |
|-----|------|
| 已移动文件 | 68 |
| 跳过文件 | 0 |
| 错误文件 | 0 |
| 总计处理 | 68 |

---

## 🗂️ 整理详情

### 1. 临时报告归档
- `*_report_202601*.md` → `archive/temp-reports/2026-01/`
- `*_report_202602*.md` → `archive/temp-reports/2026-02/`
- `*_report_202603*.md` → `archive/temp-reports/2026-03/`
- `*_report_202604*.md` → `archive/temp-reports/2026-04/`

### 2. 过时文档归档
- 2025年优化文档 → `archive/legacy-2025/`
- Istio相关文档 → `archive/legacy-istio/`

### 3. API文档
- API相关文档 → `api/`

### 4. 架构文档
- 系统架构 → `architecture/`
- 企业级架构 → `architecture/enterprise/`
- 网关架构 → `architecture/gateway/`
- 数据库架构 → `architecture/database/`

### 5. 智能体文档
- 小娜相关 → `agents/xiaona/`
- 小诺相关 → `agents/xiaonuo/`
- 多智能体架构 → `architecture/agents/`

### 6. 专利文档
- 中文专利文档 → `projects/patents/`
- 专利检索报告 → `projects/patents/`

### 7. 指南文档
- 快速开始 → `guides/quick-start/`
- 用户指南 → `guides/`
- 操作手册 → `guides/manuals/`

### 8. 部署文档
- 部署相关 → `deployment/`
- 迁移相关 → `deployment/migration/`
- Docker相关 → `deployment/docker/`

### 9. 配置文档
- 配置相关 → `reference/configuration/`

### 10. 安全文档
- 安全相关 → `security/`

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
   - 保持根目录整洁

---

**脚本版本**: 1.0.0
**执行者**: xujian
**主机**: m4pro.local
