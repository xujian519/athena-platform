# Athena工作平台 - 生产环境部署配置

## 📁 目录结构

```
production/
├── 🐳 docker/                          # Docker配置
│   ├── 🐋 Dockerfile.prod             # 生产环境Dockerfile
│   ├── 📋 docker-compose.prod.yml     # 生产环境编排
│   └── ⚙️ .dockerignore.prod          # 生产环境忽略文件
├── ☸️ k8s/                            # Kubernetes配置
│   ├── 🏷️ namespaces/                 # 命名空间
│   ├── 📋 configmaps/                 # 配置映射
│   ├── 🔐 secrets/                    # 密钥管理
│   ├── 🚀 deployments/                # 部署配置
│   ├── 🌐 services/                   # 服务配置
│   ├── 🚪 ingress/                    # 入口配置
│   └── 🛡️ network-policies/          # 网络策略
├── 📊 monitoring/                     # 监控系统
│   ├── 📈 prometheus/                 # Prometheus配置
│   ├── 📊 grafana/                    # Grafana配置
│   └── 🚨 alertmanager/               # 告警管理
├── 🔄 ci-cd/                          # CI/CD流水线
│   └── 🔄 .github/workflows/          # GitHub Actions
├── 🛠️ scripts/                        # 运维脚本
│   ├── 🚀 deploy.sh                   # 部署脚本
│   ├── 🏥 health-check.sh             # 健康检查
│   ├── 📝 log-collector.sh            # 日志收集
│   └── 🔄 rollback.sh                 # 回滚脚本
└── 📖 docs/                           # 文档
    ├── 🚀 deployment-guide.md         # 部署指南
    ├── 📊 monitoring-guide.md          # 监控指南
    └── 🚨 incident-response.md        # 事件响应
```

---

## 🌟 小娜自然语言交互系统（新功能）

**一句话说明**: 无需编程，直接用中文和小娜对话即可使用专业的专利法律提示词系统！

### 快速启动小娜

```bash
# 方式1: 使用启动脚本（推荐）
cd /Users/xujian/Athena工作平台/production
./start_xiaona.sh

# 方式2: 直接运行
cd /Users/xujian/Athena工作平台/production/services
python3 xiaona_natural_interface.py
```

### 使用示例

```
您: 帮我分析这个技术交底书
小娜: 【小娜】好的，我来帮您分析...

您: 检索相关的现有技术
小娜: 【小娜】我来检索"深度学习 目标检测"相关的现有技术...

您: 切换到意见答复模式
小娜: 【小娜】爸爸，我已切换到意见答复模式...
```

### 详细文档

- [自然语言交互使用指南](./XIAONA_NATURAL_INTERFACE_GUIDE.md) - 完整使用说明
- [上下文优化方案](./XIAONA_CONTEXT_OPTIMIZATION.md) - 优化上下文窗口使用
- [提示词系统说明](../prompts/README.md) - 四层提示词架构

---

## 🔍 专利智能检索系统

### 1. 环境检查
```bash
# 确保Docker和Docker Compose已安装
docker --version
docker-compose --version
```

### 2. 一键部署
```bash
# 进入生产目录
cd /Users/xujian/Athena工作平台/production

# 执行部署脚本
./dev/scripts/deploy_production.sh
```

### 3. 验证部署
```bash
# 健康检查
curl http://localhost/health

# API测试
curl -X POST http://localhost/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "发明专利的创造性判断", "top_k": 5}'
```

## 📊 服务访问

| 服务 | 地址 | 说明 |
|------|------|------|
| **专利检索API** | http://localhost:8000 | 主要API服务 |
| **Nginx代理** | http://localhost | 负载均衡入口 |
| **API文档** | http://localhost/docs | Swagger文档 |
| **监控面板** | http://localhost:3000 | Grafana (admin/admin123) |
| **Prometheus** | http://localhost:9090 | 指标收集 |
| **Qdrant管理** | http://localhost:6333 | 向量数据库 |

