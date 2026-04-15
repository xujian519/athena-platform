
# SQLite知识图谱导入指南

## 导入脚本位置
/Users/xujian/Athena工作平台/data/sqlite_to_janusgraph_import.gremlin

## 导入步骤

### 1. 连接Gremlin控制台
```bash
gremlin.sh
:remote connect tinkerpop.server conf/remote.yaml
:remote console
```

### 2. 执行导入
```bash
:load /Users/xujian/Athena工作平台/data/sqlite_to_janusgraph_import.gremlin
```

### 3. 验证导入结果
```gremlin
// 查看总数
g.V().count()
g.E().count()

// 查看节点类型
g.V().label().dedup()

// 查看关系类型
g.E().label().dedup()
```

## 导入统计
- 节点数: 302
- 边数: 0
- 生成时间: 2025-12-14T20:50:30.946715

## 注意事项
1. 导入前确保JanusGraph服务正常运行
2. 大量数据导入可能需要较长时间
3. 建议先在小数据集上测试
