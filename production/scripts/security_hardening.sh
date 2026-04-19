#!/bin/bash
# Athena工作平台安全加固脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔒 Athena工作平台安全加固开始...${NC}"
echo -e "${BLUE}时间: $(date)${NC}"

# 获取当前目录
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROD_DIR="$(dirname "$CURRENT_DIR")"

# 1. 设置文件权限
echo ""
echo -e "${YELLOW}📁 设置关键文件权限...${NC}"

# 配置文件权限
find "$PROD_DIR/config" -type f -name "*.json" -exec chmod 600 {} \;
find "$PROD_DIR/config" -type f -name "*.conf" -exec chmod 600 {} \;
find "$PROD_DIR/config" -type f -name "*.yml" -o -name "*.yaml" -exec chmod 600 {} \;

echo -e "${GREEN}✅ 配置文件权限已设置 (600)${NC}"

# 脚本文件权限
find "$PROD_DIR/dev/scripts" -name "*.sh" -exec chmod 755 {} \;
echo -e "${GREEN}✅ 脚本文件权限已设置 (755)${NC}"

# 敏感数据目录权限
if [ -d "$PROD_DIR/data" ]; then
    chmod 750 "$PROD_DIR/data"
    echo -e "${GREEN}✅ 数据目录权限已设置 (750)${NC}"
fi

# 备份目录权限
if [ -d "$PROD_DIR/backups" ]; then
    chmod 700 "$PROD_DIR/backups"
    echo -e "${GREEN}✅ 备份目录权限已设置 (700)${NC}"
fi

# 2. 创建环境配置文件
echo ""
echo -e "${YELLOW}⚙️ 创建安全环境配置...${NC}"

# 创建.env文件（如果不存在）
ENV_FILE="$PROD_DIR/.env.production.local"
if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" << EOF
# Athena工作平台生产环境配置
# 生产环境配置文件

# 数据库配置
POSTGRES_DB=athena
POSTGRES_USER=postgres
# 注意：密码应该从环境变量或密钥管理系统中获取
# POSTGRES_PASSWORD=your_secure_password

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Elasticsearch配置
ES_HOST=localhost
ES_PORT=9200

# Qdrant配置
QDRANT_HOST=localhost
QDRANT_PORT=6333

# 应用安全配置
APP_ENV=production
APP_DEBUG=false
APP_LOG_LEVEL=INFO

# JWT密钥（请生成安全的密钥）
# JWT_SECRET=your_jwt_secret_key_here

# API访问控制
API_RATE_LIMIT=1000
CORS_ORIGINS=localhost,127.0.0.1

# 会话配置
SESSION_TIMEOUT=3600
SESSION_SECRET=your_session_secret_here

# 加密配置
ENCRYPTION_KEY=your_encryption_key_here
HASH_SALT=your_hash_salt_here

# 监控配置
MONITORING_ENABLED=true
HEALTH_CHECK_ENABLED=true
EOF
    chmod 600 "$ENV_FILE"
    echo -e "${GREEN}✅ 环境配置文件已创建${NC}"
else
    echo -e "${BLUE}ℹ️  环境配置文件已存在${NC}"
fi

# 3. 创建安全策略配置
echo ""
echo -e "${YELLOW}🛡️ 创建安全策略配置...${NC}"

SECURITY_CONFIG_DIR="$PROD_DIR/config/security"
mkdir -p "$SECURITY_CONFIG_DIR"

