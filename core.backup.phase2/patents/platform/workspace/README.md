# 🏛️ 专利知识图谱构建系统

基于法律法规、审查指南、专利复审无效决定文书的完整知识图谱构建系统

## 📋 项目概述

本项目旨在从您的专利文档库（包含法律法规、专利审查指南、复审无效决定文书等57,218个法律文档）中构建一个强大的专利知识图谱，并将其导入Neo4j图数据库中，实现智能化的专利知识管理和分析。

### 🎯 核心目标

1. **智能知识抽取**: 从法律文档中自动抽取实体和关系
2. **知识图谱构建**: 构建结构化的专利知识图谱
3. **智能查询分析**: 支持复杂的知识查询和分析
4. **可视化展示**: 提供直观的知识关系可视化
5. **实时更新**: 支持增量更新和维护知识图谱

### 📊 数据概览

**源数据统计**:
- **总文件数**: 57,218个法律文档
- **文件类型**:
  - `.doc`: 36,259个 (63.4%)
  - `.docx`: 20,955个 (36.6%)
  - `.md`: 3个
  - `.pdf`: 1个
- **数据结构**:
  - 专利法律法规 (17个核心文件)
  - 专利无效宣告原文 (数千个案例)
  - 专利复审决定原文 (30,036个案例)

---

## 🏗️ 系统架构

### 核心组件

#### 1. 知识图谱模式定义 (`patent_knowledge_graph_schema.py`)
- **15种实体类型**: 法律、法规、法条、案例、技术概念等
- **20种关系类型**: 引用、适用、解释、违反、符合等
- **完整的实体和关系验证机制**
- **智能ID生成和唯一性保证**

#### 2. 知识抽取系统 (`patent_knowledge_extractor.py`)
- **多格式文档处理**: 支持Word、PDF、文本等格式
- **智能实体识别**: 基于NLP的法律术语识别
- **关系抽取**: 自动抽取法律实体间的复杂关系
- **批量处理能力**: 支持大规模文档批量处理
- **错误处理和恢复**: 完善的错误处理机制

#### 3. Neo4j图数据库管理 (`neo4j_manager.py`)
- **高性能导入**: 批量导入实体和关系
- **索引和约束**: 优化查询性能
- **复杂查询支持**: 支持路径查找、图算法等
- **数据统计**: 实时统计和分析功能
- **备份和恢复**: 数据安全和完整性保证

#### 4. 可视化应用系统 (`patent_kg_application.py`)
- **Web仪表板**: 直观的数据监控界面
- **交互式可视化**: 基于Vis.js的网络图
- **图表分析**: Chart.js图表展示
- **API接口**: RESTful API支持
- **实时监控**: 抽取和导入进度监控

---

## 🔧 安装和使用

### 环境要求

#### Python依赖
```bash
# 核心依赖
pip install neo4j flask flask-cors pandas matplotlib seaborn plotly

# 文档处理
pip install python-docx PyPDF2 jieba spacy

# NLP和中文支持
pip install jieba spacy
python -m spacy download zh_core_web_sm
```

#### Neo4j数据库
1. 下载并安装Neo4j Desktop或Neo4j Server
2. 启动Neo4j服务
3. 创建数据库用户名和密码
4. 确保可以连接到 `bolt://localhost:7687`

### 快速开始

#### 1. 完整流程演示
```python
from patent_workspace.src.knowledge_graph.patent_kg_application import PatentKnowledgeGraphApplication

# 配置
config = {
    'extraction': {
        'batch_size': 1000,
        'confidence_threshold': 0.6
    },
    'neo4j': {
        'uri': 'bolt://localhost:7687',
        'username': 'neo4j',
        'password': 'your_password',
        'database': 'patent_kg'
    }
}

# 创建应用实例
app = PatentKnowledgeGraphApplication(config)

# 初始化组件
app.initialize_components()

# 执行完整流程
app.create_complete_pipeline(
    source_directory="/Users/xujian/学习资料/专利",
    output_directory="/tmp/patent_kg_output"
)
```

