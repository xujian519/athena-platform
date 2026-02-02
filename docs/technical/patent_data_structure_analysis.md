# 专利数据库结构分析报告

## 📋 数据结构说明

### 核心认识
经过Ollama大模型分析，专利数据库的实际结构如下：

1. **patents表中的`patent_name`字段**
   - 实际存储的是**申请人（客户）名称**，不是专利发明名称
   - 例如："山东艾迈泰克机械科技有限公司"、"广东石油化工学院（徐娓）"等

2. **patent_agents表存储的是案源人**
   - 这些是专利代理人或业务开发人员
   - 例如：徐健、凯胜、傅玉秀等
   - 每个专利通过`agent_id`关联到案源人

3. **数据关系**
   - 案源人（agent）→ 服务客户（customer）→ 拥有专利（patent）
   - 案源人和客户是服务关系，不是同一实体

## 🔍 客户（申请人）分析

### 主要客户类型
1. **企业客户**
   - 山东恒科环保设备有限公司（变更为：宿迁龙净环保科技有限公司）
   - 山东中大农业科技有限公司
   - 广东石油化工学院（徐娓）
   - 山东艾迈泰克机械科技有限公司

2. **注意事项**
   - 有些客户有名称变更记录
   - 需要标准化处理相似名称
   - 地域标识很重要（山东、广东等）

## 📊 案源人业绩（前10位）

| 案源人 | 总专利数 | 说明 |
|--------|----------|------|
| 徐健 | 8,784件 | 主要案源人 |
| 凯胜 | 6,522件 |  |
| 傅玉秀 | 2,292件 |  |
| 荆向勇 | 1,788件 |  |
| 济宁李凯 | 828件 | 地域性案源人 |

## 💡 建议的SQL查询

### 1. 统计每个客户的专利数量
```sql
SELECT
    patent_name as 客户名称,
    COUNT(*) as 专利数量,
    COUNT(CASE WHEN legal_status = '已拿证' THEN 1 END) as 已授权数量,
    COUNT(CASE WHEN legal_status LIKE '%驳回%' THEN 1 END) as 驳回数量
FROM patents
WHERE patent_name IS NOT NULL
AND patent_name != ''
GROUP BY patent_name
ORDER BY 专利数量 DESC;
```

### 2. 查看某案源人服务的所有客户
```sql
SELECT
    a.client_name as 案源人,
    p.patent_name as 客户名称,
    COUNT(*) as 专利数量
FROM patent_agents a
JOIN patents p ON a.id = p.agent_id
WHERE a.client_name = '徐健'
GROUP BY a.client_name, p.patent_name
ORDER BY 专利数量 DESC;
```

### 3. 分析客户地区分布
```sql
SELECT
    CASE
        WHEN patent_name LIKE '山东%' THEN '山东省'
        WHEN patent_name LIKE '广东%' THEN '广东省'
        WHEN patent_name LIKE '北京%' THEN '北京市'
        WHEN patent_name LIKE '上海%' THEN '上海市'
        ELSE '其他地区'
    END as 地区,
    COUNT(DISTINCT patent_name) as 客户数量,
    COUNT(*) as 专利数量
FROM patents
WHERE patent_name IS NOT NULL
GROUP BY 地区
ORDER BY 专利数量 DESC;
```

## 🚀 数据结构优化建议

### 1. 创建标准化客户表
```sql
CREATE TABLE patent_customers (
    id SERIAL PRIMARY KEY,
    original_name VARCHAR(500),  -- 原始申请人名称
    standard_name VARCHAR(200),  -- 标准化名称
    region VARCHAR(50),          -- 地区
    entity_type VARCHAR(50),     -- 企业类型（公司/学院/大学等）
    has_name_change BOOLEAN,     -- 是否有名称变更
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. 数据清理任务
1. 标准化客户名称
2. 合并相似客户
3. 识别名称变更记录
4. 提取地域信息

### 3. 添加外键关系
```sql
-- 在patents表添加客户ID
ALTER TABLE patents ADD COLUMN customer_id INTEGER REFERENCES patent_customers(id);
```

## 📈 业务洞察

1. **主要客户集中在山东省**的企业和机构
2. **案源人与客户有明确的地域对应关系**（如济宁李凯）
3. **名称变更需要特别记录**，这可能是企业重组或品牌升级
4. **可以建立客户-案源人服务关系图**，优化业务分配

## ✅ 总结

- **patent_name** = 申请人/客户名称
- **patent_agents** = 案源人（代理人）
- 需要建立独立的客户表来管理客户信息
- 可以通过数据分析优化业务布局和案源人分配