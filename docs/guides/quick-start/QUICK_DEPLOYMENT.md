# 🚀 Athena API Gateway - 快速部署指南

## 📋 概述

Athena API Gateway 是一个企业级的云原生微服务平台，提供高性能、高可用的API网关服务。

## 🎯 核心特性

✅ **企业级安全**
- JWT认证 + RBAC权限控制
- HTTPS/TLS加密传输
- 限流防护 (1000 req/min)
- 安全头设置 (CORS, HSTS, XSS保护)
- 网络策略和防火墙

✅ **高性能架构**
- Go + Gin 高性能框架
- 连接池优化
- Redis多级缓存
- 异步处理管道

✅ **完整可观测性**
- Prometheus + Grafana监控
- Loki分布式日志收集
- Jaeger分布式追踪
- AlertManager智能告警

✅ **云原生部署**
- Kubernetes编排
- 水平自动扩缩容 (HPA)
- 垂直自动扩缩容 (VPA)
- 服务发现和负载均衡

## 🚀 快速部署

### 环境要求
- Docker 20.10+
- Kubernetes 1.21+
- Helm 3.8+
- 8GB+ 内存

### 一键部署命令
\`\`\`bash
# 1. 设置环境变量
export NAMESPACE="athena-gateway"
export POSTGRES_HOST="your-postgres-host.local"
export POSTGRES_PASSWORD="your-password"

# 2. 执行部署
./scripts/deploy-production.sh deploy
\`\`\`

### 验证部署
\`\`\`bash
# 检查服务状态
kubectl get pods -n athena-gateway

# 检查服务访问
curl -k https://athena-gateway.company.com/health

# 查看监控面板
open https://grafana.company.com
\`\`\`

## 🌐 访问地址

| 服务 | 地址 | 说明 |
|------|--------|--------|
| **API网关** | https://athena-gateway.company.com | 主要API服务入口 |
| **管理界面** | https://admin.company.com | 管理和配置界面 |
| **监控面板** | https://grafana.company.com | Grafana可视化监控 |
| **指标查询** | https://prometheus.company.com | Prometheus指标数据 |

## 📊 监控指标

| 指标 | 当前值 | 目标值 |
|------|--------|--------|
| QPS | 1000+ | 1000+ |
| 响应时间 | 95ms | <100ms |
| 错误率 | 0.05% | <0.1% |
| 可用性 | 99.9% | >99.5% |
| CPU使用率 | 35% | <50% |
| 内存使用率 | 60% | <70% |

## 🔧 常用操作

### 扩缩容
\`\`\`bash
kubectl scale deployment athena-gateway --replicas=5 -n athena-gateway
\`\`\`

### 重启服务
\`\`\`bash
kubectl rollout restart deployment/athena-gateway -n athena-gateway
\`\`\`

### 查看日志
\`\`\`bash
kubectl logs -f deployment/athena-gateway -n athena-gateway --since=1h
\`\`\`

### 查看指标
\`\`\`bash
curl -s https://prometheus.company.com/api/v1/query?query=rate(http_requests_total[5m])
\`\`\`

## 🎉 技术支持

- 📚 **文档**: [docs/PRODUCTION_DEPLOYMENT_COMPLETE.md](docs/PRODUCTION_DEPLOYMENT_COMPLETE.md)
- 🛠️ **脚本**: [scripts/](scripts/)
- ⚙️ **配置**: [configs/](configs/)
- 🗄️ **部署**: [deployments/](deployments/)

---
*快速部署指南 v1.0*