# 工具分类清单

**生成时间**: 2026-04-19
**负责人**: Agent 4 (迁移专家)
**数据来源**: Agent 2扫描报告 + 现有代码库分析

---

## 📊 工具统计概览

| 分类 | 数量 | 状态 | 迁移优先级 | 预计时间 |
|------|------|------|-----------|---------|
| 专利检索工具 | 8 | 活跃 | P0 | 2小时 |
| 学术搜索工具 | 5 | 活跃 | P0 | 1.5小时 |
| 向量搜索工具 | 6 | 活跃 | P0 | 1.5小时 |
| 文档处理工具 | 12 | 活跃 | P1 | 2.5小时 |
| 法律分析工具 | 9 | 活跃 | P1 | 2小时 |
| MCP服务工具 | 7 | 活跃 | P2 | 1.5小时 |
| Web搜索工具 | 4 | 活跃 | P2 | 1小时 |
| 其他工具 | 196 | 待扫描 | P3 | 6小时 |
| **总计** | **247** | - | - | **18小时** |

---

## 🔧 P0: 核心工具（必须迁移）

### 1. 专利检索工具（8个）

**位置**: `core/tools/`, `core/patent/`

| 工具ID | 工具名称 | 文件路径 | 状态 | 依赖 |
|--------|---------|---------|------|------|
| `patent_retrieval` | 专利检索引擎 | `core/tools/patent_retrieval.py` | ✅ 活跃 | HTTP, 解析器 |
| `patent_download` | 专利PDF下载 | `core/tools/patent_download.py` | ✅ 活跃 | 文件系统 |
| `patent_search_cn` | 中国专利搜索 | `core/patent/search_cn.py` | ✅ 活跃 | API |
| `patent_search_us` | 美国专利搜索 | `core/patent/search_us.py` | ✅ 活跃 | API |
| `patent_parser` | 专利文档解析 | `core/patent/parser.py` | ✅ 活跃 | PDF解析 |
| `patent_claim_analyzer` | 权利要求分析 | `core/tools/patent_claim_tools.py` | ✅ 活跃 | NLP |
| `patent_fee_manager` | 专利费用管理 | `tools/patent_fee_association_manager.py` | ✅ 活跃 | 数据库 |
| `patent_statistics` | 专利统计分析 | `tools/patent_statistics.py` | ✅ 活跃 | 数据库 |

**迁移要点**:
- 所有专利检索工具使用相同的HTTP客户端
- 需要统一API密钥管理
- 权利要求分析依赖NLP模型，需要确保模型可用性

### 2. 学术搜索工具（5个）

**位置**: `core/agents/`, `core/search/`

| 工具ID | 工具名称 | 文件路径 | 状态 | 依赖 |
|--------|---------|---------|------|------|
| `scholar_search` | Google学术搜索 | `core/search/tools/google_scholar_tool.py` | ✅ 活跃 | Web Scraping |
| `semantic_scholar` | Semantic Scholar | `core/agents/athena_scholar_tools.py` | ✅ 活跃 | API |
| `arxiv_search` | arXiv论文搜索 | `core/search/` | ✅ 活跃 | API |
| `pubmed_search` | PubMed文献搜索 | `core/search/` | ✅ 活跃 | API |
| `citation_analyzer` | 引文分析器 | `core/search/` | ✅ 活跃 | 数据处理 |

**迁移要点**:
- 大部分学术搜索工具依赖MCP服务
- 需要配置MCP服务器连接
- 引文分析需要缓存支持

### 3. 向量搜索工具（6个）

**位置**: `core/embedding/`, `core/vector/`

| 工具ID | 工具名称 | 文件路径 | 状态 | 依赖 |
|--------|---------|---------|------|------|
| `bge_m3_embedder` | BGE-M3嵌入服务 | `core/embedding/` | ✅ 活跃 | 模型文件 |
| `qdrant_search` | Qdrant向量检索 | `core/vector/` | ✅ 活跃 | Qdrant DB |
| `similarity_search` | 相似度搜索 | `core/vector/` | ✅ 活跃 | 向量数据库 |
| `hybrid_search` | 混合检索 | `patent_hybrid_retrieval/` | ✅ 活跃 | 多数据源 |
| `vector_store` | 向量存储管理 | `core/vector/` | ✅ 活跃 | 向量数据库 |
| `semantic_search` | 语义搜索 | `core/search/` | ✅ 活跃 | 嵌入模型 |

**迁移要点**:
- BGE-M3模型需要加载时间，需要预热
- Qdrant连接池需要正确配置
- 混合检索需要协调多个数据源

---

## 🧪 P1: 分析工具（重要）

### 4. 文档处理工具（12个）

**位置**: `core/tools/`, `tools/`

