# 专利混合检索系统 - Web界面

专利混合检索系统的现代化Web界面，基于Vue 3 + TypeScript + Tailwind CSS构建。

## 🌟 功能特性

### 核心功能
- **三路混合检索**: BM25全文搜索 + 向量语义检索 + 知识图谱增强
- **实时搜索**: 支持实时检索结果展示
- **高级筛选**: IPC分类、申请人、日期范围等筛选条件
- **搜索历史**: 保存和回放搜索历史
- **权重配置**: 可视化调整三种检索策略的权重
- **实时监控**: 缓存命中率、响应时间、连接数等性能指标

### 界面特色
- 🎨 现代化渐变背景设计
- 🌙 深色主题，舒适护眼
- 📊 可视化数据展示
- ⚡ 响应式布局，支持移动端
- 🔔 实时WebSocket更新

## 📁 项目结构

```
patent-retrieval-webui/
├── src/
│   ├── api/                # API客户端
│   │   └── client.ts
│   ├── assets/             # 静态资源
│   │   └── styles/
│   ├── components/         # Vue组件
│   │   ├── SearchForm.vue  # 搜索表单
│   │   ├── PatentList.vue  # 专利列表
│   │   ├── ScoreBreakdown.vue  # 评分明细
│   │   ├── MetricCard.vue  # 指标卡片
│   │   ├── NavBar.vue      # 导航栏
│   │   └── NavLink.vue     # 导航链接
│   ├── router/             # 路由配置
│   │   └── index.ts
│   ├── stores/             # 状态管理
│   │   ├── search.ts       # 搜索状态
│   │   └── config.ts       # 配置状态
│   ├── types/              # TypeScript类型定义
│   │   └── index.ts
│   ├── views/              # 页面视图
│   │   ├── SearchView.vue  # 检索页面
│   │   ├── HistoryView.vue # 历史页面
│   │   ├── ConfigView.vue  # 配置页面
│   │   └── MonitoringView.vue  # 监控页面
│   ├── App.vue             # 根组件
│   └── main.ts             # 入口文件
├── backend/                # FastAPI后端
│   ├── api_server.py       # API服务器
│   ├── requirements.txt    # Python依赖
│   └── start_server.sh     # 启动脚本
├── package.json
├── vite.config.ts
├── tsconfig.json
└── tailwind.config.js
```

## 🚀 快速开始

### 前端启动

```bash
cd patent-retrieval-webui

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将在 `http://localhost:3000` 启动。

### 后端启动

```bash
cd patent-retrieval-webui/backend

# 使用启动脚本
./start_server.sh

# 或手动启动
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python api_server.py
```

后端API将在 `http://localhost:8000` 启动，API文档：`http://localhost:8000/docs`

## 📊 API接口

### 检索接口
```
POST /api/search
```

请求体：
```json
{
  "query": "深度学习图像识别",
  "top_k": 20,
  "filters": {
    "ipc_codes": ["G06K"],
    "applicant": "某某科技",
    "date_range": {
      "start": "2020-01-01",
      "end": "2023-12-31"
    }
  }
}
```

响应：
```json
{
  "results": [...],
  "query_time": 0.123,
  "total_results": 20,
  "sources": {
    "fulltext": 15,
    "vector": 12,
    "kg": 8
  }
}
```

### 系统状态
```
GET /api/stats
```

### 权重配置
```
POST /api/config/weights
```

请求体：
```json
{
  "fulltext": 0.4,
  "vector": 0.5,
  "kg": 0.1
}
```

### 监控指标
```
GET /api/monitoring/metrics
```

### WebSocket实时更新
```
ws://localhost:8000/ws
```

## 🎨 技术栈

### 前端
- **Vue 3**: 渐进式JavaScript框架
- **TypeScript**: 类型安全的JavaScript超集
- **Tailwind CSS**: 实用优先的CSS框架
- **Vue Router**: Vue.js官方路由
- **Pinia**: Vue的状态管理库
- **ECharts**: 可视化图表库
- **Axios**: HTTP客户端

### 后端
- **FastAPI**: 高性能Python Web框架
- **Uvicorn**: ASGI服务器
- **Pydantic**: 数据验证和设置管理
- **WebSocket**: 实时双向通信

## 📈 性能指标

- **响应时间**: <500ms (95%的请求)
- **缓存命中率**: >85%
- **并发支持**: 100+ 同时连接
- **检索召回率**: >95%

## 🔧 配置说明

### 检索权重配置

默认权重：
- BM25全文搜索: 40%
- 向量语义检索: 50%
- 知识图谱增强: 10%

可在配置页面实时调整权重，权重总和必须为1.0。

### 环境变量

后端服务支持以下环境变量：

```bash
# 数据库配置
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=patents
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

# Qdrant配置
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Neo4j配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

## 📝 开发指南

### 添加新组件

1. 在 `src/components/` 创建新组件
2. 在视图中引入和使用组件
3. 使用TypeScript类型定义Props

### 添加新API接口

1. 在 `src/api/client.ts` 添加新方法
2. 在 `src/types/index.ts` 定义类型
3. 在store中调用API方法

### 样式定制

编辑 `tailwind.config.js` 自定义主题颜色和样式。

## 🐛 故障排查

### 前端无法连接后端

检查：
1. 后端服务是否在 `http://localhost:8000` 运行
2. 查看浏览器控制台的错误信息
3. 检查 `vite.config.ts` 中的代理配置

### 检索返回空结果

检查：
1. 数据库连接是否正常
2. 索引是否已构建
3. 查询关键词是否合理

### WebSocket连接失败

检查：
1. 浏览器是否支持WebSocket
2. 网络连接是否正常
3. 后端WebSocket端口是否开放

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发规范
- 遵循Vue 3组合式API风格
- 使用TypeScript类型定义
- 遵循代码风格指南
- 添加必要的注释

## 📄 许可证

MIT License

---

**专利混合检索系统** - 让专利检索更智能！
