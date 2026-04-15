# 专利指南系统重新设计文档

## 1. 系统概述

基于Athena平台现有的存储系统、NLP系统和多模态文件系统，重新设计专利审查指南系统，实现：
- 智能文档解析与理解
- 多模态数据处理（PDF、Word、图片等）
- 知识图谱与向量库融合存储
- 基于GraphRAG的智能检索
- 动态规则推荐与问答系统

## 2. 技术架构

### 2.1 存储层架构
```
┌─────────────────────────────────────────────────────────┐
│                    存储层 (Storage Layer)                │
├─────────────────┬─────────────────┬─────────────────────┤
│   PostgreSQL    │    Qdrant       │    NebulaGraph       │
│   (元数据)      │   (向量存储)     │    (知识图谱)        │
│                 │                 │                     │
│ • 文档索引      │ • 1024维向量     │ • 实体节点           │
│ • 用户信息      │ • 语义检索       │ • 关系边             │
│ • 处理状态      │ • 相似度计算     │ • 图查询             │
│ • 版本管理      │                 │                     │
└─────────────────┴─────────────────┴─────────────────────┘
```

### 2.2 处理流程
```
原始文档 → 多模态解析 → 结构化提取 → NLP处理 → 双重存储 → 智能检索
    │           │           │           │           │           │
  PDF/Word   OCR/表格   章节识别    实体关系   向量+图谱   GraphRAG
    │           │           │           │           │           │
    ↓           ↓           ↓           ↓           ↓           ↓
  文件系统   图像处理    规则引擎    本地NLP   Qdrant+NG  应用服务
```

### 2.3 系统组件
1. **多模态文档处理器** (`multimodal_processor.py`)
2. **专利指南解析器** (`patent_guideline_parser.py`)
3. **知识图谱构建器** (`patent_guideline_graph_builder.py`)
4. **向量库构建器** (`patent_guideline_vector_builder.py`)
5. **GraphRAG检索器** (`patent_guideline_retriever.py`)
6. **智能问答系统** (`patent_guideline_qa.py`)
7. **动态提示词生成器** (`dynamic_prompt_generator.py`)

## 3. 数据模型设计

### 3.1 PostgreSQL 表结构

```sql
-- 文档主表
CREATE TABLE guideline_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    version VARCHAR(50),
    file_path TEXT,
    file_type VARCHAR(20),
    file_size BIGINT,
    hash_md5 VARCHAR(32) UNIQUE,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

-- 章节结构表
CREATE TABLE guideline_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES guideline_documents(id),
    section_id VARCHAR(100) NOT NULL, -- 如 P2-C4-S3.2.1
    level INTEGER NOT NULL,
    title TEXT,
    content TEXT,
    parent_id VARCHAR(100),
    full_path TEXT,
    page_range TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(document_id, section_id)
);

-- 实体表
CREATE TABLE guideline_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_text VARCHAR(500) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    section_id UUID REFERENCES guideline_sections(id),
    position_start INTEGER,
    position_end INTEGER,
    attributes JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 引用关系表
CREATE TABLE guideline_references (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_section_id UUID REFERENCES guideline_sections(id),
    target_section_id VARCHAR(100),
    reference_type VARCHAR(50),
    reference_text TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 3.2 Qdrant 集合设计

```python
# 章节向量集合
collections = {
    "patent_guideline_sections": {
        "vector_size": 1024,
        "distance": "Cosine",
        "payload_schema": {
            "document_id": "uuid",
            "section_id": "keyword",
            "level": "integer",
            "title": "text",
            "parent_id": "keyword",
            "full_path": "text",
            "entities": "array",
            "chunk_type": "keyword"  # parent/child
        }
    }
}
```

### 3.3 NebulaGraph 图模型

```ngql
-- Tag定义
CREATE TAG IF NOT EXISTS Document (
    id string,
    title string,
    version string
);

CREATE TAG IF NOT EXISTS Section (
    id string,
    level int,
    title string,
    content string,
    full_path string
);

CREATE TAG IF NOT EXISTS Entity (
    text string,
    type string,
    attributes string
);

CREATE TAG IF NOT EXISTS LawArticle (
    id string,
    title string,
    content string
);

