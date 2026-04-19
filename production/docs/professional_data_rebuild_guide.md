# 专业数据高质量重建指南

## 概述

本指南说明如何使用本地NLP系统和大模型，重建法律、专利、商标、IPC分类、技术词典等专业数据的向量库和知识图谱。

## 系统架构

### 技术栈
- **存储层**: PostgreSQL + Qdrant + NebulaGraph
- **NLP服务**: 本地优化的BERT模型 (端口 8001)
- **大模型**: 本地部署的Qwen2.5:14b (端口 8002)
- **向量维度**: 1024维
- **向量模型**: patent_bert (专利专用BERT模型)

### 数据流程
1. 原始数据 → NLP处理 → 实体关系提取
2. 分块处理 → 向量化 → Qdrant存储
3. 知识图谱构建 → NebulaGraph导入

## 构建器列表

### 1. 专利向量库构建器
- **文件**: `patent_vector_builder_nlp.py`
- **功能**: 构建专利复审无效向量库
- **特点**:
  - 智能分块（500字符，50重叠）
  - NLP增强的文档分析
  - 自动文档类型识别
  - 关键词提取

### 2. 专利知识图谱构建器
- **文件**: `high_quality_patent_builder.py`
- **功能**: 构建专利复审无效知识图谱
- **特点**:
  - 32种实体类型
  - 26种关系类型
  - 正则表达式模式匹配
  - NLP关系提取

### 3. IPC分类知识图谱构建器
- **文件**: `ipc_knowledge_graph_builder.py`
- **功能**: 构建IPC分类知识图谱
- **特点**:
  - IPC层级关系识别
  - 技术领域映射
  - LLM辅助关系提取
  - 语义相似度计算

### 4. 技术词典知识图谱构建器
- **文件**: `technical_dictionary_builder.py`
- **功能**: 构建技术术语词典知识图谱
- **特点**:
  - 中英文术语对齐
  - 技术领域自动分类
  - 定义模式匹配
  - 术语关系推理

### 5. 主执行脚本
- **文件**: `rebuild_all_professional_data.py`
- **功能**: 批量执行所有构建任务
- **特点**:
  - 任务编排管理
  - 环境检查
  - 进度跟踪
  - 报告生成

## 使用方法

### 前置条件

1. **环境检查**
```bash
# 检查Python环境
python3 --version

# 检查依赖
pip list | grep aiohttp
pip list | grep nebula3-python

# 检查服务
curl http://localhost:8001/health  # NLP服务
curl http://localhost:8002/api/tags  # LLM服务
```

2. **数据准备**
将原始数据放在以下目录：
- `/Users/xujian/Athena工作平台/dev/tools/patent_review/` - 专利复审决定
- `/Users/xujian/Athena工作平台/dev/tools/patent_invalid/` - 无效宣告决定
- `/Users/xujian/Athena工作平台/dev/tools/ipc_data/` - IPC分类数据
- `/Users/xujian/Athena工作平台/dev/tools/technical_dict/` - 技术词典

3. **服务启动**
```bash
# 启动NLP服务
cd /Users/xujian/Athena工作平台/production
./start_nlp_service.sh

# 启动大模型服务
./start_llm_service.sh

# 启动数据库服务
docker-compose up -d
```

### 执行重建

#### 方式一：使用主脚本（推荐）
```bash
cd /Users/xujian/Athena工作平台/production
python3 dev/scripts/rebuild_all_professional_data.py
```

#### 方式二：单独执行
```bash
# 构建专利向量库
python3 dev/scripts/patent_vector_builder_nlp.py

# 构建专利知识图谱
python3 dev/scripts/high_quality_patent_builder.py

# 构建IPC知识图谱
python3 dev/scripts/ipc_knowledge_graph_builder.py

# 构建技术词典知识图谱
python3 dev/scripts/technical_dictionary_builder.py
```

## 输出结果

