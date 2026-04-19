# 专利全文处理系统 - 验证通过架构方案

**日期**: 2025-12-24
**版本**: v1.1 (简化版 - 去除Google搜索)

---

## 一、验证总结

### ✅ 已验证组件

| 组件 | 状态 | 验证结果 |
|------|------|----------|
| patent-search MCP | ✅ 通过 | 返回24个元数据字段，包含PostgreSQL ID |
| patent-downloader | ✅ 通过 | PDF下载功能正常，支持手动输入专利号 |
| 集成中间层 | ✅ 通过 | IntegratedPatentDownloader实现元数据关联 |

### ✅ 验证通过的集成流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        检索层（两种方式）                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐  ┌──────────────┐                                      │
│  │patent-search │  │  手动输入    │                                      │
│  │ MCP          │  │              │                                      │
│  │              │  │ 专利号/申请号│                                      │
│  │中国专利DB    │  │  列表        │                                      │
│  │2800万条      │  │              │                                      │
│  └──────┬───────┘  └──────┬───────┘                                      │
│         │                 │                                             │
│         │ 完整元数据       │ 专利号列表                                   │
│         │ (24字段)         │ (CN123456789A)                              │
│         │                 │                                             │
│         └─────────────────┴─────────────────┘                          │
│                                   │                                     │
│                                   ▼                                     │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │              IntegratedPatentDownloader (中间层)                 │  │
│  │                                                                   │  │
│  │  • 封装完整元数据的下载请求                                       │  │
│  │  • 维护下载→数据库映射关系                                         │  │
│  │  • 自动按CN/US/EP/WO分类                                           │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                   │                                     │
│                                   ▼                                     │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                    patent-downloader                              │  │
│  │                                                                   │  │
│  │   输入: patent_numbers[] → 下载PDF → 按国家分类存储               │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          存储与映射层                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │  文件系统    │  │  PostgreSQL  │  │  映射文件    │                  │
│  │              │  │              │  │              │                  │
│  │/Users/xujian/│  │  patent_db   │  │download_     │                  │
│  │apps/patents/PDF/  │  │  patents表   │  │mapping.json │                  │
│  │  CN/         │  │              │  │              │                  │
│  │  US/         │  │ + pdf_path   │  │ 请求→结果   │                  │
│  │  EP/         │  │ + pdf_source │  │ postgres_id │                  │
│  │  WO/         │  │ + vector_id  │  │              │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      后续处理管道（待实现）                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  PDF处理 → 文本提取 → 向量化(Qdrant) → 知识图谱(NebulaGraph)            │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 二、组件详情

### 1. patent-search MCP

**位置**: `mcp-servers/patent-search-mcp-server/`

**功能**: 搜索中国专利数据库 (PostgreSQL, 2800万+条记录)

**可用工具**:
- `search_cn_patents` - 搜索中国专利
- `get_cn_patent_by_id` - 根据申请号获取详情
- `analyze_cn_patent_landscape` - 专利布局分析

**返回元数据** (24字段):
```json
{
  "id": "UUID",                    // PostgreSQL记录ID
  "application_number": "申请号",
  "publication_number": "公开号",
  "patent_name": "专利名称",
  "patent_type": "发明/实用新型/外观设计",
  "applicant": "申请人",
  "inventor": "发明人",
  "ipc_main_class": "IPC主分类",
  "abstract": "摘要",
  "claims_content": "权利要求书",
  ...
}
```

### 2. 手动输入

**适用场景**:
- 复审/无效程序中的对比文件清单
- 已知专利号/申请号
- 其他来源的专利号列表

**输入方式**:
```python
# 方式1: Python列表
patent_numbers = [
    "CN112233445A",
    "US8460931B2",
    "WO2023123456A1"
]

# 方式2: 从文本文件读取
# patents.txt:
# CN112233445A
# US8460931B2
# WO2023123456A1

# 方式3: 从CSV文件读取
# patents.csv:
# patent_number
# CN112233445A
# US8460931B2
```

### 3. patent-downloader

**位置**: `dev/tools/patent_downloader/`

**功能**: 从Google Patents下载专利PDF

**可用工具**:
- `download_patent` - 下载单个专利
- `download_patents` - 批量下载
- `download_patents_from_file` - 从文件下载
- `get_patent_info` - 获取专利信息

**输入**: 专利号列表
**输出**: PDF文件 (按国家/地区自动分类)

**支持的专利号格式**:
- 中国: `CN112233445A`, `CN202110000001`
- 美国: `US8460931B2`, `US20230123456A1`
- 欧洲: `EP1234567B1`
| PCT: `WO2023123456A1`

### 4. IntegratedPatentDownloader (新增)

**位置**: `production/dev/scripts/patent_full_text/integrated_downloader.py`

