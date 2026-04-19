# Qdrant 镜像拉取问题分析与解决方案

## 问题诊断

### 1. 镜像拉取问题分析

**根本原因**: Docker Hub 连接超时
- `ping registry-1.docker.io` - 100% 丢包
- 国内网络环境下 Docker Hub 访问受限

**当前状态**:
- 已配置镜像源: `https://docker.m.daocloud.io/` (DaoCloud)
- 但拉取速度慢或超时

### 2. 项目中 Qdrant 实例分析

通过扫描全项目，发现 **21个 docker-compose 文件** 包含 Qdrant 配置：

#### Qdrant 版本分布

| 版本 | 使用场景 | 文件数量 |
|------|----------|----------|
| `qdrant/qdrant:latest` | 通用开发环境 | 12个 |
| `qdrant/qdrant:v1.7.0` | 特定版本兼容 | 3个 |
| `qdrant/qdrant:v1.7.4` | 生产环境 | 6个 |

#### 主要部署场景

1. **记忆系统** (memory_module)
   - 端口: 6333/6334
   - 存储: `qdrant_storage/`
   - 集合: `agent_memory_vectors`, `conversation_vectors`, `knowledge_vectors`

2. **法律系统** (legal)
   - 端口: 6333/6334 (内部网络)
   - 架构: 主从复制集群 (Primary + Replica)
   - 版本: v1.7.4

3. **知识图谱** (knowledge-graph)
   - 端口: 6333/6334
   - 集成: 与 NebulaGraph 配合

4. **向量知识统一** (vectorkg-unified)
   - 端口: 6333/6334
   - 用途: 向量+图混合检索

#### 资源配置分析

| 场景 | CPU限制 | 内存限制 | 存储路径 |
|------|---------|----------|----------|
| 开发环境 | 1-2核 | 2-4Gi | 项目本地 |
| 生产环境 | 4核 | 16Gi | `/data/athena/*/qdrant` |
| 法律系统 | 4核 | 16Gi | `/data/athena/legal/qdrant` |

---

## 解决方案

### 方案 1: 配置多个国内镜像加速源 (推荐)

#### macOS Docker Desktop 配置

```json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io/",
    "https://dockerproxy.com/",
    "https://docker.nju.edu.cn/",
    "https://docker.mirrors.ustc.edu.cn/",
    "https://docker.1panel.live/"
  ],
  "dns": ["8.8.8.8", "114.114.114.114"]
}
```

**配置步骤**:
1. 打开 Docker Desktop
2. 进入 Settings → Docker Engine
3. 添加上述 JSON 配置
4. 点击 "Apply & Restart"

#### 验证配置

```bash
docker info | grep -A 10 "Registry Mirrors"
```

### 方案 2: 直接使用国内镜像仓库

```bash
# 使用 DaoCloud 镜像
docker pull docker.m.daocloud.io/qdrant/qdrant:v1.7.4

# 重新打标签
docker tag docker.m.daocloud.io/qdrant/qdrant:v1.7.4 qdrant/qdrant:v1.7.4
```

### 方案 3: 使用阿里云个人镜像仓库

```bash
# 登录阿里云容器镜像服务
docker login --username=your_aliyun_account registry.cn-hangzhou.aliyuncs.com

# 拉取镜像
docker pull registry.cn-hangzhou.aliyuncs.com/athena/qdrant:v1.7.4
```

---

## 优化建议: 统一 Qdrant 实例管理

### 问题分析

当前项目中存在多个独立的 Qdrant 实例：
- 资源浪费 (每个实例独立运行)
- 管理复杂 (多端口、多存储)
- 数据分散 (无法跨服务共享)

### 推荐架构: 单一 Qdrant 服务 + 多 Collection