### 目录结构
```
production/data/
├── vector_db/                     # 向量数据库
│   ├── patent_review_invalid/     # 专利向量
│   └── qdrant_import_*.json       # Qdrant导入文件
├── knowledge_graph/               # 知识图谱
│   ├── patent_knowledge_graph/    # 专利知识图谱
│   │   ├── patent_entities_*.json
│   │   ├── patent_relations_*.json
│   │   └── nebula_*/              # NebulaGraph脚本
│   ├── ipc_knowledge_graph/       # IPC知识图谱
│   └── technical_dictionary_kg/   # 技术词典知识图谱
└── rebuild_report.json            # 重建报告
```

### 质量指标
- **向量质量**: 使用专利专用BERT模型
- **实体识别**: 规则+NLP双重保障
- **关系提取**: 正则+LLM三级验证
- **数据完整性**: 自动去重和校验

## 数据导入

### 向量数据导入Qdrant
```bash
# 使用qdrant-client
python3 -c "
import json
from qdrant_client import QdrantClient

client = QdrantClient(host='localhost', port=6333)

# 读取导入文件
with open('data/vector_db/patent_review_invalid/qdrant_import_*.json', 'r') as f:
    points = json.load(f)

# 创建集合
client.recreate_collection(
    collection_name='patent_review_invalid',
    vectors_config={
        'size': 1024,
        'distance': 'Cosine'
    }
)

# 上传数据
client.upload_points(
    collection_name='patent_review_invalid',
    points=points
)
"
```

### 知识图谱导入NebulaGraph
```bash
# 导入实体
nebula-console -addr 127.0.0.1 -port 9669 -u root -p nebula \
  -f data/knowledge_graph/patent_knowledge_graph/nebula_tags/patent.ngql

# 导入关系
nebula-console -addr 127.0.0.1 -port 9669 -u root -p nebula \
  -f data/knowledge_graph/patent_knowledge_graph/nebula_edges/has_claim.ngql
```

## 性能优化

### 批处理大小
- 向量化: 10个文档/批
- 实体提取: 100个文档/批
- NebulaGraph导入: 1000条/批

### 并发设置
- NLP并发: 5
- LLM并发: 2
- 数据库连接池: 10

### 缓存策略
- 向量缓存: Redis
- NLP结果缓存: 1小时
- 实体ID缓存: 内存

## 故障排查

### 常见问题

1. **NLP服务无响应**
```bash
# 检查服务状态
ps aux | grep nlp_service

# 重启服务
./start_nlp_service.sh
```

2. **内存不足**
```bash
# 减少批处理大小
# 在脚本中修改 batch_size = 5
```

3. **向量维度错误**
```bash
# 检查向量维度
# 确保 Qdrant 集合维度为 1024
```

4. **NebulaGraph连接失败**
```bash
# 检查服务
docker ps | grep nebula

# 重启服务
docker restart nebula-graphd
```

### 日志查看
```bash
# 查看构建日志
tail -f logs/rebuild.log

# 查看错误日志
grep ERROR logs/rebuild.log
```

## 监控指标

### 关键指标
- 文档处理速度: docs/s
- 向量生成速度: vectors/s
- 实体提取准确率: >85%
- 关系提取准确率: >75%
- 内存使用率: <80%
- CPU使用率: <90%

### 性能基准
- 专利向量库: 1000文档/小时
- 知识图谱: 500文档/小时
- 端到端处理: 500文档/小时

## 扩展指南

### 添加新的数据类型
1. 创建新的构建器类
2. 定义实体和关系类型
3. 实现extract_*方法
4. 添加到主执行脚本

### 自定义NLP模型
1. 准备训练数据
2. 微调BERT模型
3. 更新模型配置
4. 重新部署服务

### 集成外部数据源
1. 实现数据接口
2. 添加数据转换器
3. 更新数据读取逻辑

## 最佳实践

1. **数据质量**
   - 原始数据标准化
   - 去重和清洗
   - 格式统一

2. **处理流程**
   - 分批处理大数据
   - 保留中间结果
   - 定期备份

3. **系统维护**
   - 监控服务状态
   - 定期清理缓存
   - 更新模型版本

4. **安全考虑**
   - 数据脱敏
   - 访问控制
   - 审计日志

## 联系支持

如有问题，请联系：
- 技术支持: xujian519@gmail.com
- 文档更新: 见项目GitHub
- 问题反馈: 创建Issue