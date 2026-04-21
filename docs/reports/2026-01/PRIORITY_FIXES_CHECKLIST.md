# Athena工作平台部署配置 - 优先修复项清单

生成时间: 2026-01-26
优先级: P0 (立即修复)

---

## 🔴 P0级别 - 立即修复（本周必须完成）

### 1. 移除硬编码的API密钥
**位置**: `/Users/xujian/Athena工作平台/production/config/docker/docker-compose.production.yml`

**问题**:
```yaml
# 第95行
API_KEY_PROD=74207bed56b28b4faa4a7981d4e0b783f14f2e8a000adae2aa41f56b8ee2f7d6
```

**修复方案**:
```yaml
# 修改为环境变量
API_KEY_PROD=${API_KEY_PROD:-}
```

**验证命令**:
```bash
grep -r "74207bed56b28b4faa4a7981d4e0b783f14f2e8a000adae2aa41f56b8ee2f7d6" /Users/xujian/Athena工作平台/production/config/docker/
```

---

### 2. 统一PostgreSQL连接配置
**位置**: 
- `/Users/xujian/Athena工作平台/production/config/docker/docker-compose.core-services.yml`
- `/Users/xujian/Athena工作平台/production/config/docker/docker-compose.production.yml`

**问题**:
```yaml
# core-services.yml - 正确
POSTGRES_HOST: host.docker.internal

# production.yml - 不正确
POSTGRES_HOST: localhost
network_mode: host
```

**修复方案**:
```yaml
# 统一使用host.docker.internal
POSTGRES_HOST: host.docker.internal
POSTGRES_PORT: 5432
# 移除 network_mode: host
```

---

### 3. 统一Qdrant服务名称
**位置**: 所有Docker Compose文件

**问题**:
- `infrastructure.yml`: 服务名`qdrant`
- `unified-databases.yml`: 服务名`athena-qdrant`
- `production.yml`: 服务名`qdrant`但端口映射不同

**修复方案**:
```yaml
# 统一服务名
athena-qdrant:
  image: qdrant/qdrant:latest
  container_name: athena_qdrant
  ports:
    - "6333:6333"  # 统一端口
    - "6334:6334"
```

---

### 4. 移除不安全的默认密码
**位置**: 所有Docker Compose文件

**问题**:
```yaml
POSTGRES_PASSWORD=${DB_PASSWORD:-athena123}
REDIS_PASSWORD=${REDIS_PASSWORD:-redis123}
```

**修复方案**:
```yaml
# 强制要求设置密码
POSTGRES_PASSWORD=${DB_PASSWORD:?DB_PASSWORD not set}
REDIS_PASSWORD=${REDIS_PASSWORD:?REDIS_PASSWORD not set}
```

---

### 5. 创建根目录pyproject.toml
**位置**: `/Users/xujian/Athena工作平台/pyproject.toml`

**操作**: 创建文件

**内容示例**:
```toml
[tool.poetry]
name = "athena-platform"
version = "1.0.0"
description = "Athena工作平台 - 企业级AI智能平台"
authors = ["xujian <xujian519@gmail.com>"]
readme = "README.md"
packages = [
    { include = "core" },
    { include = "services" },
    { include = "apps" },
]

[tool.poetry.dependencies]
python = "^3.14"
fastapi = "^0.104.0"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
pydantic = "^2.5.0"
sqlalchemy = "^2.0.23"
asyncpg = "^0.29.0"
redis = "^5.0.1"
qdrant-client = "^1.7.0"
neo4j = "^5.14.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.3"
pytest-asyncio = "^0.21.1"
pytest-cov = "^4.1.0"
black = "^23.12.1"
ruff = "^0.1.9"
mypy = "^1.8.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

---

### 6. 添加环境变量验证脚本
**位置**: `/Users/xujian/Athena工作平台/scripts/validate_env.py`

**操作**: 创建文件

**内容**:
```python
#!/usr/bin/env python3
"""环境变量验证脚本"""
import os
import sys
from pathlib import Path

# 必需的环境变量
REQUIRED_VARS = {
    "DB_PASSWORD": "PostgreSQL密码",
    "REDIS_PASSWORD": "Redis密码",
    "JWT_SECRET": "JWT密钥",
}

