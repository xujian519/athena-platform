# Athena高性能层运维手册

## 📋 概述

本手册提供Athena平台高性能层的日常运维指南，包括向量检索服务和LLM服务的运维。

---

## 🚀 服务启动和停止

### 向量检索服务

**启动服务**：
```bash
# 使用systemd（Linux）
sudo systemctl start athena-vector

# 使用Docker
docker start athena-vector

# 手动启动
cd /opt/athena/vector-service
./vector-service
```

**停止服务**：
```bash
# 使用systemd
sudo systemctl stop athena-vector

# 使用Docker
docker stop athena-vector

# 手动停止
kill -TERM $(pidof vector-service)
```

**重启服务**：
```bash
# 使用systemd
sudo systemctl restart athena-vector

# 使用Docker
docker restart athena-vector
```

### LLM服务

**启动服务**：
```bash
# 使用systemd
sudo systemctl start athena-llm

# 使用Docker
docker start athena-llm

# 手动启动
cd /opt/athena/llm-service
./llm-service
```

**停止服务**：
```bash
# 使用systemd
sudo systemctl stop athena-llm

# 使用Docker
docker stop athena-llm
```

---

## 📊 监控和告警

### 关键指标

**向量检索服务**：
```bash
# 搜索延迟（P95）
- 目标: <50ms
- 告警: >100ms

# 缓存命中率
- 目标: >85%
- 告警: <70%

# QPS
- 目标: >100
- 告警: <50

# 错误率
- 目标: <0.1%
- 告警: >1%
```

**LLM服务**：
```bash
# 响应延迟（P95）
- 目标: <2000ms
- 告警: >5000ms

# 缓存命中率
- 目标: >80%
- 告警: <60%

# 成本/1K tokens
- 目标: <$1.00
- 告警: >$2.00

# 错误率
- 目标: <0.1%
- 告警: >1%
```

### 监控命令

**检查服务状态**：
```bash
# 向量检索服务
curl http://localhost:8023/health

# LLM服务
curl http://localhost:8024/health
```

**查看指标**：
```bash
# 向量检索服务
curl http://localhost:8023/metrics

# LLM服务
curl http://localhost:8024/metrics
```

**查看日志**：
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

## 🔍 性能分析

### 1. 分析性能瓶颈

**检查慢查询**：
```bash
# 查看搜索延迟分布
curl http://localhost:8023/stats | jq '.search.duration'

# 查看P95延迟
curl http://localhost:8023/stats | jq '.search.p95_duration_ms'
```

**检查缓存性能**：
```bash
# 查看缓存命中率
curl http://localhost:8023/stats | jq '.cache.hit_rate'

# 查看缓存大小
curl http://localhost:8023/stats | jq '.cache.size'
```

### 2. 性能调优

**增加缓存容量**：
```bash
# 编辑配置文件
vim /opt/athena/vector-service/config.yaml

# 更新配置
cache:
  local_size: 2000  # 增加到2000
  ttl: 3600        # 延长到1小时

# 重启服务
sudo systemctl restart athena-vector
```

**优化连接池**：
```bash
# 更新Qdrant连接池配置
qdrant:
  max_idle_conns: 200
  max_conns_per_host: 20

# 重启服务
sudo systemctl restart athena-vector
```

---

## 🛠️ 故障排查

### 问题1：服务无响应

**症状**：
```bash
curl http://localhost:8023/health
# 超时或无响应
```

**排查步骤**：
```bash
# 1. 检查进程状态
ps aux | grep vector-service

# 2. 检查端口监听
lsof -i :8023

# 3. 检查系统资源
free -h
df -h

# 4. 检查日志
sudo journalctl -u athena-vector -n 100
```

**解决方案**：
```bash
# 如果进程卡死，重启服务
sudo systemctl restart athena-vector

# 如果内存不足，增加内存或减少缓存容量
export CACHE_LOCAL_SIZE=500
```

### 问题2：缓存命中率低

**症状**：
```bash
curl http://localhost:8023/stats | jq '.cache.hit_rate'
# 返回: 50.0（低于目标85%）
```

**排查步骤**：
```bash
# 1. 检查缓存容量
curl http://localhost:8023/stats | jq '.cache.size'

# 2. 检查TTL设置
grep ttl /opt/athena/vector-service/config.yaml

# 3. 检查请求模式
sudo journalctl -u athena-vector -n 1000 | grep "cache miss"
```

**解决方案**：
```bash
# 增加缓存容量
export CACHE_LOCAL_SIZE=2000

# 延长TTL
export CACHE_TTL=3600

# 预热热点数据
curl -X POST http://localhost:8023/warmup \
  -H "Content-Type: application/json" \
  -d '{"hot_vectors": [...]}'
```

### 问题3：Qdrant连接失败

**症状**：
```
Error: connection refused to Qdrant
```

**排查步骤**：
```bash
# 1. 检查Qdrant状态
docker ps | grep qdrant

# 2. 检查Qdrant健康
curl http://localhost:16333/health

# 3. 检查网络连接
telnet localhost 16333

# 4. 检查Qdrant日志
docker logs -f qdrant
```

