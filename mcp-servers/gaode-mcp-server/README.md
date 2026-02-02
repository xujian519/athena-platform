# 🗺️ 高德地图MCP服务器

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-1.0.0-orange.svg)](https://modelcontextprotocol.io)

为AI模型提供地理空间智能服务的MCP (Model Context Protocol) 服务器。

## 🎯 功能特性

### 🌟 核心功能
- **地理编码**: 地址与坐标的相互转换
- **POI搜索**: 关键字搜索、周边搜索、多边形搜索
- **路径规划**: 驾车、步行、骑行、公交路径规划
- **地图服务**: 静态地图、天气信息查询
- **地理围栏**: 地理围栏的创建、查询和管理

### 🚀 技术优势
- **标准化接口**: 基于MCP协议的标准化工具接口
- **高性能**: 异步处理，支持并发请求
- **智能限流**: 自动API限流，避免超出配额
- **错误处理**: 完善的错误处理和重试机制
- **缓存支持**: Redis/内存缓存，提升响应速度

## 📋 系统要求

- Python 3.8+
- 高德地图API密钥
- 可选: Redis (用于缓存)

## 🚀 快速开始

### 1. 安装依赖

```bash
# 克隆项目
git clone https://github.com/athena-platform/amap-mcp-server.git
cd amap-mcp-server

# 安装依赖
pip install -r requirements.txt

# 开发模式安装
pip install -e .
```

### 2. 配置API密钥

```bash
# 复制配置文件
cp .env.example .env

# 编辑配置文件，填入你的高德地图API密钥
nano .env
```

在 `.env` 文件中配置：

```env
AMAP_API_KEY=your_amap_api_key_here
AMAP_SECRET_KEY=your_amap_secret_key_here
```

### 3. 运行服务器

```bash
# 直接运行
python -m amap_mcp_server.server

# 或使用脚本
./scripts/start.sh
```

### 4. 配置MCP客户端

在你的MCP客户端配置中添加：

```json
{
  "mcpServers": {
    "gaode-maps": {
      "command": "python",
      "args": ["-m", "amap_mcp_server.server"],
      "env": {
        "AMAP_API_KEY": "your_api_key",
        "AMAP_SECRET_KEY": "your_secret_key"
      }
    }
  }
}
```

## 📖 API文档

### 地理编码工具 (`gaode_geocode`)

将地址转换为坐标或坐标转换为地址。

```json
{
  "tool": "gaode_geocode",
  "arguments": {
    "operation": "geocode",
    "address": "北京市海淀区中关村",
    "city": "北京"
  }
}
```

**参数说明:**
- `operation`: 操作类型 (`"geocode"` 或 `"reverse_geocode"`)
- `address`: 地址文本 (地理编码时必需)
- `location`: 坐标点 `"经度,纬度"` (逆地理编码时必需)
- `city`: 城市名称 (可选)
- `radius`: 搜索半径 (逆地理编码时使用，默认1000米)

### POI搜索工具 (`gaode_poi_search`)

搜索兴趣点信息。

```json
{
  "tool": "gaode_poi_search",
  "arguments": {
    "search_type": "around",
    "keywords": "餐厅",
    "location": "116.397428,39.90923",
    "radius": 1000,
    "page": 1,
    "offset": 20
  }
}
```

**搜索类型:**
- `text`: 关键字搜索
- `around`: 周边搜索
- `polygon`: 多边形搜索

**参数说明:**
- `search_type`: 搜索类型
- `keywords`: 搜索关键词
- `location`: 中心点坐标 (周边和多边形搜索时必需)
- `radius`: 搜索半径 (周边搜索时使用)
- `polygon`: 多边形坐标点 (多边形搜索时使用)
- `city`: 城市名称
- `page`: 页码
- `offset`: 每页数量

## 🔧 配置选项

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `AMAP_API_KEY` | - | 高德地图API密钥 (必需) |
| `AMAP_SECRET_KEY` | - | 高德地图安全密钥 |
| `AMAP_RATE_LIMIT_RPM` | 100 | 每分钟请求限制 |
| `AMAP_RATE_LIMIT_RPS` | 2 | 每秒请求限制 |
| `AMAP_CACHE_ENABLED` | `true` | 是否启用缓存 |
| `AMAP_CACHE_TTL` | `300` | 缓存过期时间(秒) |
| `MCP_LOG_LEVEL` | `INFO` | 日志级别 |

### 缓存配置

支持两种缓存策略：

1. **内存缓存** (默认)
   ```env
   CACHE_STRATEGY=memory
   MAX_CACHE_SIZE=1000
   ```

2. **Redis缓存**
   ```env
   CACHE_STRATEGY=redis
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0
   ```

## 🧪 测试

```bash
# 运行单元测试
pytest tests/

# 运行集成测试
pytest tests/integration/

# 生成覆盖率报告
pytest --cov=amap_mcp_server --cov-report=html
```

## 📁 项目结构

```
amap-mcp-server/
├── src/amap_mcp_server/          # 源代码
│   ├── server.py                 # MCP服务器主入口
│   ├── config.py                 # 配置管理
│   ├── api/                      # API客户端
│   │   └── gaode_client.py       # 高德地图API客户端
│   ├── tools/                    # MCP工具实现
│   │   ├── geocoding.py          # 地理编码工具
│   │   ├── poi_search.py         # POI搜索工具
│   │   ├── route_planning.py     # 路径规划工具
│   │   ├── map_service.py        # 地图服务工具
│   │   └── geofence.py           # 地理围栏工具
│   └── utils/                    # 工具函数
├── config/                       # 配置文件
├── tests/                        # 测试文件
├── docs/                         # 文档
├── scripts/                      # 脚本文件
├── requirements.txt              # Python依赖
├── pyproject.toml               # 项目配置
└── README.md                    # 项目说明
```

## 🚀 部署

### Docker部署

```bash
# 构建镜像
docker build -t gaode-mcp-server .

# 运行容器
docker run -d \
  --name gaode-mcp-server \
  -e AMAP_API_KEY=your_api_key \
  -e AMAP_SECRET_KEY=your_secret_key \
  -p 8080:8080 \
  gaode-mcp-server
```

### Kubernetes部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gaode-mcp-server
spec:
  replicas: 2
  selector:
    matchLabels:
      app: gaode-mcp-server
  template:
    metadata:
      labels:
        app: gaode-mcp-server
    spec:
      containers:
      - name: gaode-mcp-server
        image: gaode-mcp-server:latest
        env:
        - name: AMAP_API_KEY
          valueFrom:
            secretKeyRef:
              name: amap-secrets
              key: api-key
        - name: AMAP_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: amap-secrets
              key: secret-key
```

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [高德地图开放平台](https://lbs.amap.com/) - 提供强大的地图API服务
- [MCP协议](https://modelcontextprotocol.io/) - 标准化的AI工具协议

## 📞 支持

如果你在使用过程中遇到问题，可以通过以下方式获取帮助：

- 🐛 [提交Issue](https://github.com/athena-platform/amap-mcp-server/issues)
- 📧 邮件: xujian519@gmail.com
- 📖 [查看文档](https://github.com/athena-platform/amap-mcp-server/wiki)

---

⭐ 如果这个项目对你有帮助，请给我们一个星标！