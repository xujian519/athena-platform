# IP智能体MCP Server

专利分析和撰写的MCP Server，基于Model Context Protocol实现。

## 功能特性

- **发明理解**: 分析发明交底书，提取技术特征
- **权利要求撰写**: 自动生成权利要求书
- **说明书撰写**: 生成完整的说明书草稿
- **审查意见答复**: 辅助答复审查意见
- **专利检索**: 向量相似度检索和相关案例查询
- **法条引用**: 自动匹配和引用相关法条

## 技术栈

- **MCP SDK**: @modelcontextprotocol/sdk
- **LLM**: Ollama (本地大语言模型)
- **向量数据库**: Qdrant
- **图数据库**: Neo4j
- **语言**: TypeScript

## 安装

```bash
# 安装依赖
npm install

# 构建项目
npm run build
```

## 配置

复制环境变量示例文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下参数：

- `OLLAMA_BASE_URL`: Ollama服务地址
- `OLLAMA_MODEL`: 使用的模型名称
- `QDRANT_URL`: Qdrant服务地址
- `QDRANT_COLLECTION`: 向量集合名称
- `NEO4J_URI`: Neo4j数据库地址
- `NEO4J_USER`: Neo4j用户名
- `NEO4J_PASSWORD`: Neo4j密码
- `LOG_LEVEL`: 日志级别

## 运行

### 开发模式

```bash
npm run dev
```

### 生产模式

```bash
npm run build
npm start
```

### 使用MCP Inspector测试

```bash
npm run inspector
```

## 项目结构

```
ip-mcp-server/
├── src/
│   ├── index.ts              # 主入口
│   ├── types/
│   │   └── index.ts          # 类型定义
│   ├── services/
│   │   ├── llm.ts            # LLM服务
│   │   └── knowledge.ts      # 知识库服务
│   └── utils/
│       └── logger.ts         # 日志工具
├── dist/                     # 编译输出目录
├── package.json
├── tsconfig.json
├── .env.example
└── README.md
```

## 依赖服务

### Ollama

需要安装并运行Ollama服务：

```bash
# 安装Ollama
curl https://ollama.ai/install.sh | sh

# 启动服务
ollama serve

# 下载模型
ollama pull llama2
```

### Qdrant

需要运行Qdrant向量数据库：

```bash
# 使用Docker运行
docker run -p 6333:6333 qdrant/qdrant
```

### Neo4j

需要运行Neo4j图数据库：

```bash
# 使用Docker运行
docker run -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest
```

## API工具

具体业务工具将由其他任务实现，包括：

- `understand_invention` - 发明理解
- `draft_claims` - 权利要求撰写
- `draft_specification` - 说明书撰写
- `respond_to_oa` - 审查意见答复
- `search_patents` - 专利检索
- `query_legal_provisions` - 法条查询

## 开发指南

### 添加新工具

1. 在 `src/tools/` 目录创建工具文件
2. 定义输入参数schema (使用Zod)
3. 实现工具处理逻辑
4. 在 `src/index.ts` 中注册工具

### 类型定义

所有类型定义在 `src/types/index.ts` 中，包括：

- `InventionUnderstanding` - 发明理解结果
- `Claim` - 权利要求
- `SpecificationDraft` - 说明书草稿
- `OAResponse` - 审查意见答复
- `SearchResult` - 检索结果
- 等等

## 许可证

MIT
