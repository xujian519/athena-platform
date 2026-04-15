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
