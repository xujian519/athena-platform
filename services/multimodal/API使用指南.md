# Athena 多模态文件系统 API 使用指南

## 🎉 系统已成功启动！

**服务地址**: http://localhost:8000

## 📚 API 文档

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔐 认证

系统使用JWT令牌进行认证。首先获取访问令牌：

```bash
curl -X POST http://localhost:8000/auth/login
```

响应示例：
```json
{
  "success": true,
  "access_token": "test_token_xxxx",
  "refresh_token": "refresh_xxxx",
  "expires_in": 86400,
  "user_info": {
    "user_id": "test_user",
    "role": "admin",
    "name": "测试用户"
  }
}
```

## 📁 文件操作

### 1. 上传文件

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/your/file.jpg" \
  http://localhost:8000/upload
```

### 2. 列出文件

```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/files
```

### 3. 下载文件

```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/files/{file_id}/download
```

## 🔄 批量操作

### 1. 创建批量任务

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation_type": "upload",
    "files": ["file1.jpg", "file2.pdf"]
  }' \
  http://localhost:8000/batch/operations
```

### 2. 查看批量任务状态

```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/batch/operations/{batch_id}
```

## 📊 性能监控

### 1. 获取监控仪表板

```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/monitoring/dashboard
```

响应包含：
- 系统资源使用情况（CPU、内存、磁盘）
- API性能指标
- 文件处理统计

### 2. 获取指标摘要

```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/monitoring/metrics?hours=1"
```

## 🤖 AI处理

### 1. 提交AI处理任务

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "your_file_id",
    "processing_type": "image_analysis",
    "options": {
      "analyze_colors": true,
      "extract_metadata": true
    }
  }' \
  http://localhost:8000/ai/process
```

### 2. 获取处理结果

```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/ai/process/{task_id}
```

支持的处理类型：
- `image_analysis` - 图像分析
- `document_parsing` - 文档解析
- `text_analysis` - 文本分析
- `content_extraction` - 内容提取

## 📦 存储管理

### 1. 获取存储统计

```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/storage/stats
```

### 2. 配置分布式存储

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "storage_type": "local",
    "tier": "hot",
    "base_path": "/path/to/storage"
  }' \
  http://localhost:8000/storage/configure
```

## 📝 版本管理

### 1. 获取文件版本列表

```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/files/{file_id}/versions
```

### 2. 创建新版本

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/new_file.jpg" \
  -F "change_type=update" \
  -F "comment=更新内容" \
  http://localhost:8000/files/{file_id}/versions
```

### 3. 比较版本

```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/files/{file_id}/versions/{v1}/compare/{v2}
```

## 🛠️ 快速测试

使用以下命令快速测试所有功能：

```bash
# 1. 健康检查
curl http://localhost:8000/health

# 2. 获取认证令牌
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 3. 上传测试文件
echo "测试文件内容" > /tmp/test.txt
FILE_ID=$(curl -s -X POST -F "file=@/tmp/test.txt" http://localhost:8000/upload | python3 -c "import sys, json; print(json.load(sys.stdin)['file_id'])")

# 4. 提交AI处理
TASK_ID=$(curl -s -X POST -H "Content-Type: application/json" -d "{\"file_id\":\"$FILE_ID\",\"processing_type\":\"text_analysis\"}" http://localhost:8000/ai/process | python3 -c "import sys, json; print(json.load(sys.stdin)['task_id'])")

# 5. 查看处理结果
curl -s http://localhost:8000/ai/process/$TASK_ID | python3 -m json.tool

# 6. 查看监控仪表板
curl -s http://localhost:8000/monitoring/dashboard | python3 -m json.tool
```

## 🎯 功能特性

✅ **已实现的功能**：
- JWT认证和权限管理
- 文件安全验证（类型、大小、内容扫描）
- 高性能缓存系统（Redis + 本地缓存）
- 实时性能监控和指标收集
- 批量文件操作管理
- 分布式存储支持
- 完整的版本控制系统
- AI智能处理（图像分析、文本处理等）
- 49个API端点

## 💡 使用提示

1. **文件大小限制**：默认最大100MB
2. **批量操作限制**：默认最多100个文件
3. **版本保留**：默认保留50个版本
4. **AI处理并发**：默认最多5个并发任务

## 🔒 安全特性

- 所有API端点需要认证（除了根路径和健康检查）
- JWT令牌过期时间：24小时
- 刷新令牌有效期：7天
- 文件内容安全扫描
- 基于角色的访问控制

---

## 🎉 系统状态

当前服务运行在：**http://localhost:8000**

系统状态：🟢 正常运行
文件数量：1
活动任务：0