## API 文档与 GoDoc 完善清单

- 目标：为所有导出类型、函数、方法提供清晰的注释，提升自文档能力和外部集成的可用性。
- 范围：主要覆盖 api-gateway/internal/auth、internal/middleware、internal/handlers、pkg/server 等导出 API。 
- 实施要点：
  1. 为每个导出类型提供结构说明（字段含义、用途、生命周期）。
  2. 为每个导出函数/方法提供用途、参数、返回值、异常情况的说明。
  3. 使用 GoDoc 风格的注释，确保文档生成工具可直接抽取。
  4. 在 README 或 OpenAPI 草案中补充接口用途、鉴权要求、错误码等信息。
- 示例：
  - type Server struct { ... }
    // Server 封装了 HTTP 服务器、路由和中间件集合。
- 下一步：实现全量注释并启动文档生成流程，形成对外 API 文档。
