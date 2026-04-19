# 增强文档解析器 - 集成minerU OCR

> **创建日期**: 2026-04-19
> **版本**: v2.0.0 - OCR增强版
> **核心技术**: minerU OCR引擎

---

## 功能概述

增强文档解析器支持多种文档格式的智能解析，包括OCR（光学字符识别）功能。

### 支持的格式

| 格式类别 | 支持格式 | 解析方法 |
|---------|---------|---------|
| **文本文件** | .txt, .md, .py, .js, .json, .yaml, .xml, .html, .css | 直接读取 |
| **PDF文档** | .pdf | minerU OCR |
| **图片文件** | .png, .jpg, .jpeg, .bmp, .tiff, .gif | minerU OCR |
| **Word文档** | .docx, .doc | 暂不支持（计划中） |

### OCR功能

- ✅ PDF文档OCR识别
- ✅ 扫描件图片OCR识别
- ✅ 表格识别和提取
- ✅ 图片提取
- ✅ Markdown格式输出
- ✅ 多语言支持

---

## 快速开始

### 1. 检查minerU服务状态

```bash
# 检查服务健康
curl http://localhost:7860/health

# 或者使用Python
python3 -c "import aiohttp; asyncio.run(aiohttp.ClientSession().get('http://localhost:7860/health'))"
```

### 2. 基本使用

```python
from core.tools.enhanced_document_parser import parse_document

# 解析文本文件
result = await parse_document("/path/to/document.txt")

# 解析PDF（使用OCR）
result = await parse_document(
    "/path/to/document.pdf",
    use_ocr=True,
    extract_images=True,
    extract_tables=True
)

# 解析图片（使用OCR）
result = await parse_document(
    "/path/to/image.png",
    use_ocr=True
)
```

---

## minerU部署指南

### 方式1: Docker部署（推荐）

```bash
# 1. 拉取minerU镜像
docker pull mineru/mineru:latest

# 2. 运行容器
docker run -d \
  --name mineru \
  -p 7860:7860 \
  -v /path/to/models:/models \
  mineru/mineru:latest

# 3. 查看日志
docker logs -f mineru

# 4. 检查健康
curl http://localhost:7860/health
```

### 方式2: 本地安装

```bash
# 1. 安装依赖
pip install mineru

# 2. 启动服务
mineru serve --port 7860

# 3. 验证
curl http://localhost:7860/health
```

### 方式3: Docker Compose（推荐用于生产）

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  mineru:
    image: mineru/mineru:latest
    container_name: athena-mineru
    restart: unless-stopped
    ports:
      - "7860:7860"
    volumes:
      - ./models:/models
      - ./output:/output
    environment:
      - MINERU_PORT=7860
      - MINERU_WORKERS=4
      - MINERU_TIMEOUT=120
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7860/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

启动服务：

```bash
docker compose up -d
```

---

## API使用说明

### 核心API

#### 1. parse_document - 智能解析

```python
result = await parse_document(
    file_path="/path/to/document.pdf",
    use_ocr=True,              # 是否使用OCR
    extract_images=True,        # 是否提取图片
    extract_tables=True,        # 是否提取表格
    max_length=50000           # 最大内容长度
)
```

**返回格式**:

```json
{
  "success": true,
  "method": "mineru_ocr",
  "content": "文档文本内容...",
  "markdown": "# Markdown格式...",
  "images": ["image1.png", "image2.png"],
  "tables": [{"table1": "..."}],
  "pages": 10,
  "file_info": {
    "name": "document.pdf",
    "size": 1024000,
    "size_mb": 0.98,
    "extension": ".pdf",
    "mime_type": "application/pdf"
  },
  "metadata": {
    "engine": "minerU",
    "processing_time": 15.3,
    "ocr_confidence": 0.95
  }
}
```

#### 2. parse_pdf_with_ocr - PDF专用

```python
from core.tools.enhanced_document_parser import parse_pdf_with_ocr

result = await parse_pdf_with_ocr("/path/to/document.pdf")
```

