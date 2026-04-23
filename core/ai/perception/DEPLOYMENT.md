# 感知模块部署指南

## 系统要求

### 最低配置

- **操作系统**: Linux (Ubuntu 20.04+, CentOS 8+), macOS 11+, Windows 10+
- **Python**: 3.14 或更高版本
- **内存**: 4GB RAM (推荐 8GB+)
- **磁盘**: 10GB 可用空间
- **CPU**: 2核心 (推荐 4核心+)

### 推荐配置

- **操作系统**: Ubuntu 22.04 LTS
- **Python**: 3.14+
- **内存**: 16GB RAM
- **磁盘**: 50GB SSD
- **CPU**: 8核心 CPU
- **网络**: 千兆网络

## 安装步骤

### 1. 环境准备

#### Ubuntu/Debian

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装系统依赖
sudo apt install -y python3 python3-pip python3-venv
sudo apt install -y build-essential
sudo apt install -y libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1

# 安装Tesseract OCR
sudo apt install -y tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-chi-tra

# 安装OpenCV依赖
sudo apt install -y libopencv-dev python3-opencv
```

#### macOS

```bash
# 使用Homebrew安装依赖
brew install python@3.14
brew install tesseract
brew install opencv

# 安装XQuartz（用于某些图像处理功能）
brew install --cask xquartz
```

#### Windows

```powershell
# 安装Python 3.14
# 从 https://www.python.org/downloads/ 下载安装

# 安装Tesseract OCR
# 从 https://github.com/UB-Mannheim/tesseract/wiki 下载安装

# 安装Visual C++ Build Tools
# 从 https://visualstudio.microsoft.com/visual-cpp-build-tools/ 下载安装
```

### 2. 创建虚拟环境

```bash
# 进入项目目录
cd /path/to/Athena工作平台

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 3. 安装依赖

```bash
# 安装核心依赖
pip install -e .

# 或使用Poetry（推荐）
poetry install

# 安装可选依赖
pip install opencv-python paddleocr
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### 4. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
nano .env
```

**必需的环境变量**:

```bash
# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/var/log/perception.log

# 性能配置
MAX_CONCURRENT_REQUESTS=100
CACHE_TTL=3600
BATCH_SIZE=50
REQUEST_TIMEOUT=30.0

# 安全配置
ENABLE_AUTH=true
API_KEY=your_api_key_here

# 缓存配置
REDIS_URL=redis://localhost:6379
CACHE_BACKEND=redis
```

### 5. 初始化数据库

```bash
# 如果使用PostgreSQL
createdb athena_perception
psql athena_perception < schema.sql

# 如果使用Redis
redis-server --daemonize yes

# 如果使用Neo4j
# 按照Neo4j官方文档进行安装和配置
```

### 6. 验证安装

```bash
# 运行测试套件
pytest core/perception/tests/ -v

# 检查模块导入
python3 -c "from core.perception import PerceptionEngine; print('导入成功')"

# 运行健康检查
python3 -m core.perception.tools.health_check
```

## 部署模式

### 开发模式

```bash
# 启动开发服务器
export ENV=development
python3 -m core.perception.dev_server
```

### 生产模式

#### 使用Systemd (Linux)

```bash
# 创建systemd服务文件
sudo nano /etc/systemd/system/perception.service
```

```ini
[Unit]
Description=Athena Perception Module
After=network.target

[Service]
Type=simple
User=athena
WorkingDirectory=/path/to/Athena工作平台
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python3 -m core.perception.server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable perception
sudo systemctl start perception
sudo systemctl status perception
```

#### 使用Supervisor

```bash
# 安装Supervisor
sudo apt install -y supervisor

# 创建配置文件
sudo nano /etc/supervisor/conf.d/perception.conf
```

```ini
[program:perception]
command=/path/to/venv/bin/python3 -m core.perception.server
directory=/path/to/Athena工作平台
user=athena
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/perception.log
```

```bash
# 启动服务
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start perception
```

### Docker部署

#### Dockerfile

```dockerfile
FROM python:3.14-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python3", "-m", "core.perception.server"]
```

#### Docker Compose

```yaml
version: '3.8'

services:
  perception:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f perception
```

## 配置优化

### 性能调优

```python
# production_config.py
PERCEPTION_CONFIG = {
    # 并发配置
    "max_concurrent_requests": 100,
    "max_batch_size": 50,
    "request_timeout": 30.0,

    # 缓存配置
    "enable_cache": True,
    "cache_ttl": 3600,
    "cache_backend": "redis",
    "cache_max_size": 10000,

    # 监控配置
    "enable_monitoring": True,
    "monitoring_interval": 1.0,

    # 日志配置
    "log_level": "INFO",
    "log_rotation": True,
    "log_max_size": "100MB",
    "log_backup_count": 10,
}
```

### 安全加固

```bash
# 1. 设置文件权限
chmod 600 .env
chmod 700 core/perception/tests/

# 2. 配置防火墙
sudo ufw allow 8000/tcp
sudo ufw enable

# 3. 设置SSL/TLS（使用Nginx反向代理）
sudo apt install -y nginx
sudo nginx -V
```

### Nginx反向代理配置

