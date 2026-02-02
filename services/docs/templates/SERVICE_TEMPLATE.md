# 服务标准化模板

## 📁 推荐的服务目录结构

### Python服务
```
service-name/
├── README.md              # 服务说明文档（必需）
├── requirements.txt       # Python依赖（必需）
├── main.py               # 主入口文件（必需）
├── config/               # 配置文件目录（可选）
│   ├── settings.py
│   └── config.yaml
├── src/                  # 源代码目录（可选）
│   ├── __init__.py
│   ├── api/
│   ├── models/
│   └── utils/
├── tests/                # 测试目录（可选）
│   └── test_main.py
├── Dockerfile            # Docker配置（推荐）
└── .env.example          # 环境变量示例（推荐）
```

### Node.js服务
```
service-name/
├── README.md              # 服务说明文档（必需）
├── package.json          # Node.js依赖（必需）
├── package-lock.json     # 锁定依赖版本（必需）
├── main.js               # 主入口文件（必需）
├── src/                  # 源代码目录（可选）
│   ├── api/
│   ├── models/
│   └── utils/
├── tests/                # 测试目录（可选）
│   └── main.test.js
├── Dockerfile            # Docker配置（推荐）
└── .env.example          # 环境变量示例（推荐）
```

## 📝 README.md 模板

```markdown
# 服务名称

## 简介
简要描述服务的功能和用途

## 技术栈
- 语言：Python 3.11+ / Node.js 18+
- 框架：FastAPI / Express
- 数据库：PostgreSQL / MongoDB

## 快速开始

### 安装依赖
```bash
# Python
pip install -r requirements.txt

# Node.js
npm install
```

### 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件
```

### 启动服务
```bash
# Python
python main.py

# Node.js
npm start
```

## API文档
- [Swagger UI](http://localhost:8080/docs)

## 配置说明
- PORT: 服务端口（默认：8080）
- LOG_LEVEL: 日志级别（DEBUG/INFO/WARN/ERROR）

## 开发指南
### 添加新功能
1. 在src/目录下添加新模块
2. 编写对应的测试
3. 更新API文档

### 运行测试
```bash
# Python
pytest

# Node.js
npm test
```

## 部署
### Docker
```bash
docker build -t service-name .
docker run -p 8080:8080 service-name
```

### Docker Compose
```yaml
version: '3.8'
services:
  service-name:
    build: .
    ports:
      - "8080:8080"
    environment:
      - NODE_ENV=production
```

## 监控
- 健康检查端点：GET /health
- 指标端点：GET /metrics

## 联系方式
- 维护者：xxx
- 邮箱：xxx@xxx.com
```

## 🔧 main.py 模板（Python FastAPI）

```python
#!/usr/bin/env python3
"""
服务名称 - 简要描述
"""

import os
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="服务名称",
    description="服务描述",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "服务名称",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

## ✅ 服务检查清单

### 必需项
- [ ] README.md 文档
- [ ] 主入口文件 (main.py/app.py/main.js)
- [ ] 依赖文件 (requirements.txt/package.json)
- [ ] 环境变量示例 (.env.example)

### 推荐项
- [ ] 源代码目录 (src/)
- [ ] 配置文件目录 (config/)
- [ ] 测试目录 (tests/)
- [ ] Dockerfile
- [ ] .gitignore

### 功能项
- [ ] 根路径处理 (/)
- [ ] 健康检查端点 (/health)
- [ ] 错误处理
- [ ] 日志记录
- [ ] API文档 (Swagger/OpenAPI)

### 安全项
- [ ] 环境变量配置
- [ ] CORS配置
- [ ] 输入验证
- [ ] 错误信息安全

## 🎯 一致性建议

1. **命名规范**
   - 目录：小写字母和连字符 (service-name)
   - 文件：小写字母和下划线 (service_name.py)
   - 类名：大驼峰 (ServiceName)

2. **端口分配**
   - API网关: 8080
   - AI服务: 9000-9099
   - 数据服务: 9100-9199
   - 工具服务: 9200-9299
   - 其他: 9300-9399

3. **日志规范**
   - 使用结构化日志
   - 包含请求ID
   - 统一时间格式 (ISO 8601)
   - 合适的日志级别

4. **配置管理**
   - 使用环境变量
   - 提供默认值
   - 敏感信息加密
   - 配置验证

## 📚 参考资源
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [Express.js文档](https://expressjs.com/)
- [Docker最佳实践](https://docs.docker.com/develop/dev-best-practices/)
- [12 Factor App](https://12factor.net/)