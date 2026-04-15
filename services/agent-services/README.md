# Agent Services

智能体服务集合，包含多个AI智能体核心功能。

## 包含的服务

### 1. xiao-nuo-control
小诺智能体控制系统
- 端口: 9002
- 功能: 小诺智能体的核心控制逻辑

### 2. unified-identity
统一身份认证服务
- 端口: 9003
- 功能: 跨服务身份认证和授权

### 3. vector_db
向量数据库服务
- 端口: 9004
- 功能: 高维向量存储和检索

### 4. vector-service
向量计算服务
- 端口: 9005
- 功能: 向量相似度计算和语义搜索

## 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 启动服务
```bash
# 启动所有服务
./start_all.sh

# 或单独启动
cd xiao-nuo-control && python main.py
cd unified-identity && python main.py
cd vector_db && python main.py
cd vector-service && python main.py
```

## 服务通信

服务间通过以下方式通信：
- HTTP API
- 共享Redis缓存
- 消息队列（规划中）

## 开发指南

每个服务都有独立的README和API文档。