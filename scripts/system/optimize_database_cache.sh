#!/bin/bash
# PostgreSQL SSD缓存优化脚本

# 创建临时缓存目录
mkdir -p /tmp/pg_cache

# 设置PostgreSQL参数优化（需要管理员权限）
cat > postgresql_cache_optimize.conf << 'EOL'
# SSD缓存优化配置
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
EOL

echo "SSD缓存配置已生成"
echo "请手动应用到PostgreSQL配置文件"
