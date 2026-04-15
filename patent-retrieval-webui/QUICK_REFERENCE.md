# 专利混合检索系统 - 快速参考

## 🚀 快速启动

```bash
# 一键启动
cd patent-retrieval-webui && ./start.sh

# 访问
# 前端: http://localhost:3000
# 后端: http://localhost:8000
# 文档: http://localhost:8000/docs
```

## 📦 常用命令

### 前端
```bash
npm run dev        # 开发服务器
npm run build      # 构建生产版本
npm run preview    # 预览构建
npm run lint       # 代码检查
npm run typecheck  # 类型检查
```

### 后端
```bash
cd backend
./start_server.sh  # 启动服务
python api_server.py  # 直接运行
uvicorn api_server:app --reload  # 热重载
```

### Docker
```bash
docker-compose up -d    # 启动服务
docker-compose down     # 停止服务
docker-compose logs -f  # 查看日志
```

## 🔗 重要链接

| 链接 | 地址 |
|------|------|
| 前端 | http://localhost:3000 |
| 后端API | http://localhost:8000 |
| API文档 | http://localhost:8000/docs |
| 搜索 | http://localhost:3000/ |
| 历史 | http://localhost:3000/history |
| 配置 | http://localhost:3000/config |
| 监控 | http://localhost:3000/monitoring |

## 🎨 默认权重配置

```json
{
  "fulltext": 0.4,  // BM25全文搜索 40%
  "vector": 0.5,   // 向量语义检索 50%
  "kg": 0.1        // 知识图谱增强 10%
}
```

## 📁 关键文件

| 文件 | 说明 |
|------|------|
| `src/main.ts` | 前端入口 |
| `src/App.vue` | 根组件 |
| `backend/api_server.py` | 后端服务器 |
| `package.json` | 前端依赖 |
| `backend/requirements.txt` | 后端依赖 |
| `vite.config.ts` | Vite配置 |
| `tailwind.config.js` | Tailwind配置 |

## 🔧 常见配置

### 修改端口
```typescript
// vite.config.ts
server: { port: 3001 }

// backend/api_server.py
uvicorn.run(app, port=8001)
```

### 修改主题颜色
```javascript
// tailwind.config.js
colors: {
  primary: { 500: '#your-color' }
}
```

### 环境变量
```bash
# 前端 .env
VITE_API_BASE_URL=http://localhost:8000

# 后端 .env
DATABASE_URL=postgresql://user:pass@localhost:5432/db
```

## 🐛 故障排查

### 前端问题
```bash
# 清除缓存
rm -rf node_modules dist
npm install

# 检查端口
lsof -i :3000
```

### 后端问题
```bash
# 查看日志
tail -f /var/log/patent-retrieval/api.log

# 检查数据库
psql -U user -d patents -h localhost
```

### Docker问题
```bash
# 重建容器
docker-compose down
docker-compose build
docker-compose up -d

# 查看日志
docker-compose logs -f backend
```

## 📊 性能指标

| 指标 | 值 |
|------|-----|
| 响应时间 | <500ms |
| 缓存命中率 | >85% |
| 并发连接 | 100+ |
| 页面加载 | <2s |

## 🎯 功能快捷方式

### 检索
```
输入查询 → [开始检索] → 查看结果
```

### 权重调整
```
配置页 → 拖动滑块 → [保存配置]
```

### 历史回放
```
历史页 → 点击记录 → 重新检索
```

### 监控查看
```
监控页 → 实时数据 → 自动刷新
```

## 📞 获取帮助

| 问题 | 解决方案 |
|------|----------|
| 启动失败 | 查看文档/使用说明.md |
| 代码问题 | 查看文档/开发指南.md |
| 部署问题 | 查看文档/部署指南.md |
| 其他问题 | 查看文档/快速启动.md |

## 🔍 API端点

```
POST   /api/search              # 执行检索
GET    /api/stats               # 系统统计
GET    /api/patents/{id}        # 专利详情
POST   /api/config/weights      # 更新权重
GET    /api/monitoring/metrics  # 监控指标
WS     /api/ws                  # WebSocket
```

## 💡 开发技巧

### 添加新组件
```bash
# 1. 创建组件
touch src/components/NewComponent.vue

# 2. 在视图使用
import NewComponent from '@/components/NewComponent.vue';
```

### 添加新API
```typescript
// 1. 定义类型
// src/types/index.ts

// 2. 添加方法
// src/api/client.ts

// 3. Store调用
// src/stores/yourStore.ts
```

### 样式开发
```vue
<!-- Tailwind CSS -->
<div class="bg-white p-4 rounded-lg hover:bg-gray-100">
```

---

**祝使用愉快！** 🎉
