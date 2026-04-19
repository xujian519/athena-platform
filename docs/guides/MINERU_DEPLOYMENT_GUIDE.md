# minerU OCR服务部署指南

> **部署日期**: 2026-04-19
> **服务版本**: minerU latest
> **服务端口**: 7860

---

## 快速部署

### 方法1: Docker快速启动（推荐）

```bash
# 1. 拉取镜像
docker pull mineru/mineru:latest

# 2. 启动服务
docker run -d \
  --name athena-mineru \
  -p 7860:7860 \
  --restart unless-stopped \
  -v ~/athena-mineru-models:/models \
  -v ~/athena-mineru-output:/output \
  -e MINERU_WORKERS=4 \
  -e MINERU_TIMEOUT=120 \
  mineru/mineru:latest

# 3. 查看日志
docker logs -f athena-mineru

# 4. 检查健康
curl http://localhost:7860/health
```

### 方法2: 使用Docker Compose（推荐用于生产）

创建 `~/athena-mineru/docker-compose.yml`:

```yaml
version: '3.8'

services:
  mineru:
    image: mineru/mineru:latest
    container_name: athena-mineru
    restart: unless-stopped
    ports:
      - "7860:7860"
    volumes:
      - ./models:/models:ro
      - ./output:/output
      - ./cache:/cache
    environment:
      - MINERU_PORT=7860
      - MINERU_HOST=0.0.0.0
      - MINERU_WORKERS=4
      - MINERU_TIMEOUT=120
      - MINERU_MAX_FILE_SIZE=52428800  # 50MB
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7860/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - athena-network

networks:
  athena-network:
    external: true
```

启动服务：

```bash
cd ~/athena-mineru
docker compose up -d

# 查看日志
docker compose logs -f mineru

# 停止服务
docker compose down
```

### 方法3: 源码安装

```bash
# 1. 克隆仓库
git clone https://github.com/opendatalab/MinerU.git ~/mineru
cd ~/mineru

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动服务
python3 -m mineru serve --port 7860

# 4. 后台运行
nohup python3 -m mineru serve --port 7860 > mineru.log 2>&1 &
```

---

## 配置优化

### 环境变量配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `MINERU_PORT` | 7860 | 服务端口 |
| `MINERU_HOST` | 0.0.0.0 | 监听地址 |
| `MINERU_WORKERS` | 4 | 并发处理数 |
| `MINERU_TIMEOUT` | 120 | 处理超时（秒） |
| `MINERU_MAX_FILE_SIZE` | 52428800 | 最大文件大小（字节） |
| `MINERU_CACHE_DIR` | /tmp/mineru_cache | 缓存目录 |

### 高级配置

```yaml
# config.yaml
mineru:
  # 服务配置
  host: 0.0.0.0
  port: 7860
  workers: 4

  # 处理配置
  timeout: 120
  max_file_size: 52428800  # 50MB

  # OCR配置
  ocr:
    engine: "paddleocr"  # 或 "tesseract"
    language: "ch"  # 中文
    confidence_threshold: 0.8

  # 缓存配置
  cache:
    enabled: true
    dir: /tmp/mineru_cache
    ttl: 3600

  # 输出配置
  output:
    format: "markdown"  # markdown, text, json
    extract_images: true
    extract_tables: true
```

---

## API测试

### 1. 健康检查

```bash
curl http://localhost:7860/health

# 预期响应
# {"status":"healthy","version":"x.x.x"}
```

### 2. PDF OCR测试

```bash
# 准备测试PDF
TEST_PDF="/path/to/test.pdf"

# 调用API
curl -X POST http://localhost:7860/api/v1/general \
  -H "Content-Type: application/json" \
  -d "{\"file\": \"$TEST_PDF\", \"extract_images\": true}"

# 或使用base64编码
curl -X POST http://localhost:7860/api/v1/general \
  -H "Content-Type: application/json" \
  -d "{\"file\": \"data:application/pdf;base64,$(base64 -i \"$TEST_PDF\")\", \"extract_images\": false}"
```

### 3. 图片OCR测试

```bash
# 准备测试图片
TEST_IMAGE="/path/to/test.png"

# 调用API
curl -X POST http://localhost:7860/api/v1/general \
  -H "Content-Type: application/json" \
  -d "{\"file\": \"data:image/png;base64,$(base64 -i \"$TEST_IMAGE\")\"}"
```

---

## 集成到Athena

### 1. 设置环境变量

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
export MINERU_API_URL="http://localhost:7860"
export MINERU_TIMEOUT="120"

# 或在项目 .env 文件中
echo "MINERU_API_URL=http://localhost:7860" >> .env
echo "MINERU_TIMEOUT=120" >> .env
```

### 2. 使用增强文档解析器

```python
from core.tools.enhanced_document_parser import parse_document

