#!/bin/bash
# 安全的括号修复脚本
# 只修复明确的错误模式，不尝试智能匹配

set -e

TARGET_DIR="${1:-/Users/xujian/Athena工作平台/core}"

echo "🔧 安全的括号修复工具"
echo "===================="
echo "目标目录: $TARGET_DIR"
echo ""

# 统计原始错误数
echo "📊 统计原始错误..."
ORIGINAL_ERRORS=$(find "$TARGET_DIR" -name "*.py" | xargs -I {} python3 -m py_compile {} 2>&1 | grep -c "SyntaxError" || true)
echo "原始语法错误数: $ORIGINAL_ERRORS"
echo ""

# 修复模式1: Optional[list[str] = None -> Optional[list[str]] = None
echo "🔧 修复模式1: Optional[list[str] = None"
find "$TARGET_DIR" -name "*.py" -type f -exec sed -i '' \
    's/Optional\[list\[str\] = None/Optional[list[str]] = None/g' {} \;

# 修复模式2: Optional[dict[str, Any] = None -> Optional[dict[str, Any]] = None
echo "🔧 修复模式2: Optional[dict[str, Any] = None"
find "$TARGET_DIR" -name "*.py" -type f -exec sed -i '' \
    's/Optional\[dict\[str, Any\] = None/Optional[dict[str, Any]] = None/g' {} \;

# 修复模式3: Optional[list[dict[str, Any]] = field( -> Optional[list[dict[str, Any]]]] = field(
echo "🔧 修复模式3: Optional[list[dict[str, Any]]] = field("
find "$TARGET_DIR" -name "*.py" -type f -exec sed -i '' \
    's/Optional\[list\[dict\[str, Any\]\]\] = field(/Optional[list[dict[str, Any]]]] = field(/g' {} \;

# 修复模式4: Optional[dict[str, Any]] = field( -> Optional[dict[str, Any]]] = field(
echo "🔧 修复模式4: Optional[dict[str, Any]] = field("
find "$TARGET_DIR" -name "*.py" -type f -exec sed -i '' \
    's/Optional\[dict\[str, Any\]\] = field(/Optional[dict[str, Any]]] = field(/g' {} \;

# 修复模式5: 修复多余的双括号（谨慎使用，只在特定模式下）
# dict[str, asyncio.Task]] = {} -> dict[str, asyncio.Task] = {}
echo "🔧 修复模式5: dict[str, Type]] = （谨慎修复）"
find "$TARGET_DIR" -name "*.py" -type f -exec sed -i '' \
    's/\[str, asyncio\.Task\]\] =/[str, asyncio.Task] =/g' {} \;

find "$TARGET_DIR" -name "*.py" -type f -exec sed -i '' \
    's/\[str, set\[str\]\]\] =/[str, set[str]] =/g' {} \;

# 统计修复后的错误数
echo ""
echo "📊 验证修复结果..."
FIXED_ERRORS=$(find "$TARGET_DIR" -name "*.py" | xargs -I {} python3 -m py_compile {} 2>&1 | grep -c "SyntaxError" || true)
echo "修复后语法错误数: $FIXED_ERRORS"
echo ""

# 计算改善
IMPROVEMENT=$((ORIGINAL_ERRORS - FIXED_ERRORS))
PERCENT=$((IMPROVEMENT * 100 / ORIGINAL_ERRORS))

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
    find "$TARGET_DIR" -name "*.py" | xargs -I {} python3 -m py_compile {} 2>&1 | grep "SyntaxError" | head -10
    exit 1
fi
