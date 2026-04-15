# Athena Platform

**服务类型**: Python FastAPI
**版本**: 1.0.0
**端口**: 8000

## 简介

Athena平台是智能工作平台的核心管理系统，提供统一的平台管理、服务协调和基础功能支持。

## 技术栈

- Python 3.11+
- FastAPI 0.104.1
- Uvicorn
- Pydantic
- Loguru

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件设置配置
```

### 3. 启动服务

```bash
python main.py
```

服务将在 `http://localhost:8000` 启动

## API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 主要功能

- 平台状态监控
- 服务管理
- 配置管理
- 用户认证
- 系统集成

## 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| DEBUG | false | 调试模式 |
| PORT | 8000 | 服务端口 |
| LOG_LEVEL | INFO | 日志级别 |
| DATABASE_URL | - | 数据库连接 |

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
docker build -t athena-platform .
docker run -p 8000:8000 athena-platform
```

## 联系方式

- 维护者：Athena开发团队