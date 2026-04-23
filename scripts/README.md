# Athena平台工具集

> **整理日期**: 2026-04-22
> **整理版本**: v2.0
> **状态**: ✅ 已整理完成

---

## 📊 整理统计

| 项目 | 整理前 | 整理后 | 改善 |
|-----|--------|--------|------|
| 根目录Python文件 | 60个 | 0个 | ✅ 100% |
| 重复工具 | ~25个 | 0个 | ✅ 100% |
| 目录分类 | 3个 | 18个 | ✅ 500% |

---

## 🗂️ 目录结构

```
tools/
├── patent/              # 专利相关工具 ⭐
│   ├── importer/       # 专利档案导入
│   ├── downloader/     # 专利下载
│   ├── analyzer/       # 专利分析
│   ├── database/       # 专利数据库
│   └── payment/        # 专利费用管理
├── customer/           # 客户管理工具
├── database/           # 数据库检查工具
├── agent/              # Agent开发工具
├── system/             # 系统工具
│   ├── cleanup/        # 清理工具
│   └── optimization/   # 优化工具
├── analysis/           # 分析工具
├── utils/              # 通用工具
├── cli/                # CLI工具
├── advanced/           # 高级工具
├── automation/         # 自动化脚本
├── deployment/         # 部署工具
├── download/           # 下载工具
├── mcp/                # MCP服务器管理
├── monitoring/         # 监控工具
├── optimization/       # 性能优化
├── patent-guideline-system/  # 专利审查指南GraphRAG
├── search/             # 搜索工具
└── README.md           # 本文档
```

---

## 🚀 快速导航

### 专利工具 (patent/)

#### 导入工具 (patent/importer/)
- `patent_archive_importer.py` - 专利档案导入器（v3，Ollama）
- `patent_archive_multimodal_importer.py` - 多模态专利导入器

#### 下载工具 (patent/downloader/)
- `google_patents_downloader.py` - Google Patents下载器
- `arxiv_downloader.py` - arXiv论文下载器
- `uspto_drip_irrigation_search.py` - USPTO滴灌搜索

#### 分析工具 (patent/analyzer/)
- `patent_ai_analyzer.py` - AI专利分析器
- `patent_ai_simple.py` - 简化版AI分析器
- `patent_3d_search_enhanced.py` - 增强版3D搜索
- `patent_3d_search_analyzer.py` - 3D搜索分析器
- `patent_claim_tools.py` - 权利要求工具
- `patent_pgsql_searcher.py` - PostgreSQL专利搜索
- `patent_excel_parser.py` - Excel解析器
- `patent_statistics.py` - 专利统计

#### 数据库工具 (patent/database/)
- `patent_db_import.py` - 专利数据库导入
- `restructure_patent_db.py` - 专利数据库重构
- `patent_archive_updater.py` - 专利档案更新

#### 费用管理 (patent/payment/)
- `patent_fee_association_manager.py` - 费用关联管理器
- `patent_fee_ocr_processor.py` - 费用OCR处理
- `patent_payment_final.py` - 最终费用处理
- `patent_payment_updater.py` - 费用更新器
- `update_patents_from_fees.py` - 从费用更新专利
- `associate_payment_images.py` - 关联支付图片
- `process_payment_with_voucher.py` - 凭证支付处理
- `fee_payment_importer.py` - 费用支付导入
- `fix_payment_table.py` - 修复支付表

---

### 客户工具 (customer/)

- `extract_all_customers.py` - 提取所有客户信息
- `organize_customer_files.py` - 整理客户文件
- `extract_contract_info.py` - 提取合同信息
- `parse_contract.py` - 解析合同

---

### 数据库工具 (database/)

- `check_data_integrity.py` - 检查数据完整性
- `check_database_structure.py` - 检查数据库结构
- `check_patent_numbers.py` - 检查专利号
- `diagnose_patent_numbers.py` - 诊断专利号问题

---

### Agent工具 (agent/)

