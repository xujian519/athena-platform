# Athena工作平台生产环境部署指南

## 🎯 部署概述

### 系统要求

#### 硬件要求
- **Kubernetes集群**: v1.24+
- **节点数量**: 最少3个Worker节点
- **CPU总量**: 最少16核
- **内存总量**: 最少64GB
- **存储总量**: 最少500GB SSD
- **网络带宽**: 最少1Gbps

#### 软件要求
- **kubectl**: v1.24+
- **helm**: v3.8+
- **docker**: v20.10+
- **aws-cli**: v2.0+

#### 外部依赖
- **AWS EKS/GKE**: 托管Kubernetes集群
- **AWS RDS**: PostgreSQL数据库 (可选)
- **AWS ElastiCache**: Redis缓存 (可选)
- **AWS S3**: 对象存储
- **AWS Route53**: DNS服务

## 🚀 快速部署

### 1. 环境准备

```bash
# 克隆代码仓库
git clone https://github.com/athena-platform/athena-working-platform.git
cd athena-working-platform

# 检查kubectl连接
kubectl cluster-info

# 安装必要工具
# macOS
brew install kubectl helm

# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root kubectl /usr/local/bin/kubectl
```

### 2. 配置准备

```bash
# 创建密钥配置
cp production/k8s/secrets/production-secrets.yaml.template production/k8s/secrets/production-secrets.yaml

# 编辑密钥文件
vim production/k8s/secrets/production-secrets.yaml

# 验证配置
kubectl apply --dry-run=client -f production/k8s/secrets/production-secrets.yaml
```

### 3. 一键部署

```bash
# 执行部署脚本
./production/scripts/deploy.sh production

# 监控部署进度
watch kubectl get pods -n athena-production
```

## 📋 详细部署步骤

### 阶段1: 基础设施部署 (预计15分钟)

#### 1.1 创建命名空间
```bash
# 部署命名空间
kubectl apply -f production/k8s/namespaces/production-namespaces.yaml

# 验证命名空间
kubectl get namespaces | grep athena
```

#### 1.2 配置网络策略
```bash
# 部署网络策略
kubectl apply -f production/k8s/network-policies/production-network-policies.yaml

# 验证网络策略
kubectl get networkpolicies -n athena-production
```

#### 1.3 配置存储
```bash
# 创建PVC (如需要)
kubectl apply -f production/k8s/storage/storage-classes.yaml
kubectl apply -f production/k8s/storage/persistent-volumes.yaml

# 验证存储
kubectl get pvc -n athena-production
```

### 阶段2: 数据服务部署 (预计20分钟)

#### 2.1 部署PostgreSQL
```bash
# 部署数据库
kubectl apply -f production/k8s/deployments/production-deployments.yaml -l component=postgres
kubectl apply -f production/k8s/services/production-services.yaml -l component=postgres

# 等待数据库就绪
kubectl wait --for=condition=ready pod -l component=postgres -n athena-production --timeout=300s
```

#### 2.2 部署Redis
```bash
# 部署缓存
kubectl apply -f production/k8s/deployments/production-deployments.yaml -l component=redis
kubectl apply -f production/k8s/services/production-services.yaml -l component=redis

# 等待Redis就绪
kubectl wait --for=condition=ready pod -l component=redis -n athena-production --timeout=300s
```

#### 2.3 部署Qdrant
```bash
# 部署向量数据库
kubectl apply -f production/k8s/deployments/production-deployments.yaml -l component=qdrant
kubectl apply -f production/k8s/services/production-services.yaml -l component=qdrant

# 等待Qdrant就绪
kubectl wait --for=condition=ready pod -l component=qdrant -n athena-production --timeout=300s
```

#### 2.4 数据库初始化
```bash
# 运行数据库迁移
kubectl exec -it postgres-pod -n athena-production -- psql -U athena_user -d athena_prod -f /scripts/init-database.sql

# 验证数据库结构
kubectl exec -it postgres-pod -n athena-production -- psql -U athena_user -d athena_prod -c "\dt"
```

### 阶段3: 应用服务部署 (预计25分钟)