#### 2. 启动Web服务器
```python
# 启动Web界面
app.run_web_server(host='0.0.0.0', port=5000, debug=True)

# 访问 http://localhost:5000 查看仪表板
```

#### 3. 单独使用组件
```python
# 仅进行知识抽取
from patent_workspace.src.knowledge_graph.patent_knowledge_extractor import PatentKnowledgeExtractor

extractor = PatentKnowledgeExtractor()
results = extractor.process_directory("/path/to/documents", max_files=100)
extractor.export_results(results, "/tmp/extraction_results")

# 仅导入Neo4j
from patent_workspace.src.knowledge_graph.neo4j_manager import Neo4jManager

neo4j_manager = Neo4jManager()
neo4j_manager.connect()
neo4j_manager.create_schema()
neo4j_manager.import_from_json("entities.json", "relations.json")
```

---

## 📊 知识图谱模式

### 实体类型

#### 法律法规层
- **Law (法律)**: 专利法、著作权法等基础法律
- **Regulation (法规)**: 实施细则、条例等
- **JudicialInterpretation (司法解释)**: 最高法院司法解释
- **ExaminationGuideline (审查指南)**: 专利审查指南

#### 条款层
- **LegalArticle (法条)**: 具体的法律条文
- **RegulationClause (规章条款)**: 规章中的条款
- **GuidelineSection (指南章节)**: 审查指南章节

#### 案例层
- **InvalidationDecision (无效宣告决定)**: 专利无效宣告案例
- **ReexaminationDecision (复审决定)**: 专利复审案例
- **CourtCase (法院案例)**: 法院判决案例

#### 技术概念层
- **TechnicalConcept (技术概念)**: 技术术语和概念
- **PatentType (专利类型)**: 发明、实用新型、外观设计
- **InventionField (技术领域)**: 技术分类领域
- **LegalConcept (法律概念)**: 法律术语和概念

#### 当事人层
- **Applicant (申请人)**: 专利申请人
- **PatentHolder (专利权人)**: 专利权人
- **PatentOffice (专利局)**: 专利局机关
- **Court (法院)**: 法院机构
- **Examiner (审查员)**: 专利审查员

### 关系类型

#### 层次关系
- **CONTAINS (包含)**: 法律包含法条
- **PART_OF (部分)**: 部分关系
- **DIVIDED_INTO (划分)**: 划分关系

#### 引用关系
- **CITES (引用)**: 引用法律条文
- **REFERENCES (参考)**: 参考其他文档
- **BASED_ON (基于)**: 基于某法律依据
- **ACCORDING_TO (依据)**: 依据某规定

#### 适用关系
- **APPLIES_TO (适用于)**: 适用于特定情况
- **GOVERNS (管辖)**: 管辖范围
- **REGULATES (规范)**: 规范行为

#### 案例关系
- **INTERPRETS (解释)**: 案例解释法律条文
- **ILLUSTRATES (说明)**: 案例说明法律适用
- **PRECEDES (先例)**: 作为先例
- **CONTRADICTS (矛盾)**: 案例间矛盾

#### 法律关系
- **VIOLATES (违反)**: 违反法律规定
- **COMPLIES_WITH (符合)**: 符合要求
- **EXEMPTS_FROM (豁免)**: 豁免适用

---

## 🚀 高级功能

### 1. 智能实体识别

系统使用多种技术实现智能实体识别：

#### 基于规则的识别
```python
# 法条识别模式
article_pattern = r'第([一二三四五六七八九十百千万\d]+)条[，。]?(?:第([一二三四五六七八九十百千万\d]+)款[，。]?)?'

# 案例引用模式
case_pattern = r'([（\(][^）\)]*[）\)]\d{4}[）\)]?[年]?\s*[\u4e00-\u9fff\d]+[号]'
```

