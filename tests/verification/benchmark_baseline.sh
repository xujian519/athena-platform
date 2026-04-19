#!/bin/bash
# Athena Gateway - 优化前基准测试脚本
# 用途：收集优化前的性能基准数据
# 执行时机：优化前执行一次，优化后再执行一次进行对比
# 输出：docs/reports/BENCHMARK_BASELINE_YYYYMMDD.md

set -e

# 配置
GATEWAY_URL="http://localhost:8005"
OUTPUT_DIR="docs/reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="$OUTPUT_DIR/BENCHMARK_BASELINE_$(date +%Y%m%d).md"
ITERATIONS=100
CONCURRENT=10

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 开始报告
cat > "$REPORT_FILE" << EOF
# Athena Gateway - 优化前基准测试报告

> **生成时间**: $(date +"%Y-%m-%d %H:%M:%S")
> **Gateway URL**: $GATEWAY_URL
> **测试配置**: $ITERATIONS 次请求, $CONCURRENT 并发

---

## 1. 系统环境

EOF

echo -e "${YELLOW}=== Athena Gateway 优化前基准测试 ===${NC}"
echo "报告将保存到: $REPORT_FILE"
echo ""

# 检查依赖
check_dependencies() {
    echo -n "检查依赖... "
    command -v curl >/dev/null 2>&1 || { echo -e "${RED}❌ curl未安装${NC}"; exit 1; }
    command -v ab >/dev/null 2>&1 || { echo -e "${YELLOW}⚠️  ab未安装，跳过并发测试${NC}"; }
    command -v jq >/dev/null 2>&1 || { echo -e "${YELLOW}⚠️  jq未安装，部分结果可能无法解析${NC}"; }
    echo -e "${GREEN}✅${NC}"
}

# 系统信息
collect_system_info() {
    echo -e "\n### 1.1 系统配置" >> "$REPORT_FILE"
    echo "\`\`\`" >> "$REPORT_FILE"
    echo "操作系统: $(uname -s) $(uname -r)" >> "$REPORT_FILE"
    echo "架构: $(uname -m)" >> "$REPORT_FILE"
    echo "CPU核心数: $(sysctl -n hw.ncpu 2>/dev/null || nproc 2>/dev/null || echo 'unknown')" >> "$REPORT_FILE"
    echo "内存: $(sysctl -n hw.memsize 2>/dev/null | awk '{printf "%.2f GB", $1/1024/1024/1024}' || free -h | grep Mem | awk '{print $2}' 2>/dev/null || echo 'unknown')" >> "$REPORT_FILE"
    echo "Go版本: $(go version 2>/dev/null | awk '{print $3}' || echo 'unknown')" >> "$REPORT_FILE"
    echo "\`\`\`" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
}

# Gateway健康检查
health_check() {
    echo -n "[1/6] Gateway健康检查... "
    if HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$GATEWAY_URL/health" 2>/dev/null); then
        if [ "$HTTP_CODE" = "200" ]; then
            echo -e "${GREEN}✅ PASS (HTTP $HTTP_CODE)${NC}"

            echo "### 1.2 Gateway状态" >> "$REPORT_FILE"
            echo "- **健康检查**: ✅ HTTP $HTTP_CODE" >> "$REPORT_FILE"

            # 尝试获取更多Gateway信息
            if INFO=$(curl -s "$GATEWAY_URL/health" 2>/dev/null); then
                echo "- **响应内容**:" >> "$REPORT_FILE"
                echo "\`\`\`json" >> "$REPORT_FILE"
                echo "$INFO" | jq '.' 2>/dev/null || echo "$INFO" >> "$REPORT_FILE"
                echo "\`\`\`" >> "$REPORT_FILE"
            fi
            echo "" >> "$REPORT_FILE"
        else
            echo -e "${RED}❌ FAIL (HTTP $HTTP_CODE)${NC}"
            echo "Gateway未正常运行，请先启动服务"
            exit 1
        fi
    else
        echo -e "${RED}❌ FAIL (无法连接)${NC}"
        echo "Gateway未运行，请先启动服务"
        exit 1
    fi
}

# 测试端点列表
declare -A ENDPOINTS=(
    ["健康检查"]="/health:GET"
    ["知识图谱查询"]="/api/v1/kg/query:POST"
    ["向量搜索"]="/api/v1/vector/search:POST"
    ["法律搜索"]="/api/v1/legal/search:POST"
    ["工具列表"]="/api/v1/tools:GET"
    ["服务列表"]="/api/v1/services/instances:GET"
)

