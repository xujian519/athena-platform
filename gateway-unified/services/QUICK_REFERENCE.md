# Athena高性能层快速参考指南

## 🚀 快速启动

### 启动所有服务

```bash
# 使用systemd（生产环境）
sudo systemctl start athena-vector
sudo systemctl start athena-llm

# 使用Docker（开发环境）
cd /Users/xujian/Athena工作平台
docker-compose up -d
```

### 检查服务状态

```bash
# 检查服务健康
curl http://localhost:8023/health  # 向量检索服务
curl http://localhost:8024/health  # LLM服务

# 查看服务状态
sudo systemctl status athena-vector
sudo systemctl status athena-llm
```

---

## 📊 监控命令

### 查看性能指标

```bash
# 向量检索服务
curl http://localhost:8023/metrics | grep vector_search

# LLM服务
curl http://localhost:8024/metrics | grep llm_requests
```

### 查看缓存命中率

```bash
# 向量检索服务
curl http://localhost:8023/stats | jq '.cache.hit_rate'

# LLM服务
curl http://localhost:8024/stats | jq '.cache.hit_rate'
```

### 查看日志

```bash
# 向量检索服务
sudo journalctl -u athena-vector -f

# LLM服务
sudo journalctl -u athena-llm -f

# 或使用Docker
docker logs -f athena-vector
docker logs -f athena-llm
```

---

## 🔧 常用配置

### 向量检索服务

```yaml
# /opt/athena/vector-service/config.yaml
server:
  port: 8023

qdrant:
  host: "localhost"
  port: 16333

cache:
  local_size: 1000
  ttl: 300
  enabled: true
```

### LLM服务

```yaml
# /opt/athena/llm-service/config.yaml
server:
  port: 8024

llm:
  api_base_url: "https://api.openai.com/v1"
  model: "gpt-3.5-turbo"

routing:
  enabled: true
  default_tier: "balanced"

cache:
  local_size: 500
  ttl: 86400
  enabled: true

concurrent:
  max_concurrency: 10
```

---

## 🛠️ 故障排查速查表

| 问题 | 可能原因 | 解决方案 |
|-----|---------|---------|
| 服务无法启动 | 端口被占用 | `lsof -i :8023` 然后 `kill -9 <PID>` |
| 缓存命中率低 | 缓存容量太小 | 增加 `CACHE_LOCAL_SIZE` |
| Qdrant连接失败 | Qdrant未运行 | `docker start qdrant` |
| LLM API失败 | API密钥无效 | 更新 `LLM_API_KEY` |
| 响应慢 | 并发不足 | 增加 `MAX_CONCURRENCY` |
| 内存占用高 | 缓存过大 | 减少 `CACHE_LOCAL_SIZE` |

---

## 📈 性能基准

### 向量检索服务

| 指标 | 目标 | 告警阈值 |
|-----|------|---------|
| 搜索延迟（P95） | <50ms | >100ms |
| 缓存命中率 | >85% | <70% |
| QPS | >100 | <50 |
| 错误率 | <0.1% | >1% |

### LLM服务

| 指标 | 目标 | 告警阈值 |
|-----|------|---------|
| 响应延迟（P95） | <2000ms | >5000ms |
| 缓存命中率 | >80% | <60% |
| 成本/1K tokens | <$1.00 | >$2.00 |
| 错误率 | <0.1% | >1% |

---

## 🔐 安全检查清单

### 每日检查

- [ ] 服务正常运行
- [ ] 无异常错误日志
- [ ] 关键指标在正常范围

### 每周检查

- [ ] API密钥有效期
- [ ] 磁盘空间充足
- [ ] 备份配置文件

### 每月检查

- [ ] 安全更新
- [ ] 性能评估
- [ ] 成本分析
- [ ] 容量规划

---

## 📞 紧急联系

**技术支持**: xujian519@gmail.com  
**项目地址**: /Users/xujian/Athena工作平台

---

## 📚 完整文档

- [向量检索服务部署指南](./vector/DEPLOYMENT.md)
- [LLM服务部署指南](./llm/DEPLOYMENT.md)
- [运维手册](./OPERATIONS_MANUAL.md)
- [项目总结](../../docs/reports/PROJECT_COMPLETION_SUMMARY_20260420.md)

---

**快速参考** | **更新时间**: 2026-04-20
