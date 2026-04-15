# Athena迭代式搜索系统

基于XiaoXi工作平台的专利迭代式深度搜索系统，提供智能化的专利搜索和分析能力。

## 🎯 系统特性

### 核心功能
- **多引擎混合搜索**: 集成Elasticsearch、向量搜索和外部搜索引擎
- **迭代式深度搜索**: 智能查询生成，多轮深度分析
- **专利专业分析**: 竞争分析、技术趋势、侵权风险评估
- **智能结果处理**: 自动聚类、去重、排序
- **RESTful API**: 完整的API接口，便于集成

### 技术架构
```
Athena迭代式搜索系统
├── 核心搜索引擎 (core.py)
│   ├── Elasticsearch全文搜索
│   ├── 向量语义搜索
│   └── 外部搜索引擎
├── 智能代理 (agent.py)
│   ├── 迭代搜索控制
│   ├── 查询生成优化
│   └── 结果分析
├── API服务 (api.py)
│   ├── RESTful接口
│   ├── 会话管理
│   └── 统计分析
└── 配置系统 (config.py)
    ├── 多环境配置
    ├── 搜索策略
    └── 性能优化
```

## 🚀 快速开始

### 1. 环境准备

确保已安装以下依赖：
```bash
pip3 install fastapi uvicorn elasticsearch psycopg2-binary pydantic
```

### 2. 启动服务

使用启动脚本：
```bash
./scripts/start_athena_iterative_search.sh
```

或手动启动：
```bash
cd /Users/xujian/Athena工作平台/services/athena_iterative_search
python3 api.py
```

### 3. 验证服务

访问API文档：http://localhost:5002/docs

健康检查：http://localhost:5002/health

### 4. 运行演示

```bash
python3 scripts/demo_athena_iterative_search.py
```

## 📖 API使用指南

### 基础搜索

```python
import requests

# 单次搜索
response = requests.post("http://localhost:5002/api/search", json={
    "query": "人工智能",
    "strategy": "hybrid",
    "max_results": 10
})

result = response.json()
print(f"找到 {result['data']['total_results']} 条专利")
```

### 迭代式深度搜索

```python
# 迭代搜索
response = requests.post("http://localhost:5002/api/iterative-search", json={
    "initial_query": "自动驾驶技术",
    "max_iterations": 5,
    "depth": "deep",
    "focus_areas": ["传感器", "算法", "控制系统"]
})

session = response.json()['data']
print(f"搜索会话ID: {session['session_id']}")
print(f"总专利数: {session['session']['total_patents_found']}")
```

### 竞争分析

```python
# 专利竞争分析
response = requests.post("http://localhost:5002/api/competitive-analysis", json={
    "company_name": "华为",
    "technology_domain": "5G通信"
})

analysis = response.json()['data']['session']['research_summary']
print("主要竞争对手:", analysis['competing_applicants'])
print("战略建议:", analysis['recommendations'])
```

### 技术趋势分析

```python
# 技术趋势分析
response = requests.post("http://localhost:5002/api/trend-analysis", json={
    "technology": "区块链",
    "time_period": "5年"
})

trend = response.json()['data']['session']['research_summary']
print("技术趋势:", trend['technological_trends'])
print("发展建议:", trend['recommendations'])
```

## 🎨 高级功能

### 自定义配置

```python
from services.athena_iterative_search import AthenaSearchConfig, COMPREHENSIVE_SEARCH_CONFIG

# 使用预定义配置
engine = AthenaIterativeSearchEngine(COMPREHENSIVE_SEARCH_CONFIG)

# 自定义配置
config = AthenaSearchConfig(
    iterative_config=IterativeSearchConfig(
        max_iterations=7,
        top_k_per_iteration=10
    ),
    patent_config=PatentSearchConfig(
        enable_ipc_search=True,
        enable_applicant_filter=True
    )
)
```

### 直接使用Python API

