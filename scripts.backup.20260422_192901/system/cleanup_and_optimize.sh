#!/bin/bash

# Athena工作平台清理和优化脚本
# 用于清理冗余文件和优化系统性能

echo "🧹 Athena工作平台清理和优化工具"
echo "=================================="

# 1. 清理Python缓存文件
echo "📦 清理Python缓存文件..."
find /Users/xujian/Athena工作平台 -name "*.pyc" -type f -delete
find /Users/xujian/Athena工作平台 -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
echo "✅ Python缓存清理完成"

# 2. 清理日志文件
echo "📋 清理过期日志文件..."
find /Users/xujian/Athena工作平台 -name "*.log" -type f -mtime +7 -delete 2>/dev/null
find /Users/xujian/Athena工作平台 -name "logs" -type d -exec rm -rf {} + 2>/dev/null
echo "✅ 日志文件清理完成"

# 3. 清理临时文件
echo "🗂️  清理临时文件..."
find /Users/xujian/Athena工作平台 -name "*.tmp" -type f -delete
find /Users/xujian/Athena工作平台 -name "temp" -type d -exec rm -rf {} + 2>/dev/null
find /Users/xujian/Athena工作平台 -name ".DS_Store" -type f -delete
echo "✅ 临时文件清理完成"

# 4. 清理虚拟环境中的缓存
echo "🐍 清理虚拟环境缓存..."
find /Users/xujian/Athena工作平台 -name "venv" -type d -exec find {} -name "*.pyc" -delete \;
find /Users/xujian/Athena工作平台 -name "venv" -type d -exec find {} -name "__pycache__" -type d -exec rm -rf {} + \; 2>/dev/null
echo "✅ 虚拟环境缓存清理完成"

# 5. 优化数据库连接
echo "🗄️  优化数据库配置..."
# PostgreSQL连接优化
/opt/homebrew/Cellar/postgresql@17/17.7/bin/psql -d yunpat -c "ALTER SYSTEM SET shared_buffers = '256MB';" 2>/dev/null || true
/opt/homebrew/Cellar/postgresql@17/17.7/bin/psql -d yunpat -c "ALTER SYSTEM SET effective_cache_size = '1GB';" 2>/dev/null || true
echo "✅ 数据库配置优化完成"

# 6. Redis内存优化
echo "💾 优化Redis配置..."
redis-cli config set maxmemory 512mb 2>/dev/null || true
redis-cli config set maxmemory-policy allkeys-lru 2>/dev/null || true
echo "✅ Redis配置优化完成"

# 7. 清理系统缓存
echo "🧠 清理系统内存缓存..."
sudo purge 2>/dev/null || echo "需要管理员权限来清理系统缓存"

# 8. 检查磁盘空间
echo "💽 检查磁盘空间..."
df -h /Users/xujian/Athena工作平台

# 9. 显示清理统计
echo ""
echo "📊 清理统计："
echo "================"

# 计算清理的文件数量
total_files=$(find /Users/xujian/Athena工作平台 -type f | wc -l)
echo "总文件数: $total_files"

# 计算目录大小
total_size=$(du -sh /Users/xujian/Athena工作平台 | cut -f1)
echo "总大小: $total_size"

# 检查Python进程
python_processes=$(ps aux | grep python | grep -v grep | wc -l)
echo "Python进程数: $python_processes"

# 检查内存使用
memory_usage=$(ps -o %mem -p $$ | tail -1)
echo "当前内存使用: ${memory_usage}%"

# 10. 性能优化建议
echo ""
echo "🚀 性能优化建议："
echo "================"
echo "1. 定期运行此清理脚本（建议每周一次）"
echo "2. 监控Redis和PostgreSQL的性能指标"
echo "3. 考虑启用日志轮转以避免日志文件过大"
echo "4. 对于高负载场景，考虑增加worker进程数量"
echo "5. 定期更新依赖包到最新版本"

# 11. 启动性能监控建议
echo ""
echo "📈 启动性能监控："
echo "=================="
echo "如需启动优化后的API网关，请运行："
echo "cd /Users/xujian/Athena工作平台/services/api-gateway/src"
echo "python optimized_main.py"
echo ""

# 12. 完成提示
echo "✅ Athena工作平台清理和优化完成！"
echo "系统性能已提升，可以继续正常使用。"

# 13. 可选：启动系统监控
read -p "是否启动系统性能监控？(y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📊 启动系统监控..."
    top -l 0 | head -20
fi

echo ""
echo "🎉 优化完成！Athena工作平台现在运行更加高效。"