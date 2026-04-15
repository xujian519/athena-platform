# 专利全文处理系统 - 部署文档

## 版本信息
- **版本**: v3.0.0
- **更新时间**: 2025-12-25
- **状态**: ✅ 配置完成

---

## 一、目录结构

```
production/dev/scripts/patent_full_text/
├── config/                          # 配置文件目录
│   ├── .env                         # 生产环境配置
│   ├── .env.development             # 开发环境配置
│   ├── .env.testing                 # 测试环境配置
│   ├── .env.template                # 配置模板
│   └── infrastructure/nginx/                       # Nginx配置
│       └── nginx.conf
├── phase3/                          # 核心处理模块
│   ├── pipeline_v2.py               # 处理管道
│   ├── pdf_monitor_service.py       # PDF监控服务
│   ├── model_loader.py              # 模型加载器
│   ├── db_integration.py            # 数据库集成
│   ├── system_optimization.py       # 系统优化
│   └── ...
├── docker-compose.yml               # Docker编排配置
├── config_manager.py                # 配置管理工具
├── health_check.py                  # 健康检查脚本
└── DEPLOYMENT.md                    # 本文档
```

---

## 二、环境配置

### 2.1 配置文件说明

| 文件 | 说明 | 使用场景 |
|------|------|---------|
| `config/.env` | 生产环境配置 | 生产部署 |
| `config/.env.development` | 开发环境配置 | 本地开发 |
| `config/.env.testing` | 测试环境配置 | 测试验证 |
| `config/.env.template` | 配置模板 | 新环境初始化 |

### 2.2 配置继承关系

```
平台统一配置 (config/unified/.env.base)
    ↓ 继承
专利系统配置 (config/.env)
    ↓ 覆盖
本地配置 (.env.local)
```

### 2.3 主要配置项

#### 基础配置
```bash
# 环境标识
PATENT_ENV=production
PATENT_VERSION=3.0.0

# 平台路径（继承）
ATHENA_HOME=/Users/xujian/Athena工作平台
MODEL_PATH=${ATHENA_HOME}/models
```

#### 数据库配置
```bash
# Qdrant向量数据库
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=patent_full_text_v2

# NebulaGraph图数据库
NEBULA_HOST=127.0.0.1
NEBULA_PORT=9669
NEBULA_SPACE_NAME=patent_full_text_v2

# Redis缓存
REDIS_HOST=localhost
REDIS_PORT=6379
```

#### 模型配置
```bash
PATENT_EMBEDDING_MODEL=${MODEL_PATH}/patent/"BAAI/bge-m3"
PATENT_SEQUENCE_TAGGER=${MODEL_PATH}/patent/chinese_legal_electra
```

#### 性能配置
```bash
PATENT_BATCH_SIZE=10
PATENT_MAX_WORKERS=4
PATENT_CACHE_TTL=3600
```

---

## 三、快速开始

### 3.1 初始化环境

```bash
cd /Users/xujian/Athena工作平台/production/dev/scripts/patent_full_text

# 使用配置管理工具初始化
python config_manager.py init --env production
```

### 3.2 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 3.3 健康检查

```bash
# 执行健康检查
python health_check.py

# 或使用curl
curl http://localhost:8000/health
```

### 3.4 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

---

## 四、配置管理工具

### 4.1 验证配置

```bash
python config_manager.py validate --env production
```

### 4.2 切换环境

```bash
python config_manager.py switch --env development
```

### 4.3 显示配置

```bash
python config_manager.py show --env production
```

### 4.4 初始化环境

```bash
python config_manager.py init --env production
```

---

## 五、服务说明

### 5.1 服务列表

| 服务 | 容器名 | 端口 | 说明 |
|------|--------|------|------|
| Qdrant | patent_qdrant | 6333, 6334 | 向量数据库 |
| Nebula Meta | patent_nebula_metad | 9559, 19559 | 图元数据 |
| Nebula Storage | patent_nebula_storaged | 9779, 19779 | 图存储 |
| Nebula Graph | patent_nebula_graphd | 9669, 19669 | 图查询 |
| Redis | patent_redis | 6379 | 缓存 |
| App | patent_app | 8000 | 主应用 |

### 5.2 数据卷

| 卷名 | 用途 |
|------|------|
| patent_qdrant_storage | Qdrant数据 |
| patent_nebula_meta | Nebula元数据 |
| patent_nebula_storage | Nebula存储数据 |
| patent_redis_data | Redis持久化数据 |

---

## 六、API接口

### 6.1 健康检查

```bash
GET /health
```

响应：
```json
{
  "status": "healthy",
  "version": "3.0.0",
  "timestamp": "2025-12-25T00:00:00Z",
  "services": {
    "qdrant": true,
    "nebula": true,
    "redis": true
  }
}
```

### 6.2 专利处理

```bash
POST /api/v1/patent/process
```

