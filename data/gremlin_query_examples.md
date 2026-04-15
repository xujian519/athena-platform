# JanusGraph Gremlin查询示例

生成时间: 2025-12-14T20:51:33.074740

## 基础查询

### 查看所有节点数量
**描述**: 统计图中所有节点的总数
**Gremlin查询**: ```gremlin
g.V().count()
``

### 查看所有边的数量
**描述**: 统计图中所有关系的总数
**Gremlin查询**: ```gremlin
g.E().count()
``

### 查看所有节点类型
**描述**: 获取图中所有节点的类型
**Gremlin查询**: ```gremlin
g.V().label().dedup()
``

### 查看所有关系类型
**描述**: 获取图中所有关系的类型
**Gremlin查询**: ```gremlin
g.E().label().dedup()
``

## 专利查询

### 查找所有专利
**描述**: 获取所有专利节点
**Gremlin查询**: ```gremlin
g.V().hasLabel('Patent')
``

### 查找特定专利
**描述**: 根据ID查找特定专利
**Gremlin查询**: ```gremlin
g.V().has('id', 'CN202410001234')
``

### 查找AI相关专利
**描述**: 查找人工智能领域的专利
**Gremlin查询**: ```gremlin
g.V().hasLabel('Patent').has('category', '人工智能')
``

### 按发明人查找专利
**描述**: 查找特定发明人的专利
**Gremlin查询**: ```gremlin
g.V().hasLabel('Patent').has('inventor', '张三')
``

## 关系查询

### 查找专利的所有关系
**描述**: 查看特定专利的所有关系
**Gremlin查询**: ```gremlin
g.V('CN202410001234').bothE()
``

### 查找专利所属公司
**描述**: 查找专利的申请人公司
**Gremlin查询**: ```gremlin
g.V('CN202410001234').out('ASSIGNED_TO')
``

### 查找公司的专利
**描述**: 查找特定公司的所有专利
**Gremlin查询**: ```gremlin
g.V('athena_tech').in('ASSIGNED_TO')
``

### 查找发明人的专利
**描述**: 查找特定发明人的专利
**Gremlin查询**: ```gremlin
g.V('zhang_san').out('INVENTED_BY')
``

## 复杂查询

### 专利-发明人-公司路径
**描述**: 查找专利、发明人和申请公司的完整关系
**Gremlin查询**: ```gremlin
g.V().hasLabel('Patent').as('p').out('INVENTED_BY').as('i').in('ASSIGNED_TO').as('c').select('p', 'i', 'c')
``

### AI专利的发明人信息
**描述**: 查找AI专利及其发明人信息
**Gremlin查询**: ```gremlin
g.V().hasLabel('Patent').has('category', '人工智能').as('patent').out('INVENTED_BY').as('inventor').select('patent', 'inventor')
``

### 多步关系查找
**描述**: 查找使用前沿技术且申请人在北京的专利
**Gremlin查询**: ```gremlin
g.V().hasLabel('Patent').where(__.out('USES_TECHNOLOGY').has('category', '前沿技术')).as('ai_patent').out('ASSIGNED_TO').where(__.has('location', '北京')).select('ai_patent')
``

### 聚合统计
**描述**: 统计每个公司拥有的专利数量
**Gremlin查询**: ```gremlin
g.V().hasLabel('Company').as('company').in('ASSIGNED_TO').count().as('patent_count').select('company', 'patent_count')
``

## 性能查询

### 分页查询专利
**描述**: 分页查询前10个专利
**Gremlin查询**: ```gremlin
g.V().hasLabel('Patent').range(0, 10)
``

### 按日期排序
**描述**: 按申请日期排序专利
**Gremlin查询**: ```gremlin
g.V().hasLabel('Patent').order().by('application_date')
``

### 限制返回字段
**描述**: 只返回专利的标题、发明人和申请人
**Gremlin查询**: ```gremlin
g.V().hasLabel('Patent').values('title', 'inventor', 'assignee')
``