**解决方案**：
```bash
# 启动Qdrant
docker start qdrant

# 或重新创建Qdrant容器
docker run -d -p 16333:6333 qdrant/qdrant:v1.7.0
```

### 问题4：LLM API调用失败

**症状**：
```
Error: LLM API request failed: 401 Unauthorized
```

**排查步骤**：
```bash
# 1. 检查API密钥
echo $LLM_API_KEY

# 2. 验证API密钥
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $LLM_API_KEY"

# 3. 检查服务日志
sudo journalctl -u athena-llm -n 100
```

**解决方案**：
```bash
# 更新API密钥
export LLM_API_KEY=sk-new-key

# 重启服务
sudo systemctl restart athena-llm
```

---

## 📈 容量规划

### 1. 评估当前容量

**检查QPS**：
```bash
# 向量检索服务
curl http://localhost:8023/stats | jq '.search.total_searches'

# LLM服务
curl http://localhost:8024/stats | jq '.service.total_requests'
```

**检查资源使用**：
```bash
# CPU使用率
top -b -n 1 | grep vector-service

# 内存使用
ps aux | grep vector-service | awk '{print $6}'

# 网络连接
netstat -an | grep :8023 | wc -l
```

### 2. 扩容建议

**水平扩容（增加实例）**：
```bash
# 复制服务配置
sudo cp /etc/systemd/system/athena-vector.service \
        /etc/systemd/system/athena-vector@.service

# 启动多个实例
sudo systemctl start athena-vector@1
sudo systemctl start athena-vector@2
sudo systemctl start athena-vector@3

# 使用负载均衡器
# (Nginx、HAProxy等)
```

**垂直扩容（增加资源）**：
```bash
# 增加内存限制
vim /etc/systemd/system/athena-vector.service

# 添加配置
[Service]
MemoryLimit=2G
CPUQuota=200%

# 重启服务
sudo systemctl daemon-reload
sudo systemctl restart athena-vector
```

---

## 🔄 日常维护任务

### 每日任务

- [ ] 检查服务状态
- [ ] 查看错误日志
- [ ] 监控关键指标
- [ ] 检查磁盘空间

### 每周任务

- [ ] 分析性能趋势
- [ ] 检查缓存命中率
- [ ] 清理过期日志
- [ ] 备份配置文件

### 每月任务

- [ ] 容量规划评估
- [ ] 成本分析
- [ ] 安全更新
- [ ] 性能测试

---

## 📝 配置管理

### 1. 配置文件位置

```
/etc/athena/
├── vector-service/
│   ├── config.yaml
│   └── models.yaml
└── llm-service/
    ├── config.yaml
    └── routing.yaml
```

### 2. 配置变更流程

```bash
# 1. 备份当前配置
sudo cp /etc/athena/vector-service/config.yaml \
          /etc/athena/vector-service/config.yaml.bak

# 2. 编辑配置
sudo vim /etc/athena/vector-service/config.yaml

# 3. 验证配置
./vector-service --config=/etc/athena/vector-service/config.yaml --validate

# 4. 重启服务
sudo systemctl reload athena-vector

# 5. 验证生效
curl http://localhost:8023/health
```

### 3. 配置版本控制

```bash
# 使用Git管理配置
cd /etc/athena
git init
git add .
git commit -m "Initial configuration"

# 配置变更
git add vector-service/config.yaml
git commit -m "Increase cache size to 2000"
```

---

## 🔐 安全管理

### 1. API密钥轮换

```bash
# 1. 生成新密钥
# (从OpenAI控制台生成新API密钥)

# 2. 更新环境变量
export LLM_API_KEY=sk-new-key

# 3. 更新服务配置
sudo vim /etc/systemd/system/athena-llm.service

# 4. 重启服务
sudo systemctl restart athena-llm

# 5. 验证
curl -X POST http://localhost:8024/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "test"}]}'

# 6. 撤销旧密钥
# (从OpenAI控制台撤销旧API密钥)
```

### 2. 访问控制

```bash
# 限制服务访问IP
vim /etc/athena/vector-service/config.yaml

# 添加配置
server:
  allowed_ips:
    - "10.0.0.0/8"
    - "192.168.0.0/16"

# 重启服务
sudo systemctl restart athena-vector
```

---

## 🚨 应急响应

### 服务中断

**1. 立即检查**：
```bash
# 检查所有服务状态
sudo systemctl status athena-vector athena-llm

# 检查依赖服务
docker ps | grep -E "qdrant|redis"

# 检查系统资源
free -h
df -h
top
```

**2. 快速恢复**：
```bash
# 重启服务
sudo systemctl restart athena-vector
sudo systemctl restart athena-llm

# 如果失败，回滚到上一版本
mv /opt/athena/vector-service/vector-service.old \
   /opt/athena/vector-service/vector-service
sudo systemctl restart athena-vector
```

**3. 通知相关人员**：
```bash
# 发送告警
# (配置告警通知：邮件、Slack、短信等)
```

---

## 📞 联系方式

**技术支持**：
- 邮箱: xujian519@gmail.com
- 项目地址: /Users/xujian/Athena工作平台

**紧急联系**：
- 电话: [待填写]
- Slack: #athena-ops

---

**维护者**: Athena平台团队
**更新时间**: 2026-04-20
**版本**: v1.0
