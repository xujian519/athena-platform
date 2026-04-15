# Tailscale集群部署方案

> **创建时间**: 2026-02-20 23:50
> **状态**: 待实施
> **优先级**: P2 (Gateway完善后实施)

---

## 📋 核心需求

### 目标1: 分散负载的Athena平台访问
- 其他电脑通过Tailscale使用Athena能力
- 避免M4 Pro过载，任务分散到各节点

### 目标2: OpenClaw作为任务路由器
- OpenClaw与Athena相对独立
- OpenClaw负责：收到审查意见 → 发送给负责的电脑 → 该电脑用Athena处理

### 目标3: 数据共享
- 任何节点都能访问专利数据库、法律世界模型

### 目标4: 简单可实施
- 可独立部署，不必过度复杂

---

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                      Tailscale 私有网络                         │
│              (所有设备可互相访问，使用 .ts.net 域名)            │
└─────────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┬──────────────────┐
        │                 │                 │                  │
   ┌────▼────┐     ┌──────▼──────┐   ┌────▼─────┐     ┌─────▼──────┐
   │Athena   │     │ OpenClaw    │   │ PostgreSQL│    │opencode    │
   │Gateway  │     │ Coordinator │   │  主库     │    │ 客户端群   │
   │M4 Air   │     │  M4 Air     │   │  M4 Pro   │    │  Windows   │
   │  :8005  │     │  :8888      │   │  :5432   │    │            │
   └────┬────┘     └──────┬──────┘   └──────────┘    └────────────┘
        │                 │
        │  协作(可选)      │  任务分发
        │                 │
        ▼                 ▼
   ┌─────────┐      ┌──────────┐
   │ 智能体  │      │ 任务队列  │
   │  技能   │      │ + 文档路由 │
   └─────────┘      └──────────┘
```

---

## 🖥️ 节点配置

| 节点 | 部署组件 | Tailscale域名 | 端口 | 职责 |
|------|---------|---------------|------|------|
| **M4 Air** | Gateway + 小诺 | `macbook-air-m4.ts.net` | 8005 | 协调、路由 |
| **M4 Pro** | 小娜 + 数据库 | `macbook-pro-m4.ts.net` | 8001, 5432 | 专利检索、数据 |
| **M1 Air** | OCR服务 | `macbook-air-m1.ts.net` | 8002 | 文档处理 |
| **Windows** | opencode客户端 | - | - | 案卷管理 |

---

## 🔧 实施配置

### Gateway配置（M4 Air）

```yaml
# config/production.yaml
server:
  port: 8005
  host: "0.0.0.0"  # 监听所有接口，包括Tailscale
  production: true

# 访问地址: http://macbook-air-m4.ts.net:8005
```

### 服务注册

```bash
GATEWAY="http://macbook-air-m4.ts.net:8005"

# 注册M4 Pro服务
curl -X POST $GATEWAY/api/services/batch_register -H "Content-Type: application/json" -d '{
  "services": [
    {"name": "xiaona", "host": "macbook-pro-m4.ts.net", "port": 8001},
    {"name": "database", "host": "macbook-pro-m4.ts.net", "port": 5432}
  ]
}'
```

### 路由配置

```bash
# 配置路由
curl -X POST $GATEWAY/api/routes -H "Content-Type: application/json" -d '{
  "path": "/api/legal/**",
  "target_service": "xiaona",
  "methods": ["GET", "POST"],
  "strip_prefix": true
}'
```

---

## 📅 实施计划

### Phase 1: Gateway + Tailscale（最小可用）

| 步骤 | 任务 | 预计时间 |
|------|------|----------|
| 1 | 所有设备安装Tailscale并登录 | 10分钟 |
| 2 | M4 Air部署Gateway，监听0.0.0.0:8005 | 5分钟 |
| 3 | M4 Pro部署小娜服务，监听0.0.0.0:8001 | 10分钟 |
| 4 | 配置Gateway服务注册和路由 | 10分钟 |
| 5 | Windows节点测试访问 | 5分钟 |

### Phase 2: OpenClaw集成（按需）

| 步骤 | 任务 | 预计时间 |
|------|------|----------|
| 1 | 部署OpenClaw Coordinator | 20分钟 |
| 2 | 配置任务分发规则 | 15分钟 |
| 3 | 创建Athena HTTP技能 | 10分钟 |

---

## 📝 备注

- 当前优先完成Athena统一网关的核心功能
- 本方案在Gateway完善后实施
- 保持简单实用原则，避免过度设计