-- Edge定义
CREATE EDGE IF NOT EXISTS HAS_SECTION ();
CREATE EDGE IF NOT EXISTS REFERS_TO ();
CREATE EDGE IF NOT EXISTS MENTIONS ();
CREATE EDGE IF NOT EXISTS DEFINES ();
CREATE EDGE IF NOTOTES CONTAINS_EXAMPLE ();
```

## 4. 核心功能模块

### 4.1 多模态文档处理
- PDF文本提取
- Word文档解析
- 表格识别与转换
- 图片OCR处理
- 多格式统一转换

### 4.2 智能结构解析
- 章节层级识别
- 规则条款提取
- 引用关系发现
- 案例标注识别
- 法律条款关联

### 4.3 NLP增强处理
- 实体识别（法律条款、技术术语、案例等）
- 关系抽取（引用、定义、条件、例外等）
- 语义理解
- 关键词提取
- 摘要生成

### 4.4 GraphRAG检索
- 向量语义检索
- 图谱路径遍历
- 混合结果融合
- 相关性重排序
- 上下文扩展

### 4.5 智能问答系统
- 自然语言查询理解
- 多跳问题推理
- 案例匹配
- 规则适用性判断
- 答案生成与验证

## 5. 实施计划

### Phase 1: 基础设施搭建 (3天)
1. 数据库表创建
2. NebulaGraph空间配置
3. Qdrant集合初始化
4. 基础工具类实现

### Phase 2: 文档处理模块 (5天)
1. 多模态解析器实现
2. 结构化提取引擎
3. 批量处理管道
4. 数据质量验证

### Phase 3: 知识构建模块 (5天)
1. 实体关系提取
2. 知识图谱构建
3. 向量化处理
4. 索引创建

### Phase 4: 检索应用模块 (5天)
1. GraphRAG检索器
2. 智能问答系统
3. 动态提示词生成
4. API接口实现

### Phase 5: 测试优化 (3天)
1. 功能测试
2. 性能优化
3. 用户体验优化
4. 部署文档编写

## 6. 关键技术点

### 6.1 层级结构保留
- 父子索引策略
- 上下文注入
- 路径编码
- 层级权重

### 6.2 引用关系处理
- 交叉引用解析
- 循环引用检测
- 引用强度计算
- 关联传播

### 6.3 语义增强
- 法律领域词典
- 同义词扩展
- 概念层次映射
- 领域规则注入

### 6.4 性能优化
- 分级缓存策略
- 并行处理机制
- 增量更新方案
- 查询优化

## 7. 质量保证

### 7.1 数据质量
- 结构完整性 > 98%
- 引用准确率 > 95%
- 实体识别准确率 > 90%

### 7.2 检索质量
- 查询响应 < 200ms
- 检索准确率 > 85%
- 相关规则召回 > 90%

### 7.3 系统稳定性
- 7×24小时运行
- 容错机制
- 自动恢复
- 监控告警

## 8. 创新特性

1. **多模态融合**: 统一处理PDF、Word、图片等多种格式
2. **智能理解**: 基于本地NLP的深度语义理解
3. **GraphRAG**: 向量与图谱的双重检索优势
4. **动态提示**: 实时生成专业的审查提示词
5. **增量更新**: 支持文档版本的增量式更新

## 9. 部署架构

```
┌─────────────────────────────────────────┐
│            应用服务层                    │
│  • FastAPI Web服务                      │
│  • 图形化前端界面                        │
│  • API网关                              │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│            业务逻辑层                    │
│  • 检索服务                             │
│  • 问答服务                             │
│  • 推荐服务                             │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│            数据访问层                    │
│  • PostgreSQL连接池                      │
│  • Qdrant客户端                          │
│  • NebulaGraph客户端                    │
└─────────────────────────────────────────┘
```

## 10. 预期效果

1. **效率提升**: 审查规则检索时间从分钟级降至秒级
2. **准确率提升**: 相关规则检索准确率提升至90%+
3. **智能化**: 支持自然语言查询和智能推理
4. **易用性**: 提供友好的图形化界面和API接口
5. **可扩展性**: 支持更多法律法规类型的接入