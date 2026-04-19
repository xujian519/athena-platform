# MCP服务器集合 (MCP Servers Collection)

## OVERVIEW
各种MCP(Model Context Protocol)服务器实现，为AI系统提供外部服务和工具集成。

## STRUCTURE
```
mcp-servers/
├── academic-search-mcp-server/    # 学术搜索服务
├── chrome-mcp-server/            # 浏览器自动化服务
├── gaode-mcp-server/             # 高德地图API服务
├── github-mcp-server/            # GitHub API集成服务
├── google-patents-meta-server/  # Google专利元数据服务
├── imsg-mcp-server/              # iMessage集成服务
├── jina-ai-mcp-server/           # Jina AI搜索和嵌入服务
├── patent_downloader/            # 专利PDF下载服务
├── patent-search-mcp-server/     # 专利搜索服务
└── xiaonuo-calendar-assistant/   # 小诺日历助手服务
```

## WHERE TO LOOK

| 任务 | 位置 | 备注 |
|------|--------|-------|
| Jina AI集成 | jina-ai-mcp-server/ | 提供搜索、嵌入和重排序功能 |
| 专利下载 | patent_downloader/ | 从Google Patents下载PDF文件 |
| 浏览器自动化 | chrome-mcp-server/ | 网页截图和自动化操作 |
| 学术搜索 | academic-search-mcp-server/ | 学术论文和研究搜索 |

## CONVENTIONS

### 项目特定规则
- **多语言支持**: Python (FastMCP) 和 Node.js (@modelcontextprotocol/sdk)
- **环境配置**: 统一使用.env文件管理API密钥和配置
- **标准化输出**: 使用Pydantic模型定义结构化响应格式
- **错误处理**: 统一异常处理和日志记录机制
- **配置持久化**: 关键配置保存在~/.patent_downloader/等用户目录

### 服务接口规范
- **工具定义**: 使用@server.tool装饰器定义MCP工具
- **参数验证**: Pydantic Field进行参数描述和验证
- **响应格式**: 统一success/message/payload结构
- **命名规范**: snake_case用于工具和函数命名

## ANTI-PATTERNS

### 禁止的模式
- **硬编码API密钥**: 必须使用环境变量或配置文件
- **忽略速率限制**: 所有搜索服务必须实现速率限制
- **异常静默失败**: 必须记录错误并提供有意义的错误消息
- **阻塞主线程**: 长时间操作应使用异步或后台处理
- **重复造轮子**: 优先使用现有MCP SDK和标准库

### DEPRECATED标记
- **单例模式**: 避免全局单例，使用依赖注入
- **同步阻塞**: 网络请求必须使用异步模式
- **硬编码路径**: 使用Path对象和相对路径

---
*MCP服务器集合 - 为Athena工作平台提供外部服务集成*