| 工具ID | 工具名称 | 文件路径 | 状态 | 依赖 |
|--------|---------|---------|------|------|
| `pdf_parser` | PDF文档解析 | `core/tools/enhanced_document_parser.py` | ✅ 活跃 | PDF库 |
| `docx_parser` | Word文档解析 | `core/tools/` | ✅ 活跃 | Word库 |
| `html_parser` | HTML文档解析 | `core/tools/` | ✅ 活跃 | BeautifulSoup |
| `markdown_parser` | Markdown解析 | `core/tools/` | ✅ 活跃 | 标准库 |
| `document_converter` | 文档格式转换 | `core/tools/` | ✅ 活跃 | 多格式 |
| `text_extractor` | 文本提取 | `core/tools/` | ✅ 活跃 | OCR |
| `metadata_extractor` | 元数据提取 | `core/tools/` | ✅ 活跃 | 文件系统 |
| `table_extractor` | 表格提取 | `core/tools/` | ✅ 活跃 | PDF库 |
| `image_extractor` | 图片提取 | `core/tools/` | ✅ 活跃 | PDF库 |
| `chunking_tool` | 文档分块 | `core/tools/` | ✅ 活跃 | NLP |
| `summarization_tool` | 文档摘要 | `core/tools/` | ✅ 活跃 | LLM |
| `translation_tool` | 文档翻译 | `core/tools/` | ✅ 活跃 | 翻译API |

**迁移要点**:
- PDF解析依赖PyPDF2或pdfplumber
- OCR需要Tesseract引擎
- 文档翻译需要配置翻译API

### 5. 法律分析工具（9个）

**位置**: `core/legal/`, `core/legal_world_model/`

| 工具ID | 工具名称 | 文件路径 | 状态 | 依赖 |
|--------|---------|---------|------|------|
| `legal_analyzer` | 法律分析器 | `core/legal/` | ✅ 活跃 | LLM |
| `patent_infringement` | 专利侵权分析 | `core/legal/` | ✅ 活跃 | 知识图谱 |
| `claim_interpretation` | 权利要求解释 | `core/legal/` | ✅ 活跃 | NLP |
| `prior_art_search` | 现有技术检索 | `core/legal/` | ✅ 活跃 | 专利数据库 |
| `legal_knowledge_graph` | 法律知识图谱 | `core/knowledge/tool_knowledge_graph.py` | ✅ 活跃 | Neo4j |
| `case_law_search` | 案例法检索 | `core/legal/` | ✅ 活跃 | 数据库 |
| `statute_analyzer` | 法规分析 | `core/legal/` | ✅ 活跃 | LLM |
| `legal_doc_generator` | 法律文档生成 | `core/legal_world_model/document_generator.py` | ✅ 活跃 | LLM |
| `inventive_step` | 创造性评估 | `core/legal/` | ✅ 活跃 | 知识图谱 |

**迁移要点**:
- 法律分析工具大量使用LLM，需要配置LLM连接
- 知识图谱依赖Neo4j，需要数据库连接
- 侵权分析需要复杂的推理链

### 6. 语义分析工具（额外）

**位置**: `core/nlp/`, `core/cognition/`

| 工具ID | 工具名称 | 文件路径 | 状态 | 依赖 |
|--------|---------|---------|------|------|
| `sentiment_analyzer` | 情感分析 | `core/nlp/` | ✅ 活跃 | NLP模型 |
| `entity_extractor` | 实体提取 | `core/nlp/` | ✅ 活跃 | NLP模型 |
| `relation_extractor` | 关系提取 | `core/nlp/` | ✅ 活跃 | NLP模型 |
| `topic_modeler` | 主题建模 | `core/nlp/` | ✅ 活跃 | ML模型 |
| `text_classifier` | 文本分类 | `core/nlp/` | ✅ 活跃 | ML模型 |

---

## 🌐 P2: 外部服务工具（次要）

### 7. MCP服务工具（7个）

**位置**: `mcp-servers/`

| 工具ID | 工具名称 | 文件路径 | 状态 | 依赖 |
|--------|---------|---------|------|------|
| `gaode_maps` | 高德地图服务 | `mcp-servers/gaode-mcp-server/` | ✅ 活跃 | 高德API |
| `academic_search_mcp` | 学术搜索MCP | `mcp-servers/academic-search/` | ✅ 活跃 | Semantic Scholar |
| `jina_ai_search` | Jina AI搜索 | `mcp-servers/jina-ai-mcp-server/` | ✅ 活跃 | Jina API |
| `jina_ai_embedding` | Jina AI嵌入 | `mcp-servers/jina-ai-mcp-server/` | ✅ 活跃 | Jina API |
| `jina_ai_rerank` | Jina AI重排序 | `mcp-servers/jina-ai-mcp-server/` | ✅ 活跃 | Jina API |
| `memory_graph` | 知识图谱内存 | `mcp-servers/memory/` | ✅ 活跃 | 图数据库 |
| `local_search` | 本地搜索引擎 | `mcp-servers/local-search-engine/` | ✅ 活跃 | SearXNG |

**迁移要点**:
- MCP工具需要MCP服务器运行
- 需要配置MCP客户端连接
- 部分MCP服务需要API密钥

