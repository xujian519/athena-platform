# 部署指南：Athena Gateway 扩展（微服务自动注册与发现）

目标
- 将批量注册、服务发现、动态路由、健康检查、依赖关系管理集成到现有的 Athena Gateway。

前提
- 依赖 FastAPI，Python 3.8+、Uvicorn。
- 已有 athena_gateway 基础实现，以及示例服务（user_service、product_service）注册入口。

扩展接入步骤
