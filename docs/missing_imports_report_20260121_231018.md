# 缺失导入修复报告

> 生成时间: 2026-01-21 23:10:18

---

## 🔧 修复统计

- 修复文件数: 10

## 📦 缺失依赖清单

| 模块 | 影响工具数 | 影响文件数 | 建议操作 |
|------|-----------|-----------|---------|
| app | 9 | 7 | 修复相对导入路径 |
| intelligent_caller | 7 | 1 | 安装或创建此模块 |
| langchain | 4 | 1 | pip install langchain (可选依赖) |
| proxy_manager | 4 | 1 | 修复相对导入路径 |
| athena_browser_glm | 3 | 2 | 安装或创建此模块 |
| neo4j | 2 | 1 | 项目已迁移到NebulaGraph，更新代码 |
| google_patents_retriever | 2 | 2 | 安装或创建此模块 |
| athena_playwright_agent | 1 | 1 | 安装或创建此模块 |
| athena_browser_agent | 1 | 1 | 安装或创建此模块 |
| models.baochen_models | 1 | 1 | 检查模块路径 |
| ai_integration | 1 | 1 | 检查模块是否存在于项目中 |
| apps.xiaonuo.xiaonuo_unified_g | 1 | 1 | 检查模块是否存在于项目中 |
| xiaonuo_client | 1 | 1 | 检查模块是否存在于项目中 |
| enhanced_patent_feature_extrac | 1 | 1 | 检查模块是否存在于项目中 |
| faiss | 1 | 1 | pip install faiss-cpu (可选依赖) |

## 📁 受影响的文件

### app

**建议操作**: 修复相对导入路径

**受影响文件**:
- `services/yunpat-agent/app/core/semantic_search.py`
- `services/yunpat-agent/app/services/postgresql_service.py`
- `services/yunpat-agent/app/agent/core.py`
- `services/yunpat-agent/app/services/file_service.py`
- `services/yunpat-agent/app/db/services.py`
- ... 还有 2 个文件

### intelligent_caller

**建议操作**: 安装或创建此模块

**受影响文件**:
- `services/visualization-tools/unified_visualization_module.py`

### langchain

**建议操作**: pip install langchain (可选依赖)

**受影响文件**:
- `services/visualization-tools/langchain_tools.py`

### proxy_manager

**建议操作**: 修复相对导入路径

**受影响文件**:
- `dev/tools/advanced/resilient_crawler.py`

### athena_browser_glm

**建议操作**: 安装或创建此模块

**受影响文件**:
- `services/browser-automation-service/browser_use_examples.py`
- `services/common-tools-service/browser_automation_tool.py`

### neo4j

**建议操作**: 项目已迁移到NebulaGraph，更新代码

**受影响文件**:
- `dev/tools/patent-guideline-system/src/models/graph_schema.py`

### google_patents_retriever

**建议操作**: 安装或创建此模块

**受影响文件**:
- `apps/patent-platform/core/api_services/patent_service_manager.py`
- `apps/patent-platform/core/api_services/patent_search_api.py`

### athena_playwright_agent

**建议操作**: 安装或创建此模块

**受影响文件**:
- `services/browser-automation-service/api_server_playwright.py`

### athena_browser_agent

**建议操作**: 安装或创建此模块

**受影响文件**:
- `services/browser-automation-service/api_server.py`

### models.baochen_models

**建议操作**: 检查模块路径

**受影响文件**:
- `services/yunpat-agent/ip_business/services/baochen_service.py`

## 💡 建议

1. **立即可修复** (相对导入问题)
   - 使用自动化脚本修复 `from app.` 导入
   - 修复 `proxy_manager` 等相对导入

2. **可选依赖** (可以添加try/except)
   - langchain: 可视化工具的可选依赖
   - faiss: 向量搜索的可选依赖
   - neo4j: 项目已迁移到NebulaGraph

3. **需要创建的模块**
   - athena_browser_glm: 浏览器自动化模块
   - athena_browser_agent: 浏览器代理模块
   - intelligent_caller: 智能调用器模块

---

**报告生成器**: 缺失导入修复脚本 v1.0.0