#### 3. parse_image_with_ocr - 图片专用

```python
from core.tools.enhanced_document_parser import parse_image_with_ocr

result = await parse_image_with_ocr("/path/to/image.png")
```

#### 4. enhanced_document_parser_handler - 工具处理器

```python
from core.tools.enhanced_document_parser import enhanced_document_parser_handler

result = await enhanced_document_parser_handler({
    "file_path": "/path/to/document.pdf",
    "use_ocr": True,
    "extract_images": True,
    "extract_tables": True,
    "max_length": 50000
}, context={})
```

---

## 高级功能

### 1. 表格提取

```python
result = await parse_document(
    "/path/to/document.pdf",
    extract_tables=True
)

# 访问提取的表格
for table in result.get("tables", []):
    print(table)
```

### 2. 图片提取

```python
result = await parse_document(
    "/path/to/document.pdf",
    extract_images=True
)

# 访问提取的图片路径
for image_path in result.get("images", []):
    print(f"提取的图片: {image_path}")
```

### 3. Markdown输出

```python
result = await parse_document(
    "/path/to/document.pdf",
    use_ocr=True
)

# 获取Markdown格式
markdown_content = result.get("markdown", "")
print(markdown_content)
```

### 4. OCR置信度

```python
result = await parse_document(
    "/path/to/document.pdf",
    use_ocr=True
)

# 检查OCR置信度
confidence = result["metadata"]["ocr_confidence"]
print(f"OCR置信度: {confidence:.2%}")

if confidence < 0.8:
    print("⚠️  OCR置信度较低，可能需要人工校对")
```

---

## 错误处理

### 常见错误及解决方案

#### 错误1: minerU服务不可用

**症状**: `minerU服务不可用，无法进行OCR解析`

**解决方案**:
```bash
# 检查服务状态
docker ps | grep mineru

# 重启服务
docker restart mineru

# 或重新部署
cd ~/projects/mineru
docker compose up -d
```

#### 错误2: 文件过大

**症状**: `文件过大 (XX.XMB)，minerU限制50MB`

**解决方案**:
- 压缩文件
- 分割文件
- 或调整minerU配置增加限制

#### 错误3: OCR处理超时

**症状**: `OCR处理超时（>120秒）`

**解决方案**:
```python
# 增加超时时间
import os
os.environ["MINERU_TIMEOUT"] = "300"  # 5分钟

# 或减少处理内容（如提取前几页）
```

#### 错误4: 不支持的格式

**症状**: `暂不支持 .xyz 格式`

**解决方案**:
- 转换文件格式（如将.doc转为.docx）
- 检查文件扩展名是否正确

---

## 性能优化

### 1. 批量处理

```python
async def batch_parse(file_paths):
    """批量解析文档"""
    parser = await get_document_parser()

    tasks = [
        parser.parse(fp, use_ocr=True)
        for fp in file_paths
    ]

    results = await asyncio.gather(*tasks)
    await parser.close()

    return results
```

### 2. 缓存结果

```python
import hashlib

def get_file_hash(file_path):
    """计算文件哈希"""
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

# 使用哈希作为缓存键
cache_key = get_file_hash(file_path)
# 检查缓存...
```

### 3. 并发控制

```python
import asyncio

async def parse_with_limit(file_paths, max_concurrent=5):
    """限制并发数的批量解析"""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def parse_one(file_path):
        async with semaphore:
            return await parse_document(file_path)

    tasks = [parse_one(fp) for fp in file_paths]
    return await asyncio.gather(*tasks)
```

---

## 配置选项

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `MINERU_API_URL` | `http://localhost:7860` | minerU服务地址 |
| `MINERU_TIMEOUT` | `120` | OCR处理超时时间（秒） |

### 代码配置

```python
# 创建自定义配置的解析器
from core.tools.enhanced_document_parser import EnhancedDocumentParser

parser = EnhancedDocumentParser(
    mineru_url="http://custom-host:7860"
)
```

---

