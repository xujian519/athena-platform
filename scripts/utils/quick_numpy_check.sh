#!/bin/bash
# -*- coding: utf-8 -*-
# 快速numpy兼容性检查脚本
# Quick Numpy compatibility check

echo "🔍 Numpy快速检查"
echo "=================="

# 检查Python和Numpy版本
echo ""
echo "📊 版本信息:"
python3 --version
python3 -c "import numpy; print(f'Numpy: {numpy.__version__}')" 2>/dev/null || echo "Numpy: 未安装"

# 快速兼容性测试
echo ""
echo "🧪 兼容性测试:"
if python3 -c "from config.numpy_compatibility import array, random, mean, sum; arr = array([1,2,3,4,5]); print(f'✅ 导入成功, 数组测试通过, sum={sum(arr)}, mean={mean(arr):.2f}')" 2>/dev/null; then
    echo "  ✅ 兼容性配置正常"
else
    echo "  ❌ 兼容性配置有问题"
    echo ""
    echo "💡 修复建议:"
    echo "  1. 运行: python3 tools/fix_numpy_compatibility.py --directory ."
    echo "  2. 或查看: docs/development_guidelines_numpy.md"
fi

# 检查需要修复的文件
echo ""
echo "🔧 项目状态:"
ISSUES=$(python3 tools/fix_numpy_compatibility.py --directory . --dry-run 2>&1 | grep "修复文件数:" | awk '{print $3}' || echo "0")
if [ "$ISSUES" -eq 0 ]; then
    echo "  ✅ 所有文件兼容性良好"
else
    echo "  ⚠️ 发现 $ISSUES 个文件需要修复"
fi

# 显示使用提示
echo ""
echo "📚 快速命令:"
echo "  完整检查: python3 tools/manage_numpy_versions.py"
echo "  运行测试: python3 test_numpy_compatibility.py"
echo "  自动维护: ./scripts/auto_update_numpy.sh"
echo ""
echo "📖 查看文档: docs/development_guidelines_numpy.md"