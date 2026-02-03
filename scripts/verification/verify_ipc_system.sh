#!/bin/bash
# IPC分类系统验证脚本
# Version: 1.0.0

API_BASE="http://localhost:8000/api/v2/ipc"
BASE_DIR="/Users/xujian/Athena工作平台"

echo "========================================="
echo " IPC分类系统验证"
echo "========================================="
echo "   API地址: $API_BASE"
echo ""

# 测试计数器
total_tests=0
passed_tests=0
failed_tests=0

# 测试1: IPC分类
echo "测试 1: IPC分类 ..."
response=$(curl -s -X POST "$API_BASE/classify" \
  -H "Content-Type: application/json" \
  -d '{"patent_text": "一种激光雷达传感器，用于自动驾驶车辆的环境感知", "top_n": 3}')

total_tests=$((total_tests + 1))

if echo "$response" | grep -q "classifications\|domain_suggestions"; then
    echo "   ✓ 通过"
    echo "   响应: $(echo "$response" | head -c 200)..."
    passed_tests=$((passed_tests + 1))
else
    echo "   ✗ FAILED"
    echo "   响应: $response"
    failed_tests=$((failed_tests + 1))
fi
echo ""

# 测试2: IPC搜索
echo "测试 2: IPC搜索 ..."
response=$(curl -s -X POST "$API_BASE/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "激光雷达", "limit": 5}')

total_tests=$((total_tests + 1))

if echo "$response" | grep -q "results\|ipc_codes"; then
    echo "   ✓ 通过"
    echo "   响应: $(echo "$response" | head -c 200)..."
    passed_tests=$((passed_tests + 1))
else
    echo "   ✗ FAILED"
    echo "   响应: $response"
    failed_tests=$((failed_tests + 1))
fi
echo ""

# 测试3: 领域分析
echo "测试 3: 领域分析 ..."
response=$(curl -s -X POST "$API_BASE/domain/analyze" \
  -H "Content-Type: application/json" \
  -d '{"patent_text": "本发明涉及一种新能源汽车的电池管理系统"}')

total_tests=$((total_tests + 1))

if echo "$response" | grep -q "domain\|field\|analysis"; then
    echo "   ✓ 通过"
    echo "   响应: $(echo "$response" | head -c 200)..."
    passed_tests=$((passed_tests + 1))
else
    echo "   ✗ FAILED"
    echo "   响应: $response"
    failed_tests=$((failed_tests + 1))
fi
echo ""

# 测试4: IPC详情查询
echo "测试 4: IPC详情查询 ..."
response=$(curl -s -X GET "$API_BASE/details/G01N")

total_tests=$((total_tests + 1))

if echo "$response" | grep -q "ipc_code\|description\|title"; then
    echo "   ✓ 通过"
    echo "   响应: $(echo "$response" | head -c 200)..."
    passed_tests=$((passed_tests + 1))
else
    echo "   ✗ FAILED"
    echo "   响应: $response"
    failed_tests=$((failed_tests + 1))
fi
echo ""

# 输出总结
echo "========================================="
echo " 验证总结"
echo "========================================="
echo "总测试数: $total_tests"
echo "通过: $passed_tests"
echo "失败: $failed_tests"
echo ""

if [ $failed_tests -eq 0 ]; then
    echo "✓ 所有测试通过"
    exit 0
elif [ $passed_tests -gt 0 ]; then
    echo "⚠ 有 $failed_tests 个测试失败"
    echo ""
    echo "可能的问题:"
    echo "1. API未注册或路径错误"
    echo "2. IPC分类服务未启动"
    echo "3. 依赖服务不可用 (PostgreSQL/Qdrant)"
    exit 1
else
    echo "✗ 所有测试失败 - 可能是API未注册"
    echo ""
    echo "请检查:"
    echo "1. Athena服务是否运行"
    echo "2. IPC路由是否正确注册: core/api/ipc_routes.py"
    echo "3. 查看日志: tail -f /tmp/athena-api.log"
    exit 2
fi
