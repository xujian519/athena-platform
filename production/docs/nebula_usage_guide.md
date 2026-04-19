
# NebulaGraph法律知识图谱使用指南

## 1. 连接到图空间
```ngql
USE legal_knowledge;
```

## 2. 查询示例

### 查询所有法律
```ngql
MATCH (v:Law) RETURN v LIMIT 10;
```

### 查询某部法律的所有条款
```ngql
MATCH (v:Law)-[e:HAS_ARTICLE]->(v2:Article)
WHERE v.name == "中华人民共和国民法典"
RETURN v, e, v2;
```

### 查询包含特定权利的条款
```ngql
MATCH (v:Article)-[e:GRANT]->(v2:Right)
WHERE v2.name CONTAINS "选举权"
RETURN v, e, v2;
```

### 查询机构的义务
```ngql
MATCH (v:Organization)-[e:IMPOSE]->(v2:Obligation)
WHERE v.name == "国务院"
RETURN v, e, v2;
```

## 3. 统计查询

### 统计各类实体数量
```ngql
FETCH PROP ON * * YIELD tags($$) as tag |
YIELD $-.tag as tag, count(*) as count
GROUP BY $-.tag;
```

### 统计关系类型分布
```ngql
MATCH ()-[e]->()
YIELD $$.name as src, $$.name as dst, type(e) as rel_type
RETURN rel_type, count(*) as count
GROUP BY rel_type;
```

## 4. 导入说明
1. 使用生成的 .ngql 文件通过 nebula-console 导入
2. 或使用提供的 .sh 脚本批量导入
3. 导入前请确保 NebulaGraph 服务已启动

## 5. 注意事项
- 顶点ID使用MD5哈希生成，确保唯一性
- 所有文本字段已转义特殊字符
- 建议分批导入大量数据，避免内存溢出