#### 3.1 部署Athena API
```bash
# 部署API服务
kubectl apply -f production/k8s/deployments/production-deployments.yaml -l component=api
kubectl apply -f production/k8s/services/production-services.yaml -l component=api

# 等待API就绪
kubectl wait --for=condition=available deployment/athena-api-deployment -n athena-production --timeout=600s
```

#### 3.2 部署Nginx Ingress
```bash
# 部署Ingress Controller (如未部署)
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install nginx-ingress ingress-nginx/ingress-nginx --namespace ingress-nginx

# 部署应用Ingress
kubectl apply -f production/k8s/ingress/production-ingress.yaml

# 等待Inress就绪
kubectl wait --for=condition=ready ingress --all -n athena-production --timeout=300s
```

#### 3.3 配置域名和证书
```bash
# 配置DNS记录
# 将 api.athena-patent.com 指向Ingress负载均衡器IP
# 将 app.athena-patent.com 指向Ingress负载均衡器IP

# 配置SSL证书
# 使用AWS ACM或Let's Encrypt配置证书
kubectl apply -f production/k8s/secrets/ssl-certs.yaml
```

### 阶段4: 监控系统部署 (预计20分钟)

#### 4.1 部署Prometheus
```bash
# 添加Prometheus Helm仓库
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# 部署Prometheus Stack
helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
  --namespace athena-monitoring \
  --create-namespace \
  --values production/monitoring/prometheus/values.yaml \
  --wait

# 验证Prometheus
kubectl get pods -n athena-monitoring -l app.kubernetes.io/name=prometheus
```

#### 4.2 部署Grafana
```bash
# Grafana已包含在Prometheus Stack中
# 导入仪表板配置
kubectl apply -f production/monitoring/grafana/dashboards.yaml

# 获取Grafana密码
kubectl get secret prometheus-grafana -n athena-monitoring -o jsonpath='{.data.admin-password}' | base64 -d
```

#### 4.3 配置告警
```bash
# 部署AlertManager配置
kubectl apply -f production/monitoring/alertmanager/config.yaml

# 配置Slack/Webhook通知
kubectl apply -f production/monitoring/alertmanager/secrets.yaml
```

## 🔍 部署验证

### 1. 基础验证

```bash
# 检查所有Pod状态
kubectl get pods -n athena-production

# 检查服务状态
kubectl get services -n athena-production

# 检查Ingress状态
kubectl get ingress -n athena-production

# 运行健康检查脚本
./production/scripts/health-check.sh production
```

### 2. 功能测试

```bash
# 测试API健康端点
curl -f https://api.athena-patent.com/health

# 测试API状态端点
curl -f https://api.athena-patent.com/api/v1/status

# 测试API文档
curl -f https://api.athena-patent.com/docs
```

### 3. 性能测试

```bash
# 运行负载测试
./production/scripts/load-test.sh --target=https://api.athena-patent.com --users=100 --duration=300

# 检查响应时间
./production/scripts/performance-test.sh

# 验证监控系统
curl -f http://monitoring.athena-patent.com/api/health
```

## 🔧 运维管理

### 1. 日常运维

#### 查看服务状态
```bash
# 查看所有服务状态
kubectl get all -n athena-production

# 查看资源使用
kubectl top nodes
kubectl top pods -n athena-production

# 查看事件
kubectl get events -n athena-production --sort-by='.lastTimestamp'
```

#### 日志管理
```bash
# 查看API日志
kubectl logs -f deployment/athena-api-deployment -n athena-production

# 查看数据库日志
kubectl logs -f deployment/postgres-deployment -n athena-production

# 查看特定时间段日志
kubectl logs deployment/athena-api-deployment -n athena-production --since=1h
```

#### 备份管理
```bash
# 手动触发备份
./production/scripts/backup-all.sh

# 查看备份状态
./production/scripts/backup-status.sh

# 恢复数据（如需要）
./production/scripts/restore.sh --type=postgres --backup=backup_20240220_120000.sql.gz
```

### 2. 故障排查

#### 常见问题解决

```bash
# Pod无法启动
kubectl describe pod <pod-name> -n athena-production
kubectl logs <pod-name> -n athena-production --previous

# 服务无法访问
kubectl get svc -n athena-production -o wide
kubectl describe svc <service-name> -n athena-production

# 网络问题
kubectl get networkpolicies -n athena-production
kubectl exec -it <pod-name> -n athena-production -- nslookup google.com
```

