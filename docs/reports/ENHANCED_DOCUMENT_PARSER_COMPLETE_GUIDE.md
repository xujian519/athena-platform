# Athena增强文档解析器 - 完整使用指南

> **创建日期**: 2026-04-19  
> **版本**: v2.0.0 - OCR增强版  
> **核心技术**: minerU OCR + 本地集成

---

## 功能概述

Athena增强文档解析器支持多种文档格式的智能解析，集成minerU OCR引擎，提供强大的文档处理能力。

### 支持的格式

| 格式类别 | 支持格式 | 解析方法 | 状态 |
|---------|---------|---------|------|
| **文本文件** | .txt, .md, .py, .js, .json, .yaml, .xml, .html, .css | 直接读取 | ✅ 可用 |
| **PDF文档** | .pdf | minerU OCR | ⚠️ 需启动minerU |
| **图片文件** | .png, .jpg, .jpeg, .bmp, .tiff, .gif | minerU OCR | ⚠️ 需启动minerU |
| **Word文档** | .docx, .doc | 暂不支持 | 🔄 计划中 |

### 核心功能

- ✅ **文本文件解析** - 快速读取文本内容
- ✅ **PDF OCR识别** - 扫描PDF转文字
- ✅ **图片OCR识别** - 图片文字提取
- ✅ **表格提取** - 自动识别和提取表格
- ✅ **图片提取** - 提取文档中的图片
- ✅ **Markdown输出** - 结构化Markdown格式
- ✅ **多语言支持** - 中文、英文等

---

## 快速开始

### 1. 启动minerU服务

minerU已集成在项目中，位于 `/Users/xujian/MinerU`

```bash
# 使用启动脚本
./scripts/start_mineru.sh

# 或手动启动
cd /Users/xujian/MinerU
docker compose --file docker/compose.yaml up -d mineru-gradio
```

**服务地址**:
- Gradio界面: http://localhost:7860
- API端点: http://localhost:7860/api/v1/general

### 2. 基本使用

```python
from core.tools.enhanced_document_parser import parse_document

# 解析文本文件
result = await parse_document("/path/to/document.txt")

# 解析PDF（需要minerU）
result = await parse_document(
    "/path/to/document.pdf",
    use_ocr=True,
    extract_images=True,
    extract_tables=True
)

# 解析图片（需要minerU）
result = await parse_document(
    "/path/to/image.png",
    use_ocr=True
)
```

---

## API详解

### 核心函数

#### parse_document - 智能解析

```python
result = await parse_document(
    file_path="/path/to/document.pdf",
    use_ocr=True,              # 是否使用OCR（默认True）
    extract_images=True,        # 是否提取图片（默认True）
    extract_tables=True,        # 是否提取表格（默认True）
    max_length=50000           # 最大内容长度（默认50000）
)
```

**参数说明**:
- `file_path`: 文件路径（必需）
- `use_ocr`: 是否使用OCR（默认True）
- `extract_images`: 是否提取文档中的图片（默认True）
- `extract_tables`: 是否提取表格（默认True）
- `max_length`: 返回内容的最大长度（默认50000字符）

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
    "mime_type": "application/pdf",
    "modified": "2026-04-19T..."
  },
  "metadata": {
    "engine": "minerU",
    "processing_time": 15.3,
    "ocr_confidence": 0.95
  }
}
```

#### parse_pdf_with_ocr - PDF专用

```python
from core.tools.enhanced_document_parser import parse_pdf_with_ocr

result = await parse_pdf_with_ocr("/path/to/document.pdf")
```

#### parse_image_with_ocr - 图片专用

```python
from core.tools.enhanced_document_parser import parse_image_with_ocr

result = await parse_image_with_ocr("/path/to/image.png")
```

#### enhanced_document_parser_handler - 工具处理器

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

## 使用示例

### 示例1: 解析专利文档

```python
from core.tools.enhanced_document_parser import parse_pdf_with_ocr

# 解析专利PDF
result = await parse_pdf_with_ocr("/path/to/patent.pdf")

if result["success"]:
    print(f"✅ 解析成功")
    print(f"   页数: {result['pages']}")
    print(f"   OCR置信度: {result['metadata']['ocr_confidence']:.2%}")
    
    # 获取文本内容
    text_content = result["content"]
    
    # 获取Markdown格式
    markdown_content = result.get("markdown", "")
    
    # 检查是否有表格
    if result.get("tables"):
        print(f"   提取了 {len(result['tables'])} 个表格")
    
    # 检查是否有图片
    if result.get("images"):
        print(f"   提取了 {len(result['images'])} 个图片")
else:
    print(f"❌ 解析失败: {result['error']}")