# 可选的环境变量
OPTIONAL_VARS = {
    "OPENAI_API_KEY": "OpenAI API密钥",
    "ZHIPU_API_KEY": "智谱AI API密钥",
    "GAODE_API_KEY": "高德地图API密钥",
    "JINA_API_KEY": "Jina AI API密钥",
    "SEMANTIC_SCHOLAR_API_KEY": "Semantic Scholar API密钥",
    "GITHUB_TOKEN": "GitHub Token",
}

def validate_required():
    """验证必需的环境变量"""
    print("🔍 检查必需的环境变量...")
    missing = []
    for var, desc in REQUIRED_VARS.items():
        value = os.environ.get(var)
        if not value:
            missing.append(f"  ❌ {var} ({desc})")
        else:
            print(f"  ✅ {var}")
    
    if missing:
        print("\n❌ 缺少必需的环境变量:")
        for m in missing:
            print(m)
        return False
    
    print("✅ 所有必需的环境变量已配置\n")
    return True

def validate_optional():
    """验证可选的环境变量"""
    print("🔍 检查可选的环境变量...")
    missing = []
    for var, desc in OPTIONAL_VARS.items():
        value = os.environ.get(var)
        if not value:
            missing.append(f"  ⚠️  {var} ({desc})")
        else:
            print(f"  ✅ {var}")
    
    if missing:
        print("\n⚠️  缺少可选的环境变量:")
        for m in missing:
            print(m)
        print("提示: 这些变量是可选的，但某些功能可能不可用\n")
    else:
        print("✅ 所有可选的环境变量已配置\n")
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("Athena工作平台 - 环境变量验证")
    print("=" * 60)
    print()
    
    # 检查.env文件
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env文件不存在")
        print("请从.env.example复制并填写实际值:")
        print("  cp .env.example .env")
        sys.exit(1)
    
    # 加载.env文件
    from dotenv import load_dotenv
    load_dotenv()
    
    # 验证环境变量
    required_ok = validate_required()
    optional_ok = validate_optional()
    
    if not required_ok:
        sys.exit(1)
    
    print("=" * 60)
    print("✅ 环境变量验证通过")
    print("=" * 60)

if __name__ == "__main__":
    main()
```

---

### 7. 创建统一部署脚本
**位置**: `/Users/xujian/Athena工作平台/deploy.sh`

**操作**: 创建文件并添加执行权限

**内容**:
```bash
#!/bin/bash
# Athena工作平台 - 统一部署脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 环境验证
validate_environment() {
    log_info "验证环境配置..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装"
        exit 1
    fi
    
    # 检查环境变量文件
    if [ ! -f .env ]; then
        log_error ".env文件不存在"
        exit 1
    fi
    
    # 验证环境变量
    if command -v python3 &> /dev/null; then
        python3 scripts/validate_env.py
    else
        log_warn "Python3未找到，跳过环境变量验证"
    fi
    
    log_info "环境验证完成"
}

# 部署服务
deploy_services() {
    local environment=${1:-production}
    log_info "部署环境: $environment"
    
    cd production/config/docker
    
    # 拉取最新镜像
    log_info "拉取最新镜像..."
    docker-compose pull
    
    # 停止旧服务
    log_info "停止旧服务..."
    docker-compose down
    
    # 启动新服务
    log_info "启动新服务..."
    docker-compose up -d
    
    # 等待服务健康
    log_info "等待服务健康检查..."
    sleep 30
    
    # 检查服务状态
    docker-compose ps
}

# 主函数
main() {
    log_info "开始部署Athena工作平台..."
    
    validate_environment
    deploy_services "$@"
    
    log_info "部署完成！"
}

main "$@"
```

**添加执行权限**:
```bash
chmod +x /Users/xujian/Athena工作平台/deploy.sh
```

---

## 🟡 P1级别 - 重要优化（本月完成）

### 1. 统一环境变量命名规范

**当前问题**:
- `AMAP_API_KEY` vs `GAODE_API_KEY`
- `POSTGRES_HOST` vs `DB_HOST`
- 命名不一致

**统一命名规范**:
```bash
# 数据库 - DB_前缀
DB_POSTGRES_HOST=
DB_POSTGRES_PORT=
DB_POSTGRES_NAME=
DB_POSTGRES_USER=
DB_POSTGRES_PASSWORD=