请求：
```json
{
  "patent_number": "CN112233445A",
  "title": "专利标题",
  "abstract": "专利摘要",
  "ipc_classification": "G06F40/00",
  "claims": "权利要求内容",
  "invention_content": "发明内容"
}
```

### 6.3 PDF下载

```bash
POST /api/v1/patent/download
```

请求：
```json
{
  "patent_numbers": ["CN112233445A", "US8460931B2"],
  "metadata": {
    "source": "test",
    "case_id": "TEST-001"
  }
}
```

---

## 七、监控和日志

### 7.1 日志位置

```bash
# 应用日志
${PATENT_LOG_PATH}/patent_processing.log
${PATENT_LOG_PATH}/patent_processing.jsonl

# Nginx日志
/var/log/infrastructure/infrastructure/nginx/patent_access.log
/var/log/infrastructure/infrastructure/nginx/patent_error.log
```

### 7.2 监控指标

- 处理成功率
- 平均响应时间
- 向量化延迟
- 数据库连接状态
- 缓存命中率

### 7.3 告警配置

```bash
# 启用告警
PATENT_ENABLE_ALERTS=true
PATENT_ALERT_THRESHOLD=0.95
```

---

## 八、故障排查

### 8.1 常见问题

#### Qdrant连接失败
```bash
# 检查Qdrant容器状态
docker ps | grep qdrant
docker logs patent_qdrant

# 检查端口
netstat -an | grep 6333
```

#### NebulaGraph启动失败
```bash
# 检查Nebula容器状态
docker ps | grep nebula
docker logs patent_nebula_graphd

# 检查配置
cat config/nebula/nebula-graphd.conf
```

#### 模型加载失败
```bash
# 检查模型文件
ls -la ${PATENT_MODEL_PATH}/

# 检查模型路径
echo $PATENT_EMBEDDING_MODEL
```

### 8.2 重置服务

```bash
# 完全重置
docker-compose down -v
docker-compose up -d

# 重置单个服务
docker-compose restart qdrant
```

---

## 九、生产部署

### 9.1 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 8GB+ 内存
- 50GB+ 磁盘空间

### 9.2 部署步骤

1. **准备环境**
   ```bash
   # 克隆代码
   git clone <repository>
   cd Athena工作平台/production/dev/scripts/patent_full_text
   ```

2. **配置环境**
   ```bash
   # 复制配置模板
   cp config/.env.template config/.env

   # 修改配置
   vi config/.env
   ```

3. **初始化系统**
   ```bash
   python config_manager.py init --env production
   ```

4. **启动服务**
   ```bash
   docker-compose up -d
   ```

5. **验证部署**
   ```bash
   python health_check.py
   ```

### 9.3 性能调优

#### 批处理优化
```bash
# 根据服务器资源调整
PATENT_BATCH_SIZE=20        # 批量大小
PATENT_MAX_WORKERS=8        # 工作线程
```

#### 缓存优化
```bash
# 延长缓存时间
PATENT_CACHE_TTL=7200       # 2小时
PATENT_MEMORY_CACHE_MAX_SIZE=20000
```

---

## 十、备份和恢复

### 10.1 数据备份

```bash
# Qdrant备份
docker exec patent_qdrant \
  curl -X GET http://localhost:6333/collections/patent_full_text_v2/snapshot

# Nebula备份
docker exec patent_nebula_graphd \
  nebula-backup --hosts=nebula-graphd:9669 \
  --path=/data/backup --meta=nebula-metad:9559
```

### 10.2 配置备份

```bash
# 备份配置文件
tar -czf patent_config_backup_$(date +%Y%m%d).tar.gz config/
```

---

## 十一、更新和升级

### 11.1 更新代码

```bash
# 拉取最新代码
git pull origin main

# 重新构建镜像
docker-compose build

# 重启服务
docker-compose up -d
```

### 11.2 数据迁移

```bash
# 导出数据
docker exec patent_app python dev/scripts/export_data.py

# 导入数据
docker exec patent_app python dev/scripts/import_data.py
```

---

## 十二、安全建议

1. **修改默认密码**
   ```bash
   REDIS_PASSWORD=<your_secure_password>
   NEBULA_PASSWORD=<your_secure_password>
   ```

2. **启用HTTPS**
   ```nginx
   server {
       listen 443 ssl http2;
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
   }
   ```

3. **配置防火墙**
   ```bash
   # 只开放必要端口
   ufw allow 80/tcp
   ufw allow 443/tcp
   ```

4. **定期备份**
   ```bash
   # 设置定时任务
   0 2 * * * /path/to/backup.sh
   ```

---

## 附录

### A. 配置参考

- [平台统一配置](/config/unified/.env.base)
- [Docker Compose参考](https://docs.docker.com/compose/)
- [Qdrant文档](https://qdrant.tech/documentation/)
- [NebulaGraph文档](https://docs.nebula-graph.io/)

### B. 联系方式

- 技术支持: xujian519@gmail.com
- 项目仓库: Athena工作平台
