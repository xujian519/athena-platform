# Athena Agent Marketplace

Athena平台Agent市场的Vue.js前端应用。

## 技术栈

- Vue 3 - 渐进式JavaScript框架
- Vue Router 4 - 路由管理
- Pinia - 状态管理
- Axios - HTTP客户端
- Vite - 构建工具

## 项目结构

```
src/
├── api/           # API客户端
├── assets/        # 静态资源
├── components/    # Vue组件
├── router/        # 路由配置
├── stores/        # Pinia状态管理
├── views/         # 页面组件
├── App.vue        # 根组件
├── main.js        # 应用入口
└── style.css      # 全局样式
```

## 开发

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

## API配置

开发环境下，API请求会被代理到后端服务器（默认 http://localhost:8001）。

## 功能

- Agent列表浏览
- Agent详情查看
- Agent发布
- 分类筛选
- 搜索功能
