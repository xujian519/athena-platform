# 专利检索与下载集成验证报告

**日期**: 2025-12-24
**验证范围**: patent-search MCP + patent-downloader MCP + 集成方案

---

## 一、验证结果总结

### 1. patent-search MCP ✅

**功能验证**: 通过
**数据源**: PostgreSQL patent_db (2800万+ 中国专利)

**可用工具**:
| 工具名 | 功能 | 输入 | 输出 |
|--------|------|------|------|
| search_cn_patents | 搜索中国专利 | query, patent_type, applicant等 | 专利列表+元数据 |
| get_cn_patent_by_id | 根据申请号获取详情 | application_number | 完整专利信息 |
| analyze_cn_patent_landscape | 专利布局分析 | query, group_by | 统计分析 |

**返回的元数据字段** (24个):
```json
{
  "id": "PostgreSQL UUID",
  "patent_name": "专利名称",
  "patent_type": "发明/实用新型/外观设计",
  "application_number": "申请号",
  "publication_number": "公开号",
  "authorization_number": "授权号",
  "applicant": "申请人",
  "inventor": "发明人",
  "ipc_main_class": "IPC主分类",
  "abstract": "摘要",
  "claims_content": "权利要求书",
  "application_date": "申请日",
  "publication_date": "公开日",
  ...
}
```

### 2. patent-downloader MCP ⚠️

**功能验证**: 下载功能正常
**数据源**: Google Patents
**位置**: `/Users/xujian/Athena工作平台/dev/tools/patent_downloader/`

**可用工具**:
| 工具名 | 功能 | 输入 |
|--------|------|------|
| download_patent | 下载单个专利 | patent_number, output_dir |
| download_patents | 批量下载 | patent_numbers[], output_dir |
| download_patents_from_file | 从文件下载 | file_path, has_header |
| get_patent_info | 获取专利信息 | patent_number |

**输入限制**:
```python
# 只接受专利号
download_patent(patent_number="CN112233445A")

# ❌ 不支持其他参数
# download_patent(
#     patent_number="CN112233445A",
#     postgres_id="xxx",  # 不支持
#     applicant="xxx",    # 不支持
#     ipc_code="xxx"      # 不支持
# )
```

### 3. Google Patents网页检索 - 待验证

**计划验证方式**:
1. 访问 patents.google.com
2. 检索关键词
3. 导出专利号列表
4. 传递给patent-downloader

---

## 二、集成问题分析

### 问题1: 上下文信息丢失

**现状流程**:
```
patent-search检索
  ↓
返回: 专利列表 + 完整元数据 (24字段)
  ↓
提取: patent_numbers[]  # 只提取专利号
  ↓
传递: patent-downloader
  ↓
下载: PDF文件
  ↓
❌ 丢失: 与PostgreSQL记录的关联
```

### 问题2: 后处理困难

下载的PDF文件:
- 文件名: `CN112233445A.pdf`
- 无法知道对应的PostgreSQL记录ID
- 无法知道申请人、发明人等上下文
- 需要重新通过申请号查询数据库重建关联

---

## 三、改进方案

### 方案: 集成中间层 (已实现)

创建 `IntegratedPatentDownloader` 作为中间层：

**核心功能**:
1. **元数据封装**: `PatentDownloadRequest` 携带完整上下文
2. **自动分类**: 按CN/US/EP/WO自动分配目录
3. **映射追踪**: `MetadataTracker` 维护下载→数据库关联
4. **批量处理**: 支持从patent-search结果直接创建下载任务

**数据流**:
```
patent-search检索
  ↓
PatentDownloadRequest[] (携带完整元数据)
  ↓
IntegratedPatentDownloader.download_batch()
  ↓
for each request:
  - 确定输出目录 (CN/US/EP/WO)
  - 调用patent-downloader (只传专利号)
  - 记录映射 (request → result → postgres_id)
  ↓
MetadataTracker 记录到 download_mapping.json
  ↓
PostgreSQL更新 (根据映射)
```

**文件结构**:
```
/Users/xujian/apps/apps/patents/
├── PDF/
│   ├── CN/           # 中国专利
│   ├── US/           # 美国专利
│   ├── EP/           # 欧洲专利
│   └── WO/           # PCT专利
└── checkpoints/
    └── download_mapping.json  # 下载映射记录
```

**映射记录格式**:
```json
{
  "cache_key": {
    "patent_number": "CN112233445A",
    "application_number": "CN202110000001",
    "postgres_id": "uuid-xxx",
    "file_path": "/Users/xujian/apps/apps/patents/PDF/CN/CN112233445A.pdf",
    "file_size": 1234567,
    "downloaded_at": "2025-12-24T22:30:00",
    "success": true,
    "metadata": {
      "patent_name": "一种人工智能算法",
      "applicant": "某某公司",
      "source": "patent_search"
    }
  }
}
```

---

## 四、使用示例

### 示例1: 从patent-search结果下载

```python
from integrated_downloader import IntegratedPatentDownloader

# 1. 执行patent-search检索
patents = search_cn_patents(query="人工智能", limit=10)

# 2. 创建下载请求
downloader = IntegratedPatentDownloader()
requests = downloader.create_requests_from_patent_search(patents)

# 3. 批量下载
results = downloader.download_batch(requests)

# 4. 查询映射
for request, result in zip(requests, results):
    if result.success:
        # 使用request.postgres_id更新数据库
        update_patent_pdf_path(
            postgres_id=request.postgres_id,
            pdf_path=result.file_path
        )
```

### 示例2: 从专利号列表下载

```python
# 1. 从Google Patents复制专利号
patent_numbers = [
    "CN112233445A",
    "US20231234567A1",
    "WO2023123456A1"
]

# 2. 创建下载请求
downloader = IntegratedPatentDownloader()
requests = downloader.create_requests_from_patent_numbers(
    patent_numbers,
    metadata={"source": "google_patents", "search_query": "AI"}
)

# 3. 批量下载
results = downloader.download_batch(requests)

# 4. 后处理：通过申请号关联PostgreSQL
for request, result in zip(requests, results):
    if result.success:
        patent = get_patent_by_application_number(request.application_number)
        if patent:
            update_patent_pdf_path(patent['id'], result.file_path)
```

---

## 五、下一步计划

### Phase 1: 验证Google Patents
1. 访问patents.google.com
2. 检索测试关键词
3. 验证专利号导出
4. 测试与patent-downloader集成

### Phase 2: 完善中间层
1. 添加PostgreSQL自动更新
2. 实现PDF处理触发
3. 添加错误重试机制

### Phase 3: 集成到MCP
1. 创建新的MCP工具
2. 支持带元数据的下载请求
3. 提供完整的检索→下载→处理工作流

---

## 六、关键文件

| 文件 | 位置 | 功能 |
|------|------|------|
| patent_search_mcp | mcp-servers/patent-search-mcp-server/ | 中国专利检索 |
| patent_downloader | dev/tools/patent_downloader/ | PDF下载 |
| integrated_downloader | production/dev/scripts/patent_full_text/ | 集成中间层 |
| verify_integration | production/dev/scripts/patent_full_text/ | 验证测试脚本 |

---

**结论**:

✅ patent-search MCP 功能完整，返回丰富元数据
✅ patent-downloader MCP 下载功能正常
⚠️ 存在集成问题: 上下文信息丢失
✅ 解决方案: IntegratedPatentDownloader 中间层

**推荐**: 使用中间层方案，维护元数据关联，实现检索→下载→数据库更新的完整流程。
