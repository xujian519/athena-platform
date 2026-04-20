#!/usr/bin/env python3
"""
创建标准化的服务模板
"""

import argparse
from pathlib import Path
from typing import Any


def create_python_service(service_name: str, path: Path) -> Any:
    """创建Python服务模板"""
    service_path = path / service_name
    service_path.mkdir(exist_ok=True)

    # 创建目录结构
    dirs = ["src", "config", "tests"]
    for d in dirs:
        (service_path / d).mkdir(exist_ok=True)
        if d == "src":
            (service_path / d / "__init__.py").touch()

    # 创建main.py
    main_py_content = f'''#!/usr/bin/env python3
"""
{service_name} - 服务描述
"""

import os
import logging
from core.logging_config import setup_logging
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title="{service_name}",
    description="服务描述",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置 - 从环境变量读取
from core.security.auth import ALLOWED_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=3600,
)

@app.get("/")
async def root():
    """根路径"""
    return {{
        "service": "{service_name}",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {{
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="127.0.0.1", port=port)  # 内网通信，通过Gateway访问
'''
    (service_path / "main.py").write_text(main_py_content)

    # 创建requirements.txt
    requirements_content = """# 服务依赖
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0
pydantic==2.5.0

# 开发依赖
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
"""
    (service_path / "requirements.txt").write_text(requirements_content)

    # 创建.env.example
    env_example = """# 服务配置
PORT=8080
LOG_LEVEL=INFO

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# API配置
API_HOST=0.0.0.0
API_RELOAD=false
"""
    (service_path / ".env.example").write_text(env_example)

    # 创建README.md
    readme_content = f"""# {service_name}

## 简介
服务描述

## 技术栈
- Python 3.11+
- FastAPI 0.104.1
- Uvicorn

## 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件设置配置
```

### 启动服务
```bash
python main.py
```

## API文档
- [Swagger UI](http://localhost:8080/docs)
- [ReDoc](http://localhost:8080/redoc)

## 健康检查
- GET /health

## 开发
### 运行测试
```bash
pytest
```

### 代码格式化
```bash
black .
```

## 部署
### Docker
```bash
docker build -t {service_name} .
docker run -p 8080:8080 {service_name}
```

## 联系方式
- 维护者：
- 邮箱：
"""
    (service_path / "README.md").write_text(readme_content)

    # 创建配置文件
    config_py_content = """# 配置管理
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    service_name: str = "default"
    port: int = 8080
    log_level: str = "INFO"
    database_url: str = "postgresql://localhost/db"

    class Config:
        env_file = ".env"

settings = Settings()
"""
    (service_path / "config" / "settings.py").write_text(config_py_content)

    # 创建Dockerfile
    dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY . .

# 暴露端口
EXPOSE 8080

# 运行服务
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
"""
    (service_path / "Dockerfile").write_text(dockerfile_content)

    # 创建.gitignore
    gitignore_content = """__pycache__/
*.py[cod]
*$py.class
.env
.venv
venv/
.env.local
.env.*.local
.DS_Store
.pytest_cache/
.coverage
htmlcov/
"""
    (service_path / ".gitignore").write_text(gitignore_content)

    # 创建测试文件
    test_content = """import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
"""
    (service_path / "tests" / "test_main.py").write_text(test_content)

    print(f"✅ Python服务 '{service_name}' 创建成功！")
    print(f"📍 路径: {service_path}")
    print("\n🚀 快速开始:")
    print(f"   cd {service_path}")
    print("   pip install -r requirements.txt")
    print("   python main.py")

def create_nodejs_service(service_name: str, path: Path) -> Any:
    """创建Node.js服务模板"""
    service_path = path / service_name
    service_path.mkdir(exist_ok=True)

    # 创建目录结构
    dirs = ["src", "tests"]
    for d in dirs:
        (service_path / d).mkdir(exist_ok=True)

    # 创建package.json
    package_json = f'''{{
  "name": "{service_name}",
  "version": "1.0.0",
  "description": "服务描述",
  "main": "main.js",
  "scripts": {{
    "start": "node main.js",
    "dev": "nodemon main.js",
    "test": "jest",
    "test:watch": "jest --watch"
  }},
  "dependencies": {{
    "express": "^4.18.2",
    "dotenv": "^16.3.1",
    "cors": "^2.8.5"
  }},
  "dev_dependencies": {{
    "jest": "^29.7.0",
    "supertest": "^6.3.3",
    "nodemon": "^3.0.2"
  }}
}}
'''
    (service_path / "package.json").write_text(package_json)

    # 创建main.js
    main_js_content = f'''/**
 * {service_name} - 服务描述
 */

const express = require('express');
const cors = require('cors');
const path = require('path');

// 加载环境变量
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 8080;

// 中间件
app.use(cors());
app.use(express.json());

// 根路径
app.get('/', (req, res) => {{
  res.json({{
    service: '{service_name}',
    status: 'running',
    version: '1.0.0',
    timestamp: new Date().to_isostring()
  }});
}});

// 健康检查
app.get('/health', (req, res) => {{
  res.json({{
    status: 'healthy',
    timestamp: new Date().to_isostring()
  }});
}});

// 启动服务
app.listen(PORT, () => {{
  console.log(`🚀 {service_name} 服务运行在端口 ${{PORT}}`);
}});
'''
    (service_path / "main.js").write_text(main_js_content)

    # 创建.env.example
    (service_path / ".env.example").write_text("""# 服务配置
PORT=8080
NODE_ENV=development

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
""")

    # 创建README.md（同Python版本，调整技术栈部分）
    readme_content = f"""# {service_name}

## 简介
服务描述

## 技术栈
- Node.js 18+
- Express 4.18
- JavaScript

## 快速开始

### 安装依赖
```bash
npm install
```

### 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件设置配置
```

### 启动服务
```bash
npm start

# 开发模式（自动重启）
npm run dev
```

## API文档
- 健康检查: GET /health

## 开发
### 运行测试
```bash
npm test
```

## 部署
### Docker
```bash
docker build -t {service_name} .
docker run -p 8080:8080 {service_name}
```

## 联系方式
- 维护者：
- 邮箱：
"""
    (service_path / "README.md").write_text(readme_content)

    # 创建其他必要文件...
    (service_path / ".gitignore").write_text("""node_modules/
.env
.env.local
.env.*.local
.DS_Store
coverage/
.nyc_output
""")

    print(f"✅ Node.js服务 '{service_name}' 创建成功！")
    print(f"📍 路径: {service_path}")
    print("\n🚀 快速开始:")
    print(f"   cd {service_path}")
    print("   npm install")
    print("   npm start")

def main() -> None:
    parser = argparse.ArgumentParser(description="创建标准化服务")
    parser.add_argument("name", help="服务名称")
    parser.add_argument("--type", choices=["python", "nodejs"], default="python", help="服务类型")
    parser.add_argument("--path", default="/Users/xujian/Athena工作平台/services", help="创建路径")

    args = parser.parse_args()

    base_path = Path(args.path)
    service_name = args.name.lower().replace(" ", "-")

    if args.type == "python":
        create_python_service(service_name, base_path)
    else:
        create_nodejs_service(service_name, base_path)

if __name__ == "__main__":
    main()
