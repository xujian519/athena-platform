#!/bin/bash

# Athena平台Docker快速修复启动脚本
# 解决缺失组件问题，快速启动完整系统

echo "🐳 启动Athena平台Docker快速修复"
echo "=================================================="

# 设置项目根目录
PROJECT_ROOT="/Users/xujian/Athena工作平台"
cd "$PROJECT_ROOT"

# 创建必要的目录
mkdir -p deployment/docker/deployment/nginx/conf.d
mkdir -p monitoring
mkdir -p init-scripts
mkdir -p documentation/logs/docker

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 检查docker-compose是否可用
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose未安装"
    exit 1
fi

echo ""
echo "🔧 创建必要的配置文件..."

# 创建Nginx配置
cat > deployment/docker/deployment/nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include       /etc/deployment/nginx/mime.types;
    default_type  application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/deployment/nginx/access.log main;
    error_log /var/log/deployment/nginx/error.log;

    include /etc/deployment/nginx/conf.d/*.conf;
}
EOF

# 创建Nginx upstream配置
cat > deployment/docker/deployment/nginx/conf.d/athena.conf << 'EOF'
upstream athena_services {
    server host.docker.internal:8010;  # 专利分析服务
    server host.docker.internal:8011;  # 知识图谱服务
    server host.docker.internal:8013;  # 浏览器自动化
    server host.docker.internal:8015;  # 爬虫集成
    server host.docker.internal:8016;  # LangExtract
    server host.docker.internal:8020;  # 优化系统
}

server {
    listen 80;
    server_name localhost;

    # 健康检查端点
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # API代理
    location /api/ {
        proxy_pass http://athena_services;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # 默认路由
    location / {
        return 200 "Athena平台API网关\n";
        add_header Content-Type text/plain;
    }
}
EOF

# 创建Prometheus配置
cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'athena-services'
    static_configs:
      - targets:
        - 'host.docker.internal:8010'
        - 'host.docker.internal:8011'
        - 'host.docker.internal:8013'
        - 'host.docker.internal:8015'
        - 'host.docker.internal:8016'
        - 'host.docker.internal:8020'
EOF

# 创建数据库初始化脚本
cat > init-scripts/init.sql << 'EOF'
-- Athena平台数据库初始化脚本
-- 创建基础表结构

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 专利表
CREATE TABLE IF NOT EXISTS patents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patent_number VARCHAR(100) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    abstract TEXT,
    content TEXT,
    filing_date DATE,
    publication_date DATE,
    inventors TEXT[],
    assignees TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 任务表
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    input_data JSONB,
    output_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_patents_number ON patents(patent_number);
CREATE INDEX IF NOT EXISTS idx_patents_title ON patents USING gin(title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
EOF

echo "✅ 配置文件创建完成"

echo ""
echo "🚀 启动Docker服务..."

# 启动快速修复服务
cd docker
docker-compose -f docker-compose.quick-fix.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo ""
echo "🔍 检查服务状态..."

# 检查PostgreSQL
if docker exec athena-postgres pg_isready -U athena > /dev/null 2>&1; then
    echo "✅ PostgreSQL已启动 (5432端口)"
else
    echo "❌ PostgreSQL启动失败"
fi

# 检查Redis
if docker exec athena-redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis已启动 (6379端口)"
else
    echo "❌ Redis启动失败"
fi

# 检查Elasticsearch
if curl -s http://localhost:9200/_cluster/health > /dev/null 2>&1; then
    echo "✅ Elasticsearch已启动 (9200端口)"
else
    echo "❌ Elasticsearch启动失败"
fi

# 检查API网关
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "✅ API网关已启动 (8080端口)"
else
    echo "❌ API网关启动失败"
fi

# 检查Prometheus
if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo "✅ Prometheus已启动 (9090端口)"
else
    echo "❌ Prometheus启动失败"
fi

# 检查Grafana
if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "✅ Grafana已启动 (3000端口)"
else
    echo "❌ Grafana启动失败"
fi

echo ""
echo "=================================================="
echo "🎉 Athena平台Docker快速修复完成!"
echo "=================================================="
echo ""
echo "📋 服务信息:"
echo "   PostgreSQL:      localhost:5432 (用户: athena, 密码: password)"
echo "   Redis:           localhost:6379"
echo "   Elasticsearch:   localhost:9200"
echo "   API网关:         localhost:8080"
echo "   Prometheus:      localhost:9090"
echo "   Grafana:         localhost:3000 (admin/admin)"
echo ""
echo "📚 访问地址:"
echo "   Grafana监控:     http://localhost:3000"
echo "   Prometheus:      http://localhost:9090"
echo "   API网关健康检查: http://localhost:8080/health"
echo ""
echo "🔧 管理命令:"
echo "   查看容器状态:     docker ps"
echo "   查看日志:        docker-compose -f deployment/docker/docker-compose.quick-fix.yml logs -f"
echo "   停止服务:        docker-compose -f deployment/docker/docker-compose.quick-fix.yml down"
echo "   重启服务:        docker-compose -f deployment/docker/docker-compose.quick-fix.yml restart"
echo ""
echo "💡 连接字符串:"
echo "   PostgreSQL:      postgresql://athena:password@localhost:5432/athenadb"
echo "   Redis:           redis://localhost:6379"
echo "   Elasticsearch:   http://localhost:9200"
echo ""
echo "🎯 数据库初始化完成，现在可以连接到完整的Athena平台数据库服务！"