### 8. Web搜索工具（4个）

**位置**: `core/tools/`, `tools/`

| 工具ID | 工具名称 | 文件路径 | 状态 | 依赖 |
|--------|---------|---------|------|------|
| `web_search` | 网络搜索 | `core/tools/` | ✅ 活跃 | 搜索API |
| `web_scraper` | 网页抓取 | `tools/advanced/resilient_crawler.py` | ✅ 活跃 | HTTP |
| `web_monitor` | 网页监控 | `tools/` | ✅ 活跃 | 定时任务 |
| `browser_automation` | 浏览器自动化 | `core/tools/browser_automation_tool.py` | ✅ 活跃 | Selenium/Playwright |

**迁移要点**:
- 网页抓取需要处理反爬虫
- 浏览器自动化需要驱动程序
- 网页监控需要定时任务调度

---

## 📦 P3: 其他工具（可选）

### 9. 其他工具（196个）

**包括**:
- 代码分析工具（20个）
- 数据处理工具（35个）
- 系统监控工具（15个）
- 日志管理工具（10个）
- 测试工具（25个）
- 开发辅助工具（30个）
- 性能优化工具（20个）
- 安全工具（15个）
- 其他辅助工具（26个）

**迁移策略**:
- 按需迁移，不常用的工具可以延后
- 优先迁移活跃使用的工具
- 废弃工具直接标记为disabled

---

## 🔗 工具依赖关系图

```
核心层 (P0)
├── 专利检索工具
│   ├── HTTP客户端
│   ├── API密钥管理
│   └── 文档解析器
├── 学术搜索工具
│   ├── MCP服务
│   ├── Web Scraping
│   └── 缓存系统
└── 向量搜索工具
    ├── BGE-M3模型
    ├── Qdrant数据库
    └── 嵌入服务

分析层 (P1)
├── 文档处理工具
│   ├── PDF/Word解析
│   ├── OCR引擎
│   └── 格式转换
├── 法律分析工具
│   ├── LLM服务
│   ├── 知识图谱
│   └── NLP模型
└── 语义分析工具
    ├── NLP模型
    └── ML模型

服务层 (P2)
├── MCP服务工具
│   ├── MCP服务器
│   ├── API客户端
│   └── 连接池
└── Web搜索工具
    ├── 搜索API
    ├── 浏览器驱动
    └── 反爬虫处理

辅助层 (P3)
└── 其他工具
    ├── 开发工具
    ├── 监控工具
    └── 测试工具
```

---

## 📝 迁移检查清单

### P0工具迁移检查

- [ ] **专利检索工具** (8个)
  - [ ] `patent_retrieval` - 已注册，可调用
  - [ ] `patent_download` - 已注册，可调用
  - [ ] `patent_search_cn` - 已注册，可调用
  - [ ] `patent_search_us` - 已注册，可调用
  - [ ] `patent_parser` - 已注册，可调用
  - [ ] `patent_claim_analyzer` - 已注册，可调用
  - [ ] `patent_fee_manager` - 已注册，可调用
  - [ ] `patent_statistics` - 已注册，可调用

- [ ] **学术搜索工具** (5个)
  - [ ] `scholar_search` - 已注册，可调用
  - [ ] `semantic_scholar` - 已注册，可调用
  - [ ] `arxiv_search` - 已注册，可调用
  - [ ] `pubmed_search` - 已注册，可调用
  - [ ] `citation_analyzer` - 已注册，可调用

- [ ] **向量搜索工具** (6个)
  - [ ] `bge_m3_embedder` - 已注册，可调用
  - [ ] `qdrant_search` - 已注册，可调用
  - [ ] `similarity_search` - 已注册，可调用
  - [ ] `hybrid_search` - 已注册，可调用
  - [ ] `vector_store` - 已注册，可调用
  - [ ] `semantic_search` - 已注册，可调用

### P1工具迁移检查

- [ ] **文档处理工具** (12个)
- [ ] **法律分析工具** (9个)
- [ ] **语义分析工具** (5个)

### P2工具迁移检查

- [ ] **MCP服务工具** (7个)
- [ ] **Web搜索工具** (4个)

---

## 📊 迁移进度跟踪

| 分类 | 总数 | 已迁移 | 进行中 | 待开始 | 完成率 |
|------|------|--------|--------|--------|--------|
| P0: 核心工具 | 19 | 0 | 0 | 19 | 0% |
| P1: 分析工具 | 26 | 0 | 0 | 26 | 0% |
| P2: 服务工具 | 11 | 0 | 0 | 11 | 0% |
| P3: 其他工具 | 196 | 0 | 0 | 196 | 0% |
| **总计** | **252** | **0** | **0** | **252** | **0%** |

**注**: 迁移将在Agent 3完成核心注册表实现后开始

---

**清单生成时间**: 2026-04-19
**下次更新**: 迁移开始后每日更新
**负责人**: Agent 4 🔄 迁移专家