- `agent_certifier.py` - Agent认证工具
- `create_agent.py` - 创建Agent
- `deep_technical_analysis_tools.py` - 深度技术分析
- `prompt_optimizer.py` - 提示词优化器

---

### 系统工具 (system/)

#### 清理工具 (system/cleanup/)
- `platform_cleanup.py` - 平台清理

#### 优化工具 (system/optimization/)
- `unify_numpy_stack.py` - 统一NumPy堆栈

---

### 分析工具 (analysis/)

- `analyze_dependencies.py` - 分析依赖关系
- `analyze_m4_usage.py` - 分析M4使用情况
- `analyze_tools_categories.py` - 分析工具分类

---

### 通用工具 (utils/)

- `file_type_detector.py` - 文件类型检测器
- `fix_syntax_errors.py` - 修复语法错误
- `organize_work_folder.py` - 整理工作文件夹

---

## 📋 已删除的重复工具

### 专利导入工具（已删除）
- ❌ `patent_archive_ollama_importer.py` - MLX版本（过时）
- ❌ `patent_archive_ollama_importer_v2.py` - MLX版本（过时）

### 客户工具（已删除）
- ❌ `export_customers_simple.py` - 重复
- ❌ `get_real_customers.py` - 重复
- ❌ `check_current_customers.py` - 重复
- ❌ `query_customer_sun_junxia.py` - 个人化工具
- ❌ `query_customer_wang_yurong.py` - 个人化工具

### NumPy工具（已删除）
- ❌ `fix_numpy_compatibility.py` - 重复
- ❌ `manage_numpy_versions.py` - 重复

### 清理工具（已删除）
- ❌ `project_cleaner.py` - 重复
- ❌ `quick_cleanup_scan.py` - 重复

### 其他（已删除）
- ❌ `patent_downloader.py` - 与google_patents_downloader重复
- ❌ `simple_fee_importer.py` - 与fee_payment_importer重复
- ❌ `test_ollama_response.py` - 测试文件
- ❌ `test_patent_format.py` - 测试文件

---

## 🔧 使用指南

### 专利档案导入

```bash
# 使用Ollama导入专利档案
python tools/patent/importer/patent_archive_importer.py

# 使用多模态导入
python tools/patent/importer/patent_archive_multimodal_importer.py
```

### 专利下载

```bash
# 从Google Patents下载
python tools/patent/downloader/google_patents_downloader.py

# 从arXiv下载论文
python tools/patent/downloader/arxiv_downloader.py
```

### 费用管理

```bash
# OCR处理费用
python tools/patent/payment/patent_fee_ocr_processor.py

# 关联费用
python tools/patent/payment/patent_fee_association_manager.py
```

### 数据库检查

```bash
# 检查数据完整性
python tools/database/check_data_integrity.py

# 检查数据库结构
python tools/database/check_database_structure.py
```

---

## 📝 维护规范

### 新增工具

1. **按功能分类** - 将工具放入合适的子目录
2. **命名规范** - 使用描述性名称，添加功能前缀
3. **文档说明** - 为工具添加docstring和使用说明
4. **避免重复** - 检查是否已有类似功能

### 工具命名规范

```
[功能前缀]_[具体功能]_[后缀].py

示例:
- patent_archive_importer.py
- google_patents_downloader.py
- check_data_integrity.py
```

### 定期清理

- 每季度检查一次重复工具
- 删除过时和不再使用的工具
- 更新README文档

---

## 🔄 更新历史

### v2.0 (2026-04-22)
- ✅ 根目录Python文件：60个 → 0个
- ✅ 删除重复工具：~25个
- ✅ 新增分类目录：15个
- ✅ 创建索引文档

### v1.0 (初始版本)
- 根目录包含60个Python文件
- 无分类结构
- 大量重复功能

---

## 📞 反馈与建议

如发现工具问题或有改进建议，请联系：
- **维护者**: 徐健 (xujian519@gmail.com)
- **项目**: Athena工作平台

---

**最后更新**: 2026-04-22
**整理状态**: ✅ 完成