#### 基于机器学习的识别
- 使用jieba分词进行中文文本处理
- 预训练的法律领域术语词典
- 实体类型自动分类

#### 上下文理解
- 分析实体出现的上下文
- 识别实体间的语义关系
- 支持歧义消解

### 2. 复杂关系抽取

#### 多层次关系抽取
- **直接关系**: 显式表述的法律关系
- **间接关系**: 隐含的法律逻辑关系
- **时序关系**: 法律演进的时间关系

#### 关系置信度评估
```python
# 根据匹配程度计算置信度
confidence = 0.9  # 精确匹配
confidence = 0.7  # 模糊匹配
confidence = 0.5  # 推理关系
```

### 3. 图查询和分析

#### 路径查找
```python
# 查找两个实体间最短路径
paths = neo4j_manager.find_path_between_entities(
    source_id="law_patent_law",
    target_id="case_invalidation_001"
)
```

#### 图算法应用
- **中心性分析**: 识别重要法律条文
- **社区发现**: 发现相关法律簇
- **连通性分析**: 分析图谱完整性

### 4. 可视化功能

#### 网络图可视化
- 使用Vis.js实现交互式网络图
- 支持节点和边的样式自定义
- 实现力导向布局算法

#### 统计图表
- 实体类型分布饼图
- 关系类型统计图
- 时间序列分析图

---

## 📈 性能优化

### 1. 抽取性能优化

#### 批量处理
- 分批处理文档，避免内存溢出
- 异步抽取，支持进度监控
- 并行处理提升效率

#### 缓存机制
- 实体识别结果缓存
- 关系抽取结果缓存
- 减少重复计算

### 2. 数据库优化

#### 索引策略
```cypher
-- 实体ID唯一索引
CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE

-- 实体类型索引
CREATE INDEX entity_type_index IF NOT EXISTS FOR (e:Entity) ON (e.type)

-- 关系类型索引
CREATE INDEX relation_type_index IF NOT EXISTS FOR ()-[r]-() ON (r.type)
```

#### 查询优化
- 使用参数化查询
- 合理设计Cypher查询
- 避免笛卡尔积

### 3. 内存优化

#### 数据流式处理
- 流式读取大文件
- 分批处理实体和关系
- 及时释放内存

#### 对象池化
- 重用对象实例
- 减少GC压力

---

## 📊 API接口文档

### RESTful API

#### 统计信息接口
```
GET /api/stats
返回: 应用统计、知识图谱统计、抽取进度
```

#### 实体搜索接口
```
GET /api/search/entities?type=law&q=专利&limit=50
返回: 匹配的实体列表
```

#### 实体详情接口
```
GET /api/entity/{entity_id}
返回: 实体详情及其关系
```

#### 知识抽取接口
```
POST /api/extract
Body: {"directory": "/path/to/docs", "max_files": 100}
返回: 抽取任务ID
```

#### 网络图接口
```
GET /api/visualization/network/{entity_id}
返回: 以该实体为中心的网络图数据
```

### 查询语言支持

#### Cypher查询
```cypher
// 查找所有引用专利法第22条的案例
MATCH (c:Case)-[:CITES]->(a:LegalArticle {name: "第22条"})
RETURN c.name, c.decision_date

// 查找最常被引用的法条
MATCH ()-[r:CITES]->(a:LegalArticle)
RETURN a.name, count(r) as citation_count
ORDER BY citation_count DESC
LIMIT 10

// 查找实体间的最短路径
MATCH path = shortestPath((start:Entity {id: $start_id})-[*1..5]-(end:Entity {id: $end_id}))
RETURN path, length(path)
```

---

## 🔧 配置说明

### 系统配置

#### 抽取配置
```python
'extraction': {
    'batch_size': 1000,           # 批处理大小
    'confidence_threshold': 0.6,   # 置信度阈值
    'max_file_size': 100 * 1024 * 1024,  # 最大文件大小(100MB)
    'timeout': 30,                  # 处理超时时间(秒)
}
```