```

### 示例2: 批量处理文档

```python
import asyncio
from pathlib import Path
from core.tools.enhanced_document_parser import parse_document

async def batch_process(directory):
    """批量处理目录中的所有文档"""
    path = Path(directory)
    
    # 获取所有PDF文件
    pdf_files = list(path.glob("*.pdf"))
    
    print(f"📄 找到 {len(pdf_files)} 个PDF文件")
    
    results = []
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n处理 {i}/{len(pdf_files)}: {pdf_file.name}")
        
        result = await parse_document(
            str(pdf_file),
            use_ocr=True,
            extract_tables=True
        )
        
        results.append(result)
        
        if result["success"]:
            print(f"   ✅ 成功 - {result['pages']}页")
        else:
            print(f"   ❌ 失败 - {result.get('error')}")
    
    return results

# 使用
results = await batch_process("/path/to/documents")
```

### 示例3: 图片OCR识别

```python
from core.tools.enhanced_document_parser import parse_image_with_ocr

# 解析扫描图片
result = await parse_image_with_ocr("/path/to/scanned_page.png")

if result["success"]:
    print(f"✅ OCR识别成功")
    print(f"   识别内容:\n{result['content']}")
    print(f"   置信度: {result['metadata']['ocr_confidence']:.2%}")
else:
    print(f"❌ OCR识别失败: {result['error']}")
```

---

## 管理和监控

### 查看minerU状态

```bash
# 检查容器状态
docker ps | grep mineru

# 查看日志
docker logs -f mineru-gradio

# 健康检查
curl http://localhost:7860
```

### 停止minerU服务

```bash
# 使用docker compose
cd /Users/xujian/MinerU
docker compose --file docker/compose.yaml down

# 或直接停止容器
docker stop mineru-gradio
docker rm mineru-gradio
```

### 重启minerU服务

```bash
cd /Users/xujian/MinerU
docker compose --file docker/compose.yaml restart mineru-gradio
```

---

## 故障排查

### 问题1: minerU服务未启动

**症状**: `minerU服务不可用，无法进行OCR解析`

**解决方案**:
```bash
# 启动服务
./scripts/start_mineru.sh

# 或手动启动
cd /Users/xujian/MinerU
docker compose --file docker/compose.yaml up -d mineru-gradio

# 验证
curl http://localhost:7860
```

### 问题2: OCR识别率低

**症状**: 返回内容不正确或为空

**可能原因**:
- 文档质量差
- 分辨率过低
- 文字模糊
- 特殊字体

**解决方案**:
- 提高扫描质量
- 使用更高分辨率
- 调整图片对比度

### 问题3: 处理超时

**症状**: `OCR处理超时（>120秒）`

**解决方案**:
```python
# 增加超时时间
import os
os.environ["MINERU_TIMEOUT"] = "300"  # 5分钟

# 重新导入
from core.tools.enhanced_document_parser import parse_document
```

### 问题4: 文件过大

**症状**: `文件过大 (XX.XMB)，minerU限制50MB`

**解决方案**:
- 压缩PDF
- 分割文件
- 或分页处理

---

## 性能优化

### 1. 批量处理并发控制

```python
import asyncio

async def parse_with_limit(file_paths, max_concurrent=3):
    """限制并发数避免资源耗尽"""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def parse_one(file_path):
        async with semaphore:
            return await parse_document(file_path, use_ocr=True)

    tasks = [parse_one(fp) for fp in file_paths]
    return await asyncio.gather(*tasks)
```

### 2. 结果缓存

```python
import hashlib
import json
from pathlib import Path

def get_file_hash(file_path):
    """计算文件哈希用于缓存"""
    return hashlib.md5(Path(file_path).read_bytes()).hexdigest()

async def parse_with_cache(file_path, cache_dir="/tmp/parse_cache"):
    """带缓存的解析"""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(exist_ok=True)
    
    # 计算缓存键
    file_hash = get_file_hash(file_path)
    cache_file = cache_dir / f"{file_hash}.json"
    
    # 检查缓存
    if cache_file.exists():
        with open(cache_file) as f:
            return json.load(f)
    
    # 解析文档
    result = await parse_document(file_path, use_ocr=True)
    
    # 保存缓存
    with open(cache_file, 'w') as f:
        json.dump(result, f)
    
    return result
```

### 3. 分页处理大文件

```python
async def parse_pdf_in_chunks(file_path, chunk_size=10):
    """分页处理大PDF"""
    # 这里可以扩展为分页处理
    # 目前minerU支持全文档解析
    result = await parse_document(
        file_path,
        use_ocr=True,
        max_length=100000  # 增加内容长度限制
    )
    
    return result
