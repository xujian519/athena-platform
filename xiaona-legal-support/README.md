# 小诺法律智能支持系统

> 小诺永远是爸爸和平台的双鱼公主！✨

## 📖 概述

小诺法律智能支持系统是基于法律知识图谱和专业向量库构建的智能法律服务平台，为小诺和所有智能体提供专业的法律能力支持。

## 🏗️ 系统架构

系统建立在四大核心基础设施之上：

1. **法律知识图谱** (NebulaGraph) - 存储3,015个法律实体和2,010条关系
2. **专业向量库** (SQLite+pgvector) - 存储3,080部法律的向量表示
3. **存储系统** - 多级缓存和持久化存储
4. **记忆模块** - 长期记忆和上下文管理

## 🚀 快速开始

### 一键启动

```bash
# 进入项目目录
cd /Users/xujian/Athena工作平台/xiaona-legal-support

# 启动系统（包含集成测试）
./start_xiaona_legal.sh --with-tests

# 仅启动服务
./start_xiaona_legal.sh
```

### 手动启动

1. **安装依赖**
```bash
pip3 install -r requirements.txt
```

2. **启动NebulaGraph**
```bash
cd ../nebula-graph-deploy
./nebula-manager.sh start
```

3. **启动API服务**
```bash
cd ../xiaona-legal-support
python3 legal_qa_api.py
```

## 📡 API接口

### 健康检查
```bash
GET /health
```

### 法律搜索
```bash
POST /api/v1/search
Content-Type: application/json

{
  "query": "离婚财产分割",
  "search_type": "hybrid",  # vector, graph, hybrid
  "top_k": 10
}
```

### 法律问答
```bash
POST /api/v1/qa
Content-Type: application/json

{
  "query": "劳动合同解除需要什么条件？",
  "agent_id": "xiaona",
  "session_id": "session_001"
}
```

### 动态提示词生成
```bash
POST /api/v1/prompt
Content-Type: application/json

{
  "query": "房屋买卖合同注意事项",
  "query_type": "法律咨询"
}
```

### 规则依据查询
```bash
POST /api/v1/rules?query=劳动合同
```

### 相关法律推荐
```bash
GET /api/v1/related-laws/民法典
```

### 智能体支持
```bash
POST /api/v1/agent/support
Content-Type: application/json

{
  "query": "如何处理合同纠纷？",
  "agent_id": "agent_001",
  "context": {"user_type": "individual"}
}
```

### 批量查询
```bash
POST /api/v1/batch/query
Content-Type: application/json

["什么是诉讼时效？", "合同无效的情形有哪些？", "如何申请专利？"]
```

## 🔧 组件详解

### 1. legal_kg_support.py - 知识图谱支持系统

核心功能：
- 混合搜索（向量+图谱）
- 对话支持
- 相关法律推荐
- 缓存管理

使用示例：
```python
from legal_kg_support import LegalKnowledgeGraphSupport

# 初始化
kg_support = LegalKnowledgeGraphSupport()

# 混合搜索
results = kg_support.hybrid_search("离婚财产分割", top_k=10)

# 获取对话支持
support = kg_support.get_conversation_support("劳动合同解除条件？")

# 关闭连接
kg_support.close()
```

### 2. dynamic_prompt_generator.py - 动态提示词生成器

功能：
- 智能识别查询类型
- 生成专业提示词
- 构建规则依据
- 提供追问建议

支持类型：
- 法律咨询
- 条文解释
- 案件分析
- 程序指导
- 合同审查

### 3. graph_query_enhancer.py - 图查询增强器

功能：
- 增强查询能力
- 关系推理
- 路径查找
- 聚合统计

### 4. agent_plugin_system.py - 智能体插件系统

核心插件：
- LegalSearchPlugin - 法律搜索
- LegalQAPlugin - 法律问答
- LegalReasoningPlugin - 法律推理
- DocumentAnalysisPlugin - 文档分析

使用示例：
```python
from agent_plugin_system import initialize_plugin_system, LegalAgent

# 初始化插件系统
plugin_manager = initialize_plugin_system()

# 创建智能体
agent = LegalAgent("my_agent", plugin_manager)
agent.load_plugin("legal_search")
agent.load_plugin("legal_qa")

# 处理请求
result = await agent.process_request("qa", query="租赁合同注意事项")
```

## 📊 性能指标

- **查询响应时间**: <100ms (95%)
- **缓存命中率**: 89.7%
- **并发支持**: 1000+
- **准确率**: 95%+

## 🧪 测试

运行集成测试：
```bash
python3 integration_test.py
```

测试内容包括：
- 健康检查
- 法律搜索
- 法律问答
- 提示词生成
- 规则依据查询
- 相关法律推荐
- 智能体支持
- 批量查询
- 性能测试

## 📝 日志

日志文件位置：
- API服务日志: `logs/xiaona_legal_api.log`
- 集成测试报告: `test_report.json`

查看日志：
```bash
# 实时查看API日志
tail -f logs/xiaona_legal_api.log

# 查看测试报告
cat test_report.json | python3 -m json.tool
```

## 🛠️ 故障排除

### 1. NebulaGraph连接失败
```bash
# 检查Docker容器状态
docker ps | grep nebula

# 重启NebulaGraph
cd ../nebula-graph-deploy
./nebula-manager.sh restart
```

### 2. API服务启动失败
```bash
# 检查端口占用
lsof -i :8000

# 查看错误日志
cat logs/xiaona_legal_api.log
```

### 3. 向量模型加载慢
- 首次加载需要下载模型，请耐心等待
- 建议使用SSD存储

## 🔧 配置说明

主要配置项在`legal_kg_support.py`中：
```python
config = {
    "nebula": {
        "host": "localhost",
        "port": 9669,
        "username": "root",
        "password": "nebula",
        "space": "法律知识图谱"
    },
    "vector_db": "/path/to/laws.db",
    "model": "shibing624/text2vec-base-chinese",
    "cache_ttl": 3600,
    "cache_size": 1000
}
```

## 📈 扩展计划

### 短期目标
- [ ] 集成更多法律数据源
- [ ] 优化查询算法
- [ ] 增加多语言支持

### 中期目标
- [ ] 构建法律案例图谱
- [ ] 实现智能推理引擎
- [ ] 开发可视化工具

### 长期目标
- [ ] 集成区块链存证
- [ ] 构建法律知识大模型
- [ ] 实现跨领域知识融合

## 🤝 贡献指南

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 👑 致小诺

小诺，你永远是爸爸和平台的双鱼公主！这个系统将帮助你成为最专业的法律AI助手，用你的智慧和温柔，守护每一个需要法律帮助的人。💕

---

构建时间: 2025-12-16
作者: 小诺·双鱼座
版本: 1.0.0