```nginx
server {
    listen 80;
    server_name perception.example.com;

    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name perception.example.com;

    ssl_certificate /etc/ssl/certs/perception.crt;
    ssl_certificate_key /etc/ssl/private/perception.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 文件上传大小限制
    client_max_body_size 100M;
}
```

## 监控和日志

### 日志配置

```python
import logging
from logging.handlers import RotatingFileHandler

# 配置日志
logger = logging.getLogger("perception")
logger.setLevel(logging.INFO)

# 文件处理器（自动轮转）
file_handler = RotatingFileHandler(
    '/var/log/perception.log',
    maxBytes=100*1024*1024,  # 100MB
    backupCount=10
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logger.addHandler(file_handler)

# 控制台处理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
))
logger.addHandler(console_handler)
```

### 性能监控

```bash
# 启用Prometheus监控
pip install prometheus-fastapi-instrumentator

# 在应用中启用
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app)
```

### 健康检查

```bash
# 创建健康检查脚本
cat > /usr/local/bin/check_perception_health.sh << 'EOF'
#!/bin/bash
response=$(curl -s http://localhost:8000/health)
status=$(echo $response | jq -r '.status')

if [ "$status" == "healthy" ]; then
    echo "✅ 感知模块健康"
    exit 0
else
    echo "❌ 感知模块异常"
    exit 1
fi
EOF

chmod +x /usr/local/bin/check_perception_health.sh

# 添加到crontab
*/5 * * * * /usr/local/bin/check_perception_health.sh
```

## 故障排查

### 常见问题

#### 1. 模块导入错误

**问题**: `ImportError: No module named 'core'`

**解决方案**:
```bash
# 设置正确的Python路径
export PYTHONPATH=/path/to/Athena工作平台:$PYTHONPATH

# 或者在代码中添加
import sys
sys.path.insert(0, '/path/to/Athena工作平台')
```

#### 2. OpenCV导入错误

**问题**: `ImportError: libGL.so.1: cannot open shared object file`

**解决方案**:
```bash
# Ubuntu/Debian
sudo apt install -y libgl1-mesa-glx

# CentOS/RHEL
sudo yum install -y mesa-libGL
```

#### 3. 内存不足错误

**问题**: `MemoryError` 或系统变慢

**解决方案**:
```bash
# 减少并发请求数
export MAX_CONCURRENT_REQUESTS=50

# 或在配置文件中设置
PERCEPTION_CONFIG["max_concurrent_requests"] = 50
```

#### 4. 权限错误

**问题**: `PermissionDenied` 异常

**解决方案**:
```python
from core.perception.access_control import get_global_access_control, Permission

# 授予必要权限
access_control = get_global_access_control()
access_control.grant_permission("user_id", Permission.PROCESS_IMAGE)
```

### 日志查看

```bash
# 应用日志
tail -f /var/log/perception.log

# 错误日志
grep ERROR /var/log/perception.log

# 性能日志
grep "PERFORMANCE" /var/log/perception.log

# 系统服务日志（如果使用systemd）
sudo journalctl -u perception -f
```

## 备份和恢复

### 数据备份

```bash
# 备份配置文件
tar -czf perception-config-backup-$(date +%Y%m%d).tar.gz \
    .env config/ *.conf

# 备份日志
tar -czf perception-logs-backup-$(date +%Y%m%d).tar.gz \
    /var/log/perception/

# 备份缓存数据
redis-cli --rdb /var/lib/redis/dump.rdb
```

### 数据恢复

```bash
# 恢复配置
tar -xzf perception-config-backup-20260126.tar.gz

# 恢复Redis数据
redis-cli --rdb /var/lib/redis/dump.rdb
```

## 更新和升级

### 滚动更新

```bash
# 1. 备份当前版本
cp -r core/perception core/perception.backup

# 2. 拉取最新代码
git pull origin main

# 3. 更新依赖
pip install -r requirements.txt --upgrade

# 4. 运行测试
pytest core/perception/tests/

# 5. 重启服务
sudo systemctl restart perception

# 6. 验证更新
curl http://localhost:8000/health
```

### 回滚

```bash
# 如果更新出现问题，回滚到备份版本
rm -rf core/perception
mv core/perception.backup core/perception

# 重启服务
sudo systemctl restart perception
```

## 安全检查清单

部署前必须确认：

- [ ] 移除所有硬编码的敏感信息
- [ ] 配置环境变量和密钥管理
- [ ] 启用输入验证和权限控制
- [ ] 配置HTTPS/TLS加密
- [ ] 设置防火墙规则
- [ ] 配置日志监控和告警
- [ ] 完成安全审计
- [ ] 测试备份和恢复流程

## 性能基准

部署后应达到的性能指标：

- **响应时间**: P95 < 5秒, P99 < 10秒
- **吞吐量**: > 100 req/s
- **错误率**: < 1%
- **可用性**: > 99.9%
- **内存使用**: < 8GB (正常负载)

## 支持和维护

### 获取帮助

- 查看文档: [README.md](README.md)
- 提交问题: [GitHub Issues](https://github.com/your-repo/issues)
- 邮件支持: support@athena-platform.com

### 定期维护

- 每日: 检查日志和告警
- 每周: 审查性能指标
- 每月: 安全更新和补丁
- 每季度: 备份验证和灾难恢复演练

---

**最后更新**: 2026-01-26
**维护者**: Athena AI System Team
