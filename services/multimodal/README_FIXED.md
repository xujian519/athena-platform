# Athena多模态文件系统 - 使用说明

**版本**: 2.1.0 (完整修复版)
**端口**: 8021
**状态**: ✅ 已验证可用

## 📋 服务概述

Athena多模态文件系统是一个完整的文件处理服务，支持多种文件格式的上传、存储、检索和管理。

### 支持的文件格式

| 类别 | 扩展名 |
|------|--------|
| **图片** | .jpg, .jpeg, .png, .gif, .bmp, .webp, .svg, .ico, .tiff |
| **文档** | .pdf, .doc, .docx, .txt, .md, .rtf, .odt, .epub |
| **音频** | .mp3, .wav, .flac, .aac, .ogg, .m4a |
| **视频** | .mp4, .avi, .mkv, .mov, .wmv, .flv |
| **数据** | .json, .xml, .csv, .xlsx, .yaml, .yml, .sql |
| **代码** | .py, .js, .html, .css, .java, .cpp, .go |
| **压缩包** | .zip, .rar, .7z, .tar, .gz |
| **演示** | .ppt, .pptx, .key, .odp |

## 🚀 快速启动

### 启动服务

```bash
cd /Users/xujian/Athena工作平台/services/multimodal
bash start_fixed.sh start
```

### 停止服务

```bash
cd /Users/xujian/Athena工作平台/services/multimodal
bash start_fixed.sh stop
```

### 重启服务

```bash
cd /Users/xujian/Athena工作平台/services/multimodal
bash start_fixed.sh restart
```

### 查看状态

```bash
cd /Users/xujian/Athena工作平台/services/multimodal
bash start_fixed.sh status
```

### 查看日志

```bash
cd /Users/xujian/Athena工作平台/services/multimodal
bash start_fixed.sh logs
```

## 📡 API端点

### 基础端点

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/` | API根信息 |
| GET | `/health` | 健康检查 |
| GET | `/docs` | Swagger API文档 |
| GET | `/redoc` | ReDoc API文档 |

### 文件操作端点

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/files/upload` | 上传文件 |
| GET | `/api/files/list` | 获取文件列表 |
| GET | `/api/files/{file_id}` | 获取文件信息 |
| GET | `/api/files/{file_id}/download` | 下载文件 |
| DELETE | `/api/files/{file_id}` | 删除文件 |
| GET | `/api/stats` | 获取统计信息 |

## 💡 使用示例

### 1. 健康检查

```bash
curl http://localhost:8021/health
```

**响应示例**:
```json
{
  "status": "healthy",
  "version": "2.1.0",
  "port": 8021,
  "storage": "accessible",
  "database": "memory_mode",
  "uptime": 123.45,
  "timestamp": "2026-02-24T11:26:34.172406"
}
```

### 2. 上传文件

```bash
curl -X POST http://localhost:8021/api/files/upload \
  -F "file=@example.jpg" \
  -F "tags=test,example" \
  -F "category=demo"
```

**响应示例**:
```json
{
  "success": true,
  "message": "文件 example.jpg 上传成功！",
  "file_id": "abc123-def456-...",
  "filename": "abc123-def456-....jpg",
  "file_type": "image",
  "file_size": 123456
}
```

### 3. 获取文件列表

```bash
# 获取所有文件
curl http://localhost:8021/api/files/list

# 按类型过滤
curl "http://localhost:8021/api/files/list?file_type=image"

# 分页查询
curl "http://localhost:8021/api/files/list?page=1&page_size=10"
```