```

---

## 集成到Athena工具系统

### 注册增强文档解析器

```python
from core.tools.enhanced_document_parser import enhanced_document_parser_handler
from core.tools.base import ToolDefinition, ToolCategory, ToolPriority, ToolCapability

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

### 通过工具系统调用

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

print(f"解析状态: {result['success']}")
print(f"内容长度: {len(result.get('content', ''))}")
```

---

## 测试

### 运行测试

```bash
# 运行完整测试套件
python3 -m pytest tests/tools/test_enhanced_document_parser.py -v

# 运行快速测试
python3 scripts/test_enhanced_document_parser.py
```

### 测试覆盖

- ✅ 文本文件解析
- ✅ 错误处理
- ✅ 参数验证
- ⚠️ PDF OCR（需要minerU运行）
- ⚠️ 图片OCR（需要minerU运行）

---

## 配置选项

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `MINERU_API_URL` | `http://localhost:7860` | minerU服务地址 |
| `MINERU_TIMEOUT` | `120` | OCR处理超时（秒） |

### 配置示例

```bash
# 在 .env 文件中配置
echo "MINERU_API_URL=http://localhost:7860" >> .env
echo "MINERU_TIMEOUT=120" >> .env

# 或在代码中配置
import os
os.environ["MINERU_API_URL"] = "http://localhost:7860"
os.environ["MINERU_TIMEOUT"] = "300"  # 增加到5分钟
```

---

## 最佳实践

### 1. 文件预处理

```python
from pathlib import Path

def validate_file(file_path):
    """验证文件是否适合OCR处理"""
    path = Path(file_path)
    
    # 检查文件存在
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 检查文件大小
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > 50:
        raise ValueError(f"文件过大 ({size_mb:.1f}MB)，建议压缩或分割")
    
    # 检查格式
    supported_formats = ['.pdf', '.png', '.jpg', '.jpeg', '.txt', '.md']
    if path.suffix not in supported_formats:
        raise ValueError(f"不支持的格式: {path.suffix}")
    
    return True

# 使用
try:
    validate_file("/path/to/document.pdf")
    result = await parse_document("/path/to/document.pdf")
except (FileNotFoundError, ValueError) as e:
    print(f"文件验证失败: {e}")
```

### 2. 结果验证

```python
async def parse_and_validate(file_path):
    """解析并验证结果"""
    result = await parse_document(file_path, use_ocr=True)
    
    if not result["success"]:
        print(f"❌ 解析失败: {result['error']}")
        return None
    
    # 检查OCR置信度
    if "metadata" in result:
        confidence = result["metadata"].get("ocr_confidence", 0)
        if confidence < 0.8:
            print(f"⚠️  OCR置信度较低: {confidence:.2%}")
            print("   建议人工校对结果")
    
    # 检查内容长度
    content_length = len(result.get("content", ""))
    if content_length == 0:
        print("⚠️  未提取到内容")
        return None
    
    # 检查页数
    pages = result.get("pages", 0)
    if pages == 0 and result.get("method") == "mineru_ocr":
        print("⚠️  OCR未识别到页数")
    
    return result
```

### 3. 资源清理

```python
from core.tools.enhanced_document_parser import get_document_parser

async def parse_with_cleanup(file_path):
    """解析并清理资源"""
    parser = await get_document_parser()
    
    try:
        result = await parser.parse(file_path, use_ocr=True)
        # 处理结果...
        return result
    finally:
        await parser.close()  # 确保释放资源
```

---

## 总结

### 功能对比

| 功能 | 原版document_parser | 增强版document_parser |
|------|-------------------|---------------------|
| 文本文件 | ✅ | ✅ |
| PDF文档 | ❌ 仅提示 | ✅ OCR支持 |
| 图片OCR | ❌ 不支持 | ✅ 支持 |
| 表格提取 | ❌ 不支持 | ✅ 支持 |
| 图片提取 | ❌ 不支持 | ✅ 支持 |
| Markdown输出 | ❌ 不支持 | ✅ 支持 |
| OCR置信度 | ❌ 不提供 | ✅ 提供 |

### 使用建议

1. **文本文件** - 使用增强版或原版都可以
2. **PDF文档** - 必须使用增强版（启用OCR）
3. **扫描图片** - 必须使用增强版（启用OCR）
4. **表格提取** - 使用增强版
5. **批量处理** - 使用增强版的并发控制

### 下一步

1. ✅ 启动minerU服务
2. ✅ 测试文档解析功能
3. ✅ 集成到工具系统
4. ⏳ 添加Word文档支持
5. ⏳ 优化OCR识别率
6. ⏳ 添加更多格式支持

---

**文档版本**: v1.0  
**最后更新**: 2026-04-19  
**维护者**: Athena平台团队  
**状态**: ✅ 完成，可以投入使用
