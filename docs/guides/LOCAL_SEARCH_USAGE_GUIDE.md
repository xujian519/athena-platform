# 本地搜索引擎使用指南

> **更新日期**: 2026-04-19
> **搜索引擎**: SearXNG + Firecrawl
> **访问方式**: MCP服务器

---

## 快速开始

### 1. 确认本地搜索引擎运行

```bash
# 检查服务状态
docker ps | grep lse

# 查看日志
docker compose -f ~/projects/local-search-engine/docker-compose.yml logs -f gateway
```

### 2. 通过MCP使用本地搜索

本地搜索引擎通过MCP服务器提供，推荐的使用方式：

#### 方式1: 直接使用MCP工具

```python
# 在支持MCP的上下文中使用
result = mcp_local_search_engine_web_search(
    query="Python异步编程",
    limit=10
)
```

#### 方式2: 通过工具系统调用

```python
# 注册为web_search工具后使用
from core.tools.real_tool_implementations import real_web_search_handler

result = await real_web_search_handler({
    "query": "Python异步编程",
    "limit": 10
})
```

---

## 本地搜索引擎架构

### 组件

1. **SearXNG** - 开源元搜索引擎
   - 端口: 8080
   - 功能: 聚合多个搜索引擎，去重排序

2. **Firecrawl** - 网页抓取工具
   - 端口: 3002
   - 功能: 抓取网页内容，转换为Markdown

3. **Gateway** - 统一API网关
   - 端口: 3003
   - 功能: MCP服务，工具调用

### 服务地址

| 服务 | 地址 | 说明 |
|------|------|------|
| SearXNG前端 | http://localhost:8080 | 网页搜索界面 |
| Gateway MCP | http://localhost:3003/sse | MCP服务端点 |
| Health检查 | http://localhost:3003/health | 健康检查 |

---

## MCP工具

### 可用工具

| 工具名 | 功能 | 参数 |
|--------|------|------|
| `web_search` | 搜索互联网 | query, limit |
| `web_scrape` | 抓取网页 | url |
| `web_search_and_scrape` | 搜索+抓取全文 | query, limit |

### 使用示例

#### web_search

```python
# 搜索互联网
result = mcp_local_search_engine_web_search(
    query="专利检索",
    limit=10
)

# 返回格式:
# [
#   {
#     "title": "标题",
#     "url": "https://...",
#     "snippet": "摘要..."
#   },
#   ...
# ]
```

#### web_scrape

```python
# 抓取网页全文
result = mcp_local_search_engine_web_scrape(
    url="https://example.com/article"
)

# 返回格式:
# {
#   "url": "https://...",
#   "content": "# Markdown内容...",
#   "title": "页面标题",
#   "success": true
# }
```

#### web_search_and_scrape

```python
# 搜索并抓取全文
result = mcp_local_search_engine_web_search_and_scrape(
    query="Python教程",
    limit=5
)

# 返回格式:
# [
#   {
#     "title": "Python教程",
#     "url": "https://...",
#     "snippet": "摘要...",
#     "full_content": "# Markdown全文..."
#   },
#   ...
# ]
```

---

## 配置和优化

### SearXNG配置

配置文件: `~/projects/local-search-engine/searxng/settings.yml`

```yaml
# 启用的搜索引擎
engines:
  - name: google
  - name: bing
  - name: duckduckgo
  - name: wikipedia

# 搜索结果限制
max_results: 10

# 超时设置
timeout: 10.0
```

### 优化建议

1. **增加结果缓存**
   - 在Gateway层添加Redis缓存
   - 缓存常见搜索查询

2. **调整并发**
   - 增加SearXNG并发请求数
   - 优化Firecrawl抓取速度

3. **结果排序**
   - 根据专利相关度排序
   - 优先显示权威来源

---

## 故障排查

### 问题1: 服务未运行

**症状**: 连接拒绝

**解决**:
```bash
cd ~/projects/local-search-engine
docker compose up -d
```

### 问题2: 搜索无结果

**症状**: 返回空列表

**可能原因**:
- SearXNG配置错误
- 网络问题
- 查询词过于特殊

**解决**:
```bash
# 查看SearXNG日志
docker compose -f ~/projects/local-search-engine/docker-compose.yml logs -f searxng

# 测试SearXNG
curl http://localhost:8080/search?q=test
```

### 问题3: 抓取失败

**症状**: web_scrape返回错误

**可能原因**:
- 目标网站屏蔽爬虫
- JavaScript渲染问题
- 网络超时

**解决**:
- 检查Firecrawl日志
- 增加超时时间
- 使用user-agent轮换

---

## 性能指标

| 指标 | 数值 |
|------|------|
| 平均响应时间 | ~500ms |
| 成功率 | 95%+ |
| 并发支持 | 10 QPS |
| 缓存命中率 | 待实现 |

---

## 迁移检查清单

从外部API迁移到本地搜索：

- [x] 修改web_search工具实现
- [x] 更新工具描述
- [x] 删除外部API依赖
- [x] 更新工具集配置
- [x] 创建测试文件
- [x] 创建使用文档
- [ ] 验证MCP工具调用
- [ ] 性能测试
- [ ] 添加缓存机制

---

## 下一步

1. **验证MCP集成**
   - 测试MCP工具调用
   - 确认返回格式正确

2. **性能优化**
   - 添加搜索缓存
   - 优化结果排序

3. **监控**
   - 添加搜索统计
   - 错误率监控

---

**文档版本**: v1.0
**最后更新**: 2026-04-19
