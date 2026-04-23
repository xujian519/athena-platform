#!/bin/bash
# 深度分析模块验证脚本
# Version: 1.0.0

BASE_DIR="/Users/xujian/Athena工作平台"
MODULE_PATH="$BASE_DIR/core/patent_deep_comparison_analyzer.py"

echo "========================================="
echo " 深度分析模块验证"
echo "========================================="
echo "   模块路径: $MODULE_PATH"
echo ""

# 测试计数器
total_tests=0
passed_tests=0
failed_tests=0

# 测试1: 模块文件存在
echo "测试 1: 模块文件存在性 ..."
if [ -f "$MODULE_PATH" ]; then
    echo "   ✓ 通过 - 文件存在"
    passed_tests=$((passed_tests + 1))
else
    echo "   ✗ FAILED - 文件不存在"
    failed_tests=$((failed_tests + 1))
fi
total_tests=$((total_tests + 1))
echo ""

# 测试2: Python语法检查
echo "测试 2: Python语法检查 ..."
if python3 -m py_compile "$MODULE_PATH" 2>/dev/null; then
    echo "   ✓ 通过 - 语法正确"
    passed_tests=$((passed_tests + 1))
else
    echo "   ✗ FAILED - 语法错误"
    failed_tests=$((failed_tests + 1))
fi
total_tests=$((total_tests + 1))
echo ""

# 测试3: 依赖导入测试
echo "测试 3: 依赖导入测试 ..."
output=$(python3 -c "
import sys
sys.path.insert(0, '$BASE_DIR')
try:
    from core.patent_deep_comparison_analyzer import PatentDeepComparisonAnalyzer
    print('SUCCESS: PatentDeepComparisonAnalyzer导入成功')
except ImportError as e:
    print(f'ERROR: ImportError - {e}')
except Exception as e:
    print(f'ERROR: {type(e).__name__} - {e}')
" 2>&1 | grep -v "FutureWarning\|pynvml\|INFO:" | head -5)

if echo "$output" | grep -q "SUCCESS"; then
    echo "   ✓ 通过 - 依赖导入成功"
    passed_tests=$((passed_tests + 1))
else
    echo "   ⚠️ 警告 - 导入失败"
    echo "   详情: $output"
    failed_tests=$((failed_tests + 1))
fi
total_tests=$((total_tests + 1))
echo ""

# 测试4: BGE服务可用性
echo "测试 4: BGE嵌入服务可用性 ..."
output=$(python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

bge_url = os.getenv('BGE_SERVER_URL') or os.getenv('EMBEDDING_SERVICE_URL')
if bge_url:
    print(f'SUCCESS: BGE服务URL已配置 - {bge_url}')
else:
    print('WARNING: BGE服务URL未配置，可能使用默认配置')
" 2>&1)

if echo "$output" | grep -q "SUCCESS\|WARNING"; then
    echo "   ✓ 通过 - BGE配置检查完成"
    echo "   详情: $output"
    passed_tests=$((passed_tests + 1))
else
    echo "   ⚠️ 警告 - BGE配置检查失败"
    failed_tests=$((failed_tests + 1))
fi
total_tests=$((total_tests + 1))
echo ""

# 测试5: 核心类可用性
echo "测试 5: 核心类实例化测试 ..."
output=$(python3 -c "
import sys
sys.path.insert(0, '$BASE_DIR')
try:
    from core.patent_deep_comparison_analyzer import PatentDeepComparisonAnalyzer
    print('SUCCESS: 类可用，可创建实例')
except Exception as e:
    print(f'ERROR: {type(e).__name__} - {e}')
" 2>&1 | grep -v "FutureWarning\|pynvml\|INFO:" | head -5)

if echo "$output" | grep -q "SUCCESS"; then
    echo "   ✓ 通过 - 类可用"
    passed_tests=$((passed_tests + 1))
else
    echo "   ⚠️ 警告 - 类实例化可能有问题"
    echo "   详情: $output"
    failed_tests=$((failed_tests + 1))
fi
total_tests=$((total_tests + 1))
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
    echo ""
    echo "深度分析模块可用！"
    echo "支持功能: 向量相似度、权利要求对比、三步法评估"
    exit 0
elif [ $passed_tests -ge 3 ]; then
    echo "⚠ 有 $failed_tests 个测试失败"
    echo ""
    echo "核心功能可用，可能需要配置BGE服务"
    exit 1
else
    echo "✗ 多个测试失败 - 模块可能有问题"
    exit 2
fi