**核心功能**:
- 封装完整元数据的下载请求
- 自动按国家/地区分类 (CN/US/EP/WO)
- 维护下载→数据库映射关系
- 支持从patent-search或手动输入创建请求

**关键类**:
```python
PatentDownloadRequest  # 携带完整元数据的下载请求
MetadataTracker       # 映射关系管理器
IntegratedPatentDownloader  # 下载协调器
```

---

## 三、使用方式

### 方式A: patent-search检索 (推荐)

**适用**: 需要检索并下载中国专利

```python
from integrated_downloader import IntegratedPatentDownloader

# 1. 使用patent-search检索
patents = search_cn_patents(
    query="人工智能",
    patent_type="发明",
    limit=10
)

# 2. 创建下载请求 (自动包含PostgreSQL ID)
downloader = IntegratedPatentDownloader()
requests = downloader.create_requests_from_patent_search(patents)

# 3. 批量下载
results = downloader.download_batch(requests)

# 4. 更新数据库
for request, result in zip(requests, results):
    if result.success:
        update_patent_pdf_path(
            postgres_id=request.postgres_id,
            pdf_path=result.file_path
        )
```

**优势**:
- ✅ 包含完整元数据
- ✅ 自动关联PostgreSQL记录
- ✅ 无需后处理匹配

### 方式B: 手动输入专利号

**适用**: 已知专利号，需要下载PDF

```python
from integrated_downloader import IntegratedPatentDownloader

# 1. 准备专利号列表
patent_numbers = [
    "CN112233445A",
    "US8460931B2",
    "WO2023123456A1"
]

# 2. 创建下载请求
downloader = IntegratedPatentDownloader()
requests = downloader.create_requests_from_patent_numbers(
    patent_numbers,
    metadata={"source": "manual", "case_id": "CASE-2025-001"}
)

# 3. 批量下载
results = downloader.download_batch(requests)

# 4. 后处理: 通过申请号匹配PostgreSQL
for request, result in zip(requests, results):
    if result.success:
        # 通过申请号查找PostgreSQL记录
        patent = get_patent_by_application_number(
            request.application_number or request.patent_number
        )
        if patent:
            update_patent_pdf_path(patent['id'], result.file_path)
```

### 方式C: 从文件批量下载

**适用**: 从文本文件或CSV文件批量下载

```python
from integrated_downloader import IntegratedPatentDownloader

# 1. 从文件读取专利号
def read_patent_numbers(file_path):
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

patent_numbers = read_patent_numbers("patents.txt")

# 2. 创建下载请求
downloader = IntegratedPatentDownloader()
requests = downloader.create_requests_from_patent_numbers(
    patent_numbers,
    metadata={"source": "file", "file_name": "patents.txt"}
)

# 3. 批量下载
results = downloader.download_batch(requests)
```

---

## 四、数据流向

```
检索阶段:
┌─────────────────────────────────────────────────────────────┐
│ patent-search          手动输入                               │
│     │                     │                                  │
│     │ 24字段+UUID          │ 专利号列表                        │
│     └─────────┬───────────┘                                  │
│               │                                             │
│               ▼                                             │
└─────── IntegratedPatentDownloader ───────────────────────────┘
                    │
                    ▼
         ┌───────────────────────┐
         │  patent-downloader    │
         │  只接受专利号          │
         │  下载PDF              │
         └───────────────────────┘
                    │
                    ▼
         ┌───────────────────────┐
         │  存储层               │
         ├───────────────────────┤
         │ PDF: CN/US/EP/WO/     │
         │ 映射: mapping.json    │
         │ 数据: PostgreSQL      │
         └───────────────────────┘
```

---

## 五、目录结构

```
/Users/xujian/apps/apps/patents/
├── PDF/                          # PDF存储
│   ├── CN/                       # 中国专利
│   ├── US/                       # 美国专利
│   ├── EP/                       # 欧洲专利
│   └── WO/                       # PCT专利
│
├── checkpoints/                  # 检查点
│   └── download_mapping.json     # 下载映射记录
│
└── logs/                         # 日志文件

/Users/xujian/Athena工作平台/
├── production/dev/scripts/patent_full_text/
│   ├── integrated_downloader.py   # 集成下载器 ⭐
│   ├── test_integration.py        # 集成测试
│   ├── verify_integration.py      # 验证脚本
│   └── FINAL_ARCHITECTURE.md      # 本文档
│
├── dev/tools/patent_downloader/       # PDF下载工具
└── mcp-servers/
    └── patent-search-mcp-server/  # 中国专利检索
```

---

## 六、API参考

### IntegratedPatentDownloader