## 集成到工具系统

### 注册工具

```python
from core.tools.enhanced_document_parser import enhanced_document_parser_handler
from core.tools.base import ToolDefinition, ToolCategory, ToolCapability

manager.register_tool(ToolDefinition(
    tool_id="enhanced_document_parser",
    name="增强文档解析器",
    category=ToolCategory.DATA_EXTRACTION,
    description="增强文档解析工具 - 支持OCR、表格提取、图片提取",
    capability=ToolCapability(
        input_types=["document", "image", "pdf"],
        output_types=["text", "markdown", "structured_data"],
        domains=["all"],
        task_types=["parse", "extract", "ocr"]
    ),
    required_params=["file_path"],
    optional_params=["use_ocr", "extract_images", "extract_tables", "max_length"],
    handler=enhanced_document_parser_handler,
    timeout=120.0,  # OCR可能需要较长时间
    priority=ToolPriority.HIGH
))
```

### 使用示例

```python
# 通过工具系统调用
result = await call_tool(
    "enhanced_document_parser",
    parameters={
        "file_path": "/path/to/patent.pdf",
        "use_ocr": True,
        "extract_tables": True
    }
)
```

---

## 测试

### 运行测试

```bash
# 运行单元测试
python3 -m pytest tests/tools/test_enhanced_document_parser.py -v

# 运行快速测试
python3 scripts/test_enhanced_document_parser.py
```

### 测试覆盖率

- 文本文件解析 ✅
- PDF OCR（需要minerU）⚠️
- 图片OCR（需要minerU）⚠️
- 错误处理 ✅
- 边界条件 ✅

---

## 故障排查

### 问题1: 导入错误

**错误**: `ModuleNotFoundError: No module named 'aiohttp'`

**解决**:
```bash
pip install aiohttp
```

### 问题2: OCR识别率低

**可能原因**:
- 图片质量差
- 图片分辨率低
- 文字模糊
- 特殊字体

**解决**:
- 提高扫描质量
- 调整图片对比度
- 使用更高分辨率扫描

### 问题3: 处理速度慢

**可能原因**:
- 文件过大
- OCR并发限制
- 网络延迟

**解决**:
- 调整`MINERU_TIMEOUT`
- 优化minerU配置（增加workers）
- 使用本地文件而非网络路径

---

## 最佳实践

### 1. 文件预处理

```python
# 处理前检查文件
path = Path(file_path)

# 检查大小
if path.stat().st_size > 50 * 1024 * 1024:  # 50MB
    print("文件过大，考虑压缩或分割")

# 检查格式
if path.suffix not in ['.pdf', '.png', '.jpg', '.txt']:
    print(f"不支持的格式: {path.suffix}")
```

### 2. 结果验证

```python
result = await parse_document(file_path, use_ocr=True)

# 验证结果
if result["success"]:
    # 检查OCR置信度
    if "metadata" in result:
        confidence = result["metadata"].get("ocr_confidence", 0)
        if confidence < 0.8:
            print("⚠️  OCR置信度较低，建议人工校对")

    # 检查内容长度
    content_length = len(result.get("content", ""))
    if content_length == 0:
        print("⚠️  未提取到内容")
```

### 3. 资源清理

```python
parser = await get_document_parser()

try:
    result = await parser.parse(file_path)
    # 处理结果...
finally:
    await parser.close()  # 清理资源
```

---

## 总结

### 优势

- ✅ 多格式支持
- ✅ OCR功能强大
- ✅ 易于集成
- ✅ 性能可配置
- ✅ 错误处理完善

### 局限

- ⚠️ 依赖minerU服务
- ⚠️ OCR质量取决于输入
- ⚠️ 大文件处理时间较长
- ⚠️ Word格式暂不支持

### 适用场景

- 专利文档解析
- 扫描件数字化
- 表格数据提取
- 图片文字识别
- 批量文档处理

---

**文档版本**: v1.0
**最后更新**: 2026-04-19
**维护者**: Athena平台团队
