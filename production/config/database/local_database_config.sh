#!/bin/bash
# Athena平台 - 本地数据库环境变量配置
# Local Database Environment Variables Configuration
#
# 使用方法:
#   source config/database/local_database_config.sh
#
# 此脚本设置所有必要的环境变量，使项目连接到本地数据库服务

# 颜色输出
export GREEN='\033[0;32m'
export YELLOW='\033[1;33m'
export NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Athena平台 - 本地数据库环境配置${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# PostgreSQL环境变量
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_USER="xujian"
export DB_PASSWORD=""

# 数据库连接URL
export DATABASE_URL="postgresql://xujian@localhost:5432/patent_legal_db"
export DB_LEGAL_URL="postgresql://xujian@localhost:5432/patent_legal_db"
export DB_RULES_URL="postgresql://xujian@localhost:5432/patent_rules"
export DB_MEMORY_URL="postgresql://xujian@localhost:5432/agent_memory_db"

# Qdrant向量数据库
export QDRANT_URL="http://localhost:6333"
export QDRANT_HOST="localhost"
export QDRANT_PORT="6333"

# Redis缓存
export REDIS_URL="redis://localhost:6379/0"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"

# NebulaGraph图数据库
export NEBULA_URI="127.0.0.1:9669"
export NEBULA_HOST="127.0.0.1"
export NEBULA_PORT="9669"
export NEBULA_USER="root"
export NEBULA_PASSWORD="nebula"

# 应用配置
export APP_ENV="local"
export LOG_LEVEL="INFO"

echo -e "${GREEN}✓ 环境变量已设置${NC}"
echo ""
echo "数据库连接:"
echo "  PostgreSQL: localhost:5432 (用户: xujian)"
echo "  Qdrant:     http://localhost:6333"
echo "  Redis:      localhost:6379"
echo "  NebulaGraph:127.0.0.1:9669"
echo ""
echo -e "${YELLOW}提示: 使用 'source config/database/local_database_config.sh' 加载此配置${NC}"
echo ""
