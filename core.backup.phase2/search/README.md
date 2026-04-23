# Athena智能搜索系统

## 🚀 项目概述

Athena智能搜索系统是一个分散式的智能搜索架构，集成多个搜索引擎工具，通过AI智能选择最佳工具组合，提供统一、高效的搜索体验。

### 🏗️ 核心架构特性

- **分散式设计**: 工具保持独立，避免单点故障
- **智能选择**: 基于查询内容自动选择最佳工具
- **轻量协调**: 非侵入式的配置同步和监控
- **结果融合**: 多源结果的智能合并和排序
- **健康监控**: 实时监控工具状态和性能指标

### 📁 项目结构

```
core/search/
├── standards/              # 标准化接口层
│   └── base_search_tool.py # BaseSearchTool抽象基类
├── registry/               # 工具注册表
│   └── tool_registry.py    # ToolRegistry工具管理器
├── selector/               # 智能选择器
│   └── athena_search_selector.py # AthenaSearchSelector智能选择器
├── coordinator/            # 轻量协调器
│   └── lightweight_coordinator.py # LightweightCoordinator协调器
├── athena/                 # 核心系统
│   └── athena_smart_search.py # AthenaSmartSearch主系统
├── tools/                  # 搜索工具
│   ├── adapted_web_search_manager.py  # Web搜索适配器
│   ├── adapted_patent_retriever.py    # 专利搜索适配器
│   ├── real_web_search_adapter.py    # 真实Web搜索适配器
│   └── real_patent_search_adapter.py # 真实专利搜索适配器
├── config/                 # 配置管理
│   ├── search_api_config.json       # API配置文件
│   └── api_key_manager.py           # API密钥管理器
├── demo_search_system.py   # 演示脚本
├── start_with_real_tools.py # 真实工具启动脚本
└── README.md              # 本文档
```

## 🚀 快速开始

### 1. 快速演示

运行演示脚本，体验智能搜索功能：

```bash
PYTHONPATH=/Users/xujian/Athena工作平台 python3 core/search/demo_search_system.py
```

### 2. 配置真实API密钥

编辑配置文件添加您的API密钥：

```bash
# 编辑API配置文件
vim core/search/config/search_api_config.json

# 或使用配置向导
python3 core/search/start_with_real_tools.py --config-only
```

### 3. 运行真实搜索

```bash
# 演示模式
python3 core/search/start_with_real_tools.py --demo

# 交互模式
python3 core/search/start_with_real_tools.py --interactive

# 单次搜索
python3 core/search/start_with_real_tools.py --query "您的搜索内容"
```

## 🔧 配置指南

### API密钥配置

在 `core/search/config/search_api_config.json` 中配置您的API密钥：

```json
{
  "search_api_keys": {
    "tavily": {
      "api_key": "your_tavily_api_key",
      "enabled": true
    },
    "google_custom_search": {
      "api_key": "your_google_api_key",
      "search_engine_id": "your_search_engine_id",
      "enabled": true
    },
    "bocha": {
      "api_key": "your_bocha_api_key",
      "enabled": true
    }
  }
}
```

### 支持的搜索引擎

#### Web搜索引擎
- **Tavily**: AI驱动的实时搜索引擎
- **Google Custom Search**: Google官方搜索API
- **Bocha**: 中文友好的AI搜索引擎
- **Metaso**: 智能搜索服务

#### 专利搜索引擎
- **Google Patents**: 免费专利数据库
- **USPTO**: 美国专利商标局
- **EPO**: 欧洲专利局
- **CNIPA**: 中国国家知识产权局

## 📖 使用示例

### 基础搜索

```python
import asyncio
from core.search.athena.athena_smart_search import initialize_athena_smart_search

async def basic_search():
    # 初始化系统
    athena = await initialize_athena_smart_search()

    # 执行简单搜索
    result = await athena.search_simple("人工智能最新技术", max_results=10)

    print(f"找到 {len(result.fused_documents)} 个文档")
    for doc in result.fused_documents:
        print(f"- {doc.title}")

asyncio.run(basic_search())
```

### 高级搜索

```python
from core.search.athena.athena_smart_search import SearchRequest

async def advanced_search():
    athena = await initialize_athena_smart_search()

    # 创建搜索请求
    request = SearchRequest(
        query_text="机器学习专利研究",
        max_results=15,
        max_tools=3,
        enable_result_fusion=True,
        strategy="quality_optimized"
    )

    # 执行搜索
    result = await athena.search(request)

    print(f"使用工具: {result.tools_used}")
    print(f"推荐工具: {[rec.tool_name for rec in result.tool_recommendations]}")

asyncio.run(advanced_search())
```

### 集成真实工具