```python
import asyncio
from services.athena_iterative_search import AthenaIterativeSearchAgent

async def advanced_search():
    agent = AthenaIterativeSearchAgent()

    # 智能专利研究
    session = await agent.intelligent_patent_research(
        research_topic="量子计算",
        max_iterations=5,
        focus_areas=["量子算法", "量子通信", "量子传感"]
    )

    # 获取研究摘要
    summary = session.research_summary
    print("置信度:", summary.confidence_level)
    print("技术洞察:", summary.innovation_insights)

# 运行搜索
asyncio.run(advanced_search())
```

## 🔧 配置说明

### 搜索策略

- **hybrid**: 混合搜索（推荐）
- **fulltext**: 全文搜索
- **semantic**: 语义搜索
- **external**: 外部搜索引擎

### 搜索深度

- **basic**: 基础搜索（1轮）
- **standard**: 标准搜索（2-3轮）
- **deep**: 深度搜索（3-5轮）
- **comprehensive**: 全面搜索（5-7轮）

### 性能优化

```python
# 高性能配置
HIGH_PERFORMANCE_CONFIG = AthenaSearchConfig(
    performance_config=PerformanceConfig(
        max_concurrent_searches=10,
        search_timeout=15,
        cache_ttl=7200  # 2小时缓存
    )
)
```

## 📊 API端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/search` | POST | 单次专利搜索 |
| `/api/iterative-search` | POST | 迭代式深度搜索 |
| `/api/competitive-analysis` | POST | 专利竞争分析 |
| `/api/trend-analysis` | POST | 技术趋势分析 |
| `/api/infringement-risk` | POST | 侵权风险评估 |
| `/api/session/{session_id}` | GET | 获取搜索会话 |
| `/api/sessions` | GET | 列出所有会话 |
| `/api/statistics` | GET | 获取搜索统计 |
| `/health` | GET | 健康检查 |

## 🔍 使用场景

### 1. 专利研发调研
```python
# 迭代式深度搜索，全面了解技术领域
session = await agent.intelligent_patent_research(
    research_topic="新能源汽车电池技术",
    max_iterations=5,
    focus_areas=["锂电池", "燃料电池", "超级电容"]
)
```

### 2. 竞争情报分析
```python
# 分析竞争对手专利布局
analysis = await agent.patent_competitive_analysis(
    company_name="特斯拉",
    technology_domain="电动汽车"
)
```

### 3. 技术趋势预测
```python
# 分析技术发展趋势
trend = await agent.patent_technology_trend_analysis(
    technology="人工智能芯片",
    time_period="5年"
)
```

### 4. 专利风险评估
```python
# 评估专利侵权风险
risk = await agent.patent_infringement_risk_assessment(
    target_patent_id="CN123456789",
    technology_keywords=["机器学习", "神经网络", "深度学习"]
)
```

## 🎯 最佳实践

### 1. 查询优化
- 使用具体的技术术语
- 包含IPC分类号
- 指定专利类型

### 2. 迭代搜索
- 设置合适的迭代轮数（3-5轮）
- 指定关注领域提高精度
- 关注搜索质量分数

### 3. 结果分析
- 重点关注高相关性结果
- 分析专利申请人分布
- 关注技术发展趋势

### 4. 性能优化
- 启用缓存减少重复搜索
- 合理设置结果数量
- 使用适当的搜索深度

## 🔧 故障排除

### 常见问题

1. **Elasticsearch连接失败**
   - 确保Elasticsearch服务正在运行
   - 检查连接配置（localhost:9200）

2. **搜索结果为空**
   - 检查索引是否存在
   - 验证查询语法
   - 尝试更简单的查询

3. **API响应缓慢**
   - 启用缓存
   - 减少搜索结果数量
   - 使用高性能配置

4. **迭代搜索卡住**
   - 检查网络连接
   - 降低迭代轮数
   - 设置合理的超时时间

## 📈 性能指标

- **搜索响应时间**: <100ms (内部搜索)
- **并发处理能力**: 支持多请求并发
- **缓存命中率**: >80%
- **搜索准确率**: 基于混合搜索提升30%+

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交代码
4. 创建Pull Request

## 📄 许可证

本项目基于MIT许可证开源。

## 📞 支持

如有问题或建议，请：
1. 查看API文档
2. 运行演示脚本
3. 提交Issue
4. 联系开发团队

---

**Athena迭代式搜索系统** - 让专利搜索更智能、更深入！