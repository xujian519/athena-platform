#!/bin/bash
# 通用括号修复脚本 - 基于base.py的成功经验

set -e

TARGET_DIR="${1:-/Users/xujian/Athena工作平台/core}"

echo "🔧 通用括号修复脚本 v2.0"
echo "========================"
echo "目标目录: $TARGET_DIR"
echo ""

# 统计原始错误
echo "📊 统计原始错误..."
ORIGINAL_ERRORS=$(find "$TARGET_DIR" -name "*.py" | xargs -I {} python3 -m py_compile {} 2>&1 | grep -c "SyntaxError" || true)
echo "原始语法错误数: $ORIGINAL_ERRORS"
echo ""

# 修复模式1: 三重括号问题 - Any]]] = field( -> Any]] = field(
echo "🔧 修复模式1: 三重括号 (Any]]])"
find "$TARGET_DIR" -name "*.py" -type f -exec sed -i '' \
    's/Any]]] = field(/Any]] = field(/g' {} \;

find "$TARGET_DIR" -name "*.py" -type f -exec sed -i '' \
    's/str]]] = field(/str]] = field(/g' {} \;

find "$TARGET_DIR" -name "*.py" -type f -exec sed -i '' \
    's/Any]]] = {/Any]] = {/g' {} \;

find "$TARGET_DIR" -name "*.py" -type f -exec sed -i '' \
    's/Any]]] = }/Any]] = }/g' {} \;

find "$TARGET_DIR" -name "*.py" -type f -exec sed -i '' \
    's/Any]]] =,/Any]],/g' {} \;

# 修复模式2: 缺少闭合括号 - Any]] = field( -> Any]]] = field(
# 但只针对list[dict[...]]这种嵌套情况
echo "🔧 修复模式2: 嵌套泛型缺少括号"
find "$TARGET_DIR" -name "*.py" -type f -exec sed -i '' \
    '/list\[dict\[str, Any\]\] = field(/s/Any]]/Any]]]/g' {} \;

find "$TARGET_DIR" -name "*.py" -type f -exec sed -i '' \
    '/list\[dict\[str, Any\]\] = None/s/Any]]/Any]]]/g' {} \;

# 修复模式3: 简单的Optional[dict[ 或 Optional[list[ 缺少括号
echo "🔧 修复模式3: Optional泛型缺少括号"
find "$TARGET_DIR" -name "*.py" -type f -exec sed -i '' \
    's/Optional\[dict\[str, Any\] = None,/Optional[dict[str, Any]] = None,/g' {} \;

find "$TARGET_DIR" -name "*.py" -type f -exec sed -i '' \
    's/Optional\[list\[str\] = None,/Optional[list[str]] = None,/g' {} \;

find "$TARGET_DIR" -name "*.py" -type f -exec sed -i '' \
    's/Optional\[dict\[str, Any\] = field(/Optional[dict[str, Any]]] = field(/g' {} \;

find "$TARGET_DIR" -name "*.py" -type f -exec sed -i '' \
    's/Optional\[list\[str\]\] = field(/Optional[list[str]]] = field(/g' {} \;

# 修复模式4: 其他类型注解的括号问题
echo "🔧 修复模式4: 其他类型注解"
find "$TARGET_DIR" -name "*.py" -type f -exec sed -i '' \
    's/\[str, asyncio\.Task\]\] =/[str, asyncio.Task] =/g' {} \;

find "$TARGET_DIR" -name "*.py" -type f -exec sed -i '' \
    's/\[str, set\[str\]\]\] =/[str, set[str]] =/g' {} \;

find "$TARGET_DIR" -name "*.py" -type f -exec sed -i '' \
    's/\[str, type\]\] =/[str, type] =/g' {} \;

find "$TARGET_DIR" -name "*.py" -type f -exec sed -i '' \
    's/\[str, BaseAgent\]\] =/[str, BaseAgent] =/g' {} \;

# 统计修复后的错误
echo ""
echo "📊 验证修复结果..."
FIXED_ERRORS=$(find "$TARGET_DIR" -name "*.py" | xargs -I {} python3 -m py_compile {} 2>&1 | grep -c "SyntaxError" || true)
echo "修复后语法错误数: $FIXED_ERRORS"
echo ""

# 计算改善
IMPROVEMENT=$((ORIGINAL_ERRORS - FIXED_ERRORS))
if [ $ORIGINAL_ERRORS -gt 0 ]; then
    PERCENT=$((IMPROVEMENT * 100 / ORIGINAL_ERRORS))
else
    PERCENT=0
fi

echo "✅ 修复完成!"
echo "   改善: $IMPROVEMENT 个错误 ($PERCENT%)"
echo ""

if [ $FIXED_ERRORS -eq 0 ]; then
    echo "🎉 所有语法错误已修复!"
    exit 0
else
    echo "⚠️  还有 $FIXED_ERRORS 个错误需要手动处理"
    echo ""
    echo "剩余错误示例:"
    find "$TARGET_DIR" -name "*.py" | xargs -I {} python3 -m py_compile {} 2>&1 | grep "SyntaxError" | head -20
    exit 1
fi