DB_REDIS_HOST=
DB_REDIS_PORT=
DB_REDIS_PASSWORD=

# API密钥 - API_KEY_前缀
API_KEY_OPENAI=
API_KEY_ZHIPU=
API_KEY_GAODE=
API_KEY_JINA=

# 应用配置 - APP_前缀
APP_ENVIRONMENT=
APP_LOG_LEVEL=
APP_PORT=

# 安全配置 - SEC_前缀
SEC_JWT_SECRET=
SEC_ENCRYPTION_KEY=

# 监控配置 - MON_前缀
MON_PROMETHEUS_PORT=
MON_GRAFANA_PORT=
```

---

### 2. 整合网络配置

**当前问题**: 7个独立的网络

**修复方案**: 统一使用`athena-network`

```yaml
# 移除以下网络
- athena-infrastructure
- athena-core-services
- athena-mcp-servers
- athena-applications
- athena-monitoring
- unified-db-network
- athena-prod-network

# 统一使用
networks:
  athena-network:
    name: athena-network
    driver: bridge
    ipam:
      config:
        - subnet: 172.25.0.0/16
```

---

### 3. 添加配置验证脚本

**位置**: `/Users/xujian/Athena工作平台/scripts/validate_config.py`

**功能**:
- 检查Docker Compose配置语法
- 检查端口冲突
- 检查服务依赖
- 检查资源限制

---

### 4. 优化资源配置

**当前问题**: Qdrant过度配置，Redis配置不足

**优化方案**:
```yaml
qdrant:
  deploy:
    resources:
      limits:
        cpus: '2.0'  # 从4核降到2核
        memory: 8G   # 从16G降到8G

redis:
  deploy:
    resources:
      limits:
        cpus: '2.0'  # 从1核增加到2核
        memory: 4G   # 从2G增加到4G
```

---

### 5. 添加密钥管理方案

**方案1: Docker Secrets**
```bash
# 创建secrets
echo "your_password" | docker secret create db_password -
echo "your_password" | docker secret create redis_password -

# 在docker-compose.yml中使用
services:
  api:
    secrets:
      - db_password
    environment:
      DB_PASSWORD_FILE: /run/secrets/db_password

secrets:
  db_password:
    external: true
```

**方案2: HashiCorp Vault**
- 使用Vault管理所有密钥
- 实现密钥轮换
- 审计密钥使用

---

## 验证检查清单

完成修复后，使用以下检查清单验证：

```bash
# 1. 检查硬编码密钥是否已移除
grep -r "74207bed56b28b4faa4a7981d4e0b783f14f2e8a000adae2aa41f56b8ee2f7d6" production/config/docker/
# 预期: 无结果

# 2. 检查PostgreSQL连接是否统一
grep -r "POSTGRES_HOST: localhost" production/config/docker/
# 预期: 无结果

# 3. 检查Qdrant服务名是否统一
grep -r "container_name: qdrant" production/config/docker/
# 预期: 无结果

# 4. 检查默认密码是否已移除
grep -r "athena123\|redis123" production/config/docker/
# 预期: 无结果

# 5. 检查pyproject.toml是否存在
ls -la pyproject.toml
# 预期: 文件存在

# 6. 检查验证脚本是否存在
ls -la scripts/validate_env.py
# 预期: 文件存在

# 7. 检查部署脚本是否存在
ls -la deploy.sh
# 预期: 文件存在且可执行

# 8. 运行环境变量验证
python3 scripts/validate_env.py
# 预期: 验证通过

# 9. 测试Docker Compose配置
cd production/config/docker
docker-compose config
# 预期: 配置有效

# 10. 测试部署
./deploy.sh
# 预期: 部署成功
```

---

## 预期效果

完成P0级别修复后：
- ✅ 无硬编码密钥
- ✅ 配置一致性提升
- ✅ 安全性显著提高
- ✅ 部署流程标准化
- ✅ 环境验证自动化

---

**文档版本**: 1.0
**创建时间**: 2026-01-26
**责任人**: xujian
**审核人**: 待定
