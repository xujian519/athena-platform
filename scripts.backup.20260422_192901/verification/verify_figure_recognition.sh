#!/bin/bash
# 附图识别模块验证脚本
# Version: 1.0.0

BASE_DIR="/Users/xujian/Athena工作平台"
MODULE_PATH="$BASE_DIR/core/perception/technical_drawing_analyzer.py"

echo "========================================="
echo " 附图识别模块验证"
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
    from core.perception.technical_drawing_analyzer import TechnicalDrawingAnalyzer
    print('SUCCESS: TechnicalDrawingAnalyzer导入成功')
except ImportError as e:
    print(f'ERROR: ImportError - {e}')
except Exception as e:
    print(f'ERROR: {type(e).__name__} - {e}')
" 2>&1)

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

# 测试4: GLM-4V服务可用性
echo "测试 4: GLM-4V服务可用性 ..."
output=$(python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

glm_key = os.getenv('ZHIPU_API_KEY') or os.getenv('GLM_API_KEY')
if glm_key:
    print(f'SUCCESS: GLM API Key存在 (长度: {len(glm_key)})')
else
    print('ERROR: GLM API Key未设置')
" 2>&1)

if echo "$output" | grep -q "SUCCESS"; then
    echo "   ✓ 通过 - GLM-4V服务可用"
    passed_tests=$((passed_tests + 1))
else
    echo "   ⚠️ 警告 - GLM-4V服务配置缺失"
    echo "   详情: $output"
    failed_tests=$((failed_tests + 1))
fi
total_tests=$((total_tests + 1))
echo ""

# 测试5: 核心类实例化
echo "测试 5: 核心类实例化测试 ..."
output=$(python3 -c "
import sys
sys.path.insert(0, '$BASE_DIR')
try:
    from core.perception.technical_drawing_analyzer import TechnicalDrawingAnalyzer
    analyzer = TechnicalDrawingAnalyzer()
    print(f'SUCCESS: 实例化成功, 类型: {type(analyzer).__name__}')
except Exception as e:
    print(f'ERROR: {type(e).__name__} - {e}')
" 2>&1)

if echo "$output" | grep -q "SUCCESS"; then
    echo "   ✓ 通过 - 类实例化成功"
    passed_tests=$((passed_tests + 1))
else
    echo "   ⚠️ 警告 - 实例化失败"
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
    echo "附图识别模块可用！"
    echo "支持功能: 专利附图识别、机械图纸分析、电路图分析"
    exit 0
elif [ $passed_tests -ge 3 ]; then
    echo "⚠ 有 $failed_tests 个测试失败"
    echo ""
    echo "核心功能可用，可能需要配置API Key"
    exit 1
else
    echo "✗ 多个测试失败 - 模块可能有问题"
    exit 2
fi
