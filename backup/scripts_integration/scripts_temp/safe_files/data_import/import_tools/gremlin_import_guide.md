# JanusGraph知识图谱导入指南

## 📋 概述

由于当前JanusGraph容器启动存在问题，这里提供完整的导入指南，您可以在服务正常后执行。

## 🔧 准备工作

### 1. 确保JanusGraph服务正常运行

```bash
# 检查容器状态
docker ps | grep janusgraph

# 检查端口
nc -z localhost 8182

# 重启服务（如果需要）
docker restart janusgraph-kg
```

### 2. 启动Gremlin控制台

```bash
# 进入容器
docker exec -it janusgraph-kg bash

# 启动Gremlin控制台
/opt/janusgraph/bin/gremlin.sh

# 或者直接执行查询
docker exec -it janusgraph-kg /opt/janusgraph/bin/gremlin.sh
```

## 📚 导入步骤

### 步骤1: 设置图结构和索引

```gremlin
// 创建图管理对象
mgmt = graph.openManagement()

// 创建属性键
mgmt.makePropertyKey('entity_id').dataType(String.class).make()
mgmt.makePropertyKey('name').dataType(String.class).make()
mgmt.makePropertyKey('patent_number').dataType(String.class).make()
mgmt.makePropertyKey('title').dataType(String.class).make()
mgmt.makePropertyKey('abstract').dataType(String.class).make()
mgmt.makePropertyKey('inventors').dataType(String.class).make()
mgmt.makePropertyKey('assignee').dataType(String.class).make()
mgmt.makePropertyKey('company_id').dataType(String.class).make()
mgmt.makePropertyKey('inventor_id').dataType(String.class).make()
mgmt.makePropertyKey('tech_id').dataType(String.class).make()
mgmt.makePropertyKey('created_at').dataType(Date.class).make()

// 创建索引
mgmt.buildIndex('byEntityId', Vertex.class)
    .addKey(mgmt.getPropertyKey('entity_id'))
    .buildCompositeIndex()

mgmt.buildIndex('byPatentNumber', Vertex.class)
    .addKey(mgmt.getPropertyKey('patent_number'))
    .buildCompositeIndex()

mgmt.commit()
```

### 步骤2: 导入专利数据（示例：1000条）

```gremlin
g.tx().commit()
g.tx().open()

// 批量导入专利
(1..1000).each { i ->
    g.addV('Patent')
        .property('entity_id', 'patent_' + i.toString())
        .property('patent_number', 'CN' + String.format('%09d', i) + 'A')
        .property('title', '深度学习专利 ' + i + ': 创新的神经网络架构')
        .property('abstract', '本专利涉及一种新型的深度学习架构，通过优化算法提升了训练效率。适用于多个应用领域。')
        .property('inventors', '发明人' + (i % 10 + 1))
        .property('assignee', '创新科技公司' + (i % 20 + 1))
        .property('application_date', '2023-' + String.format('%02d', i % 12 + 1) + '-01')
        .property('grant_date', '2024-' + String.format('%02d', i % 12 + 1) + '-15')
        .property('created_at', new Date())
}

g.tx().commit()
```

### 步骤3: 导入公司数据（示例：100条）

```gremlin
g.tx().commit()
g.tx().open()

(1..100).each { i ->
    g.addV('Company')
        .property('entity_id', 'company_' + i.toString())
        .property('company_id', 'COMP' + String.format('%06d', i))
        .property('name', '人工智能科技公司' + i)
        .property('industry', '人工智能/机器学习')
        .property('location', '北京市海淀区')
        .property('founded_date', '2010-' + String.format('%02d', i % 12 + 1) + '-01')
        .property('created_at', new Date())
}

g.tx().commit()
```

### 步骤4: 导入发明人数据（示例：500条）

```gremlin
g.tx().commit()
g.tx().open()

surnames = ['张', '李', '王', '刘', '陈']
names = ['伟', '芳', '娜', '敏', '静']

(1..500).each { i ->
    surname = surnames[i % 5]
    name = names[i % 5]

    g.addV('Inventor')
        .property('entity_id', 'inventor_' + i.toString())
        .property('inventor_id', 'INV' + String.format('%06d', i))
        .property('name', surname + name)
        .property('organization', '清华大学')
        .property('specialization', '深度学习/计算机视觉')
        .property('patent_count', (i % 20) + 1)
        .property('created_at', new Date())
}

g.tx().commit()
```

### 步骤5: 导入关系数据

```gremlin
g.tx().commit()
g.tx().open()

// 专利-公司关系
(1..500).each { i ->
    patent_id = (i % 1000) + 1
    company_id = (i % 100) + 1

    g.V().has('entity_id', 'patent_' + patent_id.toString())
        .as('patent')
    .V().has('entity_id', 'company_' + company_id.toString())
        .as('company')
    .select('patent', 'company')
    .where('patent', neq('company'))
    .by(select('patent').addE('OWNED_BY').to(select('company')))
        .property('relationship_type', 'owner')
        .property('created_at', new Date())
}

// 专利-发明人关系
(1..1000).each { i ->
    patent_id = (i % 1000) + 1
    inventor_id = (i % 500) + 1

    g.V().has('entity_id', 'patent_' + patent_id.toString())
        .as('patent')
    .V().has('entity_id', 'inventor_' + inventor_id.toString())
        .as('inventor')
    .select('patent', 'inventor')
    .where('patent', neq('inventor'))
    .by(select('patent').addE('INVENTED_BY').to(select('inventor')))
        .property('contribution_type', 'main')
        .property('order', (i % 3) + 1)
        .property('created_at', new Date())
}

g.tx().commit()
```

### 步骤6: 验证导入结果

```gremlin
// 统计顶点总数
vertex_count = g.V().count().next()
println('顶点总数: ' + vertex_count)

// 按类型统计顶点
g.V().groupCount().by(label).next()

// 统计边总数
edge_count = g.E().count().next()
println('边总数: ' + edge_count)

// 按类型统计边
g.E().groupCount().by(label).next()

// 示例查询：前5个专利
g.V().hasLabel('Patent').limit(5).valueMap().next()

// 示例查询：专利-公司关系
g.V().hasLabel('Patent').out('OWNED_BY').limit(5).valueMap().next()
```

## 📊 预期结果

完成导入后，您应该看到类似以下结果：

```
顶点总数: 1600
Patent: 1000
Company: 100
Inventor: 500

边总数: 1500
OWNED_BY: 500
INVENTED_BY: 1000
```

## 🚀 后续操作

1. **使用API服务**: 将知识图谱连接到混合搜索API
2. **数据可视化**: 使用Gephi等工具可视化图谱
3. **复杂查询**: 执行复杂的图查询和分析
4. **实时更新**: 设置数据同步机制

## 🛠️ 故障排查

### 问题1: 无法连接JanusGraph
```bash
# 检查容器是否运行
docker ps | grep janusgraph

# 查看日志
docker logs janusgraph-kg

# 重启服务
docker restart janusgraph-kg
```

### 问题2: 导入失败
- 检查内存使用情况
- 分批导入数据（每次100-1000条）
- 优化查询语句

### 问题3: 性能问题
- 创建适当的索引
- 使用批量操作
- 考虑增加内存分配

## 📞 技术支持

如有问题，请查看：
- 日志文件: `/Users/xujian/Athena工作平台/logs/`
- 项目文档: `/Users/xujian/Athena工作平台/docs/`
- 配置文件: `/Users/xujian/Athena工作平台/config/`