```python
class IntegratedPatentDownloader:
    def __init__(self, default_output_dir="/Users/xujian/apps/apps/patents/PDF")

    # 从patent-search结果创建请求
    def create_requests_from_patent_search(
        self, patents_data: List[Dict]
    ) -> List[PatentDownloadRequest]

    # 从专利号列表创建请求
    def create_requests_from_patent_numbers(
        self, patent_numbers: List[str], metadata: Dict
    ) -> List[PatentDownloadRequest]

    # 下载单个专利
    def download_single(self, request: PatentDownloadRequest) -> PatentDownloadResult

    # 批量下载
    def download_batch(self, requests: List[PatentDownloadRequest]) -> List[PatentDownloadResult]

    # 映射查询
    @property
    def tracker(self) -> MetadataTracker
```

### PatentDownloadRequest

```python
@dataclass
class PatentDownloadRequest:
    patent_number: str              # 专利号 (必需)
    application_number: str         # 申请号
    postgres_id: str                # PostgreSQL UUID
    patent_name: str                # 专利名称
    applicant: str                  # 申请人
    source: str                     # 来源: patent_search, manual, file
    output_dir: str                 # 输出目录 (可选)
```

---

## 七、完整示例

### 示例1: 复审程序对比文件下载

```python
from integrated_downloader import IntegratedPatentDownloader

# 复审程序中的对比文件清单
comparison_files = [
    "CN112233445A",  # 对比文件1
    "US8460931B2",  # 对比文件2
    "EP1234567B1",  # 对比文件3
]

# 创建下载器
downloader = IntegratedPatentDownloader()

# 创建请求
requests = downloader.create_requests_from_patent_numbers(
    comparison_files,
    metadata={
        "source": "reexamination_case",
        "case_id": "CASE-2025-001",
        "case_type": "复审"
    }
)

# 批量下载
results = downloader.download_batch(requests)

# 输出结果
print(f"\n下载结果:")
for request, result in zip(requests, results):
    status = "✅" if result.success else "❌"
    print(f"{status} {request.patent_number} → {result.file_path}")
```

### 示例2: 无效程序证据收集

```python
# 从文本文件读取专利号
def read_patent_list(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

# 读取专利号
patent_numbers = read_patent_list("invalidation_evidence.txt")

# 下载
downloader = IntegratedPatentDownloader()
requests = downloader.create_requests_from_patent_numbers(
    patent_numbers,
    metadata={"source": "invalidation", "case_id": "INV-2025-001"}
)
results = downloader.download_batch(requests)

# 统计
successful = sum(1 for r in results if r.success)
print(f"下载完成: {successful}/{len(results)} 成功")
```

### 示例3: patent-search检索并下载

```python
# 1. 检索
patents = search_cn_patents(
    query="人工智能 图像识别",
    patent_type="发明",
    start_year=2020,
    limit=20
)

# 2. 下载
downloader = IntegratedPatentDownloader()
requests = downloader.create_requests_from_patent_search(patents)
results = downloader.download_batch(requests)

# 3. 更新数据库
for request, result in zip(requests, results):
    if result.success:
        sql = f"""
        UPDATE patents SET
            pdf_path = '{result.file_path}',
            pdf_source = 'patent_search',
            pdf_downloaded_at = NOW(),
            full_text_processed = FALSE
        WHERE id = '{request.postgres_id}'
        """
        execute_sql(sql)
```

---

## 八、下一步实施

### Phase 1: 基础设施 ✅ (已完成)
- ✅ 创建 `/Users/xujian/apps/apps/patents/` 目录结构
- ✅ 扩展 PostgreSQL patents 表
- ✅ 创建 Qdrant `patent_full_text` 集合
- ✅ 创建 NebulaGraph `patent_full_text` 空间
- ✅ 实现 IntegratedPatentDownloader

### Phase 2: 处理管道 (待开发)
- [ ] PDF文本提取
- [ ] 权利要求解析
- [ ] 向量化处理 (BGE)
- [ ] 知识图谱构建
- [ ] PostgreSQL自动更新

### Phase 3: 业务集成 (待开发)
- [ ] 新颖性分析工具
- [ ] 创造性分析工具
- [ ] 复审/无效程序支持

---

## 九、关键文件

| 文件 | 功能 |
|------|------|
| `integrated_downloader.py` | 集成下载器 (核心) |
| `test_integration.py` | 集成测试脚本 |
| `setup_qdrant.py` | Qdrant集合设置 |
| `setup_nebula_graph.py` | NebulaGraph空间设置 |

---

**结论**:

架构简化完成！保留两种专利获取方式：

1. **patent-search MCP**: 检索中国专利，包含完整元数据和PostgreSQL ID
2. **手动输入**: 已知专利号，直接下载PDF

核心是使用 `IntegratedPatentDownloader` 作为中间层，统一处理两种来源的下载请求。
