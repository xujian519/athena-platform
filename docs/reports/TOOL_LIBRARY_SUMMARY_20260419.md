# Athena工具库清单 - 快速参考

> **更新日期**: 2026-04-19
> **总计**: 47个工具（22个已实现，25个待实现）

---

## ✅ 已实现工具（22个）

### 核心工具（12个）

| 工具ID | 名称 | 分类 | 状态 | 优先级 | 说明 |
|--------|------|------|------|--------|------|
| `code_analyzer` | 代码分析器 | CODE_ANALYSIS | ✅ 可用 | HIGH | AST静态分析，复杂度检测 |
| `system_monitor` | 系统监控 | MONITORING | ✅ 可用 | CRITICAL | CPU/内存/磁盘/网络监控 |
| `web_search` | 网络搜索 | WEB_SEARCH | ⚠️ 基础 | MEDIUM | DuckDuckGo搜索 |
| `knowledge_graph` | 知识图谱 | KNOWLEDGE_GRAPH | ⚠️ 演示 | MEDIUM | 本地微型知识库 |
| `chat_companion` | 聊天伴侣 | CHAT_COMPLETION | ⚠️ 演示 | LOW | 规则对话系统 |
| `text_embedding` | 文本向量化 | VECTOR_SEARCH | ✅ 可用 | HIGH | BGE-M3嵌入 |
| `api_tester` | API测试器 | API_INTEGRATION | ✅ 可用 | MEDIUM | HTTP请求测试 |
| `document_parser` | 文档解析器 | DATA_EXTRACTION | ✅ 可用 | HIGH | PDF/DOCX/TXT解析 |
| `emotional_support` | 情感支持 | CHAT_COMPLETION | ⚠️ 演示 | LOW | 情感分析 |
| `decision_engine` | 决策引擎 | MONITORING | ⚠️ 基础 | MEDIUM | MCDA决策 |
| `risk_analyzer` | 风险分析器 | MONITORING | ⚠️ 基础 | HIGH | 风险评估 |

### MCP工具（8个）

| 工具ID | 功能 | 状态 |
|--------|------|------|
| `gaode-mcp-server` | 高德地图（地理编码、路径规划） | ✅ 可用 |
| `academic-search` | 学术搜索（Semantic Scholar） | ✅ 可用 |
| `jina-ai-read-web` | 网页抓取（Jina Reader） | ✅ 可用 |
| `jina-ai-vector-search` | 向量搜索（语义检索） | ✅ 可用 |
| `jina-ai-rerank` | 文档重排序 | ✅ 可用 |
| `jina-ai-web-search` | 网络搜索 | ✅ 可用 |
| `memory` | 知识图谱内存 | ✅ 可用 |
| `local-search-engine` | 本地搜索引擎（SearXNG） | ✅ 可用 |

### 工具基础设施（2个）

| 工具ID | 功能 | 状态 |
|--------|------|------|
| `permissions` | 工具权限控制 | ✅ 可用 |
| `hooks` | Hook生命周期 | ✅ 可用 |

---

## ❌ 待实现工具（25个）

### 🔴 高优先级（13个）

**专利检索工具集**:
- `enhanced_patent_search` - 增强专利检索
- `pdf_patent_parser` - PDF专利解析器
- `google_scholar_search` - Google学术搜索

**新颖性分析工具集**:
- `novelty_analyzer` - 新颖性分析器
- `claim_comparator` - 权利要求对比器
- `technical_feature_extractor` - 技术特征提取器
- `legal_reasoning_engine` - 法律推理引擎

**审查意见答复工具集**:
- `oa_analyzer` - 审查意见分析器
- `claim_amender` - 权利要求修改器
- `response_generator` - 答复生成器

**侵权分析工具集**:
- `infringement_analyzer` - 侵权分析器
- `claim_coverage_checker` - 权利要求覆盖检查器
- `equivalence_judge` - 等同判断器

### 🟡 中优先级（9个）

- `legal_case_search` - 法律案例检索
- `legal_template_manager` - 法律模板管理器
- `document_generator` - 文档生成器
- `template_manager` - 模板管理器
- `content_validator` - 内容验证器
- `paper_summarizer` - 论文摘要器
- `citation_analyzer` - 引用分析器

### 🟢 低优先级（3个）

- `legal_formatter` - 法律格式化器
- `citation_analyzer` - 引用分析器（重复）

---

## 🎯 工具甄别建议

### 立即保留（✅）
1. **代码分析器** - 成熟、实用
2. **系统监控** - 关键基础设施
3. **文本向量化** - 核心NLP能力
4. **API测试器** - 实用工具
5. **文档解析器** - 核心数据处理
6. **所有MCP工具** - 成熟外部服务

### 需要增强（⚠️）
1. **网络搜索** - 集成更多引擎
2. **知识图谱** - 接入真实KG
3. **风险分析器** - 建立知识库
4. **决策引擎** - 支持更多算法

### 应重构/替换（❌）
1. **聊天伴侣** - 替换为LLM
2. **情感支持** - 整合到聊天系统
3. **知识图谱** - 当前过于简单

---

## 📊 统计摘要

```
总工具数: 47
已实现:   22 (46.8%)
待实现:   25 (53.2%)

核心可用: 12/22 = 54.5%
演示级别: 6/22  = 27.3%
MCP工具:  8/22  = 36.4%

高优先级缺口: 13个工具
```

---

## 🚀 实施建议

### Phase 1（1-2周）
- ✅ 优化现有工具
- ✅ 替换简单工具
- ✅ 集成LLM

### Phase 2（3-4周）
- 🔴 实现专利检索工具集
- 🔴 实现新颖性分析工具集

### Phase 3（5-8周）
- 🔴 实现审查意见答复工具集
- 🔴 实现侵权分析工具集

---

**详细报告**: 参见 `TOOL_LIBRARY_AUDIT_REPORT_20260419.md`