# 解析PDF
result = await parse_document(
    "/path/to/patent.pdf",
    use_ocr=True,
    extract_images=True,
    extract_tables=True
)

# 检查结果
if result["success"]:
    print(f"✅ 解析成功")
    print(f"   页数: {result.get('pages', 0)}")
    print(f"   内容长度: {len(result.get('content', ''))}")
    print(f"   OCR置信度: {result['metadata'].get('ocr_confidence', 0):.2%}")
else:
    print(f"❌ 解析失败: {result.get('error')}")
```

---

## 性能调优

### 1. 增加并发处理

```bash
# 修改docker-compose.yml
environment:
  - MINERU_WORKERS=8  # 增加到8个worker
```

### 2. 调整超时时间

```python
# 对于大文件，增加超时
import os
os.environ["MINERU_TIMEOUT"] = "300"  # 5分钟
```

### 3. 启用缓存

```bash
# 挂载缓存目录
docker run -v ~/athena-mineru-cache:/cache \
  -e MINERU_CACHE_DIR=/cache \
  mineru/mineru:latest
```

---

## 监控和日志

### 查看实时日志

```bash
# Docker方式
docker logs -f athena-mineru

# Docker Compose方式
docker compose logs -f mineru

# 源码方式
tail -f mineru.log
```

### 性能监控

```bash
# 查看资源使用
docker stats athena-mineru

# 查看进程
docker exec athena-mineru ps aux
```

---

## 故障排查

### 问题1: 服务启动失败

**症状**: 容器立即退出

**解决**:
```bash
# 查看详细日志
docker logs athena-mineru

# 检查端口占用
lsof -i :7860

# 检查磁盘空间
df -h
```

### 问题2: OCR识别率低

**症状**: 返回内容不正确或为空

**解决**:
- 检查输入文件质量
- 尝试不同的OCR引擎（paddleocr vs tesseract）
- 调整图片分辨率和对比度

### 问题3: 处理超时

**症状**: `OCR处理超时（>120秒）`

**解决**:
```bash
# 增加超时时间
docker run -e MINERU_TIMEOUT=300 mineru/mineru:latest

# 或减少worker数量避免资源竞争
docker run -e MINERU_WORKERS=2 mineru/mineru:latest
```

### 问题4: 内存不足

**症状**: OOM错误

**解决**:
```bash
# 增加Docker内存限制
docker run -m 4g mineru/mineru:latest

# 或减少并发
docker run -e MINERU_WORKERS=2 mineru/mineru:latest
```

---

## 生产环境部署

### 使用systemd管理

创建 `/etc/systemd/system/athena-mineru.service`:

```ini
[Unit]
Description=Athena minerU OCR Service
After=network.target

[Service]
Type=simple
User=athena
WorkingDirectory=/opt/athena-mineru
ExecStart=/usr/bin/python3 -m mineru serve --port 7860
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable athena-mineru
sudo systemctl start athena-mineru
sudo systemctl status athena-mineru
```

### 使用Nginx反向代理

创建 `/etc/nginx/conf.d/athena-mineru.conf`:

```nginx
upstream mineru {
    server localhost:7860;
}

server {
    listen 80;
    server_name mineru.athena.local;

    location / {
        proxy_pass http://mineru;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
    }
}
```

---

## 安全建议

### 1. 网络隔离

```bash
# 只监听本地
docker run -e MINERU_HOST=127.0.0.1 mineru/mineru:latest

# 或通过防火墙限制访问
sudo ufw allow from 192.168.1.0/24 to any port 7860
```

### 2. 文件大小限制

```bash
# 限制上传大小
docker run -e MINERU_MAX_FILE_SIZE=10485760 mineru/mineru:latest
# 10MB限制
```

### 3. 认证（如需要）

```bash
# 添加API密钥认证
docker run -e MINERU_API_KEY=your_secret_key mineru/mineru:latest
```

---

## 备份和恢复

### 备份配置

```bash
# 备份配置文件
docker cp athena-mineru:/config /backup/mineru-config

# 备份模型文件
tar -czf ~/backup/mineru-models-$(date +%Y%m%d).tar.gz ~/athena-mineru-models/
```

### 恢复配置

```bash
# 恢复配置
docker cp /backup/mineru-config athena-mineru:/config

# 重启服务
docker restart athena-mineru
```

---

## 总结

### 部署检查清单

- [ ] minerU服务运行正常
- [ ] 健康检查通过
- [ ] 端口7860可访问
- [ ] 环境变量已配置
- [ ] 日志正常输出
- [ ] 资源使用正常
- [ ] 与Athena集成测试通过

### 维护建议

1. **定期检查日志** - 每天查看错误日志
2. **监控资源使用** - CPU、内存、磁盘
3. **定期备份** - 配置和模型文件
4. **更新服务** - 跟随minerU版本更新

---

**文档版本**: v1.0
**最后更新**: 2026-04-19
**维护者**: Athena平台团队