#### 性能问题排查

```bash
# 检查资源限制
kubectl describe pod <pod-name> -n athena-production | grep -A 5 Limits

# 检查节点资源
kubectl describe node <node-name>

# 分析慢查询
kubectl exec -it postgres-pod -n athena-production -- psql -U athena_user -d athena_prod -c "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

## 📊 监控和告警

### 1. 关键指标监控

#### 系统指标
- **CPU使用率**: < 80%
- **内存使用率**: < 85%
- **磁盘使用率**: < 90%
- **网络带宽**: 监控流量和延迟

#### 应用指标
- **API响应时间**: P95 < 2秒
- **错误率**: < 1%
- **请求量**: 监控并发和峰值
- **可用性**: > 99.9%

#### 业务指标
- **用户活跃数**: 实时监控
- **AI请求成功率**: > 95%
- **数据查询响应时间**: P95 < 5秒
- **向量搜索精度**: 监控搜索质量

### 2. 告警配置

#### 告警级别
- **Critical**: 立即响应 (1分钟内)
- **Warning**: 1小时内处理
- **Info**: 日度回顾

#### 告警渠道
- **Slack**: #athena-alerts
- **邮件**: ops-team@athena-patent.com
- **短信**: 紧急联系人
- **PagerDuty**: 值班工程师

## 🔄 升级和维护

### 1. 滚动升级

```bash
# 执行滚动升级
kubectl set image deployment/athena-api-deployment athena-api=athena-platform/api:v2.2.0 -n athena-production

# 监控升级进度
kubectl rollout status deployment/athena-api-deployment -n athena-production

# 回滚（如需要）
kubectl rollout undo deployment/athena-api-deployment -n athena-production
```

### 2. 蓝绿部署

```bash
# 使用ArgoCD进行蓝绿部署
kubectl argo rollouts set image athena-api athena-platform/api:v2.2.0 -n athena-production

# 切换流量
kubectl argo rollouts promote athena-api -n athena-production

# 清理旧版本
kubectl argo rollouts abort athena-api -n athena-production
```

## 📚 附录

### 1. 配置文件参考

#### 环境变量配置
```yaml
# production/config/production-env.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: athena-production-env
  namespace: athena-production
data:
  ATHENA_ENV: "production"
  LOG_LEVEL: "INFO"
  API_WORKERS: "4"
  DB_POOL_SIZE: "20"
  REDIS_POOL_SIZE: "50"
```

#### 资源限制配置
```yaml
# production/config/resource-limits.yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: athena-production-limits
  namespace: athena-production
spec:
  limits:
  - default:
      cpu: "1000m"
      memory: "2Gi"
    defaultRequest:
      cpu: "500m"
      memory: "1Gi"
    type: Container
```

### 2. 安全配置

#### 网络安全策略
```yaml
# 允许的最小端口范围
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: athena-production-network-policy
  namespace: athena-production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: athena-production
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
  - to: []
    ports:
    - protocol: TCP
      port: 443
    - protocol: TCP
      port: 80
```

#### RBAC权限配置
```yaml
# production/config/rbac.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: athena-production
  name: athena-api-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps"]
  verbs: ["get", "list", "watch"]
```

### 3. 联系和支持

#### 紧急联系
- **运维团队**: ops-team@athena-patent.com
- **技术负责人**: tech-lead@athena-patent.com
- **值班电话**: +1-XXX-XXX-XXXX
- **Slack频道**: #athena-ops

#### 文档和资源
- **API文档**: https://api.athena-patent.com/docs
- **监控面板**: https://monitoring.athena-patent.com
- **架构文档**: https://docs.athena-patent.com/architecture
- **故障处理手册**: https://docs.athena-patent.com/troubleshooting

---

**⚠️ 重要提醒**:
1. 首次部署前请务必备份数据
2. 生产环境部署建议在低峰期进行
3. 部署过程中请密切监控系统状态
4. 部署完成后请进行全面的功能测试
5. 定期检查和更新安全配置

---

*Athena工作平台生产环境部署指南 - 2026-02-20*