## 🔧 管理命令

### 服务管理
```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启API服务
docker-compose restart patent-api

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f patent-api
```

### 数据备份
```bash
# 手动备份
./dev/scripts/backup_data.sh

# 查看备份
ls -la backups/
```

### 性能测试
```bash
# 轻量测试 (10并发用户)
python3 dev/scripts/load_test.py

# 重量测试 (50并发用户)
python3 dev/scripts/load_test.py --search-users 50 --search-requests 10
```

## 📡 API接口

### 专利检索
```bash
curl -X POST http://localhost/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "专利创造性判断标准",
    "top_k": 10,
    "search_type": "hybrid"
  }'
```

### 语义分析
```bash
curl -X POST http://localhost/api/v1/semantic-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "text": "本发明涉及新型数据处理方法",
    "analysis_type": "comprehensive"
  }'
```

### 案例推荐
```bash
curl -X POST http://localhost/api/v1/case-recommendation \
  -H "Content-Type: application/json" \
  -d '{
    "case_description": "通信技术专利纠纷",
    "similarity_threshold": 0.7,
    "max_recommendations": 5
  }'
```

## 🔍 监控告警

### 关键指标
- **API响应时间**: < 2秒
- **成功率**: > 99%
- **并发处理**: 50+ QPS
- **内存使用**: < 80%
- **CPU使用**: < 70%

### 告警规则
```yaml
# 示例Prometheus告警规则
groups:
- name: patent-api
  rules:
  - alert: HighResponseTime
    expr: histogram_quantile(0.95, http_request_duration_seconds) > 2
    for: 5m

  - alert: LowSuccessRate
    expr: rate(http_requests_total{status!~"2.."}[5m]) > 0.01
    for: 5m
```

## 🛠️ 故障排除

### 常见问题

**1. API服务无法访问**
```bash
# 检查服务状态
docker-compose ps

# 查看API日志
docker-compose logs patent-api

# 重启服务
docker-compose restart patent-api
```

**2. Qdrant连接失败**
```bash
# 检查Qdrant状态
curl http://localhost:6333/collections

# 重启Qdrant
docker-compose restart qdrant
```

**3. 性能问题**
```bash
# 检查系统资源
docker stats

# 查看慢查询日志
docker-compose logs patent-api | grep "slow"
```

### 日志位置
- **API日志**: `logs/patent_retrieval_api.log`
- **Nginx日志**: `/var/log/infrastructure/infrastructure/nginx/`
- **系统日志**: `docker-compose logs`

## 📈 性能优化

### 1. 数据库优化
- Qdrant集合索引优化
- 向量维度调整
- 分片策略配置

### 2. 缓存策略
- Redis热点查询缓存
- API响应缓存
- 静态资源CDN

### 3. 扩容方案
- 水平扩展API实例
- 数据库读写分离
- 负载均衡优化

## 🔒 安全配置

### 1. 访问控制
```nginx
# 示例IP白名单
location /api/ {
    allow 192.168.1.0/24;
    deny all;
    proxy_pass http://patent_api;
}
```

### 2. 限流配置
```nginx
# API限流
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /api/ {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://patent_api;
}
```

### 3. HTTPS配置
```nginx
server {
    listen 443 ssl;
    ssl_certificate /etc/infrastructure/infrastructure/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/infrastructure/infrastructure/nginx/ssl/key.pem;
    # ... 其他配置
}
```

## 📞 技术支持

### 联系方式
- **技术支持**: support@athena-patent.com
- **紧急响应**: 24/7监控告警

### 文档资源
- [API详细文档](http://localhost/docs)
- [系统架构文档](../docs/)
- [故障处理手册](troubleshooting.md)

---

**⚠️ 重要提醒**:
1. 生产部署前请务必备份数据
2. 定期检查系统运行状态
3. 及时更新安全补丁
4. 监控系统资源使用情况