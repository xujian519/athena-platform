#!/bin/bash
# 修复评估与反思模块已知限制
# Fix Known Limitations for Evaluation and Reflection Module

set -e  # 遇到错误立即退出

PROJECT_ROOT="/Users/xujian/Athena工作平台"
cd "$PROJECT_ROOT"

echo "========================================================================"
echo "🔧 修复评估与反思模块已知限制"
echo "========================================================================"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ========== 问题1: 修复 autonomous-control 模块导入 ==========

echo ""
echo "📋 问题1: 修复 autonomous-control 模块导入"
echo "------------------------------------------------------------------------"

AUTONOMOUS_DIR="$PROJECT_ROOT/services/autonomous-control"
AUTONOMOUS_NEW_DIR="$PROJECT_ROOT/services/autonomous_control"

if [ -d "$AUTONOMOUS_DIR" ]; then
    echo "🔍 发现目录: $AUTONOMOUS_DIR"

    if [ -d "$AUTONOMOUS_NEW_DIR" ]; then
        echo -e "${YELLOW}⚠️  目标目录已存在: $AUTONOMOUS_NEW_DIR${NC}"
        echo "是否删除并重建? (y/n)"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            echo "🗑️  删除旧目录..."
            rm -rf "$AUTONOMOUS_NEW_DIR"
        else
            echo -e "${RED}❌ 取消操作${NC}"
            exit 1
        fi
    fi

    echo "🔄 重命名目录: autonomous-control → autonomous_control"
    mv "$AUTONOMOUS_DIR" "$AUTONOMOUS_NEW_DIR"

    if [ -d "$AUTONOMOUS_NEW_DIR" ]; then
        echo -e "${GREEN}✅ 目录重命名成功${NC}"
    else
        echo -e "${RED}❌ 目录重命名失败${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  目录不存在: $AUTONOMOUS_DIR${NC}"
    echo "可能已经修复过，继续下一步..."
fi

# 验证导入
echo ""
echo "🔍 验证导入..."
python3 << 'EOF'
import sys
sys.path.insert(0, '/Users/xujian/Athena工作平台')

try:
    from services.autonomous_control.evaluation.evaluation_reflection_engine import (
        EvaluationReflectionEngine,
        EvaluationType,
        ReflectionType,
    )
    print("✅ autonomous_control 模块导入成功")
    print(f"   - EvaluationReflectionEngine: {EvaluationReflectionEngine}")
    print(f"   - EvaluationType: {EvaluationType}")
    print(f"   - ReflectionType: {ReflectionType}")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 问题1修复成功${NC}"
else
    echo -e "${RED}❌ 问题1修复失败${NC}"
    exit 1
fi

# ========== 问题2: 检查 Enhanced Xiaonuo 依赖 ==========

echo ""
echo "📋 问题2: 检查 Enhanced Xiaonuo 依赖"
echo "------------------------------------------------------------------------"

python3 << 'EOF'
import sys
sys.path.insert(0, '/Users/xujian/Athena工作平台')

modules_to_check = [
    ("core.memory.unified_agent_memory_system", "统一记忆系统"),
    ("core.learning.enhanced_meta_learning", "增强元学习引擎"),
    ("core.learning.memory_consolidation_system", "记忆整合系统"),
    ("core.agents.xiaonuo.unified_xiaonuo_agent", "统一小诺智能体"),
]

missing_modules = []
existing_modules = []

print("🔍 检查依赖模块:")
print("-" * 80)

for module_name, description in modules_to_check:
    try:
        __import__(module_name)
        print(f"✅ {description:30s} ({module_name})")
        existing_modules.append(module_name)
    except ImportError as e:
        print(f"❌ {description:30s} ({module_name})")
        print(f"   错误: {e}")
        missing_modules.append((module_name, description, str(e)))

print("-" * 80)
print(f"\n📊 统计:")
print(f"  ✅ 已存在: {len(existing_modules)} 个")
print(f"  ❌ 缺失: {len(missing_modules)} 个")

if missing_modules:
    print(f"\n⚠️  缺失模块详情:")
    for module_name, description, error in missing_modules:
        print(f"  - {description} ({module_name})")
        print(f"    错误: {error}")
EOF

echo ""
echo "🔍 测试 Enhanced Xiaonuo 导入..."

python3 << 'EOF'
import sys
sys.path.insert(0, '/Users/xujian/Athena工作平台')

try:
    from core.agents.xiaonuo.enhanced_xiaonuo import EnhancedXiaonuo
    print("✅ Enhanced Xiaonuo 导入成功")
    print(f"   - 类: {EnhancedXiaonuo}")
except ImportError as e:
    print(f"❌ Enhanced Xiaonuo 导入失败: {e}")
    print("\n💡 建议解决方案:")
    print("   1. 检查依赖模块是否存在")
    print("   2. 修复导入路径")
    print("   3. 创建备用实现")
    print("   4. 简化依赖（注释掉非核心功能）")
EOF

# ========== 更新相关文件 ==========

echo ""
echo "📋 更新相关文件中的路径引用"
echo "------------------------------------------------------------------------"

echo "🔍 查找需要更新的文件..."
echo "   (查找包含 'autonomous-control' 的文件)"

# 查找需要更新的文件（但暂不自动修改，由用户确认）
grep -r "autonomous-control" "$PROJECT_ROOT" \
    --include="*.py" \
    --include="*.sh" \
    --include="*.md" \
    2>/dev/null | head -20 || echo "   ✅ 没有找到需要更新的文件"

echo ""
echo "💡 提示: 如果上述输出显示有文件包含 'autonomous-control'，"
echo "   请手动更新为 'autonomous_control'"

# ========== 总结 ==========

echo ""
echo "========================================================================"
echo "📊 修复总结"
echo "========================================================================"
echo ""
echo "✅ 已完成:"
echo "  1. 重命名目录: autonomous-control → autonomous_control"
echo "  2. 验证模块导入"
echo "  3. 检查依赖模块"
echo ""
echo "📋 后续步骤:"
echo "  1. 如果 Enhanced Xiaonuo 仍有问题，请查看上述错误信息"
echo "  2. 根据需要手动更新文件中的路径引用"
echo "  3. 运行验证脚本确认修复效果:"
echo "     python3 tests/evaluation_reflection_final_verification.py"
echo ""
echo "========================================================================"

exit 0
