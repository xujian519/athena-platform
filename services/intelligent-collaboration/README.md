# intelligent-collaboration

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
docker build -t intelligent-collaboration .
docker run -p 8080:8080 intelligent-collaboration
```

## 联系方式
- 维护者：
- 邮箱：
