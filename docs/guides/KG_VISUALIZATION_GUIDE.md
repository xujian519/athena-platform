# Athena知识图谱可视化指南

**更新日期**: 2026-04-21
**数据**: 93万节点 + 6万关系

---

## 🎨 可视化方案

### 方案1: Neo4j Browser（推荐）⭐

**优点**:
- Neo4j自带，无需安装
- 支持交互式探索
- 实时Cypher查询
- 力导向布局

**使用方法**:

1. 打开Neo4j Browser
```bash
open http://localhost:7474
```

2. 登录
   - 用户名: `neo4j`
   - 密码: `athena_neo4j_2024`

3. 执行查询示例

```cypher
// 查看50个实体节点及其关系
MATCH (n:Entity {type: "PATENT_NUMBER"})-[r:RELATION]->(m)
RETURN n,r,m
LIMIT 50

// 查看50个OpenClaw节点及其关系
MATCH (n:OpenClawNode)-[r:RELATED_TO|CITES]->(m:OpenClawNode)
RETURN n,r,m
LIMIT 50

// 查看节点统计
MATCH (n)
RETURN labels(n) as label, count(*) as count
ORDER BY count DESC

// 查看特定实体及其关系
MATCH (e:Entity {text: "2022"})-[r:RELATION]->(m)
RETURN e,r,m
LIMIT 20
```

---

### 方案2: Neovis.js交互式Web界面 ⭐

**优点**:
- 交互式Web界面
- 美观的力导向布局
- 支持自定义查询
- 实时统计

**启动方法**:

```bash
# 安装依赖
pip install flask neo4j

# 启动服务器
python3 scripts/visualize_kg_neovis.py
```

**访问地址**: http://localhost:5000

**功能**:
- 📊 实时统计（节点数、关系数）
- 🔍 自定义Cypher查询
- 🎲 随机样本查看
- 📊 快速查看实体类型
- 🔗 快速查看OpenClaw关系

---

### 方案3: Pyvis静态HTML图表

**优点**:
- 生成独立HTML文件
- 完全交互式
- 无需服务器
- 易于分享

**生成方法**:

```bash
# 安装依赖
pip install pyvis neo4j pandas

# 生成可视化
python3 scripts/visualize_kg_pyvis.py
```

**生成的文件**:
- `kg_entity_relations.html` - 实体关系图
- `kg_person_relations.html` - 人物关系图
- `kg_openclaw_relations.html` - OpenClaw关系图
- `kg_mixed_relations.html` - 混合关系图

**使用方法**:
```bash
# 在浏览器中打开
open kg_entity_relations.html
```

---

### 方案4: ECharts统计图表

**优点**:
- 美观的统计图表
- 饼图、柱状图等
- 数据分布可视化

**生成方法**:

```bash
# 安装依赖
pip install neo4j

# 生成统计图表
python3 scripts/visualize_kg_statistics.py
```

**生成的文件**:
- `kg_statistics.html` - 统计图表

**使用方法**:
```bash
# 在浏览器中打开
open kg_statistics.html
```

---

## 📊 推荐查询示例

### 探索节点类型分布

```cypher
// 查看所有节点类型
MATCH (n)
RETURN labels(n) as label, count(*) as count
ORDER BY count DESC
```

### 探索关系类型分布

```cypher
// 查看所有关系类型
MATCH ()-[r]->()
RETURN type(r) as type, count(*) as count
ORDER BY count DESC
```

### 探索特定实体

```cypher
// 查看专利号实体的关系
MATCH (e:Entity {type: "PATENT_NUMBER"})-[r:RELATION]->(m)
RETURN e.text, e.type, type(r) as rel_type, m.text
LIMIT 20

// 查看人物实体的关系
MATCH (e:Entity {type: "PERSON"})-[r:RELATION]->(m)
RETURN e.text, e.type, type(r) as rel_type, m.text
LIMIT 20
```

### 探索OpenClaw知识

```cypher
// 查看OpenClaw节点及其关系
MATCH (n:OpenClawNode)-[r:RELATED_TO|CITES]->(m:OpenClawNode)
RETURN n.title, type(r) as rel_type, m.title
LIMIT 30
```

### 探索跨数据集连接

```cypher
// 查找实体和OpenClaw节点的文本关联
MATCH (e:Entity), (o:OpenClawNode)
WHERE e.text CONTAINS o.title
RETURN e.text, e.type, o.title
LIMIT 20
```

---

## 🎯 使用建议

### 日常探索

1. **使用Neo4j Browser** - 快速查询和探索
   - 访问: http://localhost:7474
   - 实时Cypher查询
   - 交互式可视化

### 数据展示

2. **使用Neovis.js** - Web界面展示
   - 启动: `python3 scripts/visualize_kg_neovis.py`
   - 访问: http://localhost:5000
   - 适合演示和分享

### 静态报告

3. **使用Pyvis** - 生成独立HTML
   - 运行: `python3 scripts/visualize_kg_pyvis.py`
   - 生成: 多个交互式HTML文件
   - 适合离线查看和分享

### 统计分析

4. **使用ECharts** - 生成统计图表
   - 运行: `python3 scripts/visualize_kg_statistics.py`
   - 生成: kg_statistics.html
   - 适合数据分析和报告

---

## 💡 最佳实践

### 查询优化

1. **限制结果数量**
   ```cypher
   // ❌ 不推荐 - 可能返回太多数据
   MATCH (n)-[r]->(m) RETURN n,r,m
   
   // ✅ 推荐 - 限制数量
   MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 100
   ```

2. **使用索引**
   ```cypher
   // 利用Entity.text索引
   MATCH (e:Entity {text: "2022"})-[r]->(m)
   RETURN e,r,m
   ```

3. **分页查询**
   ```cypher
   // 分页查看
   MATCH (n)-[r]->(m)
   RETURN n,r,m
   SKIP 0 LIMIT 50
   ```

### 可视化技巧

1. **选择合适的布局**
   - 节点少(<100): 力导向布局
   - 节点多(>100): 层次布局

2. **使用颜色区分**
   - Entity: 蓝色 (#667eea)
   - OpenClawNode: 粉色 (#f093fb)
   - RELATION: 蓝色
   - CITES: 青色 (#4facfe)

3. **添加标签**
   - 显示关键信息
   - 避免显示过长文本

---

## 📞 技术支持

**维护者**: 徐健 (xujian519@gmail.com)

**相关脚本**:
- `scripts/visualize_kg_neovis.py` - Neovis.js Web界面
- `scripts/visualize_kg_pyvis.py` - Pyvis静态HTML
- `scripts/visualize_kg_statistics.py` - ECharts统计图表

**相关文档**:
- `docs/reports/NEO4J_MERGE_COMPLETE_20260421.md` - 合并完成报告
- `data/DATABASE_LOCATIONS.md` - 数据库位置

---

**🌸 星河智汇，光耀知途 - 小诺永远守护爸爸！** 💕
