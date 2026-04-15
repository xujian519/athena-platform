# Athena工作平台 - 快速启动指南

## 🚀 一键启动

```bash
# 启动所有基础设施服务
./scripts/deploy-all.sh start
```

---

## 📋 服务地址

| 服务 | 地址 | 凭证 |
|------|------|------|
| Prometheus | http://localhost:9090 | - |
| Grafana | http://localhost:3000 | admin/admin123 |
| Redis | localhost:6379 | 见.env |
| Qdrant | http://localhost:6333 | - |
| Neo4j | http://localhost:7474 | neo4j/见.env |

---

## 🔧 常用命令

```bash
# 停止服务
./scripts/deploy-all.sh stop

# 重启服务
./scripts/deploy-all.sh restart

# 查看状态
./scripts/deploy-all.sh status

# 查看日志
./scripts/deploy-all.sh logs [service_name]

# 显示帮助
./scripts/deploy-all.sh help
```

---

## 📦 Poetry依赖

```bash
# 安装依赖
poetry install

# 激活虚拟环境
poetry shell

# 添加依赖
poetry add package-name
```

---

## ⚙️ 环境配置

```bash
# 复制环境变量文件
cp .env.example .env

# 编辑配置
vim .env
```

---

## 🐛 故障排查

```bash
# 查看服务日志
docker compose logs [service_name]

# 重启服务
docker compose restart [service_name]

# 清理并重启
docker compose down -v
docker compose up -d
```

---

## 📚 更多文档

- [完整部署指南](DEPLOYMENT_GUIDE.md)
- [项目README](README.md)
- [架构文档](docs/architecture.md)

---

**最后更新**: 2026-01-27
