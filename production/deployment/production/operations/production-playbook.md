# 小诺总控平台生产环境运维手册

## 📋 目录
- [环境架构](#环境架构)
- [部署指南](#部署指南)
- [日常运维](#日常运维)
- [故障处理](#故障处理)
- [监控告警](#监控告警)
- [备份恢复](#备份恢复)
- [升级维护](#升级维护)
- [安全运维](#安全运维)

---

## 🏗️ 环境架构

### 生产环境架构概览
```
┌─────────────────────────────────────────────────────────────┐
│                    Production Environment                 │
├─────────────────────────────────────────────────────────────┤
│  Load Balancer (Nginx/HAProxy)                                │
│         ↓                                                        │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │
│  │ Ingress     │    │   Control   │    │   Business  │       │
│  │ Controller  │◄──►│    Center   │◄──►│   Services  │       │
│  └─────────────┘    └─────────────┘    └─────────────┘       │
│         │                    │                    │       │
│         ▼                    ▼                    │       │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 Kubernetes Cluster                     │ │
│  │                                                         │ │
│  │ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │ │
│  │ │ Master Nodes  │  │ Worker Nodes │  │Storage     │   │ │
│  │ │   (3+)       │  │   (5+)      │  │ Clusters    │   │ │
│  │ └─────────────┘  └─────────────┘  └─────────────┘   │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 组件清单
| 组件类别 | 组件名称 | 版本 | 实例数 | 功能 |
|----------|----------|------|--------|------|
| **负载均衡** | Nginx/HAProxy | 1.21+ | 2+ | 流量分发 |
| **容器编排** | Kubernetes | 1.28+ | 8+ | 集群管理 |
| **控制中心** | Xiaonuo API | v1.0.0 | 3+ | 核心服务 |
| **智能预测** | AI Predictor | v1.0.0 | 2+ | 智能分析 |
| **业务服务** | Patents/Legal/Media | v1.0.0 | 按需 | AI代理服务 |
| **监控** | Prometheus | 2.45+ | 1 | 指标收集 |
| **可视化** | Grafana | 9.5+ | 1 | 仪表板 |
| **告警** | AlertManager | 0.25+ | 1 | 告警通知 |
| **日志** | ELK Stack | 8.8+ | 3+ | 日志管理 |
| **存储** | PostgreSQL | 15+ | 2+ | 数据存储 |
| **缓存** | Redis Cluster | 7.0+ | 3+ | 缓存服务 |
| **向量DB** | Qdrant | 1.7+ | 1+ | 向量搜索 |

---

## 🚀 部署指南

### 1. 环境准备

#### 1.1 硬件要求
```yaml
Master节点 (3台):
  CPU: 4核心
  内存: 8GB
  存储: 100GB SSD
  网络: 千兆网卡

Worker节点 (5台):
  CPU: 8核心
  内存: 16GB
  存储: 200GB SSD
  网络: 千兆网卡

存储节点 (可选):
  CPU: 4核心
  内存: 16GB
  存储: 2TB+ NVMe
  网络: 千兆网卡

网络要求:
  内网带宽: 万兆交换机
  外网带宽: 100Mbps+
  VPN接入: 专线或IPSec
```

#### 1.2 软件依赖
```bash
# Kubernetes 1.28+
kubectl version --client
kubectl version --short

# Docker 20.10+
docker --version

# Helm 3.12+
helm version

# kubeadm 1.28+
kubeadm version
```

### 2. 集群部署

#### 2.1 集群初始化
```bash
# 1. 部署Master节点
kubeadm init --config=kubeadm-config.yaml

# 2. 配置kubectl
mkdir -p $HOME/.kube
sudo cp -i /etc/infrastructure/infrastructure/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# 3. 安装网络插件 (Calico)
kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml

# 4. 加入Worker节点
kubeadm join <master-ip>:<port> --token <token> --discovery-token-ca-cert-hash <hash>
```

#### 2.2 存储配置
```yaml
# Longhorn部署
helm repo add longhorn https://charts.longhorn.io
helm repo update

helm install longhorn longhorn/longhorn \
  --namespace longhorn-system \
  --set defaultSettings.defaultReplicaCount=3 \
  --set defaultSettings.defaultLonghornStaticStorageClass=true

# 或使用Rook Ceph
kubectl apply -f rook/cluster.yaml
kubectl apply -f rook/ceph/cluster.yaml
```

### 3. 应用部署

#### 3.1 命名空间创建
```bash
kubectl apply -f infrastructure/deployment/production/k8s/namespace.yaml
```

#### 3.2 密钥管理
```bash
# 创建TLS证书
kubectl create secret generic athena-secrets \
  --from-literal=jwt-secret=$(openssl rand -hex 32) \
  --from-literal=database-url="postgresql://user:pass@postgres:5432/athena" \
  --from-literal=redis-url="redis://redis-cluster:6379/0" \
  --namespace athena-control-center
```

#### 3.3 核心服务部署
```bash
# 部署控制中心
kubectl apply -f infrastructure/deployment/production/k8s/control-center-deployment.yaml

# 部署业务服务
kubectl apply -f infrastructure/deployment/production/k8s/business-services.yaml

# 部署监控系统
kubectl apply -f infrastructure/deployment/production/infrastructure/infrastructure/monitoring/
```

#### 3.4 Ingress配置
```bash
# 安装NGINX Ingress Controller
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm install ingress-nginx ingress-infrastructure/nginx/ingress-nginx \
  --namespace ingress-nginx \
  --set controller.replicaCount=2 \
  --set controller.nodeSelector."kubernetes.io/os"=linux \
  --set defaultBackend.enabled=true
```

### 4. 验证部署

#### 4.1 集群状态检查
```bash
# 检查节点状态
kubectl get nodes -o wide

# 检查Pod状态
kubectl get pods --all-namespaces

# 检查服务状态
kubectl get svc --all-namespaces

# 检查Ingress
kubectl get ingress --all-namespaces
```

#### 4.2 服务连通性测试
```bash
# 测试控制中心API
kubectl port-forward svc/xiaonuo-control-center-service 9002:9002 -n athena-control-center
curl http://localhost:9002/health

# 测试业务服务
kubectl port-forward svc/xiaona-patent-service 8010:8010 -n athena-services
curl http://localhost:8010/health
```

---

## 🔧 日常运维

### 1. 健康检查

#### 1.1 自动化健康检查脚本
```bash
#!/bin/bash
# health-check.sh

echo "🔍 系统健康检查 - $(date)"

# 1. 检查集群状态
echo -e "\n📊 Kubernetes集群状态:"
kubectl get nodes | grep -E "(Ready|NotReady|SchedulingDisabled)"

# 2. 检查Pod状态
echo -e "\n🚀 Pod状态统计:"
kubectl get pods --all-namespaces | awk 'NR>1{print $3}' | sort | uniq -c

# 3. 检查服务健康
echo -e "\n💚 服务健康状态:"
for namespace in athena-control-center athena-services athena-monitoring; do
  services=$(kubectl get svc -n $namespace -o jsonpath='{.items[*].metadata.name}')
  for service in $services; do
    if kubectl get pods -n $namespace -l app=control-center-api -o name | head -1 | grep -q "Running"; then
      status="✅"
    else
      status="❌"
    fi
    echo "  $namespace/$service: $status"
  done
done

# 4. 检查资源使用
echo -e "\n📈 资源使用情况:"
kubectl top nodes | head -n 10

# 5. 检查存储使用
echo -e "\n💾 存储使用情况:"
kubectl get pvc --all-namespaces
```

#### 1.2 服务专项检查
```bash
# 控制中心服务检查
kubectl get pods -n athena-control-center -l app=xiaonuo-control-center -o wide

# 业务服务检查
kubectl get pods -n athena-services -l scenario --show-labels

# AI服务状态检查
kubectl get pods -l ai-agent -o custom-columns='NAME:.metadata.name,AI_AGENT:.metadata.labels.ai-agent,STATUS:.status.phase'

# 场景切换日志检查
kubectl logs -n athena-control-center -l app=xiaonuo-control-center --tail=100 | grep -i "scenario"
```

### 2. 场景管理

#### 2.1 场景切换操作
```bash
#!/bin/bash
# scenario-manager.sh

SCENARIO=$1
FORCE=${2:-false}

if [ -z "$SCENARIO" ]; then
    echo "用法: $0 <场景名> [force]"
    echo "可用场景:"
    echo "  - patent-legal (专利法律服务)"
    echo "  - baochen-business (宝宸公司事务)"
    echo "  - media-operations (自媒体运营)"
    echo "  - general-platform (通用平台)"
    exit 1
fi

echo "🔄 切换到场景: $SCENARIO"

# 场景切换API调用
FORCE_PARAM=""
if [ "$FORCE" = "true" ]; then
    FORCE_PARAM='{"force": true}'
fi

curl -X POST "http://xiaonuo-control-center-service.athena-control-center.svc.cluster.local:9002/api/v1/scenarios/switch" \
  -H "Content-Type: application/json" \
  -d "{\"scenario\": \"$SCENARIO\", $FORCE_PARAM}"

echo "✅ 场景切换请求已发送"

# 等待切换完成
sleep 10

# 检查切换结果
curl -s "http://xiaonuo-control-center-service.athena-control-center.svc.cluster.local:9002/api/v1/scenarios/current" | jq '.data'
```

#### 2.2 场景自动调度
```yaml
# 基于时间的自动调度规则
# 每天定时任务配置
apiVersion: batch/v1
kind: CronJob
metadata:
  name: auto-scenario-scheduler
  namespace: athena-control-center
spec:
  schedule: "0 9 * * *"  # 每天上午9点
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: scenario-switcher
            image: curlimages/curl:7.85.0
            command:
            - /bin/sh
            - -c
            - |
              # 根据工作日自动选择场景
              DAY_OF_WEEK=$(date +%u)
              if [ $DAY_OF_WEEK -eq 1 ]; then
                SCENARIO="patent-legal"
              elif [ $DAY_OF_WEEK -le 5 ]; then
                SCENARIO="baochen-business"
              else
                SCENARIO="general-platform"
              fi

              curl -X POST "http://xiaonuo-control-center-service.athena-control-center.svc.cluster.local:9002/api/v1/scenarios/switch" \
                -H "Content-Type: application/json" \
                -d "{\"scenario\": \"$SCENARIO\"}"
          restartPolicy: OnFailure
```

### 3. 资源监控

#### 3.1 资源使用监控
```bash
#!/bin/bash
# resource-monitor.sh

echo "📊 资源监控报告 - $(date)"

# 1. 集群资源概览
echo -e "\n🏗️ 集群资源:"
kubectl top nodes

# 2. 命名空间资源使用
echo -e "\n📋 命名空间资源使用:"
kubectl top pods -n athena-control-center --containers=true
kubectl top pods -n athena-services --containers=true

# 3. 存储使用情况
echo -e "\n💾 存储使用情况:"
kubectl get pv --all-namespaces
kubectl get pvc --all-namespaces

# 4. 网络流量
echo -e "\l🌐 网络流量统计:"
kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.metadata.name}{"range .spec.containers[*]}{.name}{"end"}}' | xargs -I {} sh -c 'kubectl exec {} -n $(kubectl get pod {} -o jsonpath='{.metadata.namespace}' | tr -d \'"\') -- netstat -i 2>/dev/null | grep ESTABLISHED | wc -l'

# 5. 资源配额使用
echo -e "\n⚖️ 资源配额:"
kubectl describe quota
```

#### 3.2 性能指标分析
```bash
# 获取实时性能数据
curl -s "http://prometheus.athena-monitoring.svc.cluster.local:9090/api/v1/query_range" \
  -d '{
    "start": "'$(date -d '5 minutes ago' --iso-8601)'",
    "end": "'$(date --iso-8601)'",
    "queries": [
      {
        "metric": "rate(http_requests_total[5m])",
        "step": "30s"
      },
      {
        "metric": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
        "step": "30s"
      },
      {
        "metric": "sum(container_memory_usage_bytes)",
        "step": "30s"
      }
    ]
  }' | python3 -m json.tool
```

### 4. 日志管理

#### 4.1 日志收集配置
```yaml
# Filebeat配置
apiVersion: v1
kind: ConfigMap
metadata:
  name: filebeat-config
  namespace: athena-monitoring
data:
  filebeat.yml: |
    filebeat.inputs:
    - type: container
      paths:
        - /var/log/containers/*.log
      processors:
        - add_kubernetes_metadata:
            host: ${NODE_NAME}
            matchers:
            - logs_path:
                info: /var/log/containers/*${data.kubernetes.container.name}*.log
            - labels:
              info: /var/log/containers/*${data.kubernetes.container.name}*.log

    output.elasticsearch:
      hosts: ["elasticsearch.athena-monitoring.svc.cluster.local:9200"]
      index: "athena-logs-%{+yyyy.MM.dd}"
      template.pattern: "athena-logs-%{+yyyy.MM.dd}-%{+HH.mm}"
```

#### 4.2 日志查询分析
```bash
# 分析控制中心日志
kubectl logs -n athena-control-center -l app=xiaonuo-control-center --tail=100 | \
  grep -E "(scenario|switch|prediction|error|warning)"

# 分析业务服务日志
kubectl logs -n athena-services -l ai-agent=xiaona --tail=50 | \
  grep -E "(patent|legal|analysis|success|error)"

# 查看系统事件
kubectl get events --all-namespaces --sort-by='.lastTimestamp' --field-selector='type!=Normal'

# 错误日志分析
kubectl logs --all-namespaces --tail=200 | grep -i "error\|exception\|failed" | tail -20
```

---

## 🚨 故障处理

### 1. 常见故障诊断

#### 1.1 Pod启动失败
```bash
# 诊断Pod启动问题
kubectl describe pod <pod-name> -n <namespace>

# 查看Pod事件
kubectl get events --field-selector=involvedObject.name=<pod-name> -n <namespace>

# 查看Pod日志
kubectl logs <pod-name> -n <namespace> --previous

# 进入Pod调试
kubectl exec -it <pod-name> -n <namespace> -- /bin/bash
```

#### 1.2 网络连接问题
```bash
# 检查网络策略
kubectl get networkpolicy --all-namespaces

# 测试服务连通性
kubectl exec -it $(kubectl get pod -l app=control-center-api -n athena-control-center -o jsonpath='{.items[0].metadata.name}') \
  -n athena-control-center -- curl -v http://localhost:9002/health

# 检查DNS解析
kubectl exec -it $(kubectl get pod -l app=control-center-api -n athena-control-center -o jsonpath='{.items[0].metadata.name}') \
  -n athena-control-center -- nslookup xiaonuo-control-center-service.athena-control-center.svc.cluster.local

# 检查负载均衡器
kubectl get svc --all-namespaces
kubectl get ingress --all-namespaces
```

#### 1.3 存储问题
```bash
# 检查PVC状态
kubectl get pvc --all-namespaces

# 检查存储类
kubectl get storageclass

# 检查挂载点
kubectl exec -it $(kubectl get pod -l app=xiaona-patent-service -n athena-services -o jsonpath='{.items[0].metadata.name}') \
  -n athena-services -- df -h

# 清理僵尸卷
kubectl get pvc --all-namespaces -o jsonpath='{.items[?(@.status.phase=="Lost")].metadata.name}'
```

### 2. 紧急响应流程

#### 2.1 服务故障响应
```yaml
# 故障响应等级
CRITICAL: 5分钟内响应
WARNING: 15分钟内响应
INFO: 2小时内响应

# 响应时间要求
场景切换失败: 1分钟内恢复
服务完全不可用: 5分钟内恢复
部分功能异常: 30分钟内恢复
性能下降50%: 15分钟内恢复
```

#### 2.2 故障恢复程序
```bash
#!/bin/bash
# emergency-recovery.sh

FAILURE_TYPE=$1
SERVICE_NAME=$2

echo "🚨 紧急恢复程序启动 - $(date)"
echo "故障类型: $FAILURE_TYPE"
echo "服务名称: $SERVICE_NAME"

case $FAILURE_TYPE in
    "service_down")
        echo "🔄 启动服务恢复流程..."

        # 1. 立即重启故障Pod
        kubectl delete pod -l app=$SERVICE_NAME -n athena-services
        kubectl rollout status infrastructure/deployment/$SERVICE_NAME -n athenen-services

        # 2. 检查资源使用
        kubectl top pods -n athena-services

        # 3. 检查依赖服务
        echo "检查依赖服务状态..."
        ;;

    "high_load")
        echo "📈 高负载恢复流程..."

        # 1. 立即扩容
        kubectl scale deployment $SERVICE_NAME --replicas=6 -n athena-services

        # 2. 监控资源使用
        while true; do
            CPU=$(kubectl top pods -l app=$SERVICE_NAME -n athena-services --no-headers | awk '{sum+=$3} END {print}' | tail -1)
            if [ $CPU -lt 200 ]; then
                echo "CPU使用已降至安全水平: $CPU%"
                break
            fi
            sleep 30
        done

        # 3. 逐步缩容
        kubectl scale deployment $SERVICE_NAME --replicas=3 -n athena-services
        ;;

    "storage_issue")
        echo "💾 存储问题恢复流程..."

        # 1. 检查存储状态
        kubectl get pvc --all-namespaces

        # 2. 清理临时文件
        kubectl exec -it $(kubectl get pod -l app=$SERVICE_NAME -n athena-services -o jsonpath='{.items[0].metadata.name}') \
            -n athena-services -- find /tmp -name "*.tmp" -delete

        # 3. 重启服务
        kubectl rollout restart infrastructure/deployment/$SERVICE_NAME -n athena-services
        ;;
esac

echo "✅ 紧急恢复完成"
```

### 3. 事后分析

#### 3.1 故障报告模板
```markdown
# 故障报告

## 基本信息
- **故障时间**: 2025-01-XX XX:XX:XX
- **故障服务**: [服务名称]
- **故障类型**: [故障类型]
- **影响范围**: [影响范围]
- **恢复时间**: XX分钟

## 故障描述
### 症状描述
[详细描述故障现象]

### 错误日志
```
[相关错误日志]
```

## 根本原因分析
### 直接原因
[直接原因分析]

### 间接原因
[间接原因分析]

### 相关因素
[其他可能的影响因素]

## 处理过程
### 发现时间
XX:XX:XX

### 处理措施
1. [处理步骤1]
2. [处理步骤2]
3. [处理步骤3]

### 恢复时间
XX:XX:XX

## 预防措施
### 短期措施
1. [预防措施1]
2. [预防措施2]
3. [预防措施3]

### 长期措施
1. [改进计划1]
2. [改进计划2]
3. [改进计划3]

## 经验教训
1. [教训1]
2. [教训2]
3. [教训3]

## 附录
- 相关链接: [相关文档链接]
- 参考资料: [参考资料]
```

#### 3.2 持续改进机制
```bash
# 定期系统健康检查
0 6 * * * /path/to/health-check.sh
0 0 * * 0 /path/to/cleanup-temp-files.sh

# 月度性能优化
0 0 1 1 * /path/to/performance-optimization.sh

# 季度演练
0 0 1 1 * /path/to/disaster-recovery-drill.sh
```

---

## 📊 监控告警

### 1. 监控指标体系

#### 1.1 系统级指标
```yaml
基础设施监控:
  - 集群健康度
  - 节点状态
  - 网络延迟
  - 存储使用率

应用性能监控:
  - API响应时间
  - 错误率
  - 吞吐量
  - 并发用户数

业务指标监控:
  - 场景切换成功率
  - AI预测准确率
  - 服务可用时间
  - 用户满意度
```

#### 1.2 告警规则配置
```yaml
# 关键告警规则
高优先级 (Critical):
  - 服务完全不可用
  - 数据丢失风险
  - 安全事件
  - 系统过载

中优先级 (Warning):
  - 性能下降50%+
  - 磁盘使用率>90%
  - 内存使用率>85%
  - 场景切换失败

低优先级 (Info):
  - 配置变更
  - 资源使用趋势
  - 预测准确率下降
```

### 2. 告警通知配置

#### 2.1 通知渠道配置
```yaml
# 通知渠道配置
紧急通知:
  - 钉群: @oncall-team
  - 邮件: oncall@athena-platform.com
  - 电话: 自动语音通知
  - 短信: 自动短信通知

常规通知:
  - 钉群: @ops-team
  - 邮件: ops@athena-platform.com
  - 钉钉: 企业微信群通知

信息通知:
  - 钉群: @all-team
  - 邮件: all@athena-platform.com
```

#### 2.2 告警内容模板
```json
{
  "title": "🚨 ATHENA平台告警",
  "severity": "critical",
  "timestamp": "2025-01-XXTXX:XX:XX",
  "alert_name": "ServiceDown",
  "service": "xiaonuo-control-center",
  "namespace": "athena-control-center",
  "message": "控制中心API服务不可用",
  "description": "在过去5分钟内，控制中心API服务无法访问",
  "current_status": {
    "total_services": 10,
    "running_services": 7,
    "failed_services": 3,
    "recovery_actions": []
  },
  "recommended_actions": [
    "检查Pod状态: kubectl get pods -n athena-control-center",
    "查看服务日志: kubectl logs -l app=xiaonuo-control-center",
    "检查资源使用: kubectl top pods -n athena-control-center"
  ],
  "contact": {
    "oncall": "+86-138-0013-8000",
    "email": "oncall@athena-platform.com",
    "slack": "#athena-critical"
  }
}
```

### 3. 监控仪表板

#### 3.1 Grafana仪表板配置
```json
{
  "dashboard": {
    "title": "Athena平台监控仪表板",
    "panels": [
      {
        "title": "服务健康状态",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(up{namespace=~\"athena-\"})",
            "legendFormat": "运行中"
          }
        ]
      },
      {
        "title": "场景切换成功率",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(scenario_switch_success_total[1h])) / sum(rate(scenario_switch_total[1h])) * 100",
            "legendFormat": "成功率"
          }
        ]
      },
      {
        "title": "AI预测准确率",
        "type": "graph",
        "targets": [
          {
            "expr": "ai_prediction_accuracy",
            "legendFormat": "预测准确率"
          }
        ]
      },
      {
        "title": "资源使用趋势",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(container_memory_usage_bytes{namespace=~\"athena-\"}) / 1024 / 1024",
            "legendFormat": "内存使用(GB)"
          }
        ]
      },
      {
        "title": "API响应时间",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95%分位响应时间"
          }
        ]
      },
      {
        "title": "错误率趋势",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
            "legendFormat": "5xx错误率"
          }
        ]
      }
    ]
  }
}
```

#### 3.2 告警仪表板
```json
{
  "dashboard": {
    "title": "Athena告警监控仪表板",
    "panels": [
      {
        "title": "活跃告警数量",
        "type": "stat",
        "targets": [
          {
            "expr": "alertmanager_alerts_active",
            "legendFormat": "活跃告警"
          }
        ]
      },
      {
        "title": "告警级别分布",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum by (severity) (alertmanager_alerts_active)",
            "legendFormat": "{{severity}}"
          }
        ]
      },
      {
        "title": "告警处理时间",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(alertmanager_notifications_sent_total[5m])",
            "legendFormat": "通知发送率"
          }
        ]
      }
    ]
  }
}
```

---

## 💾 备份恢复

### 1. 数据备份策略

#### 1.1 备份配置
```yaml
# 备份策略配置
数据备份:
  - 数据库备份: 每日全量 + 每小时增量
  - 配置备份: 每次变更后
  - 镜像备份: 每周定期
  - 日志备份: 每7天轮换

备份存储:
  - 本地存储: 热备份 + 增量备份
  - 远程存储: 异地备份 (对象存储)
  - 备份保留: 30天本地 + 90天远程
```

#### 1.2 自动化备份脚本
```bash
#!/bin/bash
# backup-athena.sh

BACKUP_DIR="/backup/athena"
DATE=$(date +%Y%m%d)
RETENTION_DAYS=30

echo "🔄 开始Athena平台备份 - $(date)"

# 创建备份目录
mkdir -p $BACKUP_DIR/$DATE/{database,config,logs}

# 1. 数据库备份
echo "📊 备份数据库..."
kubectl exec -n postgres-0 -c postgres \
  -c "pg_dump athena_production > /tmp/athena_backup_$DATE.sql"

# 移动到备份目录
mv /tmp/athena_backup_$DATE.sql $BACKUP_DIR/$DATE/infrastructure/infrastructure/database/

# 2. 配置备份
echo "⚙️ 备份配置..."
kubectl get configmaps --all-namespaces -o yaml > $BACKUP_DIR/$DATE/config/configmaps.yaml
kubectl get secrets --all-namespaces -o yaml > $BACKUP_DIR/$DATE/config/secrets.yaml

# 3. 清理旧备份
echo "🧹 清理旧备份..."
find $BACKUP_DIR -type d -mtime +$RETENTION_DAYS -exec rm -rf {} \;

# 4. 备份到远程存储 (可选)
# aws s3 sync $BACKUP/$DATE s3://athena-backups/ --delete

echo "✅ 备份完成: $BACKUP_DIR/$DATE"
```

#### 1.3 恢复程序
```bash
#!/bin/bash
# restore-athena.sh

BACKUP_DATE=$1
BACKUP_DIR="/backup/athena"

if [ -z "$BACKUP_DATE" ]; then
    echo "❌ 请指定备份日期"
    echo "可用备份:"
    ls $BACKUP_DIR
    exit 1
fi

echo "🔄 开始恢复Athena平台 - $(date)"

# 1. 停止服务
echo "⏹ 停止相关服务..."
kubectl scale deployment xiaonuo-control-center --replicas=0 -n athena-control-center

# 2. 恢复数据库
echo "💾 恢复数据库..."
kubectl cp $BACKUP_DIR/$BACKUP_DATE/infrastructure/infrastructure/database/athena_backup_$BACKUP_DATE.sql /tmp/restore.sql
kubectl exec -n postgres-0 -c postgres -c "psql -d athena_production < /tmp/restore.sql"

# 3. 恢复配置
echo "⚙️ 恢复配置..."
kubectl apply -f $BACKUP_DIR/$BACKUP_DATE/config/configmaps.yaml
kubectl apply -f $BACKUP_DIR/$BACKUP_DIR/config/secrets.yaml

# 4. 重启服务
echo "🚀 重启服务..."
kubectl scale deployment xiaonuo-control-center --replicas=3 -n athena-control-center

# 5. 验证恢复
echo "✅ 验证恢复状态..."
kubectl get pods -n athena-control-center
kubectl get svc -n athena-control-center

echo "🎉 恢复完成"
```

### 2. 灾难恢复

#### 2.1 灾难恢复计划
```yaml
灾难类型:
  - 单节点故障
  - 整个集群故障
  - 数据中心故障
  - 网络分区

RTO (恢复时间目标):
  - 关键服务: 5分钟
  - 重要服务: 30分钟
  - 一般服务: 2小时
  - 完整平台: 4小时

RPO (恢复点目标):
  - 关键数据: 0小时
  - 重要数据: 15分钟
  - 一般数据: 4小时
  - 配置数据: 24小时
```

#### 2.2 灾难恢复脚本
```bash
#!/bin/bash
# disaster-recovery.sh

DISASTER_TYPE=$1
RECOVERY_LOCATION=$2

echo "🚨 灾难恢复程序启动 - $(date)"
echo "灾难类型: $DISASTER_TYPE"
echo "恢复位置: $RECOVERY_LOCATION"

case $DISASTER_TYPE in
    "single_node")
        # 单节点故障恢复
        echo "🔧 单节点故障恢复..."

        # 1. 标记故障节点
        kubectl cordon node <failed-node>

        # 2. 驺移Pod
        kubectl get pods -o wide | grep <failed-node> | \
          awk '{print $1}' | xargs -I {} kubectl delete pod {} --grace-period=0

        # 3. 解除节点标记
        kubectl uncordon node <failed-node>
        ;;

    "cluster_failure")
        # 整个集群故障恢复
        echo "🏥️ 集群故障恢复..."

        # 1. 启动应急环境
        echo "启动应急环境..."

        # 2. 从备份恢复数据
        echo "从备份恢复数据..."

        # 3. 重建集群
        echo "重建Kubernetes集群..."
        ;;

    "datacenter_failure")
        # 数据中心故障恢复
        echo "🌍 数据中心故障恢复..."

        # 1. 切换到异地数据中心
        echo "切换到异地数据中心..."

        # 2. 恢复服务
        echo "恢复关键服务..."

        # 3. 数据同步
        echo "同步最新数据..."
        ;;
esac

echo "✅ 灾难恢复完成"
```

---

## 🔄 升级维护

### 1. 滚动升级策略

#### 1.1 蓝绿部署配置
```yaml
# 蓝绿部署配置
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: athena-control-center
  namespace: athena-control-center
spec:
  replicas: 3
  strategy:
    canary:
      steps: 2
      maxUnavailable: 1
    blueGreen:
      autoPromotionEnabled: true
      scaleDownDelaySeconds: 30
      prePromotionAnalysis: false
      postPromotionAnalysis: true
  selector:
    matchLabels:
      app: xiaonuo-control-center
  template:
    metadata:
      labels:
        app: xiaonuo-control-center
        version: v1.0.0
    spec:
      containers:
      - name: control-center-api
        image: athena/xiaonuo-control-center:v1.0.1
        ports:
        - containerPort: 9002
        readinessProbe:
          httpGet:
            path: /health
            port: 9002
          initialDelaySeconds: 30
          periodSeconds: 10
```

#### 1.2 升级脚本
```bash
#!/bin/bash
# upgrade-athena.sh

VERSION=$1
ENVIRONMENT=$2

echo "🔄 Athena平台升级 - $(date)"
echo "目标版本: $VERSION"
echo "环境: $ENVIRONMENT"

# 1. 升级前检查
echo "🔍 升级前检查..."

# 检查集群状态
if ! kubectl get nodes | grep -q "Ready"; then
    echo "❌ 集群状态异常，停止升级"
    exit 1
fi

# 检查备份
echo "检查备份状态..."
BACKUP_CHECK=$(curl -s "http://backup-service/health" | jq -r '.status')
if [ "$BACKUP_CHECK" != "healthy" ]; then
    echo "⚠️ 备份服务异常，建议先完成备份"
    read -p "是否继续升级? (y/N): " continue_upgrade
    if [ "$continue_upgrade" != "y" ]; then
        echo "❌ 用户取消升级"
        exit 1
    fi
fi

# 2. 准备升级
echo "⚙️ 准备升级..."

# 创建备份
./backup-athena.sh

# 导出当前配置
kubectl get deployment xiaonuo-control-center -n athena-control-center -o yaml > /tmp/deployment-backup.yaml

# 暂停非关键服务
kubectl scale deployment yunxi-baochen-service --replicas=0 -n athena-services
kubectl scale deployment xiaochen-media-service --replicas=0 -n athena-services

# 3. 执行升级
echo "🚀 执行升级..."

# 更新镜像
kubectl set image infrastructure/deployment/xiaonuo-control-center \
  xiaonuo-control-center=athena/xiaonuo-control-center:$VERSION \
  -n athena-control-center

# 等待滚动更新完成
echo "⏳ 等待滚动更新完成..."
kubectl rollout status infrastructure/deployment/xiaonuo-control-center -n athena-control-center

# 4. 验证升级
echo "✅ 验证升级结果..."

# 检查Pod状态
kubectl get pods -n athena-control-center -l app=xiaonuo-control-center

# 检查服务健康
kubectl port-forward svc/xiaonuo-control-center 9002:9002 -n athena-control-center &
PORT_FORWARD_PID=$!
sleep 3
curl -s http://localhost:9002/health | jq -r '.success'
kill $PORT_FORWARD_PID

# 恢复非关键服务
kubectl scale deployment yunxi-baochen-service --replicas=2 -n athena-services
kubectl scale deployment xiaochen-media-service --replicas=1 -n athena-services

# 5. 后续验证
echo "📊 后续监控..."

# 监控10分钟
for i in {1..10}; do
    echo "监控中... ($i/10)"
    sleep 60
    if ! kubectl get pods -n athena-control-center | grep -q "Running"; then
        echo "❌ 发现异常状态，准备回滚"
        break
    fi
done

echo "✅ 升级完成"

# 清理备份
rm -f /tmp/deployment-backup.yaml
```

### 2. 回滚机制

#### 2.1 回滚配置
```bash
#!/bin/bash
# rollback-athena.sh

ROLLBACK_VERSION=$1

echo "🔄 Athena平台回滚 - $(date)"
echo "回滚到版本: $ROLLBACK_VERSION"

# 1. 停止滚动更新
kubectl rollout undo infrastructure/deployment/xiaonuo-control-center -n athena-control-center

# 2. 恢复镜像版本
kubectl set image infrastructure/deployment/xiaonuo-control-center \
  xiaonuo-control-center=athena/xiaonuo-control-center:$ROLLBACK_VERSION \
  -n athena-control-center

# 3. 验证回滚
kubectl rollout status infrastructure/deployment/xiaonuo-control-center -n athena-control-center

echo "✅ 回滚完成"
```

---

## 🔒 安全运维

### 1. 安全配置

#### 1.1 网络安全
```yaml
# NetworkPolicy配置
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: athena-network-policy
  namespace: athena-control-center
spec:
  podSelector:
    matchLabels:
      app: xiaonuo-control-center
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
  - from:
    - namespaceSelector:
        matchLabels:
          name: athena-services
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 443
    - protocol: TCP
      port: 80
```

#### 1.2 RBAC配置
```yaml
# RBAC配置
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: athena-admin
rules:
- apiGroups: [""]
  resources: ["*"]
  verbs: ["*"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["create", "get", "list", "update", "delete", "patch"]
- apiGroups: ["batch"]
  resources: ["jobs", "cronjobs"]
  verbs: ["create", "get", "list", "update", "delete"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: athena-admin-binding
subjects:
  - kind: User
    name: athena-admin
roleRef:
  kind: ClusterRole
  name: athena-admin
```

#### 1.3 密钥管理
```yaml
# 密钥轮换策略
证书轮换:
  - 频度: 每30天
  - 提前15天通知
  - 自动续期
  - 备份旧证书

数据库密码:
  - 长度: 90天
  - 复杂度要求: 16位以上
  - 定期轮换

API密钥:
  - 长度: 180天
  - 自动生成
  - 定期轮换
  - 审计访问日志
```

### 2. 安全监控

#### 2.1 安全扫描
```bash
#!/bin/bash
# security-scan.sh

echo "🔒 开始安全扫描 - $(date)"

# 1. 容器镜像安全扫描
echo "📦 扫描容器镜像..."
for image in $(kubectl get pods -o jsonpath='{.items[*].spec.containers[*].image}' | sort | uniq); do
    echo "扫描镜像: $image"
    trivy image --exit-code 1 "$image"
done

# 2. 配置文件安全扫描
echo "⚙️ 扫描配置文件..."
find . -name "*.yaml" -o -name "*.json" | xargs -I {} \
  yamllint "$FILE" 2>/dev/null || echo "文件格式检查完成"

# 3. 权限检查
echo "🔑 权限检查..."
kubectl auth can-i --list --all-namespaces

# 4. 网络策略检查
echo "🌐 网络策略检查..."
kubectl get networkpolicy --all-namespaces

# 5. 密钥检查
echo "🔑 密钥安全检查"
kubectl get secrets --all-namespaces --field-selector=type=Opaque | \
  grep -E "(password|key|token|secret)"
```

#### 2.2 侵入检测
```bash
#!/bin/bash
# intrusion-detection.sh

echo "🔍 入侵检测 - $(date)"

# 1. 异常登录检测
echo "🔑 检查异常登录..."
kubectl auth can-i --list --no-headers | \
  grep -E "(cluster-admin|system:admin)" | \
  wc -l

# 2. 异常网络活动检测
echo "🌐 检查网络连接..."
kubectl get events --all-namespaces --sort-by='.lastTimestamp' | \
  grep -E "(Forbidden|Permission denied|Unreachable)" | tail -10

# 3. 异常资源使用检测
echo "📊 检查资源使用..."
kubectl top pods --all-namespaces | \
  grep -E "(1000%|ERROR|OOMKilled)"

# 4. 日志异常检测
echo "📝 检查日志异常..."
kubectl logs --all-namespaces --tail=100 | \
  grep -E "(error|exception|failed|denied)" | \
  tail -20
```

### 3. 合规性管理

#### 3.1 审计日志
```yaml
# 审计日志配置
logging:
  access_logs:
    - source: nginx-ingress
      format: nginx
      retention: 90天
    - source: application
      format: json
      retention: 365 days
    - source: system
      format: syslog
      retention: 180 days

  security_logs:
    - authentication_logs
    - authorization_logs
    - admin_actions
    - security_events
    retention: 1825 days
```

#### 3.2 数据保护
```yaml
# 数据保护配置
data_protection:
  encryption:
    at_rest:
      database: AES-256
      storage: AES-256
    in_transit:
      network: TLS 1.3
      internal: mTLS

  privacy:
    data_classification:
      - PII: 个人身份信息
      - PHI: 健康信息
      - Business: 商业机密
      - Public: 公开信息

    access_control:
      - role_based_access: true
      - least_privilege: true
      - audit_trail: true
      - consent_management: true
```

## 📚 手册使用指南

### 1. 快速查找
```bash
# 搜索特定主题
grep -r "故障处理" /path/to/playbook.md

# 获取目录结构
cat /path/to/playbook.md | grep "^## " | head -10

# 搜索命令
grep -B2 -A5 "升级维护" /path/to/playbook.md
```

### 2. 交叉引用
```markdown
## 相关文档
- [架构设计文档](./architecture-design.md)
- [部署配置文档](../k8s/)
- [监控配置文档](../infrastructure/infrastructure/monitoring/)
- [安全策略文档](../security/)
```

### 3. 实用链接
```markdown
## 外部资源
- [Kubernetes官方文档](https://kubernetes.io/docs/)
- [Prometheus文档](https://prometheus.io/docs/)
- [Grafana文档](https://grafana.com/docs/)
- [Helm文档](https://helm.sh/docs/)
- [NGINX文档](https://nginx.org/en/docs/)

## 联系信息
- 运维团队: ops@athena-platform.com
- 紧急联系: +86-138-0013-8000
- 技术支持: support@athena-platform.com
- 安全举报: security@athena-platform.com
```

---

## 🎯 总结

本运维手册提供了小诺总控平台生产环境的完整运维指南，涵盖了从部署到日常运维、故障处理、监控告警、备份恢复、升级维护和安全运维的各个方面。

### 关键要点

1. **预防为主**: 建立完善的监控告警体系，提前发现问题
2. **快速响应**: 制定详细的故障响应流程，确保快速恢复
3. **持续改进**: 建立事后分析机制，不断优化系统
4. **安全第一**: 实施多层次安全防护，保障系统安全

### 最佳实践

1. **定期检查**: 每日健康检查，每周深度检查
2. **自动化**: 自动化部署、监控、备份、恢复
3. **文档化**: 详细记录所有操作和变更
4. **测试验证**: 定期演练故障恢复和场景切换

通过遵循本手册，可以确保小诺总控平台在生产环境中稳定、安全、高效运行。