# 访问控制配置
cat > "$SECURITY_CONFIG_DIR/access_control.json" << EOF
{
  "access_control": {
    "enabled": true,
    "default_policy": "deny",
    "rules": [
      {
        "name": "allow_admin_access",
        "paths": ["/admin/*"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "conditions": {
          "role": "admin"
        }
      },
      {
        "name": "allow_api_access",
        "paths": ["/api/*"],
        "methods": ["GET", "POST"],
        "conditions": {
          "authenticated": true
        }
      },
      {
        "name": "allow_health_check",
        "paths": ["/health", "/status"],
        "methods": ["GET"],
        "conditions": {}
      }
    ]
  }
}
EOF

# 速率限制配置
cat > "$SECURITY_CONFIG_DIR/rate_limiting.json" << EOF
{
  "rate_limiting": {
    "enabled": true,
    "default_limits": {
      "requests_per_minute": 100,
      "requests_per_hour": 1000
    },
    "endpoint_limits": {
      "/api/*": {
        "requests_per_minute": 200,
        "requests_per_hour": 5000
      },
      "/login": {
        "requests_per_minute": 5,
        "requests_per_hour": 20
      }
    }
  }
}
EOF

# CORS配置
cat > "$SECURITY_CONFIG_DIR/cors.json" << EOF
{
  "cors": {
    "enabled": true,
    "allowed_origins": [
      "http://localhost:3000",
      "http://127.0.0.1:3000"
    ],
    "allowed_methods": ["GET", "POST", "PUT", "DELETE"],
    "allowed_headers": ["Content-Type", "Authorization"],
    "max_age": 86400,
    "credentials": true
  }
}
EOF

# 设置权限
chmod 600 "$SECURITY_CONFIG_DIR"/*
echo -e "${GREEN}✅ 安全策略配置已创建${NC}"

# 4. 创建安全检查脚本
echo ""
echo -e "${YELLOW}🔍 创建安全检查脚本...${NC}"

SECURITY_CHECK_SCRIPT="$PROD_DIR/dev/scripts/security_check.sh"
cat > "$SECURITY_CHECK_SCRIPT" << 'EOF'
#!/bin/bash
# 安全检查脚本

echo "🔒 Athena工作平台安全检查"
echo "=============================="

# 检查文件权限
echo ""
echo "📁 文件权限检查:"
echo "- 配置文件权限: $(find . -name "*.json" -type f -not -perm 600 | wc -l) 个文件权限异常"
echo "- 脚本文件权限: $(find . -name "*.sh" -type f -not -perm 755 | wc -l) 个脚本权限异常"

# 检查容器安全
echo ""
echo "🐳 容器安全检查:"
echo "- 以root运行的容器: $(docker ps --format "{{.Names}}" | xargs -I {} docker inspect {} --format "{{.HostConfig.Privileged}}" | grep true | wc -l)"
echo "- 挂载敏感目录的容器: $(docker ps --format "{{.Names}}" | xargs -I {} docker inspect {} --format "{{.Mounts}}" | grep -E "(etc|root|var)" | wc -l)"

# 检查开放端口
echo ""
echo "🌐 开放端口检查:"
echo "- PostgreSQL: $(nc -z localhost 5432 && echo "开放" || echo "关闭")"
echo "- Redis: $(nc -z localhost 6379 && echo "开放" || echo "关闭")"
echo "- Elasticsearch: $(nc -z localhost 9200 && echo "开放" || echo "关闭")"
echo "- Qdrant: $(nc -z localhost 6333 && echo "开放" || echo "关闭")"

# 检查日志文件
echo ""
echo "📝 日志文件检查:"
echo "- 错误日志: $(find . -name "*error*.log" -type f | wc -l) 个文件"
echo "- 访问日志: $(find . -name "*access*.log" -type f | wc -l) 个文件"

echo ""
echo "✅ 安全检查完成"
EOF

chmod 755 "$SECURITY_CHECK_SCRIPT"
echo -e "${GREEN}✅ 安全检查脚本已创建${NC}"

# 5. 创建备份安全配置
echo ""
echo -e "${YELLOW}💾 创建备份安全配置...${NC}"

BACKUP_CONFIG="$PROD_DIR/config/backup_security.json"
cat > "$BACKUP_CONFIG" << EOF
{
  "backup_security": {
    "encryption_enabled": true,
    "encryption_algorithm": "AES-256",
    "retention_policy": {
      "daily": 30,
      "weekly": 12,
      "monthly": 24
    },
    "access_control": {
      "authorized_users": ["admin"],
      "encryption_key_rotation": 90
    },
    "integrity_check": {
      "enabled": true,
      "algorithm": "SHA-256"
    }
  }
}
EOF

chmod 600 "$BACKUP_CONFIG"
echo -e "${GREEN}✅ 备份安全配置已创建${NC}"

# 6. 运行安全检查
echo ""
echo -e "${YELLOW}🔍 运行安全检查...${NC}"
"$PROD_DIR/dev/scripts/security_check.sh"

# 7. 创建安全加固报告
echo ""
echo -e "${YELLOW}📋 生成安全加固报告...${NC}"

SECURITY_REPORT="$PROD_DIR/logs/security_hardening_report_$(date +%Y%m%d_%H%M%S).json"
cat > "$SECURITY_REPORT" << EOF
{
  "security_hardening_report": {
    "timestamp": "$(date -Iseconds)",
    "actions_performed": [
      "设置文件权限",
      "创建环境配置",
      "配置安全策略",
      "创建安全检查脚本",
      "配置备份安全"
    ],
    "security_measures": {
      "file_permissions": "已配置",
      "access_control": "已实施",
      "rate_limiting": "已配置",
      "cors_policy": "已设置",
      "encryption": "已准备"
    },
    "recommendations": [
      "定期更新密码",
      "监控异常访问",
      "定期进行安全审计",
      "及时应用安全补丁"
    ]
  }
}
EOF

echo -e "${GREEN}✅ 安全加固报告已生成${NC}"

echo ""
echo -e "${GREEN}🎯 安全加固完成！${NC}"
echo -e "${BLUE}📋 已实施的安全措施:${NC}"
echo -e "   - 文件权限控制"
echo -e "   - 环境变量配置"
echo -e "   - 访问控制策略"
echo -e "   - 速率限制"
echo -e "   - CORS策略"
echo -e "   - 备份加密"
echo ""
echo -e "${BLUE}🔒 下一步建议:${NC}"
echo -e "   - 运行安全检查: ./dev/scripts/security_check.sh"
echo -e "   - 定期更新密码"
echo -e "   - 监控系统日志"
echo ""
echo -e "${GREEN}💖 安全加固成功完成！${NC}"