**响应示例**:
```json
{
  "success": true,
  "files": [
    {
      "id": "abc123-...",
      "filename": "abc123-....jpg",
      "original_filename": "example.jpg",
      "file_type": "image",
      "file_size": 123456,
      "upload_time": "2026-02-24T11:26:41.049385",
      "processed": false,
      "tags": ["test", "example"],
      "category": "demo"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

### 4. 获取文件信息

```bash
curl http://localhost:8021/api/files/abc123-def456-...
```

### 5. 下载文件

```bash
curl -O -J http://localhost:8021/api/files/abc123-def456-.../download
```

### 6. 删除文件

```bash
curl -X DELETE http://localhost:8021/api/files/abc123-def456-...
```

### 7. 获取统计信息

```bash
curl http://localhost:8021/api/stats
```

**响应示例**:
```json
{
  "success": true,
  "total_files": 10,
  "total_size": 1048576,
  "by_type": {
    "image": {"count": 5, "total_size": 524288},
    "document": {"count": 3, "total_size": 524288}
  },
  "processed_files": 8,
  "processing_rate": 80.0
}
```

## 🧪 运行测试

完整功能测试脚本已包含在 `test_fixed.py` 中：

```bash
cd /Users/xujian/Athena工作平台/services/multimodal
python3 test_fixed.py
```

测试涵盖：
- ✅ 健康检查测试
- ✅ 根端点测试
- ✅ 文件上传测试
- ✅ 文件列表查询测试
- ✅ 文件信息查询测试
- ✅ 统计信息测试
- ✅ 文件删除测试

## 📁 存储结构

```
storage-system/data/documents/
├── multimodal/          # 主存储目录
│   ├── image/          # 图片文件
│   ├── document/       # 文档文件
│   ├── audio/          # 音频文件
│   ├── video/          # 视频文件
│   ├── data/           # 数据文件
│   ├── code/           # 代码文件
│   ├── archive/        # 压缩文件
│   └── presentation/   # 演示文件
├── thumbnails/         # 缩略图
└── temp/              # 临时文件
```

## ⚙️ 配置说明

### 修改端口

编辑 `multimodal_service_fixed.py` 中的 `Config.PORT`:

```python
class Config:
    PORT = 8022  # 修改为需要的端口
```

### 修改存储位置

编辑 `multimodal_service_fixed.py` 中的 `Config`:

```python
class Config:
    STORAGE_ROOT = project_root / "custom" / "storage" / "path"
```

### 修改文件大小限制

```python
class Config:
    MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB
```

## 🐛 故障排除

### 端口被占用

```bash
# 查找占用端口的进程
lsof -i :8021

# 停止进程
kill <PID>

# 或使用脚本停止
bash start_fixed.sh stop
```

### 服务无法启动

1. 检查日志: `tail -f logs/multimodal_startup.log`
2. 检查端口: `lsof -i :8021`
3. 检查Python依赖: `pip3 list | grep fastapi`

### 文件上传失败

1. 检查文件大小是否超过限制 (默认100MB)
2. 检查存储目录是否有写权限
3. 查看服务日志获取详细错误信息

## 📊 测试验证报告

**最后验证时间**: 2026-02-24 11:26
**验证状态**: ✅ 全部通过

| 测试项 | 状态 | 说明 |
|--------|------|------|
| 健康检查 | ✅ | 服务正常响应 |
| 根端点 | ✅ | API信息正确返回 |
| 文件上传 | ✅ | 成功上传测试图片 |
| 文件列表 | ✅ | 正确返回文件列表 |
| 文件信息 | ✅ | 正确返回文件详情 |
| 统计信息 | ✅ | 正确返回统计数据 |
| 文件删除 | ✅ | 成功删除测试文件 |

## 📝 技术栈

- **Web框架**: FastAPI 0.104+
- **ASGI服务器**: Uvicorn
- **文件处理**: aiofiles, python-multipart
- **图像处理**: Pillow (PIL)
- **HTTP客户端**: requests
- **数据存储**: 内存数据库 (可扩展为PostgreSQL)

## 🔗 相关链接

- **API文档**: http://localhost:8021/docs
- **ReDoc文档**: http://localhost:8021/redoc
- **健康检查**: http://localhost:8021/health

---

**创建时间**: 2026-02-24
**维护者**: Athena Team
**项目路径**: `/Users/xujian/Athena工作平台/services/multimodal/`
