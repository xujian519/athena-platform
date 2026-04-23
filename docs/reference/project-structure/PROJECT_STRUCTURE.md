# Athena工作平台项目结构

## 📁 目录说明

### 核心服务
- **`services/`** - 微服务集合
  - `knowledge-graph-service/` - 知识图谱API服务
  - `modules/storage/storage-system/` - 存储系统服务
  - `yunpat-agent/` - 专利智能代理服务

### 数据存储
- **`data/`** - 项目数据
  - `guideline_graph/` - 专利审查指南知识图谱
  - `guideline_vectors/` - 审查指南向量库
  - `patent_guideline_system.db` - SQLite数据库

### 核心模块
- **`core/`** - 核心功能模块
  - `modules/memory/memory/` - 内存管理
  - `cognition/` - 认知引擎
  - `modules/knowledge/knowledge/` - 知识管理
  - `learning/` - 学习系统

### 专利相关
- **`apps/patent-platform/`** - 专利平台
- **`patent-guideline-system/`** - 专利审查指南系统
- **`modules/patent/patent_hybrid_retrieval/`** - 专利混合检索

### 配置文件
- **`configs/`** - Docker和系统配置
- **`docs/`** - 项目文档
- **`dev/scripts/`** - 自动化脚本

### MCP服务器
- **`mcp-servers/`** - Model Context Protocol服务器
  - `gaode-mcp-server/` - 高德地图MCP
  - `patent-mcp-server/` - 专利MCP

### 基础设施
- **`infrastructure/database/`** - 数据库相关
- **`infrastructure/docker/`** - Docker配置
- **`infrastructure/nginx/`** - Nginx配置

### 其他
- **`dev/examples/`** - 使用示例
- **`dev/tools/`** - 工具集
- **`dev/tests/`** - 测试代码（已清理）
- **`temp/`** - 临时文件
- **`logs/`** - 日志文件

## 🚀 快速开始

### 1. 环境准备
```bash
# 设置Python环境
source /opt/miniconda3/bin/activate
export PYTHONPATH=/Users/xujian/Athena工作平台:$PYTHONPATH

# 加载环境变量
cp .env.template .env
```

### 2. 启动服务
```bash
# 启动知识图谱API
cd services/knowledge-graph-service
./start.sh

# 启动存储系统
cd storage-system
./start.sh
```

### 3. 访问服务
- 知识图谱API: http://localhost:8080/docs
- 审查指南搜索: http://localhost:8080/api/v2/guidelines/search
- Qdrant管理: http://localhost:6333/dashboard

## 📊 今日完成内容

### ✅ 专利审查指南知识图谱
- 构建了53个节点的知识图谱
- 包含6个主要章节（初步审查、实质审查等）
- 提取了19条审查规则和9个示例
- 生成了768维向量表示

### ✅ 向量库集成
- Qdrant集合：patent_guideline
- 53个向量已导入
- 支持语义搜索和相似度查询

### ✅ API服务集成
- 新增4个审查指南API端点
- 动态提示词生成功能
- 智能规则提取能力

### ✅ 项目清理
- 删除100个测试和demo文件
- 清理缓存和临时文件
- 整理项目目录结构
- 重要文件已备份

## 📝 维护说明

- 定期清理日志文件：`logs/`
- 监控向量库大小：`data/guideline_vectors/`
- 备份重要数据：`backup/`
- 更新文档：`docs/`

## 🔗 相关链接
- [API文档](http://localhost:8080/docs)
- [Qdrant管理界面](http://localhost:6333/dashboard)
- [项目README](./README.md)