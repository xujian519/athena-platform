# 云熙记忆系统设计方案
# YunPat Memory System Design

## 🧠 系统架构

### 记忆类型分类

```yaml
memory_types:
  短期记忆:
    描述: 临时交互记忆
    存储时间: 会话期间（~30分钟）
    内容: 对话上下文、临时数据
    存储: 内存/Redis

  长期记忆:
    描述: 持久化重要信息
    存储时间: 永久
    内容: 用户偏好、重要对话、知识积累
    存储: PostgreSQL

  工作记忆:
    描述: 专利业务相关记忆
    存储时间: 业务周期内
    内容: 专利分析、案例库、法规要点
    存储: PostgreSQL + Qdrant

  情感记忆:
    描述: 情感交互记录
    存储时间: 永久
    内容: 用户情绪、特殊时刻、关系进展
    存储: PostgreSQL
```

### 数据模型
```yaml
memory_items:
  memory_id: UUID (主键)
  memory_type: string (short/long/work/emotional)
  content: text/json (记忆内容)
  metadata: json (元数据)
  user_id: string (用户标识)
  importance: float (0-1, 重要性权重)
  tags: array (标签)
  created_at: timestamp
  accessed_at: timestamp (最后访问时间)
  access_count: integer (访问次数)
  vector_embedding: array (语义向量，用于相似度搜索)
```

## 🔧 技术实现

### 1. 记忆存储接口
```python
class MemoryManager:
    def save_memory(self, content, memory_type, user_id, **kwargs)
    def recall_memory(self, query, user_id, memory_type=None, limit=10)
    def search_similar(self, query, user_id, similarity_threshold=0.7)
    def update_memory(self, memory_id, updates)
    def delete_memory(self, memory_id)
    def get_memories_by_type(self, memory_type, user_id)
```

### 2. 智能检索策略
- **语义搜索**：使用向量相似度
- **关键词搜索**：基于内容匹配
- **时间衰减**：近期记忆权重更高
- **个性化排序**：基于访问历史

### 3. 记忆管理规则
- 自动保存重要对话
- 定期清理过期短期记忆
- 记忆关联和链接
- 记忆重要性评估

## 🗄️ 数据库设计

### PostgreSQL表结构
```sql
CREATE TABLE memory_items (
    memory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_type VARCHAR(20) NOT NULL CHECK (memory_type IN ('short', 'long', 'work', 'emotional')),
    user_id VARCHAR(100) NOT NULL DEFAULT 'default',
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    importance FLOAT DEFAULT 0.5 CHECK (importance >= 0 AND importance <= 1),
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    vector_id UUID,  -- 引用向量库ID
    expires_at TIMESTAMP,  -- 短期记忆过期时间
    is_archived BOOLEAN DEFAULT FALSE
);

-- 索引
CREATE INDEX idx_memory_user_type ON memory_items(user_id, memory_type);
CREATE INDEX idx_memory_created ON memory_items(created_at DESC);
CREATE INDEX idx_memory_importance ON memory_items(importance DESC);
CREATE INDEX idx_memory_tags ON memory_items USING GIN(tags);
```

### 记忆元数据示例
```json
{
  "source": "patent_analysis",
  "patent_id": "CN202312345678",
  "context": "用户询问专利无效性分析",
  "sentiment": "curious",
  "confidence": 0.9,
  "related_topics": ["专利", "无效性", "知识产权"]
}
```

## 🔄 记忆处理流程

### 记忆保存流程
```
用户输入 → 内容分析 → 类型判断 → 重要性评估 → 存储策略 → 持久化
                                    ↓
                            生成向量嵌入 → 存储到Qdrant
```

### 记忆检索流程
```
查询请求 → 查询分析 → 多策略搜索 → 结果排序 → 相关性过滤 → 返回结果
```

## 📊 功能特性

### 1. 智能分类
- 自动识别记忆类型
- 基于内容重要性评估
- 动态调整存储策略

### 2. 相似度搜索
- 语义相似度匹配
- 情感关联发现
- 上下文理解

### 3. 个性化管理
- 用户独立的记忆空间
- 个性化推荐
- 记忆关联图

### 4. 记忆可视化
- 记忆时间线
- 关系图谱
- 热点话题分析

## 🔌 API接口设计

### 记忆管理API
```yaml
/api/v1/modules/modules/memory/memory/modules/memory/memory/save:
  POST
  保存记忆

  body:
    content: string
    type: string (short/long/work/emotional)
    importance: float
    tags: array
    metadata: object

/api/v1/modules/modules/memory/memory/modules/memory/memory/recall:
  GET
  回忆记忆

  params:
    query: string
    type: string
    limit: integer

/api/v1/modules/modules/memory/memory/modules/memory/memory/search:
  POST
  相似度搜索

  body:
    query: string
    similarity_threshold: float
    limit: integer

/api/v1/modules/modules/memory/memory/modules/memory/memory/update:
  PUT
  更新记忆

  params:
    memory_id: uuid
  body: update_data

/api/v1/modules/modules/memory/memory/modules/memory/memory/delete:
  DELETE
  删除记忆

  params:
    memory_id: uuid
```

### 智能记忆API
```yaml
/api/v1/modules/modules/memory/memory/modules/memory/memory/auto-save:
  POST
  自动保存对话

  body:
    conversation: array
    user_id: string

/api/v1/modules/modules/memory/memory/modules/memory/memory/insights:
  GET
  获取记忆洞察

  params:
    user_id: string
    time_range: string (day/week/month)
```

## 🚀 实施计划

### 第一阶段：基础功能（1周）
1. 数据库表设计
2. 基础CRUD操作
3. 简单记忆保存和检索

### 第二阶段：智能化（2周）
1. 向量嵌入集成
2. 相似度搜索
3. 智能分类系统

### 第三阶段：高级功能（1周）
1. 记忆关联分析
2. 个性化推荐
3. 记忆可视化

## 📈 性能优化

### 存储优化
- 分区表存储（按用户和时间）
- 冷热数据分离
- 自动归档机制

### 查询优化
- 向量索引加速
- 缓存热点查询
- 预计算关联关系

### 扩展性
- 支持分布式存储
- 读写分离
- 异步处理

## 🔒 安全考虑

### 数据隐私
- 用户数据隔离
- 敏感信息加密
- 记忆权限控制

### 数据保护
- 定期备份
- 版本控制
- 删除策略

## 💡 创新特性

### 1. 情感记忆
- 记录用户的情感变化
- 建立情感关系图谱
- 情感化响应优化

### 2. 智能关联
- 自动发现记忆关联
- 构建知识网络
- 推断式记忆扩展

### 3. 记忆进化
- 记忆重要性动态调整
- 过期记忆自动清理
- 知识图谱持续更新