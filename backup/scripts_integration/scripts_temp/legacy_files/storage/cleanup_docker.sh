#!/bin/bash
# Docker深度清理脚本
# Deep Docker Cleanup Script

echo "🐳 开始Docker深度清理..."
echo "时间: $(date)"
echo "=================================="

# 显示清理前的磁盘使用情况
echo "📊 清理前磁盘使用情况:"
df -h | grep -E "(Filesystem|/dev)"

# 显示Docker占用的空间
echo ""
echo "🐳 Docker当前占用空间:"
docker system df

# 1. 删除所有停止的容器
echo ""
echo "🗑️ 删除停止的容器..."
stopped_containers=$(docker ps -aq --filter "status=exited")
if [ -n "$stopped_containers" ]; then
    echo "发现 $stopped_containers 个停止的容器，正在删除..."
    docker rm $stopped_containers
else
    echo "没有停止的容器需要删除"
fi

# 2. 删除所有未使用的网络
echo ""
echo "🌐 删除未使用的网络..."
unused_networks=$(docker network ls -q --filter "dangling=true")
if [n "$unused_networks" ]; then
    echo "发现 $unused_networks 个未使用的网络，正在删除..."
    docker network rm $unused_networks
else
    echo "没有未使用的网络需要删除"
fi

# 3. 删除所有未使用的镜像
echo ""
echo "🖼️ 删除未使用的镜像..."
untagged_images=$(docker images -f "dangling=true" -q)
if [n "$untagged_images" ]; then
    echo "发现 $untagged_images 个未使用的镜像，正在删除..."
    docker rmi $untagged_images
else
    echo "没有未使用的镜像需要删除"
fi

# 4. 删除所有未使用的卷
echo ""
echo "💾 删除未使用的卷..."
unused_volumes=$(docker volume ls -q -f "dangling=true")
if [n "$unused_volumes" ]; then
    echo "发现 $unused_volumes 个未使用的卷，正在删除..."
    echo "⚠️ 警告：删除卷将永久删除数据！"
    read -p "是否继续删除？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker volume rm $unused_volumes
    else
        echo "跳过卷删除"
    fi
else
    echo "没有未使用的卷需要删除"
fi

# 5. 强制清理所有Docker资源（最激进）
echo ""
echo "🧹 强制清理所有Docker资源..."
read -p "⚠️ 这将删除所有Docker容器、镜像、网络和卷！确认继续？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "正在执行强制清理..."

    # 停止所有运行中的容器
    echo "停止所有容器..."
    docker stop $(docker ps -q) 2>/dev/null || true

    # 删除所有容器
    echo "删除所有容器..."
    docker rm $(docker ps -aq) 2>/dev/null || true

    # 删除所有镜像
    echo "删除所有镜像..."
    docker rmi -f $(docker images -q) 2>/dev/null || true

    # 删除所有网络
    echo "删除所有网络..."
    docker network rm $(docker network ls -q) 2>/dev/null || true

    # 删除所有卷
    echo "删除所有卷..."
    docker volume rm $(docker volume ls -q) 2>/dev/null || true

    echo "✅ 强制清理完成"
else
    echo "跳过强制清理"
fi

# 6. 清理Docker系统缓存
echo ""
echo "🧹 清理Docker系统缓存..."
docker system prune -a -f

# 7. 清理构建缓存
echo ""
echo "🏗️ 清理构建缓存..."
docker builder prune -a -f

# 8. 清理未使用的构建器
echo ""
echo "🔧 清理未使用的构建器..."
docker buildx prune -f 2>/dev/null || echo "buildx不可用，跳过"

# 显示清理后的磁盘使用情况
echo ""
echo "📊 清理后磁盘使用情况:"
df -h | grep -E "(Filesystem|/dev)"

# 显示清理后的Docker占用空间
echo ""
echo "🐳 清理后Docker占用空间:"
docker system df

# 9. 查看Docker根目录大小
echo ""
echo "📁 Docker根目录占用:"
docker system du

# 10. 如果使用了外置硬盘，检查Docker数据目录
EXTERNAL_DISK="/Volumes/xujian"
if [ -d "$EXTERNAL_DISK/docker" ]; then
    echo ""
    echo "💾 外置硬盘中的Docker数据:"
    du -sh "$EXTERNAL_DISK/docker"/* 2>/dev/null || true
fi

# 11. 显示优化建议
echo ""
echo "💡 Docker优化建议:"
echo "=================================="
echo "1. 设置日志轮转限制："
echo "   echo '{\"log-driver\":\"json-file\",\"log-opts\":{\"max-size\":\"10m\",\"max-file\":\"3\"}}' >> /etc/deployment/docker/daemon.json"
echo ""
echo "2. 定期运行清理脚本："
echo "   0 2 * * * bash /path/to/cleanup_docker.sh"
echo ""
echo "3. 使用多阶段构建减小镜像大小"
echo "   FROM node:16-alpine AS builder"
echo "   # ... 构建步骤"
echo "   FROM alpine:3.18"
echo "   COPY --from=builder /app /app"
echo ""
echo "4. 使用.dockerignore忽略不必要文件"
echo "   echo 'node_modules' > .dockerignore"
echo ""

echo "✅ Docker深度清理完成！"
echo "当前时间: $(date)"
echo ""
echo "📈 清理效果对比:"
echo "- 释放了大量的磁盘空间"
echo "- 提高了Docker运行效率"
echo "- 减少了Docker维护成本"