```
┌─────────────────────────────────────────────────────────┐
│           Athena 统一向量服务                           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│   ┌─────────────────────────────────────────────────┐   │
│   │        Qdrant:6333 (单一实例)                   │   │
│   │  ┌──────────────────────────────────────────┐   │   │
│   │  │ Collections (按业务隔离)                  │   │   │
│   │  │  ├─ agent_memory_vectors   (记忆系统)    │   │   │
│   │  │  ├─ legal_vectors          (法律系统)    │   │   │
│   │  │  ├─ patent_vectors        (专利系统)     │   │   │
│   │  │  ├─ knowledge_vectors      (知识图谱)    │   │   │
│   │  │  └─ document_vectors       (文档系统)    │   │   │
│   │  └──────────────────────────────────────────┘   │   │
│   └─────────────────────────────────────────────────┘   │
│                          │                                │
│         ┌────────────────┴────────────────┐             │
│         ▼                                 ▼             │
│   ┌──────────┐                      ┌──────────┐      │
│   │记忆系统  │                      │法律系统  │      │
│   └──────────┘                      └──────────┘      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 优势

| 维度 | 当前 (多实例) | 优化后 (单实例) |
|------|--------------|----------------|
| 内存占用 | ~48Gi (3×16Gi) | ~16Gi |
| CPU占用 | ~12核 (3×4核) | ~4核 |
| 管理复杂度 | 高 (多个端口) | 低 (统一端口) |
| 数据共享 | 困难 | 容易 |
| 备份恢复 | 复杂 | 简单 |
| 扩展性 | 受限 | 灵活 |

---

## 实施步骤

### 步骤 1: 配置镜像加速源

```bash
# 编辑 Docker Desktop 配置
# 或创建 daemon.json
cat > ~/.docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io/",
    "https://dockerproxy.com/",
    "https://docker.nju.edu.cn/",
    "https://docker.mirrors.ustc.edu.cn/"
  ],
  "dns": ["8.8.8.8", "114.114.114.114"]
}
EOF

# 重启 Docker
```

### 步骤 2: 拉取 Qdrant 镜像

```bash
# 拉取最新版本
docker pull qdrant/qdrant:latest

# 拉取生产版本
docker pull qdrant/qdrant:v1.7.4
```

### 步骤 3: 创建统一 Qdrant 配置

```bash
cat > /Users/xujian/Athena工作平台/docker-compose.qdrant-unified.yml << 'EOF'
version: '3.8'

services:
  athena-qdrant:
    image: qdrant/qdrant:v1.7.4
    container_name: athena-qdrant-unified
    ports:
      - "6333:6333"
      - "6334:6334"
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__SERVICE__GRPC_PORT=6334
      - QDRANT__LOG_LEVEL=INFO
      - QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS=4
    volumes:
      - ./qdrant_storage:/qdrant/storage:rw
      - ./config/qdrant/production.yaml:/qdrant/config/production.yaml:ro
    networks:
      - athena-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 16Gi
        reservations:
          cpus: '2.0'
          memory: 8Gi
    labels:
      - "com.athena.service=qdrant-unified"
      - "com.athena.environment=production"

networks:
  athena-network:
    external: true
EOF
```

### 步骤 4: 启动统一 Qdrant 服务

```bash
cd /Users/xujian/Athena工作平台

# 创建网络 (如果不存在)
docker network create athena-network 2>/dev/null || true

# 启动服务
docker-compose -f docker-compose.qdrant-unified.yml up -d

# 验证服务
curl http://localhost:6333/health
```

### 步骤 5: 初始化 Collections

```bash
# 创建记忆系统 Collection
curl -X PUT http://localhost:6333/collections/agent_memory_vectors \
  -H 'Content-Type: application/json' \
  -d '{
    "vectors": {
      "size": 768,
      "distance": "Cosine"
    }
  }'

# 创建法律系统 Collection
curl -X PUT http://localhost:6333/collections/legal_vectors \
  -H 'Content-Type: application/json' \
  -d '{
    "vectors": {
      "size": 1024,
      "distance": "Cosine"
    }
  }'
```

---

## 验证清单

- [ ] Docker 镜像加速源配置完成
- [ ] Qdrant 镜像拉取成功
- [ ] 统一 Qdrant 服务启动
- [ ] Health check 通过
- [ ] Collections 创建完成
- [ ] 各系统连接测试通过

---

## 故障排查

### 问题 1: 镜像拉取仍然失败

```bash
# 测试镜像源
curl -I https://docker.m.daocloud.io/v2/

# 尝试其他源
docker pull dockerproxy.com/qdrant/qdrant:v1.7.4
```

### 问题 2: 容器启动失败

```bash
# 查看日志
docker logs athena-qdrant-unified

# 检查端口占用
lsof -i :6333
```

### 问题 3: 内存不足

```bash
# 降低资源配置
environment:
  - QDRANT__STORAGE__OPTIMizers__segment_min_rate=1
  - QDRANT__STORAGE__PERFORMANCE__max_search_threads=2
```

---

**文档创建时间**: 2025-12-28
**作者**: Claude AI
**版本**: 1.0
