#!/usr/bin/env bash
# 权利要求解析模块验证脚本
# Verify Claim Parser Module

set -e

PYTHON="${PYTHON:-python3}"
CLAIM_PARSER="/Users/xujian/Athena工作平台/production/scripts/patent_full_text/phase3/claim_parser_v2.py"

echo "🔍 开始验证权利要求解析模块..."
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# 测试计数器
TOTAL_TESTS=0
PASSED_TESTS=0

# 测试函数
test_claim_parser() {
    local test_name="$1"
    local patent_number="$2"
    local claims_text="$3"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    echo -n "测试 $TOTAL_TESTS: $test_name ... "

    # 创建临时Python脚本运行测试
    temp_script=$(mktemp)
    cat > "$temp_script" << EOF
import sys
sys.path.append('/Users/xujian/Athena工作平台')

from claim_parser_v2 import parse_claims

claims_text = '''$claims_text'''

result = parse_claims("$patent_number", claims_text)

if result.success:
    print(f"PASSED: {result.total_claim_count}条权利要求解析成功")
    print(f"独立: {len(result.independent_claims)}, 从属: {len(result.dependent_claims)}")
else:
    print(f"FAILED: {result.error_message}")
    sys.exit(1)
EOF

    output=$($PYTHON "$temp_script" 2>&1)
    result=$?

    rm -f "$temp_script"

    if echo "$output" | grep -q "PASSED"; then
        echo -e "${GREEN}✓ PASSED${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo "   $output"
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "   $output"
    fi
    echo ""
}

echo "=========================================="
echo " 权利要求解析模块验证"
echo "=========================================="
echo ""

# 测试数据1: 简单独立权利要求
test_claim_parser "简单独立权利要求" "CN1234567A" "1. 一种图像识别方法，其特征在于，包括以下步骤：
获取待识别图像；
使用深度学习模型提取图像特征；
根据所述图像特征进行分类识别，得到识别结果。"

# 测试数据2: 独立+从属权利要求
test_claim_parser "独立+从属权利要求" "CN1234568A" "1. 一种基于人工智能的图像识别方法，其特征在于，包括以下步骤：
获取待识别图像；
使用深度学习模型提取图像特征；
根据所述图像特征进行分类识别，得到识别结果。

2. 根据权利要求1所述的图像识别方法，其特征在于，所述深度学习模型为卷积神经网络模型。

3. 根据权利要求1或2所述的图像识别方法，其特征在于，所述待识别图像为医学影像图像。"

# 测试数据3: 复杂引用关系
test_claim_parser "复杂引用关系" "CN1234569A" "1. 一种包装机传送装置，包括机架、传送带和限位板。

2. 根据权利要求1所述的装置，其特征在于，所述限位板可滑动安装。

3. 根据权利要求1或2所述的装置，其特征在于，还包括驱动单元。

4. 根据权利要求2或3所述的装置，其特征在于，所述驱动单元为电机驱动。"

# 总结
echo "=========================================="
echo " 验证总结"
echo "=========================================="
echo "总测试数: $TOTAL_TESTS"
echo -e "通过: ${GREEN}$PASSED_TESTS${NC}"
echo -e "失败: $((TOTAL_TESTS - PASSED_TESTS))${NC}"
echo ""

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo -e "${GREEN}✓ 所有测试通过！权利要求解析模块验证成功。${NC}"
    echo ""
    echo "下一步: 可以开始开发 athena-claims 扩展技能"
    exit 0
else
    echo -e "${RED}✗ 有 $((TOTAL_TESTS - PASSED_TESTS)) 个测试失败${NC}"
    exit 1
fi