# 单端点延迟测试
test_latency() {
    echo -e "\n## 2. 单端点延迟测试" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "| 端点 | 平均延迟 | P50 | P95 | P99 | 最小 | 最大 | 成功率 |"
    echo "|------|---------|-----|-----|-----|------|------|--------|" >> "$REPORT_FILE"

    echo -e "\n[2/6] 单端点延迟测试 ($ITERATIONS 次请求)"

    for name in "${!ENDPOINTS[@]}"; do
        IFS=':' read -r path method <<< "${ENDPOINTS[$name]}"
        echo -n "  测试 $name... "

        # 收集延迟数据
        latencies=()
        success=0
        failed=0

        for i in $(seq 1 $ITERATIONS); do
            start=$(date +%s%3N)
            if [ "$method" = "GET" ]; then
                code=$(curl -s -o /dev/null -w "%{http_code}" "$GATEWAY_URL$path" 2>/dev/null) || true
            else
                code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$GATEWAY_URL$path" \
                    -H "Content-Type: application/json" -d '{}' 2>/dev/null) || true
            fi
            end=$(date +%s%3N)
            latency=$((end - start))

            if [[ "$code" =~ ^(200|201|204|401|422|400)$ ]]; then
                ((success++))
                latencies+=($latency)
            else
                ((failed++))
            fi
        done

        # 计算统计数据
        if [ ${#latencies[@]} -gt 0 ]; then
            sorted_latencies=($(echo "${latencies[@]}" | tr ' ' '\n' | sort -n))
            total=0
            for lat in "${latencies[@]}"; do total=$((total + lat)); done
            avg=$((total / ${#latencies[@]}))

            p50_idx=$((${#sorted_latencies[@]} * 50 / 100))
            p95_idx=$((${#sorted_latencies[@]} * 95 / 100))
            p99_idx=$((${#sorted_latencies[@]} * 99 / 100))

            p50=${sorted_latencies[$p50_idx]}
            p95=${sorted_latencies[$p95_idx]}
            p99=${sorted_latencies[$p99_idx]}
            min=${sorted_latencies[0]}
            max=${sorted_latencies[$-${#sorted_latencies[@]}]}

            success_rate=$((success * 100 / ITERATIONS))

            echo "| $name | ${avg}ms | ${p50}ms | ${p95}ms | ${p99}ms | ${min}ms | ${max}ms | ${success_rate}% |" >> "$REPORT_FILE"
            echo -e "${GREEN}✅${NC} 平均=${avg}ms, P95=${p95}ms, 成功率=${success_rate}%"
        else
            echo "| $name | - | - | - | - | - | - | 0% |" >> "$REPORT_FILE"
            echo -e "${RED}❌ 全部失败${NC}"
        fi
    done
    echo "" >> "$REPORT_FILE"
}

# 并发性能测试（需要ab工具）
test_concurrent() {
    if ! command -v ab >/dev/null 2>&1; then
        echo -e "\n[3/6] 并发性能测试... ${YELLOW}⚠️  跳过 (ab未安装)${NC}"
        return
    fi

    echo -e "\n## 3. 并发性能测试" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "| 端点 | 并发数 | 总请求数 | RPS | 平均延迟 | 失败率 |"
    echo "|------|--------|----------|-----|---------|--------|" >> "$REPORT_FILE"

    echo -e "\n[3/6] 并发性能测试 (并发=$CONCURRENT, 总请求=500)"

    for name in "${!ENDPOINTS[@]}"; do
        IFS=':' read -r path method <<< "${ENDPOINTS[$name]}"
        echo -n "  测试 $name... "

        # 构建ab命令
        if [ "$method" = "GET" ]; then
            cmd="ab -n 500 -c $CONCURRENT -q $GATEWAY_URL$path"
        else
            # POST请求需要临时文件
            tmpfile=$(mktemp)
            echo '{}' > "$tmpfile"
            cmd="ab -n 500 -c $CONCURRENT -q -p $tmpfile -T application/json $GATEWAY_URL$path"
        fi

        # 执行测试并解析结果
        output=$(eval "$cmd" 2>&1) || true

        # 提取关键指标
        rps=$(echo "$output" | grep "Requests per second" | awk '{print $4}')
        avg=$(echo "$output" | grep "Time per request.*mean" | awk '{print $4}' | head -1)
        failed=$(echo "$output" | grep "Failed requests" | awk '{print $3}')

        if [ -n "$rps" ] && [ -n "$avg" ]; then
            failed_pct=$(echo "scale=1; $failed * 100 / 500" | bc 2>/dev/null || echo "0")
            echo "| $name | $CONCURRENT | 500 | ${rps} | ${avg}ms | ${failed_pct}% |" >> "$REPORT_FILE"
            echo -e "${GREEN}✅${NC} RPS=${rps}, 平均=${avg}ms"
        else
            echo "| $name | $CONCURRENT | 500 | - | - | 100% |" >> "$REPORT_FILE"
            echo -e "${RED}❌ 测试失败${NC}"
        fi

        # 清理临时文件
        [ -f "$tmpfile" ] && rm -f "$tmpfile"
    done
    echo "" >> "$REPORT_FILE"
}

# 路由匹配性能
test_router_performance() {
    echo -e "\n## 4. 路由匹配性能" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    echo -e "\n[4/6] 路由匹配性能测试"

    # 测试所有已定义路由
    routes=(
        "/health"
        "/api/v1/kg/query"
        "/api/v1/vector/search"
        "/api/v1/legal/search"
        "/api/v1/tools"
        "/api/v1/services/instances"
        "/api/v1/auth/login"
    )

    echo -n "  测试 ${#routes[@]} 个路由的匹配速度... "

    total_time=0
    iterations=1000

    for i in $(seq 1 $iterations); do
        start=$(date +%s%3N)
        for route in "${routes[@]}"; do
            curl -s -o /dev/null "$GATEWAY_URL$route" 2>/dev/null || true
        done
        end=$(date +%s%3N)
        total_time=$((total_time + end - start))
    done

    avg_time=$((total_time / iterations))
    avg_per_route=$((avg_time / ${#routes[@]}))

    echo "- **路由数量**: ${#routes[@]}" >> "$REPORT_FILE"
    echo "- **测试轮数**: $iterations" >> "$REPORT_FILE"
    echo "- **总耗时**: ${total_time}ms" >> "$REPORT_FILE"
    echo "- **平均每轮**: ${avg_time}ms" >> "$REPORT_FILE"
    echo "- **平均每路由**: ${avg_per_route}ms" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    echo -e "${GREEN}✅${NC} 平均每路由=${avg_per_route}ms"
}

# 连接池状态（如果可访问）
test_connection_pool() {
    echo -e "\n## 5. 连接池状态" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    echo -e "\n[5/6] 连接池状态检查"

    # 尝试从metrics获取连接池信息
    if metrics=$(curl -s "$GATEWAY_URL/metrics" 2>/dev/null); then
        echo "### 5.1 Prometheus指标" >> "$REPORT_FILE"
        echo "\`\`\`" >> "$REPORT_FILE"
        echo "$metrics" | grep -i "pool\|connection" || echo "无连接池相关指标" >> "$REPORT_FILE"
        echo "\`\`\`" >> "$REPORT_FILE"
        echo -e "${GREEN}✅${NC} 已收集指标"
    else
        echo "当前Gateway未暴露连接池指标" >> "$REPORT_FILE"
        echo -e "${YELLOW}⚠️  ${NC}未暴露指标"
    fi
    echo "" >> "$REPORT_FILE"
}

# 内存和CPU使用情况
test_resource_usage() {
    echo -e "\n## 6. 资源使用情况" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    echo -e "\n[6/6] 资源使用情况"

    # 查找Gateway进程
    if pid=$(pgrep -f "athena-gateway|gateway-unified" | head -1); then
        echo "### 6.1 进程信息" >> "$REPORT_FILE"
        echo "- **PID**: $pid" >> "$REPORT_FILE"

        # 内存使用
        if mem=$(ps -o rss= -p "$pid" 2>/dev/null); then
            mem_mb=$((mem / 1024))
            echo "- **内存使用**: ${mem_mb} MB" >> "$REPORT_FILE"
        fi

        # CPU使用
        if cpu=$(ps -o %cpu= -p "$pid" 2>/dev/null); then
            echo "- **CPU使用**: ${cpu}%" >> "$REPORT_FILE"
        fi

        # 线程数
        if threads=$(ps -o nlwp= -p "$pid" 2>/dev/null); then
            echo "- **线程数**: $threads" >> "$REPORT_FILE"
        fi

        # 打开文件数
        if files=$(ls -l /proc/$pid/fd 2>/dev/null | wc -l || lsof -p "$pid" 2>/dev/null | wc -l); then
            echo "- **打开文件数**: $files" >> "$REPORT_FILE"
        fi

        echo -e "${GREEN}✅${NC} 进程PID=$pid, 内存=${mem_mb}MB, CPU=${cpu}%"
    else
        echo "未找到Gateway进程" >> "$REPORT_FILE"
        echo -e "${YELLOW}⚠️  ${NC}未找到进程"
    fi
    echo "" >> "$REPORT_FILE"
}

# 生成总结
generate_summary() {
    echo -e "\n---\n" >> "$REPORT_FILE"
    echo "## 总结" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "此报告包含优化前的性能基准数据。优化完成后，请再次运行此脚本进行对比。" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "**下一步**:" >> "$REPORT_FILE"
    echo "1. 实施 P0 优化项（连接池、日志、限流）" >> "$REPORT_FILE"
    echo "2. 再次运行此脚本收集优化后数据" >> "$REPORT_FILE"
    echo "3. 对比两个报告的性能指标" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "**报告生成时间**: $(date +"%Y-%m-%d %H:%M:%S")" >> "$REPORT_FILE"
}

# 主执行流程
main() {
    check_dependencies
    collect_system_info
    health_check
    test_latency
    test_concurrent
    test_router_performance
    test_connection_pool
    test_resource_usage
    generate_summary

    echo ""
    echo -e "${GREEN}=== 基准测试完成 ===${NC}"
    echo "报告已保存: $REPORT_FILE"
    echo ""
    echo "优化后请再次运行此脚本进行对比:"
    echo "  bash $0"
}

# 执行
main
