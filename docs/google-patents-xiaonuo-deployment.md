# Google Patents Meta Tags - 小娜集成部署文档

## 📋 概述

本文档描述了如何将基于Meta标签技术的Google专利检索模块部署到Athena平台，并为小娜提供专利检索调用能力。

## 🏗️ 架构设计

### 核心组件

1. **Google Patents Meta Retriever** (`google_patents_meta_retriever.py`)
   - 基于Meta标签和Jina AI的专利检索器
   - 支持多层降级策略
   - 智能内容质量评估

2. **MCP服务器** (`google-patents-meta-server/`)
   - 为小娜提供标准化的API接口
   - 支持Model Context Protocol (MCP)
   - 容器化部署支持

3. **小娜集成接口** (`xiaonuo_patent_integration.py`)
   - 专为小娜设计的调用接口
   - 会话管理和用户追踪
   - 统计和监控功能

## 🚀 部署步骤

### 1. 环境准备

```bash
# 检查Python环境
python3 --version  # 需要 Python 3.8+

# 检查Node.js环境
node --version     # 需要 Node.js 16+
npm --version      # 需要 npm 8+

# 安装Python依赖
pip3 install httpx beautifulsoup4 aiofiles
```

### 2. 快速启动

#### 方法一: 使用启动脚本（推荐）

```bash
cd /Users/xujian/Athena工作平台/mcp-servers
./start_google_patents_server.sh
```

#### 方法二: 使用Docker

```bash
cd /Users/xujian/Athena工作平台/mcp-servers

# 启动Google Patents服务器
docker-compose up google-patents-meta-server -d

# 查看日志
docker logs -f google-patents-meta-server
```

### 3. 验证部署

```bash
# 运行小娜集成测试
cd /Users/xujian/Athena工作平台/services/xiaonuo-integration
python3 xiaonuo_patent_demo.py
```

## 🤖 小娜调用接口

### 可用工具

1. **google_patents_search** - 专利搜索
   ```python
   result = await xiaonuo_search_patents(
       user_id="xiaonuo_user",
       session_id="session_123",
       query="人工智能 机器学习",
       max_results=10,
       priority="high"
   )
   ```

2. **google_patents_details** - 获取专利详情
   ```python
   details = await xiaonuo_get_patent_details(
       patent_id="CN202300000001.0",
       user_id="xiaonuo_user",
       session_id="session_123"
   )
   ```

3. **google_patents_export** - 导出专利数据
   ```python
   export_result = await xiaonuo_export_patents(
       patents=patent_list,
       format="json",
       filename="patents_export.json",
       user_id="xiaonuo_user",
       session_id="session_123"
   )
   ```

4. **google_patents_statistics** - 获取统计信息
   ```python
   stats = await xiaonuo_get_patent_statistics()
   ```

### 调用示例

```python
import asyncio
from xiaonuo_patent_integration import xiaonuo_search_patents

async def xiaonuo_patent_search():
    # 小娜专利搜索
    result = await xiaonuo_search_patents(
        user_id="xiaonuo_001",
        session_id="session_20251219",
        query="深度学习 神经网络",
        max_results=5,
        filters={"priority": "high"},
        priority="high"
    )

    if result['success']:
        print(f"✅ 小娜找到 {result['total_found']} 个专利")
        for patent in result['apps/apps/patents']:
            print(f"📄 {patent['title']}")
    else:
        print(f"❌ 搜索失败: {result['error']}")

# 运行
asyncio.run(xiaonuo_patent_search())
```

## ⚙️ 配置选项

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `JINA_API_KEY` | - | Jina AI API密钥（可选） |
| `LOG_LEVEL` | `info` | 日志级别 |
| `TIMEOUT` | `30000` | 请求超时时间（毫秒） |
| `MAX_RETRIES` | `3` | 最大重试次数 |
| `XIAONUO_ENABLED` | `true` | 启用小娜集成 |

### Python配置

```python
config = {
    'timeout': 30,           # 请求超时时间（秒）
    'delay': 2,             # 请求延迟（秒）
    'max_retries': 2,       # 最大重试次数
    'jina_api_key': 'your_key'  # Jina AI API密钥
}
```

## 📊 监控和统计

### 检索统计

```python
# 获取小娜集成统计
stats = await xiaonuo_get_patent_statistics()

xiaonuo_stats = stats['xiaonuo_integration']
print(f"总请求数: {xiaonuo_stats['total_requests']}")
print(f"成功率: {xiaonuo_stats['success_rate']:.2%}")
print(f"平均搜索时间: {xiaonuo_stats['average_search_time']:.2f}s")
```

### 日志监控

服务器日志位置：
- 容器日志: `docker logs google-patents-meta-server`
- 文件日志: `logs/google-patents-meta-server.log`

## 🔧 故障排除

### 常见问题

1. **Python模块导入失败**
   ```bash
   export PYTHONPATH=/path/to/apps/apps/patent-platform/core/core_programs
   ```

2. **Jina AI访问失败**
   - 检查网络连接
   - 验证API密钥配置

3. **小娜调用无响应**
   - 检查MCP服务器状态
   - 验证端口配置（默认3000）

### 性能优化

1. **启用缓存**
   ```python
   config = {
       'cache_enabled': True,
       'cache_ttl': 3600  # 缓存1小时
   }
   ```

2. **并发控制**
   ```python
   config = {
       'max_concurrent': 5,  # 最大并发数
       'request_delay': 1    # 请求间隔
   }
   ```

## 📈 扩展功能

### 添加新的检索方法

```python
# 在GooglePatentsMetaRetriever类中添加新方法
async def _get_content_via_custom_method(self, url: str) -> Optional[str]:
    """自定义内容获取方法"""
    # 实现自定义逻辑
    pass
```

### 自定义小娜接口

```python
# 在xiaonuo_patent_integration.py中添加新接口
async def xiaonuo_custom_patent_analysis(
    patent_id: str,
    analysis_type: str,
    user_id: str = '',
    session_id: str = ''
) -> Dict[str, Any]:
    """自定义专利分析接口"""
    # 实现自定义逻辑
    pass
```

## 📚 API参考

### 检索请求参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| query | string | ✅ | 搜索查询词或专利号 |
| max_results | integer | ❌ | 最大结果数（默认10） |
| filters | object | ❌ | 搜索过滤条件 |
| priority | string | ❌ | 检索优先级（high/medium/low） |

### 响应格式

```json
{
  "success": true,
  "apps/apps/patents": [
    {
      "patent_id": "CN202300000001.0",
      "title": "专利标题",
      "abstract": "专利摘要",
      "inventors": "发明人",
      "assignee": "申请人",
      "content_quality": 0.85,
      "extraction_method": "meta_tags"
    }
  ],
  "total_found": 5,
  "search_time": 3.2,
  "metadata": {
    "user_id": "xiaonuo_001",
    "session_id": "session_123",
    "query": "人工智能"
  }
}
```

## 🔒 安全考虑

1. **API密钥管理**
   - 使用环境变量存储敏感信息
   - 定期轮换API密钥

2. **访问控制**
   - 实施用户认证
   - 限制API调用频率

3. **数据保护**
   - 不记录敏感用户数据
   - 定期清理日志文件

## 📞 技术支持

- **项目负责人**: Athena工作平台
- **技术文档**: `/docs/google-patents-xiaonuo-deployment.md`
- **代码仓库**: Athena工作平台MCP服务器

---

**部署完成后，小娜将能够调用Google专利全文检索功能，为用户提供专业的专利信息服务。**