```python
from core.search.tools.real_web_search_adapter import create_real_web_search
from core.search.config.api_key_manager import get_api_key_manager

async def integrate_real_tools():
    # 获取API配置
    api_manager = get_api_key_manager()

    # 创建真实Web搜索工具
    web_config = {
        "tavily_api_key": api_manager.get_api_key("tavily"),
        "google_api_key": api_manager.get_api_key("google_custom_search")
    }

    web_tool = await create_real_web_search(web_config)

    # 注册到系统
    athena = await initialize_athena_smart_search()
    await athena.registry.register_tool(web_tool)

    # 使用真实工具搜索
    result = await athena.search_simple("最新科技新闻")

    # 结果包含真实的API搜索数据
    for doc in result.fused_documents:
        print(f"- {doc.title} ({doc.url})")

asyncio.run(integrate_real_tools())
```

## 🛠️ 开发指南

### 添加新的搜索工具

1. **继承BaseSearchTool**:

```python
from core.search.standards.base_search_tool import BaseSearchTool

class MySearchTool(BaseSearchTool):
    def __init__(self):
        super().__init__("my_search_tool")

    async def initialize(self):
        # 初始化您的搜索工具
        pass

    async def search(self, query):
        # 实现搜索逻辑
        pass

    def get_capabilities(self):
        # 返回工具能力描述
        pass
```

2. **注册到系统**:

```python
# 创建工具实例
my_tool = MySearchTool()
await my_tool.initialize()

# 注册到Athena系统
athena = await initialize_athena_smart_search()
await athena.registry.register_tool(my_tool)
```

### 自定义选择策略

```python
from core.search.selector.athena_search_selector import AthenaSearchSelector

class MySelector(AthenaSearchSelector):
    async def select_tools(self, query):
        # 实现您的选择逻辑
        if "专利" in query:
            return [self.get_tool_by_category("patent_search")]
        return [self.get_tool_by_category("web_search")]
```

### 扩展配置管理

```python
from core.search.config.api_key_manager import get_api_key_manager

# 添加新的服务配置
manager = get_api_key_manager()
manager.update_api_key(
    "my_service",
    "my_api_key",
    description="我的搜索服务",
    enabled=True
)
```

## 📊 性能优化

### 搜索策略

- **speed_optimized**: 速度优先，使用最快的前2个工具
- **quality_optimized**: 质量优先，使用最适合的前3个工具
- **comprehensive**: 全面搜索，使用所有可用工具
- **cost_optimized**: 成本优先，优先使用免费工具

### 并行执行

系统自动并行执行多个搜索工具，显著提升搜索效率：

```
单工具搜索: 2-3秒
双工具并行: 1.5-2秒
三工具并行: 1-1.5秒
```

### 缓存机制

内置智能缓存，减少重复搜索：

- 查询结果缓存: 5分钟有效期
- 工具状态缓存: 30秒有效期
- 配置缓存: 实时更新

## 🏥 监控和健康检查

### 系统健康检查

```python
# 获取系统健康状态
health = await athena.health_check()

# 检查特定工具
tool_health = await athena.registry.health_check()
```

### 性能指标

```python
# 获取系统统计
stats = athena.get_stats()

# 获取工具指标
tool_stats = athena.registry.get_tool_stats("web_search")
```

### 告警系统

```python
from core.search.coordinator.lightweight_coordinator import AlertLevel

# 创建告警
await coordinator.add_alert(
    level=AlertLevel.WARNING,
    title="搜索延迟",
    message="搜索响应时间超过阈值",
    tool_name="web_search"
)
```

## 🔍 故障排除

### 常见问题

1. **导入错误**: 确保设置了正确的PYTHONPATH
2. **API密钥无效**: 检查配置文件中的API密钥是否正确
3. **工具初始化失败**: 查看日志中的详细错误信息
4. **搜索无结果**: 检查网络连接和API服务状态

### 调试模式

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 测试工具

```python
# 测试单个工具
result = await web_tool.search(SearchQuery(text="测试查询"))
print(f"搜索结果: {result.success}")

# 测试选择器
tools = await selector.select_tools(SearchQuery(text="专利搜索"))
print(f"选择的工具: {[tool.name for tool in tools]}")
```

## 📈 路线图

### v1.1 (计划中)
- [ ] 更多搜索引擎支持 (DuckDuckGo, Bing API)
- [ ] 搜索结果缓存优化
- [ ] 用户反馈学习系统
- [ ] 搜索历史分析

### v1.2 (计划中)
- [ ] 分布式部署支持
- [ ] 高可用集群模式
- [ ] 实时监控仪表板
- [ ] API限流和配额管理

### v2.0 (远期规划)
- [ ] 多模态搜索 (图片、语音)
- [ ] 知识图谱集成
- [ ] 个性化搜索推荐
- [ ] 搜索结果可视化

## 📞 支持和贡献

### 报告问题

请在项目Issue中报告bug和功能请求。

### 贡献代码

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 发起Pull Request

### 文档改进

欢迎提交文档改进建议和新增内容。

---

**Athena智能搜索系统** - 让搜索更智能、更高效、更可靠！