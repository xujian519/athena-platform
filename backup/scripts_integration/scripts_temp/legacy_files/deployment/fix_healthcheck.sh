#!/bin/bash
# 修复Docker容器的健康检查配置

echo "🔧 修复Docker容器健康检查配置..."

# 要修复的容器列表
containers=("athena-platform-manager" "athena-xiao-nuo-control" "athena-platform-monitor")

for container in "${containers[@]}"; do
    echo -n "检查容器 $container: "

    # 检查容器是否存在
    if docker ps -a --format 'table {{.Names}}' | grep -q "^$container$"; then
        echo "存在"

        # 获取当前健康检查状态
        health_status=$(docker inspect $container --format='{{.State.Health.Status}}' 2>/dev/null)
        echo "  当前状态: $health_status"

        # 如果健康检查失败，尝试修复
        if [ "$health_status" = "unhealthy" ]; then
            echo "  尝试修复健康检查..."

            # 方法1: 重启容器
            echo "  重启容器..."
            docker restart $container

            # 等待容器启动
            sleep 10

            # 检查健康状态
            new_status=$(docker inspect $container --format='{{.State.Health.Status}}' 2>/dev/null)
            echo "  新状态: $new_status"
        fi
    else
        echo "不存在"
    fi

    echo ""
done

echo "✅ 健康检查修复完成"

# 显示当前所有容器状态
echo ""
echo "📊 当前容器状态:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"