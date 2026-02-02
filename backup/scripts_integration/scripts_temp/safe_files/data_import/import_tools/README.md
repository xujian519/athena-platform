# Athena知识图谱导入工具使用指南

## 📋 概述

本目录包含Athena平台知识图谱数据导入所需的全部工具和脚本。

## 🚀 快速开始

### 1. 准备工作

确保以下服务已启动：
- JanusGraph (端口8182)
- Qdrant (端口6333) - 可选，用于向量搜索

```bash
# 启动JanusGraph
cd /Users/xujian/Athena工作平台/services/knowledge-graph-service
docker-compose up -d janusgraph
```

### 2. 执行导入

```bash
# 运行批量导入脚本
./batch_import_knowledge_graph.sh
```

### 3. 验证导入

```bash
# 验证导入结果
./validate_knowledge_graph.sh
```

## 📁 文件说明

- `batch_import_knowledge_graph.sh` - 批量导入主脚本
- `validate_knowledge_graph.sh` - 数据验证脚本
- `monitor_knowledge_graph.sh` - 实时监控脚本
- `import_dashboard.html` - Web监控仪表板（如果存在）

## 🔍 监控和验证

### 实时监控
```bash
# 启动实时监控（每5秒刷新）
./monitor_knowledge_graph.sh
```

### 数据验证
```bash
# 查看顶点总数
echo "g.V().count()" | gremlin.sh -

# 查看边总数
echo "g.E().count()" | gremlin.sh -

# 查看类型分布
echo "g.V().groupCount().by(label)" | gremlin.sh -
```

## 📊 API测试

导入完成后，可以通过API进行测试：

```bash
# 健康检查
curl http://localhost:8080/health

# 混合搜索测试
curl -X POST http://localhost:8080/api/v1/search/hybrid \
  -H "Content-Type: application/json" \
  -d '{
    "query": "深度学习专利",
    "limit": 10
  }'

# 查看API文档
open http://localhost:8080/docs
```

## 🛠️ 故障排查

### 问题1: JanusGraph连接失败
```bash
# 检查端口
nc -z localhost 8182

# 查看日志
docker logs janusgraph
```

### 问题2: 导入速度慢
- 调整batch_size参数
- 检查内存使用
- 考虑分批导入

### 问题3: 内存不足
```bash
# 增加JVM内存
export JAVA_OPTS="-Xmx8g -Xms4g"
```

## 📈 性能优化建议

1. **批量大小**: 将batch_size设置为1000-10000
2. **事务控制**: 每1000条提交一次事务
3. **索引优化**: 导入前创建必要的索引
4. **并行导入**: 考虑使用多线程并行导入

## 📞 技术支持

- 日志位置: `/Users/xujian/Athena工作平台/logs/knowledge_graph_import.log`
- 配置文件: `/Users/xujian/Athena工作平台/config/`
- API文档: http://localhost:8080/docs