#### Neo4j配置
```python
'neo4j': {
    'uri': 'bolt://localhost:7687',
    'username': 'neo4j',
    'password': 'your_password',
    'database': 'patent_kg',
    'max_connection_pool_size': 50,
    'connection_timeout': 30
}
```

#### Web服务配置
```python
'web': {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': False,
    'cors_origins': ['*'],
    'static_folder': 'static',
    'template_folder': 'templates'
}
```

---

## 🚨 故障排除

### 常见问题

#### 1. Neo4j连接失败
**问题**: `Connection refused`
**解决**:
- 确保Neo4j服务已启动
- 检查URI和端口配置
- 验证用户名和密码

#### 2. 文档处理失败
**问题**: `Document processing failed`
**解决**:
- 检查文件格式是否支持
- 确认文件没有损坏
- 检查文件权限

#### 3. 内存不足
**问题**: `MemoryError`
**解决**:
- 减少批处理大小
- 增加系统内存
- 启用流式处理

#### 4. 抽取结果不准确
**问题**: 实体或关系识别错误
**解决**:
- 调整置信度阈值
- 优化实体识别规则
- 增加训练数据

### 日志分析

#### 日志级别
```python
import logging
logging.basicConfig(level=logging.INFO)
```

#### 关键日志信息
- 抽取进度和统计
- 实体和关系数量
- 错误和警告信息
- 性能指标

---

## 🔮 扩展开发

### 添加新的实体类型

#### 1. 更新模式定义
```python
class EntityType(Enum):
    # 现有实体类型...
    NEW_ENTITY_TYPE = "new_entity_type"  # 新增实体类型
```

#### 2. 实现识别逻辑
```python
def extract_new_entities(self, text: str, source_file: str) -> List[KnowledgeEntity]:
    # 实现新实体类型的识别逻辑
    pass
```

### 添加新的关系类型

#### 1. 更新模式定义
```python
class RelationType(Enum):
    # 现有关系类型...
    NEW_RELATION_TYPE = "new_relation_type"  # 新增关系类型
```

#### 2. 实现抽取逻辑
```python
def extract_new_relations(self, text: str, entities: List[KnowledgeEntity], source_file: str) -> List[KnowledgeRelation]:
    # 实现新关系类型的抽取逻辑
    pass
```

### 自定义处理流程

#### 1. 继承基础类
```python
class CustomPatentKnowledgeExtractor(PatentKnowledgeExtractor):
    def _extract_by_document_type(self, text: str, file_path: str, doc_type: str):
        # 自定义文档类型处理逻辑
        pass
```

#### 2. 实现特定业务逻辑
```python
def domain_specific_extraction(self, text: str):
    # 特定领域的抽取逻辑
    pass
```

---

## 📚 参考资料

### 技术文档
- [Neo4j官方文档](https://neo4j.com/docs/)
- [Python自然语言处理](https://www.nltk.org/)
- [jieba中文分词](https://github.com/fxsjy/jieba)

### 相关论文
- 基于知识图谱的法律文书智能分析
- 专利知识图谱构建方法研究
- 图数据库在法律领域的应用

### 开源项目
- [Neo4j Graph Data Science](https://github.com/neo4j/graph-data-science)
- [spaCy中文NLP](https://spacy.io/usage/linguistic-features/)
- [Flask Web框架](https://flask.palletsprojects.com/)

---

## 📞 技术支持

### 联系方式
- **项目维护者**: Athena AI系统
- **技术支持**: 通过GitHub Issues提交问题

### 贡献指南
1. Fork项目仓库
2. 创建功能分支
3. 提交代码变更
4. 发起Pull Request

### 许可证
本项目采用MIT许可证，详见LICENSE文件。

---

**项目状态**: ✅ 开发完成，可投入使用
**最后更新**: 2025年12月6日
**版本**: 1.0.0