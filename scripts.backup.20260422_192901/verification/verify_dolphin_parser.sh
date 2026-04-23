#!/bin/bash
# Dolphin文档解析验证脚本
# Version: 1.0.0

API_BASE="http://localhost:8000/api/v2/dolphin"

echo "========================================="
echo " Dolphin文档解析验证"
echo "========================================="
echo "   API地址: $API_BASE"
echo ""

# 测试计数器
total_tests=0
passed_tests=0
failed_tests=0

# 测试1: 健康检查
echo "测试 1: 健康检查 ..."
response=$(curl -s "$API_BASE/health")

total_tests=$((total_tests + 1))

if echo "$response" | grep -q "status\|healthy\|ok"; then
    echo "   ✓ 通过"
    echo "   响应: $(echo "$response" | head -c 200)..."
    passed_tests=$((passed_tests + 1))
else
    echo "   ✗ FAILED"
    echo "   响应: $response"
    failed_tests=$((failed_tests + 1))
fi
echo ""

# 测试2: 模型信息
echo "测试 2: 模型信息 ..."
response=$(curl -s "$API_BASE/model/info")

total_tests=$((total_tests + 1))

if echo "$response" | grep -q "model\|version\|engine"; then
    echo "   ✓ 通过"
    echo "   响应: $(echo "$response" | head -c 200)..."
    passed_tests=$((passed_tests + 1))
else
    echo "   ✗ FAILED"
    echo "   响应: $response"
    failed_tests=$((failed_tests + 1))
fi
echo ""

# 测试3: 通用解析（文本测试）
echo "测试 3: 通用解析（文本）..."
response=$(curl -s -X POST "$API_BASE/parse" \
  -H "Content-Type: application/json" \
  -d '{"text": "本发明涉及一种激光雷达传感器，用于自动驾驶。"}')

total_tests=$((total_tests + 1))

if echo "$response" | grep -q "result\|parsed\|content"; then
    echo "   ✓ 通过"
    echo "   响应: $(echo "$response" | head -c 200)..."
    passed_tests=$((passed_tests + 1))
else
    echo "   ✗ FAILED"
    echo "   响应: $response"
    failed_tests=$((failed_tests + 1))
fi
echo ""

# 测试4: 聊天式解析
echo "测试 4: 聊天式解析..."
response=$(curl -s -X POST "$API_BASE/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "解析这段文本：激光雷达是重要的传感器。"}')

total_tests=$((total_tests + 1))

if echo "$response" | grep -q "response\|result\|answer"; then
    echo "   ✓ 通过"
    echo "   响应: $(echo "$response" | head -c 200)..."
    passed_tests=$((passed_tests + 1))
else
    echo "   ✗ FAILED"
    echo "   响应: $response"
    failed_tests=$((failed_tests + 1))
fi
echo ""

# 测试5: 专利文档解析
echo "测试 5: 专利文档解析..."
response=$(curl -s -X POST "$API_BASE/parse/patent" \
  -H "Content-Type: application/json" \
  -d '{"title": "激光雷达传感器", "abstract": "本发明涉及自动驾驶领域的激光雷达。", "claims": "1. 一种激光雷达传感器..."}')

total_tests=$((total_tests + 1))

if echo "$response" | grep -q "parsed\|elements\|analysis"; then
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
    echo "1. Dolphin服务未启动"
    echo "2. 模型未加载"
    echo "3. 依赖服务不可用"
    exit 1
else
    echo "✗ 所有测试失败"
    exit 2
fi
